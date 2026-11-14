from typing import TypedDict, Optional
import re
import time
from langchain_core.messages import HumanMessage
from app.llm.client import get_llm
from app.llm.prompts import GENERATE_PROMPT, CORRECT_PROMPT, VALIDATE_PROMPT
from app.db.engine import execute_query
from app.validators.sql_guard import is_safe
from app.utils.toon import extract_sql_from_toon, schema_text_to_toon

MAX_RETRIES = 3


def _normalize_sql(sql: str) -> str:
    cleaned = sql.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    if cleaned.lower().startswith("sql\n"):
        cleaned = cleaned[4:].strip()
    # Strip any residual ''' wrapping the LLM emitted despite instructions
    if cleaned.startswith("'''"):
        cleaned = cleaned[3:]
    if cleaned.endswith("'''") or cleaned.endswith("''''"):
        cleaned = cleaned.rstrip("'")
    # Fix doubled single-quotes from old TOON wrapping artifact (''value'' -> 'value')
    cleaned = re.sub(r"''([^']+)''", r"'\1'", cleaned)
    return cleaned.strip()

