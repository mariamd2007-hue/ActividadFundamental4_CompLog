"""API REST. Los endpoints delegan las reglas a Order."""

from typing import Callable

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.domain import DomainException, InvalidOrderData, InvalidOrderTransition, Order
from app.specifications import DiscountPolicy
from cargar_csv import load_fixture


class ShipRequest(BaseModel):
    tracking_number: str = Field(min_length=1)


class CancelRequest(BaseModel):
    reason: str = Field(min_length=1)


def create_app(orders: dict[str, Order] | None = None) -> FastAPI:
    app = FastAPI(
        title="TechStore U4",
        version="1.0.0",
        description="Administración de pedidos en memoria para la Actividad 4.",
    )
    app.state.orders = orders if orders is not None else load_fixture()
    policy = DiscountPolicy()

    def get_order(order_id: str) -> Order:
        order = app.state.orders.get(order_id)
        if order is None:
            raise HTTPException(status_code=404, detail="No existe el pedido")
        return order

    def view(order: Order) -> dict:
        discount = policy.evaluate(order)
        return {
            "id": order.id,
            "customer_id": order.customer.id,
            "status": order.status.value,
            "units": order.units,
            "total_mxn": str(order.total.amount),
            "discount_percent": discount.percentage,
            "discount_mxn": str(discount.discount.amount),
            "total_after_discount_mxn": str(discount.total_after_discount.amount),
            "events": [event.name for event in order.events],
        }

    def perform(order_id: str, action: Callable[[Order], None]) -> dict:
        order = get_order(order_id)
        try:
            action(order)
        except InvalidOrderTransition as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except InvalidOrderData as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except DomainException as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return view(order)

    @app.get("/orders/{order_id}")
    def get_order_detail(order_id: str) -> dict:
        return view(get_order(order_id))

    @app.post("/orders/{order_id}/confirm")
    def confirm_order(order_id: str) -> dict:
        return perform(order_id, lambda order: order.confirm())

    @app.post("/orders/{order_id}/ship")
    def ship_order(order_id: str, request: ShipRequest) -> dict:
        return perform(order_id, lambda order: order.ship(request.tracking_number))

    @app.post("/orders/{order_id}/cancel")
    def cancel_order(order_id: str, request: CancelRequest) -> dict:
        return perform(order_id, lambda order: order.cancel(request.reason))

    @app.post("/orders/{order_id}/deliver")
    def deliver_order(order_id: str) -> dict:
        return perform(order_id, lambda order: order.deliver())

    @app.post("/orders/{order_id}/return")
    def return_order(order_id: str) -> dict:
        return perform(order_id, lambda order: order.return_order())

    return app


app = create_app()
