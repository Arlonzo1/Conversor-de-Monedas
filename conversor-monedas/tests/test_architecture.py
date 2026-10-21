"""Verificación automática de la regla de dependencia (RNF-03, riesgos R3 y R4).

Se analizan los imports de cada archivo sin ejecutarlo. Se usa una lista de
módulos PERMITIDOS (no de prohibidos): cualquier librería nueva en el núcleo
hace fallar la prueba hasta que se justifique.
"""
import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "core"

# Librería estándar "pura": no hace E/S, red ni interfaz.
CORE_ALLOWED_STDLIB = {
    "__future__", "abc", "collections", "dataclasses", "datetime",
    "decimal", "re", "typing", "uuid",
}


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:  # import relativo: queda dentro del mismo paquete
                modules.add("core.<relativo>")
            else:
                modules.add(node.module)
    return modules


def python_files(folder: Path) -> list[Path]:
    return sorted(folder.rglob("*.py"))


@pytest.mark.parametrize("path", python_files(CORE), ids=lambda p: str(p.relative_to(ROOT)))
def test_core_only_depends_on_itself_and_pure_stdlib(path):
    forbidden = {
        module
        for module in imported_modules(path)
        if module.split(".")[0] not in CORE_ALLOWED_STDLIB | {"core"}
    }
    assert not forbidden, f"{path.relative_to(ROOT)} importa {sorted(forbidden)}"


@pytest.mark.parametrize("path", python_files(CORE / "domain"), ids=lambda p: p.name)
def test_domain_does_not_depend_on_application(path):
    assert not any(m.startswith("core.application") for m in imported_modules(path))


def test_ports_live_in_the_core_and_adapters_implement_them():
    from adapters.inbound.cli_controller import CliController  # noqa: F401  (solo usa puertos)
    from adapters.outbound.fake_exchange_rate_provider import FakeExchangeRateProvider
    from adapters.outbound.http_exchange_rate_provider import HttpExchangeRateProvider
    from adapters.outbound.in_memory_conversion_repository import InMemoryConversionRepository
    from adapters.outbound.json_file_conversion_repository import JsonFileConversionRepository
    from core.application.ports.outbound.conversion_repository import ConversionRepository
    from core.application.ports.outbound.exchange_rate_provider import ExchangeRateProvider

    for adapter in (FakeExchangeRateProvider, HttpExchangeRateProvider):
        assert issubclass(adapter, ExchangeRateProvider)
    for adapter in (InMemoryConversionRepository, JsonFileConversionRepository):
        assert issubclass(adapter, ConversionRepository)
    assert not list((ROOT / "adapters").rglob("*port*.py")), "los puertos deben vivir en core/"


def test_adapters_do_not_depend_on_each_other_or_on_main():
    for path in python_files(ROOT / "adapters"):
        own_package = path.parent.name  # inbound / outbound
        for module in imported_modules(path):
            assert module != "main", f"{path.name} importa el composition root"
            if module.startswith("adapters."):
                assert module.split(".")[1] == own_package, f"{path.name} importa {module}"
