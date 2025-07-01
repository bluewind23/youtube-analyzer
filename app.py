from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
import requests
import time
import collections
import os
import json
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import csv
import pandas as pd

app = Flask(__name__)
app.secret_key = 'supersecretkey_for_session'
SECRET_ADMIN_PREFIX = '/admin'

# --- 설정 ---
UPLOAD_FOLDER = 'static/uploads'
SETTINGS_FILE = 'settings.json'
FEEDBACK_FILE = 'feedback.json'
VISITOR_LOG_FILE = 'visitor_log.csv'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --- 캐시 및 통계 변수 ---
search_term_counter_by_date = {}
search_log = collections.deque(maxlen=20)
YOUTUBE_API_BASE_URL = "https://www.googleapis.com/youtube/v3/"
trending_cache = {}
category_cache = {'data': None, 'timestamp': 0}

# --- 방문자 통계 처리 함수 ---


def process_visitor_stats():
    if not os.path.exists(VISITOR_LOG_FILE):
        return {
            "daily_visits": {}, "peak_hour": "N/A", "today_visits": 0,
            "yesterday_visits": 0, "avg_daily_visits": 0, "total_visits": 0
        }

    try:
        df = pd.read_csv(VISITOR_LOG_FILE, header=None, names=['timestamp'])
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        total_visits = len(df)

        daily_counts = df.set_index('timestamp').resample('D').size()
        daily_visits_dict = {date.strftime(
            '%Y-%m-%d'): count for date, count in daily_counts.items()}

        hourly_counts = df['timestamp'].dt.hour.value_counts()
        peak_hour = hourly_counts.idxmax() if not hourly_counts.empty else "N/A"

        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        today_visits = int(daily_counts.get(pd.to_datetime(today), 0))
        yesterday_visits = int(daily_counts.get(pd.to_datetime(yesterday), 0))

        avg_daily_visits = round(
            daily_counts.mean(), 1) if not daily_counts.empty else 0

        return {
            "daily_visits": daily_visits_dict,
            "peak_hour": f"{peak_hour:02d}:00 - {peak_hour+1:02d}:00" if isinstance(peak_hour, int) else "N/A",
            "today_visits": today_visits,
            "yesterday_visits": yesterday_visits,
            "avg_daily_visits": avg_daily_visits,
            "total_visits": total_visits
        }
    except Exception as e:
        print(f"Error processing visitor stats: {e}")
        return {
            "daily_visits": {}, "peak_hour": "N/A", "today_visits": 0,
            "yesterday_visits": 0, "avg_daily_visits": 0, "total_visits": 0
        }

# --- 헬퍼 함수 ---


def get_settings():
    defaults = {'title_text': 'YouTube 영상 분석 툴', 'logo_path': None,
                'admin_password': 'admin', 'shared_api_key': ''}
    if not os.path.exists(SETTINGS_FILE):
        return defaults
    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            settings_from_file = json.load(f)
            defaults.update(settings_from_file)
            return defaults
    except (json.JSONDecodeError, FileNotFoundError):
        return defaults


def save_settings(settings):
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=4)


def get_feedback():
    if not os.path.exists(FEEDBACK_FILE):
        return []
    try:
        with open(FEEDBACK_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def save_feedback(feedback_data):
    with open(FEEDBACK_FILE, 'w', encoding='utf-8') as f:
        json.dump(feedback_data, f, ensure_ascii=False, indent=4)


def get_youtube_api_error_message(response):
    try:
        error_details = response.json()
        error_info = error_details.get('error', {})
        errors_list = error_info.get('errors', [])
        if errors_list and isinstance(errors_list, list) and len(errors_list) > 0:
            reason = errors_list[0].get('reason')
            if reason == 'keyInvalid':
                return '잘못된 API 키입니다.'
            elif reason == 'ipAddressNotAllowed':
                return '허용되지 않은 IP 주소입니다. Google Cloud에서 IP 설정을 확인하세요.'
            elif reason == 'quotaExceeded':
                gcp_url = 'https://console.cloud.google.com/iam-admin/quotas'
                return ('유튜브에서 제공하는 API 일일 사용량(쿼터)을 초과했습니다.<br>내일 다시 시도해주세요.<br><br>사용량을 확인하고 필요 시 API를 교체하거나<br>'
                        f'<a href="{gcp_url}" target="_blank" style="color: #4F46E5; font-weight: bold;">Google Cloud Console</a>에서 쿼터를 늘려주세요.')
            elif reason == 'forbidden':
                message = error_info.get('message', '')
                if 'API not enabled' in message:
                    return '프로젝트에 YouTube Data API v3가 활성화되지 않았습니다.'
                return 'API 접근이 거부되었습니다. Google Cloud 설정을 확인해주세요.'
            else:
                return f"API 오류가 발생했습니다: {reason}"
        return error_info.get('message', f'알 수 없는 API 오류 (상태 코드: {response.status_code})')
    except (json.JSONDecodeError, AttributeError):
        return f'API 응답을 처리할 수 없습니다 (상태 코드: {response.status_code}).'


def fetch_and_process_videos(video_ids, api_key):
    if not video_ids:
        return []
    final_results = []
    for i in range(0, len(video_ids), 50):
        chunk_ids = video_ids[i:i+50]
        video_details_params = {'part': 'snippet,statistics,contentDetails', 'id': ','.join(
            chunk_ids), 'key': api_key}
        video_response = requests.get(
            f"{YOUTUBE_API_BASE_URL}videos", params=video_details_params)
        video_response.raise_for_status()
        video_data = video_response.json()
        for item in video_data.get('items', []):
            snippet, stats, content_details = item.get('snippet', {}), item.get(
                'statistics', {}), item.get('contentDetails', {})
            final_results.append({
                'title': snippet.get('title'),
                'videoUrl': f"https://www.youtube.com/watch?v={item.get('id')}",
                'thumbnail': snippet.get('thumbnails', {}).get('high', {}).get('url'), 'channel': snippet.get('channelTitle'),
                'channelId': snippet.get('channelId'), 'tags': snippet.get('tags', []),
                'viewCount': int(stats.get('viewCount', 0)), 'likeCount': int(stats.get('likeCount', 0)),
                'commentCount': int(stats.get('commentCount', 0)), 'publishedAt': snippet.get('publishedAt'),
                'duration': content_details.get('duration')
            })
    return final_results


def add_channel_stats_to_videos(videos, api_key):
    channel_ids = list(set([v['channelId']
                       for v in videos if v.get('channelId')]))
    if not channel_ids:
        return videos

    channel_stats = {}
    for i in range(0, len(channel_ids), 50):
        chunk_ids = channel_ids[i:i+50]
        channel_details_params = {'part': 'statistics',
                                  'id': ','.join(chunk_ids), 'key': api_key}
        channel_response = requests.get(
            f"{YOUTUBE_API_BASE_URL}channels", params=channel_details_params)
        if not channel_response.ok:
            continue
        channel_data = channel_response.json()
        for item in channel_data.get('items', []):
            stats = item.get('statistics', {})
            channel_stats[item['id']] = {
                'channelSubscriberCount': int(stats.get('subscriberCount', 0)) if not stats.get('hiddenSubscriberCount') else None,
                'channelTotalVideos': int(stats.get('videoCount', 0)), 'channelTotalViews': int(stats.get('viewCount', 0)),
                'channelAvgViews': int(stats.get('viewCount', 0)) // int(stats.get('videoCount', 0)) if int(stats.get('videoCount', 0)) > 0 else 0
            }
    for v in videos:
        v.update(channel_stats.get(v['channelId'], {}))
    return videos

# --- 라우트 ---


@app.route('/')
def index():
    try:
        with open(VISITOR_LOG_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    except Exception as e:
        print(f"Error writing to visitor log: {e}")

    return render_template('main_page.html', settings=get_settings())


@app.route('/get_categories')
def get_categories():
    global category_cache
    if category_cache['data'] and (time.time() - category_cache['timestamp'] < 86400):
        return jsonify(category_cache['data'])

    settings = get_settings()
    api_key = settings.get('shared_api_key')
    if not api_key:
        return jsonify({"error": "공용 API 키가 설정되지 않았습니다."}), 500

    try:
        params = {'part': 'snippet', 'regionCode': 'KR',
                  'key': api_key, 'hl': 'ko_KR'}
        response = requests.get(
            f"{YOUTUBE_API_BASE_URL}videoCategories", params=params)
        response.raise_for_status()
        data = response.json()

        assignable_categories = [cat for cat in data.get(
            'items', []) if cat.get('snippet', {}).get('assignable', False)]

        # ✨ 이 부분을 수정하여 카테고리를 추가/삭제할 수 있습니다!
        main_category_ids = {'1', '2', '10', '15',
                             '17', '20', '22', '24', '26', '28'}

        filtered_categories = [
            cat for cat in assignable_categories if cat.get('id') in main_category_ids]

        category_cache['data'] = {'categories': filtered_categories}
        category_cache['timestamp'] = time.time()

        return jsonify(category_cache['data'])
    except requests.exceptions.HTTPError as e:
        return jsonify({"error": get_youtube_api_error_message(e.response)}), e.response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/trending')
def get_trending_videos():
    global trending_cache
    category_id = request.args.get('category', '0')
    cache_key = f"trending_{category_id}"

    if trending_cache.get(cache_key) and (time.time() - trending_cache[cache_key]['timestamp'] < 3600):
        return jsonify(trending_cache[cache_key]['data'])

    settings = get_settings()
    api_key = settings.get('shared_api_key')
    if not api_key:
        return jsonify({"error": "공용 API 키가 설정되지 않았습니다."}), 500
    try:
        trending_params = {'part': 'id', 'chart': 'mostPopular',
                           'regionCode': 'KR', 'maxResults': 50, 'key': api_key}
        if category_id != '0':
            trending_params['videoCategoryId'] = category_id

        response = requests.get(
            f"{YOUTUBE_API_BASE_URL}videos", params=trending_params)
        response.raise_for_status()

        video_ids = [item['id'] for item in response.json().get('items', [])]
        videos_with_details = fetch_and_process_videos(video_ids, api_key)
        videos_with_full_details = add_channel_stats_to_videos(
            videos_with_details, api_key)

        final_response = {'videos': videos_with_full_details}
        trending_cache[cache_key] = {
            'data': final_response, 'timestamp': time.time()}

        return jsonify(final_response)
    except requests.exceptions.HTTPError as e:
        return jsonify({"error": get_youtube_api_error_message(e.response)}), e.response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/search')
def search_videos():
    query = request.args.get('q')
    api_key = request.args.get('apiKey')
    if not query or not api_key:
        return jsonify({"error": "검색어와 API 키가 필요합니다."}), 400

    try:
        today = datetime.now().strftime('%Y-%m-%d')
        if today not in search_term_counter_by_date:
            search_term_counter_by_date[today] = collections.Counter()
        search_term_counter_by_date[today][query] += 1
        search_log.appendleft(
            {'timestamp': datetime.now().strftime('%H:%M:%S'), 'term': query})
    except Exception as e:
        print(f"Error logging search term: {e}")

    try:
        video_ids = []
        next_page_token = None
        for _ in range(2):
            search_params = {'part': 'snippet', 'q': query,
                             'key': api_key, 'type': 'video', 'maxResults': 50}
            if next_page_token:
                search_params['pageToken'] = next_page_token

            search_response = requests.get(
                f"{YOUTUBE_API_BASE_URL}search", params=search_params)
            search_response.raise_for_status()
            search_data = search_response.json()
            video_ids.extend([item['id']['videoId']
                             for item in search_data.get('items', [])])
            next_page_token = search_data.get('nextPageToken')
            if not next_page_token:
                break

        if not video_ids:
            return jsonify({'videos': [], 'recommended_tags': []})

        videos_with_details = fetch_and_process_videos(video_ids, api_key)
        videos_with_full_details = add_channel_stats_to_videos(
            videos_with_details, api_key)

        all_tags = [tag.lower()
                    for v in videos_with_full_details for tag in v.get('tags', [])]
        tag_counts = collections.Counter(all_tags)
        for term in query.lower().split():
            tag_counts.pop(term, None)
        recommended_tags = [tag for tag, count in tag_counts.most_common(10)]

        final_response = {'videos': videos_with_full_details,
                          'recommended_tags': recommended_tags}
        return jsonify(final_response)
    except requests.exceptions.HTTPError as e:
        return jsonify({"error": get_youtube_api_error_message(e.response)}), e.response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route(f'{SECRET_ADMIN_PREFIX}/login', methods=['GET', 'POST'])
def login():
    if session.get('logged_in'):
        return redirect(url_for('admin_page'))
    if request.method == 'POST':
        settings = get_settings()
        if request.form.get('password') == settings.get('admin_password'):
            session['logged_in'] = True
            return redirect(url_for('admin_page'))
        else:
            flash('비밀번호가 틀렸습니다.', 'error')
    return render_template('login.html')


@app.route(f'{SECRET_ADMIN_PREFIX}/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))


@app.route('/validate_key', methods=['POST'])
def validate_key():
    data = request.get_json()
    api_key = data.get('apiKey')
    if not api_key:
        return jsonify({'success': False, 'error': 'API 키가 제공되지 않았습니다.'}), 400

    test_params = {'part': 'id', 'id': 'dQw4w9WgXcQ', 'key': api_key}
    try:
        response = requests.get(
            f"{YOUTUBE_API_BASE_URL}videos", params=test_params)
        if response.status_code == 200:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': get_youtube_api_error_message(response)}), 400
    except requests.exceptions.RequestException as e:
        return jsonify({'success': False, 'error': f'네트워크 오류: {e}'}), 500


@app.route(SECRET_ADMIN_PREFIX, methods=['GET', 'POST'])
def admin_page():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        settings = get_settings()
        settings['title_text'] = request.form.get(
            'title_text', 'YouTube 영상 분석 툴')
        if request.form.get('admin_password'):
            settings['admin_password'] = request.form.get('admin_password')
        settings['shared_api_key'] = request.form.get('shared_api_key', '')
        if 'reset_logo' in request.form:
            settings['logo_path'] = None
        else:
            file = request.files.get('logo_image')
            if file and file.filename != '':
                if not os.path.exists(app.config['UPLOAD_FOLDER']):
                    os.makedirs(app.config['UPLOAD_FOLDER'])
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                settings['logo_path'] = os.path.join(
                    'uploads', filename).replace('\\', '/')
        save_settings(settings)
        flash('설정이 성공적으로 저장되었습니다!', 'success')
        return redirect(url_for('admin_page'))

    settings = get_settings()
    visitor_stats = process_visitor_stats()

    sorted_dates = sorted(search_term_counter_by_date.keys(), reverse=True)
    selected_date = request.args.get(
        'date', sorted_dates[0] if sorted_dates else None)
    popular_searches_for_date = []
    if selected_date and selected_date in search_term_counter_by_date:
        popular_searches_for_date = search_term_counter_by_date[selected_date].most_common(
            10)

    stats_data = {
        'search_log': list(search_log),
        'available_dates': sorted_dates,
        'selected_date': selected_date,
        'popular_searches': popular_searches_for_date,
        'visitor_stats': visitor_stats
    }

    received_feedback = sorted(
        get_feedback(), key=lambda x: x['timestamp'], reverse=True)

    return render_template('admin.html', settings=settings, stats=stats_data, received_feedback=received_feedback, visitor_stats_json=json.dumps(visitor_stats))


@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    message = request.form.get('message')
    if not message:
        return jsonify({'success': False, 'error': '메시지를 입력해주세요.'}), 400

    all_feedback = get_feedback()
    new_feedback = {'message': message,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    all_feedback.insert(0, new_feedback)
    save_feedback(all_feedback)

    return jsonify({'success': True, 'message': '소중한 피드백 감사합니다!'})


@app.route(f'{SECRET_ADMIN_PREFIX}/delete_feedback', methods=['POST'])
def delete_feedback():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    ids_to_delete = request.form.getlist('feedback_ids')
    if not ids_to_delete:
        flash('삭제할 피드백을 선택해주세요.', 'error')
        return redirect(url_for('admin_page'))

    all_feedback = get_feedback()
    feedback_to_keep = [
        fb for fb in all_feedback if fb['timestamp'] not in ids_to_delete]
    save_feedback(feedback_to_keep)

    flash(f'{len(ids_to_delete)}개의 피드백을 삭제했습니다.', 'success')
    return redirect(url_for('admin_page'))


if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    extra_files = ['settings.json']
    app.run(debug=True, port=5001, extra_files=extra_files)
