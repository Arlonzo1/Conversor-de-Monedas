from datetime import datetime, timedelta

import pytest

from adapters.outbound.fake_exchange_rate_provider import FakeExchangeRateProvider
from adapters.outbound.in_memory_conversion_repository import InMemoryConversionRepository
from core.application.services.convert_currency_service import ConvertCurrencyService
from core.application.services.get_conversion_history_service import GetConversionHistoryService
from tests.builders import NOW


class SteppingClock:
    """Reloj controlable: cada llamada avanza un minuto."""

    def __init__(self, start: datetime = NOW) -> None:
        self._next = start

    def __call__(self) -> datetime:
        current = self._next
        self._next += timedelta(minutes=1)
        return current


@pytest.fixture
def clock() -> SteppingClock:
    return SteppingClock()


@pytest.fixture
def provider() -> FakeExchangeRateProvider:
    return FakeExchangeRateProvider({("USD", "COP"): "4000", ("EUR", "USD"): "1.10"})


@pytest.fixture
def repository() -> InMemoryConversionRepository:
    return InMemoryConversionRepository()


@pytest.fixture
def convert(provider, repository, clock) -> ConvertCurrencyService:
    return ConvertCurrencyService(provider, repository, clock=clock)


@pytest.fixture
def history(repository) -> GetConversionHistoryService:
    return GetConversionHistoryService(repository)
