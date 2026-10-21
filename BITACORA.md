# Bitácora del proyecto

Registro de lo realizado y de lo que falta por hacer. Se actualiza al final de cada sesión de trabajo: lo nuevo se agrega arriba en el registro, y los pendientes se marcan `[x]` al completarse.

- **Repositorio:** https://github.com/Arlonzo1/Conversor-de-Monedas
- **CI (pruebas automáticas):** https://github.com/Arlonzo1/Conversor-de-Monedas/actions
- **Informe de avance detallado:** [avance-implementacion.md](avance-implementacion.md)

---

## Estado general (21 de octubre de 2026)

| Bloque | Estado |
|---|---|
| Análisis y planificación (propuesta técnica, fases 1 a 6) | ✅ Completo |
| Implementación, fases I-0 a I-5 de la hoja de ruta | ✅ Completo |
| Extensiones opcionales: API REST, caché y segundo proveedor | ✅ Completo |
| Pruebas | ✅ 175 aprobadas sin internet, más 4 contra las APIs reales |
| CI en Windows, Linux y macOS | ✅ Los 6 jobs aprobados (3 sistemas × Python 3.11 y 3.13) |

---

## Pendientes

### Por hacer

- [x] ~~Confirmar el job de CI de macOS con Python 3.11.~~ Aprobado; RNF-07 queda cerrado.
- [ ] **Decidir qué hacer con la propuesta técnica.** Las secciones 15 a 17 todavía describen la implementación como "futura" y los criterios de éxito no están marcados. Hay dos opciones:
  - (a) dejarla intacta como documento de planificación original, y que el informe de avance muestre el resultado;
  - (b) actualizarla para marcar los criterios cumplidos.

### Mejoras opcionales

- [ ] **Registrar qué proveedor entregó cada tasa.** Hoy, si responde el proveedor de respaldo (currency-api), el historial guarda la tasa pero no de dónde vino.
  - Implica agregar un campo a `ExchangeRate`, que es el único cambio de esta lista que toca el núcleo.
  - También implica ajustar el repositorio JSON y la API REST.
- [ ] **Servidor de producción para la API REST.** `wsgiref` sirve para la demostración pero no para producción. Se podría usar `waitress`, o migrar el adaptador a FastAPI, sin tocar el núcleo.
- [ ] **Preparar la demostración para la sustentación.** Propuesta de guion:
  1. Convertir por consola.
  2. Convertir por la API REST con `curl`.
  3. Mostrar que las dos comparten el historial.
  4. Usar `--sin-conexion` para mostrar el intercambio de adaptadores.
  5. Agregar un `import urllib` al dominio para que la prueba de arquitectura falle en vivo.

---

## Registro de sesiones

### 21 de octubre de 2026

**Commit `6f9214f`: implementación base (fases I-0 a I-5)**
- Se verificó a mano la API ExchangeRate-API: responde y soporta COP, con lo que se cierra el riesgo R1.
- **Dominio:** `CurrencyCode`, `Money` (con `Decimal`), `ExchangeRate`, `Conversion` y los errores del dominio.
- **Puertos y casos de uso:** 4 puertos, más `ConvertCurrencyService` y `GetConversionHistoryService`.
- **Adaptadores de salida:**
  - proveedor HTTP de ExchangeRate-API;
  - proveedor falso;
  - historial en memoria;
  - historial en archivo JSON, con escritura atómica.
- **Adaptador de entrada:** consola, en modo interactivo o con comando único. Composition root en `main.py`.
- **Prueba de arquitectura:** verifica automáticamente que `core/` no importe nada externo. Se comprobó que falla cuando se viola la regla.
- Documentación: README del código e informe de avance. Repositorio creado en GitHub.

**Commit `86f523d`: extensiones opcionales y CI**
- **API REST** (`--servidor`) como segundo adaptador primario: `POST /conversiones`, `GET /conversiones` y `GET /salud`.
- **Segundo proveedor de tasas:** fawazahmed0/currency-api. Se descartó Frankfurter porque no soporta COP.
- **Respaldo:** si el proveedor principal falla, responde el segundo. Se probó en vivo.
- **Caché de tasas** por 30 minutos: la conversión pasó de 1,52 s a 0,012 s.
- **GitHub Actions:** pruebas en Windows, Linux y macOS con Python 3.11 y 3.13.
- **Este commit no modificó ningún archivo de `core/`.** Es la evidencia de que se pueden agregar adaptadores sin tocar el núcleo.

**Commit de cierre de sesión**
- Informe de avance actualizado con las extensiones y el resultado del CI.
- Se crea esta bitácora.
- CI final: los 6 jobs aprobados, con lo que se cierra RNF-07 (portabilidad).

---

## Cómo retomar el trabajo

```bash
cd conversor-monedas
python -m pip install -r requirements-dev.txt   # solo instala pytest
python -m pytest                                # debe dar 175 aprobadas, 4 omitidas
python main.py 100 USD COP                      # prueba rápida con las APIs reales
```

Al terminar cada sesión:
1. Agregar una entrada en el **Registro de sesiones**.
2. Marcar o agregar **Pendientes**.
3. Actualizar el **Estado general**.
