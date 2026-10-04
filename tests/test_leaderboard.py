"""
tests/test_leaderboard.py
--------------------------
Unit and integration tests for Leaderboard System in QuizMaster AI.

Test Cases:
    1. Test Leaderboard ranking logic (highest percentage score, highest score, fastest time).
    2. Test Category and Difficulty filtering in ResultService.get_leaderboard.
    3. Test Privacy Protection (no passwords, hashes, or emails in leaderboard data).
    4. Test LeaderboardScreen GUI rendering and filtering interactions.
"""

import os
import tempfile
import unittest

from database.database import DatabaseManager
from gui.app import App
from gui.leaderboard import LeaderboardScreen
from services.authentication import AuthenticationService
from services.quiz_service import QuizService
from services.result_service import ResultService


class TestLeaderboard(unittest.TestCase):
    """
    Test suite for Leaderboard data queries, privacy enforcement, and GUI filtering.
    """

    def setUp(self):
        """Set up isolated temporary database and populate sample attempt data for multiple students."""
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        self.db_mgr = DatabaseManager(db_path=self.temp_db_path)
        self.db_mgr.initialize_database()

        self.auth_service = AuthenticationService(db_mgr=self.db_mgr)
        self.quiz_service = QuizService(db_mgr=self.db_mgr)
        self.result_service = ResultService(db_mgr=self.db_mgr)

        self.app = App(auth_service=self.auth_service)
        self.app.withdraw()

        # Register 3 sample students
        s1 = self.auth_service.register_user("Alice Top", "alice", "alice@secret.com", "Password123!", "student")
        s2 = self.auth_service.register_user("Bob Mid", "bob", "bob@secret.com", "Password123!", "student")
        s3 = self.auth_service.register_user("Charlie High", "charlie", "charlie@secret.com", "Password123!", "student")

        self.alice_id = s1["user"].id
        self.bob_id = s2["user"].id
        self.charlie_id = s3["user"].id

        # Add sample questions
        q1 = self.quiz_service.add_question("Python", "Basics", "easy", "Python Question #1 text?", "A", "B", "C", "D", "A")
        q2 = self.quiz_service.add_question("Python", "Basics", "easy", "Python Question #2 text?", "A", "B", "C", "D", "B")
        q3 = self.quiz_service.add_question("C++", "Pointers", "hard", "C++ Question #1 text?", "A", "B", "C", "D", "C")

        qs_py = [q1["question"], q2["question"]]
        qs_cpp = [q3["question"]]

        # Submit attempts:
        # Alice: Python easy -> 2/2 (100%), time 40s
        self.quiz_service.submit_quiz_attempt(
            user_id=self.alice_id,
            quiz_config={"category": "Python", "topic": "Basics", "difficulty": "easy"},
            questions=qs_py,
            user_answers={qs_py[0].question_id: "A", qs_py[1].question_id: "B"},
            time_taken=40
        )

        # Bob: Python easy -> 1/2 (50%), time 30s
        self.quiz_service.submit_quiz_attempt(
            user_id=self.bob_id,
            quiz_config={"category": "Python", "topic": "Basics", "difficulty": "easy"},
            questions=qs_py,
            user_answers={qs_py[0].question_id: "A", qs_py[1].question_id: "C"},
            time_taken=30
        )

        # Charlie: C++ hard -> 1/1 (100%), time 20s
        self.quiz_service.submit_quiz_attempt(
            user_id=self.charlie_id,
            quiz_config={"category": "C++", "topic": "Pointers", "difficulty": "hard"},
            questions=qs_cpp,
            user_answers={qs_cpp[0].question_id: "C"},
            time_taken=20
        )

    def tearDown(self):
        """Clean up App instance and temporary database."""
        self.app.destroy()
        os.close(self.temp_db_fd)
        if os.path.exists(self.temp_db_path):
            os.remove(self.temp_db_path)

    def test_overall_leaderboard_ranking(self):
        """Test Overall leaderboard query ranking."""
        leaderboard = self.result_service.get_leaderboard()

        self.assertEqual(len(leaderboard), 3)

        # Top ranks should be 100% scores (Alice / Charlie)
        r1_name = leaderboard[0]["student_name"]
        r2_name = leaderboard[1]["student_name"]
        r3_name = leaderboard[2]["student_name"]

        self.assertIn(r1_name, ["Alice Top", "Charlie High"])
        self.assertIn(r2_name, ["Alice Top", "Charlie High"])
        self.assertEqual(r3_name, "Bob Mid")
        self.assertEqual(leaderboard[2]["formatted_percentage"], "50.0%")

    def test_category_and_difficulty_filtering(self):
        """Test filtering leaderboard by Category and Difficulty."""
        # Filter Category: Python
        py_lb = self.result_service.get_leaderboard(category="Python")
        self.assertEqual(len(py_lb), 2)
        names = [item["student_name"] for item in py_lb]
        self.assertIn("Alice Top", names)
        self.assertIn("Bob Mid", names)

        # Filter Category: C++
        cpp_lb = self.result_service.get_leaderboard(category="C++")
        self.assertEqual(len(cpp_lb), 1)
        self.assertEqual(cpp_lb[0]["student_name"], "Charlie High")

        # Filter Difficulty: Hard
        hard_lb = self.result_service.get_leaderboard(difficulty="hard")
        self.assertEqual(len(hard_lb), 1)
        self.assertEqual(hard_lb[0]["student_name"], "Charlie High")

    def test_privacy_protection_no_sensitive_fields(self):
        """Verify no sensitive fields (email, password_hash) exist in leaderboard items."""
        leaderboard = self.result_service.get_leaderboard()

        for item in leaderboard:
            self.assertNotIn("password", item)
            self.assertNotIn("password_hash", item)
            self.assertNotIn("email", item)
            # Must contain only public fields
            self.assertIn("rank", item)
            self.assertIn("student_name", item)
            self.assertIn("category", item)
            self.assertIn("score", item)
            self.assertIn("percentage", item)

    def test_leaderboard_screen_gui(self):
        """Test LeaderboardScreen widget initialization and filter updates."""
        self.auth_service.login_user("alice", "Password123!")
        screen = LeaderboardScreen(self.app.container, self.app)

        # Default overall count
        children = screen.tree.get_children()
        self.assertEqual(len(children), 3)

        # Select C++ filter
        screen.cmb_category.set("C++")
        screen._load_leaderboard()
        children_cpp = screen.tree.get_children()
        self.assertEqual(len(children_cpp), 1)


if __name__ == "__main__":
    unittest.main()
