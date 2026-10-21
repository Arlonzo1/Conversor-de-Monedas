"""Pruebas del adaptador HTTP sin red: se inyecta una función `fetch` falsa."""
import socket
from datetime import datetime, timezone
from decimal import Decimal
from functools import partial
from urllib.error import URLError

import pytest

from adapters.outbound.http_exchange_rate_provider import HttpExchangeRateProvider
from core.domain.currency_code import CurrencyCode
from core.domain.errors import ExchangeRateUnavailable, UnsupportedCurrency
from tests.adapters.fake_fetch import FakeFetch as BaseFetch

USD, COP = CurrencyCode("USD"), CurrencyCode("COP")

# Fragmento real del formato de https://open.er-api.com/v6/latest/USD
SUCCESS_BODY = (
    b'{"result":"success","base_code":"USD","time_last_update_unix":1792540952,'
    b'"rates":{"USD":1,"COP":3153.773599,"EUR":0.89075}}'
)
FakeFetch = partial(BaseFetch, body=SUCCESS_BODY)


def test_reads_the_rate_without_losing_precision():
    fetch = FakeFetch()
    rate = HttpExchangeRateProvider(fetch=fetch).get_rate(USD, COP)

    assert rate.value == Decimal("3153.773599")
    assert (rate.source, rate.target) == (USD, COP)
    assert rate.retrieved_at == datetime.fromtimestamp(1792540952, tz=timezone.utc)
    assert fetch.urls == ["https://open.er-api.com/v6/latest/USD"]


def test_with_api_key_uses_the_keyed_endpoint_and_format():
    fetch = FakeFetch(body={"result": "success", "conversion_rates": {"COP": 4000}})
    rate = HttpExchangeRateProvider(api_key="mi-clave", fetch=fetch).get_rate(USD, COP)

    assert rate.value == Decimal("4000")
    assert fetch.urls == ["https://v6.exchangerate-api.com/v6/mi-clave/latest/USD"]


def test_unsupported_source_currency():
    fetch = FakeFetch(status=404, body={"result": "error", "error-type": "unsupported-code"})
    with pytest.raises(UnsupportedCurrency):
        HttpExchangeRateProvider(fetch=fetch).get_rate(CurrencyCode("XYZ"), COP)


def test_unsupported_target_currency():
    with pytest.raises(UnsupportedCurrency, match="XYZ"):
        HttpExchangeRateProvider(fetch=FakeFetch()).get_rate(USD, CurrencyCode("XYZ"))


@pytest.mark.parametrize(
    "error",
    [URLError("sin conexión"), TimeoutError("timed out"), socket.gaierror("DNS"), ConnectionResetError()],
)
def test_network_failures_become_domain_errors(error):
    with pytest.raises(ExchangeRateUnavailable, match="conexión"):
        HttpExchangeRateProvider(fetch=FakeFetch(error=error)).get_rate(USD, COP)


@pytest.mark.parametrize(
    ("status", "body"),
    [
        (200, b"<html>no es json</html>"),
        (500, b"Internal Server Error"),
        (200, b"[1, 2, 3]"),
        (200, {"result": "success"}),
        (200, {"result": "success", "rates": {"COP": "abc"}}),
        (200, {"result": "success", "rates": {"COP": -1}}),
        (503, {"result": "error"}),
    ],
)
def test_unexpected_responses_become_domain_errors(status, body):
    with pytest.raises(ExchangeRateUnavailable):
        HttpExchangeRateProvider(fetch=FakeFetch(status=status, body=body)).get_rate(USD, COP)


def test_quota_reached_has_a_clear_message():
    fetch = FakeFetch(status=429, body={"result": "error", "error-type": "quota-reached"})
    with pytest.raises(ExchangeRateUnavailable, match="límite"):
        HttpExchangeRateProvider(api_key="k", fetch=fetch).get_rate(USD, COP)


def test_only_https_is_allowed():
    """RNF-08."""
    with pytest.raises(ValueError):
        HttpExchangeRateProvider(base_url="http://open.er-api.com/v6")
