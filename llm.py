"""
llm.py
Thin wrapper around the official Groq Python SDK used to:
  1. Generate a PostgreSQL SELECT statement from a natural language question.
  2. Generate a natural language explanation from query results.
"""

import logging
from typing import Any, List

from groq import Groq, APIError, APIConnectionError, APITimeoutError

from config import settings
from prompts import build_sql_prompt, build_explanation_prompt

logger = logging.getLogger(__name__)


class LLMError(Exception):
    """Raised when the LLM call fails or returns an unusable response."""


class GroqClient:
    def __init__(self) -> None:
        self._client = Groq(api_key=settings.GROQ_API_KEY)
        self._model = settings.GROQ_MODEL

    def _chat(self, system_prompt: str, user_prompt: str, temperature: float = 0.0) -> str:
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=1024,
            )
            content = response.choices[0].message.content
            if not content:
                raise LLMError("The AI model returned an empty response.")
            return content.strip()
        except APITimeoutError as exc:
            logger.error("Groq API timeout: %s", exc)
            raise LLMError("The AI model timed out. Please try again.") from exc
        except APIConnectionError as exc:
            logger.error("Groq API connection error: %s", exc)
            raise LLMError("Could not connect to the Groq API. Check your network/API key.") from exc
        except APIError as exc:
            logger.error("Groq API error: %s", exc)
            raise LLMError(f"Groq API returned an error: {exc}") from exc
        except Exception as exc:  # noqa: BLE001
            logger.error("Unexpected LLM error: %s", exc)
            raise LLMError(f"Unexpected error calling the AI model: {exc}") from exc

    def generate_sql(self, schema: str, question: str, history: str = "") -> str:
        system_prompt, user_prompt = build_sql_prompt(schema, question, history)
        raw = self._chat(system_prompt, user_prompt, temperature=0.0)
        return raw

    def generate_explanation(
        self,
        question: str,
        sql: str,
        columns: List[str],
        rows: List[dict[str, Any]],
        row_count: int,
    ) -> str:
        system_prompt, user_prompt = build_explanation_prompt(
            question=question, sql=sql, columns=columns, rows=rows, row_count=row_count
        )
        return self._chat(system_prompt, user_prompt, temperature=0.3)


_client_instance: GroqClient | None = None


def get_llm_client() -> GroqClient:
    global _client_instance
    if _client_instance is None:
        _client_instance = GroqClient()
    return _client_instance
