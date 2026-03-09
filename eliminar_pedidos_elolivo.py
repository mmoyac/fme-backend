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
    Local,
    Inventario,
    MovimientoInventario, 
    MovimientoPuntos,
    Despacho,
    PickingItem,
    Enrolamiento,
    Lote,
    StockCajasProveedor,
    MovimientoStockCajas,
    Compra,
    DetalleCompra,
    Proveedor,
    Producto,
    Precio,
    PuntosCliente,
    TurnoCaja,
    OperacionCaja,
    HojaRutaItem,
    HojaRuta
)


def eliminar_pedidos_elolivo(eliminar_clientes=True):
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
        
        # Obtener locales del tenant (para filtrar compras, inventario, movimientos)
        locales_tenant = db.query(Local).filter(Local.tenant_id == tenant.id).all()
        locales_ids = [local.id for local in locales_tenant]
        print(f'\n🏪 Locales del tenant: {len(locales_ids)}')
        for local in locales_tenant:
            print(f'   • {local.nombre} (ID: {local.id}, Código: {local.codigo})')
        
        # 2. Contar pedidos del tenant
        pedidos = db.query(Pedido).join(Cliente).filter(
            Cliente.tenant_id == tenant.id
        ).all()
        
        total_pedidos = len(pedidos)
        print(f'\n📊 Total de pedidos a eliminar: {total_pedidos}')
        
        # SIEMPRE verificar enrolamientos y lotes, incluso sin pedidos
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
        todos_stock_cajas_count = db.query(StockCajasProveedor).join(
            Proveedor, StockCajasProveedor.proveedor_id == Proveedor.id
        ).filter(
            Proveedor.tenant_id == tenant.id
        ).count()
        
        print(f'📦 Enrolamientos del tenant: {todos_enrolamientos_count}')
        print(f'📦 Lotes del tenant: {todos_lotes_count}')
        print(f'📦 Movimientos stock cajas del tenant: {todos_movs_stock_cajas_count}')
        print(f'📦 StockCajasProveedor del tenant: {todos_stock_cajas_count}')
        
        # Contar compras e inventario (incluso sin pedidos)
        compras_tenant_count = 0
        inventario_tenant_count = 0
        todos_movs_inv_tenant_count = 0
        
        if locales_ids:
            compras_tenant_count = db.query(Compra).filter(Compra.local_id.in_(locales_ids)).count()
            inventario_tenant_count = db.query(Inventario).filter(Inventario.local_id.in_(locales_ids)).count()
            todos_movs_inv_tenant_count = db.query(MovimientoInventario).filter(
                (MovimientoInventario.local_origen_id.in_(locales_ids)) |
                (MovimientoInventario.local_destino_id.in_(locales_ids))
            ).count()
        
        print(f'📦 Compras del tenant: {compras_tenant_count}')
        print(f'📦 Inventario del tenant: {inventario_tenant_count}')
        print(f'📦 Movimientos inventario del tenant: {todos_movs_inv_tenant_count}')
        
        # Productos, precios, clientes del tenant
        productos_count = db.query(Producto).filter(Producto.tenant_id == tenant.id).count()
        precios_count = 0
        if locales_ids:
            precios_count = db.query(Precio).filter(Precio.local_id.in_(locales_ids)).count()
        clientes_count = db.query(Cliente).filter(Cliente.tenant_id == tenant.id).count()
        puntos_clientes_count = db.query(PuntosCliente).join(
            Cliente, PuntosCliente.cliente_id == Cliente.id
        ).filter(Cliente.tenant_id == tenant.id).count()
        
        # Sistema de caja
        turnos_caja_count = 0
        operaciones_caja_count = 0
        if locales_ids:
            turnos = db.query(TurnoCaja).filter(TurnoCaja.local_id.in_(locales_ids)).all()
            turnos_caja_count = len(turnos)
            if turnos:
                turnos_ids = [t.id for t in turnos]
                operaciones_caja_count = db.query(OperacionCaja).filter(
                    OperacionCaja.turno_caja_id.in_(turnos_ids)
                ).count()
        
        print(f'📦 Productos del tenant: {productos_count}')
        print(f'📦 Precios del tenant: {precios_count}')
        print(f'📦 Clientes del tenant: {clientes_count}')
        print(f'📦 Puntos de clientes: {puntos_clientes_count}')
        print(f'📦 Turnos de caja: {turnos_caja_count}')
        print(f'📦 Operaciones de caja: {operaciones_caja_count}')
        
        if total_pedidos == 0 and todos_enrolamientos_count == 0 and todos_lotes_count == 0 and todos_stock_cajas_count == 0 and todos_movs_stock_cajas_count == 0 and compras_tenant_count == 0 and inventario_tenant_count == 0 and todos_movs_inv_tenant_count == 0 and productos_count == 0 and clientes_count == 0 and turnos_caja_count == 0:
            print('ℹ️  No hay datos para eliminar')
            print('✅ Base de datos ya está limpia para El Olivo')
            return
        
        # Si hay datos pero no pedidos, eliminar todo
        if total_pedidos == 0:
            print('\n🔄 No hay pedidos, pero sí otros datos. Limpiando TODO...')
            
            # Eliminar compras (detalles en cascada)
            if locales_ids and compras_tenant_count > 0:
                compras_elim = db.query(Compra).filter(
                    Compra.local_id.in_(locales_ids)
                ).delete(synchronize_session=False)
                print(f'   ✓ {compras_elim} compras eliminadas')
            
            # Eliminar TODOS los movimientos de inventario
            if locales_ids and todos_movs_inv_tenant_count > 0:
                movs_inv_elim = db.query(MovimientoInventario).filter(
                    (MovimientoInventario.local_origen_id.in_(locales_ids)) |
                    (MovimientoInventario.local_destino_id.in_(locales_ids))
                ).delete(synchronize_session=False)
                print(f'   ✓ {movs_inv_elim} movimientos de inventario eliminados')
            
            # Eliminar inventario (stock)
            if locales_ids and inventario_tenant_count > 0:
                inventario_elim = db.query(Inventario).filter(
                    Inventario.local_id.in_(locales_ids)
                ).delete(synchronize_session=False)
                print(f'   ✓ {inventario_elim} registros de inventario eliminados')
            
            # Eliminar precios
            if locales_ids and precios_count > 0:
                precios_elim = db.query(Precio).filter(
                    Precio.local_id.in_(locales_ids)
                ).delete(synchronize_session=False)
                print(f'   ✓ {precios_elim} precios eliminados')
            
            # Eliminar puntos de clientes
            if eliminar_clientes and puntos_clientes_count > 0:
                clientes_ids = [c.id for c in db.query(Cliente).filter(Cliente.tenant_id == tenant.id).all()]
                if clientes_ids:
                    puntos_elim = db.query(PuntosCliente).filter(
                        PuntosCliente.cliente_id.in_(clientes_ids)
                    ).delete(synchronize_session=False)
                    print(f'   ✓ {puntos_elim} registros de puntos eliminados')
            
            # Eliminar clientes
            if eliminar_clientes and clientes_count > 0:
                clientes_elim = db.query(Cliente).filter(
                    Cliente.tenant_id == tenant.id
                ).delete(synchronize_session=False)
                print(f'   ✓ {clientes_elim} clientes eliminados')
            elif not eliminar_clientes:
                print(f'   ⏭ Clientes CONSERVADOS ({clientes_count} registros)')
            
            # NOTA: Productos se conservan intencionalmente
                        # Eliminar operaciones de caja (antes de eliminar turnos)
            if locales_ids and operaciones_caja_count > 0:
                turnos = db.query(TurnoCaja).filter(TurnoCaja.local_id.in_(locales_ids)).all()
                if turnos:
                    turnos_ids = [t.id for t in turnos]
                    operaciones_elim = db.query(OperacionCaja).filter(
                        OperacionCaja.turno_caja_id.in_(turnos_ids)
                    ).delete(synchronize_session=False)
                    print(f'   ✓ {operaciones_elim} operaciones de caja eliminadas')
            
            # Eliminar turnos de caja
            if locales_ids and turnos_caja_count > 0:
                turnos_elim = db.query(TurnoCaja).filter(
                    TurnoCaja.local_id.in_(locales_ids)
                ).delete(synchronize_session=False)
                print(f'   ✓ {turnos_elim} turnos de caja eliminados')
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
            print('✅ Base de datos limpiada exitosamente:')
            print('   • Compras eliminadas')
            print('   • Inventario reseteado')
            print('   • Movimientos de inventario eliminados')
            print('   • Precios eliminados')
            print('   • Clientes y puntos eliminados')
            print('   • Productos: CONSERVADOS')
            print('   • Turnos y operaciones de caja eliminados')
            print('   • Enrolamientos, lotes, movimientos y stock de cajas eliminados')
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
        
        # TODOS los movimientos de inventario del tenant (no solo pedidos)
        todos_movs_inv_count = 0
        if locales_ids:
            todos_movs_inv_count = db.query(MovimientoInventario).filter(
                (MovimientoInventario.local_origen_id.in_(locales_ids)) |
                (MovimientoInventario.local_destino_id.in_(locales_ids))
            ).count()
        
        # Movimientos de puntos
        movs_pts_count = db.query(MovimientoPuntos).filter(
            MovimientoPuntos.pedido_id.in_(pedidos_ids)
        ).count()
        
        # Compras del tenant (en sus locales)
        compras_count = 0
        detalles_compra_count = 0
        if locales_ids:
            compras = db.query(Compra).filter(Compra.local_id.in_(locales_ids)).all()
            compras_count = len(compras)
            if compras:
                compras_ids = [c.id for c in compras]
                detalles_compra_count = db.query(DetalleCompra).filter(
                    DetalleCompra.compra_id.in_(compras_ids)
                ).count()
        
        # Inventario del tenant (en sus locales)
        inventario_count = 0
        if locales_ids:
            inventario_count = db.query(Inventario).filter(
                Inventario.local_id.in_(locales_ids)
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
        print(f'   - Movimientos de inventario (pedidos): {movs_inv_count}')
        print(f'   - TODOS los movimientos de inventario: {todos_movs_inv_count}')
        print(f'   - Movimientos de puntos: {movs_pts_count}')
        print(f'   - Compras: {compras_count}')
        print(f'   - Detalles de compras: {detalles_compra_count}')
        print(f'   - Registros de inventario (stock): {inventario_count}')
        print(f'   - Precios: {precios_count}')
        print(f'   - Clientes: {clientes_count}')
        print(f'   - Puntos de clientes: {puntos_clientes_count}')
        print(f'   - Productos: {productos_count}')
        print(f'   - Turnos de caja: {turnos_caja_count}')
        print(f'   - Operaciones de caja: {operaciones_caja_count}')
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
        
        # 4.3. Eliminar compras del tenant (DetalleCompra se elimina por cascade)
        compras_eliminadas = 0
        if locales_ids:
            compras_eliminadas = db.query(Compra).filter(
                Compra.local_id.in_(locales_ids)
            ).delete(synchronize_session=False)
        print(f'   ✓ {compras_eliminadas} compras eliminadas (detalles en cascada)')
        
        # 4.4. Eliminar TODOS los movimientos de inventario del tenant
        movs_inv_eliminados = 0
        if locales_ids:
            movs_inv_eliminados = db.query(MovimientoInventario).filter(
                (MovimientoInventario.local_origen_id.in_(locales_ids)) |
                (MovimientoInventario.local_destino_id.in_(locales_ids))
            ).delete(synchronize_session=False)
        print(f'   ✓ {movs_inv_eliminados} movimientos de inventario eliminados (TODOS: transferencias, entradas, ajustes)')
        
        # 4.5. Eliminar TODO el inventario del tenant (stock)
        inventario_eliminado = 0
        if locales_ids:
            inventario_eliminado = db.query(Inventario).filter(
                Inventario.local_id.in_(locales_ids)
            ).delete(synchronize_session=False)
        print(f'   ✓ {inventario_eliminado} registros de inventario eliminados (stock reseteado)')
        
        # 4.6. Eliminar TODOS los movimientos de stock de cajas del tenant
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
        
        # 4.7. CRITICAL: Eliminar items de pedidos ANTES de lotes (tienen FK a lotes.id)
        items = db.query(ItemPedido).filter(
            ItemPedido.pedido_id.in_(pedidos_ids)
        ).delete(synchronize_session=False)
        print(f'   ✓ {items} items de pedidos eliminados')
        
        # 4.8. Eliminar TODOS los lotes del tenant (ahora sin conflicto de FK)
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
        
        # 4.9. Eliminar TODOS los enrolamientos del tenant
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
        
        # 4.10. Eliminar TODOS los StockCajasProveedor del tenant
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
        
        # 4.11. Eliminar movimientos de puntos
        movs_pts = db.query(MovimientoPuntos).filter(
            MovimientoPuntos.pedido_id.in_(pedidos_ids)
        ).delete(synchronize_session=False)
        print(f'   ✓ {movs_pts} movimientos de puntos eliminados')
        
        # 4.11b. Eliminar hoja_ruta_items que referencian estos pedidos
        hoja_ruta_items_elim = db.query(HojaRutaItem).filter(
            HojaRutaItem.pedido_id.in_(pedidos_ids)
        ).delete(synchronize_session=False)
        print(f'   ✓ {hoja_ruta_items_elim} hoja_ruta_items eliminados')
        
        # 4.11c. Eliminar hojas_ruta del tenant (las vacías o cualquier restante)
        hojas_ruta_elim = db.query(HojaRuta).filter(
            HojaRuta.tenant_id == tenant.id
        ).delete(synchronize_session=False)
        print(f'   ✓ {hojas_ruta_elim} hojas de ruta eliminadas')
        
        # 4.12. Eliminar pedidos
        eliminados = db.query(Pedido).filter(
            Pedido.id.in_(pedidos_ids)
        ).delete(synchronize_session=False)
        print(f'   ✓ {eliminados} pedidos eliminados')
        
        # 4.13. Eliminar precios (ahora que no hay pedidos)
        precios_eliminados = 0
        if locales_ids:
            precios_eliminados = db.query(Precio).filter(
                Precio.local_id.in_(locales_ids)
            ).delete(synchronize_session=False)
        print(f'   ✓ {precios_eliminados} precios eliminados')
        
        # 4.14. Eliminar puntos de clientes (antes de eliminar clientes)
        clientes_ids = [c.id for c in db.query(Cliente).filter(Cliente.tenant_id == tenant.id).all()]
        puntos_eliminados = 0
        if eliminar_clientes and clientes_ids:
            puntos_eliminados = db.query(PuntosCliente).filter(
                PuntosCliente.cliente_id.in_(clientes_ids)
            ).delete(synchronize_session=False)
            print(f'   ✓ {puntos_eliminados} registros de puntos eliminados')
        elif not eliminar_clientes:
            print(f'   ⏭ Puntos de clientes CONSERVADOS')
        
        # 4.15. Eliminar clientes
        clientes_eliminados = 0
        if eliminar_clientes:
            clientes_eliminados = db.query(Cliente).filter(
                Cliente.tenant_id == tenant.id
            ).delete(synchronize_session=False)
            print(f'   ✓ {clientes_eliminados} clientes eliminados')
        else:
            print(f'   ⏭ Clientes CONSERVADOS ({clientes_count} registros)')
        
        # NOTA: Productos se conservan intencionalmente
        
        # 4.17. Eliminar operaciones de caja (antes de eliminar turnos)
        operaciones_caja_eliminadas = 0
        if locales_ids:
            turnos = db.query(TurnoCaja).filter(TurnoCaja.local_id.in_(locales_ids)).all()
            if turnos:
                turnos_ids = [t.id for t in turnos]
                operaciones_caja_eliminadas = db.query(OperacionCaja).filter(
                    OperacionCaja.turno_caja_id.in_(turnos_ids)
                ).delete(synchronize_session=False)
        print(f'   ✓ {operaciones_caja_eliminadas} operaciones de caja eliminadas')
        
        # 4.18. Eliminar turnos de caja
        turnos_caja_eliminados = 0
        if locales_ids:
            turnos_caja_eliminados = db.query(TurnoCaja).filter(
                TurnoCaja.local_id.in_(locales_ids)
            ).delete(synchronize_session=False)
        print(f'   ✓ {turnos_caja_eliminados} turnos de caja eliminados')
        
        # 5. Commit
        db.commit()
        print('\n✅ Todos los datos de El Olivo han sido eliminados exitosamente')
        print('✅ Registros eliminados:')
        print('   • Pedidos, despachos y picking items')
        print('   • Compras y detalles de compras')
        print('   • Inventario (stock reseteado)')
        print('   • Movimientos de inventario (transferencias e historial)')
        print('   • Lotes, enrolamientos, stock de cajas y movimientos')
        print('   • Movimientos de puntos')
        print('   • Precios')
        if eliminar_clientes:
            print('   • Clientes y puntos de fidelización')
        print('   • Productos: CONSERVADOS')
        print('   • Turnos y operaciones de caja')
        
        # 6. Verificación
        pedidos_restantes = db.query(Pedido).join(Cliente).filter(
            Cliente.tenant_id == tenant.id
        ).count()
        productos_restantes = db.query(Producto).filter(
            Producto.tenant_id == tenant.id
        ).count()
        clientes_restantes = db.query(Cliente).filter(
            Cliente.tenant_id == tenant.id
        ).count()
        print(f'\n✅ Verificación:')
        print(f'   • {pedidos_restantes} pedidos restantes')
        print(f'   • {productos_restantes} productos restantes')
        print(f'   • {clientes_restantes} clientes restantes')
        
    except Exception as e:
        db.rollback()
        print(f'\n❌ Error durante la eliminación: {str(e)}')
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()


if __name__ == '__main__':
    print('=' * 60)
    print('🗑️  RESET COMPLETO DE BASE DE DATOS - EL OLIVO')
    print('=' * 60)
    print('\n⚠️  Este script eliminará TODO de El Olivo:')
    print('   📦 Todos los PRODUCTOS (se CONSERVAN)')
    print('   💰 Todos los PRECIOS')
    print('   👥 Todos los CLIENTES y puntos')
    print('   🛒 Todas las COMPRAS')
    print('   📊 Todo el INVENTARIO (stock)')
    print('   🔄 Todos los MOVIMIENTOS (transferencias e historial)')
    print('   📋 Todos los PEDIDOS y despachos')
    print('   🏭 Todos los LOTES y enrolamientos')
    print('   💵 Todos los TURNOS y OPERACIONES de CAJA')
    print('\n✅ Se mantienen (maestras):')
    print('   • Locales')
    print('   • Proveedores')
    print('   • Categorías, Unidades de Medida, Tipos')
    print('   • Usuarios y Roles')
    print('\n⚠️  La operación es IRREVERSIBLE - Reset completo\n')
    
    respuesta = input('¿Confirmas que deseas RESETEAR TODO? (SI/NO): ').strip().upper()
    
    if respuesta != 'SI':
        print('\n❌ Operación cancelada')
    else:
        resp_clientes = input('¿Eliminar también los CLIENTES y sus puntos? (SI/NO): ').strip().upper()
        eliminar_clientes = (resp_clientes == 'SI')
        if not eliminar_clientes:
            print('   → Clientes serán CONSERVADOS')
        eliminar_pedidos_elolivo(eliminar_clientes=eliminar_clientes)
