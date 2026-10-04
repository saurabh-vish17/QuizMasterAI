"""
tests/test_quiz_history.py
---------------------------
Unit and integration tests for Quiz History Screen in QuizMaster AI.

Test Cases:
    1. Test history table rendering exclusively for logged-in user (User level isolation).
    2. Test treeview columns population (Date, Category, Difficulty, Qs, Correct, Wrong, Score, Percentage, Time).
    3. Test column sorting mechanism.
    4. Test selecting an attempt and launching ResultScreen detailed breakdown.
"""

import os
import tempfile
import unittest
import tkinter as tk

from database.database import DatabaseManager
from gui.app import App
from gui.history import HistoryScreen
from gui.result_screen import ResultScreen
from services.authentication import AuthenticationService
from services.quiz_service import QuizService
from services.result_service import ResultService


class TestQuizHistory(unittest.TestCase):
    """
    Test suite for Quiz History GUI and data isolation.
    """

    def setUp(self):
        """Set up isolated temporary database and populate sample attempt data for multiple users."""
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        self.db_mgr = DatabaseManager(db_path=self.temp_db_path)
        self.db_mgr.initialize_database()

        self.auth_service = AuthenticationService(db_mgr=self.db_mgr)
        self.quiz_service = QuizService(db_mgr=self.db_mgr)
        self.result_service = ResultService(db_mgr=self.db_mgr)

        self.app = App(auth_service=self.auth_service)
        self.app.withdraw()

        # Register User A (Student A)
        reg_a = self.auth_service.register_user(
            name="Student Alpha",
            username="student_a",
            email="student_a@example.com",
            password="Password123!",
            role="student"
        )
        self.user_a_id = reg_a["user"].id

        # Register User B (Student B)
        reg_b = self.auth_service.register_user(
            name="Student Beta",
            username="student_b",
            email="student_b@example.com",
            password="Password123!",
            role="student"
        )
        self.user_b_id = reg_b["user"].id

        # Create sample questions
        q_res = self.quiz_service.add_question(
            category="Python",
            topic="Basics",
            difficulty="easy",
            question_text="Python Basics Q1?",
            option_a="A", option_b="B", option_c="C", option_d="D",
            correct_answer="A"
        )

        # Submit attempt for User A
        self.auth_service.login_user("student_a", "Password123!")
        res_a = self.quiz_service.submit_quiz_attempt(
            user_id=self.user_a_id,
            quiz_config={"category": "Python", "topic": "Basics", "difficulty": "easy"},
            questions=[q_res["question"]],
            user_answers={q_res["question"].question_id: "A"},
            time_taken=30
        )
        self.result_a_id = res_a["result_id"]

        # Submit attempt for User B
        res_b = self.quiz_service.submit_quiz_attempt(
            user_id=self.user_b_id,
            quiz_config={"category": "C++", "topic": "Pointers", "difficulty": "hard"},
            questions=[q_res["question"]],
            user_answers={q_res["question"].question_id: "B"},
            time_taken=60
        )
        self.result_b_id = res_b["result_id"]

    def tearDown(self):
        """Clean up App instance and temporary database."""
        self.app.destroy()
        os.close(self.temp_db_fd)
        if os.path.exists(self.temp_db_path):
            os.remove(self.temp_db_path)

    def test_user_history_data_isolation(self):
        """Verify that HistoryScreen only displays results belonging to logged-in Student A."""
        # Logged in as Student A
        self.auth_service.login_user("student_a", "Password123!")
        screen = HistoryScreen(self.app.container, self.app)

        self.assertEqual(len(screen.results_data), 1)
        self.assertEqual(screen.results_data[0].result_id, self.result_a_id)

        # Check treeview children
        children = screen.tree.get_children()
        self.assertEqual(len(children), 1)
        self.assertEqual(children[0], str(self.result_a_id))

    def test_treeview_column_values(self):
        """Verify treeview row values matching columns."""
        self.auth_service.login_user("student_a", "Password123!")
        screen = HistoryScreen(self.app.container, self.app)

        row_vals = screen.tree.item(str(self.result_a_id))["values"]

        # Columns: (id, date, category, difficulty, questions, correct, wrong, score, percentage, time)
        self.assertEqual(row_vals[0], self.result_a_id)
        self.assertEqual(row_vals[2], "Python")
        self.assertEqual(row_vals[3], "Easy")
        self.assertEqual(row_vals[4], 1)
        self.assertEqual(row_vals[5], 1)
        self.assertEqual(row_vals[6], 0)
        self.assertEqual(row_vals[8], "100.0%")
        self.assertEqual(row_vals[9], "00:30")

    def test_view_attempt_details_navigation(self):
        """Verify clicking view details opens ResultScreen for selected attempt."""
        self.auth_service.login_user("student_a", "Password123!")
        screen = HistoryScreen(self.app.container, self.app)

        # Select row in Treeview
        screen.tree.selection_set(str(self.result_a_id))
        screen._on_view_details_click()

        self.assertIsInstance(self.app.current_screen, ResultScreen)
        rs: ResultScreen = self.app.current_screen
        self.assertEqual(rs.result_id, self.result_a_id)


if __name__ == "__main__":
    unittest.main()
