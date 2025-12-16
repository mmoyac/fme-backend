import requests
import json
import os
import sys

# Agregar directorio raiz para importar config si fuera necesario, 
# pero usare requests directo a localhost
BASE_URL = "http://localhost:8000/api"

def login():
    print("🔐 Autenticando...")
    try:
        response = requests.post(
            f"http://localhost:8000/api/auth/token",
            data={"username": "admin@fme.cl", "password": "admin"} # Default desde seed
        )
        if response.status_code == 200:
            token = response.json()["access_token"]
            print("✅ Login exitoso")
            return {"Authorization": f"Bearer {token}"}
        else:
            print(f"❌ Error Login: {response.text}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Excepción Login: {e}")
        sys.exit(1)

def test_compra():
    headers = login()
    
    # 1. Obtener datos maestros necesarios
    print("\n📦 Obteniendo datos maestros...")
    
    # Proveedores
    try:
        r = requests.get(f"{BASE_URL}/compras/proveedores", headers=headers)
        r.raise_for_status()
        proveedores = r.json()
        if not proveedores:
            # Crear proveedor dummy si no hay
            print("  ℹ️  Creando proveedor dummy...")
            dummy_prov = {"nombre": "Proveedor Test", "rut": "1-9", "activo": True}
            r = requests.post(f"{BASE_URL}/compras/proveedores", json=dummy_prov, headers=headers)
            proveedores = [r.json()]
        proveedor_id = proveedores[0]["id"]
        print(f"  👉 Proveedor ID: {proveedor_id}")
    except Exception as e:
        print(f"❌ Error obteniendo proveedores: {e}")
        return

    # Locales
    try:
        r = requests.get(f"{BASE_URL}/locales/", headers=headers)
        r.raise_for_status()
        locales = r.json()
        if not locales:
            print("❌ No hay locales. Crea uno primero.")
            return
        local_id = locales[0]["id"]
        print(f"  👉 Local ID: {local_id}")
    except Exception as e:
        print(f"❌ Error obteniendo locales: {e}")
        return

    # Tipos Documento
    try:
        r = requests.get(f"{BASE_URL}/maestras/tipos-documento", headers=headers)
        r.raise_for_status()
        tipos = r.json()
        if not tipos:
            print("❌ No hay tipos de documento. Debes correr seed.")
            return
        tipo_id = tipos[0]["id"]
        print(f"  👉 Tipo Documento ID: {tipo_id} ({tipos[0]['nombre']})")
    except Exception as e:
        print(f"❌ Error obteniendo tipos documento: {e}")
        return

    # Productos (para detalle)
    try:
        r = requests.get(f"{BASE_URL}/productos/", headers=headers)
        r.raise_for_status()
        productos = r.json()
        if not productos:
             # Crear producto dummy 
            print("  ℹ️  Creando producto dummy...")
            dummy_prod = {
                "nombre": "Harina Test", "sku": "HAR-TEST-001", 
                "categoria_id": 1, "tipo_producto_id": 1, "unidad_medida_id": 1,
                "es_vendible": True, "activo": True, "stock_minimo": 10, "stock_critico": 5
            }
            # Asumiendo maestras existen... si falla es otro tema
            r = requests.post(f"{BASE_URL}/productos/", json=dummy_prod, headers=headers)
            if r.status_code != 201:
                 print(f" Error creando producto: {r.text}")
                 return
            productos = [r.json()]
        
        producto_id = productos[0]["id"]
        print(f"  👉 Producto ID: {producto_id}")
    except Exception as e:
        print(f"❌ Error obteniendo productos: {e}")
        return

    # 2. Crear Compra
    print("\n🛒 Creando Compra de Prueba...")
    payload = {
        "proveedor_id": proveedor_id,
        "local_id": local_id,
        "tipo_documento_id": tipo_id,
        "fecha_compra": "2023-12-16", # Probar formato corto
        "numero_documento": "TEST-123456",
        "notas": "Compra generada por script de prueba",
        "detalles": [
            {
                "producto_id": producto_id,
                "cantidad": 100,
                "precio_unitario": 500.5
            }
        ]
    }
    
    try:
        res = requests.post(f"{BASE_URL}/compras/", json=payload, headers=headers)
        if res.status_code == 200:
            compra = res.json()
            print(f"✅ Compra creada exitosamente! ID: {compra.get('id')}")
            print(json.dumps(compra, indent=2))
        else:
            print(f"❌ Error al crear compra: {res.status_code}")
            print(res.text)
    except Exception as e:
        print(f"❌ Excepción al crear compra: {e}")

if __name__ == "__main__":
    test_compra()
