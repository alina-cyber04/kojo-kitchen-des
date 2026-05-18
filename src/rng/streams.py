from __future__ import annotations

from dataclasses import dataclass

from src.rng.lcg import LCG

# Separacion entre semillas de streams distintos.
# Con ~200 clientes por dia cada stream consume menos de 200 numeros,
# por lo que 1_000_000 de separacion garantiza que nunca se solapan.
_STREAM_GAP = 1_000_000


@dataclass
class RngStreams:
    """Agrupa los tres streams independientes que necesita la simulacion.

    Cada stream es un LCG con su propia semilla, separados por _STREAM_GAP
    posiciones para garantizar que sus secuencias no se solapan durante un
    día simulado (~200 clientes × 3 streams = 600 números por réplica).

    Attributes:
        arrivals: Stream para los tiempos entre llegadas sucesivas de clientes.
        type: Stream para determinar el tipo de pedido de cada cliente.
        service: Stream para la duración de preparación de cada pedido.
    """

    arrivals: LCG
    type:     LCG
    service:  LCG

    @classmethod
    def from_seed(cls, base_seed: int) -> RngStreams:
        """Construye los tres streams a partir de una semilla base.

        Args:
            base_seed: Semilla del stream de llegadas; los otros streams
                usan base_seed + k·_STREAM_GAP para garantizar independencia.

        Returns:
            Instancia con los tres LCGs inicializados.
        """
        return cls(
            arrivals = LCG(seed=base_seed),
            type     = LCG(seed=base_seed + _STREAM_GAP),
            service  = LCG(seed=base_seed + 2 * _STREAM_GAP),
        )
