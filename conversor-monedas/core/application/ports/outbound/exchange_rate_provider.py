from __future__ import annotations

from abc import ABC, abstractmethod

from core.domain.currency_code import CurrencyCode
from core.domain.exchange_rate import ExchangeRate


class ExchangeRateProvider(ABC):
    """Puerto de salida: de dónde obtiene el núcleo las tasas de cambio (RF-03, RF-07).

    Lo define el núcleo según lo que necesita; cada proveedor concreto se adapta a él.
    Las implementaciones deben traducir sus fallos a UnsupportedCurrency o
    ExchangeRateUnavailable y nunca dejar escapar errores de red o de formato.
    """

    @abstractmethod
    def get_rate(self, source: CurrencyCode, target: CurrencyCode) -> ExchangeRate:
        """Tasa vigente para convertir de `source` a `target`."""
