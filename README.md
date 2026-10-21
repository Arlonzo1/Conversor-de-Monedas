# Conversor de Monedas con Historial

Proyecto individual de la asignatura **Arquitectura de Software**, de Ingeniería de Software en la Fundación Escuela Tecnológica de Neiva "Jesús Oviedo Pérez".

Es un caso de estudio de **arquitectura hexagonal (puertos y adaptadores)**: una aplicación de consola que convierte montos entre monedas con tasas reales y guarda un historial.

| Contenido | Descripción |
|---|---|
| [propuesta-tecnica-arquitectura-hexagonal.md](propuesta-tecnica-arquitectura-hexagonal.md) | Análisis y planificación: arquitectura, requerimientos, diseño, riesgos y hoja de ruta |
| [avance-implementacion.md](avance-implementacion.md) | Estado de la implementación por fase y trazabilidad de requerimientos |
| [conversor-monedas/](conversor-monedas/) | Código fuente y pruebas (ver su [README](conversor-monedas/README.md)) |

## Inicio rápido

```bash
cd conversor-monedas
python main.py 100 USD COP          # requiere Python 3.11+, sin dependencias externas
python -m pip install -r requirements-dev.txt
python -m pytest                    # 129 pruebas, sin internet
```

**Autor:** Arlen Jose Perdomo Rojas
