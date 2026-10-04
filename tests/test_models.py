"""
tests/test_models.py
---------------------
Unit tests for the OOP model layer (User, Student, Admin, Question, Quiz, Result).
Verifies encapsulation, inheritance, polymorphism, properties, and helper methods.
"""

import hashlib
import unittest
from models.user import User, Student, Admin
from models.question import Question
from models.quiz import Quiz
from models.result import Result


class TestUserModels(unittest.TestCase):
    """Test suite for User, Student, and Admin domain models."""

    def setUp(self):
        self.password = "secret123"
        self.pass_hash = hashlib.sha256(self.password.encode("utf-8")).hexdigest()

    def test_user_encapsulation_and_properties(self):
        """Test read-only properties and setters validation."""
        user = User(1, "Alice Smith", "alice", "alice@example.com", self.pass_hash, role="student")

        self.assertEqual(user.user_id, 1)
        self.assertEqual(user.name, "Alice Smith")
        self.assertEqual(user.username, "alice")
        self.assertEqual(user.email, "alice@example.com")
        self.assertEqual(user.role, "student")

        # Test name setter
        user.name = "Alice Johnson"
        self.assertEqual(user.name, "Alice Johnson")

        with self.assertRaises(ValueError):
            user.name = "   "

    def test_password_verification(self):
        """Test password verification with SHA-256 hash."""
        user = User(1, "Alice", "alice", "alice@example.com", self.pass_hash)
        self.assertTrue(user.check_password("secret123"))
        self.assertFalse(user.check_password("wrongpass"))

    def test_student_and_admin_inheritance(self):
        """Test inheritance for Student and Admin subclasses."""
        student = Student(2, "Bob Student", "bob", "bob@example.com", self.pass_hash)
        admin = Admin(3, "Carol Admin", "carol", "carol@example.com", self.pass_hash)

        self.assertIsInstance(student, User)
        self.assertIsInstance(admin, User)

        self.assertTrue(student.is_student())
        self.assertFalse(student.is_admin())

        self.assertTrue(admin.is_admin())
        self.assertFalse(admin.is_student())

    def test_polymorphism(self):
        """Test polymorphic behavior across User, Student, and Admin."""
        base_user = User(1, "Base", "base", "base@example.com", self.pass_hash)
        student = Student(2, "Bob", "bob", "bob@example.com", self.pass_hash)
        admin = Admin(3, "Carol", "carol", "carol@example.com", self.pass_hash)

        # Role display polymorphism
        self.assertEqual(base_user.get_role_display(), "Student")
        self.assertEqual(student.get_role_display(), "Student")
        self.assertEqual(admin.get_role_display(), "Administrator")

        # Permissions polymorphism
        self.assertIn("take_quizzes", student.get_permissions())
        self.assertNotIn("create_quizzes", student.get_permissions())
        self.assertIn("create_quizzes", admin.get_permissions())

        # Dashboard welcome polymorphism
        self.assertIn("Learning Dashboard", student.get_dashboard_welcome())
        self.assertIn("Admin Control Panel", admin.get_dashboard_welcome())


class TestQuestionModel(unittest.TestCase):
    """Test suite for Question domain model."""

    def setUp(self):
        self.q = Question(
            question_id=10,
            category="Python",
            topic="Basics",
            difficulty="easy",
            question_text="What is the output of print(2 + 3)?",
            option_a="4",
            option_b="5",
            option_c="6",
            option_d="23",
            correct_answer="B",
            explanation="2 + 3 equals 5"
        )

    def test_question_properties(self):
        self.assertEqual(self.q.question_id, 10)
        self.assertEqual(self.q.category, "Python")
        self.assertEqual(self.q.difficulty, "easy")

    def test_get_options(self):
        options = self.q.get_options()
        self.assertEqual(options["A"], "4")
        self.assertEqual(options["B"], "5")

    def test_check_answer(self):
        self.assertTrue(self.q.check_answer("B"))
        self.assertTrue(self.q.check_answer("b"))
        self.assertTrue(self.q.check_answer("5"))
        self.assertFalse(self.q.check_answer("A"))


class TestQuizModel(unittest.TestCase):
    """Test suite for Quiz domain model."""

    def test_quiz_operations(self):
        quiz = Quiz(
            title="Python Fundamentals",
            category="Programming",
            topic="Python",
            difficulty="medium",
            time_limit=300,
            quiz_id=1
        )

        q1 = Question(1, "Prog", "Py", "medium", "Q1", "a", "b", "c", "d", "A")
        q2 = Question(2, "Prog", "Py", "medium", "Q2", "a", "b", "c", "d", "B")

        quiz.add_question(q1)
        quiz.add_question(q2)

        self.assertEqual(quiz.total_questions(), 2)
        self.assertTrue(quiz.has_time_limit())
        self.assertEqual(quiz.get_difficulty_color(), "#FFB300")

        quiz.remove_question(1)
        self.assertEqual(quiz.total_questions(), 1)


class TestResultModel(unittest.TestCase):
    """Test suite for Result domain model."""

    def test_result_grading_and_formatting(self):
        res_pass = Result(
            user_id=1,
            category="Python",
            difficulty="easy",
            total_questions=10,
            correct_answers=8,
            wrong_answers=2,
            unanswered=0,
            score=80.0,
            percentage=85.0,
            time_taken=135,
            result_id=100
        )

        self.assertTrue(res_pass.is_passed())
        self.assertEqual(res_pass.get_grade(), "B")
        self.assertEqual(res_pass.formatted_time(), "02:15")

        res_fail = Result(
            user_id=1,
            category="Python",
            difficulty="hard",
            total_questions=10,
            correct_answers=4,
            wrong_answers=6,
            unanswered=0,
            score=40.0,
            percentage=40.0,
            time_taken=300
        )

        self.assertFalse(res_fail.is_passed())
        self.assertEqual(res_fail.get_grade(), "F")


if __name__ == "__main__":
    unittest.main()
