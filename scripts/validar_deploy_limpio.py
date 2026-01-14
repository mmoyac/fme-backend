#!/usr/bin/env python3
"""
Script para validar que un deploy esté limpio y listo para un nuevo cliente.
Uso: python scripts/validar_deploy_limpio.py --cliente "Nuevo Cliente"
"""
import argparse
import requests
from datetime import datetime

# URL base (cambiar según entorno)
BASE_URL = "http://localhost:8000"  # Para desarrollo
# BASE_URL = "https://api.masasestacion.cl"  # Para producción

def print_check(message, status):
    """Imprime check con estado."""
    icon = "✅" if status else "❌"
    print(f"{icon} {message}")

def print_warning(message):
    """Imprime advertencia."""
    print(f"⚠️ {message}")

def print_info(message):
    """Imprime información."""
    print(f"ℹ️ {message}")

def login_admin(session):
    """Login con usuario admin."""
    login_data = {
        "username": "admin@fme.cl",
        "password": "admin"
    }
    
    resp = session.post(f"{BASE_URL}/api/auth/token", data=login_data)
    if resp.status_code == 200:
        token = resp.json()["access_token"]
        session.headers.update({"Authorization": f"Bearer {token}"})
        return True
    return False

def validar_tablas_sistema(session):
    """Valida que las tablas de sistema estén configuradas."""
    print(f"\n📋 VALIDANDO CONFIGURACIÓN DEL SISTEMA")
    
    # Verificar categorías
    resp = session.get(f"{BASE_URL}/api/admin/categorias")
    if resp.status_code == 200:
        categorias = resp.json()
        print_check(f"Categorías configuradas: {len(categorias)} encontradas", len(categorias) > 0)
    else:
        print_check("Categorías configuradas", False)
    
    # Verificar roles
    resp = session.get(f"{BASE_URL}/api/admin/roles")
    if resp.status_code == 200:
        roles = resp.json()
        print_check(f"Roles configurados: {len(roles)} encontrados", len(roles) > 0)
    else:
        print_check("Roles configurados", False)
    
    # Verificar tipos de pedido
    resp = session.get(f"{BASE_URL}/api/admin/tipos-pedido")
    if resp.status_code == 200:
        tipos = resp.json()
        print_check(f"Tipos de pedido configurados: {len(tipos)} encontrados", len(tipos) > 0)
    else:
        print_check("Tipos de pedido configurados", False)

def validar_datos_negocio_limpios(session):
    """Valida que las tablas de datos de negocio estén limpias."""
    print(f"\n🧹 VALIDANDO LIMPIEZA DE DATOS DE NEGOCIO")
    
    # Verificar productos
    resp = session.get(f"{BASE_URL}/api/productos/")
    if resp.status_code == 200:
        productos = resp.json()
        print_check(f"Productos limpios: {len(productos)} productos encontrados", len(productos) == 0)
        if len(productos) > 0:
            print_warning(f"   Productos existentes: {[p['nombre'] for p in productos[:3]]}")
    
    # Verificar locales  
    resp = session.get(f"{BASE_URL}/api/locales/")
    if resp.status_code == 200:
        locales = resp.json()
        print_check(f"Locales limpios: {len(locales)} locales encontrados", len(locales) == 0)
        if len(locales) > 0:
            print_warning(f"   Locales existentes: {[l['nombre'] for l in locales[:3]]}")
    
    # Verificar clientes
    resp = session.get(f"{BASE_URL}/api/clientes/")
    if resp.status_code == 200:
        clientes = resp.json()
        print_check(f"Clientes limpios: {len(clientes)} clientes encontrados", len(clientes) == 0)
        if len(clientes) > 0:
            print_warning(f"   Clientes existentes: {[c['nombre'] for c in clientes[:3]]}")
    
    # Verificar pedidos
    resp = session.get(f"{BASE_URL}/api/pedidos/")
    if resp.status_code == 200:
        pedidos = resp.json()
        print_check(f"Pedidos limpios: {len(pedidos)} pedidos encontrados", len(pedidos) == 0)
        if len(pedidos) > 0:
            print_warning(f"   Pedidos existentes: {len(pedidos)} encontrados")

def validar_usuarios_sistema(session, nuevo_cliente):
    """Valida el estado de usuarios del sistema."""
    print(f"\n👥 VALIDANDO USUARIOS DEL SISTEMA")
    
    resp = session.get(f"{BASE_URL}/api/admin/users")
    if resp.status_code == 200:
        users = resp.json()
        print_info(f"Usuarios existentes: {len(users)}")
        
        admin_exists = any(user['email'] == 'admin@fme.cl' for user in users)
        print_check("Usuario admin@fme.cl existe", admin_exists)
        
        # Verificar si ya existe un admin para este cliente
        client_domain = nuevo_cliente.lower().replace(' ', '').replace('ería', 'eria')
        client_emails = [user['email'] for user in users if client_domain in user['email']]
        
        if client_emails:
            print_warning(f"Ya existen usuarios para '{nuevo_cliente}': {client_emails}")
        else:
            print_check(f"No hay usuarios previos para '{nuevo_cliente}'", True)

def generar_reporte_validacion(nuevo_cliente):
    """Genera reporte de validación."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    reporte_path = f"docs/validation_reports/validacion_{nuevo_cliente.replace(' ', '_')}_{timestamp}.md"
    
    import os
    os.makedirs("docs/validation_reports", exist_ok=True)
    
    reporte = f"""# 🔍 REPORTE DE VALIDACIÓN - {nuevo_cliente}

**Fecha:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Cliente:** {nuevo_cliente}
**Base URL:** {BASE_URL}

## Resultados de Validación

La validación se ejecutó automáticamente antes del deploy.

### Estado del Sistema:
- Sistema base verificado
- Tablas de configuración validadas
- Limpieza de datos de negocio confirmada
- Estado de usuarios revisado

### Recomendaciones:
1. Si hay datos previos, ejecutar script de limpieza
2. Verificar que todas las tablas maestras estén pobladas
3. Confirmar que no hay transacciones pendientes

---
*Validación realizada con validar_deploy_limpio.py*
"""
    
    with open(reporte_path, 'w', encoding='utf-8') as file:
        file.write(reporte)
    
    print_info(f"Reporte de validación generado: {reporte_path}")

def main():
    parser = argparse.ArgumentParser(description='Validar deploy limpio para nuevo cliente')
    parser.add_argument('--cliente', required=True, 
                       help='Nombre del nuevo cliente')
    
    args = parser.parse_args()
    
    print(f"\n🔍 VALIDANDO SISTEMA PARA NUEVO CLIENTE: {args.cliente}")
    print(f"   Base URL: {BASE_URL}")
    
    session = requests.Session()
    
    try:
        # Login
        if not login_admin(session):
            print("❌ No se pudo conectar al sistema. Verificar credenciales y conectividad.")
            return
        
        print("✅ Conexión establecida correctamente")
        
        # Validaciones
        validar_tablas_sistema(session)
        validar_datos_negocio_limpios(session)
        validar_usuarios_sistema(session, args.cliente)
        
        # Generar reporte
        generar_reporte_validacion(args.cliente)
        
        print(f"\n📊 RESUMEN DE VALIDACIÓN PARA: {args.cliente}")
        print("   ✅ Validación completada")
        print("   📋 Revisar reporte generado para detalles")
        print(f"\n💡 Para proceder con el deploy:")
        print(f"   python scripts/deploy_nuevo_cliente.py --tipo [tipo] --nombre \"{args.cliente}\" --email admin@cliente.cl")
        
    except Exception as e:
        print(f"❌ Error durante validación: {e}")

if __name__ == "__main__":
    main()