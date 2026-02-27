import requests

# Configuración
DEV_API = "http://localhost:8000/api/paleta-colores/"
PROD_API = "https://api.masasestacion.cl/api/paleta-colores/"

# Reemplaza estos tokens por los de admin válidos en cada entorno
DEV_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbkBmbWUuY2wiLCJyb2xlIjoiYWRtaW4iLCJ0ZW5hbnRfaWQiOjEsImV4cCI6MTc3MjE3MTUyMn0.nocn_fcQ78mEc1ZtMO2Brkz7R6E91lFerfLLglv6nzk"
PROD_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbkBmbWUuY2wiLCJyb2xlIjoiYWRtaW4iLCJ0ZW5hbnRfaWQiOjEsImV4cCI6MTc3MjE3MTU2Nn0.LhSSTGW0J7QLFTZFUfv-seKt-0vXKUgCUHZhB4sRuhU"

# 1. Obtener todas las paletas de desarrollo
headers_dev = {"Authorization": f"Bearer {DEV_TOKEN}"}
resp = requests.get(DEV_API, headers=headers_dev)
resp.raise_for_status()
paletas = resp.json()

print(f"Paletas encontradas en desarrollo: {len(paletas)}")

# 2. Crear cada paleta en producción
headers_prod = {"Authorization": f"Bearer {PROD_TOKEN}", "Content-Type": "application/json"}
for paleta in paletas:
    # Elimina campos que no deben enviarse (id, fechas, etc.)
    data = {k: v for k, v in paleta.items() if k not in ["id", "fecha_creacion", "fecha_actualizacion", "creado_por", "es_publica"]}
    print(f"Copiando paleta: {data.get('nombre')}")
    r = requests.post(PROD_API, json=data, headers=headers_prod)
    if r.status_code == 201:
        print(f"  ✔️ Copiada: {data.get('nombre')}")
    elif r.status_code == 409:
        print(f"  ⚠️ Ya existe: {data.get('nombre')}")
    else:
        print(f"  ❌ Error: {r.status_code} - {r.text}")
