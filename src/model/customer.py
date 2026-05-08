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

    Registra los instantes clave y la duracion del servicio:
        arrival_time   : cuando entra al sistema (cola o servicio directo)
        service_time   : cuanto dura su preparacion (dibujado al llegar, fijo)
        service_start  : cuando un empleado comienza a atenderlo
        departure_time : cuando sale del sistema = service_start + service_time

    service_time se dibuja al llegar y se guarda aqui para garantizar CRN:
    el cliente k consume siempre el k-esimo numero del stream de servicio,
    sin importar cuando empiece a ser atendido (que varia entre escenarios).

    service_start == None significa que el cliente sigue esperando en cola.
    departure_time == None significa que el cliente sigue en el sistema.
    """

    arrival_time:   float
    customer_type:  CustomerType
    service_time:   float
    customer_id:    int          = field(default_factory=lambda: next(_customer_counter))
    service_start:  float | None = field(default=None)
    departure_time: float | None = field(default=None)

    @property
    def wait_time(self) -> float:
        """Tiempo de espera en cola en minutos. Requiere que service_start este definido."""
        if self.service_start is None:
            raise RuntimeError(f"Cliente {self.customer_id} aun no inicio servicio")
        return self.service_start - self.arrival_time

    @property
    def sojourn_time(self) -> float:
        """Tiempo total en el sistema: espera en cola + tiempo de servicio."""
        if self.departure_time is None:
            raise RuntimeError(f"Cliente {self.customer_id} aun no salio del sistema")
        return self.departure_time - self.arrival_time

    def waited_more_than(self, threshold: float) -> bool:
        """True si el cliente espero mas de `threshold` minutos en cola."""
        return self.wait_time > threshold

    @property
    def is_sandwich(self) -> bool:
        """True si el cliente pidio sandwich, False si pidio sushi."""
        return self.customer_type == CustomerType.SANDWICH
