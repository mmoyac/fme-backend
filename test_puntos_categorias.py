"""
Test para verificar los puntos configurados por categoría.
"""
import requests
import json


def obtener_token():
    """Obtiene token de autenticación."""
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
            return response.json().get("access_token")
        else:
            print(f"❌ Error login: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def test_puntos_por_categoria():
    """Verificar los puntos configurados por categoría."""
    print("=== TEST PUNTOS POR CATEGORÍA ===\n")
    
    # 1. Obtener token
    token = obtener_token()
    if not token:
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 2. Obtener categorías
    print("📋 Obteniendo categorías...")
    response = requests.get("http://localhost:8000/api/maestras/categorias", headers=headers)
    
    if response.status_code == 200:
        categorias = response.json()
        print(f"✅ {len(categorias)} categorías encontradas\n")
        
        print("🎯 CONFIGURACIÓN ACTUAL DE PUNTOS:")
        print("=" * 50)
        
        for categoria in categorias:
            nombre = categoria.get('nombre', 'Sin nombre')
            puntos = categoria.get('puntos_fidelidad', 0)
            
            if puntos > 0:
                print(f"✅ {nombre:15} → {puntos:3} puntos por producto")
            else:
                print(f"❌ {nombre:15} → Sin bonificación")
        
        print("=" * 50)
        
        # 3. Buscar la categoría Lácteos específicamente
        categoria_lacteos = None
        for cat in categorias:
            if 'lácteos' in cat.get('nombre', '').lower() or 'lacteos' in cat.get('nombre', '').lower():
                categoria_lacteos = cat
                break
        
        if categoria_lacteos:
            print(f"\n🧀 ANÁLISIS CATEGORÍA LÁCTEOS:")
            print(f"   - Nombre: {categoria_lacteos.get('nombre')}")
            print(f"   - ID: {categoria_lacteos.get('id')}")
            print(f"   - Puntos por producto: {categoria_lacteos.get('puntos_fidelidad')}")
            print(f"   - Descripción: {categoria_lacteos.get('descripcion', 'N/A')}")
            
            puntos_esperados = categoria_lacteos.get('puntos_fidelidad', 0)
            if puntos_esperados == 8:
                print(f"   ✅ Configuración CORRECTA: 8 puntos")
            elif puntos_esperados == 60:
                print(f"   ❌ Configuración INCORRECTA: 60 puntos (debería ser 8)")
                print(f"   🔧 NECESITA CORRECCIÓN")
            else:
                print(f"   ⚠️ Configuración INESPERADA: {puntos_esperados} puntos")
            
        else:
            print(f"\n❌ No se encontró categoría 'Lácteos'")
            print(f"Categorías disponibles:")
            for cat in categorias:
                print(f"   - {cat.get('nombre')}")
    
    else:
        print(f"❌ Error obteniendo categorías: {response.status_code}")
        print(response.text)
    
    # 4. Hacer un cálculo de prueba
    print(f"\n🧮 SIMULACIÓN DE CÁLCULO:")
    print(f"📦 Producto: 1 queso ($6,000)")
    print(f"📂 Categoría: Lácteos")
    
    if categoria_lacteos:
        puntos_configurados = categoria_lacteos.get('puntos_fidelidad', 0)
        cantidad = 1
        puntos_calculados = puntos_configurados * cantidad
        
        print(f"🔢 Cálculo: {puntos_configurados} puntos × {cantidad} producto = {puntos_calculados} puntos")
        
        if puntos_calculados == 8:
            print(f"✅ Resultado CORRECTO: 8 puntos")
        elif puntos_calculados == 60:
            print(f"❌ Resultado INCORRECTO: 60 puntos")
            print(f"🔧 Problema: La categoría Lácteos tiene {puntos_configurados} puntos en lugar de 8")
        else:
            print(f"⚠️ Resultado INESPERADO: {puntos_calculados} puntos")


if __name__ == "__main__":
    test_puntos_por_categoria()