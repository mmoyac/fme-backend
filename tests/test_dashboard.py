"""
Tests para endpoints de Dashboard.
"""
import pytest


def test_estadisticas_dashboard(client, producto_con_inventario):
    """Test obtener estadísticas del dashboard."""
    producto = producto_con_inventario["producto"]
    
    # Crear algunos pedidos
    for i in range(3):
        client.post(
            "/api/pedidos/",
            json={
                "cliente_nombre": f"Cliente {i}",
                "cliente_email": f"cliente{i}@example.com",
                "cliente_telefono": "+56912345678",
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
    
    response = client.get("/api/dashboard/estadisticas")
    assert response.status_code == 200
    data = response.json()
    
    # Verificar estructura
    assert "ventas" in data
    assert "pedidos" in data
    assert "por_cobrar" in data
    assert "ticket_promedio" in data
    assert "top_productos" in data
    assert "stock_bajo" in data
    assert "ventas_por_dia" in data
    assert "ultimos_pedidos" in data
    
    # Verificar datos
    assert data["pedidos"]["total"] >= 3
    assert "hoy" in data["ventas"]
    assert "mes" in data["ventas"]


def test_estadisticas_con_pedidos_confirmados(client, producto_con_inventario):
    """Test estadísticas con pedidos en diferentes estados."""
    producto = producto_con_inventario["producto"]
    local = producto_con_inventario["local"]
    
    # Crear pedido y confirmarlo
    response = client.post(
        "/api/pedidos/",
        json={
            "cliente_nombre": "Cliente Confirmado",
            "cliente_email": "confirmado@example.com",
            "cliente_telefono": "+56912345678",
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
    pedido = response.json()
    pedido_id = pedido["pedido_id"]
    pedido_id = pedido["pedido_id"]
    
    # Confirmar
    client.put(
        f"/api/pedidos/{pedido_id}",
        json={
            "estado": "CONFIRMADO",
            "local_despacho_id": local["id"]
        }
    )
    
    # Obtener estadísticas
    response = client.get("/api/dashboard/estadisticas")
    assert response.status_code == 200
    data = response.json()
    
    assert data["pedidos"]["por_estado"]["CONFIRMADO"] >= 1
    assert data["ventas"]["mes"] > 0


def test_estadisticas_por_cobrar(client, producto_con_inventario):
    """Test métrica de pedidos por cobrar."""
    producto = producto_con_inventario["producto"]
    local = producto_con_inventario["local"]
    
    # Crear pedido sin pagar
    response = client.post(
        "/api/pedidos/",
        json={
            "cliente_nombre": "Cliente Por Cobrar",
            "cliente_email": "porcobrar@example.com",
            "cliente_telefono": "+56912345678",
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
    pedido = response.json()
    pedido_id = pedido["pedido_id"]
    
    # Confirmar pero no pagar
    client.put(
        f"/api/pedidos/{pedido_id}",
        json={
            "estado": "CONFIRMADO",
            "local_despacho_id": local["id"]
        }
    )
    
    # Obtener estadísticas
    response = client.get("/api/dashboard/estadisticas")
    data = response.json()
    
    assert data["por_cobrar"]["cantidad"] >= 1
    assert data["por_cobrar"]["monto"] >= 5000.0


def test_top_productos_vendidos(client, producto_con_inventario):
    """Test top productos más vendidos."""
    producto = producto_con_inventario["producto"]
    local = producto_con_inventario["local"]
    
    # Crear varios pedidos del mismo producto
    for i in range(3):
        response = client.post(
            "/api/pedidos/",
            json={
                "cliente_nombre": f"Cliente Top {i}",
                "cliente_email": f"top{i}@example.com",
                "cliente_telefono": "+56912345678",
                "direccion_entrega": "Calle Test 123",
                "comuna": "Santiago",
                "items": [
                    {
                        "sku": producto["sku"],
                        "cantidad": 10
                    }
                ]
            }
        )
        pedido = response.json()
        pedido_id = pedido["pedido_id"]
        pedido_id = pedido["pedido_id"]
        
        # Confirmar
        client.put(
            f"/api/pedidos/{pedido_id}",
            json={
                "estado": "CONFIRMADO",
                "local_despacho_id": local["id"]
            }
        )
    
    # Obtener estadísticas
    response = client.get("/api/dashboard/estadisticas")
    data = response.json()
    
    assert len(data["top_productos"]) > 0
    assert data["top_productos"][0]["cantidad_vendida"] >= 30
