# Despliegue de SGI v0.3.5 en Render Free (staging)

## Decisión de hosting

Usar **Render Free** durante los sprints de prueba. Railway tiene un plan Free de USD 0 con crédito mensual limitado (USD 1 según la documentación consultada) y un crédito inicial de prueba sujeto a cuenta/uso; no lo tomo como garantía de coste cero sostenido. Render documenta un plan Free explícito para web services.

Fuentes oficiales revisadas el 13/10/2026:
- Render Free: https://render.com/docs/free
- Railway Free Trial: https://docs.railway.com/pricing/free-trial
- Railway plans: https://docs.railway.com/pricing/plans

### Límites importantes de Render Free

- Se suspende por inactividad luego de 15 minutos y el primer request tras volver puede tardar aproximadamente un minuto.
- El filesystem es efímero; no guardar archivos, cachés ni datos necesarios para persistir en el disco local. SGI debe usar Supabase para datos.
- Se otorgan 750 horas de instancia Free por workspace por mes; se consumen los límites de ancho de banda y build minutes. Si se agota el incluido y no hay medio de pago, Render suspende servicios/builds antes que cobrar cargos adicionales.
- No es un entorno de producción. Para pruebas, avisar al equipo sobre el cold start.
- Render advierte que un volumen inusualmente alto de tráfico saliente (por ejemplo consultas a APIs o bases externas) puede suspender servicios gratuitos. Mantener las pruebas moderadas.

## 1. Precondiciones: proteger la base existente

1. Confirmar que el repositorio tiene la última versión revisada y el historial completo de migraciones.
2. Hacer backup/confirmar punto de restauración de Supabase.
3. En la carpeta `backend`, ejecutar `supabase migration list --linked` y guardar el resultado.
4. No ejecutar `supabase db reset` ni el baseline destructivo `20261008100000_schema_mvp_final.sql` sobre una base con datos.
5. Aplicar migraciones pendientes únicamente después de revisar qué cambios van a afectar la base. Las migraciones del repositorio no se aplican automáticamente al arrancar la API.
6. Ejecutar `python scripts/check_db.py` contra el proyecto Supabase correcto.

## 2. Deploy desde GitHub

1. Subir el backend completo a un repositorio privado o al repositorio del equipo. Incluir Dockerfile, render.yaml, app, scripts, tests, `docs/` y `supabase/migrations/`. No subir `.env`, contraseñas ni datasets grandes.
2. Entrar a https://dashboard.render.com/ y seleccionar **New → Blueprint** para que lea `render.yaml`; o crear **New → Web Service**, conectar el repositorio y elegir Docker.
3. Si el ZIP es el repositorio raíz, dejar `Root Directory` vacío. Si está dentro de un monorepo, indicar esa carpeta.
4. Confirmar que el servicio usa **Free** (el YAML declara `plan: free`). No crear Render Postgres: la base ya está en Supabase.
5. Render construye la imagen desde `Dockerfile`. El comando final ya utiliza `0.0.0.0:$PORT`.
6. Completar las variables de entorno indicadas abajo y lanzar el deploy.

## 3. Variables en Render → Environment

`render.yaml` configura valores no secretos y pide completar las variables con `sync: false`:

- `DATABASE_URL`: URL PostgreSQL server-side copiada desde Supabase → Connect. Preferir Session Pooler si el entorno no tiene conectividad IPv6 directa. Mantener TLS como indique Supabase. No utilizar claves `anon`/`service_role` como si fueran URLs PostgreSQL.
- `ALLOWED_HOSTS`: el Blueprint permite inicialmente `*.onrender.com` para poder crear el servicio; cambiarlo al hostname exacto asignado por Render, sin `https://` ni rutas, una vez creado el dominio.
- `CORS_ORIGINS`: el Blueprint permite inicialmente `http://localhost:5173,http://localhost:3000` para desarrollo local. Agregar el origen exacto del Frontend desplegado, con protocolo y sin rutas; quitar los orígenes que no correspondan al equipo. No usar `*`.

Variables definidas en el Blueprint: `APP_ENV=production`, `APP_VERSION=0.3.5`, `RAG_ENABLED=false`, `DOCS_ENABLED=false`, `DB_MIN_SIZE=1`, `DB_MAX_SIZE=5`, `DB_TIMEOUT_SECONDS=5`, `USIG_TIMEOUT_SECONDS=10`, `USIG_MAX_RETRIES=2`. No activar RAG/Ollama: no es necesario para el flujo determinista y no hay un modelo remoto configurado para staging.

Después del primer deploy, obtener el hostname real de Settings → Domains, actualizar `ALLOWED_HOSTS` y guardar. El origen Frontend exacto se agrega a `CORS_ORIGINS`; Render suele redeplegar al cambiar variables.

## 4. Validación de despliegue

En el navegador o Postman, reemplazar `<API_URL>` por el dominio HTTPS real:

1. `GET <API_URL>/api/v1/health` → HTTP 200.
2. `GET <API_URL>/api/v1/ready` → inspeccionar `status`, `degraded` y `degraded_capabilities`. Si devuelve 503, no declarar listo: revisar logs, `DATABASE_URL` y esquema core. Un 200 con `degraded=true` significa que faltan capacidades opcionales y hay que leer la lista.
3. `GET <API_URL>/api/v1/activities?search=gastronom%C3%ADa` → devolver candidatos y fuentes.
4. `POST <API_URL>/api/v1/territory` con JSON:

```json
{
  "activity": "Alimentación en general y gastronomía",
  "activity_code": "1.5",
  "address": "Corrientes 2500",
  "surface_m2": 80,
  "include_geometry": false
}
```

5. Verificar la respuesta funcional, `request_id`, `warnings`, `sources`, `trace.persistence_status` y el `status` de negocio. No basta HTTP 200: se espera `trace.persistence_status=stored` para aceptar la persistencia completa.
6. Cuando el entorno desplegado y local usen la misma base segura de staging, ejecutar `python scripts/smoke_territory.py --base-url <API_URL>`. La prueba se conecta a PostgreSQL con `DATABASE_URL` y revisa el registro y las evidencias. No establecer que pasó si no se pudo conectar a la DB y corroborar los datos.
7. Confirmar CORS llamando la API desde el origen real del Frontend. Un curl directo no prueba CORS.

## 5. Esquema/migraciones de auditoría

Una ejecución anterior dio `trace.persistence_status=stored_partial` y `QUERY_AUDIT_SCHEMA_LEGACY`. Esta versión incluye una migración incremental de reparación de la auditoría (`20261013150000_repair_query_audit_schema.sql`) y compatibilidad con esquemas antiguos en `reference_key`.

Antes de aplicar migraciones, revisar `supabase migration list --linked` y usar una base de staging/backup. Luego aplicar de forma ordenada las migraciones pendientes con la CLI de Supabase instalada y vinculada al proyecto correcto (`supabase db push`). Después ejecutar `python scripts/check_db.py` y el smoke test. No se pudo verificar el Supabase remoto desde este paquete, por lo que esa verificación sigue pendiente de quien tenga las credenciales.

## 6. Diagnóstico rápido

- **Build falla al instalar dependencias GIS:** el runtime ya no instala GeoPandas/Pyogrio; las ingestas offline usan `requirements-ingestion.txt`. Revisar imports runtime antes de volver a agregarlos.
- **La API no arranca:** revisar logs y `DATABASE_URL`; el servicio abre pool en el startup.
- **`/ready` devuelve 503:** comprobar migraciones, tablas `parcels`, `barrios`, `comunas`, `urban_parcel_rules` y conectividad de Supabase.
- **CORS en navegador:** ajustar `CORS_ORIGINS` al origen completo del Frontend; reiniciar/redeploy.
- **Primera llamada lenta:** es esperable tras el sleep del servicio Free.
- **`stored_partial`:** comprobar que aplicaste la migración de reparación y que `query_evidence` acepta los campos de referencia. Revisar el warning devuelto y logs; no ocultar el estado parcial.
- **No hay polígono:** esperado mientras `parcel_geometries` no contenga geometrías cargadas. El marcador usa coordenadas; no equivale al contorno catastral.

## 7. Railway como alternativa futura

No es la alternativa primaria si el requisito es coste cero sostenido: la documentación actual indica $1 de créditos por mes en Free y un crédito único de $5 en la prueba de nuevos usuarios durante 30 días. El saldo y el uso dependen de la cuenta. Si se cambia en el futuro, puede usarse el mismo Dockerfile y `railway.toml`, pero primero verificar créditos y controles de gasto de la cuenta.
