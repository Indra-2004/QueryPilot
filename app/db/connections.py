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


