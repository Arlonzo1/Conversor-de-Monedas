"""Adaptador secundario: tasas fijas en memoria.

Sirve para las pruebas y para usar la aplicación sin internet. Las tasas NO son reales.
"""
from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from decimal import Decimal

from core.application.ports.outbound.exchange_rate_provider import ExchangeRateProvider
from core.domain.currency_code import CurrencyCode
from core.domain.errors import ExchangeRateUnavailable, UnsupportedCurrency
from core.domain.exchange_rate import ExchangeRate

DEFAULT_RATES: Mapping[tuple[str, str], str] = {
    ("USD", "COP"): "4000",
    ("COP", "USD"): "0.00025",
    ("USD", "EUR"): "0.90",
    ("EUR", "USD"): "1.11",
    ("EUR", "COP"): "4400",
    ("COP", "EUR"): "0.000227",
}
FIXED_TIME = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)


class FakeExchangeRateProvider(ExchangeRateProvider):
    def __init__(
        self,
        rates: Mapping[tuple[str, str], str | Decimal] | None = None,
        *,
        available: bool = True,
        retrieved_at: datetime = FIXED_TIME,
    ) -> None:
        self._rates = {
            (CurrencyCode.parse(source), CurrencyCode.parse(target)): Decimal(str(value))
            for (source, target), value in (DEFAULT_RATES if rates is None else rates).items()
        }
        self._available = available
        self._retrieved_at = retrieved_at
        # Registro de consultas, para que las pruebas verifiquen si se llamó al proveedor.
        self.requests: list[tuple[CurrencyCode, CurrencyCode]] = []

    def get_rate(self, source: CurrencyCode, target: CurrencyCode) -> ExchangeRate:
        self.requests.append((source, target))
        if not self._available:
            raise ExchangeRateUnavailable("El proveedor de tasas no está disponible (simulado).")
        try:
            value = self._rates[(source, target)]
        except KeyError:
            raise UnsupportedCurrency(f"No hay tasa de prueba para {source}->{target}.") from None
        return ExchangeRate(source, target, value, self._retrieved_at)
