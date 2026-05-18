from __future__ import annotations

import math

import numpy as np
from scipy import stats

from src.metrics.collector import ReplicationResult


# ── Tipos auxiliares ───────────────────────────────────────────────────────────

CIResult = tuple[float, float, float]   # (mean, lower, upper)


# ── Funciones públicas ─────────────────────────────────────────────────────────

def confidence_interval(data: list[float], confidence: float = 0.95) -> CIResult:
    """Calcula el intervalo de confianza para la media de una muestra.

    Usa la distribución t de Student con df = n-1 porque la varianza
    poblacional es desconocida. Fórmula: IC = x̄ ± t(α/2, n-1) × (s/√n).

    Args:
        data: Observaciones de la muestra.
        confidence: Nivel de confianza deseado (por defecto 0.95).

    Returns:
        Tupla (media, límite inferior, límite superior).
    """
    arr = np.asarray(data, dtype=float)
    n = len(arr)
    if n < 2:
        mean = float(arr[0]) if n == 1 else float("nan")
        return mean, mean, mean

    mean = float(np.mean(arr))
    sem  = float(stats.sem(arr))          # desviación estándar / √n

    # Varianza cero: todos los valores son iguales, CI puntual
    if sem == 0.0:
        return mean, mean, mean

    lo, hi = stats.t.interval(confidence, df=n - 1, loc=mean, scale=sem)
    return mean, float(lo), float(hi)


def summarize_results(results: list[ReplicationResult]) -> dict:
    """Calcula media e IC 95 % para cada métrica de salida.

    Args:
        results: Lista de resultados de réplicas del mismo escenario.

    Returns:
        Diccionario con claves pct_over_5min, avg_wait_time, max_wait_time,
        avg_queue_length, avg_utilization. Cada valor es un dict con
        las claves 'mean', 'lower', 'upper', 'std', 'n'.
    """
    def _stats(values: list[float]) -> dict:
        mean, lo, hi = confidence_interval(values)
        return {
            "mean":  mean,
            "lower": lo,
            "upper": hi,
            "std":   float(np.std(values, ddof=1)),
            "n":     len(values),
        }

    # Extraer arrays de cada métrica
    pct      = [r.pct_over_5min    for r in results]
    wait     = [r.avg_wait_time    for r in results]
    max_wait = [r.max_wait_time    for r in results]
    q_len    = [r.avg_queue_length for r in results]
    util     = [float(np.mean(r.employee_utilizations)) for r in results]

    return {
        "pct_over_5min":    _stats(pct),
        "avg_wait_time":    _stats(wait),
        "max_wait_time":    _stats(max_wait),
        "avg_queue_length": _stats(q_len),
        "avg_utilization":  _stats(util),
    }


def compare_scenarios(
    results_a: list[ReplicationResult],
    results_b: list[ReplicationResult],
) -> dict:
    """Compara dos escenarios usando t-test pareado sobre réplicas CRN.

    Con CRN las réplicas están positivamente correlacionadas, por lo que
    el test correcto es ttest_rel (pareado). Trabaja sobre las diferencias
    D_i = A_i - B_i para la métrica pct_over_5min.

    H₀: μ_D = 0 (escenarios equivalentes) — test bilateral.

    Args:
        results_a: Resultados del Escenario A, alineados con results_b.
        results_b: Resultados del Escenario B, alineados con results_a.

    Returns:
        Diccionario con claves t_stat, p_value, mean_diff, ci_diff
        (tupla lower-upper), significant (bool al 5 %) y correlation (ρ).
    """
    pct_a = np.asarray([r.pct_over_5min for r in results_a], dtype=float)
    pct_b = np.asarray([r.pct_over_5min for r in results_b], dtype=float)

    # t-test pareado
    t_stat, p_value = stats.ttest_rel(pct_a, pct_b)

    # CI de la diferencia media D̄ = Ā - B̄
    diffs = pct_a - pct_b
    mean_diff, lo_diff, hi_diff = confidence_interval(diffs.tolist())

    # Correlación entre A y B (muestra el beneficio del CRN)
    corr, _ = stats.pearsonr(pct_a, pct_b)

    return {
        "t_stat":      float(t_stat),
        "p_value":     float(p_value),
        "mean_diff":   mean_diff,
        "ci_diff":     (lo_diff, hi_diff),
        "significant": bool(p_value < 0.05),
        "correlation": float(corr),
    }


def stopping_analysis(results: list[ReplicationResult]) -> dict:
    """Determina si n réplicas son suficientes para el nivel de precisión pedido.

    Aplica el criterio de semi-anchura relativa con r = 0.05 (5 %):
        h = t(α/2, n-1) × s/√n          — semi-anchura del IC actual
        n* = ⌈(t × s / (r × x̄))²⌉      — réplicas necesarias para precisión r

    n* ≤ n_actual indica que el criterio se satisface. También devuelve
    las medias acumuladas réplica a réplica para el gráfico de convergencia.

    Args:
        results: Lista de resultados de réplicas del mismo escenario.

    Returns:
        Diccionario con claves n_actual, n_required, sufficient, half_width,
        relative_precision y cumulative_means.
    """
    pct = np.asarray([r.pct_over_5min for r in results], dtype=float)
    n   = len(pct)
    r   = 0.05   # precisión relativa deseada: 5 %

    mean, lo, hi = confidence_interval(pct.tolist())
    half_width   = (hi - lo) / 2.0

    # Réplicas necesarias para h/x̄ ≤ r
    if mean > 0:
        t_crit     = stats.t.ppf(0.975, df=n - 1)
        s          = float(np.std(pct, ddof=1))
        n_required = math.ceil((t_crit * s / (r * mean)) ** 2)
    else:
        n_required = 0

    # Media acumulada réplica a réplica
    cumulative_means = (np.cumsum(pct) / np.arange(1, n + 1)).tolist()

    return {
        "n_actual":          n,
        "n_required":        n_required,
        "sufficient":        n_required <= n,
        "half_width":        half_width,
        "relative_precision": half_width / mean if mean > 0 else float("nan"),
        "cumulative_means":  cumulative_means,
    }
