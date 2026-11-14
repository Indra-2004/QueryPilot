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


def _fernet() -> Fernet:
    raw = os.environ.get("SECRETS_ENCRYPTION_KEY") or os.environ.get("CONNECTION_ENCRYPTION_KEY")
    if not raw:
        # Development fallback is intentionally process-stable only. Production
        # must provide a key or profiles cannot be recovered after restart.
        raw = Fernet.generate_key().decode()
        os.environ["SECRETS_ENCRYPTION_KEY"] = raw
    try:
        return Fernet(raw.encode() if isinstance(raw, str) else raw)
    except Exception as exc:
        raise ConnectionError("SECRETS_ENCRYPTION_KEY must be a valid Fernet key") from exc


def _store_engine() -> Engine:
    uri = os.environ.get("CONNECTION_STORE_URI", "sqlite:///data/connections.db")
    if uri.startswith("sqlite:///"):
        os.makedirs(os.path.dirname(uri.removeprefix("sqlite:///")) or ".", exist_ok=True)
    engine = create_engine(uri)
    Base.metadata.create_all(engine)
    return engine


_metadata_engine: Engine | None = None
_engines: dict[str, Engine] = {}
_lock = RLock()


def metadata_engine() -> Engine:
    global _metadata_engine
    with _lock:
        if _metadata_engine is None:
            _metadata_engine = _store_engine()
        return _metadata_engine


def _validate_uri(uri: str, *, allow_private_hosts: bool = False) -> str:
    if not uri or not uri.strip():
        raise ConnectionError("Database URI is required")
    try:
        parsed = make_url(uri)
    except Exception as exc:
        raise ConnectionError("Invalid database URI") from exc
    if parsed.drivername.split("+")[0] not in ALLOWED_DIALECTS:
        raise ConnectionError("Supported database types are SQLite, PostgreSQL, and MySQL")
    if parsed.drivername == "sqlite" or parsed.drivername.startswith("sqlite+"):
        return uri
    host = parsed.host
    if not host:
        raise ConnectionError("Database URI must include a host")
    if not allow_private_hosts:
        try:
            addresses = {item[4][0] for item in socket.getaddrinfo(host, parsed.port or 0, type=socket.SOCK_STREAM)}
            for address in addresses:
                ip = ipaddress.ip_address(address)
                if ip.is_loopback or ip.is_private or ip.is_link_local or ip.is_reserved or ip.is_unspecified:
                    raise ConnectionError("Private or local database hosts are not allowed")
        except socket.gaierror as exc:
            raise ConnectionError("Database host could not be resolved") from exc
    return uri


def _dialect(uri: str) -> str:
    return make_url(uri).drivername.split("+")[0]


def test_connection(uri: str, *, allow_private_hosts: bool = False) -> dict[str, Any]:
    validated = _validate_uri(uri, allow_private_hosts=allow_private_hosts)
    engine = create_engine(validated, pool_pre_ping=True, pool_recycle=1800)
    try:
        with engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1")
        return {"status": "ok", "dialect": _dialect(validated)}
    except SQLAlchemyError as exc:
        raise ConnectionError("Unable to connect to database") from exc
    finally:
        engine.dispose()


