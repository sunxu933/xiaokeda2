"""Mistakes routes - Wrong answer notebook."""
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, g, jsonify

from app.extensions import db
from app.models.mistake import Mistake
from app.models.material import Material
from app.services.ai_service import ai_service
from app.helpers import save_uploaded_file

mistakes_bp = Blueprint('mistakes', __name__)


@mistakes_bp.route('/')
def list():
    """List all mistakes."""
    student = g.current_student
    if not student:
        return redirect(url_for('settings.student_profile'))

    subject = request.args.get('subject')
    topic = request.args.get('topic')
    mastered = request.args.get('mastered')

    query = Mistake.query.filter_by(student_id=student.id)

    if subject:
        query = query.filter_by(subject=subject)
    if topic:
        query = query.filter_by(topic=topic)
    if mastered == 'true':
        query = query.filter_by(mastered=True)
    elif mastered == 'false':
        query = query.filter_by(mastered=False)

    mistakes = query.order_by(Mistake.created_at.desc()).all()

    return render_template('mistakes/list.html', mistakes=mistakes)


@mistakes_bp.route('/add', methods=['GET', 'POST'])
def add():
    """Add a new mistake manually."""
    from app.forms import MistakeForm

    student = g.current_student
    if not student:
        return redirect(url_for('settings.student_profile'))

    form = MistakeForm()

    if form.validate_on_submit():
        mistake = Mistake(
            student_id=student.id,
            subject=form.subject.data,
            grade=student.grade,
            topic=form.topic.data,
            knowledge_point=form.knowledge_point.data,
            question_text=form.question_text.data,
            student_answer=form.student_answer.data,
            correct_answer=form.correct_answer.data,
            explanation=form.explanation.data,
            source='manual',
            difficulty=form.difficulty.data or 'medium'
        )

        db.session.add(mistake)
        db.session.commit()

        flash('错题已添加', 'success')
        return redirect(url_for('mistakes.detail', id=mistake.id))

    return render_template('mistakes/add.html', student=student, form=form)


@mistakes_bp.route('/<int:id>')
def detail(id):
    """View mistake detail."""
    student = g.current_student
    mistake = Mistake.query.get_or_404(id)

    if mistake.student_id != student.id:
        return redirect(url_for('mistakes.list'))

    return render_template('mistakes/detail.html', mistake=mistake)


@mistakes_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
def edit(id):
    """Edit a mistake."""
    student = g.current_student
    mistake = Mistake.query.get_or_404(id)

    if mistake.student_id != student.id:
        return redirect(url_for('mistakes.list'))

    if request.method == 'POST':
        mistake.subject = request.form.get('subject')
        mistake.topic = request.form.get('topic')
        mistake.knowledge_point = request.form.get('knowledge_point')
        mistake.question_text = request.form.get('question_text')
        mistake.student_answer = request.form.get('student_answer')
        mistake.correct_answer = request.form.get('correct_answer')
        mistake.explanation = request.form.get('explanation')
        mistake.difficulty = request.form.get('difficulty')

        db.session.commit()
        flash('错题已更新', 'success')
        return redirect(url_for('mistakes.detail', id=mistake.id))

    return render_template('mistakes/edit.html', mistake=mistake)


@mistakes_bp.route('/<int:id>/delete', methods=['POST'])
def delete(id):
    """Delete a mistake."""
    student = g.current_student
    mistake = Mistake.query.get_or_404(id)

    if mistake.student_id != student.id:
        return redirect(url_for('mistakes.list'))

    db.session.delete(mistake)
    db.session.commit()
    flash('错题已删除', 'success')
    return redirect(url_for('mistakes.list'))


@mistakes_bp.route('/<int:id>/mark-mastered', methods=['POST'])
def mark_mastered(id):
    """Mark mistake as mastered."""
    student = g.current_student
    mistake = Mistake.query.get_or_404(id)

    if mistake.student_id != student.id:
        return redirect(url_for('mistakes.list'))

    mistake.mark_mastered()
    db.session.commit()
    flash('已标记为已掌握', 'success')
    return redirect(url_for('mistakes.detail', id=mistake.id))


@mistakes_bp.route('/<int:id>/mark-reviewed', methods=['POST'])
def mark_reviewed(id):
    """Mark mistake as reviewed (spaced repetition)."""
    student = g.current_student
    mistake = Mistake.query.get_or_404(id)

    if mistake.student_id != student.id:
        return redirect(url_for('mistakes.list'))

    mistake.mark_reviewed()
    db.session.commit()

    if mistake.mastered:
        flash('太棒了！这道题已经掌握了！', 'success')
    else:
        next_review = mistake.next_review.strftime('%Y-%m-%d') if mistake.next_review else '未知'
        flash(f'已复习，下次复习日期：{next_review}', 'info')

    return redirect(url_for('mistakes.list'))


@mistakes_bp.route('/by-topic')
def by_topic():
    """View mistakes grouped by topic."""
    student = g.current_student
    if not student:
        return redirect(url_for('settings.student_profile'))

    mistakes = Mistake.query.filter_by(student_id=student.id).all()

    # Group by subject and topic
    grouped = {}
    for m in mistakes:
        key = (m.subject, m.topic or '未分类')
        if key not in grouped:
            grouped[key] = {
                'subject': m.subject,
                'topic': m.topic,
                'mistakes': [],
                'mastered_count': 0,
                'total_count': 0
            }
        grouped[key]['mistakes'].append(m)
        grouped[key]['total_count'] += 1
        if m.mastered:
            grouped[key]['mastered_count'] += 1

    topics = sorted(grouped.values(), key=lambda x: x['total_count'], reverse=True)

    return render_template('mistakes/by_topic.html', topics=topics)


@mistakes_bp.route('/review-due')
def review_due():
    """Show mistakes due for review today."""
    student = g.current_student
    if not student:
        return redirect(url_for('settings.student_profile'))

    from datetime import date
    due_mistakes = Mistake.get_due_for_review(student.id, date.today())

    return render_template('mistakes/review_due.html', mistakes=due_mistakes)
