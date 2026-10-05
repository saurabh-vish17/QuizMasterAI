"""
services/ai_service.py
----------------------
AI Integration Service for QuizMaster AI powered by Google Gemini API.

Responsibilities:
    - Secure API configuration reading via python-dotenv
    - AI Question Generation with JSON schema validation
    - Instant Question Explanation & Rationale
    - Performance Analytics & Weakness Identification
    - Adaptive Difficulty Recommendation
    - Personalized AI Study Plan Generation
    - Interactive AI Tutor Chatbot

Security & Resilience Rules:
    - API keys are NEVER hardcoded; loaded strictly from environment variables or explicitly passed args.
    - All AI API calls are executed inside isolated, thread-safe containers with configurable timeouts.
    - Full exception handling ensures API outages or invalid JSON responses NEVER crash the GUI app.
    - Privacy protection: Sensitive fields (passwords, emails, raw user IDs) are stripped before sending prompts.
"""

import json
import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

# Load environment configuration from .env if present
load_dotenv()

logger = logging.getLogger("QuizMasterAI.AIService")


class AIService:
    """
    Isolated service layer for interacting with Google Gemini API with fallback mechanisms.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: Optional[int] = None
    ):
        # 1. Load API Configuration from Environment (Never hardcode secrets!)
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "").strip()
        self.model_name = model_name or os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()

        raw_timeout = os.getenv("AI_REQUEST_TIMEOUT", "15")
        try:
            self.timeout = timeout if timeout is not None else int(raw_timeout)
        except ValueError:
            self.timeout = 15

        self.genai_client = None
        self.is_configured = False
        self._explanation_cache: Dict[str, Dict[str, Any]] = {}

        self._initialize_client()

    def _initialize_client(self):
        """Initializes the Google Generative AI client if a valid API key is present."""
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            logger.info("No valid GEMINI_API_KEY configured. AIService operating in offline/fallback mode.")
            self.is_configured = False
            return

        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.genai_client = genai.GenerativeModel(self.model_name)
            self.is_configured = True
            logger.info(f"AIService configured successfully with model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini API client: {e}")
            self.is_configured = False

    # =========================================================================
    # CORE EXECUTOR & TIMEOUT WRAPPER
    # =========================================================================

    def _call_gemini(self, prompt: str) -> Optional[str]:
        """
        Executes a Gemini prompt inside a ThreadPoolExecutor with timeout protection.
        Returns the raw string output or None on failure/timeout.
        """
        if not self.is_configured or not self.genai_client:
            return None

        def worker():
            try:
                response = self.genai_client.generate_content(prompt, generation_config={"temperature": 0.9})
                return response.text if response else None
            except Exception as ex:
                logger.error(f"Exception inside worker: {ex}")
                return None

        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(worker)
                return future.result(timeout=self.timeout)
        except FutureTimeoutError:
            logger.warning(f"AI API call timed out after {self.timeout} seconds.")
            return None
        except Exception as e:
            logger.error(f"AI API execution error: {e}")
            return None

    def _extract_and_validate_json(self, raw_text: Optional[str]) -> Optional[Any]:
        """
        Cleans markdown wrappers (e.g. ```json ... ```) and parses JSON string safely.
        """
        if not raw_text or not raw_text.strip():
            return None

        cleaned = raw_text.strip()
        # Remove markdown code fence if present
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\n?", "", cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r"\n?```$", "", cleaned)
        cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI JSON response: {e}. Raw text snippet: {cleaned[:100]}")
            return None

    # =========================================================================
    # PUBLIC AI SERVICE METHODS
    # =========================================================================

    def generate_questions(
        self,
        topic: str,
        category: str,
        difficulty: str = "medium",
        count: int = 5
    ) -> Dict[str, Any]:
        """
        Generates multiple-choice quiz questions using AI.
        Returns structured dict with questions list and validation status.
        """
        import random
        random_seed = random.randint(10000, 99999)
        
        prompt = f"""
I need {count} completely different multiple-choice questions about the following topic.
You must return a raw JSON array containing exactly {count} objects.
EACH question MUST cover a completely different sub-topic or angle. Do not repeat questions or concepts. Ensure all {count} questions are unique.

Category: {category}
Topic: {topic}
Difficulty: {difficulty}
Random Seed (to ensure variety): {random_seed}

Provide the output strictly as a JSON array of objects. Use this EXACT schema for EACH object:
[
  {{
      "question_text": "First unique question text here?",
      "option_a": "Option A text",
      "option_b": "Option B text",
      "option_c": "Option C text",
      "option_d": "Option D text",
      "correct_answer": "A",
      "explanation": "Clear explanation of why this answer is correct."
  }},
  {{
      "question_text": "Second unique question covering a DIFFERENT angle?",
      "option_a": "...",
      "option_b": "...",
      "option_c": "...",
      "option_d": "...",
      "correct_answer": "B",
      "explanation": "..."
  }}
]
"""

        try:
            raw_resp = self._call_gemini(prompt)
            parsed = self._extract_and_validate_json(raw_resp)
        except Exception as e:
            logger.error(f"Error in generate_questions: {e}")
            parsed = None

        if isinstance(parsed, list) and len(parsed) > 0:
            validated_questions = []
            for item in parsed:
                if (
                    isinstance(item, dict)
                    and "question_text" in item
                    and "option_a" in item
                    and "option_b" in item
                    and "option_c" in item
                    and "option_d" in item
                    and "correct_answer" in item
                ):
                    item["category"] = category
                    item["topic"] = topic
                    item["difficulty"] = difficulty.lower()
                    if "explanation" not in item:
                        item["explanation"] = f"Correct answer is {item['correct_answer']}."
                    validated_questions.append(item)

            if validated_questions:
                return {
                    "success": True,
                    "message": f"Successfully generated {len(validated_questions)} AI questions.",
                    "questions": validated_questions
                }

        # Fallback if API fails or returns invalid format
        logger.info("Using offline fallback for question generation.")
        fallback_questions = self._get_fallback_questions(topic, category, difficulty, count)
        return {
            "success": False,
            "message": "AI service unavailable. Loaded standard offline questions.",
            "questions": fallback_questions
        }

    def explain_answer_detailed(
        self,
        question_text: str,
        selected_answer: str,
        correct_answer: str,
        options: Dict[str, str],
        existing_explanation: str = ""
    ) -> Dict[str, Any]:
        """
        Provides detailed 3-part AI explanation:
            1. Why correct answer is correct
            2. Why student answer was incorrect (if applicable)
            3. Short learning tip / key takeaway

        Caches explanation responses in memory to reduce repeated API calls.
        """
        clean_q = question_text.strip()
        sel = selected_answer.strip().upper() if selected_answer else "UNANSWERED"
        corr = correct_answer.strip().upper()
        cache_key = f"{clean_q}||{sel}||{corr}"

        # 1. Cache Lookup
        if cache_key in self._explanation_cache:
            logger.info("Returning cached AI explanation.")
            res = dict(self._explanation_cache[cache_key])
            res["cached"] = True
            return res

        opts_str = ", ".join([f"{k}: {v}" for k, v in options.items()])

        prompt = f"""
Analyze this quiz question attempt and return ONLY a valid JSON object:
Question: {clean_q}
Options: {opts_str}
Student Choice: {sel}
Correct Answer Key: {corr}
Database Explanation: {existing_explanation}

SAFETY RULES:
- Do NOT dispute or modify the correct answer key ({corr}).
- Keep explanations concise, clear, and focused.

JSON Format:
{{
    "why_correct": "Concise explanation of why option {corr} is the correct answer.",
    "why_incorrect": "Concise explanation of why option {sel} was wrong (or 'N/A' if student answered correctly).",
    "learning_tip": "Short 1-sentence learning tip or memory rule of thumb."
}}
        """.strip()

        try:
            raw_resp = self._call_gemini(prompt)
            parsed = self._extract_and_validate_json(raw_resp)
        except Exception as e:
            logger.error(f"Error calling Gemini for detailed explanation: {e}")
            parsed = None

        if isinstance(parsed, dict) and ("why_correct" in parsed or "explanation" in parsed):
            why_corr = parsed.get("why_correct") or parsed.get("explanation", "")
            result = {
                "success": True,
                "why_correct": str(why_corr).strip(),
                "why_incorrect": str(parsed.get("why_incorrect", "N/A")).strip(),
                "learning_tip": str(parsed.get("learning_tip", "")).strip(),
                "key_concept": str(parsed.get("key_concept", "Question Rationale")).strip(),
                "cached": False
            }
            # Cache response
            self._explanation_cache[cache_key] = result
            return result

        # Graceful Offline Fallback
        is_corr = (sel == corr)
        fallback_why_corr = f"Option {corr} is the correct answer. {existing_explanation}".strip()
        fallback_why_inc = "Student answer matched the correct answer." if is_corr else (f"Option {sel} was selected instead of {corr}." if sel != "UNANSWERED" else "Question was left unanswered.")

        return {
            "success": False,
            "why_correct": fallback_why_corr,
            "why_incorrect": fallback_why_inc,
            "learning_tip": "Review core concept notes and attempt similar practice questions.",
            "key_concept": "Question Rationale",
            "cached": False
        }

    def explain_answer(
        self,
        question_text: str,
        selected_answer: str,
        correct_answer: str,
        options: Dict[str, str]
    ) -> Dict[str, Any]:
        """Backward-compatible shortcut to explain_answer_detailed."""
        res = self.explain_answer_detailed(question_text, selected_answer, correct_answer, options)
        return {
            "success": res["success"],
            "explanation": f"Why Correct: {res['why_correct']} | Learning Tip: {res['learning_tip']}",
            "key_concept": res.get("key_concept", "Question Rationale"),
            "is_correct": (selected_answer.strip().upper() == correct_answer.strip().upper())
        }

    def analyze_performance(self, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyzes student performance data objectively using summarized statistics.
        Identifies strong topics, weak topics, topics needing revision, recommended difficulty, and recommendations.
        """
        # Strip any sensitive user data before building prompt
        safe_data = {
            "total_quizzes": performance_data.get("total_quizzes", 0),
            "average_score": performance_data.get("average_score", 0.0),
            "best_score": performance_data.get("best_score", 0.0),
            "strongest_category": performance_data.get("strongest_category", "N/A"),
            "weakest_category": performance_data.get("weakest_category", "N/A"),
            "category_performance": performance_data.get("category_performance", {}),
            "topic_performance": performance_data.get("topic_performance", {})
        }

        prompt = f"""
You are an objective educational analytics AI assistant.
Analyze this student's quiz performance statistics based ONLY on observable score metrics.
Performance Data: {json.dumps(safe_data)}

SAFETY & COMPLIANCE RULES:
- Do NOT include any personal identifiers or passwords.
- Do NOT use subjective personality judgments or character assumptions.
- Base all insights strictly on topic accuracy, category scores, and attempt counts.
- Identify specific strong topics, weak topics, topics needing revision, difficulty recommendation, and learning advice.

Return ONLY a valid JSON object matching this schema:
{{
    "summary": "Objective performance summary paragraph based on observable quiz metrics.",
    "strengths": ["Strong Area/Topic 1", "Strong Area/Topic 2"],
    "weak_topics": ["Weak Area/Topic 1", "Weak Area/Topic 2"],
    "revision_topics": ["Topic Needing Revision 1", "Topic Needing Revision 2"],
    "difficulty_recommendation": "easy | medium | hard",
    "recommendations": [
        "Actionable recommendation 1",
        "Actionable recommendation 2"
    ]
}}
        """.strip()

        try:
            raw_resp = self._call_gemini(prompt)
            parsed = self._extract_and_validate_json(raw_resp)
        except Exception as e:
            logger.error(f"Error in analyze_performance: {e}")
            parsed = None

        if isinstance(parsed, dict) and "strengths" in parsed:
            return {
                "success": True,
                "summary": str(parsed.get("summary", "")).strip(),
                "strengths": parsed.get("strengths", []),
                "weak_topics": parsed.get("weak_topics", []),
                "revision_topics": parsed.get("revision_topics", parsed.get("weak_topics", [])),
                "difficulty_recommendation": str(parsed.get("difficulty_recommendation", "medium")).strip().lower(),
                "recommendations": parsed.get("recommendations", [])
            }

        # Deterministic Fallback based on objective calculations
        avg = safe_data["average_score"]
        weak = safe_data["weakest_category"]
        strong = safe_data["strongest_category"]

        rec_diff = "hard" if avg >= 80 else ("medium" if avg >= 50 else "easy")

        return {
            "success": False,
            "summary": f"Overall average score is {avg:.1f}%. Highest accuracy in {strong}.",
            "strengths": [f"{strong} Fundamentals"] if strong != "N/A" else ["General Quiz Basics"],
            "weak_topics": [f"{weak} Concepts"] if weak != "N/A" else ["Review fundamental concepts"],
            "revision_topics": [f"{weak} Practice"] if weak != "N/A" else ["Foundational Topics"],
            "difficulty_recommendation": rec_diff,
            "recommendations": [
                f"Practice {rec_diff}-level questions in {weak} before attempting higher difficulty levels." if weak != "N/A" else "Attempt quizzes across all categories.",
                "Review detailed answer explanations after each quiz."
            ]
        }

    def recommend_difficulty(self, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyzes student quiz history metrics and recommends an adaptive difficulty level.
        Returns current_level, recommended_level, reason, weak_topics, and recommended_practice.
        """
        current_lvl = str(performance_data.get("current_level", "medium")).lower()
        recent_acc = float(performance_data.get("recent_accuracy", 0.0))
        attempts = int(performance_data.get("number_of_attempts", 0))
        weaks = performance_data.get("weak_topics", [])
        topic_acc = performance_data.get("topic_accuracy", {})
        recent_wrongs = int(performance_data.get("recent_wrong_answers", 0))

        safe_data = {
            "current_level": current_lvl,
            "recent_accuracy": round(recent_acc, 1),
            "number_of_attempts": attempts,
            "recent_wrong_answers": recent_wrongs,
            "weak_topics": weaks,
            "topic_accuracy": topic_acc
        }

        prompt = f"""
You are an adaptive educational AI assistant.
Analyze these deterministic student performance statistics and recommend the appropriate quiz difficulty level (easy, medium, or hard).
Student Stats: {json.dumps(safe_data)}

RULES:
- Do NOT judge personality.
- Be objective and transparent. Explain the reason referring to recent accuracy percentage and weak topics.
- Example reason: "Recent accuracy is 68%, with lower performance in OOP."

Return ONLY a valid JSON object matching this schema:
{{
    "current_level": "{current_lvl}",
    "recommended_level": "easy" | "medium" | "hard",
    "reason": "Clear justification citing accuracy and weak topics.",
    "weak_topics": ["Topic 1", "Topic 2"],
    "recommended_practice": "Actionable practice guidance."
}}
        """.strip()

        try:
            raw_resp = self._call_gemini(prompt)
            parsed = self._extract_and_validate_json(raw_resp)
        except Exception as e:
            logger.error(f"Error in recommend_difficulty: {e}")
            parsed = None

        if isinstance(parsed, dict) and ("recommended_level" in parsed or "recommended_difficulty" in parsed):
            rec = str(parsed.get("recommended_level", parsed.get("recommended_difficulty", current_lvl))).lower()
            if rec in ("easy", "medium", "hard"):
                return {
                    "success": True,
                    "current_level": current_lvl.capitalize(),
                    "recommended_level": rec.capitalize(),
                    "recommended_difficulty": rec,
                    "reason": str(parsed.get("reason", "")).strip(),
                    "weak_topics": parsed.get("weak_topics", weaks),
                    "recommended_practice": str(parsed.get("recommended_practice", "")).strip()
                }

        # Deterministic Rule-Based Fallback
        if attempts == 0:
            rec_lvl = current_lvl
            reason_text = "No previous quiz history found. Starting at selected difficulty level."
        elif recent_acc >= 80.0:
            rec_lvl = "hard" if current_lvl == "medium" else ("medium" if current_lvl == "easy" else "hard")
            reason_text = f"Recent accuracy is {recent_acc:.0f}%, demonstrating strong mastery. Upgrading to {rec_lvl.capitalize()}!"
        elif recent_acc <= 50.0:
            rec_lvl = "easy" if current_lvl == "medium" else ("medium" if current_lvl == "hard" else "easy")
            weak_str = f", with lower performance in {weaks[0]}" if weaks else ""
            reason_text = f"Recent accuracy is {recent_acc:.0f}%{weak_str}. Recommending {rec_lvl.capitalize()} for concept reinforcement."
        else:
            rec_lvl = current_lvl
            weak_str = f", with lower performance in {weaks[0]}" if weaks else ""
            reason_text = f"Recent accuracy is {recent_acc:.0f}%{weak_str}. Maintaining {rec_lvl.capitalize()} level."

        pract_text = f"Practice {rec_lvl}-level questions focusing on {', '.join(weaks[:2]) if weaks else 'core topics'}."

        return {
            "success": False,
            "current_level": current_lvl.capitalize(),
            "recommended_level": rec_lvl.capitalize(),
            "recommended_difficulty": rec_lvl,
            "reason": reason_text,
            "weak_topics": weaks if weaks else ["Foundational Topics"],
            "recommended_practice": pract_text
        }

    def recommend_weak_area_focus(self, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recommends target weak topics and difficulty level for a targeted weak area quiz session.
        """
        safe_data = {
            "weak_topics": performance_data.get("weak_topics", []),
            "topic_accuracy": performance_data.get("topic_accuracy", {}),
            "recent_accuracy": performance_data.get("recent_accuracy", 0.0),
            "current_level": performance_data.get("current_level", "medium")
        }

        prompt = f"""
You are an educational AI assistant.
Analyze these student performance statistics and recommend target focus topics and difficulty for a targeted weak area quiz session.
Performance Data: {json.dumps(safe_data)}

Return ONLY a valid JSON object matching:
{{
    "target_topics": ["Topic 1", "Topic 2"],
    "target_difficulty": "easy" | "medium" | "hard",
    "rationale": "Clear rationale for this targeted practice quiz."
}}
        """.strip()

        try:
            raw_resp = self._call_gemini(prompt)
            parsed = self._extract_and_validate_json(raw_resp)
        except Exception as e:
            logger.error(f"Error in recommend_weak_area_focus: {e}")
            parsed = None

        if isinstance(parsed, dict) and "target_topics" in parsed:
            diff = str(parsed.get("target_difficulty", "medium")).lower()
            if diff not in ("easy", "medium", "hard"):
                diff = "medium"
            return {
                "success": True,
                "target_topics": parsed.get("target_topics", safe_data["weak_topics"]),
                "target_difficulty": diff,
                "rationale": str(parsed.get("rationale", "")).strip()
            }

        # Deterministic Fallback
        weaks = safe_data["weak_topics"]
        avg = safe_data["recent_accuracy"]
        target_diff = "hard" if avg >= 80 else ("medium" if avg >= 50 else "easy")

        return {
            "success": False,
            "target_topics": weaks if weaks else ["General Concepts"],
            "target_difficulty": target_diff,
            "rationale": f"Focusing practice on {', '.join(weaks[:2]) if weaks else 'core topics'} at {target_diff.capitalize()} level."
        }

    def generate_study_plan(self, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates a personalized AI study plan based on deterministic student statistics.
        Does NOT invent statistics. Uses provided deterministic metrics.
        """
        weak_topics = performance_data.get("weak_topics", [])
        weak_cat = performance_data.get("weakest_category", "General Concepts")
        rec_diff = performance_data.get("recommended_difficulty", "medium")
        recent_acc = performance_data.get("recent_accuracy", 50.0)
        topic_acc = performance_data.get("topic_performance", {})

        safe_data = {
            "weak_topics": weak_topics,
            "weakest_category": weak_cat,
            "recommended_difficulty": rec_diff,
            "recent_accuracy": round(recent_acc, 1),
            "topic_accuracy": topic_acc
        }

        prompt = f"""
You are an educational AI study advisor.
Analyze these deterministic student performance statistics and generate a structured, personalized 7-day study plan.
DO NOT invent statistics. Use ONLY the provided student stats.

Student Stats: {json.dumps(safe_data)}

Return ONLY a valid JSON object matching this schema:
{{
    "title": "7-Day Personalized Mastery Plan",
    "suggested_practice_duration": "30 mins / day",
    "recommended_difficulty": "{rec_diff}",
    "questions_to_practice": 15,
    "weak_topics": ["Topic 1", "Topic 2"],
    "recommended_topics": ["Topic 3", "Topic 4"],
    "revision_priorities": [
        {{
            "priority": 1,
            "topic": "Topic 1",
            "reason": "Low accuracy in recent attempts.",
            "daily_minutes": 20,
            "target_questions": 5
        }}
    ],
    "study_plan": [
        {{
            "day": 1,
            "topic": "Topic Name",
            "focus": "Core focus objective for Day 1",
            "activities": ["Read topic notes", "Solve 5 practice questions"]
        }}
    ]
}}
        """.strip()

        try:
            raw_resp = self._call_gemini(prompt)
            parsed = self._extract_and_validate_json(raw_resp)
        except Exception as e:
            logger.error(f"Error in generate_study_plan: {e}")
            parsed = None

        if isinstance(parsed, dict) and "study_plan" in parsed and isinstance(parsed["study_plan"], list):
            return {
                "success": True,
                "title": parsed.get("title", f"7-Day {weak_cat} Study Plan"),
                "suggested_practice_duration": parsed.get("suggested_practice_duration", "30 mins / day"),
                "recommended_difficulty": parsed.get("recommended_difficulty", rec_diff).capitalize(),
                "questions_to_practice": parsed.get("questions_to_practice", 15),
                "weak_topics": parsed.get("weak_topics", weak_topics if weak_topics else [weak_cat]),
                "recommended_topics": parsed.get("recommended_topics", [weak_cat]),
                "revision_priorities": parsed.get("revision_priorities", [
                    {"priority": idx + 1, "topic": t, "reason": "Focus area based on accuracy", "daily_minutes": 20, "target_questions": 5}
                    for idx, t in enumerate(weak_topics[:3] if weak_topics else [weak_cat])
                ]),
                "study_plan": parsed["study_plan"]
            }

        # Deterministic Offline Fallback Plan
        fallback_priorities = []
        for idx, t in enumerate((weak_topics[:3] if weak_topics else [weak_cat]), start=1):
            fallback_priorities.append({
                "priority": idx,
                "topic": t,
                "reason": f"Priority concept requiring reinforcement at {rec_diff.capitalize()} level.",
                "daily_minutes": 20,
                "target_questions": 5
            })

        fallback_schedule = []
        for d in range(1, 8):
            t_focus = weak_topics[(d - 1) % len(weak_topics)] if weak_topics else weak_cat
            fallback_schedule.append({
                "day": d,
                "topic": t_focus,
                "focus": f"Review {t_focus} key principles and practice {rec_diff.capitalize()}-level problems.",
                "activities": [
                    f"Read concept summary for {t_focus}",
                    f"Solve 5 {rec_diff.capitalize()}-level practice questions in {t_focus}"
                ]
            })

        return {
            "success": False,
            "title": f"7-Day {weak_cat} Mastery Plan",
            "suggested_practice_duration": "30 mins / day",
            "recommended_difficulty": rec_diff.capitalize(),
            "questions_to_practice": 15,
            "weak_topics": weak_topics if weak_topics else [weak_cat],
            "recommended_topics": [weak_cat],
            "revision_priorities": fallback_priorities,
            "study_plan": fallback_schedule
        }

    def chat_with_student(
        self,
        user_message: str,
        request_type: Optional[str] = "general_chat",
        context_data: Optional[Dict[str, Any]] = None,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        AI Learning Assistant chatbot interface focused strictly on academic learning.
        Supports specific request types: explain_concept, explain_question, give_hint,
        summarize_topic, suggest_topics, explain_correct_answer.
        """
        clean_msg = user_message.strip()
        if not clean_msg:
            return {"success": False, "response": "Please enter a question or message.", "suggested_followups": []}

        # Truncate history to avoid overly long contexts
        safe_history = chat_history[-6:] if chat_history else []

        prompt = f"""
You are QuizMaster AI Assistant, an expert academic tutor for Computer Science and quiz subjects.

CRITICAL ACADEMIC SAFETY RULES:
1. Focus strictly on academic learning, computer science concepts, explanations, hints, and study guidance.
2. Keep responses educational, clear, and concise.
3. Never output executable code scripts or commands that could alter database/system state.
4. Keep answers focused strictly on learning objectives.

Request Type: {request_type}
Context Data: {json.dumps(context_data or {})}
Recent Conversation History: {json.dumps(safe_history)}
Student Question / Message: "{clean_msg}"

Return ONLY a valid JSON object matching:
{{
    "response": "Concise, educational response clearly addressing the student's request...",
    "suggested_followups": ["Followup question 1?", "Followup question 2?"]
}}
        """.strip()

        try:
            raw_resp = self._call_gemini(prompt)
            parsed = self._extract_and_validate_json(raw_resp)
        except Exception as e:
            logger.error(f"Error in chat_with_student: {e}")
            parsed = None

        if isinstance(parsed, dict) and "response" in parsed:
            return {
                "success": True,
                "response": str(parsed["response"]).strip(),
                "suggested_followups": parsed.get("suggested_followups", [])
            }

        # Offline Fallback Response
        fallback_map = {
            "explain_concept": f"Key Concept Overview: '{clean_msg}' is a foundational topic. Review core definitions, syntax rules, and practical examples.",
            "give_hint": f"Hint for '{clean_msg}': Focus on the core mechanism or base condition involved before working through the options.",
            "summarize_topic": f"Summary of '{clean_msg}': Concentrates on key syntax, data structures, algorithm efficiency, and best practices.",
            "suggest_topics": "Recommended Practice Topics: 1. Python Data Structures, 2. Object-Oriented Programming (OOP), 3. Database Normalization.",
            "explain_correct_answer": f"Explanation for '{clean_msg}': The correct answer directly aligns with standard specification rules.",
        }

        resp_text = fallback_map.get(
            request_type,
            f"I'm QuizMaster AI Assistant! Regarding '{clean_msg}': Review key principles and practice related questions in your weak areas."
        )

        return {
            "success": False,
            "response": resp_text,
            "suggested_followups": [
                "Can you give me a practice hint?",
                "Suggest practice topics for revision."
            ]
        }

    # =========================================================================
    # OFFLINE FALLBACK DATA HELPERS
    # =========================================================================

    def _get_fallback_questions(
        self,
        topic: str,
        category: str,
        difficulty: str,
        count: int
    ) -> List[Dict[str, Any]]:
        """Generates standard offline questions when AI API is unavailable."""
        questions = []
        for i in range(1, count + 1):
            questions.append({
                "question_text": f"Offline Practice Q#{i}: What is a core principle of {category} ({topic})?",
                "option_a": f"Primary principle of {category}",
                "option_b": f"Secondary feature of {topic}",
                "option_c": "Alternative implementation detail",
                "option_d": "None of the above",
                "correct_answer": "A",
                "explanation": f"Option A represents the core standard concept for {category} ({topic}).",
                "category": category,
                "topic": topic,
                "difficulty": difficulty.lower()
            })
        return questions
