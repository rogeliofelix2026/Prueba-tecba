-- Seed idempotente de trámite piloto. Información publicada en páginas oficiales consultadas el 2026-10-13; revisar vigencia antes de cada release.
-- Las páginas informativas no se tratan como normas con vigencia legal propia.
BEGIN;
INSERT INTO sources(code,name,publisher,canonical_url) VALUES
('gcba_habilitacion_actividad','Habilitación de actividad económica','Gobierno de la Ciudad Autónoma de Buenos Aires','https://buenosaires.gob.ar/tramites/habilitacion-de-actividad-economica'),
('agc_consulta_apertura_local','¿Querés abrir tu local comercial?','Agencia Gubernamental de Control','https://atencionvirtual.agcontrol.gob.ar/users/service/description?service=1'),
('gcba_habilitacion_expres','Habilitación de actividad económica exprés','Gobierno de la Ciudad Autónoma de Buenos Aires','https://buenosaires.gob.ar/tramites/habilitacion-de-actividad-economica-expres'),
('gcba_autorizacion_actividades_pdf','Autorización de Actividades Económicas (PDF)','Gobierno de la Ciudad Autónoma de Buenos Aires','https://static.buenosaires.gob.ar/sites/default/files/2025-04/Autorizaci%C3%B3n%20de%20Actividades%20Econ%C3%B3micas..pdf'),
('agc_estado_tramite','Consulta de autorización ya iniciada','Agencia Gubernamental de Control','https://atencionvirtual.agcontrol.gob.ar/users/service/description?service=2'),
('agc_portal_habilitaciones','Portal de habilitaciones','Agencia Gubernamental de Control','https://dghpsh.agcontrol.gob.ar/Dghp.Habilitaciones.PublicWebSite/'),
('gcba_historico_habilitacion','Página histórica de habilitación','Gobierno de la Ciudad Autónoma de Buenos Aires','https://buenosaires.gob.ar/gcaba_historico/habilitacion'),
('resolucion_96_agc_25_anexo_ii','Resolución 96/AGC/25 — Anexo II: Usos de Actividad Económica y Tipos de Trámites','Gobierno de la Ciudad Autónoma de Buenos Aires — AGC','https://www.boletinoficial.buenosaires.gob.ar/normativaba/norma/781370')
ON CONFLICT(code) DO UPDATE SET name=EXCLUDED.name,publisher=EXCLUDED.publisher,canonical_url=EXCLUDED.canonical_url;

-- Bajar versiones activas anteriores antes de activar el snapshot de esta fuente.
UPDATE source_versions sv SET status='superseded'
FROM sources s
WHERE s.id=sv.source_id
  AND s.code IN ('gcba_habilitacion_actividad','agc_consulta_apertura_local','gcba_habilitacion_expres','gcba_autorizacion_actividades_pdf','agc_estado_tramite','agc_portal_habilitaciones','gcba_historico_habilitacion')
  AND sv.status='active' AND sv.version_label <> 'snapshot-2026-10-13';
UPDATE source_versions sv SET status='superseded'
FROM sources s
WHERE s.id=sv.source_id AND s.code='resolucion_96_agc_25_anexo_ii'
  AND sv.status='active' AND sv.version_label <> '2025-03-14';

INSERT INTO source_versions(source_id,version_label,status)
SELECT id,'snapshot-2026-10-13',CASE WHEN code='gcba_historico_habilitacion' THEN 'ingested' ELSE 'active' END FROM sources
WHERE code IN ('gcba_habilitacion_actividad','agc_consulta_apertura_local','gcba_habilitacion_expres','gcba_autorizacion_actividades_pdf','agc_estado_tramite','agc_portal_habilitaciones','gcba_historico_habilitacion')
ON CONFLICT(source_id,version_label) DO UPDATE SET status=EXCLUDED.status;

INSERT INTO source_versions(source_id,version_label,published_at,effective_from,status)
SELECT id,'2025-03-14','2025-03-14','2025-03-14','active'
FROM sources WHERE code='resolucion_96_agc_25_anexo_ii'
ON CONFLICT(source_id,version_label) DO UPDATE SET published_at=EXCLUDED.published_at,effective_from=EXCLUDED.effective_from,status='active';

INSERT INTO source_resources(source_version_id,resource_type,uri,mime_type,retrieved_at)
SELECT sv.id,'normative_page',s.canonical_url,'text/html',now()
FROM sources s JOIN source_versions sv ON sv.source_id=s.id AND sv.version_label='2025-03-14'
WHERE s.code='resolucion_96_agc_25_anexo_ii'
ON CONFLICT(source_version_id,uri) DO UPDATE SET retrieved_at=EXCLUDED.retrieved_at;

-- Copia del PDF de la Resolución y anexos alojada por CPAU; se conserva aparte del registro oficial.
INSERT INTO source_resources(source_version_id,resource_type,uri,mime_type,retrieved_at)
SELECT sv.id,'normative_annex_pdf',
       'https://static.cpau.org/.newsite/servicios/biblioteca/boletin_oficial/2025/Resoluci%C3%B3n_96-AGC-2025_Tramitacion_Actividades_Economicas_v2025.pdf',
       'application/pdf',now()
FROM sources s JOIN source_versions sv ON sv.source_id=s.id AND sv.version_label='2025-03-14'
WHERE s.code='resolucion_96_agc_25_anexo_ii'
ON CONFLICT(source_version_id,uri) DO UPDATE SET retrieved_at=EXCLUDED.retrieved_at;

INSERT INTO source_resources(source_version_id,resource_type,uri,mime_type,retrieved_at)
SELECT sv.id,CASE WHEN s.code='gcba_autorizacion_actividades_pdf' THEN 'pdf' ELSE 'web_page' END,s.canonical_url,
       CASE WHEN s.code='gcba_autorizacion_actividades_pdf' THEN 'application/pdf' ELSE 'text/html' END,now()
FROM sources s JOIN source_versions sv ON sv.source_id=s.id AND sv.version_label='snapshot-2026-10-13'
WHERE s.code IN ('gcba_habilitacion_actividad','agc_consulta_apertura_local','gcba_habilitacion_expres','gcba_autorizacion_actividades_pdf','agc_estado_tramite','agc_portal_habilitaciones','gcba_historico_habilitacion')
ON CONFLICT(source_version_id,uri) DO UPDATE SET retrieved_at=EXCLUDED.retrieved_at;

-- Registrar cada recurso en el catálogo documental, sin copiar el archivo binario a PostgreSQL.
INSERT INTO documents(source_resource_id,document_key,title,mime_type,document_type,authority_level)
SELECT sr.id,'source-page',s.name,sr.mime_type,
       CASE WHEN s.code='gcba_autorizacion_actividades_pdf' THEN 'annex'
            WHEN s.code='gcba_historico_habilitacion' THEN 'other'
            ELSE 'procedure' END,
       CASE WHEN s.code='gcba_historico_habilitacion' THEN 'contextual'
            WHEN s.code IN ('gcba_habilitacion_actividad','gcba_habilitacion_expres','agc_consulta_apertura_local') THEN 'official_procedure'
            ELSE 'official_guidance' END
FROM source_resources sr JOIN source_versions sv ON sv.id=sr.source_version_id
JOIN sources s ON s.id=sv.source_id
WHERE sv.version_label='snapshot-2026-10-13'
  AND s.code IN ('gcba_habilitacion_actividad','agc_consulta_apertura_local','gcba_habilitacion_expres','gcba_autorizacion_actividades_pdf','agc_estado_tramite','agc_portal_habilitaciones','gcba_historico_habilitacion')
ON CONFLICT(source_resource_id,document_key) DO UPDATE SET title=EXCLUDED.title,mime_type=EXCLUDED.mime_type,document_type=EXCLUDED.document_type,authority_level=EXCLUDED.authority_level;

INSERT INTO documents(source_resource_id,document_key,title,mime_type,document_type,authority_level)
SELECT sr.id,'norma-y-anexos',s.name,sr.mime_type,'normative','primary_normative'
FROM sources s JOIN source_versions sv ON sv.source_id=s.id AND sv.version_label='2025-03-14'
JOIN source_resources sr ON sr.source_version_id=sv.id
WHERE s.code='resolucion_96_agc_25_anexo_ii' AND sr.resource_type='normative_page'
ON CONFLICT(source_resource_id,document_key) DO UPDATE SET title=EXCLUDED.title,mime_type=EXCLUDED.mime_type,document_type=EXCLUDED.document_type,authority_level=EXCLUDED.authority_level;

INSERT INTO documents(source_resource_id,document_key,title,mime_type,document_type,authority_level)
SELECT sr.id,'resolucion-pdf-mirror','Resolución 96/AGC/25 y anexos (copia PDF de consulta)',sr.mime_type,'normative','primary_normative'
FROM sources s JOIN source_versions sv ON sv.source_id=s.id AND sv.version_label='2025-03-14'
JOIN source_resources sr ON sr.source_version_id=sv.id
WHERE s.code='resolucion_96_agc_25_anexo_ii' AND sr.resource_type='normative_annex_pdf'
ON CONFLICT(source_resource_id,document_key) DO UPDATE SET title=EXCLUDED.title,mime_type=EXCLUDED.mime_type,document_type=EXCLUDED.document_type,authority_level=EXCLUDED.authority_level;

INSERT INTO procedures(code,name,description,source_version_id)
SELECT 'habilitacion_actividad_economica','Autorización de actividad económica (trámite general)',
       'Solicitud online ante GCBA/AGC. Requiere evaluación técnica profesional; la documentación puede variar por actividad y condiciones del local.',sv.id
FROM sources s JOIN source_versions sv ON sv.source_id=s.id AND sv.version_label='snapshot-2026-10-13'
WHERE s.code='gcba_habilitacion_actividad'
ON CONFLICT(code) DO UPDATE SET name=EXCLUDED.name,description=EXCLUDED.description,source_version_id=EXCLUDED.source_version_id;

INSERT INTO procedures(code,name,description,source_version_id)
SELECT 'habilitacion_actividad_economica_expres','Habilitación de actividad económica exprés',
       'Vía simplificada con superficie máxima de 200 m² y requisitos de ubicación, accesibilidad y actividad. Si falla alguna condición, evaluar otra vía.',sv.id
FROM sources s JOIN source_versions sv ON sv.source_id=s.id AND sv.version_label='snapshot-2026-10-13'
WHERE s.code='gcba_habilitacion_expres'
ON CONFLICT(code) DO UPDATE SET name=EXCLUDED.name,description=EXCLUDED.description,source_version_id=EXCLUDED.source_version_id;

-- Modalidades generales publicadas en la página de GCBA. Los códigos de variante son
-- canónicos; el mapeo Anexo II mantiene DDRR_SP/DDRR_CP y el repositorio hace el crosswalk explícito.
WITH p AS (SELECT id FROM procedures WHERE code='habilitacion_actividad_economica'),
sv AS (SELECT id FROM source_versions WHERE version_label='snapshot-2026-10-13' AND source_id=(SELECT id FROM sources WHERE code='gcba_habilitacion_actividad'))
INSERT INTO procedure_variants(procedure_id,code,name,description,conditions,immediate_start_allowed,prior_inspection_required,validity_years,source_version_id)
SELECT p.id,x.code,x.name,x.description,x.conditions,x.immediate_start_allowed,x.prior_inspection_required,x.validity_years,sv.id
FROM p CROSS JOIN sv CROSS JOIN (VALUES
('DDRR_SIN_PLANO','Declaración responsable sin planos','La página oficial indica esta modalidad hasta 500 m²; la aprobación final queda sujeta a revisión técnica.', '{"surface_max_m2":500,"plans_required":false,"final_review_required":true}'::jsonb, true, false, NULL::smallint),
('DDRR_CON_PLANO','Declaración responsable con plano','La página oficial indica inicio inmediato con presentación de plano, sujeta a revisión técnica salvo casos con inspección previa por norma específica.', '{"plans_required":true,"final_review_required":true,"exceptions_may_require_prior_inspection":true}'::jsonb, true, false, NULL::smallint),
('LICENCIA','Licencia de actividad económica','No iniciar actividad hasta recibir notificación oficial de aprobación; requiere inspección previa. La página informa una validez de 15 años.', '{"start_requires_official_approval":true,"prior_inspection_required":true}'::jsonb, false, true, 15::smallint)
) AS x(code,name,description,conditions,immediate_start_allowed,prior_inspection_required,validity_years)
ON CONFLICT(procedure_id,code) DO UPDATE SET name=EXCLUDED.name,description=EXCLUDED.description,conditions=EXCLUDED.conditions,immediate_start_allowed=EXCLUDED.immediate_start_allowed,prior_inspection_required=EXCLUDED.prior_inspection_required,validity_years=EXCLUDED.validity_years,source_version_id=EXCLUDED.source_version_id;

-- La vía exprés se asocia a DDRR_E. Los campos de inicio/inspección quedan NULL
-- porque la página consultada describe condiciones y derivación, pero no deben
-- inferirse permisos no expresados literalmente.
WITH p AS (SELECT id FROM procedures WHERE code='habilitacion_actividad_economica_expres'),
sv AS (SELECT id FROM source_versions WHERE version_label='snapshot-2026-10-13' AND source_id=(SELECT id FROM sources WHERE code='gcba_habilitacion_expres'))
INSERT INTO procedure_variants(procedure_id,code,name,description,conditions,immediate_start_allowed,prior_inspection_required,validity_years,source_version_id)
SELECT p.id,'DDRR_E','Declaración Responsable Exprés','Vía simplificada sujeta a superficie, uso, ubicación y demás condiciones oficiales.',
       '{"surface_max_m2":200,"surface_operator":"lte","eligibility_requires_all_conditions":true}'::jsonb,
       NULL,NULL,NULL,sv.id FROM p CROSS JOIN sv
ON CONFLICT(procedure_id,code) DO UPDATE SET name=EXCLUDED.name,description=EXCLUDED.description,conditions=EXCLUDED.conditions,source_version_id=EXCLUDED.source_version_id,active=TRUE;

WITH p AS (SELECT id FROM procedures WHERE code='habilitacion_actividad_economica'),
sv AS (SELECT id FROM source_versions WHERE version_label='snapshot-2026-10-13' AND source_id=(SELECT id FROM sources WHERE code='gcba_habilitacion_actividad'))
INSERT INTO procedure_requirements(procedure_id,requirement_code,title,description,conditional,conditions,source_version_id)
SELECT p.id,x.code,x.title,x.description,x.conditional,x.conditions,sv.id FROM p CROSS JOIN sv CROSS JOIN (VALUES
('MIBA_N3','Usuario miBA nivel 3','Contar con usuario y clave miBA nivel 3.',false,'{}'::jsonb),
('FORM_UNIDAD_USO','Formulario de conformación de la unidad de uso','Declaración jurada que informa la actividad comercial.',false,'{}'::jsonb),
('ANEXO_TECNICO','Anexo Técnico profesional','Firmado por profesional responsable; incluye encomienda, datos profesionales, información de unidad de uso, mixtura o área especial, croquis y declaración jurada de verificación.',false,'{}'::jsonb),
('CAA','Certificado de Aptitud Ambiental','Solicitar el certificado correspondiente ante la autoridad ambiental.',false,'{}'::jsonb),
('CERT_SOBRECARGA','Certificado de sobrecarga','Se presenta cuando corresponda.',true,'{"trigger":"cuando_corresponda"}'::jsonb),
('PLANO_USO','Plano de Uso de Actividad Económica','Presentación condicional.',true,'{"trigger":"cuando_corresponda"}'::jsonb),
('AUTORIZACION_EMPLAZAMIENTO','Autorización de Emplazamiento','Presentación condicional.',true,'{"trigger":"cuando_corresponda"}'::jsonb),
('DOC_RUBRO_ESPECIFICO','Documentación específica del rubro','La normativa aplicable a la actividad puede exigir documentación adicional.',true,'{"trigger":"actividad_especifica"}'::jsonb)
) AS x(code,title,description,conditional,conditions)
ON CONFLICT (procedure_id, requirement_code) WHERE requirement_code IS NOT NULL DO UPDATE SET title=EXCLUDED.title, description=EXCLUDED.description, conditional=EXCLUDED.conditional, conditions=EXCLUDED.conditions, source_version_id=EXCLUDED.source_version_id;

WITH p AS (SELECT id FROM procedures WHERE code='habilitacion_actividad_economica'),
sv AS (SELECT id FROM source_versions WHERE version_label='snapshot-2026-10-13' AND source_id=(SELECT id FROM sources WHERE code='gcba_habilitacion_actividad'))
INSERT INTO procedure_documents(procedure_id,document_code,title,description,conditional,conditions,source_version_id)
SELECT p.id,x.code,x.title,x.description,x.conditional,x.conditions,sv.id FROM p CROSS JOIN sv CROSS JOIN (VALUES
('FORM_UNIDAD_USO','Formulario de conformación de la unidad de uso','Declaración jurada de la actividad.',false,'{}'::jsonb),
('ANEXO_TECNICO','Anexo Técnico firmado','Incluye encomienda profesional, croquis, información de unidad de uso y verificación.',false,'{}'::jsonb),
('CERT_SOBRECARGA','Certificado de sobrecarga','Solo cuando corresponda.',true,'{"trigger":"cuando_corresponda"}'::jsonb),
('PLANO_USO','Plano de Uso de Actividad Económica','Solo cuando corresponda.',true,'{"trigger":"cuando_corresponda"}'::jsonb),
('AUTORIZACION_EMPLAZAMIENTO','Autorización de Emplazamiento','Solo cuando corresponda.',true,'{"trigger":"cuando_corresponda"}'::jsonb),
('DOC_RUBRO_ESPECIFICO','Documentación particular del rubro','La autoridad puede requerir documentación adicional.',true,'{"trigger":"actividad_especifica"}'::jsonb)
) AS x(code,title,description,conditional,conditions)
ON CONFLICT (procedure_id, document_code) WHERE document_code IS NOT NULL DO UPDATE SET title=EXCLUDED.title, description=EXCLUDED.description, conditional=EXCLUDED.conditional, conditions=EXCLUDED.conditions, source_version_id=EXCLUDED.source_version_id;

WITH p AS (SELECT id FROM procedures WHERE code='habilitacion_actividad_economica'),
sv AS (SELECT id FROM source_versions WHERE version_label='snapshot-2026-10-13' AND source_id=(SELECT id FROM sources WHERE code='gcba_habilitacion_actividad'))
INSERT INTO procedure_steps(procedure_id,step_order,title,description,source_version_id)
SELECT p.id,x.ord,x.title,x.description,sv.id FROM p CROSS JOIN sv CROSS JOIN (VALUES
(1,'Iniciar solicitud','Ingresar a la plataforma SSIT de AGC con usuario miBA y seleccionar “Nueva Autorización de Actividad Económica”.'),
(2,'Identificar titular o firmante','Ingresar CUIT de la persona solicitante o firmante, física o jurídica.'),
(3,'Declarar ubicación','Informar dirección, tipo de ubicación, partida o matriz, datos catastrales, ubicación especial y contacto.'),
(4,'Guardar solicitud','Se genera Número de Trámite y Código de Seguridad, necesarios para el Anexo Técnico.'),
(5,'Solicitar Certificado de Aptitud Ambiental','Tramitar el CAA en el servicio indicado por GCBA.'),
(6,'Presentar documentación y esperar evaluación','La Dirección General de Habilitaciones y Permisos evalúa y puede librar al uso, aprobar, observar o rechazar.')
) AS x(ord,title,description)
ON CONFLICT(procedure_id,step_order) DO UPDATE SET title=EXCLUDED.title,description=EXCLUDED.description,source_version_id=EXCLUDED.source_version_id;

-- Condiciones de elegibilidad del exprés. Cada condición se representa como requisito
-- estructurado; el motor solo puede confirmar elegibilidad si todas se conocen y cumplen.
WITH p AS (SELECT id FROM procedures WHERE code='habilitacion_actividad_economica_expres'),
sv AS (SELECT id FROM source_versions WHERE version_label='snapshot-2026-10-13' AND source_id=(SELECT id FROM sources WHERE code='gcba_habilitacion_expres'))
INSERT INTO procedure_requirements(procedure_id,requirement_code,title,description,conditional,conditions,source_version_id)
SELECT p.id,x.code,x.title,x.description,false,x.conditions,sv.id FROM p CROSS JOIN sv CROSS JOIN (VALUES
('SUPERFICIE_MAX_200','Superficie máxima de 200 m²','La superficie total no debe superar 200 m².','{"operator":"lte","field":"surface_m2","value":200}'::jsonb),
('SIN_EXPLOSIVOS','No comercializar explosivos','No debe comercializar explosivos.','{"operator":"not_contains","field":"merchandise","value":"explosivos"}'::jsonb),
('SIN_INFLAMABLES','No comercializar inflamables','No debe comercializar inflamables.','{"operator":"not_contains","field":"merchandise","value":"inflamables"}'::jsonb),
('SIN_MEDICAMENTOS_SIN_ENVASAR','No vender medicamentos sin envasar','No debe comercializar productos medicinales sin envasar.','{"operator":"not_contains","field":"merchandise","value":"medicamentos_sin_envasar"}'::jsonb),
('UBICACION_NO_EXCLUIDA','Ubicación admisible','No estar en galerías, centros comerciales, paseos de compras, mercados, patios gastronómicos, estaciones de subte/tren, aeropuertos u otros complejos comerciales.','{"operator":"not_in","field":"location_type","values":["galeria","centro_comercial","paseo_compras","mercado","patio_gastronomico","estacion_subte","estacion_tren","aeropuerto","complejo_comercial"]}'::jsonb),
('SIN_AREA_ESPECIAL','Sin área especial excluida','No estar en un área especial histórica, cultural, ambiental o con restricciones específicas.','{"operator":"equals","field":"special_area_excluded","value":false}'::jsonb),
('EDIFICIO_NO_CATALOGADO','Edificio no catalogado con restricciones','No estar en edificio catalogado o restringido.','{"operator":"equals","field":"catalogued_or_restricted_building","value":false}'::jsonb),
('ACCESIBILIDAD','Condiciones de accesibilidad','Debe cumplir condiciones de accesibilidad vigentes.','{"operator":"equals","field":"accessibility_compliant","value":true}'::jsonb),
('SIN_ENTREPISO','Sin entrepisos','No debe haber entrepisos en las plantas a habilitar.','{"operator":"equals","field":"has_mezzanine","value":false}'::jsonb),
('SIN_REGIMEN_ESPECIFICO','Actividad sin régimen específico excluyente','No desarrollar actividad que requiera normativa específica incompatible con la vía exprés.','{"operator":"equals","field":"requires_specific_regime","value":false}'::jsonb)
) AS x(code,title,description,conditions)
ON CONFLICT (procedure_id, requirement_code) WHERE requirement_code IS NOT NULL DO UPDATE SET title=EXCLUDED.title, description=EXCLUDED.description, conditional=EXCLUDED.conditional, conditions=EXCLUDED.conditions, source_version_id=EXCLUDED.source_version_id;

WITH p AS (SELECT id FROM procedures WHERE code='habilitacion_actividad_economica_expres'),
sv AS (SELECT id FROM source_versions WHERE version_label='snapshot-2026-10-13' AND source_id=(SELECT id FROM sources WHERE code='gcba_habilitacion_expres'))
INSERT INTO procedure_steps(procedure_id,step_order,title,description,source_version_id)
SELECT p.id,x.ord,x.title,x.description,sv.id FROM p CROSS JOIN sv CROSS JOIN (VALUES
(1,'Ingresar a SSIT','Acceder a la plataforma SSIT de AGC con usuario y contraseña miBA.'),
(2,'Declarar ubicación','Ingresar dirección, partida/datos catastrales o ubicación especial.'),
(3,'Identificar titular o firmante','Ingresar CUIT de la persona solicitante.'),
(4,'Completar datos del local y conformidad de uso','Informar dimensiones, tipo de superficie, ventilación, destino y características generales del local.'),
(5,'Declarar rubros y actividades','Indicar el rubro del negocio y las actividades que se desarrollarán.'),
(6,'Confirmar y enviar','Revisar datos. Si no se cumplen las condiciones, el sistema deriva a otro trámite; la información oficial indica que el CAA se genera automáticamente en esta vía.')
) AS x(ord,title,description)
ON CONFLICT(procedure_id,step_order) DO UPDATE SET title=EXCLUDED.title,description=EXCLUDED.description,source_version_id=EXCLUDED.source_version_id;

COMMIT;
