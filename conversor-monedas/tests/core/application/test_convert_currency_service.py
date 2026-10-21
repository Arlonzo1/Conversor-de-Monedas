"""Casos de uso probados sin internet, archivos ni consola (RNF-02)."""
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from adapters.outbound.fake_exchange_rate_provider import FakeExchangeRateProvider
from core.application.ports.outbound.exchange_rate_provider import ExchangeRateProvider
from core.application.services.convert_currency_service import ConvertCurrencyService
from core.domain.currency_code import CurrencyCode
from core.domain.errors import (
    ExchangeRateUnavailable,
    InvalidAmount,
    InvalidCurrencyCode,
    UnsupportedCurrency,
)
from core.domain.exchange_rate import ExchangeRate
from core.domain.money import Money
from tests.builders import NOW

COP = CurrencyCode("COP")


def test_converts_with_the_provider_rate_and_saves_it(convert, repository):
    conversion = convert.execute("100", "USD", "COP")

    assert conversion.converted == Money(Decimal("400000.00"), COP)
    assert conversion.created_at == NOW
    assert repository.list_all() == [conversion]


def test_accepts_user_input_with_spaces_and_lowercase(convert):
    conversion = convert.execute(" 2.5 ", "usd", "cop")
    assert conversion.converted == Money(Decimal("10000.00"), COP)


def test_same_currency_does_not_query_the_provider(convert, provider):
    conversion = convert.execute("10", "USD", "USD")
    assert conversion.converted.amount == Decimal("10.00")
    assert provider.requests == []


@pytest.mark.parametrize(
    ("amount", "source", "target", "error"),
    [
        ("-5", "USD", "COP", InvalidAmount),
        ("0", "USD", "COP", InvalidAmount),
        ("diez", "USD", "COP", InvalidAmount),
        ("10", "US", "COP", InvalidCurrencyCode),
        ("10", "USD", "PESOS", InvalidCurrencyCode),
    ],
)
def test_invalid_input_neither_queries_the_provider_nor_saves(
    convert, provider, repository, amount, source, target, error
):
    with pytest.raises(error):
        convert.execute(amount, source, target)
    assert provider.requests == []
    assert repository.list_all() == []


def test_provider_failure_is_reported_and_nothing_is_saved(repository, clock):
    service = ConvertCurrencyService(FakeExchangeRateProvider(available=False), repository, clock=clock)
    with pytest.raises(ExchangeRateUnavailable):
        service.execute("100", "USD", "COP")
    assert repository.list_all() == []


def test_unsupported_currency_is_reported(convert):
    with pytest.raises(UnsupportedCurrency):
        convert.execute("100", "USD", "JPY")


def test_works_with_any_implementation_of_the_port(repository, clock):
    """El caso de uso solo conoce la interfaz: sirve cualquier clase que la implemente."""

    class OneToTwoProvider(ExchangeRateProvider):
        def get_rate(self, source, target):
            return ExchangeRate(source, target, Decimal("2"), datetime(2026, 1, 1, tzinfo=timezone.utc))

    service = ConvertCurrencyService(OneToTwoProvider(), repository, clock=clock)
    assert service.execute("21", "ABC", "XYZ").converted.amount == Decimal("42.00")
