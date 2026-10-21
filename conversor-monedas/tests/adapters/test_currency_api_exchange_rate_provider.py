"""Pruebas del segundo proveedor HTTP sin red: se inyecta una función `fetch` falsa."""
import socket
from datetime import datetime, timezone
from decimal import Decimal
from urllib.error import URLError

import pytest

from adapters.outbound.currency_api_exchange_rate_provider import CurrencyApiExchangeRateProvider
from core.domain.currency_code import CurrencyCode
from core.domain.errors import ExchangeRateUnavailable, UnsupportedCurrency
from tests.adapters.fake_fetch import FakeFetch

USD, COP = CurrencyCode("USD"), CurrencyCode("COP")

# Fragmento real del formato de .../v1/currencies/usd.json
SUCCESS_BODY = b'{"date": "2026-10-20", "usd": {"cop": 3174.06966497, "eur": 0.88999126}}'


def test_reads_the_rate_with_lowercase_codes_and_exact_decimals():
    fetch = FakeFetch(body=SUCCESS_BODY)
    rate = CurrencyApiExchangeRateProvider(fetch=fetch).get_rate(USD, COP)

    assert rate.value == Decimal("3174.06966497")
    assert rate.retrieved_at == datetime(2026, 10, 20, tzinfo=timezone.utc)
    assert fetch.urls == [
        "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/usd.json"
    ]


def test_unknown_source_currency_returns_404():
    fetch = FakeFetch(status=404, body=b"Couldn't find the requested file")
    with pytest.raises(UnsupportedCurrency, match="XYZ"):
        CurrencyApiExchangeRateProvider(fetch=fetch).get_rate(CurrencyCode("XYZ"), COP)


def test_unknown_target_currency():
    with pytest.raises(UnsupportedCurrency, match="XYZ"):
        CurrencyApiExchangeRateProvider(fetch=FakeFetch(body=SUCCESS_BODY)).get_rate(USD, CurrencyCode("XYZ"))


@pytest.mark.parametrize("error", [URLError("sin conexión"), TimeoutError(), socket.gaierror("DNS")])
def test_network_failures_become_domain_errors(error):
    with pytest.raises(ExchangeRateUnavailable, match="conexión"):
        CurrencyApiExchangeRateProvider(fetch=FakeFetch(error=error)).get_rate(USD, COP)


@pytest.mark.parametrize(
    ("status", "body"),
    [
        (500, b"error"),
        (200, b"<html></html>"),
        (200, b'{"date": "2026-10-20"}'),
        (200, b'{"date": "2026-10-20", "usd": {"cop": 0}}'),
        (200, b'{"date": "2026-10-20", "usd": {"cop": "abc"}}'),
    ],
)
def test_unexpected_responses_become_domain_errors(status, body):
    with pytest.raises(ExchangeRateUnavailable):
        CurrencyApiExchangeRateProvider(fetch=FakeFetch(status=status, body=body)).get_rate(USD, COP)


def test_only_https_is_allowed():
    with pytest.raises(ValueError):
        CurrencyApiExchangeRateProvider(base_url="http://cdn.jsdelivr.net")
