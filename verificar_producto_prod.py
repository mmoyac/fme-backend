"""
Verificar que el producto 999999 existe en producción.
"""
import requests

API_URL = "https://api.masasestacion.cl"

# Autenticar
print("🔐 Autenticando...")
resp = requests.post(f"{API_URL}/api/auth/token", data={
    "username": "admin@fme.cl",
    "password": "admin"
})
token = resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Buscar producto
print("🔍 Buscando producto SKU 999999...")
resp = requests.get(f"{API_URL}/api/productos/", headers=headers)
productos = resp.json()

producto = next((p for p in productos if p.get('sku') == '999999'), None)

if producto:
    print("\n✅ PRODUCTO ENCONTRADO EN PRODUCCIÓN:")
    print("=" * 80)
    print(f"  ID: {producto.get('id')}")
    print(f"  SKU: {producto.get('sku')}")
    print(f"  Nombre: {producto.get('nombre')}")
    print(f"  Descripción: {producto.get('descripcion')}")
    print(f"  Categoría ID: {producto.get('categoria_id')}")
    print(f"  Tipo Producto ID: {producto.get('tipo_producto_id')}")
    print(f"  Unidad Medida ID: {producto.get('unidad_medida_id')}")
    print(f"  Tenant ID: {producto.get('tenant_id')}")
    print(f"  Es Vendible: {producto.get('es_vendible')}")
    print(f"  Es Vendible Web: {producto.get('es_vendible_web')}")
    print(f"  Activo: {producto.get('activo')}")
    print("=" * 80)
    print("\n🎉 CONFIRMADO: El producto importado desde Google Sheet está en producción!")
else:
    print("\n❌ Producto no encontrado")
