from __future__ import annotations

import time
import unicodedata
from pathlib import Path
from typing import Any, Sequence

from app.constants import AIRPORT_KEYWORDS, PORTO_SEGURO_KEYWORDS

SelectorSpec = dict[str, Any]


def parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def parse_int(value: str | None, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def ensure_directory(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def normalize_for_match(value: str | None) -> str:
    if not value:
        return ""
    normalized = unicodedata.normalize("NFKD", value)
    without_accents = "".join(char for char in normalized if not unicodedata.combining(char))
    return " ".join(without_accents.lower().strip().split())


def is_airport_location(value: str | None) -> bool:
    normalized = normalize_for_match(value)
    if not normalized:
        return False
    has_city = any(keyword in normalized for keyword in PORTO_SEGURO_KEYWORDS)
    has_airport = any(keyword in normalized for keyword in AIRPORT_KEYWORDS)
    return has_city and has_airport


def dedupe_preserve_order(values: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        key = normalize_for_match(value)
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(value.strip())
    return deduped


def first_existing_path(paths: Sequence[str | Path | None]) -> str | None:
    for path in paths:
        if path and Path(path).exists():
            return str(path)
    return None


def build_locator(target: Any, selector: SelectorSpec) -> Any:
    kind = selector["kind"]
    if kind == "role":
        return target.get_by_role(
            selector["role"],
            name=selector.get("name"),
            exact=selector.get("exact", False),
        )
    if kind == "label":
        return target.get_by_label(selector["text"], exact=selector.get("exact", False))
    if kind == "placeholder":
        return target.get_by_placeholder(selector["text"], exact=selector.get("exact", False))
    if kind == "text":
        return target.get_by_text(selector["text"], exact=selector.get("exact", False))
    if kind == "test_id":
        return target.get_by_test_id(selector["text"])
    if kind == "css":
        return target.locator(selector["text"])
    if kind == "xpath":
        return target.locator(f"xpath={selector['text']}")
    raise ValueError(f"Tipo de seletor nao suportado: {kind}")


def _resolve_first(locator: Any) -> Any:
    first = getattr(locator, "first", None)
    return first if first is not None else locator


def _locator_has_nodes(locator: Any) -> bool:
    try:
        return locator.count() > 0
    except Exception:
        try:
            return bool(locator.is_visible())
        except Exception:
            return False


def _locator_is_visible(locator: Any) -> bool:
    try:
        return bool(locator.is_visible())
    except Exception:
        return _locator_has_nodes(locator)


def find_first_present(target: Any, selectors: Sequence[SelectorSpec]) -> Any | None:
    for selector in selectors:
        try:
            locator = _resolve_first(build_locator(target, selector))
            if _locator_has_nodes(locator):
                return locator
        except Exception:
            continue
    return None


def find_nth_present(target: Any, selectors: Sequence[SelectorSpec], index: int) -> Any | None:
    for selector in selectors:
        try:
            locator = build_locator(target, selector)
            if hasattr(locator, "count") and locator.count() > index:
                candidate = locator.nth(index) if hasattr(locator, "nth") else _resolve_first(locator)
                if _locator_has_nodes(candidate):
                    return candidate
        except Exception:
            continue
    return None


def find_first_visible(
    target: Any,
    selectors: Sequence[SelectorSpec],
    timeout_ms: int = 0,
) -> Any | None:
    for selector in selectors:
        try:
            locator = _resolve_first(build_locator(target, selector))
            if timeout_ms and hasattr(locator, "wait_for"):
                try:
                    locator.wait_for(state="visible", timeout=timeout_ms)
                except Exception:
                    pass
            if _locator_is_visible(locator):
                return locator
        except Exception:
            continue
    return None


def find_nth_visible(
    target: Any,
    selectors: Sequence[SelectorSpec],
    index: int,
    timeout_ms: int = 0,
) -> Any | None:
    for selector in selectors:
        try:
            locator = build_locator(target, selector)
            if hasattr(locator, "count") and locator.count() > index:
                candidate = locator.nth(index) if hasattr(locator, "nth") else _resolve_first(locator)
                if timeout_ms and hasattr(candidate, "wait_for"):
                    try:
                        candidate.wait_for(state="visible", timeout=timeout_ms)
                    except Exception:
                        pass
                if _locator_is_visible(candidate):
                    return candidate
        except Exception:
            continue
    return None


def click_with_fallback(
    target: Any,
    selectors: Sequence[SelectorSpec],
    timeout_ms: int = 0,
) -> bool:
    locator = find_first_visible(target, selectors, timeout_ms=timeout_ms)
    if not locator:
        return False
    try:
        if hasattr(locator, "scroll_into_view_if_needed"):
            locator.scroll_into_view_if_needed()
        locator.click()
        return True
    except Exception:
        return False


def click_nth_with_fallback(
    target: Any,
    selectors: Sequence[SelectorSpec],
    index: int,
    timeout_ms: int = 0,
) -> bool:
    locator = find_nth_visible(target, selectors, index=index, timeout_ms=timeout_ms)
    if not locator:
        return False
    try:
        if hasattr(locator, "scroll_into_view_if_needed"):
            locator.scroll_into_view_if_needed()
        locator.click()
        return True
    except Exception:
        return False


def fill_with_fallback(
    target: Any,
    selectors: Sequence[SelectorSpec],
    value: str,
    timeout_ms: int = 0,
) -> bool:
    locator = find_first_visible(target, selectors, timeout_ms=timeout_ms)
    if not locator:
        return False
    try:
        locator.fill(value)
        return True
    except Exception:
        return False


def fill_nth_with_fallback(
    target: Any,
    selectors: Sequence[SelectorSpec],
    index: int,
    value: str,
    timeout_ms: int = 0,
) -> bool:
    locator = find_nth_visible(target, selectors, index=index, timeout_ms=timeout_ms)
    if not locator:
        return False
    try:
        locator.fill(value)
        return True
    except Exception:
        return False


def safe_text(locator: Any) -> str | None:
    for attr in ("inner_text", "text_content", "input_value"):
        method = getattr(locator, attr, None)
        if not method:
            continue
        try:
            value = method()
        except Exception:
            continue
        if value:
            return str(value).strip()
    return None


def wait_for_any(timeout_ms: int) -> None:
    if timeout_ms <= 0:
        return
    time.sleep(timeout_ms / 1000)
