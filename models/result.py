"""
models/result.py
----------------
Result domain model for QuizMaster AI.
Independent from database and GUI components.
"""

from typing import Optional


class Result:
    """
    Represents a student's completed quiz attempt score and metrics.
    """

    def __init__(
        self,
        user_id: int,
        category: str,
        difficulty: str,
        total_questions: int,
        correct_answers: int,
        wrong_answers: int,
        unanswered: int,
        score: float,
        percentage: float,
        time_taken: int,
        result_id: Optional[int] = None,
        quiz_date: Optional[str] = None
    ):
        self._result_id = result_id
        self._user_id = user_id
        self._category = category
        self._difficulty = difficulty.lower()
        self._total_questions = total_questions
        self._correct_answers = correct_answers
        self._wrong_answers = wrong_answers
        self._unanswered = unanswered
        self._score = score
        self._percentage = percentage
        self._time_taken = time_taken  # seconds
        self._quiz_date = quiz_date

    # --- Encapsulation: Properties ---
    @property
    def result_id(self) -> Optional[int]:
        return self._result_id

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def category(self) -> str:
        return self._category

    @property
    def difficulty(self) -> str:
        return self._difficulty

    @property
    def total_questions(self) -> int:
        return self._total_questions

    @property
    def correct_answers(self) -> int:
        return self._correct_answers

    @property
    def wrong_answers(self) -> int:
        return self._wrong_answers

    @property
    def unanswered(self) -> int:
        return self._unanswered

    @property
    def score(self) -> float:
        return self._score

    @property
    def percentage(self) -> float:
        return self._percentage

    @property
    def time_taken(self) -> int:
        return self._time_taken

    @property
    def quiz_date(self) -> Optional[str]:
        return self._quiz_date

    # --- Methods ---
    def is_passed(self, pass_percentage: float = 60.0) -> bool:
        """
        Determines whether the attempt passed based on pass threshold.
        """
        return self._percentage >= pass_percentage

    def get_grade(self) -> str:
        """
        Calculates letter grade based on percentage score.
        """
        if self._percentage >= 90.0:
            return "A"
        elif self._percentage >= 80.0:
            return "B"
        elif self._percentage >= 70.0:
            return "C"
        elif self._percentage >= 60.0:
            return "D"
        else:
            return "F"

    def formatted_time(self) -> str:
        """
        Returns time taken formatted as MM:SS string.
        """
        minutes = self._time_taken // 60
        seconds = self._time_taken % 60
        return f"{minutes:02d}:{seconds:02d}"

    def to_summary_dict(self) -> dict:
        """
        Returns a dictionary summary of the result metrics.
        """
        return {
            "id": self._result_id,
            "user_id": self._user_id,
            "category": self._category,
            "difficulty": self._difficulty,
            "total_questions": self._total_questions,
            "correct_answers": self._correct_answers,
            "wrong_answers": self._wrong_answers,
            "unanswered": self._unanswered,
            "score": self._score,
            "percentage": self._percentage,
            "grade": self.get_grade(),
            "passed": self.is_passed(),
            "time_taken_formatted": self.formatted_time(),
            "quiz_date": self._quiz_date,
        }

    def __repr__(self) -> str:
        return (
            f"Result(id={self._result_id}, score={self._score}, "
            f"percentage={self._percentage:.1f}%, grade={self.get_grade()!r})"
        )
