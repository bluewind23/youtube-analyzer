from extensions import db
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
import datetime


class SearchHistory(db.Model):
    __tablename__ = 'search_history'

    # [수정] 모든 속성이 클래스 내부에 있도록 들여쓰기를 수정합니다.
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey(
        'users.id', ondelete='CASCADE'), nullable=False)
    search_term = db.Column(db.String(500), nullable=False)
    searched_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    user = relationship('User', back_populates='search_history')
