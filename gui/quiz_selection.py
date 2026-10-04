"""
gui/quiz_selection.py
---------------------
Interactive Quiz Selection Screen with Adaptive AI Engine for QuizMaster AI.

Allows students to customize their quiz attempt parameters:
    - Technical Category (Python, C++, Java, DBMS, Computer Networks, General Knowledge)
    - Specific Topic (Dynamically loaded based on selected Category)
    - Difficulty Level (Easy, Medium, Hard) - with manual override support
    - Question Count (5, 10, 15, 20)

Features Adaptive AI Engine:
    - Analyzes deterministic student statistics from SQLite (recent accuracy, topic accuracy, attempt history)
    - Displays: Current Level, Recommended Level, Reason, Weak Topics, Recommended Practice
    - Allows student to click [APPLY AI RECOMMENDATION] or choose any difficulty level manually
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import TYPE_CHECKING, Optional, List, Dict, Any

from services.quiz_service import QuizService
from utils.constants import (
    ACCENT_GLOW,
    ACCENT_PRIMARY,
    BG_PRIMARY,
    BG_SECONDARY,
    BG_TERTIARY,
    SUPPORTED_CATEGORIES,
    SUPPORTED_DIFFICULTIES,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)

if TYPE_CHECKING:
    from gui.app import App


class QuizSelectionScreen(tk.Frame):
    """
    Quiz Configuration interface featuring Adaptive AI Difficulty Recommendations.
    """

    def __init__(self, parent: tk.Widget, controller: "App"):
        super().__init__(parent, bg=BG_PRIMARY)
        self.controller = controller

        self.quiz_service = QuizService(db_mgr=self.controller.auth_service.db_mgr)
        self.latest_recommendation: Dict[str, Any] = {}

        self._create_widgets()
        self._update_topic_options()
        self._load_adaptive_recommendation()
        self._update_question_availability_count()

    def _create_widgets(self):
        # Header Navbar
        nav = tk.Frame(self, bg=BG_SECONDARY, padx=20, pady=12)
        nav.pack(fill="x", side="top")

        lbl_logo = tk.Label(
            nav,
            text="⚡ QuizMaster AI — Quiz Customization & Adaptive Engine",
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

        # Scrollable Canvas
        canvas = tk.Canvas(self, bg=BG_PRIMARY, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=BG_PRIMARY)

        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Main Card Box
        card = tk.Frame(
            scroll_frame,
            bg=BG_SECONDARY,
            padx=35,
            pady=25,
            highlightbackground=ACCENT_PRIMARY,
            highlightthickness=1
        )
        card.pack(pady=20, padx=40, fill="x")

        lbl_title = tk.Label(
            card,
            text="🎯 Configure Your Quiz Session",
            font=("Segoe UI", 18, "bold"),
            bg=BG_SECONDARY,
            fg=TEXT_PRIMARY
        )
        lbl_title.pack(pady=(0, 4))

        lbl_sub = tk.Label(
            card,
            text="Select your desired subject, topic, difficulty, and question count.",
            font=("Segoe UI", 9),
            bg=BG_SECONDARY,
            fg=TEXT_SECONDARY
        )
        lbl_sub.pack(pady=(0, 15))

        # Form Layout
        form = tk.Frame(card, bg=BG_SECONDARY)
        form.pack(fill="x", expand=True)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TCombobox", fieldbackground=BG_TERTIARY, background=BG_TERTIARY, foreground=TEXT_PRIMARY, font=("Segoe UI", 10))
        style.map("TCombobox", fieldbackground=[("readonly", BG_TERTIARY)], foreground=[("readonly", TEXT_PRIMARY)])

        # 1. Category Selection
        f_cat = tk.Frame(form, bg=BG_SECONDARY)
        f_cat.pack(fill="x", pady=6)
        tk.Label(f_cat, text="Subject Category:", font=("Segoe UI", 10, "bold"), bg=BG_SECONDARY, fg=ACCENT_PRIMARY, width=18, anchor="w").pack(side="left")
        self.cmb_category = ttk.Combobox(f_cat, values=SUPPORTED_CATEGORIES, state="readonly", width=28)
        self.cmb_category.set(SUPPORTED_CATEGORIES[0])
        self.cmb_category.pack(side="left", padx=10, ipady=3)
        self.cmb_category.bind("<<ComboboxSelected>>", self._on_category_changed)

        # 2. Topic Selection
        f_topic = tk.Frame(form, bg=BG_SECONDARY)
        f_topic.pack(fill="x", pady=6)
        tk.Label(f_topic, text="Topic:", font=("Segoe UI", 10, "bold"), bg=BG_SECONDARY, fg=ACCENT_PRIMARY, width=18, anchor="w").pack(side="left")
        self.cmb_topic = ttk.Combobox(f_topic, state="readonly", width=28)
        self.cmb_topic.pack(side="left", padx=10, ipady=3)
        self.cmb_topic.bind("<<ComboboxSelected>>", self._on_topic_changed)

        # 3. Difficulty Selection
        f_diff = tk.Frame(form, bg=BG_SECONDARY)
        f_diff.pack(fill="x", pady=6)
        tk.Label(f_diff, text="Difficulty Level:", font=("Segoe UI", 10, "bold"), bg=BG_SECONDARY, fg=ACCENT_PRIMARY, width=18, anchor="w").pack(side="left")
        difficulties_display = ["Easy", "Medium", "Hard"]
        self.cmb_difficulty = ttk.Combobox(f_diff, values=difficulties_display, state="readonly", width=28)
        self.cmb_difficulty.set("Easy")
        self.cmb_difficulty.pack(side="left", padx=10, ipady=3)
        self.cmb_difficulty.bind("<<ComboboxSelected>>", lambda e: self._update_question_availability_count())

        # 4. Question Count Selection
        f_count = tk.Frame(form, bg=BG_SECONDARY)
        f_count.pack(fill="x", pady=6)
        tk.Label(f_count, text="Number of Questions:", font=("Segoe UI", 10, "bold"), bg=BG_SECONDARY, fg=ACCENT_PRIMARY, width=18, anchor="w").pack(side="left")
        self.cmb_count = ttk.Combobox(f_count, values=["5", "10", "15", "20"], state="readonly", width=28)
        self.cmb_count.set("10")
        self.cmb_count.pack(side="left", padx=10, ipady=3)
        self.cmb_count.bind("<<ComboboxSelected>>", lambda e: self._update_question_availability_count())

        # --- Adaptive AI Recommendation Container ---
        self.ai_card = tk.Frame(
            card,
            bg=BG_TERTIARY,
            padx=18,
            pady=12,
            highlightbackground=ACCENT_PRIMARY,
            highlightthickness=1
        )
        self.ai_card.pack(fill="x", pady=(15, 10))

        hdr = tk.Frame(self.ai_card, bg=BG_TERTIARY)
        hdr.pack(fill="x", pady=(0, 6))

        tk.Label(hdr, text="🤖 Adaptive AI Difficulty Recommendation", font=("Segoe UI", 11, "bold"), bg=BG_TERTIARY, fg=ACCENT_PRIMARY).pack(side="left")

        self.btn_apply_ai = tk.Button(
            hdr,
            text="⚡ APPLY RECOMMENDATION",
            font=("Segoe UI", 9, "bold"),
            bg=ACCENT_PRIMARY,
            fg="#000000",
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=2,
            command=self._apply_ai_recommendation
        )
        self.btn_apply_ai.pack(side="right")

        self.ai_body = tk.Frame(self.ai_card, bg=BG_TERTIARY)
        self.ai_body.pack(fill="x")

        # Availability Live Status Badge
        self.lbl_status = tk.Label(
            card,
            text="",
            font=("Segoe UI", 9, "italic"),
            bg=BG_TERTIARY,
            fg=ACCENT_PRIMARY,
            padx=15,
            pady=8,
            relief="flat"
        )
        self.lbl_status.pack(fill="x", pady=(10, 15))

        # Start Quiz Action Button
        btn_start = tk.Button(
            card,
            text="🚀 START QUIZ NOW",
            font=("Segoe UI", 11, "bold"),
            bg=ACCENT_PRIMARY,
            fg="#000000",
            activebackground=ACCENT_GLOW,
            activeforeground="#000000",
            relief="flat",
            cursor="hand2",
            command=self._on_start_quiz_click
        )
        btn_start.pack(fill="x", ipady=8)

    def _on_category_changed(self, event=None):
        self._update_topic_options()
        self._load_adaptive_recommendation()
        self._update_question_availability_count()

    def _on_topic_changed(self, event=None):
        self._load_adaptive_recommendation()
        self._update_question_availability_count()

    def _update_topic_options(self):
        category = self.cmb_category.get()
        distinct_topics = self.quiz_service.get_available_topics(category)
        topics = ["All Topics"] + distinct_topics
        self.cmb_topic["values"] = topics
        self.cmb_topic.set("All Topics")

    def _load_adaptive_recommendation(self):
        """Computes deterministic stats from SQLite and renders AI recommendation."""
        user = self.controller.auth_service.current_user
        user_id = user.id if user else 1
        category = self.cmb_category.get()
        topic = self.cmb_topic.get()
        topic_arg = topic if topic != "All Topics" else None
        curr_diff = self.cmb_difficulty.get().lower()

        rec = self.quiz_service.get_adaptive_difficulty_recommendation(
            user_id=user_id,
            category=category,
            topic=topic_arg,
            current_difficulty=curr_diff
        )
        self.latest_recommendation = rec

        # Clear AI body
        for child in self.ai_body.winfo_children():
            child.destroy()

        # Render Recommendation Details
        curr_lvl = rec.get("current_level", "Medium")
        rec_lvl = rec.get("recommended_level", "Medium")
        reason = rec.get("reason", "Based on quiz history analytics.")
        weaks = rec.get("weak_topics", [])
        practice = rec.get("recommended_practice", "")

        # Row 1: Current vs Recommended Level Badges
        r1 = tk.Frame(self.ai_body, bg=BG_TERTIARY)
        r1.pack(fill="x", pady=(0, 4))

        tk.Label(r1, text="Current Level: ", font=("Segoe UI", 9, "bold"), bg=BG_TERTIARY, fg=TEXT_SECONDARY).pack(side="left")
        tk.Label(r1, text=curr_lvl, font=("Segoe UI", 9, "bold"), bg=BG_PRIMARY, fg=TEXT_PRIMARY, padx=6, pady=1).pack(side="left", padx=(0, 15))

        tk.Label(r1, text="Recommended Level: ", font=("Segoe UI", 9, "bold"), bg=BG_TERTIARY, fg=TEXT_SECONDARY).pack(side="left")
        tk.Label(r1, text=rec_lvl, font=("Segoe UI", 9, "bold"), bg=ACCENT_PRIMARY, fg="#000000", padx=8, pady=1).pack(side="left")

        # Row 2: Reason
        tk.Label(self.ai_body, text=f"Reason: {reason}", font=("Segoe UI", 9), bg=BG_TERTIARY, fg=TEXT_PRIMARY, anchor="w", wraplength=700, justify="left").pack(fill="x", pady=(2, 2))

        # Row 3: Weak Topics & Practice (if available)
        if weaks:
            weak_str = ", ".join(weaks) if isinstance(weaks, list) else str(weaks)
            tk.Label(self.ai_body, text=f"Weak Topics: {weak_str}", font=("Segoe UI", 9, "bold"), bg=BG_TERTIARY, fg="#FF4C6A", anchor="w").pack(fill="x", pady=(1, 1))

        if practice:
            tk.Label(self.ai_body, text=f"Recommended Practice: {practice}", font=("Segoe UI", 9, "italic"), bg=BG_TERTIARY, fg=TEXT_SECONDARY, anchor="w", wraplength=700, justify="left").pack(fill="x", pady=(1, 2))

        # Manual Override Notice
        tk.Label(
            self.ai_body,
            text="💡 Tip: Click 'Apply Recommendation' or manually select any difficulty level from the dropdown above.",
            font=("Segoe UI", 8, "italic"),
            bg=BG_TERTIARY,
            fg=TEXT_SECONDARY,
            anchor="w"
        ).pack(fill="x", pady=(4, 0))

    def _apply_ai_recommendation(self):
        """Applies the recommended difficulty level to the combobox, allowing manual override."""
        rec_lvl = self.latest_recommendation.get("recommended_level", "Medium")
        self.cmb_difficulty.set(rec_lvl.capitalize())
        self._update_question_availability_count()

    def _update_question_availability_count(self):
        """Queries database to show live question count for selected options."""
        category = self.cmb_category.get()
        topic = self.cmb_topic.get()
        difficulty = self.cmb_difficulty.get().lower()

        avail_count = self.quiz_service.count_questions(
            category=category,
            topic=topic if topic != "All Topics" else None,
            difficulty=difficulty
        )

        requested_count = int(self.cmb_count.get() or "10")
        if avail_count >= requested_count:
            self.lbl_status.config(
                text=f"✅ {avail_count} questions available for {category} ({difficulty.capitalize()}). Ready to start!",
                fg="#00E676"
            )
        elif avail_count > 0:
            self.lbl_status.config(
                text=f"⚠️ Only {avail_count} question(s) available matching your filter (Requested {requested_count}).",
                fg="#FFC107"
            )
        else:
            self.lbl_status.config(
                text=f"❌ No questions currently exist for {category} ({difficulty.capitalize()}). Please change filters.",
                fg="#FF4C6A"
            )

    def _on_start_quiz_click(self):
        """Validates configuration and launches QuizScreen."""
        category = self.cmb_category.get()
        topic = self.cmb_topic.get()
        difficulty = self.cmb_difficulty.get().lower()
        requested_count = int(self.cmb_count.get() or "10")

        avail_count = self.quiz_service.count_questions(
            category=category,
            topic=topic if topic != "All Topics" else None,
            difficulty=difficulty
        )

        if avail_count == 0:
            messagebox.showwarning(
                "No Questions Available",
                f"No questions exist in the Question Bank matching:\n"
                f"• Category: {category}\n"
                f"• Topic: {topic}\n"
                f"• Difficulty: {difficulty.capitalize()}\n\n"
                f"Please select another category or difficulty level.",
                parent=self
            )
            return

        if avail_count < requested_count:
            confirm = messagebox.askyesno(
                "Insufficient Questions",
                f"Only {avail_count} question(s) exist matching your criteria, "
                f"which is less than your requested {requested_count} questions.\n\n"
                f"Would you like to start the quiz with all {avail_count} available question(s)?",
                parent=self,
                icon="warning"
            )
            if not confirm:
                return
            quiz_count = avail_count
        else:
            quiz_count = requested_count

        questions = self.quiz_service.get_random_questions(
            category=category,
            topic=topic if topic != "All Topics" else None,
            difficulty=difficulty,
            count=quiz_count
        )

        quiz_config = {
            "category": category,
            "topic": topic,
            "difficulty": difficulty,
            "count": len(questions)
        }

        self.controller.show_quiz_screen(quiz_config=quiz_config, questions=questions)
