"""
tests/test_quiz_service.py
---------------------------
Unit tests for QuizService (Question Bank Management Service).

Test Cases:
    1. Test question data validation rules.
    2. Test adding valid questions (across categories and difficulties).
    3. Test fetching questions (all & by ID).
    4. Test filtering questions by category.
    5. Test filtering questions by topic.
    6. Test filtering questions by difficulty (easy, medium, hard).
    7. Test random question selection (for quiz generation).
    8. Test updating an existing question.
    9. Test deleting a question.
"""

import os
import tempfile
import unittest
from database.database import DatabaseManager
from services.quiz_service import QuizService
from models.question import Question


class TestQuizService(unittest.TestCase):
    """
    Test suite for Question Bank management service.
    """

    def setUp(self):
        """Set up an isolated temporary database for each test run."""
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        self.db_mgr = DatabaseManager(db_path=self.temp_db_path)
        self.db_mgr.initialize_database()

        self.service = QuizService(db_mgr=self.db_mgr)

    def tearDown(self):
        """Clean up temporary database file."""
        os.close(self.temp_db_fd)
        if os.path.exists(self.temp_db_path):
            os.remove(self.temp_db_path)

    def test_question_data_validation(self):
        """Test question validation rules."""
        # Empty category
        valid, msg = self.service.validate_question_data(
            "", "Topic", "easy", "What is Python?", "A", "B", "C", "D", "A"
        )
        self.assertFalse(valid)
        self.assertIn("Category", msg)

        # Invalid difficulty
        valid, msg = self.service.validate_question_data(
            "Python", "Topic", "super_hard", "What is Python?", "A", "B", "C", "D", "A"
        )
        self.assertFalse(valid)
        self.assertIn("difficulty", msg)

        # Short question text
        valid, msg = self.service.validate_question_data(
            "Python", "Topic", "easy", "What", "A", "B", "C", "D", "A"
        )
        self.assertFalse(valid)
        self.assertIn("at least 5 characters", msg)

        # Invalid correct answer key
        valid, msg = self.service.validate_question_data(
            "Python", "Topic", "easy", "What is Python?", "Option A", "Option B", "Option C", "Option D", "Z"
        )
        self.assertFalse(valid)
        self.assertIn("Correct answer", msg)

    def test_add_and_get_question(self):
        """Test adding questions and fetching by ID."""
        res = self.service.add_question(
            category="Python",
            topic="Basics",
            difficulty="easy",
            question_text="Which keyword is used to define a function in Python?",
            option_a="func",
            option_b="def",
            option_c="function",
            option_d="define",
            correct_answer="B",
            explanation="The 'def' keyword is used to declare a function in Python."
        )

        self.assertTrue(res["success"])
        self.assertIsNotNone(res["question_id"])

        # Fetch question by ID
        q = self.service.get_question_by_id(res["question_id"])
        self.assertIsNotNone(q)
        self.assertEqual(q.category, "Python")
        self.assertEqual(q.topic, "Basics")
        self.assertEqual(q.difficulty, "easy")
        self.assertEqual(q.correct_answer, "B")
        self.assertTrue(q.check_answer("B"))
        self.assertTrue(q.check_answer("def"))

    def test_get_questions_by_category(self):
        """Test filtering questions by category."""
        self.service.add_question("Python", "OOP", "easy", "What is self?", "A", "B", "C", "D", "A")
        self.service.add_question("Java", "OOP", "medium", "What is JVM?", "A", "B", "C", "D", "B")
        self.service.add_question("Python", "Data Structures", "hard", "What is a list comprehension?", "A", "B", "C", "D", "C")

        py_questions = self.service.get_questions_by_category("Python")
        self.assertEqual(len(py_questions), 2)
        for q in py_questions:
            self.assertEqual(q.category, "Python")

        java_questions = self.service.get_questions_by_category("Java")
        self.assertEqual(len(java_questions), 1)
        self.assertEqual(java_questions[0].category, "Java")

    def test_get_questions_by_topic(self):
        """Test filtering questions by topic."""
        self.service.add_question("DBMS", "Normalization", "medium", "What is 1NF?", "A", "B", "C", "D", "A")
        self.service.add_question("DBMS", "SQL Queries", "easy", "What is SELECT?", "A", "B", "C", "D", "B")
        self.service.add_question("C++", "Normalization", "hard", "What is BCNF?", "A", "B", "C", "D", "C")

        norm_questions = self.service.get_questions_by_topic("Normalization")
        self.assertEqual(len(norm_questions), 2)

    def test_get_questions_by_difficulty(self):
        """Test filtering questions by difficulty."""
        self.service.add_question("Computer Networks", "TCP/IP", "easy", "What is IP?", "A", "B", "C", "D", "A")
        self.service.add_question("Computer Networks", "Routing", "medium", "What is OSPF?", "A", "B", "C", "D", "B")
        self.service.add_question("General Knowledge", "Geography", "hard", "What is the capital of Nepal?", "A", "B", "C", "D", "C")

        easy_qs = self.service.get_questions_by_difficulty("easy")
        self.assertEqual(len(easy_qs), 1)
        self.assertEqual(easy_qs[0].difficulty, "easy")

        hard_qs = self.service.get_questions_by_difficulty("hard")
        self.assertEqual(len(hard_qs), 1)
        self.assertEqual(hard_qs[0].difficulty, "hard")

    def test_random_question_selection(self):
        """Test random question selection for automated quiz generation."""
        for i in range(15):
            self.service.add_question(
                category="Python",
                topic=f"Topic_{i}",
                difficulty="medium" if i % 2 == 0 else "easy",
                question_text=f"Sample Question #{i} text?",
                option_a="A", option_b="B", option_c="C", option_d="D",
                correct_answer="A"
            )

        random_5 = self.service.get_random_questions(category="Python", count=5)
        self.assertEqual(len(random_5), 5)
        self.assertTrue(all(q.category == "Python" for q in random_5))

        random_medium_3 = self.service.get_random_questions(category="Python", difficulty="medium", count=3)
        self.assertEqual(len(random_medium_3), 3)
        self.assertTrue(all(q.difficulty == "medium" for q in random_medium_3))

    def test_update_question(self):
        """Test updating an existing question."""
        res = self.service.add_question(
            category="C++",
            topic="Pointers",
            difficulty="medium",
            question_text="What is a raw pointer?",
            option_a="A", option_b="B", option_c="C", option_d="D",
            correct_answer="A"
        )
        qid = res["question_id"]

        update_res = self.service.update_question(
            question_id=qid,
            category="C++",
            topic="Memory Management",
            difficulty="hard",
            question_text="What is a smart pointer in C++11?",
            option_a="std::unique_ptr",
            option_b="void*",
            option_c="int*",
            option_d="malloc",
            correct_answer="A",
            explanation="std::unique_ptr manages automatic memory cleanup."
        )

        self.assertTrue(update_res["success"])
        updated_q = update_res["question"]
        self.assertEqual(updated_q.topic, "Memory Management")
        self.assertEqual(updated_q.difficulty, "hard")
        self.assertEqual(updated_q.option_a, "std::unique_ptr")

    def test_delete_question(self):
        """Test deleting a question by ID."""
        res = self.service.add_question(
            category="General Knowledge",
            topic="Trivia",
            difficulty="easy",
            question_text="Temporary trivia question?",
            option_a="A", option_b="B", option_c="C", option_d="D",
            correct_answer="A"
        )
        qid = res["question_id"]

        del_res = self.service.delete_question(qid)
        self.assertTrue(del_res["success"])

        # Verify question is no longer in DB
        self.assertIsNone(self.service.get_question_by_id(qid))

        # Re-deleting returns error
        del_again = self.service.delete_question(qid)
        self.assertFalse(del_again["success"])


if __name__ == "__main__":
    unittest.main()
