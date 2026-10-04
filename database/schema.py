"""
database/schema.py
-------------------
Defines schema initialization and default admin seeding functions
for QuizMaster AI using DatabaseManager.
"""

import hashlib
from database.database import DatabaseManager


def initialize_schema(db_path: str = None) -> DatabaseManager:
    """
    Initializes the database schema using DatabaseManager.
    """
    db_mgr = DatabaseManager(db_path) if db_path else DatabaseManager()
    db_mgr.initialize_database()
    return db_mgr


def seed_default_admin(db_mgr: DatabaseManager = None) -> None:
    """
    Inserts a default admin user if no admin exists yet.
    Default Admin:
        Username: admin
        Email: admin@quizmaster.ai
        Password: admin123 (stored hashed)
        Role: admin
    """
    if db_mgr is None:
        db_mgr = DatabaseManager()

    existing_admin = db_mgr.fetch_one(
        "SELECT id FROM users WHERE role = ? LIMIT 1;", ("admin",)
    )
    if existing_admin:
        return

    from services.authentication import AuthenticationService
    auth_service = AuthenticationService(db_mgr=db_mgr)
    password_hash = auth_service.hash_password("admin123")
    db_mgr.execute_query(
        """
        INSERT INTO users (name, username, email, password_hash, role)
        VALUES (?, ?, ?, ?, ?);
        """,
        ("System Administrator", "admin", "admin@quizmaster.ai", password_hash, "admin")
    )

    print("[DB] Default admin account seeded: username='admin', password='admin123'")
