"""Tests de integración para KojoKitchen, runner y scenarios.

Cubre: humo, propiedades del modelo, CRN, comportamiento de picos,
       y corrección de las métricas de salida.
"""

import pytest

from src.experiments.runner import run_replication, run_experiment
from src.experiments.scenarios import compare_scenarios
from src.metrics.collector import ReplicationResult
from src.model.config import SCENARIO_A, SCENARIO_B, SimulationConfig
from src.model.kojo_kitchen import KojoKitchen
from src.rng.streams import RngStreams


# ── Helpers ───────────────────────────────────────────────────────────────────

def _kitchen(config: SimulationConfig, seed: int = 42) -> KojoKitchen:
    return KojoKitchen(config, RngStreams.from_seed(seed))


# ── Tests de humo (smoke tests) ───────────────────────────────────────────────

def test_scenario_a_runs_without_error() -> None:
    """Escenario A completa una réplica sin lanzar excepciones."""
    result = run_replication(SCENARIO_A, seed=42)
    assert isinstance(result, ReplicationResult)


def test_scenario_b_runs_without_error() -> None:
    """Escenario B completa una réplica sin lanzar excepciones."""
    result = run_replication(SCENARIO_B, seed=42)
    assert isinstance(result, ReplicationResult)


# ── Propiedades del resultado ─────────────────────────────────────────────────

def test_result_metrics_are_non_negative() -> None:
    """Todas las métricas de salida son >= 0."""
    result = run_replication(SCENARIO_A, seed=99)
    assert result.total_customers      >= 0
    assert result.customers_over_5min  >= 0
    assert result.pct_over_5min        >= 0.0
    assert result.avg_wait_time        >= 0.0
    assert result.max_wait_time        >= 0.0
    assert result.avg_service_time     >= 0.0
    assert result.avg_queue_length     >= 0.0
    for u in result.employee_utilizations:
        assert 0.0 <= u <= 1.0, f"Utilizacion fuera de [0,1]: {u}"


def test_pct_over_5min_consistent_with_count() -> None:
    """pct_over_5min es consistente con customers_over_5min / total."""
    result = run_replication(SCENARIO_A, seed=7)
    if result.total_customers > 0:
        expected = result.customers_over_5min / result.total_customers * 100
        assert abs(result.pct_over_5min - expected) < 1e-6


def test_max_wait_ge_avg_wait() -> None:
    """El tiempo de espera máximo nunca es menor que el promedio."""
    result = run_replication(SCENARIO_A, seed=13)
    assert result.max_wait_time >= result.avg_wait_time


def test_customers_over_5min_le_total() -> None:
    """Los clientes que esperan > 5 min no pueden superar el total."""
    result = run_replication(SCENARIO_A, seed=21)
    assert result.customers_over_5min <= result.total_customers


def test_scenario_a_has_two_utilizations() -> None:
    """Escenario A tiene exactamente 2 empleados activos todo el día."""
    result = run_replication(SCENARIO_A, seed=42)
    assert len(result.employee_utilizations) == 2


def test_scenario_b_has_correct_employee_count() -> None:
    """Escenario B: los empleados base (2) siempre están; extra sale en pico."""
    result = run_replication(SCENARIO_B, seed=42)
    # Al final del día solo quedan los empleados base
    assert len(result.employee_utilizations) == 2


# ── CRN — Common Random Numbers ──────────────────────────────────────────────

def test_crn_same_seed_same_total_customers() -> None:
    """Con la misma seed, A y B reciben el mismo número de clientes."""
    r_a = run_replication(SCENARIO_A, seed=42)
    r_b = run_replication(SCENARIO_B, seed=42)
    assert r_a.total_customers == r_b.total_customers


def test_crn_same_seed_same_service_times() -> None:
    """Con la misma seed, el tiempo de servicio medio es el mismo en A y B.

    El service_time se dibuja al llegar (no al ser atendido), por lo que
    ambos escenarios consumen el mismo stream de servicio en el mismo orden.
    """
    r_a = run_replication(SCENARIO_A, seed=42)
    r_b = run_replication(SCENARIO_B, seed=42)
    assert abs(r_a.avg_service_time - r_b.avg_service_time) < 0.01


def test_crn_different_seeds_different_customers() -> None:
    """Seeds distintas producen días con distinto número de clientes."""
    r1 = run_replication(SCENARIO_A, seed=42)
    r2 = run_replication(SCENARIO_A, seed=142_000)
    # No es garantizado, pero con seeds muy distintas es prácticamente siempre cierto
    assert r1.total_customers != r2.total_customers or \
           r1.avg_wait_time   != r2.avg_wait_time


# ── Comparación entre escenarios ──────────────────────────────────────────────

def test_scenario_b_improves_pct_over_5min_on_average() -> None:
    """Con 30 réplicas, B tiene menor % > 5 min que A."""
    results = compare_scenarios(n_replications=30, base_seed=42)
    mean_a = sum(r.pct_over_5min for r in results["A"]) / 30
    mean_b = sum(r.pct_over_5min for r in results["B"]) / 30
    assert mean_b < mean_a, (
        f"Se esperaba B ({mean_b:.2f}%) < A ({mean_a:.2f}%)"
    )


def test_scenario_b_improves_in_every_replication() -> None:
    """B es mejor que A en las 30 réplicas individuales (con CRN)."""
    results = compare_scenarios(n_replications=30, base_seed=42)
    for i, (r_a, r_b) in enumerate(zip(results["A"], results["B"])):
        assert r_b.pct_over_5min <= r_a.pct_over_5min, (
            f"Replica {i}: B ({r_b.pct_over_5min:.2f}%) >= A ({r_a.pct_over_5min:.2f}%)"
        )


def test_scenario_b_reduces_avg_wait_time() -> None:
    """El tiempo de espera medio es menor en B que en A."""
    results = compare_scenarios(n_replications=30, base_seed=42)
    mean_wait_a = sum(r.avg_wait_time for r in results["A"]) / 30
    mean_wait_b = sum(r.avg_wait_time for r in results["B"]) / 30
    assert mean_wait_b < mean_wait_a


# ── runner.py ─────────────────────────────────────────────────────────────────

def test_run_experiment_returns_correct_count() -> None:
    """run_experiment devuelve exactamente n_replications resultados."""
    results = run_experiment(SCENARIO_A, n_replications=5, base_seed=42)
    assert len(results) == 5
    assert all(isinstance(r, ReplicationResult) for r in results)


def test_run_experiment_replications_differ() -> None:
    """Réplicas distintas producen resultados distintos (seeds independientes)."""
    results = run_experiment(SCENARIO_A, n_replications=10, base_seed=42)
    pcts = [r.pct_over_5min for r in results]
    # Al menos 2 valores distintos confirma que las seeds son independientes
    assert len(set(pcts)) > 1


def test_run_experiment_reproducible() -> None:
    """Dos llamadas con los mismos parámetros producen resultados idénticos."""
    r1 = run_experiment(SCENARIO_A, n_replications=5, base_seed=42)
    r2 = run_experiment(SCENARIO_A, n_replications=5, base_seed=42)
    for a, b in zip(r1, r2):
        assert a.pct_over_5min    == b.pct_over_5min
        assert a.total_customers  == b.total_customers
        assert a.avg_wait_time    == b.avg_wait_time


# ── Configuración personalizada ───────────────────────────────────────────────

def test_custom_config_extra_staff_zero_equals_scenario_a() -> None:
    """Una config con extra_staff=0 se comporta igual que SCENARIO_A."""
    custom = SimulationConfig(base_staff=2, extra_staff=0)
    r_a      = run_replication(SCENARIO_A, seed=42)
    r_custom = run_replication(custom,     seed=42)
    assert r_a.total_customers == r_custom.total_customers
    assert r_a.pct_over_5min   == r_custom.pct_over_5min


def test_more_employees_never_worse() -> None:
    """Más empleados nunca empeora la métrica principal."""
    config_3 = SimulationConfig(base_staff=3, extra_staff=0)
    results_2 = run_experiment(SCENARIO_A, n_replications=10, base_seed=42)
    results_3 = run_experiment(config_3,   n_replications=10, base_seed=42)
    mean_2 = sum(r.pct_over_5min for r in results_2) / 10
    mean_3 = sum(r.pct_over_5min for r in results_3) / 10
    assert mean_3 <= mean_2, (
        f"3 empleados ({mean_3:.2f}%) peor que 2 ({mean_2:.2f}%)"
    )
