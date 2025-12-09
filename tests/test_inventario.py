"""
Tests para endpoints de Inventario.
"""
import pytest


def test_crear_inventario(client, sample_producto, sample_local):
    """Test crear registro de inventario."""
    response = client.put(
        f"/api/inventario/producto/{sample_producto['id']}/local/{sample_local['id']}",
        json={"cantidad_stock": 50}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["cantidad_stock"] == 50


def test_actualizar_inventario(client, producto_con_inventario):
    """Test actualizar cantidad de inventario."""
    producto = producto_con_inventario["producto"]
    local = producto_con_inventario["local"]
    
    response = client.put(
        f"/api/inventario/producto/{producto['id']}/local/{local['id']}",
        json={"cantidad_stock": 75}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["cantidad_stock"] == 75


def test_listar_inventario(client, producto_con_inventario):
    """Test listar todo el inventario."""
    response = client.get("/api/inventario/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0


def test_resumen_inventario(client, producto_con_inventario):
    """Test obtener resumen de inventario."""
    response = client.get("/api/inventario/resumen")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert "sku" in data[0]
    assert "stock_total" in data[0]


def test_detalle_inventario(client, producto_con_inventario):
    """Test obtener detalle de inventario por SKU."""
    producto = producto_con_inventario["producto"]
    
    response = client.get(f"/api/inventario/detalle/{producto['sku']}")
    assert response.status_code == 200
    data = response.json()
    assert data["sku"] == producto["sku"]
    assert "stock_total" in data
    assert "detalle_locales" in data
