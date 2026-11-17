"""
Tests de alcance por local en inventario (change OpenSpec: add-inventario-alcance-por-local).

Contra PostgreSQL real dentro de una transacción revertida.
    DATABASE_URL=postgresql://... pytest tests/test_alcance_local.py
"""
import os
import uuid
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from database.models import (
    CategoriaProducto, Inventario, Local, MovimientoInventario, Producto, Role, TipoProducto, UnidadMedida, User,
)
from routers import inventario as r_inv
from routers import movimientos_inventario as r_mov
from schemas.movimiento_inventario import TransferenciaInventario
from services import conteo_inventario_service as conteo
from utils.alcance_local import exigir_local, local_de_alcance

DB_URL = os.getenv("DATABASE_URL", "")


# ---------------- Regla (sin BD) ----------------

def _u(rol="vendedor", local=5, superadmin=False):
    return SimpleNamespace(role=SimpleNamespace(nombre=rol), local_defecto_id=local, is_superadmin=superadmin)


@pytest.mark.parametrize("user,esperado", [
    (_u("admin", 5), None),
    (_u("Admin", 5), None),
    (_u("vendedor", 5, superadmin=True), None),
    (_u("vendedor", None), None),
    (_u("vendedor", 5), 5),
    (_u("produccion", 7), 7),
])
def test_local_de_alcance(user, esperado):
    assert local_de_alcance(user) == esperado


def test_exigir_local():
    exigir_local(_u("admin", 5), 9)
    exigir_local(_u("vendedor", 5), 5)
    with pytest.raises(HTTPException) as ex:
        exigir_local(_u("vendedor", 5), 9)
    assert ex.value.status_code == 403


# ---------------- Endpoints (con BD) ----------------

pg = pytest.mark.skipif(not DB_URL.startswith("postgresql"), reason="Requiere PostgreSQL (DATABASE_URL)")


@pytest.fixture
def db():
    engine = create_engine(DB_URL)
    conn = engine.connect()
    trans = conn.begin()
    session = Session(bind=conn, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        trans.rollback()
        conn.close()
        engine.dispose()


@pytest.fixture
def esc(db):
    def local(nombre):
        loc = Local(tenant_id=1, codigo=f"TA{uuid.uuid4().hex[:6]}", nombre=nombre, activo=True)
        db.add(loc)
        db.flush()
        return loc

    def user(rol, local_id):
        role = db.query(Role).filter(Role.tenant_id == 1, Role.nombre == rol).first()
        u = User(email=f"test-alc-{uuid.uuid4().hex[:8]}@test.cl", nombre_completo=f"Test {rol}", is_active=True,
                 role_id=role.id, tenant_id=1, is_superadmin=False, local_defecto_id=local_id)
        db.add(u)
        db.flush()
        return u

    lampa, tiltil = local("Lampa A"), local("TilTil A")
    p = Producto(tenant_id=1, nombre="Producto alcance test", sku=f"TA-{uuid.uuid4().hex[:8]}",
                 categoria_id=db.query(CategoriaProducto.id).first()[0],
                 tipo_producto_id=db.query(TipoProducto.id).first()[0],
                 unidad_medida_id=db.query(UnidadMedida.id).first()[0], activo=True)
    db.add(p)
    db.flush()
    for loc in (lampa, tiltil):
        db.add(Inventario(producto_id=p.id, local_id=loc.id, cantidad_stock=Decimal("20")))
    db.flush()
    return SimpleNamespace(lampa=lampa, tiltil=tiltil, prod=p,
                           vendedor_tiltil=user("vendedor", tiltil.id), admin=user("admin", None))


def _stock(db, prod, loc):
    inv = db.query(Inventario).filter_by(producto_id=prod.id, local_id=loc.id).one()
    db.refresh(inv)
    return inv.cantidad_stock


@pg
def test_merma_solo_en_local_propio(db, esc):
    with pytest.raises(HTTPException) as ex:
        r_inv.ajuste_merma(producto_id=esc.prod.id, local_id=esc.lampa.id, cantidad=1, motivo="",
                           db=db, current_user=esc.vendedor_tiltil)
    assert ex.value.status_code == 403
    assert _stock(db, esc.prod, esc.lampa) == Decimal("20")
    r_inv.ajuste_merma(producto_id=esc.prod.id, local_id=esc.tiltil.id, cantidad=2, motivo="",
                       db=db, current_user=esc.vendedor_tiltil)
    assert _stock(db, esc.prod, esc.tiltil) == Decimal("18")


@pg
def test_transferir_solo_desde_local_propio(db, esc):
    t = lambda o, d: TransferenciaInventario(producto_id=esc.prod.id, local_origen_id=o.id, local_destino_id=d.id, cantidad=3)
    with pytest.raises(HTTPException) as ex:
        r_mov.transferir_inventario(t(esc.lampa, esc.tiltil), db, esc.vendedor_tiltil)
    assert ex.value.status_code == 403
    r_mov.transferir_inventario(t(esc.tiltil, esc.lampa), db, esc.vendedor_tiltil)
    assert _stock(db, esc.prod, esc.lampa) == Decimal("23")
    r_mov.transferir_inventario(t(esc.lampa, esc.tiltil), db, esc.admin)  # admin: cualquier origen
    assert _stock(db, esc.prod, esc.lampa) == Decimal("20")


@pg
def test_historial_forzado_al_local_propio(db, esc):
    r_mov.transferir_inventario(TransferenciaInventario(
        producto_id=esc.prod.id, local_origen_id=esc.lampa.id, local_destino_id=esc.tiltil.id, cantidad=1), db, esc.admin)
    db.add(MovimientoInventario(producto_id=esc.prod.id, local_origen_id=esc.lampa.id, cantidad=1, tipo_movimiento="MERMA"))
    db.flush()
    movs = r_mov.listar_movimientos(skip=0, limit=100, producto_id=esc.prod.id, local_id=esc.lampa.id,
                                    tipo_movimiento=None, db=db, current_user=esc.vendedor_tiltil)
    assert movs and all(esc.tiltil.id in (m["local_origen_id"], m["local_destino_id"]) for m in movs)
    todos = r_mov.listar_movimientos(skip=0, limit=100, producto_id=esc.prod.id, local_id=None,
                                     tipo_movimiento=None, db=db, current_user=esc.admin)
    assert len(todos) == 2


@pg
def test_conteo_limitado_al_local_propio(db, esc):
    with pytest.raises(HTTPException) as ex:
        conteo.iniciar_conteo(db, esc.vendedor_tiltil, esc.lampa.id, "PARCIAL")
    assert ex.value.status_code == 403

    ajeno = conteo.iniciar_conteo(db, esc.admin, esc.lampa.id, "COMPLETO")
    propio = conteo.iniciar_conteo(db, esc.vendedor_tiltil, esc.tiltil.id, "COMPLETO")

    item_ajeno = ajeno.items[0]
    for accion in (
        lambda: conteo.obtener_detalle(db, esc.vendedor_tiltil, ajeno.id),
        lambda: conteo.registrar_cantidad(db, esc.vendedor_tiltil, ajeno.id, item_ajeno.id, 1),
        lambda: conteo.finalizar_conteo(db, esc.vendedor_tiltil, ajeno.id),
        lambda: conteo.cancelar_conteo(db, esc.vendedor_tiltil, ajeno.id),
        lambda: conteo.exportar_excel(db, esc.vendedor_tiltil, ajeno.id),
    ):
        with pytest.raises(HTTPException) as ex:
            accion()
        assert ex.value.status_code == 403

    ids_vendedor = {c["id"] for c in conteo.listar_conteos(db, esc.vendedor_tiltil, local_id=esc.lampa.id)}
    assert propio.id in ids_vendedor and ajeno.id not in ids_vendedor
    ids_admin = {c["id"] for c in conteo.listar_conteos(db, esc.admin)}
    assert {propio.id, ajeno.id} <= ids_admin
