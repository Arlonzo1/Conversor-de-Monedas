"""Prueba contra la API real. No corre por defecto para que la suite no dependa de internet (R8).

Para ejecutarla:  CONVERSOR_PRUEBAS_RED=1 python -m pytest -m red
"""
import os
from decimal import Decimal

import pytest

from adapters.outbound.currency_api_exchange_rate_provider import CurrencyApiExchangeRateProvider
from adapters.outbound.http_exchange_rate_provider import HttpExchangeRateProvider
from core.domain.currency_code import CurrencyCode
from core.domain.errors import UnsupportedCurrency

pytestmark = [
    pytest.mark.red,
    pytest.mark.skipif(
        os.environ.get("CONVERSOR_PRUEBAS_RED") != "1",
        reason="requiere internet; activar con CONVERSOR_PRUEBAS_RED=1",
    ),
]


PROVIDERS = [HttpExchangeRateProvider, CurrencyApiExchangeRateProvider]


@pytest.mark.parametrize("provider_class", PROVIDERS)
def test_real_api_supports_usd_to_cop(provider_class):
    """Verifica el riesgo R1: las APIs gratuitas soportan COP."""
    rate = provider_class().get_rate(CurrencyCode("USD"), CurrencyCode("COP"))
    assert rate.value > Decimal("1000")


@pytest.mark.parametrize("provider_class", PROVIDERS)
def test_real_api_reports_unsupported_codes(provider_class):
    with pytest.raises(UnsupportedCurrency):
        provider_class().get_rate(CurrencyCode("XYZ"), CurrencyCode("COP"))
