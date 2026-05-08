"""Tests del sistema de generación de números aleatorios.

Cubre: LCG, distribuciones (exponential, uniform, bernoulli) y streams.
"""

import math

import pytest

from src.rng.lcg import LCG
from src.rng.distributions import bernoulli, exponential, uniform
from src.rng.streams import RngStreams


# ── LCG ───────────────────────────────────────────────────────────────────────

def test_lcg_reproducibility() -> None:
    """Misma seed produce exactamente la misma secuencia."""
    lcg1 = LCG(seed=42)
    lcg2 = LCG(seed=42)
    for _ in range(1_000):
        assert lcg1.next_float() == lcg2.next_float()


def test_lcg_different_seeds_differ() -> None:
    """Seeds distintas producen secuencias distintas."""
    lcg1 = LCG(seed=42)
    lcg2 = LCG(seed=99)
    values1 = [lcg1.next_float() for _ in range(20)]
    values2 = [lcg2.next_float() for _ in range(20)]
    assert values1 != values2


def test_lcg_range() -> None:
    """Todos los valores están estrictamente en (0, 1)."""
    lcg = LCG(seed=0)
    for _ in range(10_000):
        v = lcg.next_float()
        assert 0.0 < v < 1.0, f"Valor fuera de (0,1): {v}"


def test_lcg_period_no_immediate_repeat() -> None:
    """El período del LCG es 2^32: no repite en las primeras 100 000 posiciones."""
    lcg = LCG(seed=1)
    seen = set()
    for _ in range(100_000):
        v = lcg.next_float()
        assert v not in seen, "Valor repetido antes de lo esperado"
        seen.add(v)


def test_lcg_seed_modulo() -> None:
    """Seeds mayores que M se reducen a seed % M correctamente."""
    M = 2 ** 32
    lcg1 = LCG(seed=5)
    lcg2 = LCG(seed=5 + M)   # equivalente
    for _ in range(100):
        assert lcg1.next_float() == lcg2.next_float()


# ── Distribución exponencial ──────────────────────────────────────────────────

def test_exponential_positive() -> None:
    """La distribución exponencial solo produce valores positivos."""
    lcg = LCG(seed=7)
    for _ in range(5_000):
        v = exponential(lcg, lam=0.30)
        assert v > 0.0, f"Valor no positivo: {v}"


def test_exponential_mean() -> None:
    """La media muestral converge a 1/lambda (ley de grandes números)."""
    n   = 50_000
    lam = 0.30
    lcg = LCG(seed=123)
    total = sum(exponential(lcg, lam) for _ in range(n))
    mean  = total / n
    expected = 1.0 / lam   # = 3.333...
    # Tolerancia del 2 % sobre la media esperada
    assert abs(mean - expected) / expected < 0.02, (
        f"Media {mean:.4f} demasiado lejos de {expected:.4f}"
    )


def test_exponential_reproducible() -> None:
    """Misma seed produce la misma secuencia de tiempos entre llegadas."""
    lam = 0.17
    lcg1, lcg2 = LCG(seed=0), LCG(seed=0)
    for _ in range(200):
        assert exponential(lcg1, lam) == exponential(lcg2, lam)


# ── Distribución uniforme ─────────────────────────────────────────────────────

def test_uniform_range() -> None:
    """Todos los valores caen en [a, b]."""
    lcg = LCG(seed=55)
    a, b = 3.0, 5.0
    for _ in range(5_000):
        v = uniform(lcg, a, b)
        assert a <= v <= b, f"Valor {v} fuera de [{a}, {b}]"


def test_uniform_mean() -> None:
    """La media muestral converge a (a + b) / 2."""
    n        = 50_000
    a, b     = 5.0, 8.0
    lcg      = LCG(seed=77)
    total    = sum(uniform(lcg, a, b) for _ in range(n))
    mean     = total / n
    expected = (a + b) / 2   # = 6.5
    assert abs(mean - expected) / expected < 0.01, (
        f"Media {mean:.4f} demasiado lejos de {expected:.4f}"
    )


def test_uniform_reproducible() -> None:
    """Misma seed produce la misma secuencia de tiempos de servicio."""
    lcg1, lcg2 = LCG(seed=9), LCG(seed=9)
    for _ in range(200):
        assert uniform(lcg1, 3.0, 5.0) == uniform(lcg2, 3.0, 5.0)


# ── Distribución Bernoulli ────────────────────────────────────────────────────

def test_bernoulli_only_bool() -> None:
    """bernoulli siempre devuelve True o False."""
    lcg = LCG(seed=1)
    for _ in range(1_000):
        v = bernoulli(lcg, p=0.5)
        assert isinstance(v, bool)


def test_bernoulli_proportion() -> None:
    """La proporción de True converge a p."""
    n   = 50_000
    p   = 0.5
    lcg = LCG(seed=42)
    trues = sum(1 for _ in range(n) if bernoulli(lcg, p))
    proportion = trues / n
    assert abs(proportion - p) < 0.01, (
        f"Proporcion {proportion:.4f} demasiado lejos de {p}"
    )


def test_bernoulli_p_zero() -> None:
    """Con p=0 nunca sale True."""
    lcg = LCG(seed=1)
    assert all(not bernoulli(lcg, p=0.0) for _ in range(500))


def test_bernoulli_p_one() -> None:
    """Con p=1 siempre sale True."""
    lcg = LCG(seed=1)
    assert all(bernoulli(lcg, p=1.0) for _ in range(500))


# ── RngStreams ────────────────────────────────────────────────────────────────

def test_streams_reproducibility() -> None:
    """from_seed con la misma seed produce idéntica secuencia en los 3 streams."""
    s1 = RngStreams.from_seed(42)
    s2 = RngStreams.from_seed(42)
    for _ in range(500):
        assert s1.arrivals.next_float() == s2.arrivals.next_float()
        assert s1.type.next_float()     == s2.type.next_float()
        assert s1.service.next_float()  == s2.service.next_float()


def test_streams_independence() -> None:
    """Los 3 streams con la misma base producen secuencias distintas entre sí."""
    s = RngStreams.from_seed(42)
    arr  = [s.arrivals.next_float() for _ in range(200)]
    typ  = [s.type.next_float()     for _ in range(200)]
    svc  = [s.service.next_float()  for _ in range(200)]
    # Ningún par de streams debe ser idéntico
    assert arr != typ
    assert arr != svc
    assert typ != svc


def test_streams_different_seeds_differ() -> None:
    """Seeds distintas dan streams distintos."""
    s1 = RngStreams.from_seed(42)
    s2 = RngStreams.from_seed(43)
    arr1 = [s1.arrivals.next_float() for _ in range(50)]
    arr2 = [s2.arrivals.next_float() for _ in range(50)]
    assert arr1 != arr2


def test_streams_gap_prevents_overlap() -> None:
    """El gap de 1 000 000 entre streams es mayor que el consumo diario."""
    from src.rng.streams import _STREAM_GAP
    max_events_per_day  = 500   # cota superior holgada de clientes/día
    streams_per_rep     = 3
    consumption_per_rep = max_events_per_day * streams_per_rep
    assert _STREAM_GAP > consumption_per_rep, (
        f"Gap {_STREAM_GAP} insuficiente para {consumption_per_rep} eventos"
    )
