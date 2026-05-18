from dataclasses import dataclass, field
from enum import Enum
from itertools import count

_counter = count()


class EventType(Enum):
    ARRIVAL    = "ARRIVAL"
    DEPARTURE  = "DEPARTURE"
    PEAK_START = "PEAK_START"
    PEAK_END   = "PEAK_END"
    END_OF_DAY = "END_OF_DAY"


@dataclass
class Event:
    """Un instante en el tiempo donde algo cambia en el sistema.

    Attributes:
        time: Minutos desde la apertura (0 = 10:00 am, 660 = 9:00 pm).
        event_type: Tipo de evento que ocurre en este instante.
        data: Payload opcional con referencias a entidades (empleado, cliente).
        _seq: Número de creación; desempata eventos con el mismo tiempo.
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
