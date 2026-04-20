"""Mock test models."""
from datetime import datetime, timezone
from app.extensions import db


class MockTest(db.Model):
    """Mock test/exam model."""
    __tablename__ = 'mock_tests'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('review_plans.id'))
    subject = db.Column(db.String(20))
    grade = db.Column(db.Integer)
    title = db.Column(db.String(200))
    total_questions = db.Column(db.Integer)
    score = db.Column(db.Float)
    max_score = db.Column(db.Float, default=100)
    time_limit = db.Column(db.Integer)
    time_spent = db.Column(db.Integer)
    status = db.Column(db.String(20))
    chapter = db.Column(db.String(200))
    ai_prompt_used = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    student = db.relationship('Student', back_populates='mock_tests')
    review_plan = db.relationship('ReviewPlan', back_populates='mock_tests')
    items = db.relationship('MockTestItem', back_populates='mock_test', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<MockTest {self.title}>'

    @property
    def correct_count(self):
        return sum(1 for item in self.items if item.is_correct)

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'plan_id': self.plan_id,
            'subject': self.subject,
            'grade': self.grade,
            'title': self.title,
            'total_questions': self.total_questions,
            'score': self.score,
            'max_score': self.max_score,
            'time_limit': self.time_limit,
            'time_spent': self.time_spent,
            'status': self.status,
            'chapter': self.chapter,
            'correct_count': self.correct_count,
            'items': [item.to_dict() for item in self.items]
        }


class MockTestItem(db.Model):
    """Individual question in a mock test."""
    __tablename__ = 'mock_test_items'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    mock_test_id = db.Column(db.Integer, db.ForeignKey('mock_tests.id'), nullable=False)
    question_number = db.Column(db.Integer)
    question_text = db.Column(db.Text)
    answer = db.Column(db.Text)
    options = db.Column(db.Text)
    question_type = db.Column(db.String(30))
    student_answer = db.Column(db.Text)
    is_correct = db.Column(db.Boolean)
    knowledge_point = db.Column(db.String(100))
    difficulty = db.Column(db.String(20))
    explanation = db.Column(db.Text)
    score = db.Column(db.Float)
    max_score = db.Column(db.Float)
    ai_generated = db.Column(db.Boolean, default=False)

    # Relationships
    mock_test = db.relationship('MockTest', back_populates='items')

    def __repr__(self):
        return f'<MockTestItem {self.question_number}>'

    def to_dict(self):
        import json
        options = []
        if self.options:
            try:
                options = json.loads(self.options)
            except json.JSONDecodeError:
                pass
        return {
            'id': self.id,
            'mock_test_id': self.mock_test_id,
            'question_number': self.question_number,
            'question_text': self.question_text,
            'answer': self.answer,
            'options': options,
            'question_type': self.question_type,
            'student_answer': self.student_answer,
            'is_correct': self.is_correct,
            'knowledge_point': self.knowledge_point,
            'difficulty': self.difficulty,
            'explanation': self.explanation,
            'score': self.score,
            'max_score': self.max_score,
            'ai_generated': self.ai_generated
        }
