# 복사 버튼을 눌러 전체 코드를 복사하세요
from routes.user_actions_routes import user_actions_routes
from routes.admin_routes import admin_routes
from routes.channel_routes import channel_routes
from routes.auth_routes import auth_routes, google_bp
from routes.main_routes import main_routes

from flask import Flask, render_template, redirect, request, session
from flask_migrate import Migrate
from config import Config
from extensions import db, cache
from models.user import User
from flask_login import LoginManager
from jinja2.runtime import Undefined
import os
# [수정 또는 추가할 코드 시작]
# ProxyFix 임포트
from werkzeug.middleware.proxy_fix import ProxyFix
# [수정 또는 추가할 코드 끝]

app = Flask(__name__)

# [수정 또는 추가할 코드 시작]
# WSGI 미들웨어에 ProxyFix 적용. 반드시 app = Flask(__name__) 바로 다음에 위치해야 합니다.
# 이 코드는 서버가 프록시(예: Render) 뒤에 있을 때 올바른 URL(https, 도메인 등)을 인식하게 해줍니다.
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
# [수정 또는 추가할 코드 끝]

app.secret_key = os.environ.get("FLASK_SECRET_KEY", "your-secret-key")

# 숫자를 사람이 읽기 쉬운 형태로 변환하는 필터


def human_format(num):
    if num is None or isinstance(num, Undefined):
        return ""
    num = float('{:.3g}'.format(num))
    magnitude = 0
    while abs(num) >= 10000 and magnitude < 3:
        magnitude += 1
        num /= 10000.0
    unit = ['', '만', '억', '조'][magnitude]
    if num % 1 == 0:
        return '{}{}'.format(int(num), unit)
    return '{:.1f}{}'.format(num, unit).replace('.0', '')


app.jinja_env.filters['human_format'] = human_format
app.jinja_env.add_extension('jinja2.ext.do')

# Config 적용 및 캐시 설정
app.config.from_object(Config)
app.config['CACHE_TYPE'] = 'SimpleCache'
app.config['CACHE_DEFAULT_TIMEOUT'] = 300

# 확장 기능 초기화
cache.init_app(app)
db.init_app(app)
migrate = Migrate(app, db, render_as_batch=True)

# 로그인 매니저 설정
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# 블루프린트 등록
app.register_blueprint(main_routes)
app.register_blueprint(auth_routes)
app.register_blueprint(google_bp, url_prefix="/login")
app.register_blueprint(channel_routes)
app.register_blueprint(admin_routes)
app.register_blueprint(user_actions_routes)

# 에러 핸들러


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500


@app.errorhandler(503)
def service_unavailable(error):
    return render_template('errors/503.html'), 503


# 앱 실행
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=False)
