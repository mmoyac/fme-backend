import requests
import json

print("🧪 Probando Gemini Vision API directamente con tu imagen...")

# Usar la imagen real
image_path = r"D:\ProyectosAI\Masas_Estacion\Etiqueta_Caja.jpeg"

# Verificar que existe
import os
if not os.path.exists(image_path):
    print(f"❌ No encontré la imagen en: {image_path}")
    exit(1)

print(f"📸 Usando imagen: {image_path}")

# Probar sin autenticación primero para ver qué pasa
try:
    print("\n🔓 Prueba 1: Sin autenticación...")
    with open(image_path, "rb") as f:
        files = {"file": ("etiqueta_caja.jpeg", f, "image/jpeg")}
        response = requests.post("http://localhost:8000/api/gemini/extraer-etiqueta", files=files)
    
    print(f"Status: {response.status_code}")
    print(f"Respuesta: {response.text}")
    
except Exception as e:
    print(f"Error: {e}")

# Si necesita autenticación, intentar con token
if response.status_code == 401:
    print("\n🔑 Necesita autenticación, creando usuario admin...")
    
    # Intentar crear admin
    admin_data = {
        "email": "test@test.com", 
        "password": "test123",
        "nombre_completo": "Test User",
        "role_id": 1
    }
    
    try:
        setup_response = requests.post("http://localhost:8000/api/auth/setup/create_admin", json=admin_data)
        print(f"Setup admin: {setup_response.status_code} - {setup_response.text}")
    except:
        print("Usuario admin ya existe o error en setup")
    
    # Login con admin existente o nuevo
    login_data = {
        "username": "admin@fme.cl",  # Usuario por defecto
        "password": "admin"
    }
    
    # Intentar diferentes endpoints de login
    login_urls = [
        "http://localhost:8000/api/auth/token",
        "http://localhost:8000/api/auth/login", 
        "http://localhost:8000/auth/token",
        "http://localhost:8000/token"
    ]
    
    token = None
    for login_url in login_urls:
        try:
            print(f"🔑 Intentando login en: {login_url}")
            login_response = requests.post(login_url, data=login_data)
            print(f"   Status: {login_response.status_code}")
            
            if login_response.status_code == 200:
                token_info = login_response.json()
                token = token_info.get("access_token")
                if token:
                    print(f"✅ Token obtenido: {token[:20]}...")
                    break
            else:
                print(f"   Error: {login_response.text[:100]}")
        except Exception as e:
            print(f"   Error: {e}")
    
    if token:
        print(f"\n🔒 Prueba 2: Con autenticación...")
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            with open(image_path, "rb") as f:
                files = {"file": ("etiqueta_caja.jpeg", f, "image/jpeg")}
                auth_response = requests.post(
                    "http://localhost:8000/api/gemini/extraer-etiqueta", 
                    files=files, 
                    headers=headers
                )
            
            print(f"Status: {auth_response.status_code}")
            print(f"Headers: {dict(auth_response.headers)}")
            print(f"Respuesta completa:")
            print("=" * 50)
            print(auth_response.text)
            print("=" * 50)
            
            if auth_response.status_code == 200:
                try:
                    data = auth_response.json()
                    print("✅ ¡JSON válido!")
                    print(json.dumps(data, indent=2, ensure_ascii=False))
                except:
                    print("❌ No es JSON válido pero status 200")
                    
        except Exception as e:
            print(f"Error con token: {e}")
    else:
        print("❌ No pude obtener token de autenticación")

print("\n🔍 Verificando logs del backend...")
print("Revisa la terminal de logs del backend para ver qué respondió Gemini exactamente.")