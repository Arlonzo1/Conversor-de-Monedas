from datetime import timedelta

import pytest

from adapters.outbound.cached_exchange_rate_provider import CachedExchangeRateProvider
from adapters.outbound.fake_exchange_rate_provider import FakeExchangeRateProvider
from core.domain.currency_code import CurrencyCode
from core.domain.errors import ExchangeRateUnavailable
from tests.builders import NOW

USD, COP, EUR = CurrencyCode("USD"), CurrencyCode("COP"), CurrencyCode("EUR")


class ManualClock:
    def __init__(self):
        self.now = NOW

    def __call__(self):
        return self.now


@pytest.fixture
def clock():
    return ManualClock()


def test_repeated_requests_within_ttl_hit_the_inner_provider_once(clock):
    inner = FakeExchangeRateProvider()
    cached = CachedExchangeRateProvider(inner, ttl=timedelta(minutes=30), clock=clock)

    first = cached.get_rate(USD, COP)
    clock.now += timedelta(minutes=29)
    assert cached.get_rate(USD, COP) is first
    assert inner.requests == [(USD, COP)]


def test_expired_rates_are_requested_again(clock):
    inner = FakeExchangeRateProvider()
    cached = CachedExchangeRateProvider(inner, ttl=timedelta(minutes=30), clock=clock)

    cached.get_rate(USD, COP)
    clock.now += timedelta(minutes=30)
    cached.get_rate(USD, COP)
    assert inner.requests == [(USD, COP), (USD, COP)]


def test_each_pair_is_cached_separately(clock):
    inner = FakeExchangeRateProvider()
    cached = CachedExchangeRateProvider(inner, clock=clock)

    cached.get_rate(USD, COP)
    cached.get_rate(USD, EUR)
    cached.get_rate(USD, COP)
    assert inner.requests == [(USD, COP), (USD, EUR)]


def test_errors_are_not_cached(clock):
    inner = FakeExchangeRateProvider(available=False)
    cached = CachedExchangeRateProvider(inner, clock=clock)

    for _ in range(2):
        with pytest.raises(ExchangeRateUnavailable):
            cached.get_rate(USD, COP)
    assert len(inner.requests) == 2
