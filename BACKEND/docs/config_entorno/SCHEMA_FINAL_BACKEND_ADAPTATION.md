# Adaptación del backend al schema MVP definitivo

## Contrato aplicado

El backend utiliza `SGI_SCHEMA_MVP_FINAL.sql` como única referencia estructural.

### Territorio

- `parcels` es la entidad territorial canónica.
- `smp` es UNIQUE en `parcels`.
- Tablas hijas usan `parcel_id`.
- `urban_parcel_rules` conserva solo `uso_1..3`.
- `parcel_special_districts` reemplaza columnas repetitivas de distritos.
- `land_use_observations` no repite SMP/barrio ni datos catastrales.

### Geocoding

- El cache conserva `smp` por trazabilidad del proveedor.
- `resolved_parcel_id` conecta el resultado de USIG con la parcela local.
- La respuesta completa del proveedor vive en `response_json`.
- Existe una `source_version` operacional de USIG (`rest`) para satisfacer la FK obligatoria.

### Actividades y normativa

- `activities` + `activity_aliases`.
- `activity_use_rules` contiene el motor determinístico del Cuadro 3.3.
- No se almacenan columnas urbanísticas que el MVP no utiliza.

### Trámites

- `activity_procedures` es el vínculo actividad-procedimiento.
- `procedure_rules` apunta a ese vínculo y evita relaciones ambiguas con actividad/procedimiento por separado.
- Requisitos, documentos y pasos conservan `source_version_id` y, cuando existe, `source_document_chunk_id`.

### RAG

- `documents` referencia `source_resources`.
- `document_chunks` no tiene `metadata` JSON redundante.
- La búsqueda lexical usa `to_tsvector('spanish', content)` directamente.
- Embeddings usan `halfvec(1024)` y HNSW parcial sobre filas con embedding.

### Consultas y evidencia

`query_runs` registra los datos de entrada relevantes para reproducir una evaluación y `query_evidence` referencia directamente reglas, chunks y versiones de fuente.

## Orden de carga recomendado

```text
schema
  ↓
parcelas
  ↓
Código Urbanístico
  ↓
RUS
  ↓
Cuadro 3.3
  ↓
procedimientos/documentos
  ↓
embeddings
  ↓
queries
```

El script de Código Urbanístico exige que la parcela/SMP exista previamente y no reemplaza su geometría.
