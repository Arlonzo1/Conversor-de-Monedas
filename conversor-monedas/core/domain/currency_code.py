from __future__ import annotations

import re
from dataclasses import dataclass

from core.domain.errors import InvalidCurrencyCode

_ISO_4217 = re.compile(r"[A-Z]{3}")


@dataclass(frozen=True)
class CurrencyCode:
    """Objeto de valor: código de moneda de 3 letras mayúsculas, p. ej. USD o COP."""

    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not _ISO_4217.fullmatch(self.value):
            raise InvalidCurrencyCode(
                f"'{self.value}' no es un código de moneda válido: "
                "deben ser 3 letras (p. ej. USD, COP)."
            )

    @classmethod
    def parse(cls, raw: str) -> CurrencyCode:
        """Crea el código a partir de lo que escribe el usuario (ignora espacios y minúsculas)."""
        if not isinstance(raw, str):
            raise InvalidCurrencyCode(f"'{raw}' no es un código de moneda válido.")
        return cls(raw.strip().upper())

    def __str__(self) -> str:
        return self.value
