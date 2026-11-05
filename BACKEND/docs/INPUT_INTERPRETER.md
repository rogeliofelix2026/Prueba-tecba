# Intérprete de entrada — SGI v0.3.7

## Propósito

`app/services/input_interpreter.py` convierte texto libre en **candidatos estructurados**, no en decisiones de negocio. Utiliza el cliente de Ollama local configurado por `OLLAMA_BASE_URL` y solicita JSON estricto. La salida se valida con Pydantic, se contrasta contra evidencia literal en el texto y finalmente se cruza con los servicios determinísticos existentes.

## Campos que puede proponer

- `activity_candidates`: hasta cinco menciones literales de actividades con evidencia textual.
- `address_candidate`: una mención textual que se puede parsear como calle + altura.
- `surface_m2`, `street_width_m` y `frontage_m`: valor numérico más evidencia semántica específica.

El intérprete no crea nombres oficiales ni asigna códigos. Los valores numéricos solo se utilizan si el número aparece en la evidencia, el contexto corresponde al campo y el valor no supera los límites defensivos del flujo. Nunca reemplazan un valor enviado explícitamente en el request.

## Flujo de validación

1. `TerritoryFlowService` conserva los valores explícitos del usuario como fuente prioritaria.
2. Primero se intenta reconocer la actividad de forma determinística. El intérprete solo se invoca cuando hay texto libre y falta una actividad reconocible, dirección o parámetros identificables por el texto.
3. La respuesta debe cumplir el esquema estructurado. Una mención o evidencia que no aparezca en el texto se descarta.
4. La dirección candidata pasa por `extract_address`; luego se valida de nuevo mediante geocodificación USIG.
5. Las actividades se pasan a `ActivityRepository.resolve_detailed`. Las coincidencias exactas pueden alimentar el flujo, pero una actividad inferida desde texto requiere confirmación cuando aplique. `search_catalog` solo produce sugerencias; nunca autoriza una selección por similitud parcial.
6. Si hay varios candidatos válidos, la respuesta usa `needs_activity_confirmation` y muestra las alternativas para el frontend.
7. Si Ollama falla, supera `AI_INPUT_INTERPRETER_TIMEOUT_SECONDS`, el JSON es inválido o la salida no cumple el contrato, se emite `AI_INPUT_INTERPRETER_UNAVAILABLE` y se conserva la extracción determinística.

## Configuración

Por defecto la función permanece desactivada:

```dotenv
AI_INPUT_INTERPRETER_ENABLED=false
AI_EXPLANATION_ENABLED=false
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_CHAT_MODEL=qwen3:8b
OLLAMA_CHAT_TIMEOUT_SECONDS=120
AI_INPUT_INTERPRETER_TIMEOUT_SECONDS=12
OLLAMA_CHAT_MAX_CONCURRENCY=2
```

Para probar localmente:

```bash
ollama serve
ollama pull qwen3:8b
# En otra terminal, con DB y entorno de Python ya configurados:
# cambiar AI_INPUT_INTERPRETER_ENABLED=true en .env
uvicorn app.main:app --reload
```

El intérprete no necesita embeddings ni pgvector. El camino principal usa el chat de Ollama con formato JSON; después valida la respuesta localmente. No debe exponerse Ollama a Internet ni reemplazarse `OLLAMA_BASE_URL` por un proveedor externo sin una decisión explícita de privacidad.

## Contrato de ejecución

`execution.mode` permanece `deterministic`, porque resolución de catálogo, geocodificación, parcela, compatibilidad y clasificación siguen en backend. `execution.ai_used` solo indica que al menos una extracción aceptada contribuyó a la respuesta. `execution.ai_stages.input_interpreter` expone `enabled`, `status`, `used`, `called`, `candidate_count` y `fallback`.

Estados del intérprete:

- `disabled`: flag apagada.
- `skipped`: flag activa pero no se necesita interpretar texto.
- `running`: estado transitorio durante la llamada; no debería llegar en una respuesta normal.
- `completed`: salida estructurada válida.
- `completed_no_candidates`: salida válida sin candidatos estructurados.
- `unavailable_fallback`: la llamada falló o la salida no cumplió el esquema; se conserva el camino determinístico.

## Pruebas

```bash
pytest -q tests/test_input_interpreter.py
pytest -q tests/test_territory_flow.py
pytest -q tests/test_config.py tests/test_procedure_codes.py
```

Las pruebas del servicio usan un cliente de Ollama falso: comprueban validación de evidencia, dirección, números, JSON inválido y fallback de flujo sin requerir el modelo real. La aceptación final requiere repetir las pruebas con Ollama local y con staging accesible.
