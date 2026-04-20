"""Application factory."""
import os
from datetime import datetime
from pathlib import Path
from flask import Flask, g, render_template
from dotenv import load_dotenv

from app.config import config
from app.extensions import db, migrate, csrf

load_dotenv()


def create_app(config_name='default'):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    # Create upload directories
    create_upload_dir()

    # Register blueprints
    register_blueprints(app)

    # Register template filters
    register_template_filters(app)

    # Register context processors
    register_context_processors(app)

    # Register error handlers
    register_error_handlers(app)

    # Create database tables
    with app.app_context():
        db.create_all()
        _seed_initial_data()

    return app


def create_upload_dir():
    """Create upload directories if they don't exist."""
    base = Path(__file__).parent / 'static' / 'uploads'
    for subfolder in ['homework', 'mistakes', 'materials']:
        path = base / subfolder
        path.mkdir(parents=True, exist_ok=True)


def register_blueprints(app):
    """Register all blueprints."""
    from app.routes.main import main_bp
    from app.routes.homework import homework_bp
    from app.routes.mistakes import mistakes_bp
    from app.routes.ai_tutor import ai_tutor_bp
    from app.routes.materials import materials_bp
    from app.routes.review import review_bp
    from app.routes.reports import reports_bp
    from app.routes.settings import settings_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(homework_bp, url_prefix='/homework')
    app.register_blueprint(mistakes_bp, url_prefix='/mistakes')
    app.register_blueprint(ai_tutor_bp, url_prefix='/ai-tutor')
    app.register_blueprint(materials_bp, url_prefix='/materials')
    app.register_blueprint(review_bp, url_prefix='/review')
    app.register_blueprint(reports_bp, url_prefix='/reports')
    app.register_blueprint(settings_bp, url_prefix='/settings')


def register_template_filters(app):
    """Register custom Jinja2 filters."""
    from datetime import datetime

    @app.template_filter('datetimeformat')
    def datetimeformat(value):
        if isinstance(value, datetime):
            return value.strftime('%Y-%m-%d %H:%M')
        return value

    @app.template_filter('dateformat')
    def dateformat(value):
        if isinstance(value, (datetime, str)):
            if isinstance(value, str):
                try:
                    value = datetime.fromisoformat(value)
                except ValueError:
                    return value
            return value.strftime('%Y-%m-%d')
        return value

    @app.template_filter('subject_color')
    def subject_color(subject):
        colors = {
            '语文': '#e74c3c',
            '数学': '#3498db',
            '英语': '#2ecc71'
        }
        return colors.get(subject, '#95a5a6')

    @app.template_filter('subject_icon')
    def subject_icon(subject):
        icons = {
            '语文': '📖',
            '数学': '🔢',
            '英语': '🔤'
        }
        return icons.get(subject, '📚')

    @app.template_filter('nl2br')
    def nl2br(value):
        if value:
            return value.replace('\n', '<br>')
        return value

    @app.template_filter('from_json')
    def from_json(value):
        import json
        if value and isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return value

    @app.template_filter('to_letter')
    def to_letter(value):
        if isinstance(value, int) and 0 <= value <= 25:
            return chr(65 + value)
        return value


def register_context_processors(app):
    """Register context processors for template globals."""
    from functools import wraps
    from flask import redirect, url_for, session

    def require_student(f):
        """Decorator to require a student to be selected."""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from app.models.settings import AppSetting
            current_student_id = AppSetting.get('current_student_id')
            if not current_student_id:
                return redirect(url_for('settings.student_profile'))
            return f(*args, **kwargs)
        return decorated_function

    @app.before_request
    def inject_globals():
        """Inject global variables into each request."""
        from app.models.student import Student
        from app.models.settings import AppSetting

        try:
            current_student_id = AppSetting.get('current_student_id')
            if current_student_id:
                g.current_student = db.session.get(Student, int(current_student_id))
            else:
                g.current_student = None
        except Exception:
            g.current_student = None

        g.today = datetime.today()


def register_error_handlers(app):
    """Register error handlers."""

    @app.errorhandler(404)
    def not_found(error):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('500.html'), 500


def _seed_initial_data():
    """Seed initial data if tables are empty."""
    from app.models.settings import AppSetting
    from app.models.knowledge import KnowledgePoint
    import json

    # Seed app settings if empty
    if AppSetting.query.count() == 0:
        default_settings = [
            ('ai_api_endpoint', 'https://api.openai.com/v1', 'AI API endpoint URL'),
            ('ai_api_key', '', 'AI API key'),
            ('ai_model', 'gpt-4o', 'Default AI model'),
            ('ai_vision_model', 'gpt-4o', 'AI model for vision tasks'),
            ('daily_study_goal_minutes', '60', 'Daily study goal in minutes'),
            ('current_student_id', '', 'Currently selected student ID'),
            ('materials_local_dir', '', 'Local directory for browsing materials'),
        ]
        for key, value, description in default_settings:
            setting = AppSetting(key=key, value=value, description=description)
            db.session.add(setting)

    # Seed knowledge points if empty
    if KnowledgePoint.query.count() == 0:
        seed_file = Path(__file__).parent / 'seed_data' / 'knowledge_points.json'
        if seed_file.exists():
            with open(seed_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            _import_knowledge_points(data)

    db.session.commit()


def _import_knowledge_points(data, parent_id=None):
    """Import knowledge points from JSON structure using bulk insert.

    Returns the count of imported records. Caller is responsible for commit.
    """
    from app.models.knowledge import KnowledgePoint

    kp_list = []
    for subject, grades in data.items():
        for grade_str, semesters in grades.items():
            grade = int(grade_str)
            for semester, chapters in semesters.items():
                for chapter_data in chapters:
                    chapter = chapter_data.get('chapter', '')
                    topics = chapter_data.get('topics', [])
                    for topic in topics:
                        kp = KnowledgePoint(
                            subject=subject,
                            grade=grade,
                            semester=semester,
                            chapter=chapter,
                            topic=topic,
                            parent_id=parent_id
                        )
                        kp_list.append(kp)

    # Bulk insert for better performance
    if kp_list:
        db.session.bulk_save_objects(kp_list)
        return len(kp_list)
    return 0
