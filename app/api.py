import json
import logging
import os
import re
import sqlite3
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from pydantic import BaseModel
from app.core.config import settings
from app.main import QueryResponse, query_agent, _session_manager
from scripts.ingest_schema import (
    connection_schema_namespace,
    delete_pinecone_namespace,
    extract_schema,
    extract_schema_from_engine,
    upsert_schema_chunks_to_pinecone,
)
from app.db import connections
from app.llm import profiles as provider_profiles
from app.llm.client import get_llm, ProviderError
from app.queue import enqueue_seed, drain_seed_queue

app = FastAPI(title="SQL-RAG Agent", description="Natural language to SQL agent powered by RAG", version="1.0.0")
logger = logging.getLogger("nerfsql.api")
app.mount("/frontend", StaticFiles(directory="frontend", html=True), name="frontend")

@app.on_event("startup")
def drain_startup_seed_queue():
    """Replay durable seed jobs after a container restart."""
    try:
        drain_seed_queue()
    except Exception:
        # The API remains available if Upstash is temporarily unreachable.
        pass

@app.get("/", include_in_schema=False)
def home():
    return RedirectResponse(url="/frontend/")

app.add_middleware(GZipMiddleware, minimum_size=1000)
_allowed_hosts = [
    host.strip()
    for host in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]
app.add_middleware(TrustedHostMiddleware, allowed_hosts=_allowed_hosts)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://127.0.0.1"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Cache-Control"] = "no-store"
        response.headers["Content-Security-Policy"] = "default-src 'none'; style-src 'self' 'unsafe-inline'; font-src 'self'; script-src 'self'; connect-src 'self'"
        return response

app.add_middleware(SecurityHeadersMiddleware)

class QueryRequest(BaseModel):
    question: str
    connection_id: str | None = None
    provider_id: str | None = None
    model: str | None = None
    schema_strategy: Literal["rag", "full"] = "rag"

