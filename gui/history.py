"""
gui/history.py
--------------
Quiz Attempt History screen for QuizMaster AI.

Features:
    - Displays previous quiz attempts for the currently logged-in student
    - Columns: Date, Category, Difficulty, Questions, Correct, Wrong, Score, Percentage, Time
    - Column sorting support (Click column headers to sort asc/desc)
    - Double-click row or click "View Details" to open detailed ResultScreen breakdown
    - Strict user-level isolation (only displays results belonging to active user)
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import TYPE_CHECKING, Optional, List

from models.result import Result
from services.result_service import ResultService
from utils.constants import (
    ACCENT_PRIMARY,
    BG_PRIMARY,
    BG_SECONDARY,
    BG_TERTIARY,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)

if TYPE_CHECKING:
    from gui.app import App


class HistoryScreen(tk.Frame):
    """
    Student Quiz History interface.
    """

    def __init__(self, parent: tk.Widget, controller: "App"):
        super().__init__(parent, bg=BG_PRIMARY)
        self.controller = controller

        self.result_service = ResultService(db_mgr=self.controller.auth_service.db_mgr)
        self.results_data: List[Result] = []
        self.sort_reverse: dict = {}  # {col_name: bool}

        self._create_widgets()
        self._load_user_history()

    def _create_widgets(self):
        # 1. Header Navbar
        nav = tk.Frame(self, bg=BG_SECONDARY, padx=20, pady=12)
        nav.pack(fill="x", side="top")

        lbl_logo = tk.Label(
            nav,
            text="📜 Quiz Attempt History",
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

        # 2. Controls Toolbar
        toolbar = tk.Frame(self, bg=BG_PRIMARY, padx=20, pady=10)
        toolbar.pack(fill="x")

        lbl_sub = tk.Label(
            toolbar,
            text="Select an attempt or double-click to view detailed question breakdown.",
            font=("Segoe UI", 9),
            bg=BG_PRIMARY,
            fg=TEXT_SECONDARY
        )
        lbl_sub.pack(side="left")

        btn_view_details = tk.Button(
            toolbar,
            text="👁️ VIEW ATTEMPT DETAILS",
            font=("Segoe UI", 9, "bold"),
            bg=ACCENT_PRIMARY,
            fg="#000000",
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=4,
            command=self._on_view_details_click
        )
        btn_view_details.pack(side="right", padx=(5, 0))

        btn_refresh = tk.Button(
            toolbar,
            text="🔄 REFRESH",
            font=("Segoe UI", 9, "bold"),
            bg=BG_TERTIARY,
            fg=TEXT_PRIMARY,
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=4,
            command=self._load_user_history
        )
        btn_refresh.pack(side="right")

        # 3. History Treeview Table
        table_frame = tk.Frame(self, bg=BG_PRIMARY, padx=20, pady=5)
        table_frame.pack(fill="both", expand=True)

        columns = ("id", "date", "category", "difficulty", "questions", "correct", "wrong", "score", "percentage", "time")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")

        # Configure Column Headers & Widths
        headers = {
            "id": ("# ID", 50),
            "date": ("Date & Time", 140),
            "category": ("Category", 120),
            "difficulty": ("Difficulty", 90),
            "questions": ("Total Qs", 75),
            "correct": ("Correct", 70),
            "wrong": ("Wrong", 70),
            "score": ("Score", 70),
            "percentage": ("Percentage", 95),
            "time": ("Time Spent", 90),
        }

        for col, (text, width) in headers.items():
            self.tree.heading(col, text=text, command=lambda c=col: self._sort_column(c))
            self.tree.column(col, width=width, anchor="center")

        # Add Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind Double-Click Event
        self.tree.bind("<Double-1>", lambda event: self._on_view_details_click())

        # Empty State Message Label (hidden when records exist)
        self.lbl_empty = tk.Label(
            self,
            text="No previous quiz attempts found.\nClick 'Start Quiz' from your Dashboard to attempt your first quiz!",
            font=("Segoe UI", 11),
            bg=BG_PRIMARY,
            fg=TEXT_SECONDARY,
            pady=20
        )

    def _load_user_history(self):
        """Loads quiz results belonging exclusively to the logged-in user."""
        user = self.controller.auth_service.current_user
        if not user:
            return

        self.results_data = self.result_service.get_user_results(user.id)

        # Clear Treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not self.results_data:
            self.lbl_empty.pack(pady=40)
            return
        else:
            self.lbl_empty.pack_forget()

        for res in self.results_data:
            pct_str = f"{res.percentage:.1f}%"
            diff_str = res.difficulty.capitalize()
            date_str = res.quiz_date[:16] if res.quiz_date else "N/A"

            self.tree.insert(
                "",
                "end",
                iid=str(res.result_id),
                values=(
                    res.result_id,
                    date_str,
                    res.category,
                    diff_str,
                    res.total_questions,
                    res.correct_answers,
                    res.wrong_answers,
                    f"{res.score:.0f}",
                    pct_str,
                    res.formatted_time()
                )
            )

    def _sort_column(self, col: str):
        """Sorts Treeview table rows when column header is clicked."""
        reverse = self.sort_reverse.get(col, False)

        # Retrieve items from treeview
        items = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]

        # Numeric sorting for specific columns
        if col in ("id", "questions", "correct", "wrong", "score"):
            items.sort(key=lambda x: float(x[0].replace("%", "").strip() or 0), reverse=reverse)
        elif col == "percentage":
            items.sort(key=lambda x: float(x[0].replace("%", "").strip() or 0), reverse=reverse)
        else:
            items.sort(key=lambda x: str(x[0]).lower(), reverse=reverse)

        # Rearrange items in tree
        for index, (_, k) in enumerate(items):
            self.tree.move(k, "", index)

        # Toggle sort direction
        self.sort_reverse[col] = not reverse

    def _on_view_details_click(self):
        """Opens ResultScreen for selected history row."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Select Attempt", "Please select a quiz attempt from the history table to view details.", parent=self)
            return

        result_id = int(selected[0])
        self.controller.show_result_screen(result_id)
