import os

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from app.core.config import settings

_engine = None
LOCAL_DB_URI = "sqlite:///data/local.db"


def _candidate_uris() -> list[str]:
    uris: list[str] = []
    if settings.db_uri:
        uris.append(settings.db_uri)
    if LOCAL_DB_URI not in uris and os.path.exists("data/local.db"):
        uris.append(LOCAL_DB_URI)
    return uris

