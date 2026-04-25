from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class QuoteRequest:
    pickup_location: str
    pickup_date: str
    pickup_time: str
    return_date: str
    return_time: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(slots=True)
class CarOption:
    provider: str
    name: str
    group: str | None = None
    total_price: float | None = None
    total_price_text: str | None = None
    daily_price_text: str | None = None
    policies: list[str] = field(default_factory=list)
    observations: list[str] = field(default_factory=list)
    detail_url: str | None = None
    raw_text: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class QuoteResult:
    provider: str
    success: bool = False
    agency_name: str | None = None
    airport_validated: bool = False
    addons_cleared: bool | None = None
    options: list[CarOption] = field(default_factory=list)
    observations: list[str] = field(default_factory=list)
    error: str | None = None
    final_url: str | None = None
    collected_at: str | None = None
    screenshot_paths: list[str] = field(default_factory=list)
    error_artifacts: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["options"] = [option.to_dict() for option in self.options]
        return data


@dataclass(slots=True)
class RunSummary:
    request: QuoteRequest
    localiza: QuoteResult
    movida: QuoteResult
    errors: list[str] = field(default_factory=list)
    executed_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "request": self.request.to_dict(),
            "localiza": self.localiza.to_dict(),
            "movida": self.movida.to_dict(),
            "errors": list(self.errors),
            "executed_at": self.executed_at,
            "screenshots": {
                "localiza": list(self.localiza.screenshot_paths),
                "movida": list(self.movida.screenshot_paths),
            },
        }

