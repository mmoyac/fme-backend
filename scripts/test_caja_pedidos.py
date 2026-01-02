"""
Script para probar la integración del sistema de caja con pedidos.
Ejecutar: docker-compose exec backend python scripts/test_caja_pedidos.py
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_caja_integration():
    session = requests.Session()

    # 1. Login
    print("🔐 Logueando como admin...")
    login_data = {
        "username": "admin@fme.cl",
        "password": "admin"
    }
    resp = session.post(f"{BASE_URL}/api/auth/token", data=login_data)
    if resp.status_code != 200:
        print(f"❌ Error login: {resp.text}")
        return
    
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Login exitoso\n")

    # 2. Obtener locales
    print("📋 Obteniendo locales...")
    resp = session.get(f"{BASE_URL}/api/locales/", headers=headers)
    locales = resp.json()
    local_fisico = next((l for l in locales if l["codigo"] != "WEB"), None)
    if not local_fisico:
        print("❌ No hay locales físicos disponibles")
        return
    print(f"✅ Local físico: {local_fisico['nombre']} (ID: {local_fisico['id']})")

    # 3. Verificar si ya hay turno abierto y cerrarlo
    print("🔍 Verificando turnos abiertos...")
    resp = session.get(f"{BASE_URL}/api/caja/estado", headers=headers)
    estado = resp.json()
    
    if estado["tiene_caja_abierta"] and estado["turno_activo"]:
        print(f"🔒 Cerrando turno abierto (ID: {estado['turno_activo']['id']})...")
        cierre_previo = {
            "efectivo_real": 100000.0,  # Efectivo real contado
            "observaciones_cierre": "Cierre automático para limpiar estado antes de prueba"
        }
        resp = session.put(f"{BASE_URL}/api/caja/turno/{estado['turno_activo']['id']}/cerrar", json=cierre_previo, headers=headers)
        if resp.status_code == 200:
            print("✅ Turno anterior cerrado")
        else:
            print(f"⚠️ Error cerrando turno anterior: {resp.text}")

    # 4. Abrir turno de caja
    print("💰 Abriendo turno de caja...")
    turno_data = {
        "local_id": local_fisico["id"],
        "monto_inicial": 50000.0,
        "observaciones": "Turno de prueba para integración con pedidos"
    }
    resp = session.post(f"{BASE_URL}/api/caja/turno/abrir", json=turno_data, headers=headers)
    if resp.status_code != 201:
        print(f"❌ Error abriendo turno: {resp.text}")
        return
    
    turno = resp.json()
    print(f"✅ Turno abierto (ID: {turno['id']})")

    # 5. Crear cliente de prueba
    print("👤 Creando cliente de prueba...")
    cliente_data = {
        "nombre": "Cliente Test Caja",
        "email": f"test.caja.{turno['id']}@ejemplo.com",
        "telefono": "+56912345678",
        "direccion": "Dirección de prueba 123",
        "comuna": "Santiago"
    }
    resp = session.post(f"{BASE_URL}/api/clientes/", json=cliente_data, headers=headers)
    cliente = resp.json()
    print(f"✅ Cliente creado (ID: {cliente['id']})")

    # 6. Obtener productos
    resp = session.get(f"{BASE_URL}/api/productos/", headers=headers)
    productos = resp.json()
    if not productos:
        print("❌ No hay productos disponibles")
        return
    
    producto = productos[0]
    print(f"✅ Producto seleccionado: {producto['nombre']} (ID: {producto['id']})")

    # 6.5. Agregar inventario al producto (simplificado)
    print("📦 Agregando inventario al producto...")
    inventario_data = {
        "cantidad_stock": 100
    }
    resp = session.put(f"{BASE_URL}/api/inventario/producto/{producto['id']}/local/{local_fisico['id']}", 
                      json=inventario_data, headers=headers)
    if resp.status_code == 200:
        print("✅ Inventario agregado (100 unidades)")
    else:
        print(f"⚠️ Error agregando inventario: {resp.text}")

    # 7. Obtener o crear medio de pago
    resp = session.get(f"{BASE_URL}/api/maestras/medios-pago", headers=headers)
    medios = resp.json()
    
    if not medios:
        # Crear un medio de pago de prueba
        print("💳 Creando medio de pago de prueba...")
        medio_data = {
            "nombre": "Efectivo",
            "descripcion": "Pago en efectivo",
            "activo": True,
            "permite_cheque": False
        }
        resp = session.post(f"{BASE_URL}/api/maestras/medios-pago", json=medio_data, headers=headers)
        if resp.status_code == 201:
            medio_efectivo = resp.json()
            print(f"✅ Medio de pago creado: {medio_efectivo['nombre']} (ID: {medio_efectivo['id']})")
        else:
            print(f"❌ Error creando medio de pago: {resp.text}")
            return
    else:
        medio_efectivo = next((m for m in medios if "efectivo" in m["nombre"].lower()), medios[0])
        print(f"✅ Medio de pago: {medio_efectivo['nombre']} (ID: {medio_efectivo['id']})")

    # 8. Crear pedido desde backoffice
    print("📋 Creando pedido desde backoffice...")
    pedido_data = {
        "cliente_id": cliente["id"],
        "cliente_nombre": cliente["nombre"],
        "cliente_email": cliente["email"],
        "cliente_telefono": cliente["telefono"],
        "direccion_entrega": cliente["direccion"],
        "local_id": local_fisico["id"],
        "medio_pago_id": medio_efectivo["id"],
        "items": [
            {
                "sku": producto["sku"],
                "producto_id": producto["id"],
                "cantidad": 2,
                "precio_unitario_venta": 2500.0
            }
        ],
        "notas": "Pedido de prueba para integración caja",
        "puntos_usar": 0
    }
    
    resp = session.post(f"{BASE_URL}/api/pedidos/backoffice", json=pedido_data, headers=headers)
    if resp.status_code != 201:
        print(f"❌ Error creando pedido: {resp.text}")
        return
    
    pedido = resp.json()
    print(f"✅ Pedido creado (ID: {pedido['pedido_id']}, Total: ${pedido['monto_total']})")

    # 9. Verificar que no hay operaciones de caja todavía
    resp = session.get(f"{BASE_URL}/api/caja/turno/{turno['id']}", headers=headers)
    turno_detalle = resp.json()
    operaciones_antes = turno_detalle.get('operaciones', [])
    print(f"ℹ️  Operaciones antes de confirmar: {len(operaciones_antes)}")

    # 10. Confirmar pedido (esto debe crear la operación de caja automáticamente)
    print("✅ Confirmando pedido (esto debería crear operación de caja)...")
    confirmacion_data = {
        "estado": "CONFIRMADO",
        "local_despacho_id": local_fisico["id"]
    }
    
    resp = session.put(f"{BASE_URL}/api/pedidos/{pedido['pedido_id']}", json=confirmacion_data, headers=headers)
    if resp.status_code != 200:
        print(f"❌ Error confirmando pedido: {resp.text}")
        return
    
    pedido_confirmado = resp.json()
    print(f"✅ Pedido confirmado (Estado: {pedido_confirmado['estado']})")

    # 11. Verificar que se creó la operación de caja
    resp = session.get(f"{BASE_URL}/api/caja/turno/{turno['id']}", headers=headers)
    turno_detalle_despues = resp.json()
    operaciones_despues = turno_detalle_despues.get('operaciones', [])
    print(f"💰 Operaciones después de confirmar: {len(operaciones_despues)}")
    
    if len(operaciones_despues) > len(operaciones_antes):
        nueva_operacion = operaciones_despues[-1]  # La última operación
        print("🎉 ¡Integración exitosa! Nueva operación de caja:")
        print(f"   - Tipo: {nueva_operacion['tipo_operacion']}")
        print(f"   - Monto: ${nueva_operacion['monto']}")
        print(f"   - Descripción: {nueva_operacion['descripcion']}")
        print(f"   - Observaciones: {nueva_operacion['observaciones'][:50]}...")
    else:
        print("❌ No se creó operación de caja automáticamente")

    # 12. Verificar totales del turno
    turno_actualizado = turno_detalle_despues  # Ya lo obtuvimos en el paso anterior
    print(f"\n💼 Estado del turno después de la venta:")
    print(f"   - Monto inicial: ${turno_actualizado['monto_inicial']}")
    print(f"   - Total de operaciones: {len(operaciones_despues)} operaciones")
    
    # Calcular totales a partir de las operaciones
    total_ventas = sum([float(op['monto']) for op in operaciones_despues if op['tipo_operacion'] == 'VENTA'])
    print(f"   - Total ventas calculado: ${total_ventas}")

    # 13. Cerrar turno (opcional)
    print("\n🔒 Cerrando turno...")
    cierre_data = {
        "efectivo_real": 50000.0 + total_ventas,  # monto_inicial + ventas calculadas
        "observaciones_cierre": "Cierre automático después de prueba de integración"
    }
    
    resp = session.put(f"{BASE_URL}/api/caja/turno/{turno['id']}/cerrar", json=cierre_data, headers=headers)
    if resp.status_code == 200:
        print("✅ Turno cerrado exitosamente")
    else:
        print(f"⚠️ Error cerrando turno: {resp.text}")

    print("\n🎉 ¡Prueba de integración completada!")

if __name__ == "__main__":
    test_caja_integration()