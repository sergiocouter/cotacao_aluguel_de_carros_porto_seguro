from __future__ import annotations

from datetime import datetime

from app.models import QuoteRequest


def parse_br_date(value: str) -> datetime:
    return datetime.strptime(value, "%d/%m/%Y")


def quote_window_slug(request: QuoteRequest) -> str:
    pickup = parse_br_date(request.pickup_date).strftime("%Y-%m-%d")
    dropoff = parse_br_date(request.return_date).strftime("%Y-%m-%d")
    pickup_time = request.pickup_time.replace(":", "")
    dropoff_time = request.return_time.replace(":", "")
    return f"{pickup}_{pickup_time}_to_{dropoff}_{dropoff_time}"


def format_brl(value: float | None) -> str:
    if value is None:
        return "N/D"
    integer, cents = f"{value:.2f}".split(".")
    parts: list[str] = []
    while integer:
        parts.insert(0, integer[-3:])
        integer = integer[:-3]
    return f"R$ {'.'.join(parts)},{cents}"


def format_request_period(request: QuoteRequest) -> str:
    return (
        f"Retirada: {request.pickup_date} {request.pickup_time}\n"
        f"Devolucao: {request.return_date} {request.return_time}"
    )

