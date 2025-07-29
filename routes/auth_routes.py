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

auth_routes = Blueprint('auth_routes', __name__)
google_bp = make_google_blueprint(
    scope=["openid", "https://www.googleapis.com/auth/userinfo.email",
           "https://www.googleapis.com/auth/userinfo.profile"],
    redirect_to='auth_routes.google_login_callback'
)


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


@auth_routes.route("/login/google/callback")
def google_login_callback():
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
        # [수정 또는 추가할 코드 시작]
        # 최초 가입 시 이메일이 관리자 이메일과 같으면 is_admin 플래그 설정
        if user_email == os.environ.get('ADMIN_EMAIL'):
             user.is_admin = True
        # [수정 또는 추가할 코드 끝]
        db.session.add(user)
        db.session.commit()
        flash("가입이 완료되었습니다!", "success")
    else:
        user.username = user_info.get("name")
        user.profile_pic = user_info.get("picture")
        db.session.commit()

    login_user(user)
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
    
    video_categories = SavedVideoCategory.query.filter_by(user_id=current_user.id).order_by(SavedVideoCategory.name).all()
    channel_categories = SavedChannelCategory.query.filter_by(user_id=current_user.id).order_by(SavedChannelCategory.name).all()

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