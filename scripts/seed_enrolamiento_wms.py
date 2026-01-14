"""
Script para cargar datos iniciales del sistema de enrolamiento WMS.
"""
import sys
import os
# Agregar el directorio raíz del proyecto al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy.orm import Session
from database.database import engine
from database.models import TipoVehiculo, EstadoEnrolamiento, Ubicacion, TipoProveedor, Proveedor


def cargar_datos_enrolamiento():
    """Cargar datos iniciales para el sistema de enrolamiento."""
    
    with Session(engine) as db:
        print("🚚 Cargando datos iniciales del sistema de enrolamiento WMS...")
        
        # ============================================
        # TIPOS DE VEHÍCULO
        # ============================================
        tipos_vehiculo = [
            {
                "codigo": "CAMION",
                "nombre": "Camión",
                "descripcion": "Camión de gran tonelaje para entrega de mercadería",
                "activo": True
            },
            {
                "codigo": "FURGON",
                "nombre": "Furgón",
                "descripcion": "Furgón mediano para entregas locales",
                "activo": True
            },
            {
                "codigo": "CAMIONETA",
                "nombre": "Camioneta",
                "descripcion": "Camioneta pickup para entregas pequeñas",
                "activo": True
            }
        ]
        
        for tipo_data in tipos_vehiculo:
            existing = db.query(TipoVehiculo).filter_by(codigo=tipo_data["codigo"]).first()
            if not existing:
                tipo = TipoVehiculo(**tipo_data)
                db.add(tipo)
                print(f"  ✅ Creado tipo de vehículo: {tipo_data['nombre']}")
            else:
                print(f"  ⏭️  Tipo de vehículo ya existe: {tipo_data['nombre']}")
        
        # ============================================
        # ESTADOS DE ENROLAMIENTO
        # ============================================
        estados_enrolamiento = [
            {
                "codigo": "PENDIENTE",
                "nombre": "Pendiente",
                "descripcion": "Vehículo registrado, pendiente de inicio de proceso",
                "activo": True
            },
            {
                "codigo": "EN_PROCESO",
                "nombre": "En Proceso",
                "descripcion": "Procesando cajas individuales del vehículo",
                "activo": True
            },
            {
                "codigo": "FINALIZADO",
                "nombre": "Finalizado",
                "descripcion": "Proceso completado, cajas disponibles para venta",
                "activo": True
            }
        ]
        
        for estado_data in estados_enrolamiento:
            existing = db.query(EstadoEnrolamiento).filter_by(codigo=estado_data["codigo"]).first()
            if not existing:
                estado = EstadoEnrolamiento(**estado_data)
                db.add(estado)
                print(f"  ✅ Creado estado: {estado_data['nombre']}")
            else:
                print(f"  ⏭️  Estado ya existe: {estado_data['nombre']}")
        
        # ============================================
        # UBICACIONES DE ALMACÉN
        # ============================================
        ubicaciones = [
            # Piso 1, Sector A (Carnes frescas)
            {"codigo": "P1-A-01", "nombre": "Cámaras Frío Sector A-01", "descripcion": "Cámara frigorífica para carnes rojas", "capacidad_maxima": 50},
            {"codigo": "P1-A-02", "nombre": "Cámaras Frío Sector A-02", "descripcion": "Cámara frigorífica para aves", "capacidad_maxima": 40},
            {"codigo": "P1-A-03", "nombre": "Cámaras Frío Sector A-03", "descripcion": "Cámara frigorífica para embutidos", "capacidad_maxima": 30},
            
            # Piso 1, Sector B (Productos secos)
            {"codigo": "P1-B-01", "nombre": "Estantería B-01", "descripcion": "Productos secos nivel bajo", "capacidad_maxima": 60},
            {"codigo": "P1-B-02", "nombre": "Estantería B-02", "descripcion": "Productos secos nivel medio", "capacidad_maxima": 60},
            {"codigo": "P1-B-03", "nombre": "Estantería B-03", "descripcion": "Productos secos nivel alto", "capacidad_maxima": 60},
            
            # Sector C (Área de preparación)
            {"codigo": "P1-C-01", "nombre": "Mesa Preparación 1", "descripcion": "Mesa para reempaque y etiquetado", "capacidad_maxima": 20},
            {"codigo": "P1-C-02", "nombre": "Mesa Preparación 2", "descripcion": "Mesa para control de calidad", "capacidad_maxima": 20},
            
            # Área de cuarentena
            {"codigo": "CUARENTENA", "nombre": "Área Cuarentena", "descripcion": "Productos en revisión antes de liberación", "capacidad_maxima": 25}
        ]
        
        for ubicacion_data in ubicaciones:
            existing = db.query(Ubicacion).filter_by(codigo=ubicacion_data["codigo"]).first()
            if not existing:
                ubicacion = Ubicacion(**ubicacion_data)
                db.add(ubicacion)
                print(f"  ✅ Creada ubicación: {ubicacion_data['codigo']} - {ubicacion_data['nombre']}")
            else:
                print(f"  ⏭️  Ubicación ya existe: {ubicacion_data['codigo']}")
        
        # ============================================
        # VERIFICAR PROVEEDORES DE CARNES
        # ============================================
        tipo_carnes = db.query(TipoProveedor).filter_by(codigo="CARNES").first()
        if tipo_carnes:
            proveedores_carnes = db.query(Proveedor).filter_by(tipo_proveedor_id=tipo_carnes.id).all()
            print(f"\n🥩 Proveedores de tipo CARNES disponibles para enrolamiento:")
            for proveedor in proveedores_carnes:
                print(f"  📋 ID {proveedor.id}: {proveedor.nombre} ({proveedor.rut})")
            if not proveedores_carnes:
                print("  ⚠️  No hay proveedores de tipo CARNES. Crear algunos para testing.")
        else:
            print("  ❌ Tipo de proveedor CARNES no encontrado. Ejecutar seed de tipos de proveedor primero.")
        
        db.commit()
        print("\n✅ Datos iniciales del sistema de enrolamiento cargados exitosamente!")
        print("\n📊 Resumen cargado:")
        print(f"   • {len(tipos_vehiculo)} tipos de vehículo")
        print(f"   • {len(estados_enrolamiento)} estados de enrolamiento") 
        print(f"   • {len(ubicaciones)} ubicaciones de almacén")
        
        print("\n🚀 El sistema de enrolamiento WMS está listo para uso!")
        print("\n📝 Próximos pasos:")
        print("   1. Registrar enrolamientos de camiones con proveedores CARNES")
        print("   2. Procesar cajas individuales (foto + QR + peso)")
        print("   3. Finalizar enrolamientos para activar disponibilidad de venta")


if __name__ == "__main__":
    cargar_datos_enrolamiento()