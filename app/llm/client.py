"""Provider-neutral LLM construction and encrypted provider secrets."""
from __future__ import annotations
import os
from dataclasses import dataclass
from typing import Any, Mapping
from urllib.parse import urlparse
import yaml
from cryptography.fernet import Fernet, InvalidToken
from langchain_groq import ChatGroq
from app.core.config import settings
try:
    from langchain_openai import ChatOpenAI
except ImportError:
    ChatOpenAI = None
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    ChatGoogleGenerativeAI = None

class ProviderError(RuntimeError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)

@dataclass(frozen=True)
class ProviderProfile:
    provider_id: str
    owner_id: str
    name: str
    provider_type: str
    api_key: str
    model: str
    base_url: str | None = None
    enabled: bool = True

