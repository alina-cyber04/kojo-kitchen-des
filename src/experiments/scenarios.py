from src.experiments.runner import run_replication, _REPLICATION_GAP
from src.metrics.collector import ReplicationResult
from src.model.config import SCENARIO_A, SCENARIO_B, SimulationConfig


def compare_scenarios(
    n_replications: int = 30,
    base_seed: int = 42,
) -> dict[str, list[ReplicationResult]]:
    """Compara Escenario A vs B usando CRN (Common Random Numbers).

    Cada réplica i corre ambos escenarios con la misma semilla, de modo que
    los mismos clientes (mismos tiempos de llegada, tipo de pedido y servicio)
    llegan a ambos sistemas. La única diferencia es la política de personal.
    Esto induce correlación positiva entre A_i y B_i, reduciendo la varianza
    del estimador de diferencia y habilitando el t-test pareado.

    Args:
        n_replications: Número de réplicas a ejecutar por escenario.
        base_seed: Semilla de la primera réplica.

    Returns:
        Diccionario con claves "A" y "B"; cada valor es una lista de
        n_replications resultados alineados por índice de réplica.
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
    """Corre un único escenario personalizado con n réplicas.

    Args:
        config: Configuración del modelo a evaluar.
        n_replications: Número de réplicas a ejecutar.
        base_seed: Semilla de la primera réplica.

    Returns:
        Lista de n_replications resultados independientes.
    """
    return [
        run_replication(config, base_seed + i * _REPLICATION_GAP)
        for i in range(n_replications)
    ]
