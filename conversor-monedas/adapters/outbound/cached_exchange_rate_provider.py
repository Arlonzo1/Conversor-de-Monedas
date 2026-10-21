"""Adaptador secundario (decorador): guarda en memoria las tasas ya consultadas.

Envuelve a cualquier otro ExchangeRateProvider e implementa el mismo puerto, así que
el núcleo no nota la diferencia. Las APIs gratuitas actualizan las tasas una vez al
día, de modo que repetir la consulta en cada conversión solo gasta cuota y tiempo.
Los errores no se guardan: si una consulta falla, la siguiente vuelve a intentarlo.
"""
from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta, timezone

from core.application.ports.outbound.exchange_rate_provider import ExchangeRateProvider
from core.domain.currency_code import CurrencyCode
from core.domain.exchange_rate import ExchangeRate

DEFAULT_TTL = timedelta(minutes=30)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CachedExchangeRateProvider(ExchangeRateProvider):
    def __init__(
        self,
        inner: ExchangeRateProvider,
        ttl: timedelta = DEFAULT_TTL,
        clock: Callable[[], datetime] = _utc_now,
    ) -> None:
        self._inner = inner
        self._ttl = ttl
        self._clock = clock
        self._cache: dict[tuple[CurrencyCode, CurrencyCode], tuple[datetime, ExchangeRate]] = {}

    def get_rate(self, source: CurrencyCode, target: CurrencyCode) -> ExchangeRate:
        now = self._clock()
        cached = self._cache.get((source, target))
        if cached is not None and now - cached[0] < self._ttl:
            return cached[1]
        rate = self._inner.get_rate(source, target)
        self._cache[(source, target)] = (now, rate)
        return rate
