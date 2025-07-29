from flask import Blueprint, request, jsonify, Response
from flask_login import current_user, login_required
from functools import wraps
from models import db
from models.saved_item import SavedItem
from models.saved_video import SavedVideo, SavedVideoCategory
from models.saved_channel import SavedChannelCategory
import csv
import io

user_actions_routes = Blueprint('user_actions_routes', __name__)

def api_login_required(f):
    """API 전용 로그인 필수 데코레이터 - 401 JSON 응답 반환"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': '로그인이 필요합니다.'}), 401
        return f(*args, **kwargs)
    return decorated_function

@user_actions_routes.route('/save-item', methods=['POST'])
@api_login_required
def save_item():
    data = request.json
    item_type = data.get('item_type')
    item_value = data.get('item_value')
    item_display_name = data.get('item_display_name')
    category_id = data.get('category_id')

    if not all([item_type, item_value]):
        return jsonify({'success': False, 'error': '필수 정보가 누락되었습니다.'}), 400

    # 이미 저장되었는지 확인
    existing_item = SavedItem.query.filter_by(
        user_id=current_user.id,
        item_type=item_type,
        item_value=item_value
    ).first()

    if existing_item:
        return jsonify({'success': False, 'error': '이미 저장된 항목입니다.'})

    # 채널 카테고리 유효성 검증 (채널인 경우에만)
    if item_type == 'channel' and category_id:
        category = SavedChannelCategory.query.filter_by(
            id=category_id,
            user_id=current_user.id
        ).first()
        if not category:
            return jsonify({'success': False, 'error': '존재하지 않는 카테고리입니다.'}), 400

    new_item = SavedItem(
        user_id=current_user.id,
        item_type=item_type,
        item_value=item_value,
        item_display_name=item_display_name,
        category_id=category_id if item_type == 'channel' and category_id else None
    )
    db.session.add(new_item)
    db.session.commit()

    return jsonify({'success': True, 'item': {'id': new_item.id}})

@user_actions_routes.route('/unsave-item', methods=['POST'])
@api_login_required
def unsave_item():
    data = request.json
    item_type = data.get('item_type')
    item_value = data.get('item_value')

    if not all([item_type, item_value]):
        return jsonify({'success': False, 'error': '필수 정보가 누락되었습니다.'}), 400

    item_to_delete = SavedItem.query.filter_by(
        user_id=current_user.id,
        item_type=item_type,
        item_value=item_value
    ).first()

    if not item_to_delete:
        return jsonify({'success': False, 'error': '삭제할 항목을 찾을 수 없습니다.'}), 404

    db.session.delete(item_to_delete)
    db.session.commit()

    return jsonify({'success': True})

@user_actions_routes.route('/delete-saved-item', methods=['POST'])
@api_login_required
def delete_saved_item():
    data = request.json
    item_id = data.get('item_id')

    if not item_id:
        return jsonify({'success': False, 'error': 'ID가 누락되었습니다.'}), 400

    item_to_delete = SavedItem.query.get(item_id)

    if not item_to_delete or item_to_delete.user_id != current_user.id:
        return jsonify({'success': False, 'error': '항목을 찾을 수 없거나 삭제 권한이 없습니다.'}), 404

    db.session.delete(item_to_delete)
    db.session.commit()

    return jsonify({'success': True})


# Video Category API Endpoints
@user_actions_routes.route('/api/video-categories', methods=['GET'])
@api_login_required
def get_video_categories():
    """사용자의 영상 카테고리 목록 조회"""
    try:
        categories = SavedVideoCategory.query.filter_by(user_id=current_user.id).all()
        return jsonify({
            'success': True,
            'categories': [category.to_dict() for category in categories]
        })
    except Exception as e:
        print(f"Error in get_video_categories: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': '카테고리 조회 중 오류가 발생했습니다.'}), 500


@user_actions_routes.route('/api/video-categories', methods=['POST'])
@api_login_required
def create_video_category():
    """새 영상 카테고리 생성"""
    data = request.json
    if not data:
        return jsonify({'success': False, 'error': '요청 데이터가 없습니다.'}), 400
    
    name = (data.get('name') or '').strip()
    description = (data.get('description') or '').strip()
    
    if not name:
        return jsonify({'success': False, 'error': '카테고리 이름은 필수입니다.'}), 400
    
    # 같은 이름의 카테고리가 이미 있는지 확인
    existing_category = SavedVideoCategory.query.filter_by(
        user_id=current_user.id,
        name=name
    ).first()
    
    if existing_category:
        return jsonify({'success': False, 'error': '같은 이름의 카테고리가 이미 존재합니다.'}), 400
    
    # 새 카테고리 생성
    new_category = SavedVideoCategory(
        user_id=current_user.id,
        name=name,
        description=description if description else None
    )
    
    try:
        db.session.add(new_category)
        db.session.commit()
        return jsonify({
            'success': True,
            'category': new_category.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': '카테고리 생성 중 오류가 발생했습니다.'}), 500


@user_actions_routes.route('/api/save-video', methods=['POST'])
@api_login_required
def save_video():
    """영상 저장/해제 토글"""
    data = request.json
    if not data:
        return jsonify({'success': False, 'error': '요청 데이터가 없습니다.'}), 400
    
    # 필수 필드 검증
    required_fields = ['video_id', 'video_title', 'channel_id', 'channel_title']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'success': False, 'error': f'{field}는 필수 항목입니다.'}), 400
    
    video_id = data.get('video_id')
    video_title = data.get('video_title')
    channel_id = data.get('channel_id')
    channel_title = data.get('channel_title')
    thumbnail_url = data.get('thumbnail_url')
    category_id = data.get('category_id')
    notes = (data.get('notes') or '').strip()
    
    # 이미 저장된 영상인지 확인
    existing_video = SavedVideo.query.filter_by(
        user_id=current_user.id,
        video_id=video_id
    ).first()
    
    if existing_video:
        # 이미 저장된 영상이면 삭제 (토글)
        try:
            db.session.delete(existing_video)
            db.session.commit()
            return jsonify({
                'success': True,
                'action': 'removed',
                'message': '영상 저장이 취소되었습니다.'
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': '영상 저장 취소 중 오류가 발생했습니다.'}), 500
    
    # 카테고리 ID가 제공된 경우 유효성 검증
    if category_id:
        category = SavedVideoCategory.query.filter_by(
            id=category_id,
            user_id=current_user.id
        ).first()
        if not category:
            return jsonify({'success': False, 'error': '존재하지 않는 카테고리입니다.'}), 400
    
    # 새 영상 저장
    new_video = SavedVideo(
        user_id=current_user.id,
        category_id=category_id if category_id else None,
        video_id=video_id,
        title=video_title,
        channel_id=channel_id,
        channel_title=channel_title,
        thumbnail_url=thumbnail_url,
        notes=notes if notes else None
    )
    
    try:
        db.session.add(new_video)
        db.session.commit()
        return jsonify({
            'success': True,
            'action': 'saved',
            'message': '영상이 저장되었습니다.',
            'video': new_video.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': '영상 저장 중 오류가 발생했습니다.'}), 500


@user_actions_routes.route('/api/check-saved-video/<video_id>', methods=['GET'])
@api_login_required
def check_saved_video(video_id):
    """영상 저장 상태 확인"""
    try:
        saved_video = SavedVideo.query.filter_by(
            user_id=current_user.id,
            video_id=video_id
        ).first()
        
        return jsonify({
            'success': True,
            'is_saved': saved_video is not None,
            'video': saved_video.to_dict() if saved_video else None
        })
    except Exception as e:
        print(f"Error in check_saved_video: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': '저장 상태 확인 중 오류가 발생했습니다.'}), 500


@user_actions_routes.route('/api/delete-saved-video', methods=['POST'])
@api_login_required
def delete_saved_video():
    """저장된 영상 삭제"""
    data = request.json
    video_id = data.get('video_id')
    
    if not video_id:
        return jsonify({'success': False, 'error': 'video_id가 필요합니다.'}), 400
    
    # 저장된 영상 찾기
    saved_video = SavedVideo.query.filter_by(
        id=video_id,
        user_id=current_user.id
    ).first()
    
    if not saved_video:
        return jsonify({'success': False, 'error': '삭제할 영상을 찾을 수 없습니다.'}), 404
    
    try:
        db.session.delete(saved_video)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': '영상 삭제 중 오류가 발생했습니다.'}), 500


# CSV Export Endpoints
@user_actions_routes.route('/api/export-saved-videos-csv', methods=['GET'])
@api_login_required
def export_saved_videos_csv():
    """저장된 영상 CSV 내보내기"""
    try:
        # 사용자의 저장된 영상 조회
        saved_videos = SavedVideo.query.filter_by(user_id=current_user.id).order_by(SavedVideo.saved_at.desc()).all()
        
        # CSV 데이터 생성
        output = io.StringIO()
        writer = csv.writer(output, lineterminator='\n')
        
        # 헤더 작성
        writer.writerow([
            '영상 제목', '채널명', '카테고리', '메모', 'YouTube URL', 
            '영상 ID', '채널 ID', '썸네일 URL', '저장일시'
        ])
        
        # 데이터 작성
        for video in saved_videos:
            writer.writerow([
                video.title,
                video.channel_title,
                video.category.name if video.category else '기본 카테고리',
                video.notes or '',
                f'https://www.youtube.com/watch?v={video.video_id}',
                video.video_id,
                video.channel_id,
                video.thumbnail_url or '',
                video.saved_at.strftime('%Y-%m-%d %H:%M:%S') if video.saved_at else ''
            ])
        
        # CSV 응답 생성
        output.seek(0)
        response = Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=saved_videos_{current_user.id}.csv'}
        )
        response.headers['Content-Type'] = 'text/csv; charset=utf-8-sig'  # BOM for Excel
        return response
        
    except Exception as e:
        return jsonify({'success': False, 'error': 'CSV 생성 중 오류가 발생했습니다.'}), 500


@user_actions_routes.route('/api/export-saved-queries-csv', methods=['GET'])
@api_login_required
def export_saved_queries_csv():
    """저장된 검색어 CSV 내보내기"""
    try:
        # 사용자의 저장된 검색어 조회
        saved_queries = SavedItem.query.filter_by(
            user_id=current_user.id, 
            item_type='query'
        ).order_by(SavedItem.saved_at.desc()).all()
        
        # CSV 데이터 생성
        output = io.StringIO()
        writer = csv.writer(output, lineterminator='\n')
        
        # 헤더 작성
        writer.writerow(['검색어', '저장일시'])
        
        # 데이터 작성
        for query in saved_queries:
            writer.writerow([
                query.item_value,
                query.saved_at.strftime('%Y-%m-%d %H:%M:%S') if query.saved_at else ''
            ])
        
        # CSV 응답 생성
        output.seek(0)
        response = Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=saved_queries_{current_user.id}.csv'}
        )
        response.headers['Content-Type'] = 'text/csv; charset=utf-8-sig'  # BOM for Excel
        return response
        
    except Exception as e:
        return jsonify({'success': False, 'error': 'CSV 생성 중 오류가 발생했습니다.'}), 500


@user_actions_routes.route('/api/export-saved-channels-csv', methods=['GET'])
@api_login_required
def export_saved_channels_csv():
    """저장된 채널 CSV 내보내기"""
    try:
        # 사용자의 저장된 채널 조회
        saved_channels = SavedItem.query.filter_by(
            user_id=current_user.id, 
            item_type='channel'
        ).order_by(SavedItem.saved_at.desc()).all()
        
        # CSV 데이터 생성
        output = io.StringIO()
        writer = csv.writer(output, lineterminator='\n')
        
        # 헤더 작성
        writer.writerow(['채널명', '채널 ID', 'YouTube URL', '저장일시'])
        
        # 데이터 작성
        for channel in saved_channels:
            writer.writerow([
                channel.item_display_name or channel.item_value,
                channel.item_value,
                f'https://www.youtube.com/channel/{channel.item_value}',
                channel.saved_at.strftime('%Y-%m-%d %H:%M:%S') if channel.saved_at else ''
            ])
        
        # CSV 응답 생성
        output.seek(0)
        response = Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=saved_channels_{current_user.id}.csv'}
        )
        response.headers['Content-Type'] = 'text/csv; charset=utf-8-sig'  # BOM for Excel
        return response
        
    except Exception as e:
        return jsonify({'success': False, 'error': 'CSV 생성 중 오류가 발생했습니다.'}), 500


@user_actions_routes.route('/api/bulk-delete-saved-videos', methods=['POST'])
@api_login_required
def bulk_delete_saved_videos():
    """저장된 영상 일괄 삭제"""
    data = request.json
    video_ids = data.get('video_ids', [])
    
    if not video_ids or not isinstance(video_ids, list):
        return jsonify({'success': False, 'error': '삭제할 영상 ID 목록이 필요합니다.'}), 400
    
    try:
        # 사용자의 저장된 영상들만 삭제
        deleted_videos = SavedVideo.query.filter(
            SavedVideo.id.in_(video_ids),
            SavedVideo.user_id == current_user.id
        ).all()
        
        deleted_count = len(deleted_videos)
        
        for video in deleted_videos:
            db.session.delete(video)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': '일괄 삭제 중 오류가 발생했습니다.'}), 500


# Channel Category API Endpoints
@user_actions_routes.route('/api/channel-categories', methods=['GET'])
@api_login_required
def get_channel_categories():
    """사용자의 채널 카테고리 목록 조회"""
    try:
        categories = SavedChannelCategory.query.filter_by(user_id=current_user.id).all()
        return jsonify({
            'success': True,
            'categories': [category.to_dict() for category in categories]
        })
    except Exception as e:
        print(f"Error in get_channel_categories: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': '카테고리 조회 중 오류가 발생했습니다.'}), 500


@user_actions_routes.route('/api/channel-categories', methods=['POST'])
@api_login_required
def create_channel_category():
    """새 채널 카테고리 생성"""
    data = request.json
    if not data:
        return jsonify({'success': False, 'error': '요청 데이터가 없습니다.'}), 400
    
    name = (data.get('name') or '').strip()
    description = (data.get('description') or '').strip()
    
    if not name:
        return jsonify({'success': False, 'error': '카테고리 이름은 필수입니다.'}), 400
    
    # 같은 이름의 카테고리가 이미 있는지 확인
    existing_category = SavedChannelCategory.query.filter_by(
        user_id=current_user.id,
        name=name
    ).first()
    
    if existing_category:
        return jsonify({'success': False, 'error': '같은 이름의 카테고리가 이미 존재합니다.'}), 400
    
    # 새 카테고리 생성
    new_category = SavedChannelCategory(
        user_id=current_user.id,
        name=name,
        description=description if description else None
    )
    
    try:
        db.session.add(new_category)
        db.session.commit()
        return jsonify({
            'success': True,
            'category': new_category.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': '카테고리 생성 중 오류가 발생했습니다.'}), 500

# Category Update/Delete endpoints
@user_actions_routes.route('/api/video-categories/<int:category_id>', methods=['PUT'])
@api_login_required
def update_video_category(category_id):
    """영상 카테고리 수정"""
    category = SavedVideoCategory.query.filter_by(
        id=category_id,
        user_id=current_user.id
    ).first()
    
    if not category:
        return jsonify({'success': False, 'error': '카테고리를 찾을 수 없습니다.'}), 404
    
    data = request.json
    name = (data.get('name') or '').strip()
    description = (data.get('description') or '').strip()
    
    if not name:
        return jsonify({'success': False, 'error': '카테고리 이름은 필수입니다.'}), 400
    
    # 같은 이름의 다른 카테고리가 있는지 확인
    existing_category = SavedVideoCategory.query.filter(
        SavedVideoCategory.user_id == current_user.id,
        SavedVideoCategory.name == name,
        SavedVideoCategory.id != category_id
    ).first()
    
    if existing_category:
        return jsonify({'success': False, 'error': '같은 이름의 카테고리가 이미 존재합니다.'}), 400
    
    category.name = name
    category.description = description if description else None
    
    try:
        db.session.commit()
        return jsonify({
            'success': True,
            'category': category.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': '카테고리 수정 중 오류가 발생했습니다.'}), 500


@user_actions_routes.route('/api/video-categories/<int:category_id>', methods=['DELETE'])
@api_login_required
def delete_video_category(category_id):
    """영상 카테고리 삭제"""
    category = SavedVideoCategory.query.filter_by(
        id=category_id,
        user_id=current_user.id
    ).first()
    
    if not category:
        return jsonify({'success': False, 'error': '카테고리를 찾을 수 없습니다.'}), 404
    
    # 해당 카테고리의 영상들을 기본 카테고리로 이동
    SavedVideo.query.filter_by(
        category_id=category_id,
        user_id=current_user.id
    ).update({'category_id': None})
    
    try:
        db.session.delete(category)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': '카테고리 삭제 중 오류가 발생했습니다.'}), 500


@user_actions_routes.route('/api/channel-categories/<int:category_id>', methods=['PUT'])
@api_login_required
def update_channel_category(category_id):
    """채널 카테고리 수정"""
    category = SavedChannelCategory.query.filter_by(
        id=category_id,
        user_id=current_user.id
    ).first()
    
    if not category:
        return jsonify({'success': False, 'error': '카테고리를 찾을 수 없습니다.'}), 404
    
    data = request.json
    name = (data.get('name') or '').strip()
    description = (data.get('description') or '').strip()
    
    if not name:
        return jsonify({'success': False, 'error': '카테고리 이름은 필수입니다.'}), 400
    
    # 같은 이름의 다른 카테고리가 있는지 확인
    existing_category = SavedChannelCategory.query.filter(
        SavedChannelCategory.user_id == current_user.id,
        SavedChannelCategory.name == name,
        SavedChannelCategory.id != category_id
    ).first()
    
    if existing_category:
        return jsonify({'success': False, 'error': '같은 이름의 카테고리가 이미 존재합니다.'}), 400
    
    category.name = name
    category.description = description if description else None
    
    try:
        db.session.commit()
        return jsonify({
            'success': True,
            'category': category.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': '카테고리 수정 중 오류가 발생했습니다.'}), 500


@user_actions_routes.route('/api/channel-categories/<int:category_id>', methods=['DELETE'])
@api_login_required
def delete_channel_category(category_id):
    """채널 카테고리 삭제"""
    category = SavedChannelCategory.query.filter_by(
        id=category_id,
        user_id=current_user.id
    ).first()
    
    if not category:
        return jsonify({'success': False, 'error': '카테고리를 찾을 수 없습니다.'}), 404
    
    # 해당 카테고리의 채널들을 기본 카테고리로 이동
    SavedItem.query.filter_by(
        user_id=current_user.id,
        item_type='channel',
        category_id=category_id
    ).update({'category_id': None})
    
    try:
        db.session.delete(category)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': '카테고리 삭제 중 오류가 발생했습니다.'}), 500