import requests, csv
from io import StringIO

SHEET_ID = "1acE1CN_1foFi16a7eF2xCXaq8es2gSKMfu-paUaubZM"
url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=productos"
r = requests.get(url)
found = False
for row in csv.DictReader(StringIO(r.text)):
    clean = {k.strip().lstrip("#").strip(): v for k, v in row.items()}
    sku = clean.get("sku", "").strip()
    if sku == "10068":
        found = True
        print("Fila encontrada:")
        for k, v in clean.items():
            print(f"  {k}: {repr(v)}")
        break
if not found:
    print("SKU 10068 NO encontrado en el sheet")
