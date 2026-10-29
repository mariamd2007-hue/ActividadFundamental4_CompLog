from decimal import Decimal

import pytest

from app.domain import (
    Customer,
    InvalidOrderData,
    InvalidOrderTransition,
    Money,
    Order,
    OrderItem,
    OrderItemLimitExceeded,
    OrderStatus,
)


def make_order(*, active=True, quantities=(1,)):
    order = Order(Customer("C-test", is_vip=True, active=active), "O-test")
    for quantity in quantities:
        order.add_item(OrderItem("SKU", quantity, Money(Decimal("10.00"))))
    return order


def test_money_rechaza_negativos_y_floats():
    with pytest.raises(InvalidOrderData):
        Money(Decimal("-0.01"))
    with pytest.raises(InvalidOrderData):
        Money(10.0)


def test_money_add_devuelve_un_objeto_y_rechaza_moneda_distinta():
    original = Money(Decimal("10.25"))
    total = original.add(Money(Decimal("2.75")))
    assert total.amount == Decimal("13.00")
    assert original.amount == Decimal("10.25")
    with pytest.raises(InvalidOrderData):
        original.add(Money(Decimal("1"), "USD"))


def test_orderitem_calcula_subtotal_y_rechaza_cantidad_invalida():
    item = OrderItem("SKU", 3, Money(Decimal("12.50")))
    assert item.subtotal == Money(Decimal("37.50"))
    with pytest.raises(InvalidOrderData):
        OrderItem("SKU", 0, Money(Decimal("12.50")))


def test_total_y_unidades_suman_cantidades_no_renglones():
    order = make_order(quantities=(3, 4))
    assert order.units == 7
    assert order.total.amount == Decimal("70.00")


def test_limite_de_20_unidades_se_aplica_a_la_suma():
    order = make_order(quantities=(19,))
    order.add_item(OrderItem("OTRO", 1, Money(Decimal("1"))))
    before = (order.units, len(order.items), len(order.events))
    with pytest.raises(OrderItemLimitExceeded):
        order.add_item(OrderItem("SKU", 1, Money(Decimal("1"))))
    assert (order.units, len(order.items), len(order.events)) == before


@pytest.mark.parametrize("active, has_items", [(False, True), (True, False)])
def test_confirmar_requiere_cliente_activo_y_articulos(active, has_items):
    order = make_order(active=active, quantities=(1,) if has_items else ())
    with pytest.raises(InvalidOrderData):
        order.confirm()
    assert order.status is OrderStatus.DRAFT
    assert order.events == []


def test_confirmar_y_enviar_registran_eventos_despues_de_validar():
    order = make_order()
    order.confirm()
    assert order.status is OrderStatus.CONFIRMED
    assert [e.name for e in order.events] == ["OrderConfirmed"]
    with pytest.raises(InvalidOrderData):
        order.ship(" ")
    assert order.status is OrderStatus.CONFIRMED
    assert [e.name for e in order.events] == ["OrderConfirmed"]
    order.ship("TRACK-1")
    assert order.status is OrderStatus.SHIPPED
    assert [e.name for e in order.events] == ["OrderConfirmed", "OrderShipped"]


def test_transiciones_terminales_y_cancelacion_desde_shipped():
    order = make_order()
    order.confirm()
    order.ship("TRACK-1")
    with pytest.raises(InvalidOrderTransition):
        order.cancel("motivo")
    assert order.status is OrderStatus.SHIPPED
    assert [e.name for e in order.events] == ["OrderConfirmed", "OrderShipped"]
    order.return_order()
    assert order.status is OrderStatus.RETURNED
    assert order.events[-1].name == "OrderReturned"


def test_evento_de_entrega():
    order = make_order()
    order.confirm()
    order.ship("TRACK-1")
    order.deliver()
    assert order.status is OrderStatus.DELIVERED
    assert [e.name for e in order.events] == [
        "OrderConfirmed", "OrderShipped", "OrderDelivered"
    ]


def test_cancelacion_valida_desde_confirmed_registra_evento():
    order = make_order()
    order.confirm()
    order.cancel("El cliente cambió de opinión")
    assert order.status is OrderStatus.CANCELLED
    assert [e.name for e in order.events] == ["OrderConfirmed", "OrderCancelled"]


def test_cancelar_requiere_motivo_y_no_cambia_estado():
    order = make_order()
    order.confirm()
    with pytest.raises(InvalidOrderData):
        order.cancel("  ")
    assert order.status is OrderStatus.CONFIRMED
    assert [e.name for e in order.events] == ["OrderConfirmed"]


@pytest.mark.parametrize("operation", ["deliver", "return_order"])
def test_entregar_o_devolver_exige_shipped(operation):
    order = make_order()
    order.confirm()
    with pytest.raises(InvalidOrderTransition):
        getattr(order, operation)()
    assert order.status is OrderStatus.CONFIRMED
    assert [e.name for e in order.events] == ["OrderConfirmed"]


def test_no_se_agregan_articulos_fuera_de_draft():
    order = make_order()
    order.confirm()
    with pytest.raises(InvalidOrderTransition):
        order.add_item(OrderItem("SKU", 1, Money(Decimal("10.00"))))
    assert order.units == 1


def test_total_de_pedido_vacio_tiene_dos_decimales():
    assert str(make_order(quantities=()).total.amount) == "0.00"
