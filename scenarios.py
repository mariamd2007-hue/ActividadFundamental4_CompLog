"""Ejecución reproducible de E01–E15, cada caso con fixtures nuevos."""

from dataclasses import dataclass
from decimal import Decimal

from app.domain import DomainException, Money, OrderItem
from app.specifications import DiscountPolicy
from cargar_csv import load_fixture


@dataclass(frozen=True)
class ScenarioResult:
    case_id: str
    order_id: str
    operation: str
    outcome: str
    status: str
    units: int
    total_mxn: str
    events: tuple[str, ...]
    error_type: str | None


def execute_scenario(case_id: str) -> ScenarioResult:
    orders = load_fixture()
    order_id = {
        "E01": "O001", "E02": "O002", "E03": "O003", "E04": "O005",
        "E05": "O006", "E06": "O007", "E07": "O008", "E08": "O009",
        "E09": "O010", "E10": "O011", "E11": "O012", "E12": "O013",
        "E13": "O014", "E14": "O015", "E15": "O016",
    }.get(case_id)
    if order_id is None:
        raise ValueError(f"Escenario desconocido: {case_id}")
    order = orders[order_id]
    policy = DiscountPolicy()
    operation = ""
    outcome = ""
    error_type = None

    # Casos donde el dominio DEBE rechazar la operación. El resultado se
    # asigna solo tras ejecutar: si no hay excepción, queda "Éxito inesperado".
    expected_rejection = {"E03", "E06", "E08", "E11", "E12", "E13"}

    try:
        if case_id in {"E01", "E02", "E04", "E05", "E09", "E10"}:
            operation = "Evaluar descuento"
            outcome = f"{policy.percentage_for(order)}%"
        elif case_id in {"E03", "E06", "E07"}:
            operation = "Confirmar"
            order.confirm()
        elif case_id == "E08":
            operation = "Agregar SKU003 x2 a un pedido con 19 unidades"
            order.add_item(OrderItem("SKU003", 2, Money(Decimal("120.00"))))
        elif case_id == "E11":
            operation = "Confirmar y enviar sin guía"
            order.confirm()
            order.ship("   ")
        elif case_id == "E12":
            operation = "Confirmar dos veces"
            order.confirm()
            order.confirm()
        elif case_id == "E13":
            operation = "Confirmar, enviar y cancelar"
            order.confirm()
            order.ship("GUIA-O014")
            order.cancel("Solicitud de cancelación")
        elif case_id == "E14":
            operation = "Confirmar, enviar y devolver"
            order.confirm()
            order.ship("GUIA-O015")
            order.return_order()
        elif case_id == "E15":
            operation = "Confirmar, enviar y entregar"
            order.confirm()
            order.ship("GUIA-O016")
            order.deliver()
        if not outcome:
            if case_id in expected_rejection:
                outcome = "Éxito inesperado"
            else:
                outcome = f"Éxito: {order.status.value}"
    except DomainException as exc:
        error_type = type(exc).__name__
        if case_id not in expected_rejection:
            raise
        outcome = f"Rechazo: {error_type}"

    return ScenarioResult(
        case_id=case_id,
        order_id=order.id,
        operation=operation,
        outcome=outcome,
        status=order.status.value,
        units=order.units,
        total_mxn=str(order.total.amount),
        events=tuple(event.name for event in order.events),
        error_type=error_type,
    )


def main() -> None:
    print("caso | pedido | resultado | estado final | eventos")
    for number in range(1, 16):
        result = execute_scenario(f"E{number:02d}")
        print(
            f"{result.case_id} | {result.order_id} | {result.outcome} | "
            f"{result.status} | {', '.join(result.events) or 'ninguno'}"
        )


if __name__ == "__main__":
    main()
