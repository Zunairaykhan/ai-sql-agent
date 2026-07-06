"""
app.py
FastAPI application exposing the AI SQL Agent /chat endpoint.

Flow per request:
  1. Receive user question (+ optional session id).
  2. Read database schema (auto-discovered, cached).
  3. Send schema + question + conversation history to Groq -> generate SQL.
  4. Validate SQL (SELECT-only, no dangerous keywords).
  5. Execute SQL against PostgreSQL.
  6. Send results back to Groq -> generate natural language explanation.
  7. Return JSON with sql, columns, rows, explanation.
"""

import logging
import time
import uuid
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from config import settings, configure_logging
from database import init_pool, close_pool, test_connection, execute_select, DatabaseError
from schema import get_schema_description
from validator import validate_sql
from llm import get_llm_client, LLMError

configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI SQL Agent",
    description="Ask questions in plain English and get answers from your PostgreSQL database.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory per-session conversation history: {session_id: [ {question, sql, explanation}, ... ]}
_conversation_memory: Dict[str, List[Dict[str, str]]] = {}
_MAX_HISTORY_TURNS = 6


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    question: str
    sql: Optional[str] = None
    columns: List[str] = []
    rows: List[Dict[str, Any]] = []
    row_count: int = 0
    explanation: str
    success: bool
    error: Optional[str] = None
    elapsed_ms: int


@app.on_event("startup")
def on_startup() -> None:
    logger.info("Starting AI SQL Agent backend...")
    init_pool()
    if not test_connection():
        logger.warning("Database connectivity test failed at startup. Check your PG settings.")
    else:
        logger.info("Database connection verified.")


@app.on_event("shutdown")
def on_shutdown() -> None:
    close_pool()
    logger.info("AI SQL Agent backend shut down cleanly.")


@app.get("/health")
def health_check() -> Dict[str, Any]:
    db_ok = test_connection()
    return {"status": "ok" if db_ok else "degraded", "database_connected": db_ok}


@app.get("/schema")
def get_schema() -> Dict[str, str]:
    try:
        return {"schema": get_schema_description(force_refresh=True)}
    except DatabaseError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


def _format_history(session_id: str) -> str:
    turns = _conversation_memory.get(session_id, [])
    if not turns:
        return ""
    lines = []
    for turn in turns[-_MAX_HISTORY_TURNS:]:
        lines.append(f"Q: {turn['question']}\nSQL: {turn['sql']}\nAnswer: {turn['explanation']}")
    return "\n\n".join(lines)


def _remember(session_id: str, question: str, sql: str, explanation: str) -> None:
    _conversation_memory.setdefault(session_id, []).append(
        {"question": question, "sql": sql, "explanation": explanation}
    )
    if len(_conversation_memory[session_id]) > _MAX_HISTORY_TURNS:
        _conversation_memory[session_id] = _conversation_memory[session_id][-_MAX_HISTORY_TURNS:]


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    start_time = time.time()
    session_id = request.session_id or str(uuid.uuid4())
    question = request.question.strip()

    logger.info("[%s] New question: %s", session_id, question)

    try:
        schema_description = get_schema_description()
    except DatabaseError as exc:
        elapsed = int((time.time() - start_time) * 1000)
        return ChatResponse(
            session_id=session_id,
            question=question,
            explanation="I couldn't read the database schema.",
            success=False,
            error=str(exc),
            elapsed_ms=elapsed,
        )

    history_text = _format_history(session_id)
    llm_client = get_llm_client()

    try:
        raw_sql = llm_client.generate_sql(schema_description, question, history_text)
        logger.info("[%s] Raw SQL generated: %s", session_id, raw_sql)
    except LLMError as exc:
        elapsed = int((time.time() - start_time) * 1000)
        return ChatResponse(
            session_id=session_id,
            question=question,
            explanation="I couldn't generate a SQL query for that question.",
            success=False,
            error=str(exc),
            elapsed_ms=elapsed,
        )

    validation = validate_sql(raw_sql)
    if not validation.is_valid:
        logger.warning("[%s] SQL rejected: %s", session_id, validation.reason)
        elapsed = int((time.time() - start_time) * 1000)
        return ChatResponse(
            session_id=session_id,
            question=question,
            sql=raw_sql,
            explanation="The generated query was rejected for safety reasons.",
            success=False,
            error=validation.reason,
            elapsed_ms=elapsed,
        )

    clean_sql = validation.cleaned_sql

    if "UNABLE_TO_ANSWER" in clean_sql.upper():
        elapsed = int((time.time() - start_time) * 1000)
        return ChatResponse(
            session_id=session_id,
            question=question,
            sql=clean_sql,
            explanation=(
                "I couldn't find a way to answer that question using the current "
                "database schema. Try rephrasing or asking about the available tables."
            ),
            success=False,
            error="Question could not be mapped to the schema.",
            elapsed_ms=elapsed,
        )

    try:
        columns, rows = execute_select(clean_sql)
    except DatabaseError as exc:
        logger.error("[%s] SQL execution failed: %s", session_id, exc)
        elapsed = int((time.time() - start_time) * 1000)
        return ChatResponse(
            session_id=session_id,
            question=question,
            sql=clean_sql,
            explanation="The query failed to execute against the database.",
            success=False,
            error=str(exc),
            elapsed_ms=elapsed,
        )

    try:
        explanation = llm_client.generate_explanation(
            question=question, sql=clean_sql, columns=columns, rows=rows, row_count=len(rows)
        )
    except LLMError as exc:
        logger.warning("[%s] Explanation generation failed: %s", session_id, exc)
        explanation = (
            f"Query executed successfully and returned {len(rows)} row(s), "
            "but I couldn't generate a natural language summary."
        )

    _remember(session_id, question, clean_sql, explanation)

    elapsed = int((time.time() - start_time) * 1000)
    logger.info("[%s] Completed in %dms, %d rows returned", session_id, elapsed, len(rows))

    return ChatResponse(
        session_id=session_id,
        question=question,
        sql=clean_sql,
        columns=columns,
        rows=rows,
        row_count=len(rows),
        explanation=explanation,
        success=True,
        error=None,
        elapsed_ms=elapsed,
    )


@app.delete("/chat/{session_id}")
def clear_session(session_id: str) -> Dict[str, str]:
    _conversation_memory.pop(session_id, None)
    return {"status": "cleared", "session_id": session_id}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host=settings.APP_HOST, port=settings.APP_PORT, reload=True)
