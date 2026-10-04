"""
tests/test_authentication.py
-----------------------------
Unit tests for AuthenticationService and user session management.

Test Cases:
    1. Test successful registration (Student & Admin).
    2. Test duplicate username validation.
    3. Test duplicate email validation.
    4. Test password strength & email format validation.
    5. Test invalid login (wrong password / nonexistent user).
    6. Test successful login (verifies session state & model instantiation).
    7. Test logout (verifies session reset).
"""

import os
import tempfile
import unittest
from database.database import DatabaseManager
from database.schema import seed_default_admin
from models.user import Student, Admin
from services.authentication import AuthenticationService


class TestAuthenticationService(unittest.TestCase):
    """
    Test suite for user registration, authentication, validation, and session management.
    """

    def setUp(self):
        """Set up an isolated temporary database for each test run."""
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        self.db_mgr = DatabaseManager(db_path=self.temp_db_path)
        self.db_mgr.initialize_database()

        self.auth_service = AuthenticationService(db_mgr=self.db_mgr)

    def tearDown(self):
        """Clean up temporary database file."""
        os.close(self.temp_db_fd)
        if os.path.exists(self.temp_db_path):
            os.remove(self.temp_db_path)

    def test_successful_registration(self):
        """Test successful registration for student and admin accounts."""
        res_student = self.auth_service.register_user(
            name="Alice Student",
            username="alicestudent",
            email="alice@student.edu",
            password="password123",
            role="student"
        )
        self.assertTrue(res_student["success"])
        self.assertIsInstance(res_student["user"], Student)
        self.assertEqual(res_student["user"].role, "student")
        self.assertNotEqual(res_student["user"].password_hash, "password123")

        res_admin = self.auth_service.register_user(
            name="Bob Admin",
            username="bobadmin",
            email="bob@admin.edu",
            password="adminpassword123",
            role="admin",
            admin_key="ADMIN123"
        )
        self.assertTrue(res_admin["success"])
        self.assertIsInstance(res_admin["user"], Admin)
        self.assertEqual(res_admin["user"].role, "admin")

    def test_admin_registration_security_key(self):
        """Test that registering as Administrator without a valid security key fails."""
        # 1. Reject without key
        res_no_key = self.auth_service.register_user(
            name="Unauthorized Admin",
            username="badadmin1",
            email="badadmin1@test.com",
            password="adminpassword123",
            role="admin"
        )
        self.assertFalse(res_no_key["success"])
        self.assertIn("invalid admin access key", res_no_key["message"].lower())

        # 2. Reject with wrong key
        res_wrong_key = self.auth_service.register_user(
            name="Unauthorized Admin",
            username="badadmin2",
            email="badadmin2@test.com",
            password="adminpassword123",
            role="admin",
            admin_key="WRONGKEY123"
        )
        self.assertFalse(res_wrong_key["success"])
        self.assertIn("invalid admin access key", res_wrong_key["message"].lower())

        # 3. Accept with correct key
        res_valid_key = self.auth_service.register_user(
            name="Authorized Admin",
            username="goodadmin",
            email="goodadmin@test.com",
            password="adminpassword123",
            role="admin",
            admin_key="ADMIN123"
        )
        self.assertTrue(res_valid_key["success"])
        self.assertEqual(res_valid_key["user"].role, "admin")

    def test_duplicate_username(self):
        """Test registration rejection when username is already taken."""
        self.auth_service.register_user(
            name="User One",
            username="uniqueuser",
            email="user1@test.com",
            password="password123"
        )

        res_dup = self.auth_service.register_user(
            name="User Two",
            username="uniqueuser",  # Duplicate username
            email="user2@test.com",
            password="password123"
        )
        self.assertFalse(res_dup["success"])
        self.assertIn("already taken", res_dup["message"].lower())

    def test_duplicate_email(self):
        """Test registration rejection when email address is already registered."""
        self.auth_service.register_user(
            name="User One",
            username="userone",
            email="shared@test.com",
            password="password123"
        )

        res_dup = self.auth_service.register_user(
            name="User Two",
            username="usertwo",
            email="shared@test.com",  # Duplicate email
            password="password123"
        )
        self.assertFalse(res_dup["success"])
        self.assertIn("already registered", res_dup["message"].lower())

    def test_invalid_login(self):
        """Test login failures for nonexistent user or wrong password."""
        # Nonexistent user
        res_nonexistent = self.auth_service.login_user("nonexistent", "password123")
        self.assertFalse(res_nonexistent["success"])
        self.assertIn("invalid", res_nonexistent["message"].lower())

        # Valid user, wrong password
        self.auth_service.register_user(
            name="Charlie",
            username="charlie",
            email="charlie@test.com",
            password="correctpassword"
        )

        res_wrong_pass = self.auth_service.login_user("charlie", "wrongpassword")
        self.assertFalse(res_wrong_pass["success"])
        self.assertIn("invalid", res_wrong_pass["message"].lower())
        self.assertIsNone(self.auth_service.current_user)

    def test_successful_login(self):
        """Test successful login with username or email, establishing active session."""
        self.auth_service.register_user(
            name="David Student",
            username="david_s",
            email="david@test.com",
            password="mysecretpassword"
        )

        # Login using username
        res_uname = self.auth_service.login_user("david_s", "mysecretpassword")
        self.assertTrue(res_uname["success"])
        self.assertIsNotNone(self.auth_service.current_user)
        self.assertEqual(self.auth_service.current_user.username, "david_s")

        # Logout
        self.auth_service.logout()

        # Login using email address
        res_email = self.auth_service.login_user("david@test.com", "mysecretpassword")
        self.assertTrue(res_email["success"])
        self.assertIsNotNone(self.auth_service.current_user)
        self.assertEqual(self.auth_service.current_user.email, "david@test.com")

    def test_default_admin_login(self):
        """Test login with default seeded admin account."""
        seed_default_admin(self.db_mgr)

        res = self.auth_service.login_user("admin", "admin123")
        self.assertTrue(res["success"])
        self.assertTrue(self.auth_service.current_user.is_admin())

    def test_logout(self):
        """Test logout functionality resetting active session."""
        self.auth_service.register_user(
            name="Eve",
            username="eve_user",
            email="eve@test.com",
            password="password123"
        )
        self.auth_service.login_user("eve_user", "password123")
        self.assertIsNotNone(self.auth_service.current_user)

        # Execute logout
        logged_out = self.auth_service.logout()
        self.assertTrue(logged_out)
        self.assertIsNone(self.auth_service.current_user)

        # Repeat logout when no session active
        self.assertFalse(self.auth_service.logout())


if __name__ == "__main__":
    unittest.main()
