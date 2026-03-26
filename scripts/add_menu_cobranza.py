"""
Script para agregar el menú de Cobranza en producción.
Ejecutar: python scripts/add_menu_cobranza.py
"""
import requests

BASE_URL = "https://api.masasestacion.cl"

def add_menu_cobranza():
    session = requests.Session()

    # 1. Login como admin
    print("Logueando como admin...")
    login_data = {
        "username": "admin@fme.cl",
        "password": "admin"
    }
    resp = session.post(f"{BASE_URL}/api/auth/token", data=login_data)
    if resp.status_code != 200:
        print(f"Error login: {resp.text}")
        return

    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("Login exitoso\n")

    # 2. Obtener roles
    print("Obteniendo roles...")
    resp = session.get(f"{BASE_URL}/api/admin/roles", headers=headers)
    if resp.status_code != 200:
        print(f"Error obteniendo roles: {resp.text}")
        return
    roles = resp.json()

    # 3. Obtener menu items actuales
    resp = session.get(f"{BASE_URL}/api/admin/menu_items", headers=headers)
    if resp.status_code != 200:
        print(f"Error obteniendo menu items: {resp.text}")
        return
    menu_items_actuales = resp.json()
    print(f"Menu items actuales: {len(menu_items_actuales)}")

    # 4. Verificar si ya existe
    cobranza_item = next((m for m in menu_items_actuales if m["nombre"] == "Cobranza"), None)

    if cobranza_item:
        print(f"El menu 'Cobranza' ya existe (ID: {cobranza_item['id']})")
        cobranza_id = cobranza_item['id']
    else:
        print("Creando menu 'Cobranza'...")
        nuevo_menu = {
            "nombre": "Cobranza",
            "href": "/admin/cobranza",
            "icon": "🏦",
            "orden": 10
        }
        resp = session.post(f"{BASE_URL}/api/admin/menu_items", json=nuevo_menu, headers=headers)
        if resp.status_code in [200, 201]:
            cobranza_item = resp.json()
            cobranza_id = cobranza_item['id']
            print(f"Menu 'Cobranza' creado (ID: {cobranza_id})")
        else:
            print(f"Error creando menu: {resp.text}")
            return

    # 5. Asignar a roles: admin, administrador, tesorero
    roles_con_cobranza = ["admin", "administrador", "tesorero"]
    print(f"\nAsignando menu 'Cobranza' a roles: {roles_con_cobranza}")

    for role_name in roles_con_cobranza:
        role = next((r for r in roles if r["nombre"] == role_name), None)
        if not role:
            print(f"Rol '{role_name}' no encontrado, saltando...")
            continue

        resp = session.get(f"{BASE_URL}/api/admin/roles/{role['id']}/menu", headers=headers)
        if resp.status_code != 200:
            print(f"Error obteniendo menu del rol {role_name}: {resp.text}")
            continue

        menu_ids_role = [m["id"] for m in resp.json()]

        if cobranza_id not in menu_ids_role:
            menu_ids_role.append(cobranza_id)
            resp = session.put(
                f"{BASE_URL}/api/admin/roles/{role['id']}/menu",
                json=menu_ids_role,
                headers=headers
            )
            if resp.status_code in [200, 204]:
                print(f"Cobranza asignada al rol '{role_name}'")
            else:
                print(f"Error asignando a '{role_name}': {resp.text}")
        else:
            print(f"Rol '{role_name}' ya tiene acceso a Cobranza")

    print("\nListo. Los usuarios deben recargar la pagina para ver el nuevo menu.")

if __name__ == "__main__":
    add_menu_cobranza()
