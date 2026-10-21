# Avance de implementación: Conversor de Monedas con Historial

**Autor:** Arlen Jose Perdomo Rojas
**Asignatura:** Arquitectura de Software
**Fecha del corte:** 21 de octubre de 2026
**Documento base:** [propuesta-tecnica-arquitectura-hexagonal.md](propuesta-tecnica-arquitectura-hexagonal.md), sección 16 (hoja de ruta)
**Código:** [conversor-monedas/](conversor-monedas/)
**Repositorio:** https://github.com/Arlonzo1/Conversor-de-Monedas

---

## 1. Resumen

Se completaron las fases **I-0 a I-5** de la hoja de ruta y las **tres extensiones opcionales** (API REST, caché de tasas y segundo proveedor). La aplicación funciona de punta a punta con las APIs reales de tasas, por consola o por HTTP:

```
$ python main.py 100 USD COP
100.00 USD = 315,377.36 COP
  Tasa: 1 USD = 3153.773599 COP (actualizada 2026-10-20 19:02)
```

- **175 pruebas automáticas aprobadas** sin internet, más 4 pruebas opcionales contra las APIs reales, también aprobadas. GitHub Actions las ejecuta en cada push en Windows, Linux y macOS.
- El núcleo (`core/`) **no importa ninguna librería de HTTP, archivos ni consola**, y una prueba lo verifica en cada ejecución.
- Hay **dos adaptadores primarios** (consola y API REST) y **varios adaptadores por cada puerto de salida**. Se intercambian y combinan desde `main.py` sin modificar el núcleo.
- Agregar las tres extensiones **no cambió ningún archivo de `core/`**, como muestra el diff del commit `86f523d`. Es la evidencia más directa del beneficio de la arquitectura (RNF-01).

## 2. Estado por fase

| Fase | Estado | Evidencia |
|---|---|---|
| **I-0. Preparación** | Completa | Se probó a mano la API `open.er-api.com`: responde, **soporta COP** (riesgo R1 cerrado) y devuelve `{"result":"error","error-type":"unsupported-code"}` ante monedas inválidas. Estructura de carpetas creada y código publicado en GitHub (mitiga el riesgo R10). |
| **I-1. Dominio** | Completa | `CurrencyCode`, `Money`, `ExchangeRate`, `Conversion` y los errores del dominio. 40 pruebas. |
| **I-2. Puertos y casos de uso** | Completa | Los 4 puertos y los 2 servicios, probados con adaptadores falsos. 16 pruebas. |
| **I-3. Adaptadores secundarios** | Completa | `HttpExchangeRateProvider`, `FakeExchangeRateProvider`, `InMemoryConversionRepository`, `JsonFileConversionRepository`. Los dos repositorios pasan las **mismas pruebas de contrato**. |
| **I-4. Adaptador primario y composition root** | Completa | `CliController` (modo interactivo y comando único) y `main.py`. 41 pruebas de adaptadores en total. |
| **I-5. Demostración y documentación** | Completa | Prueba automática de la regla de dependencia (26 verificaciones). Prueba de intercambio de adaptadores. README con diagrama Mermaid. |

### Extensiones opcionales (sección 16)

| Extensión | Implementación | Evidencia |
|---|---|---|
| **API REST** como segundo adaptador primario | `RestApi`, aplicación WSGI de la librería estándar: `POST /conversiones`, `GET /conversiones?limite=n`, `GET /salud`. Se inicia con `python main.py --servidor`. | 22 pruebas en `test_rest_api.py`. Una prueba en `test_main.py` comprueba que consola y API comparten el mismo núcleo y el mismo historial. También se probó con `curl` contra el servidor real. |
| **Caché** de tasas | `CachedExchangeRateProvider` (patrón decorador sobre el puerto), con vigencia de 30 min. No guarda errores. | 4 pruebas. Medido con el servidor real: la primera conversión tardó **1,52 s** y la siguiente **0,012 s**. |
| **Segundo proveedor** de tasas | `CurrencyApiExchangeRateProvider` (fawazahmed0/currency-api) y `FallbackExchangeRateProvider`, que consulta los proveedores en orden. Composición final: `Cached(Fallback(ExchangeRate-API, currency-api))`. | 18 pruebas. Prueba en vivo: con el proveedor principal apuntando a un dominio inexistente, la tasa USD→COP la entregó el respaldo. |

**Sobre la elección del segundo proveedor:** primero se evaluó **Frankfurter**, pero publica las tasas del Banco Central Europeo y **no incluye COP**. Ese es exactamente el riesgo R1 de la propuesta, y por eso se verificó la cobertura antes de elegir.

## 3. Trazabilidad de requerimientos

| Requerimiento | Dónde se cumple | Cómo se verifica |
|---|---|---|
| RF-01 Ingresar monto y monedas | `CliController` y `RestApi` → puerto `ConvertCurrency` | `test_cli_controller.py`, `test_rest_api.py` |
| RF-02 Validar monto positivo y código de 3 letras | `Money.require_positive`, `CurrencyCode` | `test_money.py`, `test_currency_code.py` |
| RF-03 Obtener la tasa de una API pública | `HttpExchangeRateProvider`, con `CurrencyApiExchangeRateProvider` como respaldo | Pruebas de cada proveedor y `tests/integration` (APIs reales) |
| RF-04 Calcular y mostrar | `ExchangeRate.apply`, `format_conversion` | `test_exchange_rate.py`, `test_cli_controller.py` |
| RF-05 Guardar cada conversión | `ConvertCurrencyService` → `ConversionRepository` | `test_convert_currency_service.py` |
| RF-06 Consultar el historial | `GetConversionHistoryService` | `test_get_conversion_history_service.py` |
| RF-07 Informar fallos de la API | Los adaptadores HTTP traducen los fallos a `ExchangeRateUnavailable` / `UnsupportedCurrency`; la API REST los convierte en `503` / `422` | 14 + 10 escenarios de fallo en las pruebas de los proveedores |
| RNF-01 Modificabilidad | Puertos con varias implementaciones, combinables | `test_conversion_repository_contract.py`, `test_main.py`; las extensiones no tocaron `core/` |
| RNF-02 Testabilidad | Todas las pruebas del núcleo usan adaptadores falsos | La suite completa corre en ~0,5 s sin red |
| RNF-03 Mantenibilidad | Regla de dependencia | `test_architecture.py` (se comprobó que falla si se agrega `import urllib` al dominio) |
| RNF-04 Rendimiento < 3 s | Caché de tasas | Medido entre 0,65 s y 1,5 s sin caché, y 0,012 s con caché |
| RNF-05 Confiabilidad | Errores del dominio, manejados en la consola y en la API REST, más el proveedor de respaldo | `test_api_failure_does_not_crash_the_program`, `test_provider_down_is_503_and_nothing_is_saved`, `test_fallback_exchange_rate_provider.py` |
| RNF-06 Precisión decimal | `Decimal` en todo el flujo, incluso al leer el JSON de la API | `test_parse_keeps_exact_decimal_values`, `test_reads_the_rate_without_losing_precision` |
| RNF-07 Portabilidad | Solo librería estándar; salida en UTF-8 | GitHub Actions: aprobado en Windows y Linux con Python 3.11 y 3.13, y en macOS con 3.13. Al cierre de este corte, **macOS con 3.11 seguía en cola**. |
| RNF-08 Seguridad | Solo HTTPS; la clave se lee de `EXCHANGE_RATE_API_KEY` | `test_only_https_is_allowed` |
| RNF-09 Usabilidad | Mensajes en español, comando `ayuda` | `test_cli_controller.py` |
| RNF-10 Persistencia | `JsonFileConversionRepository` con escritura atómica | `test_history_survives_between_instances`, `test_json_history_persists_between_runs` |

## 4. Criterios de éxito de la implementación (sección 17)

- [x] Se puede convertir un monto y consultar el historial.
- [x] El núcleo no importa HTTP, base de datos ni consola, y la verificación está automatizada.
- [x] Hay al menos dos adaptadores por cada puerto de salida.
- [x] Extensiones opcionales: API REST, caché y segundo proveedor.
- [x] Se cambia de adaptador sin modificar el núcleo (`--sin-conexion`, `--memoria`).
- [x] Los casos de uso se prueban sin internet.

## 5. Cambios respecto a la propuesta

| Propuesta | Implementación | Motivo |
|---|---|---|
| Carpetas `ports/in`, `ports/out`, `adapters/in`, `adapters/out` | `inbound/` y `outbound/` | `in` es palabra reservada en Python. |
| Cliente HTTP `httpx` o `requests` | `urllib` (librería estándar) | La aplicación queda sin dependencias externas. Como el HTTP está aislado en un adaptador, cambiarlo no afecta al núcleo. |
| Errores no detallados | Nuevo módulo `core/domain/errors.py` | Hace concreto el mecanismo de RNF-05 descrito en la sección 8.7. |
| `now()` dentro del caso de uso | Reloj inyectable (`clock`) | Permite probar fechas y el orden del historial de forma determinista. |
| — | Si origen y destino son iguales, la tasa es 1 y no se consulta la API | Evita una llamada innecesaria. |
| API REST con FastAPI, Spring o ASP.NET (sección 9) | WSGI de la librería estándar (`wsgiref`) | Mantiene el proyecto sin dependencias. `wsgiref` sirve para la demostración pero no para producción; como la API es un adaptador, se podría migrar a FastAPI sin tocar el núcleo. |

## 6. Pendientes y siguientes pasos

La lista completa y actualizada está en [BITACORA.md](BITACORA.md).

1. Opcional: registrar en cada `Conversion` qué proveedor entregó la tasa. Hoy, si responde el respaldo, el historial guarda la tasa pero no su origen.
2. Opcional: un servidor WSGI de producción (por ejemplo `waitress`) si la API se fuera a desplegar.
