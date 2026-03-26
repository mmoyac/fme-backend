#!/usr/bin/env python3
"""
Hook de pre-commit: valida que la cadena de migraciones Alembic sea consistente.
Verifica que todo down_revision referenciado exista como archivo en el repo.
"""
import re
import subprocess
import sys
from pathlib import Path

MIGRATIONS_DIR = Path("migrations/versions")

def get_staged_migration_files():
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        capture_output=True, text=True
    )
    return [
        Path(f) for f in result.stdout.splitlines()
        if f.startswith("migrations/versions/") and f.endswith(".py")
    ]

def get_all_known_revisions():
    """Revisiones en el repo (commiteadas) + staged."""
    revisions = set()

    # Commiteadas
    result = subprocess.run(
        ["git", "ls-files", str(MIGRATIONS_DIR)],
        capture_output=True, text=True
    )
    for filepath in result.stdout.splitlines():
        content = Path(filepath).read_text(encoding="utf-8")
        match = re.search(r"^Revision ID:\s*(\w+)", content, re.MULTILINE)
        if match:
            revisions.add(match.group(1))

    # Staged (pueden ser nuevas, no están en ls-files aún)
    for filepath in get_staged_migration_files():
        if filepath.exists():
            content = filepath.read_text(encoding="utf-8")
            match = re.search(r"^Revision ID:\s*(\w+)", content, re.MULTILINE)
            if match:
                revisions.add(match.group(1))

    return revisions

def get_down_revisions_from_staged():
    """Obtiene los down_revision de los archivos staged."""
    deps = []
    for filepath in get_staged_migration_files():
        if not filepath.exists():
            continue
        content = filepath.read_text(encoding="utf-8")
        match = re.search(r'down_revision[^=]*=\s*[\'"](\w+)[\'"]', content)
        if match:
            deps.append((filepath, match.group(1)))
    return deps

def main():
    staged = get_staged_migration_files()
    if not staged:
        sys.exit(0)

    known = get_all_known_revisions()
    errors = []

    for filepath, downrev in get_down_revisions_from_staged():
        if downrev not in known:
            errors.append(
                f"  {filepath.name}\n"
                f"    → down_revision='{downrev}' no existe en el repositorio.\n"
                f"    → Ejecuta: git add migrations/versions/*{downrev}*"
            )

    if errors:
        print("\n[ERROR] Cadena de migraciones Alembic incompleta:")
        for e in errors:
            print(e)
        print("\nCommit bloqueado. Agrega las migraciones faltantes antes de commitear.\n")
        sys.exit(1)

    print("[OK] Cadena de migraciones Alembic verificada.")
    sys.exit(0)

if __name__ == "__main__":
    main()
