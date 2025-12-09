"""
Tests para transferencias de inventario.
"""
import pytest


def test_transferir_inventario(client):
    """Test transferir inventario entre locales."""
    # Crear producto
    producto = client.post(
        "/api/productos/",
        json={"nombre": "Producto Test", "sku": "TEST-001"}
    ).json()
    
    # Crear dos locales
    local_origen = client.post(
        "/api/locales/",
        json={"codigo": "A", "nombre": "Local A"}
    ).json()
    
    local_destino = client.post(
        "/api/locales/",
        json={"codigo": "B", "nombre": "Local B"}
    ).json()
    
    # Crear inventario en origen
    client.put(
        f"/api/inventario/producto/{producto['id']}/local/{local_origen['id']}",
        json={"cantidad_stock": 50}
    )
    
    # Crear inventario en destino
    client.put(
        f"/api/inventario/producto/{producto['id']}/local/{local_destino['id']}",
        json={"cantidad_stock": 10}
    )
    
    # Realizar transferencia
    response = client.post(
        "/api/movimientos/transferencia",
        json={
            "producto_id": producto["id"],
            "local_origen_id": local_origen["id"],
            "local_destino_id": local_destino["id"],
            "cantidad": 20,
            "notas": "Transferencia de prueba"
        }
    )
    assert response.status_code == 201
    data = response.json()
    # Verificar que la transferencia se creó exitosamente
    assert "mensaje" in data or "movimientos" in data


def test_transferir_sin_stock_suficiente(client):
    """Test error al transferir sin stock suficiente."""
    # Crear producto y locales
    producto = client.post(
        "/api/productos/",
        json={"nombre": "Producto Test", "sku": "TEST-002"}
    ).json()
    
    local_a = client.post(
        "/api/locales/",
        json={"codigo": "LA", "nombre": "Local A"}
    ).json()
    
    local_b = client.post(
        "/api/locales/",
        json={"codigo": "LB", "nombre": "Local B"}
    ).json()
    
    # Solo 10 en origen
    client.put(
        f"/api/inventario/producto/{producto['id']}/local/{local_a['id']}",
        json={"cantidad_stock": 10}
    )
    
    # Intentar transferir 20 (más de lo disponible)
    response = client.post(
        "/api/movimientos/transferencia",
        json={
            "producto_id": producto["id"],
            "local_origen_id": local_a["id"],
            "local_destino_id": local_b["id"],
            "cantidad": 20
        }
    )
    assert response.status_code == 400


def test_listar_historial_movimientos(client):
    """Test listar historial de movimientos."""
    # Crear datos
    producto = client.post(
        "/api/productos/",
        json={"nombre": "Producto Test", "sku": "TEST-003"}
    ).json()
    
    local_a = client.post(
        "/api/locales/",
        json={"codigo": "LA2", "nombre": "Local A"}
    ).json()
    
    local_b = client.post(
        "/api/locales/",
        json={"codigo": "LB2", "nombre": "Local B"}
    ).json()
    
    client.put(
        f"/api/inventario/producto/{producto['id']}/local/{local_a['id']}",
        json={"cantidad_stock": 50}
    )
    
    # Realizar transferencia
    client.post(
        "/api/movimientos/transferencia",
        json={
            "producto_id": producto["id"],
            "local_origen_id": local_a["id"],
            "local_destino_id": local_b["id"],
            "cantidad": 10
        }
    )
    
    # Listar movimientos
    response = client.get("/api/movimientos/historial")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["tipo_movimiento"] == "TRANSFERENCIA"


def test_filtrar_movimientos_por_producto(client):
    """Test filtrar historial por producto."""
    # Crear producto
    producto = client.post(
        "/api/productos/",
        json={"nombre": "Producto Filtro", "sku": "FILT-001"}
    ).json()
    
    local_a = client.post(
        "/api/locales/",
        json={"codigo": "FA", "nombre": "Local FA"}
    ).json()
    
    local_b = client.post(
        "/api/locales/",
        json={"codigo": "FB", "nombre": "Local FB"}
    ).json()
    
    client.put(
        f"/api/inventario/producto/{producto['id']}/local/{local_a['id']}",
        json={"cantidad_stock": 50}
    )
    
    # Realizar transferencia
    client.post(
        "/api/movimientos/transferencia",
        json={
            "producto_id": producto["id"],
            "local_origen_id": local_a["id"],
            "local_destino_id": local_b["id"],
            "cantidad": 5
        }
    )
    
    # Filtrar por producto
    response = client.get(f"/api/movimientos/historial?producto_id={producto['id']}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert all(m["producto"]["id"] == producto["id"] for m in data)
