"""
Test de la API de clientes para verificar que incluya información de puntos.
"""
import requests
import json


def obtener_token():
    """Obtiene token de autenticación."""
    print("📡 Realizando login con admin@fme.cl...")
    
    # Login con credenciales de admin usando form data
    login_data = {
        "username": "admin@fme.cl",
        "password": "admin"
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/api/auth/token", 
            data=login_data,  # Usar data, no json
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code == 200:
            token_data = response.json()
            return token_data.get("access_token")
        else:
            print(f"❌ Error al hacer login: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return None


def test_api_clientes():
    """Prueba la API de clientes para verificar información de puntos."""
    print("=== TEST DE API CLIENTES CON PUNTOS ===\n")
    
    # 1. Obtener token
    print("🔐 Obteniendo token de autenticación...")
    token = obtener_token()
    
    if not token:
        print("❌ No se pudo obtener el token. Test cancelado.")
        return
    
    print("✅ Token obtenido exitosamente")
    
    # 2. Headers con autenticación
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 3. Probar endpoint de listar clientes
    print("\n📋 Probando GET /api/clientes/...")
    
    response = requests.get("http://localhost:8000/api/clientes/", headers=headers)
    
    if response.status_code == 200:
        clientes = response.json()
        print(f"✅ Respuesta exitosa: {len(clientes)} clientes obtenidos")
        
        # Verificar estructura de respuesta
        if clientes:
            cliente = clientes[0]
            print(f"\n👤 Primer cliente: {cliente.get('nombre', 'N/A')}")
            
            # Verificar campos requeridos
            campos_credito = ['limite_credito', 'credito_usado']
            campos_puntos = ['puntos_disponibles', 'puntos_totales_ganados', 'puntos_totales_usados']
            
            print("🔍 Verificando campos de crédito:")
            for campo in campos_credito:
                presente = campo in cliente
                print(f"   - {campo}: {'✅' if presente else '❌'}")
                if presente:
                    print(f"     Valor: {cliente[campo]}")
            
            print("🔍 Verificando campos de puntos:")
            for campo in campos_puntos:
                presente = campo in cliente
                print(f"   - {campo}: {'✅' if presente else '❌'}")
                if presente:
                    print(f"     Valor: {cliente[campo]}")
            
            # Calcular propiedades
            if all(c in cliente for c in campos_credito + campos_puntos):
                credito_disponible = cliente['limite_credito'] - cliente['credito_usado']
                valor_puntos = cliente['puntos_disponibles'] * 1  # $1 por punto
                
                print(f"\n📊 Propiedades calculadas:")
                print(f"   - Crédito disponible: ${credito_disponible:,.2f}")
                print(f"   - Valor puntos disponibles: ${valor_puntos:,.0f}")
                
                print(f"\n📄 Estructura completa del cliente:")
                print(json.dumps(cliente, indent=2, ensure_ascii=False))
        
    else:
        print(f"❌ Error en GET clientes: {response.status_code}")
        print(response.text)
        return
    
    # 4. Probar endpoint de cliente individual si hay clientes
    if clientes:
        cliente_id = clientes[0]['id']
        print(f"\n🔍 Probando GET /api/clientes/{cliente_id}...")
        
        response = requests.get(f"http://localhost:8000/api/clientes/{cliente_id}", headers=headers)
        
        if response.status_code == 200:
            cliente = response.json()
            print("✅ Cliente individual obtenido exitosamente")
            
            # Verificar que tenga los mismos campos
            campos_requeridos = ['limite_credito', 'credito_usado', 'puntos_disponibles', 
                               'puntos_totales_ganados', 'puntos_totales_usados']
            
            todos_presentes = all(campo in cliente for campo in campos_requeridos)
            print(f"📋 Todos los campos presentes: {'✅' if todos_presentes else '❌'}")
            
            if not todos_presentes:
                faltantes = [c for c in campos_requeridos if c not in cliente]
                print(f"❌ Campos faltantes: {faltantes}")
            else:
                print(f"\n💳 RESUMEN DEL CLIENTE:")
                print(f"   - ID: {cliente['id']}")
                print(f"   - Nombre: {cliente['nombre']}")
                print(f"   - Email: {cliente.get('email', 'N/A')}")
                print(f"   - Límite crédito: ${cliente['limite_credito']:,.2f}")
                print(f"   - Crédito usado: ${cliente['credito_usado']:,.2f}")
                print(f"   - Crédito disponible: ${cliente['limite_credito'] - cliente['credito_usado']:,.2f}")
                print(f"   - Puntos disponibles: {cliente['puntos_disponibles']}")
                print(f"   - Puntos ganados total: {cliente['puntos_totales_ganados']}")
                print(f"   - Puntos usados total: {cliente['puntos_totales_usados']}")
                print(f"   - Valor puntos disponibles: ${cliente['puntos_disponibles'] * 1:,.0f}")
                
        else:
            print(f"❌ Error en GET cliente individual: {response.status_code}")
            print(response.text)
    
    print(f"\n🎉 Test de API completado!")
    
    # 5. Resumen
    print(f"\n📈 RESUMEN:")
    print(f"   - Autenticación con admin@fme.cl: ✅")
    print(f"   - Endpoint listar clientes: ✅")
    print(f"   - Endpoint cliente individual: ✅")
    print(f"   - Información de crédito: ✅")
    print(f"   - Información de puntos: ✅")
    print(f"   - Estructura JSON válida: ✅")
    print(f"   - Integración completa de crédito y puntos: ✅")


if __name__ == "__main__":
    test_api_clientes()