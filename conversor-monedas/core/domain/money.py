from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from core.domain.currency_code import CurrencyCode
from core.domain.errors import InvalidAmount

_CENT = Decimal("0.01")
# Montos de 10^12 o más se rechazan al leerlos: no son conversiones realistas
# y así el resultado siempre cabe en la precisión decimal por defecto.
_MAX_INPUT_MAGNITUDE = 12


@dataclass(frozen=True)
class Money:
    """Objeto de valor: monto decimal en una moneda.

    Nunca es negativo y nunca usa punto flotante (RNF-06).
    """

    amount: Decimal
    currency: CurrencyCode

    def __post_init__(self) -> None:
        if not isinstance(self.amount, Decimal):
            raise TypeError("Money.amount debe ser Decimal; los float no son precisos para dinero.")
        if not self.amount.is_finite():
            raise InvalidAmount("El monto debe ser un número finito.")
        if self.amount < 0:
            raise InvalidAmount("El monto no puede ser negativo.")

    @classmethod
    def parse(cls, raw: str | Decimal, currency: CurrencyCode) -> Money:
        """Crea un Money a partir de texto ("100", "12.50") o de un Decimal."""
        if isinstance(raw, Decimal):
            amount = raw
        elif isinstance(raw, str):
            text = raw.strip()
            try:
                amount = Decimal(text)
            except InvalidOperation:
                hint = " Use punto como separador decimal (p. ej. 12.50)." if "," in text else ""
                raise InvalidAmount(f"'{text}' no es un monto válido.{hint}") from None
        else:
            raise InvalidAmount(f"'{raw}' no es un monto válido.")
        if amount.is_finite() and amount.adjusted() >= _MAX_INPUT_MAGNITUDE:
            raise InvalidAmount("El monto es demasiado grande.")
        return cls(amount, currency)

    def require_positive(self) -> Money:
        """Regla de negocio: solo se convierten montos mayores que cero (RF-02)."""
        if self.amount == 0:
            raise InvalidAmount("El monto a convertir debe ser mayor que cero.")
        return self

    def rounded(self) -> Money:
        """Redondea a centavos (2 decimales, mitad hacia arriba)."""
        return Money(self.amount.quantize(_CENT, rounding=ROUND_HALF_UP), self.currency)

    def __str__(self) -> str:
        return f"{self.amount} {self.currency}"
