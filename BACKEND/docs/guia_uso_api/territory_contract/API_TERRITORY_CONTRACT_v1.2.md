# Contrato de `POST /api/v1/territory` — v1.2

Este documento describe el contrato de aplicación del flujo territorial. El esquema de respuesta mantiene campos opcionales y estados parciales: la ausencia de datos no equivale a una evaluación favorable.

## Entrada

```json
{
  "query": "Quiero abrir una cafetería en Av. Corrientes 2880, CABA",
  "activity": "Cafetería",
  "activity_code": null,
  "address": "Av. Corrientes 2880, CABA",
  "confirm_activity": false,
  "surface_m2": 120,
  "street_width_m": null,
  "frontage_m": null,
  "include_geometry": false
}
```

Se puede enviar solo `activity` + `address`. `activity_code` es opcional; si se envía junto con `activity`, el backend verifica el conflicto. `surface_m2`, `street_width_m`, `frontage_m` e `include_geometry` son opcionales. Confirmar la actividad es una decisión explícita de la persona, no una decisión del modelo.

## Respuesta

La forma completa depende de qué datos estén disponibles; la estructura estable es:

```json
{
  "contract_version": "1.2",
  "request_id": "<uuid>",
  "generated_at": "<timestamp ISO-8601>",
  "query": {
    "text_input": "...",
    "activity_input": "Cafetería",
    "activity_code_input": null,
    "address_input": "...",
    "address_extracted": null,
    "address_extraction_method": "explicit_input",
    "address_candidate_evidence": null,
    "input_interpretation": {
      "status": "disabled",
      "activity_mentions": [],
      "address_candidate": null,
      "parameter_fields_applied": [],
      "rejected_candidate_count": 0
    },
    "address_used": "...",
    "parameters": {
      "surface_m2": 120,
      "street_width_m": null,
      "frontage_m": null,
      "include_geometry": false,
      "extracted_by_ai": []
    }
  },
  "execution": {
    "mode": "deterministic",
    "ai_used": false,
    "ai_stages": {
      "input_interpreter": {"enabled": false, "status": "disabled", "used": false, "called": false, "candidate_count": 0, "fallback": "deterministic"},
      "explanation_generator": {"enabled": false, "status": "disabled", "used": false, "called": false}
    }
  },
  "activity": null,
  "location": null,
  "territory": {
    "parcel": null,
    "administrative": {"barrio": null, "comuna": null},
    "urbanism": {"status": "unavailable", "mixturas": [], "special_districts": [], "indicators": {}},
    "land_use": [],
    "useful_data": {}
  },
  "compatibility": null,
  "procedure_type_mapping": null,
  "procedures": {"status": "not_loaded", "items": []},
  "sources": [],
  "warnings": []
}
```

Los valores `null`, listas vacías y estados iniciales de arriba son ilustrativos del esqueleto de respuesta, no una promesa de que una consulta real devuelva exactamente esos valores. El flujo puede añadir propiedades a `activity`, `location`, `territory`, `compatibility`, `procedure_type_mapping`, `procedures`, `sources`, `warnings` y `metadata`.

## Cómo interpretar el resultado

- `status` raíz: estado de la consulta; valores actuales incluyen `resolved`, `partial`, `needs_activity`, `needs_activity_confirmation` y `needs_address`.
- `activity.status`: resolución de catálogo; si es `ambiguous` o requiere confirmación, mostrar candidatos y no seleccionar automáticamente.
- `location`: resultado de geocodificación y enlace a la parcela; una dirección geocodificada no garantiza que se haya recuperado una regla urbanística.
- `territory.urbanism.status`: `available` o `unavailable`; `mixturas: []` no significa compatibilidad.
- `compatibility`: puede ser `null` o insuficiente si faltan entradas/reglas. Nunca interpretar ausencia como aprobación.
- `procedure_type_mapping`: clasificación Anexo II con estado y fuente.
- `procedures.status`: `available`, `partial` o `not_loaded`; revisar además requisitos, documentos y pasos de cada elemento.
- `warnings`: códigos de máquina; el frontend debe mapearlos a mensajes claros sin borrar el código técnico en logs.
- `sources`: fuentes/versiones utilizadas, cuando estén disponibles.
- `query.address_extraction_method`: `explicit_input`, `deterministic_pattern`, `ai_interpreter_candidate` o `not_found` para trazabilidad de la dirección usada. `address_candidate_evidence` solo se completa si la dirección fue propuesta y validada por el intérprete.
- `query.input_interpretation`: menciones estructuradas validadas contra el texto, candidato de dirección, estado del intérprete y recuento de candidatos rechazados. `activity_mentions` no contiene un código oficial: deben contrastarse con `activity.candidates` y el catálogo.
- `query.parameters.extracted_by_ai`: nombres de parámetros que el intérprete propuso con evidencia validada y que completaron campos no informados explícitamente.
- `execution.ai_stages.input_interpreter`: `enabled` indica configuración, `called` si se invocó el modelo, `used` si un candidato aceptado contribuyó al flujo, `candidate_count` indica cuántos candidatos estructurados se recibieron, y `fallback` indica que se mantiene el camino determinístico. `status` puede ser `disabled`, `skipped`, `running`, `completed`, `completed_no_candidates` o `unavailable_fallback`.
- `execution.mode` continúa siendo `deterministic`, porque las decisiones y cálculos del dominio no los toma el modelo. `execution.ai_used` se activa únicamente cuando se usa una extracción aceptada.
- `execution.ai_stages.explanation_generator` permanece apagado/no conectado en v0.3.7.

## HTTP vs estados de negocio

- `200`: la consulta fue procesada, incluso si el resultado funcional es parcial o necesita aclaraciones.
- `404 ADDRESS_NOT_FOUND`: el proveedor no logró identificar la dirección.
- `422`: entrada inválida o insuficiente para iniciar el proceso.
- `502`: proveedor externo no disponible.
- `503`: servicio o dependencia crítica no disponible.

El frontend no debe tratar cada `200` como resultado final ni cada `partial` como error de servidor.
