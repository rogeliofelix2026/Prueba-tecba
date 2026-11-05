# ANÁLISIS FUNCIONAL INICIAL Y REQUISITOS DEL MVP
## Caso piloto: Inicio de una actividad gastronómica desde cero
*Documento preliminar sujeto a revisión del equipo*

Este documento organiza una definición funcional inicial para que los distintos roles tengan una base común. Los requisitos son preliminares y pueden ampliarse, modificarse, dividirse o eliminarse luego de la revisión del equipo.

## 1. Objetivo

Describir el recorrido funcional inicial para una persona que desea comenzar una actividad gastronómica desde cero, relacionando la actividad, la ubicación, la información territorial, las fuentes oficiales, los trámites y los requisitos necesarios.
## 2. Alcance preliminar

- Usuario objetivo: persona interesada en iniciar un emprendimiento gastronómico.
- Actividad: construcción y puesta en funcionamiento de una cafetería.
- Ubicación: parcela ubicada en Av. Corrientes 2500, Ciudad Autónoma de Buenos Aires.
- Situación inicial: la persona desea comenzar desde cero y recibir orientación sobre la factibilidad y los pasos que debe seguir.
- Consulta de ejemplo: “Quiero construir una cafetería en Av. Corrientes 2500. ¿Qué tengo que hacer?”
- Queda por confirmar si el MVP abarcará solamente la factibilidad urbanística o si también incluirá permisos de obra, habilitación comercial y requisitos específicos para una actividad gastronómica.
## 3. Recorrido funcional general

- La persona ingresa una consulta en lenguaje natural.
- La plataforma identifica la actividad que desea realizar.
- La plataforma identifica el tipo de proyecto, en este caso, construir una cafetería desde cero.
- La plataforma procesa la ubicación indicada y verifica si puede reconocerla.
- La plataforma obtiene información territorial y, cuando sea posible, relaciona la dirección con la parcela correspondiente.
- La plataforma consulta la información urbanística, los trámites y los requisitos relacionados con la actividad y la ubicación.
- La información obtenida se integra, se organiza y se presenta de forma comprensible.
## 4. Información que debería recibir el usuario

- Identificación de la actividad que desea realizar.
- Ubicación reconocida y datos territoriales disponibles.
- Información sobre uso del suelo, normativa aplicable, condiciones y restricciones de la parcela.
- Información sobre la factibilidad de realizar la actividad en esa ubicación, según las fuentes disponibles.
- Trámites y permisos que podrían corresponder.
- Requisitos y documentación necesarios para cada etapa.
- Requisitos específicos vinculados con una actividad gastronómica.
- Orden sugerido de próximos pasos.
- Fuentes que respaldan la información presentada.
- Aclaración cuando la información no sea suficiente para determinar una respuesta.
## 5. Requisitos funcionales preliminares

| Código | Nombre | Descripción |
|---|---|---|
| RF-01 | Ingresar consulta | Se propone que el sistema permita que la persona ingrese una consulta en lenguaje natural. |
| RF-02 | Identificar actividad | Se propone que el sistema identifique la actividad que la persona desea realizar. |
| RF-03 | Identificar tipo de proyecto | Se propone que el sistema identifique si el proyecto parte desde cero y qué tipo de establecimiento se desea desarrollar. |
| RF-04 | Procesar ubicación | Se propone que el sistema procese la dirección o ubicación indicada por la persona. |
| RF-05 | Mostrar ubicación | Se propone que el sistema muestre la ubicación reconocida y, cuando corresponda, los datos territoriales asociados. |
| RF-06 | Obtener información territorial | Se propone que el sistema consulte información territorial relacionada con la ubicación. |
| RF-07 | Relacionar actividad y ubicación | Se propone que el sistema relacione la actividad solicitada con la información territorial y normativa disponible. |
| RF-08 | Consultar fuentes | Se propone que el sistema consulte las fuentes oficiales definidas para el MVP. |
| RF-09 | Organizar requisitos | Se propone que el sistema organice los trámites, requisitos y documentación según las etapas del proyecto. |
| RF-10 | Presentar orientación | Se propone que el sistema presente una orientación integrada y ordenada para la persona usuaria. |
| RF-11 | Mostrar fuentes | Se propone que el sistema identifique o permita consultar las fuentes que respaldan la información presentada. |
| RF-12 | Utilizar IA como apoyo | Se propone que el sistema pueda utilizar IA para interpretar la consulta y organizar la respuesta utilizando como base la información de las fuentes. |
| RF-13 | Informar falta de información | Se propone que el sistema informe cuando no exista información suficiente o cuando una respuesta no pueda determinarse con los datos disponibles. |

## 6. Camino feliz del caso piloto

El camino feliz representa el funcionamiento esperado cuando la persona proporciona una consulta válida, la ubicación puede identificarse y las fuentes responden correctamente.
- La persona ingresa: “Quiero construir una cafetería en Av. Corrientes 2500”.
- La plataforma identifica la actividad gastronómica.
- La plataforma procesa y valida la dirección.
- La ubicación se relaciona con la parcela correspondiente.
- Se consulta la información urbanística y territorial.
- Se consultan las fuentes relacionadas con trámites y requisitos.
- La información se integra y organiza.
- La IA, si corresponde, ayuda a interpretar y presentar la información.
- La plataforma muestra una orientación clara, con fuentes y próximos pasos.
## 7. Fuentes e información necesaria

| Necesidad de información | Qué se necesita conocer | Posible grupo de fuentes |
|---|---|---|
| Información urbanística | Uso del suelo, normativa aplicable, condiciones y restricciones de la parcela. | Fuentes oficiales de urbanismo y Código Urbanístico. |
| Información territorial | Ubicación, parcela, datos geográficos y relación con la dirección. | Datos territoriales oficiales y servicio de geocodificación. |
| Permisos de construcción | Trámites, documentación y condiciones para realizar una obra, si forman parte del MVP. | Portal oficial de trámites y organismos competentes. |
| Habilitación de actividad | Requisitos para habilitar y poner en funcionamiento el establecimiento. | Organismos oficiales de habilitaciones y control. |
| Requisitos gastronómicos | Condiciones sanitarias, manipulación de alimentos y requisitos específicos de la actividad. | Organismos oficiales de seguridad alimentaria. |

La definición de las fuentes a utilizar se propone como un trabajo conjunto entre los roles involucrados, considerando especialmente los aportes de BI, Data y Machine Learning. En esta etapa, se propone identificar primero qué información necesita responder la plataforma.
Las fuentes podrían evaluarse según su disponibilidad, actualización, calidad, estructura, posibilidad de acceso y relación con el caso piloto.
## 8. Arquitectura inicial de la solución

- Frontend: interfaz mediante la cual la persona ingresa la consulta y recibe la respuesta.
- Backend: componente que coordina el procesamiento de la consulta, la integración de fuentes y la entrega de resultados.
- Geocodificación: componente o servicio que ayuda a interpretar la dirección y relacionarla con una ubicación geográfica.
- Fuentes oficiales: organismos y servicios que aportan información urbanística, territorial, de trámites y de requisitos.
- Base de datos o almacenamiento: espacio destinado a conservar la información que el equipo determine que debe almacenarse.
- Capa de integración: componente encargado de reunir y organizar información proveniente de distintas fuentes.
- IA como apoyo: capa que puede ayudar a interpretar la consulta y redactar la respuesta, sin reemplazar las fuentes oficiales ni inventar información.
- Flujo general: Persona usuaria → Frontend → Backend → Geocodificación y fuentes → Integración → IA/presentación → Respuesta.
## 9. Criterios iniciales de validación QA

- La actividad identificada corresponde con la intención de la consulta.
- La dirección mostrada corresponde con la dirección ingresada o se informa claramente si no pudo reconocerse.
- La información territorial corresponde con la ubicación seleccionada.
- La relación entre la actividad y la ubicación está respaldada por información disponible.
- Los trámites, requisitos y condiciones presentados tienen una fuente identificable.
- La IA no agrega como hechos datos que no estén respaldados.
- Cuando falta información, el sistema lo comunica de manera clara.
- La respuesta está organizada en un orden comprensible para la persona usuaria.
- Las fuentes pueden identificarse y consultarse cuando corresponda.
## 10. Preguntas

- ¿El alcance incluye solamente factibilidad urbanística o también permisos de construcción, habilitación y requisitos gastronómicos?
- ¿Se supone que la persona ya dispone de la parcela o la propiedad, el alquiler y la autorización forman parte del alcance?
- ¿Cuál será la información mínima que debe contener una respuesta válida?
- ¿Qué fuentes oficiales se utilizarán inicialmente?
- ¿La IA responderá únicamente con información respaldada por fuentes?
- ¿Qué hará el sistema cuando la dirección no sea reconocida?
- ¿Qué hará el sistema cuando una fuente no esté disponible o entregue información incompleta?
- ¿Qué información se almacenará y qué información se consultará en tiempo real?
## 11. Relación con los roles

- Todos los roles: pueden aportar a la revisión del alcance, el recorrido y el resultado esperado.
- UX/UI: podría aportar al diseño de la forma de ingresar consultas y mostrar resultados, fuentes, mapas y próximos pasos.
- Frontend: podría encargarse de la interacción de la interfaz.
- Backend: podría encargarse de la lógica de procesamiento y coordinación de servicios.
- BI/Data/Machine Learning: podrían aportar a la investigación, preparación, integración y evaluación de las fuentes y del uso de IA.
- QA: podría aportar a la identificación de escenarios, riesgos y criterios de validación, y posteriormente a la verificación de lo acordado.
## 12. Próximos pasos

- Como próximos pasos, se propone revisar y validar el alcance exacto del caso piloto.
- Revisar el camino feliz y las situaciones que podrían contemplarse además de ese recorrido.
- Acordar cuál sería el resultado mínimo que debería recibir la persona usuaria.
- Identificar la información necesaria en cada etapa del recorrido.
- Proponer y evaluar las fuentes iniciales.
- Ajustar, dividir o eliminar requisitos según lo que acuerde el equipo.
- Revisar la arquitectura y la participación de cada componente.
- Registrar riesgos y decisiones que queden pendientes de definición.
- Cuando los requisitos estén acordados, convertirlos en criterios de aceptación y escenarios de prueba.