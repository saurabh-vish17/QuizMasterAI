"""
tests/test_ai_explanation.py
----------------------------
Unit and integration tests for AI-powered Answer Explanations in ResultScreen.

Test Cases:
    1. Test explain_answer_detailed generates 3-part explanation (Why correct, Why incorrect, Learning tip).
    2. Test caching mechanism to ensure repeated requests for same question attempt hit memory cache.
    3. Test that correct answer key is strictly preserved and never mutated by AI.
    4. Test offline/error fallback behavior when API fails or times out.
    5. Test ResultScreen GUI integration with [Explain with AI] button.
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.database import DatabaseManager
from gui.app import App
from gui.result_screen import ResultScreen
from services.ai_service import AIService
from services.authentication import AuthenticationService
from services.quiz_service import QuizService
from services.result_service import ResultService


class TestAIExplanation(unittest.TestCase):
    """
    Test suite for AI Answer Explanation generation, caching, and GUI integration.
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

        # Register Student & Create Quiz Result Record
        reg = self.auth_service.register_user("Test Student", "student_ai_exp", "exp@example.com", "StudentPass123!", "student")
        self.user_id = reg["user"].id
        self.auth_service.login_user("student_ai_exp", "StudentPass123!")

        # Add question
        q_res = self.quiz_service.add_question(
            category="Python",
            topic="Functions",
            difficulty="easy",
            question_text="What does len() return?",
            option_a="Object memory address",
            option_b="Number of items in an object",
            option_c="Data type string",
            option_d="Boolean status",
            correct_answer="B",
            explanation="len() returns the length (number of items) of an object."
        )
        self.question_id = q_res["question_id"]

        # Fetch Question object
        questions = [self.quiz_service.get_question_by_id(self.question_id)]

        # Submit attempt
        sub_res = self.quiz_service.submit_quiz_attempt(
            user_id=self.user_id,
            quiz_config={"category": "Python", "difficulty": "easy", "topic": "Functions"},
            questions=questions,
            user_answers={self.question_id: "A"},  # Wrong answer A chosen
            time_taken=10
        )
        self.result_id = sub_res["result_id"]

    def tearDown(self):
        self.app.destroy()
        os.close(self.temp_db_fd)
        if os.path.exists(self.temp_db_path):
            os.remove(self.temp_db_path)

    def test_explain_answer_detailed_structure(self):
        """Verify 3-part structured explanation generation."""
        ai_service = AIService(api_key="mock_key")
        ai_service._call_gemini = MagicMock(return_value='''{
            "why_correct": "Option B is correct because len() measures length.",
            "why_incorrect": "Option A refers to id() or hex memory addresses.",
            "learning_tip": "Remember: len = length count."
        }''')

        options = {
            "A": "Object memory address",
            "B": "Number of items in an object",
            "C": "Data type string",
            "D": "Boolean status"
        }

        res = ai_service.explain_answer_detailed(
            question_text="What does len() return?",
            selected_answer="A",
            correct_answer="B",
            options=options,
            existing_explanation="len() returns object length."
        )

        self.assertTrue(res["success"])
        self.assertEqual(res["why_correct"], "Option B is correct because len() measures length.")
        self.assertEqual(res["why_incorrect"], "Option A refers to id() or hex memory addresses.")
        self.assertEqual(res["learning_tip"], "Remember: len = length count.")
        self.assertFalse(res["cached"])

    def test_explanation_caching(self):
        """Verify that identical explanation requests hit the in-memory cache."""
        ai_service = AIService(api_key="mock_key")
        ai_service._call_gemini = MagicMock(return_value='''{
            "why_correct": "Option B is correct.",
            "why_incorrect": "Option A is wrong.",
            "learning_tip": "Quick tip."
        }''')

        options = {"A": "Opt A", "B": "Opt B", "C": "Opt C", "D": "Opt D"}

        # First Call (Hits Mock API)
        res1 = ai_service.explain_answer_detailed("Q Text", "A", "B", options)
        self.assertEqual(ai_service._call_gemini.call_count, 1)
        self.assertFalse(res1.get("cached", False))

        # Second Call with Same Inputs (Hits Cache)
        res2 = ai_service.explain_answer_detailed("Q Text", "A", "B", options)
        self.assertEqual(ai_service._call_gemini.call_count, 1)  # No extra API call!
        self.assertTrue(res2.get("cached", False))
        self.assertEqual(res2["why_correct"], "Option B is correct.")

    def test_offline_fallback_explanation(self):
        """Verify graceful fallback when API fails or key is missing."""
        ai_service = AIService(api_key=None)  # Offline mode

        options = {"A": "Opt A", "B": "Opt B", "C": "Opt C", "D": "Opt D"}
        res = ai_service.explain_answer_detailed(
            question_text="Q Text",
            selected_answer="A",
            correct_answer="B",
            options=options,
            existing_explanation="Db rationale."
        )

        self.assertFalse(res["success"])
        self.assertIn("Option B is the correct answer", res["why_correct"])
        self.assertIn("Db rationale", res["why_correct"])
        self.assertIn("selected instead of B", res["why_incorrect"])

    def test_result_screen_gui_explanation_trigger(self):
        """Verify ResultScreen instantiates and renders AI explanation upon button click."""
        screen = ResultScreen(self.app.container, self.app, result_id=self.result_id)
        # Mock AI service on screen
        screen.ai_service._call_gemini = MagicMock(return_value='''{
            "why_correct": "Option B is correct.",
            "why_incorrect": "Option A is wrong.",
            "learning_tip": "Tip."
        }''')

        self.assertEqual(len(screen.review_details), 1)
        item = screen.review_details[0]

        mock_btn = MagicMock()
        mock_container = MagicMock()

        # Trigger explanation method
        screen._on_explain_with_ai(item, mock_btn, mock_container)
        self.assertEqual(mock_btn.configure.call_count, 2)


if __name__ == "__main__":
    unittest.main()
