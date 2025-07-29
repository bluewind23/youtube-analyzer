# 복사 버튼을 눌러 전체 코드를 복사하세요
from flask import redirect, url_for, flash, Blueprint, render_template, request
from flask_login import login_user, logout_user, current_user, login_required
from flask_dance.contrib.google import make_google_blueprint, google
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

# Flask-Dance 블루프린트를 생성합니다.
google_bp = make_google_blueprint(
    scope=["openid", "https://www.googleapis.com/auth/userinfo.email",
           "https://www.googleapis.com/auth/userinfo.profile"],
    # 로그인이 성공하면 여기로 지정된 'auth_routes.google_callback' 함수로 리디렉션됩니다.
    redirect_to='auth_routes.google_callback'
)


@auth_routes.route("/login")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main_routes.index'))
    # Flask-Dance가 생성한 로그인 URL(/login/google)로 리디렉션합니다.
    return redirect(url_for("google.login"))


@auth_routes.route("/logout")
@login_required
def logout():
    logout_user()
    flash("성공적으로 로그아웃되었습니다.", "success")
    return redirect(url_for("main_routes.index"))


# [수정된 부분]
# 라이브러리와의 주소 충돌을 피하기 위해 콜백 URL을 고유하게 변경합니다.
# 이전: @auth_routes.route("/login/google/authorized")
@auth_routes.route("/google/callback")
def google_callback():
    if not google.authorized:
        flash("로그인에 실패했습니다.", "danger")
        return redirect(url_for("main_routes.index"))

    resp = google.get("/oauth2/v2/userinfo")
    if not resp.ok:
        flash("사용자 정보를 가져오는 데 실패했습니다.", "danger")
        return redirect(url_for("main_routes.index"))

    user_info = resp.json()
    user_email = user_info.get("email")
    if not user_email:
        flash("구글 계정에서 이메일 정보를 가져올 수 없습니다.", "danger")
        return redirect(url_for("main_routes.index"))

    user = User.query.filter_by(email=user_email).first()
    if not user:
        user = User(email=user_email, username=user_info.get(
            "name"), profile_pic=user_info.get("picture"))
        # 환경 변수에 설정된 관리자 이메일과 동일한 경우 is_admin 플래그를 True로 설정합니다.
        if user_email == os.environ.get('ADMIN_EMAIL'):
            user.is_admin = True
        db.session.add(user)
        db.session.commit()
        flash("가입이 완료되었습니다!", "success")
    else:
        # 기존 사용자의 정보(이름, 프로필 사진)를 최신 정보로 업데이트합니다.
        user.username = user_info.get("name")
        user.profile_pic = user_info.get("picture")
        db.session.commit()

    # Flask-Login 로그인
    login_user(user)

    # 세션에 user 정보 추가 (중요!)
    from flask import session
    session['user'] = {
        'id': user.id,
        'email': user.email,
        'username': user.username,
        'is_admin': user.is_admin
    }

    return redirect(url_for("main_routes.index"))


@auth_routes.route('/mypage', methods=['GET', 'POST'])
@login_required
def mypage():
    form = AddApiKeyForm()
    if form.validate_on_submit():
        new_key_value = form.youtube_api_key.data

        existing_key = ApiKey.query.filter(
            ApiKey.user_id == current_user.id).all()
        is_duplicate = any(k.key == new_key_value for k in existing_key)

        if is_duplicate:
            flash('이미 등록된 API 키입니다.', 'danger')
        else:
            new_api_key = ApiKey(user=current_user)
            new_api_key.key = new_key_value
            db.session.add(new_api_key)
            db.session.commit()
            flash('새 API 키가 성공적으로 추가되었습니다!', 'success')
        return redirect(url_for('auth_routes.mypage'))

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
