"""Cliente mínimo para llamar una aplicación WSGI en las pruebas, sin abrir puertos."""
import io
import json
from wsgiref.util import setup_testing_defaults


def call(app, method, path, body=None, query=""):
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
    assert captured["headers"]["Content-Type"] == "application/json; charset=utf-8"
    return captured["status"], json.loads(payload), captured["headers"]
