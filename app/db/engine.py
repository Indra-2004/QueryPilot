import os

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from app.core.config import settings

_engine = None
LOCAL_DB_URI = "sqlite:///data/local.db"


