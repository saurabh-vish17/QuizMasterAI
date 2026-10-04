"""
gui/quiz_screen.py
------------------
Interactive Quiz Execution Engine for QuizMaster AI.

Features:
    - Single MCQ display per view with 4 distinct options (A, B, C, D)
    - Dynamic Question Counter & Visual Progress Stepper Grid
    - Previous, Next, and Submit navigation buttons
    - Real-time countdown timer with automatic submission upon expiry
    - State-preserved answer selection (prevents answer loss during navigation)
    - Deterministic scoring executed purely in Python against DB answer keys
    - Detailed quiz attempt persistence to 'results' and 'quiz_attempts' tables
    - Confirmation dialogs for manual submission with unanswered question count warnings
"""

import time
import tkinter as tk
from tkinter import messagebox
from typing import TYPE_CHECKING, Optional, List, Dict, Any

from models.question import Question
from services.quiz_service import QuizService
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


class QuizScreen(tk.Frame):
    """
    Active Quiz Execution Controller and Interface.
    """

    def __init__(
        self,
        parent: tk.Widget,
        controller: "App",
        quiz_config: Optional[Dict[str, Any]] = None,
        questions: Optional[List[Question]] = None
    ):
        super().__init__(parent, bg=BG_PRIMARY)
        self.controller = controller
        self.quiz_config = quiz_config or {"category": "General", "difficulty": "easy", "topic": "General"}
        self.questions: List[Question] = questions or []

        self.quiz_service = QuizService(db_mgr=self.controller.auth_service.db_mgr)
        self.current_index = 0
        self.user_answers: Dict[int, str] = {}  # {question_id: "A"|"B"|"C"|"D"}

        # Calculate time limit: 60 seconds per question (default min 60s)
        self.total_seconds = max(60, len(self.questions) * 60)
        self.time_remaining = self.total_seconds
        self.start_time = time.time()
        self.timer_job = None
        self.submitted = False

        self._create_widgets()
        if self.questions:
            self._load_question(0)
            self._start_timer()

    def _create_widgets(self):
        # 1. Header Navbar & Timer Bar
        nav = tk.Frame(self, bg=BG_SECONDARY, padx=20, pady=12)
        nav.pack(fill="x", side="top")

        cat = self.quiz_config.get("category", "Quiz")
        diff = str(self.quiz_config.get("difficulty", "easy")).capitalize()
        lbl_title = tk.Label(
            nav,
            text=f"⏱️ {cat} Quiz ({diff})",
            font=("Segoe UI", 15, "bold"),
            bg=BG_SECONDARY,
            fg=ACCENT_PRIMARY
        )
        lbl_title.pack(side="left")

        # Timer Badge
        self.lbl_timer = tk.Label(
            nav,
            text="⏱️ Time Remaining: --:--",
            font=("Segoe UI", 12, "bold"),
            bg=BG_TERTIARY,
            fg="#00E676",
            padx=12,
            pady=4
        )
        self.lbl_timer.pack(side="right")

        # 2. Main Question Card Frame
        self.card = tk.Frame(
            self,
            bg=BG_SECONDARY,
            padx=30,
            pady=25,
            highlightbackground=ACCENT_PRIMARY,
            highlightthickness=1
        )
        self.card.pack(fill="both", expand=True, padx=25, pady=(15, 10))

        # Top Meta Bar (Question Counter & Topic)
        meta_bar = tk.Frame(self.card, bg=BG_SECONDARY)
        meta_bar.pack(fill="x", pady=(0, 10))

        self.lbl_counter = tk.Label(
            meta_bar,
            text="Question 1 of 1",
            font=("Segoe UI", 11, "bold"),
            bg=BG_SECONDARY,
            fg=ACCENT_PRIMARY
        )
        self.lbl_counter.pack(side="left")

        self.lbl_topic = tk.Label(
            meta_bar,
            text="",
            font=("Segoe UI", 9, "italic"),
            bg=BG_SECONDARY,
            fg=TEXT_SECONDARY
        )
        self.lbl_topic.pack(side="right")

        # Question Text Box
        self.lbl_question_text = tk.Label(
            self.card,
            text="",
            font=("Segoe UI", 13, "bold"),
            bg=BG_SECONDARY,
            fg=TEXT_PRIMARY,
            wraplength=850,
            justify="left",
            anchor="w"
        )
        self.lbl_question_text.pack(fill="x", pady=(5, 15))

        # Options Container Frame (4 Options: A, B, C, D)
        self.opts_frame = tk.Frame(self.card, bg=BG_SECONDARY)
        self.opts_frame.pack(fill="both", expand=True)

        self.selected_var = tk.StringVar(value="")
        self.option_buttons: Dict[str, tk.Button] = {}

        for key in ["A", "B", "C", "D"]:
            btn_opt = tk.Button(
                self.opts_frame,
                text=f"{key}. Option",
                font=("Segoe UI", 11),
                bg=BG_TERTIARY,
                fg=TEXT_PRIMARY,
                activebackground=ACCENT_PRIMARY,
                activeforeground="#000000",
                anchor="w",
                padx=15,
                pady=10,
                relief="flat",
                cursor="hand2",
                command=lambda k=key: self._on_option_selected(k)
            )
            btn_opt.pack(fill="x", pady=5)
            self.option_buttons[key] = btn_opt

        # 3. Question Stepper Grid (Progress Indicator)
        self.stepper_frame = tk.Frame(self, bg=BG_PRIMARY, padx=25, pady=5)
        self.stepper_frame.pack(fill="x")

        self.stepper_buttons: List[tk.Button] = []
        for i in range(len(self.questions)):
            btn_st = tk.Button(
                self.stepper_frame,
                text=str(i + 1),
                font=("Segoe UI", 9, "bold"),
                width=3,
                bg=BG_SECONDARY,
                fg=TEXT_SECONDARY,
                relief="flat",
                cursor="hand2",
                command=lambda idx=i: self._jump_to_question(idx)
            )
            btn_st.pack(side="left", padx=3)
            self.stepper_buttons.append(btn_st)

        # 4. Bottom Navigation Toolbar
        nav_bar = tk.Frame(self, bg=BG_SECONDARY, padx=25, pady=12)
        nav_bar.pack(fill="x", side="bottom")

        self.btn_prev = tk.Button(
            nav_bar,
            text="← PREVIOUS",
            font=("Segoe UI", 10, "bold"),
            bg=BG_PRIMARY,
            fg=ACCENT_PRIMARY,
            relief="flat",
            cursor="hand2",
            padx=15,
            pady=5,
            command=self._on_prev_click
        )
        self.btn_prev.pack(side="left")

        self.btn_next = tk.Button(
            nav_bar,
            text="NEXT →",
            font=("Segoe UI", 10, "bold"),
            bg=ACCENT_PRIMARY,
            fg="#000000",
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=5,
            command=self._on_next_click
        )
        self.btn_next.pack(side="left", padx=15)

        self.btn_submit = tk.Button(
            nav_bar,
            text="🏁 SUBMIT QUIZ",
            font=("Segoe UI", 10, "bold"),
            bg="#00E676",
            fg="#000000",
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=5,
            command=self._on_submit_click
        )
        self.btn_submit.pack(side="right")

    # --- Timer Engine ---
    def _start_timer(self):
        """Starts countdown timer loop."""
        self._update_timer()

    def _update_timer(self):
        """Ticks countdown timer every 1000ms."""
        if self.submitted:
            return

        mins = self.time_remaining // 60
        secs = self.time_remaining % 60
        timer_str = f"⏱️ Time Remaining: {mins:02d}:{secs:02d}"
        self.lbl_timer.config(text=timer_str)

        if self.time_remaining <= 30:
            self.lbl_timer.config(fg="#FF4C6A", bg="#330011")  # Alert Red Glow
        elif self.time_remaining <= 60:
            self.lbl_timer.config(fg="#FFB300", bg="#2A2216")  # Warning Amber Glow
        else:
            self.lbl_timer.config(fg="#00E676", bg=BG_TERTIARY)

        if self.time_remaining <= 0:
            self._auto_submit_timer_expired()
        else:
            self.time_remaining -= 1
            self.timer_job = self.after(1000, self._update_timer)


    def _auto_submit_timer_expired(self):
        """Triggered automatically when countdown timer reaches zero."""
        if self.submitted:
            return
        messagebox.showinfo("Time Expired!", "⏱️ Time has expired! Your quiz answers are automatically being submitted now.")
        self._execute_submission()

    # --- Navigation & Display Engine ---
    def _load_question(self, index: int):
        """Loads question data at index and updates option selections and stepper styles."""
        if not self.questions or index < 0 or index >= len(self.questions):
            return

        self.current_index = index
        q: Question = self.questions[index]

        # Update counter & topic
        self.lbl_counter.config(text=f"Question {index + 1} of {len(self.questions)}")
        self.lbl_topic.config(text=f"Topic: {q.topic}")
        self.lbl_question_text.config(text=f"Q{index + 1}. {q.question_text}")

        # Update options text
        opts = {
            "A": q.option_a,
            "B": q.option_b,
            "C": q.option_c,
            "D": q.option_d,
        }

        selected_key = self.user_answers.get(q.question_id, "")
        self.selected_var.set(selected_key)

        for key, btn in self.option_buttons.items():
            btn.config(text=f"{key}. {opts[key]}")
            if key == selected_key:
                btn.config(bg=ACCENT_PRIMARY, fg="#000000", font=("Segoe UI", 11, "bold"))
            else:
                btn.config(bg=BG_TERTIARY, fg=TEXT_PRIMARY, font=("Segoe UI", 11))

        # Update Navigation Buttons
        self.btn_prev.config(state="normal" if index > 0 else "disabled")
        if index == len(self.questions) - 1:
            self.btn_next.config(text="NEXT →", state="disabled")
        else:
            self.btn_next.config(text="NEXT →", state="normal")

        # Update Stepper Grid Buttons
        self._update_stepper_grid()

    def _update_stepper_grid(self):
        """Updates stepper grid buttons to indicate answered vs unanswered vs current question."""
        for i, btn in enumerate(self.stepper_buttons):
            q_id = self.questions[i].question_id
            is_answered = q_id in self.user_answers and self.user_answers[q_id] != ""

            if i == self.current_index:
                btn.config(bg=ACCENT_PRIMARY, fg="#000000", font=("Segoe UI", 9, "bold"))
            elif is_answered:
                btn.config(bg="#00E676", fg="#000000", font=("Segoe UI", 9, "bold"))
            else:
                btn.config(bg=BG_SECONDARY, fg=TEXT_SECONDARY, font=("Segoe UI", 9))

    def _on_option_selected(self, key: str):
        """Fired when user clicks an option button A, B, C, or D."""
        if self.submitted or not self.questions:
            return

        q_id = self.questions[self.current_index].question_id
        self.user_answers[q_id] = key
        self.selected_var.set(key)

        # Highlight selected option button
        for k, btn in self.option_buttons.items():
            if k == key:
                btn.config(bg=ACCENT_PRIMARY, fg="#000000", font=("Segoe UI", 11, "bold"))
            else:
                btn.config(bg=BG_TERTIARY, fg=TEXT_PRIMARY, font=("Segoe UI", 11))

        self._update_stepper_grid()

    def _jump_to_question(self, index: int):
        """Direct jump to specified question index."""
        self._load_question(index)

    def _on_prev_click(self):
        if self.current_index > 0:
            self._load_question(self.current_index - 1)

    def _on_next_click(self):
        if self.current_index < len(self.questions) - 1:
            self._load_question(self.current_index + 1)

    # --- Quiz Submission Engine ---
    def _on_submit_click(self):
        """Triggered when user clicks SUBMIT QUIZ button."""
        if self.submitted:
            return

        # Check unanswered questions count
        unanswered_count = 0
        for q in self.questions:
            if q.question_id not in self.user_answers or not self.user_answers[q.question_id]:
                unanswered_count += 1

        if unanswered_count > 0:
            msg = f"⚠️ You have {unanswered_count} unanswered question(s) out of {len(self.questions)}.\n\nAre you sure you want to submit your quiz now?"
        else:
            msg = f"✅ You have answered all {len(self.questions)} question(s).\n\nAre you sure you want to submit your quiz now?"

        confirm = messagebox.askyesno("Confirm Submission", msg, icon="question", parent=self)
        if confirm:
            self._execute_submission()

    def _execute_submission(self):
        """Finalizes attempt, stops timer, evaluates score deterministically, and saves result."""
        if self.submitted:
            return
        self.submitted = True

        if self.timer_job is not None:
            self.after_cancel(self.timer_job)
            self.timer_job = None

        time_taken = int(time.time() - self.start_time)
        user = self.controller.auth_service.current_user
        user_id = user.id if user else 1

        res = self.quiz_service.submit_quiz_attempt(
            user_id=user_id,
            quiz_config=self.quiz_config,
            questions=self.questions,
            user_answers=self.user_answers,
            time_taken=time_taken
        )

        if res["success"]:
            result_id = res["result_id"]
            self.controller.show_result_screen(result_id)
        else:
            messagebox.showerror("Submission Error", res["message"], parent=self)
