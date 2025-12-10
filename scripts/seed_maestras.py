"""
Script para poblar las tablas maestras con datos iniciales completos.
Ejecutar: python scripts/seed_maestras.py
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def setup_maestras():
    session = requests.Session()

    # 1. Login
    print(f"🔐 Logueando como admin...")
    login_data = {
        "username": "admin@fme.cl",
        "password": "admin"
    }
    resp = session.post(f"{BASE_URL}/api/auth/token", data=login_data)
    if resp.status_code != 200:
        print(f"❌ Error login: {resp.text}")
        return
    
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Login exitoso\n")

    # ============================================
    # 2. CATEGORÍAS DE PRODUCTO
    # ============================================
    print("📦 Creando Categorías de Producto...")
    categorias = [
        {"codigo": "PANADERIA", "nombre": "Panadería", "descripcion": "Productos de panadería", "puntos_fidelidad": 10},
        {"codigo": "PASTELERIA", "nombre": "Pastelería", "descripcion": "Productos de pastelería", "puntos_fidelidad": 15},
        {"codigo": "EMPANADAS", "nombre": "Empanadas", "descripcion": "Empanadas y productos salados", "puntos_fidelidad": 12},
        {"codigo": "LACTEOS", "nombre": "Lácteos", "descripcion": "Quesos, mantequilla, etc", "puntos_fidelidad": 8},
        {"codigo": "ABARROTES", "nombre": "Abarrotes", "descripcion": "Productos de abarrotes", "puntos_fidelidad": 5},
    ]

    for cat in categorias:
        resp = session.post(f"{BASE_URL}/api/maestras/categorias", json=cat, headers=headers)
        if resp.status_code == 201:
            print(f"  ✅ Categoría creada: {cat['nombre']}")
        elif resp.status_code == 400 and "existe" in resp.text:
            print(f"  ℹ️  Categoría ya existe: {cat['nombre']}")
        else:
            print(f"  ❌ Error creando categoría {cat['nombre']}: {resp.text}")

    # ============================================
    # 3. TIPOS DE PRODUCTO (ya existen, agregar más si es necesario)
    # ============================================
    print("\n🏷️  Creando Tipos de Producto...")
    tipos = [
        {"codigo": "INSUMO", "nombre": "Insumo", "descripcion": "Materiales no vendibles (envases, etc)"},
        {"codigo": "SERVICIO", "nombre": "Servicio", "descripcion": "Servicios ofrecidos"},
    ]

    for tipo in tipos:
        resp = session.post(f"{BASE_URL}/api/maestras/tipos", json=tipo, headers=headers)
        if resp.status_code == 201:
            print(f"  ✅ Tipo creado: {tipo['nombre']}")
        elif resp.status_code == 400 and "existe" in resp.text:
            print(f"  ℹ️  Tipo ya existe: {tipo['nombre']}")
        else:
            print(f"  ❌ Error creando tipo {tipo['nombre']}: {resp.text}")

    # ============================================
    # 4. UNIDADES DE MEDIDA (agregar más)
    # ============================================
    print("\n📏 Creando Unidades de Medida...")
    unidades = [
        {"codigo": "DOCENA", "nombre": "Docena", "simbolo": "doc", "tipo": "CANTIDAD", "factor_conversion": 12, "unidad_base_id": 1},
        {"codigo": "MEDIA_DOCENA", "nombre": "Media Docena", "simbolo": "1/2 doc", "tipo": "CANTIDAD", "factor_conversion": 6, "unidad_base_id": 1},
        {"codigo": "CAJA", "nombre": "Caja", "simbolo": "caja", "tipo": "CANTIDAD", "factor_conversion": 1, "unidad_base_id": None},
        {"codigo": "PAQUETE", "nombre": "Paquete", "simbolo": "paq", "tipo": "CANTIDAD", "factor_conversion": 1, "unidad_base_id": None},
    ]

    for unidad in unidades:
        resp = session.post(f"{BASE_URL}/api/maestras/unidades", json=unidad, headers=headers)
        if resp.status_code == 201:
            print(f"  ✅ Unidad creada: {unidad['nombre']}")
        elif resp.status_code == 400 and "existe" in resp.text:
            print(f"  ℹ️  Unidad ya existe: {unidad['nombre']}")
        else:
            print(f"  ❌ Error creando unidad {unidad['nombre']}: {resp.text}")

    # ============================================
    # 5. RESUMEN
    # ============================================
    print("\n" + "="*50)
    print("📊 RESUMEN DE DATOS MAESTROS")
    print("="*50)

    # Listar categorías
    resp = session.get(f"{BASE_URL}/api/maestras/categorias", headers=headers)
    if resp.status_code == 200:
        categorias = resp.json()
        print(f"\n📦 Categorías ({len(categorias)}):")
        for cat in categorias:
            print(f"  - {cat['codigo']}: {cat['nombre']} (Puntos: {cat['puntos_fidelidad']})")

    # Listar tipos
    resp = session.get(f"{BASE_URL}/api/maestras/tipos", headers=headers)
    if resp.status_code == 200:
        tipos = resp.json()
        print(f"\n🏷️  Tipos de Producto ({len(tipos)}):")
        for tipo in tipos:
            print(f"  - {tipo['codigo']}: {tipo['nombre']}")

    # Listar unidades
    resp = session.get(f"{BASE_URL}/api/maestras/unidades", headers=headers)
    if resp.status_code == 200:
        unidades = resp.json()
        print(f"\n📏 Unidades de Medida ({len(unidades)}):")
        for unidad in unidades:
            base_info = f" (base: {unidad['unidad_base']['nombre']})" if unidad.get('unidad_base') else ""
            print(f"  - {unidad['codigo']}: {unidad['nombre']} ({unidad['simbolo']}){base_info}")

    print("\n✅ Proceso completado!")

if __name__ == "__main__":
    setup_maestras()
