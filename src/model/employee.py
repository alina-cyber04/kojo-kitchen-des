from __future__ import annotations

from dataclasses import dataclass, field

from src.model.customer import Customer


@dataclass
class Employee:
    """Recurso servidor del sistema Kojo's Kitchen.

    Encapsula el estado de un empleado individual y acumula estadísticas
    de ocupación para calcular la utilización al final de cada réplica.

    Attributes:
        employee_id: Identificador único del empleado.
        is_busy: True si el empleado está atendiendo a un cliente en este momento.
        current_customer: Referencia al cliente en atención; None si está libre.
        marked_for_removal: True cuando el empleado debe retirarse al terminar
            el servicio actual (solo empleados extra al finalizar hora pico).
        customers_served: Cantidad acumulada de clientes atendidos.
        total_busy_time: Minutos totales en estado ocupado.
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

        Args:
            customer: Cliente que comienza a ser atendido.
            t: Tiempo de inicio del servicio en minutos desde la apertura.
        """
        self.is_busy = True
        self.current_customer = customer
        self._busy_since = t
        customer.service_start = t

    def release(self, t: float) -> Customer:
        """Libera al empleado al terminar el servicio del cliente actual.

        Acumula el intervalo ocupado en total_busy_time y resetea el estado
        para que el empleado quede disponible para el siguiente cliente.

        Args:
            t: Tiempo de finalización del servicio en minutos.

        Returns:
            El cliente que acaba de ser atendido.
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
        """Devuelve la fracción del tiempo total que el empleado estuvo ocupado.

        Args:
            duration: Duración total del día en minutos.

        Returns:
            Valor en [0, 1]; 0.0 si duration es no positivo.
        """
        if duration <= 0:
            return 0.0
        return self.total_busy_time / duration
