"""Adaptador secundario (compuesto): consulta varios proveedores en orden.

Devuelve la primera tasa que obtiene. Si el proveedor principal se cae, cambia su
formato o no maneja una moneda, responde el siguiente (riesgos R1 y R2). Implementa
el mismo puerto, así que el núcleo sigue viendo un solo proveedor.
"""
from __future__ import annotations

from core.application.ports.outbound.exchange_rate_provider import ExchangeRateProvider
from core.domain.currency_code import CurrencyCode
from core.domain.errors import ExchangeRateUnavailable, UnsupportedCurrency
from core.domain.exchange_rate import ExchangeRate


class FallbackExchangeRateProvider(ExchangeRateProvider):
    def __init__(self, *providers: ExchangeRateProvider) -> None:
        if not providers:
            raise ValueError("Se necesita al menos un proveedor de tasas.")
        self._providers = providers

    def get_rate(self, source: CurrencyCode, target: CurrencyCode) -> ExchangeRate:
        errors: list[ExchangeRateUnavailable | UnsupportedCurrency] = []
        for provider in self._providers:
            try:
                return provider.get_rate(source, target)
            except (ExchangeRateUnavailable, UnsupportedCurrency) as error:
                errors.append(error)
        # Solo se afirma que la moneda no existe si TODOS respondieron eso;
        # si alguno falló por conexión, no se sabe y se informa como no disponible.
        unavailable = [error for error in errors if isinstance(error, ExchangeRateUnavailable)]
        raise unavailable[0] if unavailable else errors[0]
