"""
tests/test_ai_performance_analysis.py
-------------------------------------
Unit and integration tests for AI-Powered Student Performance Analysis.

Test Cases:
    1. Test Python deterministic performance metrics & topic breakdown aggregation.
    2. Test AIService.analyze_performance receiving sanitized metrics and returning structured insights.
    3. Test saving and retrieving AI analysis records to/from SQLite 'ai_analysis' table.
    4. Test offline/error fallback behavior producing objective feedback without crashing.
    5. Test PerformanceScreen GUI integration with AI Analysis card and action triggers.
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.database import DatabaseManager
from gui.app import App
from gui.performance import PerformanceScreen
from services.ai_service import AIService
from services.authentication import AuthenticationService
from services.quiz_service import QuizService
from services.result_service import ResultService


class TestAIPerformanceAnalysis(unittest.TestCase):
    """
    Test suite for AI Performance Analysis, database persistence, and UI integration.
    """

    def setUp(self):
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        self.db_mgr = DatabaseManager(db_path=self.temp_db_path)
        self.db_mgr.initialize_database()

        self.auth_service = AuthenticationService(db_mgr=self.db_mgr)
        self.quiz_service = QuizService(db_mgr=self.db_mgr)
        self.result_service = ResultService(db_mgr=self.db_mgr)

        self.app = App(auth_service=self.auth_service)
        self.app.withdraw()

        # Register Student & Add Sample Questions
        reg = self.auth_service.register_user("Perf Student", "perf_user", "perf@example.com", "StudentPass123!", "student")
        self.user_id = reg["user"].id
        self.auth_service.login_user("perf_user", "StudentPass123!")

        q1 = self.quiz_service.add_question("Python", "Variables", "easy", "Q1 text", "A", "B", "C", "D", "A", "Exp1")
        q2 = self.quiz_service.add_question("Python", "OOP", "medium", "Q2 text", "A", "B", "C", "D", "B", "Exp2")

        # Submit attempt
        questions = [self.quiz_service.get_question_by_id(q1["question_id"]), self.quiz_service.get_question_by_id(q2["question_id"])]
        sub = self.quiz_service.submit_quiz_attempt(
            user_id=self.user_id,
            quiz_config={"category": "Python", "difficulty": "medium", "topic": "General"},
            questions=questions,
            user_answers={q1["question_id"]: "A", q2["question_id"]: "A"},  # Q1 correct, Q2 wrong
            time_taken=20
        )
        self.result_id = sub["result_id"]

    def tearDown(self):
        self.app.destroy()
        os.close(self.temp_db_fd)
        if os.path.exists(self.temp_db_path):
            os.remove(self.temp_db_path)

    def test_topic_breakdown_aggregation(self):
        """Verify deterministic calculation of topic accuracy from SQLite attempt records."""
        topics = self.result_service.get_topic_performance_breakdown(self.user_id)
        self.assertIn("Variables", topics)
        self.assertIn("OOP", topics)
        self.assertEqual(topics["Variables"]["accuracy"], 100.0)
        self.assertEqual(topics["OOP"]["accuracy"], 0.0)

    def test_ai_service_analyze_performance_mocked(self):
        """Verify AIService processes performance stats and returns objective analysis."""
        ai_service = AIService(api_key="mock_key")
        ai_service._call_gemini = MagicMock(return_value='''{
            "summary": "Solid grasp in Variables, needs improvement in OOP.",
            "strengths": ["Python Variables", "Data Types"],
            "weak_topics": ["OOP", "Exception Handling"],
            "revision_topics": ["OOP Encapsulation"],
            "difficulty_recommendation": "medium",
            "recommendations": ["Practice medium-level OOP questions before attempting hard questions."]
        }''')

        perf = self.result_service.get_student_performance_analytics(self.user_id)
        res = ai_service.analyze_performance(perf)

        self.assertTrue(res["success"])
        self.assertEqual(res["strengths"], ["Python Variables", "Data Types"])
        self.assertEqual(res["weak_topics"], ["OOP", "Exception Handling"])
        self.assertEqual(res["difficulty_recommendation"], "medium")
        self.assertIn("Practice medium-level OOP", res["recommendations"][0])

    def test_save_and_retrieve_ai_analysis_sqlite(self):
        """Verify saving AI analysis to ai_analysis table and retrieving latest record."""
        mock_analysis = {
            "summary": "Objective analysis summary.",
            "strengths": ["Variables"],
            "weak_topics": ["OOP"],
            "revision_topics": ["OOP Methods"],
            "difficulty_recommendation": "medium",
            "recommendations": ["Review OOP notes."]
        }

        analysis_id = self.result_service.save_ai_analysis(self.user_id, mock_analysis, result_id=self.result_id)
        self.assertIsNotNone(analysis_id)

        latest = self.result_service.get_latest_ai_analysis(self.user_id)
        self.assertIsNotNone(latest)
        self.assertEqual(latest["strengths"], ["Variables"])
        self.assertEqual(latest["weak_topics"], ["OOP"])
        self.assertEqual(latest["difficulty_recommendation"], "medium")

    def test_offline_fallback_analysis(self):
        """Verify objective fallback when API is unconfigured."""
        ai_service = AIService(api_key=None)
        res = self.result_service.generate_and_save_ai_analysis(self.user_id, ai_service=ai_service)

        self.assertFalse(res["success"])
        self.assertIn("Python", res["strengths"][0])
        self.assertIsNotNone(res.get("analysis_id"))

    def test_performance_screen_ai_card_rendering(self):
        """Verify PerformanceScreen initializes AI analysis card and trigger button."""
        screen = PerformanceScreen(self.app.container, self.app)
        self.assertIsNotNone(screen.btn_gen_ai)

        # Trigger AI analysis generation
        screen._on_generate_ai_analysis()
        self.assertEqual(screen.btn_gen_ai["text"], "⚡ REFRESH AI ANALYSIS")


if __name__ == "__main__":
    unittest.main()
