#!/usr/bin/env python3
"""
Script para gestión y control de facturas SII.
"""
import sys
sys.path.append('.')

from datetime import datetime
from database.database import SessionLocal
from database.models import Pedido, TipoDocumento, Cliente

def mostrar_facturas_pendientes():
    """Mostrar facturas pendientes de envío al SII."""
    db = SessionLocal()
    try:
        # Buscar tipo de documento FACTURA
        tipo_factura = db.query(TipoDocumento).filter(TipoDocumento.codigo == "FAC").first()
        if not tipo_factura:
            print("❌ No se encontró tipo de documento FACTURA")
            return
        
        # Facturas pendientes de SII
        facturas_pendientes = db.query(Pedido).filter(
            Pedido.tipo_documento_tributario_id == tipo_factura.id,
            Pedido.estado_sii.in_(["PENDIENTE", None])
        ).all()
        
        print(f"\n📋 FACTURAS PENDIENTES DE ENVÍO AL SII")
        print("=" * 60)
        
        if not facturas_pendientes:
            print("✅ No hay facturas pendientes de envío")
            return
        
        print(f"Total: {len(facturas_pendientes)} facturas")
        print()
        
        for pedido in facturas_pendientes:
            cliente = db.query(Cliente).filter(Cliente.id == pedido.cliente_id).first()
            print(f"🧾 Pedido #{pedido.numero_pedido}")
            print(f"   📅 Fecha: {pedido.fecha_pedido.strftime('%d/%m/%Y %H:%M')}")
            print(f"   👤 Cliente: {cliente.nombre if cliente else 'N/A'}")
            print(f"   🆔 RUT: {cliente.rut if cliente and cliente.rut else 'Sin RUT'}")
            print(f"   💰 Total: ${pedido.monto_total:,.0f}")
            print(f"   📄 Estado: {pedido.estado}")
            print(f"   🏛️ Estado SII: {pedido.estado_sii or 'PENDIENTE'}")
            print("-" * 50)
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

def marcar_factura_enviada(numero_pedido: str, folio_sii: str):
    """Marcar una factura como enviada al SII."""
    db = SessionLocal()
    try:
        pedido = db.query(Pedido).filter(Pedido.numero_pedido == numero_pedido).first()
        if not pedido:
            print(f"❌ No se encontró pedido #{numero_pedido}")
            return
        
        # Actualizar estado SII
        pedido.estado_sii = "ENVIADO"
        pedido.folio_sii = folio_sii
        pedido.fecha_envio_sii = datetime.now()
        
        db.commit()
        print(f"✅ Factura #{numero_pedido} marcada como enviada al SII")
        print(f"   📋 Folio SII: {folio_sii}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
    finally:
        db.close()

def marcar_factura_aprobada(folio_sii: str, numero_dte: str = None):
    """Marcar una factura como aprobada por el SII."""
    db = SessionLocal()
    try:
        pedido = db.query(Pedido).filter(Pedido.folio_sii == folio_sii).first()
        if not pedido:
            print(f"❌ No se encontró pedido con folio SII #{folio_sii}")
            return
        
        # Actualizar estado SII
        pedido.estado_sii = "APROBADO"
        pedido.fecha_respuesta_sii = datetime.now()
        if numero_dte:
            pedido.numero_dte = numero_dte
        
        db.commit()
        print(f"✅ Factura con folio #{folio_sii} marcada como APROBADA")
        if numero_dte:
            print(f"   📄 Número DTE: {numero_dte}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
    finally:
        db.close()

def mostrar_resumen_sii():
    """Mostrar resumen de estados SII."""
    db = SessionLocal()
    try:
        # Buscar tipo de documento FACTURA
        tipo_factura = db.query(TipoDocumento).filter(TipoDocumento.codigo == "FAC").first()
        if not tipo_factura:
            print("❌ No se encontró tipo de documento FACTURA")
            return
        
        print(f"\n📊 RESUMEN DE FACTURAS SII")
        print("=" * 40)
        
        # Contar por estado
        estados = ["PENDIENTE", "ENVIADO", "APROBADO", "RECHAZADO"]
        for estado in estados:
            count = db.query(Pedido).filter(
                Pedido.tipo_documento_tributario_id == tipo_factura.id,
                Pedido.estado_sii == estado
            ).count()
            print(f"{estado.ljust(12)}: {count} facturas")
        
        # Pendientes (NULL)
        count_null = db.query(Pedido).filter(
            Pedido.tipo_documento_tributario_id == tipo_factura.id,
            Pedido.estado_sii.is_(None)
        ).count()
        print(f"{'SIN ESTADO'.ljust(12)}: {count_null} facturas")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Gestión de facturas SII")
    parser.add_argument("--accion", choices=["pendientes", "enviada", "aprobada", "resumen"], 
                       default="pendientes", help="Acción a realizar")
    parser.add_argument("--pedido", help="Número de pedido")
    parser.add_argument("--folio", help="Folio SII")
    parser.add_argument("--dte", help="Número DTE")
    
    args = parser.parse_args()
    
    if args.accion == "pendientes":
        mostrar_facturas_pendientes()
    elif args.accion == "enviada":
        if not args.pedido or not args.folio:
            print("❌ Se requiere --pedido y --folio")
        else:
            marcar_factura_enviada(args.pedido, args.folio)
    elif args.accion == "aprobada":
        if not args.folio:
            print("❌ Se requiere --folio")
        else:
            marcar_factura_aprobada(args.folio, args.dte)
    elif args.accion == "resumen":
        mostrar_resumen_sii()