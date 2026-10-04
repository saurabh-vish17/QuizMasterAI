"""
tests/test_gui_navigation.py
-----------------------------
Unit and integration tests for App window navigation controller and screen transitions.
Verifies clean screen switching, single-root window instance, and role-based dashboard routing.
"""

import os
import tempfile
import unittest
import tkinter as tk

from database.database import DatabaseManager
from gui.admin_panel import AdminPanelScreen
from gui.ai_assistant import AIAssistantScreen
from gui.app import App
from gui.history import HistoryScreen
from gui.leaderboard import LeaderboardScreen
from gui.login import LoginScreen
from gui.performance import PerformanceScreen
from gui.quiz_selection import QuizSelectionScreen
from gui.register import RegisterScreen
from gui.student_dashboard import StudentDashboardScreen
from gui.study_plan import StudyPlanScreen
from gui.welcome import WelcomeScreen
from services.authentication import AuthenticationService


class TestGuiNavigation(unittest.TestCase):
    """
    Test suite for GUI navigation, screen transitions, and session routing.
    """

    def setUp(self):
        """Set up an isolated database and headless Tkinter App instance."""
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        self.db_mgr = DatabaseManager(db_path=self.temp_db_path)
        self.db_mgr.initialize_database()

        self.auth_service = AuthenticationService(db_mgr=self.db_mgr)

        # Create App controller and withdraw window to prevent popup during headless testing
        self.app = App(auth_service=self.auth_service)
        self.app.withdraw()

    def tearDown(self):
        """Clean up App instance and temporary database."""
        self.app.destroy()
        os.close(self.temp_db_fd)
        if os.path.exists(self.temp_db_path):
            os.remove(self.temp_db_path)

    def test_initial_screen_is_welcome(self):
        """Verify that app initializes on WelcomeScreen."""
        self.assertIsInstance(self.app.current_screen, WelcomeScreen)

    def test_navigate_to_login_screen(self):
        """Verify navigation to LoginScreen."""
        self.app.show_login()
        self.assertIsInstance(self.app.current_screen, LoginScreen)

    def test_navigate_to_register_screen(self):
        """Verify navigation to RegisterScreen."""
        self.app.show_register()
        self.assertIsInstance(self.app.current_screen, RegisterScreen)

    def test_unauthenticated_dashboard_routing(self):
        """Verify that show_dashboard routes to WelcomeScreen if no user is logged in."""
        self.app.show_dashboard()
        self.assertIsInstance(self.app.current_screen, WelcomeScreen)

    def test_student_dashboard_routing(self):
        """Verify show_dashboard routes to StudentDashboardScreen for student role."""
        self.auth_service.register_user(
            name="Alice Student",
            username="alicestudent",
            email="alice@test.com",
            password="password123",
            role="student"
        )
        self.auth_service.login_user("alicestudent", "password123")

        self.app.show_dashboard()
        self.assertIsInstance(self.app.current_screen, StudentDashboardScreen)

    def test_student_dashboard_feature_hooks(self):
        """Verify navigation hooks from Student Dashboard to feature screens."""
        self.auth_service.register_user(
            name="Alice Student",
            username="alicestudent",
            email="alice@test.com",
            password="password123",
            role="student"
        )
        self.auth_service.login_user("alicestudent", "password123")
        self.app.show_dashboard()

        # Test Start Quiz hook
        self.app.show_quiz_selection()
        self.assertIsInstance(self.app.current_screen, QuizSelectionScreen)

        # Test History hook
        self.app.show_history()
        self.assertIsInstance(self.app.current_screen, HistoryScreen)

        # Test Leaderboard hook
        self.app.show_leaderboard()
        self.assertIsInstance(self.app.current_screen, LeaderboardScreen)

        # Test Performance hook
        self.app.show_performance()
        self.assertIsInstance(self.app.current_screen, PerformanceScreen)

        # Test Study Plan hook
        self.app.show_study_plan()
        self.assertIsInstance(self.app.current_screen, StudyPlanScreen)

        # Test AI Assistant hook
        self.app.show_ai_assistant()
        self.assertIsInstance(self.app.current_screen, AIAssistantScreen)

    def test_admin_dashboard_routing(self):
        """Verify show_dashboard routes to AdminPanelScreen for admin role."""
        self.auth_service.register_user(
            name="Bob Admin",
            username="bobadmin",
            email="bob@admin.com",
            password="adminpassword123",
            role="admin",
            admin_key="ADMIN123"
        )
        self.auth_service.login_user("bobadmin", "adminpassword123")

        self.app.show_dashboard()
        self.assertIsInstance(self.app.current_screen, AdminPanelScreen)

    def test_logout_navigation(self):
        """Verify logout clears session and navigates back to WelcomeScreen."""
        self.auth_service.register_user("User", "testuser", "user@test.com", "pass123")
        self.auth_service.login_user("testuser", "pass123")
        self.app.show_dashboard()
        self.assertIsInstance(self.app.current_screen, StudentDashboardScreen)

        # Trigger logout
        self.app.logout()
        self.assertIsNone(self.auth_service.current_user)
        self.assertIsInstance(self.app.current_screen, WelcomeScreen)


if __name__ == "__main__":
    unittest.main()
