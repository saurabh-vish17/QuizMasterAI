"""
main.py
-------
Main entry point for QuizMaster AI.
Initializes the database layer and launches the Tkinter GUI application.
"""

import os
import sys

# Ensure root directory is on Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.schema import initialize_schema, seed_default_admin
from services.authentication import AuthenticationService
from gui.app import App


def main():
    """App startup sequence."""
    print("=" * 50)
    print("  ⚡ QuizMaster AI — Initializing Application")
    print("=" * 50)

    # 1. Initialize SQLite database schema
    db_mgr = initialize_schema()

    # 2. Seed default admin user if not present
    seed_default_admin(db_mgr)

    # 3. Create Authentication Service
    auth_service = AuthenticationService(db_mgr=db_mgr)

    print("Starting Tkinter GUI Application...")

    # 4. Launch GUI Application
    app = App(auth_service=auth_service)
    app.mainloop()


if __name__ == "__main__":
    main()
