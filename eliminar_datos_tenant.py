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
    Comision, LiquidacionComision
)

# ─── Argumentos ───────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description="Eliminar datos operativos de un tenant")
parser.add_argument("--tenant-id", type=int, required=True, help="ID del tenant a limpiar")
parser.add_argument("--eliminar-clientes", action="store_true",
                    help="También eliminar clientes y sus puntos de fidelización (por defecto se conservan)")
parser.add_argument("--si", action="store_true",
                    help="Confirmar automáticamente sin prompt interactivo")
args = parser.parse_args()

TENANT_ID = args.tenant_id
CONSERVAR_CLIENTES = not args.eliminar_clientes
AUTO_CONFIRM = args.si


def eliminar_datos(tenant_id: int, conservar_clientes: bool = False):
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

        total_a_eliminar = sum(v for k, v in counts.items() if k != "productos")
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
        print(f"\n   📦 Productos:                  CONSERVADOS ({counts['productos']})")
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

        # Clientes y puntos (opcional)
        if not conservar_clientes:
            if clientes_ids:
                n = db.query(PuntosCliente).filter(PuntosCliente.cliente_id.in_(clientes_ids)).delete(synchronize_session=False)
                print(f"   ✓ {n} puntos de clientes")
            n = db.query(Cliente).filter(Cliente.tenant_id == tenant.id).delete(synchronize_session=False)
            print(f"   ✓ {n} clientes")
        else:
            print(f"   ⏭ Clientes CONSERVADOS")

        db.commit()
        print(f"\n✅ Reset completo del tenant [{tenant.id}] {tenant.nombre}")

        # Verificación
        restantes_pedidos = db.query(Pedido).join(Cliente).filter(Cliente.tenant_id == tenant.id).count()
        restantes_productos = db.query(Producto).filter(Producto.tenant_id == tenant.id).count()
        restantes_clientes = db.query(Cliente).filter(Cliente.tenant_id == tenant.id).count()
        print(f"   Pedidos restantes:   {restantes_pedidos}")
        print(f"   Productos:           {restantes_productos} (conservados)")
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
    print("\n✅ Se CONSERVAN: Productos, Locales, Proveedores, Usuarios, Roles")
    print("\n⚠️  La operación es IRREVERSIBLE\n")

    if not AUTO_CONFIRM:
        try:
            respuesta = input("¿Confirmas el reset? (SI/NO): ").strip().upper()
        except EOFError:
            respuesta = "NO"
        if respuesta != "SI":
            print("❌ Operación cancelada")
            sys.exit(0)

    eliminar_datos(TENANT_ID, conservar_clientes=CONSERVAR_CLIENTES)
