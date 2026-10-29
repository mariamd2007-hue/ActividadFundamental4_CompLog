from fastapi.testclient import TestClient

from app.api import create_app
from cargar_csv import load_fixture


def client_with_fixtures():
    return TestClient(create_app(load_fixture()))


def test_get_pedido_incluye_descuento_y_datos_de_catalogo():
    response = client_with_fixtures().get("/orders/O001")
    assert response.status_code == 200
    assert response.json()["status"] == "DRAFT"
    assert response.json()["units"] == 4
    assert response.json()["total_mxn"] == "2100.00"
    assert response.json()["discount_percent"] == 10


def test_pedido_inexistente_responde_404():
    assert client_with_fixtures().post("/orders/no-existe/confirm").status_code == 404


def test_confirmacion_doble_responde_409():
    client = client_with_fixtures()
    assert client.post("/orders/O013/confirm").status_code == 200
    assert client.post("/orders/O013/confirm").status_code == 409


def test_confirmar_pedido_vacio_responde_422():
    assert client_with_fixtures().post("/orders/O007/confirm").status_code == 422


def test_envio_y_cancelacion_api():
    client = client_with_fixtures()
    assert client.post("/orders/O001/confirm").status_code == 200
    shipped = client.post("/orders/O001/ship", json={"tracking_number": "TRK-1"})
    assert shipped.status_code == 200
    assert shipped.json()["status"] == "SHIPPED"
    assert client.post("/orders/O001/cancel", json={"reason": "cambio"}).status_code == 409


def test_cancelacion_exitosa_desde_confirmed():
    client = client_with_fixtures()
    assert client.post("/orders/O013/confirm").status_code == 200
    response = client.post("/orders/O013/cancel", json={"reason": "cambio"})
    assert response.status_code == 200
    assert response.json()["status"] == "CANCELLED"
    assert response.json()["events"] == ["OrderConfirmed", "OrderCancelled"]


def test_envio_sin_guia_en_blanco_responde_422_y_no_cambia_estado():
    client = client_with_fixtures()
    client.post("/orders/O012/confirm")
    assert client.post("/orders/O012/ship", json={"tracking_number": "   "}).status_code == 422
    assert client.get("/orders/O012").json()["status"] == "CONFIRMED"


def test_entrega_y_devolucion_por_api():
    client = client_with_fixtures()
    for order_id in ("O015", "O016"):
        client.post(f"/orders/{order_id}/confirm")
        client.post(f"/orders/{order_id}/ship", json={"tracking_number": "TRK"})
    assert client.post("/orders/O015/return").json()["status"] == "RETURNED"
    assert client.post("/orders/O016/deliver").json()["status"] == "DELIVERED"
    assert client.post("/orders/O016/return").status_code == 409


def test_entregar_desde_draft_responde_409():
    assert client_with_fixtures().post("/orders/O001/deliver").status_code == 409
