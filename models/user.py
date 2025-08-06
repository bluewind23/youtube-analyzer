from extensions import db
from flask_login import UserMixin
import datetime
from sqlalchemy import UniqueConstraint
from models.search_history import SearchHistory
from models.saved_item import SavedItem


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    google_id = db.Column(db.String(120), nullable=True)
    profile_pic = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)

    api_keys = db.relationship(
        'ApiKey', back_populates='user', lazy=True, cascade="all, delete-orphan")

    search_history = db.relationship(
        'SearchHistory', back_populates='user', lazy='dynamic', cascade="all, delete-orphan")

    saved_items = db.relationship(
        'SavedItem', back_populates='user', lazy=True, cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('username', name='uq_users_username'),
        UniqueConstraint('google_id', name='uq_users_google_id'),
    )

    def has_active_api_keys(self):
        """사용자가 활성화된 API 키를 가지고 있는지 확인합니다."""
        # SQLAlchemy relationship을 활용하여 순환 import 문제 해결
        return any(key.is_active for key in self.api_keys)

    def __repr__(self):
        return f'<User {self.username or self.email}>'
