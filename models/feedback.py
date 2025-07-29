from . import db
from datetime import datetime

class Feedback(db.Model):
    """사용자 피드백 모델"""
    __tablename__ = 'feedbacks'
    
    id = db.Column(db.Integer, primary_key=True)
    feedback_type = db.Column(db.String(50), nullable=False, default='general')  # suggestion, bug, feature, general
    message = db.Column(db.Text, nullable=False)
    user_ip = db.Column(db.String(45))  # IPv6 support
    user_agent = db.Column(db.String(500))
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    admin_notes = db.Column(db.Text)
    
    def __repr__(self):
        return f'<Feedback {self.id}: {self.feedback_type}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'feedback_type': self.feedback_type,
            'message': self.message,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'is_read': self.is_read,
            'admin_notes': self.admin_notes
        }
    
    @staticmethod
    def get_type_display(feedback_type):
        """피드백 타입을 한국어로 표시"""
        type_map = {
            'suggestion': '제안',
            'bug': '버그 신고',
            'feature': '기능 요청',
            'general': '일반 의견'
        }
        return type_map.get(feedback_type, feedback_type)