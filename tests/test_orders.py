
import pytest
from fastapi.testclient import TestClient

from app.main import app, Base, engine, SessionLocal, Order


@pytest.fixture
def client():
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        db.query(Order).delete()
        db.commit()

    with TestClient(app) as test_client:
        yield test_client

    with SessionLocal() as db:
        db.query(Order).delete()
        db.commit()


def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["database"] == "connected"


def test_create_order(client):
    response = client.post(
        "/orders",
        json={
            "customer_name": "jani",
            "item": "Keyboard",
            "quantity": 2,
            "unit_price": "1500.00",
        },
    )

    assert response.status_code == 201
    assert response.json()["customer_name"] == "jani"
    assert response.json()["total_price"] == "3000.00"


def test_list_and_retrieve_orders(client):
    created = client.post(
        "/orders",
        json={
            "customer_name": "supriya",
            "item": "keyboard",
            "quantity": 2,
            "unit_price": "1500.00",
        },
    )

    order_id = created.json()["id"]

    listed = client.get("/orders")
    retrieved = client.get(f"/orders/{order_id}")

    assert listed.status_code == 200
    assert any(order["id"] == order_id for order in listed.json())
    assert retrieved.status_code == 200
    assert retrieved.json()["item"] == "keyboard"


def test_missing_order_returns_404(client):
    response = client.get("/orders/999999")

    assert response.status_code == 404


def test_invalid_quantity_is_rejected(client):
    response = client.post(
        "/orders",
        json={
            "customer_name": "jani",
            "item": "Keyboard",
            "quantity": 0,
            "unit_price": "1500.00",
        },
    )

    assert response.status_code == 422


