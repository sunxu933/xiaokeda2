"""Statistics service for generating study reports."""
from datetime import datetime, date, timedelta
from sqlalchemy import func, and_
from app.extensions import db
from app.models.study_session import StudySession
from app.models.mistake import Mistake
from app.models.homework import Homework
from app.models.student import Student


class StatsService:
    """Service for computing study statistics and reports."""

    @staticmethod
    def get_study_time_summary(student_id, start_date=None, end_date=None):
        """Get study time summary by date and subject."""
        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - timedelta(days=30)

        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

        sessions = StudySession.query.filter(
            StudySession.student_id == student_id,
            func.date(StudySession.start_time) >= start_date,
            func.date(StudySession.start_time) <= end_date
        ).all()

        # Group by date and subject
        daily_data = {}
        current = start_date
        while current <= end_date:
            daily_data[current.isoformat()] = {'语文': 0, '数学': 0, '英语': 0, '综合': 0, 'total': 0}
            current += timedelta(days=1)

        for session in sessions:
            day_key = session.start_time.date().isoformat()
            subject = session.subject or '综合'
            if day_key in daily_data:
                daily_data[day_key][subject] = daily_data[day_key].get(subject, 0) + session.duration_minutes
                daily_data[day_key]['total'] += session.duration_minutes

        return {
            'daily_data': daily_data,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        }

    @staticmethod
    def get_mistake_distribution(student_id, start_date=None, end_date=None):
        """Get mistake distribution by subject, difficulty, and topic."""
        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - timedelta(days=30)

        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

        mistakes = Mistake.query.filter(
            Mistake.student_id == student_id,
            func.date(Mistake.created_at) >= start_date,
            func.date(Mistake.created_at) <= end_date
        ).all()

        by_subject = {'语文': 0, '数学': 0, '英语': 0}
        by_difficulty = {'easy': 0, 'medium': 0, 'hard': 0}
        by_topic = {}
        total = len(mistakes)
        mastered = sum(1 for m in mistakes if m.mastered)

        for m in mistakes:
            if m.subject in by_subject:
                by_subject[m.subject] += 1
            if m.difficulty in by_difficulty:
                by_difficulty[m.difficulty] += 1
            topic_key = m.topic or '未分类'
            by_topic[topic_key] = by_topic.get(topic_key, 0) + 1

        return {
            'total': total,
            'mastered': mastered,
            'unmastered': total - mastered,
            'mastery_rate': round(mastered / total * 100, 1) if total > 0 else 0,
            'by_subject': by_subject,
            'by_difficulty': by_difficulty,
            'by_topic': by_topic
        }

    @staticmethod
    def get_weak_areas(student_id, top_n=10):
        """Get top weak areas by priority."""
        results = db.session.query(
            Mistake.subject,
            Mistake.topic,
            func.count(Mistake.id).label('total'),
            func.sum(db.case((Mistake.mastered == True, 1), else_=0)).label('mastered')
        ).filter(
            Mistake.student_id == student_id,
            Mistake.mastered == False
        ).group_by(
            Mistake.subject, Mistake.topic
        ).all()

        weak_areas = []
        for r in results:
            unmastered = r.total - (r.mastered or 0)
            priority = unmastered * 3 + r.total
            weak_areas.append({
                'subject': r.subject,
                'topic': r.topic or '未分类',
                'total_mistakes': r.total,
                'unmastered': unmastered,
                'mastered': r.mastered or 0,
                'priority': priority
            })

        weak_areas.sort(key=lambda x: x['priority'], reverse=True)
        return weak_areas[:top_n]

    @staticmethod
    def get_subject_comparison(student_id):
        """Get subject comparison metrics."""
        student = db.session.get(Student, student_id)
        if not student:
            return None

        comparison = []
        for subject in ['语文', '数学', '英语']:
            # Mistake stats
            total_mistakes = Mistake.query.filter_by(student_id=student_id, subject=subject).count()
            mastered_mistakes = Mistake.query.filter_by(student_id=student_id, subject=subject, mastered=True).count()

            # Homework stats
            homeworks = Homework.query.filter_by(student_id=student_id, subject=subject).all()
            total_homework = len(homeworks)
            completed_homework = sum(1 for h in homeworks if h.status == 'completed')

            # Study time (last 30 days)
            thirty_days_ago = date.today() - timedelta(days=30)
            study_time = db.session.query(func.sum(StudySession.duration)).filter(
                StudySession.student_id == student_id,
                StudySession.subject == subject,
                func.date(StudySession.start_time) >= thirty_days_ago
            ).scalar() or 0

            completion_rate = round(completed_homework / total_homework * 100, 1) if total_homework > 0 else 0
            mastery_rate = round(mastered_mistakes / total_mistakes * 100, 1) if total_mistakes > 0 else 0

            comparison.append({
                'subject': subject,
                'mistake_count': total_mistakes,
                'mastery_rate': mastery_rate,
                'homework_count': total_homework,
                'completion_rate': completion_rate,
                'study_time_30d': study_time
            })

        return comparison

    @staticmethod
    def get_weekly_summary(student_id, weeks=4):
        """Get weekly summary for the last N weeks."""
        today = date.today()
        summaries = []

        for week in range(weeks):
            # Find Monday of the week
            days_since_monday = today.weekday()
            week_start = today - timedelta(days=days_since_monday + week * 7)
            week_end = week_start + timedelta(days=6)

            # Mistakes this week
            mistake_count = Mistake.query.filter(
                Mistake.student_id == student_id,
                func.date(Mistake.created_at) >= week_start,
                func.date(Mistake.created_at) <= week_end
            ).count()

            # Study time this week
            study_minutes = db.session.query(func.sum(StudySession.duration)).filter(
                StudySession.student_id == student_id,
                func.date(StudySession.start_time) >= week_start,
                func.date(StudySession.start_time) <= week_end
            ).scalar() or 0

            # Homework count
            homework_count = Homework.query.filter(
                Homework.student_id == student_id,
                func.date(Homework.homework_date) >= week_start,
                func.date(Homework.homework_date) <= week_end
            ).count()

            summaries.append({
                'week_start': week_start.isoformat(),
                'week_end': week_end.isoformat(),
                'mistake_count': mistake_count,
                'study_minutes': study_minutes,
                'homework_count': homework_count
            })

        return summaries

    @staticmethod
    def get_dashboard_stats(student_id):
        """Get quick stats for dashboard."""
        today = date.today()

        # Today's homework
        today_homework = Homework.query.filter(
            Homework.student_id == student_id,
            func.date(Homework.homework_date) == today
        ).count()

        # Due for review
        due_reviews = Mistake.get_due_for_review(student_id, today)

        # In-progress review plans
        from app.models.review_plan import ReviewPlan
        active_plans = ReviewPlan.query.filter(
            ReviewPlan.student_id == student_id,
            ReviewPlan.status == 'active'
        ).count()

        # Total unmastered mistakes
        unmastered = Mistake.query.filter(
            Mistake.student_id == student_id,
            Mistake.mastered == False
        ).count()

        # Study time today
        study_time_today = db.session.query(func.sum(StudySession.duration)).filter(
            StudySession.student_id == student_id,
            func.date(StudySession.start_time) == today
        ).scalar() or 0

        return {
            'today_homework': today_homework,
            'due_reviews': len(due_reviews),
            'active_plans': active_plans,
            'unmastered_mistakes': unmastered,
            'study_time_today': study_time_today
        }


stats_service = StatsService()
