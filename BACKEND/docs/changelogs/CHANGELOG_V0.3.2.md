# SGI Backend v0.3.2 — compatibilidad e integridad del flujo

- Entrada principal flexible para `POST /api/v1/territory`: actividad + dirección; superficie, dimensiones, código interno y geometría son opcionales.
- Alias aceptados para formularios: `rubro`/`actividad` y `direccion`/`domicilio`; campos extra de UI y controles opcionales serializados como cadenas vacías no bloquean la resolución.
- Normalización de SMP de ingesta conserva secciones de dos o tres dígitos; la resolución consulta variantes equivalentes manteniendo igualdad indexable por `parcels.smp`.
- Las columnas modernas de auditoría JSON pasan a ser opcionales para el registro básico de consultas; el backend persiste en el esquema legado cuando puede e informa la degradación.
- Un fallo aislado de auditoría no transforma una resolución territorial calculada en HTTP 503.
- `/ready` diferencia el esquema territorial esencial de capacidades opcionales como geometría, usos observados, mapeo de trámites, detalle de procedimientos y auditoría estructurada.
- Se diferencia dirección no encontrada (`404`) de indisponibilidad de proveedor (`502`).
- Se agregan pruebas HTTP aisladas, pruebas de compatibilidad de auditoría y SQL de diagnóstico de solo lectura.
- `requirements-dev.txt` incorpora `httpx2` para el backend actual de `TestClient` en Starlette; el cliente HTTP usado por la aplicación sigue siendo `httpx`.

## Validación realizada en el entorno de trabajo

`pytest -q`: 112 pruebas aprobadas con stubs temporales de importación para las dependencias de PostgreSQL/pgvector ausentes en este contenedor. Esto valida las rutas de lógica y los contratos con repositorios fake, pero no reemplaza el smoke test contra Supabase/PostGIS real.
