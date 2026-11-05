"""Inspecciona migraciones locales sin aplicar SQL ni modificar la base.

El baseline 20261008100000_schema_mvp_final.sql contiene DROP TABLE ... CASCADE.
La alineación del historial remoto debe verificarse mediante Supabase CLI antes

de cualquier push. Este script existe intencionalmente como preflight local,
no como migrador SQL propio.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = ROOT / "supabase" / "migrations"
VERSION_RE = re.compile(r"^(\d{12,14})_.*\.sql$")


def main() -> int:
    if not MIGRATIONS.is_dir():
        print(f"ERROR: no existe {MIGRATIONS}")
        return 1

    files = sorted(MIGRATIONS.glob("*.sql"))
    if not files:
        print("ERROR: no hay migraciones SQL en supabase/migrations.")
        return 1

    versions: set[str] = set()
    destructive: list[str] = []
    malformed: list[str] = []
    print("SGI migration preflight — SOLO LECTURA")
    print("Este comando no abre una conexión ni ejecuta sentencias SQL.\n")
    for path in files:
        match = VERSION_RE.match(path.name)
        if not match:
            malformed.append(path.name)
        else:
            version = match.group(1)
            if version in versions:
                print(f"ERROR: versión duplicada {version}: {path.name}")
                return 1
            versions.add(version)
        sql = path.read_text(encoding="utf-8", errors="replace")
        if re.search(r"\bDROP\s+TABLE\b|\bTRUNCATE\b", sql, re.IGNORECASE):
            destructive.append(path.name)
        print(f"  {'DESTRUCTIVA' if path.name in destructive else 'revisada'}  {path.name}")

    if malformed:
        print("\nERROR: nombres no versionados: " + ", ".join(malformed))
        return 1
    print(f"\nMigraciones locales: {len(files)}")
    if destructive:
        print("\nATENCIÓN: contienen DROP TABLE/TRUNCATE y no deben reejecutarse sobre la BD cargada:")
        for filename in destructive:
            print(f"  - {filename}")
    print("\nSiguiente paso manual seguro:")
    print("  1. supabase migration list --linked")
    print("  2. Verificar que cada migración destructiva ya figure aplicada en el historial remoto.")
    print("  3. Solo si el historial coincide, evaluar supabase db push --linked.")
    print("  4. Ejecutar python scripts/check_db.py y revisar errores/advertencias.")
    print("No utilizar un --reset ni ejecutar archivos de migración directamente con psql.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
