# Sistema de Gestión Inteligente

**InnovaLab 2C 2026 — Equipo 7**

Plataforma web inteligente de consulta y orientación para actividades comerciales, trámites e información territorial de la Ciudad.

> **Estado del proyecto:** MVP en etapa inicial de análisis, definición de arquitectura y desarrollo.

---

## 📌 Descripción

El **Sistema de Gestión Inteligente** busca simplificar la forma en que una persona accede a información relacionada con una actividad comercial y una ubicación determinada.

La propuesta parte de una necesidad expresada en lenguaje natural —qué quiere hacer y dónde— para relacionar información proveniente de distintas fuentes y ofrecer una orientación contextualizada.

El MVP está orientado inicialmente a un **caso de uso concreto vinculado con el inicio de una nueva actividad comercial**.

La solución busca integrar información sobre:

* Actividades y trámites.
* Requisitos y documentación.
* Pasos necesarios para avanzar con una gestión.
* Información territorial y de contexto.
* Ubicación y georreferenciación.
* Fuentes oficiales.
* Consulta mediante Inteligencia Artificial.
* Visualización de información territorial mediante un mapa interactivo.

El objetivo es transformar información distribuida en una respuesta **simple, contextualizada y accionable**, sin exigir que la persona conozca previamente qué organismos, sistemas o fuentes debe consultar.

---

## 🎯 Objetivo del MVP

Validar un recorrido completo para un caso de uso concreto, integrando:

1. Consulta de la necesidad de la persona.
2. Identificación de la actividad.
3. Identificación de la ubicación.
4. Recuperación e integración de información relevante.
5. Orientación sobre trámites, requisitos, documentación y pasos.
6. Información territorial asociada.
7. Visualización mediante mapa interactivo.
8. Consulta y profundización mediante IA.
9. Referencias a las fuentes utilizadas.

El MVP contempla como requisito mínimo la integración de **al menos tres fuentes de información**, junto con información territorial, mapa interactivo y consulta mediante IA.

---

## 🧩 Problemática

La información necesaria para realizar una gestión puede encontrarse distribuida entre diferentes sistemas, plataformas, organismos y fuentes de datos.

Estas fuentes pueden presentar:

* Diferentes formatos.
* Diferentes estructuras.
* Diferentes mecanismos de acceso.
* Información territorial separada de la información de trámites.
* Diferentes niveles de actualización y procesamiento.

Esto puede obligar a la ciudadanía a identificar por su cuenta qué fuente consultar, localizar la información y relacionar los resultados.

El proyecto busca abordar esta fragmentación mediante una experiencia de consulta integrada.

---

## 💡 Solución propuesta

La solución plantea un recorrido basado en:

```text
Necesidad ciudadana
        ↓
    Ubicación
        ↓
Integración de fuentes
        ↓
   Interpretación
        ↓
Orientación contextualizada
        ↓
Visualización territorial
        ↓
   Profundización
```

La plataforma deberá relacionar la consulta de la persona con la información disponible y presentar los resultados de forma comprensible.

---

## 🗺️ Recorrido principal del MVP

El camino esperado para el caso piloto contempla:

```text
Consulta
   ↓
Actividad + ubicación
   ↓
Procesamiento de información
   ↓
Respuesta contextualizada
   ↓
Trámites / requisitos / documentación / pasos
   ↓
Información territorial
   ↓
Mapa
   ↓
Fuentes utilizadas
   ↓
Preguntas de seguimiento
```

La experiencia deberá permitir continuar profundizando sobre la necesidad inicial sin perder el contexto de la consulta.

---

## 🤖 Inteligencia Artificial

La IA funcionará como una **capa de interpretación y organización de la información**, no como fuente de verdad.

El flujo previsto es:

```text
Interpretación de la consulta
          ↓
Identificación de actividad y ubicación
          ↓
Recuperación de información relevante
          ↓
Organización de la información
          ↓
Explicación de la respuesta
```

La información sobre trámites, territorio y requisitos deberá provenir de las fuentes integradas.

Las respuestas generadas deberán poder relacionarse con las fuentes que respaldan la información presentada.

Para el MVP no se plantea como requisito inicial una arquitectura RAG compleja; la implementación de IA deberá adecuarse a las necesidades y fuentes efectivamente seleccionadas.

---

## 🗃️ Fuentes y datos

El proyecto contempla la integración de diferentes tipos de fuentes, que pueden incluir información territorial, datos abiertos y fuentes relacionadas con trámites.

Durante el MVP se deberán analizar:

* Disponibilidad.
* Estructura.
* Calidad.
* Formato.
* Mecanismo de acceso.
* Actualización.
* Relaciones entre datos.
* Posibles inconsistencias o datos faltantes.

Los formatos considerados en el proyecto pueden incluir:

```text
PDF
CSV
XLSX
KML
SHP
JSON
APIs
```

La selección definitiva de fuentes se realizará durante el desarrollo del MVP.

---

## 🗺️ Información territorial

La solución contempla trabajar con información geográfica y territorial relacionada con la consulta.

Entre las capacidades previstas se encuentran:

* Ubicación de direcciones.
* Geocodificación.
* Información territorial.
* Relación entre ubicación y actividad.
* Visualización mediante mapa interactivo.
* Navegación entre la respuesta y la información territorial.

---

## 🏗️ Arquitectura y tecnologías

La arquitectura se encuentra actualmente en etapa de definición.

El documento del MVP plantea tecnologías posibles para cubrir las distintas necesidades del sistema.

| Área                    | Tecnologías / herramientas posibles     |
| ----------------------- | --------------------------------------- |
| Frontend                | React / Next.js                         |
| Lenguaje                | JavaScript / TypeScript                 |
| Backend / APIs          | Python + FastAPI                        |
| Base de datos           | PostgreSQL / Supabase                   |
| Información geoespacial | PostgreSQL + PostGIS                    |
| Procesamiento de datos  | Python / Pandas                         |
| Datos geográficos       | GeoPandas                               |
| Mapas                   | Leaflet / MapLibre GL / Mapbox          |
| Geocodificación         | Servicio compatible                     |
| APIs / fuentes          | APIs REST / datasets públicos           |
| IA                      | API de modelo LLM                       |
| UX/UI                   | Figma                                   |
| Flujos / arquitectura   | FigJam / Miro                           |
| Testing de APIs         | Postman                                 |
| QA                      | Jira + Zephyr / herramienta equivalente |
| Control de versiones    | Git + GitHub                            |
| Frontend hosting        | Vercel                                  |
| Backend hosting         | Render / Railway                        |
| Datos / almacenamiento  | Supabase                                |

**Importante:** esta tabla representa alternativas planteadas en la documentación del MVP. La selección definitiva de tecnologías corresponde a las decisiones de arquitectura del equipo.

---

## 👥 Áreas de trabajo

El proyecto se desarrolla mediante trabajo multidisciplinario:

### UX/UI

Responsable de la experiencia de la persona usuaria, recorridos, navegación, jerarquía de información, accesibilidad y presentación de resultados.

### FRONT

Responsable de la interfaz y de la integración de la experiencia de consulta, mapa, resultados, fuentes y demás componentes que correspondan al frontend.

Actualmente existe una **base técnica inicial de frontend** en el repositorio. Esta base no representa todavía la plataforma completa.

### BACK

Responsable de servicios, APIs, integración de fuentes, procesamiento territorial, geocodificación, lógica de trámites, IA y demás componentes backend que se definan en la arquitectura.

### DATA / BI / Machine Learning

Responsable del análisis, transformación, relación y calidad de los datos, además de la validación de las relaciones entre actividad, ubicación, territorio y trámites.

### QA

Responsable de la estrategia y validación de calidad:

* Análisis funcional.
* Escenarios de prueba.
* Casos de prueba.
* Validación del camino feliz.
* Pruebas negativas.
* Validación de datos.
* Validación de ubicación.
* Validación del mapa.
* Validación de integración de fuentes.
* Validación de respuestas de IA.
* Testing End-to-End.
* Regresión.
* Registro y seguimiento de defectos.

---

## 📁 Estructura del repositorio

La estructura se organizará por áreas:

```text
sistema-gestion-inteligente/
│
├── FRONT/
│   └── ...
│
├── BACK/
│   └── ...
│
├── QA/
│   └── ...
│
├── UX/
│   └── ...
│
├── DATA/
│   └── ...
│
└── README.md
```

La estructura podrá evolucionar a medida que avance la arquitectura del proyecto.

---

## 🌿 Estrategia de ramas

La organización inicial contempla una rama principal y ramas de trabajo por área:

```text
main
├── front
├── back
├── qa
├── ux
└── data
```

### `main`

Rama principal de integración del proyecto.

### Branches de área

Cada área trabajará inicialmente en su propia branch.

El flujo previsto es:

```text
Branch del área
       ↓
     Trabajo
       ↓
    Commit
       ↓
     Push
       ↓
 Pull Request
       ↓
    Revisión
       ↓
     main
```

No se recomienda realizar cambios directamente sobre `main`.

---

## 🧪 Estrategia inicial de QA

La estrategia de QA contempla validar el recorrido completo del MVP y no solamente funcionalidades aisladas.

Se deberán considerar, entre otros:

* Camino feliz.
* Variaciones de consultas.
* Consultas ambiguas.
* Consultas incompletas.
* Consultas fuera de alcance.
* Direcciones válidas e inválidas.
* Información incompleta.
* Fuentes no disponibles.
* Inconsistencias entre fuentes.
* Relación entre respuesta y fuente.
* Relación entre respuesta y mapa.
* Exactitud de datos.
* Geocodificación.
* Preguntas de seguimiento.
* Respuestas generadas mediante IA.
* Integración End-to-End.

La validación deberá comprobar que la plataforma no presente como válida información que no esté respaldada por las fuentes disponibles.

---

## 🔎 Criterios generales de calidad

El MVP deberá avanzar hacia una experiencia en la que:

* La persona pueda expresar su necesidad de forma comprensible.
* La actividad y la ubicación puedan identificarse correctamente.
* La información de las fuentes pueda relacionarse.
* Los resultados territoriales sean consistentes.
* El mapa corresponda con la información presentada.
* Los trámites y requisitos sean comprensibles.
* Las fuentes utilizadas sean identificables.
* Las respuestas de IA estén respaldadas por información disponible.
* Las situaciones de información incompleta o no disponible sean comunicadas correctamente.
* El recorrido pueda validarse de punta a punta.

---

## 🚀 Alcance del MVP

El MVP se concentra inicialmente en un **caso piloto vinculado con el inicio de una actividad comercial**.

El objetivo no es resolver desde el comienzo todos los trámites y situaciones posibles de la Ciudad.

La arquitectura deberá permitir una evolución posterior hacia:

```text
Actividades
     +
Trámites
     +
Información territorial
     +
Fuentes oficiales
     +
IA
```

manteniendo como núcleo:

```text
necesidad ciudadana
        ↓
ubicación
        ↓
integración de fuentes
        ↓
interpretación
        ↓
orientación contextualizada
        ↓
visualización territorial
```

---

## 📅 Plan de trabajo

El proyecto contempla un proceso progresivo de desarrollo, validación e iteración.

### Sprint 1 — Preparación

Definición del equipo, caso piloto, recorrido principal y fuentes candidatas.

### Sprint 2 — Fundamentos

Primeras definiciones de UX/UI, arquitectura, fuentes, datos y estrategia de testing.

### Sprint 3 — Primer desarrollo

Primera consulta mediante IA, identificación de actividad y ubicación y primeras respuestas contextualizadas.

### Sprint 4 — Desarrollo e integración

Integración de fuentes, información territorial, mapa, geocodificación, IA y trazabilidad.

### Sprint 5 — Iteración

Testing integral, corrección de inconsistencias, mejoras de experiencia y validación de respuestas.

### Sprint 6 — Cierre

Regresión final, validación del MVP, documentación, despliegue y preparación de la presentación.

---

## ✅ Resultado esperado del MVP

Al finalizar el MVP se espera contar con una versión funcional capaz de demostrar un caso piloto de punta a punta que incluya:

* Al menos tres fuentes efectivamente integradas.
* Consulta de actividad y ubicación.
* Información territorial.
* Mapa interactivo.
* Información sobre trámites, requisitos y documentación.
* Consulta y profundización mediante IA.
* Preguntas de seguimiento.
* Trazabilidad de las fuentes.
* Manejo de información incompleta o no disponible.
* Testing End-to-End.
* Documentación técnica y funcional.

Las funcionalidades que excedan el caso piloto deberán identificarse como **Future Scope**.

---

## 📌 Estado actual

El proyecto se encuentra en una etapa inicial.

Actualmente se está trabajando en:

* Organización del repositorio.
* Definición de arquitectura.
* Organización de las áreas.
* Selección y análisis de fuentes.
* Definición del caso piloto.
* Diseño de la experiencia.
* Estrategia de datos.
* Estrategia inicial de QA.
* Desarrollo de la base técnica inicial.

La implementación de las funcionalidades del MVP se irá incorporando progresivamente.

---

## 📚 Documentación

La documentación funcional, técnica, de datos, UX y QA se incorporará progresivamente al repositorio dentro de las áreas correspondientes.

---

## 👥 Equipo

**InnovaLab 2C 2026 — Equipo 7**

Áreas:

* UX/UI
* Frontend
* Backend
* Data / BI / Machine Learning
* QA

---

## 🔗 Repositorio

**Sistema de Gestión Inteligente**

`InnovaLab-2C-2026-Equipo-7/sistema-gestion-inteligente`

---

> **Nota:** Este README resume el alcance y los lineamientos del documento de proyecto MVP. Las decisiones técnicas, funcionales y de arquitectura pueden evolucionar durante el desarrollo y deberán mantenerse actualizadas en la documentación correspondiente.
# Prueba-tecba
