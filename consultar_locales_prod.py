"""
Consultar locales existentes en producción.
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

# Obtener locales
print("🏪 Obteniendo locales de producción...\n")
resp = requests.get(f"{API_URL}/api/locales/", headers=headers)
locales = resp.json()

print("=" * 100)
print("LOCALES EN PRODUCCIÓN:")
print("=" * 100)

if locales:
    print(f"{'ID':<5} {'Código':<15} {'Nombre':<30} {'Dirección':<30} {'Tipo':<10}")
    print("-" * 100)
    for local in locales:
        print(f"{local.get('id', 'N/A'):<5} {local.get('codigo', 'N/A'):<15} {local.get('nombre', 'N/A'):<30} {str(local.get('direccion', 'N/A'))[:29]:<30} {local.get('tipo', 'N/A'):<10}")
    
    print("=" * 100)
    print(f"\nTotal: {len(locales)} locales\n")
    
    # Generar CSV
    print("📄 Generando CSV:")
    print("-" * 100)
    print("codigo,nombre,direccion,telefono,tipo")
    for local in locales:
        codigo = local.get('codigo', '')
        nombre = local.get('nombre', '')
        direccion = local.get('direccion', '') or ''
        telefono = local.get('telefono', '') or ''
        tipo = local.get('tipo', '')
        print(f"{codigo},{nombre},{direccion},{telefono},{tipo}")
    print("-" * 100)
else:
    print("⚠️ No hay locales registrados")
