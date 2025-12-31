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
    # 5. MEDIOS DE PAGO
    # ============================================
    print("\n💳 Creando Medios de Pago...")
    medios_pago = [
        {
            "codigo": "EFECTIVO",
            "nombre": "Efectivo",
            "descripcion": "Pago en efectivo",
            "permite_cheque": False,
            "activo": True
        },
        {
            "codigo": "TARJETA_DEBITO",
            "nombre": "Tarjeta de Débito",
            "descripcion": "Pago con tarjeta de débito",
            "permite_cheque": False,
            "activo": True
        },
        {
            "codigo": "TARJETA_CREDITO",
            "nombre": "Tarjeta de Crédito",
            "descripcion": "Pago con tarjeta de crédito",
            "permite_cheque": False,
            "activo": True
        },
        {
            "codigo": "TRANSFERENCIA",
            "nombre": "Transferencia Bancaria",
            "descripcion": "Transferencia electrónica",
            "permite_cheque": False,
            "activo": True
        },
        {
            "codigo": "CHEQUE",
            "nombre": "Cheque",
            "descripcion": "Pago con cheque al día o a fecha",
            "permite_cheque": True,
            "activo": True
        },
        {
            "codigo": "MERCADOPAGO",
            "nombre": "MercadoPago",
            "descripcion": "Pago a través de MercadoPago",
            "permite_cheque": False,
            "activo": True
        }
    ]

    for medio in medios_pago:
        resp = session.post(f"{BASE_URL}/api/maestras/medios-pago", json=medio, headers=headers)
        if resp.status_code == 200:
            print(f"  ✅ Medio de pago creado: {medio['nombre']}")
        elif resp.status_code == 400 and "existe" in resp.text:
            print(f"  ℹ️  Medio de pago ya existe: {medio['nombre']}")
        else:
            print(f"  ❌ Error creando medio de pago {medio['nombre']}: {resp.text}")

    # ============================================
    # 6. ESTADOS DE CHEQUE
    # ============================================
    print("\n📋 Creando Estados de Cheque...")
    estados_cheque = [
        {
            "codigo": "PENDIENTE",
            "nombre": "Pendiente",
            "descripcion": "Cheque recibido, pendiente de cobro",
            "es_final": False,
            "activo": True
        },
        {
            "codigo": "DEPOSITADO",
            "nombre": "Depositado",
            "descripcion": "Cheque depositado en el banco",
            "es_final": False,
            "activo": True
        },
        {
            "codigo": "COBRADO",
            "nombre": "Cobrado",
            "descripcion": "Cheque cobrado exitosamente",
            "es_final": True,
            "activo": True
        },
        {
            "codigo": "RECHAZADO",
            "nombre": "Rechazado",
            "descripcion": "Cheque rechazado por fondos insuficientes",
            "es_final": True,
            "activo": True
        },
        {
            "codigo": "VENCIDO",
            "nombre": "Vencido",
            "descripcion": "Cheque vencido sin cobrar",
            "es_final": True,
            "activo": True
        },
        {
            "codigo": "ANULADO",
            "nombre": "Anulado",
            "descripcion": "Cheque anulado por el cliente",
            "es_final": True,
            "activo": False
        }
    ]

    for estado in estados_cheque:
        resp = session.post(f"{BASE_URL}/api/maestras/estados-cheque", json=estado, headers=headers)
        if resp.status_code == 200:
            print(f"  ✅ Estado de cheque creado: {estado['nombre']}")
        elif resp.status_code == 400 and "existe" in resp.text:
            print(f"  ℹ️  Estado de cheque ya existe: {estado['nombre']}")
        else:
            print(f"  ❌ Error creando estado de cheque {estado['nombre']}: {resp.text}")

    # ============================================
    # 7. BANCOS
    # ============================================
    print("\n🏦 Creando Bancos...")
    bancos = [
        {
            "codigo": "BANCO_CHILE",
            "nombre": "Banco de Chile",
            "nombre_corto": "Chile",
            "activo": True
        },
        {
            "codigo": "BANCO_ESTADO",
            "nombre": "BancoEstado",
            "nombre_corto": "Estado",
            "activo": True
        },
        {
            "codigo": "SANTANDER",
            "nombre": "Banco Santander Chile",
            "nombre_corto": "Santander",
            "activo": True
        },
        {
            "codigo": "BCI",
            "nombre": "Banco de Crédito e Inversiones",
            "nombre_corto": "BCI",
            "activo": True
        },
        {
            "codigo": "ITAU",
            "nombre": "Banco Itaú Chile",
            "nombre_corto": "Itaú",
            "activo": True
        },
        {
            "codigo": "SCOTIABANK",
            "nombre": "Scotiabank Chile",
            "nombre_corto": "Scotia",
            "activo": True
        },
        {
            "codigo": "FALABELLA",
            "nombre": "Banco Falabella",
            "nombre_corto": "Falabella",
            "activo": True
        },
        {
            "codigo": "RIPLEY",
            "nombre": "Banco Ripley",
            "nombre_corto": "Ripley",
            "activo": True
        },
        {
            "codigo": "SECURITY",
            "nombre": "Banco Security",
            "nombre_corto": "Security",
            "activo": True
        },
        {
            "codigo": "BICE",
            "nombre": "Banco BICE",
            "nombre_corto": "BICE",
            "activo": True
        }
    ]

    for banco in bancos:
        resp = session.post(f"{BASE_URL}/api/maestras/bancos", json=banco, headers=headers)
        if resp.status_code == 200:
            print(f"  ✅ Banco creado: {banco['nombre']}")
        elif resp.status_code == 400 and "existe" in resp.text:
            print(f"  ℹ️  Banco ya existe: {banco['nombre']}")
        else:
            print(f"  ❌ Error creando banco {banco['nombre']}: {resp.text}")

    # ============================================
    # 8. RESUMEN
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

    # Listar medios de pago
    resp = session.get(f"{BASE_URL}/api/maestras/medios-pago", headers=headers)
    if resp.status_code == 200:
        medios = resp.json()
        print(f"\n💳 Medios de Pago ({len(medios)}):")
        for medio in medios:
            cheque_info = " ✅ Permite cheque" if medio['permite_cheque'] else ""
            print(f"  - {medio['codigo']}: {medio['nombre']}{cheque_info}")

    # Listar estados de cheque
    resp = session.get(f"{BASE_URL}/api/maestras/estados-cheque", headers=headers)
    if resp.status_code == 200:
        estados = resp.json()
        print(f"\n📋 Estados de Cheque ({len(estados)}):")
        for estado in estados:
            final_info = " (Final)" if estado['es_final'] else ""
            activo_info = " ❌ Inactivo" if not estado['activo'] else ""
            print(f"  - {estado['codigo']}: {estado['nombre']}{final_info}{activo_info}")

    # Listar bancos
    resp = session.get(f"{BASE_URL}/api/maestras/bancos", headers=headers)
    if resp.status_code == 200:
        bancos = resp.json()
        print(f"\n🏦 Bancos ({len(bancos)}):")
        for banco in bancos:
            nombre_completo = f"{banco['nombre']}"
            if banco.get('nombre_corto'):
                nombre_completo += f" ({banco['nombre_corto']})"
            print(f"  - {banco['codigo']}: {nombre_completo}")

    print("\n✅ Proceso completado!")

if __name__ == "__main__":
    setup_maestras()
