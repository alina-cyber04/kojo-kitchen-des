import heapq
from typing import Optional

from src.engine.event import Event


class EventScheduler:
    """Lista de Eventos Futuros (FEL) implementada con un min-heap.

    Responsabilidades:
        - Mantener eventos ordenados por tiempo
        - Avanzar el reloj al procesar cada evento
        - Exponer API limpia: schedule / next_event / peek_time / is_empty / now

    No contiene logica del problema — solo gestiona tiempo y orden.
    """

    def __init__(self) -> None:
        self._heap: list[Event] = []
        self._now: float = 0.0

    @property
    def now(self) -> float:
        """Tiempo actual de simulacion en minutos desde apertura."""
        return self._now

    def schedule(self, event: Event) -> None:
        """Inserta un evento en la FEL. O(log n)."""
        heapq.heappush(self._heap, event)

    def next_event(self) -> Event:
        """Extrae el evento mas proximo y avanza el reloj. O(log n)."""
        event = heapq.heappop(self._heap)
        self._now = event.time
        return event

    def peek_time(self) -> Optional[float]:
        """Tiempo del proximo evento sin extraerlo. O(1)."""
        return self._heap[0].time if self._heap else None

    def is_empty(self) -> bool:
        """True si no quedan eventos pendientes."""
        return len(self._heap) == 0

    def __len__(self) -> int:
        return len(self._heap)
