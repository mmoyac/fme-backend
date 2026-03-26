"""
Script para agregar el menú de Notas de Crédito en producción.
Ejecutar: python scripts/add_menu_notas_credito.py
"""
import requests

BASE_URL = "https://api.masasestacion.cl"

def add_menu_notas_credito():
    session = requests.Session()

    # 1. Login como admin
    print("Logueando como admin...")
    resp = session.post(f"{BASE_URL}/api/auth/token", data={
        "username": "admin@fme.cl",
        "password": "admin"
    })
    if resp.status_code != 200:
        print(f"Error login: {resp.text}")
        return

    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("Login exitoso\n")

    # 2. Obtener roles y menu items
    roles = session.get(f"{BASE_URL}/api/admin/roles", headers=headers).json()
    menu_items = session.get(f"{BASE_URL}/api/admin/menu_items", headers=headers).json()
    print(f"Menu items actuales: {len(menu_items)}")

    # 3. Verificar si ya existe
    existing = next((m for m in menu_items if m["href"] == "/admin/notas-credito"), None)
    if existing:
        print(f"El menu 'Notas de Crédito' ya existe (ID: {existing['id']})")
        nota_id = existing["id"]
    else:
        # Determinar orden: después de Facturas
        facturas = next((m for m in menu_items if m["href"] == "/admin/facturas"), None)
        orden = (facturas["orden"] + 1) if facturas else 99

        print("Creando menu 'Notas de Crédito'...")
        resp = session.post(f"{BASE_URL}/api/admin/menu_items", headers=headers, json={
            "nombre": "Notas de Crédito",
            "href": "/admin/notas-credito",
            "icon": "🧾",
            "orden": orden,
        })
        if resp.status_code not in [200, 201]:
            print(f"Error creando menu: {resp.text}")
            return
        nota_id = resp.json()["id"]
        print(f"Menu 'Notas de Crédito' creado (ID: {nota_id})")

    # 4. Asignar a los mismos roles que tienen Facturas
    roles_objetivo = ["admin", "administrador", "tesorero"]
    print(f"\nAsignando a roles: {roles_objetivo}")

    for role_name in roles_objetivo:
        role = next((r for r in roles if r["nombre"] == role_name), None)
        if not role:
            print(f"Rol '{role_name}' no encontrado, saltando...")
            continue

        resp = session.get(f"{BASE_URL}/api/admin/roles/{role['id']}/menu", headers=headers)
        menu_ids = [m["id"] for m in resp.json()]

        if nota_id not in menu_ids:
            menu_ids.append(nota_id)
            resp = session.put(f"{BASE_URL}/api/admin/roles/{role['id']}/menu", headers=headers, json=menu_ids)
            if resp.status_code in [200, 204]:
                print(f"Asignado al rol '{role_name}'")
            else:
                print(f"Error asignando a '{role_name}': {resp.text}")
        else:
            print(f"Rol '{role_name}' ya tiene acceso")

    print("\nListo. Los usuarios deben recargar la página para ver el nuevo menú.")

if __name__ == "__main__":
    add_menu_notas_credito()
