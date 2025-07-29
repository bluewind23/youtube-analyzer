from datetime import datetime
from extensions import db


class ChannelStats(db.Model):
    __tablename__ = 'channel_stats'

    id = db.Column(db.Integer, primary_key=True)
    channel_id = db.Column(db.String(255), nullable=False, index=True)
    channel_title = db.Column(db.String(500), nullable=False)
    custom_url = db.Column(db.String(255))
    thumbnail_url = db.Column(db.Text)
    
    # Statistics
    subscriber_count = db.Column(db.BigInteger, default=0)
    video_count = db.Column(db.Integer, default=0)
    total_view_count = db.Column(db.BigInteger, default=0)
    
    # Derived metrics
    avg_views_per_video = db.Column(db.Float, default=0.0)
    
    # Tracking
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Indexes for efficient queries
    __table_args__ = (
        db.Index('idx_channel_recorded', 'channel_id', 'recorded_at'),
    )

    @classmethod
    def get_latest_stats(cls, channel_id):
        """Get the most recent stats for a channel"""
        return cls.query.filter_by(channel_id=channel_id)\
                      .order_by(cls.recorded_at.desc())\
                      .first()

    @classmethod
    def get_channel_history(cls, channel_id, days=30):
        """Get channel statistics history for the last N days"""
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return cls.query.filter(
            cls.channel_id == channel_id,
            cls.recorded_at >= cutoff_date
        ).order_by(cls.recorded_at.desc()).all()

    @classmethod
    def record_stats(cls, channel_data):
        """Record new channel statistics"""
        stats = cls(
            channel_id=channel_data['id'],
            channel_title=channel_data.get('title', ''),
            custom_url=channel_data.get('customUrl', ''),
            thumbnail_url=channel_data.get('thumbnailUrl', ''),
            subscriber_count=channel_data.get('subscriberCount', 0),
            video_count=channel_data.get('videoCount', 0),
            total_view_count=channel_data.get('channelViewCount', 0),
            avg_views_per_video=channel_data.get('channelViewCount', 0) / max(channel_data.get('videoCount', 1), 1)
        )
        db.session.add(stats)
        return stats

    def to_dict(self):
        return {
            'channel_id': self.channel_id,
            'channel_title': self.channel_title,
            'custom_url': self.custom_url,
            'thumbnail_url': self.thumbnail_url,
            'subscriber_count': self.subscriber_count,
            'video_count': self.video_count,
            'total_view_count': self.total_view_count,
            'avg_views_per_video': self.avg_views_per_video,
            'recorded_at': self.recorded_at.isoformat()
        }