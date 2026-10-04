"""
services/authentication.py
---------------------------
Authentication Service for QuizMaster AI.
Manages user registration, secure login verification, session state, and password hashing.
"""

import hashlib
import sqlite3
from typing import Dict, Optional, Tuple, Union
from database.database import DatabaseManager
from models.user import User, Student, Admin
from utils.constants import ADMIN_SECRET_KEY
from utils.validators import (
    validate_email,
    validate_name,
    validate_password,
    validate_username,
)


class AuthenticationService:
    """
    Handles authentication business logic, user creation, password hashing, and active session management.
    """

    def __init__(self, db_mgr: Optional[DatabaseManager] = None):
        self.db_mgr = db_mgr if db_mgr else DatabaseManager()
        self._current_user: Optional[User] = None

    @property
    def current_user(self) -> Optional[User]:
        """Returns the currently logged in user session object."""
        return self._current_user

    def hash_password(self, password: str, salt: str = "QuizMasterAI_Salt_2026") -> str:
        """
        Hashes a plaintext password using SHA-256 algorithm with salt.
        Returns hex digest string.
        """
        return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


    def register_user(
        self,
        name: str,
        username: str,
        email: str,
        password: str,
        role: str = "student",
        admin_key: Optional[str] = None
    ) -> Dict[str, Union[bool, str, Optional[User]]]:
        """
        Registers a new student or admin user.
        Performs input validation, admin key verification, username & email uniqueness check,
        password hashing, and database insertion.
        """
        # 1. Validate Full Name
        valid_name, err = validate_name(name)
        if not valid_name:
            return {"success": False, "message": err, "user": None}

        # 2. Validate Username
        valid_uname, err = validate_username(username)
        if not valid_uname:
            return {"success": False, "message": err, "user": None}

        # 3. Validate Email
        valid_email, err = validate_email(email)
        if not valid_email:
            return {"success": False, "message": err, "user": None}

        # 4. Validate Password
        valid_pass, err = validate_password(password)
        if not valid_pass:
            return {"success": False, "message": err, "user": None}

        # 5. Normalize inputs
        clean_name = name.strip()
        clean_username = username.strip().lower()
        clean_email = email.strip().lower()
        clean_role = role.lower()

        if clean_role not in ("student", "admin"):
            return {"success": False, "message": "Invalid user role specified.", "user": None}

        # Verify Admin Secret Key for Administrator registration
        if clean_role == "admin":
            if not admin_key or admin_key.strip() != ADMIN_SECRET_KEY:
                return {
                    "success": False,
                    "message": "Invalid Admin Access Key. Registration as Administrator requires a valid authorization key.",
                    "user": None
                }

        try:
            # 6. Check Username Uniqueness
            existing_user = self.db_mgr.fetch_one(
                "SELECT id FROM users WHERE LOWER(username) = ?;", (clean_username,)
            )
            if existing_user:
                return {
                    "success": False,
                    "message": "Username is already taken. Please choose another.",
                    "user": None
                }

            # 7. Check Email Uniqueness
            existing_email = self.db_mgr.fetch_one(
                "SELECT id FROM users WHERE LOWER(email) = ?;", (clean_email,)
            )
            if existing_email:
                return {
                    "success": False,
                    "message": "Email address is already registered.",
                    "user": None
                }

            # 8. Hash Password securely
            password_hash = self.hash_password(password)

            # 9. Insert User into Database using Parameterized Query
            user_id = self.db_mgr.execute_query(
                """
                INSERT INTO users (name, username, email, password_hash, role)
                VALUES (?, ?, ?, ?, ?);
                """,
                (clean_name, clean_username, clean_email, password_hash, clean_role)
            )

            # 10. Instantiate OOP Model Object
            if clean_role == "admin":
                user_obj = Admin(user_id, clean_name, clean_username, clean_email, password_hash)
            else:
                user_obj = Student(user_id, clean_name, clean_username, clean_email, password_hash)

            return {
                "success": True,
                "message": "Registration successful! You can now log in.",
                "user": user_obj
            }

        except sqlite3.Error as e:
            return {
                "success": False,
                "message": f"Database error during registration: {e}",
                "user": None
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"An unexpected error occurred: {e}",
                "user": None
            }

    def login_user(
        self,
        username_or_email: str,
        password: str
    ) -> Dict[str, Union[bool, str, Optional[User]]]:
        """
        Authenticates a user by username or email and password.
        Establishes active user session on success.
        """
        if not username_or_email or not username_or_email.strip():
            return {"success": False, "message": "Please enter your username or email.", "user": None}

        if not password:
            return {"success": False, "message": "Please enter your password.", "user": None}

        query_identifier = username_or_email.strip().lower()

        try:
            # Parameterized search by username OR email
            user_row = self.db_mgr.fetch_one(
                """
                SELECT id, name, username, email, password_hash, role, created_at
                FROM users
                WHERE LOWER(username) = ? OR LOWER(email) = ?;
                """,
                (query_identifier, query_identifier)
            )

            if not user_row:
                return {
                    "success": False,
                    "message": "Invalid username/email or password.",
                    "user": None
                }

            # Verify password hash
            input_hash = self.hash_password(password)
            if input_hash != user_row["password_hash"]:
                return {
                    "success": False,
                    "message": "Invalid username/email or password.",
                    "user": None
                }

            # Create domain object based on role
            role = user_row["role"].lower()
            if role == "admin":
                user_obj = Admin(
                    user_id=user_row["id"],
                    name=user_row["name"],
                    username=user_row["username"],
                    email=user_row["email"],
                    password_hash=user_row["password_hash"],
                    created_at=user_row["created_at"]
                )
            else:
                user_obj = Student(
                    user_id=user_row["id"],
                    name=user_row["name"],
                    username=user_row["username"],
                    email=user_row["email"],
                    password_hash=user_row["password_hash"],
                    created_at=user_row["created_at"]
                )

            # Establish session
            self._current_user = user_obj

            return {
                "success": True,
                "message": f"Welcome back, {user_obj.name}!",
                "user": user_obj
            }

        except sqlite3.Error as e:
            return {
                "success": False,
                "message": f"Database error during login: {e}",
                "user": None
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"An unexpected error occurred: {e}",
                "user": None
            }

    def logout(self) -> bool:
        """
        Clears current user session.
        Returns True if session was active, False otherwise.
        """
        if self._current_user is not None:
            self._current_user = None
            return True
        return False
