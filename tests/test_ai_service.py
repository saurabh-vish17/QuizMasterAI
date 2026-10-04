"""
tests/test_ai_service.py
-------------------------
Unit and isolation tests for AIService in QuizMaster AI.

Test Cases:
    1. Test environment variable loading (python-dotenv & GEMINI_API_KEY).
    2. Test AIService fallback mode when API key is missing or blank.
    3. Test mocked generate_questions returning valid structured schema.
    4. Test mocked explain_answer rationale.
    5. Test mocked analyze_performance producing summary, strengths, and recommendations.
    6. Test mocked recommend_difficulty mapping scores to difficulty levels.
    7. Test mocked generate_study_plan producing 7-day plan.
    8. Test mocked chat_with_student response.
    9. Test timeout and exception handling (API failure never crashes application).
    10. Test JSON cleaning and schema validation helper.
"""

import os
import unittest
from unittest.mock import MagicMock, patch

from services.ai_service import AIService


class TestAIService(unittest.TestCase):
    """
    Test suite for AIService API abstraction, timeout handling, and fallback resilience.
    """

    def setUp(self):
        """Initialize AIService instance in offline/mock mode."""
        self.ai_service = AIService(api_key=None)

    def test_environment_configuration_reading(self):
        """Verify AIService reads configuration parameters from environment variables."""
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test_env_key_123", "GEMINI_MODEL": "gemini-2.5-flash", "AI_REQUEST_TIMEOUT": "20"}):
            service = AIService()
            self.assertEqual(service.api_key, "test_env_key_123")
            self.assertEqual(service.model_name, "gemini-2.5-flash")
            self.assertEqual(service.timeout, 20)

    def test_unconfigured_fallback_mode(self):
        """Verify AIService operates safely in fallback mode when API key is unconfigured."""
        service = AIService(api_key="")
        self.assertFalse(service.is_configured)

        # generate_questions should return fallback questions without throwing exception
        res = service.generate_questions("Basics", "Python", "easy", 3)
        self.assertFalse(res["success"])
        self.assertEqual(len(res["questions"]), 3)
        self.assertIn("Offline Practice", res["questions"][0]["question_text"])

    def test_json_extraction_and_validation(self):
        """Test cleaning markdown code fences and JSON parsing helper."""
        raw_markdown = """
```json
{
    "summary": "Good performance overall",
    "strengths": ["Python"],
    "weak_topics": ["DBMS"],
    "recommendations": ["Practice SQL"]
}
```
        """
        parsed = self.ai_service._extract_and_validate_json(raw_markdown)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["summary"], "Good performance overall")
        self.assertEqual(parsed["strengths"], ["Python"])

    @patch.object(AIService, "_call_gemini")
    def test_mocked_generate_questions(self, mock_gemini):
        """Test generate_questions with mocked Gemini JSON output."""
        mock_gemini.return_value = """
[
    {
        "question_text": "What is GIL in Python?",
        "option_a": "Global Interpreter Lock",
        "option_b": "General Interface Logic",
        "option_c": "Global Instance Level",
        "option_d": "Graph Inspection Library",
        "correct_answer": "A",
        "explanation": "GIL stands for Global Interpreter Lock."
    }
]
        """
        service = AIService(api_key="mock_key")
        service.is_configured = True

        res = service.generate_questions("Threading", "Python", "hard", 1)
        self.assertTrue(res["success"])
        self.assertEqual(len(res["questions"]), 1)
        self.assertEqual(res["questions"][0]["question_text"], "What is GIL in Python?")
        self.assertEqual(res["questions"][0]["correct_answer"], "A")

    @patch.object(AIService, "_call_gemini")
    def test_mocked_explain_answer(self, mock_gemini):
        """Test explain_answer with mocked Gemini JSON output."""
        mock_gemini.return_value = """
{
    "explanation": "Tuple is immutable whereas list is mutable.",
    "key_concept": "Immutability",
    "is_correct": true
}
        """
        service = AIService(api_key="mock_key")
        service.is_configured = True

        res = service.explain_answer("Difference between tuple and list?", "A", "A", {"A": "Tuple immutable", "B": "List immutable"})
        self.assertTrue(res["success"])
        self.assertEqual(res["key_concept"], "Immutability")
        self.assertTrue(res["is_correct"])

    @patch.object(AIService, "_call_gemini")
    def test_mocked_analyze_performance(self, mock_gemini):
        """Test analyze_performance with mocked Gemini JSON response."""
        mock_gemini.return_value = """
{
    "summary": "Strong in Python, needs practice in Computer Networks.",
    "strengths": ["Python Basics", "OOP"],
    "weak_topics": ["OSI Model", "TCP/IP"],
    "recommendations": ["Study OSI layers"]
}
        """
        service = AIService(api_key="mock_key")
        service.is_configured = True

        perf = {"average_score": 75.0, "total_quizzes": 5, "strongest_category": "Python", "weakest_category": "Computer Networks"}
        res = service.analyze_performance(perf)
        self.assertTrue(res["success"])
        self.assertEqual(len(res["strengths"]), 2)
        self.assertIn("OSI Model", res["weak_topics"])

    @patch.object(AIService, "_call_gemini")
    def test_mocked_recommend_difficulty(self, mock_gemini):
        """Test recommend_difficulty with mocked response."""
        mock_gemini.return_value = """
{
    "recommended_difficulty": "hard",
    "reason": "Student achieved 90% average score.",
    "target_score": 85.0
}
        """
        service = AIService(api_key="mock_key")
        service.is_configured = True

        res = service.recommend_difficulty({"average_score": 90.0})
        self.assertTrue(res["success"])
        self.assertEqual(res["recommended_difficulty"], "hard")

    @patch.object(AIService, "_call_gemini")
    def test_mocked_generate_study_plan(self, mock_gemini):
        """Test generate_study_plan with mocked 7-day JSON plan."""
        mock_gemini.return_value = """
{
    "title": "7-Day DBMS Mastery Plan",
    "duration_days": 7,
    "study_plan": [
        {"day": 1, "topic": "Normalization", "focus": "1NF & 2NF", "activities": ["Read notes", "Solve 5 Qs"]}
    ]
}
        """
        service = AIService(api_key="mock_key")
        service.is_configured = True

        res = service.generate_study_plan({"weakest_category": "DBMS"})
        self.assertTrue(res["success"])
        self.assertEqual(res["title"], "7-Day DBMS Mastery Plan")
        self.assertEqual(len(res["study_plan"]), 1)

    @patch.object(AIService, "_call_gemini")
    def test_mocked_chat_with_student(self, mock_gemini):
        """Test chat_with_student response."""
        mock_gemini.return_value = """
{
    "response": "Recursion is a function calling itself until a base condition is met.",
    "suggested_followups": ["What is a base case?", "Stack overflow error in recursion?"]
}
        """
        service = AIService(api_key="mock_key")
        service.is_configured = True

        res = service.chat_with_student("What is recursion?")
        self.assertTrue(res["success"])
        self.assertIn("Recursion is a function", res["response"])
        self.assertEqual(len(res["suggested_followups"]), 2)

    @patch.object(AIService, "_call_gemini", side_effect=Exception("API Connection Refused"))
    def test_exception_handling_resilience(self, mock_gemini):
        """Verify API exception never crashes application and returns graceful fallback."""
        service = AIService(api_key="mock_key")
        service.is_configured = True

        res = service.generate_questions("Trees", "Java", "medium", 2)
        self.assertFalse(res["success"])
        self.assertEqual(len(res["questions"]), 2)
        self.assertIn("AI service unavailable", res["message"])

    @patch.object(AIService, "_call_gemini", return_value=None)
    def test_timeout_handling(self, mock_gemini):
        """Verify AIService handles timeouts gracefully when Gemini return is None."""
        service = AIService(api_key="mock_key", timeout=1)
        service.is_configured = True

        res = service.generate_questions("Graphs", "C++", "hard", 2)
        self.assertFalse(res["success"])
        self.assertEqual(len(res["questions"]), 2)

    @patch.object(AIService, "_call_gemini", return_value="INVALID_NOT_JSON_CONTENT")
    def test_malformed_json_response(self, mock_gemini):
        """Verify AIService handles malformed non-JSON Gemini responses gracefully."""
        service = AIService(api_key="mock_key")
        service.is_configured = True

        res = service.generate_questions("Recursion", "Python", "easy", 2)
        self.assertFalse(res["success"])
        self.assertEqual(len(res["questions"]), 2)



if __name__ == "__main__":
    unittest.main()
