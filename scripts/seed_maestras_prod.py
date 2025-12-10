"""
Script para poblar las tablas maestras en PRODUCCIÓN.
Ejecutar: python scripts/seed_maestras_prod.py
"""
import requests
import json
import sys

# URL de producción
BASE_URL = "https://api.masasestacion.cl"

def setup_maestras_prod():
    session = requests.Session()

    print(f"🌍 Conectando a {BASE_URL}...")

    # 1. Login
    print(f"🔐 Logueando como admin...")
    login_data = {
        "username": "admin@fme.cl",
        "password": "admin"
    }
    
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
    # 2. TIPOS DE PRODUCTO
    # ============================================
    print("\n🏷️  Creando Tipos de Producto...")
    tipos = [
        {"codigo": "MP", "nombre": "Materia Prima", "descripcion": "Harina, levadura, etc."},
        {"codigo": "PT", "nombre": "Producto Terminado", "descripcion": "Pan, empanadas para venta"},
        {"codigo": "SP", "nombre": "Semi-elaborado", "descripcion": "Masas, rellenos"},
        {"codigo": "INSUMO", "nombre": "Insumo", "descripcion": "Envases, cajas"},
        {"codigo": "SERVICIO", "nombre": "Servicio", "descripcion": "Despacho, etc"},
    ]

    for tipo in tipos:
        resp = session.post(f"{BASE_URL}/api/maestras/tipos", json=tipo, headers=headers)
        if resp.status_code in [200, 201]:
            print(f"  ✅ Tipo revisado: {tipo['nombre']}")
        elif resp.status_code == 400:
            print(f"  ℹ️  Tipo ya existe: {tipo['nombre']}")
        else:
            print(f"  ❌ Error: {resp.status_code} - {resp.text}")

    # ============================================
    # 3. UNIDADES DE MEDIDA
    # ============================================
    print("\n📏 Creando Unidades de Medida...")
    # Primero las base
    unidades_base = [
        {"codigo": "UN", "nombre": "Unidad", "simbolo": "un", "tipo": "CANTIDAD", "factor_conversion": 1, "unidad_base_id": None},
        {"codigo": "KG", "nombre": "Kilogramo", "simbolo": "kg", "tipo": "PESO", "factor_conversion": 1, "unidad_base_id": None},
        {"codigo": "LT", "nombre": "Litro", "simbolo": "lt", "tipo": "VOLUMEN", "factor_conversion": 1, "unidad_base_id": None},
    ]
    
    mapa_unidades = {} # Para guardar IDs

    for unidad in unidades_base:
        resp = session.post(f"{BASE_URL}/api/maestras/unidades", json=unidad, headers=headers)
        if resp.status_code in [200, 201]:
            data = resp.json()
            mapa_unidades[unidad['codigo']] = data['id']
            print(f"  ✅ Unidad base creada: {unidad['nombre']}")
        elif resp.status_code == 400:
            # Intentar buscar el ID si ya existe
            print(f"  ℹ️  Unidad base ya existe: {unidad['nombre']}")
            # Aquí deberíamos buscar el ID, pero simplificaremos asumiendo IDs estándar 1, 2, 3 si es base limpia
            # O mejor, hacemos un GET para buscarlo
            all_units = session.get(f"{BASE_URL}/api/maestras/unidades", headers=headers).json()
            for u in all_units:
                if u['codigo'] == unidad['codigo']:
                    mapa_unidades[unidad['codigo']] = u['id']
        else:
            print(f"  ❌ Error: {resp.text}")

    # Unidades derivadas
    if 'KG' in mapa_unidades and 'LT' in mapa_unidades and 'UN' in mapa_unidades:
        unidades_derivadas = [
            {"codigo": "GR", "nombre": "Gramo", "simbolo": "gr", "tipo": "PESO", "factor_conversion": 0.001, "unidad_base_id": mapa_unidades['KG']},
            {"codigo": "CC", "nombre": "Centímetro Cúbico", "simbolo": "cc", "tipo": "VOLUMEN", "factor_conversion": 0.001, "unidad_base_id": mapa_unidades['LT']},
            {"codigo": "DOC", "nombre": "Docena", "simbolo": "doc", "tipo": "CANTIDAD", "factor_conversion": 12, "unidad_base_id": mapa_unidades['UN']},
        ]

        for unidad in unidades_derivadas:
            resp = session.post(f"{BASE_URL}/api/maestras/unidades", json=unidad, headers=headers)
            if resp.status_code in [200, 201]:
                print(f"  ✅ Unidad derivada creada: {unidad['nombre']}")
            elif resp.status_code == 400:
                print(f"  ℹ️  Unidad derivada ya existe: {unidad['nombre']}")
            else:
                print(f"  ❌ Error: {resp.text}")
    else:
        print("⚠️ No se pudieron crear unidades derivadas por falta de unidades base")

    # ============================================
    # 4. CATEGORÍAS
    # ============================================
    print("\n📦 Creando Categorías...")
    categorias = [
        {"codigo": "PAN", "nombre": "Panadería", "descripcion": "Panes varios", "puntos_fidelidad": 10},
        {"codigo": "EMP", "nombre": "Empanadas", "descripcion": "Empanadas horno y fritas", "puntos_fidelidad": 15},
        {"codigo": "PAS", "nombre": "Pastelería", "descripcion": "Tortas y pasteles", "puntos_fidelidad": 20},
        {"codigo": "BEB", "nombre": "Bebidas", "descripcion": "Bebidas y jugos", "puntos_fidelidad": 5},
    ]

    for cat in categorias:
        resp = session.post(f"{BASE_URL}/api/maestras/categorias", json=cat, headers=headers)
        if resp.status_code in [200, 201]:
            print(f"  ✅ Categoría creada: {cat['nombre']}")
        elif resp.status_code == 400:
            print(f"  ℹ️  Categoría ya existe: {cat['nombre']}")
        else:
            print(f"  ❌ Error: {resp.text}")

    print("\n✅ Proceso completado!")

if __name__ == "__main__":
    setup_maestras_prod()
