"""Reports routes - Study reports and analytics."""
from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, g, jsonify

from app.models.student import Student
from app.services.stats_service import stats_service

reports_bp = Blueprint('reports', __name__)


@reports_bp.route('/')
def dashboard():
    """Reports dashboard."""
    student = g.current_student
    if not student:
        return redirect(url_for('settings.student_profile'))

    return render_template('reports/dashboard.html', student=student)


@reports_bp.route('/weak-areas')
def weak_areas():
    """View weak areas detail."""
    student = g.current_student
    if not student:
        return redirect(url_for('settings.student_profile'))

    weak_areas = stats_service.get_weak_areas(student.id, top_n=20)

    return render_template('reports/weak_areas.html', weak_areas=weak_areas, student=student)


@reports_bp.route('/api/study-time')
def api_study_time():
    """Get study time data (JSON)."""
    student = g.current_student
    if not student:
        return jsonify({'error': 'No student'}), 400

    start = request.args.get('start')
    end = request.args.get('end')

    data = stats_service.get_study_time_summary(student.id, start, end)
    return jsonify(data)


@reports_bp.route('/api/mistake-distribution')
def api_mistake_distribution():
    """Get mistake distribution (JSON)."""
    student = g.current_student
    if not student:
        return jsonify({'error': 'No student'}), 400

    start = request.args.get('start')
    end = request.args.get('end')

    data = stats_service.get_mistake_distribution(student.id, start, end)
    return jsonify(data)


@reports_bp.route('/api/subject-comparison')
def api_subject_comparison():
    """Get subject comparison data (JSON)."""
    student = g.current_student
    if not student:
        return jsonify({'error': 'No student'}), 400

    data = stats_service.get_subject_comparison(student.id)
    return jsonify({'subjects': data})


@reports_bp.route('/api/weekly-summary')
def api_weekly_summary():
    """Get weekly summary (JSON)."""
    student = g.current_student
    if not student:
        return jsonify({'error': 'No student'}), 400

    weeks = request.args.get('weeks', 4, type=int)
    data = stats_service.get_weekly_summary(student.id, weeks)
    return jsonify({'weeks': data})
