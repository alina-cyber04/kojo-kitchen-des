from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from itertools import count

_customer_counter = count()


class CustomerType(Enum):
    SANDWICH = "SANDWICH"
    SUSHI    = "SUSHI"


@dataclass
class Customer:
    """Entidad cliente que fluye por el sistema Kojo's Kitchen.

    Registra los instantes clave de su ciclo de vida. service_time se
    extrae al llegar (no al ser atendido) para garantizar CRN: el cliente
    k siempre consume el k-ésimo número del stream de servicio, independiente
    de cuándo empiece a ser atendido.

    Attributes:
        arrival_time: Minuto en que el cliente entra al sistema.
        customer_type: Tipo de pedido (SANDWICH o SUSHI).
        service_time: Duración de la preparación, fijada en la llegada.
        customer_id: Identificador único asignado automáticamente.
        service_start: Minuto en que un empleado inicia su atención;
            None mientras el cliente espera en cola.
        departure_time: Minuto en que el cliente abandona el sistema;
            None si aún está siendo atendido.
    """

    arrival_time:   float
    customer_type:  CustomerType
    service_time:   float
    customer_id:    int          = field(default_factory=lambda: next(_customer_counter))
    service_start:  float | None = field(default=None)
    departure_time: float | None = field(default=None)

    @property
    def wait_time(self) -> float:
        """Tiempo de espera en cola en minutos.

        Returns:
            Diferencia entre service_start y arrival_time.

        Raises:
            RuntimeError: Si service_start aún no está definido.
        """
        if self.service_start is None:
            raise RuntimeError(f"Cliente {self.customer_id} aun no inicio servicio")
        return self.service_start - self.arrival_time

    @property
    def sojourn_time(self) -> float:
        """Tiempo total en el sistema: espera en cola más tiempo de servicio.

        Returns:
            Diferencia entre departure_time y arrival_time.

        Raises:
            RuntimeError: Si departure_time aún no está definido.
        """
        if self.departure_time is None:
            raise RuntimeError(f"Cliente {self.customer_id} aun no salio del sistema")
        return self.departure_time - self.arrival_time

    def waited_more_than(self, threshold: float) -> bool:
        """Indica si el cliente esperó más de threshold minutos en cola.

        Args:
            threshold: Umbral en minutos.

        Returns:
            True si wait_time supera threshold.
        """
        return self.wait_time > threshold

    @property
    def is_sandwich(self) -> bool:
        """Devuelve True si el cliente pidió sandwich, False si pidió sushi.

        Returns:
            True para SANDWICH, False para SUSHI.
        """
        return self.customer_type == CustomerType.SANDWICH
