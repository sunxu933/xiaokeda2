"""Settings routes - System and student configuration."""
import os
from datetime import datetime
from pathlib import Path
from flask import Blueprint, render_template, request, redirect, url_for, flash, g, jsonify, send_file

from app.extensions import db
from app.models.student import Student
from app.models.settings import AppSetting
from app.services.ai_service import ai_service

settings_bp = Blueprint('settings', __name__)


@settings_bp.route('/')
def index():
    """Settings overview."""
    student = g.current_student
    settings = AppSetting.get_all()
    student_count = Student.query.count()

    return render_template('settings/index.html',
                         settings=settings,
                         student=student,
                         student_count=student_count)


@settings_bp.route('/student', methods=['GET', 'POST'])
def student_profile():
    """Student profile management."""
    from app.forms import StudentForm

    students = Student.query.order_by(Student.created_at.desc()).all()
    current_student = g.current_student
    form = StudentForm()

    # Populate grade choices dynamically
    form.grade.choices = [(i, f'{i}年级') for i in range(1, 7)]

    if form.validate_on_submit():
        student = Student(
            name=form.name.data,
            grade=form.grade.data,
            school=form.school.data
        )
        db.session.add(student)
        db.session.commit()

        # If first student, set as current
        if len(students) == 0:
            AppSetting.set('current_student_id', str(student.id))
            return redirect(url_for('main.index'))

        flash(f'学生 {form.name.data} 已添加', 'success')
        return redirect(url_for('settings.student_profile'))

    return render_template('settings/student_profile.html',
                         students=students,
                         current_student=current_student,
                         form=form)


@settings_bp.route('/student/<int:id>/select', methods=['POST'])
def select_student(id):
    """Switch active student."""
    student = Student.query.get_or_404(id)
    AppSetting.set('current_student_id', str(student.id))
    flash(f'已切换到 {student.name}', 'success')
    return redirect(url_for('main.index'))


@settings_bp.route('/student/<int:id>/delete', methods=['POST'])
def delete_student(id):
    """Delete a student."""
    student = Student.query.get_or_404(id)
    current_student_id = AppSetting.get('current_student_id')

    if str(student.id) == current_student_id:
        AppSetting.set('current_student_id', '')

    db.session.delete(student)
    db.session.commit()

    flash('学生已删除', 'success')

    if g.current_student and g.current_student.id == id:
        return redirect(url_for('settings.student_profile'))

    return redirect(url_for('settings.student_profile'))


@settings_bp.route('/ai-config', methods=['GET', 'POST'])
def ai_config():
    """AI API configuration."""
    if request.method == 'POST':
        endpoint = request.form.get('ai_api_endpoint', '')
        api_key = request.form.get('ai_api_key', '')
        model = request.form.get('ai_model', 'gpt-4o')
        vision_model = request.form.get('ai_vision_model', 'gpt-4o')

        AppSetting.set('ai_api_endpoint', endpoint)
        AppSetting.set('ai_api_key', api_key)
        AppSetting.set('ai_model', model)
        AppSetting.set('ai_vision_model', vision_model)

        # Reset AI service to pick up new settings
        import app.services.ai_service as ai_module
        ai_module._ai_service = None

        flash('AI配置已保存', 'success')
        return redirect(url_for('settings.ai_config'))

    settings = AppSetting.get_all()
    return render_template('settings/ai_config.html', settings=settings)


@settings_bp.route('/ai-test', methods=['POST'])
def test_ai():
    """Test AI connection (JSON)."""
    result = ai_service.test_connection()
    return jsonify(result)


@settings_bp.route('/export')
def export():
    """Data export page."""
    return render_template('settings/export.html')


@settings_bp.route('/export/db', methods=['POST'])
def export_db():
    """Export database backup."""
    db_path = Path(__file__).parent.parent.parent / 'instance' / 'xiaokeda.db'

    if not db_path.exists():
        flash('数据库文件不存在', 'error')
        return redirect(url_for('settings.export'))

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'xiaokeda_backup_{timestamp}.db'

    return send_file(
        db_path,
        mimetype='application/x-sqlite3',
        as_attachment=True,
        download_name=filename
    )
