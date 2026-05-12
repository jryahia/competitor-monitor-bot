"""
config.py — Environment-based configuration via python-dotenv.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    telegram_bot_token: str
    telegram_chat_id: str
    openai_api_key: str
    competitor_urls: list[str]
    state_file: Path
    check_interval_hours: float
    price_drop_threshold: float

    @classmethod
    def from_env(cls) -> "Config":
        """Load and validate configuration from environment variables."""
        token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
        openai_key = os.environ.get("OPENAI_API_KEY", "")

        raw_urls = os.environ.get("COMPETITOR_URLS", "")
        urls = [u.strip() for u in raw_urls.split(",") if u.strip()][:5]

        if not token:
            raise ValueError("TELEGRAM_BOT_TOKEN is required")
        if not chat_id:
            raise ValueError("TELEGRAM_CHAT_ID is required")
        if not openai_key:
            raise ValueError("OPENAI_API_KEY is required")
        if not urls:
            raise ValueError("COMPETITOR_URLS must contain at least one URL")

        return cls(
            telegram_bot_token=token,
            telegram_chat_id=chat_id,
            openai_api_key=openai_key,
            competitor_urls=urls,
            state_file=Path(os.environ.get("STATE_FILE", "state.json")),
            check_interval_hours=float(os.environ.get("CHECK_INTERVAL_HOURS", "24")),
            price_drop_threshold=float(os.environ.get("PRICE_DROP_THRESHOLD", "0.10")),
        )
