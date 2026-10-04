"""
gui/result_screen.py
--------------------
Post-quiz summary and detailed Answer Review screen for QuizMaster AI.

Displays:
    - Overall score, percentage badge, grade, and pass/fail status
    - Breakdown metrics: Total questions, Correct, Wrong, Unanswered, Time Taken, Category, Difficulty
    - "Review Answers" scrollable view showing student answer vs correct answer and explanation
    - "Explain with AI" feature: 3-part breakdown (Why correct, Why incorrect, Learning tip) with caching
"""

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING, Optional, List, Dict, Any

from models.result import Result
from services.ai_service import AIService
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


class ResultScreen(tk.Frame):
    """
    Detailed Quiz Results & Answer Review screen with AI-powered explanation support.
    """

    def __init__(self, parent: tk.Widget, controller: "App", result_id: int):
        super().__init__(parent, bg=BG_PRIMARY)
        self.controller = controller
        self.result_id = result_id

        self.result_service = ResultService(db_mgr=self.controller.auth_service.db_mgr)
        self.ai_service = AIService()
        self.result: Optional[Result] = self.result_service.get_result_by_id(result_id)
        self.review_details: List[Dict[str, Any]] = self.result_service.get_result_details(result_id)

        self._create_widgets()

    def _create_widgets(self):
        # 1. Navbar Header
        nav = tk.Frame(self, bg=BG_SECONDARY, padx=20, pady=12)
        nav.pack(fill="x", side="top")

        lbl_logo = tk.Label(
            nav,
            text="📊 Quiz Performance Report",
            font=("Segoe UI", 16, "bold"),
            bg=BG_SECONDARY,
            fg=ACCENT_PRIMARY
        )
        lbl_logo.pack(side="left")

        btn_dash = tk.Button(
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
        btn_dash.pack(side="right")

        if not self.result:
            lbl_err = tk.Label(self, text="Result record not found.", fg="#FF4C6A", bg=BG_PRIMARY, font=("Segoe UI", 14))
            lbl_err.pack(expand=True)
            return

        # 2. Main Scrollable Container or Tab Control
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=20, pady=15)

        # Tab 1: Score Summary Card
        tab_summary = tk.Frame(notebook, bg=BG_PRIMARY, padx=20, pady=20)
        notebook.add(tab_summary, text=" 🏆 Score Summary ")

        # Tab 2: Answer Review
        tab_review = tk.Frame(notebook, bg=BG_PRIMARY, padx=20, pady=20)
        notebook.add(tab_review, text=" 🔍 Answer Review ")

        self._build_summary_tab(tab_summary, notebook)
        self._build_review_tab(tab_review)

    def _build_summary_tab(self, parent: tk.Frame, notebook: ttk.Notebook):
        """Builds score metrics summary dashboard card."""
        res = self.result

        # Card Box
        card = tk.Frame(
            parent,
            bg=BG_SECONDARY,
            padx=40,
            pady=30,
            highlightbackground=ACCENT_PRIMARY,
            highlightthickness=1
        )
        card.place(relx=0.5, rely=0.48, anchor="center")

        # Grade / Status Banner
        passed = res.is_passed()
        grade = res.get_grade()
        banner_bg = "#00E676" if passed else "#FF4C6A"
        banner_text = f"🎉 QUIZ PASSED — GRADE {grade}" if passed else f"⚠️ QUIZ FAILED — GRADE {grade}"

        lbl_banner = tk.Label(
            card,
            text=banner_text,
            font=("Segoe UI", 14, "bold"),
            bg=banner_bg,
            fg="#000000",
            padx=20,
            pady=6
        )
        lbl_banner.pack(fill="x", pady=(0, 20))

        # Main Score Display
        f_score = tk.Frame(card, bg=BG_TERTIARY, padx=30, pady=15)
        f_score.pack(pady=(0, 20))

        lbl_score_num = tk.Label(
            f_score,
            text=f"{res.percentage:.1f}%",
            font=("Segoe UI", 32, "bold"),
            bg=BG_TERTIARY,
            fg=ACCENT_PRIMARY
        )
        lbl_score_num.pack()

        lbl_score_sub = tk.Label(
            f_score,
            text=f"Score: {res.score:.0f} / {res.total_questions} Points",
            font=("Segoe UI", 11),
            bg=BG_TERTIARY,
            fg=TEXT_SECONDARY
        )
        lbl_score_sub.pack()

        # Grid of Metrics
        grid = tk.Frame(card, bg=BG_SECONDARY)
        grid.pack(fill="x", pady=10)

        metrics = [
            ("Category", res.category.capitalize(), ACCENT_PRIMARY),
            ("Difficulty", res.difficulty.capitalize(), ACCENT_PRIMARY),
            ("Total Questions", str(res.total_questions), TEXT_PRIMARY),
            ("Correct Answers", f"✅ {res.correct_answers}", "#00E676"),
            ("Wrong Answers", f"❌ {res.wrong_answers}", "#FF4C6A"),
            ("Unanswered", f"⚠️ {res.unanswered}", "#FFC107"),
            ("Time Taken", f"⏱️ {res.formatted_time()}", TEXT_PRIMARY),
            ("Quiz Date", res.quiz_date[:10] if res.quiz_date else "Today", TEXT_SECONDARY),
        ]

        for idx, (label, val, color) in enumerate(metrics):
            r = idx // 2
            c = idx % 2

            cell = tk.Frame(grid, bg=BG_TERTIARY, padx=15, pady=8)
            cell.grid(row=r, column=c, padx=8, pady=6, sticky="ew")
            grid.columnconfigure(c, weight=1)

            tk.Label(cell, text=label, font=("Segoe UI", 9), bg=BG_TERTIARY, fg=TEXT_SECONDARY).pack(anchor="w")
            tk.Label(cell, text=val, font=("Segoe UI", 11, "bold"), bg=BG_TERTIARY, fg=color).pack(anchor="w")

        # Action Buttons Toolbar
        btn_box = tk.Frame(card, bg=BG_SECONDARY)
        btn_box.pack(fill="x", pady=(20, 0))

        btn_review = tk.Button(
            btn_box,
            text="🔍 REVIEW ANSWERS",
            font=("Segoe UI", 10, "bold"),
            bg=ACCENT_PRIMARY,
            fg="#000000",
            relief="flat",
            cursor="hand2",
            padx=15,
            pady=6,
            command=lambda: notebook.select(1)
        )
        btn_review.pack(side="left", expand=True, fill="x", padx=(0, 5))

        btn_retake = tk.Button(
            btn_box,
            text="🔄 NEW QUIZ",
            font=("Segoe UI", 10, "bold"),
            bg=BG_TERTIARY,
            fg=TEXT_PRIMARY,
            relief="flat",
            cursor="hand2",
            padx=15,
            pady=6,
            command=self.controller.show_quiz_selection
        )
        btn_retake.pack(side="right", expand=True, fill="x", padx=(5, 0))

    def _build_review_tab(self, parent: tk.Frame):
        """Builds scrollable Answer Review interface with AI explanation button."""
        canvas = tk.Canvas(parent, bg=BG_PRIMARY, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=BG_PRIMARY)

        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        if not self.review_details:
            lbl_empty = tk.Label(scroll_frame, text="No question details recorded.", bg=BG_PRIMARY, fg=TEXT_SECONDARY)
            lbl_empty.pack(pady=20)
            return

        for idx, item in enumerate(self.review_details):
            card = tk.Frame(
                scroll_frame,
                bg=BG_SECONDARY,
                padx=20,
                pady=15,
                highlightbackground=BG_TERTIARY,
                highlightthickness=1
            )
            card.pack(fill="x", pady=10, padx=10)

            # Header (Question number & Status Badge)
            h_frame = tk.Frame(card, bg=BG_SECONDARY)
            h_frame.pack(fill="x", pady=(0, 8))

            q_num = f"Question {idx + 1}"
            tk.Label(h_frame, text=f"{q_num} • Topic: {item['topic']}", font=("Segoe UI", 10, "bold"), bg=BG_SECONDARY, fg=ACCENT_PRIMARY).pack(side="left")

            if not item["selected_answer"]:
                status_text = "⚠️ UNANSWERED"
                status_bg = "#FFC107"
            elif item["is_correct"]:
                status_text = "✅ CORRECT"
                status_bg = "#00E676"
            else:
                status_text = "❌ INCORRECT"
                status_bg = "#FF4C6A"

            tk.Label(h_frame, text=status_text, font=("Segoe UI", 9, "bold"), bg=status_bg, fg="#000000", padx=8, pady=2).pack(side="right")

            # Question Text
            tk.Label(
                card,
                text=item["question_text"],
                font=("Segoe UI", 11, "bold"),
                bg=BG_SECONDARY,
                fg=TEXT_PRIMARY,
                wraplength=800,
                justify="left"
            ).pack(anchor="w", pady=(0, 10))

            # Options and Answer Comparison
            opts = {
                "A": item["option_a"],
                "B": item["option_b"],
                "C": item["option_c"],
                "D": item["option_d"],
            }

            ans_frame = tk.Frame(card, bg=BG_TERTIARY, padx=12, pady=10)
            ans_frame.pack(fill="x", pady=(0, 10))

            stud_ans_str = f"{item['selected_answer']}. {opts.get(item['selected_answer'], 'None')}" if item['selected_answer'] else "None (Skipped)"
            corr_ans_str = f"{item['correct_answer']}. {opts.get(item['correct_answer'], '')}"

            tk.Label(ans_frame, text=f"Your Answer:  {stud_ans_str}", font=("Segoe UI", 10), bg=BG_TERTIARY, fg="#FF4C6A" if not item["is_correct"] else "#00E676").pack(anchor="w")
            tk.Label(ans_frame, text=f"Correct Key:   {corr_ans_str}", font=("Segoe UI", 10, "bold"), bg=BG_TERTIARY, fg="#00E676").pack(anchor="w", pady=(4, 0))

            # Explanation Box (Standard)
            exp_box = tk.Frame(card, bg=BG_PRIMARY, padx=12, pady=8)
            exp_box.pack(fill="x", pady=(0, 10))
            tk.Label(exp_box, text="💡 Rationale / Explanation:", font=("Segoe UI", 9, "bold"), bg=BG_PRIMARY, fg=ACCENT_PRIMARY).pack(anchor="w")
            tk.Label(exp_box, text=item["explanation"], font=("Segoe UI", 9), bg=BG_PRIMARY, fg=TEXT_SECONDARY, wraplength=780, justify="left").pack(anchor="w", pady=(2, 0))

            # AI Explanation Action Bar & Container
            ai_bar = tk.Frame(card, bg=BG_SECONDARY)
            ai_bar.pack(fill="x")

            exp_ai_container = tk.Frame(card, bg=BG_SECONDARY)
            exp_ai_container.pack(fill="x")

            btn_ai = tk.Button(
                ai_bar,
                text="🤖 EXPLAIN WITH AI",
                font=("Segoe UI", 9, "bold"),
                bg=ACCENT_PRIMARY,
                fg="#000000",
                relief="flat",
                cursor="hand2",
                padx=10,
                pady=4
            )
            btn_ai.configure(command=lambda itm=item, b=btn_ai, c=exp_ai_container: self._on_explain_with_ai(itm, b, c))
            btn_ai.pack(side="left")

    def _on_explain_with_ai(self, item: Dict[str, Any], btn_ai: tk.Button, exp_container: tk.Frame):
        """Triggers AI answer explanation and displays detailed 3-part breakdown."""
        btn_ai.configure(state="disabled", text="🤖 GENERATING AI EXPLANATION...")
        self.update_idletasks()

        options = {
            "A": item["option_a"],
            "B": item["option_b"],
            "C": item["option_c"],
            "D": item["option_d"],
        }

        res = self.ai_service.explain_answer_detailed(
            question_text=item["question_text"],
            selected_answer=item["selected_answer"] or "",
            correct_answer=item["correct_answer"],
            options=options,
            existing_explanation=item.get("explanation", "")
        )

        btn_ai.configure(state="normal", text="🤖 REFRESH AI EXPLANATION")

        for w in exp_container.winfo_children():
            w.destroy()

        ai_box = tk.Frame(
            exp_container,
            bg=BG_TERTIARY,
            padx=15,
            pady=12,
            highlightbackground=ACCENT_PRIMARY,
            highlightthickness=1
        )
        ai_box.pack(fill="x", pady=(10, 0))

        hdr = tk.Frame(ai_box, bg=BG_TERTIARY)
        hdr.pack(fill="x", pady=(0, 6))

        tk.Label(hdr, text="🤖 AI Detailed Rationale", font=("Segoe UI", 10, "bold"), bg=BG_TERTIARY, fg=ACCENT_PRIMARY).pack(side="left")
        if res.get("cached"):
            tk.Label(hdr, text="⚡ CACHED", font=("Segoe UI", 8, "bold"), bg=BG_PRIMARY, fg=TEXT_SECONDARY, padx=6, pady=1).pack(side="right")

        # 1. Why Correct
        tk.Label(ai_box, text="1. Why Correct:", font=("Segoe UI", 9, "bold"), bg=BG_TERTIARY, fg="#00E676", anchor="w").pack(fill="x", pady=(2, 0))
        tk.Label(ai_box, text=res.get("why_correct", ""), font=("Segoe UI", 9), bg=BG_TERTIARY, fg=TEXT_PRIMARY, wraplength=760, justify="left").pack(fill="x", pady=(0, 6))

        # 2. Why Incorrect (if student answer was wrong/unanswered)
        if not item["is_correct"]:
            tk.Label(ai_box, text="2. Why Selection Was Incorrect:", font=("Segoe UI", 9, "bold"), bg=BG_TERTIARY, fg="#FF4C6A", anchor="w").pack(fill="x", pady=(2, 0))
            tk.Label(ai_box, text=res.get("why_incorrect", ""), font=("Segoe UI", 9), bg=BG_TERTIARY, fg=TEXT_PRIMARY, wraplength=760, justify="left").pack(fill="x", pady=(0, 6))

        # 3. Learning Tip
        tk.Label(ai_box, text="3. 💡 Key Learning Tip:", font=("Segoe UI", 9, "bold"), bg=BG_TERTIARY, fg=ACCENT_PRIMARY, anchor="w").pack(fill="x", pady=(2, 0))
        tk.Label(ai_box, text=res.get("learning_tip", ""), font=("Segoe UI", 9, "italic"), bg=BG_TERTIARY, fg=TEXT_SECONDARY, wraplength=760, justify="left").pack(fill="x")
