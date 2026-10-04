"""
tests/test_adaptive_quiz_engine.py
-----------------------------------
Unit and integration tests for the Adaptive AI Quiz Engine in QuizMaster AI.

Test Cases:
    1. Test Python deterministic statistics calculation (recent accuracy, topic accuracy, attempts).
    2. Test recommendation logic for high accuracy (>= 80% triggers level upgrade).
    3. Test recommendation logic for low accuracy (<= 50% triggers level downgrade).
    4. Test AIService.recommend_difficulty schema compliance (Current Level, Recommended Level, Reason, Weak Topics, Recommended Practice).
    5. Test manual difficulty override by student in QuizSelectionScreen.
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.database import DatabaseManager
from gui.app import App
from gui.quiz_selection import QuizSelectionScreen
from services.ai_service import AIService
from services.authentication import AuthenticationService
from services.quiz_service import QuizService


class TestAdaptiveQuizEngine(unittest.TestCase):
    """
    Test suite for Adaptive AI Difficulty Recommendation Engine and manual override behavior.
    """

    def setUp(self):
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        self.db_mgr = DatabaseManager(db_path=self.temp_db_path)
        self.db_mgr.initialize_database()

        self.auth_service = AuthenticationService(db_mgr=self.db_mgr)
        self.quiz_service = QuizService(db_mgr=self.db_mgr)

        self.app = App(auth_service=self.auth_service)
        self.app.withdraw()

        # Register Student
        reg = self.auth_service.register_user("Adapt Student", "adapt_user", "adapt@example.com", "StudentPass123!", "student")
        self.user_id = reg["user"].id
        self.auth_service.login_user("adapt_user", "StudentPass123!")

        # Add questions in Easy and Medium
        q1 = self.quiz_service.add_question("Python", "OOP", "easy", "Q1 text", "A", "B", "C", "D", "A", "Exp1")
        q2 = self.quiz_service.add_question("Python", "Variables", "medium", "Q2 text", "A", "B", "C", "D", "B", "Exp2")
        self.q1_id = q1["question_id"]
        self.q2_id = q2["question_id"]

    def tearDown(self):
        self.app.destroy()
        os.close(self.temp_db_fd)
        if os.path.exists(self.temp_db_path):
            os.remove(self.temp_db_path)

    def test_deterministic_statistics_calculation(self):
        """Verify Python calculates deterministic statistics from SQLite quiz history."""
        questions = [self.quiz_service.get_question_by_id(self.q1_id)]
        self.quiz_service.submit_quiz_attempt(
            user_id=self.user_id,
            quiz_config={"category": "Python", "difficulty": "easy", "topic": "OOP"},
            questions=questions,
            user_answers={self.q1_id: "A"},  # 100% score
            time_taken=10
        )

        rec = self.quiz_service.get_adaptive_difficulty_recommendation(
            user_id=self.user_id,
            category="Python",
            current_difficulty="easy"
        )

        self.assertEqual(rec["deterministic_metrics"]["recent_accuracy"], 100.0)
        self.assertEqual(rec["deterministic_metrics"]["number_of_attempts"], 1)

    def test_level_upgrade_recommendation(self):
        """Verify high accuracy (>= 80%) recommends upgrading difficulty level."""
        questions = [self.quiz_service.get_question_by_id(self.q1_id)]
        self.quiz_service.submit_quiz_attempt(
            user_id=self.user_id,
            quiz_config={"category": "Python", "difficulty": "easy", "topic": "OOP"},
            questions=questions,
            user_answers={self.q1_id: "A"},  # 100% correct
            time_taken=10
        )

        ai_service = AIService(api_key=None)  # Rule-based offline mode
        rec = self.quiz_service.get_adaptive_difficulty_recommendation(
            user_id=self.user_id,
            category="Python",
            current_difficulty="easy",
            ai_service=ai_service
        )

        self.assertEqual(rec["current_level"], "Easy")
        self.assertEqual(rec["recommended_level"], "Medium")
        self.assertIn("Recent accuracy is 100%", rec["reason"])

    def test_level_downgrade_recommendation(self):
        """Verify low accuracy (<= 50%) recommends downgrading difficulty level."""
        questions = [self.quiz_service.get_question_by_id(self.q2_id)]
        self.quiz_service.submit_quiz_attempt(
            user_id=self.user_id,
            quiz_config={"category": "Python", "difficulty": "hard", "topic": "Variables"},
            questions=questions,
            user_answers={self.q2_id: "C"},  # 0% correct (wrong)
            time_taken=10
        )

        ai_service = AIService(api_key=None)
        rec = self.quiz_service.get_adaptive_difficulty_recommendation(
            user_id=self.user_id,
            category="Python",
            current_difficulty="hard",
            ai_service=ai_service
        )

        self.assertEqual(rec["current_level"], "Hard")
        self.assertEqual(rec["recommended_level"], "Medium")
        self.assertIn("Recent accuracy is 0%", rec["reason"])

    def test_ai_service_recommendation_schema(self):
        """Verify AIService output contains all required recommendation fields."""
        ai_service = AIService(api_key="mock_key")
        ai_service._call_gemini = MagicMock(return_value='''{
            "current_level": "medium",
            "recommended_level": "medium",
            "reason": "Recent accuracy is 68%, with lower performance in OOP.",
            "weak_topics": ["OOP", "Exception Handling"],
            "recommended_practice": "Practice medium-level OOP questions before attempting hard questions."
        }''')

        rec = ai_service.recommend_difficulty({
            "current_level": "medium",
            "recent_accuracy": 68.0,
            "number_of_attempts": 3,
            "weak_topics": ["OOP", "Exception Handling"]
        })

        self.assertTrue(rec["success"])
        self.assertEqual(rec["current_level"], "Medium")
        self.assertEqual(rec["recommended_level"], "Medium")
        self.assertEqual(rec["reason"], "Recent accuracy is 68%, with lower performance in OOP.")
        self.assertEqual(rec["weak_topics"], ["OOP", "Exception Handling"])
        self.assertIn("Practice medium-level OOP", rec["recommended_practice"])

    def test_quiz_selection_manual_override(self):
        """Verify student can apply AI recommendation OR manually override difficulty."""
        screen = QuizSelectionScreen(self.app.container, self.app)

        # Mock AI recommendation recommending "Hard"
        screen.latest_recommendation = {
            "current_level": "Medium",
            "recommended_level": "Hard",
            "reason": "High score",
            "weak_topics": [],
            "recommended_practice": ""
        }

        # Click Apply AI Recommendation
        screen._apply_ai_recommendation()
        self.assertEqual(screen.cmb_difficulty.get(), "Hard")

        # Manual override by student back to "Easy"
        screen.cmb_difficulty.set("Easy")
        self.assertEqual(screen.cmb_difficulty.get(), "Easy")


if __name__ == "__main__":
    unittest.main()
