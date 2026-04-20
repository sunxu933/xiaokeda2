"""Review engine for creating and managing study review plans."""
from datetime import datetime, date, timedelta, timezone
from collections import defaultdict
from app.models.mistake import Mistake
from app.models.review_plan import ReviewPlan, ReviewTask
from app.models.student import Student
from app.extensions import db


class ReviewEngine:
    """Engine for generating and managing review plans."""

    @staticmethod
    def auto_generate_plan(student_id, title, exam_date, subject=None):
        """Auto-generate a review plan based on student's mistakes."""
        student = db.session.get(Student, student_id)
        if not student:
            raise ValueError("Student not found")

        if isinstance(exam_date, str):
            exam_date = datetime.strptime(exam_date, '%Y-%m-%d').date()

        today = date.today()
        days_until_exam = (exam_date - today).days

        if days_until_exam < 3:
            raise ValueError("考试日期距今至少需要3天")

        # Reserve last 2 days for mock tests
        study_days = days_until_exam - 2
        if study_days < 1:
            raise ValueError("复习时间不足")

        # Get unmastered mistakes
        unmastered = Mistake.query.filter(
            Mistake.student_id == student_id,
            Mistake.mastered == False
        ).all()

        # Group by subject|topic
        topic_groups = defaultdict(list)
        for m in unmastered:
            key = f"{m.subject}|{m.topic or '综合'}"
            topic_groups[key].append(m)

        # Calculate priority for each topic
        topic_priorities = []
        for key, mistakes in topic_groups.items():
            subject_name, topic = key.split('|', 1)
            priority = len(mistakes) * 3
            if subject and subject != subject_name:
                continue
            topic_priorities.append({
                'subject': subject_name,
                'topic': topic,
                'mistakes': mistakes,
                'priority': priority
            })

        topic_priorities.sort(key=lambda x: x['priority'], reverse=True)

        # Create plan
        plan = ReviewPlan(
            student_id=student_id,
            title=title,
            subject=subject,
            exam_date=exam_date,
            start_date=today,
            end_date=exam_date - timedelta(days=2),
            status='active',
            ai_generated=True
        )
        db.session.add(plan)
        db.session.flush()

        # Distribute tasks across days
        tasks = []
        current_day = 0
        topic_idx = 0

        mid_point = study_days // 2

        for day in range(study_days):
            scheduled_date = today + timedelta(days=day)

            # First half: review mistakes
            if day < mid_point and topic_idx < len(topic_priorities):
                topic_data = topic_priorities[topic_idx]
                mistake_ids = [m.id for m in topic_data['mistakes'][:5]]  # Max 5 per topic

                task = ReviewTask(
                    plan_id=plan.id,
                    day_number=day + 1,
                    scheduled_date=scheduled_date,
                    subject=topic_data['subject'],
                    topic=topic_data['topic'],
                    task_type='review_mistakes',
                    description=f"复习{topic_data['topic']}相关错题",
                    knowledge_point=topic_data['topic'],
                    mistake_ids=str(mistake_ids),
                    status='pending'
                )
                tasks.append(task)
                topic_idx += 1

                # Add practice task if enough topics
                if topic_idx < len(topic_priorities) and day < mid_point - 1:
                    next_topic = topic_priorities[topic_idx]
                    practice_task = ReviewTask(
                        plan_id=plan.id,
                        day_number=day + 1,
                        scheduled_date=scheduled_date,
                        subject=next_topic['subject'],
                        topic=next_topic['topic'],
                        task_type='practice',
                        description=f"练习{next_topic['topic']}相关题目",
                        knowledge_point=next_topic['topic'],
                        status='pending'
                    )
                    tasks.append(practice_task)
                    topic_idx += 1

            # Second half: comprehensive review or remaining topics
            elif topic_idx < len(topic_priorities):
                topic_data = topic_priorities[topic_idx]
                task = ReviewTask(
                    plan_id=plan.id,
                    day_number=day + 1,
                    scheduled_date=scheduled_date,
                    subject=topic_data['subject'],
                    topic=topic_data['topic'],
                    task_type='review_mistakes',
                    description=f"综合复习{topic_data['topic']}",
                    knowledge_point=topic_data['topic'],
                    status='pending'
                )
                tasks.append(task)
                topic_idx += 1
            else:
                # Free review day
                task = ReviewTask(
                    plan_id=plan.id,
                    day_number=day + 1,
                    scheduled_date=scheduled_date,
                    subject=subject or '综合',
                    topic='综合复习',
                    task_type='knowledge_review',
                    description='自由复习',
                    status='pending'
                )
                tasks.append(task)

        # Add mock test tasks for last 2 days
        for i in range(2):
            mock_date = exam_date - timedelta(days=1 - i)
            task = ReviewTask(
                plan_id=plan.id,
                day_number=study_days + i + 1,
                scheduled_date=mock_date,
                subject=subject or '综合',
                topic='模拟测试',
                task_type='mock_test',
                description=f'模拟测试（第{i + 1}套）',
                status='pending'
            )
            tasks.append(task)

        # Add all tasks
        for task in tasks:
            db.session.add(task)

        # Update plan totals
        plan.total_tasks = len(tasks)

        # If no mistakes, generate knowledge review plan
        if not unmastered:
            ReviewEngine._generate_knowledge_review_plan(plan, student, today, study_days, subject)

        db.session.commit()
        return plan

    @staticmethod
    def _generate_knowledge_review_plan(plan, student, start_date, days, subject=None):
        """Generate a knowledge-based review plan when there are no mistakes."""
        from app.models.knowledge import KnowledgePoint

        query = KnowledgePoint.query.filter_by(grade=student.grade)
        if subject:
            query = query.filter_by(subject=subject)

        topics = query.all()
        topics_per_day = max(1, len(topics) // days)

        current_topic_idx = 0
        for day in range(days):
            scheduled_date = start_date + timedelta(days=day)
            daily_topics = topics[current_topic_idx:current_topic_idx + topics_per_day]

            if not daily_topics:
                continue

            topic_names = ', '.join([t.topic for t in daily_topics])
            task = ReviewTask(
                plan_id=plan.id,
                day_number=day + 1,
                scheduled_date=scheduled_date,
                subject=daily_topics[0].subject if daily_topics else subject,
                topic='知识点复习',
                task_type='knowledge_review',
                description=f"复习章节：{topic_names}",
                status='pending'
            )
            db.session.add(task)
            current_topic_idx += topics_per_day

    @staticmethod
    def complete_task(task_id, time_spent=None):
        """Mark a task as completed."""
        task = db.session.get(ReviewTask, task_id)
        if not task:
            raise ValueError("Task not found")

        task.status = 'completed'
        task.completed_at = datetime.now(timezone.utc)
        if time_spent:
            task.time_spent = time_spent

        # Update plan progress
        plan = task.plan
        completed = ReviewTask.query.filter_by(plan_id=plan.id, status='completed').count()
        plan.completed_tasks = completed

        if completed >= plan.total_tasks:
            plan.status = 'completed'

        db.session.commit()
        return task

    @staticmethod
    def skip_task(task_id):
        """Skip a task."""
        task = db.session.get(ReviewTask, task_id)
        if not task:
            raise ValueError("Task not found")

        task.status = 'skipped'
        db.session.commit()
        return task

    @staticmethod
    def get_due_reviews(student_id, as_of_date=None):
        """Get all review tasks due for today."""
        if as_of_date is None:
            as_of_date = date.today()

        return ReviewTask.query.join(ReviewPlan).filter(
            ReviewPlan.student_id == student_id,
            ReviewTask.scheduled_date <= as_of_date,
            ReviewTask.status == 'pending'
        ).order_by(ReviewTask.scheduled_date).all()


review_engine = ReviewEngine()
