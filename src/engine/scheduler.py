import heapq
from typing import Optional

from src.engine.event import Event


class EventScheduler:
    """Lista de Eventos Futuros (FEL) implementada con un min-heap.

    Mantiene los eventos ordenados por tiempo y avanza el reloj de simulación
    cada vez que se extrae un evento. No contiene lógica de dominio.

    Attributes:
        now: Tiempo actual de simulación en minutos desde la apertura.
    """

    def __init__(self) -> None:
        self._heap: list[Event] = []
        self._now: float = 0.0

    @property
    def now(self) -> float:
        """Tiempo actual de simulacion en minutos desde apertura."""
        return self._now

    def schedule(self, event: Event) -> None:
        """Inserta un evento en la FEL en O(log n).

        Args:
            event: Evento a planificar.
        """
        heapq.heappush(self._heap, event)

    def next_event(self) -> Event:
        """Extrae el evento más próximo y avanza el reloj en O(log n).

        Returns:
            El evento con el menor tiempo de entre los pendientes.
        """
        event = heapq.heappop(self._heap)
        self._now = event.time
        return event

    def peek_time(self) -> Optional[float]:
        """Tiempo del próximo evento sin extraerlo en O(1).

        Returns:
            Tiempo del siguiente evento, o None si la FEL está vacía.
        """
        return self._heap[0].time if self._heap else None

    def is_empty(self) -> bool:
        """Devuelve True si no quedan eventos pendientes.

        Returns:
            True cuando la FEL está vacía.
        """
        return len(self._heap) == 0

    def __len__(self) -> int:
        return len(self._heap)
