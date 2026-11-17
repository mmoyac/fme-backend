"""
Tests de seguridad del módulo inventario (change OpenSpec: fix-seguridad-inventario).

Llaman directo a las funciones de los routers contra PostgreSQL real, dentro de una
transacción que se revierte (el TestClient de la suite está roto).
    DATABASE_URL=postgresql://... pytest tests/test_seguridad_inventario.py
"""
import os
import uuid

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from database.models import (
    CategoriaProducto, EstadoEnrolamiento, Local, Producto, Proveedor, Role, SolicitudTransferencia, StockCajasProveedor,
    TipoProducto, UnidadMedida, User,
)
from routers import solicitudes_transferencia as st
from routers import stock_cajas as sc
from schemas.solicitud_transferencia import (
    ItemSolicitudTransferenciaCreate, SolicitudTransferenciaCreate, SolicitudTransferenciaUpdate,
)
from schemas.stock_cajas import ActualizacionStockCajas, ReservaStockCajas, StockCajasProveedorUpdate

DB_URL = os.getenv("DATABASE_URL", "")
pytestmark = pytest.mark.skipif(not DB_URL.startswith("postgresql"), reason="Requiere PostgreSQL (DATABASE_URL)")


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


def _user(db, tenant_id, rol, local_id=None):
    role = db.query(Role).filter(Role.tenant_id == tenant_id, Role.nombre == rol).first()
    u = User(email=f"test-seg-{uuid.uuid4().hex[:8]}@test.cl", nombre_completo=f"Test {rol}", is_active=True,
             role_id=role.id, tenant_id=tenant_id, is_superadmin=False, local_defecto_id=local_id)
    db.add(u)
    db.flush()
    return u


def _local(db, tenant_id, nombre):
    loc = Local(tenant_id=tenant_id, codigo=f"TS{uuid.uuid4().hex[:6]}", nombre=nombre, activo=True)
    db.add(loc)
    db.flush()
    return loc


def _producto(db, tenant_id):
    p = Producto(tenant_id=tenant_id, nombre="Producto seguridad test", sku=f"TS-{uuid.uuid4().hex[:8]}",
                 categoria_id=db.query(CategoriaProducto.id).first()[0],
                 tipo_producto_id=db.query(TipoProducto.id).first()[0],
                 unidad_medida_id=db.query(UnidadMedida.id).first()[0], activo=True)
    db.add(p)
    db.flush()
    return p


@pytest.fixture
def esc(db):
    t1, t2 = 1, 2
    lampa, tiltil = _local(db, t1, "Lampa T"), _local(db, t1, "TilTil T")
    local_ajeno = _local(db, t2, "Local ajeno")
    prod, prod_ajeno = _producto(db, t1), _producto(db, t2)
    return {
        "lampa": lampa, "tiltil": tiltil, "local_ajeno": local_ajeno, "prod": prod, "prod_ajeno": prod_ajeno,
        "solicitante": _user(db, t1, "vendedor", tiltil.id),
        "otro_vendedor": _user(db, t1, "vendedor", lampa.id),
        "admin": _user(db, t1, "admin"),
        "ajeno": _user(db, t2, "admin"),
    }


def _crear(db, e, user=None, **kw):
    data = SolicitudTransferenciaCreate(
        local_origen_id=kw.get("origen", e["lampa"].id),
        local_destino_id=kw.get("destino", e["tiltil"].id),
        items=[ItemSolicitudTransferenciaCreate(producto_id=kw.get("producto", e["prod"].id), cantidad_solicitada=5)],
        tenant_id=kw.get("tenant_id"), usuario_solicitante_id=kw.get("solicitante_id"), estado_id=kw.get("estado_id"),
    )
    return st.crear_solicitud_transferencia(data, db, user or e["solicitante"])


# ---------------- Solicitudes ----------------

def test_crear_fija_tenant_solicitante_y_estado_desde_servidor(db, esc):
    r = _crear(db, esc, tenant_id=2, solicitante_id=esc["ajeno"].id, estado_id=3)  # 3 = FINALIZADO
    s = db.get(SolicitudTransferencia, r.solicitud_id)
    assert s.tenant_id == 1
    assert s.usuario_solicitante_id == esc["solicitante"].id
    assert db.get(EstadoEnrolamiento, s.estado_id).codigo == "PENDIENTE"


@pytest.mark.parametrize("campo", ["origen", "producto"])
def test_crear_con_local_o_producto_de_otro_tenant_404(db, esc, campo):
    kw = {"origen": esc["local_ajeno"].id} if campo == "origen" else {"producto": esc["prod_ajeno"].id}
    with pytest.raises(HTTPException) as ex:
        _crear(db, esc, **kw)
    assert ex.value.status_code == 404


def test_obtener_y_editar_solicitud_de_otro_tenant_404(db, esc):
    r = _crear(db, esc)
    with pytest.raises(HTTPException) as ex:
        st.obtener_solicitud_transferencia(r.solicitud_id, db, esc["ajeno"])
    assert ex.value.status_code == 404
    with pytest.raises(HTTPException) as ex:
        st.actualizar_solicitud_transferencia(r.solicitud_id, SolicitudTransferenciaUpdate(nota="x"), db, esc["ajeno"])
    assert ex.value.status_code == 404


def test_listado_solo_del_tenant_del_usuario(db, esc):
    r = _crear(db, esc)
    assert r.solicitud_id in {x.solicitud_id for x in st.listar_solicitudes_transferencia(db, esc["admin"])}
    assert r.solicitud_id not in {x.solicitud_id for x in st.listar_solicitudes_transferencia(db, esc["ajeno"])}


def test_eliminar_restringido(db, esc):
    r = _crear(db, esc)
    with pytest.raises(HTTPException) as ex:
        st.eliminar_solicitud_transferencia(r.solicitud_id, db, esc["ajeno"])
    assert ex.value.status_code == 404
    with pytest.raises(HTTPException) as ex:
        st.eliminar_solicitud_transferencia(r.solicitud_id, db, esc["otro_vendedor"])
    assert ex.value.status_code == 403
    st.eliminar_solicitud_transferencia(r.solicitud_id, db, esc["solicitante"])
    assert db.get(SolicitudTransferencia, r.solicitud_id) is None


def test_admin_puede_eliminar(db, esc):
    r = _crear(db, esc)
    st.eliminar_solicitud_transferencia(r.solicitud_id, db, esc["admin"])
    assert db.get(SolicitudTransferencia, r.solicitud_id) is None


def test_editar_items_con_producto_de_otro_tenant_404(db, esc):
    r = _crear(db, esc)
    upd = SolicitudTransferenciaUpdate(items=[ItemSolicitudTransferenciaCreate(
        producto_id=esc["prod_ajeno"].id, cantidad_solicitada=1)])
    with pytest.raises(HTTPException) as ex:
        st.actualizar_solicitud_transferencia(r.solicitud_id, upd, db, esc["solicitante"])
    assert ex.value.status_code == 404


# ---------------- Stock de Cajas ----------------

@pytest.fixture
def stock_ajeno(db, esc):
    prov = db.query(Proveedor).filter(Proveedor.tenant_id == 2).first()
    stock = StockCajasProveedor(producto_id=esc["prod_ajeno"].id, proveedor_id=prov.id, cajas_disponibles=10,
                                cajas_totales_recibidas=10, cajas_totales_vendidas=0)
    db.add(stock)
    db.flush()
    return stock


def test_ajustar_cajas_de_otro_tenant_404(db, esc, stock_ajeno):
    with pytest.raises(HTTPException) as ex:
        sc.ajustar_stock_manual(stock_ajeno.producto_id, stock_ajeno.proveedor_id,
                                StockCajasProveedorUpdate(cajas_disponibles=0), db, esc["admin"])
    assert ex.value.status_code == 404
    db.refresh(stock_ajeno)
    assert stock_ajeno.cajas_disponibles == 10


def test_actualizar_desde_enrolamiento_otro_tenant_404(db, esc, stock_ajeno):
    with pytest.raises(HTTPException) as ex:
        sc.actualizar_stock_desde_enrolamiento(ActualizacionStockCajas(
            producto_id=stock_ajeno.producto_id, proveedor_id=stock_ajeno.proveedor_id, cajas_a_sumar=5), db, esc["admin"])
    assert ex.value.status_code == 404
    db.refresh(stock_ajeno)
    assert stock_ajeno.cajas_disponibles == 10


def test_reservar_para_pedido_otro_tenant_404(db, esc, stock_ajeno):
    with pytest.raises(HTTPException) as ex:
        sc.reservar_stock_para_pedido(ReservaStockCajas(items=[{
            "producto_id": stock_ajeno.producto_id, "proveedor_id": stock_ajeno.proveedor_id, "cajas_requeridas": 1}]),
            db, esc["admin"])
    assert ex.value.status_code == 404
