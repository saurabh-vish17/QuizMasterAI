"""
gui/student_dashboard.py
-------------------------
AI-Powered Learning Dashboard for QuizMaster AI.

Provides an executive student portal with:
    - 5 Key Metric Cards (Overall Score, Quizzes Completed, Strongest Topic, Weakest Topic, Recommended Difficulty)
    - 6 Core Learning Sections:
        1. AI Performance Summary
        2. Recommended Quiz
        3. Weak Topics
        4. Study Plan
        5. Recent Performance
        6. AI Study Assistant
    - Quick Action Button Navigation Bar & CTAs:
        [Start Quiz], [Practice Weak Areas], [View Performance],
        [AI Study Plan], [Ask AI], [Quiz History], [Leaderboard]
"""

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING, Dict, Any, List, Optional

from services.result_service import ResultService
from services.quiz_service import QuizService
from services.ai_service import AIService
from utils.constants import (
    ACCENT_GLOW,
    ACCENT_PRIMARY,
    BG_PRIMARY,
    BG_SECONDARY,
    BG_TERTIARY,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)

if TYPE_CHECKING:
    from gui.app import App


class StudentDashboardScreen(tk.Frame):
    """
    AI-Powered Learning Dashboard Screen Component.
    """

    def __init__(self, parent: tk.Widget, controller: "App"):
        super().__init__(parent, bg=BG_PRIMARY)
        self.controller = controller
        self.result_service = ResultService(db_mgr=self.controller.auth_service.db_mgr)
        self.quiz_service = QuizService(db_mgr=self.controller.auth_service.db_mgr)
        self.ai_service = AIService()

        self._create_widgets()

    def _create_widgets(self):
        user = self.controller.auth_service.current_user
        student_name = user.name if user else "Student"

        # --- 1. Top Navigation & Action Bar ---
        navbar = tk.Frame(self, bg=BG_SECONDARY, padx=20, pady=10)
        navbar.pack(fill="x", side="top")

        lbl_logo = tk.Label(
            navbar,
            text="⚡ QuizMaster AI",
            font=("Segoe UI", 15, "bold"),
            bg=BG_SECONDARY,
            fg=ACCENT_PRIMARY
        )
        lbl_logo.pack(side="left")

        user_badge = tk.Label(
            navbar,
            text=f"👤 {student_name}",
            font=("Segoe UI", 10, "bold"),
            bg=BG_TERTIARY,
            fg=TEXT_PRIMARY,
            padx=10,
            pady=3
        )
        user_badge.pack(side="left", padx=15)

        # Logout Button
        btn_logout = tk.Button(
            navbar,
            text="LOG OUT",
            font=("Segoe UI", 8, "bold"),
            bg="#FF4C6A",
            fg="#FFFFFF",
            activebackground="#D32F2F",
            activeforeground="#FFFFFF",
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=4,
            command=self.controller.logout
        )
        btn_logout.pack(side="right", padx=(10, 0))

        # Main Quick Navigation Action Buttons
        nav_buttons = [
            ("📝 Start Quiz", self.controller.show_quiz_selection, ACCENT_PRIMARY),
            ("🎯 Practice Weak Areas", self.controller.start_weak_area_quiz, "#FF4C6A"),
            ("📈 View Performance", self.controller.show_performance, "#9C27B0"),
            ("💡 AI Study Plan", self.controller.show_study_plan, "#00BCD4"),
            ("🤖 Ask AI", self.controller.show_ai_assistant, "#FF4081"),
            ("📜 Quiz History", self.controller.show_history, "#00E676"),
            ("🏆 Leaderboard", self.controller.show_leaderboard, "#FFB300"),
        ]

        for text, cmd, col in reversed(nav_buttons):
            btn = tk.Button(
                navbar,
                text=text,
                font=("Segoe UI", 8, "bold"),
                bg=BG_TERTIARY,
                fg=TEXT_PRIMARY,
                activebackground=col,
                activeforeground="#000000",
                relief="flat",
                cursor="hand2",
                padx=8,
                pady=4,
                command=cmd
            )
            btn.pack(side="right", padx=3)

        # --- 2. Main Scrollable Container ---
        self.canvas_container = tk.Frame(self, bg=BG_PRIMARY)
        self.canvas_container.pack(fill="both", expand=True, padx=20, pady=10)

        self.canvas = tk.Canvas(self.canvas_container, bg=BG_PRIMARY, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.canvas_container, orient="vertical", command=self.canvas.yview)
        self.scrollable_content = tk.Frame(self.canvas, bg=BG_PRIMARY)

        self.scrollable_content.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_content, anchor="nw")

        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width)
        )
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # --- 3. Render Dashboard Data Sections ---
        self._load_and_render_dashboard()

    def _load_and_render_dashboard(self):
        """Fetches student statistics and renders the 5 metric cards + 6 AI sections."""
        for child in self.scrollable_content.winfo_children():
            child.destroy()

        user = self.controller.auth_service.current_user
        if not user:
            return

        student_name = user.name
        user_id = user.id

        # Gather Statistics
        perf_data = self.result_service.get_student_performance_analytics(user_id)
        topic_data = self.result_service.get_topic_performance_breakdown(user_id)
        recent_results = self.result_service.get_user_results(user_id)
        saved_plan = self.result_service.get_latest_study_plan(user_id)

        adaptive_rec = self.quiz_service.get_adaptive_difficulty_recommendation(
            user_id=user_id,
            category=perf_data.get("weakest_category", "Python"),
            ai_service=self.ai_service
        )
        rec_diff = adaptive_rec.get("recommended_level", "Medium")

        # Weak Topics Filter (< 70% accuracy)
        weak_topics = []
        for t_name, t_info in topic_data.items():
            if t_info["accuracy"] < 70.0:
                weak_topics.append((t_name, t_info["accuracy"], t_info["asked"]))

        if not weak_topics and topic_data:
            sorted_topics = sorted(topic_data.items(), key=lambda x: x[1]["accuracy"])
            for t_name, t_info in sorted_topics[:3]:
                weak_topics.append((t_name, t_info["accuracy"], t_info["asked"]))

        # --- Welcome Header Banner ---
        banner = tk.Frame(
            self.scrollable_content,
            bg=BG_SECONDARY,
            padx=20,
            pady=15,
            highlightbackground=ACCENT_PRIMARY,
            highlightthickness=1
        )
        banner.pack(fill="x", pady=(0, 15))

        b_left = tk.Frame(banner, bg=BG_SECONDARY)
        b_left.pack(side="left", fill="both", expand=True)

        lbl_welcome = tk.Label(
            b_left,
            text=f"Welcome back, {student_name}! 🎓",
            font=("Segoe UI", 16, "bold"),
            bg=BG_SECONDARY,
            fg=TEXT_PRIMARY,
            anchor="w"
        )
        lbl_welcome.pack(fill="x", pady=(0, 2))

        lbl_subtitle = tk.Label(
            b_left,
            text=f"AI Status: Adaptive level set to {rec_diff.capitalize()} | {len(weak_topics)} weak topics identified for revision.",
            font=("Segoe UI", 9),
            bg=BG_SECONDARY,
            fg=TEXT_SECONDARY,
            anchor="w"
        )
        lbl_subtitle.pack(fill="x")

        cta_frame = tk.Frame(banner, bg=BG_SECONDARY)
        cta_frame.pack(side="right")

        btn_weak_cta = tk.Button(
            cta_frame,
            text="🎯 PRACTICE WEAK AREAS",
            font=("Segoe UI", 9, "bold"),
            bg="#FF4C6A",
            fg="#FFFFFF",
            activebackground="#D32F2F",
            activeforeground="#FFFFFF",
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=6,
            command=self.controller.start_weak_area_quiz
        )
        btn_weak_cta.pack(side="left", padx=4)

        btn_quiz_cta = tk.Button(
            cta_frame,
            text="📝 START QUIZ",
            font=("Segoe UI", 9, "bold"),
            bg=ACCENT_PRIMARY,
            fg="#000000",
            activebackground=ACCENT_GLOW,
            activeforeground="#000000",
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=6,
            command=self.controller.show_quiz_selection
        )
        btn_quiz_cta.pack(side="left", padx=4)

        # --- 5 Top Metric Cards Grid ---
        metrics_frame = tk.Frame(self.scrollable_content, bg=BG_PRIMARY)
        metrics_frame.pack(fill="x", pady=(0, 15))

        for col in range(5):
            metrics_frame.columnconfigure(col, weight=1)

        avg_score_str = f"{perf_data.get('average_score', 0.0):.1f}%" if perf_data.get("has_data") else "N/A"
        quizzes_str = f"{perf_data.get('total_quizzes', 0)} Quizzes"
        strong_str = perf_data.get("strongest_category", "N/A")
        weak_str = perf_data.get("weakest_category", "N/A")

        metric_cards = [
            ("Overall Score", avg_score_str, "📈", "#00E676"),
            ("Quizzes Completed", quizzes_str, "📝", "#FFB300"),
            ("Strongest Topic", strong_str, "⭐", "#00BCD4"),
            ("Weakest Topic", weak_str, "⚠️", "#FF4C6A"),
            ("Recommended Difficulty", rec_diff.capitalize(), "⚡", "#9C27B0"),
        ]

        for idx, (title, val, icon, color) in enumerate(metric_cards):
            card = tk.Frame(
                metrics_frame,
                bg=BG_SECONDARY,
                padx=12,
                pady=10,
                highlightbackground=color,
                highlightthickness=1
            )
            card.grid(row=0, column=idx, sticky="nsew", padx=4)

            lbl_m_hdr = tk.Label(
                card,
                text=f"{icon} {title}",
                font=("Segoe UI", 8),
                bg=BG_SECONDARY,
                fg=TEXT_SECONDARY,
                anchor="w"
            )
            lbl_m_hdr.pack(fill="x")

            lbl_m_val = tk.Label(
                card,
                text=val,
                font=("Segoe UI", 12, "bold"),
                bg=BG_SECONDARY,
                fg=color,
                anchor="w"
            )
            lbl_m_val.pack(fill="x", pady=(4, 0))

        # --- 6 Core AI-Powered Sections Grid (2 Columns) ---
        grid_sections = tk.Frame(self.scrollable_content, bg=BG_PRIMARY)
        grid_sections.pack(fill="both", expand=True)

        grid_sections.columnconfigure(0, weight=1, pad=10)
        grid_sections.columnconfigure(1, weight=1, pad=10)

        # ---------------------------------------------------------------------
        # SECTION 1: AI Performance Summary
        # ---------------------------------------------------------------------
        sec1 = self._create_section_card(grid_sections, "🤖 1. AI Performance Summary", "#00E676")
        sec1.grid(row=0, column=0, sticky="nsew", pady=6)

        if perf_data.get("has_data"):
            summary_txt = (
                f"• Average Score: {avg_score_str} across {quizzes_str}.\n"
                f"• Strongest Area: {strong_str} (consistent high performance).\n"
                f"• Needs Revision: {weak_str} requires targeted practice.\n"
                f"• Trend Rationale: {adaptive_rec.get('reason', 'Maintain steady practice to improve mastery.')}"
            )
        else:
            summary_txt = "No quiz attempts recorded yet. Attempt your first quiz to generate AI performance insights!"

        lbl_s1 = tk.Label(sec1, text=summary_txt, font=("Segoe UI", 9), bg=BG_SECONDARY, fg=TEXT_PRIMARY, justify="left", anchor="nw")
        lbl_s1.pack(fill="both", expand=True, pady=(0, 10))

        btn_s1 = tk.Button(sec1, text="📈 View Performance Analysis", font=("Segoe UI", 8, "bold"), bg="#00E676", fg="#000000", relief="flat", cursor="hand2", command=self.controller.show_performance)
        btn_s1.pack(fill="x")

        # ---------------------------------------------------------------------
        # SECTION 2: Recommended Quiz
        # ---------------------------------------------------------------------
        sec2 = self._create_section_card(grid_sections, "🎯 2. Recommended Quiz", ACCENT_PRIMARY)
        sec2.grid(row=0, column=1, sticky="nsew", pady=6)

        rec_topic_str = weak_topics[0][0] if weak_topics else perf_data.get("weakest_category", "General Concepts")
        rec_txt = (
            f"• Recommended Topic: {rec_topic_str}\n"
            f"• Target Difficulty: {rec_diff.capitalize()}\n"
            f"• Question Bank: Approved Questions Only\n"
            f"• Rationale: {adaptive_rec.get('reason', 'Build confidence with adaptive practice.')}"
        )
        lbl_s2 = tk.Label(sec2, text=rec_txt, font=("Segoe UI", 9), bg=BG_SECONDARY, fg=TEXT_PRIMARY, justify="left", anchor="nw")
        lbl_s2.pack(fill="both", expand=True, pady=(0, 10))

        btn_s2 = tk.Button(sec2, text="🚀 Launch Recommended Quiz", font=("Segoe UI", 8, "bold"), bg=ACCENT_PRIMARY, fg="#000000", relief="flat", cursor="hand2", command=self.controller.start_weak_area_quiz)
        btn_s2.pack(fill="x")

        # ---------------------------------------------------------------------
        # SECTION 3: Weak Topics
        # ---------------------------------------------------------------------
        sec3 = self._create_section_card(grid_sections, "📌 3. Weak Topics", "#FF4C6A")
        sec3.grid(row=1, column=0, sticky="nsew", pady=6)

        if weak_topics:
            w_str_list = [f"• {t[0]}: {t[1]:.1f}% Accuracy ({t[2]} asked)" for t in weak_topics[:3]]
            w_txt = "\n".join(w_str_list)
        else:
            w_txt = "No weak topics detected! Your performance across attempted topics is strong (>= 70%)."

        lbl_s3 = tk.Label(sec3, text=w_txt, font=("Segoe UI", 9), bg=BG_SECONDARY, fg=TEXT_PRIMARY, justify="left", anchor="nw")
        lbl_s3.pack(fill="both", expand=True, pady=(0, 10))

        btn_s3 = tk.Button(sec3, text="🎯 Practice Weak Areas", font=("Segoe UI", 8, "bold"), bg="#FF4C6A", fg="#FFFFFF", relief="flat", cursor="hand2", command=self.controller.start_weak_area_quiz)
        btn_s3.pack(fill="x")

        # ---------------------------------------------------------------------
        # SECTION 4: Study Plan
        # ---------------------------------------------------------------------
        sec4 = self._create_section_card(grid_sections, "💡 4. AI Study Plan", "#00BCD4")
        sec4.grid(row=1, column=1, sticky="nsew", pady=6)

        if saved_plan:
            plan_txt = (
                f"• Title: {saved_plan.get('title', 'Personalized Plan')}\n"
                f"• Daily Goal: ⏱️ {saved_plan.get('suggested_practice_duration', '30 mins')} | 📝 {saved_plan.get('questions_to_practice', 15)} Qs\n"
                f"• Target Level: {saved_plan.get('recommended_difficulty', 'Medium')}\n"
                f"• Focus: {', '.join(saved_plan.get('weak_topics', [])[:2])}"
            )
        else:
            plan_txt = "No study plan generated yet. Generate a personalized 7-day revision schedule targeting your weak areas!"

        lbl_s4 = tk.Label(sec4, text=plan_txt, font=("Segoe UI", 9), bg=BG_SECONDARY, fg=TEXT_PRIMARY, justify="left", anchor="nw")
        lbl_s4.pack(fill="both", expand=True, pady=(0, 10))

        btn_s4 = tk.Button(sec4, text="💡 Open AI Study Plan", font=("Segoe UI", 8, "bold"), bg="#00BCD4", fg="#000000", relief="flat", cursor="hand2", command=self.controller.show_study_plan)
        btn_s4.pack(fill="x")

        # ---------------------------------------------------------------------
        # SECTION 5: Recent Performance
        # ---------------------------------------------------------------------
        sec5 = self._create_section_card(grid_sections, "📜 5. Recent Performance", "#FFB300")
        sec5.grid(row=2, column=0, sticky="nsew", pady=6)

        if recent_results:
            r_lines = []
            for res in recent_results[:3]:
                d_str = res.quiz_date[:10] if res.quiz_date else "Recent"
                r_lines.append(f"• {d_str} | {res.category} ({res.difficulty}) : {res.percentage:.1f}% ({res.correct_answers}/{res.total_questions})")
            rec_txt = "\n".join(r_lines)
        else:
            rec_txt = "No past quiz attempts found in history."

        lbl_s5 = tk.Label(sec5, text=rec_txt, font=("Segoe UI", 9), bg=BG_SECONDARY, fg=TEXT_PRIMARY, justify="left", anchor="nw")
        lbl_s5.pack(fill="both", expand=True, pady=(0, 10))

        btn_s5 = tk.Button(sec5, text="📜 View Full History", font=("Segoe UI", 8, "bold"), bg="#FFB300", fg="#000000", relief="flat", cursor="hand2", command=self.controller.show_history)
        btn_s5.pack(fill="x")

        # ---------------------------------------------------------------------
        # SECTION 6: AI Study Assistant
        # ---------------------------------------------------------------------
        sec6 = self._create_section_card(grid_sections, "🤖 6. AI Study Assistant", "#FF4081")
        sec6.grid(row=2, column=1, sticky="nsew", pady=6)

        ast_txt = (
            "• Ask concept explanations, hints, topic summaries, or question rationale.\n"
            "• Instant interactive tutor available 24/7.\n"
            "• Focused strictly on Computer Science academic learning."
        )
        lbl_s6 = tk.Label(sec6, text=ast_txt, font=("Segoe UI", 9), bg=BG_SECONDARY, fg=TEXT_PRIMARY, justify="left", anchor="nw")
        lbl_s6.pack(fill="both", expand=True, pady=(0, 10))

        btn_s6 = tk.Button(sec6, text="💬 Ask AI Study Assistant", font=("Segoe UI", 8, "bold"), bg="#FF4081", fg="#FFFFFF", relief="flat", cursor="hand2", command=self.controller.show_ai_assistant)
        btn_s6.pack(fill="x")

    def _create_section_card(self, parent: tk.Widget, title: str, color: str) -> tk.Frame:
        """Helper to construct styled section card frame."""
        card = tk.Frame(
            parent,
            bg=BG_SECONDARY,
            padx=15,
            pady=12,
            highlightbackground=color,
            highlightthickness=1
        )
        lbl_hdr = tk.Label(
            card,
            text=title,
            font=("Segoe UI", 11, "bold"),
            bg=BG_SECONDARY,
            fg=color,
            anchor="w"
        )
        lbl_hdr.pack(fill="x", pady=(0, 8))
        return card
