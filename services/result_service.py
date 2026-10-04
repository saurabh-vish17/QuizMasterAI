"""
services/result_service.py
---------------------------
Business logic for managing quiz results and performance evaluation in QuizMaster AI.

Responsibilities:
    - Retrieving stored quiz results by ID or User ID
    - Fetching itemized attempt breakdowns and question explanations for Answer Review
    - Leaderboard and aggregate performance analytics querying
"""

from typing import List, Optional, Dict, Any
from database.database import DatabaseManager
from models.result import Result


class ResultService:
    """
    Service layer for querying and persisting quiz attempt results.
    """

    def __init__(self, db_mgr: Optional[DatabaseManager] = None):
        self.db_mgr = db_mgr if db_mgr is not None else DatabaseManager()

    def get_result_by_id(self, result_id: int) -> Optional[Result]:
        """Fetches a single quiz result by ID."""
        sql = """
            SELECT id, user_id, category, difficulty, total_questions,
                   correct_answers, wrong_answers, unanswered,
                   score, percentage, time_taken, quiz_date
            FROM results
            WHERE id = ?
        """
        row = self.db_mgr.fetch_one(sql, (result_id,))
        if not row:
            return None

        return Result(
            result_id=row["id"],
            user_id=row["user_id"],
            category=row["category"],
            difficulty=row["difficulty"],
            total_questions=row["total_questions"],
            correct_answers=row["correct_answers"],
            wrong_answers=row["wrong_answers"],
            unanswered=row["unanswered"],
            score=row["score"],
            percentage=row["percentage"],
            time_taken=row["time_taken"],
            quiz_date=row["quiz_date"]
        )

    def get_user_results(self, user_id: int) -> List[Result]:
        """Fetches all past quiz attempt results for a given user."""
        sql = """
            SELECT id, user_id, category, difficulty, total_questions,
                   correct_answers, wrong_answers, unanswered,
                   score, percentage, time_taken, quiz_date
            FROM results
            WHERE user_id = ?
            ORDER BY quiz_date DESC
        """
        rows = self.db_mgr.fetch_all(sql, (user_id,))
        results = []
        for row in rows:
            results.append(
                Result(
                    result_id=row[0],
                    user_id=row[1],
                    category=row[2],
                    difficulty=row[3],
                    total_questions=row[4],
                    correct_answers=row[5],
                    wrong_answers=row[6],
                    unanswered=row[7],
                    score=row[8],
                    percentage=row[9],
                    time_taken=row[10],
                    quiz_date=row[11]
                )
            )
        return results

    def get_result_details(self, result_id: int) -> List[Dict[str, Any]]:
        """
        Retrieves itemized question review breakdown joining quiz_attempts with questions table.
        Returns list of dicts containing question text, options, student answer, correct answer,
        correctness status, and explanation.
        """
        sql = """
            SELECT
                qa.question_id,
                q.question_text,
                q.option_a,
                q.option_b,
                q.option_c,
                q.option_d,
                qa.selected_answer,
                qa.correct_answer,
                qa.is_correct,
                q.explanation,
                q.topic
            FROM quiz_attempts qa
            JOIN questions q ON qa.question_id = q.id
            WHERE qa.result_id = ?
            ORDER BY qa.id ASC
        """
        rows = self.db_mgr.fetch_all(sql, (result_id,))
        details = []

        for r in rows:
            details.append({
                "question_id": r[0],
                "question_text": r[1],
                "option_a": r[2],
                "option_b": r[3],
                "option_c": r[4],
                "option_d": r[5],
                "selected_answer": r[6],
                "correct_answer": r[7],
                "is_correct": bool(r[8]),
                "explanation": r[9] or "No explanation provided for this question.",
                "topic": r[10]
            })

        return details

    def get_leaderboard(
        self,
        category: Optional[str] = None,
        difficulty: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Retrieves top student scores joining results table with users table.
        Filters by category and/or difficulty.
        Ranks by highest percentage score, highest score, then shortest time taken.
        Only returns public student display fields (name, category, difficulty, score, percentage, time_taken).
        """
        conditions = []
        params = []

        if category and category.strip() and category != "All Categories":
            conditions.append("LOWER(r.category) = LOWER(?)")
            params.append(category.strip())

        if difficulty and difficulty.strip() and difficulty != "All Difficulties":
            conditions.append("LOWER(r.difficulty) = LOWER(?)")
            params.append(difficulty.strip())

        sql = """
            SELECT 
                u.name AS student_name,
                r.category,
                r.difficulty,
                r.score,
                r.total_questions,
                r.percentage,
                r.time_taken,
                r.quiz_date
            FROM results r
            JOIN users u ON r.user_id = u.id
        """
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)

        sql += " ORDER BY r.percentage DESC, r.score DESC, r.time_taken ASC, r.quiz_date ASC LIMIT ?"
        params.append(limit)

        rows = self.db_mgr.fetch_all(sql, tuple(params))
        leaderboard = []

        for idx, r in enumerate(rows, start=1):
            t_sec = r[6] if len(r) > 6 else 0
            mins = t_sec // 60
            secs = t_sec % 60
            t_fmt = f"{mins:02d}:{secs:02d}"

            leaderboard.append({
                "rank": idx,
                "student_name": r[0],
                "category": r[1],
                "difficulty": r[2].capitalize(),
                "score": f"{r[3]:.0f} / {r[4]}",
                "raw_score": r[3],
                "percentage": r[5],
                "formatted_percentage": f"{r[5]:.1f}%",
                "time_taken": t_fmt,
                "quiz_date": r[7][:16] if r[7] else ""
            })

        return leaderboard

    def get_student_performance_analytics(self, user_id: int) -> Dict[str, Any]:
        """
        Calculates comprehensive performance metrics for a specific student.
        Returns overall average score, total quizzes, best score, weakest category,
        strongest category, category-wise breakdowns, and progression over time.
        """
        sql_summary = """
            SELECT
                COUNT(*) AS total_quizzes,
                AVG(percentage) AS avg_percentage,
                MAX(percentage) AS max_percentage
            FROM results
            WHERE user_id = ?
        """
        row_sum = self.db_mgr.fetch_one(sql_summary, (user_id,))
        total_quizzes = row_sum["total_quizzes"] if row_sum and row_sum["total_quizzes"] else 0

        if total_quizzes == 0:
            return {
                "has_data": False,
                "total_quizzes": 0,
                "average_score": 0.0,
                "best_score": 0.0,
                "strongest_category": "N/A",
                "weakest_category": "N/A",
                "category_performance": {},
                "score_progression": []
            }

        avg_score = float(row_sum["avg_percentage"]) if row_sum["avg_percentage"] is not None else 0.0
        best_score = float(row_sum["max_percentage"]) if row_sum["max_percentage"] is not None else 0.0

        # Category-wise Performance Query
        sql_cat = """
            SELECT category, AVG(percentage) AS avg_pct, COUNT(*) AS count
            FROM results
            WHERE user_id = ?
            GROUP BY LOWER(category)
            ORDER BY avg_pct DESC
        """
        rows_cat = self.db_mgr.fetch_all(sql_cat, (user_id,))
        cat_perf = {}
        for r in rows_cat:
            cat_name = r[0]
            avg_pct = round(float(r[1]), 1)
            cnt = r[2]
            cat_perf[cat_name] = {"avg_percentage": avg_pct, "count": cnt}

        sorted_cats = sorted(cat_perf.items(), key=lambda x: x[1]["avg_percentage"], reverse=True)
        strongest_cat = sorted_cats[0][0] if sorted_cats else "N/A"
        weakest_cat = sorted_cats[-1][0] if sorted_cats else "N/A"

        # Score Progression Over Time Query
        sql_prog = """
            SELECT id, category, percentage, quiz_date
            FROM results
            WHERE user_id = ?
            ORDER BY id ASC
        """
        rows_prog = self.db_mgr.fetch_all(sql_prog, (user_id,))
        progression = []
        for idx, r in enumerate(rows_prog, start=1):
            date_label = r[3][:10] if r[3] else f"Attempt #{idx}"
            progression.append({
                "attempt_num": idx,
                "result_id": r[0],
                "category": r[1],
                "percentage": float(r[2]),
                "date": date_label
            })

        return {
            "has_data": True,
            "total_quizzes": total_quizzes,
            "average_score": round(avg_score, 1),
            "best_score": round(best_score, 1),
            "strongest_category": strongest_cat,
            "weakest_category": weakest_cat,
            "category_performance": cat_perf,
            "score_progression": progression
        }

    def get_topic_performance_breakdown(self, user_id: int) -> Dict[str, Dict[str, Any]]:
        """
        Calculates deterministic accuracy metrics grouped by question topic for a user.
        """
        sql = """
            SELECT q.topic, COUNT(*) AS asked, SUM(qa.is_correct) AS correct, AVG(qa.is_correct)*100 AS accuracy
            FROM quiz_attempts qa
            JOIN results r ON qa.result_id = r.id
            JOIN questions q ON qa.question_id = q.id
            WHERE r.user_id = ?
            GROUP BY LOWER(q.topic)
            ORDER BY accuracy DESC
        """
        rows = self.db_mgr.fetch_all(sql, (user_id,))
        topics = {}
        for r in rows:
            top_name = r[0]
            asked = r[1]
            correct = r[2]
            acc = round(float(r[3]), 1)
            topics[top_name] = {"asked": asked, "correct": correct, "accuracy": acc}
        return topics

    def save_ai_analysis(self, user_id: int, analysis_data: Dict[str, Any], result_id: Optional[int] = None) -> int:
        """
        Saves generated AI performance analysis into the SQLite 'ai_analysis' table.
        """
        import json
        sql = """
            INSERT INTO ai_analysis (
                user_id, result_id, strengths, weak_topics,
                recommendations, difficulty_recommendation, study_plan
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        strengths_json = json.dumps(analysis_data.get("strengths", []))
        weak_json = json.dumps(analysis_data.get("weak_topics", []))
        recs_json = json.dumps(analysis_data.get("recommendations", []))
        diff_rec = analysis_data.get("difficulty_recommendation", "medium")
        plan_json = json.dumps(analysis_data.get("revision_topics", []))

        params = (user_id, result_id, strengths_json, weak_json, recs_json, diff_rec, plan_json)
        return self.db_mgr.execute_query(sql, params)

    def get_latest_ai_analysis(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Fetches the latest stored AI analysis record for a specific user from SQLite.
        """
        import json
        sql = """
            SELECT id, user_id, result_id, strengths, weak_topics,
                   recommendations, difficulty_recommendation, study_plan, created_at
            FROM ai_analysis
            WHERE user_id = ?
            ORDER BY id DESC LIMIT 1
        """
        row = self.db_mgr.fetch_one(sql, (user_id,))
        if not row:
            return None

        def safe_json_load(val):
            try:
                return json.loads(val) if val else []
            except Exception:
                return [val] if val else []

        return {
            "id": row[0],
            "user_id": row[1],
            "result_id": row[2],
            "strengths": safe_json_load(row[3]),
            "weak_topics": safe_json_load(row[4]),
            "recommendations": safe_json_load(row[5]),
            "difficulty_recommendation": row[6] or "medium",
            "revision_topics": safe_json_load(row[7]),
            "created_at": row[8]
        }

    def generate_and_save_ai_analysis(self, user_id: int, ai_service: Optional[Any] = None) -> Dict[str, Any]:
        """
        Aggregates deterministic quiz statistics, invokes AIService for analysis,
        stores analysis in SQLite ai_analysis table, and returns the analysis object.
        """
        if ai_service is None:
            from services.ai_service import AIService
            ai_service = AIService()

        # 1. Deterministic statistics aggregation
        perf_data = self.get_student_performance_analytics(user_id)
        topic_data = self.get_topic_performance_breakdown(user_id)
        perf_data["topic_performance"] = topic_data

        # 2. Invoke AI Service
        ai_res = ai_service.analyze_performance(perf_data)

        # 3. Save to database
        analysis_id = self.save_ai_analysis(user_id, ai_res)
        ai_res["analysis_id"] = analysis_id
        return ai_res

    def save_study_plan(self, user_id: int, plan_data: Dict[str, Any]) -> int:
        """
        Saves a generated AI Study Plan into the SQLite 'ai_analysis' table.
        Stores full study plan JSON string in the 'study_plan' column.
        """
        import json
        sql = """
            INSERT INTO ai_analysis (
                user_id, result_id, strengths, weak_topics,
                recommendations, difficulty_recommendation, study_plan
            ) VALUES (?, NULL, ?, ?, ?, ?, ?)
        """
        strengths_json = json.dumps(plan_data.get("recommended_topics", []))
        weak_json = json.dumps(plan_data.get("weak_topics", []))
        recs_json = json.dumps(plan_data.get("revision_priorities", []))
        diff_rec = plan_data.get("recommended_difficulty", "Medium")
        full_plan_json = json.dumps(plan_data)

        params = (user_id, strengths_json, weak_json, recs_json, diff_rec, full_plan_json)
        return self.db_mgr.execute_query(sql, params)

    def get_latest_study_plan(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Fetches the latest stored study plan record for a user from SQLite 'ai_analysis'.
        """
        import json
        sql = """
            SELECT id, user_id, strengths, weak_topics,
                   recommendations, difficulty_recommendation, study_plan, created_at
            FROM ai_analysis
            WHERE user_id = ? AND study_plan IS NOT NULL AND study_plan != ''
            ORDER BY id DESC LIMIT 1
        """
        row = self.db_mgr.fetch_one(sql, (user_id,))
        if not row:
            return None

        study_plan_raw = row[6]
        try:
            parsed = json.loads(study_plan_raw)
            if isinstance(parsed, dict) and "study_plan" in parsed:
                parsed["created_at"] = row[7]
                return parsed
        except Exception:
            pass

        return None

    def generate_and_save_study_plan(self, user_id: int, ai_service: Optional[Any] = None) -> Dict[str, Any]:
        """
        Calculates student statistics from SQLite, invokes AIService for a personalized study plan,
        stores the plan in the SQLite 'ai_analysis' table, and returns the plan.
        """
        if ai_service is None:
            from services.ai_service import AIService
            ai_service = AIService()

        # 1. Calculate deterministic statistics
        perf_data = self.get_student_performance_analytics(user_id)
        topic_data = self.get_topic_performance_breakdown(user_id)

        weak_topics = []
        for t_name, data in topic_data.items():
            if data["accuracy"] < 70.0:
                weak_topics.append(t_name)

        if not weak_topics and topic_data:
            sorted_topics = sorted(topic_data.items(), key=lambda x: x[1]["accuracy"])
            weak_topics = [x[0] for x in sorted_topics[:2]]

        # Fetch adaptive difficulty
        from services.quiz_service import QuizService
        qs = QuizService(db_mgr=self.db_mgr)
        adaptive_rec = qs.get_adaptive_difficulty_recommendation(
            user_id=user_id,
            category=perf_data.get("weakest_category", "Python"),
            ai_service=ai_service
        )
        rec_diff = adaptive_rec.get("recommended_level", "Medium")

        stats = {
            "weak_topics": weak_topics,
            "weakest_category": perf_data.get("weakest_category", "Python"),
            "strongest_category": perf_data.get("strongest_category", "Python"),
            "recent_accuracy": perf_data.get("average_score", 50.0),
            "recommended_difficulty": rec_diff,
            "topic_performance": topic_data
        }

        # 2. Invoke AIService to generate personalized study plan
        plan = ai_service.generate_study_plan(stats)

        # 3. Store in SQLite ai_analysis table
        analysis_id = self.save_study_plan(user_id, plan)
        plan["analysis_id"] = analysis_id
        return plan
