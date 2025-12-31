#!/usr/bin/env python3
"""
Script para probar el sistema de cheques con un ejemplo completo.
"""
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

def test_sistema_cheques():
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

    # 2. Crear pedido con medio de pago CHEQUE
    print("📝 Creando pedido con medio de pago CHEQUE...")
    
    # Primero verificar que existe el medio de pago CHEQUE
    resp = session.get(f"{BASE_URL}/api/maestras/medios-pago", headers=headers)
    medios = resp.json()
    medio_cheque = next((m for m in medios if m['codigo'] == 'CHEQUE'), None)
    
    if not medio_cheque:
        print("❌ Medio de pago CHEQUE no encontrado")
        return
    
    print(f"✅ Medio de pago CHEQUE encontrado (ID: {medio_cheque['id']})")
    
    # Crear pedido de prueba con cheque
    pedido_data = {
        "cliente_nombre": "Juan",
        "cliente_apellido": "Pérez", 
        "cliente_email": "juan.perez.cheque@test.cl",
        "cliente_telefono": "987654321",
        "direccion_entrega": "Av. Principal 123",
        "comuna": "Santiago",
        "medio_pago_codigo": "CHEQUE",
        "notas": "Pedido de prueba para pago con cheques",
        "items": [
            {"sku": "10050", "cantidad": 2},
            {"sku": "10051", "cantidad": 1}
        ]
    }
    
    resp = session.post(f"{BASE_URL}/api/pedidos/", json=pedido_data, headers=headers)
    if resp.status_code != 201:
        print(f"❌ Error creando pedido: {resp.text}")
        return
    
    pedido = resp.json()
    pedido_id = pedido["pedido_id"]
    print(f"✅ Pedido creado (ID: {pedido_id}, Total: ${pedido['monto_total']})")
    
    # 3. Crear dos cheques para el pedido
    print(f"\n💰 Creando cheques para el pedido {pedido_id}...")
    
    # Buscar estado PENDIENTE
    resp = session.get(f"{BASE_URL}/api/maestras/estados-cheque", headers=headers)
    estados = resp.json()
    estado_pendiente = next((e for e in estados if e['codigo'] == 'PENDIENTE'), None)
    
    # Cheque 1 - $50.000
    cheque1_data = {
        "pedido_id": pedido_id,
        "numero_cheque": "12345678",
        "banco": "Banco Estado",
        "monto": 50000,
        "fecha_emision": datetime.now().isoformat(),
        "fecha_vencimiento": (datetime.now() + timedelta(days=30)).isoformat(),
        "librador_nombre": "Juan Pérez",
        "librador_rut": "12345678-9",
        "observaciones": "Primer cheque del pedido"
    }
    
    resp = session.post(f"{BASE_URL}/api/cheques/", json=cheque1_data, headers=headers)
    if resp.status_code != 200:
        print(f"❌ Error creando cheque 1: {resp.text}")
        return
    
    cheque1 = resp.json()
    print(f"✅ Cheque 1 creado (ID: {cheque1['id']}, Monto: ${cheque1['monto']})")
    
    # Cheque 2 - Resto del monto
    monto_restante = float(pedido['monto_total']) - 50000
    cheque2_data = {
        "pedido_id": pedido_id,
        "numero_cheque": "87654321",
        "banco": "Banco Chile",
        "monto": monto_restante,
        "fecha_emision": datetime.now().isoformat(),
        "fecha_vencimiento": (datetime.now() + timedelta(days=60)).isoformat(),
        "librador_nombre": "Juan Pérez",
        "librador_rut": "12345678-9",
        "observaciones": "Segundo cheque del pedido"
    }
    
    resp = session.post(f"{BASE_URL}/api/cheques/", json=cheque2_data, headers=headers)
    if resp.status_code != 200:
        print(f"❌ Error creando cheque 2: {resp.text}")
        return
    
    cheque2 = resp.json()
    print(f"✅ Cheque 2 creado (ID: {cheque2['id']}, Monto: ${cheque2['monto']})")
    
    # 4. Ver estado del pedido con cheques
    print(f"\n📊 Estado actual del pedido...")
    resp = session.get(f"{BASE_URL}/api/cheques/pedido/{pedido_id}", headers=headers)
    if resp.status_code == 200:
        detalle = resp.json()
        print(f"  Pedido: {detalle['numero_pedido']}")
        print(f"  Monto Total: ${detalle['monto_total']}")
        print(f"  ¿Está Pagado?: {detalle['es_pagado']}")
        print(f"  Medio de Pago: {detalle['medio_pago_codigo']}")
        
        if detalle['resumen_cheques']:
            resumen = detalle['resumen_cheques']
            print(f"  Total Cheques: {resumen['total_cheques']}")
            print(f"  Monto Total Cheques: ${resumen['monto_total_cheques']}")
            print(f"  Cheques Pendientes: {resumen['cheques_pendientes']}")
            print(f"  Cheques Cobrados: {resumen['cheques_cobrados']}")
            print(f"  ¿Todos Cobrados?: {resumen['todos_cobrados']}")
    
    # 5. Simular cobro del primer cheque
    print(f"\n💳 Cobrando primer cheque...")
    
    # Buscar estado COBRADO
    estado_cobrado = next((e for e in estados if e['codigo'] == 'COBRADO'), None)
    if not estado_cobrado:
        print("❌ Estado COBRADO no encontrado")
        return
    
    update_data = {
        "estado_id": estado_cobrado['id'],
        "observaciones": "Cheque cobrado exitosamente"
    }
    
    resp = session.put(f"{BASE_URL}/api/cheques/{cheque1['id']}", json=update_data, headers=headers)
    if resp.status_code == 200:
        print("✅ Primer cheque marcado como COBRADO")
        
        # Ver estado actualizado
        resp = session.get(f"{BASE_URL}/api/cheques/pedido/{pedido_id}/resumen", headers=headers)
        if resp.status_code == 200:
            resumen = resp.json()
            print(f"  Cheques Cobrados: {resumen['cheques_cobrados']}/{resumen['total_cheques']}")
            print(f"  ¿Pedido Pagado?: {not resumen['todos_cobrados']}")  # Debería ser False
    
    # 6. Cobrar segundo cheque
    print(f"\n💳 Cobrando segundo cheque...")
    
    resp = session.put(f"{BASE_URL}/api/cheques/{cheque2['id']}", json=update_data, headers=headers)
    if resp.status_code == 200:
        print("✅ Segundo cheque marcado como COBRADO")
        
        # Ver estado final
        resp = session.get(f"{BASE_URL}/api/cheques/pedido/{pedido_id}", headers=headers)
        if resp.status_code == 200:
            detalle = resp.json()
            print(f"\n🎉 ESTADO FINAL:")
            print(f"  Pedido: {detalle['numero_pedido']}")
            print(f"  ¿Está Pagado?: {detalle['es_pagado']}")  # Debería ser True
            
            if detalle['resumen_cheques']:
                resumen = detalle['resumen_cheques']
                print(f"  ¿Todos los cheques cobrados?: {resumen['todos_cobrados']}")
    
    print("\n✅ Prueba completada!")

if __name__ == "__main__":
    test_sistema_cheques()