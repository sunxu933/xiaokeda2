"""Student model."""
from datetime import datetime, timezone
from app.extensions import db


class Student(db.Model):
    """Student model for tracking children."""
    __tablename__ = 'students'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    grade = db.Column(db.Integer, nullable=False)
    school = db.Column(db.String(100))
    avatar = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    homeworks = db.relationship('Homework', back_populates='student', cascade='all, delete-orphan')
    mistakes = db.relationship('Mistake', back_populates='student', cascade='all, delete-orphan')
    study_sessions = db.relationship('StudySession', back_populates='student', cascade='all, delete-orphan')
    review_plans = db.relationship('ReviewPlan', back_populates='student', cascade='all, delete-orphan')
    mock_tests = db.relationship('MockTest', back_populates='student', cascade='all, delete-orphan')
    materials = db.relationship('Material', back_populates='student', cascade='all, delete-orphan')
    ai_interactions = db.relationship('AIInteraction', back_populates='student', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Student {self.name} Grade {self.grade}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'grade': self.grade,
            'school': self.school,
            'avatar': self.avatar,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
