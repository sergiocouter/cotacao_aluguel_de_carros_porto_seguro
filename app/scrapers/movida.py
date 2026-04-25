from __future__ import annotations

import re
from typing import Any

from app.constants import (
    DEFAULT_USER_AGENT,
    MOVIDA_MAINTENANCE_PATTERNS,
    MOVIDA_NAME,
    MOVIDA_RESERVATION_URL,
    MOVIDA_SELECTORS,
    MOVIDA_STORE_URL,
    MOVIDA_URL,
)
from app.models import QuoteResult
from app.scrapers.base_scraper import BaseScraper


class MovidaScraper(BaseScraper):
    provider_name = MOVIDA_NAME
    provider_slug = "movida"
    start_urls = (MOVIDA_URL, MOVIDA_RESERVATION_URL)
    selectors = MOVIDA_SELECTORS

    @property
    def user_agent(self) -> str | None:
        return DEFAULT_USER_AGENT

    def page_is_available(self, page: Any) -> bool:
        page_text = self.get_page_text(page)
        return not any(pattern.search(page_text) for pattern in MOVIDA_MAINTENANCE_PATTERNS)

    def scrape(self, page: Any, result: QuoteResult) -> QuoteResult:
        if not self.page_is_available(page):
            raise RuntimeError("Site da Movida aparenta estar em manutencao no momento da coleta.")

        self._ensure_reservation_area(page)
        selected_pickup, _ = self.fill_standard_quote_form(page)
        self.wait_for_results(page)

        addons_cleared, addon_observations = self.clear_optional_addons(page)
        result.addons_cleared = addons_cleared
        result.observations.extend(addon_observations)
        result.final_url = page.url

        agency_name = self.extract_agency_name(page, selected_hint=selected_pickup)
        if agency_name is None:
            agency_name = self._fallback_store_name(page) or "PORTO SEGURO AEROPORTO"

        options = self.parse_result_cards(page)
        self.capture_success_screenshot(page, result)
        return self.finalize_result(result, options, agency_name)

    def _ensure_reservation_area(self, page: Any) -> None:
        if self._has_pickup_input(page):
            return

        try:
            page.goto(MOVIDA_RESERVATION_URL, wait_until="domcontentloaded")
            self._wait_for_page(page)
        except Exception:
            pass

        if self._has_pickup_input(page):
            return

        raise RuntimeError("Area de reserva da Movida nao ficou acessivel para automacao.")

    def _fallback_store_name(self, page: Any) -> str | None:
        try:
            temp_page = page.context.new_page()
            temp_page.goto(MOVIDA_STORE_URL, wait_until="domcontentloaded")
            self._wait_for_page(temp_page)
            text = temp_page.locator("body").inner_text()
            temp_page.close()
        except Exception:
            return None

        for line in text.splitlines():
            if re.search(r"porto seguro.*aeroporto|aeroporto.*porto seguro", line, re.I):
                return line.strip()
        return None

    def _has_pickup_input(self, page: Any) -> bool:
        locator = page.locator("input[placeholder*='retirada'], input[name*='pickup'], input[name*='agency']")
        try:
            return locator.count() > 0
        except Exception:
            return False
