from extensions import db
from models.api_key import KeyEncryptor
from sqlalchemy import UniqueConstraint


class AdminApiKey(db.Model):
    __tablename__ = 'admin_api_keys'

    id = db.Column(db.Integer, primary_key=True)
    # 실제 DB 컬럼 이름은 'encrypted_key' 입니다.
    _encrypted_key = db.Column('encrypted_key', db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    last_used = db.Column(db.DateTime, nullable=True)
    quota_exceeded_at = db.Column(db.DateTime, nullable=True)

    __table_args__ = (
        # [수정] 파이썬 변수명 '_encrypted_key' -> 실제 DB 컬럼명 'encrypted_key'
        UniqueConstraint(
            'encrypted_key', name='uq_admin_api_keys_encrypted_key'),
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
    def get_active_fallback_key():
        return AdminApiKey.query.filter_by(is_active=True).order_by(AdminApiKey.last_used.asc()).first()
