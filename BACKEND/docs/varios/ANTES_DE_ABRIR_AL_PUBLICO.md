# Checklist antes de abrir SGI al público general

Estado al 13/10/2026: **no publicar para uso público general todavía**. La URL de Render Free se considera entorno de staging de equipo/demo.

## P0 — obligatorio antes de una demo compartida

- [ ] Aplicar migraciones incrementales pendientes tras backup/validación de staging.
- [ ] `scripts/check_db.py` pasa contra la DB usada por el backend.
- [ ] `scripts/smoke_territory.py` pasa con `status=resolved`, `trace.persistence_status=stored`, fuente de evidencia y respuesta guardada completa.
- [ ] `ALLOWED_HOSTS` está configurado con el hostname real de la API y `CORS_ORIGINS` solo incluye los orígenes reales autorizados.
- [ ] `RAG_ENABLED=false` hasta configurar modelo remoto y validar sus límites; ningún servicio depende del Ollama local.
- [ ] `DOCS_ENABLED=false` en staging compartido si no se necesita Swagger; contrato frontend disponible como archivo versionado.
- [ ] No hay `.env`, claves ni URL con password en Git, registros, documentación o bundle del navegador.
- [ ] La pantalla no presenta actividad provisional como definitiva ni compatibilidad como aprobación legal.
- [ ] Fuentes, versiones, warnings y estados parciales son visibles y consistentes.
- [ ] El equipo entiende que Render Free se duerme por inactividad, tiene filesystem efímero y no es producción.

## P1 — obligatorio antes de acceso público más amplio

- [ ] Implementar rate limiting efectivo. El actual `429` está contemplado en el manejo de errores, pero en esta versión no se ha incorporado un limitador distribuido. El limitador debe funcionar detrás del proxy de Render sin confiar ciegamente en headers IP aportados por el usuario.
- [ ] Establecer límites de tamaño de request en el servidor/proxy y tests de abuso de body grande, JSON inválido y entradas largas.
- [ ] Revisar la superficie de endpoints heredados, especialmente `/api/v1/queries`; deshabilitar rutas que no necesite el MVP o exigir controles adicionales antes de habilitar IA.
- [ ] Definir si las consultas almacenadas contienen datos personales; limitar lo que se persiste, establecer una política de retención/eliminación y documentarla.
- [ ] Determinar necesidad de autenticación/cuotas y proteger futuros historiales de usuario. Supabase `service_role` nunca va al cliente.
- [ ] Configurar monitoreo de errores, alertas de disponibilidad y una forma de consultar logs usando `request_id` sin registrar preguntas/direcciones completas en logs ordinarios.
- [ ] Ejecutar pruebas de concurrencia moderada, timeout, caída de USIG, caída de DB y cold start.
- [ ] Confirmar licencias/atribución, permisos de acceso y estabilidad de cada fuente externa/cartográfica. No extraer ni depender de endpoints privados no documentados de Ciudad 3D.
- [ ] Establecer procedimiento de actualización de datasets y normativa: fuente, fecha de corte, responsables, validación y rollback.
- [ ] Revisión de seguridad del despliegue y dependencias; escaneo de vulnerabilidades y actualización de librerías.
- [ ] Revisar CORS, TrustedHost, cabeceras de seguridad, secretos, permisos mínimos de DB y conexiones SSL en Supabase.
- [ ] Ejecutar pruebas end-to-end y de regresión contra fuentes oficiales con un conjunto de entradas esperadas.

## P2 — antes de calificar el MVP como completo según TECBA

- [ ] Integrar y relacionar efectivamente al menos tres fuentes relevantes; mantener una matriz que indique qué campo/regla aporta cada fuente.
- [ ] Completar el mapa con ubicación y al menos una capa o información territorial visualizada sobre el mapa, con atribución verificable.
- [ ] Implementar la experiencia de consulta en lenguaje natural mediante IA y preguntas de profundización previstas para semanas 5–6 en adelante.
- [ ] Restringir la IA a contexto recuperado de fuentes, probar alucinaciones/consultas fuera de alcance y mostrar fuentes de respaldo.
- [ ] Validar requisitos/trámites y el camino feliz de punta a punta, sin errores críticos.
- [ ] Confirmar el comportamiento para datos incompletos, reglas con fechas de corte o advertencias contradictorias.
- [ ] Decidir si se mantiene el mapa básico o se añade capa IDECABA/contorno catastral; RUS queda fuera del alcance actual por decisión del equipo.
- [ ] Probar una release candidate completa y documentar limitaciones conocidas.

## Criterio de apertura

No abrir al público general hasta cerrar los P1 y los requisitos mínimos del MVP que sean exigibles en la evaluación final. Un endpoint sano, el SSL y CORS no sustituyen rate limiting, política de retención, validación de contenido, trazabilidad comprobada ni una prueba end-to-end.
