from database.database import SessionLocal
from database.models import User

db = SessionLocal()

# Buscar todos los usuarios del tenant 2
usuarios = db.query(User).filter(User.tenant_id == 2).all()

print(f'Total usuarios tenant 2: {len(usuarios)}')
print()

for usuario in usuarios:
    print(f'Usuario ID {usuario.id}:')
    print(f'  Nombre: {usuario.nombre_completo}')
    print(f'  Email: {usuario.email}')
    print(f'  Role: {usuario.role.nombre if usuario.role else "Sin rol"}')
    print(f'  Activo: {usuario.is_active}')
    print()
