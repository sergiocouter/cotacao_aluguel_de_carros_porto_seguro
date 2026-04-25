from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from app.models import QuoteRequest
from app.utils.helpers import ensure_directory, parse_bool, parse_int


@dataclass(slots=True)
class AppConfig:
    base_dir: Path
    telegram_bot_token: str | None
    telegram_chat_id: str | None
    quote_request: QuoteRequest
    headless: bool
    timezone: str
    playwright_timeout_ms: int
    max_retries: int
    screenshot_full_page: bool
    logs_dir: Path
    output_dir: Path
    screenshots_dir: Path
    errors_dir: Path
    log_file: Path
    latest_json_file: Path
    latest_markdown_file: Path

    @classmethod
    def load(cls, base_dir: str | Path | None = None) -> "AppConfig":
        root = Path(base_dir or Path(__file__).resolve().parent.parent).resolve()
        load_dotenv(root / ".env")

        logs_dir = ensure_directory(root / "logs")
        output_dir = ensure_directory(root / "output")
        screenshots_dir = ensure_directory(output_dir / "screenshots")
        errors_dir = ensure_directory(output_dir / "errors")

        request = QuoteRequest(
            pickup_location=os.getenv("RENTAL_PICKUP_LOCATION", "Aeroporto de Porto Seguro"),
            pickup_date=os.getenv("RENTAL_PICKUP_DATE", "12/09/2026"),
            pickup_time=os.getenv("RENTAL_PICKUP_TIME", "14:00"),
            return_date=os.getenv("RENTAL_RETURN_DATE", "19/09/2026"),
            return_time=os.getenv("RENTAL_RETURN_TIME", "11:00"),
        )

        return cls(
            base_dir=root,
            telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
            telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID"),
            quote_request=request,
            headless=parse_bool(os.getenv("HEADLESS"), default=True),
            timezone=os.getenv("TIMEZONE", "America/Sao_Paulo"),
            playwright_timeout_ms=parse_int(os.getenv("PLAYWRIGHT_TIMEOUT_MS"), 45000),
            max_retries=max(1, parse_int(os.getenv("MAX_RETRIES"), 2)),
            screenshot_full_page=parse_bool(
                os.getenv("SCREENSHOT_FULL_PAGE"),
                default=True,
            ),
            logs_dir=logs_dir,
            output_dir=output_dir,
            screenshots_dir=screenshots_dir,
            errors_dir=errors_dir,
            log_file=logs_dir / "app.log",
            latest_json_file=output_dir / "latest_quote.json",
            latest_markdown_file=output_dir / "latest_quote.md",
        )

