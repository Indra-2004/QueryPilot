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


