"""
models/question.py
-------------------
Question domain model for QuizMaster AI.
Independent from database and GUI components.
"""

from typing import Dict, Optional


class Question:
    """
    Represents a quiz question with options, correct answer validation, and metadata.
    """

    def __init__(
        self,
        question_id: Optional[int],
        category: str,
        topic: str,
        difficulty: str,
        question_text: str,
        option_a: str,
        option_b: str,
        option_c: str,
        option_d: str,
        correct_answer: str,
        explanation: str = "",
        created_at: Optional[str] = None
    ):
        self._question_id = question_id
        self._category = category
        self._topic = topic
        self._difficulty = difficulty.lower()
        self._question_text = question_text
        self._option_a = option_a
        self._option_b = option_b
        self._option_c = option_c
        self._option_d = option_d
        self._correct_answer = correct_answer.strip()
        self._explanation = explanation
        self._created_at = created_at

    # --- Encapsulation: Properties ---
    @property
    def question_id(self) -> Optional[int]:
        return self._question_id

    @property
    def category(self) -> str:
        return self._category

    @property
    def topic(self) -> str:
        return self._topic

    @property
    def difficulty(self) -> str:
        return self._difficulty

    @property
    def question_text(self) -> str:
        return self._question_text

    @property
    def option_a(self) -> str:
        return self._option_a

    @property
    def option_b(self) -> str:
        return self._option_b

    @property
    def option_c(self) -> str:
        return self._option_c

    @property
    def option_d(self) -> str:
        return self._option_d

    @property
    def correct_answer(self) -> str:
        return self._correct_answer

    @property
    def explanation(self) -> str:
        return self._explanation

    @property
    def created_at(self) -> Optional[str]:
        return self._created_at

    # --- Methods ---
    def get_options(self) -> Dict[str, str]:
        """
        Returns a dictionary mapping option keys ('A', 'B', 'C', 'D') to option text.
        """
        return {
            "A": self._option_a,
            "B": self._option_b,
            "C": self._option_c,
            "D": self._option_d,
        }

    def check_answer(self, user_answer: str) -> bool:
        """
        Checks if the provided user answer matches the correct answer.
        Supports checking by option letter ('A', 'B', 'C', 'D') or by exact text.
        """
        if not user_answer:
            return False

        clean_user_ans = user_answer.strip().upper()
        clean_correct_ans = self._correct_answer.upper()

        # Direct option key match (e.g. 'A' == 'A')
        if clean_user_ans == clean_correct_ans:
            return True

        # Match option text if correct_answer was stored as key ('A', 'B', 'C', 'D')
        options = self.get_options()
        if clean_correct_ans in options:
            return options[clean_correct_ans].strip().lower() == user_answer.strip().lower()

        # Match if user_answer was option key and correct_answer was full text
        if clean_user_ans in options:
            return options[clean_user_ans].strip().lower() == self._correct_answer.strip().lower()

        return False

    def to_dict(self) -> dict:
        """
        Converts the Question object into a standard dictionary representation.
        """
        return {
            "id": self._question_id,
            "category": self._category,
            "topic": self._topic,
            "difficulty": self._difficulty,
            "question_text": self._question_text,
            "option_a": self._option_a,
            "option_b": self._option_b,
            "option_c": self._option_c,
            "option_d": self._option_d,
            "correct_answer": self._correct_answer,
            "explanation": self._explanation,
        }

    def __repr__(self) -> str:
        return f"Question(id={self._question_id}, topic={self._topic!r}, difficulty={self._difficulty!r})"
