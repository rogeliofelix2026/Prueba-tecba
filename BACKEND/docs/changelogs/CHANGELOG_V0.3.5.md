# Changelog v0.3.5 — staging y contrato frontend

## Cambios incluidos

- Añadido `docs/API_SIMPLE_v1.md` con el contrato recomendado para integrar React/Next.js.
- Añadida la guía de despliegue prioritaria en Render Free (`render.yaml`) con `RAG_ENABLED=false`, health check y valores iniciales de pool/timeouts. Railway queda documentado como opción alternativa con crédito gratuito limitado.
- Separadas las dependencias GIS/PDF offline de `requirements.txt`; Docker instala el runtime mínimo. `requirements-ingestion.txt` incluye los módulos GIS y PDF para ingestas.
- Añadida migración idempotente e incremental de auditoría `20261013150000_repair_query_audit_schema.sql`. Añade `request_payload`, `response_json`, `execution_mode` y FKs de evidencia ausentes; no elimina datos ni tablas.
- Ajustada la escritura de evidencia para completar `reference_key` en esquemas antiguos que la contienen.
- Documentado estado por semana 2/3 del cronograma TECBA, mapa Ciudad 3D/IDECABA y checklist pre-público.
- El runtime de staging desactiva RAG y Swagger por defecto. El endpoint determinista continúa siendo el camino principal.

## Pendientes de verificación externa

- Aplicar y comprobar migraciones contra Supabase real, respetando el historial previo.
- Ejecutar `scripts/check_db.py`, la suite `pytest` completa y `scripts/smoke_territory.py` con dependencias instaladas y `DATABASE_URL` de staging.
- Configurar dominio real y origen del Frontend en Render, y validar CORS desde el navegador.
- Validar que al menos tres fuentes contribuyen efectivamente a la respuesta y registrar una prueba de referencia con QA.
- Confirmar si IDECABA tiene una capa WMS/WFS de parcelas consumible; no se implementa ninguna URL de capa sin comprobar el catálogo.

## Nota de versión

La versión 0.3.5 es un paquete de preparación para staging e integración, no una certificación de producción. La prueba de usuario previa mostraba `trace.persistence_status=stored_partial`; la migración y los cambios se incluyen para resolverlo, pero se requiere ejecutar la migración y repetir el smoke test en el entorno remoto para confirmar el resultado.
