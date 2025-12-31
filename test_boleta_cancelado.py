#!/usr/bin/env python3
"""
Script para probar la boleta del pedido cancelado PED-00026.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests

def test_boleta_pedido_cancelado():
    print("=== 🧾 TEST: Boleta de pedido cancelado ===")
    
    try:
        # Hacer login para obtener token
        login_response = requests.post(
            "http://localhost:8000/api/auth/token",
            data={
                "username": "admin@fme.cl",
                "password": "admin"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if login_response.status_code != 200:
            print(f"❌ Error al hacer login: {login_response.status_code}")
            return
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Obtener información del pedido 26
        response = requests.get("http://localhost:8000/api/pedidos/26", headers=headers)
        
        if response.status_code != 200:
            print(f"❌ Error al obtener pedido: {response.status_code}")
            return
        
        pedido = response.json()
        print(f"✅ Información del pedido:")
        print(f"   Número: {pedido['numero_pedido']}")
        print(f"   Estado: {pedido['estado']}")
        print(f"   Total: ${pedido['total']}")
        print(f"   Puntos ganados: {pedido.get('puntos_ganados', 'NO INCLUIDO')}")
        
        # Generar boleta del pedido cancelado
        print(f"\n📄 Generando boleta...")
        boleta_response = requests.get("http://localhost:8000/api/pedidos/26/boleta", headers=headers)
        
        if boleta_response.status_code == 200:
            print(f"✅ Boleta generada exitosamente")
            
            # Guardar boleta cancelada
            with open("boleta_pedido_26_cancelado.pdf", "wb") as f:
                f.write(boleta_response.content)
            print(f"📄 Boleta guardada como 'boleta_pedido_26_cancelado.pdf'")
            print(f"💡 La boleta NO debería mostrar puntos ganados porque el pedido está CANCELADO")
            
        else:
            print(f"❌ Error al generar boleta: {boleta_response.status_code}")
        
    except Exception as e:
        print(f"❌ Error durante test: {e}")

if __name__ == "__main__":
    test_boleta_pedido_cancelado()