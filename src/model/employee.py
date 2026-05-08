from __future__ import annotations

from dataclasses import dataclass, field

from src.model.customer import Customer


@dataclass
class Employee:
    """Recurso servidor del sistema Kojo's Kitchen.

    Encapsula el estado de un empleado individual:
        is_busy            : True si esta atendiendo a alguien ahora
        current_customer   : referencia al cliente que atiende actualmente
        marked_for_removal : True si debe retirarse al terminar el servicio actual
                             (exclusivo del Escenario B al finalizar hora pico)
        customers_served   : contador acumulado de clientes atendidos
        total_busy_time    : minutos totales ocupado (para calcular utilizacion)

    El campo _busy_since es privado — registra cuando inicio el servicio actual
    para poder acumular total_busy_time correctamente en release().
    """

    employee_id:        int
    is_busy:            bool            = field(default=False)
    current_customer:   Customer | None = field(default=None)
    marked_for_removal: bool            = field(default=False)
    customers_served:   int             = field(default=0)
    total_busy_time:    float           = field(default=0.0)
    _busy_since:        float | None    = field(default=None, init=False, repr=False)

    def assign(self, customer: Customer, t: float) -> None:
        """Asigna un cliente a este empleado e inicia el servicio.

        Registra t como inicio del servicio para acumular busy_time en release().
        """
        self.is_busy = True
        self.current_customer = customer
        self._busy_since = t
        customer.service_start = t

    def release(self, t: float) -> Customer:
        """Libera al empleado al terminar el servicio del cliente actual.

        Acumula el tiempo ocupado en total_busy_time y devuelve el cliente
        que acaba de ser atendido para que el motor registre su departure_time.
        """
        if self._busy_since is not None:
            self.total_busy_time += t - self._busy_since

        customer = self.current_customer
        self.customers_served += 1
        self.is_busy = False
        self.current_customer = None
        self._busy_since = None
        return customer

    def utilization(self, duration: float) -> float:
        """Fraccion del tiempo total que el empleado estuvo ocupado. Entre 0 y 1."""
        if duration <= 0:
            return 0.0
        return self.total_busy_time / duration
