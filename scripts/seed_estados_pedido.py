#!/usr/bin/env python
"""
Script para poblar la tabla estados_pedido con los estados iniciales.

Uso:
    docker exec -it fme-backend python scripts/seed_estados_pedido.py
"""

from database.database import SessionLocal
from database.models import EstadoPedido

def seed_estados_pedido():
    """Crea los estados de pedido iniciales."""
    db = SessionLocal()
    
    try:
        # Verificar si ya existen estados
        count = db.query(EstadoPedido).count()
        if count > 0:
            print(f'✓ Ya existen {count} estados de pedido en la base de datos')
            return
        
        # Estados iniciales
        estados = [
            {
                'id': 1,
                'codigo': 'PENDIENTE',
                'nombre': 'Pendiente',
                'descripcion': 'Pedido creado, pendiente de confirmación',
                'color': 'yellow-500',
                'orden': 1,
                'es_final': False
            },
            {
                'id': 2,
                'codigo': 'CONFIRMADO',
                'nombre': 'Confirmado',
                'descripcion': 'Pedido confirmado, inventario descontado',
                'color': 'blue-500',
                'orden': 2,
                'es_final': False
            },
            {
                'id': 3,
                'codigo': 'EN_PREPARACION',
                'nombre': 'En Preparación',
                'descripcion': 'Pedido en proceso de preparación',
                'color': 'purple-500',
                'orden': 3,
                'es_final': False
            },
            {
                'id': 4,
                'codigo': 'ENTREGADO',
                'nombre': 'Entregado',
                'descripcion': 'Pedido entregado al cliente',
                'color': 'green-500',
                'orden': 4,
                'es_final': True
            },
            {
                'id': 5,
                'codigo': 'CANCELADO',
                'nombre': 'Cancelado',
                'descripcion': 'Pedido cancelado',
                'color': 'red-500',
                'orden': 5,
                'es_final': True
            }
        ]
        
        print('Creando estados de pedido...')
        for estado_data in estados:
            estado = EstadoPedido(**estado_data)
            db.add(estado)
            print(f'  ✓ {estado_data["nombre"]} ({estado_data["codigo"]})')
        
        db.commit()
        print(f'\n✅ {len(estados)} estados de pedido creados exitosamente')
        
    except Exception as e:
        db.rollback()
        print(f'\n❌ Error: {e}')
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == '__main__':
    seed_estados_pedido()
