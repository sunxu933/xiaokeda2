"""AI Tutor routes."""
import json
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, g, jsonify

from app.extensions import db
from app.models.mistake import Mistake
from app.models.material import Material
from app.models.ai_log import AIInteraction
from app.services.ai_service import ai_service
from app.helpers import save_uploaded_file

ai_tutor_bp = Blueprint('ai_tutor', __name__)


@ai_tutor_bp.route('/')
def chat():
    """AI chat interface."""
    student = g.current_student
    if not student:
        return redirect(url_for('settings.student_profile'))

    return render_template('ai_tutor/chat.html', student=student)


@ai_tutor_bp.route('/explain/<int:mistake_id>')
def explain(mistake_id):
    """Explain a specific mistake."""
    student = g.current_student
    mistake = Mistake.query.get_or_404(mistake_id)

    if mistake.student_id != student.id:
        return redirect(url_for('ai_tutor.chat'))

    explanation = None
    if mistake.explanation:
        explanation = mistake.explanation
    elif mistake.question_text and mistake.correct_answer:
        try:
            explanation = ai_service.explain_problem(
                mistake.question_text,
                mistake.correct_answer,
                student.grade,
                student.id,
                mistake.subject
            )
        except Exception as e:
            flash(f'AI讲解失败: {str(e)}', 'error')

    return render_template('ai_tutor/explain.html', mistake=mistake, explanation=explanation)


@ai_tutor_bp.route('/practice/<int:mistake_id>')
def practice(mistake_id):
    """Generate similar practice problems for a mistake."""
    student = g.current_student
    mistake = Mistake.query.get_or_404(mistake_id)

    if mistake.student_id != student.id:
        return redirect(url_for('ai_tutor.chat'))

    return render_template('ai_tutor/practice.html', mistake=mistake)


@ai_tutor_bp.route('/chat', methods=['POST'])
def chat_api():
    """Handle chat messages (JSON API)."""
    student = g.current_student
    if not student:
        return jsonify({'error': 'No student'}), 400

    data = request.get_json()
    messages = data.get('messages', [])
    subject = data.get('subject')

    try:
        response = ai_service.chat(messages, student.grade, subject)
        return jsonify({'success': True, 'response': response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@ai_tutor_bp.route('/analyze-photo', methods=['POST'])
def analyze_photo():
    """Analyze a photo with AI."""
    student = g.current_student
    if not student:
        return jsonify({'error': 'No student'}), 400

    if 'photo' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['photo']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    filepath = save_uploaded_file(file, 'materials')

    try:
        result = ai_service.analyze_photo(filepath, student.grade, student.id)
        return jsonify({'success': True, 'filepath': filepath, 'data': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@ai_tutor_bp.route('/explain/<int:id>/generate', methods=['POST'])
def generate_explanation(id):
    """Generate explanation for a mistake (JSON API)."""
    student = g.current_student
    mistake = Mistake.query.get_or_404(id)

    if mistake.student_id != student.id:
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        explanation = ai_service.explain_problem(
            mistake.question_text,
            mistake.correct_answer,
            student.grade,
            student.id,
            mistake.subject
        )

        # Save explanation to mistake
        mistake.explanation = explanation
        db.session.commit()

        return jsonify({'success': True, 'explanation': explanation})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@ai_tutor_bp.route('/practice/<int:id>/generate', methods=['POST'])
def generate_practice(id):
    """Generate similar problems for a mistake (JSON API)."""
    student = g.current_student
    mistake = Mistake.query.get_or_404(id)

    if mistake.student_id != student.id:
        return jsonify({'error': 'Unauthorized'}), 403

    count = request.form.get('count', 3, type=int)

    try:
        result = ai_service.generate_similar_problems(
            mistake.question_text,
            mistake.correct_answer,
            student.grade,
            count,
            mistake.subject
        )
        return jsonify({'success': True, 'problems': result.get('problems', [])})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@ai_tutor_bp.route('/generate-practice', methods=['POST'])
def generate_practice_by_topic():
    """Generate practice problems by topic (JSON API)."""
    student = g.current_student
    if not student:
        return jsonify({'error': 'No student'}), 400

    data = request.get_json()
    topic = data.get('topic')
    subject = data.get('subject')
    count = data.get('count', 5)

    try:
        result = ai_service.generate_practice_by_topic(topic, subject, student.grade, count)
        return jsonify({'success': True, 'problems': result.get('problems', [])})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@ai_tutor_bp.route('/history')
def history():
    """View AI interaction history."""
    student = g.current_student
    if not student:
        return redirect(url_for('settings.student_profile'))

    interactions = AIInteraction.query.filter_by(student_id=student.id).order_by(
        AIInteraction.created_at.desc()
    ).limit(100).all()

    return render_template('ai_tutor/history.html', interactions=interactions)
