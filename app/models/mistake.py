"""Mistake model for wrong answers."""
from datetime import datetime, date, timedelta, timezone
from app.extensions import db


class Mistake(db.Model):
    """Wrong answer/mistake record for spaced repetition review."""
    __tablename__ = 'mistakes'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    subject = db.Column(db.String(20), nullable=False)
    grade = db.Column(db.Integer)
    topic = db.Column(db.String(100))
    knowledge_point = db.Column(db.String(100))
    question_text = db.Column(db.Text, nullable=False)
    student_answer = db.Column(db.Text)
    correct_answer = db.Column(db.Text)
    explanation = db.Column(db.Text)
    source = db.Column(db.String(50))
    source_id = db.Column(db.Integer)
    image_path = db.Column(db.String(300))
    ai_analysis = db.Column(db.Text)
    difficulty = db.Column(db.String(20))
    review_count = db.Column(db.Integer, default=0)
    mastered = db.Column(db.Boolean, default=False)
    next_review = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    student = db.relationship('Student', back_populates='mistakes')

    # Spaced repetition intervals in days
    INTERVALS = [1, 3, 7, 14, 30]

    def __repr__(self):
        return f'<Mistake {self.id} - {self.topic}>'

    def mark_reviewed(self):
        """Mark this mistake as reviewed and schedule next review."""
        self.review_count += 1
        if self.review_count >= 5:
            self.mastered = True
        idx = min(self.review_count - 1, len(self.INTERVALS) - 1)
        self.next_review = date.today() + timedelta(days=self.INTERVALS[idx])
        return self

    def mark_mastered(self):
        """Mark this mistake as mastered."""
        self.mastered = True

    @classmethod
    def get_due_for_review(cls, student_id, as_of_date=None):
        """Get mistakes due for review."""
        if as_of_date is None:
            as_of_date = date.today()
        return cls.query.filter(
            cls.student_id == student_id,
            cls.mastered == False,
            cls.next_review <= as_of_date
        ).all()

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'subject': self.subject,
            'grade': self.grade,
            'topic': self.topic,
            'knowledge_point': self.knowledge_point,
            'question_text': self.question_text,
            'student_answer': self.student_answer,
            'correct_answer': self.correct_answer,
            'explanation': self.explanation,
            'source': self.source,
            'difficulty': self.difficulty,
            'review_count': self.review_count,
            'mastered': self.mastered,
            'next_review': self.next_review.isoformat() if self.next_review else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
