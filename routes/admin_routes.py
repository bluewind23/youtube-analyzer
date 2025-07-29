from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, abort
from flask_login import login_required, current_user
from functools import wraps
from extensions import db
from models.admin_api_key import AdminApiKey
from forms import AddAdminApiKeyForm
from models.api_key import KeyEncryptor
import os
import hashlib
import secrets

# 복잡한 관리자 URL 생성
ADMIN_SECRET_PATH = os.environ.get(
    'ADMIN_SECRET_PATH', 'a7b9f3e2d8c1x4m6n9p2q5r8t1v4w7z0')
admin_routes = Blueprint('admin_routes', __name__,
                         url_prefix=f'/sys-mgmt-{ADMIN_SECRET_PATH}')

# [수정 또는 추가할 코드 시작]
# 강화된 관리자 권한 확인 데코레이터 (DB 필드 확인 방식으로 변경)


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 로그인 여부 확인
        if not current_user.is_authenticated:
            current_app.logger.warning(
                f"Admin access attempt without login from IP: {request.remote_addr}")
            flash('관리자 페이지 접근을 위해 로그인이 필요합니다.', 'warning')
            return redirect(url_for('auth_routes.login'))

        # 관리자 권한 확인
        if not getattr(current_user, 'is_admin', False):
            current_app.logger.warning(
                f"Unauthorized admin access attempt by user: {current_user.email} from IP: {request.remote_addr}"
            )
            abort(404)  # 관리자가 아닌 경우 404로 위장

        current_app.logger.info(
            f"Admin access granted for: {current_user.email}")
        return f(*args, **kwargs)
    return decorated_function
# [수정 또는 추가할 코드 끝]

# 관리자 컨텍스트 프로세서


@admin_routes.context_processor
def inject_admin_context():
    unread_feedback_count = 0
    # [수정] 관리자 확인 로직을 is_admin 필드로 변경
    if current_user.is_authenticated and getattr(current_user, 'is_admin', False):
        try:
            from models.feedback import Feedback
            unread_feedback_count = Feedback.query.filter_by(
                is_read=False).count()
        except Exception:
            pass
    return dict(unread_feedback_count=unread_feedback_count)


@admin_routes.route('/')
@admin_routes.route('/dashboard')
@login_required
# @admin_required
def dashboard():
    return f"<h1>Admin 테스트</h1><p>관리자: {current_user.username}</p><p>이메일: {current_user.email}</p><p>관리자 권한: {current_user.is_admin}</p>"


@admin_routes.route('/system-stats')
@login_required
@admin_required
def system_stats():
    """시스템 통계"""
    return render_template('admin/system_stats.html', title="시스템 통계")


@admin_routes.route('/manage-keys', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_keys():
    form = AddAdminApiKeyForm()
    if form.validate_on_submit():
        key_value = form.admin_api_key.data

        encrypted_value = KeyEncryptor.encrypt(key_value)
        if AdminApiKey.query.filter_by(_encrypted_key=encrypted_value).first():
            flash('이미 등록된 키입니다.', 'danger')
        else:
            new_key = AdminApiKey()
            new_key.key = key_value
            db.session.add(new_key)
            db.session.commit()
            flash('새로운 공용 API 키가 등록되었습니다.', 'success')
        return redirect(url_for('admin_routes.manage_keys'))

    keys = AdminApiKey.query.order_by(AdminApiKey.id.desc()).all()
    return render_template('admin/manage_keys.html', form=form, keys=keys, title="공용 API 키 관리")


@admin_routes.route('/delete-key/<int:key_id>', methods=['POST'])
@login_required
@admin_required
def delete_key(key_id):
    key_to_delete = AdminApiKey.query.get_or_404(key_id)
    db.session.delete(key_to_delete)
    db.session.commit()
    flash('공용 API 키가 삭제되었습니다.', 'info')
    return redirect(url_for('admin_routes.manage_keys'))


@admin_routes.route('/feedback')
@login_required
@admin_required
def view_feedback():
    """피드백 목록 보기"""
    from models.feedback import Feedback

    page = request.args.get('page', 1, type=int)
    per_page = 20

    feedback_query = Feedback.query.order_by(Feedback.submitted_at.desc())

    # 필터링 옵션
    filter_type = request.args.get('type')
    if filter_type and filter_type != 'all':
        feedback_query = feedback_query.filter_by(feedback_type=filter_type)

    filter_status = request.args.get('status')
    if filter_status == 'unread':
        feedback_query = feedback_query.filter_by(is_read=False)
    elif filter_status == 'read':
        feedback_query = feedback_query.filter_by(is_read=True)

    feedback_list = feedback_query.paginate(
        page=page, per_page=per_page, error_out=False
    )

    # 통계 정보
    total_feedback = Feedback.query.count()
    unread_count = Feedback.query.filter_by(is_read=False).count()

    return render_template('admin/feedback.html',
                           feedback_list=feedback_list,
                           total_feedback=total_feedback,
                           unread_count=unread_count,
                           current_filter_type=filter_type,
                           current_filter_status=filter_status,
                           title="피드백 관리")


@admin_routes.route('/feedback/<int:feedback_id>/mark-read', methods=['POST'])
@login_required
@admin_required
def mark_feedback_read(feedback_id):
    """피드백을 읽음으로 표시"""
    from models.feedback import Feedback

    feedback = Feedback.query.get_or_404(feedback_id)
    feedback.is_read = True
    db.session.commit()
    flash('피드백이 읽음으로 표시되었습니다.', 'success')
    return redirect(url_for('admin_routes.view_feedback'))


@admin_routes.route('/feedback/<int:feedback_id>/add-note', methods=['POST'])
@login_required
@admin_required
def add_feedback_note(feedback_id):
    """피드백에 관리자 노트 추가"""
    from models.feedback import Feedback

    feedback = Feedback.query.get_or_404(feedback_id)
    admin_note = request.form.get('admin_note', '').strip()

    if admin_note:
        feedback.admin_notes = admin_note
        feedback.is_read = True
        db.session.commit()
        flash('관리자 노트가 추가되었습니다.', 'success')
    else:
        flash('노트 내용을 입력해주세요.', 'warning')

    return redirect(url_for('admin_routes.view_feedback'))


@admin_routes.route('/feedback/<int:feedback_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_feedback(feedback_id):
    """피드백 삭제"""
    from models.feedback import Feedback

    feedback = Feedback.query.get_or_404(feedback_id)
    db.session.delete(feedback)
    db.session.commit()
    flash('피드백이 삭제되었습니다.', 'info')
    return redirect(url_for('admin_routes.view_feedback'))
