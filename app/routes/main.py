"""Main routes - Dashboard and home."""
from flask import Blueprint, render_template, g
from datetime import date

from app.models.homework import Homework
from app.models.mistake import Mistake
from app.models.review_plan import ReviewPlan
from app.models.study_session import StudySession
from app.services.stats_service import stats_service

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Dashboard - main page."""
    student = g.current_student

    if not student:
        return render_template('main/no_student.html')

    # Get dashboard stats
    stats = stats_service.get_dashboard_stats(student.id)

    # Today's homework
    today = date.today()
    today_homework = Homework.query.filter(
        Homework.student_id == student.id,
        Homework.homework_date == today
    ).order_by(Homework.created_at.desc()).all()

    # Due for review
    due_reviews = Mistake.get_due_for_review(student.id, today)

    # Active plans
    active_plans = ReviewPlan.query.filter(
        ReviewPlan.student_id == student.id,
        ReviewPlan.status == 'active'
    ).order_by(ReviewPlan.exam_date).all()

    return render_template('main/index.html',
                         stats=stats,
                         today_homework=today_homework,
                         due_reviews=due_reviews[:5],
                         active_plans=active_plans)
