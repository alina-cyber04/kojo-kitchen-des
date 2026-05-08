from dataclasses import dataclass, field
from enum import Enum
from itertools import count

_counter = count()


class EventType(Enum):
    LLEGADA        = "LLEGADA"
    PARTIDA        = "PARTIDA"
    INICIO_PICO    = "INICIO_PICO"
    FIN_PICO       = "FIN_PICO"
    FIN_SIMULACION = "FIN_SIMULACION"


@dataclass
class Event:
    """Un instante en el tiempo donde algo cambia en el sistema.

    time       : minutos desde apertura (0 = 10:00am, 660 = 9:00pm)
    event_type : que tipo de evento ocurre
    data       : informacion adicional (cliente_id, empleado_id, etc.)
    _seq       : orden de creacion — desempata eventos con igual tiempo
    """
    time:       float
    event_type: EventType
    data:       dict = field(default_factory=dict)
    _seq:       int  = field(default_factory=lambda: next(_counter),
                             init=False, repr=False)

    def __lt__(self, other: "Event") -> bool:
        return (self.time, self._seq) < (other.time, other._seq)

    def __le__(self, other: "Event") -> bool:
        return not (other < self)

    def __gt__(self, other: "Event") -> bool:
        return other < self

    def __ge__(self, other: "Event") -> bool:
        return not (self < other)
