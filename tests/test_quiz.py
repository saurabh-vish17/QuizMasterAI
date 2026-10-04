"""
tests/test_quiz.py
-------------------
Unit tests for Quiz Engine, question loading, category/difficulty filtering, answer selection,
navigation, timer, submission, and score calculation.
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.database import DatabaseManager
from gui.app import App
from gui.quiz_screen import QuizScreen
from models.question import Question
from services.authentication import AuthenticationService
from services.quiz_service import QuizService
from services.result_service import ResultService


class TestQuizEngineSuite(unittest.TestCase):
    """
    Test suite covering Quiz Loading, Filtering, Answer Selection, Navigation, Timer, Submission, & Scoring.
    """

    def setUp(self):
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        self.db_mgr = DatabaseManager(db_path=self.temp_db_path)
        self.db_mgr.initialize_database()

        self.quiz_service = QuizService(db_mgr=self.db_mgr)
        self.result_service = ResultService(db_mgr=self.db_mgr)
        self.auth_service = AuthenticationService(db_mgr=self.db_mgr)

        self.app = App(auth_service=self.auth_service)
        self.app.withdraw()

        # Create user
        reg = self.auth_service.register_user("Quiz User", "quizuser", "quiz@test.com", "Password123!", "student")
        self.user_id = reg["user"].id

        # Populate sample questions across categories & difficulties
        self.q1 = self.quiz_service.add_question("Python", "Variables", "easy", "What is x = 5?", "Integer", "Float", "String", "Bool", "A")
        self.q2 = self.quiz_service.add_question("Python", "OOP", "medium", "What is inheritance?", "Concept A", "Concept B", "Concept C", "Concept D", "B")
        self.q3 = self.quiz_service.add_question("DBMS", "SQL", "hard", "What is 3NF?", "Normal Form 3", "Form 2", "Form 1", "Form 4", "A")

    def tearDown(self):
        self.app.destroy()
        os.close(self.temp_db_fd)
        if os.path.exists(self.temp_db_path):
            os.remove(self.temp_db_path)

    def test_question_loading_and_filtering(self):
        """Test question loading, category filtering, and difficulty filtering."""
        all_qs = self.quiz_service.get_questions()
        self.assertEqual(len(all_qs), 3)

        py_qs = self.quiz_service.get_questions_by_category("Python")
        self.assertEqual(len(py_qs), 2)

        hard_qs = self.quiz_service.get_questions_by_difficulty("hard")
        self.assertEqual(len(hard_qs), 1)
        self.assertEqual(hard_qs[0].category, "DBMS")

    def test_answer_selection_and_navigation(self):
        """Test QuizScreen question navigation and answer selection persistence."""
        questions = [self.quiz_service.get_question_by_id(self.q1["question_id"]), self.quiz_service.get_question_by_id(self.q2["question_id"])]
        screen = QuizScreen(self.app.container, self.app, quiz_config={"category": "Python", "difficulty": "easy"}, questions=questions)

        self.assertEqual(screen.current_index, 0)
        screen._on_option_selected("A")
        self.assertEqual(screen.user_answers[questions[0].question_id], "A")

        # Navigate Next
        screen._on_next_click()
        self.assertEqual(screen.current_index, 1)

        # Answer Q2
        screen._on_option_selected("B")
        self.assertEqual(screen.user_answers[questions[1].question_id], "B")

        # Navigate Prev
        screen._on_prev_click()
        self.assertEqual(screen.current_index, 0)
        self.assertEqual(screen.user_answers[questions[0].question_id], "A")

    def test_timer_initialization(self):
        """Test timer initialization calculation."""
        questions = [self.quiz_service.get_question_by_id(self.q1["question_id"])]
        screen = QuizScreen(self.app.container, self.app, quiz_config={"category": "Python", "difficulty": "easy"}, questions=questions)
        self.assertGreaterEqual(screen.total_seconds, 60)

    def test_quiz_submission_and_score_calculation(self):
        """Test quiz attempt submission and deterministic score calculation."""
        questions = [
            self.quiz_service.get_question_by_id(self.q1["question_id"]),  # Ans: A
            self.quiz_service.get_question_by_id(self.q2["question_id"])   # Ans: B
        ]

        # 1 Correct (A), 1 Wrong (C)
        answers = {
            questions[0].question_id: "A",
            questions[1].question_id: "C"
        }

        res = self.quiz_service.submit_quiz_attempt(
            user_id=self.user_id,
            quiz_config={"category": "Python", "difficulty": "mixed"},
            questions=questions,
            user_answers=answers,
            time_taken=20
        )

        self.assertTrue(res["success"])
        result = self.result_service.get_result_by_id(res["result_id"])
        self.assertEqual(result.correct_answers, 1)
        self.assertEqual(result.wrong_answers, 1)
        self.assertEqual(result.unanswered, 0)
        self.assertEqual(result.percentage, 50.0)


if __name__ == "__main__":
    unittest.main()
