import requests

r = requests.post('http://localhost:8000/api/auth/token', data={'username':'admin@elquincho.com','password':'admin123'})
token = r.json()['access_token']
h = {'Authorization': 'Bearer ' + token}

# Endpoint que usa el frontend (solo_con_stock=True por defecto)
r2 = requests.get('http://localhost:8000/api/stock-cajas/producto/64', headers=h)
print('=== /producto/64 (solo_con_stock=True) ===')
print(r2.json())

# Sin filtro de stock
r3 = requests.get('http://localhost:8000/api/stock-cajas/producto/64?solo_con_stock=false', headers=h)
print('=== /producto/64?solo_con_stock=false ===')
print(r3.json())

# Resumen general del stock
r4 = requests.get('http://localhost:8000/api/stock-cajas/', headers=h)
print('=== /stock-cajas/ (todos) ===')
for item in r4.json():
    print(f"  producto={item['producto_nombre']} proveedor={item['proveedor_nombre']} disponibles={item['cajas_disponibles']}")
