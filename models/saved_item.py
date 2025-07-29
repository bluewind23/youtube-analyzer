from extensions import db
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
import datetime


class SavedItem(db.Model):
    __tablename__ = 'saved_items'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey(
        'users.id', ondelete='CASCADE'), nullable=False)
    # 'query' 또는 'channel'
    item_type = db.Column(db.String(50), nullable=False)
    item_value = db.Column(db.String(500), nullable=False)  # 검색어 또는 채널 ID
    item_display_name = db.Column(
        db.String(500), nullable=True)  # 채널명 등 표시될 이름
    category_id = db.Column(db.Integer, nullable=True)  # 카테고리 ID (채널용)
    saved_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    user = relationship('User', back_populates='saved_items')

    __table_args__ = (
        UniqueConstraint('user_id', 'item_type',
                         'item_value', name='_user_item_uc'),
    )
