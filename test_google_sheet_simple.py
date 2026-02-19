"""
Script simple para leer Google Sheet público sin autenticación.
Solo funciona si el sheet tiene permisos de "cualquiera con el enlace puede VER".
"""
import requests
import csv
from io import StringIO

# ID del Google Sheet (extraído del URL)
SHEET_ID = "1acE1CN_1foFi16a7eF2xCXaq8es2gSKMfu-paUaubZM"
SHEET_NAME = "productos"  # Nombre de la pestaña

# URL para exportar como CSV
url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"

print(f"🔗 Intentando leer: {SHEET_NAME}")
print(f"📄 URL: {url}\n")

try:
    response = requests.get(url)
    response.raise_for_status()
    
    # Parsear CSV
    csv_data = StringIO(response.text)
    reader = csv.DictReader(csv_data)
    
    productos = list(reader)
    
    print(f"✅ ÉXITO! Se leyeron {len(productos)} productos\n")
    print("=" * 100)
    
    # Mostrar los productos
    for i, producto in enumerate(productos, 1):
        print(f"\n📦 Producto {i}:")
        print(f"   SKU: {producto.get('sku', 'N/A')}")
        print(f"   Nombre: {producto.get('nombre', 'N/A')}")
        print(f"   Categoría ID: {producto.get('categoria_id', 'N/A')}")
        print(f"   Tipo Producto ID: {producto.get('tipo_producto_id', 'N/A')}")
        print(f"   Unidad Medida ID: {producto.get('unidad_medida_id', 'N/A')}")
    
    print("\n" + "=" * 100)
    print(f"✅ Total: {len(productos)} productos leídos correctamente")
    
except requests.exceptions.RequestException as e:
    print(f"❌ ERROR: No se pudo acceder al sheet")
    print(f"   Detalle: {e}")
    print("\n💡 Posibles causas:")
    print("   1. El sheet NO está compartido como 'cualquiera con el enlace puede VER'")
    print("   2. El nombre de la pestaña no es exactamente 'productos'")
    print("   3. Problema de conexión a internet")
    print("\n🔧 Solución: Verifica los permisos de compartir del Google Sheet")

except Exception as e:
    print(f"❌ ERROR inesperado: {e}")
