"""
tests/test_performance.py
--------------------------
Unit and integration tests for Performance Analytics in QuizMaster AI.

Test Cases:
    1. Test ResultService.get_student_performance_analytics calculations (Avg, Best, Strongest, Weakest).
    2. Test Performance analytics empty state handling when student has 0 attempts.
    3. Test PerformanceScreen GUI rendering with analytics data and Matplotlib canvas.
    4. Test PerformanceScreen empty state rendering.
"""

import os
import tempfile
import unittest

from database.database import DatabaseManager
from gui.app import App
from gui.performance import PerformanceScreen
from services.authentication import AuthenticationService
from services.quiz_service import QuizService
from services.result_service import ResultService


class TestPerformanceAnalytics(unittest.TestCase):
    """
    Test suite for Performance Analytics business logic and Matplotlib GUI integration.
    """

    def setUp(self):
        """Set up isolated temporary database and populate sample attempt data."""
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        self.db_mgr = DatabaseManager(db_path=self.temp_db_path)
        self.db_mgr.initialize_database()

        self.auth_service = AuthenticationService(db_mgr=self.db_mgr)
        self.quiz_service = QuizService(db_mgr=self.db_mgr)
        self.result_service = ResultService(db_mgr=self.db_mgr)

        self.app = App(auth_service=self.auth_service)
        self.app.withdraw()

        # Register Student with data
        s1 = self.auth_service.register_user("Perf Student", "perf_stud", "perf@example.com", "Password123!", "student")
        self.user_id = s1["user"].id

        # Register Student with NO data (empty state)
        s2 = self.auth_service.register_user("New Student", "new_stud", "new@example.com", "Password123!", "student")
        self.empty_user_id = s2["user"].id

        # Create Questions
        q_py1 = self.quiz_service.add_question("Python", "Basics", "easy", "Python Q1 text?", "A", "B", "C", "D", "A")
        q_py2 = self.quiz_service.add_question("Python", "Basics", "easy", "Python Q2 text?", "A", "B", "C", "D", "B")
        q_db1 = self.quiz_service.add_question("DBMS", "SQL", "medium", "DBMS Q1 text?", "A", "B", "C", "D", "C")

        qs_py = [q_py1["question"], q_py2["question"]]
        qs_db = [q_db1["question"]]

        # Submit attempts for perf_stud:
        # Attempt 1: Python -> 100% (2/2)
        self.quiz_service.submit_quiz_attempt(
            user_id=self.user_id,
            quiz_config={"category": "Python", "topic": "Basics", "difficulty": "easy"},
            questions=qs_py,
            user_answers={qs_py[0].question_id: "A", qs_py[1].question_id: "B"},
            time_taken=45
        )

        # Attempt 2: DBMS -> 0% (0/1)
        self.quiz_service.submit_quiz_attempt(
            user_id=self.user_id,
            quiz_config={"category": "DBMS", "topic": "SQL", "difficulty": "medium"},
            questions=qs_db,
            user_answers={qs_db[0].question_id: "A"},  # Wrong (Correct C)
            time_taken=30
        )

    def tearDown(self):
        """Clean up App instance and temporary database."""
        self.app.destroy()
        os.close(self.temp_db_fd)
        if os.path.exists(self.temp_db_path):
            os.remove(self.temp_db_path)

    def test_analytics_calculations(self):
        """Test calculation of overall average score, total quizzes, best score, strongest, and weakest categories."""
        data = self.result_service.get_student_performance_analytics(self.user_id)

        self.assertTrue(data["has_data"])
        self.assertEqual(data["total_quizzes"], 2)
        self.assertEqual(data["average_score"], 50.0)  # (100 + 0) / 2
        self.assertEqual(data["best_score"], 100.0)
        self.assertEqual(data["strongest_category"], "Python")
        self.assertEqual(data["weakest_category"], "DBMS")
        self.assertEqual(len(data["score_progression"]), 2)

    def test_analytics_empty_state_handling(self):
        """Test analytics metrics returned for a user with zero attempts."""
        data = self.result_service.get_student_performance_analytics(self.empty_user_id)

        self.assertFalse(data["has_data"])
        self.assertEqual(data["total_quizzes"], 0)
        self.assertEqual(data["average_score"], 0.0)
        self.assertEqual(data["best_score"], 0.0)
        self.assertEqual(data["strongest_category"], "N/A")
        self.assertEqual(data["weakest_category"], "N/A")
        self.assertEqual(data["score_progression"], [])

    def test_performance_screen_gui_rendering(self):
        """Test PerformanceScreen GUI initialization with active data."""
        self.auth_service.login_user("perf_stud", "Password123!")
        screen = PerformanceScreen(self.app.container, self.app)

        self.assertTrue(screen.analytics_data["has_data"])
        self.assertEqual(screen.analytics_data["total_quizzes"], 2)

    def test_performance_screen_empty_state_gui(self):
        """Test PerformanceScreen GUI initialization with empty user state."""
        self.auth_service.login_user("new_stud", "Password123!")
        screen = PerformanceScreen(self.app.container, self.app)

        self.assertFalse(screen.analytics_data["has_data"])


if __name__ == "__main__":
    unittest.main()
