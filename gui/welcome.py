"""
gui/welcome.py
--------------
Welcome screen for QuizMaster AI displaying options to Log In or Register.
"""

import tkinter as tk
from typing import TYPE_CHECKING
from utils.constants import (
    ACCENT_GLOW,
    ACCENT_PRIMARY,
    BG_PRIMARY,
    BG_SECONDARY,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)

if TYPE_CHECKING:
    from gui.app import App


class WelcomeScreen(tk.Frame):
    """
    Initial welcome view component.
    """

    def __init__(self, parent: tk.Widget, controller: "App"):
        super().__init__(parent, bg=BG_PRIMARY)
        self.controller = controller

        self._create_widgets()

    def _create_widgets(self):
        """Constructs the dark theme + neon blue welcome interface."""
        card = tk.Frame(
            self,
            bg=BG_SECONDARY,
            padx=50,
            pady=50,
            highlightbackground=ACCENT_PRIMARY,
            highlightthickness=1
        )
        card.place(relx=0.5, rely=0.5, anchor="center")

        # Logo / Badge
        lbl_logo = tk.Label(
            card,
            text="⚡ QuizMaster AI",
            font=("Segoe UI", 28, "bold"),
            bg=BG_SECONDARY,
            fg=ACCENT_PRIMARY
        )
        lbl_logo.pack(pady=(0, 5))

        lbl_desc = tk.Label(
            card,
            text="AI-Enhanced Interactive Quiz Management System",
            font=("Segoe UI", 11),
            bg=BG_SECONDARY,
            fg=TEXT_SECONDARY
        )
        lbl_desc.pack(pady=(0, 30))

        # Log In Button
        btn_login = tk.Button(
            card,
            text="LOG IN TO ACCOUNT",
            font=("Segoe UI", 11, "bold"),
            bg=ACCENT_PRIMARY,
            fg="#000000",
            activebackground=ACCENT_GLOW,
            activeforeground="#000000",
            relief="flat",
            cursor="hand2",
            width=28,
            command=self.controller.show_login
        )
        btn_login.pack(ipady=8, pady=(0, 15))

        # Register Button
        btn_register = tk.Button(
            card,
            text="CREATE NEW ACCOUNT",
            font=("Segoe UI", 11, "bold"),
            bg=BG_PRIMARY,
            fg=ACCENT_PRIMARY,
            activebackground=BG_SECONDARY,
            activeforeground=ACCENT_GLOW,
            highlightbackground=ACCENT_PRIMARY,
            highlightthickness=1,
            relief="flat",
            cursor="hand2",
            width=28,
            command=self.controller.show_register
        )
        btn_register.pack(ipady=8)
