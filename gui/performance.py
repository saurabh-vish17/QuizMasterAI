"""
gui/performance.py
-------------------
Performance Analytics screen for QuizMaster AI.

Features:
    - Displays overall average score, total quizzes, best score, strongest category, weakest category
    - Embeds live Matplotlib charts:
        1. Category-wise performance (Bar Chart)
        2. Score progression over time (Line Chart)
    - Incorporates AI-Powered Student Performance Analysis:
        - Strong Areas & Weak Topics
        - Recommended Difficulty Badge
        - Actionable Learning Recommendations
        - SQLite Persistence in 'ai_analysis' table
    - Handles empty state gracefully when student has no quiz history
"""

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING, Dict, Any, Optional

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from services.result_service import ResultService
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


class PerformanceScreen(tk.Frame):
    """
    Student Performance Analytics view incorporating Matplotlib charts and AI Learning Analysis.
    """

    def __init__(self, parent: tk.Widget, controller: "App"):
        super().__init__(parent, bg=BG_PRIMARY)
        self.controller = controller

        self.result_service = ResultService(db_mgr=self.controller.auth_service.db_mgr)
        self.analytics_data: Dict[str, Any] = {}

        self._create_widgets()
        self._load_analytics()

    def _create_widgets(self):
        # 1. Header Navbar
        nav = tk.Frame(self, bg=BG_SECONDARY, padx=20, pady=12)
        nav.pack(fill="x", side="top")

        lbl_logo = tk.Label(
            nav,
            text="📈 Student Performance Analytics",
            font=("Segoe UI", 16, "bold"),
            bg=BG_SECONDARY,
            fg=ACCENT_PRIMARY
        )
        lbl_logo.pack(side="left")

        btn_back = tk.Button(
            nav,
            text="← BACK TO DASHBOARD",
            font=("Segoe UI", 9, "bold"),
            bg=BG_PRIMARY,
            fg=ACCENT_PRIMARY,
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=4,
            command=self.controller.show_dashboard
        )
        btn_back.pack(side="right")

        # Main Scrollable Content Canvas
        self.canvas = tk.Canvas(self, bg=BG_PRIMARY, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.content_frame = tk.Frame(self.canvas, bg=BG_PRIMARY, padx=20, pady=15)

        self.content_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.create_window((0, 0), window=self.content_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

    def _load_analytics(self):
        """Fetches student result data and builds KPI cards, AI Analysis card, and Matplotlib charts."""
        user = self.controller.auth_service.current_user
        if not user:
            return

        for child in self.content_frame.winfo_children():
            child.destroy()

        self.analytics_data = self.result_service.get_student_performance_analytics(user.id)

        # Empty State Handler
        if not self.analytics_data.get("has_data", False):
            self._render_empty_state()
            return

        self._render_kpi_cards()
        self._render_ai_analysis_card()
        self._render_charts()

    def _render_empty_state(self):
        """Renders friendly message when student has no quiz history."""
        card = tk.Frame(
            self.content_frame,
            bg=BG_SECONDARY,
            padx=40,
            pady=40,
            highlightbackground=ACCENT_PRIMARY,
            highlightthickness=1
        )
        card.pack(pady=40, anchor="center")

        lbl_icon = tk.Label(card, text="📊", font=("Segoe UI", 48), bg=BG_SECONDARY)
        lbl_icon.pack(pady=(0, 10))

        lbl_title = tk.Label(
            card,
            text="No Performance Analytics Available",
            font=("Segoe UI", 16, "bold"),
            bg=BG_SECONDARY,
            fg=TEXT_PRIMARY
        )
        lbl_title.pack(pady=(0, 10))

        lbl_sub = tk.Label(
            card,
            text="Take your first quiz to generate detailed performance charts and topic breakdowns!",
            font=("Segoe UI", 10),
            bg=BG_SECONDARY,
            fg=TEXT_SECONDARY,
            wraplength=400,
            justify="center"
        )
        lbl_sub.pack(pady=(0, 20))

        btn_quiz = tk.Button(
            card,
            text="🚀 START A QUIZ NOW",
            font=("Segoe UI", 10, "bold"),
            bg=ACCENT_PRIMARY,
            fg="#000000",
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=8,
            command=self.controller.show_quiz_selection
        )
        btn_quiz.pack()

    def _render_kpi_cards(self):
        """Renders key metrics summary cards (Overall Avg, Quizzes, Best, Strongest, Weakest)."""
        data = self.analytics_data
        kpi_frame = tk.Frame(self.content_frame, bg=BG_PRIMARY)
        kpi_frame.pack(fill="x", pady=(0, 15))

        cards_data = [
            ("Overall Avg Score", f"{data['average_score']:.1f}%", ACCENT_PRIMARY),
            ("Quizzes Attempted", str(data["total_quizzes"]), TEXT_PRIMARY),
            ("Best Score", f"{data['best_score']:.1f}%", "#00E676"),
            ("Strongest Category", data["strongest_category"].capitalize(), "#00E5FF"),
            ("Weakest Category", data["weakest_category"].capitalize(), "#FF4C6A"),
        ]

        for idx, (title, val, color) in enumerate(cards_data):
            card = tk.Frame(kpi_frame, bg=BG_SECONDARY, padx=15, pady=12, highlightbackground=BG_TERTIARY, highlightthickness=1)
            card.pack(side="left", fill="both", expand=True, padx=4 if idx > 0 else 0)

            tk.Label(card, text=title, font=("Segoe UI", 9), bg=BG_SECONDARY, fg=TEXT_SECONDARY).pack(anchor="w")
            tk.Label(card, text=val, font=("Segoe UI", 13, "bold"), bg=BG_SECONDARY, fg=color).pack(anchor="w", pady=(4, 0))

    def _render_ai_analysis_card(self):
        """Renders AI-Powered Performance Analysis section."""
        ai_card = tk.Frame(
            self.content_frame,
            bg=BG_SECONDARY,
            padx=20,
            pady=15,
            highlightbackground=ACCENT_PRIMARY,
            highlightthickness=1
        )
        ai_card.pack(fill="x", pady=(0, 15))

        hdr = tk.Frame(ai_card, bg=BG_SECONDARY)
        hdr.pack(fill="x", pady=(0, 10))

        tk.Label(
            hdr,
            text="🤖 AI-Powered Learning Analysis",
            font=("Segoe UI", 12, "bold"),
            bg=BG_SECONDARY,
            fg=ACCENT_PRIMARY
        ).pack(side="left")

        user = self.controller.auth_service.current_user
        latest_analysis = self.result_service.get_latest_ai_analysis(user.id) if user else None

        self.btn_gen_ai = tk.Button(
            hdr,
            text="⚡ REFRESH AI ANALYSIS" if latest_analysis else "⚡ GENERATE AI ANALYSIS",
            font=("Segoe UI", 9, "bold"),
            bg=ACCENT_PRIMARY,
            fg="#000000",
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=4,
            command=self._on_generate_ai_analysis
        )
        self.btn_gen_ai.pack(side="right")

        self.ai_body_frame = tk.Frame(ai_card, bg=BG_SECONDARY)
        self.ai_body_frame.pack(fill="x")

        if latest_analysis:
            self._display_analysis_data(self.ai_body_frame, latest_analysis)
        else:
            tk.Label(
                self.ai_body_frame,
                text="Click 'Generate AI Analysis' to receive objective performance feedback based on your quiz statistics.",
                font=("Segoe UI", 9, "italic"),
                bg=BG_SECONDARY,
                fg=TEXT_SECONDARY
            ).pack(anchor="w", pady=5)

    def _on_generate_ai_analysis(self):
        """Generates AI analysis based on objective quiz stats, saves to DB, and displays result."""
        user = self.controller.auth_service.current_user
        if not user:
            return

        self.btn_gen_ai.configure(state="disabled", text="⚡ ANALYZING PERFORMANCE...")
        self.update_idletasks()

        analysis = self.result_service.generate_and_save_ai_analysis(user.id)

        self.btn_gen_ai.configure(state="normal", text="⚡ REFRESH AI ANALYSIS")

        for child in self.ai_body_frame.winfo_children():
            child.destroy()

        self._display_analysis_data(self.ai_body_frame, analysis)

    def _display_analysis_data(self, container: tk.Frame, analysis: Dict[str, Any]):
        """Renders 3-column analysis view: Strong Areas, Needs Improvement, and Recommendations."""
        # Summary Header
        if analysis.get("summary"):
            tk.Label(
                container,
                text=analysis["summary"],
                font=("Segoe UI", 9, "italic"),
                bg=BG_SECONDARY,
                fg=TEXT_PRIMARY,
                wraplength=800,
                justify="left"
            ).pack(anchor="w", pady=(0, 10))

        grid = tk.Frame(container, bg=BG_SECONDARY)
        grid.pack(fill="x")
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)
        grid.columnconfigure(2, weight=1)

        # Column 1: Strong Areas
        col1 = tk.Frame(grid, bg=BG_TERTIARY, padx=12, pady=10)
        col1.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        tk.Label(col1, text="💪 Strong Areas", font=("Segoe UI", 10, "bold"), bg=BG_TERTIARY, fg="#00E676").pack(anchor="w", pady=(0, 4))
        strengths = analysis.get("strengths", [])
        if not isinstance(strengths, list):
            strengths = [str(strengths)]
        for s in strengths:
            tk.Label(col1, text=f"• {s}", font=("Segoe UI", 9), bg=BG_TERTIARY, fg=TEXT_PRIMARY, anchor="w").pack(fill="x", pady=1)

        # Column 2: Needs Improvement
        col2 = tk.Frame(grid, bg=BG_TERTIARY, padx=12, pady=10)
        col2.grid(row=0, column=1, sticky="nsew", padx=3)

        tk.Label(col2, text="🎯 Needs Improvement", font=("Segoe UI", 10, "bold"), bg=BG_TERTIARY, fg="#FF4C6A").pack(anchor="w", pady=(0, 4))
        weaks = analysis.get("weak_topics", [])
        if not isinstance(weaks, list):
            weaks = [str(weaks)]
        for w in weaks:
            tk.Label(col2, text=f"• {w}", font=("Segoe UI", 9), bg=BG_TERTIARY, fg=TEXT_PRIMARY, anchor="w").pack(fill="x", pady=1)

        # Column 3: Recommendations & Recommended Difficulty
        col3 = tk.Frame(grid, bg=BG_TERTIARY, padx=12, pady=10)
        col3.grid(row=0, column=2, sticky="nsew", padx=(6, 0))

        diff_rec = str(analysis.get("difficulty_recommendation", "medium")).upper()
        tk.Label(col3, text=f"📌 Recommended Level: {diff_rec}", font=("Segoe UI", 10, "bold"), bg=BG_TERTIARY, fg=ACCENT_PRIMARY).pack(anchor="w", pady=(0, 4))

        recs = analysis.get("recommendations", [])
        if not isinstance(recs, list):
            recs = [str(recs)]
        for r in recs:
            tk.Label(col3, text=f"💡 {r}", font=("Segoe UI", 9), bg=BG_TERTIARY, fg=TEXT_SECONDARY, wraplength=240, justify="left").pack(anchor="w", pady=2)

    def _render_charts(self):
        """Embeds Matplotlib Bar Chart (Category-wise) and Line Chart (Score Progression)."""
        charts_frame = tk.Frame(self.content_frame, bg=BG_PRIMARY)
        charts_frame.pack(fill="both", expand=True, pady=(10, 0))

        fig = Figure(figsize=(10, 4.2), dpi=100, facecolor=BG_PRIMARY)
        fig.subplots_adjust(wspace=0.35, bottom=0.22, top=0.88, left=0.08, right=0.96)

        # Chart 1: Category-Wise Performance (Bar Chart)
        ax1 = fig.add_subplot(121, facecolor=BG_SECONDARY)
        cat_perf = self.analytics_data.get("category_performance", {})

        if cat_perf:
            categories = list(cat_perf.keys())
            scores = [cat_perf[c]["avg_percentage"] for c in categories]

            bars = ax1.bar(categories, scores, color="#6366F1", width=0.55, edgecolor="#818CF8", linewidth=1.2)
            ax1.set_title("Category-Wise Avg Score (%)", color=TEXT_PRIMARY, fontsize=11, fontweight="bold", pad=12)
            ax1.set_ylim(0, 105)
            ax1.set_ylabel("Avg Score (%)", color=TEXT_SECONDARY, fontsize=9)
            ax1.tick_params(colors=TEXT_SECONDARY, labelsize=8)
            ax1.grid(axis="y", color="#334155", linestyle="--", alpha=0.6)

            for bar in bars:
                height = bar.get_height()
                ax1.annotate(
                    f"{height:.1f}%",
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha="center",
                    va="bottom",
                    color=TEXT_PRIMARY,
                    fontsize=8,
                    fontweight="bold"
                )
            ax1.set_xticklabels(categories, rotation=15, ha="right")
        else:
            ax1.text(0.5, 0.5, "No Category Data", ha="center", va="center", color=TEXT_SECONDARY)

        # Chart 2: Score Progression Over Time (Line Chart)
        ax2 = fig.add_subplot(122, facecolor=BG_SECONDARY)
        progression = self.analytics_data.get("score_progression", [])

        if progression:
            attempts = [item["attempt_num"] for item in progression]
            percentages = [item["percentage"] for item in progression]

            ax2.plot(attempts, percentages, color="#00E676", marker="o", linewidth=2.5, markersize=6, markerfacecolor="#00E5FF", markeredgecolor="#00E676")
            ax2.set_title("Score Progression Over Time", color=TEXT_PRIMARY, fontsize=11, fontweight="bold", pad=12)
            ax2.set_xlabel("Attempt Number", color=TEXT_SECONDARY, fontsize=9)
            ax2.set_ylabel("Score (%)", color=TEXT_SECONDARY, fontsize=9)
            ax2.set_ylim(0, 105)
            ax2.tick_params(colors=TEXT_SECONDARY, labelsize=8)
            ax2.grid(True, color="#334155", linestyle="--", alpha=0.6)

            for x, y in zip(attempts, percentages):
                ax2.annotate(
                    f"{y:.0f}%",
                    xy=(x, y),
                    xytext=(0, 6),
                    textcoords="offset points",
                    ha="center",
                    color=TEXT_PRIMARY,
                    fontsize=8,
                    fontweight="bold"
                )
        else:
            ax2.text(0.5, 0.5, "No Progression Data", ha="center", va="center", color=TEXT_SECONDARY)

        canvas = FigureCanvasTkAgg(fig, master=charts_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
