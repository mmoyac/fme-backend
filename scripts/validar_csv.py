"""
Script para validar archivos CSV del cliente antes de importar.
Verifica formato, integridad referencial y reglas de negocio.
"""
import csv
import sys
from pathlib import Path
from typing import Dict, List, Set

class ValidadorCSV:
    def __init__(self, carpeta_csv: str):
        self.carpeta = Path(carpeta_csv)
        self.errores: List[str] = []
        self.warnings: List[str] = []
        
        # Datos cargados
        self.productos: Dict[str, dict] = {}
        self.locales: Dict[str, dict] = {}
        self.inventarios: List[dict] = []
        self.precios: List[dict] = []
    
    def validar_todo(self) -> bool:
        """Ejecuta todas las validaciones. Retorna True si todo OK."""
        print("\n" + "="*70)
        print("  VALIDACIÓN DE ARCHIVOS CSV")
        print("="*70 + "\n")
        
        # 1. Verificar que existen los archivos
        if not self._verificar_archivos():
            return False
        
        # 2. Cargar y validar productos
        if not self._validar_productos():
            return False
        
        # 3. Cargar y validar locales
        if not self._validar_locales():
            return False
        
        # 4. Validar inventario
        if not self._validar_inventario():
            return False
        
        # 5. Validar precios
        if not self._validar_precios():
            return False
        
        # 6. Validaciones de negocio
        self._validaciones_negocio()
        
        # Mostrar resultado
        self._mostrar_resultado()
        
        return len(self.errores) == 0
    
    def _verificar_archivos(self) -> bool:
        """Verifica que existan los 4 archivos requeridos."""
        archivos_requeridos = [
            'productos.csv',
            'locales.csv',
            'inventario_inicial.csv',
            'precios.csv'
        ]
        
        for archivo in archivos_requeridos:
            ruta = self.carpeta / archivo
            if not ruta.exists():
                self.errores.append(f"❌ Archivo faltante: {archivo}")
        
        return len(self.errores) == 0
    
    def _validar_productos(self) -> bool:
        """Valida productos.csv"""
        print("📦 Validando productos.csv...")
        
        archivo = self.carpeta / 'productos.csv'
        
        try:
            with open(archivo, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                
                # Verificar columnas requeridas
                columnas_req = {'sku', 'nombre', 'descripcion', 'categoria_id', 'unidad_medida'}
                columnas_archivo = set(c.strip().lower() for c in reader.fieldnames or [])
                
                faltantes = columnas_req - columnas_archivo
                if faltantes:
                    self.errores.append(f"❌ productos.csv: Columnas faltantes: {faltantes}")
                    return False
                
                # Validar cada fila
                for i, row in enumerate(reader, start=2):
                    sku = row.get('sku', '').strip()
                    nombre = row.get('nombre', '').strip()
                    categoria_id = row.get('categoria_id', '').strip()
                    
                    if not sku:
                        self.errores.append(f"❌ productos.csv línea {i}: SKU vacío")
                    
                    if not nombre:
                        self.errores.append(f"❌ productos.csv línea {i}: Nombre vacío")
                    
                    if not categoria_id.isdigit():
                        self.errores.append(f"❌ productos.csv línea {i}: categoria_id debe ser número (1-6)")
                    elif int(categoria_id) not in range(1, 7):
                        self.errores.append(f"❌ productos.csv línea {i}: categoria_id debe estar entre 1 y 6")
                    
                    # Verificar SKU único
                    if sku in self.productos:
                        self.errores.append(f"❌ productos.csv línea {i}: SKU duplicado: {sku}")
                    else:
                        self.productos[sku] = row
                
                print(f"   ✅ {len(self.productos)} productos cargados")
                return True
                
        except Exception as e:
            self.errores.append(f"❌ Error leyendo productos.csv: {e}")
            return False
    
    def _validar_locales(self) -> bool:
        """Valida locales.csv"""
        print("🏪 Validando locales.csv...")
        
        archivo = self.carpeta / 'locales.csv'
        
        try:
            with open(archivo, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                
                columnas_req = {'codigo', 'nombre', 'direccion', 'tipo'}
                columnas_archivo = set(c.strip().lower() for c in reader.fieldnames or [])
                
                faltantes = columnas_req - columnas_archivo
                if faltantes:
                    self.errores.append(f"❌ locales.csv: Columnas faltantes: {faltantes}")
                    return False
                
                tiene_web = False
                
                for i, row in enumerate(reader, start=2):
                    codigo = row.get('codigo', '').strip()
                    nombre = row.get('nombre', '').strip()
                    tipo = row.get('tipo', '').strip().upper()
                    
                    if not codigo:
                        self.errores.append(f"❌ locales.csv línea {i}: Código vacío")
                    
                    if tipo not in ['ECOMMERCE', 'TIENDA_FISICA']:
                        self.errores.append(f"❌ locales.csv línea {i}: tipo debe ser ECOMMERCE o TIENDA_FISICA")
                    
                    if codigo == 'WEB' and tipo == 'ECOMMERCE':
                        tiene_web = True
                    
                    if codigo in self.locales:
                        self.errores.append(f"❌ locales.csv línea {i}: Código duplicado: {codigo}")
                    else:
                        self.locales[codigo] = row
                
                if not tiene_web:
                    self.warnings.append("⚠️  No hay local WEB (código='WEB', tipo='ECOMMERCE'). Sin esto no funciona la landing page.")
                
                print(f"   ✅ {len(self.locales)} locales cargados")
                return True
                
        except Exception as e:
            self.errores.append(f"❌ Error leyendo locales.csv: {e}")
            return False
    
    def _validar_inventario(self) -> bool:
        """Valida inventario_inicial.csv"""
        print("📊 Validando inventario_inicial.csv...")
        
        archivo = self.carpeta / 'inventario_inicial.csv'
        
        try:
            with open(archivo, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                
                columnas_req = {'producto_sku', 'local_codigo', 'cantidad_stock'}
                columnas_archivo = set(c.strip().lower() for c in reader.fieldnames or [])
                
                faltantes = columnas_req - columnas_archivo
                if faltantes:
                    self.errores.append(f"❌ inventario_inicial.csv: Columnas faltantes: {faltantes}")
                    return False
                
                for i, row in enumerate(reader, start=2):
                    sku = row.get('producto_sku', '').strip()
                    local = row.get('local_codigo', '').strip()
                    stock = row.get('cantidad_stock', '').strip()
                    
                    # Validar que exista el producto
                    if sku not in self.productos:
                        self.errores.append(f"❌ inventario_inicial.csv línea {i}: SKU '{sku}' no existe en productos.csv")
                    
                    # Validar que exista el local
                    if local not in self.locales:
                        self.errores.append(f"❌ inventario_inicial.csv línea {i}: Local '{local}' no existe en locales.csv")
                    
                    # Validar que sea local físico (no WEB)
                    if local == 'WEB':
                        self.errores.append(f"❌ inventario_inicial.csv línea {i}: No incluir local WEB (se calcula automático)")
                    
                    # Validar cantidad numérica
                    if not stock.replace('.', '', 1).isdigit():
                        self.errores.append(f"❌ inventario_inicial.csv línea {i}: cantidad_stock debe ser número")
                    
                    self.inventarios.append(row)
                
                print(f"   ✅ {len(self.inventarios)} registros de inventario cargados")
                return True
                
        except Exception as e:
            self.errores.append(f"❌ Error leyendo inventario_inicial.csv: {e}")
            return False
    
    def _validar_precios(self) -> bool:
        """Valida precios.csv"""
        print("💰 Validando precios.csv...")
        
        archivo = self.carpeta / 'precios.csv'
        
        try:
            with open(archivo, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                
                columnas_req = {'producto_sku', 'local_codigo', 'monto_precio'}
                columnas_archivo = set(c.strip().lower() for c in reader.fieldnames or [])
                
                faltantes = columnas_req - columnas_archivo
                if faltantes:
                    self.errores.append(f"❌ precios.csv: Columnas faltantes: {faltantes}")
                    return False
                
                productos_con_precio_web: Set[str] = set()
                
                for i, row in enumerate(reader, start=2):
                    sku = row.get('producto_sku', '').strip()
                    local = row.get('local_codigo', '').strip()
                    precio = row.get('monto_precio', '').strip()
                    
                    # Validar que exista el producto
                    if sku not in self.productos:
                        self.errores.append(f"❌ precios.csv línea {i}: SKU '{sku}' no existe en productos.csv")
                    
                    # Validar que exista el local
                    if local not in self.locales:
                        self.errores.append(f"❌ precios.csv línea {i}: Local '{local}' no existe en locales.csv")
                    
                    # Validar precio numérico y positivo
                    if not precio.replace('.', '', 1).isdigit():
                        self.errores.append(f"❌ precios.csv línea {i}: monto_precio debe ser número")
                    elif float(precio) <= 0:
                        self.errores.append(f"❌ precios.csv línea {i}: monto_precio debe ser mayor a 0")
                    
                    # Registrar productos con precio WEB
                    if local == 'WEB':
                        productos_con_precio_web.add(sku)
                    
                    self.precios.append(row)
                
                # Validar que todos los productos tengan precio WEB
                if 'WEB' in self.locales:
                    productos_sin_precio_web = set(self.productos.keys()) - productos_con_precio_web
                    if productos_sin_precio_web:
                        self.warnings.append(f"⚠️  Productos sin precio en local WEB: {productos_sin_precio_web}")
                
                print(f"   ✅ {len(self.precios)} precios cargados")
                return True
                
        except Exception as e:
            self.errores.append(f"❌ Error leyendo precios.csv: {e}")
            return False
    
    def _validaciones_negocio(self):
        """Validaciones adicionales de reglas de negocio"""
        print("🔍 Validaciones de negocio...")
        
        # Verificar que cada producto tenga al menos un precio
        productos_sin_precio = set(self.productos.keys())
        for precio in self.precios:
            productos_sin_precio.discard(precio.get('producto_sku', '').strip())
        
        if productos_sin_precio:
            self.errores.append(f"❌ Productos sin ningún precio definido: {productos_sin_precio}")
        
        print("   ✅ Validaciones de negocio completadas")
    
    def _mostrar_resultado(self):
        """Muestra el resultado final de las validaciones"""
        print("\n" + "="*70)
        print("  RESULTADO DE VALIDACIÓN")
        print("="*70)
        
        if self.errores:
            print("\n❌ ERRORES ENCONTRADOS:\n")
            for error in self.errores:
                print(f"  {error}")
        
        if self.warnings:
            print("\n⚠️  ADVERTENCIAS:\n")
            for warning in self.warnings:
                print(f"  {warning}")
        
        print("\n" + "="*70)
        
        if not self.errores:
            print("✅ VALIDACIÓN EXITOSA - Archivos listos para importar")
        else:
            print(f"❌ VALIDACIÓN FALLIDA - {len(self.errores)} errores encontrados")
        
        print("="*70 + "\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python validar_csv.py <carpeta_con_csvs>")
        print("Ejemplo: python validar_csv.py ./datos_cliente")
        sys.exit(1)
    
    carpeta = sys.argv[1]
    validador = ValidadorCSV(carpeta)
    
    if validador.validar_todo():
        sys.exit(0)
    else:
        sys.exit(1)
