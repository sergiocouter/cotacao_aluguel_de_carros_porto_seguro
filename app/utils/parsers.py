from __future__ import annotations

import re

from app.utils.helpers import dedupe_preserve_order, normalize_for_match

PRICE_PATTERN = re.compile(r"R\$\s*([0-9]{1,3}(?:\.[0-9]{3})*,[0-9]{2}|[0-9]+,[0-9]{2})")


def parse_brl_price(text: str | None) -> float | None:
    if not text:
        return None
    match = PRICE_PATTERN.search(text)
    if not match:
        return None
    numeric = match.group(1).replace(".", "").replace(",", ".")
    try:
        return float(numeric)
    except ValueError:
        return None


def extract_brl_values(text: str | None) -> list[tuple[str, float]]:
    if not text:
        return []
    values: list[tuple[str, float]] = []
    for match in PRICE_PATTERN.finditer(text):
        raw = match.group(0)
        parsed = parse_brl_price(raw)
        if parsed is not None:
            values.append((raw, parsed))
    return values


def split_visible_lines(text: str | None) -> list[str]:
    if not text:
        return []
    lines = [line.strip() for line in text.splitlines()]
    return dedupe_preserve_order([line for line in lines if line])


def looks_like_daily_price(line: str) -> bool:
    normalized = normalize_for_match(line)
    return "/dia" in normalized or " diaria" in normalized or "por dia" in normalized


def looks_like_group_line(line: str) -> bool:
    normalized = normalize_for_match(line)
    return "grupo" in normalized or "classe" in normalized or "categoria" in normalized

