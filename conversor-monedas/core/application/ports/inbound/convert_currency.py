from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal

from core.domain.conversion import Conversion


class ConvertCurrency(ABC):
    """Puerto de entrada: convertir un monto entre dos monedas y registrarlo.

    Cubre RF-01 a RF-05 y RF-07.
    """

    @abstractmethod
    def execute(self, amount: str | Decimal, source: str, target: str) -> Conversion:
        """Recibe los datos tal como llegan del exterior; el núcleo los valida.

        Lanza un DomainError si los datos son inválidos o no se puede obtener la tasa.
        """
