"""Free-tier friendly RAG vs full-schema benchmark for the deployed API."""
from __future__ import annotations

import argparse
import json
import math
import re
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
ALLOWED_TABLES = {"customers", "products", "orders", "order_items"}


def request_json(base_url: str, path: str, payload: dict | None = None) -> tuple[int, dict]:
    body = json.dumps(payload).encode() if payload is not None else None
    request = Request(
        base_url.rstrip("/") + path,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST" if body is not None else "GET",
    )
    try:
        with urlopen(request, timeout=120) as response:
            return response.status, json.loads(response.read().decode())
    except HTTPError as exc:
        try:
            return exc.code, json.loads(exc.read().decode())
        except Exception:
            return exc.code, {"error": str(exc)}
    except URLError as exc:
        return 0, {"error": str(exc)}


def run_query_with_backoff(base_url: str, payload: dict, max_attempts: int) -> tuple[int, dict, float]:
    total_started = time.perf_counter()
    status, response = 0, {}
    for attempt in range(1, max_attempts + 1):
        status, response = request_json(base_url, "/query", payload)
        if status != 429:
            break
        if attempt < max_attempts:
            wait_seconds = 60 * attempt
            print(f"  provider rate limit; waiting {wait_seconds}s before retry {attempt + 1}/{max_attempts}")
            time.sleep(wait_seconds)
    return status, response, round((time.perf_counter() - total_started) * 1000, 2)


