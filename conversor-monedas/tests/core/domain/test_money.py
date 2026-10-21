from decimal import Decimal

import pytest

from core.domain.currency_code import CurrencyCode
from core.domain.errors import InvalidAmount
from core.domain.money import Money

USD = CurrencyCode("USD")


def test_parse_keeps_exact_decimal_values():
    # Con float, 0.1 + 0.2 da 0.30000000000000004 (RNF-06).
    total = Money.parse("0.1", USD).amount + Money.parse("0.2", USD).amount
    assert total == Decimal("0.3")


def test_parse_accepts_decimal_and_surrounding_spaces():
    assert Money.parse(" 12.50 ", USD) == Money(Decimal("12.50"), USD)
    assert Money.parse(Decimal("7"), USD).amount == Decimal("7")


def test_rejects_negative_amounts():
    with pytest.raises(InvalidAmount, match="negativo"):
        Money(Decimal("-1"), USD)


def test_rejects_float_amounts():
    with pytest.raises(TypeError):
        Money(0.1, USD)
    with pytest.raises(InvalidAmount):
        Money.parse(0.1, USD)


@pytest.mark.parametrize("raw", ["abc", "", "NaN", "Infinity", "1e20", "10 USD"])
def test_parse_rejects_invalid_text(raw):
    with pytest.raises(InvalidAmount):
        Money.parse(raw, USD)


def test_parse_hints_decimal_separator_when_comma_is_used():
    with pytest.raises(InvalidAmount, match="punto"):
        Money.parse("12,50", USD)


def test_require_positive_rejects_zero():
    with pytest.raises(InvalidAmount, match="mayor que cero"):
        Money(Decimal("0"), USD).require_positive()


def test_rounded_uses_half_up_to_cents():
    assert Money(Decimal("2.345"), USD).rounded().amount == Decimal("2.35")
    assert Money(Decimal("2.344"), USD).rounded().amount == Decimal("2.34")
