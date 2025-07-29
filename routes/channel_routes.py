from flask import Blueprint, render_template, abort, jsonify, request
from services.youtube_service import get_channels_details_batch
import logging

channel_routes = Blueprint('channel_routes', __name__)
logger = logging.getLogger(__name__)


@channel_routes.route('/channel/<string:channel_id>')
def detail(channel_id):
    # 채널 정보 가져오기 (SEO/OG 태그용)
    channel_info = None
    try:
        # 채널 상세 정보 가져오기
        channels_data = get_channels_details_batch([channel_id])
        if channels_data and len(channels_data) > 0:
            channel_info = channels_data[0]
            logger.info(f"Channel info fetched for SEO: {channel_info.get('snippet', {}).get('title', 'Unknown')}")
    except Exception as e:
        logger.warning(f"Failed to fetch channel info for SEO: {e}")
        # SEO 정보 없이도 계속 진행

    # Channel analysis feature is temporarily disabled while we collect more data
    # Return JSON for AJAX requests, HTML for direct access
    if request.headers.get('Accept', '').startswith('application/json'):
        return jsonify({
            'success': False,
            'message': '채널 분석 기능은 현재 준비 중입니다. 더 나은 서비스를 위해 데이터를 수집하고 있어요! 🚧'
        }), 503

    # For direct browser access, render a coming soon page with SEO data
    return render_template('channel_coming_soon.html', 
                         channel_id=channel_id, 
                         channel_info=channel_info), 503
