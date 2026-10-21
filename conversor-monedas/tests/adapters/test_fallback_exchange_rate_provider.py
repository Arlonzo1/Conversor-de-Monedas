from decimal import Decimal

import pytest

from adapters.outbound.fake_exchange_rate_provider import FakeExchangeRateProvider
from adapters.outbound.fallback_exchange_rate_provider import FallbackExchangeRateProvider
from core.domain.currency_code import CurrencyCode
from core.domain.errors import ExchangeRateUnavailable, UnsupportedCurrency

USD, COP = CurrencyCode("USD"), CurrencyCode("COP")


def working(rate="4000"):
    return FakeExchangeRateProvider({("USD", "COP"): rate})


def down():
    return FakeExchangeRateProvider(available=False)


def without_cop():
    return FakeExchangeRateProvider({})


def test_uses_the_first_provider_when_it_works():
    primary, secondary = working("4000"), working("9999")
    rate = FallbackExchangeRateProvider(primary, secondary).get_rate(USD, COP)

    assert rate.value == Decimal("4000")
    assert secondary.requests == []


@pytest.mark.parametrize("failing", [down, without_cop], ids=["caido", "sin-moneda"])
def test_falls_back_to_the_next_provider(failing):
    rate = FallbackExchangeRateProvider(failing(), working("4100")).get_rate(USD, COP)
    assert rate.value == Decimal("4100")


def test_unsupported_only_when_every_provider_says_so():
    with pytest.raises(UnsupportedCurrency):
        FallbackExchangeRateProvider(without_cop(), without_cop()).get_rate(USD, COP)


def test_unavailable_when_any_provider_could_not_answer():
    with pytest.raises(ExchangeRateUnavailable):
        FallbackExchangeRateProvider(without_cop(), down()).get_rate(USD, COP)


def test_requires_at_least_one_provider():
    with pytest.raises(ValueError):
        FallbackExchangeRateProvider()
