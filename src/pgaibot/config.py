from __future__ import annotations

import os
from dataclasses import dataclass

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - keeps dry config checks usable before install
    load_dotenv = None


DEFAULT_TEST_NUMBER = "+18054398008"


@dataclass(frozen=True)
class Settings:
    twilio_account_sid: str
    twilio_auth_token: str
    twilio_from_number: str
    public_base_url: str = ""
    pg_test_number: str = DEFAULT_TEST_NUMBER
    openrouter_api_key: str = ""
    openrouter_model: str = "openai/gpt-4o-mini"


def load_settings() -> Settings:
    if load_dotenv:
        load_dotenv()

    return Settings(
        twilio_account_sid=_required_env("TWILIO_ACCOUNT_SID"),
        twilio_auth_token=_required_env("TWILIO_AUTH_TOKEN"),
        twilio_from_number=_required_env("TWILIO_FROM_NUMBER"),
        public_base_url=os.getenv("PUBLIC_BASE_URL", "").strip().rstrip("/"),
        pg_test_number=os.getenv("PG_TEST_NUMBER", DEFAULT_TEST_NUMBER),
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY", ""),
        openrouter_model=os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
    )


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ConfigError(f"Missing required environment variable: {name}")
    return value


class ConfigError(RuntimeError):
    pass
