#!/usr/bin/env python
"""
Script para eliminar todos los datos operativos de un tenant.
Corre dentro del contenedor Docker (acceso directo a la BD).

Uso (desde fuera del contenedor):
    docker compose exec backend python eliminar_datos_tenant.py --tenant-id 3
    docker exec masas_estacion_backend python eliminar_datos_tenant.py --tenant-id 1

Uso directo:
    python eliminar_datos_tenant.py --tenant-id 3 [--conservar-clientes]

Se ELIMINAN:
    - Pedidos, despachos, picking items
    - Compras y detalles de compras
    - Inventario (stock reseteado)
    - Movimientos de inventario
    - Lotes, enrolamientos, stock de cajas y sus movimientos
    - Movimientos de puntos
    - Comisiones y liquidaciones de comisiones
    - Precios
    - Clientes y puntos de fidelización (configurable)
    - Turnos y operaciones de caja
    - Hojas de ruta

Se CONSERVAN (maestras):
    - Productos
    - Locales
    - Proveedores
    - Categorías, Unidades de Medida, Tipos
    - Usuarios y Roles
"""
import sys
import io
import argparse

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from database.database import SessionLocal
from database.models import (
    Tenant, Pedido, ItemPedido, Cliente, Local,
    Inventario, MovimientoInventario, MovimientoPuntos,
    Despacho, PickingItem, Enrolamiento, Lote,
    StockCajasProveedor, MovimientoStockCajas,
    Compra, DetalleCompra, Proveedor, Producto,
    Precio, PuntosCliente, TurnoCaja, OperacionCaja,
    HojaRutaItem, HojaRuta,
    SolicitudTransferencia, ItemSolicitudTransferencia,
    Comision, LiquidacionComision,
    Receta, IngredienteReceta,
    Cotizacion,
    Devolucion, ItemDevolucion, NotaCredito
)

# ─── Argumentos ───────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description="Eliminar datos operativos de un tenant")
parser.add_argument("--tenant-id", type=int, required=True, help="ID del tenant a limpiar")
parser.add_argument("--eliminar-clientes", action="store_true",
                    help="También eliminar clientes y sus puntos de fidelización (por defecto se conservan)")
parser.add_argument("--eliminar-cotizaciones", action="store_true",
                    help="También eliminar cotizaciones (por defecto se conservan)")
parser.add_argument("--eliminar-productos", action="store_true",
                    help="También eliminar productos (por defecto se conservan)")
parser.add_argument("--si", action="store_true",
                    help="Confirmar automáticamente sin prompt interactivo")
args = parser.parse_args()

TENANT_ID = args.tenant_id
CONSERVAR_CLIENTES = not args.eliminar_clientes
CONSERVAR_COTIZACIONES = not args.eliminar_cotizaciones
CONSERVAR_PRODUCTOS = not args.eliminar_productos
AUTO_CONFIRM = args.si


def eliminar_datos(tenant_id: int, conservar_clientes: bool = False, conservar_cotizaciones: bool = True):
    db = SessionLocal()
    try:
        # ── Buscar tenant ────────────────────────────────────────────────────
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            print(f"❌ Tenant ID {tenant_id} no encontrado")
            print("\nTenants disponibles:")
            for t in db.query(Tenant).all():
                print(f"  [{t.id}] {t.nombre} ({t.codigo})")
            sys.exit(1)

        print(f"✅ Tenant: [{tenant.id}] {tenant.nombre} ({tenant.codigo})")
        print("=" * 70)

        # ── Recopilar contexto ───────────────────────────────────────────────
        locales = db.query(Local).filter(Local.tenant_id == tenant.id).all()
        locales_ids = [l.id for l in locales]
        print(f"\n🏪 Locales: {len(locales_ids)}")
        for l in locales:
            print(f"   • {l.nombre} (ID: {l.id}, Código: {l.codigo})")

        pedidos = db.query(Pedido).join(Cliente).filter(Cliente.tenant_id == tenant.id).all()
        pedidos_ids = [p.id for p in pedidos]

        # Conteos para mostrar resumen
        counts = {}
        counts["pedidos"] = len(pedidos_ids)

        despachos = db.query(Despacho).filter(Despacho.pedido_id.in_(pedidos_ids)).all() if pedidos_ids else []
        despachos_ids = [d.id for d in despachos]
        counts["despachos"] = len(despachos_ids)
        counts["picking_items"] = db.query(PickingItem).filter(PickingItem.despacho_id.in_(despachos_ids)).count() if despachos_ids else 0
        counts["items_pedido"] = db.query(ItemPedido).filter(ItemPedido.pedido_id.in_(pedidos_ids)).count() if pedidos_ids else 0

        counts["compras"] = db.query(Compra).filter(Compra.local_id.in_(locales_ids)).count() if locales_ids else 0
        counts["inventario"] = db.query(Inventario).filter(Inventario.local_id.in_(locales_ids)).count() if locales_ids else 0
        counts["movs_inventario"] = db.query(MovimientoInventario).filter(
            (MovimientoInventario.local_origen_id.in_(locales_ids)) |
            (MovimientoInventario.local_destino_id.in_(locales_ids))
        ).count() if locales_ids else 0

        # Lotes / enrolamientos / stock cajas
        todos_enrolamientos = db.query(Enrolamiento).join(
            Proveedor, Enrolamiento.proveedor_id == Proveedor.id
        ).filter(Proveedor.tenant_id == tenant.id).all()
        enrolamientos_ids = [e.id for e in todos_enrolamientos]
        counts["enrolamientos"] = len(enrolamientos_ids)

        lotes_ids = [l.id for l in db.query(Lote).filter(Lote.enrolamiento_id.in_(enrolamientos_ids)).all()] if enrolamientos_ids else []
        counts["lotes"] = len(lotes_ids)

        movs_stock_con_lote = db.query(MovimientoStockCajas).filter(MovimientoStockCajas.lote_id.in_(lotes_ids)).all() if lotes_ids else []
        movs_stock_sin_lote = db.query(MovimientoStockCajas).join(
            Proveedor, MovimientoStockCajas.proveedor_id == Proveedor.id
        ).filter(Proveedor.tenant_id == tenant.id, MovimientoStockCajas.lote_id == None).all()
        movs_stock_ids = [m.id for m in movs_stock_con_lote] + [m.id for m in movs_stock_sin_lote]
        counts["movs_stock_cajas"] = len(movs_stock_ids)
        counts["stock_cajas"] = db.query(StockCajasProveedor).join(
            Proveedor, StockCajasProveedor.proveedor_id == Proveedor.id
        ).filter(Proveedor.tenant_id == tenant.id).count()

        counts["movs_puntos"] = db.query(MovimientoPuntos).filter(MovimientoPuntos.pedido_id.in_(pedidos_ids)).count() if pedidos_ids else 0
        counts["precios"] = db.query(Precio).filter(Precio.local_id.in_(locales_ids)).count() if locales_ids else 0

        clientes_ids = [c.id for c in db.query(Cliente).filter(Cliente.tenant_id == tenant.id).all()]
        counts["clientes"] = len(clientes_ids)
        counts["puntos_clientes"] = db.query(PuntosCliente).filter(PuntosCliente.cliente_id.in_(clientes_ids)).count() if clientes_ids else 0

        turnos = db.query(TurnoCaja).filter(TurnoCaja.local_id.in_(locales_ids)).all() if locales_ids else []
        turnos_ids = [t.id for t in turnos]
        counts["turnos_caja"] = len(turnos_ids)
        counts["operaciones_caja"] = db.query(OperacionCaja).filter(OperacionCaja.turno_caja_id.in_(turnos_ids)).count() if turnos_ids else 0

        counts["hojas_ruta"] = db.query(HojaRuta).filter(HojaRuta.tenant_id == tenant.id).count()
        counts["hoja_ruta_items"] = db.query(HojaRutaItem).filter(HojaRutaItem.pedido_id.in_(pedidos_ids)).count() if pedidos_ids else 0

        counts["solicitudes"] = db.query(SolicitudTransferencia).filter(SolicitudTransferencia.tenant_id == tenant.id).count()

        counts["productos"] = db.query(Producto).filter(Producto.tenant_id == tenant.id).count()

        conservar_productos = CONSERVAR_PRODUCTOS
        total_a_eliminar = sum(v for k, v in counts.items() if k != "productos")
        if not conservar_productos:
            total_a_eliminar += counts["productos"]
        if conservar_clientes:
            total_a_eliminar -= counts["clientes"] + counts["puntos_clientes"]

        print(f"\n📊 Datos a eliminar:")
        print(f"   🛒 Pedidos:                    {counts['pedidos']}")
        print(f"   📦 Items de pedidos:           {counts['items_pedido']}")
        print(f"   🚚 Despachos / picking items:  {counts['despachos']} / {counts['picking_items']}")
        print(f"   🏭 Compras:                    {counts['compras']}")
        print(f"   📊 Inventario (stock):         {counts['inventario']}")
        print(f"   🔄 Movimientos inventario:     {counts['movs_inventario']}")
        print(f"   📦 Enrolamientos / Lotes:      {counts['enrolamientos']} / {counts['lotes']}")
        print(f"   📦 Stock cajas / Movimientos:  {counts['stock_cajas']} / {counts['movs_stock_cajas']}")
        print(f"   🎯 Movimientos de puntos:      {counts['movs_puntos']}")
        print(f"   💰 Precios:                    {counts['precios']}")
        print(f"   💵 Turnos / Operaciones caja:  {counts['turnos_caja']} / {counts['operaciones_caja']}")
        print(f"   🗺️  Hojas de ruta / Items:      {counts['hojas_ruta']} / {counts['hoja_ruta_items']}")
        print(f"   📋 Solicitudes transferencia:  {counts['solicitudes']}")
        if conservar_clientes:
            print(f"   👥 Clientes:                   CONSERVADOS ({counts['clientes']})")
        else:
            print(f"   👥 Clientes / Puntos:          {counts['clientes']} / {counts['puntos_clientes']}")
        if conservar_productos:
            print(f"\n   📦 Productos:                  CONSERVADOS ({counts['productos']})")
        else:
            print(f"\n   📦 Productos:                  {counts['productos']} (SE ELIMINARÁN)")
        print("=" * 70)

        if total_a_eliminar == 0:
            print("ℹ️  No hay datos operativos que eliminar. La BD ya está limpia.")
            return

        # ── Eliminación ──────────────────────────────────────────────────────
        print("\n🔄 Eliminando en orden...")

        # Picking items
        if despachos_ids:
            n = db.query(PickingItem).filter(PickingItem.despacho_id.in_(despachos_ids)).delete(synchronize_session=False)
            print(f"   ✓ {n} picking items")

        # Despachos
        if pedidos_ids:
            n = db.query(Despacho).filter(Despacho.pedido_id.in_(pedidos_ids)).delete(synchronize_session=False)
            print(f"   ✓ {n} despachos")

        # Hoja ruta items
        if pedidos_ids:
            n = db.query(HojaRutaItem).filter(HojaRutaItem.pedido_id.in_(pedidos_ids)).delete(synchronize_session=False)
            print(f"   ✓ {n} hoja_ruta_items")

        # Hojas de ruta
        n = db.query(HojaRuta).filter(HojaRuta.tenant_id == tenant.id).delete(synchronize_session=False)
        print(f"   ✓ {n} hojas de ruta")

        # Compras (DetalleCompra en cascada)
        if locales_ids:
            n = db.query(Compra).filter(Compra.local_id.in_(locales_ids)).delete(synchronize_session=False)
            print(f"   ✓ {n} compras (detalles en cascada)")

        # Movimientos de inventario
        if locales_ids:
            n = db.query(MovimientoInventario).filter(
                (MovimientoInventario.local_origen_id.in_(locales_ids)) |
                (MovimientoInventario.local_destino_id.in_(locales_ids))
            ).delete(synchronize_session=False)
            print(f"   ✓ {n} movimientos de inventario")

        # Inventario (stock)
        if locales_ids:
            n = db.query(Inventario).filter(Inventario.local_id.in_(locales_ids)).delete(synchronize_session=False)
            print(f"   ✓ {n} registros de inventario (stock reseteado)")

        # Movimientos de stock de cajas
        if movs_stock_ids:
            n = db.query(MovimientoStockCajas).filter(MovimientoStockCajas.id.in_(movs_stock_ids)).delete(synchronize_session=False)
            print(f"   ✓ {n} movimientos de stock cajas")

        # Items de devolución (FK RESTRICT a items_pedido — debe ir antes)
        if pedidos_ids:
            devolucion_ids = [d.id for d in db.query(Devolucion).filter(Devolucion.pedido_id.in_(pedidos_ids)).all()]
            if devolucion_ids:
                n = db.query(ItemDevolucion).filter(ItemDevolucion.devolucion_id.in_(devolucion_ids)).delete(synchronize_session=False)
                print(f"   ✓ {n} items de devolución")

        # Items de pedidos (FK a lotes)
        if pedidos_ids:
            n = db.query(ItemPedido).filter(ItemPedido.pedido_id.in_(pedidos_ids)).delete(synchronize_session=False)
            print(f"   ✓ {n} items de pedidos")

        # Lotes
        if lotes_ids:
            n = db.query(Lote).filter(Lote.id.in_(lotes_ids)).delete(synchronize_session=False)
            print(f"   ✓ {n} lotes")

        # Enrolamientos
        if enrolamientos_ids:
            n = db.query(Enrolamiento).filter(Enrolamiento.id.in_(enrolamientos_ids)).delete(synchronize_session=False)
            print(f"   ✓ {n} enrolamientos")

        # StockCajasProveedor
        stock_cajas_ids = [s.id for s in db.query(StockCajasProveedor).join(
            Proveedor, StockCajasProveedor.proveedor_id == Proveedor.id
        ).filter(Proveedor.tenant_id == tenant.id).all()]
        if stock_cajas_ids:
            n = db.query(StockCajasProveedor).filter(StockCajasProveedor.id.in_(stock_cajas_ids)).delete(synchronize_session=False)
            print(f"   ✓ {n} StockCajasProveedor")

        # Movimientos de puntos
        if pedidos_ids:
            n = db.query(MovimientoPuntos).filter(MovimientoPuntos.pedido_id.in_(pedidos_ids)).delete(synchronize_session=False)
            print(f"   ✓ {n} movimientos de puntos")

        # Comisiones (FK pedido_id con RESTRICT — debe eliminarse antes que los pedidos)
        if pedidos_ids:
            n = db.query(Comision).filter(Comision.pedido_id.in_(pedidos_ids)).delete(synchronize_session=False)
            print(f"   ✓ {n} comisiones")

        # Liquidaciones de comisiones del tenant
        n = db.query(LiquidacionComision).filter(LiquidacionComision.tenant_id == tenant.id).delete(synchronize_session=False)
        if n:
            print(f"   ✓ {n} liquidaciones de comisiones")

        # Devoluciones (FK RESTRICT a pedidos)
        if pedidos_ids:
            n = db.query(Devolucion).filter(Devolucion.pedido_id.in_(pedidos_ids)).delete(synchronize_session=False)
            if n:
                print(f"   ✓ {n} devoluciones")

        # Notas de crédito (FK RESTRICT a pedidos)
        if pedidos_ids:
            n = db.query(NotaCredito).filter(NotaCredito.pedido_id.in_(pedidos_ids)).delete(synchronize_session=False)
            if n:
                print(f"   ✓ {n} notas de crédito")

        # Pedidos
        if pedidos_ids:
            n = db.query(Pedido).filter(Pedido.id.in_(pedidos_ids)).delete(synchronize_session=False)
            print(f"   ✓ {n} pedidos")

        # Precios
        if locales_ids:
            n = db.query(Precio).filter(Precio.local_id.in_(locales_ids)).delete(synchronize_session=False)
            print(f"   ✓ {n} precios")

        # Operaciones de caja
        if turnos_ids:
            n = db.query(OperacionCaja).filter(OperacionCaja.turno_caja_id.in_(turnos_ids)).delete(synchronize_session=False)
            print(f"   ✓ {n} operaciones de caja")

        # Turnos de caja
        if locales_ids:
            n = db.query(TurnoCaja).filter(TurnoCaja.local_id.in_(locales_ids)).delete(synchronize_session=False)
            print(f"   ✓ {n} turnos de caja")

        # Solicitudes de transferencia (items en cascada via ondelete)
        n = db.query(SolicitudTransferencia).filter(SolicitudTransferencia.tenant_id == tenant.id).delete(synchronize_session=False)
        print(f"   ✓ {n} solicitudes de transferencia")

        # Cotizaciones (opcional, independiente de clientes)
        if not conservar_cotizaciones:
            n = db.query(Cotizacion).filter(Cotizacion.tenant_id == tenant.id).delete(synchronize_session=False)
            if n:
                print(f"   ✓ {n} cotizaciones")
        else:
            print(f"   ⏭ Cotizaciones CONSERVADAS")

        # Clientes y puntos (opcional)
        if not conservar_clientes:
            if clientes_ids:
                n = db.query(PuntosCliente).filter(PuntosCliente.cliente_id.in_(clientes_ids)).delete(synchronize_session=False)
                print(f"   ✓ {n} puntos de clientes")
            n = db.query(Cliente).filter(Cliente.tenant_id == tenant.id).delete(synchronize_session=False)
            print(f"   ✓ {n} clientes")
        else:
            print(f"   ⏭ Clientes CONSERVADOS")

        # Productos (opcional)
        if not conservar_productos:
            # Recolectar IDs de productos del tenant
            productos_ids = [p.id for p in db.query(Producto).filter(Producto.tenant_id == tenant.id).all()]
            if productos_ids:
                # 1. IngredienteReceta (FK RESTRICT producto_ingrediente_id)
                n = db.query(IngredienteReceta).filter(
                    IngredienteReceta.producto_ingrediente_id.in_(productos_ids)
                ).delete(synchronize_session=False)
                if n:
                    print(f"   ✓ {n} ingredientes de receta (como ingrediente)")

                # 2. Recetas propias del producto (con cascade en ingredientes)
                recetas_ids = [r.id for r in db.query(Receta).filter(Receta.producto_id.in_(productos_ids)).all()]
                if recetas_ids:
                    n = db.query(IngredienteReceta).filter(IngredienteReceta.receta_id.in_(recetas_ids)).delete(synchronize_session=False)
                    if n:
                        print(f"   ✓ {n} ingredientes de receta (de recetas propias)")
                    n = db.query(Receta).filter(Receta.id.in_(recetas_ids)).delete(synchronize_session=False)
                    print(f"   ✓ {n} recetas")

                # 3. DetalleOrdenProduccion (FK RESTRICT producto_id)
                from database.models import OrdenProduccion, DetalleOrdenProduccion
                ordenes_ids = [o.id for o in db.query(OrdenProduccion).filter(OrdenProduccion.local_id.in_(locales_ids)).all()] if locales_ids else []
                n = db.query(DetalleOrdenProduccion).filter(
                    DetalleOrdenProduccion.producto_id.in_(productos_ids)
                ).delete(synchronize_session=False)
                if n:
                    print(f"   ✓ {n} detalles de orden de producción")
                if ordenes_ids:
                    n = db.query(OrdenProduccion).filter(OrdenProduccion.id.in_(ordenes_ids)).delete(synchronize_session=False)
                    if n:
                        print(f"   ✓ {n} órdenes de producción")

                # 4. ItemSolicitudTransferencia (FK RESTRICT producto_id) — por si acaso
                from database.models import ItemSolicitudTransferencia
                n = db.query(ItemSolicitudTransferencia).filter(
                    ItemSolicitudTransferencia.producto_id.in_(productos_ids)
                ).delete(synchronize_session=False)
                if n:
                    print(f"   ✓ {n} items de solicitud de transferencia")

                # 5. MovimientoStockCajas residuales (FK RESTRICT producto_id)
                n = db.query(MovimientoStockCajas).filter(
                    MovimientoStockCajas.producto_id.in_(productos_ids)
                ).delete(synchronize_session=False)
                if n:
                    print(f"   ✓ {n} movimientos stock cajas residuales")

                # 6. OrdenesTrabajo (OtItem/OtLog en cascada) — FK RESTRICT producto_id via ot_items
                from database.models import OrdenTrabajo
                n = db.query(OrdenTrabajo).filter(OrdenTrabajo.tenant_id == tenant.id).delete(synchronize_session=False)
                if n:
                    print(f"   ✓ {n} órdenes de trabajo (ot_items/ot_log en cascada)")

            n = db.query(Producto).filter(Producto.tenant_id == tenant.id).delete(synchronize_session=False)
            print(f"   ✓ {n} productos")
        else:
            print(f"   ⏭ Productos CONSERVADOS")

        db.commit()
        print(f"\n✅ Reset completo del tenant [{tenant.id}] {tenant.nombre}")

        # Verificación
        restantes_pedidos = db.query(Pedido).join(Cliente).filter(Cliente.tenant_id == tenant.id).count() if conservar_clientes else 0
        restantes_productos = db.query(Producto).filter(Producto.tenant_id == tenant.id).count()
        restantes_clientes = db.query(Cliente).filter(Cliente.tenant_id == tenant.id).count()
        print(f"   Pedidos restantes:   {restantes_pedidos}")
        print(f"   Productos:           {restantes_productos}{'  (conservados)' if conservar_productos else ''}")
        print(f"   Clientes restantes:  {restantes_clientes}")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Error durante la eliminación: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 70)
    print(f"🗑️  RESET DE DATOS — TENANT ID {TENANT_ID}")
    print("=" * 70)
    print("\n⚠️  Se eliminarán TODOS los datos operativos del tenant:")
    print("   Pedidos, compras, inventario, precios, lotes, enrolamientos,")
    print("   movimientos, cajas, hojas de ruta...")
    if CONSERVAR_CLIENTES:
        print("   Clientes: CONSERVADOS (comportamiento por defecto)")
    else:
        print("   Clientes y puntos de fidelización (--eliminar-clientes activo)")
    if CONSERVAR_PRODUCTOS:
        print("   Productos: CONSERVADOS (comportamiento por defecto)")
    else:
        print("   Productos (--eliminar-productos activo)")
    print("\n✅ Se CONSERVAN: Locales, Proveedores, Usuarios, Roles")
    if CONSERVAR_PRODUCTOS:
        print("✅ Se CONSERVAN también: Productos")
    print("\n⚠️  La operación es IRREVERSIBLE\n")

    if not AUTO_CONFIRM:
        try:
            respuesta = input("¿Confirmas el reset? (SI/NO): ").strip().upper()
        except EOFError:
            respuesta = "NO"
        if respuesta != "SI":
            print("❌ Operación cancelada")
            sys.exit(0)

    eliminar_datos(TENANT_ID, conservar_clientes=CONSERVAR_CLIENTES, conservar_cotizaciones=CONSERVAR_COTIZACIONES)
