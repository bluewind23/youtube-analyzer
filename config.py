import os
import json
from dotenv import load_dotenv

load_dotenv()
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'a_default_secret_key')

    # [추가] 암호화 키 로드
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')

    # [추가] 관리자 이메일 설정
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@example.com')

    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    GOOGLE_OAUTH_CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
    GOOGLE_OAUTH_CLIENT_SECRET = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")

    # 커스텀 도메인 환경에서 세션 쿠키가 올바르게 작동하도록 설정합니다.
    SESSION_COOKIE_DOMAIN = os.getenv('SESSION_COOKIE_DOMAIN', None)
    SESSION_COOKIE_SECURE = True
