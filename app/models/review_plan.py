"""Review plan models."""
from datetime import datetime, timezone
from app.extensions import db


class ReviewPlan(db.Model):
    """Study review plan."""
    __tablename__ = 'review_plans'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(20))
    exam_date = db.Column(db.Date)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='draft')
    total_tasks = db.Column(db.Integer)
    completed_tasks = db.Column(db.Integer, default=0)
    ai_generated = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    student = db.relationship('Student', back_populates='review_plans')
    tasks = db.relationship('ReviewTask', back_populates='plan', cascade='all, delete-orphan')
    mock_tests = db.relationship('MockTest', back_populates='review_plan')

    def __repr__(self):
        return f'<ReviewPlan {self.title}>'

    @property
    def progress_percentage(self):
        if self.total_tasks and self.total_tasks > 0:
            return int(self.completed_tasks / self.total_tasks * 100)
        return 0

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'title': self.title,
            'subject': self.subject,
            'exam_date': self.exam_date.isoformat() if self.exam_date else None,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'status': self.status,
            'total_tasks': self.total_tasks,
            'completed_tasks': self.completed_tasks,
            'progress_percentage': self.progress_percentage,
            'ai_generated': self.ai_generated,
            'tasks': [task.to_dict() for task in self.tasks]
        }


class ReviewTask(db.Model):
    """Individual task within a review plan."""
    __tablename__ = 'review_tasks'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('review_plans.id'), nullable=False)
    day_number = db.Column(db.Integer)
    scheduled_date = db.Column(db.Date)
    subject = db.Column(db.String(20))
    topic = db.Column(db.String(100))
    task_type = db.Column(db.String(30))
    description = db.Column(db.Text)
    knowledge_point = db.Column(db.String(100))
    status = db.Column(db.String(20), default='pending')
    time_spent = db.Column(db.Integer)
    mistake_ids = db.Column(db.Text)
    completed_at = db.Column(db.DateTime)

    # Relationships
    plan = db.relationship('ReviewPlan', back_populates='tasks')

    def __repr__(self):
        return f'<ReviewTask {self.topic} - {self.task_type}>'

    def to_dict(self):
        import json
        mistake_ids = []
        if self.mistake_ids:
            try:
                mistake_ids = json.loads(self.mistake_ids)
            except json.JSONDecodeError:
                pass
        return {
            'id': self.id,
            'plan_id': self.plan_id,
            'day_number': self.day_number,
            'scheduled_date': self.scheduled_date.isoformat() if self.scheduled_date else None,
            'subject': self.subject,
            'topic': self.topic,
            'task_type': self.task_type,
            'description': self.description,
            'knowledge_point': self.knowledge_point,
            'status': self.status,
            'time_spent': self.time_spent,
            'mistake_ids': mistake_ids,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
