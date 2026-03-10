import requests

r = requests.post('http://localhost:8000/api/auth/token', data={'username':'admin@elquincho.com','password':'admin123'})
token = r.json()['access_token']
h = {'Authorization': 'Bearer ' + token}

# 1. Ver todos los precios con proveedores cruzados (proveedor de otro tenant)
print('=== Precios proveedor actuales para tenant 9 ===')
r2 = requests.get('http://localhost:8000/api/precios-proveedor/?solo_activos=false&limit=1000', headers=h)
for pp in r2.json():
    print('id=%s producto_id=%s proveedor_id=%s proveedor=%s precio_kg=%s activo=%s' % (
        pp['id'], pp['producto_id'], pp['proveedor_id'], pp['proveedor_nombre'], pp['precio_kg'], pp['activo']))

# 2. Desactivar los precios con proveedor de otro tenant (ids 11, 13, 32 identificados)
# id=11 -> proveedor_id=1 (Valentina Chavez, otro tenant), producto=62
# id=13 -> proveedor_id=1 (Valentina Chavez), producto=64 (Asiento)
# id=32 -> proveedor_id=51 (PULS, tenant 2), producto=64 (Asiento)
print('\n=== Desactivando precios con proveedores cross-tenant ===')
for bad_id in [11, 13, 32]:
    rd = requests.delete('http://localhost:8000/api/precios-proveedor/%d' % bad_id, headers=h)
    print('DELETE id=%d -> %d %s' % (bad_id, rd.status_code, rd.text[:100]))

# 3. Crear precio correcto: Asiento (64) + Pampa (54) = 9100
print('\n=== Creando precio correcto: Asiento + Pampa ===')
payload = {'producto_id': 64, 'proveedor_id': 54, 'precio_kg': 9100.0}
rc = requests.post('http://localhost:8000/api/precios-proveedor/', json=payload, headers=h)
print('POST -> %d %s' % (rc.status_code, rc.text[:200]))

# 4. Verificar resultado
print('\n=== Estado final precios para producto 64 (Asiento) ===')
r3 = requests.get('http://localhost:8000/api/precios-proveedor/?producto_id=64', headers=h)
for pp in r3.json():
    print('proveedor_id=%s proveedor=%s precio_kg=%s' % (pp['proveedor_id'], pp['proveedor_nombre'], pp['precio_kg']))
