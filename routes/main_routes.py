import requests
import math
from flask import Blueprint, render_template, request, flash, url_for, redirect, jsonify, Response, send_file, current_app
from flask_login import current_user
from extensions import db
from services.youtube_service import get_trending_videos, search_videos_by_keyword
from services.video_processor import process_videos
from extensions import cache
import datetime
import io
import csv
import os

main_routes = Blueprint("main_routes", __name__)


@main_routes.route("/")
def index():
    query = request.args.get("query", "")
    page_token = request.args.get("page_token")
    can_search = current_user.is_authenticated and bool(current_user.api_keys)

    saved_channel_ids = []
    is_query_saved = False

    if current_user.is_authenticated:
        from models.saved_item import SavedItem
        saved_channels = SavedItem.query.filter_by(
            user_id=current_user.id, item_type='channel').all()
        saved_channel_ids = [item.item_value for item in saved_channels]
        
        if query:
            existing_saved_query = SavedItem.query.filter_by(
                user_id=current_user.id,
                item_type='query',
                item_value=query
            ).first()
            if existing_saved_query:
                is_query_saved = True

    if request.headers.get('Accept') == 'application/json':
        return get_video_data_api()

    return render_template(
        "main_page.html",
        query=query,
        page_token=page_token,
        active_category=request.args.get("category", "0"),
        view_mode=request.args.get("view", "grid"),
        can_search=can_search,
        saved_channel_ids=saved_channel_ids,
        is_query_saved=is_query_saved
    )


@main_routes.route("/api/videos")
def get_video_data_api():
    query = request.args.get("query", "")
    page_token = request.args.get("page_token")
    can_search = current_user.is_authenticated and bool(current_user.api_keys)

    # 검색과 인기동영상을 구분하여 캐시 키 생성
    if query and query.strip():
        # 검색의 경우
        cache_key = f"search:{query}:{page_token or ''}:{request.args.get('max_results', '50')}"
    else:
        # 인기동영상의 경우 - 카테고리별로 캐시
        cache_key = f"trending:{request.args.get('category', '0')}:{request.args.get('max_results', '50')}"

    cached_data = cache.get(cache_key)
    if cached_data:
        return jsonify(cached_data)

    max_results = int(request.args.get("max_results", 50))

    youtube_service = None

    try:
        if query and query.strip():
            if not can_search:
                return jsonify({'success': False, 'error': '검색 기능은 로그인 후 마이페이지에서 API 키를 등록해야 사용할 수 있습니다.'}), 403

            if current_user.is_authenticated:
                from models.search_history import SearchHistory
                last_search = SearchHistory.query.filter_by(user_id=current_user.id).order_by(
                    SearchHistory.searched_at.desc()).first()
                if not last_search or last_search.search_term.lower() != query.lower():
                    new_search = SearchHistory(
                        user_id=current_user.id, search_term=query)
                    db.session.add(new_search)
                    db.session.commit()

            all_raw_videos = []
            next_page_token_for_loop = page_token
            pages_to_fetch = math.ceil(max_results / 50)

            for _ in range(pages_to_fetch):
                results_per_page = min(50, max_results - len(all_raw_videos))
                if results_per_page <= 0:
                    break
                
                raw_videos_page, page_token_from_service, service = search_videos_by_keyword(
                    query=query, max_results=results_per_page, page_token=next_page_token_for_loop,
                    date_filter=None, type_filter='all'
                )

                if service and not youtube_service:
                    youtube_service = service
                
                all_raw_videos.extend(raw_videos_page)
                next_page_token_for_loop = page_token_from_service
                
                if not next_page_token_for_loop:
                    break

            if not youtube_service:
                return jsonify({'success': False, 'error': '사용 가능한 개인 YouTube API 키가 없습니다. 마이페이지에서 키를 등록해주세요.'}), 500

            processed_videos, recommended_tags = process_videos(
                youtube_service, all_raw_videos, query, "전체", "publishedAt", "desc", "all"
            )

            result = {
                'success': True,
                'videos': processed_videos,
                'recommended_tags': recommended_tags,
                'next_page_token': next_page_token_for_loop,
            }
            cache.set(cache_key, result, timeout=1800)  # 검색 결과는 30분 캐시
            return jsonify(result)

        else: 
            raw_videos, _, youtube_service = get_trending_videos(
                max_results=max_results, category_id=request.args.get("category", "0")
            )
            if not youtube_service:
                return jsonify({'success': False, 'error': '사용 가능한 공용 YouTube API 키가 없습니다. 관리자에게 문의하세요.'}), 500

            processed_videos, recommended_tags = process_videos(
                youtube_service, raw_videos, query, "전체", "publishedAt", "desc", "all"
            )

            result = {
                'success': True,
                'videos': processed_videos,
                'recommended_tags': recommended_tags,
                'next_page_token': None,
            }
            cache.set(cache_key, result, timeout=10800)  # 인기동영상은 3시간 캐시 (GitHub Actions 갱신 주기와 맞춤)
            return jsonify(result)

    except Exception as e:
        current_app.logger.error(f"Error in get_video_data_api: {e}")
        return jsonify({
            'success': False,
            'error': f'비디오 데이터를 불러오는 중 오류가 발생했습니다: {str(e)}'
        }), 500


@main_routes.route("/download-thumbnail")
def download_thumbnail():
    image_url = request.args.get('url')
    title = request.args.get('title', 'thumbnail')
    if not image_url:
        return "이미지 URL이 없습니다.", 400
    try:
        response = requests.get(image_url, stream=True)
        response.raise_for_status()
        safe_title = "".join(c for c in title if c.isalnum()
                             or c in (' ', '.')).rstrip()
        filename = f"{safe_title}_thumbnail.jpg"
        image_io = io.BytesIO(response.content)
        return send_file(
            image_io,
            mimetype='image/jpeg',
            as_attachment=True,
            download_name=filename
        )
    except requests.exceptions.RequestException as e:
        print(f"이미지 다운로드 실패: {e}")
        return "이미지를 다운로드할 수 없습니다.", 500


@main_routes.route("/download-csv")
def download_csv():
    query = request.args.get("query", "")
    date_filter = request.args.get("date", "")
    sort_by = request.args.get("sort", "publishedAt")
    direction = request.args.get("direction", "desc")
    subs_filter = request.args.get("subs", "all")
    type_filter = request.args.get("type", "all")
    category_id = request.args.get("category", "0")

    all_raw_videos = []
    youtube_service = None

    if query:
        if not current_user.is_authenticated or not current_user.api_keys:
            flash("CSV 다운로드는 로그인 및 API 키 등록이 필요합니다.", "danger")
            return redirect(url_for('main_routes.index'))

        next_page_token = None
        for _ in range(5):
            raw_videos, page_token, service = search_videos_by_keyword(
                query=query, max_results=50, page_token=next_page_token,
                date_filter=date_filter, type_filter=type_filter
            )
            if service and not youtube_service:
                youtube_service = service
            all_raw_videos.extend(raw_videos)
            if not page_token:
                break
            next_page_token = page_token
    else:
        raw_videos, _, service = get_trending_videos(max_results=100, category_id=category_id)
        if service and not youtube_service:
            youtube_service = service
        all_raw_videos.extend(raw_videos)

    if not youtube_service:
        flash("데이터를 불러올 수 있는 API 키가 없습니다.", "danger")
        return redirect(request.referrer or url_for('main_routes.index'))

    processed_videos, _ = process_videos(
        youtube_service, all_raw_videos, query, date_filter, sort_by, direction, subs_filter)

    if not processed_videos:
        flash("다운로드할 데이터가 없습니다.", "info")
        return redirect(request.referrer or url_for('main_routes.index'))

    output = io.StringIO()
    writer = csv.writer(output)
    headers = ["Rank", "Title", "Channel", "Subscribers", "Views", "Likes",
               "Like Rate (%)", "Comments", "Views per Day", "Published At", "URL"]
    writer.writerow(headers)
    for video in processed_videos:
        video_id = video.get('id')
        if isinstance(video_id, dict):
            video_id = video_id.get('videoId', '')

        row = [
            video.get('rank', ''), video.get(
                'title', ''), video.get('channelTitle', ''),
            video.get('subscriberCount', 0), video.get(
                'viewCount', 0), video.get('likeCount', 0),
            f"{video.get('likeRate', 0):.2f}", video.get('commentCount', 0),
            f"{video.get('viewsPerDay', 0):.2f}", video.get(
                'publishedAtFormatted', ''),
            f"https://www.youtube.com/watch?v={video_id}"
        ]
        writer.writerow(row)

    output.seek(0)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"youtube_analysis_{timestamp}.csv"
    return Response(output.getvalue(), mimetype="text/csv", headers={"Content-Disposition": f"attachment;filename={filename}"})


@main_routes.route('/suggestions')
def get_suggestions():
    query = request.args.get('q', '')
    if not query:
        return jsonify({"suggestions": []})
    url = "http://suggestqueries.google.com/complete/search"
    params = {"client": "firefox", "q": query, "ds": "yt", "hl": "ko"}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        suggestions = response.json()[1]
        return jsonify({"suggestions": suggestions})
    except:
        return jsonify({"suggestions": []}), 500


@main_routes.route('/channel-tooltip/<channel_id>')
def channel_tooltip(channel_id):
    from services.youtube_service import get_public_youtube_service, get_channels_details_batch
    from models.channel_stats import ChannelStats

    try:
        cached_stats = ChannelStats.get_latest_stats(channel_id)
        if cached_stats:
            from datetime import datetime, timedelta
            if datetime.utcnow() - cached_stats.recorded_at < timedelta(hours=24):
                return jsonify({"success": True, "data": {"title": cached_stats.channel_title, "subscriberCount": cached_stats.subscriber_count, "videoCount": cached_stats.video_count, "avgViewsPerVideo": int(cached_stats.avg_views_per_video), "thumbnailUrl": cached_stats.thumbnail_url}})

        youtube, _ = get_public_youtube_service()
        if not youtube:
            return jsonify({"success": False, "error": "사용 가능한 공용 API 키가 없습니다."}), 503

        # [수정] get_channels_details_batch는 딕셔너리를 반환하므로, 잘못된 인덱싱 로직[0]을 제거
        channel_details = get_channels_details_batch(
            youtube, tuple([channel_id]))
        
        if not channel_details or channel_id not in channel_details:
            return jsonify({"success": False, "error": "채널 정보를 찾을 수 없습니다."}), 404

        channel = channel_details[channel_id]
        try:
            channel_data = {
                'id': channel_id, 'title': channel.get('title', ''), 'customUrl': channel.get('customUrl', ''),
                'thumbnailUrl': channel.get('thumbnailUrl', ''), 'subscriberCount': channel.get('subscriberCount', 0),
                'videoCount': channel.get('videoCount', 0), 'channelViewCount': channel.get('channelViewCount', 0)
            }
            ChannelStats.record_stats(channel_data)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.warning(
                f"Failed to save channel stats for {channel_id}: {e}")

        avg_views_per_video = 0
        video_count = channel.get('videoCount', 0)
        if video_count > 0:
            avg_views_per_video = channel.get('channelViewCount', 0) / video_count

        return jsonify({
            "success": True,
            "data": {
                "title": channel.get('title', ''), "subscriberCount": channel.get('subscriberCount', 0),
                "videoCount": video_count, "avgViewsPerVideo": int(avg_views_per_video),
                "thumbnailUrl": channel.get('thumbnailUrl', '')
            }
        })
    except Exception as e:
        current_app.logger.error(f"Error fetching channel tooltip data for {channel_id}: {e}")
        return jsonify({"success": False, "error": "서버 오류가 발생했습니다."}), 500


@main_routes.route('/submit-feedback', methods=['POST'])
def submit_feedback():
    """사용자 피드백 제출"""
    try:
        from models.feedback import Feedback
        
        data = request.get_json()
        if not data or not data.get('message'):
            return jsonify({"success": False, "error": "메시지가 필요합니다."}), 400
        
        feedback = Feedback(
            feedback_type=data.get('feedback_type', 'general'),
            message=data.get('message'),
            user_ip=request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr),
            user_agent=request.headers.get('User-Agent', '')[:500]  # Limit length
        )
        
        db.session.add(feedback)
        db.session.commit()
        
        current_app.logger.info(f"New feedback submitted: {feedback.feedback_type} - {len(feedback.message)} chars")
        
        return jsonify({"success": True, "message": "피드백이 성공적으로 전송되었습니다."})
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error submitting feedback: {e}")
        return jsonify({"success": False, "error": "피드백 전송 중 오류가 발생했습니다."}), 500


@main_routes.route('/api-guide')
def api_guide():
    """YouTube API 키 등록 가이드 페이지"""
    return render_template('api_guide.html', title="YouTube API 키 설정 가이드")


@main_routes.route('/api/warm-cache', methods=['POST'])
def warm_cache_api():
    """캐시 워밍을 위한 API 엔드포인트 (GitHub Actions용)"""
    # 보안을 위한 토큰 확인
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"success": False, "error": "인증이 필요합니다."}), 401
    
    token = auth_header.split(' ')[1]
    # 환경변수에서 설정한 토큰과 비교
    expected_token = current_app.config.get('CACHE_WARM_TOKEN')
    if not expected_token or token != expected_token:
        return jsonify({"success": False, "error": "잘못된 토큰입니다."}), 403
    
    try:
        # 기존 캐시 먼저 지우기
        from extensions import cache
        
        # 주요 카테고리 목록
        popular_categories = ['0', '1', '2', '10', '15', '17', '19', '20', '22', '23', '24', '25', '26', '27', '28']
        
        # 기존 인기동영상 캐시 삭제
        for category_id in popular_categories:
            cache_key = f"trending:{category_id}:50"
            cache.delete(cache_key)
            
        # get_trending_videos 함수의 memoize 캐시도 강제 삭제
        cache.delete_memoized(get_trending_videos)
        
        success_count = 0
        error_count = 0
        
        for category_id in popular_categories:
            try:
                videos, _, service = get_trending_videos(max_results=50, category_id=category_id)
                if videos:
                    success_count += 1
                    current_app.logger.info(f"Cache warmed for category {category_id}: {len(videos)} videos")
                else:
                    error_count += 1
                    current_app.logger.warning(f"No videos found for category {category_id}")
            except Exception as e:
                error_count += 1
                current_app.logger.error(f"Failed to warm cache for category {category_id}: {e}")
        
        return jsonify({
            "success": True,
            "message": f"캐시 워밍 완료: {success_count}개 성공, {error_count}개 실패",
            "details": {
                "success_count": success_count,
                "error_count": error_count,
                "total_categories": len(popular_categories)
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Cache warming failed: {e}")
        return jsonify({"success": False, "error": "캐시 워밍 중 오류 발생"}), 500


@main_routes.route('/api/clear-cache', methods=['POST'])
def clear_cache_api():
    """캐시 강제 삭제 API (관리자용)"""
    # 보안을 위한 토큰 확인
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"success": False, "error": "인증이 필요합니다."}), 401
    
    token = auth_header.split(' ')[1]
    expected_token = current_app.config.get('CACHE_WARM_TOKEN')
    if not expected_token or token != expected_token:
        return jsonify({"success": False, "error": "잘못된 토큰입니다."}), 403
    
    try:
        # 모든 캐시 삭제
        cache.clear()
        current_app.logger.info("All cache cleared manually")
        
        return jsonify({
            "success": True,
            "message": "모든 캐시가 삭제되었습니다."
        })
        
    except Exception as e:
        current_app.logger.error(f"Cache clearing failed: {e}")
        return jsonify({"success": False, "error": "캐시 삭제 중 오류 발생"}), 500