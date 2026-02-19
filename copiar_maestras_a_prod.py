"""
Script para copiar datos maestros de desarrollo a producción
"""
import requests
import json

# URLs
DEV_URL = "http://localhost:8000"
PROD_URL = "https://api.masasestacion.cl"

# Credenciales
USERNAME = "admin@fme.cl"
PASSWORD = "admin"

def login(base_url):
    """Obtener token de autenticación"""
    response = requests.post(
        f"{base_url}/api/auth/token",
        data={"username": USERNAME, "password": PASSWORD}
    )
    response.raise_for_status()
    return response.json()["access_token"]

def get_headers(token):
    """Headers con autenticación"""
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

def main():
    print("🔐 Autenticando en desarrollo...")
    dev_token = login(DEV_URL)
    print("✅ Autenticado en desarrollo")
    
    print("\n🔐 Autenticando en producción...")
    prod_token = login(PROD_URL)
    print("✅ Autenticado en producción")
    
    # Obtener tipos de documento de desarrollo
    print("\n📋 Obteniendo tipos de documento de desarrollo...")
    response = requests.get(
        f"{DEV_URL}/api/maestras/tipos-documento",
        headers=get_headers(dev_token)
    )
    tipos_doc_dev = response.json()
    print(f"✅ Obtenidos {len(tipos_doc_dev)} tipos de documento")
    
    # Obtener medios de pago de desarrollo
    print("\n📋 Obteniendo medios de pago de desarrollo...")
    response = requests.get(
        f"{DEV_URL}/api/maestras/medios-pago",
        headers=get_headers(dev_token)
    )
    medios_pago_dev = response.json()
    print(f"✅ Obtenidos {len(medios_pago_dev)} medios de pago")
    
    # Obtener datos existentes en producción
    print("\n📋 Verificando datos existentes en producción...")
    response = requests.get(
        f"{PROD_URL}/api/maestras/tipos-documento",
        headers=get_headers(prod_token)
    )
    tipos_doc_prod = response.json()
    tipos_doc_prod_codigos = {td['codigo'] for td in tipos_doc_prod}
    print(f"   Tipos de documento en producción: {len(tipos_doc_prod)}")
    
    response = requests.get(
        f"{PROD_URL}/api/maestras/medios-pago",
        headers=get_headers(prod_token)
    )
    medios_pago_prod = response.json()
    medios_pago_prod_codigos = {mp['codigo'] for mp in medios_pago_prod}
    print(f"   Medios de pago en producción: {len(medios_pago_prod)}")
    
    # Copiar tipos de documento
    print("\n📤 Copiando tipos de documento a producción...")
    for tipo_doc in tipos_doc_dev:
        if tipo_doc['codigo'] in tipos_doc_prod_codigos:
            print(f"   ⏭️  Saltando {tipo_doc['codigo']} - {tipo_doc['nombre']} (ya existe)")
            continue
        
        data = {
            "codigo": tipo_doc['codigo'],
            "nombre": tipo_doc['nombre'],
            "descripcion": tipo_doc.get('descripcion', ''),
            "requiere_datos_tributarios": tipo_doc.get('requiere_datos_tributarios', False),
            "es_electronico": tipo_doc.get('es_electronico', False)
        }
        
        try:
            response = requests.post(
                f"{PROD_URL}/api/maestras/tipos-documento",
                headers=get_headers(prod_token),
                json=data
            )
            response.raise_for_status()
            print(f"   ✅ Creado {tipo_doc['codigo']} - {tipo_doc['nombre']}")
        except Exception as e:
            print(f"   ❌ Error creando {tipo_doc['codigo']}: {e}")
    
    # Copiar medios de pago
    print("\n📤 Copiando medios de pago a producción...")
    for medio_pago in medios_pago_dev:
        if medio_pago['codigo'] in medios_pago_prod_codigos:
            print(f"   ⏭️  Saltando {medio_pago['codigo']} - {medio_pago['nombre']} (ya existe)")
            continue
        
        data = {
            "codigo": medio_pago['codigo'],
            "nombre": medio_pago['nombre'],
            "descripcion": medio_pago.get('descripcion', ''),
            "activo": medio_pago['activo']
        }
        
        try:
            response = requests.post(
                f"{PROD_URL}/api/maestras/medios-pago",
                headers=get_headers(prod_token),
                json=data
            )
            response.raise_for_status()
            print(f"   ✅ Creado {medio_pago['codigo']} - {medio_pago['nombre']}")
        except Exception as e:
            print(f"   ❌ Error creando {medio_pago['codigo']}: {e}")
    
    print("\n🎉 ¡Proceso completado!")

if __name__ == "__main__":
    main()
