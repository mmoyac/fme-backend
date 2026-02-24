from sqlalchemy import create_engine, text

# Conectar a producción usando SQLAlchemy
DATABASE_URL = "postgresql://fme:fme@168.231.96.205:5432/fme_database"
engine = create_engine(DATABASE_URL)

print("=" * 80)
print("ESTRUCTURA DE LA TABLA 'inventario' EN PRODUCCIÓN")
print("=" * 80)

with engine.connect() as conn:
    # Ver columnas
    print("\n📋 COLUMNAS:")
    result = conn.execute(text("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns 
        WHERE table_name = 'inventario'
        ORDER BY ordinal_position;
    """))
    for row in result:
        print(f"  • {row[0]:<20} {row[1]:<15} nullable={row[2]:<3} default={row[3]}")
    
    # Ver constraints
    print("\n🔒 CONSTRAINTS:")
    result = conn.execute(text("""
        SELECT 
            con.conname AS constraint_name,
            con.contype AS constraint_type,
            pg_get_constraintdef(con.oid) AS constraint_definition
        FROM pg_constraint con
        JOIN pg_class rel ON rel.oid = con.conrelid
        WHERE rel.relname = 'inventario';
    """))
    
    constraints = list(result)
    if constraints:
        for row in constraints:
            tipo_map = {'p': 'PRIMARY KEY', 'f': 'FOREIGN KEY', 'u': 'UNIQUE', 'c': 'CHECK'}
            tipo = tipo_map.get(row[1], row[1])
            print(f"  • {row[0]:<40} [{tipo}]")
            print(f"    {row[2]}")
    else:
        print("  (no hay constraints adicionales)")
    
    # Verificar CHECK constraints específicamente en cantidad_stock
    print("\n🔍 CHECK CONSTRAINTS en cantidad_stock:")
    result = conn.execute(text("""
        SELECT con.conname, pg_get_constraintdef(con.oid)
        FROM pg_constraint con
        JOIN pg_class rel ON rel.oid = con.conrelid
        WHERE rel.relname = 'inventario' 
        AND con.contype = 'c'
        AND pg_get_constraintdef(con.oid) LIKE '%cantidad_stock%';
    """))
    
    check_constraints = list(result)
    if check_constraints:
        for row in check_constraints:
            print(f"  ✅ {row[0]}: {row[1]}")
    else:
        print("  ❌ NO hay CHECK constraint en cantidad_stock")
        print("  ⚠️  La tabla ACEPTA valores negativos")

print("=" * 80)
