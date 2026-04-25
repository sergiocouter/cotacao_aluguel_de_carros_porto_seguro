from __future__ import annotations

from app.utils.helpers import click_with_fallback, fill_with_fallback, find_first_visible, is_airport_location


class FakeLocator:
    def __init__(self, visible: bool = True) -> None:
        self.visible = visible
        self.clicked = False
        self.filled_value: str | None = None

    @property
    def first(self) -> "FakeLocator":
        return self

    def is_visible(self) -> bool:
        return self.visible

    def click(self) -> None:
        self.clicked = True

    def fill(self, value: str) -> None:
        self.filled_value = value

    def count(self) -> int:
        return 1


class FakeTarget:
    def __init__(self, mapping: dict[tuple[str, str], FakeLocator]) -> None:
        self.mapping = mapping

    def get_by_role(self, role: str, name=None, exact: bool = False):  # noqa: ANN001
        return self.mapping[("role", role)]

    def get_by_label(self, text, exact: bool = False):  # noqa: ANN001
        return self.mapping[("label", str(text))]

    def get_by_placeholder(self, text, exact: bool = False):  # noqa: ANN001
        return self.mapping[("placeholder", str(text))]

    def get_by_text(self, text, exact: bool = False):  # noqa: ANN001
        return self.mapping[("text", str(text))]

    def locator(self, text: str):  # noqa: ANN201
        return self.mapping[("css", text)]


def test_find_first_visible_uses_fallback_order() -> None:
    hidden = FakeLocator(visible=False)
    visible = FakeLocator(visible=True)
    target = FakeTarget(
        {
            ("label", "campo1"): hidden,
            ("placeholder", "campo2"): visible,
        }
    )
    selectors = [
        {"kind": "label", "text": "campo1"},
        {"kind": "placeholder", "text": "campo2"},
    ]

    assert find_first_visible(target, selectors) is visible


def test_click_with_fallback_clicks_first_visible_locator() -> None:
    hidden = FakeLocator(visible=False)
    visible = FakeLocator(visible=True)
    target = FakeTarget(
        {
            ("label", "campo1"): hidden,
            ("placeholder", "campo2"): visible,
        }
    )
    selectors = [
        {"kind": "label", "text": "campo1"},
        {"kind": "placeholder", "text": "campo2"},
    ]

    assert click_with_fallback(target, selectors) is True
    assert visible.clicked is True


def test_fill_with_fallback_fills_first_visible_locator() -> None:
    hidden = FakeLocator(visible=False)
    visible = FakeLocator(visible=True)
    target = FakeTarget(
        {
            ("label", "campo1"): hidden,
            ("placeholder", "campo2"): visible,
        }
    )
    selectors = [
        {"kind": "label", "text": "campo1"},
        {"kind": "placeholder", "text": "campo2"},
    ]

    assert fill_with_fallback(target, selectors, "valor") is True
    assert visible.filled_value == "valor"


def test_is_airport_location_requires_airport_keyword() -> None:
    assert is_airport_location("Aeroporto de Porto Seguro") is True
    assert is_airport_location("Porto Seguro Centro") is False

