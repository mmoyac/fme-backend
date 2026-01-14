#!/usr/bin/env python3
"""
Script para probar que el endpoint de alertas funciona correctamente después del fix de autenticación
"""

import requests

BASE_URL = "http://localhost:8000"

def test_alertas():
    print("🔐 Haciendo login...")
    
    # Login
    login_data = {'username': 'admin@fme.cl', 'password': 'admin'}
    response = requests.post(f'{BASE_URL}/api/auth/token', data=login_data)
    
    if response.status_code == 200:
        token = response.json()['access_token']
        print('✅ Login exitoso')
        
        # Test alertas endpoint
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.get(f'{BASE_URL}/api/alertas/productos-sin-precio', headers=headers)
        print(f'📡 Status alertas: {response.status_code}')
        
        if response.status_code == 200:
            data = response.json()
            print(f'📋 Productos sin precio: {len(data)}')
            if data:
                primer_producto = data[0]
                print(f'   - Primer producto: {primer_producto["producto_nombre"]}')
                print(f'   - Proveedor: {primer_producto["proveedor_nombre"]}')
                print(f'   - Total cajas: {primer_producto["total_cajas"]}')
            else:
                print('   - ✅ No hay productos sin precio configurado')
        else:
            print(f'❌ Error: {response.text}')
    else:
        print(f'❌ Error login: {response.status_code} - {response.text}')

if __name__ == "__main__":
    test_alertas()