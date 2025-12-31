#!/usr/bin/env python3
"""
Script para probar el endpoint de boletas del backoffice con la nueva información de puntos
"""

import sys
sys.path.append('.')
import requests

def probar_endpoint_boleta():
    try:
        print("🧪 PROBANDO ENDPOINT DE BOLETA PED-00027")
        print("=" * 50)
        
        # URL del endpoint de boletas
        url = "http://localhost:8000/api/pedidos/27/boleta"
        
        print(f"📡 Solicitando boleta desde: {url}")
        
        # Headers básicos
        headers = {
            "Accept": "application/pdf",
            "Content-Type": "application/json"
        }
        
        # Hacer petición
        response = requests.get(url, headers=headers)
        
        print(f"📊 Respuesta del servidor:")
        print(f"   Status code: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('Content-Type', 'No definido')}")
        print(f"   Content-Length: {len(response.content)} bytes")
        
        if response.status_code == 200:
            # Guardar la boleta recibida
            filename = "static/boletas/PED-00027-endpoint-test.pdf"
            import os
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            with open(filename, 'wb') as f:
                f.write(response.content)
            
            print(f"✅ Boleta guardada desde endpoint: {filename}")
            print(f"📄 Tamaño: {len(response.content)} bytes")
            
            print(f"\n📋 INFORMACIÓN ESPERADA EN LA BOLETA:")
            print(f"   • Subtotal: $6,000")
            print(f"   • Descuento puntos (5 pts): -$5")
            print(f"   • TOTAL: $5,995")
            print(f"   • Puntos ganados ✓: +8 pts")
            print(f"   • Puntos disponibles: 11 pts ← NUEVA INFORMACIÓN")
            
        else:
            print(f"❌ Error en la petición:")
            print(f"   Status: {response.status_code}")
            print(f"   Mensaje: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    probar_endpoint_boleta()