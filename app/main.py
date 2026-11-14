from dataclasses import dataclass
from typing import Optional
import time
from app.core.config import settings  # ensures env is loaded once
from app.core.session import SessionManager
from app.graph.graph import build_graph
from app.retriever.schema_retriever import SchemaRetriever
from app.db.connections import get_connection_engine
from scripts.ingest_schema import connection_schema_namespace, extract_schema_from_engine

_ = settings

_graph = None
_retriever = None
_session_manager = SessionManager()

def _get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph

