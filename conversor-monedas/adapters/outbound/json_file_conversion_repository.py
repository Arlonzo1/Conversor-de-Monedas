"""Adaptador secundario: historial en un archivo JSON (RNF-10).

Los montos y las tasas se guardan como texto para no perder precisión decimal.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from core.application.ports.outbound.conversion_repository import ConversionRepository
from core.domain.conversion import Conversion
from core.domain.currency_code import CurrencyCode
from core.domain.errors import DomainError, HistoryUnavailable
from core.domain.exchange_rate import ExchangeRate
from core.domain.money import Money


class JsonFileConversionRepository(ConversionRepository):
    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    def save(self, conversion: Conversion) -> None:
        records = self._read_records()
        records.append(_to_record(conversion))
        self._write_records(records)

    def list_all(self) -> list[Conversion]:
        records = self._read_records()
        try:
            return [_from_record(record) for record in records]
        except (KeyError, TypeError, ValueError, InvalidOperation, DomainError) as error:
            raise HistoryUnavailable(
                f"El historial en {self._path} está dañado y no se puede leer."
            ) from error

    def _read_records(self) -> list[Any]:
        if not self._path.exists():
            return []
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            raise HistoryUnavailable(f"No se pudo leer el historial en {self._path}.") from error
        if not isinstance(data, list):
            raise HistoryUnavailable(f"El historial en {self._path} no tiene el formato esperado.")
        return data

    def _write_records(self, records: list[Any]) -> None:
        temporary = self._path.with_name(self._path.name + ".tmp")
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            temporary.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
            # Reemplazo atómico: si algo falla, el historial anterior queda intacto.
            os.replace(temporary, self._path)
        except OSError as error:
            raise HistoryUnavailable(f"No se pudo guardar el historial en {self._path}.") from error


def _to_record(conversion: Conversion) -> dict[str, Any]:
    return {
        "id": conversion.id,
        "created_at": conversion.created_at.isoformat(),
        "original": _money_to_record(conversion.original),
        "converted": _money_to_record(conversion.converted),
        "rate": {
            "value": str(conversion.rate.value),
            "retrieved_at": conversion.rate.retrieved_at.isoformat(),
        },
    }


def _from_record(record: dict[str, Any]) -> Conversion:
    original = _money_from_record(record["original"])
    converted = _money_from_record(record["converted"])
    rate = ExchangeRate(
        original.currency,
        converted.currency,
        Decimal(record["rate"]["value"]),
        datetime.fromisoformat(record["rate"]["retrieved_at"]),
    )
    return Conversion(
        original, converted, rate, datetime.fromisoformat(record["created_at"]), id=record["id"]
    )


def _money_to_record(money: Money) -> dict[str, str]:
    return {"amount": str(money.amount), "currency": str(money.currency)}


def _money_from_record(record: dict[str, Any]) -> Money:
    return Money(Decimal(record["amount"]), CurrencyCode(record["currency"]))
