import datetime
from collections import Counter
from services.youtube_service import get_channels_details_batch

# [수정] 첫 번째 인자로 youtube 서비스 객체를 받도록 변경
def process_videos(youtube, videos, query, date_filter, sort_by, direction, subs_filter="all"):
    if not videos or not isinstance(videos, list):
        return [], []

    channel_ids_to_fetch = list(set(v['channelId'] for v in videos if v.get('channelId')))
    
    channel_details_map = {}
    if youtube and channel_ids_to_fetch:
        channel_details_map = get_channels_details_batch(youtube, tuple(channel_ids_to_fetch))

    processed = []
    all_tags = []

    for video in videos:
        channel_id = video.get('channelId')
        channel_info = channel_details_map.get(channel_id, {})
        video['subscriberCount'] = channel_info.get('subscriberCount', 0)

        view_count = video.get('viewCount', 0)
        like_count = video.get('likeCount', 0)
        video['likeRate'] = (like_count / view_count * 100) if view_count > 0 else 0
        
        published_date_str = video.get("publishedAt", "")
        if published_date_str:
            published_date = datetime.datetime.fromisoformat(published_date_str.replace("Z", "+00:00"))
            days_since_published = (datetime.datetime.now(datetime.timezone.utc) - published_date).days
            video['viewsPerDay'] = view_count / days_since_published if days_since_published >= 1 else view_count
            video['publishedAtFormatted'] = published_date.strftime('%y.%m.%d')
        else:
            video['viewsPerDay'] = 0
            video['publishedAtFormatted'] = 'N/A'

        if query and video.get('tags') and isinstance(video['tags'], list):
            if query.lower() not in [tag.lower() for tag in video['tags']]:
                all_tags.extend(video['tags'])
        
        processed.append(video)

    if subs_filter and subs_filter != 'all':
        subs_map = {
            'micro': (0, 10000), 
            'small': (10000, 100000), 
            'medium': (100000, 1000000),
            'large': (1000000, float('inf'))
        }
        thresholds = subs_map.get(subs_filter)
        if thresholds:
            min_subs, max_subs = thresholds
            processed = [v for v in processed if min_subs <= v.get('subscriberCount', 0) < max_subs]

    top_tags = [tag for tag, count in Counter(all_tags).most_common(7)]

    sort_reverse = (direction == 'desc')
    processed.sort(key=lambda v: v.get(sort_by, 0) or 0, reverse=sort_reverse)

    for i, video in enumerate(processed):
        video['rank'] = i + 1

    return processed, top_tags