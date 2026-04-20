"""Test configuration and fixtures."""
import pytest
from app import create_app
from app.extensions import db


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app('development')
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key-for-csrf'
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create test CLI runner."""
    return app.test_cli_runner()


@pytest.fixture
def init_student(app):
    """Initialize a test student."""
    with app.app_context():
        from app.models import Student
        student = Student(name='测试学生', grade=3, school='测试学校')
        db.session.add(student)
        db.session.commit()
        return student.id
