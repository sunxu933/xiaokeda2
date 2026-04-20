"""Integration tests for xiaokeda application."""
import pytest
from datetime import date, datetime, timedelta
from app import create_app
from app.extensions import db
from app.models import Student, Homework, HomeworkItem, Mistake, Material


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app('development')
    app.config['TESTING'] = True
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
        student = Student(name='测试学生', grade=3, school='测试学校')
        db.session.add(student)
        db.session.commit()
        return student.id


class TestStudentModel:
    """Tests for Student model."""

    def test_create_student(self, app, init_student):
        with app.app_context():
            student = db.session.get(Student, init_student)
            assert student is not None
            assert student.name == '测试学生'
            assert student.grade == 3

    def test_student_to_dict(self, app, init_student):
        with app.app_context():
            student = db.session.get(Student, init_student)
            data = student.to_dict()
            assert data['name'] == '测试学生'
            assert data['grade'] == 3


class TestHomeworkModel:
    """Tests for Homework model."""

    def test_create_homework(self, app, init_student):
        with app.app_context():
            homework = Homework(
                student_id=init_student,
                title='数学作业',
                subject='数学',
                homework_date=date.today()
            )
            db.session.add(homework)
            db.session.commit()

            assert homework.id is not None
            assert homework.title == '数学作业'

    def test_homework_items(self, app, init_student):
        with app.app_context():
            homework = Homework(
                student_id=init_student,
                title='数学作业',
                subject='数学',
                homework_date=date.today()
            )
            db.session.add(homework)
            db.session.flush()

            item = HomeworkItem(
                homework_id=homework.id,
                question_number=1,
                content='1+1=？',
                correct_answer='2',
                is_correct=True
            )
            db.session.add(item)
            db.session.commit()

            assert len(homework.items) == 1
            assert homework.items[0].content == '1+1=？'

    def test_mistake_count(self, app, init_student):
        with app.app_context():
            homework = Homework(
                student_id=init_student,
                title='数学作业',
                subject='数学',
                homework_date=date.today()
            )
            db.session.add(homework)
            db.session.flush()

            item1 = HomeworkItem(homework_id=homework.id, is_correct=True)
            item2 = HomeworkItem(homework_id=homework.id, is_correct=False)
            db.session.add_all([item1, item2])
            db.session.commit()

            assert homework.mistake_count == 1


class TestMistakeModel:
    """Tests for Mistake model with spaced repetition."""

    def test_create_mistake(self, app, init_student):
        with app.app_context():
            mistake = Mistake(
                student_id=init_student,
                subject='数学',
                question_text='2+2=？',
                student_answer='5',
                correct_answer='4'
            )
            db.session.add(mistake)
            db.session.commit()

            assert mistake.review_count == 0
            assert mistake.mastered is False

    def test_mark_reviewed(self, app, init_student):
        with app.app_context():
            mistake = Mistake(
                student_id=init_student,
                subject='数学',
                question_text='2+2=？'
            )
            db.session.add(mistake)
            db.session.commit()

            mistake.mark_reviewed()

            assert mistake.review_count == 1
            assert mistake.next_review == date.today() + timedelta(days=1)

    def test_spaced_repetition_intervals(self, app, init_student):
        with app.app_context():
            mistake = Mistake(
                student_id=init_student,
                subject='数学',
                question_text='2+2=？'
            )
            db.session.add(mistake)
            db.session.commit()

            intervals = [1, 3, 7, 14, 30]
            for i in range(5):
                mistake.mark_reviewed()

            assert mistake.review_count == 5
            assert mistake.mastered is True

    def test_get_due_for_review(self, app, init_student):
        with app.app_context():
            mistake = Mistake(
                student_id=init_student,
                subject='数学',
                question_text='2+2=？',
                next_review=date.today() - timedelta(days=1)
            )
            db.session.add(mistake)
            db.session.commit()

            due = Mistake.get_due_for_review(init_student)
            assert len(due) == 1
            assert due[0].id == mistake.id


class TestHomeworkRoutes:
    """Tests for homework routes."""

    def test_homework_list(self, client, app, init_student):
        with app.app_context():
            from app.models.settings import AppSetting
            AppSetting.set('current_student_id', str(init_student))

            response = client.get('/homework/')
            assert response.status_code == 200

    def test_create_homework(self, client, app, init_student):
        with app.app_context():
            from app.models.settings import AppSetting
            AppSetting.set('current_student_id', str(init_student))

            response = client.post('/homework/add', data={
                'title': '测试作业',
                'subject': '数学',
                'homework_date': date.today().strftime('%Y-%m-%d')
            }, follow_redirects=False)

            assert response.status_code == 302


class TestMistakeRoutes:
    """Tests for mistake routes."""

    def test_mistake_list(self, client, app, init_student):
        with app.app_context():
            from app.models.settings import AppSetting
            AppSetting.set('current_student_id', str(init_student))

            response = client.get('/mistakes/')
            assert response.status_code == 200

    def test_add_mistake(self, client, app, init_student):
        with app.app_context():
            from app.models.settings import AppSetting
            AppSetting.set('current_student_id', str(init_student))

            response = client.post('/mistakes/add', data={
                'subject': '数学',
                'topic': '加法',
                'question_text': '1+1=？',
                'correct_answer': '2'
            }, follow_redirects=False)

            assert response.status_code == 302

    def test_mark_reviewed(self, client, app, init_student):
        with app.app_context():
            from app.models.settings import AppSetting
            AppSetting.set('current_student_id', str(init_student))

            mistake = Mistake(
                student_id=init_student,
                subject='数学',
                question_text='2+2=？'
            )
            db.session.add(mistake)
            db.session.commit()
            mistake_id = mistake.id

            response = client.post(f'/mistakes/{mistake_id}/mark-reviewed', follow_redirects=False)
            assert response.status_code == 302


class TestReviewEngine:
    """Tests for review engine."""

    def test_generate_plan_validation(self, app, init_student):
        from app.services.review_engine import review_engine

        with app.app_context():
            with pytest.raises(ValueError, match="考试日期距今至少需要3天"):
                review_engine.auto_generate_plan(
                    init_student,
                    '测试计划',
                    date.today() + timedelta(days=1)
                )

    def test_generate_plan_success(self, app, init_student):
        from app.services.review_engine import review_engine

        with app.app_context():
            plan = review_engine.auto_generate_plan(
                init_student,
                '期中复习',
                date.today() + timedelta(days=7)
            )

            assert plan is not None
            assert plan.title == '期中复习'
            assert plan.status == 'active'
            assert plan.total_tasks > 0


class TestStatsService:
    """Tests for statistics service."""

    def test_dashboard_stats(self, app, init_student):
        from app.services.stats_service import stats_service

        with app.app_context():
            stats = stats_service.get_dashboard_stats(init_student)

            assert 'today_homework' in stats
            assert 'due_reviews' in stats
            assert 'unmastered_mistakes' in stats


class TestPDFService:
    """Tests for PDF service."""

    def test_clean_question_text(self, app):
        from app.services.pdf_service import PDFService

        with app.app_context():
            text = "1. 计算下列题目 (5分)\n答案："
            cleaned = PDFService._clean_question_text(text)
            assert '5分' not in cleaned
            assert '答案：' in cleaned


class TestAIServiceJSONExtraction:
    """Tests for AI service JSON extraction."""

    def test_extract_json_from_text(self, app):
        with app.app_context():
            from app.helpers import extract_json_from_text

            # Test direct JSON
            result = extract_json_from_text('{"key": "value"}')
            assert result == {"key": "value"}

            # Test JSON in code block
            result = extract_json_from_text('```json\n{"key": "value"}\n```')
            assert result == {"key": "value"}

            # Test invalid JSON
            result = extract_json_from_text('not json at all')
            assert result is None


class TestMaterialModel:
    """Tests for Material model."""

    def test_create_material(self, app, init_student):
        with app.app_context():
            material = Material(
                student_id=init_student,
                title='数学试卷',
                file_path='uploads/materials/test.pdf',
                file_type='pdf',
                status='pending'
            )
            db.session.add(material)
            db.session.commit()

            assert material.id is not None
            assert material.status == 'pending'


class TestReviewPlanModel:
    """Tests for ReviewPlan model."""

    def test_progress_percentage(self, app, init_student):
        with app.app_context():
            from app.models.review_plan import ReviewPlan

            plan = ReviewPlan(
                student_id=init_student,
                title='测试计划',
                total_tasks=10,
                completed_tasks=5
            )
            db.session.add(plan)
            db.session.commit()

            assert plan.progress_percentage == 50
