# Seguridad — backend 0.1.0

## Estado actual

El MVP no implementa autenticación/autorización todavía. Esto es aceptable para desarrollo local o una demo controlada, pero es **bloqueante antes de exponer la API públicamente**.

La integración futura recomendada es un proveedor institucional OIDC/OAuth (por ejemplo miBA, si el equipo obtiene acceso oficial), usando tokens Bearer y validación de issuer, audience, expiración y firmas. No conviene introducir un sistema casero de usuarios/contraseñas como solución intermedia.

## Medidas ya incorporadas

- Validación y límites de longitud en requests.
- `X-Request-ID` validado como UUID y devuelto en la respuesta.
- Headers de seguridad básicos (`nosniff`, `DENY`, `Referrer-Policy`, `Permissions-Policy`).
- CORS explícito; credenciales de navegador deshabilitadas por defecto.
- `TrustedHostMiddleware` configurable mediante `ALLOWED_HOSTS`.
- Compresión GZip para respuestas suficientemente grandes.
- Backpressure por proceso para consultas concurrentes.
- Semáforos independientes para USIG y Ollama.
- Retries limitados para errores transitorios.
- Ollama no debe publicarse directamente a Internet.
- `.env` excluido del repositorio.
- La API no devuelve mensajes internos de fallos de infraestructura.
- El RAG trata documentos recuperados como datos, no como instrucciones.
- Evidencia y versiones de fuentes se registran en `query_evidence` / `query_runs`.

## Antes de producción pública

1. Integrar OIDC/OAuth institucional.
2. Aplicar autorización por rol/ámbito si aparecen endpoints administrativos.
3. Añadir rate limiting distribuido si hay múltiples réplicas; un semáforo local no reemplaza ese control.
4. Deshabilitar Swagger/ReDoc (`DOCS_ENABLED=false`) salvo que exista una necesidad concreta.
5. Configurar `ALLOWED_HOSTS` con los dominios reales.
6. Usar TLS extremo a extremo o el mecanismo gestionado por la plataforma de despliegue.
7. Configurar backups/PITR de Cloud SQL y probar restauración.
8. Definir políticas de retención para `query_runs`, `query_evidence` y la caché USIG.
9. Revisar qué datos de consulta deben persistirse según la política institucional de privacidad.
10. Ejecutar auditoría de dependencias (`pip-audit`) en CI y usar un lockfile antes del despliegue.

## No hacer

No almacenar contraseñas en el backend de este MVP, no exponer Ollama, no habilitar logs de SQL completos en producción, no registrar cuerpos de consultas por defecto y no confiar en el texto generado por el LLM como fuente de verdad.
