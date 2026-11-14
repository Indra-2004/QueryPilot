"""
In-memory session manager for storing conversation history.
Each conversation is identified by a unique chat_id (UUID).
Maintains a sliding window of the last 4 queries and 4 responses,
plus an immutable first query.
"""

from dataclasses import dataclass, field
from datetime import datetime
from collections import deque
from threading import Lock
from typing import Dict, Optional
from uuid import uuid4


@dataclass
class QueryRecord:
    """Represents a natural language query from the user."""
    timestamp: datetime
    question: str
    error: Optional[str] = None
    connection_id: Optional[str] = None
    provider_id: Optional[str] = None
    model: Optional[str] = None


@dataclass
class ResponseRecord:
    """Represents a response from the query agent."""
    timestamp: datetime
    sql: str
    sql_raw: str
    result: Optional[list]
    error: Optional[str]
    retries: int
    connection_id: Optional[str] = None
    provider_id: Optional[str] = None
    model: Optional[str] = None


@dataclass
class ChatSession:
    """Represents a single conversation session."""
    chat_id: str
    created_at: datetime
    first_query: QueryRecord
    queries: deque = field(default_factory=lambda: deque(maxlen=4))  # Last 4 queries
    responses: deque = field(default_factory=lambda: deque(maxlen=4))  # Last 4 responses
    connection_id: Optional[str] = None
    provider_id: Optional[str] = None
    model: Optional[str] = None


