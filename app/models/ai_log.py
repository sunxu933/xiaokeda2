"""AI interaction log model."""
from datetime import datetime, timezone
from app.extensions import db


class AIInteraction(db.Model):
    """AI interaction log for tracking API calls."""
    __tablename__ = 'ai_interactions'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'))
    interaction_type = db.Column(db.String(30))
    subject = db.Column(db.String(20))
    prompt_text = db.Column(db.Text)
    response_text = db.Column(db.Text)
    image_path = db.Column(db.String(300))
    model_used = db.Column(db.String(50))
    tokens_used = db.Column(db.Integer)
    duration_ms = db.Column(db.Integer)
    related_id = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    student = db.relationship('Student', back_populates='ai_interactions')

    def __repr__(self):
        return f'<AIInteraction {self.id} - {self.interaction_type}>'

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'interaction_type': self.interaction_type,
            'subject': self.subject,
            'prompt_text': self.prompt_text,
            'response_text': self.response_text,
            'image_path': self.image_path,
            'model_used': self.model_used,
            'tokens_used': self.tokens_used,
            'duration_ms': self.duration_ms,
            'related_id': self.related_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
