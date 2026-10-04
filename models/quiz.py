"""
models/quiz.py
---------------
Quiz domain model for QuizMaster AI.
Independent from database and GUI components.
"""

from typing import List, Optional, Dict, Any
from models.question import Question


class Quiz:
    """
    Represents a quiz consisting of metadata and a collection of Question objects.
    """

    def __init__(
        self,
        title: str,
        category: str,
        topic: str,
        difficulty: str = "medium",
        time_limit: int = 0,
        description: str = "",
        quiz_id: Optional[int] = None,
        questions: Optional[List[Question]] = None
    ):
        self._quiz_id = quiz_id
        self._title = title
        self._category = category
        self._topic = topic
        self._difficulty = difficulty.lower()
        self._time_limit = time_limit  # in seconds (0 = no limit)
        self._description = description
        self._questions: List[Question] = questions if questions is not None else []

    # --- Encapsulation: Properties ---
    @property
    def quiz_id(self) -> Optional[int]:
        return self._quiz_id

    @property
    def title(self) -> str:
        return self._title

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
    def time_limit(self) -> int:
        return self._time_limit

    @property
    def description(self) -> str:
        return self._description

    @property
    def questions(self) -> List[Question]:
        return list(self._questions)

    # --- Methods ---
    def add_question(self, question: Question) -> None:
        """Adds a question to the quiz."""
        if not isinstance(question, Question):
            raise TypeError("Only Question instances can be added to a Quiz.")
        self._questions.append(question)

    def remove_question(self, question_id: int) -> bool:
        """Removes a question by its ID. Returns True if removed."""
        initial_len = len(self._questions)
        self._questions = [q for q in self._questions if q.question_id != question_id]
        return len(self._questions) < initial_len

    def total_questions(self) -> int:
        """Returns total question count in the quiz."""
        return len(self._questions)

    def has_time_limit(self) -> bool:
        """Returns True if the quiz has a positive time limit."""
        return self._time_limit > 0

    def get_difficulty_color(self) -> str:
        """Returns hex color code representing quiz difficulty for UI styling."""
        colors = {
            "easy": "#00E676",    # Green
            "medium": "#FFB300",  # Amber/Yellow
            "hard": "#FF4C6A"     # Red
        }
        return colors.get(self._difficulty, "#00BFFF")

    def evaluate_attempt(self, user_answers: Dict[int, str]) -> Dict[str, Any]:
        """
        Evaluates student's attempt deterministically using database answer keys.
        Returns detailed summary and itemized attempt results.
        """
        total = len(self._questions)
        correct = 0
        wrong = 0
        unanswered = 0
        attempts_detail = []

        for q in self._questions:
            user_ans = user_answers.get(q.question_id, "").strip().upper()
            db_ans = q.correct_answer.strip().upper()

            if not user_ans:
                unanswered += 1
                is_correct = False
            elif user_ans == db_ans or q.check_answer(user_ans):
                correct += 1
                is_correct = True
            else:
                wrong += 1
                is_correct = False

            attempts_detail.append({
                "question_id": q.question_id,
                "selected_answer": user_ans,
                "correct_answer": db_ans,
                "is_correct": 1 if is_correct else 0
            })

        score = float(correct)
        percentage = (correct / total * 100.0) if total > 0 else 0.0

        return {
            "total_questions": total,
            "correct_answers": correct,
            "wrong_answers": wrong,
            "unanswered": unanswered,
            "score": score,
            "percentage": percentage,
            "attempts": attempts_detail
        }

    def to_dict(self) -> dict:
        """Converts the Quiz into a dictionary structure."""
        return {
            "id": self._quiz_id,
            "title": self._title,
            "category": self._category,
            "topic": self._topic,
            "difficulty": self._difficulty,
            "time_limit": self._time_limit,
            "description": self._description,
            "total_questions": self.total_questions(),
        }

    def __repr__(self) -> str:
        return f"Quiz(title={self._title!r}, category={self._category!r}, questions={len(self._questions)})"
