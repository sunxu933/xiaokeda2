"""Material models for learning resources."""
from datetime import datetime, timezone
from app.extensions import db


class Material(db.Model):
    """Learning material/document model."""
    __tablename__ = 'materials'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(20))
    material_type = db.Column(db.String(30))
    file_path = db.Column(db.String(300))
    file_type = db.Column(db.String(20))
    description = db.Column(db.Text)
    source_grade = db.Column(db.Integer)
    source_semester = db.Column(db.String(10))
    source_chapter = db.Column(db.String(200))
    ai_analysis = db.Column(db.Text)
    page_images = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')
    tags = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    student = db.relationship('Student', back_populates='materials')
    knowledge_points = db.relationship('MaterialKnowledge', back_populates='material', cascade='all, delete-orphan')
    questions = db.relationship('MaterialQuestion', back_populates='material', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Material {self.title}>'

    def to_dict(self):
        import json
        page_images = []
        if self.page_images:
            try:
                page_images = json.loads(self.page_images)
            except json.JSONDecodeError:
                pass
        return {
            'id': self.id,
            'student_id': self.student_id,
            'title': self.title,
            'subject': self.subject,
            'material_type': self.material_type,
            'file_path': self.file_path,
            'file_type': self.file_type,
            'description': self.description,
            'source_grade': self.source_grade,
            'source_semester': self.source_semester,
            'source_chapter': self.source_chapter,
            'status': self.status,
            'tags': self.tags,
            'page_images': page_images,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class MaterialKnowledge(db.Model):
    """Knowledge points extracted from materials."""
    __tablename__ = 'material_knowledge'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    material_id = db.Column(db.Integer, db.ForeignKey('materials.id'), nullable=False)
    subject = db.Column(db.String(20))
    chapter = db.Column(db.String(200))
    topic = db.Column(db.String(200))
    content = db.Column(db.Text)
    key_formulas = db.Column(db.Text)
    key_points = db.Column(db.Text)
    difficulty = db.Column(db.String(20))
    importance = db.Column(db.String(20))

    # Relationships
    material = db.relationship('Material', back_populates='knowledge_points')

    def __repr__(self):
        return f'<MaterialKnowledge {self.topic}>'

    def to_dict(self):
        import json
        key_formulas = []
        key_points = []
        if self.key_formulas:
            try:
                key_formulas = json.loads(self.key_formulas)
            except json.JSONDecodeError:
                pass
        if self.key_points:
            try:
                key_points = json.loads(self.key_points)
            except json.JSONDecodeError:
                pass
        return {
            'id': self.id,
            'material_id': self.material_id,
            'subject': self.subject,
            'chapter': self.chapter,
            'topic': self.topic,
            'content': self.content,
            'key_formulas': key_formulas,
            'key_points': key_points,
            'difficulty': self.difficulty,
            'importance': self.importance
        }


class MaterialQuestion(db.Model):
    """Questions extracted from materials."""
    __tablename__ = 'material_questions'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    material_id = db.Column(db.Integer, db.ForeignKey('materials.id'), nullable=False)
    question_text = db.Column(db.Text)
    answer = db.Column(db.Text)
    explanation = db.Column(db.Text)
    question_type = db.Column(db.String(30))
    knowledge_point = db.Column(db.String(200))
    difficulty = db.Column(db.String(20))
    options = db.Column(db.Text)
    page_number = db.Column(db.Integer)
    score = db.Column(db.Float)
    ai_generated = db.Column(db.Boolean, default=False)

    # Relationships
    material = db.relationship('Material', back_populates='questions')

    def __repr__(self):
        return f'<MaterialQuestion {self.id}>'

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
            'material_id': self.material_id,
            'question_text': self.question_text,
            'answer': self.answer,
            'explanation': self.explanation,
            'question_type': self.question_type,
            'knowledge_point': self.knowledge_point,
            'difficulty': self.difficulty,
            'options': options,
            'page_number': self.page_number,
            'score': self.score,
            'ai_generated': self.ai_generated
        }
