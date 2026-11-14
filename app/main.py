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

def _get_retriever():
    global _retriever
    if _retriever is None:
        _retriever = SchemaRetriever()
    return _retriever

def _schema_for_query(question: str, connection_id: Optional[str], schema_strategy: str = "rag") -> str:
    if connection_id:
        if schema_strategy == "full":
            engine = get_connection_engine(connection_id, owner_id="default")
            return "\n".join(extract_schema_from_engine(engine))
        # Search only the selected connection's vector namespace. Never reuse
        # the deployment-wide namespace, which may describe a different DB.
        retrieved = _get_retriever().retrieve(
            question,
            namespace=connection_schema_namespace(connection_id),
            allow_local_fallback=False,
        )
        if retrieved:
            return retrieved
        # Pinecone is optional, and a newly added connection may still be
        # indexing. Live introspection keeps queries correct in either case.
        engine = get_connection_engine(connection_id, owner_id="default")
        return "\n".join(extract_schema_from_engine(engine))
    return _get_retriever().retrieve(question)

@dataclass
class QueryResponse:
    sql: str
    result: Optional[list]
    error: Optional[str]
    retries: int
    chat_id: str = ""
    connection_id: Optional[str] = None
    provider_id: Optional[str] = None
    model: Optional[str] = None
    schema_strategy: str = "rag"
    input_tokens: int = 0
    output_tokens: int = 0
    llm_calls: int = 0
    llm_latency_ms: float = 0.0
    total_latency_ms: float = 0.0

