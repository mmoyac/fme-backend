#!/usr/bin/env python3
"""
Script para crear un pedido con múltiples cheques de prueba.
"""
import requests
import json
from datetime import datetime

# Configuración
BASE_URL = "http://localhost:8000"

def login_admin():
    """Login como administrador."""
    print("🔐 Logueando como admin...")
    
    session = requests.Session()
    
    # Datos de login
    login_data = {
        "username": "admin@fme.cl",
        "password": "admin"
    }
    
    resp = session.post(f"{BASE_URL}/api/auth/token", data=login_data)
    if resp.status_code != 200:
        print(f"❌ Error en login: {resp.status_code}")
        return None, None
        
    token_data = resp.json()
    token = token_data.get("access_token")
    
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Login exitoso")
    
    return session, headers

def obtener_datos_base(session, headers):
    """Obtener cliente, productos, local y medio de pago."""
    print("\n📋 Obteniendo datos base...")
    
    # Obtener primer cliente
    resp = session.get(f"{BASE_URL}/api/clientes/", headers=headers)
    clientes = resp.json()
    if not clientes:
        print("❌ No hay clientes disponibles")
        return None
    cliente = clientes[0]
    print(f"✅ Cliente: {cliente['nombre']} ({cliente['email']})")
    
    # Obtener productos
    resp = session.get(f"{BASE_URL}/api/productos/", headers=headers)
    productos = resp.json()
    if not productos:
        print("❌ No hay productos disponibles")
        return None
    producto = productos[0]
    print(f"✅ Producto: {producto['nombre']} (SKU: {producto['sku']})")
    
    # Obtener local WEB
    resp = session.get(f"{BASE_URL}/api/locales/", headers=headers)
    locales = resp.json()
    local_web = next((l for l in locales if l['codigo'] == 'WEB'), None)
    if not local_web:
        print("❌ Local WEB no encontrado")
        return None
    print(f"✅ Local: {local_web['nombre']}")
    
    # Obtener medio de pago CHEQUE
    resp = session.get(f"{BASE_URL}/api/maestras/medios-pago", headers=headers)
    medios = resp.json()
    medio_cheque = next((m for m in medios if m['codigo'] == 'CHEQUE'), None)
    if not medio_cheque:
        print("❌ Medio de pago CHEQUE no encontrado")
        return None
    print(f"✅ Medio de pago: {medio_cheque['nombre']}")
    
    # Obtener primer banco
    resp = session.get(f"{BASE_URL}/api/maestras/bancos", headers=headers)
    bancos = resp.json()
    if not bancos:
        print("❌ No hay bancos disponibles")
        return None
    banco = bancos[1] if len(bancos) > 1 else bancos[0]  # Usar segundo banco si existe
    print(f"✅ Banco: {banco['nombre']} ({banco['codigo']})")
    
    # Obtener estado PENDIENTE
    resp = session.get(f"{BASE_URL}/api/maestras/estados-cheque", headers=headers)
    estados = resp.json()
    estado_pendiente = next((e for e in estados if e['codigo'] == 'PENDIENTE'), None)
    if not estado_pendiente:
        print("❌ Estado PENDIENTE no encontrado")
        return None
    print(f"✅ Estado cheque: {estado_pendiente['nombre']}")
    
    return {
        'cliente': cliente,
        'producto': producto,
        'local': local_web,
        'medio_pago': medio_cheque,
        'banco': banco,
        'estado_cheque': estado_pendiente
    }

def crear_pedido_con_cheques():
    """Crear un pedido con 3 cheques."""
    session, headers = login_admin()
    if not session:
        return
    
    datos = obtener_datos_base(session, headers)
    if not datos:
        return
    
    print("\n💰 Creando pedido...")
    
    # Crear pedido
    pedido_data = {
        "cliente_id": datos['cliente']['id'],
        "cliente_nombre": datos['cliente']['nombre'],
        "cliente_email": datos['cliente']['email'],
        "cliente_telefono": datos['cliente']['telefono'],
        "direccion_entrega": datos['cliente']['direccion'],
        "local_id": datos['local']['id'],
        "medio_pago_id": datos['medio_pago']['id'],
        "notas": "Pedido de prueba con 3 cheques",
        "items": [
            {
                "sku": datos['producto']['sku'],
                "producto_id": datos['producto']['id'],
                "cantidad": 5,
                "precio_unitario_venta": 3500.0
            }
        ]
    }
    
    resp = session.post(f"{BASE_URL}/api/pedidos/", json=pedido_data, headers=headers)
    if resp.status_code != 201:
        print(f"❌ Error creando pedido: {resp.status_code} - {resp.text}")
        return
    
    pedido = resp.json()
    
    # Verificar que tenga pedido_id
    if 'pedido_id' not in pedido:
        print(f"❌ Error: La respuesta del pedido no contiene pedido_id")
        return
    
    pedido_id = pedido['pedido_id']
    total = pedido['monto_total']
    print(f"✅ Pedido creado: #{pedido_id} ({pedido['numero_pedido']}) - Total: ${total}")
    
    # Crear los 3 cheques
    print(f"\n📄 Creando 3 cheques...")
    
    # Dividir el total en 3 cheques
    monto_por_cheque = round(total / 3, 2)
    ultimo_cheque = total - (monto_por_cheque * 2)  # Ajuste para el total exacto
    
    cheques_data = [
        {
            "numero_cheque": "0002345671",
            "banco_id": datos['banco']['id'],
            "monto": monto_por_cheque,
            "fecha_emision": "2025-12-31T10:00:00",
            "fecha_vencimiento": "2025-12-31T23:59:59",
            "librador_nombre": "Juan Pérez García",
            "librador_rut": "12.345.678-9",
            "observaciones": "Cheque 1/3 - Vencimiento diciembre"
        },
        {
            "numero_cheque": "0002345672", 
            "banco_id": datos['banco']['id'],
            "monto": monto_por_cheque,
            "fecha_emision": "2025-12-31T10:00:00",
            "fecha_vencimiento": "2026-01-31T23:59:59",
            "librador_nombre": "Juan Pérez García",
            "librador_rut": "12.345.678-9",
            "observaciones": "Cheque 2/3 - Vencimiento enero"
        },
        {
            "numero_cheque": "0002345673",
            "banco_id": datos['banco']['id'], 
            "monto": ultimo_cheque,
            "fecha_emision": "2025-12-31T10:00:00",
            "fecha_vencimiento": "2026-02-28T23:59:59",
            "librador_nombre": "Juan Pérez García",
            "librador_rut": "12.345.678-9",
            "observaciones": "Cheque 3/3 - Vencimiento febrero"
        }
    ]
    
    cheques_creados = []
    for i, cheque_data in enumerate(cheques_data, 1):
        cheque_data["pedido_id"] = pedido_id
        cheque_data["estado_id"] = datos['estado_cheque']['id']
        
        resp = session.post(f"{BASE_URL}/api/cheques/", json=cheque_data, headers=headers)
        if resp.status_code not in [200, 201]:
            print(f"❌ Error creando cheque {i}: {resp.status_code} - {resp.text}")
            continue
            
        cheque = resp.json()
        cheques_creados.append(cheque)
        vencimiento = cheque['fecha_vencimiento'][:10]
        print(f"✅ Cheque {i}: #{cheque['numero_cheque']} - ${cheque['monto']} - Vence: {vencimiento}")
    
    print(f"\n🎉 Pedido creado exitosamente!")
    print(f"📊 Resumen:")
    print(f"   • Pedido ID: {pedido_id}")
    print(f"   • Cliente: {datos['cliente']['nombre']}")
    print(f"   • Total: ${total}")
    print(f"   • Medio de pago: {datos['medio_pago']['nombre']}")
    print(f"   • Banco: {datos['banco']['nombre']}")
    print(f"   • Cheques creados: {len(cheques_creados)}")
    
    # Verificar que el pedido no se marque como pagado (debe ser False porque los cheques están PENDIENTES)
    resp = session.get(f"{BASE_URL}/api/pedidos/{pedido_id}", headers=headers)
    if resp.status_code == 200:
        pedido_actualizado = resp.json()
        estado_pago = "PAGADO" if pedido_actualizado.get('es_pagado') else "PENDIENTE"
        print(f"   • Estado de pago: {estado_pago} ✅")

if __name__ == "__main__":
    crear_pedido_con_cheques()