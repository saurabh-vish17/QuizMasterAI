"""
utils/constants.py
------------------
Global configuration settings, themes, typography, colors, and paths for QuizMaster AI.
"""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_PATH = os.path.join(BASE_DIR, "data", "quiz.db")

# Security & Authorization Tokens
ADMIN_SECRET_KEY = os.getenv("ADMIN_SECRET_KEY", "ADMIN123")


# Dark Theme + Modern Desktop Colors
BG_PRIMARY = "#0D0F14"
BG_SECONDARY = "#13161E"
BG_TERTIARY = "#1A1E2A"
BG_CARD = "#161B26"

ACCENT_PRIMARY = "#00BFFF"       # Electric Blue (Primary Action)
ACCENT_GLOW = "#00D4FF"
TEXT_PRIMARY = "#E8EAF0"
TEXT_SECONDARY = "#8A94A8"

COLOR_SUCCESS = "#00E676"        # Emerald Green
COLOR_DANGER = "#FF4C6A"         # Crimson Red
COLOR_WARNING = "#FFB300"        # Amber Yellow
COLOR_SECONDARY_BTN = "#232838"    # Dark Slate (Secondary Buttons)
COLOR_BORDER = "#2A3042"

# Typography Tokens
FONT_HEADER = ("Segoe UI", 18, "bold")
FONT_TITLE = ("Segoe UI", 14, "bold")
FONT_SUBTITLE = ("Segoe UI", 11, "bold")
FONT_BODY = ("Segoe UI", 10)
FONT_BODY_BOLD = ("Segoe UI", 10, "bold")
FONT_CAPTION = ("Segoe UI", 9)
FONT_TIMER = ("Segoe UI", 14, "bold")
FONT_QUESTION = ("Segoe UI", 12, "bold")

# Supported Question Categories & Difficulties
SUPPORTED_CATEGORIES = [
    "Python",
    "C++",
    "Java",
    "DBMS",
    "Computer Networks",
    "General Knowledge"
]

SUPPORTED_DIFFICULTIES = [
    "easy",
    "medium",
    "hard"
]
