import requests
import json

print("👤 Creando usuario admin...")

# Crear admin inicial
setup_url = "http://localhost:8000/api/auth/setup/create_admin"
admin_data = {
    "email": "admin@fme.cl",
    "password": "admin",
    "nombre_completo": "Super Admin",
    "role_id": 1
}

try:
    setup_response = requests.post(setup_url, json=admin_data)
    print(f"📊 Status Code: {setup_response.status_code}")
    
    if setup_response.status_code == 200:
        print("✅ Usuario admin creado exitosamente")
        admin_info = setup_response.json()
        print(f"👤 Usuario: {admin_info.get('email')}")
        print(f"🏷️  Nombre: {admin_info.get('nombre_completo')}")
        print("\n🚀 Ahora puedes ejecutar: python test_gemini.py")
    elif setup_response.status_code == 400:
        print("⚠️ Usuario admin ya existe o hay un error en los datos")
        print("📝 Respuesta:", setup_response.text)
        print("\n🚀 Intenta ejecutar: python test_gemini.py")
    else:
        print(f"❌ Error {setup_response.status_code}: {setup_response.text}")
        
except Exception as e:
    print(f"💥 Error: {e}")
    print("🔍 Verifica que el backend esté corriendo")