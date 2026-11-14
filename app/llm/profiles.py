"""Encrypted provider profile registry used by the API and LLM factory."""
from __future__ import annotations
from dataclasses import asdict
from threading import RLock
from uuid import uuid4
from app.llm.client import ProviderProfile, encrypt_secret, provider_metadata
from sqlalchemy import String, Text, Boolean, select
from sqlalchemy.orm import Mapped, mapped_column, Session
from app.db.connections import Base, metadata_engine

