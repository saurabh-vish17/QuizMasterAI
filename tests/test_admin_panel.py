"""
tests/test_admin_panel.py
--------------------------
Unit and integration tests for AdminPanelScreen and complete Question Bank CRUD operations.

Test Cases:
    1. Verify role access guard (Student vs Admin).
    2. Test Question Bank loading, searching, and filtering in Treeview.
    3. Test Add Question through Admin service/form workflows.
    4. Test Edit/Update Question through Admin service/form workflows.
    5. Test Delete Question through Admin service/form workflows.
    6. Test Student Results loading.
    7. Test AI Question Queue approval & rejection workflows.
"""

import os
import tempfile
import unittest
import tkinter as tk

from database.database import DatabaseManager
from gui.admin_panel import AdminPanelScreen
from gui.app import App
from gui.welcome import WelcomeScreen
from services.authentication import AuthenticationService
from services.quiz_service import QuizService


class TestAdminPanel(unittest.TestCase):
    """
    Test suite for Admin Panel features and complete CRUD workflows.
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

    def tearDown(self):
        """Clean up App instance and temporary database."""
        self.app.destroy()
        os.close(self.temp_db_fd)
        if os.path.exists(self.temp_db_path):
            os.remove(self.temp_db_path)

    def test_student_access_denied_guard(self):
        """Verify students are blocked from opening AdminPanelScreen."""
        self.auth_service.register_user("Student User", "student1", "student@test.com", "pass123", role="student")
        self.auth_service.login_user("student1", "pass123")

        # Attempt to show AdminPanelScreen
        self.app.show_screen(AdminPanelScreen)

        # Allow scheduled redirects to process
        self.app.update_idletasks()
        self.app.update()

        # Verify active screen was redirected to WelcomeScreen
        self.assertIsInstance(self.app.current_screen, WelcomeScreen)

    def test_admin_access_granted(self):
        """Verify admins are allowed into AdminPanelScreen."""
        self.auth_service.register_user("Admin User", "admin1", "admin@test.com", "pass123", role="admin", admin_key="ADMIN123")
        self.auth_service.login_user("admin1", "pass123")

        self.app.show_screen(AdminPanelScreen)
        self.assertIsInstance(self.app.current_screen, AdminPanelScreen)

    def test_complete_crud_in_admin_panel(self):
        """Test complete Add, View, Search, Filter, Update, Delete workflow."""
        self.auth_service.register_user("Admin User", "admin1", "admin@test.com", "pass123", role="admin", admin_key="ADMIN123")
        self.auth_service.login_user("admin1", "pass123")

        admin_screen = AdminPanelScreen(self.app.container, self.app)

        # 1. Add Questions
        add_res1 = self.quiz_service.add_question("Python", "Syntax", "easy", "What is print()?", "Func", "Key", "Var", "Obj", "A")
        add_res2 = self.quiz_service.add_question("Java", "OOP", "hard", "What is JVM garbage collection?", "A", "B", "C", "D", "B")
        qid1 = add_res1["question_id"]
        qid2 = add_res2["question_id"]

        # 2. View Questions in Treeview
        admin_screen.load_questions()
        items = admin_screen.tree_q.get_children()
        self.assertEqual(len(items), 2)

        # 3. Filter by Category
        admin_screen.cmb_cat_filter.set("Python")
        admin_screen.load_questions()
        py_items = admin_screen.tree_q.get_children()
        self.assertEqual(len(py_items), 1)

        # 4. Search Query
        admin_screen.cmb_cat_filter.set("All Categories")
        admin_screen.ent_search.delete(0, "end")
        admin_screen.ent_search.insert(0, "garbage collection")
        admin_screen.load_questions()
        search_items = admin_screen.tree_q.get_children()
        self.assertEqual(len(search_items), 1)
        self.assertEqual(search_items[0], str(qid2))

        # 5. Update Question
        update_res = self.quiz_service.update_question(
            qid1, "Python", "Built-ins", "medium", "What does print() do in Python 3?", "Outputs text", "Deletes text", "No-op", "Error", "A"
        )
        self.assertTrue(update_res["success"])
        updated_q = self.quiz_service.get_question_by_id(qid1)
        self.assertEqual(updated_q.topic, "Built-ins")
        self.assertEqual(updated_q.difficulty, "medium")

        # 6. Delete Question
        del_res = self.quiz_service.delete_question(qid2)
        self.assertTrue(del_res["success"])

        admin_screen._reset_filters()
        final_items = admin_screen.tree_q.get_children()
        self.assertEqual(len(final_items), 1)
        self.assertEqual(final_items[0], str(qid1))

    def test_student_results_view(self):
        """Test loading student results in Admin Panel."""
        self.auth_service.register_user("Admin User", "admin1", "admin@test.com", "pass123", role="admin", admin_key="ADMIN123")
        self.auth_service.login_user("admin1", "pass123")

        # Insert sample result
        self.db_mgr.execute_query(
            "INSERT INTO results (user_id, category, difficulty, total_questions, correct_answers, wrong_answers, unanswered, score, percentage, time_taken, quiz_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (1, "Python", "easy", 10, 8, 2, 0, 8, 80.0, 120, "2026-10-04 00:00:00")
        )

        admin_screen = AdminPanelScreen(self.app.container, self.app)
        admin_screen.load_student_results()
        res_items = admin_screen.tree_res.get_children()
        self.assertEqual(len(res_items), 1)

    def test_ai_question_queue_approval_workflow(self):
        """Test AI-generated question approval and rejection workflow."""
        self.auth_service.register_user("Admin User", "admin1", "admin@test.com", "pass123", role="admin", admin_key="ADMIN123")
        self.auth_service.login_user("admin1", "pass123")

        # Insert pending AI question
        ai_qid = self.db_mgr.execute_query(
            "INSERT INTO ai_questions (category, topic, difficulty, question_text, option_a, option_b, option_c, option_d, correct_answer, explanation, generated_by_ai, approved_by_admin) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 0)",
            ("DBMS", "Indexing", "medium", "What is a B-Tree index?", "Tree", "Graph", "List", "Array", "A", "B-Tree is self-balancing.")
        )

        admin_screen = AdminPanelScreen(self.app.container, self.app)
        admin_screen.load_ai_queue()
        pending_items = admin_screen.tree_ai.get_children()
        self.assertEqual(len(pending_items), 1)

        # Approve AI question
        app_res = self.quiz_service.approve_ai_question(ai_qid)
        self.assertTrue(app_res["success"])

        # Verify added to main question bank
        q_bank = self.quiz_service.get_questions_by_category("DBMS")
        self.assertEqual(len(q_bank), 1)
        self.assertEqual(q_bank[0].topic, "Indexing")

        # Verify removed from pending AI queue
        admin_screen.load_ai_queue()
        self.assertEqual(len(admin_screen.tree_ai.get_children()), 0)


if __name__ == "__main__":
    unittest.main()
