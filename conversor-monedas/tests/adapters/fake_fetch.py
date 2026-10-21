"""Sustituto de la función `fetch` de los adaptadores HTTP: responde sin usar la red."""
import json


class FakeFetch:
    def __init__(self, status=200, body=b"{}", error=None):
        self.status, self.body, self.error = status, body, error
        self.urls = []

    def __call__(self, url, timeout):
        self.urls.append(url)
        if self.error:
            raise self.error
        body = self.body if isinstance(self.body, bytes) else json.dumps(self.body).encode()
        return self.status, body
