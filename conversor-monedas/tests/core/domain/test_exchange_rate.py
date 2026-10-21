from datetime import datetime, timezone
from decimal import Decimal

import pytest

from core.domain.currency_code import CurrencyCode
from core.domain.errors import CurrencyMismatch, InvalidExchangeRate
from core.domain.exchange_rate import ExchangeRate
from core.domain.money import Money

USD, COP, EUR = CurrencyCode("USD"), CurrencyCode("COP"), CurrencyCode("EUR")
AT = datetime(2026, 10, 21, tzinfo=timezone.utc)


def test_apply_multiplies_and_rounds_to_cents():
    rate = ExchangeRate(USD, COP, Decimal("3153.773599"), AT)
    assert rate.apply(Money(Decimal("100"), USD)) == Money(Decimal("315377.36"), COP)


def test_apply_rejects_money_in_another_currency():
    rate = ExchangeRate(USD, COP, Decimal("4000"), AT)
    with pytest.raises(CurrencyMismatch):
        rate.apply(Money(Decimal("10"), EUR))


@pytest.mark.parametrize("value", [Decimal("0"), Decimal("-1"), Decimal("NaN"), 1.5])
def test_rejects_non_positive_or_non_decimal_values(value):
    with pytest.raises(InvalidExchangeRate):
        ExchangeRate(USD, COP, value, AT)


def test_identity_rate_is_one():
    rate = ExchangeRate.identity(USD, AT)
    assert rate.value == 1
    assert rate.apply(Money(Decimal("5"), USD)) == Money(Decimal("5"), USD)


def test_rate_to_same_currency_must_be_one():
    with pytest.raises(InvalidExchangeRate):
        ExchangeRate(USD, USD, Decimal("2"), AT)
