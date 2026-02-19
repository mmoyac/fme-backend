#!/usr/bin/env python
"""
Script automatizado para eliminar todos los pedidos de El Olivo.
Ejecuta la eliminación sin confirmaciones interactivas.
"""

import sys
from database.database import SessionLocal
from database.models import (
    Tenant, 
    Pedido, 
    ItemPedido, 
    Cliente, 
    MovimientoInventario, 
    MovimientoPuntos,
    Despacho,
    PickingItem,
    Enrolamiento,
    Lote,
    StockCajasProveedor,
    MovimientoStockCajas
)


def eliminar_pedidos_elolivo():
    """Elimina todos los pedidos del tenant El Olivo."""
    db = SessionLocal()
    
    try:
        # 1. Buscar el tenant El Olivo
        tenant = db.query(Tenant).filter(Tenant.nombre == "El Olivo").first()
        if not tenant:
            print('❌ Error: Tenant "El Olivo" no encontrado')
            print('\nTenants disponibles:')
            tenants = db.query(Tenant).all()
            for t in tenants:
                print(f'  - {t.nombre} (ID: {t.id})')
            return
        
        print(f'✅ Tenant encontrado: {tenant.nombre} (ID: {tenant.id})')
        print('=' * 60)
        
        # 2. Contar pedidos del tenant
        pedidos = db.query(Pedido).join(Cliente).filter(
            Cliente.tenant_id == tenant.id
        ).all()
        
        total_pedidos = len(pedidos)
        print(f'\n📊 Total de pedidos a eliminar: {total_pedidos}')
        
        # SIEMPRE verificar enrolamientos y lotes, incluso sin pedidos
        from database.models import Proveedor
        todos_enrolamientos = db.query(Enrolamiento).join(
            Proveedor, Enrolamiento.proveedor_id == Proveedor.id
        ).filter(
            Proveedor.tenant_id == tenant.id
        ).all()
        todos_enrolamientos_count = len(todos_enrolamientos)
        
        todos_lotes_count = db.query(Lote).join(
            Enrolamiento, Lote.enrolamiento_id == Enrolamiento.id
        ).join(
            Proveedor, Enrolamiento.proveedor_id == Proveedor.id
        ).filter(
            Proveedor.tenant_id == tenant.id
        ).count()
        
        # TODOS los movimientos de stock de cajas del tenant
        todos_movs_stock_cajas_count = 0
        if todos_lotes_count > 0:
            todos_movs_stock_cajas_count = db.query(MovimientoStockCajas).join(
                Lote, MovimientoStockCajas.lote_id == Lote.id
            ).join(
                Enrolamiento, Lote.enrolamiento_id == Enrolamiento.id
            ).join(
                Proveedor, Enrolamiento.proveedor_id == Proveedor.id
            ).filter(
                Proveedor.tenant_id == tenant.id
            ).count()
        
        # Movimientos sin lote (vinculados directamente por proveedor_id)
        movs_sin_lote_count = db.query(MovimientoStockCajas).join(
            Proveedor, MovimientoStockCajas.proveedor_id == Proveedor.id
        ).filter(
            Proveedor.tenant_id == tenant.id,
            MovimientoStockCajas.lote_id == None
        ).count()
        
        todos_movs_stock_cajas_count += movs_sin_lote_count
        
        # TODOS los registros de StockCajasProveedor del tenant
        from database.models import Local
        todos_stock_cajas_count = db.query(StockCajasProveedor).join(
            Proveedor, StockCajasProveedor.proveedor_id == Proveedor.id
        ).filter(
            Proveedor.tenant_id == tenant.id
        ).count()
        
        print(f'📦 Enrolamientos del tenant: {todos_enrolamientos_count}')
        print(f'📦 Lotes del tenant: {todos_lotes_count}')
        print(f'📦 Movimientos stock cajas del tenant: {todos_movs_stock_cajas_count}')
        print(f'📦 StockCajasProveedor del tenant: {todos_stock_cajas_count}')
        
        if total_pedidos == 0 and todos_enrolamientos_count == 0 and todos_lotes_count == 0 and todos_stock_cajas_count == 0 and todos_movs_stock_cajas_count == 0:
            print('ℹ️  No hay pedidos, enrolamientos, lotes, stock de cajas ni movimientos para eliminar')
            print('✅ Base de datos ya está limpia para El Olivo')
            return
        
        # Si hay enrolamientos/lotes pero no pedidos, solo eliminar esos
        if total_pedidos == 0:
            print('\n🔄 No hay pedidos, pero sí datos de enrolamiento/stock. Limpiando...')
            
            # Obtener IDs de TODOS los movimientos de stock cajas del tenant (con y sin lote)
            movs_stock_ids = []
            
            # Movimientos con lote_id
            movs_con_lote = db.query(MovimientoStockCajas).join(
                Lote, MovimientoStockCajas.lote_id == Lote.id
            ).join(
                Enrolamiento, Lote.enrolamiento_id == Enrolamiento.id
            ).join(
                Proveedor, Enrolamiento.proveedor_id == Proveedor.id
            ).filter(
                Proveedor.tenant_id == tenant.id
            ).all()
            movs_stock_ids.extend([mov.id for mov in movs_con_lote])
            
            # Movimientos sin lote_id (vinculados por proveedor_id)
            movs_sin_lote = db.query(MovimientoStockCajas).join(
                Proveedor, MovimientoStockCajas.proveedor_id == Proveedor.id
            ).filter(
                Proveedor.tenant_id == tenant.id,
                MovimientoStockCajas.lote_id == None
            ).all()
            movs_stock_ids.extend([mov.id for mov in movs_sin_lote])
            
            # Eliminar todos los movimientos de stock cajas
            if movs_stock_ids:
                movs_eliminados = db.query(MovimientoStockCajas).filter(
                    MovimientoStockCajas.id.in_(movs_stock_ids)
                ).delete(synchronize_session=False)
                print(f'   ✓ {movs_eliminados} movimientos de stock cajas eliminados (con y sin lote)')
            
            # Obtener IDs de lotes del tenant
            lotes_ids_tenant = [lote.id for lote in db.query(Lote).join(
                Enrolamiento, Lote.enrolamiento_id == Enrolamiento.id
            ).join(
                Proveedor, Enrolamiento.proveedor_id == Proveedor.id
            ).filter(
                Proveedor.tenant_id == tenant.id
            ).all()]
            
            # Eliminar todos los lotes
            if lotes_ids_tenant:
                lotes_eliminados = db.query(Lote).filter(
                    Lote.id.in_(lotes_ids_tenant)
                ).delete(synchronize_session=False)
                print(f'   ✓ {lotes_eliminados} lotes eliminados')
            
            # Obtener IDs de enrolamientos del tenant
            enrolamientos_ids_tenant = [e.id for e in todos_enrolamientos]
            
            # Eliminar todos los enrolamientos
            if enrolamientos_ids_tenant:
                enrolamientos_eliminados = db.query(Enrolamiento).filter(
                    Enrolamiento.id.in_(enrolamientos_ids_tenant)
                ).delete(synchronize_session=False)
                print(f'   ✓ {enrolamientos_eliminados} enrolamientos eliminados')
            
            # Obtener IDs de StockCajasProveedor del tenant
            stock_cajas_ids = [stock.id for stock in db.query(StockCajasProveedor).join(
                Proveedor, StockCajasProveedor.proveedor_id == Proveedor.id
            ).filter(
                Proveedor.tenant_id == tenant.id
            ).all()]
            
            # Eliminar todos los registros de StockCajasProveedor
            if stock_cajas_ids:
                stock_eliminados = db.query(StockCajasProveedor).filter(
                    StockCajasProveedor.id.in_(stock_cajas_ids)
                ).delete(synchronize_session=False)
                print(f'   ✓ {stock_eliminados} registros de StockCajasProveedor eliminados')
            
            db.commit()
            print('✅ Enrolamientos, lotes, movimientos y stock de cajas eliminados exitosamente')
            return
        
        # Obtener IDs de pedidos
        pedidos_ids = [p.id for p in pedidos]
        
        # Mostrar muestra de pedidos
        print(f'\n📋 Muestra de pedidos (primeros 10):')
        for i, pedido in enumerate(pedidos[:10], 1):
            estado_str = pedido.estado_pedido.codigo if pedido.estado_pedido else 'N/A'
            print(f'   {i}. Pedido #{pedido.numero_pedido} - '
                  f'Cliente: {pedido.cliente.nombre} - '
                  f'Total: ${pedido.monto_total:.0f} - '  
                  f'Estado: {estado_str}')
        
        if total_pedidos > 10:
            print(f'   ... y {total_pedidos - 10} pedidos más')
        
        # 3. Contar registros relacionados
        
        # Despachos y PickingItems
        despachos = db.query(Despacho).filter(
            Despacho.pedido_id.in_(pedidos_ids)
        ).all()
        despachos_ids = [d.id for d in despachos]
        despachos_count = len(despachos)
        
        picking_items_count = 0
        if despachos_ids:
            picking_items_count = db.query(PickingItem).filter(
                PickingItem.despacho_id.in_(despachos_ids)
            ).count()
        
        # Items de pedidos
        items_pedido = db.query(ItemPedido).filter(
            ItemPedido.pedido_id.in_(pedidos_ids)
        ).all()
        items_pedido_ids = [item.id for item in items_pedido]
        items_count = len(items_pedido)
        
        # Lotes asociados a items de pedido
        lotes_ids = []
        for item in items_pedido:
            if item.lote_id:
                lotes_ids.append(item.lote_id)
        lotes_ids = list(set(lotes_ids))  # Eliminar duplicados
        lotes_count = len(lotes_ids)
        
        # Movimientos de stock de cajas relacionados a lotes
        movs_stock_cajas_count = 0
        if lotes_ids:
            movs_stock_cajas_count = db.query(MovimientoStockCajas).filter(
                MovimientoStockCajas.lote_id.in_(lotes_ids)
            ).count()
        
        # Enrolamientos relacionados a lotes
        enrolamientos_count = 0
        if lotes_ids:
            enrolamientos = db.query(Enrolamiento).join(
                Lote, Enrolamiento.id == Lote.enrolamiento_id
            ).filter(
                Lote.id.in_(lotes_ids)
            ).all()
            enrolamientos_count = len(enrolamientos)
        
        # Movimientos de inventario tradicional
        movs_inv_count = db.query(MovimientoInventario).filter(
            MovimientoInventario.referencia_id.in_(pedidos_ids),
            MovimientoInventario.tipo_movimiento.in_(['PEDIDO', 'AJUSTE'])
        ).count()
        
        # Movimientos de puntos
        movs_pts_count = db.query(MovimientoPuntos).filter(
            MovimientoPuntos.pedido_id.in_(pedidos_ids)
        ).count()
        
        print(f'\n📦 Registros relacionados a eliminar:')
        print(f'   - Pedidos: {total_pedidos}')
        print(f'   - Items de pedidos: {items_count}')
        print(f'   - Despachos: {despachos_count}')
        print(f'   - Picking items: {picking_items_count}')
        print(f'   - Lotes usados en pedidos: {lotes_count}')
        print(f'   - TODOS los lotes del tenant: {todos_lotes_count}')
        print(f'   - TODOS los enrolamientos del tenant: {todos_enrolamientos_count}')
        print(f'   - TODOS los movimientos de stock cajas: {todos_movs_stock_cajas_count}')
        print(f'   - TODOS los registros de StockCajasProveedor: {todos_stock_cajas_count}')
        print(f'   - Movimientos de inventario: {movs_inv_count}')
        print(f'   - Movimientos de puntos: {movs_pts_count}')
        print('=' * 60)
        
        print('\n🔄 Eliminando registros...')
        
        # 4. Eliminar en orden (respetando integridad referencial)
        
        # 4.1. Eliminar picking items (dependen de despachos)
        picking_items_eliminados = 0
        if despachos_ids:
            picking_items_eliminados = db.query(PickingItem).filter(
                PickingItem.despacho_id.in_(despachos_ids)
            ).delete(synchronize_session=False)
        print(f'   ✓ {picking_items_eliminados} picking items eliminados')
        
        # 4.2. Eliminar despachos (dependen de pedidos)
        despachos_eliminados = db.query(Despacho).filter(
            Despacho.pedido_id.in_(pedidos_ids)
        ).delete(synchronize_session=False)
        print(f'   ✓ {despachos_eliminados} despachos eliminados')
        
        # 4.3. Eliminar movimientos de inventario tradicional
        movs_inv = db.query(MovimientoInventario).filter(
            MovimientoInventario.referencia_id.in_(pedidos_ids),
            MovimientoInventario.tipo_movimiento.in_(['PEDIDO', 'AJUSTE'])
        ).delete(synchronize_session=False)
        print(f'   ✓ {movs_inv} movimientos de inventario eliminados')
        
        # 4.4. Eliminar TODOS los movimientos de stock de cajas del tenant
        movs_stock_ids = []
        
        # Movimientos con lote_id (vinculados a través de lotes)
        movs_con_lote = db.query(MovimientoStockCajas).join(
            Lote, MovimientoStockCajas.lote_id == Lote.id
        ).join(
            Enrolamiento, Lote.enrolamiento_id == Enrolamiento.id
        ).join(
            Proveedor, Enrolamiento.proveedor_id == Proveedor.id
        ).filter(
            Proveedor.tenant_id == tenant.id
        ).all()
        movs_stock_ids.extend([mov.id for mov in movs_con_lote])
        
        # Movimientos sin lote_id (vinculados directamente por proveedor_id)
        movs_sin_lote = db.query(MovimientoStockCajas).join(
            Proveedor, MovimientoStockCajas.proveedor_id == Proveedor.id
        ).filter(
            Proveedor.tenant_id == tenant.id,
            MovimientoStockCajas.lote_id == None
        ).all()
        movs_stock_ids.extend([mov.id for mov in movs_sin_lote])
        
        movs_stock_cajas_eliminados = 0
        if movs_stock_ids:
            movs_stock_cajas_eliminados = db.query(MovimientoStockCajas).filter(
                MovimientoStockCajas.id.in_(movs_stock_ids)
            ).delete(synchronize_session=False)
        print(f'   ✓ {movs_stock_cajas_eliminados} movimientos de stock cajas eliminados (TODOS del tenant, con y sin lote)')
        
        # 4.5. CRITICAL: Eliminar items de pedidos ANTES de lotes (tienen FK a lotes.id)
        items = db.query(ItemPedido).filter(
            ItemPedido.pedido_id.in_(pedidos_ids)
        ).delete(synchronize_session=False)
        print(f'   ✓ {items} items de pedidos eliminados')
        
        # 4.6. Eliminar TODOS los lotes del tenant (ahora sin conflicto de FK)
        from database.models import Proveedor
        lotes_ids_tenant = [lote.id for lote in db.query(Lote).join(
            Enrolamiento, Lote.enrolamiento_id == Enrolamiento.id
        ).join(
            Proveedor, Enrolamiento.proveedor_id == Proveedor.id
        ).filter(
            Proveedor.tenant_id == tenant.id
        ).all()]
        
        lotes_eliminados = 0
        if lotes_ids_tenant:
            lotes_eliminados = db.query(Lote).filter(
                Lote.id.in_(lotes_ids_tenant)
            ).delete(synchronize_session=False)
        print(f'   ✓ {lotes_eliminados} lotes eliminados (TODOS del tenant)')
        
        # 4.7. Eliminar TODOS los enrolamientos del tenant
        enrolamientos_ids_tenant = [e.id for e in db.query(Enrolamiento).join(
            Proveedor, Enrolamiento.proveedor_id == Proveedor.id
        ).filter(
            Proveedor.tenant_id == tenant.id
        ).all()]
        
        enrolamientos_eliminados = 0
        if enrolamientos_ids_tenant:
            enrolamientos_eliminados = db.query(Enrolamiento).filter(
                Enrolamiento.id.in_(enrolamientos_ids_tenant)
            ).delete(synchronize_session=False)
        print(f'   ✓ {enrolamientos_eliminados} enrolamientos eliminados (TODOS del tenant)')
        
        # 4.8. Eliminar TODOS los StockCajasProveedor del tenant
        stock_cajas_ids = [stock.id for stock in db.query(StockCajasProveedor).join(
            Proveedor, StockCajasProveedor.proveedor_id == Proveedor.id
        ).filter(
            Proveedor.tenant_id == tenant.id
        ).all()]
        
        stock_cajas_eliminados = 0
        if stock_cajas_ids:
            stock_cajas_eliminados = db.query(StockCajasProveedor).filter(
                StockCajasProveedor.id.in_(stock_cajas_ids)
            ).delete(synchronize_session=False)
        print(f'   ✓ {stock_cajas_eliminados} registros de StockCajasProveedor eliminados (TODOS del tenant)')
        
        # 4.9. Eliminar movimientos de puntos
        movs_pts = db.query(MovimientoPuntos).filter(
            MovimientoPuntos.pedido_id.in_(pedidos_ids)
        ).delete(synchronize_session=False)
        print(f'   ✓ {movs_pts} movimientos de puntos eliminados')
        
        # 4.10. Eliminar pedidos
        eliminados = db.query(Pedido).filter(
            Pedido.id.in_(pedidos_ids)
        ).delete(synchronize_session=False)
        print(f'   ✓ {eliminados} pedidos eliminados')
        
        # 5. Commit
        db.commit()
        print('\n✅ Todos los pedidos de El Olivo han sido eliminados exitosamente')
        print('✅ Todos los registros relacionados (despachos, picking, lotes, enrolamientos, movimientos, stock cajas) han sido limpiados')
        
        # 6. Verificación
        pedidos_restantes = db.query(Pedido).join(Cliente).filter(
            Cliente.tenant_id == tenant.id
        ).count()
        print(f'✅ Verificación: {pedidos_restantes} pedidos restantes para "El Olivo"')
        
    except Exception as e:
        db.rollback()
        print(f'\n❌ Error durante la eliminación: {str(e)}')
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()


if __name__ == '__main__':
    print('=' * 60)
    print('ELIMINACIÓN AUTOMÁTICA DE PEDIDOS DE EL OLIVO')
    print('=' * 60)
    print('\n⚠️  Este script eliminará TODOS los pedidos de El Olivo')
    print('⚠️  La operación es IRREVERSIBLE\n')
    
    respuesta = input('¿Confirmas que deseas continuar? (SI/NO): ').strip().upper()
    
    if respuesta == 'SI':
        eliminar_pedidos_elolivo()
    else:
        print('\n❌ Operación cancelada')
