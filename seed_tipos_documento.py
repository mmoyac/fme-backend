#!/usr/bin/env python3
"""
Script para insertar tipos de documento tributario básicos.
"""
import sys
sys.path.append('.')

from database.database import SessionLocal
from database.models import TipoDocumento

def seed_tipos_documento():
    """Insertar tipos de documento básicos."""
    db = SessionLocal()
    try:
        # Verificar si ya existen
        if db.query(TipoDocumento).count() > 0:
            print("✅ Los tipos de documento ya existen")
            return
        
        tipos_documento = [
            {
                "codigo": "BOLETA",
                "nombre": "Boleta",
                "descripcion": "Documento para consumo final (personas)",
                "activo": True
            },
            {
                "codigo": "FACTURA", 
                "nombre": "Factura",
                "descripcion": "Documento para empresas con RUT",
                "activo": True
            },
            {
                "codigo": "NOTA_CREDITO_BOLETA",
                "nombre": "Nota de Crédito Boleta", 
                "descripcion": "Anula o modifica una boleta (devoluciones, descuentos)",
                "activo": True
            },
            {
                "codigo": "NOTA_CREDITO_FACTURA",
                "nombre": "Nota de Crédito Factura",
                "descripcion": "Anula o modifica una factura (devoluciones, descuentos)", 
                "activo": True
            },
            {
                "codigo": "NOTA_DEBITO_BOLETA",
                "nombre": "Nota de Débito Boleta",
                "descripcion": "Cargos adicionales sobre una boleta",
                "activo": True
            },
            {
                "codigo": "NOTA_DEBITO_FACTURA", 
                "nombre": "Nota de Débito Factura",
                "descripcion": "Cargos adicionales sobre una factura",
                "activo": True
            },
            {
                "codigo": "GUIA_DESPACHO",
                "nombre": "Guía de Despacho",
                "descripcion": "Documento para traslado de mercancías",
                "activo": True
            }
        ]
        
        for tipo_data in tipos_documento:
            tipo = TipoDocumento(**tipo_data)
            db.add(tipo)
        
        db.commit()
        print("✅ Tipos de documento tributario creados exitosamente:")
        
        # Mostrar los tipos creados
        tipos = db.query(TipoDocumento).all()
        for tipo in tipos:
            print(f"  - ID: {tipo.id}, Código: {tipo.codigo}, Nombre: {tipo.nombre}")
            
    except Exception as e:
        db.rollback()
        print(f"❌ Error creando tipos de documento: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_tipos_documento()