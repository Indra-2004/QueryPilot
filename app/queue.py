"""Small durable seed queue backed by Upstash Redis (Redis protocol)."""
from __future__ import annotations
import json, os, sqlite3
from datetime import datetime, timezone
from pathlib import Path

QUEUE_KEY = os.getenv("SEED_QUEUE_KEY", "nerfsql:seed:queue")
DONE_PREFIX = os.getenv("SEED_DONE_PREFIX", "nerfsql:seed:done:")

