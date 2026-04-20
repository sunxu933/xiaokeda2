"""Tests for security features."""
import pytest
from pathlib import Path


class TestPathTraversal:
    """Tests for path traversal prevention."""

    def test_browse_list_rejects_path_traversal(self, app, client):
        """Test that path traversal attacks are blocked in materials browse."""
        with app.app_context():
            from app.models.settings import AppSetting
            from app.models import Student
            import app.extensions as ext

            # Set up student first
            student = Student(name='测试', grade=3)
            ext.db.session.add(student)
            ext.db.session.commit()
            student_id = student.id
            AppSetting.set('current_student_id', str(student_id))

            AppSetting.set('materials_local_dir', '/tmp/test_materials')

            # Create test directory structure
            import os
            os.makedirs('/tmp/test_materials', exist_ok=True)
            Path('/tmp/test_materials/legit_file.txt').touch()

            # Try path traversal
            response = client.get('/materials/browse/api/list?path=../../../etc/passwd')

            # Should be rejected
            assert response.status_code == 400
            assert b'Invalid path' in response.data or b'error' in response.data

    def test_browse_list_accepts_normal_path(self, app, client):
        """Test that normal paths work correctly."""
        with app.app_context():
            from app.models.settings import AppSetting
            from app.models import Student
            import app.extensions as ext
            import os

            # Set up student first
            student = Student(name='测试', grade=3)
            ext.db.session.add(student)
            ext.db.session.commit()
            student_id = student.id
            AppSetting.set('current_student_id', str(student_id))

            os.makedirs('/tmp/test_materials/subdir', exist_ok=True)
            Path('/tmp/test_materials/legit_file.txt').touch()

            AppSetting.set('materials_local_dir', '/tmp/test_materials')

            response = client.get('/materials/browse?path=legit_file.txt')

            # Should work
            assert response.status_code == 200


class TestCSRFProtection:
    """Tests for CSRF protection."""

    def test_post_without_csrf_token_fails(self, app, client):
        """Test that POST requests without CSRF token are rejected when CSRF is enabled."""
        with app.app_context():
            from app.models.settings import AppSetting
            from app.models import Student
            import app.extensions as ext

            student = Student(name='测试', grade=3)
            ext.db.session.add(student)
            ext.db.session.commit()
            student_id = student.id

            AppSetting.set('current_student_id', str(student_id))

            # Enable CSRF for this test
            app.config['WTF_CSRF_ENABLED'] = True

            response = client.post('/homework/add', data={
                'title': '测试作业',
                'subject': '数学'
            }, follow_redirects=False)

            # Should be rejected with CSRF error
            assert response.status_code == 400

    def test_post_with_csrf_token_succeeds(self, app, client):
        """Test that POST requests with valid CSRF token succeed."""
        with app.app_context():
            from app.models.settings import AppSetting
            from app.models import Student
            import app.extensions as ext

            student = Student(name='测试', grade=3)
            ext.db.session.add(student)
            ext.db.session.commit()
            student_id = student.id

            AppSetting.set('current_student_id', str(student_id))

            # Get CSRF token from page
            response = client.get('/homework/add')
            assert response.status_code == 200

            # Extract CSRF token from meta tag
            html = response.data.decode('utf-8')
            import re
            match = re.search(r'name="csrf-token" content="([^"]+)"', html)
            assert match

            csrf_token = match.group(1)

            # Make POST request with CSRF token
            response = client.post('/homework/add', data={
                'title': '测试作业',
                'subject': '数学',
                'homework_date': '2024-01-15',
                'csrf_token': csrf_token
            }, follow_redirects=False)

            assert response.status_code == 302
