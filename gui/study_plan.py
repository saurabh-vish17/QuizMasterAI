"""
gui/study_plan.py
-----------------
AI Study Plan Screen Component for QuizMaster AI.

Renders personalized study plans generated from deterministic student quiz history
in a clear timeline / card format.

Features:
    - Displays Weak Topics, Recommended Topics, Recommended Difficulty, Practice Duration, Target Questions Count.
    - Displays Revision Priorities in structured card cards.
    - Displays 7-Day Study Timeline Schedule.
    - [Generate Study Plan], [Regenerate], [Refresh] actions.
    - Persists and reloads latest plan from SQLite `ai_analysis` table.
"""

import threading
import tkinter as tk
from tkinter import ttk, messagebox
from typing import TYPE_CHECKING, Optional, Dict, Any

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


class StudyPlanScreen(tk.Frame):
    """
    GUI Screen for viewing, generating, and refreshing personalized AI study plans.
    """

    def __init__(self, parent: tk.Widget, controller: "App"):
        super().__init__(parent, bg=BG_PRIMARY)
        self.controller = controller
        self.result_service = ResultService(db_mgr=self.controller.auth_service.db_mgr)
        self.current_plan: Optional[Dict[str, Any]] = None

        self._create_widgets()
        self._load_saved_study_plan()

    def _create_widgets(self):
        user = self.controller.auth_service.current_user
        student_name = user.name if user else "Student"

        # --- Top Navigation Bar ---
        navbar = tk.Frame(self, bg=BG_SECONDARY, padx=20, pady=12)
        navbar.pack(fill="x", side="top")

        lbl_title = tk.Label(
            navbar,
            text="💡 AI Personalized Study Plan",
            font=("Segoe UI", 16, "bold"),
            bg=BG_SECONDARY,
            fg=ACCENT_PRIMARY
        )
        lbl_title.pack(side="left")

        btn_dashboard = tk.Button(
            navbar,
            text="🏠 BACK TO DASHBOARD",
            font=("Segoe UI", 9, "bold"),
            bg=BG_TERTIARY,
            fg=TEXT_PRIMARY,
            activebackground=ACCENT_PRIMARY,
            activeforeground="#000000",
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=5,
            command=self.controller.show_dashboard
        )
        btn_dashboard.pack(side="right")

        # --- Sub-Header Toolbar ---
        toolbar = tk.Frame(self, bg=BG_PRIMARY, padx=25, pady=10)
        toolbar.pack(fill="x")

        lbl_sub = tk.Label(
            toolbar,
            text=f"Personalized study plan for {student_name} based on stored attempt statistics.",
            font=("Segoe UI", 9),
            bg=BG_PRIMARY,
            fg=TEXT_SECONDARY
        )
        lbl_sub.pack(side="left")

        btn_frame = tk.Frame(toolbar, bg=BG_PRIMARY)
        btn_frame.pack(side="right")

        self.btn_generate = tk.Button(
            btn_frame,
            text="⚡ GENERATE STUDY PLAN",
            font=("Segoe UI", 9, "bold"),
            bg=ACCENT_PRIMARY,
            fg="#000000",
            activebackground=ACCENT_GLOW,
            activeforeground="#000000",
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=6,
            command=self._generate_plan_async
        )
        self.btn_generate.pack(side="left", padx=5)

        self.btn_refresh = tk.Button(
            btn_frame,
            text="🔄 REFRESH",
            font=("Segoe UI", 9, "bold"),
            bg=BG_TERTIARY,
            fg=TEXT_PRIMARY,
            activebackground=ACCENT_PRIMARY,
            activeforeground="#000000",
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=6,
            command=self._load_saved_study_plan
        )
        self.btn_refresh.pack(side="left", padx=5)

        # Status / Spinner Label
        self.lbl_status = tk.Label(
            self,
            text="",
            font=("Segoe UI", 9, "italic"),
            bg=BG_PRIMARY,
            fg=ACCENT_PRIMARY
        )
        self.lbl_status.pack(pady=(0, 5))

        # --- Main Scrollable Canvas Frame ---
        self.canvas_container = tk.Frame(self, bg=BG_PRIMARY)
        self.canvas_container.pack(fill="both", expand=True, padx=25, pady=(0, 15))

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

    def _load_saved_study_plan(self):
        """Loads the latest stored study plan from SQLite ai_analysis table."""
        user = self.controller.auth_service.current_user
        if not user:
            return

        plan = self.result_service.get_latest_study_plan(user.id)
        if plan:
            self.current_plan = plan
            self.btn_generate.config(text="🔄 REGENERATE STUDY PLAN")
            self._render_study_plan(plan)
        else:
            self._render_empty_state()

    def _render_empty_state(self):
        """Renders initial state when no study plan has been generated yet."""
        for child in self.scrollable_content.winfo_children():
            child.destroy()

        card = tk.Frame(
            self.scrollable_content,
            bg=BG_SECONDARY,
            padx=40,
            pady=40,
            highlightbackground=ACCENT_PRIMARY,
            highlightthickness=1
        )
        card.pack(fill="x", pady=30, padx=20)

        lbl_icon = tk.Label(card, text="💡", font=("Segoe UI", 36), bg=BG_SECONDARY)
        lbl_icon.pack(pady=(0, 10))

        lbl_heading = tk.Label(
            card,
            text="No Study Plan Generated Yet",
            font=("Segoe UI", 16, "bold"),
            bg=BG_SECONDARY,
            fg=TEXT_PRIMARY
        )
        lbl_heading.pack(pady=(0, 6))

        lbl_desc = tk.Label(
            card,
            text="Click 'Generate Study Plan' below to create a personalized 7-day revision timeline\n"
                 "targeting your weak areas based on stored quiz results.",
            font=("Segoe UI", 10),
            bg=BG_SECONDARY,
            fg=TEXT_SECONDARY,
            justify="center"
        )
        lbl_desc.pack(pady=(0, 20))

        btn_gen = tk.Button(
            card,
            text="⚡ GENERATE STUDY PLAN NOW",
            font=("Segoe UI", 10, "bold"),
            bg=ACCENT_PRIMARY,
            fg="#000000",
            activebackground=ACCENT_GLOW,
            activeforeground="#000000",
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=8,
            command=self._generate_plan_async
        )
        btn_gen.pack()

    def _generate_plan_async(self):
        """Runs study plan generation in a background thread to prevent UI lockup."""
        self.btn_generate.config(state="disabled")
        self.btn_refresh.config(state="disabled")
        self.lbl_status.config(text="⏳ Aggregating performance statistics and generating AI study plan...")

        def thread_target():
            user = self.controller.auth_service.current_user
            if not user:
                return

            plan = self.result_service.generate_and_save_study_plan(user_id=user.id)
            self.after(0, lambda: self._on_plan_generated(plan))

        threading.Thread(target=thread_target, daemon=True).start()

    def _on_plan_generated(self, plan: Dict[str, Any]):
        """Callback executed on main UI thread after plan generation completes."""
        self.btn_generate.config(state="normal", text="🔄 REGENERATE STUDY PLAN")
        self.btn_refresh.config(state="normal")
        self.lbl_status.config(text="✅ Study plan generated and saved successfully!")

        self.current_plan = plan
        self._render_study_plan(plan)

    def _render_study_plan(self, plan: Dict[str, Any]):
        """Renders the study plan cards, chips, priorities, and timeline schedule."""
        for child in self.scrollable_content.winfo_children():
            child.destroy()

        title = plan.get("title", "7-Day Personalized Study Plan")
        duration = plan.get("suggested_practice_duration", "30 mins / day")
        difficulty = plan.get("recommended_difficulty", "Medium")
        target_qs = plan.get("questions_to_practice", 15)
        weak_topics = plan.get("weak_topics", [])
        recommended_topics = plan.get("recommended_topics", [])
        priorities = plan.get("revision_priorities", [])
        timeline = plan.get("study_plan", [])
        saved_at = plan.get("created_at", "")

        # --- 1. Top Title & Summary Chips Banner ---
        hdr_banner = tk.Frame(
            self.scrollable_content,
            bg=BG_SECONDARY,
            padx=20,
            pady=18,
            highlightbackground=ACCENT_PRIMARY,
            highlightthickness=1
        )
        hdr_banner.pack(fill="x", pady=(0, 18))

        lbl_p_title = tk.Label(
            hdr_banner,
            text=f"🎯 {title}",
            font=("Segoe UI", 16, "bold"),
            bg=BG_SECONDARY,
            fg=TEXT_PRIMARY,
            anchor="w"
        )
        lbl_p_title.pack(fill="x", pady=(0, 10))

        # Chips Grid Header (2x2)
        chips_frame = tk.Frame(hdr_banner, bg=BG_SECONDARY)
        chips_frame.pack(fill="x")

        chip_items = [
            ("⚡ Recommended Difficulty", f"{difficulty}", "#FF4081"),
            ("⏱️ Suggested Daily Practice", f"{duration}", "#00E676"),
            ("📝 Target Questions / Day", f"{target_qs} Questions", "#00BCD4"),
            ("📌 Target Weak Areas", f"{', '.join(weak_topics[:3]) if weak_topics else 'General Practice'}", "#FFB300"),
        ]

        for idx, (label, val, color) in enumerate(chip_items):
            c_box = tk.Frame(
                chips_frame,
                bg=BG_TERTIARY,
                padx=12,
                pady=8,
                highlightbackground=color,
                highlightthickness=1
            )
            c_box.grid(row=idx // 2, column=idx % 2, sticky="nsew", padx=6, pady=6)
            chips_frame.columnconfigure(idx % 2, weight=1)

            lbl_cl = tk.Label(c_box, text=label, font=("Segoe UI", 8), bg=BG_TERTIARY, fg=TEXT_SECONDARY, anchor="w")
            lbl_cl.pack(fill="x")
            lbl_cv = tk.Label(c_box, text=val, font=("Segoe UI", 10, "bold"), bg=BG_TERTIARY, fg=color, anchor="w")
            lbl_cv.pack(fill="x")

        # --- 2. Revision Priorities Section ---
        if priorities:
            lbl_p_sec = tk.Label(
                self.scrollable_content,
                text="📌 Revision Priorities",
                font=("Segoe UI", 13, "bold"),
                bg=BG_PRIMARY,
                fg=ACCENT_PRIMARY,
                anchor="w"
            )
            lbl_p_sec.pack(fill="x", pady=(10, 8))

            p_container = tk.Frame(self.scrollable_content, bg=BG_PRIMARY)
            p_container.pack(fill="x", pady=(0, 15))

            for item in priorities:
                p_num = item.get("priority", 1)
                topic = item.get("topic", "Topic")
                reason = item.get("reason", "Requires concept revision.")
                mins = item.get("daily_minutes", 20)
                qs = item.get("target_questions", 5)

                p_card = tk.Frame(
                    p_container,
                    bg=BG_SECONDARY,
                    padx=15,
                    pady=12,
                    highlightbackground="#FF4C6A" if p_num == 1 else "#FFB300",
                    highlightthickness=1
                )
                p_card.pack(fill="x", pady=5)

                lbl_p_hdr = tk.Label(
                    p_card,
                    text=f"Priority {p_num}: {topic}",
                    font=("Segoe UI", 11, "bold"),
                    bg=BG_SECONDARY,
                    fg=TEXT_PRIMARY,
                    anchor="w"
                )
                lbl_p_hdr.pack(fill="x")

                lbl_p_rsn = tk.Label(
                    p_card,
                    text=f"• Justification: {reason}",
                    font=("Segoe UI", 9),
                    bg=BG_SECONDARY,
                    fg=TEXT_SECONDARY,
                    anchor="w"
                )
                lbl_p_rsn.pack(fill="x", pady=(2, 4))

                lbl_p_goal = tk.Label(
                    p_card,
                    text=f"• Daily Target: ⏱️ {mins} mins | 📝 {qs} practice questions",
                    font=("Segoe UI", 9, "bold"),
                    bg=BG_SECONDARY,
                    fg="#00E676",
                    anchor="w"
                )
                lbl_p_goal.pack(fill="x")

        # --- 3. 7-Day Timeline Schedule Section ---
        lbl_t_sec = tk.Label(
            self.scrollable_content,
            text="🗓️ 7-Day Mastery Schedule",
            font=("Segoe UI", 13, "bold"),
            bg=BG_PRIMARY,
            fg=ACCENT_PRIMARY,
            anchor="w"
        )
        lbl_t_sec.pack(fill="x", pady=(10, 8))

        timeline_container = tk.Frame(self.scrollable_content, bg=BG_PRIMARY)
        timeline_container.pack(fill="x", pady=(0, 20))

        for day_info in timeline:
            day_num = day_info.get("day", 1)
            t_name = day_info.get("topic", f"Day {day_num} Topic")
            focus = day_info.get("focus", "Review key concepts.")
            activities = day_info.get("activities", [])

            t_card = tk.Frame(
                timeline_container,
                bg=BG_SECONDARY,
                padx=15,
                pady=12,
                highlightbackground=BG_TERTIARY,
                highlightthickness=1
            )
            t_card.pack(fill="x", pady=6)

            hdr_line = tk.Frame(t_card, bg=BG_SECONDARY)
            hdr_line.pack(fill="x", pady=(0, 4))

            badge_day = tk.Label(
                hdr_line,
                text=f"DAY {day_num}",
                font=("Segoe UI", 9, "bold"),
                bg=ACCENT_PRIMARY,
                fg="#000000",
                padx=8,
                pady=2
            )
            badge_day.pack(side="left", padx=(0, 10))

            lbl_t_name = tk.Label(
                hdr_line,
                text=t_name,
                font=("Segoe UI", 11, "bold"),
                bg=BG_SECONDARY,
                fg=TEXT_PRIMARY,
                anchor="w"
            )
            lbl_t_name.pack(side="left", fill="x", expand=True)

            lbl_focus = tk.Label(
                t_card,
                text=f"Focus Objective: {focus}",
                font=("Segoe UI", 9, "italic"),
                bg=BG_SECONDARY,
                fg=TEXT_SECONDARY,
                anchor="w"
            )
            lbl_focus.pack(fill="x", pady=(0, 6))

            if activities:
                for act in activities:
                    lbl_act = tk.Label(
                        t_card,
                        text=f"  ✔  {act}",
                        font=("Segoe UI", 9),
                        bg=BG_SECONDARY,
                        fg=TEXT_PRIMARY,
                        anchor="w"
                    )
                    lbl_act.pack(fill="x", pady=1)
