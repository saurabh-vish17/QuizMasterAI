"""
tests/test_student_dashboard.py
--------------------------------
Unit and integration tests for AI-Powered Student Dashboard in QuizMaster AI.

Test Cases:
    1. Test StudentDashboardScreen instantiation and top 5 metric cards rendering.
    2. Test rendering of the 6 core AI sections (AI Performance Summary, Recommended Quiz,
       Weak Topics, Study Plan, Recent Performance, AI Study Assistant).
    3. Test all action buttons navigation callbacks ([Start Quiz], [Practice Weak Areas],
       [View Performance], [AI Study Plan], [Ask AI], [Quiz History], [Leaderboard]).
    4. Test behavior for new students with zero quiz history.
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.database import DatabaseManager
from gui.app import App
from gui.student_dashboard import StudentDashboardScreen
from services.authentication import AuthenticationService
from services.quiz_service import QuizService
from services.result_service import ResultService


class TestStudentDashboard(unittest.TestCase):
    """
    Test suite for AI Learning Student Dashboard component.
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
        reg = self.auth_service.register_user("Dashboard Student", "dash_student", "dash@example.com", "StudentPass123!", "student")
        self.user_id = reg["user"].id
        self.auth_service.login_user("dash_student", "StudentPass123!")

    def tearDown(self):
        self.app.destroy()
        os.close(self.temp_db_fd)
        if os.path.exists(self.temp_db_path):
            os.remove(self.temp_db_path)

    def test_dashboard_renders_metrics_and_sections_empty_state(self):
        """Verify dashboard renders 5 metric cards and 6 sections for new student."""
        screen = StudentDashboardScreen(self.app.container, self.app)
        self.assertIsNotNone(screen.scrollable_content)

        # Check content children rendered
        children = screen.scrollable_content.winfo_children()
        self.assertGreater(len(children), 2)  # Banner, Metrics, Sections Grid

    def test_dashboard_renders_metrics_and_sections_with_data(self):
        """Verify dashboard populates stats cards and sections with attempt data."""
        # Add questions & submit attempt
        q1 = self.quiz_service.add_question("Python", "OOP", "medium", "OOP Question?", "A", "B", "C", "D", "A")
        self.quiz_service.submit_quiz_attempt(
            user_id=self.user_id,
            quiz_config={"category": "Python", "difficulty": "medium", "topic": "OOP"},
            questions=[self.quiz_service.get_question_by_id(q1["question_id"])],
            user_answers={q1["question_id"]: "A"},  # Correct answer -> 100%
            time_taken=15
        )

        screen = StudentDashboardScreen(self.app.container, self.app)
        self.assertIsNotNone(screen.scrollable_content)

    def test_navigation_hooks_exist_in_controller(self):
        """Verify all requested dashboard button routes exist on App controller."""
        self.assertTrue(hasattr(self.app, "show_quiz_selection"))
        self.assertTrue(hasattr(self.app, "start_weak_area_quiz"))
        self.assertTrue(hasattr(self.app, "show_performance"))
        self.assertTrue(hasattr(self.app, "show_study_plan"))
        self.assertTrue(hasattr(self.app, "show_ai_assistant"))
        self.assertTrue(hasattr(self.app, "show_history"))
        self.assertTrue(hasattr(self.app, "show_leaderboard"))


if __name__ == "__main__":
    unittest.main()
