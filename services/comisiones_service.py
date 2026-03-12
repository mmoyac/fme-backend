"""
Servicio de comisiones de vendedores.
- Genera comisión al marcar un pedido como pagado.
- Calcula neto = monto_bruto / 1.19 (IVA chileno 19%).
- Período = YYYY-MM del mes de pago; pago previsto el día 5 del mes siguiente.
"""
from datetime import datetime, date, timedelta
from calendar import monthrange

from sqlalchemy.orm import Session

from database.models import Comision, LiquidacionComision, User, TipoPedido, EstadoPedido


IVA = 1.19


def _periodo_from_date(dt: datetime) -> str:
    """Retorna el período 'YYYY-MM' a partir de un datetime."""
    return dt.strftime("%Y-%m")


def _fecha_pago_prevista(periodo: str) -> date:
    """Retorna el 5 del mes siguiente al período dado."""
    year, month = int(periodo[:4]), int(periodo[5:7])
    if month == 12:
        return date(year + 1, 1, 5)
    return date(year, month + 1, 5)


def _fecha_inicio_periodo(periodo: str) -> date:
    year, month = int(periodo[:4]), int(periodo[5:7])
    return date(year, month, 1)


def _fecha_fin_periodo(periodo: str) -> date:
    year, month = int(periodo[:4]), int(periodo[5:7])
    _, last_day = monthrange(year, month)
    return date(year, month, last_day)


def generar_comision(pedido, db: Session) -> bool:
    """
    Genera una comisión para el vendedor del pedido si aplica.
    Idempotente: si ya existe comisión para este pedido, no hace nada.
    Retorna True si se generó, False si no aplica o ya existía.
    """
    if not pedido.usuario_id:
        return False

    # No generar comisión para pedidos cancelados
    estado = db.query(EstadoPedido).filter(EstadoPedido.id == pedido.estado_id).first()
    if estado and estado.codigo == 'CANCELADO':
        return False

    # Para CAJAS_VARIABLES el precio real se fija al confirmar (asignación de lotes).
    # Usar query directo para evitar problemas de lazy loading.
    tipo = db.query(TipoPedido).filter(TipoPedido.id == pedido.tipo_pedido_id).first() if pedido.tipo_pedido_id else None
    if tipo and tipo.codigo == 'CAJAS_VARIABLES' and not pedido.inventario_descontado:
        return False

    # Precio debe ser mayor a 0 para tener sentido
    if not pedido.monto_total or float(pedido.monto_total) <= 0:
        return False

    # Idempotencia: ya existe comisión
    existing = db.query(Comision).filter(Comision.pedido_id == pedido.id).first()
    if existing:
        return False

    # Cargar el vendedor y verificar que tenga porcentaje configurado
    user = db.query(User).filter(User.id == pedido.usuario_id).first()
    if not user or not user.porcentaje_comision:
        return False

    porcentaje = float(user.porcentaje_comision)
    monto_bruto = float(pedido.monto_total or 0)
    monto_neto = round(monto_bruto / IVA, 2)
    monto_comision = round(monto_neto * porcentaje / 100, 2)

    # Período basado en la fecha actual (cuando se pagó)
    try:
        from zoneinfo import ZoneInfo
        now = datetime.now(ZoneInfo("America/Santiago"))
    except Exception:
        now = datetime.utcnow()

    periodo = _periodo_from_date(now)

    # Si el período ya fue liquidado para este vendedor, mover al mes siguiente
    liquidacion_existente = db.query(LiquidacionComision).filter(
        LiquidacionComision.tenant_id == pedido.tenant_id,
        LiquidacionComision.vendedor_id == pedido.usuario_id,
        LiquidacionComision.periodo == periodo,
        LiquidacionComision.estado == "PAGADA",
    ).first()
    if liquidacion_existente:
        year, month = int(periodo[:4]), int(periodo[5:7])
        if month == 12:
            periodo = f"{year + 1}-01"
        else:
            periodo = f"{year}-{month + 1:02d}"

    comision = Comision(
        tenant_id=pedido.tenant_id,
        vendedor_id=pedido.usuario_id,
        pedido_id=pedido.id,
        numero_pedido=pedido.numero_pedido,
        porcentaje=porcentaje,
        monto_bruto=monto_bruto,
        monto_neto=monto_neto,
        monto_comision=monto_comision,
        periodo=periodo,
        fecha_pedido=pedido.fecha_pedido,
    )
    db.add(comision)
    # El commit lo maneja el caller
    return True


def crear_liquidacion(vendedor_id: int, periodo: str, tenant_id: int, notas: str, db: Session) -> LiquidacionComision:
    """
    Crea una liquidación para un vendedor en un período.
    Agrega todas las comisiones PENDIENTE del período y las marca como LIQUIDADA.
    """
    # Verificar que no exista ya
    existente = db.query(LiquidacionComision).filter(
        LiquidacionComision.tenant_id == tenant_id,
        LiquidacionComision.vendedor_id == vendedor_id,
        LiquidacionComision.periodo == periodo,
    ).first()
    if existente:
        raise ValueError(f"Ya existe una liquidación para este vendedor en el período {periodo}")

    # Obtener comisiones pendientes del período
    comisiones = db.query(Comision).filter(
        Comision.tenant_id == tenant_id,
        Comision.vendedor_id == vendedor_id,
        Comision.periodo == periodo,
        Comision.estado == "PENDIENTE",
    ).all()

    if not comisiones:
        raise ValueError(f"No hay comisiones pendientes para el período {periodo}")

    total_neto = sum(float(c.monto_neto) for c in comisiones)
    total_comision = sum(float(c.monto_comision) for c in comisiones)

    liquidacion = LiquidacionComision(
        tenant_id=tenant_id,
        vendedor_id=vendedor_id,
        periodo=periodo,
        fecha_inicio=_fecha_inicio_periodo(periodo),
        fecha_fin=_fecha_fin_periodo(periodo),
        fecha_pago_prevista=_fecha_pago_prevista(periodo),
        total_ventas_neto=round(total_neto, 2),
        total_comision=round(total_comision, 2),
        cantidad_pedidos=len(comisiones),
        notas=notas,
    )
    db.add(liquidacion)
    db.flush()  # Para obtener el ID

    for c in comisiones:
        c.estado = "LIQUIDADA"
        c.liquidacion_id = liquidacion.id

    return liquidacion
