from sqlalchemy.orm.exc import NoResultFound
from flask_dance.consumer import oauth_authorized
from flask import redirect, url_for, flash, Blueprint, render_template, request
from flask_login import login_user, logout_user, current_user, login_required
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin, SQLAlchemyStorage
from extensions import db
from models.user import User
from models.api_key import ApiKey
from forms import AddApiKeyForm
from models.search_history import SearchHistory
from models.saved_item import SavedItem
from models.saved_video import SavedVideo, SavedVideoCategory
from models.saved_channel import SavedChannelCategory
import os

auth_routes = Blueprint('auth_routes', __name__)
google_bp = make_google_blueprint(
    client_id=os.getenv("GOOGLE_OAUTH_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_OAUTH_CLIENT_SECRET"),
    scope=["openid", "https://www.googleapis.com/auth/userinfo.email",
           "https://www.googleapis.com/auth/userinfo.profile"]
)

# Flask-Dance 시그널을 사용한 로그인 처리


@oauth_authorized.connect_via(google_bp)
def google_logged_in(blueprint, token):
    if not token:
        flash("로그인에 실패했습니다.", "danger")
        return False

    resp = blueprint.session.get("/oauth2/v2/userinfo")
    if not resp.ok:
        flash("사용자 정보를 가져오는 데 실패했습니다.", "danger")
        return False

    user_info = resp.json()
    user_email = user_info.get("email")
    if not user_email:
        flash("구글 계정에서 이메일 정보를 가져올 수 없습니다.", "danger")
        return False

    user = User.query.filter_by(email=user_email).first()
    if not user:
        user = User(email=user_email, username=user_info.get("name"),
                    profile_pic=user_info.get("picture"))
        if user_email == os.environ.get('ADMIN_EMAIL'):
            user.is_admin = True
        db.session.add(user)
        db.session.commit()
        flash("가입이 완료되었습니다!", "success")
    else:
        user.username = user_info.get("name")
        user.profile_pic = user_info.get("picture")
        db.session.commit()

    login_user(user)
    return False  # Don't redirect automatically


@auth_routes.route("/login")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main_routes.index'))
    return redirect(url_for("google.login"))


@auth_routes.route("/logout")
@login_required
def logout():
    logout_user()
    flash("성공적으로 로그아웃되었습니다.", "success")
    return redirect(url_for("main_routes.index"))


@auth_routes.route('/mypage', methods=['GET', 'POST'])
@login_required
def mypage():
    form = AddApiKeyForm()
    if form.validate_on_submit():
        new_key_value = form.youtube_api_key.data.strip()

        # [수정] 더 안정적이고 명확한 중복 확인 및 추가 로직
        try:
            # 1. 현재 사용자의 모든 키를 가져와서 복호화된 값과 비교
            user_api_keys = ApiKey.query.filter_by(
                user_id=current_user.id).all()
            is_duplicate = any(
                key.key == new_key_value for key in user_api_keys)

            if is_duplicate:
                flash('이미 등록된 API 키입니다.', 'danger')
            else:
                # 2. 중복이 아닐 경우에만 유효성 검사 수행
                from googleapiclient.discovery import build
                from googleapiclient.errors import HttpError
                try:
                    service = build(
                        'youtube', 'v3', developerKey=new_key_value, cache_discovery=False)
                    service.videos().list(part='id', id='jNQXAC9IVRw').execute()

                    # 3. 유효성이 검증되면 새 키를 추가
                    new_api_key = ApiKey(user_id=current_user.id)
                    new_api_key.key = new_key_value
                    db.session.add(new_api_key)
                    db.session.commit()
                    flash('새 API 키가 성공적으로 추가되었습니다!', 'success')

                except HttpError:
                    flash('유효하지 않은 API 키입니다. 키를 다시 확인해주세요.', 'danger')

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                f"API Key submission error for user {current_user.id}: {e}")
            flash('API 키를 추가하는 중 오류가 발생했습니다. 관리자에게 문의하세요.', 'danger')

        return redirect(url_for('auth_routes.mypage'))
    user_api_keys = current_user.api_keys

    # [수정 또는 추가할 코드 시작]
    # 사용자 활동 데이터 조회 (페이지네이션 적용)

    # 각 목록의 페이지 번호를 URL 쿼리 파라미터에서 가져옵니다.
    video_page = request.args.get('video_page', 1, type=int)
    channel_page = request.args.get('channel_page', 1, type=int)
    query_page = request.args.get('query_page', 1, type=int)

    # 한 페이지에 표시할 항목 수
    per_page = 10

    saved_queries = SavedItem.query.filter_by(
        user_id=current_user.id, item_type='query'
    ).order_by(SavedItem.saved_at.desc()).paginate(
        page=query_page, per_page=per_page, error_out=False
    )

    saved_channels = SavedItem.query.filter_by(
        user_id=current_user.id, item_type='channel'
    ).order_by(SavedItem.saved_at.desc()).paginate(
        page=channel_page, per_page=per_page, error_out=False
    )

    saved_videos = SavedVideo.query.filter_by(
        user_id=current_user.id
    ).order_by(SavedVideo.saved_at.desc()).paginate(
        page=video_page, per_page=per_page, error_out=False
    )
    # [수정 또는 추가할 코드 끝]

    # 카테고리별 개수와 함께 비디오 카테고리 조회
    video_categories = []
    categories = SavedVideoCategory.query.filter_by(
        user_id=current_user.id).order_by(SavedVideoCategory.name).all()

    for category in categories:
        video_count = SavedVideo.query.filter_by(
            user_id=current_user.id, category_id=category.id).count()
        category.video_count = video_count
        video_categories.append(category)

    # 기본 카테고리 (카테고리 없는 비디오)
    uncategorized_video_count = SavedVideo.query.filter_by(
        user_id=current_user.id, category_id=None).count()
    if uncategorized_video_count > 0:
        from types import SimpleNamespace
        uncategorized_category = SimpleNamespace()
        uncategorized_category.id = None
        uncategorized_category.name = '기본 카테고리'
        uncategorized_category.video_count = uncategorized_video_count
        video_categories.insert(0, uncategorized_category)

    # 카테고리별 개수와 함께 채널 카테고리 조회
    channel_categories = []
    categories = SavedChannelCategory.query.filter_by(
        user_id=current_user.id).order_by(SavedChannelCategory.name).all()

    for category in categories:
        channel_count = SavedItem.query.filter_by(
            user_id=current_user.id, item_type='channel', category_id=category.id).count()
        category.channel_count = channel_count
        channel_categories.append(category)

    # 기본 카테고리 (카테고리 없는 채널)
    uncategorized_channel_count = SavedItem.query.filter_by(
        user_id=current_user.id, item_type='channel', category_id=None).count()
    if uncategorized_channel_count > 0:
        from types import SimpleNamespace
        uncategorized_category = SimpleNamespace()
        uncategorized_category.id = None
        uncategorized_category.name = '기본 카테고리'
        uncategorized_category.channel_count = uncategorized_channel_count
        channel_categories.insert(0, uncategorized_category)

    return render_template('mypage.html',
                           form=form,
                           api_keys=user_api_keys,
                           title="마이페이지",
                           saved_queries=saved_queries,
                           saved_channels=saved_channels,
                           saved_videos=saved_videos,
                           video_categories=video_categories,
                           channel_categories=channel_categories)


@auth_routes.route('/delete_key/<int:key_id>', methods=['POST'])
@login_required
def delete_key(key_id):
    key_to_delete = ApiKey.query.get_or_404(key_id)

    if key_to_delete.user_id != current_user.id:
        flash('삭제 권한이 없습니다.', 'danger')
        return redirect(url_for('auth_routes.mypage'))

    db.session.delete(key_to_delete)
    db.session.commit()
    flash('API 키가 삭제되었습니다.', 'info')
    return redirect(url_for('auth_routes.mypage'))
