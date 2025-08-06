import os
from cryptography.fernet import Fernet
from extensions import db
from flask import current_app
from sqlalchemy import UniqueConstraint, ForeignKeyConstraint


class KeyEncryptor:
    _fernet = None

    @classmethod
    def get_fernet(cls):
        if cls._fernet is None:
            encryption_key = current_app.config.get('ENCRYPTION_KEY')
            if not encryption_key:
                raise ValueError(
                    "ENCRYPTION_KEY is not set in the configuration.")

            # [수정] 환경 변수에서 읽은 문자열 키를 바이트로 인코딩합니다.
            cls._fernet = Fernet(encryption_key.encode('utf-8'))
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
        return cls.get_fernet().decrypt(encrypted_data.encode('utf-8')).decode('utf-8')

# 이하 ApiKey 클래스는 수정할 필요 없이 그대로 둡니다.


class ApiKey(db.Model):
    __tablename__ = 'api_keys'

    id = db.Column(db.Integer, primary_key=True)
    _encrypted_key = db.Column('encrypted_key', db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    last_used = db.Column(db.DateTime, nullable=True)
    quota_exceeded_at = db.Column(db.DateTime, nullable=True)

    user_id = db.Column(db.Integer, nullable=False)
    user = db.relationship('User', back_populates='api_keys')

    __table_args__ = (
        UniqueConstraint('encrypted_key', name='uq_api_keys_encrypted_key'),
        ForeignKeyConstraint(['user_id'], ['users.id'],
                             name='fk_api_keys_user_id_users', ondelete='CASCADE'),
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
        db.session.commit()

    @staticmethod
    def get_active_key_for_user(user_id):
        return ApiKey.query.filter_by(user_id=user_id, is_active=True).order_by(ApiKey.last_used.asc()).first()

    @staticmethod
    def is_key_duplicate(user_id, new_key):
        """사용자의 API 키 중에 동일한 키가 있는지 확인합니다."""
        from cryptography.fernet import Fernet
        from flask import current_app
        
        # 새 키를 암호화
        try:
            encrypted_new_key = KeyEncryptor.encrypt(new_key)
        except:
            return False
        
        # 동일한 암호화된 키가 있는지 확인
        existing_key = ApiKey.query.filter_by(
            user_id=user_id, 
            _encrypted_key=encrypted_new_key
        ).first()
        
        return existing_key is not None
