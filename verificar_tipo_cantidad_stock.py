import subprocess
import sys

# Ejecutar comando SQL remotamente
cmd = [
    "ssh", "root@168.231.96.205",
    "docker exec masas_estacion_db psql -U fme -d fme_database -c \"SELECT column_name, data_type, character_maximum_length, numeric_precision, is_nullable FROM information_schema.columns WHERE table_name = 'inventario' AND column_name = 'cantidad_stock';\""
]

print("=" * 80)
print("TIPO DE DATOS DE 'cantidad_stock' EN TABLA 'inventario'")
print("=" * 80)
print()

result = subprocess.run(cmd, capture_output=True, text=True)

if result.returncode == 0:
    print(result.stdout)
else:
    print("Error:")
    print(result.stderr)
    sys.exit(1)

# También consultar si existen CHECK constraints
print("\n" + "=" * 80)
print("CHECK CONSTRAINTS EN 'cantidad_stock'")
print("=" * 80)
print()

cmd2 = [
    "ssh", "root@168.231.96.205",
    "docker exec masas_estacion_db psql -U fme -d fme_database -c \"SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid = 'inventario'::regclass AND contype = 'c';\""
]

result2 = subprocess.run(cmd2, capture_output=True, text=True)

if result2.returncode == 0:
    output = result2.stdout.strip()
    if output and len(output.split('\n')) > 2:  # Más que solo headers
        print(output)
    else:
        print("❌ NO hay CHECK constraints en la tabla 'inventario'")
        print("⚠️  Esto significa que cantidad_stock ACEPTA valores negativos")
else:
    print("Error:")
    print(result2.stderr)
