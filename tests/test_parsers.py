from app.utils.parsers import parse_brl_price


def test_parse_brl_price_returns_float_for_currency_text() -> None:
    assert parse_brl_price("Total: R$ 1.234,56") == 1234.56
    assert parse_brl_price("R$ 89,90 / dia") == 89.90
    assert parse_brl_price("sem preco") is None

