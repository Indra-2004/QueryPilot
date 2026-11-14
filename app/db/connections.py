"""Named database connection profiles and isolated SQLAlchemy engines.

Profiles are stored in a small local metadata database by default.  Set
``CONNECTION_STORE_URI`` to the application's durable metadata database in
production.  Connection URLs are encrypted at rest and are never included in
the public profile representation.
"""

from __future__ import annotations

import ipaddress
import os
import socket
from datetime import datetime, timezone
from threading import RLock
from typing import Any
from uuid import uuid4
from urllib.parse import urlparse

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import Boolean, DateTime, String, Text, create_engine, select
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


ALLOWED_DIALECTS = {"sqlite", "postgresql", "mysql"}
LOCAL_DB_URI = "sqlite:///data/local.db"


class ConnectionError(ValueError):
    """Raised when a connection profile is invalid or unavailable."""


class Base(DeclarativeBase):
    pass


class ConnectionProfile(Base):
    __tablename__ = "connection_profiles"

    connection_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_id: Mapped[str] = mapped_column(String(255), index=True)
    name: Mapped[str] = mapped_column(String(120))
    dialect: Mapped[str] = mapped_column(String(30))
    encrypted_uri: Mapped[str] = mapped_column(Text)
    provider_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_health_check: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


