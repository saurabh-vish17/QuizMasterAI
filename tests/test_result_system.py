"""
tests/test_result_system.py
----------------------------
Unit and integration tests for the Quiz Results System in QuizMaster AI.

Test Cases:
    1. Test Result domain model properties and grade calculation.
    2. Test ResultService fetching result records by ID and User ID.
    3. Test ResultService get_result_details returning itemized answer review breakdown.
    4. Test ResultScreen GUI initialization and tab rendering.
"""

import os
import tempfile
import unittest
import tkinter as tk

from database.database import DatabaseManager
from gui.app import App
from gui.result_screen import ResultScreen
from models.result import Result
from services.authentication import AuthenticationService
from services.quiz_service import QuizService
from services.result_service import ResultService


class TestResultSystem(unittest.TestCase):
    """
    Test suite for Result model, ResultService, and ResultScreen GUI component.
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

        # Register and login student
        reg_res = self.auth_service.register_user(
            name="Results Student",
            username="res_student",
            email="res_student@example.com",
            password="Password123!",
            role="student"
        )
        self.user_id = reg_res["user"].id
        self.auth_service.login_user("res_student", "Password123!")

        # Create sample questions in Question Bank
        self.questions = []
        for i in range(4):
            q_res = self.quiz_service.add_question(
                category="Java",
                topic="Collections",
                difficulty="medium",
                question_text=f"Java Question #{i + 1} text?",
                option_a="Opt A", option_b="Opt B", option_c="Opt C", option_d="Opt D",
                correct_answer="A" if i < 3 else "B",
                explanation=f"Java Explanation #{i + 1}"
            )
            self.questions.append(q_res["question"])

        # Submit sample quiz attempt
        quiz_config = {"category": "Java", "topic": "Collections", "difficulty": "medium"}
        user_answers = {
            self.questions[0].question_id: "A",  # Correct
            self.questions[1].question_id: "A",  # Correct
            self.questions[2].question_id: "C",  # Wrong
            # Question 4 unanswered
        }
        submit_res = self.quiz_service.submit_quiz_attempt(
            user_id=self.user_id,
            quiz_config=quiz_config,
            questions=self.questions,
            user_answers=user_answers,
            time_taken=120
        )
        self.result_id = submit_res["result_id"]

    def tearDown(self):
        """Clean up App instance and temporary database."""
        self.app.destroy()
        os.close(self.temp_db_fd)
        if os.path.exists(self.temp_db_path):
            os.remove(self.temp_db_path)

    def test_result_model_grade_calculation(self):
        """Test Result model grade calculation and formatted time."""
        res = Result(
            user_id=self.user_id,
            category="Java",
            difficulty="medium",
            total_questions=10,
            correct_answers=8,
            wrong_answers=2,
            unanswered=0,
            score=8.0,
            percentage=80.0,
            time_taken=125,
            result_id=1
        )

        self.assertEqual(res.get_grade(), "B")
        self.assertTrue(res.is_passed())
        self.assertEqual(res.formatted_time(), "02:05")

    def test_result_service_get_by_id(self):
        """Test ResultService retrieving result record by result ID."""
        result = self.result_service.get_result_by_id(self.result_id)
        self.assertIsNotNone(result)
        self.assertEqual(result.category, "Java")
        self.assertEqual(result.total_questions, 4)
        self.assertEqual(result.correct_answers, 2)
        self.assertEqual(result.wrong_answers, 1)
        self.assertEqual(result.unanswered, 1)
        self.assertEqual(result.percentage, 50.0)

    def test_result_service_get_user_results(self):
        """Test ResultService retrieving all attempt results for a student."""
        user_results = self.result_service.get_user_results(self.user_id)
        self.assertEqual(len(user_results), 1)
        self.assertEqual(user_results[0].result_id, self.result_id)

    def test_result_service_get_result_details(self):
        """Test ResultService fetching itemized breakdown for answer review."""
        details = self.result_service.get_result_details(self.result_id)
        self.assertEqual(len(details), 4)

        # Question 1: Correct ("A")
        q1 = details[0]
        self.assertEqual(q1["selected_answer"], "A")
        self.assertEqual(q1["correct_answer"], "A")
        self.assertTrue(q1["is_correct"])

        # Question 3: Wrong ("C" vs "A")
        q3 = details[2]
        self.assertEqual(q3["selected_answer"], "C")
        self.assertEqual(q3["correct_answer"], "A")
        self.assertFalse(q3["is_correct"])

        # Question 4: Unanswered ("" vs "B")
        q4 = details[3]
        self.assertEqual(q4["selected_answer"], "")
        self.assertEqual(q4["correct_answer"], "B")
        self.assertFalse(q4["is_correct"])

    def test_result_screen_gui_rendering(self):
        """Test ResultScreen widget instantiation and rendering."""
        screen = ResultScreen(self.app.container, self.app, result_id=self.result_id)
        self.assertIsNotNone(screen.result)
        self.assertEqual(len(screen.review_details), 4)


if __name__ == "__main__":
    unittest.main()
