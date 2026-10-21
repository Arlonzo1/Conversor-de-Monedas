"""Adaptador primario: interacción por consola.

Traduce lo que escribe el usuario a llamadas a los puertos de entrada, y los
resultados (o errores del dominio) a texto. No contiene reglas de negocio.
"""
from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from decimal import Decimal

from core.application.ports.inbound.convert_currency import ConvertCurrency
from core.application.ports.inbound.get_conversion_history import GetConversionHistory
from core.domain.conversion import Conversion
from core.domain.errors import DomainError
from core.domain.exchange_rate import ExchangeRate
from core.domain.money import Money

HELP = """\
Comandos:
  <monto> <origen> <destino>   Convierte un monto. Ej.: 100 USD COP  (también: 100 USD a COP)
  historial [n]                Muestra las últimas n conversiones (todas si se omite n)
  ayuda                        Muestra esta ayuda
  salir                        Termina el programa"""

UNKNOWN_COMMAND = "Comando no reconocido. Escriba 'ayuda' para ver los comandos."
EXIT_WORDS = {"salir", "exit", "quit"}
HELP_WORDS = {"ayuda", "help", "?"}
SEPARATOR_WORDS = {"a", "en", "to"}


class CliController:
    def __init__(
        self,
        convert_currency: ConvertCurrency,
        get_history: GetConversionHistory,
        read_line: Callable[[str], str] = input,
        write: Callable[[str], None] = print,
    ) -> None:
        self._convert_currency = convert_currency
        self._get_history = get_history
        self._read_line = read_line
        self._write = write

    def run(self) -> None:
        """Modo interactivo: lee comandos hasta 'salir' o fin de la entrada."""
        self._write("Conversor de monedas. Escriba 'ayuda' para ver los comandos.")
        while True:
            try:
                line = self._read_line("> ")
            except (EOFError, KeyboardInterrupt):
                self._write("")
                break
            if line.strip().lower() in EXIT_WORDS:
                break
            response = self.handle(line)
            if response:
                self._write(response)
        self._write("Hasta luego.")

    def handle(self, line: str) -> str:
        """Atiende un comando y devuelve el texto a mostrar. Nunca deja escapar un DomainError."""
        words = line.split()
        if not words:
            return ""
        command = words[0].lower()
        try:
            if command in HELP_WORDS:
                return HELP
            if command == "historial":
                return self._history(words[1:])
            if command == "convertir":
                words = words[1:]
            return self._convert(words)
        except DomainError as error:
            return f"Error: {error}"

    def _convert(self, args: list[str]) -> str:
        if len(args) == 4 and args[2].lower() in SEPARATOR_WORDS:
            args = [args[0], args[1], args[3]]
        if len(args) != 3:
            return UNKNOWN_COMMAND
        amount, source, target = args
        return format_conversion(self._convert_currency.execute(amount, source, target))

    def _history(self, args: list[str]) -> str:
        if len(args) > 1 or (args and not args[0].isdigit()):
            return "Uso: historial [n], donde n es un número entero positivo."
        conversions = self._get_history.execute(int(args[0]) if args else None)
        if not conversions:
            return "El historial está vacío."
        return format_history(conversions)


def format_money(money: Money) -> str:
    amount = money.amount
    if amount.as_tuple().exponent >= -2:  # muestra al menos 2 decimales sin perder los extra
        amount = amount.quantize(Decimal("0.01"))
    return f"{amount:,f} {money.currency}"


def format_rate_value(rate: ExchangeRate) -> str:
    return f"{rate.value.normalize():f}"


def format_conversion(conversion: Conversion) -> str:
    rate = conversion.rate
    return (
        f"{format_money(conversion.original)} = {format_money(conversion.converted)}\n"
        f"  Tasa: 1 {rate.source} = {format_rate_value(rate)} {rate.target}"
        f" (actualizada {_local_time(rate.retrieved_at)})"
    )


def format_history(conversions: list[Conversion]) -> str:
    rows = [("Fecha", "Original", "Convertido", "Tasa")]
    rows += [
        (
            _local_time(c.created_at),
            format_money(c.original),
            format_money(c.converted),
            format_rate_value(c.rate),
        )
        for c in conversions
    ]
    widths = [max(len(row[i]) for row in rows) for i in range(4)]
    lines = [
        "  ".join(
            cell.ljust(width) if i == 0 else cell.rjust(width)
            for i, (cell, width) in enumerate(zip(row, widths))
        )
        for row in rows
    ]
    lines.insert(1, "  ".join("-" * width for width in widths))
    return "\n".join(lines)


def _local_time(moment: datetime) -> str:
    return moment.astimezone().strftime("%Y-%m-%d %H:%M")
