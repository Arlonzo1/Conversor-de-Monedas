"""Cliente mínimo para llamar una aplicación WSGI en las pruebas, sin abrir puertos."""
import io
import json
from wsgiref.util import setup_testing_defaults


def call(app, method, path, body=None, query=""):
    status, headers, payload = call_raw(app, method, path, body, query)
    assert headers["Content-Type"] == "application/json; charset=utf-8"
    return status, json.loads(payload), headers


def call_raw(app, method, path, body=None, query=""):
    """Como call, pero devuelve el cuerpo en bytes sin exigir JSON (p. ej. la página web)."""
    raw = body if isinstance(body, bytes) else (b"" if body is None else json.dumps(body).encode())
    environ = {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "QUERY_STRING": query,
        "CONTENT_LENGTH": str(len(raw)),
        "wsgi.input": io.BytesIO(raw),
    }
    setup_testing_defaults(environ)
    captured = {}

    def start_response(status, headers):
        captured["status"], captured["headers"] = int(status.split()[0]), dict(headers)

    payload = b"".join(app(environ, start_response))
    return captured["status"], captured["headers"], payload
