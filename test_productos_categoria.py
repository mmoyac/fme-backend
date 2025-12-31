#!/usr/bin/env python3
"""
Script para probar que el endpoint de productos incluye información de categoría.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import json

def test_productos_con_categoria():
    print("=== 🔍 TEST: Endpoint productos con información de categoría ===")
    
    try:
        # Hacer login para obtener token
        login_response = requests.post(
            "http://localhost:8000/api/auth/token",
            data={
                "username": "admin@fme.cl",
                "password": "admin"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if login_response.status_code != 200:
            print(f"❌ Error al hacer login: {login_response.status_code}")
            return
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Obtener productos
        response = requests.get("http://localhost:8000/api/productos/", headers=headers)
        
        if response.status_code != 200:
            print(f"❌ Error al obtener productos: {response.status_code}")
            print(response.text)
            return
        
        productos = response.json()
        print(f"✅ Productos obtenidos: {len(productos)}")
        
        # Buscar el queso y verificar datos
        queso = None
        for p in productos:
            if 'queso' in p['nombre'].lower():
                queso = p
                break
        
        if not queso:
            print("❌ No se encontró producto 'Queso'")
            return
        
        print(f"\n📋 Información del Queso:")
        print(f"   ID: {queso['id']}")
        print(f"   Nombre: {queso['nombre']}")
        print(f"   SKU: {queso['sku']}")
        print(f"   Categoria ID: {queso['categoria_id']}")
        print(f"   Categoria Nombre: {queso.get('categoria_nombre', 'NO INCLUIDO')}")
        print(f"   Categoria Puntos: {queso.get('categoria_puntos_fidelidad', 'NO INCLUIDO')}")
        
        # Verificar que los nuevos campos están presentes
        if 'categoria_nombre' in queso and 'categoria_puntos_fidelidad' in queso:
            print(f"\n✅ Campos de categoría incluidos correctamente")
            
            if queso['categoria_puntos_fidelidad'] == 8:
                print(f"✅ Puntos de fidelidad correctos: {queso['categoria_puntos_fidelidad']}")
            else:
                print(f"❌ Puntos incorrectos, se esperaba 8, se obtuvo {queso['categoria_puntos_fidelidad']}")
        else:
            print(f"\n❌ Faltan campos de categoría en la respuesta")
        
    except Exception as e:
        print(f"❌ Error durante test: {e}")

if __name__ == "__main__":
    test_productos_con_categoria()