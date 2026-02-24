import requests

# Autenticación
API_URL = "https://api.masasestacion.cl"
login_data = {"username": "admin@fme.cl", "password": "admin"}
resp = requests.post(f"{API_URL}/api/auth/token", data=login_data)
token = resp.json()['access_token']
headers = {"Authorization": f"Bearer {token}"}

# Obtener primer registro de inventario
resp_inv = requests.get(f"{API_URL}/api/inventario/", headers=headers)
inventarios = resp_inv.json()

if inventarios:
    primer_inv = inventarios[0]
    print("=" * 80)
    print("PRUEBA: ¿El inventario acepta valores negativos?")
    print("=" * 80)
    print(f"\nInventario original:")
    print(f"  ID: {primer_inv['id']}")
    print(f"  Producto ID: {primer_inv['producto_id']}")
    print(f"  Local ID: {primer_inv['local_id']}")
    print(f"  Stock actual: {primer_inv['cantidad_stock']}")
    
    # Intentar actualizar a valor negativo (-50)
    print(f"\n🧪 Intentando actualizar a cantidad_stock = -50...")
    
    resp_update = requests.put(
        f"{API_URL}/api/inventario/producto/{primer_inv['producto_id']}/local/{primer_inv['local_id']}",
        json={"cantidad_stock": -50},
        headers=headers
    )
    
    print(f"\nResultado:")
    print(f"  Status Code: {resp_update.status_code}")
    
    if resp_update.status_code == 200:
        inv_actualizado = resp_update.json()
        print(f"  ✅ ACEPTÓ valor negativo")
        print(f"  Nuevo stock: {inv_actualizado['cantidad_stock']}")
        
        # Restaurar valor original
        print(f"\n🔄 Restaurando valor original ({primer_inv['cantidad_stock']})...")
        requests.put(
            f"{API_URL}/api/inventario/producto/{primer_inv['producto_id']}/local/{primer_inv['local_id']}",
            json={"cantidad_stock": primer_inv['cantidad_stock']},
            headers=headers
        )
        print("  ✅ Valor restaurado")
    else:
        print(f"  ❌ RECHAZÓ valor negativo")
        print(f"  Error: {resp_update.json()}")
    
    print("=" * 80)
else:
    print("❌ No hay registros de inventario para probar")
