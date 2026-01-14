#!/usr/bin/env python3
"""
Script para automatizar el deploy desde cero de un nuevo cliente.
Uso: python scripts/deploy_nuevo_cliente.py --tipo panaderia --nombre "Panadería San Juan" --email admin@panaderiasanjuan.cl
"""
import argparse
import sys
import os
import csv
import requests
from datetime import datetime

# URL base (cambiar según entorno)
BASE_URL = "http://localhost:8000"  # Para desarrollo
# BASE_URL = "https://api.masasestacion.cl"  # Para producción

def print_step(step, message):
    """Imprime paso con formato."""
    print(f"\n{step} {message}")

def print_success(message):
    """Imprime éxito."""
    print(f"✅ {message}")

def print_error(message):
    """Imprime error."""
    print(f"❌ {message}")

def print_warning(message):
    """Imprime advertencia."""
    print(f"⚠️ {message}")

def login_admin(session):
    """Login con usuario admin inicial."""
    print_step("🔐", "Logueando como admin...")
    
    # Primero intentar login normal
    login_data = {
        "username": "admin@fme.cl",
        "password": "admin"
    }
    
    resp = session.post(f"{BASE_URL}/api/auth/token", data=login_data)
    if resp.status_code == 200:
        token = resp.json()["access_token"]
        session.headers.update({"Authorization": f"Bearer {token}"})
        print_success("Login exitoso con admin existente")
        return True
    
    # Si no existe, crear admin inicial
    print_warning("Admin no existe, creando admin inicial...")
    create_admin_data = {
        "email": "admin@fme.cl",
        "password": "admin",
        "nombre_completo": "Super Admin",
        "role_id": 1
    }
    
    resp = session.post(f"{BASE_URL}/api/auth/setup/create_admin", json=create_admin_data)
    if resp.status_code == 200:
        print_success("Admin inicial creado")
        return login_admin(session)  # Intentar login nuevamente
    else:
        print_error(f"No se pudo crear admin inicial: {resp.status_code} - {resp.text}")
        return False

def seed_sistema_base(session):
    """Ejecuta seed de tablas maestras del sistema."""
    print_step("📋", "Configurando sistema base...")
    
    # Verificar si ya existen datos maestros
    resp = session.get(f"{BASE_URL}/api/admin/categorias")
    if resp.status_code == 200 and len(resp.json()) > 0:
        print_warning("Datos maestros ya existen, omitiendo seed...")
        return True
    
    # Aquí deberías llamar a tus scripts de seed existentes
    # Por simplicidad, asumo que se ejecutan externamente
    print_success("Configuración base completada (ejecutar scripts de seed manualmente)")
    return True

def crear_locales_cliente(session, tipo_negocio, nombre_cliente):
    """Crea los locales específicos del cliente."""
    print_step("🏪", f"Creando locales para {nombre_cliente}...")
    
    csv_path = f"docs/deploy_templates/{tipo_negocio}/locales_{tipo_negocio}.csv"
    
    if not os.path.exists(csv_path):
        print_error(f"Archivo CSV no encontrado: {csv_path}")
        return False
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Personalizar nombre del local matriz
                nombre_local = row['nombre']
                if 'Principal' in nombre_local or 'Central' in nombre_local:
                    nombre_local = nombre_local.replace('Principal', nombre_cliente)
                    nombre_local = nombre_local.replace('Central', nombre_cliente)
                
                local_data = {
                    "codigo": row['codigo'],
                    "nombre": nombre_local,
                    "direccion": row['direccion'],
                    "activo": True
                }
                
                resp = session.post(f"{BASE_URL}/api/locales/", json=local_data)
                if resp.status_code in [200, 201]:
                    print_success(f"Local creado: {nombre_local}")
                else:
                    print_error(f"Error creando local {nombre_local}: {resp.status_code} - {resp.text}")
        
        return True
    except Exception as e:
        print_error(f"Error leyendo CSV de locales: {e}")
        return False

def importar_productos_cliente(session, tipo_negocio):
    """Importa productos específicos del cliente."""
    print_step("📦", "Importando productos...")
    
    csv_path = f"docs/deploy_templates/{tipo_negocio}/productos_{tipo_negocio}.csv"
    
    if not os.path.exists(csv_path):
        print_error(f"Archivo CSV no encontrado: {csv_path}")
        return False
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                producto_data = {
                    "nombre": row['nombre'],
                    "descripcion": row['descripcion'],
                    "sku": row['sku'],
                    "categoria_id": 1,  # Simplificado, debería mapear categoria_codigo
                    "tipo_producto_id": 1,  # Simplificado
                    "unidad_medida_id": 1,  # Simplificado
                    "es_vendible": True,
                    "es_vendible_web": row.get('es_vendible_web', 'true').lower() == 'true',
                    "stock_minimo": int(row.get('stock_minimo', '0')),
                    "activo": True
                }
                
                resp = session.post(f"{BASE_URL}/api/productos/", json=producto_data)
                if resp.status_code in [200, 201]:
                    producto_id = resp.json()["id"]
                    print_success(f"Producto creado: {row['nombre']}")
                    
                    # Crear precio para local WEB
                    precio_data = {
                        "producto_id": producto_id,
                        "local_id": 1,  # Asumiendo que WEB es ID=1
                        "monto_precio": float(row.get('precio_web', '0'))
                    }
                    
                    resp_precio = session.post(f"{BASE_URL}/api/precios/", json=precio_data)
                    if resp_precio.status_code in [200, 201]:
                        print_success(f"  ↳ Precio configurado: ${row.get('precio_web', '0')}")
                    
                else:
                    print_error(f"Error creando producto {row['nombre']}: {resp.status_code} - {resp.text}")
        
        return True
    except Exception as e:
        print_error(f"Error leyendo CSV de productos: {e}")
        return False

def crear_admin_cliente(session, email_cliente, password_cliente, nombre_cliente):
    """Crea el usuario admin específico del cliente."""
    print_step("👤", "Creando usuario admin del cliente...")
    
    admin_data = {
        "email": email_cliente,
        "password": password_cliente,
        "nombre_completo": f"Administrador {nombre_cliente}",
        "activo": True,
        "role_id": 1  # Admin role
    }
    
    resp = session.post(f"{BASE_URL}/api/admin/users", json=admin_data)
    if resp.status_code in [200, 201]:
        print_success(f"Admin creado: {email_cliente}")
        return True
    else:
        print_error(f"Error creando admin: {resp.status_code} - {resp.text}")
        return False

def generar_reporte_deploy(nombre_cliente, tipo_negocio, email_admin):
    """Genera un reporte del deploy realizado."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    reporte_path = f"docs/deploy_reports/deploy_{nombre_cliente.replace(' ', '_')}_{timestamp}.md"
    
    os.makedirs("docs/deploy_reports", exist_ok=True)
    
    reporte = f"""# 📋 REPORTE DE DEPLOY - {nombre_cliente}

**Fecha:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Tipo de Negocio:** {tipo_negocio.title()}
**Cliente:** {nombre_cliente}
**Admin Email:** {email_admin}

## ✅ Deploy Completado

### Datos Cargados:
- ✅ Sistema base configurado
- ✅ Locales específicos del cliente
- ✅ Productos del tipo de negocio: {tipo_negocio}
- ✅ Precios configurados para tienda online
- ✅ Usuario admin del cliente creado

### Archivos Utilizados:
- `docs/deploy_templates/{tipo_negocio}/locales_{tipo_negocio}.csv`
- `docs/deploy_templates/{tipo_negocio}/productos_{tipo_negocio}.csv`

### Acceso al Sistema:
- **URL:** {BASE_URL.replace('api.', 'admin.')}
- **Usuario:** {email_admin}
- **Contraseña:** [definida durante el proceso]

### Próximos Pasos:
1. Configurar inventario inicial por local
2. Ajustar precios si es necesario
3. Configurar medios de pago
4. Probar flujo completo de pedidos

---
*Deploy automatizado realizado con deploy_nuevo_cliente.py*
"""
    
    with open(reporte_path, 'w', encoding='utf-8') as file:
        file.write(reporte)
    
    print_success(f"Reporte generado: {reporte_path}")

def main():
    parser = argparse.ArgumentParser(description='Deploy automático para nuevo cliente')
    parser.add_argument('--tipo', required=True, 
                       choices=['panaderia', 'carniceria', 'lacteos'],
                       help='Tipo de negocio del cliente')
    parser.add_argument('--nombre', required=True, 
                       help='Nombre del cliente/negocio')
    parser.add_argument('--email', required=True, 
                       help='Email del admin del cliente')
    parser.add_argument('--password', default='admin123',
                       help='Password del admin (default: admin123)')
    
    args = parser.parse_args()
    
    print(f"\n🚀 INICIANDO DEPLOY PARA: {args.nombre}")
    print(f"   Tipo de Negocio: {args.tipo.title()}")
    print(f"   Admin Email: {args.email}")
    print(f"   Base URL: {BASE_URL}")
    
    session = requests.Session()
    
    try:
        # 1. Login inicial
        if not login_admin(session):
            print_error("No se pudo establecer sesión de admin")
            sys.exit(1)
        
        # 2. Configurar sistema base
        if not seed_sistema_base(session):
            print_error("Error configurando sistema base")
            sys.exit(1)
        
        # 3. Crear locales
        if not crear_locales_cliente(session, args.tipo, args.nombre):
            print_error("Error creando locales")
            sys.exit(1)
        
        # 4. Importar productos
        if not importar_productos_cliente(session, args.tipo):
            print_error("Error importando productos")
            sys.exit(1)
        
        # 5. Crear admin del cliente
        if not crear_admin_cliente(session, args.email, args.password, args.nombre):
            print_error("Error creando admin del cliente")
            sys.exit(1)
        
        # 6. Generar reporte
        generar_reporte_deploy(args.nombre, args.tipo, args.email)
        
        print(f"\n🎉 DEPLOY COMPLETADO EXITOSAMENTE PARA: {args.nombre}")
        print(f"   ✅ Acceso: {args.email} / {args.password}")
        print(f"   ✅ Sistema listo para usar")
        
    except KeyboardInterrupt:
        print_error("\nDeploy interrumpido por usuario")
        sys.exit(1)
    except Exception as e:
        print_error(f"Error inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()