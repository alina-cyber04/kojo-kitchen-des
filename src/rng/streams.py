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

    Cada stream es un LCG con su propia semilla — secuencias distintas
    que nunca se mezclan entre si:

        arrivals : tiempos entre llegadas sucesivas de clientes
        type     : decide si cada cliente quiere sandwich o sushi
        service  : duracion de preparacion de cada pedido

    El stream service se consume en orden de llegada (el k-esimo cliente
    dibuja su service_time al llegar y lo guarda en Customer.service_time).
    Esto garantiza CRN: ambos escenarios usan el mismo service_time para
    el mismo cliente sin importar cuando empiece a ser atendido.
    """

    arrivals: LCG
    type:     LCG
    service:  LCG

    @classmethod
    def from_seed(cls, base_seed: int) -> RngStreams:
        """Construye los tres streams a partir de una semilla base.

        Los streams quedan separados por _STREAM_GAP posiciones en el
        espacio de semillas para evitar solapamientos en la practica.
        """
        return cls(
            arrivals = LCG(seed=base_seed),
            type     = LCG(seed=base_seed + _STREAM_GAP),
            service  = LCG(seed=base_seed + 2 * _STREAM_GAP),
        )
