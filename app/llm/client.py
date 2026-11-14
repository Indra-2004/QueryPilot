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

def _fernet() -> Fernet:
    key = os.getenv("SECRETS_ENCRYPTION_KEY") or os.getenv("CONNECTION_ENCRYPTION_KEY")
    if not key: raise ProviderError("secrets_not_configured", "SECRETS_ENCRYPTION_KEY is not configured")
    try: return Fernet(key.encode())
    except Exception as exc: raise ProviderError("invalid_secrets_key", "Configured secrets key is invalid") from exc

def encrypt_secret(value: str) -> str:
    if not value: raise ValueError("secret cannot be empty")
    return _fernet().encrypt(value.encode()).decode()

def decrypt_secret(value: str) -> str:
    try: return _fernet().decrypt(value.encode()).decode()
    except (InvalidToken, UnicodeDecodeError) as exc: raise ProviderError("invalid_secret", "Stored provider secret cannot be decrypted") from exc

def validate_base_url(base_url: str | None) -> str | None:
    if not base_url: return None
    parsed = urlparse(base_url)
    if parsed.scheme != "https" or not parsed.netloc: raise ProviderError("invalid_base_url", "Custom provider URL must be an HTTPS URL")
    host = (parsed.hostname or "").lower()
    if host in {"localhost", "127.0.0.1", "0.0.0.0", "::1", "169.254.169.254"} or host.endswith(".local"): raise ProviderError("unsafe_base_url", "Custom provider URL targets a private host")
    return base_url.rstrip("/")

