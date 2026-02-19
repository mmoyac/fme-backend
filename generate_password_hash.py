"""
Script para generar hash de contraseña usando Argon2
"""
from passlib.context import CryptContext

# Mismo esquema que usa el backend
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

password = "admin"
hashed = pwd_context.hash(password)

print(f"Password: {password}")
print(f"Hash: {hashed}")
print(f"Longitud: {len(hashed)}")

# Verificar que funciona
if pwd_context.verify(password, hashed):
    print("✅ Hash verificado correctamente")
else:
    print("❌ Error en verificación")
