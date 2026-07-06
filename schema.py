"""
schema.py
Automatic PostgreSQL schema discovery. No hardcoded tables or columns -
works with any database by querying information_schema.
"""

import logging
import time
from typing import Dict, List

from config import settings
from database import _get_connection, _put_connection, DatabaseError

logger = logging.getLogger(__name__)

_schema_cache: Dict[str, str] = {"text": "", "timestamp": 0.0}
_CACHE_TTL_SECONDS = 300  # refresh schema every 5 minutes


def _fetch_tables_and_columns() -> Dict[str, List[Dict[str, str]]]:
    """Query information_schema for all tables/columns in the configured schema."""
    conn = _get_connection()
    tables: Dict[str, List[Dict[str, str]]] = {}
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT table_name, column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = %s
                ORDER BY table_name, ordinal_position;
                """,
                (settings.PG_SCHEMA,),
            )
            for table_name, column_name, data_type, is_nullable in cur.fetchall():
                tables.setdefault(table_name, []).append(
                    {
                        "column": column_name,
                        "type": data_type,
                        "nullable": is_nullable,
                    }
                )
        return tables
    except Exception as exc:  # noqa: BLE001
        logger.error("Schema discovery failed: %s", exc)
        raise DatabaseError(f"Could not read database schema: {exc}") from exc
    finally:
        _put_connection(conn)


def _fetch_primary_keys() -> Dict[str, List[str]]:
    """Return {table_name: [primary key columns]} for the configured schema."""
    conn = _get_connection()
    pks: Dict[str, List[str]] = {}
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT tc.table_name, kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON tc.constraint_name = kcu.constraint_name
                 AND tc.table_schema = kcu.table_schema
                WHERE tc.constraint_type = 'PRIMARY KEY'
                  AND tc.table_schema = %s;
                """,
                (settings.PG_SCHEMA,),
            )
            for table_name, column_name in cur.fetchall():
                pks.setdefault(table_name, []).append(column_name)
        return pks
    except Exception as exc:  # noqa: BLE001
        logger.warning("Primary key discovery failed (non-fatal): %s", exc)
        return {}
    finally:
        _put_connection(conn)


def get_schema_description(force_refresh: bool = False) -> str:
    """
    Return a human/LLM-readable description of the database schema.
    Cached for _CACHE_TTL_SECONDS to avoid hitting the DB on every request.
    """
    now = time.time()
    if (
        not force_refresh
        and _schema_cache["text"]
        and (now - _schema_cache["timestamp"]) < _CACHE_TTL_SECONDS
    ):
        return _schema_cache["text"]

    tables = _fetch_tables_and_columns()
    primary_keys = _fetch_primary_keys()

    if not tables:
        description = "No tables found in the database schema."
        _schema_cache.update(text=description, timestamp=now)
        return description

    lines: List[str] = []
    for table_name, columns in tables.items():
        pk_cols = set(primary_keys.get(table_name, []))
        col_descriptions = []
        for col in columns:
            marker = " [PK]" if col["column"] in pk_cols else ""
            nullable = "" if col["nullable"] == "YES" else " NOT NULL"
            col_descriptions.append(f"{col['column']} ({col['type']}){marker}{nullable}")
        lines.append(f"Table \"{table_name}\":\n  - " + "\n  - ".join(col_descriptions))

    description = "\n\n".join(lines)
    _schema_cache.update(text=description, timestamp=now)
    logger.info("Schema discovered: %d tables", len(tables))
    return description


def get_table_names() -> List[str]:
    tables = _fetch_tables_and_columns()
    return list(tables.keys())
