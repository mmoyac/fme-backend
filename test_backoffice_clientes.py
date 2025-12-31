"""
Test para verificar que la API de clientes incluya información de puntos para el backoffice.
"""
import requests
import json


def obtener_token():
    """Obtiene token de autenticación."""
    print("📡 Realizando login con admin@fme.cl...")
    
    login_data = {
        "username": "admin@fme.cl",
        "password": "admin"
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/api/auth/token", 
            data=login_data,
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


def test_backoffice_clientes_puntos():
    """Test para verificar que los clientes incluyan información de puntos para el backoffice."""
    print("=== TEST BACKOFFICE - CLIENTES CON PUNTOS ===\n")
    
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
    print("\n📋 Probando GET /api/clientes/ para backoffice...")
    
    response = requests.get("http://localhost:8000/api/clientes/", headers=headers)
    
    if response.status_code == 200:
        clientes = response.json()
        print(f"✅ Respuesta exitosa: {len(clientes)} clientes obtenidos")
        
        if clientes:
            cliente = clientes[0]
            print(f"\n👤 Primer cliente: {cliente.get('nombre', 'N/A')}")
            
            # Verificar estructura completa para backoffice
            campos_basicos = ['id', 'nombre', 'email', 'telefono']
            campos_credito = ['limite_credito', 'credito_usado']
            campos_puntos = ['puntos_disponibles', 'puntos_totales_ganados', 'puntos_totales_usados']
            
            print("🔍 Verificando estructura completa:")
            
            # Campos básicos
            print("   📄 Campos básicos:")
            for campo in campos_basicos:
                presente = campo in cliente
                print(f"      - {campo}: {'✅' if presente else '❌'}")
            
            # Campos de crédito
            print("   💳 Campos de crédito:")
            for campo in campos_credito:
                presente = campo in cliente
                print(f"      - {campo}: {'✅' if presente else '❌'}")
                if presente:
                    print(f"        Valor: {cliente[campo]}")
            
            # Campos de puntos
            print("   💰 Campos de puntos:")
            for campo in campos_puntos:
                presente = campo in cliente
                print(f"      - {campo}: {'✅' if presente else '❌'}")
                if presente:
                    print(f"        Valor: {cliente[campo]}")
            
            # Verificar estructura completa
            todos_campos = campos_basicos + campos_credito + campos_puntos
            todos_presentes = all(campo in cliente for campo in todos_campos)
            
            print(f"\n📊 Estructura completa para backoffice: {'✅' if todos_presentes else '❌'}")
            
            if todos_presentes:
                # Estadísticas para dashboard del backoffice
                print(f"\n📈 ESTADÍSTICAS PARA BACKOFFICE:")
                print(f"   - Cliente ID: {cliente['id']}")
                print(f"   - Nombre: {cliente['nombre']}")
                print(f"   - Crédito disponible: ${(cliente['limite_credito'] or 0) - (cliente['credito_usado'] or 0):,.0f}")
                print(f"   - Puntos disponibles: {cliente['puntos_disponibles']} (${cliente['puntos_disponibles']} valor)")
                print(f"   - Historial puntos: Ganados {cliente['puntos_totales_ganados']} | Usados {cliente['puntos_totales_usados']}")
                
                # Calcular actividad
                if cliente['puntos_totales_ganados'] and cliente['puntos_totales_ganados'] > 0:
                    porcentaje_uso = round((cliente['puntos_totales_usados'] / cliente['puntos_totales_ganados']) * 100, 1)
                    print(f"   - Actividad puntos: {porcentaje_uso}% de puntos usados")
                
        # 4. Estadísticas globales
        print(f"\n📊 ESTADÍSTICAS GLOBALES:")
        total_clientes = len(clientes)
        clientes_con_credito = len([c for c in clientes if c.get('limite_credito', 0) > 0])
        clientes_con_puntos = len([c for c in clientes if c.get('puntos_disponibles', 0) > 0])
        total_puntos_sistema = sum(c.get('puntos_disponibles', 0) for c in clientes)
        
        print(f"   - Total clientes: {total_clientes}")
        print(f"   - Con crédito: {clientes_con_credito}")
        print(f"   - Con puntos: {clientes_con_puntos}")
        print(f"   - Total puntos en sistema: {total_puntos_sistema:,} (${total_puntos_sistema:,} valor)")
        
        print(f"\n🎉 ¡API lista para backoffice!")
        
    else:
        print(f"❌ Error en GET clientes: {response.status_code}")
        print(response.text)


if __name__ == "__main__":
    test_backoffice_clientes_puntos()