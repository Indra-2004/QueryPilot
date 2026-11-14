import argparse
import json
import os
import time
from typing import Any

import numpy as np
from pinecone import Pinecone, ServerlessSpec
from fastembed import TextEmbedding
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import Engine

try:
    from app.core.config import settings
except ModuleNotFoundError:
    from dotenv import load_dotenv

    load_dotenv(dotenv_path=".env")

    class _ScriptSettings:
        pinecone_api_key = os.environ.get("PINECONE_API_KEY")
        pinecone_index_name = os.environ.get("PINECONE_INDEX_NAME", "sql-schema-rag")
        pinecone_namespace = os.environ.get("PINECONE_NAMESPACE", "default")
        pinecone_region = os.environ.get("PINECONE_REGION", "us-east-1")

    settings = _ScriptSettings()


EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def connection_schema_namespace(connection_id: str) -> str:
    """Keep every saved database in an isolated Pinecone namespace."""
    return f"connection-{connection_id}"

def extract_schema_from_engine(engine: Engine) -> list[str]:
    """Return schema chunks for an already configured database engine."""
    inspector = inspect(engine)
    chunks = []
    for table in inspector.get_table_names():
        cols = [c["name"] for c in inspector.get_columns(table)]
        fks = [f"{fk['constrained_columns']} -> {fk['referred_table']}" for fk in inspector.get_foreign_keys(table)]
        chunk = f"Table: {table}\nColumns: {', '.join(cols)}"
        if fks:
            chunk += f"\nForeign keys: {'; '.join(fks)}"
        chunks.append(chunk)
    return chunks


def extract_schema(db_uri: str) -> list[str]:
    engine = create_engine(db_uri)
    try:
        return extract_schema_from_engine(engine)
    finally:
        engine.dispose()


