import requests
import json

resp = requests.get('https://api.masasestacion.cl/api/maestras/categorias', params={'tenant_id': 1})

print("=" * 80)
print(f"Status Code: {resp.status_code}")
print("=" * 80)

if resp.status_code == 200:
    categorias = resp.json()
    print(f"Total categorías: {len(categorias)}\n")
    for c in categorias:
        print(f"  ID {c['id']:>3}: {c['nombre']}")
else:
    print("Response:")
    print(json.dumps(resp.json(), indent=2, ensure_ascii=False))
