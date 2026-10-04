"""
tests/test_full_workflow_audit.py
----------------------------------
End-to-end integration audit test suite verifying complete Student and Admin user flows:

Student Flow:
Register -> Login -> Dashboard -> Normal Quiz -> Submit -> Result -> Review Answers ->
History -> Performance -> AI Analysis -> Practice Weak Areas -> Adaptive Quiz ->
AI Study Plan -> AI Study Assistant -> Logout

Admin Flow:
Admin Login -> Admin Panel -> Add Question -> Edit Question -> Delete Question ->
Generate AI Questions -> Review Pending Queue -> Approve Question -> Verify Available in Bank
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.database import DatabaseManager
from database.schema import seed_default_admin
from gui.app import App
from gui.admin_panel import AdminPanelScreen
from gui.ai_assistant import AIAssistantScreen
from gui.history import HistoryScreen
from gui.leaderboard import LeaderboardScreen
from gui.performance import PerformanceScreen
from gui.quiz_screen import QuizScreen
from gui.quiz_selection import QuizSelectionScreen
from gui.result_screen import ResultScreen
from gui.student_dashboard import StudentDashboardScreen
from gui.study_plan import StudyPlanScreen
from services.ai_service import AIService
from services.authentication import AuthenticationService
from services.quiz_service import QuizService
from services.result_service import ResultService


class TestFullWorkflowAudit(unittest.TestCase):
    """
    End-to-end audit test verifying student and admin workflows.
    """

    def setUp(self):
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        self.db_mgr = DatabaseManager(db_path=self.temp_db_path)
        self.db_mgr.initialize_database()

        self.auth_service = AuthenticationService(db_mgr=self.db_mgr)
        self.quiz_service = QuizService(db_mgr=self.db_mgr)
        self.result_service = ResultService(db_mgr=self.db_mgr)
        self.ai_service = AIService(api_key=None)

        self.app = App(auth_service=self.auth_service)
        self.app.withdraw()

        # Seed standard questions
        self.q1 = self.quiz_service.add_question("Python", "Variables", "easy", "What is x = 10?", "Int", "Float", "Str", "Bool", "A")
        self.q2 = self.quiz_service.add_question("Python", "OOP", "medium", "What is self in Python?", "Instance", "Class", "Module", "Global", "A")
        self.q3 = self.quiz_service.add_question("DBMS", "SQL", "hard", "What is SELECT?", "Query", "Delete", "Drop", "Create", "A")

    def tearDown(self):
        self.app.destroy()
        os.close(self.temp_db_fd)
        if os.path.exists(self.temp_db_path):
            os.remove(self.temp_db_path)

    def test_complete_student_flow(self):
        """Verify Student Flow: Register -> Login -> Quiz -> Submit -> Result -> Review -> History -> Performance -> Weak Areas -> Study Plan -> Assistant -> Logout"""
        # 1. Register
        reg = self.auth_service.register_user("Alice Audit", "alice_audit", "alice@audit.edu", "Password123!", "student")
        self.assertTrue(reg["success"])

        # 2. Login
        login_res = self.auth_service.login_user("alice_audit", "Password123!")
        self.assertTrue(login_res["success"])
        self.assertIsNotNone(self.auth_service.current_user)

        # 3. Student Dashboard Screen
        self.app.show_dashboard()
        self.assertIsInstance(self.app.current_screen, StudentDashboardScreen)

        # 4. Normal Quiz Launch & Submission
        qs = [self.quiz_service.get_question_by_id(self.q1["question_id"]), self.quiz_service.get_question_by_id(self.q2["question_id"])]
        self.app.show_screen(QuizScreen, quiz_config={"category": "Python", "difficulty": "easy"}, questions=qs)
        quiz_screen = self.app.current_screen
        quiz_screen._on_option_selected("A")
        quiz_screen._on_next_click()
        quiz_screen._on_option_selected("B")

        sub_res = self.quiz_service.submit_quiz_attempt(
            user_id=self.auth_service.current_user.id,
            quiz_config={"category": "Python", "difficulty": "easy"},
            questions=qs,
            user_answers=quiz_screen.user_answers,
            time_taken=15
        )
        self.assertTrue(sub_res["success"])
        result_id = sub_res["result_id"]

        # 5. Result Screen & Answer Review
        res_obj = self.result_service.get_result_by_id(result_id)
        self.assertIsNotNone(res_obj)
        attempts = self.result_service.get_result_details(result_id)
        self.assertEqual(len(attempts), 2)
        self.app.show_screen(ResultScreen, result_id=result_id)


        # 6. History Screen
        self.app.show_history()
        self.assertIsInstance(self.app.current_screen, HistoryScreen)

        # 7. Performance Screen & AI Analysis
        self.app.show_performance()
        self.assertIsInstance(self.app.current_screen, PerformanceScreen)
        ai_perf = self.result_service.generate_and_save_ai_analysis(self.auth_service.current_user.id)
        self.assertIn("strengths", ai_perf)




        # 8. Practice My Weak Areas (Adaptive Quiz)
        rec = self.quiz_service.get_adaptive_difficulty_recommendation(self.auth_service.current_user.id, category="Python")
        self.assertIn(rec["recommended_difficulty"], ["easy", "medium", "hard"])


        weak_quiz_res = self.quiz_service.generate_weak_area_quiz(self.auth_service.current_user.id, count=5)
        self.assertTrue(weak_quiz_res["success"])
        self.assertGreater(len(weak_quiz_res["questions"]), 0)


        # 9. AI Study Plan
        self.app.show_study_plan()
        self.assertIsInstance(self.app.current_screen, StudyPlanScreen)
        plan = self.result_service.generate_and_save_study_plan(self.auth_service.current_user.id)
        self.assertIn("study_plan", plan)



        # 10. AI Study Assistant Chat
        self.app.show_ai_assistant()
        self.assertIsInstance(self.app.current_screen, AIAssistantScreen)
        chat_res = self.ai_service.chat_with_student("Explain variables in Python")
        self.assertIn("response", chat_res)


        # 11. Logout
        logout_res = self.auth_service.logout()
        self.assertTrue(logout_res)
        self.assertIsNone(self.auth_service.current_user)

    def test_complete_admin_flow(self):
        """Verify Admin Flow: Login -> Admin Panel -> Add Q -> Edit Q -> Delete Q -> AI Gen -> Review -> Approve -> Available in Bank"""
        # 1. Seed & Admin Login
        seed_default_admin(self.db_mgr)
        login_res = self.auth_service.login_user("admin", "admin123")
        self.assertTrue(login_res["success"])
        self.assertTrue(self.auth_service.current_user.is_admin())

        # 2. Admin Panel Screen
        self.app.show_dashboard()
        self.assertIsInstance(self.app.current_screen, AdminPanelScreen)



        # 3. Add Question
        new_q = self.quiz_service.add_question("Java", "Basics", "easy", "What is JVM?", "Machine", "Compiler", "IDE", "OS", "A")
        self.assertTrue(new_q["success"])
        q_id = new_q["question_id"]

        # 4. Edit Question
        edit_res = self.quiz_service.update_question(q_id, "Java", "Basics", "easy", "What is JVM in Java?", "Java Virtual Machine", "Compiler", "IDE", "OS", "A", "JVM stands for Java Virtual Machine")
        self.assertTrue(edit_res["success"])
        updated = self.quiz_service.get_question_by_id(q_id)
        self.assertEqual(updated.question_text, "What is JVM in Java?")
        self.assertEqual(updated.option_a, "Java Virtual Machine")


        # 5. Delete Question
        del_q = self.quiz_service.add_question("Java", "DeleteMe", "easy", "Temporary Question?", "A", "B", "C", "D", "A")
        del_res = self.quiz_service.delete_question(del_q["question_id"])
        self.assertTrue(del_res["success"])

        # 6. Generate AI Questions & Stage in Pending Queue
        stage_res = self.quiz_service.generate_and_stage_ai_questions(
            topic="Pointers", category="C++", difficulty="hard", count=2
        )
        self.assertTrue(stage_res["success"])
        self.assertGreaterEqual(stage_res["staged_count"], 2)

        # Verify AI Questions are staged with approved_by_admin = 0
        pending = self.quiz_service.get_pending_ai_questions()
        self.assertGreaterEqual(len(pending), 2)

        # 7. Approve Question
        ai_q_id = pending[0]["id"]
        appr_res = self.quiz_service.approve_ai_question(ai_q_id)
        self.assertTrue(appr_res["success"])

        # 8. Verify Approved Question is now available in active Question Bank
        approved_q = self.quiz_service.get_question_by_id(appr_res["question_id"])
        self.assertIsNotNone(approved_q)
        self.assertEqual(approved_q.category, "C++")



if __name__ == "__main__":
    unittest.main()
