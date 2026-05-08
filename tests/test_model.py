import pytest

from src.model.customer import Customer, CustomerType
from src.model.employee import Employee


def test_customer_wait_and_sojourn_raise_when_missing() -> None:
	customer = Customer(
		arrival_time=0.0,
		customer_type=CustomerType.SANDWICH,
		service_time=3.0,
	)
	with pytest.raises(RuntimeError):
		_ = customer.wait_time
	with pytest.raises(RuntimeError):
		_ = customer.sojourn_time


def test_customer_wait_and_sojourn_ok() -> None:
	customer = Customer(
		arrival_time=1.0,
		customer_type=CustomerType.SUSHI,
		service_time=4.0,
	)
	customer.service_start = 3.0
	customer.departure_time = 7.0

	assert customer.wait_time == 2.0
	assert customer.sojourn_time == 6.0
	assert customer.waited_more_than(1.5) is True
	assert customer.is_sandwich is False


def test_employee_assign_release_and_utilization() -> None:
	employee = Employee(employee_id=1)
	customer = Customer(
		arrival_time=0.0,
		customer_type=CustomerType.SANDWICH,
		service_time=2.0,
	)

	employee.assign(customer, t=5.0)
	assert employee.is_busy is True
	assert employee.current_customer is customer
	assert customer.service_start == 5.0

	done = employee.release(t=9.0)
	assert done is customer
	assert employee.is_busy is False
	assert employee.current_customer is None
	assert employee.customers_served == 1
	assert employee.total_busy_time == 4.0
	assert employee.utilization(duration=10.0) == 0.4
	assert employee.utilization(duration=0.0) == 0.0
