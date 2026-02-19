from database.models import ItemPedido

print('Columnas de ItemPedido:')
for col in ItemPedido.__table__.columns:
    print(f'  - {col.name}: {col.type}')
