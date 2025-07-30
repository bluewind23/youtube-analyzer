import datetime
from flask import current_app
from flask_login import current_user
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from extensions import db
from models.api_key import ApiKey
from models.admin_api_key import AdminApiKey
from extensions import cache
from functools import wraps


def get_public_youtube_service():
    """공용(관리자) API 키만 순환하며 작동하는 서비스 객체를 반환합니다."""
    admin_keys = AdminApiKey.query.filter_by(
        is_active=True).order_by(AdminApiKey.last_used.asc()).all()
    if not admin_keys:
        current_app.logger.error("No active ADMIN API keys available.")
        return None, None

    for key_instance in admin_keys:
        try:
            service = build(
                'youtube', 'v3', developerKey=key_instance.key, cache_discovery=False)
            service.videos().list(part='id', id='jNQXAC9IVRw').execute()  # 유효성 검사
            key_instance.last_used = datetime.datetime.now(
                datetime.timezone.utc)
            db.session.commit()
            return service, key_instance
        except HttpError as e:
            if e.resp.status in [400, 403]:
                reason = e.content.decode('utf-8')
                if 'quotaExceeded' in reason or 'keyInvalid' in reason:
                    key_instance.deactivate()
            continue
        except Exception as e:
            current_app.logger.error(f"Public key build failed: {e}")
            continue
    return None, None


def get_personal_youtube_service():
    """로그인한 사용자의 개인 API 키만 순환하며 작동하는 서비스 객체를 반환합니다."""
    if not current_user or not current_user.is_authenticated:
        return None, None

    user_keys = ApiKey.query.filter_by(
        user_id=current_user.id, is_active=True).order_by(ApiKey.last_used.asc()).all()
    if not user_keys:
        current_app.logger.warning(
            f"User {current_user.id} has no active personal API keys.")
        return None, None

    for key_instance in user_keys:
        try:
            service = build(
                'youtube', 'v3', developerKey=key_instance.key, cache_discovery=False)
            service.videos().list(part='id', id='jNQXAC9IVRw').execute()  # 유효성 검사
            key_instance.last_used = datetime.datetime.now(
                datetime.timezone.utc)
            db.session.commit()
            return service, key_instance
        except HttpError as e:
            if e.resp.status in [400, 403]:
                reason = e.content.decode('utf-8')
                if 'quotaExceeded' in reason or 'keyInvalid' in reason:
                    key_instance.deactivate()
            continue
        except Exception as e:
            current_app.logger.error(f"Personal key build failed: {e}")
            continue
    return None, None


def handle_api_error(e, api_key_instance):
    """API 에러를 처리하고, 할당량 초과 시 키를 비활성화합니다."""
    if isinstance(e, HttpError) and e.resp.status in [400, 403]:
        reason = e.content.decode('utf-8')
        if 'quotaExceeded' in reason or 'keyInvalid' in reason or 'keyExpired' in reason:
            if api_key_instance:
                api_key_instance.deactivate()
            return True
    current_app.logger.error(f"YouTube API Error: {e}")
    return False


# [수정] @cache.memoize(timeout=21600) 데코레이터를 삭제합니다.
def get_trending_videos(max_results=50, category_id='0'):
    """공용 키를 사용하여 인기 동영상을 가져옵니다."""
    max_retries = 3
    for attempt in range(max_retries):
        youtube, api_key = get_public_youtube_service()
        if not youtube:
            current_app.logger.error(
                "Failed to get public YouTube service for trending videos.")
            return [], None, None
        try:
            request = youtube.videos().list(
                part="snippet,statistics,contentDetails",
                chart="mostPopular", regionCode="KR",
                maxResults=max_results, videoCategoryId=category_id
            )
            response = request.execute()
            processed_items = _process_video_items(
                youtube, response.get("items", []))
            return processed_items, None, youtube
        except HttpError as e:
            handle_api_error(e, api_key)
            # [수정] memoize 캐시를 삭제하는 로직도 함께 제거합니다.
            # cache.delete_memoized(get_trending_videos,
            #                       max_results, category_id)
    return [], None, None


@cache.memoize(timeout=3600)
def search_videos_by_keyword(query, max_results=100, page_token=None, date_filter=None, type_filter='all'):
    """개인 키를 사용하여 키워드로 동영상을 검색합니다."""

    max_retries = 3
    for attempt in range(max_retries):
        youtube, api_key = get_personal_youtube_service()
        if not youtube:
            current_app.logger.error(
                "Failed to get personal YouTube service for search.")
            return [], None, None
        try:
            params = {'part': 'snippet', 'q': query,
                      'maxResults': max_results, 'type': 'video', 'regionCode': 'KR'}
            if page_token:
                params['pageToken'] = page_token
            if type_filter in ['video', 'short']:
                params['videoDuration'] = 'short' if type_filter == 'short' else 'medium'
            if date_filter and date_filter != '전체':
                days = int(date_filter.replace('일 전', ''))
                params['publishedAfter'] = (datetime.datetime.now(
                    datetime.timezone.utc) - datetime.timedelta(days=days)).isoformat("T") + "Z"

            search_response = Youtube().list(**params).execute()
            video_ids = [item['id']['videoId'] for item in search_response.get(
                "items", []) if item.get('id', {}).get('videoId')]
            if not video_ids:
                return [], None, youtube

            video_details = youtube.videos().list(part="snippet,statistics,contentDetails",
                                                  id=",".join(video_ids)).execute()
            processed_items = _process_video_items(
                youtube, video_details.get("items", []))
            return processed_items, search_response.get("nextPageToken"), youtube
        except HttpError as e:
            handle_api_error(e, api_key)
            cache.delete_memoized(search_videos_by_keyword, query,
                                  max_results, page_token, date_filter, type_filter)
    return [], None, None


@cache.memoize(timeout=3600)
def get_channels_details_batch(youtube, channel_ids):
    if not isinstance(channel_ids, tuple):
        channel_ids = tuple(sorted(list(set(channel_ids))))
    if not channel_ids or not youtube:
        return {}
    try:
        return _get_channel_statistics_helper(youtube, channel_ids)
    except HttpError as e:
        current_app.logger.warning(f"get_channels_details_batch failed: {e}")
        raise


def _process_video_items(youtube, items):
    video_data = []
    if not items:
        return video_data
    channel_ids_to_fetch = [item['snippet']['channelId']
                            for item in items if item.get('snippet', {}).get('channelId')]
    channel_details = get_channels_details_batch(
        youtube, tuple(channel_ids_to_fetch))
    for item in items:
        snippet = item.get('snippet', {})
        statistics = item.get('statistics', {})
        video_id = item.get('id')
        if not video_id:
            continue
        channel_id = snippet.get('channelId')
        channel_info = channel_details.get(channel_id, {})
        video_info = {
            'id': video_id, 'title': snippet.get('title'),
            'description': snippet.get('description'),
            'thumbnail_url': snippet.get('thumbnails', {}).get('high', {}).get('url'),
            'thumbnail_url_medium': snippet.get('thumbnails', {}).get('medium', {}).get('url'),
            'publishedAt': snippet.get('publishedAt'),
            'channelId': channel_id, 'channelTitle': snippet.get('channelTitle'),
            'tags': snippet.get('tags', []),
            'duration': item.get('contentDetails', {}).get('duration'),
            'viewCount': int(statistics.get('viewCount', 0) or 0),
            'likeCount': int(statistics.get('likeCount', 0) or 0),
            'commentCount': int(statistics.get('commentCount', 0) or 0),
            'subscriberCount': channel_info.get('subscriberCount', 0)
        }
        video_data.append(video_info)
    return video_data


def _get_channel_statistics_helper(youtube, channel_ids):
    channel_details = {}
    for i in range(0, len(channel_ids), 50):
        chunk = list(channel_ids)[i:i+50]
        request = youtube.channels().list(part="snippet,statistics", id=",".join(chunk))
        response = request.execute()
        for item in response.get('items', []):
            stats = item.get('statistics', {})
            snippet = item.get('snippet', {})
            channel_details[item['id']] = {
                'title': snippet.get('title'),
                'customUrl': snippet.get('customUrl'),
                'thumbnailUrl': snippet.get('thumbnails', {}).get('medium', {}).get('url'),
                'subscriberCount': int(stats.get('subscriberCount', 0) or 0),
                'channelViewCount': int(stats.get('viewCount', 0) or 0),
                'videoCount': int(stats.get('videoCount', 0) or 0)
            }
    return channel_details
