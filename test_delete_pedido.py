"""
Script de prueba para el endpoint DELETE /api/pedidos/{id}
"""
import requests

API_URL = "http://localhost:8000"

# 1. Autenticar
print("🔐 Autenticando...")
resp = requests.post(f"{API_URL}/api/auth/token", data={
    "username": "admin@fme.cl",
    "password": "admin"
})
token = resp.json()["access_token"]
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}
print("✅ Autenticado")

# 2. Listar pedidos
print("\n📋 Listando pedidos...")
resp = requests.get(f"{API_URL}/api/pedidos/", headers=headers)
pedidos = resp.json()
print(f"Total pedidos: {len(pedidos)}")

if len(pedidos) == 0:
    print("⚠️  No hay pedidos para probar")
    exit(0)

# Mostrar primeros 5 pedidos
print("\nPrimeros 5 pedidos:")
for p in pedidos[:5]:
    print(f"  ID: {p['id']} | #{p['numero_pedido']} | ${p['monto_total']:.0f} | Estado: {p['estado']}")

# 3. Probar DELETE con el último pedido
pedido_test = pedidos[-1]
pedido_id = pedido_test['id']
numero = pedido_test['numero_pedido']

print(f"\n🗑️  Probando DELETE con pedido ID {pedido_id} (#{numero})...")
confirmacion = input(f"¿Confirmas eliminar pedido #{numero}? (SI/NO): ").strip().upper()

if confirmacion != 'SI':
    print("❌ Prueba cancelada")
    exit(0)

# Intentar eliminar
resp = requests.delete(f"{API_URL}/api/pedidos/{pedido_id}", headers=headers)

if resp.status_code == 204:
    print(f"✅ Pedido #{numero} eliminado exitosamente (204 No Content)")
elif resp.status_code == 404:
    print(f"⚠️  Pedido no encontrado (404)")
elif resp.status_code == 405:
    print(f"❌ Método no permitido (405) - El endpoint aún no está disponible")
else:
    print(f"❌ Error {resp.status_code}: {resp.text}")

# 4. Verificar que fue eliminado
print("\n🔍 Verificando eliminación...")
resp = requests.get(f"{API_URL}/api/pedidos/{pedido_id}", headers=headers)
if resp.status_code == 404:
    print("✅ Confirmado: Pedido ya no existe")
else:
    print(f"⚠️  Pedido aún existe (status {resp.status_code})")

# 5. Contar pedidos nuevamente
resp = requests.get(f"{API_URL}/api/pedidos/", headers=headers)
pedidos_despues = resp.json()
print(f"\n📊 Total pedidos después: {len(pedidos_despues)} (antes: {len(pedidos)})")
