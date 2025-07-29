from flask import Flask, render_template, redirect, request, session
from flask_migrate import Migrate
from config import Config
from extensions import db
from models.user import User
from flask_login import LoginManager
from jinja2.runtime import Undefined
from extensions import cache

# ✅ Google OAuth 관련 모듈
import os
import pathlib
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport import requests

# ✅ 기타 초기화
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "your-secret-key")
app.jinja_env.filters['human_format'] = lambda num: "" if num is None or isinstance(num, Undefined) else \
    ('{:.1f}{}'.format(float('{:.3g}'.format(num / 10_000 ** (magnitude := sum(abs(num) >= 10_000 ** i for i in range(1, 4)))), ['', '만', '억', '조'][magnitude]).replace('.0', '') if float('{:.3g}'.format(num)) % 1 != 0 else '{}{}'.format(int(num / 10_000 ** magnitude), ['', '만', '억', '조'][magnitude]))
app.jinja_env.add_extension('jinja2.ext.do')

app.config.from_object(Config)
app.config['CACHE_TYPE']='SimpleCache'
app.config['CACHE_DEFAULT_TIMEOUT']=300
cache.init_app(app)
db.init_app(app)
migrate=Migrate(app, db, render_as_batch=True)

login_manager=LoginManager()
login_manager.init_app(app)

@ login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ✅ Google OAuth Flow 설정
os.environ["OAUTHLIB_INSECURE_TRANSPORT"]="1"  # 개발환경 허용 (Render는 https라 안전)

GOOGLE_CLIENT_ID=os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET=os.environ.get("GOOGLE_CLIENT_SECRET")
REDIRECT_URI="https://youtube-analyzer-vmkj.onrender.com/oauth2callback"

flow=Flow.from_client_config(
    {
        "web": {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token"
        }
    },
    scopes=[
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
        "openid"
    ],
    redirect_uri=REDIRECT_URI
)

# ✅ 블루프린트 등록
from routes.main_routes import main_routes
from routes.auth_routes import auth_routes
from routes.channel_routes import channel_routes
from routes.admin_routes import admin_routes
from routes.user_actions_routes import user_actions_routes

app.register_blueprint(main_routes)
app.register_blueprint(auth_routes)
app.register_blueprint(channel_routes)
app.register_blueprint(admin_routes)
app.register_blueprint(user_actions_routes)

# ✅ Google 로그인 라우트 직접 구현
@ app.route("/login")
def login():
    authorization_url, state=flow.authorization_url()
    session["state"]=state
    return redirect(authorization_url)

@ app.route("/oauth2callback")
def oauth2callback():
    flow.fetch_token(authorization_response=request.url)

    if session.get("state") != request.args.get("state"):
        return "State mismatch!", 400

    credentials=flow.credentials
    request_session=requests.Request()
    id_info=id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=request_session,
        audience=GOOGLE_CLIENT_ID
    )

    user_email=id_info.get("email")
    return f"✅ 로그인 성공! 안녕하세요, {user_email} 님!"

# ✅ 에러 핸들러
@ app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@ app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500

@ app.errorhandler(503)
def service_unavailable(error):
    return render_template('errors/503.html'), 503

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=False)
