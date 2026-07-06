"""
validator.py
SQL validation and security guardrails.
Only single, read-only SELECT statements are permitted.
"""

import logging
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Statement types / keywords that must never appear in a generated query.
FORBIDDEN_KEYWORDS = [
    "DROP",
    "DELETE",
    "UPDATE",
    "INSERT",
    "ALTER",
    "TRUNCATE",
    "CREATE",
    "GRANT",
    "REVOKE",
    "REPLACE",
    "MERGE",
    "CALL",
    "EXECUTE",
    "COPY",
    "VACUUM",
    "REINDEX",
    "COMMENT",
    "SECURITY",
    "ATTACH",
    "DETACH",
]

# Patterns that indicate multiple statements or SQL injection attempts.
DANGEROUS_PATTERNS = [
    r";\s*\S+",          # a second statement after a semicolon
    r"--",               # SQL comment (can be used to hide malicious code)
    r"/\*",              # block comment start
    r"\bpg_sleep\b",     # denial-of-service via sleep
    r"\bpg_read_file\b", # filesystem access
    r"\bdblink\b",       # cross-database access
    r"\bcopy\b.*\bfrom\b",
]


@dataclass
class ValidationResult:
    is_valid: bool
    reason: str = ""
    cleaned_sql: str = ""


def _strip_wrapping(sql: str) -> str:
    """Remove markdown code fences and trailing semicolons/whitespace."""
    sql = sql.strip()
    sql = re.sub(r"^```(sql)?", "", sql, flags=re.IGNORECASE).strip()
    sql = re.sub(r"```$", "", sql).strip()
    sql = sql.rstrip(";").strip()
    return sql


def validate_sql(raw_sql: str) -> ValidationResult:
    """
    Validate that the provided SQL is a single, safe, read-only SELECT statement.
    Returns a ValidationResult with the cleaned SQL if valid.
    """
    if not raw_sql or not raw_sql.strip():
        return ValidationResult(False, "Empty SQL query generated.")

    cleaned = _strip_wrapping(raw_sql)
    upper_sql = cleaned.upper()

    if not upper_sql.startswith("SELECT") and not upper_sql.startswith("WITH"):
        return ValidationResult(
            False,
            "Only SELECT queries are allowed. The generated query did not start with SELECT/WITH.",
        )

    for keyword in FORBIDDEN_KEYWORDS:
        if re.search(rf"\b{keyword}\b", upper_sql):
            return ValidationResult(False, f"Query contains a forbidden keyword: {keyword}.")

    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, cleaned, flags=re.IGNORECASE):
            return ValidationResult(False, f"Query matched a blocked pattern: {pattern}.")

    # Ensure there is exactly one statement (no stray semicolons splitting statements)
    statements = [s for s in cleaned.split(";") if s.strip()]
    if len(statements) > 1:
        return ValidationResult(False, "Multiple SQL statements are not allowed.")

    logger.info("SQL validated successfully: %s", cleaned)
    return ValidationResult(True, cleaned_sql=cleaned)
