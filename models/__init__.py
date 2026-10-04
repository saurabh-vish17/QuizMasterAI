"""
models package
--------------
OOP Domain Models for QuizMaster AI.

Exposes:
    User, Student, Admin — User models demonstrating inheritance & polymorphism
    Question             — Quiz question model
    Quiz                 — Quiz container model
    Result               — Quiz evaluation result model
"""

from models.user import User, Student, Admin
from models.question import Question
from models.quiz import Quiz
from models.result import Result

__all__ = [
    "User",
    "Student",
    "Admin",
    "Question",
    "Quiz",
    "Result",
]
