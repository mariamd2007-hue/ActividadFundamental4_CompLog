import pytest

from app.scenarios import execute_scenario


EXPECTED = {
    "E01": ("10%", "DRAFT", ()),
    "E02": ("0%", "DRAFT", ()),
    "E03": ("Rechazo: InvalidOrderData", "DRAFT", ()),
    "E04": ("0%", "DRAFT", ()),
    "E05": ("5%", "DRAFT", ()),
    "E06": ("Rechazo: InvalidOrderData", "DRAFT", ()),
    "E07": ("Éxito: CONFIRMED", "CONFIRMED", ("OrderConfirmed",)),
    "E08": ("Rechazo: OrderItemLimitExceeded", "DRAFT", ()),
    "E09": ("0%", "DRAFT", ()),
    "E10": ("0%", "DRAFT", ()),
    "E11": ("Rechazo: InvalidOrderData", "CONFIRMED", ("OrderConfirmed",)),
    "E12": ("Rechazo: InvalidOrderTransition", "CONFIRMED", ("OrderConfirmed",)),
    "E13": (
        "Rechazo: InvalidOrderTransition", "SHIPPED", ("OrderConfirmed", "OrderShipped")
    ),
    "E14": (
        "Éxito: RETURNED", "RETURNED",
        ("OrderConfirmed", "OrderShipped", "OrderReturned"),
    ),
    "E15": (
        "Éxito: DELIVERED", "DELIVERED",
        ("OrderConfirmed", "OrderShipped", "OrderDelivered"),
    ),
}


@pytest.mark.parametrize("case_id", EXPECTED)
def test_escenarios_e01_a_e15(case_id):
    result = execute_scenario(case_id)
    expected_outcome, expected_status, expected_events = EXPECTED[case_id]
    assert result.outcome == expected_outcome
    assert result.status == expected_status
    assert result.events == expected_events
