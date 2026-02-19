"""
Ver qué datos está leyendo el script de las hojas precios e inventario.
"""
import requests
import csv
from io import StringIO

SHEET_ID = "1acE1CN_1foFi16a7eF2xCXaq8es2gSKMfu-paUaubZM"

def leer_hoja(sheet_name):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        csv_data = StringIO(response.text)
        reader = csv.DictReader(csv_data)
        return list(reader)
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return []

print("=" * 100)
print("HOJA: precios")
print("=" * 100)
precios = leer_hoja("precios")
if precios:
    print(f"Registros: {len(precios)}")
    print(f"Columnas: {list(precios[0].keys())}")
    print("\nDatos:")
    for i, p in enumerate(precios, 1):
        print(f"  {i}. {p}")
else:
    print("⚠️  Vacía o error")

print("\n" + "=" * 100)
print("HOJA: inventario")
print("=" * 100)
inventario = leer_hoja("inventario")
if inventario:
    print(f"Registros: {len(inventario)}")
    print(f"Columnas: {list(inventario[0].keys())}")
    print("\nDatos:")
    for i, inv in enumerate(inventario, 1):
        print(f"  {i}. {inv}")
else:
    print("⚠️  Vacía o error")
