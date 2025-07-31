# 복사 버튼을 눌러 전체 코드를 복사하세요
import os

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

    SERVER_NAME = os.getenv('SERVER_NAME', None)

    # [수정 또는 추가할 코드 시작]
    # Redis 캐시 설정
    REDIS_URL = os.getenv('REDIS_URL')
    if REDIS_URL:
        CACHE_TYPE = 'redis'
        CACHE_REDIS_URL = REDIS_URL
        CACHE_DEFAULT_TIMEOUT = 3600  # 기본 캐시 시간 1시간
    else:
        # Redis가 없을 경우 메모리 캐시 사용
        CACHE_TYPE = 'simple'
        CACHE_DEFAULT_TIMEOUT = 300
    # [수정 또는 추가할 코드 끝]

    # [이 줄을 삭제하세요]
    # SESSION_COOKIE_DOMAIN = os.getenv('SESSION_COOKIE_DOMAIN', None)

    # 개발 환경에서는 HTTP를 사용하므로 SECURE를 False로 설정
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = False
