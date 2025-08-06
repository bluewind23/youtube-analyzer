# app.py

# 1. 모든 import를 파일 최상단으로 이동 (자동 정렬 플러그인과 충돌하지 않음)
import os
from flask import Flask, render_template, session, send_from_directory
from flask_migrate import Migrate
from jinja2.runtime import Undefined
from werkzeug.middleware.proxy_fix import ProxyFix
from dotenv import load_dotenv

from config import Config
from extensions import db, cache
from models.user import User
from flask_login import LoginManager

# 2. 앱 생성 및 설정을 함수 안에 캡슐화


def create_app():
    # 3. 함수가 시작될 때 .env 파일을 가장 먼저 로드
    load_dotenv()

    app = Flask(__name__)

    # ProxyFix 적용
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1,
                            x_proto=1, x_host=1, x_prefix=1)

    # 설정 로드
    app.config.from_object(Config)

    # 확장 기능 초기화
    cache.init_app(app)
    db.init_app(app)
    Migrate(app, db, render_as_batch=True)

    # 로그인 매니저 설정
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth_routes.login'
    login_manager.login_message = '이 페이지에 접근하려면 로그인이 필요합니다.'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # 4. 블루프린트는 함수 안에서 임포트하고 등록
    with app.app_context():
        from routes.main_routes import main_routes
        from routes.auth_routes import auth_routes, google_bp
        from routes.channel_routes import channel_routes
        from routes.admin_routes import admin_routes
        from routes.user_actions_routes import user_actions_routes

        app.register_blueprint(main_routes)
        app.register_blueprint(auth_routes)
        app.register_blueprint(google_bp, url_prefix="/login")
        app.register_blueprint(channel_routes)
        app.register_blueprint(admin_routes)
        app.register_blueprint(user_actions_routes)

    @app.route('/ads.txt')
    def ads_txt():
        # 또는 os.path.abspath('.') 방식
        return send_from_directory('static', 'ads.txt')

    # Jinja 필터 등록

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

    # 에러 핸들러 등록
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

    return app


# 5. 로컬에서 직접 실행할 때 사용할 부분
if __name__ == '__main__':
    app = create_app()
    # Google OAuth를 위해 localhost 사용 (private IP 주소는 허용되지 않음)
    app.run(host='127.0.0.1', port=8000, debug=True)
