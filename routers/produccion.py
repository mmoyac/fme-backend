
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from database.database import get_db
from database import models
from schemas import produccion as schemas_prod

router = APIRouter(
    prefix="/produccion",
    tags=["Produccion"]
)

@router.get("/ordenes", response_model=List[schemas_prod.OrdenProduccionRead])
def listar_ordenes(db: Session = Depends(get_db)):
    return db.query(models.OrdenProduccion).order_by(models.OrdenProduccion.id.desc()).all()

@router.delete("/ordenes/{orden_id}")
def eliminar_orden(orden_id: int, db: Session = Depends(get_db)):
    orden = db.query(models.OrdenProduccion).filter(models.OrdenProduccion.id == orden_id).first()
    if not orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    
    if orden.estado == "FINALIZADA":
        raise HTTPException(status_code=400, detail="No se puede eliminar una orden finalizada")
        
    db.delete(orden)
    db.commit()
    return {"message": "Orden eliminada"}

@router.get("/ordenes/{orden_id}/requisitos")
def calcular_requisitos_orden(orden_id: int, db: Session = Depends(get_db)):
    """
    Calcula los insumos totales necesarios para una orden sin finalizarla.
    Útil para generar la hoja de producción.
    """
    orden = db.query(models.OrdenProduccion).filter(models.OrdenProduccion.id == orden_id).first()
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
                consumo = float(ingrediente.cantidad) * factor
                
                if pid in consumos_totales:
                    consumos_totales[pid]['cantidad'] += consumo
                else:
                    # Traer datos extra para mostrar
                    prod_ing = db.query(models.Producto).filter(models.Producto.id == pid).first()
                    consumos_totales[pid] = {
                        'producto_id': pid,
                        'nombre': prod_ing.nombre,
                        'cantidad': consumo,
                        'unidad': prod_ing.unidad_medida.simbolo
                    }

    return list(consumos_totales.values())

@router.post("/ordenes", response_model=schemas_prod.OrdenProduccionRead)
def crear_orden(orden: schemas_prod.OrdenProduccionCreate, db: Session = Depends(get_db)):
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
            cantidad_programada=det.cantidad # SQLAlchemy Numeric handles Decimal typically, but lets see
        )
        db.add(nuevo_detalle)
    
    db.commit()
    db.refresh(nuevo_orden)
    return nuevo_orden

@router.post("/ordenes/{orden_id}/finalizar")
def finalizar_orden(orden_id: int, confirmacion: schemas_prod.ConfirmacionFinalizacion = None, db: Session = Depends(get_db)):
    orden = db.query(models.OrdenProduccion).filter(models.OrdenProduccion.id == orden_id).first()
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
                
                if pid not in ajustes_insumos_map:
                    consumo = float(ingrediente.cantidad) * factor
                    if pid in consumos_totales:
                        consumos_totales[pid] += consumo
                    else:
                        consumos_totales[pid] = consumo

    # 2. Incorporar ajustes manuales de insumos (sobreescriben lo calculado)
    for pid, qty in ajustes_insumos_map.items():
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
        detalle.cantidad_producida = cantidad_real # Guardamos lo real

    orden.fecha_finalizacion = datetime.now()
    orden.estado = "FINALIZADA"
    if confirmacion and confirmacion.notas_finalizacion:
        if orden.notas:
             orden.notas += f" | Cierre: {confirmacion.notas_finalizacion}"
        else:
             orden.notas = f"Cierre: {confirmacion.notas_finalizacion}"
             
    db.commit()
    
    return {"message": "Orden finalizada y stock actualizado"}

