from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from decimal import Decimal

from core.application.ports.inbound.convert_currency import ConvertCurrency
from core.application.ports.outbound.conversion_repository import ConversionRepository
from core.application.ports.outbound.exchange_rate_provider import ExchangeRateProvider
from core.domain.conversion import Conversion
from core.domain.currency_code import CurrencyCode
from core.domain.exchange_rate import ExchangeRate
from core.domain.money import Money

Clock = Callable[[], datetime]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ConvertCurrencyService(ConvertCurrency):
    """Caso de uso: convertir un monto y guardarlo en el historial.

    Solo conoce los puertos de salida (interfaces), nunca sus implementaciones.
    """

    def __init__(
        self,
        rate_provider: ExchangeRateProvider,
        repository: ConversionRepository,
        clock: Clock = utc_now,
    ) -> None:
        self._rate_provider = rate_provider
        self._repository = repository
        self._clock = clock

    def execute(self, amount: str | Decimal, source: str, target: str) -> Conversion:
        # Se valida todo antes de consultar la tasa, para no llamar a la API en vano.
        source_code = CurrencyCode.parse(source)
        target_code = CurrencyCode.parse(target)
        original = Money.parse(amount, source_code).require_positive()

        now = self._clock()
        rate = self._find_rate(source_code, target_code, now)
        conversion = Conversion.perform(original, rate, now)
        self._repository.save(conversion)
        return conversion

    def _find_rate(self, source: CurrencyCode, target: CurrencyCode, now: datetime) -> ExchangeRate:
        if source == target:
            return ExchangeRate.identity(source, now)
        return self._rate_provider.get_rate(source, target)
