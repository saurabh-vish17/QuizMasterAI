"""
gui/ai_assistant.py
-------------------
AI Study Assistant Screen Component for QuizMaster AI.

Provides an interactive academic chatbot interface helping students with:
    - Explaining concepts
    - Explaining questions & correct answers
    - Providing hints
    - Summarizing topics
    - Suggesting practice topics

Features:
    - Supported request quick action chips/buttons.
    - Asynchronous background loading indication.
    - Conversation length limiting (max 20 turns).
    - Read-only formatted output with no code execution or DB mutation.
"""

import threading
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from typing import TYPE_CHECKING, List, Dict, Any, Optional

from services.ai_service import AIService
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


MAX_CONVERSATION_TURNS = 20


class AIAssistantScreen(tk.Frame):
    """
    GUI Screen for the AI Study Assistant chatbot interface.
    """

    def __init__(self, parent: tk.Widget, controller: "App"):
        super().__init__(parent, bg=BG_PRIMARY)
        self.controller = controller
        self.ai_service = AIService()
        self.chat_history: List[Dict[str, str]] = []
        self.turn_count = 0

        self._create_widgets()
        self._send_welcome_message()

    def _create_widgets(self):
        # --- 1. Top Navigation Bar ---
        navbar = tk.Frame(self, bg=BG_SECONDARY, padx=20, pady=12)
        navbar.pack(fill="x", side="top")

        lbl_title = tk.Label(
            navbar,
            text="🤖 AI Study Assistant",
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

        btn_clear = tk.Button(
            navbar,
            text="🗑️ CLEAR CHAT",
            font=("Segoe UI", 9, "bold"),
            bg=BG_TERTIARY,
            fg=TEXT_SECONDARY,
            activebackground="#FF4C6A",
            activeforeground="#FFFFFF",
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=5,
            command=self._clear_chat
        )
        btn_clear.pack(side="right", padx=10)

        # --- 2. Sub-Header Quick Action Chips Bar ---
        chips_bar = tk.Frame(self, bg=BG_PRIMARY, padx=20, pady=10)
        chips_bar.pack(fill="x")

        lbl_chips_hdr = tk.Label(
            chips_bar,
            text="QUICK ACADEMIC REQUESTS:",
            font=("Segoe UI", 8, "bold"),
            bg=BG_PRIMARY,
            fg=TEXT_SECONDARY
        )
        lbl_chips_hdr.pack(anchor="w", pady=(0, 4))

        chips_inner = tk.Frame(chips_bar, bg=BG_PRIMARY)
        chips_inner.pack(fill="x")

        quick_requests = [
            ("💡 Explain Concept", "explain_concept", "Which concept would you like explained? (e.g. Object-Oriented Programming, Polymorphism)"),
            ("❓ Explain Question", "explain_question", "Paste or type the question text you want explained:"),
            ("🔑 Give a Hint", "give_hint", "What question or problem do you need a hint for?"),
            ("📝 Summarize Topic", "summarize_topic", "Which topic would you like summarized? (e.g. Python Exception Handling)"),
            ("🎯 Suggest Practice Topics", "suggest_topics", None),
            ("✅ Explain Correct Answer", "explain_correct_answer", "What topic or question answer would you like explained?"),
        ]

        for text, req_type, prompt_msg in quick_requests:
            btn = tk.Button(
                chips_inner,
                text=text,
                font=("Segoe UI", 8, "bold"),
                bg=BG_SECONDARY,
                fg=TEXT_PRIMARY,
                activebackground=ACCENT_PRIMARY,
                activeforeground="#000000",
                relief="flat",
                cursor="hand2",
                padx=8,
                pady=4,
                command=lambda rt=req_type, pm=prompt_msg, txt=text: self._handle_quick_request(rt, pm, txt)
            )
            btn.pack(side="left", padx=4, pady=2)

        # --- 3. Chat Messages Log Display ---
        chat_frame = tk.Frame(self, bg=BG_PRIMARY, padx=20, pady=5)
        chat_frame.pack(fill="both", expand=True)

        self.chat_display = tk.Text(
            chat_frame,
            bg=BG_SECONDARY,
            fg=TEXT_PRIMARY,
            font=("Segoe UI", 10),
            wrap="word",
            state="disabled",
            padx=15,
            pady=15,
            relief="flat",
            highlightbackground=ACCENT_PRIMARY,
            highlightthickness=1
        )
        self.chat_scrollbar = ttk.Scrollbar(chat_frame, orient="vertical", command=self.chat_display.yview)
        self.chat_display.configure(yscrollcommand=self.chat_scrollbar.set)

        self.chat_display.pack(side="left", fill="both", expand=True)
        self.chat_scrollbar.pack(side="right", fill="y")

        # Configure Text Tags for styling
        self.chat_display.tag_config("user_hdr", font=("Segoe UI", 10, "bold"), foreground="#00E676")
        self.chat_display.tag_config("ai_hdr", font=("Segoe UI", 10, "bold"), foreground=ACCENT_PRIMARY)
        self.chat_display.tag_config("system_hdr", font=("Segoe UI", 9, "italic"), foreground=TEXT_SECONDARY)
        self.chat_display.tag_config("msg_body", font=("Segoe UI", 10), foreground=TEXT_PRIMARY)
        self.chat_display.tag_config("suggest_hdr", font=("Segoe UI", 9, "bold"), foreground="#FFB300")

        # --- 4. Status Indicator & Input Bar ---
        input_container = tk.Frame(self, bg=BG_PRIMARY, padx=20, pady=10)
        input_container.pack(fill="x", side="bottom")

        self.lbl_status = tk.Label(
            input_container,
            text="",
            font=("Segoe UI", 9, "italic"),
            bg=BG_PRIMARY,
            fg=ACCENT_PRIMARY,
            anchor="w"
        )
        self.lbl_status.pack(fill="x", pady=(0, 4))

        input_inner = tk.Frame(input_container, bg=BG_PRIMARY)
        input_inner.pack(fill="x")

        self.txt_input = tk.Entry(
            input_inner,
            bg=BG_TERTIARY,
            fg=TEXT_PRIMARY,
            insertbackground=TEXT_PRIMARY,
            font=("Segoe UI", 11),
            relief="flat",
            highlightbackground=ACCENT_PRIMARY,
            highlightthickness=1
        )
        self.txt_input.pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 10))
        self.txt_input.bind("<Return>", lambda e: self._send_user_message())

        self.btn_send = tk.Button(
            input_inner,
            text="⚡ SEND",
            font=("Segoe UI", 10, "bold"),
            bg=ACCENT_PRIMARY,
            fg="#000000",
            activebackground=ACCENT_GLOW,
            activeforeground="#000000",
            relief="flat",
            cursor="hand2",
            padx=18,
            pady=8,
            command=self._send_user_message
        )
        self.btn_send.pack(side="right")

    def _send_welcome_message(self):
        """Displays initial greeting and academic guidelines."""
        welcome_txt = (
            "Hello! I am your AI Study Assistant. 🎓\n"
            "I'm here to help you master Computer Science concepts, answer quiz questions, provide hints, "
            "summarize topics, and recommend practice focus areas.\n\n"
            "How can I assist your learning today? Use the quick action buttons above or type your question below!"
        )
        self._append_chat("🤖 QuizMaster AI Tutor", welcome_txt, tag="ai_hdr")

    def _append_chat(self, header: str, message: str, tag: str = "msg_body"):
        """Appends a styled message to the chat display widget safely."""
        self.chat_display.config(state="normal")
        self.chat_display.insert("end", f"\n{header}\n", tag)
        self.chat_display.insert("end", f"{message}\n", "msg_body")
        self.chat_display.see("end")
        self.chat_display.config(state="disabled")

    def _clear_chat(self):
        """Resets chat log display and clears history session."""
        self.chat_history.clear()
        self.turn_count = 0
        self.chat_display.config(state="normal")
        self.chat_display.delete("1.0", "end")
        self.chat_display.config(state="disabled")
        self._send_welcome_message()
        self.lbl_status.config(text="Chat history cleared.")

    def _handle_quick_request(self, req_type: str, prompt_msg: Optional[str], chip_label: str):
        """Handles click on quick action chips."""
        if self.turn_count >= MAX_CONVERSATION_TURNS:
            messagebox.showwarning(
                "Limit Reached",
                f"You have reached the maximum conversation limit of {MAX_CONVERSATION_TURNS} turns.\n"
                "Please click 'CLEAR CHAT' to begin a fresh session."
            )
            return

        if prompt_msg:
            user_input = simpledialog.askstring("Academic Request", prompt_msg, parent=self)
            if not user_input or not user_input.strip():
                return
            msg_text = user_input.strip()
        else:
            msg_text = f"Please {chip_label.lower()} for me."

        self._process_message(msg_text, req_type=req_type)

    def _send_user_message(self):
        """Sends user message from entry box."""
        if self.turn_count >= MAX_CONVERSATION_TURNS:
            messagebox.showwarning(
                "Limit Reached",
                f"You have reached the maximum conversation limit of {MAX_CONVERSATION_TURNS} turns.\n"
                "Please click 'CLEAR CHAT' to begin a fresh session."
            )
            return

        msg_text = self.txt_input.get().strip()
        if not msg_text:
            return

        self.txt_input.delete(0, "end")
        self._process_message(msg_text, req_type="general_chat")

    def _process_message(self, user_msg: str, req_type: str = "general_chat"):
        """Displays user message and triggers background thread AI processing."""
        user = self.controller.auth_service.current_user
        username = user.name if user else "Student"

        self.turn_count += 1
        self._append_chat(f"👤 {username} (Turn {self.turn_count}/{MAX_CONVERSATION_TURNS})", user_msg, tag="user_hdr")
        self.chat_history.append({"role": "user", "content": user_msg})

        self.btn_send.config(state="disabled")
        self.lbl_status.config(text="⏳ AI Assistant is thinking and preparing answer...")

        def thread_target():
            res = self.ai_service.chat_with_student(
                user_message=user_msg,
                request_type=req_type,
                chat_history=self.chat_history
            )
            self.after(0, lambda: self._on_ai_response(res))

        threading.Thread(target=thread_target, daemon=True).start()

    def _on_ai_response(self, res: Dict[str, Any]):
        """Renders AI response back on main UI thread."""
        self.btn_send.config(state="normal")
        self.lbl_status.config(text="")

        resp_text = res.get("response", "I'm sorry, I could not process your question at this moment.")
        followups = res.get("suggested_followups", [])

        self.chat_history.append({"role": "assistant", "content": resp_text})
        self._append_chat("🤖 QuizMaster AI Tutor", resp_text, tag="ai_hdr")

        if followups:
            f_str = "  • " + "\n  • ".join(followups)
            self.chat_display.config(state="normal")
            self.chat_display.insert("end", f"\n💡 Suggested Follow-ups:\n{f_str}\n", "suggest_hdr")
            self.chat_display.see("end")
            self.chat_display.config(state="disabled")
