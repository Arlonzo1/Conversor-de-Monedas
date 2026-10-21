"""Pruebas de la API REST llamando la aplicación WSGI directamente (sin abrir puertos)."""
import pytest

from adapters.inbound.rest_api import RestApi
from adapters.outbound.fake_exchange_rate_provider import FakeExchangeRateProvider
from core.application.services.convert_currency_service import ConvertCurrencyService
from tests.adapters.wsgi_client import call


@pytest.fixture
def api(convert, history):
    return RestApi(convert, history)


def test_health(api):
    assert call(api, "GET", "/salud")[:2] == (200, {"estado": "ok"})


def test_create_conversion(api):
    status, body, _ = call(api, "POST", "/conversiones", {"monto": "100", "origen": "usd", "destino": "COP"})

    assert status == 201
    assert body["original"] == {"monto": "100", "moneda": "USD"}
    assert body["convertido"] == {"monto": "400000.00", "moneda": "COP"}
    assert body["tasa"]["valor"] == "4000"
    assert set(body) == {"id", "fecha", "original", "convertido", "tasa"}


@pytest.mark.parametrize("amount", [100, "100", 100.0], ids=["entero", "texto", "decimal"])
def test_amount_can_be_a_json_number_or_text(api, amount):
    status, body, _ = call(api, "POST", "/conversiones", {"monto": amount, "origen": "USD", "destino": "COP"})
    assert status == 201
    assert body["convertido"]["monto"] == "400000.00"


def test_decimal_amounts_keep_their_precision(api):
    _, body, _ = call(api, "POST", "/conversiones", b'{"monto": 0.1, "origen": "USD", "destino": "COP"}')
    assert body["original"]["monto"] == "0.1"
    assert body["convertido"]["monto"] == "400.00"


def test_list_conversions_newest_first_with_limit(api):
    for amount in ("1", "2", "3"):
        call(api, "POST", "/conversiones", {"monto": amount, "origen": "USD", "destino": "COP"})

    status, body, _ = call(api, "GET", "/conversiones", query="limite=2")
    assert status == 200
    assert [c["original"]["monto"] for c in body["conversiones"]] == ["3", "2"]
    assert len(call(api, "GET", "/conversiones/")[1]["conversiones"]) == 3


@pytest.mark.parametrize(
    ("body", "expected_status", "message"),
    [
        ({"monto": "-1", "origen": "USD", "destino": "COP"}, 400, "negativo"),
        ({"monto": "100", "origen": "US", "destino": "COP"}, 400, "código de moneda"),
        ({"monto": "100", "origen": "USD", "destino": "JPY"}, 422, "JPY"),
        ({"monto": "100", "origen": "USD"}, 400, "destino"),
        ({"monto": True, "origen": "USD", "destino": "COP"}, 400, "monto"),
        ({"monto": "1", "origen": 1, "destino": "COP"}, 400, "texto"),
        (b"{no es json", 400, "objeto JSON"),
        (b"[1, 2]", 400, "objeto JSON"),
        (None, 400, "objeto JSON"),
    ],
)
def test_invalid_requests_get_a_clear_error(api, body, expected_status, message):
    status, response, _ = call(api, "POST", "/conversiones", body)
    assert status == expected_status
    assert message in response["error"]


def test_provider_down_is_503_and_nothing_is_saved(repository, history):
    """RNF-05: el fallo de la API externa se informa con un código adecuado."""
    api = RestApi(ConvertCurrencyService(FakeExchangeRateProvider(available=False), repository), history)

    status, body, _ = call(api, "POST", "/conversiones", {"monto": "1", "origen": "USD", "destino": "COP"})
    assert status == 503
    assert body["tipo"] == "ExchangeRateUnavailable"
    assert repository.list_all() == []


@pytest.mark.parametrize("query", ["limite=abc", "limite=0", "limite=-1"])
def test_invalid_limit(api, query):
    assert call(api, "GET", "/conversiones", query=query)[0] == 400


def test_unknown_route_and_wrong_method(api):
    assert call(api, "GET", "/no-existe")[0] == 404
    status, _, headers = call(api, "DELETE", "/conversiones")
    assert status == 405
    assert headers["Allow"] == "GET, POST"


def test_rejects_oversized_bodies(api):
    huge = {"monto": "1", "origen": "USD", "destino": "COP", "relleno": "x" * 20_000}
    assert call(api, "POST", "/conversiones", huge)[0] == 413
