from datetime import datetime, timezone
from decimal import Decimal

import pytest

from core.domain.conversion import Conversion
from core.domain.currency_code import CurrencyCode
from core.domain.errors import CurrencyMismatch, InvalidAmount
from core.domain.exchange_rate import ExchangeRate
from core.domain.money import Money

USD, COP = CurrencyCode("USD"), CurrencyCode("COP")
AT = datetime(2026, 10, 21, tzinfo=timezone.utc)
RATE = ExchangeRate(USD, COP, Decimal("4000"), AT)


def test_perform_applies_the_rate():
    conversion = Conversion.perform(Money(Decimal("2.5"), USD), RATE, AT)
    assert conversion.converted == Money(Decimal("10000.00"), COP)
    assert conversion.rate is RATE
    assert conversion.created_at == AT


def test_perform_rejects_zero():
    with pytest.raises(InvalidAmount):
        Conversion.perform(Money(Decimal("0"), USD), RATE, AT)


def test_identity_is_by_id_not_by_values():
    first = Conversion.perform(Money(Decimal("1"), USD), RATE, AT)
    second = Conversion.perform(Money(Decimal("1"), USD), RATE, AT)
    assert first != second
    same_id = Conversion(first.original, first.converted, first.rate, first.created_at, id=first.id)
    assert same_id == first
    assert len({first, second, same_id}) == 2


def test_rejects_currencies_that_do_not_match_the_rate():
    with pytest.raises(CurrencyMismatch):
        Conversion(Money(Decimal("1"), USD), Money(Decimal("1"), USD), RATE, AT)
