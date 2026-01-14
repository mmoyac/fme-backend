import requests

print("🔍 Verificando endpoints disponibles...")

# Verificar que el backend esté funcionando
try:
    health_response = requests.get("http://localhost:8000/health")
    print(f"✅ Backend funcionando - Status: {health_response.status_code}")
except:
    print("❌ Backend no responde en puerto 8000")
    exit(1)

# Verificar endpoints de documentación  
try:
    docs_response = requests.get("http://localhost:8000/docs")
    if docs_response.status_code == 200:
        print("📚 Documentación disponible en: http://localhost:8000/docs")
    
    # Verificar endpoint de Gemini directamente (sin auth por ahora)
    print("\n🤖 Probando endpoint de Gemini...")
    
    # Crear una imagen de prueba muy simple
    image_path = r"D:\ProyectosAI\Masas_Estacion\Etiqueta_Caja.jpeg"
    
    with open(image_path, "rb") as f:
        files = {"file": ("etiqueta_caja.jpeg", f, "image/jpeg")}
        gemini_response = requests.post("http://localhost:8000/api/gemini/extraer-etiqueta", files=files)
    
    print(f"📊 Status Gemini: {gemini_response.status_code}")
    
    if gemini_response.status_code == 401:
        print("🔒 Endpoint requiere autenticación (esperado)")
        print("💡 Necesitamos configurar el login correctamente")
    elif gemini_response.status_code == 200:
        print("🎉 ¡Gemini funcionando sin autenticación!")
        data = gemini_response.json()
        print("📝 Datos extraídos:")
        for key, value in data.items():
            print(f"   {key}: {value}")
    else:
        print(f"📝 Respuesta: {gemini_response.text}")

except Exception as e:
    print(f"❌ Error: {e}")

print("\n🌐 Abre http://localhost:8000/docs en tu navegador para ver todos los endpoints")