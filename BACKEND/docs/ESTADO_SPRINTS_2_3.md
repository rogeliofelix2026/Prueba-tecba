# Estado del backend y prioridades — semana 2/3

Fecha de corte de esta revisión: 13/10/2026. Versión empaquetada: 0.3.5 (staging). El estado de los datos remotos no puede certificarse desde este paquete; se marcan como pendientes las comprobaciones que necesitan Supabase/Render reales.

## 1. Criterio tomado del documento TECBA

El documento del producto define un MVP concreto: inicio de una nueva actividad comercial, consulta sobre qué hacer y dónde, tres o más fuentes relacionadas, información territorial, mapa interactivo, trámites/requisitos/documentos/pasos y trazabilidad. En semanas 2–3 el entregable es la primera experiencia territorial integrada con consulta de actividad y ubicación, mapa básico, primera respuesta estructurada y relación entre fuentes. La IA y preguntas de seguimiento se trabajan en semanas 5–6 y posteriores.

En consecuencia, para semana 2/3 no bloquear la integración por un agente ReAct/RAG completo, pero tampoco interpretar el éxito del backend determinista como cumplimiento final de todo el MVP. El objetivo de ahora es un vertical slice estable, fácil de consumir y de verificar.

## 2. Qué hay implementado

| Capacidad | Estado del código | Evidencia/limitación |
|---|---|---|
| API FastAPI con endpoints versionados | Implementado | `/api/v1/health`, `/ready`, `/activities` y `/territory`. |
| Geocodificación y normalización USIG | Implementado | La prueba de Corrientes 2880 devolvió coordenadas y `from_cache=true`. Falta prueba remota repetible desde Render. |
| Actividad → código del catálogo | Implementado | Alias “Cafetería” a 1.5 provisional; exige confirmación, no es una equivalencia normativa definitiva. |
| SMP → parcela/catastro | Implementado | Prueba devolvió parcela y SMP exacto. Verificar casos ambiguos/no resueltos. |
| Barrio, comuna y Código Urbanístico | Implementado en la prueba | Balvanera, Comuna 3 y mixtura 4 devueltos para el ejemplo. No generalizar al resto de direcciones sin tests. |
| Clasificación Anexo II y procedimientos | Implementado con cobertura dependiente de los mapeos/seed | Debe probarse el camino feliz, datos ausentes y mapeos en revisión. |
| Respuesta estructurada con fuentes/advertencias | Implementado | La prueba informa 6 versiones de fuentes y advertencias legibles. |
| Mapa con marcador | Posible ahora | El frontend puede usar lat/lon sin polígonos. |
| Endpoint GeoJSON de parcela | Implementado pero capacidad no activa para el ejemplo | `geometry_status=source_not_configured`, `geometry=null`. |
| Geometría en base | Modelo/código de caché disponible | No se verificó una tabla con geometría cargada para la parcela de prueba. |
| Auditoría completa de consulta | Parcial antes de aplicar la migración de reparación | Prueba aportada: `stored_partial`, `QUERY_AUDIT_SCHEMA_LEGACY`. Se añadió migración incremental y manejo de `reference_key`; falta aplicar y verificar contra Supabase real. |
| Usos del Suelo RUS | Fuera del alcance actual por decisión de proyecto | No cargarlo en esta fase ni tratarlo como fuente integrada. |
| IA/RAG | Existe infraestructura heredada/opcional, no activada en staging | `RAG_ENABLED=false`; la IA es requisito del MVP final según TECBA, pero no bloquea la integración determinista de semana 2/3. |
| Rate limiting distribuido | Pendiente | No presentar el entorno staging como servicio público. |
| Autenticación de usuarios | No implementada | No es necesaria para el prototipo compartido si no hay datos privados, pero evaluar antes de ofrecer historiales/cuentas o abrir el servicio al público. |

## 3. Fuente de información: tres o más sin RUS

El mínimo del proyecto es integrar tres fuentes relevantes. El alcance actual puede sustentarse en estas fuentes, siempre que se mantenga el origen de cada bloque y se verifique su vigencia:

1. **USIG** — normalización y geocodificación de dirección, coordenadas y SMP.
2. **Catastro/Parcelas CABA** — identidad de parcela, SMP y partida.
3. **Código Urbanístico / Cuadro de Usos 3.3** — mixturas, afectaciones y reglas urbanísticas.
4. **Resolución 96/AGC/25, Anexo II** — correspondencia de actividad/código con tipo de trámite.
5. **Página/documentación oficial de habilitación de actividad económica GCBA/AGC** — requisitos, pasos y variantes del procedimiento.

Aunque las cinco figuren en `sources`, no considerar automáticamente que la información esté completa: `source_version_id`, estado, versión y contenidos cargados deben comprobarse. El RUS queda expresamente postergado; el documento TECBA acepta definir fuentes según su utilidad/disponibilidad técnica y no obliga a incluir un dataset particular.

## 4. Trabajo priorizado para semanas 2–3

### P0 — imprescindible antes de dar el vertical slice por integrado

- [ ] Aplicar las migraciones pendientes sobre el proyecto Supabase correcto; no ejecutar el baseline destructivo sobre tablas con datos.
- [ ] Revisar la migración nueva `20261013150000_repair_query_audit_schema.sql` y ejecutar `supabase migration list --linked` antes de `supabase db push`.
- [ ] Ejecutar `python scripts/check_db.py` contra la misma `DATABASE_URL` del backend desplegado.
- [ ] Ejecutar `python scripts/smoke_territory.py --base-url <API_URL>` y obtener `PASS`, `status=resolved` y `trace.persistence_status=stored`. Esto todavía no se probó contra la base remota desde este entorno.
- [ ] Probar con QA al menos: dirección conocida, dirección no encontrada, rubro ambiguo/provisional, ausencia de parcela, datos urbanísticos ausentes y proveedor USIG fuera de servicio.
- [ ] Conectar Frontend con `docs/API_SIMPLE_v1.md`, consumir una sola vez el endpoint principal y mostrar carga, error, confirmación de actividad y resultado parcial.
- [ ] Mostrar un marcador de mapa basado en coordenadas. El mapa debe seguir siendo utilizable si el polígono no está disponible.
- [ ] Mostrar requisitos, documentos, pasos, fuentes y advertencias sin ocultar condicionales ni el estado provisional del rubro.
- [ ] Revisar y documentar las fuentes efectivamente relacionadas; no contar la inclusión de URL en `sources` como prueba suficiente de integración si el dato no interviene en la respuesta.

### P1 — hacer dentro de semana 3 si no bloquea P0

- [ ] Probar el backend desplegado desde el dominio/origen real de Frontend para validar CORS.
- [ ] Acordar con Frontend el tipo TypeScript completo de la respuesta y estados; evitar `any` y no replicar las reglas normativas en el cliente.
- [ ] Revisar la latencia inicial por cold start de Render Free y planear la demo con una llamada de calentamiento.
- [ ] Elegir si el mapa básico usará Leaflet o MapLibre. Ambos pueden mostrar marcador y capas externas compatibles; no necesitamos una nueva librería para esperar geometría propia.
- [ ] Añadir una liga informativa a Ciudad 3D cuando sea apropiado, sin presentarlo como fuente de GeoJSON consumida por SGI.

### P2 — semana 4 en adelante

- [ ] Consolidar el camino feliz completo y la trazabilidad visual (semana 4 según TECBA).
- [ ] Evaluar una capa WMS/WFS de IDECABA si se verifica que incluye la información parcelaria necesaria y se permite su uso en el mapa del producto.
- [ ] Preparar fuentes procesadas y consultas esperadas para la primera capa de IA en semanas 5–6.
- [ ] Implementar preguntas de seguimiento con el contexto de la consulta inicial.
- [ ] Ampliar manejo de datos incompletos/contradictorios, pruebas end-to-end y control de vigencia de fuentes en semanas 7–10.

## 5. Criterio de aceptación semanal

La semana 2/3 se considera alcanzada cuando Frontend puede enviar la actividad y dirección a la API desplegada, recibir una respuesta estructurada y trazable, renderizar la ubicación, desplegar trámites/requisitos/pasos y tratar correctamente estados parcial/confirmación/error; QA contrasta una muestra con fuentes oficiales. No requiere un polígono propio ni IA conversacional completa en este sprint, pero el plan del MVP final sí contempla mapa territorial relevante e IA respaldada por fuentes.

## 6. Verificaciones de esta entrega del ZIP

- Se actualizaron los archivos de despliegue para Render Free y se separaron dependencias de ingesta del runtime.
- Se agregó documentación de contrato `docs/API_SIMPLE_v1.md`, estado de sprint, mapa/Ciudad 3D, checklist previo a público y despliegue.
- Se agregó una migración incremental de auditoría y se ajustó la evidencia antigua para respetar `reference_key` cuando esa columna exista.
- Se intentó instalar dependencias de prueba para ejecutar la suite, pero este entorno no tiene acceso de red al índice de paquetes (no se pudo instalar `psycopg`/`pgvector`). Por eso la suite completa y el smoke test de Supabase quedan pendientes; no se declaran aprobados.
- No se dispuso de credenciales/URL de tu Supabase para aplicar migraciones ni verificar filas reales.
