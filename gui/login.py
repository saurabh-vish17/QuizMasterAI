"""
gui/login.py
------------
Tkinter Login Screen for QuizMaster AI.
Sleek dark theme with neon blue accents.
"""

import tkinter as tk
from typing import TYPE_CHECKING
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


class LoginScreen(tk.Frame):
    """
    Tkinter view component for user authentication (Login).
    """

    def __init__(self, parent: tk.Widget, controller: "App"):
        super().__init__(parent, bg=BG_PRIMARY)
        self.controller = controller

        self._create_widgets()

    def _create_widgets(self):
        """Constructs the dark theme + neon blue login user interface."""
        # Main Card Frame
        card = tk.Frame(
            self,
            bg=BG_SECONDARY,
            padx=40,
            pady=40,
            highlightbackground=ACCENT_PRIMARY,
            highlightthickness=1
        )
        card.place(relx=0.5, rely=0.5, anchor="center")

        # Title Header
        lbl_title = tk.Label(
            card,
            text="QuizMaster AI",
            font=("Segoe UI", 24, "bold"),
            bg=BG_SECONDARY,
            fg=ACCENT_PRIMARY
        )
        lbl_title.pack(pady=(0, 5))

        lbl_subtitle = tk.Label(
            card,
            text="Log in to access your quizzes and dashboard",
            font=("Segoe UI", 10),
            bg=BG_SECONDARY,
            fg=TEXT_SECONDARY
        )
        lbl_subtitle.pack(pady=(0, 25))

        # Status / Feedback Message Label
        self.lbl_status = tk.Label(
            card,
            text="",
            font=("Segoe UI", 10, "bold"),
            bg=BG_SECONDARY,
            fg="#FF4C6A",
            wraplength=320
        )
        self.lbl_status.pack(pady=(0, 10))

        # Form Fields Frame
        form_frame = tk.Frame(card, bg=BG_SECONDARY)
        form_frame.pack(fill="x", expand=True)

        # Username / Email Label & Entry
        lbl_user = tk.Label(
            form_frame,
            text="Username or Email",
            font=("Segoe UI", 10, "bold"),
            bg=BG_SECONDARY,
            fg=TEXT_PRIMARY,
            anchor="w"
        )
        lbl_user.pack(fill="x", pady=(5, 2))

        self.ent_username = tk.Entry(
            form_frame,
            font=("Segoe UI", 11),
            bg=BG_TERTIARY,
            fg=TEXT_PRIMARY,
            insertbackground=ACCENT_PRIMARY,
            relief="flat",
            bd=5
        )
        self.ent_username.pack(fill="x", ipady=4, pady=(0, 15))
        self.ent_username.focus_set()

        # Password Label & Entry
        lbl_pass = tk.Label(
            form_frame,
            text="Password",
            font=("Segoe UI", 10, "bold"),
            bg=BG_SECONDARY,
            fg=TEXT_PRIMARY,
            anchor="w"
        )
        lbl_pass.pack(fill="x", pady=(5, 2))

        self.ent_password = tk.Entry(
            form_frame,
            font=("Segoe UI", 11),
            bg=BG_TERTIARY,
            fg=TEXT_PRIMARY,
            insertbackground=ACCENT_PRIMARY,
            show="•",
            relief="flat",
            bd=5
        )
        self.ent_password.pack(fill="x", ipady=4, pady=(0, 25))
        self.ent_password.bind("<Return>", lambda event: self._on_login_click())

        # Login Submit Button
        btn_login = tk.Button(
            card,
            text="LOG IN",
            font=("Segoe UI", 11, "bold"),
            bg=ACCENT_PRIMARY,
            fg="#000000",
            activebackground=ACCENT_GLOW,
            activeforeground="#000000",
            relief="flat",
            cursor="hand2",
            command=self._on_login_click
        )
        btn_login.pack(fill="x", ipady=8, pady=(0, 15))

        # Register Link Frame
        footer_frame = tk.Frame(card, bg=BG_SECONDARY)
        footer_frame.pack()

        lbl_no_account = tk.Label(
            footer_frame,
            text="Don't have an account?",
            font=("Segoe UI", 10),
            bg=BG_SECONDARY,
            fg=TEXT_SECONDARY
        )
        lbl_no_account.pack(side="left", padx=(0, 5))

        btn_register_link = tk.Label(
            footer_frame,
            text="Register here",
            font=("Segoe UI", 10, "bold", "underline"),
            bg=BG_SECONDARY,
            fg=ACCENT_PRIMARY,
            cursor="hand2"
        )
        btn_register_link.pack(side="left")
        btn_register_link.bind("<Button-1>", lambda event: self.controller.show_register())

    def _on_login_click(self):
        """Handles login button click event."""
        username_or_email = self.ent_username.get().strip()
        password = self.ent_password.get()

        res = self.controller.auth_service.login_user(username_or_email, password)
        if res["success"]:
            self.lbl_status.config(text=res["message"], fg="#00E676")
            # Navigate to logged in dashboard
            self.controller.after(300, self.controller.show_dashboard)
        else:
            self.lbl_status.config(text=res["message"], fg="#FF4C6A")
