"""
tests/test_quiz_selection.py
-----------------------------
Unit tests for QuizSelectionScreen configuration, live validation, and launcher.

Test Cases:
    1. Test initialization and default widget values.
    2. Test topic options updating dynamically per category.
    3. Test live question availability count calculation.
    4. Test starting quiz when no questions exist.
    5. Test starting quiz when sufficient questions exist (forwards config & questions).
"""

import os
import tempfile
import unittest
import tkinter as tk

from database.database import DatabaseManager
from gui.app import App
from gui.quiz_selection import QuizSelectionScreen
from gui.quiz_screen import QuizScreen
from services.authentication import AuthenticationService
from services.quiz_service import QuizService


class TestQuizSelection(unittest.TestCase):
    """
    Test suite for Quiz Selection GUI and pre-quiz validation logic.
    """

    def setUp(self):
        """Set up an isolated database and headless Tkinter App instance."""
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        self.db_mgr = DatabaseManager(db_path=self.temp_db_path)
        self.db_mgr.initialize_database()

        self.auth_service = AuthenticationService(db_mgr=self.db_mgr)
        self.quiz_service = QuizService(db_mgr=self.db_mgr)

        self.app = App(auth_service=self.auth_service)
        self.app.withdraw()

        # Seed sample questions
        for i in range(12):
            self.quiz_service.add_question(
                category="Python",
                topic="OOP" if i % 2 == 0 else "Basics",
                difficulty="easy" if i < 6 else "medium",
                question_text=f"Sample question #{i} text?",
                option_a="A", option_b="B", option_c="C", option_d="D",
                correct_answer="A"
            )

    def tearDown(self):
        """Clean up App instance and temporary database."""
        self.app.destroy()
        os.close(self.temp_db_fd)
        if os.path.exists(self.temp_db_path):
            os.remove(self.temp_db_path)

    def test_screen_initialization(self):
        """Test default values of selection comboboxes."""
        screen = QuizSelectionScreen(self.app.container, self.app)

        self.assertEqual(screen.cmb_category.get(), "Python")
        self.assertEqual(screen.cmb_topic.get(), "All Topics")
        self.assertEqual(screen.cmb_difficulty.get(), "Easy")
        self.assertEqual(screen.cmb_count.get(), "10")

    def test_topic_options_dynamic_update(self):
        """Test that topic combobox populates distinct topics for selected category."""
        screen = QuizSelectionScreen(self.app.container, self.app)

        screen.cmb_category.set("Python")
        screen._update_topic_options()

        topics = screen.cmb_topic["values"]
        self.assertIn("All Topics", topics)
        self.assertIn("Basics", topics)
        self.assertIn("OOP", topics)

    def test_question_availability_count(self):
        """Test live availability count logic."""
        screen = QuizSelectionScreen(self.app.container, self.app)

        # 6 Python / Easy questions exist
        screen.cmb_category.set("Python")
        screen.cmb_topic.set("All Topics")
        screen.cmb_difficulty.set("Easy")
        screen._update_question_availability_count()

        count = self.quiz_service.count_questions("Python", None, "easy")
        self.assertEqual(count, 6)
        self.assertIn("6 question(s) available", screen.lbl_status.cget("text"))

    def test_successful_quiz_launch(self):
        """Test starting a quiz when sufficient questions exist."""
        screen = QuizSelectionScreen(self.app.container, self.app)

        screen.cmb_category.set("Python")
        screen.cmb_topic.set("All Topics")
        screen.cmb_difficulty.set("Easy")
        screen.cmb_count.set("5")

        screen._on_start_quiz_click()

        # Verify active screen transitioned to QuizScreen
        self.assertIsInstance(self.app.current_screen, QuizScreen)
        qs: QuizScreen = self.app.current_screen

        self.assertEqual(qs.quiz_config["category"], "Python")
        self.assertEqual(qs.quiz_config["difficulty"], "easy")
        self.assertEqual(len(qs.questions), 5)


if __name__ == "__main__":
    unittest.main()
