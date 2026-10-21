"""Datos de prueba compartidos."""
from datetime import datetime, timezone
from decimal import Decimal

from core.domain.conversion import Conversion
from core.domain.currency_code import CurrencyCode
from core.domain.exchange_rate import ExchangeRate
from core.domain.money import Money

NOW = datetime(2026, 10, 21, 12, 0, tzinfo=timezone.utc)


def make_conversion(amount: str = "100", rate: str = "3153.773599", at: datetime = NOW) -> Conversion:
    exchange_rate = ExchangeRate(CurrencyCode("USD"), CurrencyCode("COP"), Decimal(rate), at)
    return Conversion.perform(Money(Decimal(amount), CurrencyCode("USD")), exchange_rate, at)
