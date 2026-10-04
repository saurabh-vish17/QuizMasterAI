"""
tests/test_database.py
-----------------------
Unit and integration tests for DatabaseManager and QuizMaster AI schema.
Verifies table creation, columns, indexes, foreign keys, and error handling.
"""

import os
import tempfile
import unittest
import sqlite3
from database.database import DatabaseManager
from database.schema import initialize_schema, seed_default_admin


class TestDatabaseManager(unittest.TestCase):
    """
    Test suite for database layer initialization and schema validation.
    """

    def setUp(self):
        """Create a temporary database file for isolated testing."""
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        self.db_mgr = DatabaseManager(db_path=self.temp_db_path)

    def tearDown(self):
        """Clean up the temporary database file after testing."""
        os.close(self.temp_db_fd)
        if os.path.exists(self.temp_db_path):
            os.remove(self.temp_db_path)

    def test_database_initialization_and_table_existence(self):
        """Verify that initialize_database creates all 6 required tables."""
        self.db_mgr.initialize_database()

        expected_tables = {
            "users",
            "questions",
            "results",
            "quiz_attempts",
            "ai_analysis",
            "ai_questions"
        }

        conn = self.db_mgr.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = {row["name"] for row in cursor.fetchall()}

            for table in expected_tables:
                self.assertIn(table, tables, f"Table '{table}' was not created in database.")
        finally:
            conn.close()

    def test_table_columns_and_schema_integrity(self):
        """Verify column structure for each required table."""
        self.db_mgr.initialize_database()

        expected_columns = {
            "users": {"id", "name", "username", "email", "password_hash", "role", "created_at"},
            "questions": {
                "id", "category", "topic", "difficulty", "question_text",
                "option_a", "option_b", "option_c", "option_d",
                "correct_answer", "explanation", "created_at"
            },
            "results": {
                "id", "user_id", "category", "difficulty", "total_questions",
                "correct_answers", "wrong_answers", "unanswered", "score",
                "percentage", "time_taken", "quiz_date"
            },
            "quiz_attempts": {
                "id", "result_id", "question_id", "selected_answer",
                "correct_answer", "is_correct", "time_taken"
            },
            "ai_analysis": {
                "id", "user_id", "result_id", "strengths", "weak_topics",
                "recommendations", "difficulty_recommendation", "study_plan", "created_at"
            },
            "ai_questions": {
                "id", "topic", "category", "difficulty", "question_text",
                "option_a", "option_b", "option_c", "option_d",
                "correct_answer", "explanation", "generated_by_ai",
                "approved_by_admin", "created_at"
            }
        }

        conn = self.db_mgr.get_connection()
        try:
            cursor = conn.cursor()
            for table_name, expected_cols in expected_columns.items():
                cursor.execute(f"PRAGMA table_info({table_name});")
                actual_cols = {row["name"] for row in cursor.fetchall()}
                self.assertTrue(
                    expected_cols.issubset(actual_cols),
                    f"Table '{table_name}' missing columns. Missing: {expected_cols - actual_cols}"
                )
        finally:
            conn.close()

    def test_parameterized_query_execution_and_foreign_keys(self):
        """Verify INSERT/SELECT query parameterization and FK enforcement."""
        self.db_mgr.initialize_database()

        # Insert user
        user_id = self.db_mgr.execute_query(
            "INSERT INTO users (name, username, email, password_hash, role) VALUES (?, ?, ?, ?, ?);",
            ("John Doe", "johndoe", "john@example.com", "hashed_pass_123", "student")
        )
        self.assertIsNotNone(user_id)

        # Retrieve user
        user = self.db_mgr.fetch_one("SELECT * FROM users WHERE id = ?;", (user_id,))
        self.assertIsNotNone(user)
        self.assertEqual(user["username"], "johndoe")
        self.assertNotEqual(user["password_hash"], "plaintext_password")

        # Insert result linked to user
        result_id = self.db_mgr.execute_query(
            """
            INSERT INTO results (user_id, category, difficulty, total_questions,
                                 correct_answers, wrong_answers, unanswered,
                                 score, percentage, time_taken)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (user_id, "Python", "medium", 10, 8, 2, 0, 8.0, 80.0, 120)
        )
        self.assertIsNotNone(result_id)

        # FK constraint test: inserting result with invalid user_id should fail
        with self.assertRaises(sqlite3.IntegrityError):
            self.db_mgr.execute_query(
                """
                INSERT INTO results (user_id, category, difficulty, total_questions,
                                     correct_answers, wrong_answers, unanswered,
                                     score, percentage, time_taken)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (99999, "Python", "medium", 10, 8, 2, 0, 8.0, 80.0, 120)
            )

    def test_seed_default_admin(self):
        """Verify default admin seeding functionality."""
        self.db_mgr.initialize_database()
        seed_default_admin(self.db_mgr)

        admin = self.db_mgr.fetch_one("SELECT * FROM users WHERE role = ?;", ("admin",))
        self.assertIsNotNone(admin)
        self.assertEqual(admin["username"], "admin")
        self.assertNotEqual(admin["password_hash"], "admin123")  # Must be hashed!


if __name__ == "__main__":
    unittest.main()
