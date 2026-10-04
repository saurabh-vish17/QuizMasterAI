"""
tests/test_practice_weak_areas.py
----------------------------------
Unit and integration tests for "Practice My Weak Areas" feature in QuizMaster AI.

Test Cases:
    1. Test deterministic calculation of weak topics from student history.
    2. Test QuizService.generate_weak_area_quiz prioritizing weak topics & recommended difficulty.
    3. Test retrieval of ONLY approved questions from the main 'questions' database table.
    4. Test AIService.recommend_weak_area_focus recommendation logic.
    5. Test App.start_weak_area_quiz launcher and transition to QuizScreen.
    6. Test student manual quiz selection remains available.
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.database import DatabaseManager
from gui.app import App
from gui.quiz_screen import QuizScreen
from gui.student_dashboard import StudentDashboardScreen
from services.ai_service import AIService
from services.authentication import AuthenticationService
from services.quiz_service import QuizService


class TestPracticeWeakAreas(unittest.TestCase):
    """
    Test suite for Practice My Weak Areas feature, approved question selection, and UI hooks.
    """

    def setUp(self):
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        self.db_mgr = DatabaseManager(db_path=self.temp_db_path)
        self.db_mgr.initialize_database()

        self.auth_service = AuthenticationService(db_mgr=self.db_mgr)
        self.quiz_service = QuizService(db_mgr=self.db_mgr)

        self.app = App(auth_service=self.auth_service)
        self.app.withdraw()

        # Register & Login Student
        reg = self.auth_service.register_user("Weak Area Student", "weak_student", "weak@example.com", "StudentPass123!", "student")
        self.user_id = reg["user"].id
        self.auth_service.login_user("weak_student", "StudentPass123!")

        # Add Approved Questions to 'questions' table
        q1 = self.quiz_service.add_question("Python", "OOP", "medium", "OOP Q1?", "A", "B", "C", "D", "A")
        q2 = self.quiz_service.add_question("Python", "OOP", "medium", "OOP Q2?", "A", "B", "C", "D", "B")
        q3 = self.quiz_service.add_question("Python", "Variables", "easy", "Var Q1?", "A", "B", "C", "D", "A")
        self.q1_id = q1["question_id"]
        self.q2_id = q2["question_id"]
        self.q3_id = q3["question_id"]

        # Insert attempt demonstrating low score in OOP (0% accuracy)
        questions = [self.quiz_service.get_question_by_id(self.q1_id), self.quiz_service.get_question_by_id(self.q2_id)]
        self.quiz_service.submit_quiz_attempt(
            user_id=self.user_id,
            quiz_config={"category": "Python", "difficulty": "medium", "topic": "OOP"},
            questions=questions,
            user_answers={self.q1_id: "C", self.q2_id: "D"},  # 0% correct
            time_taken=15
        )

    def tearDown(self):
        self.app.destroy()
        os.close(self.temp_db_fd)
        if os.path.exists(self.temp_db_path):
            os.remove(self.temp_db_path)

    def test_generate_weak_area_quiz_prioritizes_weak_topics(self):
        """Verify generate_weak_area_quiz identifies weak topics (OOP) and fetches approved questions."""
        res = self.quiz_service.generate_weak_area_quiz(user_id=self.user_id, count=5)

        self.assertTrue(res["success"])
        self.assertIn("OOP", res["weak_topics"])
        self.assertGreater(len(res["questions"]), 0)
        self.assertTrue(res["quiz_config"]["is_weak_area"])

    def test_only_approved_questions_used(self):
        """Verify weak area quiz ONLY pulls questions from 'questions' table."""
        # Insert an unapproved question into ai_questions table
        sql_unapproved = """
            INSERT INTO ai_questions (category, topic, difficulty, question_text, option_a, option_b, option_c, option_d, correct_answer, approved_by_admin)
            VALUES ('Python', 'OOP', 'medium', 'Unapproved AI Q?', 'A', 'B', 'C', 'D', 'A', 0)
        """
        self.db_mgr.execute_query(sql_unapproved)

        res = self.quiz_service.generate_weak_area_quiz(user_id=self.user_id, count=10)
        q_texts = [q.question_text for q in res["questions"]]

        self.assertNotIn("Unapproved AI Q?", q_texts)

    def test_ai_service_weak_area_focus_recommendation(self):
        """Verify AIService recommend_weak_area_focus returns expected schema."""
        ai_service = AIService(api_key="mock_key")
        ai_service._call_gemini = MagicMock(return_value='''{
            "target_topics": ["OOP", "Exception Handling"],
            "target_difficulty": "medium",
            "rationale": "Focusing practice on low accuracy topics."
        }''')

        res = ai_service.recommend_weak_area_focus({"weak_topics": ["OOP"], "recent_accuracy": 40.0})
        self.assertTrue(res["success"])
        self.assertEqual(res["target_topics"], ["OOP", "Exception Handling"])
        self.assertEqual(res["target_difficulty"], "medium")

    def test_app_start_weak_area_quiz_launcher(self):
        """Verify start_weak_area_quiz transitions controller to QuizScreen."""
        self.app.start_weak_area_quiz()
        self.assertIsInstance(self.app.current_screen, QuizScreen)

    def test_manual_quiz_selection_remains_available(self):
        """Verify student dashboard allows launching standard manual quiz selection."""
        dashboard = StudentDashboardScreen(self.app.container, self.app)
        self.app.show_quiz_selection()
        from gui.quiz_selection import QuizSelectionScreen
        self.assertIsInstance(self.app.current_screen, QuizSelectionScreen)


if __name__ == "__main__":
    unittest.main()
