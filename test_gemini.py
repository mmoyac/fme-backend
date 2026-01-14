import requests
import json
import os

print("🔐 Paso 1: Obteniendo token de autenticación...")

# Primero, obtener token de login
login_url = "http://localhost:8000/api/auth/login"
login_data = {
    "username": "admin@fme.cl",  # Usuario admin por defecto
    "password": "admin"
}

try:
    login_response = requests.post(login_url, data=login_data)
    if login_response.status_code == 200:
        token_info = login_response.json()
        access_token = token_info["access_token"]
        print("✅ Token obtenido exitosamente")
    else:
        print(f"❌ Error login {login_response.status_code}: {login_response.text}")
        print("💡 Tip: Puede que el usuario admin no exista. Usar endpoint de setup:")
        print("POST http://localhost:8000/api/auth/setup/create_admin")
        exit(1)
except Exception as e:
    print(f"💥 Error de login: {e}")
    exit(1)

# Test del endpoint de Gemini Vision con imagen real de etiqueta de carne
url = "http://localhost:8000/api/gemini/extraer-etiqueta"

# Ruta de la imagen real de etiqueta
image_path = r"D:\ProyectosAI\Masas_Estacion\Etiqueta_Caja.jpeg"

print("\n🤖 Paso 2: Probando endpoint Gemini Vision API con etiqueta real...")
print("📡 URL:", url)
print("📸 Imagen:", image_path)

# Verificar que la imagen existe
if not os.path.exists(image_path):
    print(f"❌ Error: No se encontró la imagen en {image_path}")
    exit(1)

try:
    # Headers con autenticación
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    # Hacer la petición con la imagen real
    with open(image_path, "rb") as f:
        files = {"file": ("etiqueta_caja.jpeg", f, "image/jpeg")}
        response = requests.post(url, files=files, headers=headers)
    
    print(f"📊 Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ ¡ÉXITO! Gemini Vision API está funcionando")
        data = response.json()
        print("\n🎯 DATOS EXTRAÍDOS:")
        print("=" * 50)
        print(f"🏷️  Peso Bruto:     {data.get('peso_bruto_kg', 'No detectado')} kg")
        print(f"⚖️  Peso Neto:      {data.get('peso_neto_kg', 'No detectado')} kg") 
        print(f"📅 Fecha Venc.:     {data.get('fecha_vencimiento', 'No detectada')}")
        print(f"🏭 Lote/Tropa:      {data.get('lote_tropa', 'No detectado')}")
        print(f"📊 Código Barras:   {data.get('codigo_barras_superior', 'No detectado')}")
        print(f"🎯 Confianza:       {int((data.get('confianza', 0) * 100))}%")
        
        # Calcular campos detectados
        campos_detectados = sum([
            1 if data.get('peso_bruto_kg') else 0,
            1 if data.get('peso_neto_kg') else 0,
            1 if data.get('fecha_vencimiento') else 0,
            1 if data.get('lote_tropa') else 0,
            1 if data.get('codigo_barras_superior') else 0
        ])
        
        precision = (campos_detectados / 5) * 100
        print(f"📈 Precisión:       {precision:.0f}% ({campos_detectados}/5 campos)")
        
        if campos_detectados >= 4:
            print("🎉 ¡INCREÍBLE! Precisión superior al 80%")
        elif campos_detectados >= 3:
            print("👍 ¡Muy bien! Mucho mejor que Tesseract (40%)")
        
        if data.get('texto_extraido'):
            print("\n📝 Respuesta completa de Gemini:")
            print("-" * 40)
            print(data['texto_extraido'][:500] + "..." if len(data['texto_extraido']) > 500 else data['texto_extraido'])
            
    elif response.status_code == 503:
        print("❌ Gemini API no configurada o API key inválida")
        print("🔑 Verifica que GEMINI_API_KEY esté correcta en .env")
        print("📝 Error:", response.text)
    else:
        print(f"⚠️ Error {response.status_code}: {response.text}")
        
except Exception as e:
    print(f"💥 Error de conexión: {e}")
    print("🔍 Verifica que el backend esté corriendo en puerto 8000")