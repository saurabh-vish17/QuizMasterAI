"""
gui/leaderboard.py
------------------
Student Leaderboard screen for QuizMaster AI.

Features:
    - Displays student performance rankings based purely on stored deterministic quiz results
    - Columns: Rank (🥇/🥈/🥉), Student Name, Category, Difficulty, Score, Percentage, Time Spent
    - Filter options: Overall, Subject Category, and Difficulty Level
    - Privacy protection: Never exposes emails, passwords, hashes, or private user data
"""

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING, List, Dict, Any

from services.result_service import ResultService
from utils.constants import (
    ACCENT_PRIMARY,
    BG_PRIMARY,
    BG_SECONDARY,
    BG_TERTIARY,
    SUPPORTED_CATEGORIES,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)

if TYPE_CHECKING:
    from gui.app import App


class LeaderboardScreen(tk.Frame):
    """
    Student Leaderboard & Rankings view.
    """

    def __init__(self, parent: tk.Widget, controller: "App"):
        super().__init__(parent, bg=BG_PRIMARY)
        self.controller = controller

        self.result_service = ResultService(db_mgr=self.controller.auth_service.db_mgr)
        self.leaderboard_data: List[Dict[str, Any]] = []

        self._create_widgets()
        self._load_leaderboard()

    def _create_widgets(self):
        # 1. Header Navbar
        nav = tk.Frame(self, bg=BG_SECONDARY, padx=20, pady=12)
        nav.pack(fill="x", side="top")

        lbl_logo = tk.Label(
            nav,
            text="🏆 Student Leaderboard & Rankings",
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

        # 2. Filter Bar (Overall, Category, Difficulty)
        filter_bar = tk.Frame(self, bg=BG_SECONDARY, padx=20, pady=12)
        filter_bar.pack(fill="x", padx=20, pady=(15, 5))

        # Overall Button
        btn_overall = tk.Button(
            filter_bar,
            text="🌐 OVERALL TOP RANKINGS",
            font=("Segoe UI", 9, "bold"),
            bg=ACCENT_PRIMARY,
            fg="#000000",
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=4,
            command=self._reset_filters
        )
        btn_overall.pack(side="left", padx=(0, 20))

        # Category Filter Dropdown
        tk.Label(filter_bar, text="Category:", font=("Segoe UI", 9, "bold"), bg=BG_SECONDARY, fg=TEXT_PRIMARY).pack(side="left", padx=(0, 5))
        self.cmb_category = ttk.Combobox(
            filter_bar,
            values=["All Categories"] + list(SUPPORTED_CATEGORIES),
            state="readonly",
            width=18
        )
        self.cmb_category.set("All Categories")
        self.cmb_category.pack(side="left", padx=(0, 15))
        self.cmb_category.bind("<<ComboboxSelected>>", lambda e: self._load_leaderboard())

        # Difficulty Filter Dropdown
        tk.Label(filter_bar, text="Difficulty:", font=("Segoe UI", 9, "bold"), bg=BG_SECONDARY, fg=TEXT_PRIMARY).pack(side="left", padx=(0, 5))
        self.cmb_difficulty = ttk.Combobox(
            filter_bar,
            values=["All Difficulties", "Easy", "Medium", "Hard"],
            state="readonly",
            width=15
        )
        self.cmb_difficulty.set("All Difficulties")
        self.cmb_difficulty.pack(side="left")
        self.cmb_difficulty.bind("<<ComboboxSelected>>", lambda e: self._load_leaderboard())

        # 3. Leaderboard Treeview Table
        table_frame = tk.Frame(self, bg=BG_PRIMARY, padx=20, pady=5)
        table_frame.pack(fill="both", expand=True)

        columns = ("rank", "student", "category", "difficulty", "score", "percentage", "time")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")

        headers = {
            "rank": ("Rank", 70),
            "student": ("Student Name", 180),
            "category": ("Category", 130),
            "difficulty": ("Difficulty", 95),
            "score": ("Score", 90),
            "percentage": ("Percentage", 100),
            "time": ("Time Taken", 90),
        }

        for col, (text, width) in headers.items():
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width, anchor="center" if col != "student" else "w")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Empty State Label
        self.lbl_empty = tk.Label(
            self,
            text="No leaderboard records available matching selected filters.",
            font=("Segoe UI", 11),
            bg=BG_PRIMARY,
            fg=TEXT_SECONDARY,
            pady=20
        )

    def _reset_filters(self):
        """Resets filters to Overall view."""
        self.cmb_category.set("All Categories")
        self.cmb_difficulty.set("All Difficulties")
        self._load_leaderboard()

    def _load_leaderboard(self):
        """Queries and renders ranked leaderboard data."""
        category = self.cmb_category.get()
        difficulty = self.cmb_difficulty.get()

        self.leaderboard_data = self.result_service.get_leaderboard(
            category=category,
            difficulty=difficulty
        )

        # Clear existing Treeview items
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not self.leaderboard_data:
            self.lbl_empty.pack(pady=40)
            return
        else:
            self.lbl_empty.pack_forget()

        medals = {1: "🥇 #1", 2: "🥈 #2", 3: "🥉 #3"}

        for item in self.leaderboard_data:
            rank_val = medals.get(item["rank"], f"#{item['rank']}")

            self.tree.insert(
                "",
                "end",
                values=(
                    rank_val,
                    item["student_name"],
                    item["category"],
                    item["difficulty"],
                    item["score"],
                    item["formatted_percentage"],
                    item["time_taken"]
                )
            )
