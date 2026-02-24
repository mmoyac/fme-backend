import requests
import csv
from io import StringIO

SHEET_ID = "1acE1CN_1foFi16a7eF2xCXaq8es2gSKMfu-paUaubZM"

# Intentar leer hoja "Categorias"
url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Categorias"
response = requests.get(url)

print("=" * 80)
print(f"Status Code: {response.status_code}")
print("=" * 80)

if response.status_code == 200:
    csv_data = StringIO(response.text)
    reader = csv.DictReader(csv_data)
    
    # Leer datos
    categorias = []
    for row in reader:
        clean_row = {}
        for key, value in row.items():
            clean_key = key.strip().lstrip('#').strip()
            clean_row[clean_key] = value
        if any(clean_row.values()):  # Saltar filas vacías
            categorias.append(clean_row)
    
    print(f"✅ Hoja 'Categorias' encontrada: {len(categorias)} registros\n")
    print("Columnas:", list(categorias[0].keys()) if categorias else "N/A")
    print("\nPrimeras 5 categorías:")
    for i, cat in enumerate(categorias[:5], 1):
        print(f"  {i}. {cat}")
else:
    print("❌ Hoja 'Categorias' no encontrada")
    print("Response:", response.text[:200])
