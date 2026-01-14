#!/usr/bin/env python3
"""
Script para probar la integración enrolamiento -> stock de cajas
"""
import requests
import json

BASE_URL = "http://localhost:8000"

# Primero necesitamos autenticarnos
def login():
    login_data = {
        "username": "admin@fme.cl",
        "password": "admin"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/token", data=login_data)
    if response.status_code == 200:
        token_data = response.json()
        return token_data["access_token"]
    else:
        print(f"Error en login: {response.status_code}")
        print(response.text)
        return None

def get_headers(token):
    return {"Authorization": f"Bearer {token}"}

def main():
    print("🔐 Obteniendo token de acceso...")
    token = login()
    if not token:
        print("❌ No se pudo autenticar")
        return
    
    headers = get_headers(token)
    
    # Obtener lista de enrolamientos
    print("\n📋 Obteniendo enrolamientos...")
    response = requests.get(f"{BASE_URL}/api/enrolamiento/enrolamientos", headers=headers)
    if response.status_code == 200:
        enrolamientos = response.json()
        print(f"Encontrados {len(enrolamientos)} enrolamientos:")
        
        # Debug: ver estructura de los datos
        if enrolamientos:
            print("Estructura del primer enrolamiento:")
            print(json.dumps(enrolamientos[0], indent=2, default=str))
        
        for enr in enrolamientos:
            # Usar get() para evitar KeyError
            estado = enr.get('estado_nombre', 'N/A')
            proveedor_nombre = enr.get('proveedor_nombre', 'N/A')
            print(f"  ID: {enr['id']} | Estado: {estado} | Proveedor: {proveedor_nombre}")
            
        # Buscar un enrolamiento en estado "En Proceso"
        enrolamiento_test = None
        for enr in enrolamientos:
            if enr.get('estado_nombre') == 'En Proceso' and enr['id'] != 3:  # Usar uno diferente al 3 que ya se finalizó
                enrolamiento_test = enr
                break
                
        if not enrolamiento_test:
            print("\n⚠️  No hay enrolamientos 'En Proceso' para probar")
            return
            
        print(f"\n🎯 Usando enrolamiento {enrolamiento_test['id']} para prueba")
        
    else:
        print(f"Error obteniendo enrolamientos: {response.status_code}")
        print(response.text)
        return
    
    # Obtener estado actual del stock
    print(f"\n📦 Stock ANTES de finalizar enrolamiento...")
    response = requests.get(f"{BASE_URL}/api/stock-cajas/", headers=headers)
    if response.status_code == 200:
        stock_antes = response.json()
        print(f"Registros de stock actuales: {len(stock_antes)}")
        for stock in stock_antes:
            print(f"  {stock['proveedor_nombre']} - {stock['producto_nombre']}: {stock['cantidad_disponible']} cajas")
    else:
        print("Error obteniendo stock inicial")
    
    # Finalizar el enrolamiento para activar la integración
    print(f"\n🚀 Finalizando enrolamiento {enrolamiento_test['id']}...")
    update_data = {
        "estado_id": 3  # FINALIZADO
    }
    
    response = requests.put(
        f"{BASE_URL}/api/enrolamiento/enrolamientos/{enrolamiento_test['id']}",
        json=update_data,
        headers=headers
    )
    
    if response.status_code == 200:
        print("✅ Enrolamiento finalizado exitosamente!")
        updated_enr = response.json()
        print(f"Estado actual: {updated_enr['estado']}")
        
        # Ver el stock DESPUÉS de finalizar
        print(f"\n📦 Stock DESPUÉS de finalizar enrolamiento...")
        response = requests.get(f"{BASE_URL}/api/stock-cajas/", headers=headers)
        if response.status_code == 200:
            stock_despues = response.json()
            print(f"Registros de stock actuales: {len(stock_despues)}")
            for stock in stock_despues:
                print(f"  {stock['proveedor_nombre']} - {stock['producto_nombre']}: {stock['cantidad_disponible']} cajas")
        
        # Ver movimientos de stock generados
        print(f"\n📈 Movimientos de stock generados...")
        response = requests.get(f"{BASE_URL}/api/stock-cajas/movimientos", headers=headers)
        if response.status_code == 200:
            movimientos = response.json()
            for mov in movimientos:
                if mov['tipo_movimiento'] == 'ENTRADA_ENROLAMIENTO':
                    print(f"  {mov['tipo_movimiento']}: +{mov['cantidad']} cajas - {mov['descripcion']}")
    else:
        print(f"❌ Error finalizando enrolamiento: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    main()