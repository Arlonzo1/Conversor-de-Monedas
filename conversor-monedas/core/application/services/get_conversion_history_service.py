from __future__ import annotations

from core.application.ports.inbound.get_conversion_history import GetConversionHistory
from core.application.ports.outbound.conversion_repository import ConversionRepository
from core.domain.conversion import Conversion
from core.domain.errors import DomainError


class GetConversionHistoryService(GetConversionHistory):
    """Caso de uso: consultar el historial, de la conversión más reciente a la más antigua."""

    def __init__(self, repository: ConversionRepository) -> None:
        self._repository = repository

    def execute(self, limit: int | None = None) -> list[Conversion]:
        if limit is not None and limit < 1:
            raise DomainError("La cantidad de registros debe ser un entero positivo.")
        conversions = sorted(self._repository.list_all(), key=lambda c: c.created_at, reverse=True)
        return conversions if limit is None else conversions[:limit]
