"""
database.py
PostgreSQL connection management and safe query execution using psycopg2.
Works with any PostgreSQL database - no hardcoded table/column names.
"""

import logging
from typing import Any, Dict, List, Tuple

import psycopg2
import psycopg2.extras
from psycopg2 import pool as pg_pool

from config import settings

logger = logging.getLogger(__name__)

_connection_pool: pg_pool.SimpleConnectionPool | None = None


class DatabaseError(Exception):
    """Raised when a database operation fails."""


def _build_dsn() -> str:
    if settings.DATABASE_URL:
        return settings.DATABASE_URL
    return (
        f"host={settings.PG_HOST} port={settings.PG_PORT} "
        f"dbname={settings.PG_DATABASE} user={settings.PG_USER} "
        f"password={settings.PG_PASSWORD}"
    )


def init_pool(minconn: int = 1, maxconn: int = 10) -> None:
    """Initialize the global connection pool. Safe to call multiple times."""
    global _connection_pool
    if _connection_pool is not None:
        return
    try:
        dsn = _build_dsn()
        _connection_pool = pg_pool.SimpleConnectionPool(minconn, maxconn, dsn)
        logger.info("PostgreSQL connection pool initialized (min=%s max=%s)", minconn, maxconn)
    except psycopg2.OperationalError as exc:
        logger.error("Failed to connect to PostgreSQL: %s", exc)
        raise DatabaseError(f"Could not connect to PostgreSQL: {exc}") from exc


def close_pool() -> None:
    global _connection_pool
    if _connection_pool is not None:
        _connection_pool.closeall()
        _connection_pool = None
        logger.info("PostgreSQL connection pool closed.")


def _get_connection():
    if _connection_pool is None:
        init_pool()
    assert _connection_pool is not None
    return _connection_pool.getconn()


def _put_connection(conn) -> None:
    if _connection_pool is not None:
        _connection_pool.putconn(conn)


def test_connection() -> bool:
    """Quick health check used at startup."""
    try:
        conn = _get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                cur.fetchone()
            return True
        finally:
            _put_connection(conn)
    except Exception as exc:  # noqa: BLE001
        logger.error("Database connectivity test failed: %s", exc)
        return False


def execute_select(query: str, max_rows: int | None = None) -> Tuple[List[str], List[Dict[str, Any]]]:
    """
    Execute a read-only SELECT query and return (columns, rows).
    Rows are returned as a list of JSON-serializable dictionaries.
    """
    max_rows = max_rows or settings.MAX_ROWS_RETURNED
    conn = _get_connection()
    try:
        conn.set_session(readonly=True, autocommit=True)
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(f"SET statement_timeout = {settings.QUERY_TIMEOUT_SECONDS * 1000};")
            cur.execute(query)
            if cur.description is None:
                return [], []
            columns = [desc.name for desc in cur.description]
            raw_rows = cur.fetchmany(max_rows)
            rows = [dict(row) for row in raw_rows]
            return columns, _sanitize_rows(rows)
    except psycopg2.Error as exc:
        logger.error("SQL execution error: %s", exc)
        raise DatabaseError(str(exc).strip()) from exc
    finally:
        try:
            conn.set_session(readonly=False, autocommit=False)
        except Exception:  # noqa: BLE001
            pass
        _put_connection(conn)


def _sanitize_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert non-JSON-serializable types (Decimal, datetime, etc.) to strings/numbers."""
    import datetime
    from decimal import Decimal

    sanitized: List[Dict[str, Any]] = []
    for row in rows:
        clean: Dict[str, Any] = {}
        for key, value in row.items():
            if isinstance(value, Decimal):
                clean[key] = float(value)
            elif isinstance(value, (datetime.date, datetime.datetime, datetime.time)):
                clean[key] = value.isoformat()
            elif isinstance(value, (bytes, bytearray)):
                clean[key] = value.decode("utf-8", errors="replace")
            else:
                clean[key] = value
        sanitized.append(clean)
    return sanitized
