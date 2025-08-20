import os
from flask import redirect, url_for, flash, Blueprint, render_template, request
from flask_login import login_user, logout_user, current_user, login_required
from flask_dance.contrib.google import make_google_blueprint
from flask_dance.consumer import oauth_authorized
from extensions import db
from models.user import User
from models.api_key import ApiKey, KeyEncryptor  # KeyEncryptor를 임포트합니다.
from forms import AddApiKeyForm
from models.saved_item import SavedItem
from models.saved_video import SavedVideo, SavedVideoCategory
from models.saved_channel import SavedChannelCategory

auth_routes = Blueprint('auth_routes', __name__)

# 블루프린트 설정은 그대로 유지합니다.
google_bp = make_google_blueprint(
    client_id=os.getenv("GOOGLE_OAUTH_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_OAUTH_CLIENT_SECRET"),
    scope=["openid", "https://www.googleapis.com/auth/userinfo.email",
           "https://www.googleapis.com/auth/userinfo.profile"]
)


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
    return False


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

        # =================== [수정된 API 키 추가 로직 시작] ===================
        # 전체 로직을 try...except로 감싸 예기치 않은 서버 다운을 방지합니다.
        try:
            # 1. 새로 입력된 키를 먼저 암호화합니다.
            encrypted_new_key = KeyEncryptor.encrypt(new_key_value)

            # 2. 암호화된 키가 DB에 이미 있는지 확인합니다. (가장 안전한 중복 확인)
            existing_key = ApiKey.query.filter_by(
                user_id=current_user.id,
                _encrypted_key=encrypted_new_key
            ).first()

            if existing_key:
                flash('이미 등록된 API 키입니다.', 'danger')
            else:
                # 3. 중복이 아니면 YouTube API로 유효성을 검사합니다.
                from googleapiclient.discovery import build
                from googleapiclient.errors import HttpError

                try:
                    service = build(
                        'youtube', 'v3', developerKey=new_key_value, cache_discovery=False)
                    service.videos().list(part='id', id='jNQXAC9IVRw').execute()

                    # 4. 유효한 키라면 암호화된 값으로 DB에 저장합니다.
                    new_api_key = ApiKey(
                        user_id=current_user.id,
                        _encrypted_key=encrypted_new_key
                    )
                    db.session.add(new_api_key)
                    db.session.commit()
                    flash('새 API 키가 성공적으로 추가되었습니다!', 'success')

                except HttpError as e:
                    if e.resp.status in [400, 403]:
                        flash('유효하지 않은 API 키입니다. 키를 다시 확인해주세요.', 'danger')
                    else:
                        flash('API 키 검증 중 서버 오류가 발생했습니다.', 'warning')

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                f"API Key submission error for user {current_user.id}: {e}")
            flash('API 키를 추가하는 중 심각한 오류가 발생했습니다. 관리자에게 문의하세요.', 'danger')
        # =================== [수정된 API 키 추가 로직 끝] =====================

        return redirect(url_for('auth_routes.mypage'))

    # 이하 GET 요청 처리는 기존 코드와 동일합니다.
    user_api_keys = current_user.api_keys

    video_page = request.args.get('video_page', 1, type=int)
    channel_page = request.args.get('channel_page', 1, type=int)
    query_page = request.args.get('query_page', 1, type=int)
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

    video_categories = SavedVideoCategory.query.filter_by(
        user_id=current_user.id).order_by(SavedVideoCategory.name).all()
    channel_categories = SavedChannelCategory.query.filter_by(
        user_id=current_user.id).order_by(SavedChannelCategory.name).all()

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
