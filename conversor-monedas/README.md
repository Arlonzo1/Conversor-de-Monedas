# Conversor de Monedas con Historial

Aplicación de consola que convierte montos entre monedas con tasas reales y guarda un historial.
Está construida con **arquitectura hexagonal (puertos y adaptadores)** como caso de estudio.
El análisis y el diseño completos están en [`../propuesta-tecnica-arquitectura-hexagonal.md`](../propuesta-tecnica-arquitectura-hexagonal.md).

## Requisitos

- Python 3.11 o superior. La aplicación **no tiene dependencias externas**: el cliente HTTP es `urllib`, de la librería estándar.
- `pytest`, solo para las pruebas: `python -m pip install -r requirements-dev.txt`

## Uso

```bash
python main.py                    # modo interactivo
python main.py 100 USD COP        # una conversión
python main.py 100 usd a cop      # también se acepta así
python main.py historial          # todo el historial (lo más reciente primero)
python main.py historial 5        # las últimas 5 conversiones
python main.py --sin-conexion 100 USD COP   # tasas de prueba, sin internet (no son reales)
python main.py --memoria ...      # historial solo durante esta ejecución
```

```
$ python main.py 100 USD COP
100.00 USD = 315,377.36 COP
  Tasa: 1 USD = 3153.773599 COP (actualizada 2026-10-20 19:02)
```

| Variable de entorno | Uso |
|---|---|
| `EXCHANGE_RATE_API_KEY` | Clave opcional de ExchangeRate-API. Sin ella se usa el endpoint abierto `open.er-api.com`. |
| `CONVERSOR_HISTORIAL` | Ruta del archivo de historial (por defecto `historial.json` junto a `main.py`). |

## Arquitectura

```mermaid
flowchart LR
    CLI[CliController<br/><i>adaptador primario</i>]
    subgraph CORE[Núcleo: core/]
        direction TB
        IN1([ConvertCurrency])
        IN2([GetConversionHistory])
        SVC[Servicios<br/>casos de uso]
        DOM[Dominio<br/>CurrencyCode · Money<br/>ExchangeRate · Conversion]
        OUT1([ExchangeRateProvider])
        OUT2([ConversionRepository])
        IN1 & IN2 --> SVC --> DOM
        SVC --> OUT1 & OUT2
    end
    CLI --> IN1 & IN2
    HTTP[HttpExchangeRateProvider] -.implementa.-> OUT1
    FAKE[FakeExchangeRateProvider] -.implementa.-> OUT1
    JSON[JsonFileConversionRepository] -.implementa.-> OUT2
    MEM[InMemoryConversionRepository] -.implementa.-> OUT2
    HTTP --> API[(ExchangeRate-API)]
    JSON --> FILE[(historial.json)]
```

```
core/                       el hexágono: solo importa core/ y librería estándar pura
├── domain/                 objetos de valor, entidad Conversion y errores del dominio
└── application/
    ├── ports/inbound/      ConvertCurrency, GetConversionHistory
    ├── ports/outbound/     ExchangeRateProvider, ConversionRepository
    └── services/           implementación de los casos de uso
adapters/
├── inbound/                CliController
└── outbound/               HTTP, Fake, InMemory, JsonFile
main.py                     composition root: único lugar que elige los adaptadores
tests/                      core/ con adaptadores falsos · adapters/ · arquitectura · main
```

> En Python `in` es palabra reservada, por eso las carpetas `in/` y `out/` del diseño se llaman `inbound/` y `outbound/`.

**Decisiones importantes**

- **Dinero con `Decimal`, nunca `float`** (RNF-06). Incluso el JSON de la API se lee con `parse_float=Decimal`, y el historial guarda montos y tasas como texto.
- **Errores del dominio.** Cada adaptador traduce sus fallos técnicos (red, timeout, JSON inválido, archivo dañado) a errores del dominio. La consola los muestra como `Error: ...` y sigue funcionando (RNF-05).
- **Validación antes de llamar a la API.** Si el monto o los códigos son inválidos, no se hace ninguna consulta.
- **Misma moneda (USD a USD):** el núcleo usa tasa 1 y no consulta al proveedor.
- **Escritura atómica del historial.** Se escribe en un `.tmp` y luego se reemplaza el archivo, así una falla no deja el historial a medias.
- **Solo HTTPS** en el proveedor de tasas, y la clave se lee de una variable de entorno (RNF-08).

## Pruebas

```bash
python -m pytest                                   # 129 pruebas, sin internet
CONVERSOR_PRUEBAS_RED=1 python -m pytest -m red    # 2 pruebas contra la API real
```

`tests/test_architecture.py` **verifica automáticamente la regla de dependencia**. Analiza los imports de cada archivo de `core/` y falla si alguno importa algo fuera de `core/` o de una lista de módulos de la librería estándar sin E/S. También comprueba que los adaptadores no se importen entre capas ni importen `main`.
