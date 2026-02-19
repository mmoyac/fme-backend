"""
Script para generar un paquete ZIP con los templates CSV para onboarding de nuevos tenants.

Uso:
    python scripts/generate_templates_zip.py
    
Genera: templates_csv.zip con todos los archivos de ejemplo
"""

import zipfile
from pathlib import Path


def generar_templates_zip():
    """Genera un archivo ZIP con todos los templates CSV."""
    
    templates_dir = Path(__file__).parent.parent / "templates_csv"
    output_file = Path(__file__).parent.parent / "templates_onboarding_tenant.zip"
    
    # Archivos a incluir
    archivos = [
        "README.md",
        "tenant_config.csv",
        "locales.csv",
        "productos.csv",
        "precios.csv",
        "inventario.csv",
        "usuarios.csv"
    ]
    
    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for archivo in archivos:
            filepath = templates_dir / archivo
            if filepath.exists():
                zipf.write(filepath, arcname=f"onboarding_tenant/{archivo}")
                print(f"✅ Agregado: {archivo}")
            else:
                print(f"⚠️ No encontrado: {archivo}")
    
    print(f"\n✅ ZIP generado: {output_file}")
    print(f"📦 Tamaño: {output_file.stat().st_size / 1024:.2f} KB")
    return output_file


if __name__ == "__main__":
    generar_templates_zip()
