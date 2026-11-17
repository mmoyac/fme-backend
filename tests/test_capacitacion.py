"""
Tests del Centro de Capacitación (change OpenSpec: add-centro-capacitacion).

El TestClient de la suite está roto, así que la API se prueba llamando directo a las
funciones del router con el tenant y los módulos simulados. El 401 sin token se verifica
con curl contra la API local (ver tasks.md 2.2).
"""
import json
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from routers import capacitacion as router
from services import capacitacion_service as svc


def _escribir(raiz, modulo, lecciones, archivos=None):
    carpeta = raiz / modulo
    carpeta.mkdir(parents=True, exist_ok=True)
    for nombre in archivos if archivos is not None else [l["archivo"] for l in lecciones]:
        (carpeta / nombre).write_text(f"<html>{modulo}/{nombre}</html>", encoding="utf-8")
    (carpeta / "manifest.json").write_text(json.dumps({"lecciones": lecciones}), encoding="utf-8")


def _l(slug, archivo=None):
    return {"slug": slug, "titulo": slug.title(), "descripcion": "d", "archivo": archivo or f"{slug}.html"}


@pytest.fixture
def raiz(tmp_path):
    _escribir(tmp_path, "general", [_l("primeros-pasos")])
    _escribir(tmp_path, "inventario", [_l("b"), _l("a"), _l("c")])
    _escribir(tmp_path, "cobranza", [_l("cheques")])
    return tmp_path


@pytest.fixture
def cat(raiz, monkeypatch):
    catalogo = svc.cargar_catalogo(raiz)
    monkeypatch.setattr(svc, "catalogo", lambda: catalogo)
    return catalogo


# --- Servicio --------------------------------------------------------------------------------

def test_orden_del_manifiesto_respetado(cat):
    assert [l["slug"] for l in cat["inventario"]] == ["b", "a", "c"]


def test_manifiesto_json_invalido_se_omite(raiz):
    (raiz / "inventario" / "manifest.json").write_text("{no json", encoding="utf-8")
    cat = svc.cargar_catalogo(raiz)
    assert "inventario" not in cat and "general" in cat


def test_slug_invalido_invalida_manifiesto(raiz):
    _escribir(raiz, "inventario", [_l("bien"), {**_l("x"), "slug": "../main"}], archivos=["bien.html", "x.html"])
    assert svc.cargar_manifiesto(raiz, "inventario") is None


def test_slug_duplicado_invalida_manifiesto(raiz):
    _escribir(raiz, "inventario", [_l("a"), _l("a")])
    assert svc.cargar_manifiesto(raiz, "inventario") is None


def test_archivo_fuera_de_la_carpeta_rechazado(raiz):
    (raiz / "secreto.html").write_text("x", encoding="utf-8")
    _escribir(raiz, "inventario", [_l("a", "../secreto.html")], archivos=[])
    assert svc.cargar_manifiesto(raiz, "inventario") is None


def test_archivo_inexistente_invalida_manifiesto(raiz):
    _escribir(raiz, "inventario", [_l("zz")], archivos=[])
    assert svc.cargar_manifiesto(raiz, "inventario") is None


def test_leer_leccion_rechaza_traversal_sin_leer_disco(cat):
    assert svc.leer_leccion("inventario", "../main") is None
    assert svc.leer_leccion("..", "a") is None
    assert svc.leer_leccion("inventario", "..%2F.env") is None
    assert svc.leer_leccion("inventario", "a") == "<html>inventario/a.html</html>"


def test_secciones_general_primero_y_superadmin_ve_todo(cat):
    assert [s["modulo"] for s in svc.secciones_visibles(None)] == ["general", "inventario", "cobranza"]


def test_catalogo_real_es_valido():
    """Los manifiestos versionados en capacitacion/ cargan completos."""
    cat = svc.cargar_catalogo(svc.RAIZ)
    for modulo in ("general", "inventario"):
        crudo = json.loads((svc.RAIZ / modulo / "manifest.json").read_text(encoding="utf-8"))["lecciones"]
        assert len(cat.get(modulo, [])) == len(crudo)


# --- API -------------------------------------------------------------------------------------

def _ctx(monkeypatch, tenant_id, modulos, superadmin=False):
    monkeypatch.setattr(router, "tenant_de_request", lambda request, db: tenant_id)
    monkeypatch.setattr(router, "modulos_de_tenant", lambda db, t: set(modulos) if t else set())
    return SimpleNamespace(is_superadmin=superadmin)


def test_indice_con_inventario(cat, monkeypatch):
    user = _ctx(monkeypatch, 1, {"inventario", "ventas"})
    secciones = router.indice(None, user, None)["secciones"]
    assert [s["modulo"] for s in secciones] == ["general", "inventario"]
    assert [l["slug"] for l in secciones[1]["lecciones"]] == ["b", "a", "c"]


def test_indice_sin_inventario_y_contratado_sin_lecciones(cat, monkeypatch):
    user = _ctx(monkeypatch, 1, {"ventas", "produccion"})
    secciones = router.indice(None, user, None)["secciones"]
    assert [s["modulo"] for s in secciones] == ["general"]


def test_general_visible_sin_modulos(cat, monkeypatch):
    user = _ctx(monkeypatch, 1, set())
    assert [s["modulo"] for s in router.indice(None, user, None)["secciones"]] == ["general"]


def test_superadmin_sin_tenant_ve_todo(cat, monkeypatch):
    user = _ctx(monkeypatch, None, set(), superadmin=True)
    assert [s["modulo"] for s in router.indice(None, user, None)["secciones"]] == ["general", "inventario", "cobranza"]


def test_usuario_sin_tenant_no_superadmin_solo_general(cat, monkeypatch):
    user = _ctx(monkeypatch, None, set())
    assert [s["modulo"] for s in router.indice(None, user, None)["secciones"]] == ["general"]


def test_leccion_modulo_contratado(cat, monkeypatch):
    user = _ctx(monkeypatch, 1, {"inventario"})
    resp = router.leccion("inventario", "a", None, user, None)
    assert resp.status_code == 200
    assert resp.body == b"<html>inventario/a.html</html>"
    assert resp.headers["cache-control"] == "no-store"
    assert resp.headers["x-content-type-options"] == "nosniff"


def test_leccion_general_sin_modulos(cat, monkeypatch):
    user = _ctx(monkeypatch, 1, set())
    assert router.leccion("general", "primeros-pasos", None, user, None).status_code == 200


def test_leccion_modulo_no_contratado_403(cat, monkeypatch):
    user = _ctx(monkeypatch, 1, {"inventario"})
    with pytest.raises(HTTPException) as e:
        router.leccion("cobranza", "cheques", None, user, None)
    assert e.value.status_code == 403


@pytest.mark.parametrize("modulo,slug", [
    ("inventario", "no-existe"),
    ("desconocido", "a"),
    ("..", "main"),
    ("inventario", "../main"),
    ("inventario", "..%2F.env"),
])
def test_leccion_404(cat, monkeypatch, modulo, slug):
    user = _ctx(monkeypatch, 1, {"inventario"})
    with pytest.raises(HTTPException) as e:
        router.leccion(modulo, slug, None, user, None)
    assert e.value.status_code == 404
