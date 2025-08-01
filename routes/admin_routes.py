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
        # is_authenticated: 로그인 여부 확인, is_admin: 관리자 플래그 확인
        if not current_user.is_authenticated or not getattr(current_user, 'is_admin', False):
            current_app.logger.warning(
                f"Unauthorized admin access attempt by user: {getattr(current_user, 'email', 'Anonymous')} from IP: {request.remote_addr}"
            )
            abort(404)  # 404로 위장하여 보안 강화

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
@admin_required
def dashboard():
    """관리자 대시보드"""
    try:
        from models.feedback import Feedback
        from models.user import User
        from models.api_key import ApiKey
        from models.admin_api_key import AdminApiKey

        # 통계 데이터 수집
        total_users = User.query.count()
        total_api_keys = ApiKey.query.count()
        total_admin_keys = AdminApiKey.query.count()
        total_feedback = Feedback.query.count()
        unread_feedback = Feedback.query.filter_by(is_read=False).count()

        # 최근 피드백
        recent_feedback = Feedback.query.order_by(
            Feedback.submitted_at.desc()).limit(5).all()

        # 피드백 타입별 통계
        feedback_stats = db.session.query(
            Feedback.feedback_type,
            db.func.count(Feedback.id)
        ).group_by(Feedback.feedback_type).all()

        return render_template('admin/dashboard.html',
                               total_users=total_users,
                               total_api_keys=total_api_keys,
                               total_admin_keys=total_admin_keys,
                               total_feedback=total_feedback,
                               unread_feedback=unread_feedback,
                               recent_feedback=recent_feedback,
                               feedback_stats=feedback_stats,
                               title="관리자 대시보드")
    except Exception as e:
        current_app.logger.error(f"Dashboard error: {e}")
        flash('대시보드 로딩 중 오류가 발생했습니다.', 'error')
        return render_template('admin/dashboard.html', title="관리자 대시보드")


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


@admin_routes.route('/migrate-database', methods=['GET', 'POST'])
@login_required
@admin_required
def migrate_database():
    """데이터베이스 마이그레이션 실행 (Render.com free tier용)"""
    from flask_migrate import upgrade
    from flask import jsonify
    import traceback
    
    if request.method == 'GET':
        # 마이그레이션 상태 확인 페이지
        try:
            from flask_migrate import current, show
            current_revision = current()
            return render_template('admin/migrate_database.html', 
                                 current_revision=current_revision)
        except Exception as e:
            return render_template('admin/migrate_database.html', 
                                 error=str(e))
    
    # POST 요청: 실제 마이그레이션 실행
    try:
        # 데이터베이스 마이그레이션 실행
        upgrade()
        
        # 테이블 존재 여부 확인
        from models.saved_video import SavedVideo, SavedVideoCategory
        from models.saved_channel import SavedChannelCategory
        
        # 테이블 접근 테스트
        SavedVideo.query.count()
        SavedVideoCategory.query.count() 
        SavedChannelCategory.query.count()
        
        flash('데이터베이스 마이그레이션이 성공적으로 완료되었습니다!', 'success')
        current_app.logger.info(f"Database migration completed by admin: {current_user.email}")
        
        return jsonify({
            'success': True, 
            'message': '마이그레이션이 성공적으로 완료되었습니다.'
        })
        
    except Exception as e:
        error_msg = str(e)
        current_app.logger.error(f"Migration failed: {error_msg}")
        current_app.logger.error(traceback.format_exc())
        
        # 테이블이 없는 경우 강제 생성 시도
        if 'no such table' in error_msg.lower() or 'table' in error_msg.lower():
            try:
                current_app.logger.info("Attempting to create all tables...")
                db.create_all()
                current_app.logger.info("Tables created successfully")
                
                flash('데이터베이스 테이블들이 생성되었습니다!', 'success')
                return jsonify({
                    'success': True,
                    'message': '데이터베이스 테이블들이 생성되었습니다.'
                })
            except Exception as create_error:
                current_app.logger.error(f"Table creation failed: {str(create_error)}")
                flash(f'마이그레이션 실패: {str(create_error)}', 'danger')
                return jsonify({
                    'success': False,
                    'error': str(create_error)
                })
        
        flash(f'마이그레이션 실패: {error_msg}', 'danger')
        return jsonify({
            'success': False,
            'error': error_msg
        })
