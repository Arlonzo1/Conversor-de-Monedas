"""Adaptador secundario: historial en memoria. Se pierde al cerrar la aplicación."""
from __future__ import annotations

from core.application.ports.outbound.conversion_repository import ConversionRepository
from core.domain.conversion import Conversion


class InMemoryConversionRepository(ConversionRepository):
    def __init__(self) -> None:
        self._conversions: list[Conversion] = []

    def save(self, conversion: Conversion) -> None:
        self._conversions.append(conversion)

    def list_all(self) -> list[Conversion]:
        return list(self._conversions)
