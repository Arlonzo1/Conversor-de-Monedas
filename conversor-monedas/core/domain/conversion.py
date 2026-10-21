from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4

from core.domain.errors import CurrencyMismatch
from core.domain.exchange_rate import ExchangeRate
from core.domain.money import Money


@dataclass(frozen=True, eq=False)
class Conversion:
    """Entidad: una conversión realizada (RF-05).

    Como toda entidad, se identifica por su `id` y no por sus valores: dos
    conversiones de 100 USD a COP hechas en momentos distintos son distintas.
    """

    original: Money
    converted: Money
    rate: ExchangeRate
    created_at: datetime
    id: str = field(default_factory=lambda: uuid4().hex)

    def __post_init__(self) -> None:
        if self.original.currency != self.rate.source or self.converted.currency != self.rate.target:
            raise CurrencyMismatch(
                "Las monedas de la conversión no coinciden con las de la tasa usada."
            )

    @classmethod
    def perform(cls, original: Money, rate: ExchangeRate, at: datetime) -> Conversion:
        """Realiza la conversión aplicando la tasa al monto original."""
        original.require_positive()
        return cls(original, rate.apply(original), rate, at)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Conversion) and other.id == self.id

    def __hash__(self) -> int:
        return hash(self.id)
