"""Knowledge map service for curriculum structure."""
from app.models.knowledge import KnowledgePoint
from app.extensions import db


class KnowledgeMapService:
    """Service for managing knowledge point hierarchy."""

    @staticmethod
    def get_knowledge_tree(subject=None, grade=None):
        """Get knowledge points as a tree structure."""
        query = KnowledgePoint.query
        if subject:
            query = query.filter_by(subject=subject)
        if grade:
            query = query.filter_by(grade=grade)

        points = query.order_by(KnowledgePoint.grade, KnowledgePoint.semester, KnowledgePoint.sort_order).all()

        # Build tree
        tree = {}
        for point in points:
            key = (point.subject, point.grade, point.semester, point.chapter)
            if key not in tree:
                tree[key] = {
                    'subject': point.subject,
                    'grade': point.grade,
                    'semester': point.semester,
                    'chapter': point.chapter,
                    'topics': []
                }
            tree[key]['topics'].append({
                'id': point.id,
                'topic': point.topic,
                'description': point.description,
                'parent_id': point.parent_id
            })

        return list(tree.values())

    @staticmethod
    def get_by_subject_and_grade(subject, grade):
        """Get knowledge points by subject and grade."""
        return KnowledgePoint.query.filter_by(
            subject=subject,
            grade=grade
        ).order_by(KnowledgePoint.semester, KnowledgePoint.chapter).all()

    @staticmethod
    def get_chapters(subject, grade, semester=None):
        """Get distinct chapters for a subject and grade."""
        query = db.session.query(KnowledgePoint.chapter).filter_by(
            subject=subject,
            grade=grade
        )
        if semester:
            query = query.filter_by(semester=semester)
        return [c[0] for c in query.distinct().all() if c[0]]

    @staticmethod
    def get_topics_by_chapter(subject, grade, chapter):
        """Get topics for a specific chapter."""
        return KnowledgePoint.query.filter_by(
            subject=subject,
            grade=grade,
            chapter=chapter
        ).order_by(KnowledgePoint.topic).all()

    @staticmethod
    def search(query_text, subject=None, grade=None):
        """Search knowledge points."""
        q = KnowledgePoint.query
        if subject:
            q = q.filter_by(subject=subject)
        if grade:
            q = q.filter_by(grade=grade)

        search_filter = db.or_(
            KnowledgePoint.topic.ilike(f'%{query_text}%'),
            KnowledgePoint.chapter.ilike(f'%{query_text}%'),
            KnowledgePoint.description.ilike(f'%{query_text}%')
        )
        return q.filter(search_filter).all()

    @staticmethod
    def get_weak_areas(student_id, top_n=10):
        """Get weak knowledge areas based on student's mistakes."""
        from app.models.mistake import Mistake
        from sqlalchemy import func

        results = db.session.query(
            Mistake.knowledge_point,
            Mistake.subject,
            func.count(Mistake.id).label('mistake_count'),
            func.sum(db.case((Mistake.mastered == True, 1), else_=0)).label('mastered_count')
        ).filter(
            Mistake.student_id == student_id
        ).group_by(
            Mistake.knowledge_point, Mistake.subject
        ).all()

        weak_areas = []
        for r in results:
            unmastered = r.mistake_count - (r.mastered_count or 0)
            priority = unmastered * 3 + r.mistake_count
            weak_areas.append({
                'knowledge_point': r.knowledge_point,
                'subject': r.subject,
                'total_mistakes': r.mistake_count,
                'unmastered_count': unmastered,
                'mastered_count': r.mastered_count or 0,
                'priority': priority
            })

        weak_areas.sort(key=lambda x: x['priority'], reverse=True)
        return weak_areas[:top_n]


knowledge_map_service = KnowledgeMapService()
