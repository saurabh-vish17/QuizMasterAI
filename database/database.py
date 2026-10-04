"""
database/database.py
---------------------
DatabaseManager class providing SQLite database connectivity,
table initialization, parameterized query execution, and exception handling.
"""

import os
import sqlite3
from typing import Any, List, Optional, Union
from utils.constants import DATABASE_PATH


class DatabaseManager:
    """
    Manages SQLite database connections, schema setup, and query execution.
    """

    def __init__(self, db_path: str = DATABASE_PATH):
        """
        Initialize the DatabaseManager with the specified database file path.
        """
        self.db_path = db_path
        self._ensure_data_directory()

    def _ensure_data_directory(self) -> None:
        """
        Creates the target data directory if it does not already exist.
        """
        dir_name = os.path.dirname(self.db_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

    def get_connection(self) -> sqlite3.Connection:
        """
        Returns a configured SQLite connection.
        Enforces foreign keys and row_factory for dictionary-like access.
        """
        try:
            conn = sqlite3.connect(
                self.db_path,
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
            )
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON;")
            return conn
        except sqlite3.Error as e:
            print(f"[DB Error] Connection failed to {self.db_path}: {e}")
            raise

    def initialize_database(self) -> None:
        """
        Initializes the database schema by creating all required tables and indexes.
        """
        self.create_tables()

    def create_tables(self) -> None:
        """
        Creates all required tables and indexes using parameterized DDL.
        """
        statements = [
            # 1. Users Table
            """
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                name          TEXT    NOT NULL,
                username      TEXT    NOT NULL UNIQUE,
                email         TEXT    NOT NULL UNIQUE,
                password_hash TEXT    NOT NULL,
                role          TEXT    NOT NULL CHECK(role IN ('admin', 'student')),
                created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """,
            # 2. Questions Table
            """
            CREATE TABLE IF NOT EXISTS questions (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                category      TEXT    NOT NULL,
                topic         TEXT    NOT NULL,
                difficulty    TEXT    NOT NULL CHECK(difficulty IN ('easy', 'medium', 'hard')),
                question_text TEXT    NOT NULL,
                option_a      TEXT    NOT NULL,
                option_b      TEXT    NOT NULL,
                option_c      TEXT    NOT NULL,
                option_d      TEXT    NOT NULL,
                correct_answer TEXT   NOT NULL,
                explanation   TEXT    DEFAULT '',
                created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """,
            # 3. Results Table
            """
            CREATE TABLE IF NOT EXISTS results (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id         INTEGER NOT NULL,
                category        TEXT    NOT NULL,
                difficulty      TEXT    NOT NULL,
                total_questions INTEGER NOT NULL,
                correct_answers INTEGER NOT NULL,
                wrong_answers   INTEGER NOT NULL,
                unanswered      INTEGER NOT NULL,
                score           REAL    NOT NULL,
                percentage      REAL    NOT NULL,
                time_taken      INTEGER NOT NULL,
                quiz_date       DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """,
            # 4. Quiz Attempts Table
            """
            CREATE TABLE IF NOT EXISTS quiz_attempts (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                result_id       INTEGER NOT NULL,
                question_id     INTEGER NOT NULL,
                selected_answer TEXT    DEFAULT '',
                correct_answer  TEXT    NOT NULL,
                is_correct      INTEGER NOT NULL CHECK(is_correct IN (0, 1)),
                time_taken      INTEGER DEFAULT 0,
                FOREIGN KEY (result_id) REFERENCES results(id) ON DELETE CASCADE,
                FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
            );
            """,
            # 5. AI Analysis Table
            """
            CREATE TABLE IF NOT EXISTS ai_analysis (
                id                        INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id                   INTEGER NOT NULL,
                result_id                 INTEGER,
                strengths                 TEXT    DEFAULT '',
                weak_topics               TEXT    DEFAULT '',
                recommendations           TEXT    DEFAULT '',
                difficulty_recommendation TEXT    DEFAULT '',
                study_plan                TEXT    DEFAULT '',
                created_at                DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (result_id) REFERENCES results(id) ON DELETE CASCADE
            );
            """,
            # 6. AI Questions Table
            """
            CREATE TABLE IF NOT EXISTS ai_questions (
                id                 INTEGER PRIMARY KEY AUTOINCREMENT,
                topic              TEXT    NOT NULL,
                category           TEXT    NOT NULL,
                difficulty         TEXT    NOT NULL CHECK(difficulty IN ('easy', 'medium', 'hard')),
                question_text      TEXT    NOT NULL,
                option_a           TEXT    NOT NULL,
                option_b           TEXT    NOT NULL,
                option_c           TEXT    NOT NULL,
                option_d           TEXT    NOT NULL,
                correct_answer     TEXT    NOT NULL,
                explanation        TEXT    DEFAULT '',
                generated_by_ai    INTEGER NOT NULL DEFAULT 1 CHECK(generated_by_ai IN (0, 1)),
                approved_by_admin  INTEGER NOT NULL DEFAULT 0 CHECK(approved_by_admin IN (0, 1)),
                created_at         DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """,
            # Indexes for performance optimization
            "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);",
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);",
            "CREATE INDEX IF NOT EXISTS idx_questions_category ON questions(category);",
            "CREATE INDEX IF NOT EXISTS idx_questions_topic ON questions(topic);",
            "CREATE INDEX IF NOT EXISTS idx_results_user_id ON results(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_quiz_attempts_result_id ON quiz_attempts(result_id);",
            "CREATE INDEX IF NOT EXISTS idx_quiz_attempts_question_id ON quiz_attempts(question_id);",
            "CREATE INDEX IF NOT EXISTS idx_ai_analysis_user_id ON ai_analysis(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_ai_questions_approved ON ai_questions(approved_by_admin);"
        ]

        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            for stmt in statements:
                cursor.execute(stmt)
            conn.commit()
            print(f"[DB] Database initialized successfully at: {self.db_path}")
        except sqlite3.Error as e:
            conn.rollback()
            print(f"[DB Error] Failed to create database tables: {e}")
            raise
        finally:
            conn.close()

    def execute_query(self, query: str, params: tuple = ()) -> Optional[int]:
        """
        Executes an INSERT, UPDATE, or DELETE query with parameterized inputs.
        Returns the lastrowid for INSERT operations or None.
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            conn.rollback()
            print(f"[DB Error] Execute query failed: {e}")
            raise
        finally:
            conn.close()

    def fetch_all(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """
        Executes a SELECT query and returns all matching rows as sqlite3.Row objects.
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"[DB Error] Fetch all failed: {e}")
            raise
        finally:
            conn.close()

    def fetch_one(self, query: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        """
        Executes a SELECT query and returns the first matching row or None.
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()
        except sqlite3.Error as e:
            print(f"[DB Error] Fetch one failed: {e}")
            raise
        finally:
            conn.close()
