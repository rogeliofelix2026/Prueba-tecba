# Puesta en marcha local — SGI Backend

## 1. Requisitos

- Python 3.12 o 3.13.
- PostgreSQL con PostGIS y pgvector, o Supabase.
- Ollama solo si se utilizarán RAG/IA.
- Datos GIS/CSV/PDF solo si se ejecuta la ingesta.

## 2. Entorno Python

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 3. Configuración

```powershell
Copy-Item .env.example .env
```

Definir al menos:

```dotenv
DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/DATABASE
```

## 4. Crear la base del MVP

El backend ya no utiliza una cadena de migraciones incrementales. El contrato estructural es el baseline:

```text
SGI_SCHEMA_MVP_FINAL.sql
```

Para una base vacía:

```powershell
python scripts/migrate.py
```

Para reconstruir deliberadamente las tablas del modelo SGI:

```powershell
python scripts/migrate.py --reset
```

No usar `--reset` en una base con datos que deban conservarse.

Supabase mantiene el mismo baseline en:

```text
supabase/migrations/20261008100000_schema_mvp_final.sql
```

## 5. Verificación

```powershell
python scripts/check_db.py
```

Debe terminar con:

```text
DB OK: schema MVP definitivo compatible.
```

## 6. API

```powershell
uvicorn app.main:app --reload
```

Documentación:

```text
http://127.0.0.1:8000/docs
```

## 7. Prueba territorial

Geocodificación:

```powershell
$body = @{ address = "Corrientes 2500" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/v1/geocoding -ContentType "application/json" -Body $body
```

Territorio por coordenadas o SMP:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/v1/territory?smp=09-123-456"
```

Diagnóstico PostGIS:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/v1/territory/postgis-check?latitude=-34.604792&longitude=-58.401981"
```

## 8. Datos en el orden recomendado

```text
1. fuente de parcelas
2. → parcels
3. Código Urbanístico
4. → urban_parcel_rules + parcel_special_districts
5. RUS
6. → land_use_observations
7. Cuadro 3.3
8. → activities + activity_use_rules
9. procedimientos y documentos
10. → RAG/evidencia
```

La ingesta del Código Urbanístico exige que el SMP ya exista en `parcels`.

## 9. Tests

```powershell
python -m pytest -q tests --ignore=tests/test_supabase_connection.py
```

La prueba de conexión de Supabase requiere una `DATABASE_URL` real.
