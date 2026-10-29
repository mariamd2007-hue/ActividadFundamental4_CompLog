from decimal import Decimal

from app.domain import Customer, Money, Order, OrderItem
from app.specifications import (
    ActivePromotionSpec,
    DiscountPolicy,
    MinimumAmountSpec,
    MinimumUnitsSpec,
    VIPCustomerSpec,
)


def order(*, vip=False, promo=False, price="600", quantity=1):
    result = Order(Customer("C", is_vip=vip), "O", has_promotion=promo)
    result.add_item(OrderItem("SKU", quantity, Money(Decimal(price))))
    return result


def test_composicion_and_or_not():
    eligible = MinimumAmountSpec(Decimal("500")) & VIPCustomerSpec() & ~ActivePromotionSpec()
    assert eligible.is_satisfied_by(order(vip=True))
    assert not eligible.is_satisfied_by(order(vip=False))
    alternatives = eligible | MinimumUnitsSpec(4)
    assert alternatives.is_satisfied_by(order(quantity=4, price="10"))


def test_descuento_10_por_ciento_y_prioridad_sobre_5():
    policy = DiscountPolicy()
    eligible_for_both = order(vip=True, price="1800", quantity=4)
    assert policy.percentage_for(eligible_for_both) == 10
    result = policy.evaluate(eligible_for_both)
    assert result.discount.amount == Decimal("720.00")
    assert result.total_after_discount.amount == Decimal("6480.00")


def test_descuento_5_por_ciento_y_promocion_bloquea_reglas():
    policy = DiscountPolicy()
    assert policy.percentage_for(order(price="6000")) == 5
    assert policy.percentage_for(order(vip=True, promo=True, price="6000", quantity=4)) == 0


def test_umbral_estricto_y_unidades_minimas():
    policy = DiscountPolicy()
    # Cuatro unidades de 125 MXN dan exactamente 500 MXN.
    assert policy.percentage_for(order(vip=True, price="125", quantity=4)) == 0
    assert policy.percentage_for(order(vip=True, price="600", quantity=3)) == 0


def test_politica_combina_ambas_reglas_con_or():
    policy = DiscountPolicy()
    vip_10 = order(vip=True, price="600", quantity=4)
    normal_5 = order(price="6000")
    ninguno = order(price="100")
    assert policy.any_discount.is_satisfied_by(vip_10)
    assert policy.any_discount.is_satisfied_by(normal_5)
    assert not policy.any_discount.is_satisfied_by(ninguno)
