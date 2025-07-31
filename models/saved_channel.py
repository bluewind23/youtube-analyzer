from extensions import db
from datetime import datetime


class SavedChannelCategory(db.Model):
    """저장된 채널 카테고리 모델"""
    __tablename__ = 'saved_channel_categories'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(
        db.DateTime, default=datetime.utcnow, nullable=False)

    # 관계 설정
    user = db.relationship('User', backref='channel_categories')
    saved_items = db.relationship('SavedItem',
                                  back_populates='category',
                                  cascade='all, delete-orphan')

    def __repr__(self):
        return f'<SavedChannelCategory {self.name}>'

    def to_dict(self):
        # 해당 카테고리의 채널 수 계산
        from models.saved_item import SavedItem
        channel_count = SavedItem.query.filter_by(
            user_id=self.user_id,
            item_type='channel',
            category_id=self.id
        ).count()

        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'channel_count': channel_count,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
