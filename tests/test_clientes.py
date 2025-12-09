"""
Tests para endpoints de Clientes.
"""
import pytest


def test_crear_cliente(client):
    """Test crear un cliente nuevo."""
    response = client.post(
        "/api/clientes/",
        json={
            "nombre": "María",
            "apellido": "González",
            "email": "maria@example.com",
            "telefono": "+56987654321",
            "direccion": "Av. Libertador 456",
            "comuna": "Providencia"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["nombre"] == "María"
    assert data["email"] == "maria@example.com"


def test_crear_cliente_email_duplicado(client, sample_cliente):
    """Test error al crear cliente con email duplicado."""
    response = client.post(
        "/api/clientes/",
        json={
            "nombre": "Otro Cliente",
            "email": sample_cliente["email"]
        }
    )
    assert response.status_code == 400


def test_listar_clientes(client, sample_cliente):
    """Test listar todos los clientes."""
    response = client.get("/api/clientes/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0


def test_obtener_cliente(client, sample_cliente):
    """Test obtener cliente por ID."""
    response = client.get(f"/api/clientes/{sample_cliente['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == sample_cliente["email"]


def test_actualizar_cliente(client, sample_cliente):
    """Test actualizar datos de cliente."""
    response = client.put(
        f"/api/clientes/{sample_cliente['id']}",
        json={
            "telefono": "+56911111111",
            "comuna": "Las Condes"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["telefono"] == "+56911111111"
    assert data["comuna"] == "Las Condes"


def test_eliminar_cliente_sin_pedidos(client):
    """Test eliminar cliente sin pedidos."""
    # Crear cliente
    response = client.post(
        "/api/clientes/",
        json={"nombre": "Cliente Temporal", "email": "temp@example.com"}
    )
    cliente = response.json()
    
    # Eliminar
    response = client.delete(f"/api/clientes/{cliente['id']}")
    assert response.status_code == 204


def test_no_eliminar_cliente_con_pedidos(client, producto_con_inventario):
    """Test que no se puede eliminar cliente con pedidos."""
    producto = producto_con_inventario["producto"]
    
    # Crear cliente específico para este test
    cliente = client.post(
        "/api/clientes/",
        json={
            "nombre": "Cliente Con Pedido",
            "email": "conpedido@example.com",
            "telefono": "+56912345678"
        }
    ).json()
    
    # Crear pedido con email del cliente
    client.post(
        "/api/pedidos/",
        json={
            "cliente_nombre": cliente["nombre"],
            "cliente_email": cliente["email"],
            "cliente_telefono": cliente["telefono"],
            "direccion_entrega": "Calle Test 123",
            "comuna": "Santiago",
            "items": [
                {
                    "sku": producto["sku"],
                    "cantidad": 5
                }
            ]
        }
    )
    
    # Intentar eliminar debe fallar
    response = client.delete(f"/api/clientes/{cliente['id']}")
    assert response.status_code == 400
