from __future__ import annotations

from app.models import CarOption, QuoteResult
from app.scrapers.base_scraper import BaseScraper
from app.services.report_service import ReportService
from app.services.screenshot_service import ScreenshotService


class DummyScraper(BaseScraper):
    provider_name = "Dummy"
    provider_slug = "dummy"
    start_urls = ()
    selectors = {}

    def scrape(self, page, result):  # noqa: ANN001, D401
        return result


def test_select_cheapest_options_returns_three_lowest(app_config, test_logger) -> None:
    service = ReportService(app_config, test_logger)
    options = [
        CarOption(provider="Localiza", name="A", total_price=700.0, total_price_text="R$ 700,00"),
        CarOption(provider="Localiza", name="B", total_price=300.0, total_price_text="R$ 300,00"),
        CarOption(provider="Localiza", name="C", total_price=500.0, total_price_text="R$ 500,00"),
        CarOption(provider="Localiza", name="D", total_price=200.0, total_price_text="R$ 200,00"),
    ]

    selected = service.select_cheapest_options(options)

    assert [option.name for option in selected] == ["D", "B", "C"]


def test_message_handles_one_provider_failure(app_config, test_logger) -> None:
    service = ReportService(app_config, test_logger)
    localiza = QuoteResult(
        provider="Localiza",
        success=True,
        agency_name="Aeroporto de Porto Seguro",
        airport_validated=True,
        options=[
            CarOption(provider="Localiza", name="Fiat Mobi", total_price=400.0, total_price_text="R$ 400,00"),
            CarOption(provider="Localiza", name="HB20", total_price=450.0, total_price_text="R$ 450,00"),
        ],
    )
    movida = QuoteResult(
        provider="Movida",
        success=False,
        agency_name="Nao identificada",
        error="Site indisponivel",
    )

    summary = service.build_run_summary(localiza, movida, errors=["Movida falhou na coleta."])
    message = service.build_telegram_message(summary)

    assert "🏢 Localiza" in message
    assert "1. Fiat Mobi — R$ 400,00" in message
    assert "🏢 Movida" in message
    assert "Falha: Site indisponivel" in message
    assert "- Movida falhou na coleta." in message


def test_invalid_non_airport_agency_marks_collection_invalid(app_config, test_logger) -> None:
    screenshot_service = ScreenshotService(app_config, test_logger)
    scraper = DummyScraper(app_config, test_logger, screenshot_service)
    result = QuoteResult(provider="Dummy")
    options = [CarOption(provider="Dummy", name="Carro X", total_price=123.0, total_price_text="R$ 123,00")]

    finalized = scraper.finalize_result(result, options, "Porto Seguro Centro")

    assert finalized.success is False
    assert finalized.airport_validated is False
    assert "nao foi validada como aeroporto" in (finalized.error or "")


def test_persist_outputs_when_one_provider_fails(app_config, test_logger) -> None:
    service = ReportService(app_config, test_logger)
    localiza = QuoteResult(provider="Localiza", success=True, agency_name="Aeroporto de Porto Seguro", airport_validated=True)
    movida = QuoteResult(provider="Movida", success=False, error="Falha controlada")
    summary = service.build_run_summary(localiza, movida)

    service.persist_outputs(summary)

    assert app_config.latest_json_file.exists()
    assert app_config.latest_markdown_file.exists()

