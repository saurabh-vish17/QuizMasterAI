"""
services/quiz_service.py
-------------------------
Business logic and repository service for Question Bank management in QuizMaster AI.

Responsibilities:
    - Question validation (category, difficulty, options, correct answer)
    - CRUD operations on Question Bank (Add, Read, Update, Delete)
    - Filtering and search query execution
    - Student results querying for Admin review
    - Pending AI question approval and rejection workflow
"""

from typing import List, Optional, Tuple, Dict, Any
from database.database import DatabaseManager
from models.question import Question
from models.quiz import Quiz
from models.result import Result
from utils.constants import SUPPORTED_CATEGORIES, SUPPORTED_DIFFICULTIES


class QuizService:
    """
    Question Bank & Quiz Service.
    """

    def __init__(self, db_mgr: Optional[DatabaseManager] = None):
        self.db_mgr = db_mgr if db_mgr is not None else DatabaseManager()

    # --- Validation ---
    @staticmethod
    def validate_question_data(
        category: str,
        topic: str,
        difficulty: str,
        question_text: str,
        option_a: str,
        option_b: str,
        option_c: str,
        option_d: str,
        correct_answer: str
    ) -> Tuple[bool, str]:
        """Validates question attributes. Returns (is_valid, error_message)."""
        if not category or not category.strip():
            return False, "Category cannot be empty."

        if not topic or not topic.strip():
            return False, "Topic cannot be empty."

        clean_diff = difficulty.strip().lower() if difficulty else ""
        if clean_diff not in SUPPORTED_DIFFICULTIES:
            return False, f"Invalid difficulty '{difficulty}'. Must be one of: {', '.join(SUPPORTED_DIFFICULTIES)}."

        if not question_text or len(question_text.strip()) < 5:
            return False, "Question text must be at least 5 characters long."

        if not option_a or not option_a.strip():
            return False, "Option A cannot be empty."

        if not option_b or not option_b.strip():
            return False, "Option B cannot be empty."

        if not option_c or not option_c.strip():
            return False, "Option C cannot be empty."

        if not option_d or not option_d.strip():
            return False, "Option D cannot be empty."

        clean_correct = correct_answer.strip().upper() if correct_answer else ""
        valid_keys = ["A", "B", "C", "D"]
        if clean_correct not in valid_keys:
            opts = [option_a.strip().lower(), option_b.strip().lower(), option_c.strip().lower(), option_d.strip().lower()]
            if correct_answer.strip().lower() not in opts:
                return False, "Correct answer must be one of 'A', 'B', 'C', 'D' or match exact option text."

        return True, "Validation successful."

    # --- CRUD Operations ---
    def add_question(
        self,
        category: str,
        topic: str,
        difficulty: str,
        question_text: str,
        option_a: str,
        option_b: str,
        option_c: str,
        option_d: str,
        correct_answer: str,
        explanation: str = ""
    ) -> Dict[str, Any]:
        """Validates and adds a new question to the Question Bank database."""
        is_valid, err_msg = self.validate_question_data(
            category, topic, difficulty, question_text,
            option_a, option_b, option_c, option_d, correct_answer
        )
        if not is_valid:
            return {"success": False, "message": err_msg, "question_id": None}

        clean_correct = correct_answer.strip().upper()
        if clean_correct not in ["A", "B", "C", "D"]:
            opts = {
                "A": option_a.strip().lower(),
                "B": option_b.strip().lower(),
                "C": option_c.strip().lower(),
                "D": option_d.strip().lower(),
            }
            for key, val in opts.items():
                if val == correct_answer.strip().lower():
                    clean_correct = key
                    break

        sql = """
            INSERT INTO questions (
                category, topic, difficulty, question_text,
                option_a, option_b, option_c, option_d,
                correct_answer, explanation
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            category.strip(),
            topic.strip(),
            difficulty.strip().lower(),
            question_text.strip(),
            option_a.strip(),
            option_b.strip(),
            option_c.strip(),
            option_d.strip(),
            clean_correct,
            explanation.strip()
        )

        try:
            lastrowid = self.db_mgr.execute_query(sql, params)
            new_question = self.get_question_by_id(lastrowid)
            return {
                "success": True,
                "message": "Question added successfully.",
                "question_id": lastrowid,
                "question": new_question
            }
        except Exception as e:
            return {"success": False, "message": f"Database error adding question: {str(e)}", "question_id": None}

    def get_question_by_id(self, question_id: int) -> Optional[Question]:
        """Fetches a single Question by ID."""
        sql = """
            SELECT id, category, topic, difficulty, question_text,
                   option_a, option_b, option_c, option_d,
                   correct_answer, explanation, created_at
            FROM questions
            WHERE id = ?
        """
        rows = self.db_mgr.fetch_all(sql, (question_id,))
        if not rows:
            return None

        r = rows[0]
        return Question(
            question_id=r[0],
            category=r[1],
            topic=r[2],
            difficulty=r[3],
            question_text=r[4],
            option_a=r[5],
            option_b=r[6],
            option_c=r[7],
            option_d=r[8],
            correct_answer=r[9],
            explanation=r[10],
            created_at=r[11]
        )

    def _rows_to_questions(self, rows: List[tuple]) -> List[Question]:
        """Converts database row tuples to Question domain objects."""
        return [
            Question(
                question_id=r[0],
                category=r[1],
                topic=r[2],
                difficulty=r[3],
                question_text=r[4],
                option_a=r[5],
                option_b=r[6],
                option_c=r[7],
                option_d=r[8],
                correct_answer=r[9],
                explanation=r[10],
                created_at=r[11]
            )
            for r in rows
        ]

    def get_questions(self, limit: Optional[int] = None, offset: int = 0) -> List[Question]:
        """Fetches all questions."""
        sql = """
            SELECT id, category, topic, difficulty, question_text,
                   option_a, option_b, option_c, option_d,
                   correct_answer, explanation, created_at
            FROM questions
            ORDER BY id ASC
        """
        params = []
        if limit is not None:
            sql += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])

        rows = self.db_mgr.fetch_all(sql, tuple(params))
        return self._rows_to_questions(rows)

    def get_questions_by_category(self, category: str, limit: Optional[int] = None) -> List[Question]:
        """Fetches questions matching specified category."""
        sql = """
            SELECT id, category, topic, difficulty, question_text,
                   option_a, option_b, option_c, option_d,
                   correct_answer, explanation, created_at
            FROM questions
            WHERE LOWER(category) = LOWER(?)
            ORDER BY id ASC
        """
        params: List[Any] = [category.strip()]
        if limit is not None:
            sql += " LIMIT ?"
            params.append(limit)

        rows = self.db_mgr.fetch_all(sql, tuple(params))
        return self._rows_to_questions(rows)

    def get_questions_by_topic(self, topic: str, limit: Optional[int] = None) -> List[Question]:
        """Fetches questions matching specified topic."""
        sql = """
            SELECT id, category, topic, difficulty, question_text,
                   option_a, option_b, option_c, option_d,
                   correct_answer, explanation, created_at
            FROM questions
            WHERE LOWER(topic) = LOWER(?)
            ORDER BY id ASC
        """
        params: List[Any] = [topic.strip()]
        if limit is not None:
            sql += " LIMIT ?"
            params.append(limit)

        rows = self.db_mgr.fetch_all(sql, tuple(params))
        return self._rows_to_questions(rows)

    def get_questions_by_difficulty(self, difficulty: str, limit: Optional[int] = None) -> List[Question]:
        """Fetches questions matching specified difficulty ('easy', 'medium', 'hard')."""
        sql = """
            SELECT id, category, topic, difficulty, question_text,
                   option_a, option_b, option_c, option_d,
                   correct_answer, explanation, created_at
            FROM questions
            WHERE LOWER(difficulty) = LOWER(?)
            ORDER BY id ASC
        """
        params: List[Any] = [difficulty.strip()]
        if limit is not None:
            sql += " LIMIT ?"
            params.append(limit)

        rows = self.db_mgr.fetch_all(sql, tuple(params))
        return self._rows_to_questions(rows)

    def get_filtered_questions(
        self,
        category: Optional[str] = None,
        topic: Optional[str] = None,
        difficulty: Optional[str] = None,
        search_query: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Question]:
        """Flexible query combining category, difficulty, topic, and search text filters."""
        conditions = []
        params: List[Any] = []

        if category and category.strip() and category != "All Categories":
            conditions.append("LOWER(category) = LOWER(?)")
            params.append(category.strip())

        if topic and topic.strip():
            conditions.append("LOWER(topic) = LOWER(?)")
            params.append(topic.strip())

        if difficulty and difficulty.strip() and difficulty != "All Difficulties":
            conditions.append("LOWER(difficulty) = LOWER(?)")
            params.append(difficulty.strip())

        if search_query and search_query.strip():
            term = f"%{search_query.strip().lower()}%"
            conditions.append("(LOWER(question_text) LIKE ? OR LOWER(topic) LIKE ?)")
            params.extend([term, term])

        sql = """
            SELECT id, category, topic, difficulty, question_text,
                   option_a, option_b, option_c, option_d,
                   correct_answer, explanation, created_at
            FROM questions
        """
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)

        sql += " ORDER BY id ASC"

        if limit is not None:
            sql += " LIMIT ?"
            params.append(limit)

        rows = self.db_mgr.fetch_all(sql, tuple(params))
        return self._rows_to_questions(rows)

    def get_available_topics(self, category: Optional[str] = None) -> List[str]:
        """Fetches distinct topics available in the Question Bank for a category."""
        if category and category.strip() and category != "All Categories":
            sql = "SELECT DISTINCT topic FROM questions WHERE LOWER(category) = LOWER(?) ORDER BY topic ASC"
            rows = self.db_mgr.fetch_all(sql, (category.strip(),))
        else:
            sql = "SELECT DISTINCT topic FROM questions ORDER BY topic ASC"
            rows = self.db_mgr.fetch_all(sql)
        return [r[0] for r in rows if r[0]]

    def count_questions(
        self,
        category: Optional[str] = None,
        topic: Optional[str] = None,
        difficulty: Optional[str] = None
    ) -> int:
        """Counts how many questions exist in database matching selected parameters."""
        conditions = []
        params = []

        if category and category.strip() and category != "All Categories":
            conditions.append("LOWER(category) = LOWER(?)")
            params.append(category.strip())

        if topic and topic.strip() and topic != "All Topics":
            conditions.append("LOWER(topic) = LOWER(?)")
            params.append(topic.strip())

        if difficulty and difficulty.strip() and difficulty != "All Difficulties":
            conditions.append("LOWER(difficulty) = LOWER(?)")
            params.append(difficulty.strip())

        sql = "SELECT COUNT(*) FROM questions"
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)

        rows = self.db_mgr.fetch_all(sql, tuple(params))
        return rows[0][0] if rows else 0

    def get_random_questions(
        self,
        category: Optional[str] = None,
        topic: Optional[str] = None,
        difficulty: Optional[str] = None,
        count: int = 10
    ) -> List[Question]:
        """Randomly selects N questions matching category, topic, and/or difficulty."""
        conditions = []
        params: List[Any] = []

        if category and category != "All Categories":
            conditions.append("LOWER(category) = LOWER(?)")
            params.append(category.strip())

        if topic and topic != "All Topics":
            conditions.append("LOWER(topic) = LOWER(?)")
            params.append(topic.strip())

        if difficulty and difficulty != "All Difficulties":
            conditions.append("LOWER(difficulty) = LOWER(?)")
            params.append(difficulty.strip())

        sql = """
            SELECT id, category, topic, difficulty, question_text,
                   option_a, option_b, option_c, option_d,
                   correct_answer, explanation, created_at
            FROM questions
        """
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)

        sql += " ORDER BY RANDOM() LIMIT ?"
        params.append(max(1, count))

        rows = self.db_mgr.fetch_all(sql, tuple(params))
        return self._rows_to_questions(rows)

    def update_question(
        self,
        question_id: int,
        category: str,
        topic: str,
        difficulty: str,
        question_text: str,
        option_a: str,
        option_b: str,
        option_c: str,
        option_d: str,
        correct_answer: str,
        explanation: str = ""
    ) -> Dict[str, Any]:
        """Updates an existing question by ID."""
        existing = self.get_question_by_id(question_id)
        if not existing:
            return {"success": False, "message": f"Question ID {question_id} not found."}

        is_valid, err_msg = self.validate_question_data(
            category, topic, difficulty, question_text,
            option_a, option_b, option_c, option_d, correct_answer
        )
        if not is_valid:
            return {"success": False, "message": err_msg}

        clean_correct = correct_answer.strip().upper()

        sql = """
            UPDATE questions
            SET category = ?, topic = ?, difficulty = ?, question_text = ?,
                option_a = ?, option_b = ?, option_c = ?, option_d = ?,
                correct_answer = ?, explanation = ?
            WHERE id = ?
        """
        params = (
            category.strip(),
            topic.strip(),
            difficulty.strip().lower(),
            question_text.strip(),
            option_a.strip(),
            option_b.strip(),
            option_c.strip(),
            option_d.strip(),
            clean_correct,
            explanation.strip(),
            question_id
        )

        try:
            self.db_mgr.execute_query(sql, params)
            updated_question = self.get_question_by_id(question_id)
            return {
                "success": True,
                "message": f"Question #{question_id} updated successfully.",
                "question": updated_question
            }
        except Exception as e:
            return {"success": False, "message": f"Database error updating question: {str(e)}"}

    def delete_question(self, question_id: int) -> Dict[str, Any]:
        """Deletes a question from the database by ID."""
        existing = self.get_question_by_id(question_id)
        if not existing:
            return {"success": False, "message": f"Question ID {question_id} not found."}

        sql = "DELETE FROM questions WHERE id = ?"
        try:
            self.db_mgr.execute_query(sql, (question_id,))
            return {"success": True, "message": f"Question #{question_id} deleted successfully."}
        except Exception as e:
            return {"success": False, "message": f"Database error deleting question: {str(e)}"}

    # --- Student Results & AI Questions Review ---
    def get_student_results(self) -> List[Dict[str, Any]]:
        """Fetches all student quiz result records with user names for admin review."""
        sql = """
            SELECT r.id, u.name, u.email, r.category, r.difficulty,
                   r.total_questions, r.correct_answers, r.score, r.percentage,
                   r.time_taken, r.quiz_date
            FROM results r
            LEFT JOIN users u ON r.user_id = u.id
            ORDER BY r.id DESC
        """
        rows = self.db_mgr.fetch_all(sql)
        results = []
        for r in rows:
            results.append({
                "id": r[0],
                "student_name": r[1] or "Unknown Student",
                "email": r[2] or "N/A",
                "category": r[3],
                "difficulty": r[4],
                "total_questions": r[5],
                "correct_answers": r[6],
                "score": r[7],
                "percentage": r[8],
                "time_taken": r[9],
                "quiz_date": r[10],
            })
        return results

    def get_pending_ai_questions(self) -> List[Dict[str, Any]]:
        """Fetches AI-generated questions awaiting admin review and approval."""
        sql = """
            SELECT id, category, topic, difficulty, question_text,
                   option_a, option_b, option_c, option_d, correct_answer, explanation
            FROM ai_questions
            WHERE approved_by_admin = 0
            ORDER BY id ASC
        """
        rows = self.db_mgr.fetch_all(sql)
        pending = []
        for r in rows:
            pending.append({
                "id": r[0],
                "category": r[1],
                "topic": r[2],
                "difficulty": r[3],
                "question_text": r[4],
                "option_a": r[5],
                "option_b": r[6],
                "option_c": r[7],
                "option_d": r[8],
                "correct_answer": r[9],
                "explanation": r[10]
            })
        return pending

    def approve_ai_question(self, ai_question_id: int) -> Dict[str, Any]:
        """Approves a pending AI-generated question, copying it into the main question bank."""
        sql_fetch = "SELECT category, topic, difficulty, question_text, option_a, option_b, option_c, option_d, correct_answer, explanation FROM ai_questions WHERE id = ?"
        rows = self.db_mgr.fetch_all(sql_fetch, (ai_question_id,))
        if not rows:
            return {"success": False, "message": f"Pending AI Question #{ai_question_id} not found."}

        r = rows[0]
        # Add to main question bank
        add_res = self.add_question(
            category=r[0], topic=r[1], difficulty=r[2], question_text=r[3],
            option_a=r[4], option_b=r[5], option_c=r[6], option_d=r[7],
            correct_answer=r[8], explanation=r[9] or ""
        )
        if not add_res["success"]:
            return add_res

        # Mark as approved in ai_questions table
        self.db_mgr.execute_query("UPDATE ai_questions SET approved_by_admin = 1 WHERE id = ?", (ai_question_id,))
        return {"success": True, "message": f"AI Question #{ai_question_id} approved and added to main Question Bank.", "question_id": add_res["question_id"]}


    def get_ai_question_by_id(self, ai_question_id: int) -> Optional[Dict[str, Any]]:
        """Fetches details of a specific pending AI question by ID."""
        sql = """
            SELECT id, category, topic, difficulty, question_text,
                   option_a, option_b, option_c, option_d, correct_answer, explanation, approved_by_admin
            FROM ai_questions
            WHERE id = ?
        """
        rows = self.db_mgr.fetch_all(sql, (ai_question_id,))
        if not rows:
            return None
        r = rows[0]
        return {
            "id": r[0],
            "category": r[1],
            "topic": r[2],
            "difficulty": r[3],
            "question_text": r[4],
            "option_a": r[5],
            "option_b": r[6],
            "option_c": r[7],
            "option_d": r[8],
            "correct_answer": r[9],
            "explanation": r[10] or "",
            "approved_by_admin": bool(r[11])
        }

    def generate_and_stage_ai_questions(
        self,
        topic: str,
        category: str,
        difficulty: str = "medium",
        count: int = 5,
        ai_service: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Calls AIService to generate questions, validates schemas (exactly 4 options, valid correct answer),
        and stages questions into 'ai_questions' with approved_by_admin = 0. Never auto-publishes to main bank.
        """
        if ai_service is None:
            from services.ai_service import AIService
            ai_service = AIService()

        ai_res = ai_service.generate_questions(topic=topic, category=category, difficulty=difficulty, count=count)
        raw_questions = ai_res.get("questions", [])

        staged_ids = []
        rejected_count = 0

        for q in raw_questions:
            # Validate structure: question_text length >= 5, exactly 4 non-empty options, valid correct answer
            q_text = str(q.get("question_text", "")).strip()
            opt_a = str(q.get("option_a", "")).strip()
            opt_b = str(q.get("option_b", "")).strip()
            opt_c = str(q.get("option_c", "")).strip()
            opt_d = str(q.get("option_d", "")).strip()
            corr = str(q.get("correct_answer", "")).strip().upper()
            explanation = str(q.get("explanation", "")).strip()

            if len(q_text) < 5 or not opt_a or not opt_b or not opt_c or not opt_d or corr not in ("A", "B", "C", "D"):
                rejected_count += 1
                continue

            sql = """
                INSERT INTO ai_questions (
                    category, topic, difficulty, question_text,
                    option_a, option_b, option_c, option_d,
                    correct_answer, explanation, generated_by_ai, approved_by_admin
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 0)
            """
            params = (
                category.strip(),
                topic.strip(),
                difficulty.lower(),
                q_text,
                opt_a,
                opt_b,
                opt_c,
                opt_d,
                corr,
                explanation
            )
            try:
                staged_id = self.db_mgr.execute_query(sql, params)
                staged_ids.append(staged_id)
            except Exception:
                rejected_count += 1

        if staged_ids:
            return {
                "success": True,
                "message": f"Successfully generated and staged {len(staged_ids)} AI question(s) for admin approval.",
                "staged_count": len(staged_ids),
                "staged_ids": staged_ids,
                "rejected_count": rejected_count
            }
        else:
            return {
                "success": False,
                "message": "Failed to stage AI questions. All returned questions were malformed or invalid.",
                "staged_count": 0,
                "staged_ids": [],
                "rejected_count": rejected_count
            }

    def reject_ai_question(self, ai_question_id: int) -> Dict[str, Any]:
        """Rejects/Deletes a pending AI-generated question."""
        sql = "DELETE FROM ai_questions WHERE id = ?"
        try:
            self.db_mgr.execute_query(sql, (ai_question_id,))
            return {"success": True, "message": f"Pending AI Question #{ai_question_id} rejected."}
        except Exception as e:
            return {"success": False, "message": f"Error rejecting AI question: {str(e)}"}

    # --- Quiz Execution & Scoring ---
    def submit_quiz_attempt(
        self,
        user_id: int,
        quiz_config: Dict[str, Any],
        questions: List[Question],
        user_answers: Dict[int, str],
        time_taken: int
    ) -> Dict[str, Any]:
        """
        Evaluates quiz attempt deterministically against DB answer keys and persists
        attempt records to 'results' and 'quiz_attempts' tables.
        """
        category = quiz_config.get("category", "General")
        difficulty = quiz_config.get("difficulty", "easy")
        topic = quiz_config.get("topic", "General")

        quiz = Quiz(
            title=f"{category} Quiz",
            category=category,
            topic=topic,
            difficulty=difficulty,
            questions=questions
        )

        eval_res = quiz.evaluate_attempt(user_answers)

        # Insert into results table
        sql_result = """
            INSERT INTO results (
                user_id, category, difficulty, total_questions,
                correct_answers, wrong_answers, unanswered,
                score, percentage, time_taken, quiz_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """
        params_result = (
            user_id,
            category,
            difficulty.lower(),
            eval_res["total_questions"],
            eval_res["correct_answers"],
            eval_res["wrong_answers"],
            eval_res["unanswered"],
            eval_res["score"],
            eval_res["percentage"],
            time_taken
        )

        try:
            result_id = self.db_mgr.execute_query(sql_result, params_result)

            # Insert individual question attempt breakdown into quiz_attempts table
            sql_attempt = """
                INSERT INTO quiz_attempts (
                    result_id, question_id, selected_answer,
                    correct_answer, is_correct, time_taken
                ) VALUES (?, ?, ?, ?, ?, ?)
            """
            for att in eval_res["attempts"]:
                self.db_mgr.execute_query(sql_attempt, (
                    result_id,
                    att["question_id"],
                    att["selected_answer"],
                    att["correct_answer"],
                    att["is_correct"],
                    0  # per-question time estimate placeholder
                ))

            result_obj = Result(
                user_id=user_id,
                category=category,
                difficulty=difficulty,
                total_questions=eval_res["total_questions"],
                correct_answers=eval_res["correct_answers"],
                wrong_answers=eval_res["wrong_answers"],
                unanswered=eval_res["unanswered"],
                score=eval_res["score"],
                percentage=eval_res["percentage"],
                time_taken=time_taken,
                result_id=result_id
            )

            return {
                "success": True,
                "message": "Quiz attempt submitted successfully.",
                "result_id": result_id,
                "result": result_obj,
                "evaluation": eval_res
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Database error persisting quiz result: {str(e)}",
                "result_id": None
            }

    def get_adaptive_difficulty_recommendation(
        self,
        user_id: int,
        category: str,
        topic: Optional[str] = None,
        current_difficulty: str = "medium",
        ai_service: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Calculates deterministic statistics from SQLite quiz history (recent accuracy, topic accuracy,
        recent wrong answers, previous difficulty, number of attempts) and invokes AIService for
        adaptive difficulty recommendation.
        """
        if ai_service is None:
            from services.ai_service import AIService
            ai_service = AIService()

        # 1. Fetch recent results in this category from SQLite
        sql_recent = """
            SELECT difficulty, percentage, wrong_answers, total_questions
            FROM results
            WHERE user_id = ? AND LOWER(category) = LOWER(?)
            ORDER BY id DESC LIMIT 5
        """
        rows = self.db_mgr.fetch_all(sql_recent, (user_id, category))

        if not rows:
            # Fallback to overall user results if category has no attempts
            sql_overall = """
                SELECT difficulty, percentage, wrong_answers, total_questions
                FROM results
                WHERE user_id = ?
                ORDER BY id DESC LIMIT 5
            """
            rows = self.db_mgr.fetch_all(sql_overall, (user_id,))

        number_of_attempts = len(rows)
        if number_of_attempts > 0:
            recent_accuracy = sum(float(r[1]) for r in rows) / number_of_attempts
            recent_wrong_answers = sum(int(r[2]) for r in rows)
            previous_difficulty = str(rows[0][0]).capitalize()
        else:
            recent_accuracy = 0.0
            recent_wrong_answers = 0
            previous_difficulty = current_difficulty.capitalize()

        # 2. Fetch Topic-wise accuracy
        sql_topics = """
            SELECT q.topic, AVG(qa.is_correct)*100 AS accuracy, COUNT(*) AS asked
            FROM quiz_attempts qa
            JOIN results r ON qa.result_id = r.id
            JOIN questions q ON qa.question_id = q.id
            WHERE r.user_id = ? AND LOWER(r.category) = LOWER(?)
            GROUP BY LOWER(q.topic)
            ORDER BY accuracy ASC
        """
        topic_rows = self.db_mgr.fetch_all(sql_topics, (user_id, category))
        topic_accuracy = {}
        weak_topics = []
        for tr in topic_rows:
            top_name = tr[0]
            acc = round(float(tr[1]), 1)
            topic_accuracy[top_name] = acc
            if acc < 65.0:
                weak_topics.append(top_name)

        stats = {
            "current_level": previous_difficulty.lower(),
            "recent_accuracy": round(recent_accuracy, 1),
            "number_of_attempts": number_of_attempts,
            "recent_wrong_answers": recent_wrong_answers,
            "topic_accuracy": topic_accuracy,
            "weak_topics": weak_topics
        }

        # 3. Call AIService to get recommended level and rationale
        rec = ai_service.recommend_difficulty(stats)
        rec["deterministic_metrics"] = stats
        return rec

    def generate_weak_area_quiz(
        self,
        user_id: int,
        count: int = 10,
        ai_service: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Analyzes student quiz history, identifies weak topics using deterministic statistics,
        invokes AIService for target topic recommendation, adjusts difficulty using the adaptive engine,
        and retrieves approved questions prioritizing weak topics.
        """
        if ai_service is None:
            from services.ai_service import AIService
            ai_service = AIService()

        # 1. Fetch deterministic topic accuracy breakdown from SQLite
        sql_topics = """
            SELECT q.topic, q.category, AVG(qa.is_correct)*100 AS accuracy, COUNT(*) AS asked
            FROM quiz_attempts qa
            JOIN results r ON qa.result_id = r.id
            JOIN questions q ON qa.question_id = q.id
            WHERE r.user_id = ?
            GROUP BY LOWER(q.topic)
            ORDER BY accuracy ASC
        """
        topic_rows = self.db_mgr.fetch_all(sql_topics, (user_id,))

        weak_topics = []
        topic_accuracy = {}
        weakest_category = "Python"

        for tr in topic_rows:
            t_name = tr[0]
            cat_name = tr[1]
            acc = round(float(tr[2]), 1)
            topic_accuracy[t_name] = acc
            if acc < 70.0:
                weak_topics.append(t_name)
            weakest_category = cat_name

        if not weak_topics and topic_rows:
            weak_topics = [tr[0] for tr in topic_rows[:2]]

        # Fetch adaptive difficulty recommendation
        adaptive_rec = self.get_adaptive_difficulty_recommendation(
            user_id=user_id,
            category=weakest_category,
            current_difficulty="medium",
            ai_service=ai_service
        )
        recommended_difficulty = adaptive_rec.get("recommended_level", "Medium").lower()

        # 2. Get AI focus recommendation
        ai_focus = ai_service.recommend_weak_area_focus({
            "weak_topics": weak_topics,
            "topic_accuracy": topic_accuracy,
            "recent_accuracy": adaptive_rec.get("deterministic_metrics", {}).get("recent_accuracy", 50.0),
            "current_level": recommended_difficulty
        })

        target_topics = ai_focus.get("target_topics", weak_topics)
        target_difficulty = ai_focus.get("target_difficulty", recommended_difficulty)

        # 3. Retrieve APPROVED questions prioritizing weak topics
        selected_questions: List[Question] = []
        selected_ids = set()

        if target_topics:
            placeholders = ",".join(["?"] * len(target_topics))
            sql_weak_qs = f"""
                SELECT id, category, topic, difficulty, question_text,
                       option_a, option_b, option_c, option_d, correct_answer, explanation
                FROM questions
                WHERE LOWER(topic) IN ({placeholders}) AND LOWER(difficulty) = ?
                ORDER BY RANDOM()
                LIMIT ?
            """
            params = [t.lower() for t in target_topics] + [target_difficulty.lower(), count]
            rows = self.db_mgr.fetch_all(sql_weak_qs, params)

            for r in rows:
                q = Question(r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9], r[10] if len(r) > 10 else "")
                selected_questions.append(q)
                selected_ids.add(q.question_id)

        # Fill remaining slots with general approved questions matching target difficulty
        if len(selected_questions) < count:
            needed = count - len(selected_questions)
            if selected_ids:
                excl_placeholders = ",".join(["?"] * len(selected_ids))
                sql_fill = f"""
                    SELECT id, category, topic, difficulty, question_text,
                           option_a, option_b, option_c, option_d, correct_answer, explanation
                    FROM questions
                    WHERE LOWER(difficulty) = ? AND id NOT IN ({excl_placeholders})
                    ORDER BY RANDOM()
                    LIMIT ?
                """
                params = [target_difficulty.lower()] + list(selected_ids) + [needed]
            else:
                sql_fill = """
                    SELECT id, category, topic, difficulty, question_text,
                           option_a, option_b, option_c, option_d, correct_answer, explanation
                    FROM questions
                    WHERE LOWER(difficulty) = ?
                    ORDER BY RANDOM()
                    LIMIT ?
                """
                params = [target_difficulty.lower(), needed]

            fill_rows = self.db_mgr.fetch_all(sql_fill, params)
            for r in fill_rows:
                q = Question(r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9], r[10] if len(r) > 10 else "")
                selected_questions.append(q)
                selected_ids.add(q.question_id)

        # Fallback if target difficulty questions are empty
        if len(selected_questions) == 0:
            sql_any = """
                SELECT id, category, topic, difficulty, question_text,
                       option_a, option_b, option_c, option_d, correct_answer, explanation
                FROM questions
                ORDER BY RANDOM()
                LIMIT ?
            """
            any_rows = self.db_mgr.fetch_all(sql_any, (count,))
            for r in any_rows:
                q = Question(r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9], r[10] if len(r) > 10 else "")
                selected_questions.append(q)

        quiz_config = {
            "category": "Weak Areas Practice",
            "topic": ", ".join(target_topics[:2]) if target_topics else "Adaptive Practice",
            "difficulty": target_difficulty.lower(),
            "count": len(selected_questions),
            "is_weak_area": True
        }

        return {
            "success": True,
            "quiz_config": quiz_config,
            "questions": selected_questions,
            "weak_topics": target_topics,
            "target_difficulty": target_difficulty,
            "rationale": ai_focus.get("rationale", "")
        }
