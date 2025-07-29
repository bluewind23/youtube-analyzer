from extensions import db
from datetime import datetime

class SavedVideoCategory(db.Model):
    """저장된 영상 카테고리 모델"""
    __tablename__ = 'saved_video_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # 관계 설정
    user = db.relationship('User', backref='video_categories')
    videos = db.relationship('SavedVideo', backref='category', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<SavedVideoCategory {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'video_count': len(self.videos),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class SavedVideo(db.Model):
    """저장된 영상 모델"""
    __tablename__ = 'saved_videos'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('saved_video_categories.id'), nullable=True)
    
    # YouTube 영상 정보
    video_id = db.Column(db.String(20), nullable=False)  # YouTube video ID
    title = db.Column(db.String(500), nullable=False)
    channel_id = db.Column(db.String(50), nullable=False)
    channel_title = db.Column(db.String(200), nullable=False)
    thumbnail_url = db.Column(db.String(500))
    description = db.Column(db.Text)
    published_at = db.Column(db.DateTime)
    duration = db.Column(db.String(20))
    
    # 저장 시점 통계
    view_count = db.Column(db.BigInteger, default=0)
    like_count = db.Column(db.Integer, default=0)
    comment_count = db.Column(db.Integer, default=0)
    
    # 메타데이터
    saved_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    notes = db.Column(db.Text)  # 사용자 메모
    
    # 관계 설정
    user = db.relationship('User', backref='saved_videos')
    
    # 중복 방지를 위한 유니크 제약
    __table_args__ = (
        db.UniqueConstraint('user_id', 'video_id', name='unique_user_video'),
    )
    
    def __repr__(self):
        return f'<SavedVideo {self.title[:50]}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'video_id': self.video_id,
            'title': self.title,
            'channel_id': self.channel_id,
            'channel_title': self.channel_title,
            'thumbnail_url': self.thumbnail_url,
            'description': self.description,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'duration': self.duration,
            'view_count': self.view_count,
            'like_count': self.like_count,
            'comment_count': self.comment_count,
            'saved_at': self.saved_at.isoformat() if self.saved_at else None,
            'notes': self.notes,
            'category': self.category.to_dict() if self.category else None
        }