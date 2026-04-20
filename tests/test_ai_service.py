"""Tests for AI service."""
import pytest
from unittest.mock import patch, MagicMock


class TestAIService:
    """Tests for AI service functionality."""

    def test_analyze_photo_returns_json(self, app):
        """Test that analyze_photo returns properly structured JSON."""
        with app.app_context():
            from app.services.ai_service import AIService

            service = AIService()

            # Mock the _call_vision method
            mock_response = '''{
                "questions": [
                    {
                        "content": "1+1=?",
                        "answer": "2",
                        "question_type": "calculation",
                        "knowledge_point": "加法",
                        "difficulty": "easy"
                    }
                ]
            }'''

            with patch.object(service, '_call_vision', return_value=(mock_response, 100, 50)):
                result = service.analyze_photo('test.jpg', 3)

            assert 'questions' in result
            assert len(result['questions']) == 1

    def test_explain_problem_returns_text(self, app):
        """Test that explain_problem returns text explanation."""
        with app.app_context():
            from app.services.ai_service import AIService

            service = AIService()

            mock_response = "这是解题思路..."

            with patch.object(service, '_call_text', return_value=(mock_response, 100, 50)):
                result = service.explain_problem(
                    question_text="1+1=?",
                    correct_answer="2",
                    grade=3,
                    subject="数学"
                )

            assert result == mock_response
            assert len(result) > 0

    def test_generate_similar_problems(self, app):
        """Test that generate_similar_problems returns JSON."""
        with app.app_context():
            from app.services.ai_service import AIService

            service = AIService()

            mock_response = '''{
                "problems": [
                    {
                        "question": "2+2=?",
                        "answer": "4",
                        "explanation": "加法",
                        "difficulty": "easy",
                        "knowledge_point": "加法"
                    }
                ]
            }'''

            with patch.object(service, '_call_text', return_value=(mock_response, 100, 50)):
                result = service.generate_similar_problems(
                    question_text="1+1=?",
                    correct_answer="2",
                    grade=3,
                    count=3,
                    subject="数学"
                )

            assert 'problems' in result
            assert len(result['problems']) >= 1

    def test_lazy_initialization(self, app):
        """Test that AIService initializes settings lazily."""
        with app.app_context():
            from app.services.ai_service import AIService

            # Create service without settings loaded
            service = AIService()

            # Settings should be None initially
            assert service.endpoint is None
            assert service.api_key is None
            assert service._settings_loaded is False

            # Load settings
            service._load_settings()

            # Settings should now be loaded
            assert service._settings_loaded is True

    def test_is_minimax_endpoint(self, app):
        """Test minimax endpoint detection."""
        with app.app_context():
            from app.services.ai_service import AIService

            service = AIService()
            service._load_settings()

            # Should detect minimax
            assert service._is_minimax_endpoint() == ('minimaxi.com' in service.endpoint or 'minimax.io' in service.endpoint)
