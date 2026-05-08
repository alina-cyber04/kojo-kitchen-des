from __future__ import annotations

from collections import deque

from src.engine.event import Event, EventType
from src.engine.scheduler import EventScheduler
from src.metrics.collector import MetricsCollector, ReplicationResult
from src.model.config import SimulationConfig
from src.model.customer import Customer, CustomerType
from src.model.employee import Employee
from src.rng.distributions import bernoulli, exponential, uniform
from src.rng.streams import RngStreams


class KojoKitchen:
    """Motor principal de la simulación DES de Kojo's Kitchen.

    Orquesta el bucle de eventos: llegadas, partidas, inicio/fin de hora pico
    y cierre del día. Reutiliza el scheduler, las entidades y el colector ya
    implementados; solo añade la lógica de dominio del restaurante.
    """

    def __init__(self, config: SimulationConfig, streams: RngStreams) -> None:
        self.config = config
        self.streams = streams
        self.scheduler = EventScheduler()
        self.metrics = MetricsCollector()
        self.queue: deque[Customer] = deque()
        self.employees: list[Employee] = []
        # Empleados extra añadidos en hora pico (Escenario B)
        self._extra_employees: list[Employee] = []

    # ── API pública ────────────────────────────────────────────────────

    def run(self) -> ReplicationResult:
        """Simula un día completo y devuelve las métricas de la réplica."""
        self._initialize()
        self._run_loop()
        return self.metrics.summarize(self.employees, self.config.day_duration)

    # ── Inicialización ─────────────────────────────────────────────────

    def _initialize(self) -> None:
        cfg = self.config

        # Crear empleados base (activos todo el día)
        for i in range(cfg.base_staff):
            self.employees.append(Employee(employee_id=i))

        # Primera llegada con tasa fuera de pico (t=0 es apertura, antes del pico 1)
        self._schedule_next_arrival(0.0)

        # Eventos de frontera de horas pico y cierre del día
        sched = self.scheduler
        sched.schedule(Event(cfg.peak1_start,  EventType.INICIO_PICO))
        sched.schedule(Event(cfg.peak1_end,    EventType.FIN_PICO))
        sched.schedule(Event(cfg.peak2_start,  EventType.INICIO_PICO))
        sched.schedule(Event(cfg.peak2_end,    EventType.FIN_PICO))
        sched.schedule(Event(cfg.day_duration, EventType.FIN_SIMULACION))

    # ── Bucle principal ────────────────────────────────────────────────

    def _run_loop(self) -> None:
        handlers = {
            EventType.LLEGADA:        self._on_arrival,
            EventType.PARTIDA:        self._on_departure,
            EventType.INICIO_PICO:    self._on_peak_start,
            EventType.FIN_PICO:       self._on_peak_end,
            EventType.FIN_SIMULACION: self._on_end,
        }
        while not self.scheduler.is_empty():
            event = self.scheduler.next_event()
            handlers[event.event_type](event)

    # ── Handlers de eventos ────────────────────────────────────────────

    def _on_arrival(self, event: Event) -> None:
        t = event.time
        cfg = self.config

        # Tipo de cliente: Bernoulli(p_sandwich)
        is_sandwich = bernoulli(self.streams.type, cfg.p_sandwich)
        ctype = CustomerType.SANDWICH if is_sandwich else CustomerType.SUSHI

        # Tiempo de servicio dibujado AL LLEGAR para garantizar CRN:
        # el cliente k siempre consume el k-ésimo número del stream de servicio,
        # sin importar cuándo empiece a ser atendido (varía entre escenarios).
        if is_sandwich:
            svc = uniform(self.streams.service, cfg.sandwich_min, cfg.sandwich_max)
        else:
            svc = uniform(self.streams.service, cfg.sushi_min, cfg.sushi_max)

        customer = Customer(arrival_time=t, customer_type=ctype, service_time=svc)
        self.metrics.record_arrival(customer, t)

        # Buscar primer empleado libre y disponible (no marcado para salir)
        free = next(
            (e for e in self.employees if not e.is_busy and not e.marked_for_removal),
            None,
        )

        if free:
            # Servidor libre: atención inmediata
            free.assign(customer, t)
            self.scheduler.schedule(
                Event(t + svc, EventType.PARTIDA, {"emp": free})
            )
        else:
            # Todos ocupados: cliente entra a la cola FIFO
            self.queue.append(customer)
            self.metrics.record_queue_change(len(self.queue), t)

        # Encadenar siguiente llegada (proceso Poisson no homogéneo por bloques)
        self._schedule_next_arrival(t)

    def _on_departure(self, event: Event) -> None:
        t = event.time
        emp: Employee = event.data["emp"]

        # Liberar servidor y cerrar tiempos del cliente
        customer = emp.release(t)
        customer.departure_time = t

        if self.queue and t <= self.config.day_duration:
            # Cola no vacía y dentro del horario: atender siguiente cliente
            nxt = self.queue.popleft()
            self.metrics.record_queue_change(len(self.queue), t)
            emp.assign(nxt, t)
            self.scheduler.schedule(
                Event(t + nxt.service_time, EventType.PARTIDA, {"emp": emp})
            )
        elif emp.marked_for_removal:
            # Empleado extra que esperaba terminar su servicio para irse
            self.employees.remove(emp)
            if emp in self._extra_employees:
                self._extra_employees.remove(emp)

    def _on_peak_start(self, event: Event) -> None:
        """Añade empleados extra al inicio de hora pico (solo Escenario B)."""
        t = event.time
        cfg = self.config
        if cfg.extra_staff == 0:
            return

        next_id = max((e.employee_id for e in self.employees), default=-1) + 1
        for i in range(cfg.extra_staff):
            emp = Employee(employee_id=next_id + i)
            self.employees.append(emp)
            self._extra_employees.append(emp)

            # Si hay clientes esperando, el nuevo empleado empieza a trabajar ya
            if self.queue:
                cust = self.queue.popleft()
                self.metrics.record_queue_change(len(self.queue), t)
                emp.assign(cust, t)
                self.scheduler.schedule(
                    Event(t + cust.service_time, EventType.PARTIDA, {"emp": emp})
                )

    def _on_peak_end(self, event: Event) -> None:
        """Retira empleados extra al final de hora pico (solo Escenario B)."""
        for emp in list(self._extra_employees):
            if emp.is_busy:
                # Está atendiendo: termina el servicio actual y luego se va
                emp.marked_for_removal = True
            else:
                # Libre: se va ahora mismo
                self.employees.remove(emp)
        self._extra_employees.clear()

    def _on_end(self, event: Event) -> None:
        # Los PARTIDA ya programados antes del cierre se procesan normalmente.
        # Clientes en cola al cierre no reciben servicio (filtrado en summarize).
        pass

    # ── Helpers ────────────────────────────────────────────────────────

    def _schedule_next_arrival(self, t: float) -> None:
        """Programa la próxima llegada usando la tasa vigente en t."""
        inter = exponential(self.streams.arrivals, self.config.lambda_at(t))
        next_t = t + inter
        if next_t < self.config.day_duration:
            self.scheduler.schedule(Event(next_t, EventType.LLEGADA))
