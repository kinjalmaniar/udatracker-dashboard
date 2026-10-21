import pytest
from backend.app import app, in_memory_storage


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['DEBUG'] = False
    in_memory_storage.clear()
    with app.test_client() as client:
        yield client


def create(client, order_id, status="pending", customer_id="C1"):
    return client.post('/api/orders', json={
        "order_id": order_id, "item_name": "Item", "quantity": 1,
        "customer_id": customer_id, "status": status,
    })


def test_add_order_defaults_to_pending(client):
    response = client.post('/api/orders', json={
        "order_id": "D001", "item_name": "Item", "quantity": 1, "customer_id": "C1"
    })
    assert response.status_code == 201
    assert response.json["status"] == "pending"


def test_add_order_duplicate_returns_400(client):
    create(client, "DUP001")
    response = create(client, "DUP001")
    assert response.status_code == 400
    assert "already exists" in response.json["error"]


def test_add_order_missing_field_returns_400(client):
    response = client.post('/api/orders', json={"order_id": "M001", "quantity": 1, "customer_id": "C1"})
    assert response.status_code == 400
    assert response.json["error"] == "'item_name' is required."


def test_add_order_invalid_quantity_returns_400(client):
    response = client.post('/api/orders', json={
        "order_id": "Q001", "item_name": "Item", "quantity": 0, "customer_id": "C1"
    })
    assert response.status_code == 400


def test_add_order_without_json_body_returns_400(client):
    response = client.post('/api/orders', data="not json")
    assert response.status_code == 400
    assert "error" in response.json


def test_get_order_not_found_returns_json_error(client):
    response = client.get('/api/orders/NOPE')
    assert response.status_code == 404
    assert response.json["error"] == "Order with ID 'NOPE' not found."


def test_update_status_not_found_returns_404(client):
    response = client.put('/api/orders/NOPE/status', json={"new_status": "shipped"})
    assert response.status_code == 404
    assert "error" in response.json


def test_update_status_invalid_status_returns_400(client):
    create(client, "U001")
    response = client.put('/api/orders/U001/status', json={"new_status": "lost"})
    assert response.status_code == 400
    assert client.get('/api/orders/U001').json["status"] == "pending"


def test_list_orders_empty(client):
    response = client.get('/api/orders')
    assert response.status_code == 200
    assert response.json == []


def test_list_orders_invalid_status_returns_400(client):
    response = client.get('/api/orders?status=lost')
    assert response.status_code == 400


def test_list_orders_by_customer_and_status(client):
    create(client, "F001", "pending", "C1")
    create(client, "F002", "shipped", "C1")
    create(client, "F003", "shipped", "C2")

    by_customer = client.get('/api/orders?customer_id=C1')
    assert [o["order_id"] for o in by_customer.json] == ["F001", "F002"]

    combined = client.get('/api/orders?customer_id=C1&status=shipped')
    assert [o["order_id"] for o in combined.json] == ["F002"]


def test_delete_order(client):
    create(client, "DEL001")
    response = client.delete('/api/orders/DEL001')
    assert response.status_code == 204
    assert client.get('/api/orders/DEL001').status_code == 404


def test_delete_order_not_found_returns_404(client):
    response = client.delete('/api/orders/NOPE')
    assert response.status_code == 404
