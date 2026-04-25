from __future__ import annotations

import sys
from pathlib import Path

from app.config import AppConfig
from app.constants import LOCALIZA_NAME, MOVIDA_NAME
from app.logger import setup_logger
from app.models import QuoteResult
from app.scrapers import LocalizaScraper, MovidaScraper
from app.services.report_service import ReportService
from app.services.screenshot_service import ScreenshotService
from app.services.telegram_service import TelegramService


def build_failure_result(provider: str, error_message: str) -> QuoteResult:
    return QuoteResult(provider=provider, success=False, error=error_message)


def gather_sendable_screenshots(result: QuoteResult) -> list[str]:
    candidates = list(result.screenshot_paths)
    candidates.extend(path for path in result.error_artifacts if Path(path).suffix.lower() == ".png")
    existing = [path for path in candidates if Path(path).exists()]
    deduped: list[str] = []
    for item in existing:
        if item not in deduped:
            deduped.append(item)
    return deduped[:1]


def run() -> int:
    config = AppConfig.load()
    logger = setup_logger(config.log_file)
    screenshot_service = ScreenshotService(config, logger)
    report_service = ReportService(config, logger)
    telegram_service = TelegramService(config.telegram_bot_token, config.telegram_chat_id, logger)

    localiza_result = build_failure_result(LOCALIZA_NAME, "Execucao nao iniciada.")
    movida_result = build_failure_result(MOVIDA_NAME, "Execucao nao iniciada.")
    general_errors: list[str] = []

    logger.info("Inicio da execucao da cotacao diaria.")
    logger.info("Local configurado para a coleta: %s", config.quote_request.pickup_location)

    try:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise RuntimeError(
                "Playwright nao esta instalado. Execute 'pip install -r requirements.txt' e "
                "'playwright install chromium'."
            ) from exc

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=config.headless)
            try:
                localiza_scraper = LocalizaScraper(config, logger, screenshot_service)
                movida_scraper = MovidaScraper(config, logger, screenshot_service)

                localiza_result = localiza_scraper.run(browser)
                movida_result = movida_scraper.run(browser)
            finally:
                browser.close()
    except Exception as exc:
        logger.exception("Falha geral na inicializacao da aplicacao: %s", exc)
        general_errors.append(str(exc))
        if localiza_result.error == "Execucao nao iniciada.":
            localiza_result = build_failure_result(LOCALIZA_NAME, str(exc))
        if movida_result.error == "Execucao nao iniciada.":
            movida_result = build_failure_result(MOVIDA_NAME, str(exc))

    localiza_result.options = report_service.select_cheapest_options(localiza_result.options)
    movida_result.options = report_service.select_cheapest_options(movida_result.options)

    summary = report_service.build_run_summary(localiza_result, movida_result, errors=general_errors)
    report_service.persist_outputs(summary)

    message = report_service.build_telegram_message(summary)
    telegram_service.send_message(message)

    for result in (localiza_result, movida_result):
        screenshots = gather_sendable_screenshots(result)
        if not screenshots:
            logger.warning("[%s] Nenhuma screenshot valida foi encontrada para envio.", result.provider)
            continue
        for screenshot in screenshots:
            telegram_service.send_photo(screenshot, caption=f"📸 Screenshot da cotacao - {result.provider}")

    logger.info("Execucao finalizada. Localiza=%s | Movida=%s", localiza_result.success, movida_result.success)
    if not localiza_result.success and not movida_result.success:
        return 1
    return 0


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
