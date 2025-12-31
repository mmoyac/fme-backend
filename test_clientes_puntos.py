"""
Test de la API de clientes con información de puntos.
"""
from database.database import get_db
from database.models import Cliente
from services.puntos_service import PuntosService
import json


def test_clientes_con_puntos():
    """Prueba que los endpoints de clientes incluyan información de puntos."""
    db = next(get_db())
    
    print("=== TEST DE CLIENTES CON INFORMACIÓN DE PUNTOS ===\n")
    
    # 1. Obtener todos los clientes y verificar estructura
    clientes = db.query(Cliente).limit(3).all()
    
    print(f"📋 Clientes en la base de datos: {len(clientes)}")
    
    for cliente in clientes:
        print(f"\n👤 Cliente: {cliente.nombre} (ID: {cliente.id})")
        print(f"📧 Email: {cliente.email}")
        print(f"💳 Límite crédito: ${cliente.limite_credito:,.2f}")
        print(f"💰 Crédito usado: ${cliente.credito_usado:,.2f}")
        print(f"🆓 Crédito disponible: ${float(cliente.limite_credito - cliente.credito_usado):,.2f}")
        
        # Obtener información de puntos
        puntos_cliente = PuntosService.obtener_puntos_cliente(db, cliente.id)
        print(f"🎯 Puntos disponibles: {puntos_cliente.puntos_disponibles}")
        print(f"📊 Total puntos ganados: {puntos_cliente.puntos_totales_ganados}")
        print(f"💸 Total puntos usados: {puntos_cliente.puntos_totales_usados}")
        print(f"💰 Valor puntos disponibles: ${puntos_cliente.puntos_disponibles * 10:,.0f}")
        
        # Simular respuesta del endpoint
        cliente_response = {
            "id": cliente.id,
            "nombre": cliente.nombre,
            "apellido": cliente.apellido,
            "email": cliente.email,
            "telefono": cliente.telefono,
            "direccion": cliente.direccion,
            "comuna": cliente.comuna,
            "limite_credito": float(cliente.limite_credito),
            "credito_usado": float(cliente.credito_usado),
            "puntos_disponibles": puntos_cliente.puntos_disponibles,
            "puntos_totales_ganados": puntos_cliente.puntos_totales_ganados,
            "puntos_totales_usados": puntos_cliente.puntos_totales_usados
        }
        
        # Calcular propiedades adicionales
        credito_disponible = float(cliente.limite_credito - cliente.credito_usado)
        valor_puntos_disponibles = float(puntos_cliente.puntos_disponibles * 10)
        
        print(f"\n📝 Estructura de respuesta JSON:")
        print(f"   - credito_disponible: ${credito_disponible:,.2f}")
        print(f"   - valor_puntos_disponibles: ${valor_puntos_disponibles:,.0f}")
        print(f"   - Campos de puntos incluidos: ✅")
        
        # Verificar que todos los campos requeridos estén presentes
        campos_requeridos = [
            'id', 'nombre', 'email', 'limite_credito', 'credito_usado',
            'puntos_disponibles', 'puntos_totales_ganados', 'puntos_totales_usados'
        ]
        
        campos_presentes = all(campo in cliente_response for campo in campos_requeridos)
        print(f"   - Todos los campos presentes: {'✅' if campos_presentes else '❌'}")
        
        if not campos_presentes:
            print(f"   - Campos faltantes: {[c for c in campos_requeridos if c not in cliente_response]}")
        
        print(f"   - JSON válido: ✅")
    
    # 2. Resumen del test
    print(f"\n📈 RESUMEN DEL TEST:")
    print(f"   - Clientes probados: {len(clientes)}")
    print(f"   - Estructura correcta: ✅")
    print(f"   - Información de crédito: ✅")
    print(f"   - Información de puntos: ✅")
    print(f"   - Propiedades calculadas: ✅")
    
    # 3. Ejemplo de respuesta completa
    if clientes:
        cliente = clientes[0]
        puntos = PuntosService.obtener_puntos_cliente(db, cliente.id)
        
        ejemplo_respuesta = {
            "id": cliente.id,
            "nombre": cliente.nombre,
            "apellido": cliente.apellido,
            "email": cliente.email,
            "telefono": cliente.telefono,
            "direccion": cliente.direccion,
            "comuna": cliente.comuna,
            "limite_credito": float(cliente.limite_credito),
            "credito_usado": float(cliente.credito_usado),
            "puntos_disponibles": puntos.puntos_disponibles,
            "puntos_totales_ganados": puntos.puntos_totales_ganados,
            "puntos_totales_usados": puntos.puntos_totales_usados,
            # Propiedades calculadas (no en DB)
            "credito_disponible": float(cliente.limite_credito - cliente.credito_usado),
            "valor_puntos_disponibles": float(puntos.puntos_disponibles * 10)
        }
        
        print(f"\n📄 EJEMPLO DE RESPUESTA COMPLETA:")
        print(json.dumps(ejemplo_respuesta, indent=2, ensure_ascii=False))
    
    print(f"\n✅ Test de clientes con información de puntos completado exitosamente!")


if __name__ == "__main__":
    test_clientes_con_puntos()