# Análisis y Planificación de una Arquitectura de Software
## Arquitectura Hexagonal aplicada a un Conversor de Monedas con Historial

**Autor:** Arlen Jose Perdomo Rojas
**Programa:** Ingeniería de Software — Fundación Escuela Tecnológica de Neiva "Jesús Oviedo Pérez"
**Asignatura:** Arquitectura de Software
**Tipo de trabajo:** Individual
**Fecha:** 21 de octubre de 2026

---

## Tabla de contenido

1. Resumen y objetivos
2. Descripción de la arquitectura Hexagonal
3. Principios fundamentales
4. Componentes y estructura
5. Ventajas y desventajas
6. Descripción del proyecto
7. Requerimientos funcionales y no funcionales
8. Aplicación de la arquitectura al proyecto
9. Requerimientos técnicos, herramientas y tecnologías
10. Viabilidad y pertinencia
11. Plan de trabajo por fases
12. Cronograma
13. Recursos necesarios
14. Riesgos potenciales
15. Entregables
16. Hoja de ruta para la implementación
17. Criterios de éxito
18. Conclusiones
19. Referencias

---

## 1. Resumen y objetivos

Este documento presenta una **propuesta técnica** para aplicar la **Arquitectura Hexagonal (Puertos y Adaptadores)** a un proyecto pequeño: un **conversor de monedas con historial**. El proyecto se usa como caso de estudio por ser lo bastante simple para entenderse completo y lo bastante real para necesitar una dependencia externa (una API de tasas de cambio) y persistencia.

**Objetivo general**
Analizar y planificar la aplicación de la arquitectura Hexagonal a un conversor de monedas con historial, evaluando su pertinencia y estableciendo una hoja de ruta para su implementación.

**Objetivos específicos**
- Describir la arquitectura Hexagonal, sus principios, componentes, ventajas y desventajas.
- Identificar los requerimientos funcionales y no funcionales del proyecto.
- Definir cómo se aplicarían los puertos y adaptadores al proyecto.
- Determinar herramientas, tecnologías y recursos necesarios.
- Evaluar la viabilidad de implementación y la pertinencia de la arquitectura.
- Estimar tiempos, identificar riesgos y definir entregables por fase.

---

## 2. Descripción de la arquitectura Hexagonal

La **Arquitectura Hexagonal**, también llamada **Puertos y Adaptadores**, fue propuesta por Alistair Cockburn (2005). Su propósito es **aislar la lógica de negocio de los detalles externos** (interfaz de usuario, bases de datos, servicios de terceros, frameworks), de modo que la aplicación pueda ser usada y probada de forma independiente de ellos.

La aplicación se organiza alrededor de un **núcleo** que contiene la lógica de negocio. El núcleo se comunica con el exterior **solo a través de puertos** (interfaces). Cada tecnología concreta se conecta mediante un **adaptador** que implementa o usa un puerto.

> El nombre "hexágono" no implica seis lados: es una forma de dibujar que el núcleo tiene múltiples puntos de entrada y salida, y que ninguno es "superior" a otro.

**Problema que resuelve:** en muchas aplicaciones la lógica de negocio termina mezclada con el código de la interfaz, de la base de datos o de servicios externos. Eso dificulta las pruebas, el cambio de tecnologías y el mantenimiento. La Hexagonal evita esa mezcla.

---

## 3. Principios fundamentales

| # | Principio | Significado |
|---|---|---|
| 1 | **Aislamiento del núcleo** | La lógica de negocio no conoce HTTP, bases de datos, archivos ni interfaces gráficas. |
| 2 | **Regla de dependencia** | Las dependencias apuntan hacia el núcleo. El núcleo no depende de los adaptadores; los adaptadores dependen del núcleo. |
| 3 | **Comunicación mediante puertos** | Todo intercambio con el exterior pasa por interfaces definidas por el núcleo. |
| 4 | **Adaptadores intercambiables** | Una misma interfaz puede tener varias implementaciones, y se cambian sin modificar el núcleo. |
| 5 | **Inversión de dependencias** | El núcleo define el contrato que necesita; el exterior se adapta a él. |
| 6 | **Simetría entre entrada y salida** | Quien usa la aplicación (usuario, API) y lo que la aplicación usa (base de datos, servicios) se tratan con el mismo mecanismo: puertos y adaptadores. |
| 7 | **Testabilidad** | Al depender de interfaces, el núcleo se prueba con adaptadores falsos, sin infraestructura real. |

---

## 4. Componentes y estructura

### 4.1 Componentes

| Componente | Descripción |
|---|---|
| **Núcleo (dominio y aplicación)** | Entidades, objetos de valor, reglas de negocio y casos de uso. |
| **Puertos de entrada (driving / primarios)** | Interfaces que el núcleo ofrece para ser usado desde afuera. |
| **Puertos de salida (driven / secundarios)** | Interfaces que el núcleo necesita y que el exterior implementa. |
| **Adaptadores primarios** | Reciben una petición externa (consola, REST, interfaz gráfica) y llaman a un puerto de entrada. |
| **Adaptadores secundarios** | Implementan los puertos de salida con una tecnología concreta (HTTP, archivo, base de datos). |
| **Composition root** | Único lugar donde se crean los adaptadores y se inyectan en el núcleo. |

### 4.2 Estructura general

```
        ADAPTADORES PRIMARIOS                              ADAPTADORES SECUNDARIOS
        (quien usa la aplicación)                          (lo que la aplicación usa)

   ┌──────────────┐                                      ┌─────────────────────────────┐
   │ CliController│──┐                               ┌──►│ HttpExchangeRateProvider    │──► API pública
   └──────────────┘  │                               │   ├─────────────────────────────┤
                     │      ╔═══════════════════╗    │   │ FakeExchangeRateProvider    │
   ┌──────────────┐  │      ║      NÚCLEO       ║    │   └─────────────────────────────┘
   │ API REST     │──┼─────►║                   ║────┤        (puerto: ExchangeRateProvider)
   │ (opcional)   │  │      ║  Casos de uso     ║    │
   └──────────────┘  │      ║  + Dominio        ║    │   ┌─────────────────────────────┐
                     │      ╚═══════════════════╝    └──►│ JsonFileConversionRepository│──► archivo
      (puertos de entrada)                                ├─────────────────────────────┤
                                                          │ InMemoryConversionRepository│
                                                          └─────────────────────────────┘
                                                               (puerto: ConversionRepository)
```

---

## 5. Ventajas y desventajas

### 5.1 Ventajas (y cómo se reflejan en el proyecto)

| Ventaja | En el conversor de monedas |
|---|---|
| **Alta testabilidad** | Los casos de uso se prueban sin internet usando un proveedor de tasas falso. |
| **Independencia de tecnologías** | Se puede cambiar de API de tasas o de forma de guardar el historial sin tocar la lógica. |
| **Mantenibilidad** | Cada pieza tiene una sola responsabilidad y un lugar claro. |
| **Facilidad para agregar entradas** | Agregar una API REST además de la consola no modifica el núcleo. |
| **Protección de las reglas de negocio** | Las reglas (monto no negativo, código de moneda válido) viven en un solo lugar. |
| **Posibilidad de trabajar en paralelo** | Núcleo y adaptadores se pueden desarrollar de forma independiente una vez definidos los puertos. |

### 5.2 Desventajas (y cómo se reflejan en el proyecto)

| Desventaja | En el conversor de monedas |
|---|---|
| **Mayor número de archivos e interfaces** | Una función simple de convertir queda repartida en varias piezas. |
| **Curva de aprendizaje** | Requiere entender puertos, adaptadores e inyección de dependencias. |
| **Sobreingeniería en proyectos pequeños** | Para una app tan sencilla, el costo de estructura supera el beneficio práctico. |
| **Código de traducción entre capas** | Hay que convertir la respuesta de la API a objetos del dominio. |
| **Riesgo de mal uso** | Si los puertos se colocan en el lado equivocado o el núcleo importa una librería externa, se pierde el beneficio. |

---

## 6. Descripción del proyecto

**Nombre:** Conversor de Monedas con Historial.

**Descripción:** aplicación que recibe una cantidad en una moneda, la convierte a otra usando la tasa de cambio obtenida de una API pública y guarda cada conversión en un historial que el usuario puede consultar.

**Alcance incluido**
- Conversión entre dos monedas.
- Obtención de la tasa desde una API pública.
- Registro y consulta del historial.
- Entrada por consola.

**Alcance excluido**
- Usuarios y autenticación, interfaz gráfica compleja, gráficos de evolución de tasas, conversiones en lote.

**Propósito real del proyecto:** servir como caso de estudio para entender y demostrar la arquitectura Hexagonal.

---

## 7. Requerimientos funcionales y no funcionales

### 7.1 Requerimientos funcionales

| ID | Requerimiento |
|---|---|
| RF-01 | El sistema debe permitir ingresar un monto, una moneda de origen y una moneda de destino. |
| RF-02 | El sistema debe validar que el monto sea positivo y que los códigos de moneda sean válidos (3 letras). |
| RF-03 | El sistema debe obtener la tasa de cambio desde una API pública. |
| RF-04 | El sistema debe calcular y mostrar el monto convertido. |
| RF-05 | El sistema debe guardar cada conversión en un historial (monto original, monto convertido, tasa, fecha y hora). |
| RF-06 | El sistema debe permitir consultar el historial de conversiones. |
| RF-07 | El sistema debe informar de forma clara cuando no se pueda obtener la tasa (sin conexión, moneda no soportada, API caída). |

### 7.2 Requerimientos no funcionales

| ID | Atributo de calidad | Requerimiento |
|---|---|---|
| RNF-01 | **Modificabilidad** | Cambiar de proveedor de tasas o de mecanismo de almacenamiento no debe requerir modificar el núcleo. |
| RNF-02 | **Testabilidad** | Los casos de uso deben poder probarse sin conexión a internet ni acceso a archivos. |
| RNF-03 | **Mantenibilidad** | El núcleo no debe importar librerías de HTTP, persistencia ni interfaz. |
| RNF-04 | **Rendimiento** | Una conversión debe completarse en menos de 3 segundos con conexión normal (la mayor parte del tiempo depende de la API). |
| RNF-05 | **Confiabilidad** | Ante un fallo de la API, el sistema debe responder con un mensaje claro y sin cerrarse de forma inesperada. |
| RNF-06 | **Precisión** | Los cálculos monetarios deben usar tipos decimales, no de punto flotante. |
| RNF-07 | **Portabilidad** | La aplicación debe ejecutarse en Windows, Linux y macOS con el mismo código. |
| RNF-08 | **Seguridad** | Las comunicaciones con la API deben usar HTTPS y cualquier clave de acceso no debe quedar escrita en el código. |
| RNF-09 | **Usabilidad** | Los mensajes de la consola deben ser claros y los errores comprensibles. |
| RNF-10 | **Persistencia** | El historial debe conservarse entre ejecuciones cuando se use el repositorio en archivo. |

### 7.3 Atributos de calidad prioritarios para la arquitectura

Los que justifican la elección de la Hexagonal son **modificabilidad**, **testabilidad** y **mantenibilidad** (RNF-01, RNF-02 y RNF-03).

---

## 8. Aplicación de la arquitectura al proyecto

### 8.1 Núcleo: dominio

| Pieza | Tipo | Responsabilidad |
|---|---|---|
| `CurrencyCode` | Value Object | Código válido de 3 letras. |
| `Money` | Value Object | Monto decimal y moneda; no admite negativos. |
| `ExchangeRate` | Value Object | Tasa de origen a destino y fecha de consulta. |
| `Conversion` | Entidad | Monto original, monto convertido, tasa usada y fecha. |

### 8.2 Núcleo: puertos

**Puertos de entrada**

| Puerto | Función | Requerimientos |
|---|---|---|
| `ConvertCurrency` | Convertir un monto entre dos monedas y guardarlo | RF-01 a RF-05, RF-07 |
| `GetConversionHistory` | Consultar el historial | RF-06 |

**Puertos de salida**

| Puerto | Contrato | Requerimientos |
|---|---|---|
| `ExchangeRateProvider` | `get_rate(from, to) -> ExchangeRate` | RF-03, RF-07 |
| `ConversionRepository` | `save(conversion)` · `list_all() -> [Conversion]` | RF-05, RF-06 |

### 8.3 Adaptadores

| Adaptador | Tipo | Puerto | Detalle |
|---|---|---|---|
| `CliController` | Primario | `ConvertCurrency`, `GetConversionHistory` | Interacción por consola. |
| `HttpExchangeRateProvider` | Secundario | `ExchangeRateProvider` | Llamada HTTP real a la API. |
| `FakeExchangeRateProvider` | Secundario | `ExchangeRateProvider` | Tasas fijas para pruebas y trabajo sin internet. |
| `InMemoryConversionRepository` | Secundario | `ConversionRepository` | Almacenamiento en memoria. |
| `JsonFileConversionRepository` (o SQLite) | Secundario | `ConversionRepository` | Almacenamiento persistente. |

### 8.4 Flujo de una conversión

```
1. El usuario escribe: "100 USD COP"
2. CliController (adaptador primario) llama al puerto de entrada ConvertCurrency
3. ConvertCurrency pide la tasa al puerto de salida ExchangeRateProvider
4. HttpExchangeRateProvider consulta la API y devuelve un ExchangeRate
5. El núcleo calcula el monto convertido con el dominio
6. ConvertCurrency guarda la Conversion mediante el puerto ConversionRepository
7. El resultado vuelve al CliController, que lo muestra
```

### 8.5 Ejemplo mínimo (pseudocódigo)

```text
# --- Puerto de salida (vive en el núcleo) ---
interface ExchangeRateProvider:
    get_rate(from: CurrencyCode, to: CurrencyCode) -> ExchangeRate

# --- Caso de uso (núcleo) ---
class ConvertCurrencyService implements ConvertCurrency:
    constructor(rate_provider: ExchangeRateProvider,
                repository: ConversionRepository)

    execute(amount, from, to):
        rate = rate_provider.get_rate(from, to)       # solo conoce la interfaz
        converted = Money(amount * rate.value, to)
        conversion = Conversion(Money(amount, from), converted, rate, now())
        repository.save(conversion)
        return conversion

# --- Adaptador secundario (afuera del núcleo) ---
class HttpExchangeRateProvider implements ExchangeRateProvider:
    get_rate(from, to):
        response = http_get(API_URL, params={from, to})  # aquí SÍ existe HTTP
        return ExchangeRate(from, to, response.rate, today())

# --- Composition root ---
provider   = HttpExchangeRateProvider()       # intercambiable por FakeExchangeRateProvider()
repository = JsonFileConversionRepository("historial.json")
CliController(ConvertCurrencyService(provider, repository)).run()
```

### 8.6 Estructura de carpetas

```
conversor-monedas/
├── core/                               # El hexágono: no importa nada externo
│   ├── domain/
│   │   ├── currency_code
│   │   ├── money
│   │   ├── exchange_rate
│   │   └── conversion
│   └── application/
│       ├── ports/
│       │   ├── in/
│       │   │   ├── convert_currency
│       │   │   └── get_conversion_history
│       │   └── out/
│       │       ├── exchange_rate_provider
│       │       └── conversion_repository
│       └── services/
│           ├── convert_currency_service
│           └── get_conversion_history_service
├── adapters/
│   ├── in/
│   │   └── cli_controller
│   └── out/
│       ├── http_exchange_rate_provider
│       ├── fake_exchange_rate_provider
│       ├── in_memory_conversion_repository
│       └── json_file_conversion_repository
├── main                                # Composition root
└── tests/
    ├── core/                           # con adaptadores falsos, sin internet
    └── adapters/
```

**Regla verificable:** nada dentro de `core/` importa algo de `adapters/`, ni librerías de HTTP, archivos o base de datos.

### 8.7 Cómo se cumplen los requerimientos no funcionales con la arquitectura

| RNF | Mecanismo arquitectónico |
|---|---|
| RNF-01 Modificabilidad | Puertos de salida con varias implementaciones. |
| RNF-02 Testabilidad | Adaptadores falsos inyectados en los casos de uso. |
| RNF-03 Mantenibilidad | Regla de dependencia y verificación de imports en `core/`. |
| RNF-05 Confiabilidad | El adaptador HTTP traduce los errores de red a errores del dominio que el caso de uso sabe manejar. |
| RNF-06 Precisión | `Money` usa tipo decimal en el dominio. |

---

## 9. Requerimientos técnicos, herramientas y tecnologías

> **Supuesto:** se propone un stack por defecto para tener una referencia concreta. Si el lenguaje cambia (Java, C#, TypeScript), la arquitectura y el plan no cambian; solo las herramientas.

| Categoría | Opción sugerida | Alternativas |
|---|---|---|
| **Lenguaje** | Python 3.11 o superior | Java, C#, TypeScript |
| **Cliente HTTP** | `httpx` o `requests` | `HttpClient` (Java / C#), `fetch` (TS) |
| **Persistencia** | Archivo JSON | SQLite |
| **Pruebas** | `pytest` | JUnit, xUnit, Jest |
| **Doble de pruebas** | Clases falsas escritas a mano o `unittest.mock` | Mockito, Moq |
| **Interfaz de entrada** | Consola (CLI) | API REST (FastAPI, Spring, ASP.NET) |
| **Control de versiones** | Git y GitHub | GitLab |
| **Editor** | VS Code | IntelliJ, Visual Studio, PyCharm |
| **Diagramas** | Mermaid o draw.io | PlantUML |
| **Documentación** | Markdown (README) | Docs en repositorio |
| **API de tasas de cambio** | Una API pública gratuita (por ejemplo, ExchangeRate-API en su versión abierta) | Otras APIs de tasas |

**Requerimientos mínimos del equipo:** computador con el lenguaje instalado, editor de código, Git, acceso a internet para la API y los paquetes. No requiere servidores ni licencias de pago.

**Al elegir la API:** verificar que soporte las monedas que se quieren usar (por ejemplo, COP), que no exija tarjeta de crédito, que tenga límites de uso suficientes y que su formato de respuesta sea estable. Estas condiciones pueden cambiar, así que deben comprobarse en su documentación vigente.

---

## 10. Viabilidad y pertinencia

### 10.1 Viabilidad

| Dimensión | Evaluación | Justificación |
|---|---|---|
| **Técnica** | Alta | Herramientas gratuitas y conocidas; no requiere infraestructura. El único punto externo es la API. |
| **Económica** | Alta | Costo cero: software libre y APIs gratuitas. |
| **Operativa** | Alta | Aplicación de consola, sin despliegue complejo. |
| **De tiempo** | Media-alta | Alcance pequeño, estimado en unas 5 semanas con dedicación parcial. El riesgo principal es la curva de aprendizaje. |
| **De conocimiento** | Media | Requiere entender interfaces, inyección de dependencias y pruebas con adaptadores falsos; se puede reforzar con la lectura de la fase 1. |

**Conclusión de viabilidad:** el proyecto es viable con los recursos disponibles.

### 10.2 Pertinencia de la arquitectura

**A favor**
- El proyecto tiene una dependencia externa clara (la API) y persistencia, que son los dos casos típicos donde los puertos y adaptadores aportan valor.
- Los atributos de calidad prioritarios (modificabilidad, testabilidad, mantenibilidad) son justo los que la Hexagonal favorece.
- Permite demostrar la arquitectura de forma concreta: intercambiar un adaptador sin tocar el núcleo.

**En contra**
- La lógica de negocio es mínima (multiplicar por una tasa), por lo que en un producto real una arquitectura tan estructurada sería **excesiva**.

**Valoración:** la arquitectura es **pertinente para fines de aprendizaje y demostración**, y **justificable en un producto real solo si** se espera cambiar de proveedor de tasas, agregar interfaces (web, móvil) o crecer en reglas de negocio. Para una utilidad mínima de uso único, una solución más simple bastaría.

---

## 11. Plan de trabajo por fases

> Tiempos estimados en horas de trabajo individual. Las fases 1 a 6 corresponden al **análisis y la planificación** (este documento); la implementación se planifica en la sección 16.

### Fase 1 — Fundamentación de la arquitectura
**Objetivo:** comprender y documentar la arquitectura Hexagonal.

| Actividad | Horas |
|---|---|
| Leer fuentes sobre Hexagonal (Cockburn) y compararla brevemente con Clean y Onion | 3 |
| Redactar descripción, principios y componentes | 2 |
| Redactar ventajas y desventajas | 1 |

**Recursos:** artículos y libros de referencia, editor de Markdown.
**Entregable:** secciones 2 a 5 del documento.
**Tiempo total:** 6 h.

### Fase 2 — Definición del proyecto y requerimientos
**Objetivo:** delimitar qué se va a construir y qué debe cumplir.

| Actividad | Horas |
|---|---|
| Describir el proyecto, su alcance y exclusiones | 1 |
| Levantar requerimientos funcionales | 1.5 |
| Definir requerimientos no funcionales y priorizar atributos de calidad | 1.5 |

**Recursos:** documento de la actividad, plantillas de requerimientos.
**Entregable:** secciones 6 y 7 (tabla de RF y RNF).
**Tiempo total:** 4 h.

### Fase 3 — Viabilidad, herramientas y tecnologías
**Objetivo:** definir con qué se construirá y si es posible hacerlo.

| Actividad | Horas |
|---|---|
| Seleccionar lenguaje, librerías y herramientas | 1 |
| Evaluar y probar una API pública de tasas (cobertura de monedas, límites, formato) | 2 |
| Analizar viabilidad técnica, económica, operativa y de tiempo | 1 |

**Recursos:** documentación de la API, acceso a internet.
**Entregable:** secciones 9 y 10.1 (tabla de tecnologías y análisis de viabilidad).
**Tiempo total:** 4 h.

### Fase 4 — Diseño de la arquitectura aplicada al proyecto
**Objetivo:** definir cómo se aplica la Hexagonal al conversor.

| Actividad | Horas |
|---|---|
| Identificar piezas del dominio | 1.5 |
| Definir puertos de entrada y salida | 2 |
| Definir adaptadores primarios y secundarios | 1.5 |
| Elaborar diagrama, flujo y estructura de carpetas | 2 |
| Relacionar los RNF con los mecanismos arquitectónicos | 1 |

**Recursos:** herramienta de diagramas.
**Entregable:** sección 8 completa (diagrama, puertos, adaptadores, flujo, carpetas).
**Tiempo total:** 8 h.

### Fase 5 — Planificación: cronograma, recursos, riesgos y entregables
**Objetivo:** organizar la ejecución del proyecto.

| Actividad | Horas |
|---|---|
| Estimar tiempos y elaborar el cronograma | 1 |
| Identificar y valorar riesgos con su mitigación | 1.5 |
| Consolidar recursos y entregables | 1 |
| Elaborar la hoja de ruta de implementación | 0.5 |

**Recursos:** este documento.
**Entregable:** secciones 12 a 16.
**Tiempo total:** 4 h.

### Fase 6 — Revisión y entrega
**Objetivo:** verificar que la propuesta esté completa y coherente.

| Actividad | Horas |
|---|---|
| Revisar coherencia entre requerimientos, arquitectura y plan | 2 |
| Evaluar la pertinencia y redactar conclusiones | 1 |
| Corregir formato y entregar | 1 |

**Entregable:** documento final.
**Tiempo total:** 4 h.

**Total de análisis y planificación: 30 horas.**

---

## 12. Cronograma

> Supone 6 a 8 horas de dedicación por semana. Las semanas son relativas al inicio del trabajo.

| Semana | Fases / actividades | Horas aprox. |
|---|---|---|
| Semana 1 | Fase 1 (fundamentación) y Fase 2 (requerimientos) | 10 |
| Semana 2 | Fase 3 (viabilidad y herramientas) y Fase 4 (diseño) | 12 |
| Semana 3 | Fase 5 (planificación) y Fase 6 (revisión y entrega) | 8 |
| Semanas 4 a 6 | Implementación según la hoja de ruta (sección 16), opcional o posterior | ~29 |

**Duración del análisis y la planificación:** 3 semanas.
**Duración total incluyendo la implementación:** unas 6 semanas.

---

## 13. Recursos necesarios

| Tipo | Recurso |
|---|---|
| **Humanos** | 1 estudiante (análisis, diseño, desarrollo, pruebas y documentación) |
| **Hardware** | Computador personal con conexión a internet |
| **Software** | Lenguaje de programación, editor de código, Git, herramienta de diagramas, herramienta de pruebas |
| **Servicios externos** | API pública gratuita de tasas de cambio; GitHub para el repositorio |
| **Información** | Artículos y libros sobre Hexagonal, Clean y Onion; documentación de la API |
| **Económicos** | Sin costo (software libre y servicios gratuitos) |
| **Tiempo** | ~30 h de análisis y planificación + ~29 h de implementación |

---

## 14. Riesgos potenciales

Escala: **Probabilidad** y **Impacto** en Baja / Media / Alta.

| ID | Riesgo | Prob. | Impacto | Mitigación |
|---|---|---|---|---|
| R1 | La API gratuita no soporta alguna moneda necesaria (por ejemplo, COP) | Media | Alto | Verificar la cobertura en la Fase 3 antes de elegir la API; tener una API alternativa. |
| R2 | La API cambia su formato, impone límites o deja de ser gratuita | Media | Medio | Aislarla en un adaptador; mantener `FakeExchangeRateProvider`. |
| R3 | El núcleo termina usando librerías externas o el formato de la API | Media | Alto | Revisión de imports de `core/`; traducir la respuesta dentro del adaptador. |
| R4 | Los puertos se ubican en la carpeta de adaptadores | Media | Medio | Regla: los puertos viven en `core/`, los adaptadores solo los implementan. |
| R5 | Sobreingeniería o ampliación del alcance | Media | Medio | Respetar el alcance de la sección 6; las funciones extra son opcionales. |
| R6 | Curva de aprendizaje mayor a la prevista | Media | Medio | Hacer primero la Fase 1; empezar por el dominio y los casos de uso con adaptadores falsos. |
| R7 | Retrasos por poca disponibilidad de tiempo | Media | Medio | Cronograma por semanas con holgura; priorizar fases 1 a 4 de la implementación. |
| R8 | Pruebas inestables por depender de internet | Baja | Medio | Probar el núcleo siempre con adaptadores falsos. |
| R9 | Errores por usar números de punto flotante en dinero | Baja | Medio | Usar tipos decimales en `Money`. |
| R10 | Pérdida de archivos o trabajo | Baja | Alto | Control de versiones con Git y copia en GitHub. |

---

## 15. Entregables

| Fase | Entregable | Formato |
|---|---|---|
| 1 | Fundamentación de la arquitectura (descripción, principios, componentes, ventajas y desventajas) | Documento Markdown |
| 2 | Descripción del proyecto, RF y RNF | Documento Markdown |
| 3 | Tabla de tecnologías y análisis de viabilidad | Documento Markdown |
| 4 | Diseño de la arquitectura aplicada (diagrama, puertos, adaptadores, flujo, estructura de carpetas) | Documento y diagrama |
| 5 | Cronograma, recursos, riesgos, entregables y hoja de ruta | Documento Markdown |
| 6 | **Propuesta técnica final** | Este documento |
| Futuro | Aplicación implementada, pruebas y README | Repositorio Git |

---

## 16. Hoja de ruta para la implementación

> Planificación de la implementación futura. Cada fase termina con un resultado verificable.

| Fase | Actividades | Resultado verificable | Horas |
|---|---|---|---|
| **I-0. Preparación** | Elegir lenguaje y herramientas, probar la API a mano, crear la estructura de carpetas y el repositorio | Proyecto vacío con estructura y primer commit | 3 |
| **I-1. Dominio** | Implementar `CurrencyCode`, `Money`, `ExchangeRate`, `Conversion` con sus pruebas | Pruebas del dominio aprobadas; `core/domain` sin imports externos | 4 |
| **I-2. Puertos y casos de uso** | Definir los 4 puertos, implementar los servicios, probar con adaptadores falsos | Casos de uso funcionando sin internet, archivos ni consola | 5 |
| **I-3. Adaptadores secundarios** | Fake y en memoria; adaptador HTTP con manejo de errores; repositorio en archivo | Dos adaptadores por cada puerto de salida, con pruebas | 8 |
| **I-4. Adaptador primario y composition root** | Controlador de consola y `main` que inyecta las dependencias | Aplicación funcionando de punta a punta | 4 |
| **I-5. Demostración y documentación** | Cambiar adaptadores sin tocar el núcleo, verificar la regla de dependencia, README y diagrama | Evidencia de que la arquitectura funciona y documentación final | 5 |
| **Total** | | | **29 h** |

**Extensiones opcionales (si sobra tiempo):** una API REST como segundo adaptador primario; cachear la última tasa consultada como nuevo adaptador secundario; un segundo proveedor de tasas.

---

## 17. Criterios de éxito

**Del análisis y la planificación**
- [ ] Se describen la arquitectura, sus principios, componentes, ventajas y desventajas.
- [ ] Se identifican RF y RNF, y los RNF prioritarios justifican la arquitectura.
- [ ] Se define cómo se aplican los puertos y adaptadores al proyecto.
- [ ] Hay análisis de viabilidad y pertinencia.
- [ ] Hay actividades por fase, recursos, tiempos, riesgos y entregables.
- [ ] Existe una hoja de ruta para implementar.

**De la implementación futura**
- [ ] Se puede convertir un monto y consultar el historial.
- [ ] El núcleo no importa HTTP, base de datos ni consola.
- [ ] Hay al menos dos adaptadores por cada puerto de salida.
- [ ] Se cambia de adaptador sin modificar el núcleo.
- [ ] Los casos de uso se prueban sin internet.

---

## 18. Conclusiones

- La arquitectura Hexagonal aísla la lógica de negocio mediante **puertos** (interfaces definidas por el núcleo) y **adaptadores** (implementaciones concretas), siguiendo la regla de que las dependencias apuntan hacia el núcleo.
- El conversor de monedas con historial es un caso adecuado para estudiarla: tiene una dependencia externa real (la API) y persistencia, y permite demostrar el intercambio de adaptadores sin modificar el núcleo.
- El proyecto es **viable** con recursos gratuitos y una dedicación moderada.
- La arquitectura es **pertinente como ejercicio de aprendizaje**; en un producto real solo se justificaría si se prevén cambios de proveedores, nuevas interfaces o crecimiento de las reglas de negocio.
- Los principales riesgos están en la API externa y en el mal uso de la arquitectura, y se mitigan aislando la API en un adaptador y verificando la regla de dependencia.

---

## 19. Referencias

- Cockburn, A. (2005). *Hexagonal Architecture*. alistair.cockburn.us
- Martin, R. C. (2012). *The Clean Architecture*. Blog de Clean Coder.
- Palermo, J. (2008). *The Onion Architecture* (serie de artículos). jeffreypalermo.com
- Martin, R. C. (2017). *Clean Architecture: A Craftsman's Guide to Software Structure and Design*. Prentice Hall.
- Documentación oficial de la API de tasas de cambio elegida (consultar la versión vigente).
