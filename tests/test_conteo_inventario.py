"""
Tests del servicio de Conteo de Inventario (change OpenSpec: add-conteo-inventario).

Se prueban contra PostgreSQL real (índice único parcial, FOR UPDATE) porque el
TestClient de la suite está roto. Cada test corre dentro de una transacción que
se revierte al final (los commit() del servicio quedan como SAVEPOINT).

Requiere: DATABASE_URL apuntando a una BD de desarrollo migrada (alembic head)
con al menos 2 tenants, roles, categorías, tipos de producto y unidades.
    DATABASE_URL=postgresql://fme:<pw>@localhost:5432/fme_database pytest tests/test_conteo_inventario.py
"""
import os
import uuid
from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from database.models import (
    CategoriaProducto, ConteoInventario, Inventario, Local, MovimientoInventario, Producto, Role,
    TipoProducto, UnidadMedida, User,
)
from services import conteo_inventario_service as svc

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


def _user(db, tenant_id, nombre):
    role = db.query(Role).filter(Role.tenant_id == tenant_id).first()
    u = User(email=f"test-conteo-{uuid.uuid4().hex[:8]}@test.cl", nombre_completo=nombre,
             is_active=True, role_id=role.id, tenant_id=tenant_id, is_superadmin=False)
    db.add(u)
    db.flush()
    return u


def _local(db, tenant_id):
    loc = Local(tenant_id=tenant_id, codigo=f"TC{uuid.uuid4().hex[:6]}", nombre="Local Test Conteo", activo=True)
    db.add(loc)
    db.flush()
    return loc


def _producto(db, tenant_id, nombre, categoria_id, activo=True):
    p = Producto(
        tenant_id=tenant_id, nombre=nombre, sku=f"TC-{uuid.uuid4().hex[:8]}",
        categoria_id=categoria_id,
        tipo_producto_id=db.query(TipoProducto.id).first()[0],
        unidad_medida_id=db.query(UnidadMedida.id).first()[0],
        activo=activo,
    )
    db.add(p)
    db.flush()
    return p


def _stock(db, producto, local, cantidad):
    inv = Inventario(producto_id=producto.id, local_id=local.id, cantidad_stock=Decimal(str(cantidad)))
    db.add(inv)
    db.flush()
    return inv


def _stock_de(db, producto, local):
    inv = db.query(Inventario).filter_by(producto_id=producto.id, local_id=local.id).first()
    db.refresh(inv)
    return inv.cantidad_stock


@pytest.fixture
def escenario(db):
    tenants = sorted({t for (t,) in db.query(Role.tenant_id).all()})
    assert len(tenants) >= 2, "Se requieren al menos 2 tenants con roles"
    t1, t2 = tenants[0], tenants[1]
    cats = [c for (c,) in db.query(CategoriaProducto.id).order_by(CategoriaProducto.id).limit(2).all()]
    local = _local(db, t1)
    pan = _producto(db, t1, "AAA Pan test", cats[0])
    queso = _producto(db, t1, "AAB Queso test", cats[1])
    inactivo = _producto(db, t1, "AAC Inactivo test", cats[0], activo=False)
    _stock(db, pan, local, 12)
    _stock(db, queso, local, 5)
    _stock(db, inactivo, local, 3)
    return {
        "t1": t1, "t2": t2, "local": local, "pan": pan, "queso": queso, "inactivo": inactivo,
        "cat_queso": cats[1],
        "user": _user(db, t1, "Contador Uno"), "user2": _user(db, t1, "Contador Dos"),
        "ajeno": _user(db, t2, "Usuario Otro Tenant"),
    }


def _item(db, conteo_id, producto):
    from database.models import ConteoInventarioItem
    return db.query(ConteoInventarioItem).filter_by(conteo_id=conteo_id, producto_id=producto.id).one()


# ---------------- Iniciar ----------------

def test_completo_precarga_productos_activos(db, escenario):
    e = escenario
    c = svc.iniciar_conteo(db, e["user"], e["local"].id, "COMPLETO")
    assert c.estado == "EN_PROCESO" and c.usuario_creador_id == e["user"].id
    pids = {i.producto_id for i in c.items}
    assert pids == {e["pan"].id, e["queso"].id}
    assert all(i.cantidad_contada is None for i in c.items)


def test_parcial_nace_vacio(db, escenario):
    c = svc.iniciar_conteo(db, escenario["user"], escenario["local"].id, "PARCIAL")
    assert c.items == []


def test_local_de_otro_tenant_404(db, escenario):
    with pytest.raises(HTTPException) as ex:
        svc.iniciar_conteo(db, escenario["ajeno"], escenario["local"].id, "PARCIAL")
    assert ex.value.status_code == 404


def test_un_solo_conteo_abierto_por_local_409(db, escenario):
    e = escenario
    svc.iniciar_conteo(db, e["user"], e["local"].id, "PARCIAL")
    with pytest.raises(HTTPException) as ex:
        svc.iniciar_conteo(db, e["user2"], e["local"].id, "COMPLETO")
    assert ex.value.status_code == 409


# ---------------- Líneas ----------------

def test_agregar_por_categoria_y_sin_duplicados(db, escenario):
    e = escenario
    c = svc.iniciar_conteo(db, e["user"], e["local"].id, "PARCIAL")
    assert svc.agregar_items(db, e["user"], c.id, [e["queso"].id], None) == 1
    creados = svc.agregar_items(db, e["user"], c.id, [e["queso"].id], e["cat_queso"])
    det = svc.obtener_detalle(db, e["user"], c.id)
    pids = [i["producto_id"] for i in det["items"]]
    assert pids.count(e["queso"].id) == 1
    assert creados == len(pids) - 1


def test_quitar_item_solo_parcial(db, escenario):
    e = escenario
    c = svc.iniciar_conteo(db, e["user"], e["local"].id, "COMPLETO")
    item = _item(db, c.id, e["pan"])
    with pytest.raises(HTTPException) as ex:
        svc.quitar_item(db, e["user"], c.id, item.id)
    assert ex.value.status_code == 400


# ---------------- Captura ----------------

def test_captura_guarda_auditoria(db, escenario):
    e = escenario
    c = svc.iniciar_conteo(db, e["user"], e["local"].id, "COMPLETO")
    item = _item(db, c.id, e["pan"])
    it = svc.registrar_cantidad(db, e["user2"], c.id, item.id, 10)
    assert it.stock_sistema == Decimal("12") and it.cantidad_contada == Decimal("10")
    assert it.diferencia == Decimal("-2")
    assert it.usuario_captura_id == e["user2"].id and it.fecha_captura is not None


def test_cantidad_negativa_400(db, escenario):
    e = escenario
    c = svc.iniciar_conteo(db, e["user"], e["local"].id, "COMPLETO")
    item = _item(db, c.id, e["pan"])
    with pytest.raises(HTTPException) as ex:
        svc.registrar_cantidad(db, e["user"], c.id, item.id, -1)
    assert ex.value.status_code == 400


def test_correccion_recaptura_stock_actual(db, escenario):
    e = escenario
    c = svc.iniciar_conteo(db, e["user"], e["local"].id, "COMPLETO")
    item = _item(db, c.id, e["pan"])
    svc.registrar_cantidad(db, e["user"], c.id, item.id, 10)
    inv = db.query(Inventario).filter_by(producto_id=e["pan"].id, local_id=e["local"].id).one()
    inv.cantidad_stock = Decimal("11")  # venta entre capturas
    db.flush()
    it = svc.registrar_cantidad(db, e["user2"], c.id, item.id, 9)
    assert it.stock_sistema == Decimal("11") and it.diferencia == Decimal("-2")
    assert it.usuario_captura_id == e["user2"].id


# ---------------- Finalizar ----------------

def test_finalizar_ajusta_stock_y_genera_movimiento(db, escenario):
    e = escenario
    c = svc.iniciar_conteo(db, e["user"], e["local"].id, "COMPLETO")
    svc.registrar_cantidad(db, e["user"], c.id, _item(db, c.id, e["pan"]).id, 10)
    svc.finalizar_conteo(db, e["user2"], c.id)

    assert _stock_de(db, e["pan"], e["local"]) == Decimal("10")
    mov = db.query(MovimientoInventario).filter_by(tipo_movimiento="AJUSTE_CONTEO", referencia_id=c.id).one()
    assert mov.cantidad == Decimal("2") and mov.local_origen_id == e["local"].id
    assert mov.usuario_id == e["user2"].id
    db.refresh(c)
    assert c.estado == "FINALIZADO" and c.usuario_cierre_id == e["user2"].id


def test_finalizar_preserva_ventas_posteriores(db, escenario):
    e = escenario
    c = svc.iniciar_conteo(db, e["user"], e["local"].id, "COMPLETO")
    svc.registrar_cantidad(db, e["user"], c.id, _item(db, c.id, e["pan"]).id, 10)
    inv = db.query(Inventario).filter_by(producto_id=e["pan"].id, local_id=e["local"].id).one()
    inv.cantidad_stock = Decimal("9")  # se vendieron 3 tras la captura
    db.flush()
    svc.finalizar_conteo(db, e["user"], c.id)
    assert _stock_de(db, e["pan"], e["local"]) == Decimal("7")


def test_finalizar_lineas_sin_diferencia_o_no_contadas(db, escenario):
    e = escenario
    c = svc.iniciar_conteo(db, e["user"], e["local"].id, "COMPLETO")
    svc.registrar_cantidad(db, e["user"], c.id, _item(db, c.id, e["pan"]).id, 12)  # sin diferencia
    svc.finalizar_conteo(db, e["user"], c.id)
    assert _stock_de(db, e["pan"], e["local"]) == Decimal("12")
    assert _stock_de(db, e["queso"], e["local"]) == Decimal("5")  # no contado
    assert db.query(MovimientoInventario).filter_by(referencia_id=c.id, tipo_movimiento="AJUSTE_CONTEO").count() == 0
    det = svc.obtener_detalle(db, e["user"], c.id)
    queso = next(i for i in det["items"] if i["producto_id"] == e["queso"].id)
    assert queso["cantidad_contada"] is None


def test_finalizar_sin_lineas_contadas_400(db, escenario):
    e = escenario
    c = svc.iniciar_conteo(db, e["user"], e["local"].id, "COMPLETO")
    with pytest.raises(HTTPException) as ex:
        svc.finalizar_conteo(db, e["user"], c.id)
    assert ex.value.status_code == 400
    db.refresh(c)
    assert c.estado == "EN_PROCESO"


def test_finalizar_trunca_negativo_a_cero(db, escenario):
    e = escenario
    c = svc.iniciar_conteo(db, e["user"], e["local"].id, "COMPLETO")
    svc.registrar_cantidad(db, e["user"], c.id, _item(db, c.id, e["queso"]).id, 0)  # dif -5
    inv = db.query(Inventario).filter_by(producto_id=e["queso"].id, local_id=e["local"].id).one()
    inv.cantidad_stock = Decimal("2")
    db.flush()
    svc.finalizar_conteo(db, e["user"], c.id)
    assert _stock_de(db, e["queso"], e["local"]) == Decimal("0")
    item = _item(db, c.id, e["queso"])
    db.refresh(item)
    assert item.ajuste_aplicado == Decimal("-2")


def test_finalizar_rollback_ante_error(db, escenario, monkeypatch):
    e = escenario
    c = svc.iniciar_conteo(db, e["user"], e["local"].id, "COMPLETO")
    svc.registrar_cantidad(db, e["user"], c.id, _item(db, c.id, e["pan"]).id, 10)
    svc.registrar_cantidad(db, e["user"], c.id, _item(db, c.id, e["queso"]).id, 4)

    original = svc._stock_actual
    llamadas = {"n": 0}

    def falla_en_segunda(*a, **kw):
        llamadas["n"] += 1
        if llamadas["n"] == 2:
            raise RuntimeError("falla simulada")
        return original(*a, **kw)

    monkeypatch.setattr(svc, "_stock_actual", falla_en_segunda)
    with pytest.raises(RuntimeError):
        svc.finalizar_conteo(db, e["user"], c.id)
    monkeypatch.setattr(svc, "_stock_actual", original)

    assert _stock_de(db, e["pan"], e["local"]) == Decimal("12")
    assert _stock_de(db, e["queso"], e["local"]) == Decimal("5")
    assert db.get(ConteoInventario, c.id).estado == "EN_PROCESO"


# ---------------- Cancelar / inmutabilidad ----------------

def test_cancelar_no_toca_stock(db, escenario):
    e = escenario
    c = svc.iniciar_conteo(db, e["user"], e["local"].id, "COMPLETO")
    svc.registrar_cantidad(db, e["user"], c.id, _item(db, c.id, e["pan"]).id, 1)
    svc.cancelar_conteo(db, e["user"], c.id)
    assert _stock_de(db, e["pan"], e["local"]) == Decimal("12")
    db.refresh(c)
    assert c.estado == "CANCELADO"


def test_conteo_cerrado_inmutable_409(db, escenario):
    e = escenario
    c = svc.iniciar_conteo(db, e["user"], e["local"].id, "PARCIAL")
    svc.agregar_items(db, e["user"], c.id, [e["pan"].id], None)
    item = _item(db, c.id, e["pan"])
    svc.registrar_cantidad(db, e["user"], c.id, item.id, 10)
    svc.finalizar_conteo(db, e["user"], c.id)
    for accion in (
        lambda: svc.registrar_cantidad(db, e["user"], c.id, item.id, 5),
        lambda: svc.agregar_items(db, e["user"], c.id, [e["queso"].id], None),
        lambda: svc.finalizar_conteo(db, e["user"], c.id),
        lambda: svc.cancelar_conteo(db, e["user"], c.id),
    ):
        with pytest.raises(HTTPException) as ex:
            accion()
        assert ex.value.status_code == 409


# ---------------- Listado / tenant / Excel ----------------

def test_listado_filtra_por_local_y_tenant(db, escenario):
    e = escenario
    c = svc.iniciar_conteo(db, e["user"], e["local"].id, "COMPLETO")
    svc.registrar_cantidad(db, e["user"], c.id, _item(db, c.id, e["pan"]).id, 10)
    lista = svc.listar_conteos(db, e["user"], local_id=e["local"].id)
    assert [x["id"] for x in lista] == [c.id]
    assert lista[0]["total_items"] == 2 and lista[0]["items_contados"] == 1 and lista[0]["items_con_diferencia"] == 1
    assert svc.listar_conteos(db, e["ajeno"], local_id=e["local"].id) == []


def test_conteo_de_otro_tenant_404(db, escenario):
    e = escenario
    c = svc.iniciar_conteo(db, e["user"], e["local"].id, "PARCIAL")
    for accion in (
        lambda: svc.obtener_detalle(db, e["ajeno"], c.id),
        lambda: svc.agregar_items(db, e["ajeno"], c.id, [e["pan"].id], None),
        lambda: svc.exportar_excel(db, e["ajeno"], c.id),
    ):
        with pytest.raises(HTTPException) as ex:
            accion()
        assert ex.value.status_code == 404


def test_exportar_excel(db, escenario):
    from io import BytesIO
    from openpyxl import load_workbook

    e = escenario
    c = svc.iniciar_conteo(db, e["user"], e["local"].id, "COMPLETO")
    svc.registrar_cantidad(db, e["user"], c.id, _item(db, c.id, e["pan"]).id, 10)
    svc.finalizar_conteo(db, e["user"], c.id)
    contenido, nombre = svc.exportar_excel(db, e["user"], c.id)
    assert nombre.endswith(".xlsx")
    ws = load_workbook(BytesIO(contenido)).active
    filas = [r for r in ws.iter_rows(values_only=True)]
    header_idx = next(i for i, r in enumerate(filas) if r and r[0] == "SKU")
    datos = filas[header_idx + 1: header_idx + 3]
    assert {r[1] for r in datos} == {"AAA Pan test", "AAB Queso test"}
    pan = next(r for r in datos if r[1] == "AAA Pan test")
    assert pan[4] == 12 and pan[5] == 10 and pan[6] == -2
    assert any(r and r[0] == "Total faltantes" and r[1] == -2 for r in filas)


def test_exportar_excel_en_proceso_muestra_stock_actual_y_hora_chile(db, escenario):
    from io import BytesIO
    from openpyxl import load_workbook

    e = escenario
    c = svc.iniciar_conteo(db, e["user"], e["local"].id, "COMPLETO")
    contenido, _ = svc.exportar_excel(db, e["user"], c.id)
    filas = list(load_workbook(BytesIO(contenido)).active.iter_rows(values_only=True))
    header_idx = next(i for i, r in enumerate(filas) if r and r[0] == "SKU")
    datos = {r[1]: r for r in filas[header_idx + 1: header_idx + 3]}
    assert datos["AAA Pan test"][4] == 12 and datos["AAA Pan test"][5] == "No contado"
    assert datos["AAB Queso test"][4] == 5
    iniciado = next(r[1] for r in filas if r and r[0] == "Iniciado por")
    esperado = c.fecha_inicio.astimezone(svc.CHILE_TZ).strftime("%d-%m-%Y %H:%M")
    assert esperado in iniciado
