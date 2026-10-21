from dataclasses import FrozenInstanceError

import pytest

from core.domain.currency_code import CurrencyCode
from core.domain.errors import InvalidCurrencyCode


def test_accepts_three_uppercase_letters():
    assert CurrencyCode("USD").value == "USD"
    assert str(CurrencyCode("COP")) == "COP"


def test_parse_normalizes_user_input():
    assert CurrencyCode.parse("  cop ") == CurrencyCode("COP")


@pytest.mark.parametrize("raw", ["", "US", "USDT", "U$D", "123", "usd", " USD"])
def test_rejects_invalid_codes(raw):
    with pytest.raises(InvalidCurrencyCode):
        CurrencyCode(raw)


@pytest.mark.parametrize("raw", ["", "   ", "EURO", "1AB", None])
def test_parse_rejects_invalid_input(raw):
    with pytest.raises(InvalidCurrencyCode):
        CurrencyCode.parse(raw)


def test_is_immutable():
    code = CurrencyCode("USD")
    with pytest.raises(FrozenInstanceError):
        code.value = "EUR"
