"""Specifications composables y política de descuentos del laboratorio."""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from app.domain import InvalidOrderData, Money, Order


class Specification:
    def is_satisfied_by(self, order: Order) -> bool:
        raise NotImplementedError

    def __and__(self, other: "Specification") -> "AndSpec":
        return AndSpec(self, other)

    def __or__(self, other: "Specification") -> "OrSpec":
        return OrSpec(self, other)

    def __invert__(self) -> "NotSpec":
        return NotSpec(self)


class AndSpec(Specification):
    def __init__(self, left: Specification, right: Specification):
        self.left, self.right = left, right

    def is_satisfied_by(self, order: Order) -> bool:
        return self.left.is_satisfied_by(order) and self.right.is_satisfied_by(order)


class OrSpec(Specification):
    def __init__(self, left: Specification, right: Specification):
        self.left, self.right = left, right

    def is_satisfied_by(self, order: Order) -> bool:
        return self.left.is_satisfied_by(order) or self.right.is_satisfied_by(order)


class NotSpec(Specification):
    def __init__(self, specification: Specification):
        self.specification = specification

    def is_satisfied_by(self, order: Order) -> bool:
        return not self.specification.is_satisfied_by(order)


class MinimumAmountSpec(Specification):
    """Cumple solo cuando total es estrictamente mayor que el umbral."""

    def __init__(self, amount: Decimal):
        if not isinstance(amount, Decimal) or not amount.is_finite() or amount < 0:
            raise InvalidOrderData("El umbral debe ser Decimal, finito y no negativo")
        self.amount = amount

    def is_satisfied_by(self, order: Order) -> bool:
        return order.total.amount > self.amount


class VIPCustomerSpec(Specification):
    def is_satisfied_by(self, order: Order) -> bool:
        return order.customer.is_vip


class MinimumUnitsSpec(Specification):
    def __init__(self, minimum: int = 4):
        if minimum < 0:
            raise InvalidOrderData("El mínimo de unidades no puede ser negativo")
        self.minimum = minimum

    def is_satisfied_by(self, order: Order) -> bool:
        return order.units >= self.minimum


class ActivePromotionSpec(Specification):
    def is_satisfied_by(self, order: Order) -> bool:
        return order.has_promotion


@dataclass(frozen=True)
class DiscountResult:
    percentage: int
    discount: Money
    total_after_discount: Money


class DiscountPolicy:
    """Combina las reglas de 10 % y 5 % con OR; si ambas aplican, gana el 10 %."""

    def __init__(self):
        no_promotion = ~ActivePromotionSpec()
        self.ten_percent = (
            MinimumAmountSpec(Decimal("500"))
            & VIPCustomerSpec()
            & MinimumUnitsSpec(4)
            & no_promotion
        )
        self.five_percent = MinimumAmountSpec(Decimal("5000")) & no_promotion
        # Regla general: hay descuento si se cumple la de 10 % O la de 5 %.
        self.any_discount = self.ten_percent | self.five_percent

    def percentage_for(self, order: Order) -> int:
        if not self.any_discount.is_satisfied_by(order):
            return 0
        # Prioridad: si se cumplen ambas reglas, aplica primero el 10 %.
        return 10 if self.ten_percent.is_satisfied_by(order) else 5

    def evaluate(self, order: Order) -> DiscountResult:
        percentage = self.percentage_for(order)
        discount_amount = (order.total.amount * Decimal(percentage) / Decimal(100)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        discount = Money(discount_amount)
        return DiscountResult(
            percentage=percentage,
            discount=discount,
            total_after_discount=Money(order.total.amount - discount_amount),
        )
