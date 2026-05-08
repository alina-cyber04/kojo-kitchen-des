from src.metrics.collector import ReplicationResult
from src.model.config import SimulationConfig
from src.model.kojo_kitchen import KojoKitchen
from src.rng.streams import RngStreams

# Separación entre seeds de réplicas distintas.
# Cada réplica consume <1 000 números en total (3 streams × ~200 clientes/día).
# 100 000 de separación garantiza que los streams de réplicas distintas
# nunca se solapan entre sí.
_REPLICATION_GAP = 100_000


def run_replication(config: SimulationConfig, seed: int) -> ReplicationResult:
    """Simula un día completo con la seed dada y devuelve sus métricas."""
    streams = RngStreams.from_seed(seed)
    return KojoKitchen(config, streams).run()


def run_experiment(
    config: SimulationConfig,
    n_replications: int,
    base_seed: int,
) -> list[ReplicationResult]:
    """Corre n réplicas independientes y devuelve la lista de resultados.

    Cada réplica usa seed = base_seed + i * _REPLICATION_GAP, garantizando
    independencia estadística entre observaciones.
    """
    return [
        run_replication(config, base_seed + i * _REPLICATION_GAP)
        for i in range(n_replications)
    ]
