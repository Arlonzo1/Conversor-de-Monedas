import pytest

from adapters.inbound.cli_controller import CliController
from adapters.outbound.fake_exchange_rate_provider import FakeExchangeRateProvider
from core.application.services.convert_currency_service import ConvertCurrencyService


@pytest.fixture
def cli(convert, history):
    return CliController(convert, history)


@pytest.mark.parametrize("line", ["100 USD COP", "convertir 100 usd cop", "100 USD a COP"])
def test_converts(cli, line):
    response = cli.handle(line)
    assert response.startswith("100.00 USD = 400,000.00 COP")
    assert "1 USD = 4000 COP" in response


def test_invalid_input_shows_a_clear_error(cli):
    assert cli.handle("-5 USD COP") == "Error: El monto no puede ser negativo."
    assert cli.handle("100 USD PESOS").startswith("Error: 'PESOS' no es un código de moneda válido")


def test_unknown_command(cli):
    assert "no reconocido" in cli.handle("hola")
    assert cli.handle("   ") == ""


def test_help(cli):
    assert "historial" in cli.handle("ayuda")


def test_history(cli):
    assert cli.handle("historial") == "El historial está vacío."
    cli.handle("1 USD COP")
    cli.handle("2 EUR USD")

    lines = cli.handle("historial").splitlines()
    assert lines[0].split() == ["Fecha", "Original", "Convertido", "Tasa"]
    assert "2.00 EUR" in lines[2] and "2.20 USD" in lines[2]  # la más reciente primero
    assert "1.00 USD" in lines[3] and "4,000.00 COP" in lines[3]

    assert len(cli.handle("historial 1").splitlines()) == 3


@pytest.mark.parametrize("line", ["historial x", "historial 1 2"])
def test_history_usage(cli, line):
    assert cli.handle(line).startswith("Uso:")


def test_api_failure_does_not_crash_the_program(repository, history):
    """RNF-05: ante un fallo de la API se responde con un mensaje y se sigue funcionando."""
    convert = ConvertCurrencyService(FakeExchangeRateProvider(available=False), repository)
    output = []
    inputs = iter(["100 USD COP", "ayuda", "salir"])
    CliController(convert, history, read_line=lambda _: next(inputs), write=output.append).run()

    assert any(line.startswith("Error: El proveedor de tasas no está disponible") for line in output)
    assert any("Comandos:" in line for line in output)
    assert output[-1] == "Hasta luego."


def test_run_ends_on_end_of_input(convert, history):
    def end_of_input(_prompt):
        raise EOFError

    output = []
    CliController(convert, history, read_line=end_of_input, write=output.append).run()
    assert output[-1] == "Hasta luego."
