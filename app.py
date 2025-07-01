from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
import requests
import time
import collections
import os
import json
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'supersecretkey_for_session'

# ✨ 비밀 경로 설정 ✨
SECRET_ADMIN_PREFIX = '/manage-youtube-tool-78s1-z90p'

# --- 설정 ---
UPLOAD_FOLDER = 'static/uploads'
SETTINGS_FILE = 'settings.json'
FEEDBACK_FILE = 'feedback.json'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 캐시 및 통계 설정을 위한 변수
search_cache = {}
CACHE_DURATION = 300
total_api_calls = 0
search_term_counter_by_date = {}
search_log = collections.deque(maxlen=20)
YOUTUBE_API_BASE_URL = "https://www.googleapis.com/youtube/v3/"

# --- 헬퍼 함수 ---
def get_settings():
    defaults = {
        'title_text': 'YouTube 영상 분석 툴',
        'logo_path': None,
        'admin_password': 'admin'
    }
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
        errors_list = error_details.get('error', {}).get('errors', [])
        if errors_list and isinstance(errors_list, list) and len(errors_list) > 0:
            reason = errors_list[0].get('reason')
            if reason == 'keyInvalid':
                return '잘못된 API 키입니다.'
            elif reason == 'ipAddressNotAllowed':
                return '허용되지 않은 IP 주소입니다. Google Cloud에서 IP 설정을 확인하세요.'
            elif reason == 'quotaExceeded':
                gcp_url = 'https://console.cloud.google.com/iam-admin/quotas'
                return (
                    '유튜브에서 제공하는 API 일일 사용량(쿼터)을 초과했습니다.<br>'
                    '내일 다시 시도해주세요.<br><br>'
                    '사용량을 확인하고 필요 시 API를 교체하거나<br>'
                    f'<a href="{gcp_url}" target="_blank" style="color: #4F46E5; font-weight: bold;">Google Cloud Console</a>에서 쿼터를 늘려주세요.'
                )
            elif reason == 'forbidden':
                message = error_details.get('error', {}).get('message', '')
                if 'API not enabled' in message:
                    return '프로젝트에 YouTube Data API v3가 활성화되지 않았습니다.'
                return 'API 접근이 거부되었습니다. Google Cloud 설정을 확인해주세요.'
            else:
                return f"API 오류가 발생했습니다: {reason}"
        return error_details.get('error', {}).get('message', f'알 수 없는 API 오류 (상태 코드: {response.status_code})')
    except (json.JSONDecodeError, AttributeError):
        return f'API 응답을 처리할 수 없습니다 (상태 코드: {response.status_code}).'

@app.route('/')
def index():
    settings = get_settings()
    return render_template('main_page.html', settings=settings)

# --- 관리자 로그인/로그아웃 라우트 (비밀 주소 적용) ---
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

# --- 기존 라우트 ---
@app.route('/validate_key', methods=['POST'])
def validate_key():
    data = request.get_json()
    api_key = data.get('apiKey')
    if not api_key:
        return jsonify({'success': False, 'error': 'API 키가 제공되지 않았습니다.'}), 400
    test_params = {'part': 'id', 'id': 'dQw4w9WgXcQ', 'key': api_key}
    try:
        response = requests.get(f"{YOUTUBE_API_BASE_URL}videos", params=test_params)
        if response.status_code == 200:
            return jsonify({'success': True})
        else:
            error_message = get_youtube_api_error_message(response)
            return jsonify({'success': False, 'error': error_message}), 400
    except requests.exceptions.RequestException as e:
        return jsonify({'success': False, 'error': f'네트워크 오류: {e}'}), 500

@app.route('/search')
def search_videos():
    global total_api_calls
    query = request.args.get('q')
    api_key = request.args.get('apiKey')
    if not query or not api_key:
        return jsonify({"error": "검색어와 API 키가 필요합니다."}), 400
    cache_key = query.lower().strip()
    current_time = time.time()
    if cache_key in search_cache and current_time - search_cache[cache_key]['timestamp'] < CACHE_DURATION:
        return jsonify(search_cache[cache_key]['data'])
    try:
        total_api_calls += 1
        search_params = {'part': 'snippet', 'q': query, 'key': api_key, 'type': 'video', 'maxResults': 50}
        search_response = requests.get(f"{YOUTUBE_API_BASE_URL}search", params=search_params)
        search_response.raise_for_status()
        search_data = search_response.json()
        video_ids = [item['id']['videoId'] for item in search_data.get('items', [])]
        if not video_ids: return jsonify({'videos': [], 'recommended_tags': []})
        total_api_calls += 1
        video_details_params = {'part': 'snippet,statistics,contentDetails', 'id': ','.join(video_ids), 'key': api_key}
        video_response = requests.get(f"{YOUTUBE_API_BASE_URL}videos", params=video_details_params)
        video_response.raise_for_status()
        video_data = video_response.json()
        channel_ids = list(set([item['snippet']['channelId'] for item in video_data.get('items', []) if 'channelId' in item.get('snippet', {})]))
        channel_stats = {}
        if channel_ids:
            total_api_calls += 1
            channel_details_params = {'part': 'statistics', 'id': ','.join(channel_ids), 'key': api_key}
            channel_response = requests.get(f"{YOUTUBE_API_BASE_URL}channels", params=channel_details_params)
            channel_response.raise_for_status()
            channel_data = channel_response.json()
            for item in channel_data.get('items', []):
                stats = item.get('statistics', {})
                total_videos = int(stats.get('videoCount', 0))
                total_views = int(stats.get('viewCount', 0))
                avg_views = total_views // total_videos if total_videos > 0 else 0
                channel_stats[item['id']] = {'subscriberCount': int(stats.get('subscriberCount', 0)) if not stats.get('hiddenSubscriberCount') else None, 'totalVideoCount': total_videos, 'totalViewCount': total_views, 'avgViewsPerVideo': avg_views}
        results, all_tags = [], []
        for item in video_data.get('items', []):
            snippet, stats, content_details = item.get('snippet', {}), item.get('statistics', {}), item.get('contentDetails', {})
            channel_id = snippet.get('channelId')
            ch_stats = channel_stats.get(channel_id, {})
            video_tags = snippet.get('tags', [])
            if video_tags: all_tags.extend(video_tags)
            results.append({
                'title': snippet.get('title'),
                'videoUrl': f"https://www.youtube.com/watch?v={item.get('id')}",
                'thumbnail': snippet.get('thumbnails', {}).get('high', {}).get('url'),
                'channel': snippet.get('channelTitle'),
                'channelId': channel_id,
                'channelSubscriberCount': ch_stats.get('subscriberCount'),
                'channelTotalVideos': ch_stats.get('totalVideoCount'),
                'channelTotalViews': ch_stats.get('totalViewCount'),
                'channelAvgViews': ch_stats.get('avgViewsPerVideo'),
                'tags': video_tags,
                'viewCount': int(stats.get('viewCount', 0)),
                'likeCount': int(stats.get('likeCount', 0)),
                'commentCount': int(stats.get('commentCount', 0)),
                'publishedAt': snippet.get('publishedAt'),
                'duration': content_details.get('duration')
            })
        tag_counts = collections.Counter(all_tags)
        for term in query.lower().split(): tag_counts.pop(term, None)
        recommended_tags = [tag for tag, count in tag_counts.most_common(10)]
        final_response = {'videos': results, 'recommended_tags': recommended_tags}
        today_str = datetime.now().strftime('%Y-%m-%d')
        if today_str not in search_term_counter_by_date: search_term_counter_by_date[today_str] = collections.Counter()
        search_term_counter_by_date[today_str].update([cache_key])
        search_log.appendleft({'term': cache_key, 'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')})
        search_cache[cache_key] = {'data': final_response, 'timestamp': time.time()}
        return jsonify(final_response)
    except requests.exceptions.HTTPError as e:
        error_message = get_youtube_api_error_message(e.response)
        return jsonify({"error": error_message}), e.response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    message = request.form.get('message')
    if not message: return jsonify({'success': False, 'error': '메시지를 입력해주세요.'}), 400
    all_feedback = get_feedback()
    new_feedback = {'message': message, 'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
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
    feedback_to_keep = [fb for fb in all_feedback if fb['timestamp'] not in ids_to_delete]
    save_feedback(feedback_to_keep)
    flash(f'{len(ids_to_delete)}개의 피드백을 삭제했습니다.', 'success')
    return redirect(url_for('admin_page'))

@app.route(SECRET_ADMIN_PREFIX, methods=['GET', 'POST'])
def admin_page():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        settings = get_settings()
        settings['title_text'] = request.form.get('title_text', 'YouTube 영상 분석 툴')
        new_password = request.form.get('admin_password')
        if new_password:
            settings['admin_password'] = new_password
            flash('비밀번호가 변경되었습니다.', 'success')
        if 'reset_logo' in request.form:
            settings['logo_path'] = None
        else:
            file = request.files.get('logo_image')
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                settings['logo_path'] = os.path.join('uploads', filename).replace('\\', '/')
        save_settings(settings)
        if not new_password: flash('설정이 성공적으로 저장되었습니다!', 'success')
        return redirect(url_for('admin_page'))
    settings = get_settings()
    sorted_dates = sorted(search_term_counter_by_date.keys(), reverse=True)
    selected_date = request.args.get('date', sorted_dates[0] if sorted_dates else None)
    popular_searches_for_date = []
    if selected_date and selected_date in search_term_counter_by_date:
        popular_searches_for_date = search_term_counter_by_date[selected_date].most_common(10)
    stats_data = {
        'total_api_calls': total_api_calls,
        'search_log': list(search_log),
        'available_dates': sorted_dates,
        'selected_date': selected_date,
        'popular_searches': popular_searches_for_date
    }
    received_feedback = get_feedback()
    return render_template('admin.html', settings=settings, stats=stats_data, received_feedback=received_feedback)

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER): os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True, port=5000)