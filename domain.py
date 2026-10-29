"""Modelo de dominio de TechStore: invariantes, estados y eventos."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum


class DomainException(Exception):
    """Error causado por una regla del dominio."""


class InvalidOrderData(DomainException):
    """Los datos no permiten ejecutar la operación solicitada."""


class InvalidOrderTransition(DomainException):
    """La operación no está permitida desde el estado actual."""


class OrderItemLimitExceeded(InvalidOrderData):
    """La suma de unidades del pedido superaría el máximo permitido."""


@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str = "MXN"

    def __post_init__(self) -> None:
        if not isinstance(self.amount, Decimal):
            raise InvalidOrderData("Money.amount debe ser Decimal")
        if not self.amount.is_finite() or self.amount < 0:
            raise InvalidOrderData("El importe debe ser finito y no negativo")
        if not self.currency or not self.currency.strip():
            raise InvalidOrderData("La moneda es obligatoria")

    def add(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise InvalidOrderData("No se pueden sumar monedas distintas")
        return Money(self.amount + other.amount, self.currency)


@dataclass(frozen=True)
class Customer:
    id: str
    is_vip: bool = False
    active: bool = True

    def __post_init__(self) -> None:
        if not self.id or not self.id.strip():
            raise InvalidOrderData("El cliente requiere un identificador")


@dataclass(frozen=True)
class OrderItem:
    sku: str
    quantity: int
    unit_price: Money

    def __post_init__(self) -> None:
        if not self.sku or not self.sku.strip():
            raise InvalidOrderData("El artículo requiere un SKU")
        if isinstance(self.quantity, bool) or not isinstance(self.quantity, int) or self.quantity <= 0:
            raise InvalidOrderData("La cantidad debe ser un entero positivo")
        if not isinstance(self.unit_price, Money):
            raise InvalidOrderData("El precio unitario debe ser Money")

    @property
    def subtotal(self) -> Money:
        return Money(self.unit_price.amount * self.quantity, self.unit_price.currency)


class OrderStatus(str, Enum):
    DRAFT = "DRAFT"
    CONFIRMED = "CONFIRMED"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"
    RETURNED = "RETURNED"


@dataclass(frozen=True)
class DomainEvent:
    name: str
    order_id: str
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class Order:
    """Aggregate Root que protege las reglas y transiciones de un pedido."""

    MAX_UNITS = 20

    def __init__(self, customer: Customer, id: str, has_promotion: bool = False):
        if not isinstance(customer, Customer):
            raise InvalidOrderData("El pedido requiere un Customer")
        if not id or not id.strip():
            raise InvalidOrderData("El pedido requiere un identificador")
        self.customer = customer
        self.id = id
        self.has_promotion = bool(has_promotion)
        self._status = OrderStatus.DRAFT
        self.items: list[OrderItem] = []
        self.events: list[DomainEvent] = []

    @property
    def status(self) -> OrderStatus:
        return self._status

    @property
    def units(self) -> int:
        return sum(item.quantity for item in self.items)

    @property
    def total(self) -> Money:
        amount = sum((item.subtotal.amount for item in self.items), Decimal("0"))
        return Money(amount.quantize(Decimal("0.01")))

    def add_item(self, item: OrderItem) -> None:
        if self.status is not OrderStatus.DRAFT:
            raise InvalidOrderTransition("Solo un pedido DRAFT admite artículos")
        if not isinstance(item, OrderItem):
            raise InvalidOrderData("Se requiere un OrderItem")
        if item.unit_price.currency != "MXN":
            raise InvalidOrderData("Los pedidos de TechStore solo admiten MXN")
        if self.units + item.quantity > self.MAX_UNITS:
            raise OrderItemLimitExceeded("El pedido no puede superar 20 unidades")
        self.items.append(item)

    def _record_event(self, name: str) -> None:
        self.events.append(DomainEvent(name=name, order_id=self.id))

    def confirm(self) -> None:
        if self.status is not OrderStatus.DRAFT:
            raise InvalidOrderTransition("Solo se puede confirmar un pedido DRAFT")
        if not self.items:
            raise InvalidOrderData("No se puede confirmar un pedido sin artículos")
        if not self.customer.active:
            raise InvalidOrderData("No se puede confirmar: el cliente está inactivo")
        self._status = OrderStatus.CONFIRMED
        self._record_event("OrderConfirmed")

    def ship(self, tracking_number: str) -> None:
        if self.status is not OrderStatus.CONFIRMED:
            raise InvalidOrderTransition("Solo se puede enviar un pedido CONFIRMED")
        if not tracking_number or not tracking_number.strip():
            raise InvalidOrderData("Se requiere una guía de envío")
        self._status = OrderStatus.SHIPPED
        self._record_event("OrderShipped")

    def cancel(self, reason: str) -> None:
        if self.status is not OrderStatus.CONFIRMED:
            raise InvalidOrderTransition("Solo se puede cancelar un pedido CONFIRMED")
        if not reason or not reason.strip():
            raise InvalidOrderData("Se requiere un motivo de cancelación")
        self._status = OrderStatus.CANCELLED
        self._record_event("OrderCancelled")

    def deliver(self) -> None:
        if self.status is not OrderStatus.SHIPPED:
            raise InvalidOrderTransition("Solo se puede entregar un pedido SHIPPED")
        self._status = OrderStatus.DELIVERED
        self._record_event("OrderDelivered")

    def return_order(self) -> None:
        if self.status is not OrderStatus.SHIPPED:
            raise InvalidOrderTransition("Solo se puede devolver un pedido SHIPPED")
        self._status = OrderStatus.RETURNED
        self._record_event("OrderReturned")
