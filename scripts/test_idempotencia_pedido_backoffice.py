"""Prueba de idempotencia de POST /api/pedidos/backoffice contra la BD local.
Todo corre dentro de una transacción externa que se revierte al final: no deja datos.
Uso: python test_idempotencia.py  (desde fme-backend, con DATABASE_URL apuntando a localhost)
"""
import sys, os, uuid
sys.path.insert(0, os.getcwd())

from sqlalchemy.orm import Session
from sqlalchemy import func
from database.database import engine
from database.models import (Pedido, Cliente, MedioPago, Producto, Inventario, TurnoCaja,
                             CanalVenta, User, MovimientoInventario, Local)
from routers.pedidos import crear_pedido_backoffice
from schemas.pedido import PedidoCreateBackoffice

conn = engine.connect()
outer = conn.begin()
db = Session(bind=conn, join_transaction_mode="create_savepoint")

try:
    turno = db.query(TurnoCaja).filter(TurnoCaja.estado == 'ABIERTO').order_by(TurnoCaja.id.desc()).first()
    local = db.query(Local).get(turno.local_id)
    tenant_id = local.tenant_id
    user = db.query(User).filter(User.tenant_id == tenant_id).first()
    cliente = db.query(Cliente).filter(Cliente.tenant_id == tenant_id).first()
    medio = db.query(MedioPago).filter((MedioPago.permite_cheque == False) | (MedioPago.permite_cheque == None),
                                       func.coalesce(MedioPago.plazo_dias, 0) == 0).first()
    canal = db.query(CanalVenta).filter(CanalVenta.entrega_inmediata == True).first()
    inv = (db.query(Inventario).join(Producto, Producto.id == Inventario.producto_id)
           .filter(Inventario.local_id == local.id, Producto.tenant_id == tenant_id,
                   Inventario.cantidad_stock > 5).first())
    prod = db.query(Producto).get(inv.producto_id)
    print(f"tenant={tenant_id} local={local.id} turno={turno.id} user={user.id} cliente={cliente.id} "
          f"medio={medio.id}({medio.nombre}) canal={canal.id if canal else None} producto={prod.id} stock={inv.cantidad_stock}")

    stock_antes = float(inv.cantidad_stock)
    pedidos_antes = db.query(Pedido).filter(Pedido.tenant_id == tenant_id).count()
    cu = str(uuid.uuid4())

    def payload():
        return PedidoCreateBackoffice(
            cliente_id=cliente.id, cliente_nombre=cliente.nombre or 'x', cliente_email='x@x.cl',
            cliente_telefono='1', direccion_entrega='mostrador', local_id=local.id,
            medio_pago_id=medio.id, canal_venta_id=canal.id if canal else None,
            items=[{'sku': prod.sku, 'producto_id': prod.id, 'cantidad': 1, 'precio_unitario_venta': 1000}],
            client_uuid=cu,
        )

    r1 = crear_pedido_backoffice(payload(), db=db, current_user=user)
    r2 = crear_pedido_backoffice(payload(), db=db, current_user=user)

    db.expire_all()
    stock_despues = float(db.query(Inventario).get(inv.id).cantidad_stock)
    pedidos_despues = db.query(Pedido).filter(Pedido.tenant_id == tenant_id).count()
    nuevo = db.query(Pedido).filter(Pedido.client_uuid == cu).all()

    import json
    body2 = json.loads(r2.body) if hasattr(r2, 'body') else r2
    print("r1:", {k: r1[k] for k in ('pedido_id', 'numero_pedido', 'estado')})
    print("r2 status:", getattr(r2, 'status_code', 201), {k: body2[k] for k in ('pedido_id', 'numero_pedido', 'duplicado')})
    print(f"pedidos creados: {pedidos_despues - pedidos_antes} (esperado 1)")
    print(f"stock descontado: {stock_antes - stock_despues} (esperado 1)")
    print(f"turno_caja_id del pedido: {nuevo[0].turno_caja_id} (esperado {turno.id})  origen={nuevo[0].origen}")
    ok = (pedidos_despues - pedidos_antes == 1 and stock_antes - stock_despues == 1
          and body2['pedido_id'] == r1['pedido_id'] and body2.get('duplicado') is True
          and getattr(r2, 'status_code', None) == 200)
    print("RESULTADO:", "OK" if ok else "FALLA")
finally:
    db.close()
    outer.rollback()
    conn.close()
    print("(transacción revertida, BD sin cambios)")
