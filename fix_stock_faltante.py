"""
Fix: detecta registros faltantes en stock_cajas_proveedor
comparando con los lotes_caja_variable reales.
"""
import sys
sys.path.insert(0, '/app')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
import os

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://fme:fme@db:5432/fme_database")
engine = create_engine(DATABASE_URL)

with Session(engine) as db:
    # Obtener todos los pares (producto, proveedor) con lotes, agrupados por tenant
    pares_con_lotes = db.execute(text("""
        SELECT
            l.producto_id,
            l.proveedor_id,
            p.tenant_id,
            p.nombre AS producto_nombre,
            pr.nombre AS proveedor_nombre,
            COUNT(*) AS total_lotes,
            SUM(CASE WHEN l.disponible_venta = TRUE THEN 1 ELSE 0 END) AS cajas_disponibles,
            SUM(CASE WHEN l.disponible_venta = FALSE THEN 1 ELSE 0 END) AS cajas_vendidas_ajustadas
        FROM lotes_caja_variable l
        JOIN productos p ON p.id = l.producto_id
        JOIN proveedores pr ON pr.id = l.proveedor_id
        GROUP BY l.producto_id, l.proveedor_id, p.tenant_id, p.nombre, pr.nombre
        ORDER BY p.tenant_id, p.nombre, pr.nombre
    """)).fetchall()

    print(f"\n=== Pares (producto, proveedor) en lotes_caja_variable ===")
    for row in pares_con_lotes:
        print(f"  tenant={row.tenant_id} | {row.producto_nombre} | {row.proveedor_nombre} | "
              f"total={row.total_lotes} | disp={row.cajas_disponibles} | vendidas={row.cajas_vendidas_ajustadas}")

    # Obtener registros existentes en stock_cajas_proveedor
    existentes = db.execute(text("""
        SELECT producto_id, proveedor_id FROM stock_cajas_proveedor
    """)).fetchall()
    existentes_set = {(r.producto_id, r.proveedor_id) for r in existentes}
    print(f"\n=== Registros en stock_cajas_proveedor: {len(existentes_set)} ===")

    # Detectar faltantes
    faltantes = []
    for row in pares_con_lotes:
        if (row.producto_id, row.proveedor_id) not in existentes_set:
            faltantes.append(row)

    if not faltantes:
        print("\n✅ No hay registros faltantes en stock_cajas_proveedor")
    else:
        print(f"\n⚠️  Faltan {len(faltantes)} registros. Creando...")
        for row in faltantes:
            db.execute(text("""
                INSERT INTO stock_cajas_proveedor
                    (producto_id, proveedor_id, cajas_disponibles, cajas_totales_recibidas,
                     cajas_totales_vendidas, fecha_ultima_actualizacion)
                VALUES
                    (:prod_id, :prov_id, :disp, :total, :vendidas, NOW())
                ON CONFLICT (producto_id, proveedor_id) DO NOTHING
            """), {
                "prod_id": row.producto_id,
                "prov_id": row.proveedor_id,
                "disp": row.cajas_disponibles,
                "total": row.total_lotes,
                "vendidas": row.cajas_vendidas_ajustadas,
            })
            print(f"  ✅ Creado: tenant={row.tenant_id} | {row.producto_nombre} | {row.proveedor_nombre} "
                  f"| disp={row.cajas_disponibles} | total={row.total_lotes}")
        db.commit()
        print("\n✅ Todos los registros faltantes creados.")

    # Verificación final tenant=2
    print("\n=== Stock tenant=2 (El Olivo) FINAL ===")
    result = db.execute(text("""
        SELECT p.nombre, pr.nombre AS proveedor, s.cajas_disponibles, s.cajas_totales_recibidas
        FROM stock_cajas_proveedor s
        JOIN productos p ON p.id = s.producto_id
        JOIN proveedores pr ON pr.id = s.proveedor_id
        WHERE p.tenant_id = 2
        ORDER BY p.nombre, pr.nombre
    """)).fetchall()
    for row in result:
        print(f"  {row.nombre} | {row.proveedor} | disp={row.cajas_disponibles} | rec={row.cajas_totales_recibidas}")
