"""
gui/admin_panel.py
------------------
Admin Panel GUI component for QuizMaster AI.

Features:
    - Admin role access guard
    - Question Bank Management (Add, View, Search, Category Filter, Difficulty Filter, Update, Delete)
    - Tkinter Treeview for records display
    - Confirmation dialogs for destructive operations
    - Student Results Viewer
    - AI Question Generator (Topic, Category, Difficulty, Count selection)
    - AI-Generated Questions Approval Queue (Preview, Approve, Reject)
    - Safety: AI questions are staged into ai_questions with approved_by_admin = 0. Never auto-published.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import TYPE_CHECKING, Optional, Dict, Any

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


class AIQuestionPreviewDialog(tk.Toplevel):
    """
    Modal Dialog to Preview an AI-Generated Question before Approval/Rejection.
    """

    def __init__(self, parent: tk.Widget, question_data: Dict[str, Any], on_approve, on_reject):
        super().__init__(parent)
        self.question_data = question_data
        self.on_approve = on_approve
        self.on_reject = on_reject

        self.title(f"AI Question Preview — #{question_data['id']}")
        self.geometry("620x580")
        self.resizable(False, False)
        self.configure(bg=BG_PRIMARY)
        self.transient(parent)
        self.grab_set()

        self._create_widgets()

    def _create_widgets(self):
        card = tk.Frame(self, bg=BG_SECONDARY, padx=25, pady=25)
        card.pack(fill="both", expand=True, padx=15, pady=15)

        # Header Info
        header = tk.Frame(card, bg=BG_SECONDARY)
        header.pack(fill="x", pady=(0, 10))

        tk.Label(
            header,
            text=f"🤖 AI Pending Question #{self.question_data['id']}",
            font=("Segoe UI", 14, "bold"),
            bg=BG_SECONDARY,
            fg=ACCENT_PRIMARY
        ).pack(side="left")

        badge = tk.Label(
            header,
            text=f"{self.question_data['category']} • {self.question_data['topic']} • {self.question_data['difficulty'].upper()}",
            font=("Segoe UI", 9, "bold"),
            bg=BG_TERTIARY,
            fg=TEXT_SECONDARY,
            padx=10,
            pady=3
        )
        badge.pack(side="right")

        # Question Text Box
        tk.Label(card, text="Question Text:", font=("Segoe UI", 9, "bold"), bg=BG_SECONDARY, fg=TEXT_PRIMARY, anchor="w").pack(fill="x", pady=(5, 2))
        txt_q = tk.Text(card, font=("Segoe UI", 10), bg=BG_TERTIARY, fg=TEXT_PRIMARY, height=3, relief="flat", wrap="word")
        txt_q.insert("1.0", self.question_data["question_text"])
        txt_q.configure(state="disabled")
        txt_q.pack(fill="x", pady=(0, 10))

        # Options Breakdown
        tk.Label(card, text="Multiple Choice Options:", font=("Segoe UI", 9, "bold"), bg=BG_SECONDARY, fg=TEXT_PRIMARY, anchor="w").pack(fill="x", pady=(5, 2))
        corr_key = self.question_data["correct_answer"].upper()

        for key in ["A", "B", "C", "D"]:
            opt_val = self.question_data.get(f"option_{key.lower()}", "")
            is_corr = (key == corr_key)

            row = tk.Frame(card, bg="#0F2D1E" if is_corr else BG_TERTIARY, padx=10, pady=6)
            row.pack(fill="x", pady=2)

            lbl_key = tk.Label(row, text=f"Option {key}:", font=("Segoe UI", 9, "bold"), bg=row["bg"], fg="#00E676" if is_corr else ACCENT_PRIMARY, width=8, anchor="w")
            lbl_key.pack(side="left")

            lbl_val = tk.Label(row, text=opt_val, font=("Segoe UI", 9), bg=row["bg"], fg=TEXT_PRIMARY, anchor="w")
            lbl_val.pack(side="left", fill="x", expand=True)

            if is_corr:
                lbl_tag = tk.Label(row, text="✓ CORRECT KEY", font=("Segoe UI", 8, "bold"), bg="#00E676", fg="#000000", padx=6, pady=1)
                lbl_tag.pack(side="right")

        # Explanation Box
        tk.Label(card, text="AI Explanation / Concept Rationale:", font=("Segoe UI", 9, "bold"), bg=BG_SECONDARY, fg=TEXT_PRIMARY, anchor="w").pack(fill="x", pady=(10, 2))
        txt_exp = tk.Text(card, font=("Segoe UI", 9), bg=BG_TERTIARY, fg=TEXT_SECONDARY, height=3, relief="flat", wrap="word")
        txt_exp.insert("1.0", self.question_data.get("explanation", "No explanation provided."))
        txt_exp.configure(state="disabled")
        txt_exp.pack(fill="x", pady=(0, 15))

        # Bottom Buttons
        btn_bar = tk.Frame(card, bg=BG_SECONDARY)
        btn_bar.pack(fill="x", side="bottom")

        btn_app = tk.Button(
            btn_bar,
            text="✅ APPROVE & PUBLISH",
            font=("Segoe UI", 9, "bold"),
            bg="#00E676",
            fg="#000000",
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=6,
            command=self._do_approve
        )
        btn_app.pack(side="left", padx=(0, 10))

        btn_rej = tk.Button(
            btn_bar,
            text="❌ REJECT & DISCARD",
            font=("Segoe UI", 9, "bold"),
            bg="#FF4C6A",
            fg="#FFFFFF",
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=6,
            command=self._do_reject
        )
        btn_rej.pack(side="left")

        btn_close = tk.Button(
            btn_bar,
            text="CLOSE",
            font=("Segoe UI", 9),
            bg=BG_PRIMARY,
            fg=TEXT_SECONDARY,
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=6,
            command=self.destroy
        )
        btn_close.pack(side="right")

    def _do_approve(self):
        self.destroy()
        self.on_approve(self.question_data["id"])

    def _do_reject(self):
        self.destroy()
        self.on_reject(self.question_data["id"])


class QuestionFormDialog(tk.Toplevel):
    """
    Modal Dialog for Adding or Editing a Question in the Question Bank.
    """

    def __init__(self, parent: tk.Widget, quiz_service: QuizService, question_data: Optional[Dict[str, Any]] = None):
        super().__init__(parent)
        self.quiz_service = quiz_service
        self.question_data = question_data
        self.result = None

        is_edit = question_data is not None
        self.title("Edit Question" if is_edit else "Add New Question")
        self.geometry("600x650")
        self.resizable(False, False)
        self.configure(bg=BG_PRIMARY)
        self.transient(parent)
        self.grab_set()

        self._create_form(is_edit)

    def _create_form(self, is_edit: bool):
        card = tk.Frame(self, bg=BG_SECONDARY, padx=25, pady=25)
        card.pack(fill="both", expand=True, padx=15, pady=15)

        lbl_title = tk.Label(
            card,
            text="✏️ Edit Question" if is_edit else "➕ Add New Question",
            font=("Segoe UI", 16, "bold"),
            bg=BG_SECONDARY,
            fg=ACCENT_PRIMARY
        )
        lbl_title.pack(anchor="w", pady=(0, 15))

        form = tk.Frame(card, bg=BG_SECONDARY)
        form.pack(fill="both", expand=True)

        r1 = tk.Frame(form, bg=BG_SECONDARY)
        r1.pack(fill="x", pady=4)

        tk.Label(r1, text="Category:", font=("Segoe UI", 9, "bold"), bg=BG_SECONDARY, fg=TEXT_PRIMARY).pack(side="left")
        self.cmb_category = ttk.Combobox(r1, values=SUPPORTED_CATEGORIES, state="readonly", width=20)
        self.cmb_category.pack(side="left", padx=(5, 20))
        self.cmb_category.set(self.question_data["category"] if is_edit else SUPPORTED_CATEGORIES[0])

        tk.Label(r1, text="Difficulty:", font=("Segoe UI", 9, "bold"), bg=BG_SECONDARY, fg=TEXT_PRIMARY).pack(side="left")
        self.cmb_difficulty = ttk.Combobox(r1, values=SUPPORTED_DIFFICULTIES, state="readonly", width=12)
        self.cmb_difficulty.pack(side="left", padx=5)
        self.cmb_difficulty.set(self.question_data["difficulty"] if is_edit else "easy")

        r2 = tk.Frame(form, bg=BG_SECONDARY)
        r2.pack(fill="x", pady=4)
        tk.Label(r2, text="Topic:", font=("Segoe UI", 9, "bold"), bg=BG_SECONDARY, fg=TEXT_PRIMARY).pack(side="left")
        self.ent_topic = tk.Entry(r2, font=("Segoe UI", 10), bg=BG_TERTIARY, fg=TEXT_PRIMARY, insertbackground=ACCENT_PRIMARY, relief="flat")
        self.ent_topic.pack(side="left", fill="x", expand=True, padx=5, ipady=3)
        if is_edit:
            self.ent_topic.insert(0, self.question_data["topic"])

        tk.Label(form, text="Question Text:", font=("Segoe UI", 9, "bold"), bg=BG_SECONDARY, fg=TEXT_PRIMARY, anchor="w").pack(fill="x", pady=(8, 2))
        self.txt_question = tk.Text(form, font=("Segoe UI", 10), bg=BG_TERTIARY, fg=TEXT_PRIMARY, insertbackground=ACCENT_PRIMARY, height=3, relief="flat")
        self.txt_question.pack(fill="x", pady=(0, 8))
        if is_edit:
            self.txt_question.insert("1.0", self.question_data["question_text"])

        self.ent_opts = {}
        for key in ["A", "B", "C", "D"]:
            ro = tk.Frame(form, bg=BG_SECONDARY)
            ro.pack(fill="x", pady=2)
            tk.Label(ro, text=f"Option {key}:", font=("Segoe UI", 9, "bold"), bg=BG_SECONDARY, fg=ACCENT_PRIMARY, width=8, anchor="w").pack(side="left")
            ent = tk.Entry(ro, font=("Segoe UI", 10), bg=BG_TERTIARY, fg=TEXT_PRIMARY, insertbackground=ACCENT_PRIMARY, relief="flat")
            ent.pack(side="left", fill="x", expand=True, ipady=2)
            if is_edit:
                ent.insert(0, self.question_data.get(f"option_{key.lower()}", ""))
            self.ent_opts[key] = ent

        r4 = tk.Frame(form, bg=BG_SECONDARY)
        r4.pack(fill="x", pady=(8, 4))
        tk.Label(r4, text="Correct Answer:", font=("Segoe UI", 9, "bold"), bg=BG_SECONDARY, fg=TEXT_PRIMARY).pack(side="left")
        self.cmb_correct = ttk.Combobox(r4, values=["A", "B", "C", "D"], state="readonly", width=6)
        self.cmb_correct.pack(side="left", padx=10)
        self.cmb_correct.set(self.question_data["correct_answer"].upper() if is_edit else "A")

        tk.Label(form, text="Explanation (Optional):", font=("Segoe UI", 9, "bold"), bg=BG_SECONDARY, fg=TEXT_PRIMARY, anchor="w").pack(fill="x", pady=(6, 2))
        self.ent_explanation = tk.Entry(form, font=("Segoe UI", 9), bg=BG_TERTIARY, fg=TEXT_PRIMARY, insertbackground=ACCENT_PRIMARY, relief="flat")
        self.ent_explanation.pack(fill="x", ipady=3, pady=(0, 15))
        if is_edit and self.question_data.get("explanation"):
            self.ent_explanation.insert(0, self.question_data["explanation"])

        btn_frame = tk.Frame(card, bg=BG_SECONDARY)
        btn_frame.pack(fill="x", side="bottom")

        btn_save = tk.Button(
            btn_frame,
            text="SAVE QUESTION",
            font=("Segoe UI", 10, "bold"),
            bg=ACCENT_PRIMARY,
            fg="#000000",
            relief="flat",
            cursor="hand2",
            padx=15,
            command=self._on_save
        )
        btn_save.pack(side="right", padx=(10, 0))

        btn_cancel = tk.Button(
            btn_frame,
            text="CANCEL",
            font=("Segoe UI", 10),
            bg=BG_PRIMARY,
            fg=TEXT_SECONDARY,
            relief="flat",
            cursor="hand2",
            command=self.destroy
        )
        btn_cancel.pack(side="right")

    def _on_save(self):
        category = self.cmb_category.get()
        difficulty = self.cmb_difficulty.get()
        topic = self.ent_topic.get()
        q_text = self.txt_question.get("1.0", "end-1c").strip()
        opt_a = self.ent_opts["A"].get()
        opt_b = self.ent_opts["B"].get()
        opt_c = self.ent_opts["C"].get()
        opt_d = self.ent_opts["D"].get()
        correct = self.cmb_correct.get()
        explanation = self.ent_explanation.get()

        if self.question_data is not None:
            qid = self.question_data["id"]
            res = self.quiz_service.update_question(
                qid, category, topic, difficulty, q_text, opt_a, opt_b, opt_c, opt_d, correct, explanation
            )
        else:
            res = self.quiz_service.add_question(
                category, topic, difficulty, q_text, opt_a, opt_b, opt_c, opt_d, correct, explanation
            )

        if res["success"]:
            messagebox.showinfo("Success", res["message"], parent=self)
            self.result = res
            self.destroy()
        else:
            messagebox.showerror("Validation Error", res["message"], parent=self)


class AdminPanelScreen(tk.Frame):
    """
    Full Admin Control Panel view component.
    Requires user role == 'admin'.
    """

    def __init__(self, parent: tk.Widget, controller: "App"):
        super().__init__(parent, bg=BG_PRIMARY)
        self.controller = controller

        # Role Access Guard
        user = self.controller.auth_service.current_user
        if not user or not user.is_admin():
            self.controller.after_idle(self.controller.show_welcome)
            return

        self.quiz_service = QuizService(db_mgr=self.controller.auth_service.db_mgr)
        self._create_widgets()

    def _create_widgets(self):
        user = self.controller.auth_service.current_user

        # Header Navbar Frame
        nav = tk.Frame(self, bg=BG_SECONDARY, padx=20, pady=12)
        nav.pack(fill="x", side="top")

        lbl_logo = tk.Label(
            nav,
            text="⚡ QuizMaster AI — Admin Control Panel",
            font=("Segoe UI", 16, "bold"),
            bg=BG_SECONDARY,
            fg=ACCENT_PRIMARY
        )
        lbl_logo.pack(side="left")

        user_info = tk.Label(
            nav,
            text=f"🔑 Admin: {user.name} ({user.username})",
            font=("Segoe UI", 10, "bold"),
            bg=BG_TERTIARY,
            fg=TEXT_PRIMARY,
            padx=10,
            pady=3
        )
        user_info.pack(side="left", padx=15)

        btn_logout = tk.Button(
            nav,
            text="LOG OUT",
            font=("Segoe UI", 9, "bold"),
            bg="#FF4C6A",
            fg="#FFFFFF",
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=4,
            command=self.controller.logout
        )
        btn_logout.pack(side="right")

        # Configure ttk style for dark theme tabs & treeview
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("TNotebook", background=BG_PRIMARY, borderwidth=0)
        style.configure("TNotebook.Tab", background=BG_SECONDARY, foreground=TEXT_PRIMARY, font=("Segoe UI", 10, "bold"), padding=[15, 8])
        style.map("TNotebook.Tab", background=[("selected", ACCENT_PRIMARY)], foreground=[("selected", "#000000")])

        style.configure("Treeview", background=BG_SECONDARY, foreground=TEXT_PRIMARY, fieldbackground=BG_SECONDARY, rowheight=28, font=("Segoe UI", 9))
        style.configure("Treeview.Heading", background=BG_TERTIARY, foreground=ACCENT_PRIMARY, font=("Segoe UI", 9, "bold"))
        style.map("Treeview", background=[("selected", ACCENT_PRIMARY)], foreground=[("selected", "#000000")])

        # Main Notebook Container
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=20, pady=15)

        # Tab 1: Question Bank Management
        self.tab_questions = tk.Frame(self.notebook, bg=BG_PRIMARY)
        self.notebook.add(self.tab_questions, text="  📝 Question Bank Management  ")
        self._build_questions_tab()

        # Tab 2: Student Results
        self.tab_results = tk.Frame(self.notebook, bg=BG_PRIMARY)
        self.notebook.add(self.tab_results, text="  📊 Student Quiz Results  ")
        self._build_results_tab()

        # Tab 3: AI Questions Approval Queue
        self.tab_ai_queue = tk.Frame(self.notebook, bg=BG_PRIMARY)
        self.notebook.add(self.tab_ai_queue, text="  🤖 AI Question Generator & Approval Queue  ")
        self._build_ai_queue_tab()

    # --- TAB 1: QUESTION BANK MANAGEMENT (CRUD, SEARCH, FILTER) ---
    def _build_questions_tab(self):
        bar = tk.Frame(self.tab_questions, bg=BG_SECONDARY, padx=15, pady=12)
        bar.pack(fill="x", pady=(0, 10))

        tk.Label(bar, text="Search:", font=("Segoe UI", 9, "bold"), bg=BG_SECONDARY, fg=TEXT_PRIMARY).pack(side="left", padx=(0, 5))
        self.ent_search = tk.Entry(bar, font=("Segoe UI", 10), bg=BG_TERTIARY, fg=TEXT_PRIMARY, insertbackground=ACCENT_PRIMARY, width=22, relief="flat")
        self.ent_search.pack(side="left", padx=(0, 15), ipady=3)
        self.ent_search.bind("<Return>", lambda e: self.load_questions())

        tk.Label(bar, text="Category:", font=("Segoe UI", 9, "bold"), bg=BG_SECONDARY, fg=TEXT_PRIMARY).pack(side="left", padx=(0, 5))
        categories = ["All Categories"] + SUPPORTED_CATEGORIES
        self.cmb_cat_filter = ttk.Combobox(bar, values=categories, state="readonly", width=18)
        self.cmb_cat_filter.set("All Categories")
        self.cmb_cat_filter.pack(side="left", padx=(0, 15))
        self.cmb_cat_filter.bind("<<ComboboxSelected>>", lambda e: self.load_questions())

        tk.Label(bar, text="Difficulty:", font=("Segoe UI", 9, "bold"), bg=BG_SECONDARY, fg=TEXT_PRIMARY).pack(side="left", padx=(0, 5))
        difficulties = ["All Difficulties"] + SUPPORTED_DIFFICULTIES
        self.cmb_diff_filter = ttk.Combobox(bar, values=difficulties, state="readonly", width=14)
        self.cmb_diff_filter.set("All Difficulties")
        self.cmb_diff_filter.pack(side="left", padx=(0, 15))
        self.cmb_diff_filter.bind("<<ComboboxSelected>>", lambda e: self.load_questions())

        btn_search = tk.Button(bar, text="SEARCH", font=("Segoe UI", 9, "bold"), bg=ACCENT_PRIMARY, fg="#000000", relief="flat", cursor="hand2", command=self.load_questions)
        btn_search.pack(side="left", padx=(0, 8))

        btn_reset = tk.Button(bar, text="RESET", font=("Segoe UI", 9), bg=BG_PRIMARY, fg=TEXT_SECONDARY, relief="flat", cursor="hand2", command=self._reset_filters)
        btn_reset.pack(side="left")

        tree_frame = tk.Frame(self.tab_questions, bg=BG_PRIMARY)
        tree_frame.pack(fill="both", expand=True)

        cols = ("id", "category", "topic", "difficulty", "question_text", "correct_answer")
        self.tree_q = ttk.Treeview(tree_frame, columns=cols, show="headings", selectmode="browse")

        self.tree_q.heading("id", text="ID")
        self.tree_q.heading("category", text="Category")
        self.tree_q.heading("topic", text="Topic")
        self.tree_q.heading("difficulty", text="Difficulty")
        self.tree_q.heading("question_text", text="Question Text")
        self.tree_q.heading("correct_answer", text="Ans Key")

        self.tree_q.column("id", width=50, anchor="center")
        self.tree_q.column("category", width=140, anchor="w")
        self.tree_q.column("topic", width=140, anchor="w")
        self.tree_q.column("difficulty", width=90, anchor="center")
        self.tree_q.column("question_text", width=380, anchor="w")
        self.tree_q.column("correct_answer", width=70, anchor="center")

        sb_y = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree_q.yview)
        self.tree_q.configure(yscrollcommand=sb_y.set)

        self.tree_q.pack(side="left", fill="both", expand=True)
        sb_y.pack(side="right", fill="y")

        act_bar = tk.Frame(self.tab_questions, bg=BG_SECONDARY, padx=15, pady=10)
        act_bar.pack(fill="x", pady=(10, 0))

        btn_add = tk.Button(act_bar, text="➕ ADD QUESTION", font=("Segoe UI", 9, "bold"), bg="#00E676", fg="#000000", relief="flat", cursor="hand2", padx=10, command=self._on_add_question)
        btn_add.pack(side="left", padx=(0, 10))

        btn_edit = tk.Button(act_bar, text="✏️ EDIT QUESTION", font=("Segoe UI", 9, "bold"), bg=ACCENT_PRIMARY, fg="#000000", relief="flat", cursor="hand2", padx=10, command=self._on_edit_question)
        btn_edit.pack(side="left", padx=(0, 10))

        btn_del = tk.Button(act_bar, text="🗑️ DELETE QUESTION", font=("Segoe UI", 9, "bold"), bg="#FF4C6A", fg="#FFFFFF", relief="flat", cursor="hand2", padx=10, command=self._on_delete_question)
        btn_del.pack(side="left")

        self.load_questions()

    def _reset_filters(self):
        self.ent_search.delete(0, "end")
        self.cmb_cat_filter.set("All Categories")
        self.cmb_diff_filter.set("All Difficulties")
        self.load_questions()

    def load_questions(self):
        for item in self.tree_q.get_children():
            self.tree_q.delete(item)

        cat = self.cmb_cat_filter.get()
        diff = self.cmb_diff_filter.get()
        query = self.ent_search.get().strip()

        questions = self.quiz_service.get_filtered_questions(
            category=cat if cat != "All Categories" else None,
            difficulty=diff if diff != "All Difficulties" else None,
            search_query=query
        )

        for q in questions:
            self.tree_q.insert(
                "", "end", iid=str(q.question_id),
                values=(q.question_id, q.category, q.topic, q.difficulty.upper(), q.question_text, q.correct_answer)
            )

    def _on_add_question(self):
        dlg = QuestionFormDialog(self, self.quiz_service)
        self.wait_window(dlg)
        if dlg.result:
            self.load_questions()

    def _on_edit_question(self):
        selected = self.tree_q.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a question to edit.")
            return

        qid = int(selected[0])
        question = self.quiz_service.get_question_by_id(qid)
        if not question:
            messagebox.showerror("Error", f"Question #{qid} not found.")
            return

        dlg = QuestionFormDialog(self, self.quiz_service, question_data=question.to_dict())
        self.wait_window(dlg)
        if dlg.result:
            self.load_questions()

    def _on_delete_question(self):
        selected = self.tree_q.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a question to delete.")
            return

        qid = int(selected[0])
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to permanently delete Question #{qid}?\nThis operation cannot be undone.",
            icon="warning"
        )
        if confirm:
            res = self.quiz_service.delete_question(qid)
            if res["success"]:
                messagebox.showinfo("Deleted", res["message"])
                self.load_questions()
            else:
                messagebox.showerror("Error", res["message"])

    # --- TAB 2: STUDENT QUIZ RESULTS ---
    def _build_results_tab(self):
        header = tk.Frame(self.tab_results, bg=BG_SECONDARY, padx=15, pady=10)
        header.pack(fill="x", pady=(0, 10))

        tk.Label(header, text="📊 Student Quiz Performance Records", font=("Segoe UI", 12, "bold"), bg=BG_SECONDARY, fg=ACCENT_PRIMARY).pack(side="left")
        btn_ref = tk.Button(header, text="REFRESH RESULTS", font=("Segoe UI", 9, "bold"), bg=BG_PRIMARY, fg=ACCENT_PRIMARY, relief="flat", cursor="hand2", command=self.load_student_results)
        btn_ref.pack(side="right")

        tree_frame = tk.Frame(self.tab_results, bg=BG_PRIMARY)
        tree_frame.pack(fill="both", expand=True)

        cols = ("id", "student", "email", "category", "difficulty", "score", "percentage", "time_taken", "quiz_date")
        self.tree_res = ttk.Treeview(tree_frame, columns=cols, show="headings")

        self.tree_res.heading("id", text="ID")
        self.tree_res.heading("student", text="Student Name")
        self.tree_res.heading("email", text="Email")
        self.tree_res.heading("category", text="Category")
        self.tree_res.heading("difficulty", text="Difficulty")
        self.tree_res.heading("score", text="Score")
        self.tree_res.heading("percentage", text="Percentage")
        self.tree_res.heading("time_taken", text="Time (s)")
        self.tree_res.heading("quiz_date", text="Date")

        self.tree_res.column("id", width=45, anchor="center")
        self.tree_res.column("student", width=140, anchor="w")
        self.tree_res.column("email", width=160, anchor="w")
        self.tree_res.column("category", width=120, anchor="w")
        self.tree_res.column("difficulty", width=80, anchor="center")
        self.tree_res.column("score", width=70, anchor="center")
        self.tree_res.column("percentage", width=90, anchor="center")
        self.tree_res.column("time_taken", width=70, anchor="center")
        self.tree_res.column("quiz_date", width=130, anchor="center")

        sb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree_res.yview)
        self.tree_res.configure(yscrollcommand=sb.set)

        self.tree_res.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        self.load_student_results()

    def load_student_results(self):
        for item in self.tree_res.get_children():
            self.tree_res.delete(item)

        results = self.quiz_service.get_student_results()
        for r in results:
            self.tree_res.insert(
                "", "end", iid=str(r["id"]),
                values=(
                    r["id"], r["student_name"], r["email"], r["category"],
                    r["difficulty"].upper() if r["difficulty"] else "",
                    f"{r['correct_answers']}/{r['total_questions']}",
                    f"{r['percentage']:.1f}%", f"{r['time_taken']}s", r["quiz_date"] or ""
                )
            )

    # --- TAB 3: AI-GENERATED QUESTIONS APPROVAL QUEUE ---
    def _build_ai_queue_tab(self):
        # AI Question Generation Input Panel
        gen_box = tk.Frame(self.tab_ai_queue, bg=BG_SECONDARY, padx=15, pady=12)
        gen_box.pack(fill="x", pady=(0, 10))

        tk.Label(gen_box, text="🤖 AI Question Generator:", font=("Segoe UI", 10, "bold"), bg=BG_SECONDARY, fg=ACCENT_PRIMARY).pack(side="left", padx=(0, 10))

        # Category
        tk.Label(gen_box, text="Category:", font=("Segoe UI", 9, "bold"), bg=BG_SECONDARY, fg=TEXT_PRIMARY).pack(side="left", padx=(0, 4))
        self.cmb_ai_cat = ttk.Combobox(gen_box, values=SUPPORTED_CATEGORIES, state="readonly", width=16)
        self.cmb_ai_cat.set(SUPPORTED_CATEGORIES[0])
        self.cmb_ai_cat.pack(side="left", padx=(0, 10))

        # Topic
        tk.Label(gen_box, text="Topic:", font=("Segoe UI", 9, "bold"), bg=BG_SECONDARY, fg=TEXT_PRIMARY).pack(side="left", padx=(0, 4))
        self.ent_ai_topic = tk.Entry(gen_box, font=("Segoe UI", 9), bg=BG_TERTIARY, fg=TEXT_PRIMARY, insertbackground=ACCENT_PRIMARY, width=15, relief="flat")
        self.ent_ai_topic.insert(0, "Basics")
        self.ent_ai_topic.pack(side="left", padx=(0, 10), ipady=2)

        # Difficulty
        tk.Label(gen_box, text="Difficulty:", font=("Segoe UI", 9, "bold"), bg=BG_SECONDARY, fg=TEXT_PRIMARY).pack(side="left", padx=(0, 4))
        self.cmb_ai_diff = ttk.Combobox(gen_box, values=SUPPORTED_DIFFICULTIES, state="readonly", width=10)
        self.cmb_ai_diff.set("medium")
        self.cmb_ai_diff.pack(side="left", padx=(0, 10))

        # Count
        tk.Label(gen_box, text="Count:", font=("Segoe UI", 9, "bold"), bg=BG_SECONDARY, fg=TEXT_PRIMARY).pack(side="left", padx=(0, 4))
        self.cmb_ai_count = ttk.Combobox(gen_box, values=["5", "10", "15", "20"], state="readonly", width=6)
        self.cmb_ai_count.set("5")
        self.cmb_ai_count.pack(side="left", padx=(0, 15))

        # Generate Button
        self.btn_gen_ai = tk.Button(
            gen_box,
            text="⚡ GENERATE QUESTIONS",
            font=("Segoe UI", 9, "bold"),
            bg=ACCENT_PRIMARY,
            fg="#000000",
            relief="flat",
            cursor="hand2",
            padx=10,
            command=self._on_generate_ai_questions
        )
        self.btn_gen_ai.pack(side="left")

        # Treeview Table for Pending AI Questions
        tree_frame = tk.Frame(self.tab_ai_queue, bg=BG_PRIMARY)
        tree_frame.pack(fill="both", expand=True)

        cols = ("id", "category", "topic", "difficulty", "question_text", "correct_answer")
        self.tree_ai = ttk.Treeview(tree_frame, columns=cols, show="headings", selectmode="extended")

        self.tree_ai.heading("id", text="ID")
        self.tree_ai.heading("category", text="Category")
        self.tree_ai.heading("topic", text="Topic")
        self.tree_ai.heading("difficulty", text="Difficulty")
        self.tree_ai.heading("question_text", text="AI Question Text")
        self.tree_ai.heading("correct_answer", text="Ans")

        self.tree_ai.column("id", width=50, anchor="center")
        self.tree_ai.column("category", width=140, anchor="w")
        self.tree_ai.column("topic", width=140, anchor="w")
        self.tree_ai.column("difficulty", width=90, anchor="center")
        self.tree_ai.column("question_text", width=380, anchor="w")
        self.tree_ai.column("correct_answer", width=60, anchor="center")

        sb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree_ai.yview)
        self.tree_ai.configure(yscrollcommand=sb.set)

        self.tree_ai.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        # Action Buttons Toolbar
        act_bar = tk.Frame(self.tab_ai_queue, bg=BG_SECONDARY, padx=15, pady=10)
        act_bar.pack(fill="x", pady=(10, 0))

        btn_prev = tk.Button(act_bar, text="🔍 PREVIEW", font=("Segoe UI", 9, "bold"), bg=BG_PRIMARY, fg=ACCENT_PRIMARY, relief="flat", cursor="hand2", padx=10, command=self._on_preview_ai)
        btn_prev.pack(side="left", padx=(0, 10))

        btn_app = tk.Button(act_bar, text="✅ APPROVE", font=("Segoe UI", 9, "bold"), bg="#00E676", fg="#000000", relief="flat", cursor="hand2", padx=10, command=self._on_approve_ai)
        btn_app.pack(side="left", padx=(0, 10))

        btn_rej = tk.Button(act_bar, text="❌ REJECT", font=("Segoe UI", 9, "bold"), bg="#FF4C6A", fg="#FFFFFF", relief="flat", cursor="hand2", padx=10, command=self._on_reject_ai)
        btn_rej.pack(side="left")

        btn_ref = tk.Button(act_bar, text="REFRESH QUEUE", font=("Segoe UI", 9), bg=BG_PRIMARY, fg=TEXT_SECONDARY, relief="flat", cursor="hand2", command=self.load_ai_queue)
        btn_ref.pack(side="right")

        self.load_ai_queue()

    def _on_generate_ai_questions(self):
        category = self.cmb_ai_cat.get()
        topic = self.ent_ai_topic.get().strip()
        difficulty = self.cmb_ai_diff.get()
        try:
            count = int(self.cmb_ai_count.get())
        except ValueError:
            count = 5

        if not topic:
            messagebox.showwarning("Input Required", "Please enter a topic for AI question generation.")
            return

        self.btn_gen_ai.configure(state="disabled", text="⚡ GENERATING...")
        self.update_idletasks()

        res = self.quiz_service.generate_and_stage_ai_questions(
            topic=topic,
            category=category,
            difficulty=difficulty,
            count=count
        )

        self.btn_gen_ai.configure(state="normal", text="⚡ GENERATE QUESTIONS")

        if res["success"]:
            messagebox.showinfo("AI Generation Complete", res["message"])
            self.load_ai_queue()
        else:
            messagebox.showerror("AI Generation Error", res["message"])

    def load_ai_queue(self):
        for item in self.tree_ai.get_children():
            self.tree_ai.delete(item)

        pending = self.quiz_service.get_pending_ai_questions()
        for p in pending:
            self.tree_ai.insert(
                "", "end", iid=str(p["id"]),
                values=(p["id"], p["category"], p["topic"], p["difficulty"].upper(), p["question_text"], p["correct_answer"])
            )

    def _on_preview_ai(self):
        selected = self.tree_ai.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select an AI question to preview.")
            return

        ai_id = int(selected[0])
        question_data = self.quiz_service.get_ai_question_by_id(ai_id)
        if not question_data:
            messagebox.showerror("Error", f"AI Question #{ai_id} not found.")
            return

        dlg = AIQuestionPreviewDialog(
            parent=self,
            question_data=question_data,
            on_approve=self._approve_by_id,
            on_reject=self._reject_by_id
        )

    def _approve_by_id(self, ai_id: int):
        res = self.quiz_service.approve_ai_question(ai_id)
        if res["success"]:
            messagebox.showinfo("Approved", res["message"])
            self.load_ai_queue()
            self.load_questions()
        else:
            messagebox.showerror("Error", res["message"])

    def _reject_by_id(self, ai_id: int):
        res = self.quiz_service.reject_ai_question(ai_id)
        if res["success"]:
            messagebox.showinfo("Rejected", res["message"])
            self.load_ai_queue()
        else:
            messagebox.showerror("Error", res["message"])

    def _on_approve_ai(self):
        selected = self.tree_ai.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select one or more AI questions to approve.")
            return

        count = 0
        for item in selected:
            res = self.quiz_service.approve_ai_question(int(item))
            if res.get("success"):
                count += 1
                
        messagebox.showinfo("Approved", f"Successfully approved {count} questions.")
        self.load_ai_queue()
        self.load_questions()

    def _on_reject_ai(self):
        selected = self.tree_ai.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select one or more AI questions to reject.")
            return

        confirm = messagebox.askyesno(
            "Confirm Reject",
            f"Are you sure you want to reject and discard {len(selected)} pending AI Question(s)?",
            icon="warning"
        )
        if confirm:
            count = 0
            for item in selected:
                res = self.quiz_service.reject_ai_question(int(item))
                if res.get("success"):
                    count += 1
            messagebox.showinfo("Rejected", f"Successfully rejected {count} questions.")
            self.load_ai_queue()
