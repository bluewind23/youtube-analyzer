import os
from cryptography.fernet import Fernet
from extensions import db
from flask import current_app
from sqlalchemy import UniqueConstraint


class KeyEncryptor:
    _fernet = None

    @classmethod
    def get_fernet(cls):
        if cls._fernet is None:
            encryption_key = current_app.config.get('ENCRYPTION_KEY')
            if not encryption_key:
                raise ValueError(
                    "ENCRYPTION_KEY is not set in the configuration.")

            try:
                # [수정] 문자열 키를 바이트로 인코딩하여 Fernet을 초기화합니다.
                cls._fernet = Fernet(encryption_key.encode('utf-8'))
            except Exception as e:
                current_app.logger.error(f"Failed to initialize Fernet: {e}")
                raise ValueError(f"Invalid ENCRYPTION_KEY format: {e}")
        return cls._fernet

    @classmethod
    def encrypt(cls, data):
        if not data:
            return None
        return cls.get_fernet().encrypt(data.encode('utf-8')).decode('utf-8')

    @classmethod
    def decrypt(cls, encrypted_data):
        if not encrypted_data:
            return None
        try:
            return cls.get_fernet().decrypt(encrypted_data.encode('utf-8')).decode('utf-8')
        except Exception as e:
            current_app.logger.error(f"Failed to decrypt API key: {e}")
            return None


class ApiKey(db.Model):
    __tablename__ = 'api_keys'

    id = db.Column(db.Integer, primary_key=True)
    _encrypted_key = db.Column('encrypted_key', db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    last_used = db.Column(db.DateTime, nullable=True)
    quota_exceeded_at = db.Column(db.DateTime, nullable=True)

    user_id = db.Column(db.Integer, db.ForeignKey(
        'users.id', ondelete='CASCADE'), nullable=False)
    user = db.relationship('User', back_populates='api_keys')

    __table_args__ = (
        UniqueConstraint('encrypted_key', name='uq_api_keys_encrypted_key'),
    )

    @property
    def key(self):
        return KeyEncryptor.decrypt(self._encrypted_key)

    @key.setter
    def key(self, value):
        self._encrypted_key = KeyEncryptor.encrypt(value)

    def deactivate(self):
        from datetime import datetime
        self.is_active = False
        self.quota_exceeded_at = datetime.utcnow()
        # [수정] 직접 commit하는 대신 세션에 변경사항만 추가하여 안정성을 높입니다.
        db.session.add(self)

    @staticmethod
    def get_active_key_for_user(user_id):
        return ApiKey.query.filter_by(user_id=user_id, is_active=True).order_by(ApiKey.last_used.asc()).first()
