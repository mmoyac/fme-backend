import requests

r = requests.post('http://localhost:8000/api/auth/token', data={'username':'admin@elquincho.com','password':'admin123'})
token = r.json()['access_token']
h = {'Authorization': 'Bearer ' + token}

# Ver proveedores del tenant 9
r2 = requests.get('http://localhost:8000/api/compras/proveedores', headers=h)
print('=== PROVEEDORES ===')
for p in r2.json():
    print('id=%s nombre=%s rut=%s' % (p['id'], p['nombre'], p['rut']))

# Ver precios proveedor para producto 64 (Asiento)
r3 = requests.get('http://localhost:8000/api/precios-proveedor/?producto_id=64', headers=h)
print('\n=== PRECIOS PROVEEDOR para Asiento(64) ===')
for pp in r3.json():
    print('proveedor_id=%s producto_id=%s precio_kg=%s' % (pp['proveedor_id'], pp['producto_id'], pp['precio_kg']))
