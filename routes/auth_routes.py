# 복사 버튼을 눌러 전체 코드를 복사하세요
from flask import session
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
@auth_routes.route("/login/google/authorized")
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
        if user_email == os.environ.get('ADMIN_EMAIL'):
            user.is_admin = True
        db.session.add(user)
        db.session.commit()
        flash("가입이 완료되었습니다!", "success")
    else:
        user.username = user_info.get("name")
        user.profile_pic = user_info.get("picture")
        db.session.commit()

    # 여기를 수정하세요!
    login_user(user, remember=True)

    from flask import session
    session['user'] = {
        'id': user.id,
        'email': user.email,
        'username': user.username,
        'is_admin': user.is_admin
    }
    session.permanent = True
    session.modified = True

    return redirect(url_for("main_routes.index"))


@auth_routes.route('/mypage', methods=['GET', 'POST'])
# @login_required  # 임시 주석
def mypage():
    from flask import session
    return f"""
    <h1>로그인 디버그</h1>
    <p>current_user.is_authenticated: {current_user.is_authenticated}</p>
    <p>current_user: {current_user}</p>
    <p>session user: {session.get('user', 'No user in session')}</p>
    <p>session _user_id: {session.get('_user_id', 'No _user_id in session')}</p>
    """


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
