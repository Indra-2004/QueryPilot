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


