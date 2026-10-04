"""
tests/test_quiz_engine.py
--------------------------
Unit and integration tests for Core Quiz Engine in QuizMaster AI.

Test Cases:
    1. Test deterministic scoring in Quiz.evaluate_attempt (uses DB answer keys, NOT AI).
    2. Test QuizService.submit_quiz_attempt persistence to results & quiz_attempts tables.
    3. Test QuizScreen MCQ option selection and state preservation.
    4. Test QuizScreen navigation (Next, Previous, Stepper).
    5. Test QuizScreen unanswered questions calculation.
    6. Test QuizScreen auto-submission on timer expiry.
"""

import os
import tempfile
import unittest
import tkinter as tk
from unittest.mock import MagicMock, patch

from database.database import DatabaseManager
from gui.app import App
from gui.quiz_screen import QuizScreen
from gui.result_screen import ResultScreen
from models.question import Question
from models.quiz import Quiz
from services.authentication import AuthenticationService
from services.quiz_service import QuizService


class TestQuizEngine(unittest.TestCase):
    """
    Test suite for Core Quiz Engine, deterministic evaluation, and GUI interactions.
    """

    def setUp(self):
        """Set up isolated database, service instances, and sample questions."""
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        self.db_mgr = DatabaseManager(db_path=self.temp_db_path)
        self.db_mgr.initialize_database()

        self.auth_service = AuthenticationService(db_mgr=self.db_mgr)
        self.quiz_service = QuizService(db_mgr=self.db_mgr)

        self.app = App(auth_service=self.auth_service)
        self.app.withdraw()

        # Add sample student user
        reg_res = self.auth_service.register_user(
            name="Quiz Student",
            username="student1",
            email="student1@example.com",
            password="Password123!",
            role="student"
        )
        self.user_id = reg_res["user"].id
        self.auth_service.login_user("student1", "Password123!")

        # Create sample questions
        self.questions = []
        for i in range(5):
            q_res = self.quiz_service.add_question(
                category="Python",
                topic="Basics",
                difficulty="easy",
                question_text=f"Question #{i + 1} text?",
                option_a="Ans A",
                option_b="Ans B",
                option_c="Ans C",
                option_d="Ans D",
                correct_answer="B" if i % 2 == 0 else "A",
                explanation=f"Explanation #{i + 1}"
            )
            self.questions.append(q_res["question"])

    def tearDown(self):
        """Clean up App instance and temporary database."""
        self.app.destroy()
        os.close(self.temp_db_fd)
        if os.path.exists(self.temp_db_path):
            os.remove(self.temp_db_path)

    # --- 1. Deterministic Scoring Tests ---
    def test_deterministic_scoring_db_answer_keys(self):
        """Verify Quiz.evaluate_attempt scores deterministically using DB answer keys."""
        quiz = Quiz(
            title="Python Test",
            category="Python",
            topic="Basics",
            difficulty="easy",
            questions=self.questions
        )

        # Questions: Q1: B, Q2: A, Q3: B, Q4: A, Q5: B
        user_answers = {
            self.questions[0].question_id: "B",  # Correct
            self.questions[1].question_id: "A",  # Correct
            self.questions[2].question_id: "C",  # Wrong (Correct B)
            self.questions[3].question_id: "A",  # Correct
            # Q5 unanswered
        }

        res = quiz.evaluate_attempt(user_answers)

        self.assertEqual(res["total_questions"], 5)
        self.assertEqual(res["correct_answers"], 3)
        self.assertEqual(res["wrong_answers"], 1)
        self.assertEqual(res["unanswered"], 1)
        self.assertEqual(res["score"], 3.0)
        self.assertEqual(res["percentage"], 60.0)

    def test_submit_quiz_attempt_persistence(self):
        """Test persisting quiz attempt results to 'results' and 'quiz_attempts' tables."""
        quiz_config = {"category": "Python", "topic": "Basics", "difficulty": "easy"}
        user_answers = {
            self.questions[0].question_id: "B",
            self.questions[1].question_id: "A"
        }

        res = self.quiz_service.submit_quiz_attempt(
            user_id=self.user_id,
            quiz_config=quiz_config,
            questions=self.questions,
            user_answers=user_answers,
            time_taken=45
        )

        self.assertTrue(res["success"])
        self.assertIsNotNone(res["result_id"])
        result_id = res["result_id"]

        # Verify record in results table
        rows = self.db_mgr.fetch_all("SELECT user_id, category, correct_answers, percentage FROM results WHERE id = ?", (result_id,))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][0], self.user_id)
        self.assertEqual(rows[0][1], "Python")
        self.assertEqual(rows[0][2], 2)

        # Verify records in quiz_attempts table
        att_rows = self.db_mgr.fetch_all("SELECT question_id, selected_answer, is_correct FROM quiz_attempts WHERE result_id = ?", (result_id,))
        self.assertEqual(len(att_rows), 5)

    # --- 2. GUI Engine Tests ---
    def test_quiz_screen_navigation_and_option_selection(self):
        """Test MCQ option selection, answer preservation, and Next/Prev navigation."""
        quiz_config = {"category": "Python", "topic": "Basics", "difficulty": "easy"}
        screen = QuizScreen(self.app.container, self.app, quiz_config=quiz_config, questions=self.questions)

        # Initial Question 1 (index 0)
        self.assertEqual(screen.current_index, 0)
        self.assertEqual(screen.btn_prev.cget("state"), "disabled")

        # Select option "B" on Question 1
        screen._on_option_selected("B")
        q1_id = self.questions[0].question_id
        self.assertEqual(screen.user_answers[q1_id], "B")

        # Navigate Next to Question 2 (index 1)
        screen._on_next_click()
        self.assertEqual(screen.current_index, 1)
        self.assertEqual(screen.btn_prev.cget("state"), "normal")

        # Select option "A" on Question 2
        screen._on_option_selected("A")
        q2_id = self.questions[1].question_id
        self.assertEqual(screen.user_answers[q2_id], "A")

        # Navigate Previous back to Question 1 and verify preserved option "B"
        screen._on_prev_click()
        self.assertEqual(screen.current_index, 0)
        self.assertEqual(screen.user_answers[q1_id], "B")
        self.assertEqual(screen.selected_var.get(), "B")

    @patch("tkinter.messagebox.askyesno", return_value=True)
    def test_manual_quiz_submission(self, mock_confirm):
        """Test user manual submission transitions to ResultScreen."""
        quiz_config = {"category": "Python", "topic": "Basics", "difficulty": "easy"}
        screen = QuizScreen(self.app.container, self.app, quiz_config=quiz_config, questions=self.questions)

        screen._on_option_selected("B")
        screen._on_submit_click()

        self.assertTrue(screen.submitted)
        self.assertIsInstance(self.app.current_screen, ResultScreen)

    @patch("tkinter.messagebox.showinfo")
    def test_timer_expiry_auto_submission(self, mock_info):
        """Test automatic submission when countdown timer reaches zero."""
        quiz_config = {"category": "Python", "topic": "Basics", "difficulty": "easy"}
        screen = QuizScreen(self.app.container, self.app, quiz_config=quiz_config, questions=self.questions)

        screen.time_remaining = 0
        screen._update_timer()

        self.assertTrue(screen.submitted)
        self.assertIsInstance(self.app.current_screen, ResultScreen)


if __name__ == "__main__":
    unittest.main()
