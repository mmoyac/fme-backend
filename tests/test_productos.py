"""
Tests para endpoints de Productos.
"""
import pytest


def test_crear_producto(client):
    """Test crear un producto nuevo."""
    response = client.post(
        "/api/productos/",
        json={
            "nombre": "Hallulla",
            "descripcion": "Pan tradicional",
            "sku": "HALL-001"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["nombre"] == "Hallulla"
    assert data["sku"] == "HALL-001"
    assert "id" in data


def test_crear_producto_sku_duplicado(client, sample_producto):
    """Test error al crear producto con SKU duplicado."""
    response = client.post(
        "/api/productos/",
        json={
            "nombre": "Otro Producto",
            "descripcion": "Test",
            "sku": sample_producto["sku"]
        }
    )
    assert response.status_code == 400


def test_listar_productos(client, sample_producto):
    """Test listar todos los productos."""
    response = client.get("/api/productos/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["id"] == sample_producto["id"]


def test_obtener_producto(client, sample_producto):
    """Test obtener producto por ID."""
    response = client.get(f"/api/productos/{sample_producto['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["nombre"] == sample_producto["nombre"]


def test_actualizar_producto(client, sample_producto):
    """Test actualizar producto."""
    response = client.put(
        f"/api/productos/{sample_producto['id']}",
        json={
            "nombre": "Pan Amasado Especial",
            "descripcion": "Nueva descripción"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["nombre"] == "Pan Amasado Especial"


def test_eliminar_producto(client, sample_producto):
    """Test eliminar producto."""
    response = client.delete(f"/api/productos/{sample_producto['id']}")
    assert response.status_code == 204
    
    # Verificar que ya no existe
    response = client.get(f"/api/productos/{sample_producto['id']}")
    assert response.status_code == 404


def test_producto_no_existe(client):
    """Test obtener producto inexistente."""
    response = client.get("/api/productos/9999")
    assert response.status_code == 404
