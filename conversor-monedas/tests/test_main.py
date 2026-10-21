"""Composition root y demostración de adaptadores intercambiables (fase I-5)."""
import pytest

import main


@pytest.mark.parametrize("in_memory", [True, False], ids=["memoria", "json"])
def test_same_core_works_with_either_repository(tmp_path, in_memory):
    cli = main.build_cli(offline=True, in_memory=in_memory, history_file=tmp_path / "h.json")
    assert cli.handle("100 USD COP").startswith("100.00 USD = 400,000.00 COP")
    assert "400,000.00 COP" in cli.handle("historial")


def test_json_history_persists_between_runs(tmp_path):
    """RNF-10 de punta a punta: dos 'ejecuciones' comparten el archivo."""
    path = tmp_path / "historial.json"
    main.build_cli(offline=True, history_file=path).handle("5 EUR USD")

    assert "5.55 USD" in main.build_cli(offline=True, history_file=path).handle("historial")


def test_memory_history_is_lost_between_runs():
    main.build_cli(offline=True, in_memory=True).handle("5 EUR USD")
    assert main.build_cli(offline=True, in_memory=True).handle("historial") == "El historial está vacío."


def test_main_single_command(capsys, tmp_path):
    exit_code = main.main(["--sin-conexion", "--archivo", str(tmp_path / "h.json"), "100", "USD", "COP"])

    out = capsys.readouterr().out
    assert exit_code == 0
    assert "tasas de prueba" in out
    assert "100.00 USD = 400,000.00 COP" in out


def test_main_returns_error_code_on_invalid_input(capsys):
    assert main.main(["--sin-conexion", "--memoria", "abc", "USD", "COP"]) == 1
    assert "Error:" in capsys.readouterr().out
