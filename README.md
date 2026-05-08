# La Cocina de Kojo — Simulación de Eventos Discretos

Proyecto académico de simulación de eventos discretos (DES) para comparar
dos políticas de personal en un puesto de comida rápida.

## Problema

El administrador de Kojo's Kitchen (10 am – 9 pm) quiere reducir el número
de clientes que esperan más de 5 minutos.  Se comparan dos políticas:

| Escenario | Personal |
|-----------|----------|
| **A** — situación actual | 2 empleados todo el día |
| **B** — propuesta | 2 empleados base + 1 extra en horas pico |

**Resultado principal (30 réplicas, CRN):**
Escenario B reduce el % de clientes insatisfechos de **16.7 %** a **3.1 %**
(p = 1.12 × 10⁻¹¹, t-test pareado).

## Ejecución rápida

```bash
pip install -r requirements.txt
python main.py          # corre 30 réplicas y genera las figuras
pytest tests/ -v        # 44 tests
```

## Estructura del proyecto

```
src/
  rng/          → LCG (Knuth) + transformada inversa + streams CRN
  engine/       → Lista de Eventos Futuros (min-heap)
  model/        → KojoKitchen, Customer, Employee, SimulationConfig
  metrics/      → MetricsCollector + ReplicationResult
  experiments/  → runner (réplicas independientes) + scenarios (CRN)
  analysis/     → statistics (IC, t-test, parada) + plots (6 figuras)
report/
  main.tex      → informe LaTeX
  main.pdf      → informe compilado
  figures/      → figuras generadas por main.py
tests/          → 44 tests (rng, engine, model, integración)
main.py         → punto de entrada
```

## Informe

El informe completo (LaTeX + PDF compilado) está en `report/`.
Secciones: Introducción · Implementación · Resultados · Modelo Matemático · Conclusiones.

## Asignatura

Simulación de Eventos Discretos — Facultad de Matemática y Computación,
Universidad de La Habana.
