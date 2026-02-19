# ai_engine.py  –  HuggingFace-powered AI features with graceful fallback

from __future__ import annotations
from typing import Optional, Any

try:
    from huggingface_hub import InferenceClient
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False

from config import DEFAULT_HF_MODEL


class AIEngine:
    """Wraps Hugging Face Inference API.  Every public method works
    *without* an API key by falling back to deterministic heuristics
    so the app never breaks during a demo."""

    def __init__(self, api_key: Optional[str] = None, model: str = DEFAULT_HF_MODEL):
        self.api_key = (api_key or "").strip()
        self.model = model
        self.client: Optional[InferenceClient] = None
        self.last_error: str = ""
        if self.api_key and HF_AVAILABLE:
            try:
                self.client = InferenceClient(token=self.api_key)
            except Exception as exc:
                self.last_error = str(exc)
                self.client = None

    @property
    def is_connected(self) -> bool:
        return self.client is not None and bool(self.api_key)

    def _candidate_models(self) -> list[str]:
        models = [
            self.model,
            "Qwen/Qwen2.5-7B-Instruct",
            "HuggingFaceH4/zephyr-7b-beta",
            "mistralai/Mistral-7B-Instruct-v0.2",
        ]
        unique = []
        for model in models:
            if model and model not in unique:
                unique.append(model)
        return unique

    def _extract_text(self, response: Any) -> str:
        """Extract text from different Hugging Face response shapes."""
        if response is None:
            return ""

        if isinstance(response, str):
            return response.strip()

        try:
            choices = getattr(response, "choices", None)
            if choices and len(choices) > 0:
                content = getattr(choices[0].message, "content", "")
                if isinstance(content, list):
                    parts = [getattr(item, "text", "") for item in content]
                    return " ".join(p for p in parts if p).strip()
                return str(content).strip()
        except Exception:
            pass

        generated_text = getattr(response, "generated_text", None)
        if generated_text:
            return str(generated_text).strip()

        if isinstance(response, dict):
            if "generated_text" in response:
                return str(response["generated_text"]).strip()

        return ""

    def _chat_completion_text(self, messages: list[dict], max_tokens: int = 512, temperature: float = 0.7) -> str:
        """Primary chat endpoint."""
        if not self.client:
            return ""
        last_exception = None
        for candidate_model in self._candidate_models():
            try:
                response = self.client.chat_completion(
                    model=candidate_model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                text = self._extract_text(response)
                if text:
                    return text
            except Exception as exc:
                last_exception = exc
                continue
        if last_exception:
            raise last_exception
        return ""

    def _text_generation_text(self, prompt: str, max_new_tokens: int = 300, temperature: float = 0.7) -> str:
        """Fallback generation endpoint for models/endpoints without chat support."""
        if not self.client:
            return ""
        last_exception = None
        for candidate_model in self._candidate_models():
            try:
                response = self.client.text_generation(
                    prompt,
                    model=candidate_model,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                )
                text = self._extract_text(response)
                if text:
                    return text
            except Exception as exc:
                last_exception = exc
                continue
        if last_exception:
            raise last_exception
        return ""

    # ------------------------------------------------------------------
    #  Chat  (AI career advisor)
    # ------------------------------------------------------------------
    def chat(self, message: str, context: str = "") -> str:
        """Send a user message with optional system context.  Returns the
        assistant's reply as plain text."""
        system_prompt = (
            "You are SkillForge AI – a concise, expert career & skills coach. "
            "Give actionable, specific advice.  Keep answers under 200 words. "
            f"{context}"
        )
        if self.client:
            try:
                text = self._chat_completion_text(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": message},
                    ],
                    max_tokens=512,
                    temperature=0.7,
                )
                if text:
                    self.last_error = ""
                    return text
            except Exception as exc:
                self.last_error = f"chat_completion failed: {exc}"

            try:
                prompt = f"{system_prompt}\n\nUser: {message}\nAssistant:"
                text = self._text_generation_text(prompt, max_new_tokens=320, temperature=0.7)
                if text:
                    self.last_error = ""
                    return text
            except Exception as exc:
                self.last_error = f"text_generation failed: {exc}"

        return self._fallback_chat(message)

    # ------------------------------------------------------------------
    #  Resume skill extraction
    # ------------------------------------------------------------------
    def extract_skills_from_resume(self, resume_text: str) -> str:
        """Ask the LLM to identify skills and estimate proficiency (1-10)."""
        prompt = (
            "Analyze the following resume and list each technical skill found "
            "with an estimated proficiency from 1 to 10. Return ONLY a "
            "comma-separated list in the format:  Skill:Level, Skill:Level\n\n"
            f"Resume:\n{resume_text[:3000]}"
        )
        if self.client:
            try:
                text = self._chat_completion_text(
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=300,
                    temperature=0.3,
                )
                if text:
                    self.last_error = ""
                    return text
            except Exception as exc:
                self.last_error = f"resume chat failed: {exc}"

            try:
                text = self._text_generation_text(prompt, max_new_tokens=220, temperature=0.2)
                if text:
                    self.last_error = ""
                    return text
            except Exception as exc:
                self.last_error = f"resume generation failed: {exc}"
        return ""  # caller should fall back to keyword parser

    # ------------------------------------------------------------------
    #  Learning advice
    # ------------------------------------------------------------------
    def get_learning_advice(self, skill: str, current: int, target: int) -> str:
        prompt = (
            f"I'm at level {current}/10 in {skill} and need to reach {target}/10. "
            "Give me a concise 3-step action plan (under 100 words)."
        )
        return self.chat(prompt)

    # ------------------------------------------------------------------
    #  Fallbacks (no API key)
    # ------------------------------------------------------------------
    @staticmethod
    def _fallback_chat(message: str) -> str:
        msg = message.lower()
        responses = {
            "roadmap": (
                "Here's a general approach:\n"
                "1. **Prioritize** skills with the largest gap and highest role weight.\n"
                "2. **Dedicate** focused 2-hour daily blocks.\n"
                "3. **Build projects** that combine multiple skills.\n"
                "4. **Review** weekly with practice quizzes.\n"
                "Tip: Check the *Learning Roadmap* page for your personalized plan!"
            ),
            "python": (
                "Python is foundational for data & AI roles.\n"
                "• Start with *Automate the Boring Stuff* for basics.\n"
                "• Move to *Fluent Python* for intermediate mastery.\n"
                "• Build 2-3 portfolio projects on GitHub."
            ),
            "interview": (
                "Preparation tips:\n"
                "1. Practice coding problems on LeetCode/HackerRank.\n"
                "2. Review system-design fundamentals.\n"
                "3. Prepare STAR-format stories for behavioral rounds.\n"
                "4. Study the company's tech stack."
            ),
            "motivat": (
                "Consistency beats intensity! 🚀\n"
                "• Set small daily goals.\n"
                "• Track progress visually (this app helps!).\n"
                "• Celebrate each skill-level improvement."
            ),
        }
        for keyword, resp in responses.items():
            if keyword in msg:
                return resp
        return (
            "Great question! Here are general tips:\n"
            "1. Focus on your highest-priority skill gaps first.\n"
            "2. Use project-based learning to retain knowledge.\n"
            "3. Reassess every 2 weeks with the quiz.\n"
            "4. Check the Gap Analysis and Roadmap pages for details.\n\n"
            "💡 *Connect a Hugging Face API key in the sidebar for personalised AI advice.*"
        )
