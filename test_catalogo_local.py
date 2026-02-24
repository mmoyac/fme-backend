"""
Test del endpoint optimizado /api/productos/catalogo-local/{local_id}
"""
import requests
import json
from time import time

API_URL = "https://api.masasestacion.cl"

# Obtener token
print("🔐 Autenticando...")
resp_auth = requests.post(
    f"{API_URL}/api/auth/token",
    data={"username": "admin@fme.cl", "password": "admin"}
)

if resp_auth.status_code != 200:
    print(f"❌ Error autenticando: {resp_auth.status_code}")
    exit(1)

token = resp_auth.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

print(f"✅ Token obtenido\n")

# Probar endpoint optimizado
print("🚀 Probando endpoint optimizado /api/productos/catalogo-local/1...")
start = time()
resp = requests.get(
    f"{API_URL}/api/productos/catalogo-local/1",
    headers=headers
)
end = time()

tiempo_ms = (end - start) * 1000

print(f"⏱️  Tiempo de respuesta: {tiempo_ms:.0f}ms")
print(f"📊 Status: {resp.status_code}")

if resp.status_code == 200:
    data = resp.json()
    print(f"📦 Total productos: {len(data)}")
    
    if len(data) > 0:
        primer = data[0]
        print(f"\n✅ Ejemplo de producto returnado:")
        print(f"   ID: {primer.get('id')}")
        print(f"   SKU: {primer.get('sku')}")
        print(f"   Nombre: {primer.get('nombre')}")
        print(f"   Precio Local: ${primer.get('precio_local', 0):,.0f}")
        print(f"   Stock Local: {primer.get('stock_local', 0)}")
        print(f"   Categoría: {primer.get('categoria_nombre', 'N/A')}")
        print(f"   Puntos: {primer.get('categoria_puntos_fidelidad', 0)}")
        
        # Verificar estructura de precios
        if 'precios' in primer and len(primer['precios']) > 0:
            print(f"   Precios disponibles: {len(primer['precios'])}")
            for precio in primer['precios'][:2]:  # Mostrar primeros 2
                print(f"     - {precio['unidad_medida_nombre']}: ${precio['monto_precio']:,.0f}")
    
    # Comparación
    print(f"\n📈 Comparación:")
    print(f"   Antes: 325 requests (~30,000ms)")
    print(f"   Ahora: 1 request ({tiempo_ms:.0f}ms)")
    print(f"   Mejora: {(30000/tiempo_ms):.1f}x MÁS RÁPIDO")
else:
    print(f"❌ Error: {resp.status_code}")
    print(resp.text[:500])
