from __future__ import annotations

import re
from typing import Any

from app.constants import DEFAULT_USER_AGENT, LOCALIZA_AIRPORT_URL, LOCALIZA_NAME, LOCALIZA_SELECTORS, LOCALIZA_URL
from app.models import QuoteResult
from app.scrapers.base_scraper import BaseScraper
from app.utils.helpers import click_with_fallback


class LocalizaScraper(BaseScraper):
    provider_name = LOCALIZA_NAME
    provider_slug = "localiza"
    start_urls = (LOCALIZA_AIRPORT_URL, LOCALIZA_URL)
    selectors = LOCALIZA_SELECTORS

    @property
    def user_agent(self) -> str | None:
        return DEFAULT_USER_AGENT

    def scrape(self, page: Any, result: QuoteResult) -> QuoteResult:
        page_text = self.get_page_text(page)
        if "Localiza" not in page_text:
            raise RuntimeError("Pagina inicial da Localiza nao carregou como esperado.")

        self._maybe_open_quote_form(page)
        selected_pickup, _ = self.fill_standard_quote_form(page)
        self.wait_for_results(page)

        addons_cleared, addon_observations = self.clear_optional_addons(page)
        result.addons_cleared = addons_cleared
        result.observations.extend(addon_observations)
        result.final_url = page.url

        agency_name = self.extract_agency_name(page, selected_hint=selected_pickup) or "AGENCIA AEROPORTO PORTO SEGURO"
        options = self.parse_result_cards(page)
        self.capture_success_screenshot(page, result)
        return self.finalize_result(result, options, agency_name)

    def _maybe_open_quote_form(self, page: Any) -> None:
        if self._has_pickup_input(page):
            return

        reserve_selectors = [
            {"kind": "role", "role": "button", "name": re.compile(r"reservar", re.I)},
            {"kind": "text", "text": re.compile(r"reservar", re.I)},
        ]
        if click_with_fallback(page, reserve_selectors, timeout_ms=3000):
            self._wait_for_page(page)

    def _has_pickup_input(self, page: Any) -> bool:
        locator = page.locator("input[placeholder*='retirar'], input[name*='pickup'], input[id*='pickup']")
        try:
            return locator.count() > 0
        except Exception:
            return False
