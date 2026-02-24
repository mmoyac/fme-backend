import requests
import csv
from io import StringIO
from collections import Counter

SHEET_ID = "1acE1CN_1foFi16a7eF2xCXaq8es2gSKMfu-paUaubZM"

# Leer hoja de productos
url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=productos"
response = requests.get(url)
csv_data = StringIO(response.text)
reader = csv.DictReader(csv_data)

productos = []
for row in reader:
    clean_row = {}
    for key, value in row.items():
        clean_key = key.strip().lstrip('#').strip()
        clean_row[clean_key] = value
    productos.append(clean_row)

# Contar categoria_id
categoria_counts = Counter()
for p in productos:
    cat_id = p.get('categoria_id', '').strip()
    if cat_id:
        categoria_counts[cat_id] += 1

print("=" * 80)
print("CATEGORIA_ID EN GOOGLE SHEET (productos):")
print("=" * 80)
for cat_id, count in sorted(categoria_counts.items(), key=lambda x: int(x[0] if x[0].isdigit() else 999)):
    print(f"  categoria_id {cat_id:>3}: {count:>3} productos")
print("=" * 80)
print(f"Total productos en sheet: {len(productos)}")

# Categorías válidas en producción
categorias_validas = {1, 2, 3, 4, 5}
print("\n" + "=" * 80)
print("DIAGNÓSTICO:")
print("=" * 80)
print(f"Categorías válidas en producción: {categorias_validas}")

productos_invalidos = []
for p in productos:
    cat_id = p.get('categoria_id', '').strip()
    if cat_id and int(cat_id) not in categorias_validas:
        productos_invalidos.append({
            'sku': p.get('sku', ''),
            'nombre': p.get('nombre', ''),
            'categoria_id': cat_id
        })

if productos_invalidos:
    print(f"\n❌ {len(productos_invalidos)} productos con categoria_id INVÁLIDA:")
    for p in productos_invalidos[:10]:  # primeros 10
        print(f"   SKU {p['sku']}: {p['nombre'][:50]} (categoria_id={p['categoria_id']})")
    if len(productos_invalidos) > 10:
        print(f"   ... y {len(productos_invalidos) - 10} más")
else:
    print("\n✅ Todos los productos tienen categoria_id válida")
