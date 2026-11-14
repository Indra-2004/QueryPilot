"""Encrypted provider profile registry used by the API and LLM factory."""
from __future__ import annotations
from dataclasses import asdict
from threading import RLock
from uuid import uuid4
from app.llm.client import ProviderProfile, encrypt_secret, provider_metadata
from sqlalchemy import String, Text, Boolean, select
from sqlalchemy.orm import Mapped, mapped_column, Session
from app.db.connections import Base, metadata_engine

class ProviderProfileRecord(Base):
    __tablename__ = "llm_providers"
    provider_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_id: Mapped[str] = mapped_column(String(255), index=True)
    name: Mapped[str] = mapped_column(String(120))
    provider_type: Mapped[str] = mapped_column(String(40))
    encrypted_api_key: Mapped[str] = mapped_column(Text)
    encrypted_base_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    model: Mapped[str] = mapped_column(String(160))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
_lock = RLock()

def create_profile(*, owner_id: str, name: str, provider_type: str, api_key: str,
                   model: str, base_url: str | None = None) -> dict:
    if not owner_id or not name or not api_key or not model:
        raise ValueError("owner_id, name, api_key, and model are required")
    pid = str(uuid4())
    record = {"provider_id": pid, "owner_id": owner_id, "name": name,
              "provider_type": provider_type, "encrypted_api_key": encrypt_secret(api_key),
              "model": model, "encrypted_base_url": encrypt_secret(base_url) if base_url else None,
              "enabled": True}
    with Session(metadata_engine()) as session:
        session.add(ProviderProfileRecord(**record)); session.commit()
    return provider_metadata(record)

