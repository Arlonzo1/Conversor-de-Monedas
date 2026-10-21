from __future__ import annotations

from abc import ABC, abstractmethod

from core.domain.conversion import Conversion


class ConversionRepository(ABC):
    """Puerto de salida: dónde se guarda el historial (RF-05, RF-06).

    Las implementaciones deben traducir sus fallos de almacenamiento a HistoryUnavailable.
    """

    @abstractmethod
    def save(self, conversion: Conversion) -> None:
        """Agrega una conversión al historial."""

    @abstractmethod
    def list_all(self) -> list[Conversion]:
        """Todas las conversiones, en el orden en que se guardaron."""
