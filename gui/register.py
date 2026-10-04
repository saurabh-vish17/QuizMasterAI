"""
gui/register.py
---------------
Tkinter Register Screen for QuizMaster AI.
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


class RegisterScreen(tk.Frame):
    """
    Tkinter view component for user registration.
    """

    def __init__(self, parent: tk.Widget, controller: "App"):
        super().__init__(parent, bg=BG_PRIMARY)
        self.controller = controller

        self._create_widgets()

    def _create_widgets(self):
        """Constructs the dark theme + neon blue register user interface."""
        card = tk.Frame(
            self,
            bg=BG_SECONDARY,
            padx=40,
            pady=30,
            highlightbackground=ACCENT_PRIMARY,
            highlightthickness=1
        )
        card.place(relx=0.5, rely=0.5, anchor="center")

        # Header Title
        lbl_title = tk.Label(
            card,
            text="Create an Account",
            font=("Segoe UI", 22, "bold"),
            bg=BG_SECONDARY,
            fg=ACCENT_PRIMARY
        )
        lbl_title.pack(pady=(0, 2))

        lbl_subtitle = tk.Label(
            card,
            text="Join QuizMaster AI to take quizzes and track progress",
            font=("Segoe UI", 10),
            bg=BG_SECONDARY,
            fg=TEXT_SECONDARY
        )
        lbl_subtitle.pack(pady=(0, 15))

        # Status / Error Banner Label
        self.lbl_status = tk.Label(
            card,
            text="",
            font=("Segoe UI", 10, "bold"),
            bg=BG_SECONDARY,
            fg="#FF4C6A",
            wraplength=340
        )
        self.lbl_status.pack(pady=(0, 10))

        # Form Container
        form = tk.Frame(card, bg=BG_SECONDARY)
        form.pack(fill="x", expand=True)

        # Full Name
        lbl_name = tk.Label(form, text="Full Name", font=("Segoe UI", 9, "bold"), bg=BG_SECONDARY, fg=TEXT_PRIMARY, anchor="w")
        lbl_name.pack(fill="x", pady=(2, 1))
        self.ent_name = tk.Entry(form, font=("Segoe UI", 10), bg=BG_TERTIARY, fg=TEXT_PRIMARY, insertbackground=ACCENT_PRIMARY, relief="flat", bd=4)
        self.ent_name.pack(fill="x", ipady=3, pady=(0, 10))

        # Username
        lbl_uname = tk.Label(form, text="Username", font=("Segoe UI", 9, "bold"), bg=BG_SECONDARY, fg=TEXT_PRIMARY, anchor="w")
        lbl_uname.pack(fill="x", pady=(2, 1))
        self.ent_username = tk.Entry(form, font=("Segoe UI", 10), bg=BG_TERTIARY, fg=TEXT_PRIMARY, insertbackground=ACCENT_PRIMARY, relief="flat", bd=4)
        self.ent_username.pack(fill="x", ipady=3, pady=(0, 10))

        # Email
        lbl_email = tk.Label(form, text="Email Address", font=("Segoe UI", 9, "bold"), bg=BG_SECONDARY, fg=TEXT_PRIMARY, anchor="w")
        lbl_email.pack(fill="x", pady=(2, 1))
        self.ent_email = tk.Entry(form, font=("Segoe UI", 10), bg=BG_TERTIARY, fg=TEXT_PRIMARY, insertbackground=ACCENT_PRIMARY, relief="flat", bd=4)
        self.ent_email.pack(fill="x", ipady=3, pady=(0, 10))

        # Password
        lbl_pass = tk.Label(form, text="Password (min 6 characters)", font=("Segoe UI", 9, "bold"), bg=BG_SECONDARY, fg=TEXT_PRIMARY, anchor="w")
        lbl_pass.pack(fill="x", pady=(2, 1))
        self.ent_password = tk.Entry(form, font=("Segoe UI", 10), bg=BG_TERTIARY, fg=TEXT_PRIMARY, insertbackground=ACCENT_PRIMARY, show="•", relief="flat", bd=4)
        self.ent_password.pack(fill="x", ipady=3, pady=(0, 10))

        # Role Selection Radio Buttons
        lbl_role = tk.Label(form, text="Account Type", font=("Segoe UI", 9, "bold"), bg=BG_SECONDARY, fg=TEXT_PRIMARY, anchor="w")
        lbl_role.pack(fill="x", pady=(2, 2))

        role_frame = tk.Frame(form, bg=BG_SECONDARY)
        role_frame.pack(fill="x", pady=(0, 5))

        self.var_role = tk.StringVar(value="student")

        rdo_student = tk.Radiobutton(
            role_frame, text="Student", variable=self.var_role, value="student",
            font=("Segoe UI", 10), bg=BG_SECONDARY, fg=TEXT_PRIMARY,
            selectcolor=BG_TERTIARY, activebackground=BG_SECONDARY, activeforeground=ACCENT_PRIMARY,
            command=self._on_role_change
        )
        rdo_student.pack(side="left", padx=(0, 20))

        rdo_admin = tk.Radiobutton(
            role_frame, text="Administrator", variable=self.var_role, value="admin",
            font=("Segoe UI", 10), bg=BG_SECONDARY, fg=TEXT_PRIMARY,
            selectcolor=BG_TERTIARY, activebackground=BG_SECONDARY, activeforeground=ACCENT_PRIMARY,
            command=self._on_role_change
        )
        rdo_admin.pack(side="left")

        # Admin Secret Key Field (Hidden by default for Student)
        self.admin_key_frame = tk.Frame(form, bg=BG_SECONDARY)
        lbl_admin_key = tk.Label(
            self.admin_key_frame, text="Admin Secret Key", font=("Segoe UI", 9, "bold"),
            bg=BG_SECONDARY, fg=TEXT_PRIMARY, anchor="w"
        )
        lbl_admin_key.pack(fill="x", pady=(2, 1))
        self.ent_admin_key = tk.Entry(
            self.admin_key_frame, font=("Segoe UI", 10), bg=BG_TERTIARY, fg=TEXT_PRIMARY,
            insertbackground=ACCENT_PRIMARY, show="•", relief="flat", bd=4
        )
        self.ent_admin_key.pack(fill="x", ipady=3, pady=(0, 5))

        # Submit Register Button
        btn_register = tk.Button(
            card,
            text="CREATE ACCOUNT",
            font=("Segoe UI", 11, "bold"),
            bg=ACCENT_PRIMARY,
            fg="#000000",
            activebackground=ACCENT_GLOW,
            activeforeground="#000000",
            relief="flat",
            cursor="hand2",
            command=self._on_register_click
        )
        btn_register.pack(fill="x", ipady=7, pady=(10, 15))

        # Back to Login Link
        footer_frame = tk.Frame(card, bg=BG_SECONDARY)
        footer_frame.pack()

        lbl_has_account = tk.Label(
            footer_frame,
            text="Already have an account?",
            font=("Segoe UI", 10),
            bg=BG_SECONDARY,
            fg=TEXT_SECONDARY
        )
        lbl_has_account.pack(side="left", padx=(0, 5))

        btn_login_link = tk.Label(
            footer_frame,
            text="Log in here",
            font=("Segoe UI", 10, "bold", "underline"),
            bg=BG_SECONDARY,
            fg=ACCENT_PRIMARY,
            cursor="hand2"
        )
        btn_login_link.pack(side="left")
        btn_login_link.bind("<Button-1>", lambda event: self.controller.show_login())

    def _on_role_change(self):
        """Toggles Admin Secret Key input visibility based on chosen role."""
        if self.var_role.get() == "admin":
            self.admin_key_frame.pack(fill="x", pady=(0, 10))
        else:
            self.admin_key_frame.pack_forget()

    def _on_register_click(self):
        """Handles registration form submission."""
        name = self.ent_name.get()
        username = self.ent_username.get()
        email = self.ent_email.get()
        password = self.ent_password.get()
        role = self.var_role.get()
        admin_key = self.ent_admin_key.get().strip() if role == "admin" else None

        res = self.controller.auth_service.register_user(
            name=name,
            username=username,
            email=email,
            password=password,
            role=role,
            admin_key=admin_key
        )
        if res["success"]:
            self.lbl_status.config(text=res["message"], fg="#00E676")
            self.controller.after(800, self.controller.show_login)
        else:
            self.lbl_status.config(text=res["message"], fg="#FF4C6A")

