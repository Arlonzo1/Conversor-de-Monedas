# Avance de implementación: Conversor de Monedas con Historial

**Autor:** Arlen Jose Perdomo Rojas
**Asignatura:** Arquitectura de Software
**Fecha del corte:** 21 de octubre de 2026
**Documento base:** [propuesta-tecnica-arquitectura-hexagonal.md](propuesta-tecnica-arquitectura-hexagonal.md), sección 16 (hoja de ruta)
**Código:** [conversor-monedas/](conversor-monedas/)
**Repositorio:** https://github.com/Arlonzo1/Conversor-de-Monedas

---

## 1. Resumen

Se completaron las fases **I-0 a I-5** de la hoja de ruta. La aplicación funciona de punta a punta con la API real de tasas:

```
$ python main.py 100 USD COP
100.00 USD = 315,377.36 COP
  Tasa: 1 USD = 3153.773599 COP (actualizada 2026-10-20 19:02)
```

- **129 pruebas automáticas aprobadas** sin internet, más 2 pruebas opcionales contra la API real, también aprobadas.
- El núcleo (`core/`) **no importa ninguna librería de HTTP, archivos ni consola**, y una prueba lo verifica en cada ejecución.
- Hay **dos adaptadores por cada puerto de salida**, y se intercambian desde `main.py` sin modificar el núcleo.

## 2. Estado por fase

| Fase | Estado | Evidencia |
|---|---|---|
| **I-0. Preparación** | Completa | Se probó a mano la API `open.er-api.com`: responde, **soporta COP** (riesgo R1 cerrado) y devuelve `{"result":"error","error-type":"unsupported-code"}` ante monedas inválidas. Estructura de carpetas creada y código publicado en GitHub (mitiga el riesgo R10). |
| **I-1. Dominio** | Completa | `CurrencyCode`, `Money`, `ExchangeRate`, `Conversion` y los errores del dominio. 40 pruebas. |
| **I-2. Puertos y casos de uso** | Completa | Los 4 puertos y los 2 servicios, probados con adaptadores falsos. 16 pruebas. |
| **I-3. Adaptadores secundarios** | Completa | `HttpExchangeRateProvider`, `FakeExchangeRateProvider`, `InMemoryConversionRepository`, `JsonFileConversionRepository`. Los dos repositorios pasan las **mismas pruebas de contrato**. |
| **I-4. Adaptador primario y composition root** | Completa | `CliController` (modo interactivo y comando único) y `main.py`. 41 pruebas de adaptadores en total. |
| **I-5. Demostración y documentación** | Completa | Prueba automática de la regla de dependencia (26 verificaciones). Prueba de intercambio de adaptadores. README con diagrama Mermaid. |

## 3. Trazabilidad de requerimientos

| Requerimiento | Dónde se cumple | Cómo se verifica |
|---|---|---|
| RF-01 Ingresar monto y monedas | `CliController` → puerto `ConvertCurrency` | `test_cli_controller.py` |
| RF-02 Validar monto positivo y código de 3 letras | `Money.require_positive`, `CurrencyCode` | `test_money.py`, `test_currency_code.py` |
| RF-03 Obtener la tasa de una API pública | `HttpExchangeRateProvider` | `test_http_exchange_rate_provider.py` y `tests/integration` (API real) |
| RF-04 Calcular y mostrar | `ExchangeRate.apply`, `format_conversion` | `test_exchange_rate.py`, `test_cli_controller.py` |
| RF-05 Guardar cada conversión | `ConvertCurrencyService` → `ConversionRepository` | `test_convert_currency_service.py` |
| RF-06 Consultar el historial | `GetConversionHistoryService` | `test_get_conversion_history_service.py` |
| RF-07 Informar fallos de la API | El adaptador HTTP traduce los fallos a `ExchangeRateUnavailable` / `UnsupportedCurrency` | 14 escenarios de fallo en `test_http_exchange_rate_provider.py` |
| RNF-01 Modificabilidad | Puertos con dos implementaciones cada uno | `test_conversion_repository_contract.py`, `test_main.py` |
| RNF-02 Testabilidad | Todas las pruebas del núcleo usan adaptadores falsos | La suite completa corre en ~0,5 s sin red |
| RNF-03 Mantenibilidad | Regla de dependencia | `test_architecture.py` (se comprobó que falla si se agrega `import urllib` al dominio) |
| RNF-04 Rendimiento < 3 s | — | Medido: **~0,65 s** por conversión con la API real |
| RNF-05 Confiabilidad | Errores del dominio + manejo en la consola | `test_api_failure_does_not_crash_the_program` |
| RNF-06 Precisión decimal | `Decimal` en todo el flujo, incluso al leer el JSON de la API | `test_parse_keeps_exact_decimal_values`, `test_reads_the_rate_without_losing_precision` |
| RNF-07 Portabilidad | Solo librería estándar; salida en UTF-8 | Probado en Windows 11 con Python 3.13. **Falta probar en Linux y macOS.** |
| RNF-08 Seguridad | Solo HTTPS; la clave se lee de `EXCHANGE_RATE_API_KEY` | `test_only_https_is_allowed` |
| RNF-09 Usabilidad | Mensajes en español, comando `ayuda` | `test_cli_controller.py` |
| RNF-10 Persistencia | `JsonFileConversionRepository` con escritura atómica | `test_history_survives_between_instances`, `test_json_history_persists_between_runs` |

## 4. Criterios de éxito de la implementación (sección 17)

- [x] Se puede convertir un monto y consultar el historial.
- [x] El núcleo no importa HTTP, base de datos ni consola, y la verificación está automatizada.
- [x] Hay al menos dos adaptadores por cada puerto de salida.
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

## 6. Pendientes y siguientes pasos

1. Ejecutar las pruebas en Linux o macOS para cerrar RNF-07.
2. Extensiones opcionales de la sección 16: API REST como segundo adaptador primario, caché de la última tasa y un segundo proveedor de tasas.
