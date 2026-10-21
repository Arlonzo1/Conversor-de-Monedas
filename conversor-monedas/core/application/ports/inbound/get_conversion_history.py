from __future__ import annotations

from abc import ABC, abstractmethod

from core.domain.conversion import Conversion


class GetConversionHistory(ABC):
    """Puerto de entrada: consultar el historial de conversiones (RF-06)."""

    @abstractmethod
    def execute(self, limit: int | None = None) -> list[Conversion]:
        """Devuelve las conversiones de la más reciente a la más antigua.

        Con `limit` devuelve solo las `limit` más recientes.
        """
