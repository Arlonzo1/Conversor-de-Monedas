"""Composition root: único lugar donde se eligen los adaptadores y se conectan al núcleo.

Uso:
  python main.py                      modo interactivo (consola)
  python main.py 100 USD COP          una conversión y termina
  python main.py historial            muestra el historial
  python main.py --servidor           expone la misma aplicación como API REST
  python main.py --sin-conexion ...   usa tasas de prueba (no reales) en vez de las APIs
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
from adapters.inbound.rest_api import RestApi, serve
from adapters.outbound.cached_exchange_rate_provider import CachedExchangeRateProvider
from adapters.outbound.currency_api_exchange_rate_provider import CurrencyApiExchangeRateProvider
from adapters.outbound.fake_exchange_rate_provider import FakeExchangeRateProvider
from adapters.outbound.fallback_exchange_rate_provider import FallbackExchangeRateProvider
from adapters.outbound.http_exchange_rate_provider import HttpExchangeRateProvider
from adapters.outbound.in_memory_conversion_repository import InMemoryConversionRepository
from adapters.outbound.json_file_conversion_repository import JsonFileConversionRepository
from core.application.ports.inbound.convert_currency import ConvertCurrency
from core.application.ports.inbound.get_conversion_history import GetConversionHistory
from core.application.ports.outbound.conversion_repository import ConversionRepository
from core.application.ports.outbound.exchange_rate_provider import ExchangeRateProvider
from core.application.services.convert_currency_service import ConvertCurrencyService
from core.application.services.get_conversion_history_service import GetConversionHistoryService

DEFAULT_HISTORY_FILE = Path(__file__).resolve().parent / "historial.json"


def build_rate_provider(*, offline: bool = False, api_key: str | None = None) -> ExchangeRateProvider:
    """Proveedores reales: ExchangeRate-API y, si falla, currency-api; ambos detrás de una caché."""
    if offline:
        return FakeExchangeRateProvider()
    return CachedExchangeRateProvider(
        FallbackExchangeRateProvider(
            HttpExchangeRateProvider(api_key=api_key),
            CurrencyApiExchangeRateProvider(),
        )
    )


def build_use_cases(
    *,
    offline: bool = False,
    in_memory: bool = False,
    history_file: Path = DEFAULT_HISTORY_FILE,
    api_key: str | None = None,
) -> tuple[ConvertCurrency, GetConversionHistory]:
    """Arma el núcleo con sus adaptadores de salida. Cambiarlos no requiere tocar el núcleo (RNF-01)."""
    rate_provider = build_rate_provider(offline=offline, api_key=api_key)
    repository: ConversionRepository = (
        InMemoryConversionRepository() if in_memory else JsonFileConversionRepository(history_file)
    )
    return ConvertCurrencyService(rate_provider, repository), GetConversionHistoryService(repository)


def build_cli(
    *,
    read_line: Callable[[str], str] = input,
    write: Callable[[str], None] = print,
    **options: object,
) -> CliController:
    return CliController(*build_use_cases(**options), read_line=read_line, write=write)


def build_rest_api(**options: object) -> RestApi:
    return RestApi(*build_use_cases(**options))


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="conversor",
        description="Conversor de monedas con historial (arquitectura hexagonal).",
    )
    parser.add_argument(
        "comando", nargs="*", help="p. ej. '100 USD COP' o 'historial'. Sin comando: modo interactivo."
    )
    parser.add_argument(
        "--sin-conexion", action="store_true", help="usa tasas de prueba fijas (no reales) en vez de las APIs"
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
    parser.add_argument("--servidor", action="store_true", help="inicia la API REST en lugar de la consola")
    parser.add_argument("--host", default="127.0.0.1", help="dirección de la API REST (por defecto 127.0.0.1)")
    parser.add_argument("--puerto", type=int, default=8000, help="puerto de la API REST (por defecto 8000)")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    # En Windows la salida redirigida usa cp1252 y las tildes se dañan (RNF-07).
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = parse_args(argv)
    options = {
        "offline": args.sin_conexion,
        "in_memory": args.memoria,
        "history_file": args.archivo,
        "api_key": os.environ.get("EXCHANGE_RATE_API_KEY") or None,
    }
    if args.sin_conexion:
        print("Aviso: modo sin conexión; se usan tasas de prueba que no son reales.")
    if args.servidor:
        serve(build_rest_api(**options), args.host, args.puerto)
        return 0
    cli = build_cli(**options)
    if not args.comando:
        cli.run()
        return 0
    response = cli.handle(" ".join(args.comando))
    print(response)
    return 1 if response.startswith("Error:") else 0


if __name__ == "__main__":
    sys.exit(main())
