"""
tests/test_ai_assistant.py
---------------------------
Unit and integration tests for AI Study Assistant in QuizMaster AI.

Test Cases:
    1. Test AIService.chat_with_student with all supported request types:
       (explain_concept, explain_question, give_hint, summarize_topic, suggest_topics, explain_correct_answer).
    2. Test offline fallback responses for each request type when AI API is unavailable.
    3. Test AIAssistantScreen instantiation, quick request chips, and turn count limiting.
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.database import DatabaseManager
from gui.ai_assistant import AIAssistantScreen, MAX_CONVERSATION_TURNS
from gui.app import App
from services.ai_service import AIService
from services.authentication import AuthenticationService


class TestAIAssistant(unittest.TestCase):
    """
    Test suite for AI Study Assistant requests and UI component.
    """

    def setUp(self):
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        self.db_mgr = DatabaseManager(db_path=self.temp_db_path)
        self.db_mgr.initialize_database()

        self.auth_service = AuthenticationService(db_mgr=self.db_mgr)
        self.app = App(auth_service=self.auth_service)
        self.app.withdraw()

        # Register & Login Student
        self.auth_service.register_user("Chat Student", "chat_student", "chat@example.com", "StudentPass123!", "student")
        self.auth_service.login_user("chat_student", "StudentPass123!")

    def tearDown(self):
        self.app.destroy()
        os.close(self.temp_db_fd)
        if os.path.exists(self.temp_db_path):
            os.remove(self.temp_db_path)

    def test_ai_service_chat_request_types(self):
        """Verify chat_with_student supports all required request types."""
        ai_service = AIService(api_key="mock_key")
        ai_service._call_gemini = MagicMock(return_value='''{
            "response": "Detailed academic explanation of concept.",
            "suggested_followups": ["Followup 1?", "Followup 2?"]
        }''')

        req_types = [
            "explain_concept",
            "explain_question",
            "give_hint",
            "summarize_topic",
            "suggest_topics",
            "explain_correct_answer"
        ]

        for req in req_types:
            res = ai_service.chat_with_student("Test input message", request_type=req)
            self.assertTrue(res["success"])
            self.assertIn("response", res)
            self.assertIn("suggested_followups", res)

    def test_ai_service_chat_offline_fallback(self):
        """Verify offline fallbacks for supported request types."""
        ai_service = AIService(api_key="")  # Unconfigured API key

        res_hint = ai_service.chat_with_student("OOP Inheritance", request_type="give_hint")
        self.assertFalse(res_hint["success"])
        self.assertIn("Hint for", res_hint["response"])

        res_topics = ai_service.chat_with_student("What to practice?", request_type="suggest_topics")
        self.assertFalse(res_topics["success"])
        self.assertIn("Recommended Practice Topics", res_topics["response"])

    def test_ai_assistant_screen_widgets_and_turn_limit(self):
        """Verify AIAssistantScreen instantiates correctly and tracks turn count."""
        screen = AIAssistantScreen(self.app.container, self.app)
        self.assertIsNotNone(screen.txt_input)
        self.assertIsNotNone(screen.btn_send)
        self.assertEqual(screen.turn_count, 0)

        # Simulate messages up to turn limit
        for i in range(1, MAX_CONVERSATION_TURNS + 1):
            screen._process_message(f"Test question {i}")

        self.assertEqual(screen.turn_count, MAX_CONVERSATION_TURNS)

        # Clear Chat
        screen._clear_chat()
        self.assertEqual(screen.turn_count, 0)
        self.assertEqual(len(screen.chat_history), 0)


if __name__ == "__main__":
    unittest.main()
