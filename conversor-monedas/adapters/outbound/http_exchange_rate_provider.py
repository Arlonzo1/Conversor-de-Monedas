"""Adaptador secundario: tasas reales desde ExchangeRate-API.

Es el único lugar del proyecto que sabe de HTTP, URLs y del formato JSON de la API.
Todo fallo técnico se traduce a un error del dominio (RF-07, RNF-05).

- Sin clave: endpoint abierto  https://open.er-api.com/v6/latest/<MONEDA>
- Con clave: https://v6.exchangerate-api.com/v6/<CLAVE>/latest/<MONEDA>
  (la clave se lee de una variable de entorno en main.py, nunca del código; RNF-08)
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from http.client import HTTPException
from typing import Any
from urllib.parse import quote

from adapters.outbound.http_fetch import DEFAULT_TIMEOUT_SECONDS, Fetch, urllib_fetch
from core.application.ports.outbound.exchange_rate_provider import ExchangeRateProvider
from core.domain.currency_code import CurrencyCode
from core.domain.errors import ExchangeRateUnavailable, InvalidExchangeRate, UnsupportedCurrency
from core.domain.exchange_rate import ExchangeRate

OPEN_BASE_URL = "https://open.er-api.com/v6"
KEYED_BASE_URL = "https://v6.exchangerate-api.com/v6"


class HttpExchangeRateProvider(ExchangeRateProvider):
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        fetch: Fetch = urllib_fetch,
    ) -> None:
        base_url = base_url or (KEYED_BASE_URL if api_key else OPEN_BASE_URL)
        if not base_url.startswith("https://"):
            raise ValueError("Por seguridad (RNF-08) el proveedor de tasas solo acepta URLs HTTPS.")
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout
        self._fetch = fetch

    def get_rate(self, source: CurrencyCode, target: CurrencyCode) -> ExchangeRate:
        data = self._fetch_latest(source)
        # El endpoint abierto usa "rates"; el de clave usa "conversion_rates".
        rates = data.get("rates") or data.get("conversion_rates")
        if not isinstance(rates, dict):
            raise ExchangeRateUnavailable("El proveedor de tasas devolvió una respuesta inesperada.")
        if str(target) not in rates:
            raise UnsupportedCurrency(f"El proveedor de tasas no maneja la moneda {target}.")
        try:
            value = Decimal(str(rates[str(target)]))
            return ExchangeRate(source, target, value, _retrieved_at(data))
        except (InvalidOperation, InvalidExchangeRate):
            raise ExchangeRateUnavailable(
                f"El proveedor devolvió una tasa inválida para {source}->{target}."
            ) from None

    def _url_for(self, source: CurrencyCode) -> str:
        if self._api_key:
            return f"{self._base_url}/{quote(self._api_key, safe='')}/latest/{source}"
        return f"{self._base_url}/latest/{source}"

    def _fetch_latest(self, source: CurrencyCode) -> dict[str, Any]:
        try:
            status, body = self._fetch(self._url_for(source), self._timeout)
        except (OSError, HTTPException) as error:  # sin conexión, DNS, timeout, SSL
            raise ExchangeRateUnavailable(
                "No se pudo conectar con el proveedor de tasas. Verifique su conexión a internet."
            ) from error
        try:
            # parse_float=Decimal: la tasa nunca pasa por float (RNF-06).
            data = json.loads(body, parse_float=Decimal)
        except ValueError:
            data = None
        if not isinstance(data, dict):
            raise ExchangeRateUnavailable(
                f"El proveedor de tasas respondió con un formato inesperado (HTTP {status})."
            )
        if data.get("result") == "error" or status >= 400:
            _raise_api_error(source, data.get("error-type"), status)
        return data


def _raise_api_error(source: CurrencyCode, error_type: object, status: int) -> None:
    if error_type == "unsupported-code":
        raise UnsupportedCurrency(f"El proveedor de tasas no maneja la moneda {source}.")
    if error_type in {"invalid-key", "inactive-account"}:
        raise ExchangeRateUnavailable("La clave de la API de tasas no es válida o está inactiva.")
    if error_type == "quota-reached":
        raise ExchangeRateUnavailable(
            "Se alcanzó el límite de consultas de la API de tasas. Intente más tarde."
        )
    raise ExchangeRateUnavailable(
        f"El proveedor de tasas no está disponible (HTTP {status}, {error_type or 'sin detalle'})."
    )


def _retrieved_at(data: dict[str, Any]) -> datetime:
    timestamp = data.get("time_last_update_unix")
    if isinstance(timestamp, int) and not isinstance(timestamp, bool):
        try:
            return datetime.fromtimestamp(timestamp, tz=timezone.utc)
        except (OverflowError, OSError, ValueError):
            pass
    return datetime.now(timezone.utc)
