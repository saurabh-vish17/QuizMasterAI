"""
tests/test_study_plan.py
-------------------------
Unit and integration tests for AI Study Plan feature in QuizMaster AI.

Test Cases:
    1. Test AIService.generate_study_plan returns required schema:
       (weak_topics, recommended_topics, duration, difficulty, questions_to_practice, revision_priorities, timeline).
    2. Test ResultService.save_study_plan and get_latest_study_plan persistence in ai_analysis table.
    3. Test ResultService.generate_and_save_study_plan orchestration using deterministic stats.
    4. Test StudyPlanScreen widget instantiation and load hooks.
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.database import DatabaseManager
from gui.app import App
from gui.study_plan import StudyPlanScreen
from services.ai_service import AIService
from services.authentication import AuthenticationService
from services.quiz_service import QuizService
from services.result_service import ResultService


class TestStudyPlan(unittest.TestCase):
    """
    Test suite for AI Study Plan generation, persistence, and UI integration.
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

        # Register & Login Student
        reg = self.auth_service.register_user("Study Student", "study_student", "study@example.com", "StudentPass123!", "student")
        self.user_id = reg["user"].id
        self.auth_service.login_user("study_student", "StudentPass123!")

        # Add Questions and submit attempt to generate statistics
        q1 = self.quiz_service.add_question("Python", "OOP", "medium", "OOP Q1?", "A", "B", "C", "D", "A")
        q2 = self.quiz_service.add_question("Python", "Variables", "easy", "Var Q1?", "A", "B", "C", "D", "A")

        self.quiz_service.submit_quiz_attempt(
            user_id=self.user_id,
            quiz_config={"category": "Python", "difficulty": "medium", "topic": "OOP"},
            questions=[self.quiz_service.get_question_by_id(q1["question_id"])],
            user_answers={q1["question_id"]: "B"},  # Incorrect answer -> 0%
            time_taken=10
        )

    def tearDown(self):
        self.app.destroy()
        os.close(self.temp_db_fd)
        if os.path.exists(self.temp_db_path):
            os.remove(self.temp_db_path)

    def test_ai_service_generate_study_plan_schema(self):
        """Verify AIService.generate_study_plan returns all required fields."""
        ai_service = AIService(api_key="mock_key")
        ai_service._call_gemini = MagicMock(return_value='''{
            "title": "7-Day OOP Mastery Plan",
            "suggested_practice_duration": "30 mins / day",
            "recommended_difficulty": "medium",
            "questions_to_practice": 15,
            "weak_topics": ["OOP"],
            "recommended_topics": ["Variables"],
            "revision_priorities": [
                {"priority": 1, "topic": "OOP", "reason": "Low accuracy", "daily_minutes": 20, "target_questions": 5}
            ],
            "study_plan": [
                {"day": 1, "topic": "OOP Basics", "focus": "Review classes", "activities": ["Read notes", "Solve 5 Qs"]}
            ]
        }''')

        res = ai_service.generate_study_plan({
            "weak_topics": ["OOP"],
            "weakest_category": "Python",
            "recent_accuracy": 35.0,
            "recommended_difficulty": "medium"
        })

        self.assertTrue(res["success"])
        self.assertEqual(res["title"], "7-Day OOP Mastery Plan")
        self.assertEqual(res["suggested_practice_duration"], "30 mins / day")
        self.assertEqual(res["recommended_difficulty"], "Medium")
        self.assertEqual(res["questions_to_practice"], 15)
        self.assertIn("OOP", res["weak_topics"])
        self.assertEqual(len(res["revision_priorities"]), 1)
        self.assertEqual(len(res["study_plan"]), 1)

    def test_save_and_retrieve_study_plan_in_db(self):
        """Verify saving and retrieving study plan from ai_analysis table."""
        sample_plan = {
            "title": "Test Plan",
            "suggested_practice_duration": "25 mins / day",
            "recommended_difficulty": "Easy",
            "questions_to_practice": 10,
            "weak_topics": ["OOP"],
            "recommended_topics": ["Variables"],
            "revision_priorities": [{"priority": 1, "topic": "OOP", "reason": "Revision needed"}],
            "study_plan": [{"day": 1, "topic": "OOP", "focus": "Classes", "activities": ["Read"]}]
        }

        analysis_id = self.result_service.save_study_plan(self.user_id, sample_plan)
        self.assertGreater(analysis_id, 0)

        retrieved = self.result_service.get_latest_study_plan(self.user_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["title"], "Test Plan")
        self.assertEqual(retrieved["recommended_difficulty"], "Easy")

    def test_generate_and_save_study_plan_orchestration(self):
        """Verify full end-to-end orchestration calculates stats and saves plan."""
        plan = self.result_service.generate_and_save_study_plan(user_id=self.user_id)
        self.assertIn("study_plan", plan)
        self.assertIn("weak_topics", plan)

        saved = self.result_service.get_latest_study_plan(self.user_id)
        self.assertIsNotNone(saved)

    def test_study_plan_screen_ui(self):
        """Verify StudyPlanScreen instantiates correctly and connects to controller."""
        screen = StudyPlanScreen(self.app.container, self.app)
        self.assertIsNotNone(screen.btn_generate)
        self.assertIsNotNone(screen.btn_refresh)


if __name__ == "__main__":
    unittest.main()
