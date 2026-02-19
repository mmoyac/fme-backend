#!/usr/bin/env python
"""
Script para eliminar todos los pedidos de un tenant específico.

Este script elimina de forma segura todos los pedidos y sus datos relacionados
de un tenant en particular, manteniendo la integridad referencial de la base de datos.

Uso:
    docker exec -it fme-backend python scripts/eliminar_pedidos_tenant.py

    O directamente con Python:
    python scripts/eliminar_pedidos_tenant.py

ADVERTENCIA: Esta operación es IRREVERSIBLE. Asegúrate de tener un backup
             de la base de datos antes de ejecutar este script en producción.

Autor: Sistema FME
Fecha: 2026-02-17
"""

import sys
from database.database import SessionLocal
from database.models import (
    Tenant, 
    Pedido, 
    ItemPedido, 
    Cliente, 
    MovimientoInventario, 
    MovimientoPuntos
)


def eliminar_pedidos_tenant(nombre_tenant: str, confirmar: bool = False):
    """
    Elimina todos los pedidos de un tenant específico.
    
    Args:
        nombre_tenant: Nombre exacto del tenant (case-sensitive)
        confirmar: Si es True, ejecuta la eliminación. Si es False, solo muestra información.
    
    Returns:
        dict: Resumen de la operación con contadores de registros eliminados
    """
    db = SessionLocal()
    
    try:
        # 1. Buscar el tenant
        tenant = db.query(Tenant).filter(Tenant.nombre == nombre_tenant).first()
        if not tenant:
            print(f'❌ Error: Tenant "{nombre_tenant}" no encontrado')
            print('\nTenants disponibles:')
            tenants = db.query(Tenant).all()
            for t in tenants:
                print(f'  - {t.nombre} (ID: {t.id})')
            return None
        
        print(f'✅ Tenant encontrado: {tenant.nombre} (ID: {tenant.id})')
        print('=' * 60)
        
        # 2. Contar pedidos del tenant
        pedidos = db.query(Pedido).join(Cliente).filter(
            Cliente.tenant_id == tenant.id
        ).all()
        
        total_pedidos = len(pedidos)
        print(f'\n📊 Total de pedidos a eliminar: {total_pedidos}')
        
        if total_pedidos == 0:
            print('ℹ️  No hay pedidos para eliminar')
            return {
                'tenant_id': tenant.id,
                'tenant_nombre': tenant.nombre,
                'pedidos_eliminados': 0,
                'items_eliminados': 0,
                'movimientos_inventario_eliminados': 0,
                'movimientos_puntos_eliminados': 0
            }
        
        # Obtener IDs de pedidos
        pedidos_ids = [p.id for p in pedidos]
        
        # Mostrar muestra de pedidos
        print(f'\n📋 Muestra de pedidos (primeros 5):')
        for i, pedido in enumerate(pedidos[:5], 1):
            print(f'   {i}. Pedido #{pedido.numero_pedido} - '
                  f'Cliente: {pedido.cliente.nombre} - '
                  f'Total: ${pedido.monto_total:.0f} - '
                  f'Estado: {pedido.estado}')
        
        if total_pedidos > 5:
            print(f'   ... y {total_pedidos - 5} pedidos más')
        
        # 3. Contar registros relacionados
        movs_inv_count = db.query(MovimientoInventario).filter(
            MovimientoInventario.referencia_id.in_(pedidos_ids),
            MovimientoInventario.tipo_movimiento.in_(['PEDIDO', 'AJUSTE'])
        ).count()
        
        items_count = db.query(ItemPedido).filter(
            ItemPedido.pedido_id.in_(pedidos_ids)
        ).count()
        
        movs_pts_count = db.query(MovimientoPuntos).filter(
            MovimientoPuntos.pedido_id.in_(pedidos_ids)
        ).count()
        
        print(f'\n📦 Registros relacionados a eliminar:')
        print(f'   - Items de pedidos: {items_count}')
        print(f'   - Movimientos de inventario: {movs_inv_count}')
        print(f'   - Movimientos de puntos: {movs_pts_count}')
        print('=' * 60)
        
        # 4. Confirmación
        if not confirmar:
            print('\n⚠️  MODO CONSULTA: No se eliminarán registros.')
            print('   Para ejecutar la eliminación, llama al script con confirmar=True')
            return None
        
        print(f'\n⚠️  ADVERTENCIA: Estás a punto de eliminar {total_pedidos} pedidos')
        print(f'   del tenant "{tenant.nombre}" de forma PERMANENTE.')
        respuesta = input('\n¿Estás seguro? Escribe "CONFIRMAR" para continuar: ')
        
        if respuesta != 'CONFIRMAR':
            print('❌ Operación cancelada por el usuario')
            return None
        
        print('\n🔄 Eliminando registros...')
        
        # 5. Eliminar en orden (respetando integridad referencial)
        
        # Eliminar movimientos de inventario
        movs_inv = db.query(MovimientoInventario).filter(
            MovimientoInventario.referencia_id.in_(pedidos_ids),
            MovimientoInventario.tipo_movimiento.in_(['PEDIDO', 'AJUSTE'])
        ).delete(synchronize_session=False)
        print(f'   ✓ {movs_inv} movimientos de inventario eliminados')
        
        # Eliminar items de pedidos
        items = db.query(ItemPedido).filter(
            ItemPedido.pedido_id.in_(pedidos_ids)
        ).delete(synchronize_session=False)
        print(f'   ✓ {items} items de pedidos eliminados')
        
        # Eliminar movimientos de puntos
        movs_pts = db.query(MovimientoPuntos).filter(
            MovimientoPuntos.pedido_id.in_(pedidos_ids)
        ).delete(synchronize_session=False)
        print(f'   ✓ {movs_pts} movimientos de puntos eliminados')
        
        # Eliminar pedidos
        eliminados = db.query(Pedido).filter(
            Pedido.id.in_(pedidos_ids)
        ).delete(synchronize_session=False)
        print(f'   ✓ {eliminados} pedidos eliminados')
        
        # 6. Commit
        db.commit()
        print('\n✅ Todos los pedidos han sido eliminados exitosamente')
        
        # 7. Verificación
        pedidos_restantes = db.query(Pedido).join(Cliente).filter(
            Cliente.tenant_id == tenant.id
        ).count()
        print(f'✅ Verificación: {pedidos_restantes} pedidos restantes para "{tenant.nombre}"')
        
        return {
            'tenant_id': tenant.id,
            'tenant_nombre': tenant.nombre,
            'pedidos_eliminados': eliminados,
            'items_eliminados': items,
            'movimientos_inventario_eliminados': movs_inv,
            'movimientos_puntos_eliminados': movs_pts
        }
        
    except Exception as e:
        db.rollback()
        print(f'\n❌ Error durante la eliminación: {str(e)}')
        import traceback
        traceback.print_exc()
        return None
        
    finally:
        db.close()


def main():
    """Función principal para ejecución interactiva."""
    print('=' * 60)
    print('SCRIPT DE ELIMINACIÓN DE PEDIDOS POR TENANT')
    print('=' * 60)
    
    # Listar tenants disponibles
    db = SessionLocal()
    tenants = db.query(Tenant).all()
    db.close()
    
    print('\nTenants disponibles:')
    for i, tenant in enumerate(tenants, 1):
        print(f'  {i}. {tenant.nombre} (ID: {tenant.id})')
    
    # Solicitar nombre del tenant
    print('\n' + '=' * 60)
    nombre_tenant = input('Ingresa el nombre exacto del tenant: ').strip()
    
    if not nombre_tenant:
        print('❌ Operación cancelada')
        return
    
    # Ejecutar en modo consulta primero
    print('\n🔍 MODO CONSULTA - Analizando pedidos...\n')
    eliminar_pedidos_tenant(nombre_tenant, confirmar=False)
    
    # Preguntar si desea continuar
    print('\n' + '=' * 60)
    continuar = input('\n¿Deseas continuar con la eliminación? (s/n): ').strip().lower()
    
    if continuar == 's':
        eliminar_pedidos_tenant(nombre_tenant, confirmar=True)
    else:
        print('❌ Operación cancelada por el usuario')


if __name__ == '__main__':
    # Modo interactivo
    main()
