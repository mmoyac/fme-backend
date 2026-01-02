"""
Script para probar el endpoint de PDF.
"""
import requests
import os

BASE_URL = "http://localhost:8000"

def probar_pdf():
    # Login
    login_data = {'username': 'admin@fme.cl', 'password': 'admin'}
    resp = requests.post(f"{BASE_URL}/api/auth/token", data=login_data)
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Probar descarga PDF
    turno_id = 12
    print(f"Descargando PDF del turno {turno_id}...")
    
    resp = requests.get(f"{BASE_URL}/api/caja/turno/{turno_id}/pdf", headers=headers)
    
    if resp.status_code == 200:
        with open(f"test_cierre_turno_{turno_id}.pdf", "wb") as f:
            f.write(resp.content)
        print(f"✅ PDF generado exitosamente: test_cierre_turno_{turno_id}.pdf")
        print(f"Tamaño: {len(resp.content)} bytes")
    else:
        print(f"❌ Error: {resp.status_code}")
        print(f"Respuesta: {resp.text}")

if __name__ == "__main__":
    probar_pdf()