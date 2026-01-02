import requests

session = requests.Session()
resp = session.post('http://localhost:8000/api/auth/token', data={'username': 'admin@fme.cl', 'password': 'admin'})
token = resp.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

resp = session.get('http://localhost:8000/api/admin/menu_items', headers=headers)
items = resp.json()

print('🎛️ Items de Menú Disponibles:')
for item in sorted(items, key=lambda x: x.get('orden', 999)):
    print(f'  {item["orden"]:2d}. {item["nombre"]:15} -> {item["href"]:25} {item["icon"]}')

print('\n✅ Total de items:', len(items))