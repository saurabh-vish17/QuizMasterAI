"""
gui/app.py
----------
Main Application Controller for QuizMaster AI.
Manages root Tkinter window, screen navigation, user session persistence,
and theme styling.
"""

import tkinter as tk
from typing import Optional, Type
from services.authentication import AuthenticationService
from utils.constants import BG_PRIMARY


class App(tk.Tk):
    """
    Central Application Window Controller inheriting from tk.Tk.
    Only ONE root window instance is created throughout the application lifecycle.
    """

    def __init__(self, auth_service: Optional[AuthenticationService] = None):
        super().__init__()

        self.title("QuizMaster AI — Interactive Quiz Management System")
        self.geometry("1024x680")
        self.minsize(850, 600)
        self.configure(bg=BG_PRIMARY)

        # Center Window on Screen
        self._center_window(1024, 680)

        # Initialize shared Authentication Service
        self.auth_service = auth_service if auth_service is not None else AuthenticationService()

        # Navigation Container Frame
        self.container = tk.Frame(self, bg=BG_PRIMARY)
        self.container.pack(side="top", fill="both", expand=True)

        self.current_screen: Optional[tk.Frame] = None

        # Start on Welcome Screen
        self.show_welcome()

    def _center_window(self, width: int, height: int) -> None:
        """Centers the root window on the primary screen monitor."""
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{max(0, x)}+{max(0, y)}")

    def show_screen(self, screen_class: Type[tk.Frame], *args, **kwargs) -> None:
        """
        Reusable navigation mechanism. Destroys current active screen frame
        and instantiates the target screen frame cleanly within the main container.
        """
        if self.current_screen is not None:
            self.current_screen.destroy()

        self.current_screen = screen_class(self.container, self, *args, **kwargs)
        self.current_screen.pack(fill="both", expand=True)

    # --- Reusable Route Helper Methods ---
    def show_welcome(self) -> None:
        """Navigates to the Welcome Screen."""
        from gui.welcome import WelcomeScreen
        self.show_screen(WelcomeScreen)

    def show_login(self) -> None:
        """Navigates to the Login Screen."""
        from gui.login import LoginScreen
        self.show_screen(LoginScreen)

    def show_register(self) -> None:
        """Navigates to the Register Screen."""
        from gui.register import RegisterScreen
        self.show_screen(RegisterScreen)

    def show_dashboard(self) -> None:
        """
        Routes the logged-in user to either AdminPanelScreen or StudentDashboardScreen
        based on active session role.
        """
        user = self.auth_service.current_user
        if not user:
            self.show_welcome()
            return

        if user.is_admin():
            from gui.admin_panel import AdminPanelScreen
            self.show_screen(AdminPanelScreen)
        else:
            from gui.student_dashboard import StudentDashboardScreen
            self.show_screen(StudentDashboardScreen)

    # --- Student Portal Navigation Hooks ---
    def show_quiz_selection(self) -> None:
        """Navigates to Quiz Selection Screen."""
        from gui.quiz_selection import QuizSelectionScreen
        self.show_screen(QuizSelectionScreen)

    def start_weak_area_quiz(self) -> None:
        """
        Generates and launches a targeted weak area quiz using student quiz history,
        adaptive difficulty recommendation, and approved database questions.
        """
        from services.quiz_service import QuizService
        from tkinter import messagebox

        user = self.auth_service.current_user
        if not user:
            self.show_welcome()
            return

        quiz_service = QuizService(db_mgr=self.auth_service.db_mgr)
        res = quiz_service.generate_weak_area_quiz(user_id=user.id, count=10)

        questions = res.get("questions", [])
        if not questions:
            messagebox.showinfo(
                "No Questions Available",
                "No approved questions are currently available in the question bank for weak areas.\n"
                "Try attempting a standard quiz from Quiz Selection!",
                parent=self
            )
            return

        self.show_quiz_screen(quiz_config=res["quiz_config"], questions=questions)

    def show_quiz_screen(self, quiz_config: Optional[dict] = None, questions: Optional[list] = None) -> None:
        """Navigates to active Quiz Screen with selected parameters."""
        from gui.quiz_screen import QuizScreen
        self.show_screen(QuizScreen, quiz_config=quiz_config, questions=questions)

    def show_result_screen(self, result_id: int) -> None:
        """Navigates to Result Screen for the given result_id."""
        from gui.result_screen import ResultScreen
        self.show_screen(ResultScreen, result_id=result_id)

    def show_history(self) -> None:
        """Navigates to Quiz Attempt History Screen."""
        from gui.history import HistoryScreen
        self.show_screen(HistoryScreen)

    def show_leaderboard(self) -> None:
        """Navigates to Student Leaderboard Screen."""
        from gui.leaderboard import LeaderboardScreen
        self.show_screen(LeaderboardScreen)

    def show_performance(self) -> None:
        """Navigates to Performance Analytics Screen."""
        from gui.performance import PerformanceScreen
        self.show_screen(PerformanceScreen)

    def show_study_plan(self) -> None:
        """Navigates to AI Study Plan Screen."""
        from gui.study_plan import StudyPlanScreen
        self.show_screen(StudyPlanScreen)

    def show_ai_assistant(self) -> None:
        """Navigates to AI Study Assistant Screen."""
        from gui.ai_assistant import AIAssistantScreen
        self.show_screen(AIAssistantScreen)

    def logout(self) -> None:
        """
        Clears current user session and navigates back to Welcome Screen.
        """
        from tkinter import messagebox
        confirm = messagebox.askyesno(
            "Confirm Logout",
            "Are you sure you want to log out of QuizMaster AI?",
            icon="question",
            parent=self
        )
        if confirm:
            self.auth_service.logout()
            self.show_welcome()

