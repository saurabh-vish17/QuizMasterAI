"""
models/user.py
---------------
User domain model demonstrating OOP Encapsulation, Inheritance, and Polymorphism.

Classes:
    User    — Base user model
    Student — Student user subclass inheriting from User
    Admin   — Admin user subclass inheriting from User
"""

import hashlib
from typing import List, Optional


class User:
    """
    Base User domain model. Demonstrates encapsulation using protected attributes and properties.
    """

    def __init__(
        self,
        user_id: Optional[int],
        name: str,
        username: str,
        email: str,
        password_hash: str,
        role: str = "student",
        created_at: Optional[str] = None
    ):
        self._user_id = user_id
        self._name = name
        self._username = username
        self._email = email
        self._password_hash = password_hash
        self._role = role
        self._created_at = created_at

    # --- Encapsulation: Read-only & Controlled Properties ---
    @property
    def user_id(self) -> Optional[int]:
        return self._user_id

    @property
    def id(self) -> Optional[int]:
        return self._user_id

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, val: str) -> None:
        if not val.strip():
            raise ValueError("Name cannot be empty.")
        self._name = val.strip()

    @property
    def username(self) -> str:
        return self._username

    @property
    def email(self) -> str:
        return self._email

    @property
    def password_hash(self) -> str:
        return self._password_hash

    @property
    def role(self) -> str:
        return self._role

    @property
    def created_at(self) -> Optional[str]:
        return self._created_at

    # --- Methods ---
    def check_password(self, plain_password: str) -> bool:
        """
        Verifies a plaintext password against the stored SHA-256 password hash.
        """
        if not plain_password:
            return False
        input_hash = hashlib.sha256(plain_password.encode("utf-8")).hexdigest()
        return input_hash == self._password_hash

    def is_admin(self) -> bool:
        return self._role == "admin"

    def is_student(self) -> bool:
        return self._role == "student"

    # --- Polymorphic Methods ---
    def get_role_display(self) -> str:
        """Polymorphic method returning a user-friendly role label."""
        return self._role.capitalize()

    def get_permissions(self) -> List[str]:
        """Polymorphic method returning access control permissions list."""
        return ["view_quizzes", "take_quizzes"]

    def get_dashboard_welcome(self) -> str:
        """Polymorphic method returning dashboard greeting text."""
        return f"Welcome back, {self._name}!"

    def __repr__(self) -> str:
        return f"User(id={self._user_id}, username={self._username!r}, role={self._role!r})"


class Student(User):
    """
    Student model inheriting from User base class.
    """

    def __init__(
        self,
        user_id: Optional[int],
        name: str,
        username: str,
        email: str,
        password_hash: str,
        created_at: Optional[str] = None
    ):
        super().__init__(
            user_id=user_id,
            name=name,
            username=username,
            email=email,
            password_hash=password_hash,
            role="student",
            created_at=created_at
        )

    # --- Polymorphic Overrides ---
    def get_role_display(self) -> str:
        return "Student"

    def get_permissions(self) -> List[str]:
        return ["view_quizzes", "take_quizzes", "view_results", "view_study_plan"]

    def get_dashboard_welcome(self) -> str:
        return f"Welcome to your Learning Dashboard, {self._name}! 🎯"


class Admin(User):
    """
    Admin model inheriting from User base class.
    """

    def __init__(
        self,
        user_id: Optional[int],
        name: str,
        username: str,
        email: str,
        password_hash: str,
        created_at: Optional[str] = None
    ):
        super().__init__(
            user_id=user_id,
            name=name,
            username=username,
            email=email,
            password_hash=password_hash,
            role="admin",
            created_at=created_at
        )

    # --- Polymorphic Overrides ---
    def get_role_display(self) -> str:
        return "Administrator"

    def get_permissions(self) -> List[str]:
        return [
            "view_quizzes", "create_quizzes", "edit_quizzes", "delete_quizzes",
            "manage_questions", "approve_ai_questions", "view_analytics"
        ]

    def get_dashboard_welcome(self) -> str:
        return f"Welcome to the Admin Control Panel, {self._name}! ⚙️"
