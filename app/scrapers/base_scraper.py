from __future__ import annotations

import re
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Sequence

from zoneinfo import ZoneInfo

from app.config import AppConfig
from app.constants import OBSERVATION_KEYWORDS, OPTIONAL_ADDON_KEYWORDS, POLICY_KEYWORDS
from app.models import CarOption, QuoteResult
from app.services.screenshot_service import ScreenshotService
from app.utils.helpers import (
    SelectorSpec,
    build_locator,
    click_with_fallback,
    fill_nth_with_fallback,
    fill_with_fallback,
    find_first_present,
    find_first_visible,
    is_airport_location,
    normalize_for_match,
    safe_text,
)
from app.utils.parsers import (
    extract_brl_values,
    looks_like_daily_price,
    looks_like_group_line,
    parse_brl_price,
    split_visible_lines,
)


class BaseScraper(ABC):
    provider_name = "base"
    provider_slug = "base"
    start_urls: Sequence[str] = ()
    selectors: dict[str, list[SelectorSpec]] = {}

    def __init__(self, config: AppConfig, logger: Any, screenshot_service: ScreenshotService) -> None:
        self.config = config
        self.logger = logger
        self.screenshot_service = screenshot_service

    def run(self, browser: Any) -> QuoteResult:
        result = QuoteResult(provider=self.provider_name, collected_at=self._now_text())

        for attempt in range(1, self.config.max_retries + 1):
            context = None
            page = None
            try:
                self.logger.info("[%s] Iniciando tentativa %s/%s", self.provider_name, attempt, self.config.max_retries)
                context_kwargs = dict(
                    locale="pt-BR",
                    timezone_id=self.config.timezone,
                    viewport={"width": 1440, "height": 1200},
                )
                if self.user_agent:
                    context_kwargs["user_agent"] = self.user_agent
                context = browser.new_context(**context_kwargs)
                page = context.new_page()
                page.set_default_timeout(self.config.playwright_timeout_ms)
                page.set_default_navigation_timeout(self.config.playwright_timeout_ms)

                initial_url = self.open_start_page(page)
                self.logger.info("[%s] URL inicial carregada: %s", self.provider_name, initial_url)
                self.accept_cookies(page)

                result = self.scrape(page, result)
                result.collected_at = self._now_text()
                return result
            except Exception as exc:
                self.logger.exception("[%s] Falha na tentativa %s: %s", self.provider_name, attempt, exc)
                result.success = False
                result.error = str(exc)
                result.collected_at = self._now_text()
                artifacts = self.screenshot_service.save_error_artifacts(self.provider_slug, page)
                result.error_artifacts = list(dict.fromkeys([*result.error_artifacts, *artifacts]))
                if attempt >= self.config.max_retries:
                    return result
            finally:
                try:
                    if page is not None:
                        page.close()
                except Exception:
                    pass
                try:
                    if context is not None:
                        context.close()
                except Exception:
                    pass

        return result

    @property
    def user_agent(self) -> str | None:
        return None

    def open_start_page(self, page: Any) -> str:
        last_error: Exception | None = None
        for url in self.start_urls:
            try:
                page.goto(url, wait_until="domcontentloaded")
                self._wait_for_page(page)
                if self.page_is_available(page):
                    return url
                self.logger.warning("[%s] URL indisponivel ou inadequada: %s", self.provider_name, url)
            except Exception as exc:
                last_error = exc
                self.logger.warning("[%s] Erro ao abrir %s: %s", self.provider_name, url, exc)
        if last_error:
            raise last_error
        raise RuntimeError(f"Nenhuma URL inicial funcionou para {self.provider_name}")

    def _wait_for_page(self, page: Any) -> None:
        try:
            page.wait_for_load_state("networkidle", timeout=min(self.config.playwright_timeout_ms, 8000))
        except Exception:
            pass
        page.wait_for_timeout(1500)

    def accept_cookies(self, page: Any) -> None:
        if self.selectors.get("cookie_accept"):
            if click_with_fallback(page, self.selectors["cookie_accept"], timeout_ms=3000):
                self.logger.info("[%s] Banner de cookies fechado.", self.provider_name)

    def page_is_available(self, page: Any) -> bool:
        return True

    @abstractmethod
    def scrape(self, page: Any, result: QuoteResult) -> QuoteResult:
        raise NotImplementedError

    def fill_standard_quote_form(self, page: Any) -> tuple[str | None, str | None]:
        request = self.config.quote_request

        if not fill_with_fallback(
            page,
            self.selectors["pickup_location_input"],
            request.pickup_location,
            timeout_ms=5000,
        ):
            raise RuntimeError("Campo de retirada nao foi encontrado.")

        selected_pickup = self.select_airport_suggestion(page)

        return_location_filled = fill_with_fallback(
            page,
            self.selectors.get("return_location_input", []),
            request.pickup_location,
            timeout_ms=3000,
        )
        selected_return = None
        if return_location_filled:
            selected_return = self.select_airport_suggestion(page)

        if not self.fill_date_inputs(page):
            raise RuntimeError("Nao foi possivel preencher as datas da cotacao.")

        if not self.fill_time_inputs(page):
            raise RuntimeError("Nao foi possivel preencher os horarios da cotacao.")

        if not click_with_fallback(page, self.selectors["search_button"], timeout_ms=5000):
            raise RuntimeError("Botao de busca/cotacao nao foi encontrado.")

        self._wait_for_page(page)
        return selected_pickup, selected_return

    def fill_date_inputs(self, page: Any) -> bool:
        request = self.config.quote_request
        selectors = self.selectors.get("date_inputs") or self.selectors.get("pickup_date_input", [])
        pickup_candidates = self._date_candidates(request.pickup_date)
        return_candidates = self._date_candidates(request.return_date)
        return self._fill_indexed_values(page, selectors, 0, pickup_candidates) and self._fill_indexed_values(
            page,
            selectors,
            1,
            return_candidates,
        )

    def fill_time_inputs(self, page: Any) -> bool:
        request = self.config.quote_request
        selectors = self.selectors.get("time_inputs") or self.selectors.get("pickup_time_input", [])
        return self._fill_indexed_values(page, selectors, 0, [request.pickup_time]) and self._fill_indexed_values(
            page,
            selectors,
            1,
            [request.return_time],
        )

    def _fill_indexed_values(
        self,
        page: Any,
        selectors: Sequence[SelectorSpec],
        index: int,
        candidate_values: Sequence[str],
    ) -> bool:
        for candidate in candidate_values:
            if fill_nth_with_fallback(
                page,
                selectors,
                index=index,
                value=candidate,
                timeout_ms=3000,
            ):
                return True

            locator = self._find_indexed_locator(page, selectors, index)
            if locator is None:
                continue

            try:
                locator.evaluate(
                    """(element, value) => {
                        element.value = value;
                        element.dispatchEvent(new Event('input', { bubbles: true }));
                        element.dispatchEvent(new Event('change', { bubbles: true }));
                    }""",
                    candidate,
                )
                return True
            except Exception:
                continue
        return False

    def _find_indexed_locator(
        self,
        page: Any,
        selectors: Sequence[SelectorSpec],
        index: int,
    ) -> Any | None:
        for selector in selectors:
            try:
                locator = build_locator(page, selector)
                if hasattr(locator, "count") and locator.count() > index:
                    return locator.nth(index)
            except Exception:
                continue
        return None

    def _date_candidates(self, br_date: str) -> list[str]:
        parsed = datetime.strptime(br_date, "%d/%m/%Y")
        return [br_date, parsed.strftime("%Y-%m-%d")]

    def select_airport_suggestion(self, page: Any) -> str | None:
        patterns = (
            re.compile(r"porto seguro.*aeroporto", re.I),
            re.compile(r"aeroporto.*porto seguro", re.I),
            re.compile(r"porto seguro.*airport", re.I),
            re.compile(r"airport.*porto seguro", re.I),
            re.compile(r"porto seguro.*bps", re.I),
        )
        for selector in self.selectors.get("location_suggestions", []):
            try:
                locator = build_locator(page, selector)
                count = min(locator.count(), 15) if hasattr(locator, "count") else 0
                for index in range(count):
                    candidate = locator.nth(index)
                    text = safe_text(candidate) or ""
                    if not text:
                        continue
                    if any(pattern.search(text) for pattern in patterns):
                        candidate.click()
                        self.logger.info("[%s] Sugestao de agencia selecionada: %s", self.provider_name, text)
                        self._wait_for_page(page)
                        return text
            except Exception:
                continue
        return None

    def wait_for_results(self, page: Any) -> None:
        for _ in range(8):
            locator = find_first_present(page, self.selectors["result_cards"])
            if locator is not None:
                try:
                    if locator.count() > 0:
                        return
                except Exception:
                    return
            page.wait_for_timeout(1000)

    def clear_optional_addons(self, page: Any) -> tuple[bool, list[str]]:
        observations: list[str] = []
        action_selectors = [
            {"kind": "role", "role": "button", "name": re.compile(r"continuar sem|sem adicionais|nao quero", re.I)},
            {"kind": "text", "text": re.compile(r"continuar sem|sem adicionais|nao quero", re.I)},
            {"kind": "role", "role": "button", "name": re.compile(r"remover|desmarcar", re.I)},
            {"kind": "text", "text": re.compile(r"remover|desmarcar", re.I)},
        ]

        for selector in action_selectors:
            if click_with_fallback(page, [selector], timeout_ms=1500):
                observations.append("Fluxo exibiu opcionais e a automacao tentou seguir sem extras.")
                self._wait_for_page(page)
                return True, observations

        observations.append(
            "Nao foi possivel validar de forma conclusiva a ausencia de adicionais opcionais no fluxo visivel."
        )
        return False, observations

    def extract_agency_name(self, page: Any, selected_hint: str | None = None) -> str | None:
        candidates: list[str] = []
        if selected_hint:
            candidates.append(selected_hint)

        locator = find_first_visible(page, self.selectors.get("agency_name", []), timeout_ms=2000)
        if locator is not None:
            text = safe_text(locator)
            if text:
                candidates.append(text)

        body_lines = split_visible_lines(self.get_page_text(page))
        for line in body_lines:
            if is_airport_location(line):
                candidates.append(line)

        if not candidates:
            return None
        return max(candidates, key=len)

    def get_page_text(self, page: Any) -> str:
        try:
            return page.locator("body").inner_text()
        except Exception:
            return ""

    def parse_result_cards(self, page: Any) -> list[CarOption]:
        cards_locator = find_first_present(page, self.selectors["result_cards"])
        if cards_locator is None:
            return []

        options: list[CarOption] = []
        unique_keys: set[str] = set()

        try:
            total_cards = min(cards_locator.count(), 20)
        except Exception:
            total_cards = 0

        for index in range(total_cards):
            try:
                card = cards_locator.nth(index)
                text = safe_text(card)
                if not text or "R$" not in text:
                    continue
                option = self.option_from_card_text(text, page.url)
                if option.total_price is None:
                    continue
                key = normalize_for_match(f"{option.name}|{option.group}|{option.total_price_text}")
                if key in unique_keys:
                    continue
                unique_keys.add(key)
                options.append(option)
            except Exception:
                continue
        return sorted(options, key=lambda item: item.total_price or float("inf"))

    def option_from_card_text(self, text: str, detail_url: str) -> CarOption:
        lines = split_visible_lines(text)
        line_prices = [(line, parse_brl_price(line)) for line in lines if parse_brl_price(line) is not None]
        all_prices = extract_brl_values(text)

        daily_price_text = next((line for line, _ in line_prices if looks_like_daily_price(line)), None)
        total_price_text, total_price = self._select_total_price(line_prices, all_prices)

        group = next((line for line in lines if looks_like_group_line(line)), None)
        name = self._select_vehicle_name(lines)
        policies = [line for line in lines if any(keyword in normalize_for_match(line) for keyword in POLICY_KEYWORDS)]
        observations = [
            line for line in lines if any(keyword in normalize_for_match(line) for keyword in OBSERVATION_KEYWORDS)
        ]

        return CarOption(
            provider=self.provider_name,
            name=name,
            group=group,
            total_price=total_price,
            total_price_text=total_price_text,
            daily_price_text=daily_price_text,
            policies=policies[:5],
            observations=observations[:5],
            detail_url=detail_url,
            raw_text=text,
        )

    def _select_total_price(
        self,
        line_prices: Sequence[tuple[str, float | None]],
        all_prices: Sequence[tuple[str, float]],
    ) -> tuple[str | None, float | None]:
        preferred = (
            "total",
            "final",
            "reserva",
            "locacao",
            "pacote",
            "periodo",
        )
        for line, price in line_prices:
            normalized = normalize_for_match(line)
            if any(keyword in normalized for keyword in preferred):
                return line, price

        if all_prices:
            raw, value = max(all_prices, key=lambda item: item[1])
            return raw, value

        return None, None

    def _select_vehicle_name(self, lines: Sequence[str]) -> str:
        skip_keywords = (
            "r$",
            "porto seguro",
            "aeroporto",
            "buscar",
            "continuar",
            "remover",
            "quilometragem",
            "franquia",
        )
        for line in lines:
            normalized = normalize_for_match(line)
            if not normalized:
                continue
            if any(keyword in normalized for keyword in skip_keywords):
                continue
            if looks_like_group_line(line) or looks_like_daily_price(line):
                continue
            return line
        return lines[0] if lines else "Veiculo sem nome identificado"

    def capture_success_screenshot(self, page: Any, result: QuoteResult) -> None:
        screenshot_path = self.screenshot_service.build_quote_screenshot_path(
            self.provider_slug,
            self.config.quote_request,
        )
        result_section = find_first_visible(page, self.selectors.get("result_section", []), timeout_ms=1000)
        saved_path = self.screenshot_service.save_page_screenshot(page, screenshot_path, locator=result_section)
        if saved_path:
            result.screenshot_paths.append(saved_path)

    def finalize_result(self, result: QuoteResult, options: list[CarOption], agency_name: str | None) -> QuoteResult:
        result.agency_name = agency_name
        result.airport_validated = is_airport_location(agency_name)
        result.options = options[:3]

        if not result.airport_validated:
            result.success = False
            result.error = result.error or "Agencia selecionada nao foi validada como aeroporto."
            result.observations.append(
                f"Agencia retornada pelo site nao parece ser do aeroporto: {agency_name or 'nao identificada'}."
            )
            return result

        if not options:
            result.success = False
            result.error = result.error or "Nenhuma opcao de veiculo com preco visivel foi encontrada."
            return result

        if len(options) < 3:
            result.observations.append(f"Apenas {len(options)} opcao(oes) com preco visivel foram encontradas.")

        result.success = True
        return result

    def _now_text(self) -> str:
        return datetime.now(ZoneInfo(self.config.timezone)).strftime("%d/%m/%Y %H:%M:%S")
