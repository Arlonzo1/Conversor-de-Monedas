"""Adaptador primario: API REST (JSON sobre HTTP).

Usa exactamente los mismos puertos de entrada que la consola, así que agregarla no
cambió nada del núcleo. Es una aplicación WSGI de la librería estándar: se prueba
llamándola directamente y se sirve con wsgiref.

    GET  /                           -> 200 página web (frontend) que usa las rutas de abajo
    GET  /salud                      -> 200 {"estado": "ok"}
    POST /conversiones               {"monto": "100", "origen": "USD", "destino": "COP"} -> 201
    GET  /conversiones?limite=5      -> 200 {"conversiones": [...]} (más reciente primero)

Los montos y tasas viajan como texto para no perder precisión decimal (RNF-06).
"""
from __future__ import annotations

import json
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from decimal import Decimal
from http import HTTPStatus
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs
from wsgiref.simple_server import make_server

from core.application.ports.inbound.convert_currency import ConvertCurrency
from core.application.ports.inbound.get_conversion_history import GetConversionHistory
from core.domain.conversion import Conversion
from core.domain.errors import (
    DomainError,
    ExchangeRateUnavailable,
    HistoryUnavailable,
    UnsupportedCurrency,
)
from core.domain.money import Money

MAX_BODY_BYTES = 10_000
WEB_PAGE = Path(__file__).resolve().parent / "web" / "index.html"

StartResponse = Callable[[str, list[tuple[str, str]]], Any]


class HttpError(Exception):
    """Error del protocolo HTTP (ruta, método, cuerpo). No es un error del dominio."""

    def __init__(self, status: HTTPStatus, message: str, headers: list[tuple[str, str]] | None = None):
        super().__init__(message)
        self.status = status
        self.headers = headers or []


@dataclass(frozen=True)
class RawResponse:
    """Respuesta que no es JSON, como la página web."""

    content: bytes
    content_type: str


class RestApi:
    def __init__(self, convert_currency: ConvertCurrency, get_history: GetConversionHistory) -> None:
        self._convert_currency = convert_currency
        self._get_history = get_history
        self._web_page = WEB_PAGE.read_bytes()
        self._routes: dict[str, dict[str, Callable[[dict[str, Any]], tuple[HTTPStatus, Any]]]] = {
            "/": {"GET": self._home},
            "/salud": {"GET": self._health},
            "/conversiones": {"GET": self._list_conversions, "POST": self._create_conversion},
        }

    def __call__(self, environ: dict[str, Any], start_response: StartResponse) -> Iterable[bytes]:
        headers: list[tuple[str, str]] = []
        try:
            status, body = self._dispatch(environ)
        except HttpError as error:
            status, body, headers = error.status, {"error": str(error)}, error.headers
        except DomainError as error:
            status, body = _status_for(error), {"error": str(error), "tipo": type(error).__name__}
        if isinstance(body, RawResponse):
            payload, content_type = body.content, body.content_type
        else:
            payload = json.dumps(body, ensure_ascii=False, indent=2).encode("utf-8")
            content_type = "application/json; charset=utf-8"
        start_response(
            f"{status.value} {status.phrase}",
            [
                ("Content-Type", content_type),
                ("Content-Length", str(len(payload))),
                *headers,
            ],
        )
        return [payload]

    def _dispatch(self, environ: dict[str, Any]) -> tuple[HTTPStatus, Any]:
        path = environ.get("PATH_INFO", "/").rstrip("/") or "/"
        handlers = self._routes.get(path)
        if handlers is None:
            raise HttpError(HTTPStatus.NOT_FOUND, f"No existe la ruta {path}.")
        handler = handlers.get(environ.get("REQUEST_METHOD", "GET"))
        if handler is None:
            allowed = ", ".join(sorted(handlers))
            raise HttpError(
                HTTPStatus.METHOD_NOT_ALLOWED, f"Método no permitido. Use: {allowed}.", [("Allow", allowed)]
            )
        return handler(environ)

    def _home(self, environ: dict[str, Any]) -> tuple[HTTPStatus, Any]:
        return HTTPStatus.OK, RawResponse(self._web_page, "text/html; charset=utf-8")

    def _health(self, environ: dict[str, Any]) -> tuple[HTTPStatus, Any]:
        return HTTPStatus.OK, {"estado": "ok"}

    def _create_conversion(self, environ: dict[str, Any]) -> tuple[HTTPStatus, Any]:
        body = _read_json_body(environ)
        missing = [field for field in ("monto", "origen", "destino") if field not in body]
        if missing:
            raise HttpError(HTTPStatus.BAD_REQUEST, f"Faltan campos: {', '.join(missing)}.")
        amount = body["monto"]
        if isinstance(amount, bool) or not isinstance(amount, (str, int, Decimal)):
            raise HttpError(HTTPStatus.BAD_REQUEST, "El campo 'monto' debe ser un número o un texto.")
        if not isinstance(body["origen"], str) or not isinstance(body["destino"], str):
            raise HttpError(HTTPStatus.BAD_REQUEST, "Los campos 'origen' y 'destino' deben ser texto.")
        conversion = self._convert_currency.execute(
            str(amount) if isinstance(amount, int) else amount, body["origen"], body["destino"]
        )
        return HTTPStatus.CREATED, conversion_to_json(conversion)

    def _list_conversions(self, environ: dict[str, Any]) -> tuple[HTTPStatus, Any]:
        query = parse_qs(environ.get("QUERY_STRING", ""))
        raw_limit = query.get("limite", [None])[-1]
        if raw_limit is not None and not raw_limit.isdigit():
            raise HttpError(HTTPStatus.BAD_REQUEST, "'limite' debe ser un número entero positivo.")
        conversions = self._get_history.execute(int(raw_limit) if raw_limit else None)
        return HTTPStatus.OK, {"conversiones": [conversion_to_json(c) for c in conversions]}


def serve(app: RestApi, host: str = "127.0.0.1", port: int = 8000) -> None:
    """Sirve la API hasta Ctrl+C. Por defecto solo escucha en el propio equipo."""
    with make_server(host, port, app) as server:
        print(f"Abra http://{host}:{port} en el navegador  (API REST en la misma dirección; Ctrl+C para detener)")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nServidor detenido.")


def conversion_to_json(conversion: Conversion) -> dict[str, Any]:
    return {
        "id": conversion.id,
        "fecha": conversion.created_at.isoformat(),
        "original": _money_to_json(conversion.original),
        "convertido": _money_to_json(conversion.converted),
        "tasa": {
            "valor": str(conversion.rate.value),
            "actualizada": conversion.rate.retrieved_at.isoformat(),
        },
    }


def _money_to_json(money: Money) -> dict[str, str]:
    return {"monto": str(money.amount), "moneda": str(money.currency)}


def _status_for(error: DomainError) -> HTTPStatus:
    if isinstance(error, UnsupportedCurrency):
        return HTTPStatus.UNPROCESSABLE_ENTITY
    if isinstance(error, ExchangeRateUnavailable):
        return HTTPStatus.SERVICE_UNAVAILABLE
    if isinstance(error, HistoryUnavailable):
        return HTTPStatus.INTERNAL_SERVER_ERROR
    return HTTPStatus.BAD_REQUEST  # datos inválidos: monto, código de moneda, límite


def _read_json_body(environ: dict[str, Any]) -> dict[str, Any]:
    try:
        length = int(environ.get("CONTENT_LENGTH") or 0)
    except ValueError:
        raise HttpError(HTTPStatus.BAD_REQUEST, "Content-Length inválido.") from None
    if length > MAX_BODY_BYTES:
        raise HttpError(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "El cuerpo de la petición es demasiado grande.")
    try:
        body = json.loads(environ["wsgi.input"].read(length) or b"null", parse_float=Decimal)
    except ValueError:
        body = None
    if not isinstance(body, dict):
        raise HttpError(
            HTTPStatus.BAD_REQUEST,
            'El cuerpo debe ser un objeto JSON, p. ej. {"monto": "100", "origen": "USD", "destino": "COP"}.',
        )
    return body
