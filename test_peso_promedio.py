#!/usr/bin/env python3
"""
Script para probar el nuevo endpoint de peso promedio
"""

import requests

BASE_URL = "http://localhost:8000"

def test_peso_promedio():
    print("🔐 Haciendo login...")
    
    # Login
    login_data = {'username': 'admin@fme.cl', 'password': 'admin'}
    response = requests.post(f'{BASE_URL}/api/auth/token', data=login_data)
    
    if response.status_code == 200:
        token = response.json()['access_token']
        print('✅ Login exitoso')
        
        # Test peso promedio endpoint
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.get(f'{BASE_URL}/api/stock-cajas/peso-promedio', headers=headers)
        print(f'📡 Status peso-promedio: {response.status_code}')
        
        if response.status_code == 200:
            data = response.json()
            print(f'📋 Productos con peso promedio: {len(data)}')
            for producto in data:
                print(f'   - {producto["producto_nombre"]} ({producto["proveedor_nombre"]}):')
                print(f'     Peso promedio: {producto["peso_promedio_kg"]} kg/caja')
                print(f'     Cajas disponibles: {producto["cantidad_cajas"]}')
                print()
        else:
            print(f'❌ Error: {response.text}')
    else:
        print(f'❌ Error login: {response.status_code} - {response.text}')

if __name__ == "__main__":
    test_peso_promedio()