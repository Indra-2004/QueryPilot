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


