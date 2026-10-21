import json

import pytest

from adapters.outbound.json_file_conversion_repository import JsonFileConversionRepository
from core.domain.errors import HistoryUnavailable
from tests.builders import make_conversion


def test_history_survives_between_instances(tmp_path):
    """RNF-10: el historial se conserva entre ejecuciones."""
    path = tmp_path / "historial.json"
    conversion = make_conversion()
    JsonFileConversionRepository(path).save(conversion)

    assert JsonFileConversionRepository(path).list_all() == [conversion]


def test_creates_missing_folders_and_leaves_no_temporary_file(tmp_path):
    path = tmp_path / "datos" / "historial.json"
    JsonFileConversionRepository(path).save(make_conversion())

    assert path.exists()
    assert list(path.parent.iterdir()) == [path]


def test_stores_amounts_as_text_to_keep_precision(tmp_path):
    path = tmp_path / "historial.json"
    JsonFileConversionRepository(path).save(make_conversion(amount="0.1"))

    (record,) = json.loads(path.read_text(encoding="utf-8"))
    assert record["original"] == {"amount": "0.1", "currency": "USD"}
    assert record["rate"]["value"] == "3153.773599"


@pytest.mark.parametrize("content", ["{no es json", '{"un": "objeto"}', '[{"id": "sin campos"}]'])
def test_damaged_file_is_reported_as_domain_error(tmp_path, content):
    path = tmp_path / "historial.json"
    path.write_text(content, encoding="utf-8")
    repo = JsonFileConversionRepository(path)

    with pytest.raises(HistoryUnavailable):
        repo.list_all()


def test_damaged_file_is_not_overwritten(tmp_path):
    path = tmp_path / "historial.json"
    path.write_text("{no es json", encoding="utf-8")

    with pytest.raises(HistoryUnavailable):
        JsonFileConversionRepository(path).save(make_conversion())
    assert path.read_text(encoding="utf-8") == "{no es json"
