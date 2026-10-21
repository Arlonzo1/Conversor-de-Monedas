"""Composition root: único lugar donde se eligen los adaptadores y se conectan al núcleo.

Uso:
  python main.py                      modo interactivo
  python main.py 100 USD COP          una conversión y termina
  python main.py historial            muestra el historial
  python main.py --sin-conexion ...   usa tasas de prueba (no reales) en vez de la API
  python main.py --memoria ...        historial solo en memoria durante esta ejecución

Variables de entorno:
  EXCHANGE_RATE_API_KEY   clave opcional de ExchangeRate-API (sin ella se usa el endpoint abierto)
  CONVERSOR_HISTORIAL     ruta del archivo de historial (por defecto historial.json junto a main.py)
"""
from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Callable
from pathlib import Path

from adapters.inbound.cli_controller import CliController
from adapters.outbound.fake_exchange_rate_provider import FakeExchangeRateProvider
from adapters.outbound.http_exchange_rate_provider import HttpExchangeRateProvider
from adapters.outbound.in_memory_conversion_repository import InMemoryConversionRepository
from adapters.outbound.json_file_conversion_repository import JsonFileConversionRepository
from core.application.ports.outbound.conversion_repository import ConversionRepository
from core.application.ports.outbound.exchange_rate_provider import ExchangeRateProvider
from core.application.services.convert_currency_service import ConvertCurrencyService
from core.application.services.get_conversion_history_service import GetConversionHistoryService

DEFAULT_HISTORY_FILE = Path(__file__).resolve().parent / "historial.json"


def build_cli(
    *,
    offline: bool = False,
    in_memory: bool = False,
    history_file: Path = DEFAULT_HISTORY_FILE,
    api_key: str | None = None,
    read_line: Callable[[str], str] = input,
    write: Callable[[str], None] = print,
) -> CliController:
    """Arma la aplicación. Cambiar un adaptador aquí no requiere tocar el núcleo (RNF-01)."""
    rate_provider: ExchangeRateProvider = (
        FakeExchangeRateProvider() if offline else HttpExchangeRateProvider(api_key=api_key)
    )
    repository: ConversionRepository = (
        InMemoryConversionRepository() if in_memory else JsonFileConversionRepository(history_file)
    )
    return CliController(
        ConvertCurrencyService(rate_provider, repository),
        GetConversionHistoryService(repository),
        read_line=read_line,
        write=write,
    )


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="conversor",
        description="Conversor de monedas con historial (arquitectura hexagonal).",
    )
    parser.add_argument(
        "comando", nargs="*", help="p. ej. '100 USD COP' o 'historial'. Sin comando: modo interactivo."
    )
    parser.add_argument(
        "--sin-conexion", action="store_true", help="usa tasas de prueba fijas (no reales) en vez de la API"
    )
    parser.add_argument(
        "--memoria", action="store_true", help="guarda el historial solo en memoria durante esta ejecución"
    )
    parser.add_argument(
        "--archivo",
        type=Path,
        default=Path(os.environ.get("CONVERSOR_HISTORIAL") or DEFAULT_HISTORY_FILE),
        help="archivo JSON del historial",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    # En Windows la salida redirigida usa cp1252 y las tildes se dañan (RNF-07).
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = parse_args(argv)
    cli = build_cli(
        offline=args.sin_conexion,
        in_memory=args.memoria,
        history_file=args.archivo,
        api_key=os.environ.get("EXCHANGE_RATE_API_KEY") or None,
    )
    if args.sin_conexion:
        print("Aviso: modo sin conexión; se usan tasas de prueba que no son reales.")
    if not args.comando:
        cli.run()
        return 0
    response = cli.handle(" ".join(args.comando))
    print(response)
    return 1 if response.startswith("Error:") else 0


if __name__ == "__main__":
    sys.exit(main())
