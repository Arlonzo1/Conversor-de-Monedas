"""Adaptador secundario: tasas desde fawazahmed0/currency-api (segundo proveedor).

Es gratuito, no necesita clave, soporta COP y se sirve desde un CDN distinto al de
ExchangeRate-API, por eso es un buen respaldo (riesgo R2).

    https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/usd.json
    -> {"date": "2026-10-20", "usd": {"cop": 3174.06966497, "eur": 0.88999126, ...}}

Los códigos van en minúsculas; si la moneda de origen no existe responde 404.
"""
from __future__ import annotations

import json
from datetime import date, datetime, time, timezone
from decimal import Decimal, InvalidOperation
from http.client import HTTPException
from typing import Any

from adapters.outbound.http_fetch import DEFAULT_TIMEOUT_SECONDS, Fetch, urllib_fetch
from core.application.ports.outbound.exchange_rate_provider import ExchangeRateProvider
from core.domain.currency_code import CurrencyCode
from core.domain.errors import ExchangeRateUnavailable, InvalidExchangeRate, UnsupportedCurrency
from core.domain.exchange_rate import ExchangeRate

DEFAULT_BASE_URL = "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1"


class CurrencyApiExchangeRateProvider(ExchangeRateProvider):
    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        fetch: Fetch = urllib_fetch,
    ) -> None:
        if not base_url.startswith("https://"):
            raise ValueError("Por seguridad (RNF-08) el proveedor de tasas solo acepta URLs HTTPS.")
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._fetch = fetch

    def get_rate(self, source: CurrencyCode, target: CurrencyCode) -> ExchangeRate:
        data = self._fetch_currency(source)
        rates = data.get(str(source).lower())
        if not isinstance(rates, dict):
            raise ExchangeRateUnavailable("El proveedor de tasas devolvió una respuesta inesperada.")
        raw_value = rates.get(str(target).lower())
        if raw_value is None:
            raise UnsupportedCurrency(f"El proveedor de tasas no maneja la moneda {target}.")
        try:
            return ExchangeRate(source, target, Decimal(str(raw_value)), _retrieved_at(data))
        except (InvalidOperation, InvalidExchangeRate):
            raise ExchangeRateUnavailable(
                f"El proveedor devolvió una tasa inválida para {source}->{target}."
            ) from None

    def _fetch_currency(self, source: CurrencyCode) -> dict[str, Any]:
        url = f"{self._base_url}/currencies/{str(source).lower()}.json"
        try:
            status, body = self._fetch(url, self._timeout)
        except (OSError, HTTPException) as error:
            raise ExchangeRateUnavailable(
                "No se pudo conectar con el proveedor de tasas. Verifique su conexión a internet."
            ) from error
        if status == 404:
            raise UnsupportedCurrency(f"El proveedor de tasas no maneja la moneda {source}.")
        if status >= 400:
            raise ExchangeRateUnavailable(f"El proveedor de tasas no está disponible (HTTP {status}).")
        try:
            data = json.loads(body, parse_float=Decimal)  # la tasa nunca pasa por float (RNF-06)
        except ValueError:
            data = None
        if not isinstance(data, dict):
            raise ExchangeRateUnavailable("El proveedor de tasas respondió con un formato inesperado.")
        return data


def _retrieved_at(data: dict[str, Any]) -> datetime:
    """La API solo informa el día de la tasa; se toma la medianoche UTC de ese día."""
    try:
        return datetime.combine(date.fromisoformat(data["date"]), time(), tzinfo=timezone.utc)
    except (KeyError, TypeError, ValueError):
        return datetime.now(timezone.utc)
