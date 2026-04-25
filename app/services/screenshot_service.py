from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from zoneinfo import ZoneInfo

from app.config import AppConfig
from app.models import QuoteRequest
from app.utils.formatters import quote_window_slug
from app.utils.helpers import ensure_directory, first_existing_path


class ScreenshotService:
    def __init__(self, config: AppConfig, logger: Any) -> None:
        self.config = config
        self.logger = logger

    def build_quote_screenshot_path(self, provider: str, request: QuoteRequest) -> Path:
        filename = f"{provider.lower()}_{quote_window_slug(request)}.png"
        return ensure_directory(self.config.screenshots_dir) / filename

    def build_error_screenshot_path(self, provider: str) -> Path:
        timestamp = datetime.now(ZoneInfo(self.config.timezone)).strftime("%Y%m%d_%H%M%S")
        filename = f"{provider.lower()}_error_{timestamp}.png"
        return ensure_directory(self.config.errors_dir) / filename

    def build_error_html_path(self, provider: str) -> Path:
        timestamp = datetime.now(ZoneInfo(self.config.timezone)).strftime("%Y%m%d_%H%M%S")
        filename = f"{provider.lower()}_error_{timestamp}.html"
        return ensure_directory(self.config.errors_dir) / filename

    def save_page_screenshot(self, page: Any, path: Path, locator: Any | None = None) -> str | None:
        try:
            if locator is not None and not self.config.screenshot_full_page:
                locator.screenshot(path=str(path))
            else:
                page.screenshot(path=str(path), full_page=self.config.screenshot_full_page)
            return str(path)
        except Exception as exc:
            self.logger.warning("Falha ao salvar screenshot %s: %s", path, exc)
            return None

    def save_error_artifacts(self, provider: str, page: Any | None = None) -> list[str]:
        artifacts: list[str] = []
        if page is not None:
            screenshot_path = self.build_error_screenshot_path(provider)
            saved_screenshot = self.save_page_screenshot(page, screenshot_path)
            if saved_screenshot:
                artifacts.append(saved_screenshot)

            html_path = self.build_error_html_path(provider)
            try:
                html_path.write_text(page.content(), encoding="utf-8")
                artifacts.append(str(html_path))
            except Exception as exc:
                self.logger.warning("Falha ao salvar HTML de erro %s: %s", html_path, exc)
        return artifacts

    @staticmethod
    def choose_existing_screenshot(*paths: str | Path | None) -> str | None:
        return first_existing_path(paths)

