# PostgreSQL administrado / Supabase — SGI

El backend utiliza PostgreSQL + PostGIS + pgvector. El esquema definitivo está preparado para Supabase/PostgreSQL y mantiene los archivos originales fuera de la base para limitar consumo de almacenamiento.

## Extensiones requeridas

```text
postgis
vector
unaccent
pgcrypto
```

No se requiere `pg_trgm` en el schema MVP definitivo.

## Bootstrap

1. Crear la base/proyecto PostgreSQL.
2. Aplicar `SGI_SCHEMA_MVP_FINAL.sql` sobre una base vacía o usar la migración de Supabase.
3. Verificar con:

```powershell
python scripts/check_db.py
```

## Separación de responsabilidades

El usuario/rol de bootstrap debe poder crear extensiones y tablas. El usuario de runtime de FastAPI solo necesita los permisos de lectura/escritura sobre el modelo de aplicación.

La API no necesita permisos para crear el schema en cada arranque.

## Almacenamiento

El objetivo para el MVP es conservar en PostgreSQL únicamente:

- entidades normalizadas;
- geometría de parcelas necesaria para PostGIS;
- reglas determinísticas;
- metadatos y proveniencia;
- chunks de documentos y embeddings cuando realmente sean necesarios;
- trazabilidad de consultas.

Los GeoJSON, CSV, XLSX y PDF originales deben almacenarse fuera de PostgreSQL y referenciarse mediante `source_resources`.

## 500 MB

Con un límite de almacenamiento reducido, evitar:

- duplicar SMP/sección/manzana/parcela;
- `raw` JSONB por cada parcela;
- historial completo de geometrías dentro de la DB;
- índices generales que no correspondan a consultas reales;
- generar embeddings para documentos que todavía no participan del MVP.

`document_chunks.embedding` utiliza `halfvec(1024)` y el HNSW solo se crea para embeddings existentes.
