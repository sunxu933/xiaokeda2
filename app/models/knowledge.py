"""Knowledge point model."""
from datetime import datetime
from app.extensions import db


class KnowledgePoint(db.Model):
    """Knowledge point for curriculum mapping."""
    __tablename__ = 'knowledge_points'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    subject = db.Column(db.String(20), nullable=False)
    grade = db.Column(db.Integer, nullable=False)
    semester = db.Column(db.String(10))
    chapter = db.Column(db.String(100))
    topic = db.Column(db.String(100))
    description = db.Column(db.Text)
    parent_id = db.Column(db.Integer, db.ForeignKey('knowledge_points.id'))
    sort_order = db.Column(db.Integer)

    # Self-referential relationship
    children = db.relationship('KnowledgePoint', backref=db.backref('parent', remote_side=[id]))

    def __repr__(self):
        return f'<KnowledgePoint {self.subject} G{self.grade} {self.topic}>'

    def to_dict(self):
        return {
            'id': self.id,
            'subject': self.subject,
            'grade': self.grade,
            'semester': self.semester,
            'chapter': self.chapter,
            'topic': self.topic,
            'description': self.description,
            'parent_id': self.parent_id
        }
