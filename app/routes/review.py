"""Review routes - Review plans and mock tests."""
import json
from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, g, jsonify

from app.extensions import db
from app.models.review_plan import ReviewPlan, ReviewTask
from app.models.mock_test import MockTest, MockTestItem
from app.models.mistake import Mistake
from app.models.student import Student
from app.services.review_engine import review_engine
from app.services.ai_service import ai_service

review_bp = Blueprint('review', __name__)


@review_bp.route('/')
def list():
    """List review plans."""
    student = g.current_student
    if not student:
        return redirect(url_for('settings.student_profile'))

    status = request.args.get('status')

    query = ReviewPlan.query.filter_by(student_id=student.id)
    if status:
        query = query.filter_by(status=status)

    plans = query.order_by(ReviewPlan.created_at.desc()).all()

    return render_template('review/plans.html', plans=plans)


@review_bp.route('/create', methods=['GET', 'POST'])
def create():
    """Create a new review plan."""
    student = g.current_student
    if not student:
        return redirect(url_for('settings.student_profile'))

    if request.method == 'POST':
        title = request.form.get('title')
        subject = request.form.get('subject')
        exam_date = datetime.strptime(request.form.get('exam_date'), '%Y-%m-%d').date()

        try:
            plan = review_engine.auto_generate_plan(
                student.id,
                title,
                exam_date,
                subject if subject else None
            )
            flash('复习计划已创建', 'success')
            return redirect(url_for('review.plan_detail', id=plan.id))
        except ValueError as e:
            flash(str(e), 'error')

    return render_template('review/create_plan.html', student=student)


@review_bp.route('/plan/<int:id>')
def plan_detail(id):
    """View plan detail."""
    student = g.current_student
    plan = ReviewPlan.query.get_or_404(id)

    if plan.student_id != student.id:
        return redirect(url_for('review.list'))

    # Group tasks by day
    tasks_by_day = {}
    for task in plan.tasks:
        day = task.day_number or 0
        if day not in tasks_by_day:
            tasks_by_day[day] = []
        tasks_by_day[day].append(task)

    return render_template('review/plan_detail.html', plan=plan, tasks_by_day=tasks_by_day)


@review_bp.route('/plan/<int:plan_id>/task/<int:tid>/complete', methods=['POST'])
def complete_task(plan_id, tid):
    """Mark task as completed."""
    student = g.current_student
    plan = ReviewPlan.query.get_or_404(plan_id)

    if plan.student_id != student.id:
        return redirect(url_for('review.list'))

    time_spent = request.form.get('time_spent', type=int)

    try:
        review_engine.complete_task(tid, time_spent)
        flash('任务已完成', 'success')
    except ValueError as e:
        flash(str(e), 'error')

    return redirect(url_for('review.plan_detail', id=plan_id))


@review_bp.route('/plan/<int:plan_id>/task/<int:tid>/skip', methods=['POST'])
def skip_task(plan_id, tid):
    """Skip a task."""
    student = g.current_student
    plan = ReviewPlan.query.get_or_404(plan_id)

    if plan.student_id != student.id:
        return redirect(url_for('review.list'))

    try:
        review_engine.skip_task(tid)
        flash('任务已跳过', 'info')
    except ValueError as e:
        flash(str(e), 'error')

    return redirect(url_for('review.plan_detail', id=plan_id))


@review_bp.route('/plan/<int:id>/delete', methods=['POST'])
def delete_plan(id):
    """Delete a review plan."""
    student = g.current_student
    plan = ReviewPlan.query.get_or_404(id)

    if plan.student_id != student.id:
        return redirect(url_for('review.list'))

    db.session.delete(plan)
    db.session.commit()
    flash('复习计划已删除', 'success')
    return redirect(url_for('review.list'))


@review_bp.route('/knowledge-summary')
def knowledge_summary():
    """View knowledge summary."""
    student = g.current_student
    if not student:
        return redirect(url_for('settings.student_profile'))

    from app.models.knowledge import KnowledgePoint

    subject = request.args.get('subject')
    grade = request.args.get('grade', type=int) or student.grade

    query = KnowledgePoint.query.filter_by(grade=grade)
    if subject:
        query = query.filter_by(subject=subject)

    chapters = db.session.query(
        KnowledgePoint.subject,
        KnowledgePoint.semester,
        KnowledgePoint.chapter
    ).filter(
        KnowledgePoint.grade == grade
    ).distinct().all()

    summaries = []
    for subject, semester, chapter in chapters:
        if subject and chapter:
            summaries.append({
                'subject': subject,
                'semester': semester,
                'chapter': chapter
            })

    return render_template('review/knowledge_summary.html', summaries=summaries, student=student)


@review_bp.route('/knowledge-summary/generate', methods=['POST'])
def generate_knowledge_summary():
    """Generate AI knowledge summary (JSON)."""
    student = g.current_student
    if not student:
        return jsonify({'error': 'No student'}), 400

    data = request.get_json()
    chapter = data.get('chapter')
    subject = data.get('subject')

    try:
        content = ai_service.generate_knowledge_summary(chapter, subject, student.grade)
        return jsonify({'success': True, 'content': content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@review_bp.route('/practice')
def practice():
    """Chapter practice page."""
    student = g.current_student
    if not student:
        return redirect(url_for('settings.student_profile'))

    from app.models.knowledge import KnowledgePoint

    subject = request.args.get('subject')
    grade = request.args.get('grade', type=int) or student.grade

    chapters = db.session.query(
        KnowledgePoint.subject,
        KnowledgePoint.semester,
        KnowledgePoint.chapter
    ).filter(
        KnowledgePoint.grade == grade
    ).distinct().all()

    return render_template('review/practice.html', chapters=chapters, student=student)


@review_bp.route('/practice/generate', methods=['POST'])
def generate_practice():
    """Generate practice questions (JSON)."""
    student = g.current_student
    if not student:
        return jsonify({'error': 'No student'}), 400

    data = request.get_json()
    topic = data.get('topic')
    subject = data.get('subject', '数学')
    count = data.get('count', 5)

    try:
        result = ai_service.generate_practice_by_topic(topic, subject, student.grade, count)
        return jsonify({'success': True, 'problems': result.get('problems', [])})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@review_bp.route('/mock-test/create', methods=['GET', 'POST'])
def create_mock_test():
    """Create a mock test."""
    student = g.current_student
    if not student:
        return redirect(url_for('settings.student_profile'))

    if request.method == 'POST':
        subject = request.form.get('subject')
        title = request.form.get('title')
        chapter = request.form.get('chapter')

        try:
            result = ai_service.generate_mock_test([chapter] if chapter else [], subject, student.grade)
            questions = result.get('questions', [])

            test = MockTest(
                student_id=student.id,
                subject=subject,
                title=title or f'{subject}模拟测试',
                chapter=chapter,
                grade=student.grade,
                total_questions=len(questions),
                max_score=100,
                status='draft',
                ai_prompt_used=json.dumps({'chapter': chapter, 'subject': subject})
            )
            db.session.add(test)
            db.session.flush()

            for i, q_data in enumerate(questions):
                q = MockTestItem(
                    mock_test_id=test.id,
                    question_number=i + 1,
                    question_text=q_data.get('question', ''),
                    answer=q_data.get('answer', ''),
                    explanation=q_data.get('explanation', ''),
                    question_type=q_data.get('type', 'calculation'),
                    options=json.dumps(q_data.get('options', []), ensure_ascii=False),
                    knowledge_point=q_data.get('knowledge_point', ''),
                    difficulty=q_data.get('difficulty', 'medium'),
                    score=q_data.get('score', 5),
                    max_score=q_data.get('score', 5),
                    ai_generated=True
                )
                db.session.add(q)

            db.session.commit()
            flash('模拟测试已创建', 'success')
            return redirect(url_for('review.mock_test', id=test.id))

        except Exception as e:
            flash(f'创建失败: {str(e)}', 'error')

    return render_template('review/create_mock_test.html', student=student)


@review_bp.route('/mock-test/<int:id>')
def mock_test(id):
    """Take mock test."""
    student = g.current_student
    test = MockTest.query.get_or_404(id)

    if test.student_id != student.id:
        return redirect(url_for('review.mock_tests'))

    if test.status == 'completed':
        return redirect(url_for('review.mock_test_result', id=id))

    # Mark as in progress
    if test.status == 'draft':
        test.status = 'in_progress'
        db.session.commit()

    return render_template('review/mock_test.html', test=test)


@review_bp.route('/mock-test/<int:id>/submit', methods=['POST'])
def submit_mock_test(id):
    """Submit mock test answers."""
    student = g.current_student
    test = MockTest.query.get_or_404(id)

    if test.student_id != student.id:
        return redirect(url_for('review.mock_tests'))

    total_score = 0
    max_score = 0

    for item in test.items:
        answer_key = f'answer_{item.id}'
        student_answer = request.form.get(answer_key, '').strip()

        item.student_answer = student_answer
        item.is_correct = student_answer.lower().strip() == item.answer.lower().strip()

        if item.is_correct:
            total_score += item.score or 0
        max_score += item.max_score or 0

    test.score = total_score
    test.max_score = max_score
    test.status = 'completed'
    test.time_spent = request.form.get('time_spent', type=int)

    # Add wrong answers to mistake book
    for item in test.items:
        if not item.is_correct:
            mistake = Mistake(
                student_id=student.id,
                subject=test.subject,
                grade=test.grade,
                topic=item.knowledge_point or test.chapter,
                knowledge_point=item.knowledge_point,
                question_text=item.question_text,
                student_answer=item.student_answer,
                correct_answer=item.answer,
                explanation=item.explanation,
                source='mock_test',
                source_id=test.id,
                difficulty=item.difficulty or 'medium'
            )
            db.session.add(mistake)

    db.session.commit()
    flash('测试已提交', 'success')
    return redirect(url_for('review.mock_test_result', id=id))


@review_bp.route('/mock-test/<int:id>/result')
def mock_test_result(id):
    """View mock test result."""
    student = g.current_student
    test = MockTest.query.get_or_404(id)

    if test.student_id != student.id:
        return redirect(url_for('review.mock_tests'))

    return render_template('review/mock_test_result.html', test=test)


@review_bp.route('/mock-tests')
def mock_tests():
    """List mock tests."""
    student = g.current_student
    if not student:
        return redirect(url_for('settings.student_profile'))

    tests = MockTest.query.filter_by(student_id=student.id).order_by(
        MockTest.created_at.desc()
    ).all()

    return render_template('review/mock_test_list.html', tests=tests)
