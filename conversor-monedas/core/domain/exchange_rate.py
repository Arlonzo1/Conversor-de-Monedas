from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from core.domain.currency_code import CurrencyCode
from core.domain.errors import CurrencyMismatch, InvalidExchangeRate
from core.domain.money import Money


@dataclass(frozen=True)
class ExchangeRate:
    """Objeto de valor: cuántas unidades de `target` equivalen a 1 unidad de `source`."""

    source: CurrencyCode
    target: CurrencyCode
    value: Decimal
    retrieved_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.value, Decimal) or not self.value.is_finite() or self.value <= 0:
            raise InvalidExchangeRate(
                f"La tasa {self.source}->{self.target} debe ser un número decimal positivo."
            )
        if self.source == self.target and self.value != 1:
            raise InvalidExchangeRate("La tasa de una moneda a sí misma debe ser 1.")

    @classmethod
    def identity(cls, currency: CurrencyCode, retrieved_at: datetime) -> ExchangeRate:
        """Tasa de una moneda a sí misma; no hace falta consultarla a nadie."""
        return cls(currency, currency, Decimal(1), retrieved_at)

    def apply(self, money: Money) -> Money:
        """Convierte `money` a la moneda destino, redondeado a centavos."""
        if money.currency != self.source:
            raise CurrencyMismatch(
                f"La tasa es para {self.source}, pero el monto está en {money.currency}."
            )
        return Money(money.amount * self.value, self.target).rounded()
