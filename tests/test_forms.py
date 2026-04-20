"""Tests for forms and validation."""
import pytest
from datetime import date
from app.forms import StudentForm, HomeworkForm, MistakeForm


class TestStudentForm:
    """Tests for StudentForm validation."""

    def test_valid_student_form(self, app):
        with app.app_context():
            form = StudentForm(data={
                'name': '张三',
                'grade': '3',
                'school': '第一小学'
            })
            # Set choices dynamically (as done in routes)
            form.grade.choices = [(i, f'{i}年级') for i in range(1, 7)]
            assert form.validate()

    def test_student_form_missing_name(self, app):
        with app.app_context():
            form = StudentForm(data={
                'name': '',
                'grade': '3',
            })
            form.grade.choices = [(i, f'{i}年级') for i in range(1, 7)]
            assert not form.validate()
            assert 'name' in form.errors

    def test_student_form_name_too_long(self, app):
        with app.app_context():
            form = StudentForm(data={
                'name': 'x' * 100,
                'grade': '3',
            })
            form.grade.choices = [(i, f'{i}年级') for i in range(1, 7)]
            assert not form.validate()
            assert 'name' in form.errors


class TestHomeworkForm:
    """Tests for HomeworkForm validation."""

    def test_valid_homework_form(self, app):
        with app.app_context():
            form = HomeworkForm(data={
                'title': '数学作业',
                'subject': '数学',
                'homework_date': date.today()
            })
            assert form.validate()

    def test_homework_form_missing_title(self, app):
        with app.app_context():
            form = HomeworkForm(data={
                'title': '',
                'subject': '数学',
                'homework_date': date.today()
            })
            assert not form.validate()
            assert 'title' in form.errors

    def test_homework_form_invalid_subject(self, app):
        with app.app_context():
            form = HomeworkForm(data={
                'title': '作业',
                'subject': '物理',  # Invalid
                'homework_date': date.today()
            })
            assert not form.validate()


class TestMistakeForm:
    """Tests for MistakeForm validation."""

    def test_valid_mistake_form(self, app):
        with app.app_context():
            form = MistakeForm(data={
                'subject': '数学',
                'question_text': '1+1=?',
                'correct_answer': '2'
            })
            assert form.validate()

    def test_mistake_form_missing_question(self, app):
        with app.app_context():
            form = MistakeForm(data={
                'subject': '数学',
                'question_text': '',
            })
            assert not form.validate()
            assert 'question_text' in form.errors

    def test_mistake_form_all_difficulties(self, app):
        with app.app_context():
            for difficulty in ['easy', 'medium', 'hard']:
                form = MistakeForm(data={
                    'subject': '数学',
                    'question_text': '题目',
                    'difficulty': difficulty
                })
                assert form.validate(), f"Failed for difficulty {difficulty}"
