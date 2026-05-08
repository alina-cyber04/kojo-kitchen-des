from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from scipy import stats

from src.analysis.statistics import (
    confidence_interval,
    stopping_analysis,
    summarize_results,
)
from src.experiments.runner import run_experiment
from src.metrics.collector import ReplicationResult
from src.model.config import SimulationConfig, SCENARIO_A, SCENARIO_B

# ── Paleta de colores accesible (funciona en B/N y con daltonismo) ──────────
COLOR_A = "#2196F3"   # azul  — Escenario A
COLOR_B = "#F44336"   # rojo  — Escenario B
ALPHA_TRACE = 0.18    # transparencia para trayectorias individuales

# ── Configuración de publicación aplicada al importar el módulo ─────────────
_STYLE: dict = {
    "font.size":        10,
    "axes.titlesize":   11,
    "axes.labelsize":   10,
    "xtick.labelsize":   9,
    "ytick.labelsize":   9,
    "legend.fontsize":   9,
    "lines.linewidth":   1.8,
    "lines.markersize":  5,
    "figure.dpi":       130,
    "savefig.dpi":      300,
    "savefig.bbox":    "tight",
    "axes.spines.top":  False,
    "axes.spines.right": False,
    "axes.grid":        True,
    "grid.alpha":       0.3,
    "grid.linewidth":   0.5,
}
plt.rcParams.update(_STYLE)


# ── Helpers privados ─────────────────────────────────────────────────────────

def _save(fig: plt.Figure, output_dir: str | Path, name: str) -> Path:
    """Guarda la figura en output_dir/name.png a 300 DPI y devuelve la ruta."""
    path = Path(output_dir) / f"{name}.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path)
    plt.close(fig)
    return path


def _error_bars(mean: float, lo: float, hi: float) -> tuple[float, float]:
    """Convierte (mean, lo, hi) al formato [[below], [above]] de matplotlib."""
    return mean - lo, hi - mean


# ── Figura 1 — Barras comparativas con IC 95% ────────────────────────────────

def plot_comparison_bars(
    summary_a: dict,
    summary_b: dict,
    comparison: dict,
    ax: Optional[plt.Axes] = None,
) -> plt.Figure:
    """Barras de % > 5 min para A y B con barras de error = IC 95%.

    Añade la línea de significancia estadística y el p-value sobre las barras.
    """
    standalone = ax is None
    if standalone:
        fig, ax = plt.subplots(figsize=(5, 4))
    else:
        fig = ax.get_figure()

    sa = summary_a["pct_over_5min"]
    sb = summary_b["pct_over_5min"]

    means  = [sa["mean"],  sb["mean"]]
    below  = [_error_bars(sa["mean"], sa["lower"], sa["upper"])[0],
              _error_bars(sb["mean"], sb["lower"], sb["upper"])[0]]
    above  = [_error_bars(sa["mean"], sa["lower"], sa["upper"])[1],
              _error_bars(sb["mean"], sb["lower"], sb["upper"])[1]]

    bars = ax.bar(
        [0, 1], means,
        yerr=[below, above],
        color=[COLOR_A, COLOR_B],
        width=0.5,
        capsize=6,
        error_kw={"linewidth": 1.5, "capthick": 1.5},
        zorder=3,
    )

    # Línea de significancia estadística entre las dos barras
    y_sig = max(sa["upper"], sb["upper"]) * 1.08
    ax.plot([0, 0, 1, 1], [y_sig * 0.97, y_sig, y_sig, y_sig * 0.97],
            color="black", linewidth=1.2)
    p = comparison["p_value"]
    stars = "***" if p < 0.001 else ("**" if p < 0.01 else "*")
    ax.text(0.5, y_sig * 1.02, f"p = {p:.2e} {stars}",
            ha="center", va="bottom", fontsize=9)

    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Escenario A\n(2 empleados)", "Escenario B\n(2+1 en pico)"])
    ax.set_ylabel("% clientes con espera > 5 min")
    ax.set_title("Métrica principal: clientes insatisfechos")
    ax.set_xlim(-0.6, 1.6)

    if standalone:
        fig.tight_layout()
    return fig


# ── Figura 2 — Box plots con notches ─────────────────────────────────────────

def plot_wait_boxplots(
    results: dict[str, list[ReplicationResult]],
    ax: Optional[plt.Axes] = None,
) -> plt.Figure:
    """Box plots (con notches = IC 95% de la mediana) de avg_wait_time."""
    standalone = ax is None
    if standalone:
        fig, ax = plt.subplots(figsize=(5, 4))
    else:
        fig = ax.get_figure()

    data_a = [r.avg_wait_time for r in results["A"]]
    data_b = [r.avg_wait_time for r in results["B"]]

    bp = ax.boxplot(
        [data_a, data_b],
        notch=True,
        bootstrap=5_000,
        patch_artist=True,
        widths=0.45,
        medianprops={"color": "white", "linewidth": 2},
        whiskerprops={"linewidth": 1.2},
        capprops={"linewidth": 1.2},
        flierprops={"marker": "o", "markersize": 4, "alpha": 0.5},
    )
    bp["boxes"][0].set_facecolor(COLOR_A)
    bp["boxes"][1].set_facecolor(COLOR_B)

    ax.set_xticks([1, 2])
    ax.set_xticklabels(["Escenario A\n(2 empleados)", "Escenario B\n(2+1 en pico)"])
    ax.set_ylabel("Tiempo de espera medio (min)")
    ax.set_title("Distribución del tiempo de espera (30 réplicas)")

    patch_a = mpatches.Patch(color=COLOR_A, label="A — IC 95% mediana (notch)")
    patch_b = mpatches.Patch(color=COLOR_B, label="B — IC 95% mediana (notch)")
    ax.legend(handles=[patch_a, patch_b], fontsize=8)

    if standalone:
        fig.tight_layout()
    return fig


# ── Figura 3 — Convergencia (análisis de parada) ─────────────────────────────

def plot_convergence(
    results: dict[str, list[ReplicationResult]],
    ax: Optional[plt.Axes] = None,
) -> plt.Figure:
    """Media acumulada de pct_over_5min réplica a réplica para A y B.

    Muestra visualmente cuándo el estimador se estabiliza.
    Conecta con stopping_analysis() de statistics.py.
    """
    standalone = ax is None
    if standalone:
        fig, ax = plt.subplots(figsize=(6, 4))
    else:
        fig = ax.get_figure()

    stop_a = stopping_analysis(results["A"])
    stop_b = stopping_analysis(results["B"])

    x = list(range(1, len(stop_a["cumulative_means"]) + 1))

    ax.plot(x, stop_a["cumulative_means"], color=COLOR_A,
            marker="o", markersize=3, label="Escenario A")
    ax.plot(x, stop_b["cumulative_means"], color=COLOR_B,
            marker="s", markersize=3, label="Escenario B")

    # Líneas de la media final (estimación convergida)
    ax.axhline(stop_a["cumulative_means"][-1], color=COLOR_A,
               linestyle="--", alpha=0.45, linewidth=1)
    ax.axhline(stop_b["cumulative_means"][-1], color=COLOR_B,
               linestyle="--", alpha=0.45, linewidth=1)

    # Anotar media final
    n = len(x)
    ax.annotate(f'{stop_a["cumulative_means"][-1]:.1f}%',
                xy=(n, stop_a["cumulative_means"][-1]),
                xytext=(n - 4, stop_a["cumulative_means"][-1] + 1.5),
                fontsize=8, color=COLOR_A)
    ax.annotate(f'{stop_b["cumulative_means"][-1]:.1f}%',
                xy=(n, stop_b["cumulative_means"][-1]),
                xytext=(n - 4, stop_b["cumulative_means"][-1] + 1.5),
                fontsize=8, color=COLOR_B)

    ax.set_xlabel("Número de réplicas")
    ax.set_ylabel("Media acumulada de % > 5 min")
    ax.set_title("Convergencia del estimador (análisis de parada)")
    ax.legend()

    if standalone:
        fig.tight_layout()
    return fig


# ── Figura 4 — Utilización de empleados ──────────────────────────────────────

def plot_utilization(
    summary_a: dict,
    summary_b: dict,
    ax: Optional[plt.Axes] = None,
) -> plt.Figure:
    """Utilización media de empleados con IC 95% para A y B."""
    standalone = ax is None
    if standalone:
        fig, ax = plt.subplots(figsize=(5, 4))
    else:
        fig = ax.get_figure()

    ua = summary_a["avg_utilization"]
    ub = summary_b["avg_utilization"]

    means  = [ua["mean"] * 100, ub["mean"] * 100]
    below  = [(ua["mean"] - ua["lower"]) * 100,
              (ub["mean"] - ub["lower"]) * 100]
    above  = [(ua["upper"] - ua["mean"]) * 100,
              (ub["upper"] - ub["mean"]) * 100]

    ax.bar(
        [0, 1], means,
        yerr=[below, above],
        color=[COLOR_A, COLOR_B],
        width=0.5,
        capsize=6,
        error_kw={"linewidth": 1.5, "capthick": 1.5},
        zorder=3,
    )

    # Línea de referencia al 100% (saturación)
    ax.axhline(100, color="black", linestyle=":", linewidth=1, alpha=0.5,
               label="Saturación (100%)")

    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Escenario A\n(2 empleados)", "Escenario B\n(2+1 en pico)"])
    ax.set_ylabel("Utilización media de empleados (%)")
    ax.set_title("Utilización del personal")
    ax.set_ylim(0, 110)
    ax.legend(fontsize=8)

    if standalone:
        fig.tight_layout()
    return fig


# ── Figura 5 — Trayectorias individuales de las 30 réplicas ──────────────────

def plot_replication_traces(
    results: dict[str, list[ReplicationResult]],
    ax: Optional[plt.Axes] = None,
) -> plt.Figure:
    """Scatter de pct_over_5min por réplica con media como línea gruesa.

    Muestra la variabilidad real entre réplicas (patrón DES RAP Book).
    """
    standalone = ax is None
    if standalone:
        fig, ax = plt.subplots(figsize=(6, 4))
    else:
        fig = ax.get_figure()

    for label, color, key in [("A", COLOR_A, "A"), ("B", COLOR_B, "B")]:
        values = [r.pct_over_5min for r in results[key]]
        n = len(values)
        x = list(range(1, n + 1))

        # Puntos individuales (tenues)
        ax.scatter(x, values, color=color, alpha=ALPHA_TRACE * 3,
                   s=22, zorder=2)

        # Media como línea gruesa
        mean_val = np.mean(values)
        ax.axhline(mean_val, color=color, linewidth=2,
                   label=f"Escenario {label} — media: {mean_val:.1f}%", zorder=3)

        # Banda del IC 95%
        _, lo, hi = confidence_interval(values)
        ax.axhspan(lo, hi, color=color, alpha=0.08, zorder=1)

    ax.set_xlabel("Réplica")
    ax.set_ylabel("% clientes con espera > 5 min")
    ax.set_title("Resultados individuales de las 30 réplicas")
    ax.legend()

    if standalone:
        fig.tight_layout()
    return fig


# ── Figura 6 — Análisis de sensibilidad (variar λ_pico) ──────────────────────

def plot_sensitivity(
    output_dir: str | Path,
    ax: Optional[plt.Axes] = None,
    n_reps: int = 10,
    base_seed: int = 42,
) -> plt.Figure:
    """Variación de λ_pico de 0.10 a 0.50 y su impacto en % > 5 min.

    Responde: ¿a partir de qué tasa de llegada deja de ser suficiente
    el tercer empleado? Obligatorio por sim_proy_1.md.

    n_reps: réplicas por punto (10 es suficiente para la tendencia).
    """
    standalone = ax is None
    if standalone:
        fig, ax = plt.subplots(figsize=(6, 4))
    else:
        fig = ax.get_figure()

    lambdas = np.arange(0.10, 0.52, 0.05)
    means_a, means_b = [], []
    ci_lo_a, ci_hi_a = [], []
    ci_lo_b, ci_hi_b = [], []

    for lam in lambdas:
        cfg_a = SimulationConfig(lambda_peak=float(lam), base_staff=2, extra_staff=0)
        cfg_b = SimulationConfig(lambda_peak=float(lam), base_staff=2, extra_staff=1)

        res_a = run_experiment(cfg_a, n_reps, base_seed)
        res_b = run_experiment(cfg_b, n_reps, base_seed)

        pct_a = [r.pct_over_5min for r in res_a]
        pct_b = [r.pct_over_5min for r in res_b]

        m_a, lo_a, hi_a = confidence_interval(pct_a)
        m_b, lo_b, hi_b = confidence_interval(pct_b)

        means_a.append(m_a); ci_lo_a.append(lo_a); ci_hi_a.append(hi_a)
        means_b.append(m_b); ci_lo_b.append(lo_b); ci_hi_b.append(hi_b)

    lambdas = lambdas.tolist()

    # Líneas de media
    ax.plot(lambdas, means_a, color=COLOR_A, marker="o",
            markersize=4, label="Escenario A (2 emp.)")
    ax.plot(lambdas, means_b, color=COLOR_B, marker="s",
            markersize=4, label="Escenario B (2+1 pico)")

    # Bandas de IC
    ax.fill_between(lambdas, ci_lo_a, ci_hi_a, color=COLOR_A, alpha=0.15)
    ax.fill_between(lambdas, ci_lo_b, ci_hi_b, color=COLOR_B, alpha=0.15)

    # Línea vertical en el valor del problema
    ax.axvline(0.30, color="gray", linestyle="--", linewidth=1.2,
               label="λ del problema (0.30)")

    ax.set_xlabel("λ pico (clientes/min)")
    ax.set_ylabel("% clientes con espera > 5 min")
    ax.set_title("Sensibilidad a la tasa de llegada en hora pico")
    ax.legend(fontsize=8)

    if standalone:
        fig.tight_layout()
    return fig


# ── Figura 7 — Dashboard 2×2 (figura principal del informe) ──────────────────

def plot_dashboard(
    results: dict[str, list[ReplicationResult]],
    summary_a: dict,
    summary_b: dict,
    comparison: dict,
) -> plt.Figure:
    """Figura 2×2 con las 4 métricas principales. Figura principal del informe."""
    fig, axes = plt.subplots(2, 2, figsize=(12, 9))
    fig.suptitle(
        "La Cocina de Kojo — Análisis Comparativo de Escenarios (n = 30 réplicas)",
        fontsize=13, y=1.01,
    )

    plot_comparison_bars(summary_a, summary_b, comparison, ax=axes[0, 0])
    plot_wait_boxplots(results, ax=axes[0, 1])
    plot_convergence(results, ax=axes[1, 0])
    plot_utilization(summary_a, summary_b, ax=axes[1, 1])

    fig.tight_layout()
    return fig


# ── Facade pública ────────────────────────────────────────────────────────────

def generate_all_plots(
    results: dict[str, list[ReplicationResult]],
    output_dir: str | Path = "report/figures",
) -> list[Path]:
    """Genera las 6 figuras y las guarda en output_dir.

    Returns lista de rutas de los archivos generados.
    """
    from src.analysis.statistics import compare_scenarios as _compare

    output_dir = Path(output_dir)
    summary_a  = summarize_results(results["A"])
    summary_b  = summarize_results(results["B"])
    comparison = _compare(results["A"], results["B"])

    saved: list[Path] = []

    print("  [1/6] Dashboard 2×2...")
    saved.append(_save(
        plot_dashboard(results, summary_a, summary_b, comparison),
        output_dir, "dashboard",
    ))

    print("  [2/6] Barras comparativas...")
    saved.append(_save(
        plot_comparison_bars(summary_a, summary_b, comparison),
        output_dir, "comparison_bars",
    ))

    print("  [3/6] Box plots de tiempos de espera...")
    saved.append(_save(
        plot_wait_boxplots(results),
        output_dir, "wait_boxplots",
    ))

    print("  [4/6] Convergencia del estimador...")
    saved.append(_save(
        plot_convergence(results),
        output_dir, "convergence",
    ))

    print("  [5/6] Trayectorias individuales de réplicas...")
    saved.append(_save(
        plot_replication_traces(results),
        output_dir, "replication_traces",
    ))

    print("  [6/6] Analisis de sensibilidad (lambda_pico)...")
    saved.append(_save(
        plot_sensitivity(output_dir),
        output_dir, "sensitivity",
    ))

    return saved
