import pytest

from src.engine.event import Event, EventType
from src.engine.scheduler import EventScheduler


def test_event_order_by_time_then_seq() -> None:
	e1 = Event(time=5.0, event_type=EventType.LLEGADA)
	e2 = Event(time=5.0, event_type=EventType.LLEGADA)
	e3 = Event(time=3.0, event_type=EventType.LLEGADA)

	assert e3 < e1
	# Same time uses creation order for tie-break.
	assert (e1 < e2) != (e2 < e1)


def test_scheduler_advances_now_and_orders() -> None:
	scheduler = EventScheduler()
	scheduler.schedule(Event(10.0, EventType.LLEGADA))
	scheduler.schedule(Event(5.0, EventType.LLEGADA))

	assert scheduler.peek_time() == 5.0
	event = scheduler.next_event()
	assert event.time == 5.0
	assert scheduler.now == 5.0
	assert scheduler.peek_time() == 10.0


def test_scheduler_empty_state() -> None:
	scheduler = EventScheduler()
	assert scheduler.is_empty() is True
	assert len(scheduler) == 0
	assert scheduler.peek_time() is None
