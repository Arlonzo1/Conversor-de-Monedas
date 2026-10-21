"""Errores del dominio.

Son los únicos errores que el núcleo conoce. Los adaptadores traducen sus fallos
técnicos (red, archivos, formato) a estos tipos para que la aplicación pueda
manejarlos sin saber de dónde vienen (RF-07, RNF-05).
"""


class DomainError(Exception):
    """Base de los errores que la aplicación sabe manejar y mostrar al usuario."""


class InvalidCurrencyCode(DomainError):
    """El código de moneda no tiene el formato de 3 letras (ISO 4217)."""


class InvalidAmount(DomainError):
    """El monto no es un número válido para convertir."""


class InvalidExchangeRate(DomainError):
    """La tasa de cambio no es un número decimal positivo."""


class CurrencyMismatch(DomainError):
    """Se intentó operar con monedas que no corresponden entre sí."""


class UnsupportedCurrency(DomainError):
    """El proveedor de tasas no maneja la moneda solicitada."""


class ExchangeRateUnavailable(DomainError):
    """No se pudo obtener la tasa (sin conexión, API caída, respuesta inválida)."""


class HistoryUnavailable(DomainError):
    """No se pudo leer o escribir el historial."""
