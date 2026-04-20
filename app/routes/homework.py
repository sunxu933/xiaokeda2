"""Homework routes."""
import json
from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash, g, jsonify
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models.homework import Homework, HomeworkItem
from app.models.mistake import Mistake
from app.models.study_session import StudySession
from app.models.settings import AppSetting
from app.services.ai_service import ai_service
from app.helpers import save_uploaded_file

homework_bp = Blueprint('homework', __name__)


@homework_bp.route('/')
def list():
    """List all homework."""
    student = g.current_student
    if not student:
        return redirect(url_for('settings.student_profile'))

    subject = request.args.get('subject')
    status = request.args.get('status')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')

    query = Homework.query.filter_by(student_id=student.id)

    if subject:
        query = query.filter_by(subject=subject)
    if status:
        query = query.filter_by(status=status)
    if date_from:
        query = query.filter(Homework.homework_date >= date_from)
    if date_to:
        query = query.filter(Homework.homework_date <= date_to)

    homeworks = query.order_by(Homework.homework_date.desc()).all()

    return render_template('homework/list.html', homeworks=homeworks)


@homework_bp.route('/add', methods=['GET', 'POST'])
def add():
    """Add new homework."""
    student = g.current_student
    if not student:
        return redirect(url_for('settings.student_profile'))

    from app.forms import HomeworkForm
    form = HomeworkForm()

    if form.validate_on_submit():
        homework = Homework(
            student_id=student.id,
            title=form.title.data,
            subject=form.subject.data,
            grade=student.grade,
            homework_date=form.homework_date.data,
            notes=form.notes.data,
            status='pending'
        )

        if form.due_date.data:
            homework.due_date = form.due_date.data

        db.session.add(homework)
        db.session.commit()

        flash('作业已创建', 'success')
        return redirect(url_for('homework.detail', id=homework.id))

    return render_template('homework/add.html', student=student, form=form)


@homework_bp.route('/<int:id>')
def detail(id):
    """View homework detail."""
    student = g.current_student
    homework = Homework.query.get_or_404(id)

    if homework.student_id != student.id:
        return redirect(url_for('homework.list'))

    return render_template('homework/detail.html', homework=homework)


@homework_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
def edit(id):
    """Edit homework."""
    student = g.current_student
    homework = Homework.query.get_or_404(id)

    if homework.student_id != student.id:
        return redirect(url_for('homework.list'))

    if request.method == 'POST':
        homework.title = request.form.get('title')
        homework.subject = request.form.get('subject')
        homework.homework_date = datetime.strptime(request.form.get('homework_date'), '%Y-%m-%d').date()

        due_date = request.form.get('due_date')
        if due_date:
            homework.due_date = datetime.strptime(due_date, '%Y-%m-%d').date()

        homework.notes = request.form.get('notes')
        homework.status = request.form.get('status')
        homework.total_score = request.form.get('total_score')
        homework.max_score = request.form.get('max_score')

        db.session.commit()
        flash('作业已更新', 'success')
        return redirect(url_for('homework.detail', id=homework.id))

    return render_template('homework/edit.html', homework=homework)


@homework_bp.route('/<int:id>/delete', methods=['POST'])
def delete(id):
    """Delete homework."""
    student = g.current_student
    homework = Homework.query.get_or_404(id)

    if homework.student_id != student.id:
        return redirect(url_for('homework.list'))

    db.session.delete(homework)
    db.session.commit()
    flash('作业已删除', 'success')
    return redirect(url_for('homework.list'))


@homework_bp.route('/<int:id>/status', methods=['POST'])
def update_status(id):
    """Update homework status."""
    student = g.current_student
    homework = Homework.query.get_or_404(id)

    if homework.student_id != student.id:
        return redirect(url_for('homework.list'))

    new_status = request.form.get('status')
    old_status = homework.status
    homework.status = new_status

    # Create study session if completing
    if new_status == 'completed' and old_status != 'completed':
        session = StudySession(
            student_id=student.id,
            subject=homework.subject,
            session_type='homework',
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
            duration=homework.time_spent or 30,
            related_id=homework.id
        )
        db.session.add(session)

    db.session.commit()
    flash(f'状态已更新为 {new_status}', 'success')
    return redirect(url_for('homework.detail', id=homework.id))


@homework_bp.route('/<int:id>/items', methods=['POST'])
def add_item(id):
    """Add homework item (AJAX)."""
    homework = Homework.query.get_or_404(id)

    item = HomeworkItem(
        homework_id=homework.id,
        question_number=request.form.get('question_number'),
        content=request.form.get('content'),
        student_answer=request.form.get('student_answer'),
        correct_answer=request.form.get('correct_answer'),
        is_correct=request.form.get('is_correct') == 'true',
        mistake_type=request.form.get('mistake_type'),
        knowledge_point=request.form.get('knowledge_point')
    )

    db.session.add(item)
    db.session.commit()

    return jsonify({'success': True, 'item_id': item.id})


@homework_bp.route('/<int:id>/items/<int:item_id>', methods=['PUT'])
def update_item(id, item_id):
    """Update homework item (AJAX)."""
    item = HomeworkItem.query.get_or_404(item_id)

    item.question_number = request.form.get('question_number')
    item.content = request.form.get('content')
    item.student_answer = request.form.get('student_answer')
    item.correct_answer = request.form.get('correct_answer')
    item.is_correct = request.form.get('is_correct') == 'true'
    item.mistake_type = request.form.get('mistake_type')
    item.knowledge_point = request.form.get('knowledge_point')

    db.session.commit()

    return jsonify({'success': True})


@homework_bp.route('/<int:id>/extract-mistakes', methods=['POST'])
def extract_mistakes(id):
    """Extract mistakes from homework."""
    student = g.current_student
    homework = Homework.query.get_or_404(id)

    if homework.student_id != student.id:
        return redirect(url_for('homework.list'))

    # Find incorrect items
    incorrect_items = [item for item in homework.items if item.is_correct is False]

    created_count = 0
    for item in incorrect_items:
        mistake = Mistake(
            student_id=student.id,
            subject=homework.subject,
            grade=homework.grade,
            topic=item.knowledge_point or homework.title,
            knowledge_point=item.knowledge_point,
            question_text=item.content or '',
            student_answer=item.student_answer,
            correct_answer=item.correct_answer,
            source='homework',
            source_id=homework.id,
            difficulty='medium'
        )
        db.session.add(mistake)
        created_count += 1

    db.session.commit()
    flash(f'已提取 {created_count} 道错题到错题本', 'success')
    return redirect(url_for('mistakes.list'))


@homework_bp.route('/recognize-photo', methods=['POST'])
def recognize_photo():
    """Recognize homework from photo (AI)."""
    student = g.current_student
    if not student:
        return jsonify({'error': 'No student selected'}), 400

    if 'photo' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['photo']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # Save file
    filepath = save_uploaded_file(file, 'homework')

    # Call AI service
    try:
        result = ai_service.recognize_homework(filepath, student.grade, student.id)
        return jsonify({
            'success': True,
            'filepath': filepath,
            'data': result
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
