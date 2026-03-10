import requests

r = requests.post('http://localhost:8000/api/auth/token', data={'username':'admin@elquincho.com','password':'admin123'})
token = r.json()['access_token']
h = {'Authorization': 'Bearer ' + token}

# Ver a que tenant pertenece proveedor 51 y 1
r_admin = requests.post('http://localhost:8000/api/auth/token', data={'username':'admin@masasestacion.cl','password':'admin'})
if r_admin.status_code == 200:
    token_admin = r_admin.json()['access_token']
    h_admin = {'Authorization': 'Bearer ' + token_admin}
    r2 = requests.get('http://localhost:8000/api/compras/proveedores', headers=h_admin)
    print('=== Proveedores tenant 1 (admin general) ===')
    for p in r2.json():
        print('id=%s nombre=%s rut=%s tenant_id=%s' % (p['id'], p['nombre'], p['rut'], p.get('tenant_id','-')))

# tenant 2 (El Olivo)
r_olivo = requests.post('http://localhost:8000/api/auth/token', data={'username':'admin@elolivo.cl','password':'admin'})
if r_olivo.status_code == 200:
    token_olivo = r_olivo.json()['access_token']
    h_olivo = {'Authorization': 'Bearer ' + token_olivo}
    r3 = requests.get('http://localhost:8000/api/compras/proveedores', headers=h_olivo)
    print('\n=== Proveedores tenant 2 (El Olivo) ===')
    for p in r3.json():
        print('id=%s nombre=%s rut=%s' % (p['id'], p['nombre'], p['rut']))

# Precios proveedor para producto 64 - sin filtro tenant (como admin general si es posible)
print('\n=== precios_proveedor producto 64 (desde tenant 9) ===')
r4 = requests.get('http://localhost:8000/api/precios-proveedor/?producto_id=64', headers=h)
for pp in r4.json():
    print('id=%s proveedor_id=%s proveedor_nombre=%s precio_kg=%s' % (pp['id'], pp['proveedor_id'], pp['proveedor_nombre'], pp['precio_kg']))
