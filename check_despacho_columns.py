from database.models import Despacho

print('Columnas de Despacho:')
for col in Despacho.__table__.columns:
    print(f'  - {col.name}: {col.type}')
