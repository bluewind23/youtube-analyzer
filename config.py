# 복사 버튼을 눌러 전체 코드를 복사하세요
import os
import json
from dotenv import load_dotenv

load_dotenv()
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'a_default_secret_key')
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@example.com')

    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    GOOGLE_OAUTH_CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
    GOOGLE_OAUTH_CLIENT_SECRET = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")

    # [수정 또는 추가할 코드 시작]
    # 서버의 공식 도메인 이름을 환경 변수에서 가져오도록 설정합니다.
    SERVER_NAME = os.getenv('SERVER_NAME', None)
    # [수정 또는 추가할 코드 끝]

    SESSION_COOKIE_DOMAIN = os.getenv('SESSION_COOKIE_DOMAIN', None)
    SESSION_COOKIE_SAMESITE = 'None'
    SESSION_COOKIE_SECURE = True
