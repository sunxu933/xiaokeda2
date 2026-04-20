"""Homework models."""
from datetime import datetime, date, timezone
from app.extensions import db


class Homework(db.Model):
    """Homework assignment model."""
    __tablename__ = 'homework'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(20), nullable=False)
    grade = db.Column(db.Integer)
    homework_date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='pending')
    total_score = db.Column(db.Float)
    max_score = db.Column(db.Float)
    notes = db.Column(db.Text)
    time_spent = db.Column(db.Integer)
    image_path = db.Column(db.String(300))
    ai_recognition = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    student = db.relationship('Student', back_populates='homeworks')
    items = db.relationship('HomeworkItem', back_populates='homework', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Homework {self.title}>'

    @property
    def mistake_count(self):
        """Count of incorrect items."""
        return sum(1 for item in self.items if not item.is_correct)

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'title': self.title,
            'subject': self.subject,
            'grade': self.grade,
            'homework_date': self.homework_date.isoformat() if self.homework_date else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'status': self.status,
            'total_score': self.total_score,
            'max_score': self.max_score,
            'notes': self.notes,
            'time_spent': self.time_spent,
            'items': [item.to_dict() for item in self.items]
        }


class HomeworkItem(db.Model):
    """Individual homework question/item."""
    __tablename__ = 'homework_items'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    homework_id = db.Column(db.Integer, db.ForeignKey('homework.id'), nullable=False)
    question_number = db.Column(db.Integer)
    content = db.Column(db.Text)
    is_correct = db.Column(db.Boolean)
    student_answer = db.Column(db.Text)
    correct_answer = db.Column(db.Text)
    mistake_type = db.Column(db.String(50))
    knowledge_point = db.Column(db.String(100))

    # Relationships
    homework = db.relationship('Homework', back_populates='items')

    def __repr__(self):
        return f'<HomeworkItem {self.question_number}>'

    def to_dict(self):
        return {
            'id': self.id,
            'homework_id': self.homework_id,
            'question_number': self.question_number,
            'content': self.content,
            'is_correct': self.is_correct,
            'student_answer': self.student_answer,
            'correct_answer': self.correct_answer,
            'mistake_type': self.mistake_type,
            'knowledge_point': self.knowledge_point
        }
