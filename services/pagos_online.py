"""Núcleo de pagos en línea de pedidos (change add-pasarelas-pago; portado de EffiCheck `app/pagos.py`).

Reglas no negociables:
1. El resultado lo decide SIEMPRE el backend consultando al proveedor: el retorno del navegador y la notificación solo
   identifican la transacción.
2. Ninguna llamada HTTP al proveedor dentro de una transacción con bloqueos: se guarda la intención y se hace commit;
   luego se llama al proveedor; luego se guarda su respuesta en otra transacción.
3. Confirmación idempotente: retorno, notificación y conciliación compiten por `SELECT ... FOR UPDATE` de la intención
   y solo el primero aplica el pago al pedido.
4. Monto confirmado distinto del de la intención → EN_REVISION, sin aplicar.
5. Pedido ya pagado o cancelado al llegar un aprobado → EN_REVISION (posible devolución), sin aplicar.
6. Una intención RECHAZADO ya no acepta un aprobado posterior: solo se rechaza con una respuesta definitiva.
7. Conciliación periódica: INICIADO de más de 5 min y EXPIRADO de las últimas 24 h.

Todo es síncrono a propósito (ver incidente 2026-11-11: nada async con BD síncrona); los routers lo llaman en el
threadpool.
"""
import base64
import logging
import re
import threading
import time
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.orm import Session

from database.database import SessionLocal
from database.models import EstadoPedido, MedioPago, PagoOnline, PasarelaPago, Pedido, Tenant
from services.pasarelas import MEDIO_PAGO_POR_PROVEEDOR, adaptador_de, cifrado, config
from services.pasarelas.base import (APROBADO, PENDIENTE, RECHAZADO, ErrorPasarela, Intencion, Pasarela, Redireccion,
                                     Resultado, Urls)

log = logging.getLogger(__name__)

MINUTOS_INTENCION = 15
RE_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
ESTADOS_FINALES = ("CONFIRMADO", "RECHAZADO", "EN_REVISION")


class ErrorPago(ValueError):
    pass


class ErrorNoEncontrado(ErrorPago):
    pass


# Punto único para abrir sesiones propias (los tests lo pueden reemplazar).
abrir_sesion = SessionLocal


def _ahora() -> datetime:
    return datetime.now(timezone.utc)


# ----------------------------------------------------------------------------- pasarelas
def puede_cobrar(p: PasarelaPago, demo: bool = False) -> bool:
    """Activa, con adaptador, y en producción nunca la simulada; las de integración solo en modo demo."""
    if not p.activo or not adaptador_de(p.proveedor):
        return False
    if not config.es_produccion():
        return True
    if p.proveedor == "SIMULADA":
        return False
    return p.ambiente == "PRODUCCION" or demo


def pasarelas_disponibles(db: Session, tenant_id: int, demo: bool = False) -> list[dict]:
    """Pasarelas con las que el cliente puede pagar, en el orden configurado."""
    salida = []
    q = (db.query(PasarelaPago).filter(PasarelaPago.tenant_id == tenant_id, PasarelaPago.activo.is_(True))
         .order_by(PasarelaPago.orden, PasarelaPago.id))
    for p in q:
        if puede_cobrar(p, demo):
            a = adaptador_de(p.proveedor)
            salida.append({"id": p.id, "nombre_visible": p.nombre_visible, "proveedor": p.proveedor,
                           "requiere_email": a.requiere_email, "monto_minimo": a.monto_minimo})
    return salida


def a_pasarela(p: PasarelaPago) -> Pasarela:
    return Pasarela(id=p.id, tenant_id=p.tenant_id, proveedor=p.proveedor, ambiente=p.ambiente,
                    nombre_visible=p.nombre_visible,
                    credenciales=cifrado.descifrar(p.credenciales_cifradas, p.tenant_id, p.id))


def cargar_pasarela(db: Session, pasarela_id: int, tenant_id: int) -> Pasarela:
    p = db.query(PasarelaPago).filter(PasarelaPago.id == pasarela_id, PasarelaPago.tenant_id == tenant_id).first()
    if not p:
        raise ErrorNoEncontrado("Pasarela no encontrada")
    return a_pasarela(p)


def orden_comercio(pago_id: uuid.UUID) -> str:
    """UUID en base32 sin relleno: 26 caracteres (el máximo de Webpay; sirve a todos los proveedores)."""
    return base64.b32encode(pago_id.bytes).decode().rstrip("=")


def intencion_de(p: PagoOnline, asunto: str = "") -> Intencion:
    return Intencion(id=str(p.id), orden_comercio=p.orden_comercio, monto=int(p.monto), asunto=asunto,
                     email=p.email_pagador, expira_en=p.expira_en, token=p.token_pasarela,
                     id_transaccion=p.id_transaccion_proveedor)


def _expirar_vencidas(db: Session, tenant_id: int | None = None) -> None:
    sql = "UPDATE pagos_online SET estado = 'EXPIRADO' WHERE estado = 'INICIADO' AND expira_en <= now()"
    if tenant_id is not None:
        sql += " AND tenant_id = :t"
    db.execute(text(sql), {"t": tenant_id})


# ----------------------------------------------------------------------------- crear
def crear_intencion(db: Session, tenant_id: int, pedido_id: int, token_seguimiento: str, pasarela_id: int | None,
                    email: str | None, url_sitio: str | None, demo: bool = False) -> dict:
    """Guarda la intención (bloquea el pedido por 15 minutos) y hace commit. Todavía no habla con el proveedor.

    Si ya hay una intención vigente del pedido con la misma pasarela y su URL de pago, se reutiliza.
    """
    _expirar_vencidas(db, tenant_id)
    pedido = (db.query(Pedido).filter(Pedido.id == pedido_id, Pedido.tenant_id == tenant_id).with_for_update().first())
    if not pedido or not token_seguimiento or pedido.token_seguimiento != token_seguimiento:
        raise ErrorNoEncontrado("Pedido no encontrado")
    if pedido.es_pagado:
        raise ErrorPago("El pedido ya está pagado")
    estado = pedido.estado_pedido.codigo if pedido.estado_pedido else None
    if estado == "CANCELADO":
        raise ErrorPago("El pedido está cancelado")
    # Productos + delivery (add-delivery-por-comuna): monto_total no incluye el costo de delivery
    monto = Decimal(str(round(float(pedido.monto_total or 0) + float(pedido.costo_delivery or 0))))
    if monto <= 0:
        raise ErrorPago("El pedido no tiene monto a pagar")

    disponibles = pasarelas_disponibles(db, tenant_id, demo)
    if not disponibles:
        raise ErrorPago("El pago en línea no está habilitado para esta tienda")
    if pasarela_id is None:
        if len(disponibles) > 1:
            raise ErrorPago("Elija el medio de pago")
        elegida = disponibles[0]
    else:
        elegida = next((p for p in disponibles if p["id"] == pasarela_id), None)
        if not elegida:
            raise ErrorNoEncontrado("Medio de pago no disponible")
    if elegida["monto_minimo"] and monto < elegida["monto_minimo"]:
        raise ErrorPago(f"El monto mínimo para pagar con {elegida['nombre_visible']} es "
                        f"${elegida['monto_minimo']:,}".replace(",", "."))

    vigente = (db.query(PagoOnline).filter(PagoOnline.pedido_id == pedido.id, PagoOnline.estado == "INICIADO",
                                           PagoOnline.expira_en > _ahora()).first())
    if vigente:
        if vigente.pasarela_id == elegida["id"] and vigente.url_pago and Decimal(vigente.monto) == monto:
            db.commit()
            return {"id": str(vigente.id), "reutilizada": True, "url_pago": vigente.url_pago}
        raise ErrorPago("Ya hay un pago en curso para este pedido. Termínalo o espera unos minutos para intentar "
                        "con otro medio de pago.")

    email = (email or "").strip() or (pedido.cliente.email if pedido.cliente else None) or None
    if email and not RE_EMAIL.match(email):
        raise ErrorPago("El correo no tiene un formato válido")
    if elegida["requiere_email"] and not email:
        raise ErrorPago("Ingrese un correo para recibir el comprobante del pago")

    pid = uuid.uuid4()
    db.add(PagoOnline(id=str(pid), tenant_id=tenant_id, pedido_id=pedido.id, pasarela_id=elegida["id"], monto=monto,
                      estado="INICIADO", expira_en=_ahora() + timedelta(minutes=MINUTOS_INTENCION),
                      orden_comercio=orden_comercio(pid), email_pagador=email, url_sitio=url_sitio))
    db.commit()
    return {"id": str(pid), "reutilizada": False}


def iniciar_en_proveedor(tenant_id: int, pago_id: str, urls_base: dict) -> Redireccion:
    """Crea la transacción en el proveedor para una intención ya guardada y devuelve la redirección del cliente.

    `urls_base`: {"api": base pública del backend, "notificacion": base para el webhook, "sitio": origen de la landing}.
    """
    with abrir_sesion() as db:
        p = db.query(PagoOnline).filter(PagoOnline.id == pago_id, PagoOnline.tenant_id == tenant_id).first()
        if not p:
            raise ErrorNoEncontrado("Pago no encontrado")
        pasarela = cargar_pasarela(db, p.pasarela_id, tenant_id)
        tenant = db.get(Tenant, tenant_id)
        numero = p.pedido.numero_pedido if p.pedido else ""
        asunto = f"Pedido {numero} {tenant.nombre if tenant else ''}".strip()
        intencion = intencion_de(p, asunto)
    prov = pasarela.proveedor.lower()
    urls = Urls(retorno=f"{urls_base['api']}/api/pagos/retorno/{prov}?tenant={tenant_id}",
                notificacion=f"{urls_base['notificacion']}/api/pagos/webhook/{prov}?tenant={tenant_id}",
                portal=urls_base["sitio"])
    try:
        r = adaptador_de(pasarela.proveedor).crear(pasarela, intencion, urls)
    except ErrorPasarela as e:
        log.warning("Pasarela %s no creó el pago %s: %s", pasarela.proveedor, pago_id, e.mensaje)
        with abrir_sesion() as db:   # libera el pedido
            db.execute(text("UPDATE pagos_online SET estado = 'RECHAZADO', respuesta_proveedor = CAST(:r AS jsonb) "
                            "WHERE id = CAST(:i AS uuid) AND estado = 'INICIADO'"),
                       {"i": pago_id, "r": _json({"error": e.mensaje, "codigo": e.codigo})})
            db.commit()
        raise ErrorPago(f"No se pudo iniciar el pago con {pasarela.nombre_visible}: {e.mensaje}") from e
    with abrir_sesion() as db:
        db.execute(text("UPDATE pagos_online SET token_pasarela = :t, id_transaccion_proveedor = :x, url_pago = :u "
                        "WHERE id = CAST(:i AS uuid)"),
                   {"t": r.token, "x": r.id_transaccion, "u": r.url if r.metodo == "GET" else None, "i": pago_id})
        db.commit()
    return r


def _json(d: dict) -> str:
    import json
    return json.dumps(d, ensure_ascii=False, default=str)


# ----------------------------------------------------------------------------- confirmar
def _guardar_resultado(db: Session, p: PagoOnline, r: Resultado) -> None:
    crudo = dict(r.crudo)
    for k, v in (("medio", r.medio), ("motivo", r.motivo)):
        if v:
            crudo[k] = v
    if r.id_transaccion:
        p.id_transaccion_proveedor = r.id_transaccion
    if r.autorizacion:
        p.codigo_autorizacion = r.autorizacion[:60]
    if r.ultimos_digitos:
        p.ultimos_digitos = str(r.ultimos_digitos)[:8]
    if crudo:
        p.respuesta_proveedor = crudo


def _en_revision(p: PagoOnline, r: Resultado, motivo: str) -> dict:
    p.estado = "EN_REVISION"
    p.motivo_revision = motivo[:300]
    p.monto_confirmado = r.monto
    p.confirmado_en = _ahora()
    log.warning("Pago en línea %s en revisión: %s", p.id, motivo)
    return {"estado": "EN_REVISION", "motivo": motivo}


def confirmar_intencion(db: Session, pago_id: str, resultado: Resultado, tenant_id: int | None = None) -> dict:
    """Aplica el resultado verificado con el proveedor. Idempotente. NO hace commit: lo hace quien llama.

    Devuelve además `pedido_pagado_id` cuando en esta llamada el pedido quedó pagado (para notificar tras el commit).
    """
    q = db.query(PagoOnline).filter(PagoOnline.id == pago_id)
    if tenant_id is not None:
        q = q.filter(PagoOnline.tenant_id == tenant_id)
    p = q.with_for_update().first()
    if not p:
        raise ErrorNoEncontrado("Pago en línea no encontrado")
    if resultado.orden_comercio and resultado.orden_comercio != p.orden_comercio:
        raise ErrorPago("La transacción del proveedor no corresponde a este pago")
    if p.estado in ESTADOS_FINALES:
        return {"estado": p.estado, "repetida": True}
    if p.estado == "INICIADO" and p.expira_en <= _ahora():
        p.estado = "EXPIRADO"
    _guardar_resultado(db, p, resultado)
    if resultado.estado == PENDIENTE:
        return {"estado": p.estado}
    if resultado.estado == RECHAZADO:
        if p.estado == "INICIADO":
            p.estado = "RECHAZADO"
            return {"estado": "RECHAZADO", "motivo": resultado.motivo}
        return {"estado": p.estado}
    # APROBADO
    if resultado.monto is None or Decimal(resultado.monto) != Decimal(p.monto):
        return _en_revision(p, resultado, f"Monto confirmado por el proveedor (${resultado.monto}) distinto del de "
                                          f"la intención (${int(p.monto)}): no se aplicó al pedido")
    tardio = p.estado == "EXPIRADO"
    pedido = db.query(Pedido).filter(Pedido.id == p.pedido_id).with_for_update().first()
    estado_pedido = pedido.estado_pedido.codigo if pedido and pedido.estado_pedido else None
    if not pedido or pedido.es_pagado:
        return _en_revision(p, resultado, "Pago aprobado para un pedido que ya estaba pagado (posible pago duplicado: "
                                          "revisar devolución)")
    if estado_pedido == "CANCELADO":
        return _en_revision(p, resultado, "Pago aprobado para un pedido cancelado (revisar devolución)")
    pedido.es_pagado = True
    codigo_medio = MEDIO_PAGO_POR_PROVEEDOR.get(p.pasarela.proveedor if p.pasarela else "", "PAGO_ONLINE")
    medio = db.query(MedioPago).filter(MedioPago.codigo == codigo_medio).first()
    if medio:
        pedido.medio_pago_id = medio.id
    p.estado = "CONFIRMADO"
    p.monto_confirmado = resultado.monto
    p.confirmado_en = _ahora()
    if tardio:
        p.motivo_revision = "Pago aprobado por el proveedor después del vencimiento de la intención (aplicado)"
    return {"estado": "CONFIRMADO", "pedido_pagado_id": pedido.id}


def _notificar_pedido_pagado(db: Session, pedido_id: int | None) -> None:
    if not pedido_id:
        return
    try:
        from services.webhook_service import trigger_pedido_confirmado
        pedido = db.get(Pedido, pedido_id)
        if pedido:
            trigger_pedido_confirmado(pedido, db)
    except Exception:   # noqa: BLE001  la notificación nunca debe deshacer un pago registrado
        log.exception("No se pudo notificar el pago del pedido %s", pedido_id)


def _alertar(db: Session, tenant_id: int, tipo: str, titulo: str, cuerpo: str, pedido_id: int | None) -> None:
    try:
        from services.notification_service import notify_admins_tenant
        notify_admins_tenant(db, tenant_id, tipo, titulo, cuerpo, payload={"pedido_id": pedido_id},
                             action_url="/admin/pedidos")
    except Exception:   # noqa: BLE001  una alerta fallida nunca deshace un pago
        db.rollback()
        log.exception("No se pudo crear la alerta '%s' del pedido %s", tipo, pedido_id)


def autoconfirmar_pedido(tenant_id: int, pedido_id: int) -> bool:
    """Confirma el pedido recién pagado en línea, igual que la confirmación manual del backoffice para un pedido WEB:
    local de despacho por defecto del tipo de pedido, descuento de inventario, puntos ganados y estado CONFIRMADO.

    Los puntos USADOS no se vuelven a descontar (la landing los aplica al crear el pedido). No registra venta en caja
    (pedido WEB sin turno). Si no se puede (sin local por defecto, stock insuficiente), el pedido queda pagado y
    PENDIENTE y se alerta a los admins. Devuelve True si quedó confirmado.
    """
    from fastapi import HTTPException
    from routers.pedidos import descontar_inventario
    from services.puntos_service import PuntosService

    with abrir_sesion() as db:
        pedido = (db.query(Pedido).filter(Pedido.id == pedido_id, Pedido.tenant_id == tenant_id)
                  .with_for_update().first())
        if not pedido or pedido.inventario_descontado:
            return False
        if (pedido.estado_pedido.codigo if pedido.estado_pedido else None) != "PENDIENTE":
            return False
        numero = pedido.numero_pedido
        local_id = pedido.tipo_pedido.local_despacho_default_id if pedido.tipo_pedido else None
        motivo = None
        if not local_id:
            motivo = "el tipo de pedido no tiene local de despacho por defecto"
        else:
            confirmado = db.query(EstadoPedido).filter(EstadoPedido.codigo == "CONFIRMADO").first()
            try:
                descontar_inventario(pedido, local_id, db)
                if pedido.puntos_ganados and pedido.puntos_ganados > 0:
                    PuntosService.otorgar_puntos_por_pedido(db, pedido.cliente_id, pedido.id, pedido.puntos_ganados,
                                                            f"Puntos ganados por confirmación de pedido #{pedido.id}")
                pedido.estado_id = confirmado.id
                db.commit()
                log.info("Pedido %s confirmado automáticamente tras el pago en línea", numero)
                return True
            except HTTPException as e:
                db.rollback()
                motivo = str(e.detail)
            except Exception as e:   # noqa: BLE001
                db.rollback()
                log.exception("Error al confirmar automáticamente el pedido %s", numero)
                motivo = f"error inesperado ({type(e).__name__})"
        _alertar(db, tenant_id, "pedido_pagado_sin_confirmar", f"Pedido {numero} pagado: confirmar manualmente",
                 f"El pedido {numero} se pagó en línea pero no se pudo confirmar automáticamente: {motivo}.", pedido_id)
        return False


def confirmar_y_guardar(tenant_id: int, pago_id: str, resultado: Resultado) -> dict:
    with abrir_sesion() as db:
        try:
            r = confirmar_intencion(db, pago_id, resultado, tenant_id)
            db.commit()
        except ErrorPago:
            db.rollback()
            raise
        if r.get("estado") == "EN_REVISION" and not r.get("repetida"):
            p = db.get(PagoOnline, pago_id)
            numero = p.pedido.numero_pedido if p and p.pedido else ""
            _alertar(db, tenant_id, "pago_en_revision", f"Pago en línea en revisión: pedido {numero}",
                     r.get("motivo") or "", p.pedido_id if p else None)
    if r.get("pedido_pagado_id"):
        autoconfirmar_pedido(tenant_id, r["pedido_pagado_id"])
        with abrir_sesion() as db:
            _notificar_pedido_pagado(db, r["pedido_pagado_id"])
    return r


# ----------------------------------------------------------------------------- retorno / notificación
def _id_intencion(valor_) -> str | None:
    try:
        return str(uuid.UUID(str(valor_))) if valor_ else None
    except ValueError:
        return None


def _resultado_de(adaptador, pasarela: Pasarela, p_intencion: Intencion) -> Resultado:
    if getattr(adaptador, "verifica_por_intencion", False):
        return adaptador.consultar(pasarela, p_intencion)
    return adaptador.verificar(pasarela, p_intencion.token)


def procesar_aviso(tenant_id: int, proveedor: str, datos: dict) -> str | None:
    """Retorno del navegador o notificación del proveedor: identifica la intención (por el token del proveedor o por
    el id de la intención en nuestra URL), consulta el resultado al proveedor (nunca confía en los datos recibidos) y
    lo confirma. Con `cancelado`, si el adaptador sabe anular, anula antes de rechazar. Devuelve el id de la intención.
    """
    adaptador = adaptador_de(proveedor)
    if not adaptador:
        return None
    token = adaptador.token_de(datos)
    intencion_id = None if token else _id_intencion(datos.get("intencion"))
    if not token and not intencion_id:
        return None
    with abrir_sesion() as db:
        q = db.query(PagoOnline).join(PasarelaPago, PasarelaPago.id == PagoOnline.pasarela_id).filter(
            PagoOnline.tenant_id == tenant_id, PasarelaPago.proveedor == adaptador.codigo)
        p = (q.filter(PagoOnline.token_pasarela == token) if token else q.filter(PagoOnline.id == intencion_id)).first()
        if not p:
            return None
        pago_id = str(p.id)
        if not p.token_pasarela:          # el proveedor nunca creó la transacción: no hay nada que consultar
            return pago_id
        pasarela = cargar_pasarela(db, p.pasarela_id, tenant_id)
        intencion = intencion_de(p)
    resultado = None
    if str(datos.get("cancelado", "")).lower() in ("1", "true", "si") and hasattr(adaptador, "anular"):
        try:
            adaptador.anular(pasarela, intencion.token)
            resultado = Resultado(estado=RECHAZADO, motivo="Pago cancelado por el cliente")
        except ErrorPasarela as e:   # ya se inició o se pagó: manda el estado que informe el proveedor
            log.info("No se pudo anular el pago %s en %s: %s", pago_id, proveedor, e.mensaje)
    try:
        resultado = resultado or _resultado_de(adaptador, pasarela, intencion)
    except ErrorPasarela as e:   # la conciliación lo resolverá
        log.warning("No se pudo verificar el pago %s con %s: %s", pago_id, proveedor, e.mensaje)
        return pago_id
    try:
        confirmar_y_guardar(tenant_id, pago_id, resultado)
    except ErrorPago as e:
        log.warning("Resultado del proveedor no aplicado al pago %s: %s", pago_id, e)
    return pago_id


def confirmar_simulada(tenant_id: int, pago_id: str, aprobado: bool) -> dict:
    """Página de la pasarela simulada (solo desarrollo): aplica el resultado elegido."""
    with abrir_sesion() as db:
        p = db.query(PagoOnline).filter(PagoOnline.id == pago_id, PagoOnline.tenant_id == tenant_id).first()
        if not p:
            raise ErrorNoEncontrado("Pago no encontrado")
        pasarela = cargar_pasarela(db, p.pasarela_id, tenant_id)
        intencion = intencion_de(p)
    a = adaptador_de(pasarela.proveedor)
    if pasarela.proveedor != "SIMULADA":
        raise ErrorPago("Este pago no es de la pasarela simulada")
    try:
        resultado = a.resultado_elegido(pasarela, intencion, aprobado)
    except ErrorPasarela as e:
        raise ErrorPago(e.mensaje) from e
    return confirmar_y_guardar(tenant_id, pago_id, resultado)


# ----------------------------------------------------------------------------- conciliación
def _consultar_y_confirmar(tenant_id: int, p: PagoOnline, pasarela: Pasarela | None, contexto: str) -> bool:
    """Consulta al proveedor una intención (fuera de toda transacción) y, si tiene resultado, lo confirma."""
    adaptador = adaptador_de(pasarela.proveedor) if pasarela else None
    if not adaptador or adaptador.codigo == "SIMULADA" or not p.orden_comercio:
        return False
    try:
        resultado = adaptador.consultar(pasarela, intencion_de(p))
    except ErrorPasarela as e:
        if e.codigo == "conexion" or e.credenciales:
            log.warning("%s del pago %s: %s", contexto, p.id, e.mensaje)
        return False      # el proveedor no la conoce o no respondió: el vencimiento la expira
    if resultado.estado == PENDIENTE:
        # guarda el motivo de un intento rechazado (para mostrarlo al cliente) sin cambiar el estado
        if resultado.motivo or resultado.crudo:
            try:
                confirmar_y_guardar(tenant_id, str(p.id), resultado)
            except ErrorPago:
                pass
        return False
    try:
        return not confirmar_y_guardar(tenant_id, str(p.id), resultado).get("repetida")
    except ErrorPago as e:
        log.warning("%s del pago %s no aplicada: %s", contexto, p.id, e)
        return False


def conciliar_pagos() -> int:
    """Consulta al proveedor las intenciones sin resultado de todos los tenants: INICIADO de más de 5 minutos y
    EXPIRADO de las últimas 24 horas. Registra los aprobados cuya confirmación no llegó. Devuelve las resueltas."""
    with abrir_sesion() as db:
        _expirar_vencidas(db)
        db.commit()
        limite = _ahora()
        pendientes = (db.query(PagoOnline).filter(
            ((PagoOnline.estado == "INICIADO") & (PagoOnline.iniciado_en < limite - timedelta(minutes=5)))
            | ((PagoOnline.estado == "EXPIRADO") & (PagoOnline.expira_en > limite - timedelta(hours=24))))
            .filter(PagoOnline.token_pasarela.isnot(None))
            .order_by(PagoOnline.iniciado_en).limit(200).all())
        pasarelas: dict[int, Pasarela | None] = {}
        for p in pendientes:
            if p.pasarela_id not in pasarelas:
                try:
                    pasarelas[p.pasarela_id] = cargar_pasarela(db, p.pasarela_id, p.tenant_id)
                except cifrado.ErrorCifrado as e:
                    log.error("Pasarela %s: %s", p.pasarela_id, e)
                    pasarelas[p.pasarela_id] = None
        db.expunge_all()
    return sum(_consultar_y_confirmar(p.tenant_id, p, pasarelas.get(p.pasarela_id), "Conciliación") for p in pendientes)


INTERVALO_CONCILIACION_S = 120
_LOCK_CONCILIACION = 74_120_001   # pg_advisory_lock: una sola conciliación a la vez aunque haya varios procesos
_hilo: threading.Thread | None = None


def _ciclo_conciliacion() -> None:
    time.sleep(30)
    while True:
        try:
            with abrir_sesion() as db:
                conn = db.connection()
                if conn.execute(text("SELECT pg_try_advisory_lock(:k)"), {"k": _LOCK_CONCILIACION}).scalar():
                    try:
                        n = conciliar_pagos()
                        if n:
                            log.info("Conciliación de pagos en línea: %s resueltas", n)
                    finally:
                        conn.execute(text("SELECT pg_advisory_unlock(:k)"), {"k": _LOCK_CONCILIACION})
                        db.commit()
        except Exception:   # noqa: BLE001  el hilo nunca debe morir
            log.exception("Error en la conciliación de pagos en línea")
        time.sleep(INTERVALO_CONCILIACION_S)


def iniciar_conciliacion() -> None:
    global _hilo
    if _hilo is None or not _hilo.is_alive():
        _hilo = threading.Thread(target=_ciclo_conciliacion, name="conciliacion-pagos", daemon=True)
        _hilo.start()


# ----------------------------------------------------------------------------- consulta del cliente
INTERVALO_CONSULTA_S = 10
_ultima_consulta: dict[str, float] = {}
_candado_consulta = threading.Lock()


def estado_publico(db: Session, pago_id: str) -> dict | None:
    p = db.query(PagoOnline).filter(PagoOnline.id == pago_id).first()
    if not p:
        return None
    crudo = p.respuesta_proveedor or {}
    return {
        "id": str(p.id), "estado": p.estado, "monto": int(p.monto),
        "expira_en": p.expira_en.isoformat() if p.expira_en else None,
        "pasarela": p.pasarela.nombre_visible if p.pasarela else None,
        "numero_pedido": p.pedido.numero_pedido if p.pedido else None,
        "id_transaccion": p.id_transaccion_proveedor, "medio": crudo.get("medio"),
        "motivo": crudo.get("motivo") if p.estado in ("INICIADO", "RECHAZADO", "EXPIRADO") else None,
        "en_revision": p.estado == "EN_REVISION",
        "url_pago": p.url_pago if p.estado == "INICIADO" and p.expira_en > _ahora() else None,
        "simulada": bool(p.pasarela and p.pasarela.proveedor == "SIMULADA"),
    }


def consultar_ahora(pago_id: str) -> None:
    """Pide al proveedor el estado de una intención sin resultado (máximo una vez cada 10 s por intención)."""
    with abrir_sesion() as db:
        _expirar_vencidas(db)
        db.commit()
        p = db.query(PagoOnline).filter(PagoOnline.id == pago_id).first()
        if not p or not p.token_pasarela:
            return
        consultable = p.estado == "INICIADO" or (p.estado == "EXPIRADO" and p.expira_en > _ahora() - timedelta(hours=24))
        if not consultable:
            return
        pasarela = cargar_pasarela(db, p.pasarela_id, p.tenant_id)
        db.expunge(p)
    ahora = time.monotonic()
    with _candado_consulta:
        if ahora - _ultima_consulta.get(pago_id, -INTERVALO_CONSULTA_S) < INTERVALO_CONSULTA_S:
            return
        _ultima_consulta[pago_id] = ahora
        for k in [k for k, t in _ultima_consulta.items() if ahora - t > 3600]:   # no crece sin límite
            del _ultima_consulta[k]
    _consultar_y_confirmar(p.tenant_id, p, pasarela, "Consulta del cliente")
