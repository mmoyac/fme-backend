
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from database.database import get_db
from database import models
from schemas import produccion as schemas_prod
from routers.auth import get_current_active_user

router = APIRouter(
    prefix="/produccion",
    tags=["Produccion"]
)


def _afecta_inventario(prod) -> bool:
    """True si el producto maneja stock. Los tipos operacionales (arriendo, electricidad,
    servicios) tienen tipo_producto.afecta_inventario=False: se costean pero no descuentan
    stock en producción."""
    if not prod:
        return True
    tipo = getattr(prod, "tipo_producto", None)
    if tipo is None:
        return True
    return bool(getattr(tipo, "afecta_inventario", True))

# Endpoint para chequeo de insumos en tiempo real
@router.get("/chequear-insumos")
def chequear_insumos_producto(
    producto_id: int,
    cantidad: float,
    local_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Chequea si hay stock suficiente de insumos para elaborar una cantidad de un producto en un local.
    Retorna lista de insumos requeridos y faltantes.
    """
    producto = db.query(models.Producto).filter(models.Producto.id == producto_id).first()
    if not producto or not producto.tiene_receta or not producto.recetas:
        return {"ok": True, "insumos": [], "errores": []}
    receta = producto.recetas[0]
    rendimiento = float(receta.rendimiento)
    if rendimiento == 0:
        return {"ok": True, "insumos": [], "errores": []}
    factor = cantidad / rendimiento
    insumos = []
    errores = []
    for ingrediente in receta.ingredientes:
        pid = ingrediente.producto_ingrediente_id
        prod_ing = db.query(models.Producto).filter(models.Producto.id == pid).first()
        # Insumos operacionales (arriendo, electricidad, etc.) no manejan stock
        if not _afecta_inventario(prod_ing):
            continue
        consumo = float(ingrediente.cantidad) * factor
        inv = db.query(models.Inventario).filter(
            models.Inventario.producto_id == pid,
            models.Inventario.local_id == local_id
        ).first()
        stock_actual = float(inv.cantidad_stock) if inv else 0.0
        insumos.append({
            "producto_id": pid,
            "nombre": prod_ing.nombre if prod_ing else "Desconocido",
            "cantidad_requerida": consumo,
            "stock_actual": stock_actual,
            "unidad": prod_ing.unidad_medida.simbolo if prod_ing and prod_ing.unidad_medida else ""
        })
        if stock_actual < consumo:
            errores.append(f"Falta {prod_ing.nombre if prod_ing else 'Desconocido'}: Requiere {consumo:.2f}, Disponible {stock_actual:.2f}")
    return {"ok": len(errores) == 0, "insumos": insumos, "errores": errores}

@router.get("/ordenes", response_model=List[schemas_prod.OrdenProduccionRead])
def listar_ordenes(db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    return db.query(models.OrdenProduccion).join(models.Local).filter(
        models.Local.tenant_id == current_user.tenant_id
    ).order_by(models.OrdenProduccion.id.desc()).all()

@router.delete("/ordenes/{orden_id}")
def eliminar_orden(orden_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    orden = db.query(models.OrdenProduccion).join(models.Local).filter(
        models.OrdenProduccion.id == orden_id,
        models.Local.tenant_id == current_user.tenant_id
    ).first()
    if not orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    
    if orden.estado == "FINALIZADA":
        raise HTTPException(status_code=400, detail="No se puede eliminar una orden finalizada")
        
    db.delete(orden)
    db.commit()
    return {"message": "Orden eliminada"}

@router.get("/ordenes/{orden_id}/requisitos")
def calcular_requisitos_orden(orden_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    """
    Calcula los insumos totales necesarios para una orden sin finalizarla.
    Útil para generar la hoja de producción.
    """
    orden = db.query(models.OrdenProduccion).join(models.Local).filter(
        models.OrdenProduccion.id == orden_id,
        models.Local.tenant_id == current_user.tenant_id
    ).first()
    if not orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
        
    consumos_totales = {} # {producto_id: {'cantidad': float, 'nombre': str, 'unidad': str}}
    
    for detalle in orden.detalles:
        producto = detalle.producto
        if producto.tiene_receta and producto.recetas:
            receta = producto.recetas[0]
            rendimiento = float(receta.rendimiento)
            if rendimiento == 0: continue
            
            cantidad_a_producir = float(detalle.cantidad_programada)
            factor = cantidad_a_producir / rendimiento
            
            for ingrediente in receta.ingredientes:
                pid = ingrediente.producto_ingrediente_id
                prod_ing = db.query(models.Producto).filter(models.Producto.id == pid).first()
                # Operacionales no se incluyen en la hoja de insumos a preparar
                if not _afecta_inventario(prod_ing):
                    continue
                consumo = float(ingrediente.cantidad) * factor

                if pid in consumos_totales:
                    consumos_totales[pid]['cantidad'] += consumo
                else:
                    consumos_totales[pid] = {
                        'producto_id': pid,
                        'nombre': prod_ing.nombre,
                        'cantidad': consumo,
                        'unidad': prod_ing.unidad_medida.simbolo
                    }

    return list(consumos_totales.values())

@router.post("/ordenes", response_model=schemas_prod.OrdenProduccionRead)
def crear_orden(orden: schemas_prod.OrdenProduccionCreate, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    # Validar que el local pertenezca al tenant
    local = db.query(models.Local).filter(
        models.Local.id == orden.local_id,
        models.Local.tenant_id == current_user.tenant_id
    ).first()
    if not local:
        raise HTTPException(status_code=404, detail="Local no encontrado o no pertenece a tu organización")
    
    # --- VALIDACIÓN DE STOCK DE INSUMOS ANTES DE GUARDAR ---
    consumos_totales = {}  # {producto_id: cantidad_necesaria}
    for det in orden.detalles:
        producto = db.query(models.Producto).filter(models.Producto.id == det.producto_id).first()
        if producto and producto.tiene_receta and producto.recetas:
            receta = producto.recetas[0]  # Usar primera receta activa
            rendimiento = float(receta.rendimiento)
            if rendimiento == 0:
                continue
            factor = float(det.cantidad) / rendimiento
            for ingrediente in receta.ingredientes:
                pid = ingrediente.producto_ingrediente_id
                prod_ing = db.query(models.Producto).filter(models.Producto.id == pid).first()
                # Operacionales no validan stock
                if not _afecta_inventario(prod_ing):
                    continue
                consumo = float(ingrediente.cantidad) * factor
                if pid in consumos_totales:
                    consumos_totales[pid] += consumo
                else:
                    consumos_totales[pid] = consumo

    # Verificar disponibilidad en Base de Datos
    errores_stock = []
    for pid, cantidad_requerida in consumos_totales.items():
        if cantidad_requerida <= 0.001:
            continue
        inv = db.query(models.Inventario).filter(
            models.Inventario.producto_id == pid,
            models.Inventario.local_id == orden.local_id
        ).first()
        stock_actual = float(inv.cantidad_stock) if inv else 0.0
        if stock_actual < cantidad_requerida:
            producto_nombre = db.query(models.Producto.nombre).filter(models.Producto.id == pid).scalar()
            errores_stock.append(f"Falta {producto_nombre}: Requiere {cantidad_requerida:.2f}, Disponible {stock_actual:.2f}")
    if errores_stock:
        raise HTTPException(
            status_code=400,
            detail="Stock insuficiente de insumos: " + "; ".join(errores_stock)
        )

    # --- GUARDAR ORDEN SI HAY STOCK SUFICIENTE ---
    nuevo_orden = models.OrdenProduccion(
        local_id=orden.local_id,
        fecha_programada=orden.fecha_programada,
        notas=orden.notas,
        estado="PLANIFICADA"
    )
    db.add(nuevo_orden)
    db.commit()
    db.refresh(nuevo_orden)
    for det in orden.detalles:
        nuevo_detalle = models.DetalleOrdenProduccion(
            orden_id=nuevo_orden.id,
            producto_id=det.producto_id,
            unidad_medida_id=det.unidad_medida_id,
            cantidad_programada=det.cantidad
        )
        db.add(nuevo_detalle)
    db.commit()
    db.refresh(nuevo_orden)
    return nuevo_orden

@router.post("/ordenes/{orden_id}/finalizar")
def finalizar_orden(orden_id: int, confirmacion: schemas_prod.ConfirmacionFinalizacion = None, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    orden = db.query(models.OrdenProduccion).join(models.Local).filter(
        models.OrdenProduccion.id == orden_id,
        models.Local.tenant_id == current_user.tenant_id
    ).first()
    if not orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
        
    if orden.estado == "FINALIZADA":
        raise HTTPException(status_code=400, detail="Orden ya finalizada")
    
    # Mapeo de ajustes si existen
    ajustes_prod_map = {a.detalle_id: float(a.cantidad_producida_real) for a in confirmacion.detalles_ajustes} if confirmacion else {}
    ajustes_insumos_map = {a.producto_id: float(a.cantidad_consumida_real) for a in confirmacion.insumos_ajustes} if confirmacion else {}

    # Lógica de Validación de Stock (Pre-chequeo)
    # Agrupamos todos los consumos necesarios por ingrediente
    consumos_totales = {} # {producto_id: cantidad_necesaria}
    
    # 1. Calcular consumos teóricos basados en cantidades reales producidas o programadas
    for detalle in orden.detalles:
        # Determinar cantidad real producida (Si hay ajuste usalo, sino la programada)
        cantidad_real = ajustes_prod_map.get(detalle.id, float(detalle.cantidad_programada))
        
        producto = detalle.producto
        if producto.tiene_receta and producto.recetas:
            receta = producto.recetas[0] # Usar primera receta activa
            rendimiento = float(receta.rendimiento)
            if rendimiento == 0: continue
            
            factor = cantidad_real / rendimiento
            
            for ingrediente in receta.ingredientes:
                pid = ingrediente.producto_ingrediente_id
                # Si el usuario mandó un consumo explícito para este insumo TOTAL, usaremos ese valor FINALMENTE.
                # Pero aquí estamos sumando por detalle. Si hay ajuste manual "global" de insumo, ignoramos el cálculo parcial? 
                # Respuesta: Si hay ajuste global para un insumo en 'ajustes_insumos_map', lo usaremos directamente abajo, 
                # saltando la suma acumulada de la receta.
                # PERO, si el ajuste es nulo, sumamos.
                
                prod_ing = db.query(models.Producto).filter(models.Producto.id == pid).first()
                # Operacionales no descuentan stock
                if not _afecta_inventario(prod_ing):
                    continue
                if pid not in ajustes_insumos_map:
                    consumo = float(ingrediente.cantidad) * factor
                    if pid in consumos_totales:
                        consumos_totales[pid] += consumo
                    else:
                        consumos_totales[pid] = consumo

    # 2. Incorporar ajustes manuales de insumos (sobreescriben lo calculado)
    for pid, qty in ajustes_insumos_map.items():
        prod_ajuste = db.query(models.Producto).filter(models.Producto.id == pid).first()
        # Operacionales nunca descuentan stock, ni siquiera vía ajuste manual
        if not _afecta_inventario(prod_ajuste):
            continue
        consumos_totales[pid] = qty

    # Verificar disponibilidad en Base de Datos
    errores_stock = []
    inventarios_cache = {} # Para reusar en la fase de actualización
    
    for pid, cantidad_requerida in consumos_totales.items():
        # Optimization: If required quantity is effectively zero, skip stock check
        if cantidad_requerida <= 0.001:
            continue

        inv = db.query(models.Inventario).filter(
            models.Inventario.producto_id == pid,
            models.Inventario.local_id == orden.local_id
        ).first()
        
        stock_actual = float(inv.cantidad_stock) if inv else 0.0
        
        if stock_actual < cantidad_requerida:
            producto_nombre = db.query(models.Producto.nombre).filter(models.Producto.id == pid).scalar()
            errores_stock.append(f"Falta {producto_nombre}: Requiere {cantidad_requerida:.2f}, Disponible {stock_actual:.2f}")
        
        inventarios_cache[pid] = inv
            
    if errores_stock:
        raise HTTPException(
            status_code=400, 
            detail="Stock insuficiente de insumos: " + "; ".join(errores_stock)
        )

    # Si pasa la validación, aplicar cambios
    
    # Fase 1: Descontar Insumos
    for pid, cantidad_requerida in consumos_totales.items():
        inv = inventarios_cache.get(pid)
        if inv:
            inv.cantidad_stock = float(inv.cantidad_stock) - cantidad_requerida
        else:
             pass
        # Movimiento: salida de insumo por producción
        db.add(models.MovimientoInventario(
            producto_id=pid,
            local_origen_id=orden.local_id,
            local_destino_id=None,
            cantidad=-cantidad_requerida,
            tipo_movimiento="PRODUCCION",
            referencia_id=orden.id,
            notas=f"Consumo insumo OP #{orden.id}",
            usuario=current_user.email,
        ))

    # Fase 2: Incrementar Producto Final (Con Cantidad REAL)
    for detalle in orden.detalles:
        cantidad_real = ajustes_prod_map.get(detalle.id, float(detalle.cantidad_programada))

        inventario_final = db.query(models.Inventario).filter(
            models.Inventario.producto_id == detalle.producto_id,
            models.Inventario.local_id == orden.local_id
        ).first()

        if not inventario_final:
            inventario_final = models.Inventario(
                producto_id=detalle.producto_id,
                local_id=orden.local_id,
                cantidad_stock=0
            )
            db.add(inventario_final)

        inventario_final.cantidad_stock = float(inventario_final.cantidad_stock) + cantidad_real
        detalle.cantidad_producida = cantidad_real  # Guardamos lo real

        # Movimiento: entrada de producto terminado por producción
        db.add(models.MovimientoInventario(
            producto_id=detalle.producto_id,
            local_origen_id=None,
            local_destino_id=orden.local_id,
            cantidad=cantidad_real,
            tipo_movimiento="PRODUCCION",
            referencia_id=orden.id,
            notas=f"Producto terminado OP #{orden.id}",
            usuario=current_user.email,
        ))

    orden.fecha_finalizacion = datetime.now()
    orden.estado = "FINALIZADA"
    if confirmacion and confirmacion.notas_finalizacion:
        if orden.notas:
             orden.notas += f" | Cierre: {confirmacion.notas_finalizacion}"
        else:
             orden.notas = f"Cierre: {confirmacion.notas_finalizacion}"

    # Si hay una OT vinculada a esta OP, cerrarla automáticamente
    ot_vinculada = db.query(models.OrdenTrabajo).join(models.EstadoOT).filter(
        models.OrdenTrabajo.op_id == orden_id,
        models.EstadoOT.es_final == False,
    ).first()
    if ot_vinculada:
        estado_cerrada = db.query(models.EstadoOT).filter(models.EstadoOT.codigo == "CERRADA").first()
        if estado_cerrada:
            ot_vinculada.estado_ot_id = estado_cerrada.id
            ot_vinculada.fecha_cierre = datetime.now()
            # Avanzar a la última etapa configurada
            ultima_etapa = db.query(models.OtEtapaTipo).filter(
                models.OtEtapaTipo.tenant_id == ot_vinculada.tenant_id,
                models.OtEtapaTipo.tipo_ot_id == ot_vinculada.tipo_ot_id,
            ).order_by(models.OtEtapaTipo.orden.desc()).first()
            if ultima_etapa:
                ot_vinculada.etapa_actual_id = ultima_etapa.id
            db.add(models.OtLog(
                ot_id=ot_vinculada.id,
                accion="CERRADA",
                etapa_id=ot_vinculada.etapa_actual_id,
                usuario_id=current_user.id,
                detalle=f"Cerrada automáticamente al finalizar OP #{orden_id}",
            ))

        # Si la OT tenía un pedido vinculado → confirmar el pedido y descontar inventario
        if ot_vinculada.pedido_id:
            pedido = db.query(models.Pedido).join(models.EstadoPedido).filter(
                models.Pedido.id == ot_vinculada.pedido_id,
                models.EstadoPedido.codigo == "PENDIENTE",
            ).first()
            if pedido:
                estado_confirmado = db.query(models.EstadoPedido).filter(
                    models.EstadoPedido.codigo == "CONFIRMADO"
                ).first()
                if estado_confirmado:
                    pedido.estado_id = estado_confirmado.id
                    pedido.notas_admin = (pedido.notas_admin or "") + f" | Confirmado automáticamente al cerrar OT #{ot_vinculada.id}"
                # Descontar inventario del pedido si aún no se hizo
                if not pedido.inventario_descontado:
                    local_despacho_id = pedido.local_despacho_id or orden.local_id
                    from routers.pedidos import descontar_inventario
                    db.flush()  # Asegurar items del pedido disponibles
                    descontar_inventario(pedido, local_despacho_id, db)

    db.commit()

    return {"message": "Orden finalizada y stock actualizado"}

