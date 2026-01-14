#!/usr/bin/env python3
"""
Script para probar que el endpoint de precios-proveedor funciona correctamente después del fix
"""

import requests

BASE_URL = "http://localhost:8000"

def test_precios_proveedor():
    print("🔐 Haciendo login...")
    
    # Login
    login_data = {'username': 'admin@fme.cl', 'password': 'admin'}
    response = requests.post(f'{BASE_URL}/api/auth/token', data=login_data)
    
    if response.status_code == 200:
        token = response.json()['access_token']
        print('✅ Login exitoso')
        
        # Test precios-proveedor endpoint
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.get(f'{BASE_URL}/api/precios-proveedor/', headers=headers)
        print(f'📡 Status precios-proveedor: {response.status_code}')
        
        if response.status_code == 200:
            data = response.json()
            print(f'📋 Precios configurados: {len(data)}')
            if data:
                primer_precio = data[0]
                print(f'   - Primer precio: {primer_precio["precio_kg"]} por kg')
                print(f'   - Producto: {primer_precio["producto_nombre"]}')
                print(f'   - Proveedor: {primer_precio["proveedor_nombre"]}')
            else:
                print('   - No hay precios configurados')
        else:
            print(f'❌ Error: {response.text}')
            
        # También probar otros endpoints relacionados
        print('\n🧪 Probando endpoints relacionados...')
        
        # Productos
        response = requests.get(f'{BASE_URL}/api/productos/', headers=headers)
        print(f'📦 Status productos: {response.status_code}')
        
        # Proveedores de carne
        response = requests.get(f'{BASE_URL}/api/enrolamiento/proveedores-carne', headers=headers)
        print(f'🐄 Status proveedores-carne: {response.status_code}')
        
    else:
        print(f'❌ Error login: {response.status_code} - {response.text}')

if __name__ == "__main__":
    test_precios_proveedor()