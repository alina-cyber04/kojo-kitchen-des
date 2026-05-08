"""Punto de entrada de la simulación La Cocina de Kojo.

Uso:
    python main.py

Corre 30 réplicas de cada escenario (CRN), imprime la tabla de resultados,
ejecuta el análisis estadístico y genera las 6 figuras en report/figures/.
"""

from __future__ import annotations

from pathlib import Path

from src.analysis.plots import generate_all_plots
from src.analysis.statistics import (
    compare_scenarios,
    stopping_analysis,
    summarize_results,
)
from src.experiments.scenarios import compare_scenarios as run_scenarios
from src.model.config import SCENARIO_A, SCENARIO_B


# ── Configuración del experimento ────────────────────────────────────────────
N_REPLICATIONS = 30
BASE_SEED      = 42
OUTPUT_DIR     = Path("report/figures")


# ── Helpers de presentación ──────────────────────────────────────────────────

def _ci_str(summary: dict, key: str, pct: bool = False) -> str:
    """Formatea 'media [lo, hi]' para la tabla de resultados."""
    s = summary[key]
    scale = 1.0
    fmt   = ".3f"
    if pct:
        scale = 1.0   # ya están en porcentaje
        fmt   = ".2f"
    m  = s["mean"]  * scale
    lo = s["lower"] * scale
    hi = s["upper"] * scale
    return f"{m:{fmt}}  [{lo:{fmt}}, {hi:{fmt}}]"


def _print_header(title: str) -> None:
    width = 66
    print()
    print("=" * width)
    print(f"  {title}")
    print("=" * width)


def _print_table(summary_a: dict, summary_b: dict) -> None:
    _print_header("Resultados por escenario  —  media  [IC 95%]")

    rows = [
        ("% clientes > 5 min  (%)",  "pct_over_5min",    True),
        ("Tiempo espera medio (min)", "avg_wait_time",    False),
        ("Tiempo espera max   (min)", "max_wait_time",    False),
        ("Long. media de cola",       "avg_queue_length", False),
        ("Utilizacion empleados (%)", "avg_utilization",  True),
    ]

    col = 32
    print(f"  {'Metrica':<{col}}  {'Escenario A':<26}  {'Escenario B'}")
    print(f"  {'-'*col}  {'-'*26}  {'-'*26}")

    for label, key, pct in rows:
        if key == "avg_utilization":
            # Convertir a porcentaje para la tabla
            def _util_str(s: dict) -> str:
                m  = s["mean"]  * 100
                lo = s["lower"] * 100
                hi = s["upper"] * 100
                return f"{m:.2f}  [{lo:.2f}, {hi:.2f}]"
            a_str = _util_str(summary_a[key])
            b_str = _util_str(summary_b[key])
        else:
            a_str = _ci_str(summary_a, key, pct)
            b_str = _ci_str(summary_b, key, pct)
        print(f"  {label:<{col}}  {a_str:<26}  {b_str}")


def _print_comparison(comp: dict) -> None:
    _print_header("Comparacion estadistica  —  t-test pareado (CRN)")
    print(f"  Diferencia media (A - B): {comp['mean_diff']:.2f} puntos porcentuales")
    print(f"  IC 95% diferencia:        [{comp['ci_diff'][0]:.2f}, {comp['ci_diff'][1]:.2f}]")
    print(f"  Estadistico t:            {comp['t_stat']:.4f}")
    print(f"  p-value:                  {comp['p_value']:.2e}")
    print(f"  Significativo (alfa=0.05): {'SI' if comp['significant'] else 'NO'}")
    print(f"  Correlacion CRN (rho):    {comp['correlation']:.3f}")
    if comp["ci_diff"][0] > 0:
        print()
        print("  CONCLUSION: el IC de la diferencia no contiene el 0.")
        print("  El Escenario B reduce significativamente el % de clientes")
        print("  que esperan mas de 5 minutos.")


def _print_stopping(stop_a: dict, stop_b: dict) -> None:
    _print_header("Analisis de parada  —  criterio semi-anchura relativa 5%")
    for label, stop in [("A", stop_a), ("B", stop_b)]:
        print(f"  Escenario {label}:")
        print(f"    Replicas ejecutadas:   {stop['n_actual']}")
        print(f"    Replicas requeridas:   {stop['n_required']}")
        print(f"    Semi-anchura IC:       {stop['half_width']:.3f} pp")
        print(f"    Precision relativa:    {stop['relative_precision']:.1%}")
        suf = "SI" if stop["sufficient"] else "NO (varianza alta — test sig. de todas formas)"
        print(f"    Criterio cumplido:     {suf}")
        print()


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    print()
    print("=" * 66)
    print("  La Cocina de Kojo  —  Simulacion de Eventos Discretos")
    print(f"  {N_REPLICATIONS} replicas  |  seed base = {BASE_SEED}  |  CRN activado")
    print("=" * 66)

    # 1. Correr simulaciones
    print(f"\nCorriendo {N_REPLICATIONS} replicas de cada escenario...")
    results = run_scenarios(n_replications=N_REPLICATIONS, base_seed=BASE_SEED)
    print(f"  Escenario A: {len(results['A'])} replicas completadas")
    print(f"  Escenario B: {len(results['B'])} replicas completadas")

    # 2. Estadísticos
    summary_a  = summarize_results(results["A"])
    summary_b  = summarize_results(results["B"])
    comparison = compare_scenarios(results["A"], results["B"])
    stop_a     = stopping_analysis(results["A"])
    stop_b     = stopping_analysis(results["B"])

    # 3. Imprimir resultados
    _print_table(summary_a, summary_b)
    _print_comparison(comparison)
    _print_stopping(stop_a, stop_b)

    # 4. Generar figuras
    _print_header("Generando figuras")
    paths = generate_all_plots(results, output_dir=OUTPUT_DIR)
    for p in paths:
        size_kb = p.stat().st_size / 1024
        print(f"  {p.name:<30}  {size_kb:6.1f} KB")

    print()
    print("=" * 66)
    print(f"  Listo. {len(paths)} figuras guardadas en {OUTPUT_DIR}/")
    print("=" * 66)
    print()


if __name__ == "__main__":
    main()
