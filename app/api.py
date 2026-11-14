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

class ProviderRequest(BaseModel):
    name: str
    provider_type: str
    api_key: str
    model: str
    base_url: str | None = None

class ConnectionRequest(BaseModel):
    name: str
    db_uri: str
    provider_id: str | None = None

class IngestRequest(BaseModel):
    db_uri: str | None = None  # defaults to DB_URI from .env if omitted

    model_config = {"json_schema_extra": {"examples": [{"db_uri": "postgresql://user:pass@localhost/mydb"}]}}


def _compact_sql(sql: str) -> str:
    # Deterministic API-side formatting for JSON clients.
    return re.sub(r"\s+", " ", (sql or "")).strip()

@app.get("/health", summary="Health check", tags=["Utility"])
def health():
    """Lightweight liveness probe used by Render and external monitors."""
    return {"status": "ok", "service": "nerfsql"}

@app.get("/ready", tags=["Utility"])
def ready():
    return {"status": "ready"}

@app.post("/jobs/seed", tags=["Jobs"])
def seed_job():
    """Queue a rebuildable demo dataset; the job is safe to retry."""
    return enqueue_seed()

@app.post("/providers", tags=["Providers"])
def create_provider(req: ProviderRequest):
    try:
        profile = provider_profiles.create_profile(owner_id="default", **req.model_dump())
        # Construction validates provider type and local configuration without making a paid call.
        get_llm(profile=provider_profiles.get_profile(profile["provider_id"]))
        return profile
    except (ValueError, ProviderError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@app.get("/providers", tags=["Providers"])
def list_providers():
    return {"providers": provider_profiles.list_profiles()}

@app.get("/providers/{provider_id}", tags=["Providers"])
def get_provider(provider_id: str):
    profile = next((p for p in provider_profiles.list_profiles() if p["provider_id"] == provider_id), None)
    if not profile: raise HTTPException(status_code=404, detail="Provider not found")
    return profile

@app.delete("/providers/{provider_id}", tags=["Providers"])
def delete_provider(provider_id: str):
    if not provider_profiles.delete_profile(provider_id): raise HTTPException(status_code=404, detail="Provider not found")
    return {"deleted": True, "provider_id": provider_id}

@app.post("/connections", tags=["Connections"])
def create_connection(req: ConnectionRequest):
    try:
        profile = connections.create_profile(owner_id="default", name=req.name, uri=req.db_uri, provider_id=req.provider_id)
        profile["schema_index"] = _index_connection_schema(profile["connection_id"])
        return profile
    except connections.ConnectionError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


