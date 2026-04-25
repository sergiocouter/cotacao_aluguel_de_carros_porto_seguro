from __future__ import annotations

import logging
from pathlib import Path

import pytest

from app.config import AppConfig
from app.models import QuoteRequest


@pytest.fixture()
def quote_request() -> QuoteRequest:
    return QuoteRequest(
        pickup_location="Aeroporto de Porto Seguro",
        pickup_date="12/09/2026",
        pickup_time="14:00",
        return_date="19/09/2026",
        return_time="11:00",
    )


@pytest.fixture()
def app_config(tmp_path: Path, quote_request: QuoteRequest) -> AppConfig:
    logs_dir = tmp_path / "logs"
    output_dir = tmp_path / "output"
    screenshots_dir = output_dir / "screenshots"
    errors_dir = output_dir / "errors"
    logs_dir.mkdir(parents=True, exist_ok=True)
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    errors_dir.mkdir(parents=True, exist_ok=True)

    return AppConfig(
        base_dir=tmp_path,
        telegram_bot_token=None,
        telegram_chat_id=None,
        quote_request=quote_request,
        headless=True,
        timezone="America/Sao_Paulo",
        playwright_timeout_ms=1000,
        max_retries=1,
        screenshot_full_page=True,
        logs_dir=logs_dir,
        output_dir=output_dir,
        screenshots_dir=screenshots_dir,
        errors_dir=errors_dir,
        log_file=logs_dir / "app.log",
        latest_json_file=output_dir / "latest_quote.json",
        latest_markdown_file=output_dir / "latest_quote.md",
    )


@pytest.fixture()
def test_logger() -> logging.Logger:
    logger = logging.getLogger("tests")
    logger.handlers.clear()
    logger.propagate = False
    return logger

