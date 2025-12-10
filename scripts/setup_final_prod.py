"""
Script FINAL para configurar Roles y Usuarios en PRODUCCIÓN.
Incluye: Dueño, Vendedor, Tesorero, Cliente.
Ejecutar: python scripts/setup_final_prod.py
"""
import requests
import json
import sys

# URL de producción
BASE_URL = "https://api.masasestacion.cl"

def setup_final_prod():
    session = requests.Session()

    print(f"🌍 Conectando a {BASE_URL}...")

    # 1. Login Admin
    print(f"🔐 Logueando como admin...")
    login_data = {"username": "admin@fme.cl", "password": "admin"}
    try:
        resp = session.post(f"{BASE_URL}/api/auth/token", data=login_data)
        if resp.status_code != 200:
            print(f"❌ Error login: {resp.status_code} - {resp.text}")
            return
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Login exitoso\n")

    # ============================================
    # 2. ASEGURAR ROLES (Incluyendo Owner y Cliente)
    # ============================================
    print("--- 🛠️  Configurando Roles ---")
    roles_def = [
        {"nombre": "owner", "descripcion": "Dueño de la Empresa (Acceso Total)"},
        {"nombre": "cliente", "descripcion": "Cliente B2B con acceso limitado"},
        {"nombre": "vendedor", "descripcion": "Vendedor de local"},
        {"nombre": "tesorero", "descripcion": "Encargado de finanzas"},
    ]

    for r in roles_def:
        resp = session.post(f"{BASE_URL}/api/admin/roles", json=r, headers=headers)
        if resp.status_code == 201:
            print(f"  ✅ Rol creado: {r['nombre']}")
        elif resp.status_code == 400:
            print(f"  ℹ️  Rol existe: {r['nombre']}")
        else:
            print(f"  ❌ Error rol {r['nombre']}: {resp.text}")

    # Obtener mapa de IDs de roles
    resp = session.get(f"{BASE_URL}/api/admin/roles", headers=headers)
    all_roles = resp.json()
    role_map = {r['nombre']: r['id'] for r in all_roles}

    # ============================================
    # 3. ASIGNAR PERMISOS (MENÚ)
    # ============================================
    print("\n--- 🔗 Asignando Permisos de Menú ---")
    # Obtener todos los items de menú
    resp = session.get(f"{BASE_URL}/api/admin/menu_items", headers=headers)
    all_menu_items = resp.json()
    menu_map = {m['nombre']: m['id'] for m in all_menu_items}

    # Definir permisos
    # Owner = Todo
    all_menu_ids = list(menu_map.values())
    
    # Cliente = Solo realizar pedidos y ver historial (Dashboard maybe?)
    # Asumimos que cliente puede ver Dashboard, Pedidos, Historial.
    cliente_menus = ["Dashboard", "Pedidos", "Historial"]
    cliente_menu_ids = [menu_map[m] for m in cliente_menus if m in menu_map]

    permissions_config = {
        "owner": all_menu_ids,
        "cliente": cliente_menu_ids
    }

    for role_name, menu_ids in permissions_config.items():
        if role_name in role_map:
            role_id = role_map[role_name]
            resp = session.put(
                f"{BASE_URL}/api/admin/roles/{role_id}/menu",
                json=menu_ids,
                headers=headers
            )
            if resp.status_code == 204:
                print(f"  ✅ Permisos asignados a '{role_name}'")
            else:
                print(f"  ❌ Error asignando a '{role_name}': {resp.text}")

    # ============================================
    # 4. CREAR USUARIOS
    # ============================================
    print("\n--- 👥 Creando Usuarios ---")
    users_def = [
        {
            "email": "dueno@fme.cl", 
            "password": "dueno123", 
            "nombre_completo": "Dueño Empresa", 
            "role_nombre": "owner"
        },
        {
            "email": "cliente@fme.cl", 
            "password": "cliente123", 
            "nombre_completo": "Cliente Frecuente", 
            "role_nombre": "cliente"
        },
        {
            "email": "vendedor@fme.cl", 
            "password": "vendedor123", 
            "nombre_completo": "Vendedor Local", 
            "role_nombre": "vendedor"
        },
        {
            "email": "tesorero@fme.cl", 
            "password": "tesorero123", 
            "nombre_completo": "Tesorero Finanzas", 
            "role_nombre": "tesorero"
        }
    ]

    for u in users_def:
        role_name = u.pop("role_nombre")
        if role_name in role_map:
            u["role_id"] = role_map[role_name]
            u["is_active"] = True
            
            resp = session.post(f"{BASE_URL}/api/admin/users", json=u, headers=headers)
            if resp.status_code == 201:
                print(f"  ✅ Usuario creado: {u['email']} ({role_name})")
            elif resp.status_code == 400 and "registrado" in resp.text:
                print(f"  ℹ️  Usuario existe: {u['email']}")
            else:
                print(f"  ❌ Error usuario {u['email']}: {resp.text}")
        else:
            print(f"  ⚠️ Rol '{role_name}' no encontrado para usuario {u['email']}")

    print("\n✅ Configuración Final Completada!")

if __name__ == "__main__":
    setup_final_prod()
