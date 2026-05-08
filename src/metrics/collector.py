from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.model.customer import Customer
    from src.model.employee import Employee


@dataclass(frozen=True)
class ReplicationResult:
    """Resultado de una réplica: una fila de datos por día simulado."""

    total_customers:        int
    customers_over_5min:    int
    pct_over_5min:          float
    avg_wait_time:          float
    max_wait_time:          float
    avg_service_time:       float
    employee_utilizations:  list[float]
    avg_queue_length:       float


class MetricsCollector:
    """Acumula variables de salida durante una réplica y las resume al cierre."""

    def __init__(self) -> None:
        self._customers:     list[Customer] = []
        self._area_queue:    float = 0.0
        self._current_queue: int   = 0
        self._last_t:        float = 0.0

    def record_arrival(self, customer: Customer, t: float) -> None:
        """Registra la llegada de un nuevo cliente."""
        self._customers.append(customer)

    def record_queue_change(self, new_size: int, t: float) -> None:
        """Cierra el rectángulo anterior de la integral de cola y abre el siguiente.

        Llamar cada vez que la cola cambia de tamaño (al encolar o desencolar).
        """
        self._area_queue    += self._current_queue * (t - self._last_t)
        self._current_queue  = new_size
        self._last_t         = t

    def summarize(self, employees: list[Employee], duration: float) -> ReplicationResult:
        """Calcula todas las métricas al cierre del día.

        Excluye clientes sin service_start (quedaron en cola al cerrar).
        """
        self._area_queue += self._current_queue * (duration - self._last_t)

        served     = [c for c in self._customers if c.service_start is not None]
        wait_times = [c.wait_time    for c in served]
        svc_times  = [c.service_time for c in served]
        over_5     = [w for w in wait_times if w > 5.0]

        n = len(served)

        return ReplicationResult(
            total_customers       = len(self._customers),
            customers_over_5min   = len(over_5),
            pct_over_5min         = len(over_5) / n * 100 if n > 0 else 0.0,
            avg_wait_time         = sum(wait_times) / n   if n > 0 else 0.0,
            max_wait_time         = max(wait_times)       if n > 0 else 0.0,
            avg_service_time      = sum(svc_times)  / n   if n > 0 else 0.0,
            employee_utilizations = [e.utilization(duration) for e in employees],
            avg_queue_length      = self._area_queue / duration,
        )
