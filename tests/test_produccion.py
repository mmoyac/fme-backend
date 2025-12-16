
import pytest
from datetime import datetime

def test_flujo_produccion_completo(client, db_session):
    # 1. SETUP: Crear Unidades de Medida
    # Asumimos que existen o las creamos.
    # En un escenario ideal tendríamos fixtures para esto, pero lo haré explícito para claridad.
    
    # Kilo
    kg_response = client.post("/api/unidades-medida/", json={
        "codigo": "KG", "nombre": "Kilogramo", "simbolo": "kg", "tipo": "PESO", "factor_conversion": 1.0, "activo": True
    })
    # Si ya existe (por tests previos o fixtures globales), intentamos obtenerla, 
    # pero como es DB en memoria limpia, debería crearse.
    # Nota: Si el POST falla porque la tabla no tiene endpoint, usaremos DB directa en el test si es necesario,
    # pero lo ideal es usar la API. Asumiré que existen endpoints CRUD básicos o los crearé luego.
    # Revisando el listado de archivos, veo 'routers', probaré suerte con endpoints estándar.
    
    # Como no estoy seguro de los endpoints de ABM (Alta Baja Modificacion), 
    # voy a insertar directamente en BD en el setup para evitar ruido en el test de produccion.
    from database.models import Producto, Receta, IngredienteReceta, UnidadMedida, TipoProducto, CategoriaProducto, Local, Inventario
    
    # Crear Unidades
    kg = UnidadMedida(codigo="KG", nombre="Kilo", simbolo="kg", tipo="PESO", factor_conversion=1.0)
    un = UnidadMedida(codigo="UN", nombre="Unidad", simbolo="un", tipo="CANTIDAD", factor_conversion=1.0)
    db_session.add_all([kg, un])
    db_session.commit()
    
    # Crear Categoría y Tipos
    cat = CategoriaProducto(codigo="PAN", nombre="Panadería", descripcion="Panes varios")
    tipo_mp = TipoProducto(codigo="MP", nombre="Materia Prima")
    tipo_pe = TipoProducto(codigo="PE", nombre="Producto Elaborado")
    db_session.add_all([cat, tipo_mp, tipo_pe])
    db_session.commit()
    
    # Crear Local
    local = Local(codigo="LOC1", nombre="Fábrica", direccion="Calle 1")
    db_session.add(local)
    db_session.commit()
    
    # 2. CREAR MATERIAS PRIMAS (Harina, Levadura)
    harina = Producto(
        nombre="Harina", sku="HARINA-001", 
        categoria_id=cat.id, tipo_producto_id=tipo_mp.id, unidad_medida_id=kg.id,
        es_vendible=False, es_ingrediente=True, tiene_receta=False
    )
    levadura = Producto(
        nombre="Levadura", sku="LEV-001",
        categoria_id=cat.id, tipo_producto_id=tipo_mp.id, unidad_medida_id=kg.id,
        es_vendible=False, es_ingrediente=True, tiene_receta=False
    )
    db_session.add_all([harina, levadura])
    db_session.commit()
    
    # Stock Inicial de Materias Primas
    inv_harina = Inventario(producto_id=harina.id, local_id=local.id, cantidad_stock=100) # 100 KG
    inv_levadura = Inventario(producto_id=levadura.id, local_id=local.id, cantidad_stock=100) # 100 KG
    db_session.add_all([inv_harina, inv_levadura])
    db_session.commit()
    
    # 3. CREAR PRODUCTO FINAL (Marraqueta)
    marraqueta = Producto(
        nombre="Marraqueta", sku="MARRA-001",
        categoria_id=cat.id, tipo_producto_id=tipo_pe.id, unidad_medida_id=kg.id,
        es_vendible=True, es_ingrediente=False, tiene_receta=True
    )
    db_session.add(marraqueta)
    db_session.commit()
    
    # 4. CREAR RECETA
    # Para hacer 10 KG de Marraqueta se necesitan: 10 Kg Harina (ejemplo simplificado) y 0.5 Kg Levadura
    receta = Receta(
        producto_id=marraqueta.id, nombre="Receta Base Marraqueta", 
        rendimiento=10, unidad_rendimiento_id=kg.id,
        activa=True
    )
    db_session.add(receta)
    db_session.commit() # Commit para tener ID
    
    ing1 = IngredienteReceta(receta_id=receta.id, producto_ingrediente_id=harina.id, cantidad=10, unidad_medida_id=kg.id)
    ing2 = IngredienteReceta(receta_id=receta.id, producto_ingrediente_id=levadura.id, cantidad=0.5, unidad_medida_id=kg.id)
    db_session.add_all([ing1, ing2])
    db_session.commit()
    
    # -------------------------------------------------------------------------
    # TEST: FLUJO DE PRODUCCIÓN
    # -------------------------------------------------------------------------
    
    # A. Solicitar una Producción (Endpoint que vamos a crear)
    # Queremos producir 20 KG de Marraqueta
    payload = {
        "local_id": local.id,
        "detalles": [
            {
                "producto_id": marraqueta.id,
                "cantidad": 20, # Esto debería requerir 20kg Harina y 1kg Levadura
                "unidad_medida_id": kg.id
            }
        ],
        "fecha_programada": datetime.now().isoformat(),
        "notas": "Producción matutina"
    }
    
    response = client.post("/api/produccion/ordenes", json=payload)
    assert response.status_code == 200, f"Error creating order: {response.text}"
    orden_data = response.json()
    orden_id = orden_data["id"]
    assert orden_data["estado"] == "PLANIFICADA" or orden_data["estado"] == "PENDIENTE"
    
    # Verificar cálculos de requisitos (si el endpoint lo retorna)
    # O consultar un endpoint de detalles
    
    # B. Finalizar Producción (Endpoint para completar)
    # Esto debería descontar inventario y sumar producto terminado
    response_finalizar = client.post(f"/api/produccion/ordenes/{orden_id}/finalizar")
    assert response_finalizar.status_code == 200
    
    # C. Verificar Inventarios
    # Harina: Tenía 100. Usó 20 (porque la receta es 10->10, pedimos 20, so 20). Quedan 80.
    # Levadura: Tenía 100. Usó 1 (receta 10->0.5, pedimos 20, so 1). Quedan 99.
    # Marraqueta: Tenía 0. Produjo 20. Quedan 20.
    
    inv_harina_post = db_session.query(Inventario).filter_by(producto_id=harina.id, local_id=local.id).first()
    inv_levadura_post = db_session.query(Inventario).filter_by(producto_id=levadura.id, local_id=local.id).first()
    inv_marraqueta_post = db_session.query(Inventario).filter_by(producto_id=marraqueta.id, local_id=local.id).first()
    
    
    assert inv_harina_post.cantidad_stock == 80
    assert inv_levadura_post.cantidad_stock == 99
    assert inv_marraqueta_post.cantidad_stock == 20

def test_produccion_multiples_productos_mismo_insumo_sin_stock(client, db_session):
    """
    Test para reproducir bug de concurrencia/integridad:
    Dos productos distintos en una orden usan el mismo insumo (ej: Sal).
    No existe inventario previo de Sal.
    El sistema debe manejar la creación del inventario de Sal una sola vez y descontar ambos consumos.
    """
    from database.models import Producto, Receta, IngredienteReceta, UnidadMedida, TipoProducto, CategoriaProducto, Local, Inventario
    
    # Setup mínimo (Rehusando objetos si es posible, pero creando nuevos para aislamiento)
    kg = db_session.query(UnidadMedida).filter_by(codigo="KG").first()
    if not kg:
        kg = UnidadMedida(codigo="KG", nombre="Kilo", simbolo="kg", tipo="PESO", factor_conversion=1.0)
        db_session.add(kg)
        
    local = db_session.query(Local).filter_by(codigo="LOCTEST").first()
    if not local:
        local = Local(codigo="LOCTEST", nombre="Local Test", direccion="Test")
        db_session.add(local)
    
    cat = db_session.query(CategoriaProducto).first() or CategoriaProducto(codigo="TEST", nombre="T")
    tipo_pe = db_session.query(TipoProducto).filter_by(codigo="PE").first() or TipoProducto(codigo="PE", nombre="P")
    tipo_mp = db_session.query(TipoProducto).filter_by(codigo="MP").first() or TipoProducto(codigo="MP", nombre="M")
    
    if not cat.id: db_session.add(cat)
    if not tipo_pe.id: db_session.add(tipo_pe)
    if not tipo_mp.id: db_session.add(tipo_mp)
    db_session.commit()
    
    # 1. Insumo Común (Sal) - SIN INVENTARIO INICIAL
    sal = Producto(
        nombre="Sal", sku="SAL-001",
        categoria_id=cat.id, tipo_producto_id=tipo_mp.id, unidad_medida_id=kg.id,
        tiene_receta=False
    )
    db_session.add(sal)
    db_session.commit()
    
    # 2. Productos Finales (Pan A y Pan B)
    pan_a = Producto(nombre="Pan A", sku="PAN-A", categoria_id=cat.id, tipo_producto_id=tipo_pe.id, unidad_medida_id=kg.id, tiene_receta=True)
    pan_b = Producto(nombre="Pan B", sku="PAN-B", categoria_id=cat.id, tipo_producto_id=tipo_pe.id, unidad_medida_id=kg.id, tiene_receta=True)
    db_session.add_all([pan_a, pan_b])
    db_session.commit()
    
    # 3. Recetas (Ambas usan Sal)
    # Pan A: 1kg -> usa 0.1kg Sal
    receta_a = Receta(producto_id=pan_a.id, nombre="Receta A", rendimiento=1.0, unidad_rendimiento_id=kg.id)
    db_session.add(receta_a)
    db_session.commit()
    ing_a = IngredienteReceta(receta_id=receta_a.id, producto_ingrediente_id=sal.id, cantidad=0.1, unidad_medida_id=kg.id)
    db_session.add(ing_a)
    
    # Pan B: 1kg -> usa 0.2kg Sal
    receta_b = Receta(producto_id=pan_b.id, nombre="Receta B", rendimiento=1.0, unidad_rendimiento_id=kg.id)
    db_session.add(receta_b)
    db_session.commit()
    ing_b = IngredienteReceta(receta_id=receta_b.id, producto_ingrediente_id=sal.id, cantidad=0.2, unidad_medida_id=kg.id)
    db_session.add(ing_b)
    db_session.commit()
    
    # 4. Crear Orden con ambos productos
    payload = {
        "local_id": local.id,
        "detalles": [
            {"producto_id": pan_a.id, "cantidad": 10, "unidad_medida_id": kg.id}, # Usa 10 * 0.1 = 1kg Sal
            {"producto_id": pan_b.id, "cantidad": 10, "unidad_medida_id": kg.id}  # Usa 10 * 0.2 = 2kg Sal
        ],
        "fecha_programada": datetime.now().isoformat(),
        "notas": "Test Colisión Inventario"
    }
    
    response = client.post("/api/produccion/ordenes", json=payload)
    assert response.status_code == 200
    orden_id = response.json()["id"]
    
    # 5. Finalizar Orden - INTENTO 1: FALLARÁ POR FALTA DE STOCK
    response_fin = client.post(f"/api/produccion/ordenes/{orden_id}/finalizar")
    assert response_fin.status_code == 400
    assert "Stock insuficiente" in response_fin.json()["detail"]
    assert "Falta Sal" in response_fin.json()["detail"]

    # 6. Preparar inventario de Sal suficiente (3kg requeridos)
    # Total consumo esperado: 1kg (A) + 2kg (B) = 3kg.
    # Agregamos 5kg para que sobre.
    inv_sal = Inventario(producto_id=sal.id, local_id=local.id, cantidad_stock=5)
    db_session.add(inv_sal)
    db_session.commit()

    # 7. Finalizar Orden - INTENTO 2: ÉXITO
    response_fin = client.post(f"/api/produccion/ordenes/{orden_id}/finalizar")
    assert response_fin.status_code == 200
    
    # 8. Verificar Inventario de Sal
    # Tenía 5. Gastó 3. Quedan 2.
    db_session.refresh(inv_sal)
    assert float(inv_sal.cantidad_stock) == 2.0
