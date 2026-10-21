"""Prueba contra la API real. No corre por defecto para que la suite no dependa de internet (R8).

Para ejecutarla:  CONVERSOR_PRUEBAS_RED=1 python -m pytest -m red
"""
import os
from decimal import Decimal

import pytest

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


def test_real_api_supports_usd_to_cop():
    """Verifica el riesgo R1: la API gratuita soporta COP."""
    rate = HttpExchangeRateProvider().get_rate(CurrencyCode("USD"), CurrencyCode("COP"))
    assert rate.value > Decimal("1000")


def test_real_api_reports_unsupported_codes():
    with pytest.raises(UnsupportedCurrency):
        HttpExchangeRateProvider().get_rate(CurrencyCode("XYZ"), CurrencyCode("COP"))
