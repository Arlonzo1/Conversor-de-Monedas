import pytest

from core.domain.errors import DomainError


def test_empty_history(history):
    assert history.execute() == []


def test_returns_newest_first(convert, history):
    first = convert.execute("1", "USD", "COP")
    second = convert.execute("2", "USD", "COP")
    third = convert.execute("3", "EUR", "USD")

    assert history.execute() == [third, second, first]


def test_limit_returns_only_the_most_recent(convert, history):
    convert.execute("1", "USD", "COP")
    latest = convert.execute("2", "USD", "COP")

    assert history.execute(limit=1) == [latest]


@pytest.mark.parametrize("limit", [0, -3])
def test_rejects_non_positive_limits(history, limit):
    with pytest.raises(DomainError):
        history.execute(limit=limit)
