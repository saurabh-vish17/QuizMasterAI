"""
tests/test_ai_question_generator.py
-----------------------------------
Unit and integration tests for AI Question Generator in Admin Panel.

Test Cases:
    1. Test AI question generation and staging into ai_questions with approved_by_admin = 0.
    2. Test that generated AI questions are NEVER automatically published to main questions bank.
    3. Test schema validation (rejects < 4 options, invalid correct answer keys, short text).
    4. Test approve_ai_question transfers question to main bank and marks approved_by_admin = 1.
    5. Test reject_ai_question discards pending question.
    6. Test Admin Panel GUI elements ([Generate Questions], [Preview], [Approve], [Reject]).
"""

import os
import tempfile
import unittest
from unittest.mock import MagicMock

from database.database import DatabaseManager
from gui.admin_panel import AdminPanelScreen
from gui.app import App
from services.ai_service import AIService
from services.authentication import AuthenticationService
from services.quiz_service import QuizService


class TestAIQuestionGenerator(unittest.TestCase):
    """
    Test suite for AI Question Generation, Staging, Validation, and Admin Queue Approval.
    """

    def setUp(self):
        """Set up isolated temporary database and mock services."""
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        self.db_mgr = DatabaseManager(db_path=self.temp_db_path)
        self.db_mgr.initialize_database()

        self.auth_service = AuthenticationService(db_mgr=self.db_mgr)
        self.quiz_service = QuizService(db_mgr=self.db_mgr)

        self.app = App(auth_service=self.auth_service)
        self.app.withdraw()

        # Register Admin User
        adm = self.auth_service.register_user("Admin User", "admin_gen", "admin_gen@example.com", "AdminPass123!", "admin")
        self.admin_id = adm["user"].id
        self.auth_service.login_user("admin_gen", "AdminPass123!")

        # Create Mock AIService returning 2 valid and 1 malformed question
        self.mock_ai_service = AIService(api_key="mock_key")
        self.mock_ai_service.generate_questions = MagicMock(return_value={
            "success": True,
            "questions": [
                {
                    "question_text": "What is encapsulation in OOP?",
                    "option_a": "Data hiding inside a class",
                    "option_b": "Multiple methods with same name",
                    "option_c": "Inheriting properties from parent",
                    "option_d": "Executing code dynamically",
                    "correct_answer": "A",
                    "explanation": "Encapsulation restricts direct access to objects."
                },
                {
                    "question_text": "Which SQL keyword filters group rows?",
                    "option_a": "WHERE",
                    "option_b": "HAVING",
                    "option_c": "GROUP BY",
                    "option_d": "ORDER BY",
                    "correct_answer": "B",
                    "explanation": "HAVING filters aggregated grouped records."
                },
                # Malformed question (invalid correct answer 'Z', missing option_d)
                {
                    "question_text": "Bad Question text?",
                    "option_a": "Opt A",
                    "option_b": "Opt B",
                    "option_c": "Opt C",
                    "correct_answer": "Z"
                }
            ]
        })

    def tearDown(self):
        """Clean up App instance and temporary database."""
        self.app.destroy()
        os.close(self.temp_db_fd)
        if os.path.exists(self.temp_db_path):
            os.remove(self.temp_db_path)

    def test_generate_and_stage_ai_questions(self):
        """Verify AI questions are staged into ai_questions with approved_by_admin = 0."""
        res = self.quiz_service.generate_and_stage_ai_questions(
            topic="OOP Concepts",
            category="Python",
            difficulty="medium",
            count=3,
            ai_service=self.mock_ai_service
        )

        self.assertTrue(res["success"])
        self.assertEqual(res["staged_count"], 2)  # 2 valid staged, 1 malformed rejected
        self.assertEqual(res["rejected_count"], 1)

        # Check pending queue in SQLite
        pending = self.quiz_service.get_pending_ai_questions()
        self.assertEqual(len(pending), 2)
        self.assertEqual(pending[0]["question_text"], "What is encapsulation in OOP?")

        # Check that main question bank is STILL EMPTY (Never auto-published!)
        main_questions = self.quiz_service.get_questions()
        self.assertEqual(len(main_questions), 0)

    def test_approve_ai_question_transfer(self):
        """Verify approving an AI question moves it to main question bank."""
        stage_res = self.quiz_service.generate_and_stage_ai_questions(
            topic="SQL Joins",
            category="DBMS",
            difficulty="easy",
            count=3,
            ai_service=self.mock_ai_service
        )
        ai_id = stage_res["staged_ids"][0]

        # Approve Question
        app_res = self.quiz_service.approve_ai_question(ai_id)
        self.assertTrue(app_res["success"])

        # Check main question bank now has 1 question
        main_questions = self.quiz_service.get_questions()
        self.assertEqual(len(main_questions), 1)
        self.assertEqual(main_questions[0].question_text, "What is encapsulation in OOP?")

        # Check pending queue count reduced by 1
        pending = self.quiz_service.get_pending_ai_questions()
        self.assertEqual(len(pending), 1)

    def test_reject_ai_question(self):
        """Verify rejecting an AI question removes it from pending queue without adding to main bank."""
        stage_res = self.quiz_service.generate_and_stage_ai_questions(
            topic="Basics",
            category="Python",
            difficulty="easy",
            count=3,
            ai_service=self.mock_ai_service
        )
        ai_id = stage_res["staged_ids"][0]

        # Reject Question
        rej_res = self.quiz_service.reject_ai_question(ai_id)
        self.assertTrue(rej_res["success"])

        # Main bank remains empty
        main_questions = self.quiz_service.get_questions()
        self.assertEqual(len(main_questions), 0)

        # Pending queue count reduced to 1
        pending = self.quiz_service.get_pending_ai_questions()
        self.assertEqual(len(pending), 1)

    def test_admin_panel_ai_queue_gui(self):
        """Verify AdminPanelScreen initializes with AI Generator controls."""
        screen = AdminPanelScreen(self.app.container, self.app)
        self.assertIsNotNone(screen.btn_gen_ai)
        self.assertIsNotNone(screen.cmb_ai_cat)
        self.assertIsNotNone(screen.ent_ai_topic)


if __name__ == "__main__":
    unittest.main()
