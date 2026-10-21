"""GET HTTP compartido por los adaptadores que consultan APIs de tasas."""
from __future__ import annotations

from collections.abc import Callable
from urllib.error import HTTPError
from urllib.request import Request, urlopen

DEFAULT_TIMEOUT_SECONDS = 5.0

# (url, timeout) -> (código HTTP, cuerpo). Se inyecta para probar los adaptadores sin red.
Fetch = Callable[[str, float], tuple[int, bytes]]


def urllib_fetch(url: str, timeout: float) -> tuple[int, bytes]:
    """GET real con la librería estándar. Los fallos de red se propagan como OSError."""
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "conversor-monedas/0.2"})
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.status, response.read()
    except HTTPError as error:
        return error.code, error.read()
