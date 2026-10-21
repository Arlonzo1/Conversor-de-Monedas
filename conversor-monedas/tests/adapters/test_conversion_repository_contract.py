"""Mismas pruebas para todas las implementaciones del puerto ConversionRepository.

Si ambas pasan el contrato, son intercambiables (RNF-01).
"""
import pytest

from adapters.outbound.in_memory_conversion_repository import InMemoryConversionRepository
from adapters.outbound.json_file_conversion_repository import JsonFileConversionRepository
from tests.builders import make_conversion


@pytest.fixture(params=["memoria", "json"])
def repo(request, tmp_path):
    if request.param == "memoria":
        return InMemoryConversionRepository()
    return JsonFileConversionRepository(tmp_path / "historial.json")


def test_starts_empty(repo):
    assert repo.list_all() == []


def test_returns_saved_conversions_in_order(repo):
    first, second = make_conversion("1"), make_conversion("2")
    repo.save(first)
    repo.save(second)
    assert repo.list_all() == [first, second]


def test_keeps_every_field_with_exact_decimals(repo):
    original = make_conversion(amount="0.1", rate="3153.773599")
    repo.save(original)

    (stored,) = repo.list_all()
    assert stored.id == original.id
    assert stored.original == original.original
    assert stored.converted == original.converted
    assert stored.rate == original.rate
    assert stored.created_at == original.created_at
