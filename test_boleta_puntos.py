#!/usr/bin/env python3
"""
Script para probar la generación de boleta con información de puntos.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests

def test_boleta_con_puntos():
    print("=== 🧾 TEST: Boleta con información de puntos ===")
    
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
            print(response.text)
            return
        
        pedido = response.json()
        print(f"✅ Pedido obtenido:")
        print(f"   Número: {pedido['numero_pedido']}")
        print(f"   Estado: {pedido['estado']}")
        print(f"   Total: ${pedido['total']}")
        print(f"   Puntos ganados: {pedido.get('puntos_ganados', 'NO INCLUIDO')}")
        print(f"   Puntos usados: {pedido.get('puntos_usados', 'NO INCLUIDO')}")
        print(f"   Descuento puntos: ${pedido.get('descuento_puntos', 'NO INCLUIDO')}")
        
        # Probar generar boleta
        boleta_response = requests.get("http://localhost:8000/api/pedidos/26/boleta", headers=headers)
        
        if boleta_response.status_code == 200:
            print(f"\n✅ Boleta generada exitosamente")
            print(f"   Content-Type: {boleta_response.headers.get('content-type', 'No especificado')}")
            print(f"   Tamaño: {len(boleta_response.content)} bytes")
            
            # Verificar si es PDF
            if boleta_response.content.startswith(b'%PDF'):
                print(f"   Formato: ✅ PDF válido")
                
                # Guardar boleta para verificar manualmente
                with open("test_boleta_pedido_26.pdf", "wb") as f:
                    f.write(boleta_response.content)
                print(f"   📄 Boleta guardada como 'test_boleta_pedido_26.pdf'")
                print(f"   💡 Abrir el archivo para verificar que incluye información de puntos")
                
            else:
                print(f"   ❌ No es un PDF válido")
        else:
            print(f"❌ Error al generar boleta: {boleta_response.status_code}")
            print(boleta_response.text)
        
    except Exception as e:
        print(f"❌ Error durante test: {e}")

if __name__ == "__main__":
    test_boleta_con_puntos()