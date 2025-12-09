"""
Tests para flujo completo de pedidos.
"""
import pytest


def test_crear_pedido(client, producto_con_inventario):
    """Test crear un pedido nuevo."""
    producto = producto_con_inventario["producto"]
    
    response = client.post(
        "/api/pedidos/",
        json={
            "cliente_nombre": "Cliente Test",
            "cliente_apellido": "Apellido Test",
            "cliente_email": "test@example.com",
            "cliente_telefono": "+56912345678",
            "direccion_entrega": "Calle Test 123",
            "comuna": "Santiago",
            "items": [
                {
                    "sku": producto["sku"],
                    "cantidad": 5
                }
            ],
            "notas": "Pedido de prueba"
        }
    )
    if response.status_code != 201:
        print(f"Error: {response.status_code}")
        print(f"Body: {response.text}")
    assert response.status_code == 201
    data = response.json()
    assert data["monto_total"] == 7500.0
    assert data["estado"] == "PENDIENTE"


def test_confirmar_pedido_descuenta_inventario(client, producto_con_inventario):
    """Test que confirmar pedido descuenta el inventario."""
    producto = producto_con_inventario["producto"]
    local = producto_con_inventario["local"]
    
    # Crear pedido
    response = client.post(
        "/api/pedidos/",
        json={
            "cliente_nombre": "Cliente Test",
            "cliente_email": "confirm@example.com",
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
    
    # Verificar stock inicial
    inv_inicial = client.get("/api/inventario/").json()
    stock_inicial = next(i["cantidad_stock"] for i in inv_inicial 
                        if i["producto_id"] == producto["id"] and i["local_id"] == local["id"])
    
    # Confirmar pedido
    response = client.put(
        f"/api/pedidos/{pedido_id}",
        json={
            "estado": "CONFIRMADO",
            "local_despacho_id": local["id"]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["inventario_descontado"] == True
    
    # Verificar que se descontó el inventario
    inv_final = client.get("/api/inventario/").json()
    stock_final = next(i["cantidad_stock"] for i in inv_final 
                      if i["producto_id"] == producto["id"] and i["local_id"] == local["id"])
    assert stock_final == stock_inicial - 10


def test_cancelar_pedido_devuelve_inventario(client, producto_con_inventario):
    """Test que cancelar pedido devuelve el inventario."""
    producto = producto_con_inventario["producto"]
    local = producto_con_inventario["local"]
    
    # Crear y confirmar pedido
    response = client.post(
        "/api/pedidos/",
        json={
            "cliente_nombre": "Cliente Test",
            "cliente_email": "cancel@example.com",
            "cliente_telefono": "+56912345678",
            "direccion_entrega": "Calle Test 123",
            "comuna": "Santiago",
            "items": [
                {
                    "sku": producto["sku"],
                    "cantidad": 15
                }
            ]
        }
    )
    pedido = response.json()
    pedido_id = pedido["pedido_id"]
    
    # Confirmar
    client.put(
        f"/api/pedidos/{pedido_id}",
        json={
            "estado": "CONFIRMADO",
            "local_despacho_id": local["id"]
        }
    )
    
    # Obtener stock después de confirmar
    inv_confirmado = client.get("/api/inventario/").json()
    stock_confirmado = next(i["cantidad_stock"] for i in inv_confirmado 
                           if i["producto_id"] == producto["id"] and i["local_id"] == local["id"])
    
    # Cancelar pedido
    response = client.put(
        f"/api/pedidos/{pedido_id}",
        json={"estado": "CANCELADO"}
    )
    assert response.status_code == 200
    
    # Verificar que se devolvió el inventario
    inv_cancelado = client.get("/api/inventario/").json()
    stock_cancelado = next(i["cantidad_stock"] for i in inv_cancelado 
                          if i["producto_id"] == producto["id"] and i["local_id"] == local["id"])
    assert stock_cancelado == stock_confirmado + 15


def test_no_confirmar_sin_stock_suficiente(client, producto_con_inventario):
    """Test que no se puede confirmar pedido sin stock suficiente."""
    producto = producto_con_inventario["producto"]
    local = producto_con_inventario["local"]
    
    # Crear pedido con más cantidad que el stock disponible
    response = client.post(
        "/api/pedidos/",
        json={
            "cliente_nombre": "Cliente Test",
            "cliente_email": "nostock@example.com",
            "cliente_telefono": "+56912345678",
            "direccion_entrega": "Calle Test 123",
            "comuna": "Santiago",
            "items": [
                {
                    "sku": producto["sku"],
                    "cantidad": 150  # Más que el stock de 100
                }
            ]
        }
    )
    pedido = response.json()
    pedido_id = pedido["pedido_id"]
    
    # Intentar confirmar debe fallar
    response = client.put(
        f"/api/pedidos/{pedido_id}",
        json={
            "estado": "CONFIRMADO",
            "local_despacho_id": local["id"]
        }
    )
    assert response.status_code == 400


def test_listar_pedidos(client, producto_con_inventario):
    """Test listar todos los pedidos."""
    producto = producto_con_inventario["producto"]
    
    # Crear pedido
    client.post(
        "/api/pedidos/",
        json={
            "cliente_nombre": "Cliente Test",
            "cliente_email": "list@example.com",
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
    
    response = client.get("/api/pedidos/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
