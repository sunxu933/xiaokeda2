"""Study session model."""
from datetime import datetime
from app.extensions import db


class StudySession(db.Model):
    """Study session tracking."""
    __tablename__ = 'study_sessions'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    subject = db.Column(db.String(20))
    session_type = db.Column(db.String(30))
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    duration = db.Column(db.Integer)
    notes = db.Column(db.Text)
    related_id = db.Column(db.Integer)

    # Relationships
    student = db.relationship('Student', back_populates='study_sessions')

    def __repr__(self):
        return f'<StudySession {self.id} - {self.session_type}>'

    @property
    def duration_minutes(self):
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            return int(delta.total_seconds() / 60)
        return self.duration or 0

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'subject': self.subject,
            'session_type': self.session_type,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': self.duration_minutes,
            'notes': self.notes,
            'related_id': self.related_id
        }
