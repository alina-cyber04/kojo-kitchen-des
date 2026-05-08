from src.experiments.runner import run_replication, _REPLICATION_GAP
from src.metrics.collector import ReplicationResult
from src.model.config import SCENARIO_A, SCENARIO_B, SimulationConfig


def compare_scenarios(
    n_replications: int = 30,
    base_seed: int = 42,
) -> dict[str, list[ReplicationResult]]:
    """Compara Escenario A vs B usando CRN (Common Random Numbers).

    Cada réplica i corre ambos escenarios con la misma seed, garantizando
    que los mismos clientes (mismos tiempos de llegada, tipo y servicio)
    lleguen a ambos sistemas. La única diferencia entre réplicas es la
    política de personal evaluada.

    Esto induce correlación positiva entre A_i y B_i, reduciendo la
    varianza del estimador de diferencia hasta un 82-93 % respecto a
    muestras independientes (permite usar t-test pareado).

    Returns:
        {"A": [30 ReplicationResult], "B": [30 ReplicationResult]}
        Las listas están alineadas: results["A"][i] y results["B"][i]
        corresponden a la misma réplica (misma seed).
    """
    results_a: list[ReplicationResult] = []
    results_b: list[ReplicationResult] = []

    for i in range(n_replications):
        seed = base_seed + i * _REPLICATION_GAP
        results_a.append(run_replication(SCENARIO_A, seed))
        results_b.append(run_replication(SCENARIO_B, seed))

    return {"A": results_a, "B": results_b}


def run_scenario(
    config: SimulationConfig,
    n_replications: int = 30,
    base_seed: int = 42,
) -> list[ReplicationResult]:
    """Corre un único escenario personalizado con n réplicas."""
    return [
        run_replication(config, base_seed + i * _REPLICATION_GAP)
        for i in range(n_replications)
    ]
