# BI, Data & Machine Learning

## Objetivos

* Normalizar la información necesaria de las tres fuentes.
* Implementar primeras relaciones entre datos territoriales, contexto y trámites.
* Validar que el resultado sea consistente para el caso piloto.

---

# Pedido Backend

## Disponibilizar fuentes territoriales y de contexto

El próximo paso que necesitamos de Data sería dejar disponibles las fuentes territoriales originales, **sin transformarlas ni cargarlas todavía en Supabase**.

Por ahora, priorizaría:

1. **Parcelas**, para resolver `lat/lon → SMP → parcela`.
2. **Código Urbanístico**, con datos geográficos en `.csv` y documentación en `.pdf`.
3. **Usos del Suelo 2022-2024**, para agregar contexto sobre los usos asociados al SMP.
4. **Otros**, si les parece oportuno.

### Flujo de trabajo propuesto

La idea es conservar los archivos como **RAW** y seguir posteriormente este flujo:

```text
RAW
 ↓
Repo
 ↓
Validación
 ↓
Normalización
 ↓
Backend procesa
 ↓
Carga en BD
```

Con cada dataset necesitamos registrar:

* URL oficial.
* Fecha de descarga.
* Fecha de actualización de la fuente.
* Formato.
* CRS, si corresponde.
* Nombre del recurso.
* Breve descripción.

Primero queremos observar cómo vienen realmente los datos y validar las relaciones entre datasets.

Después sería conveniente disponer de una versión limpia/transformada para:

* Renombrar columnas.
* Eliminar registros.
* Corregir valores.
* Unificar códigos.

Si los archivos son grandes, no es necesario subirlos directamente a Git. Se puede utilizar:

* Git LFS.
* Releases.
* Otro almacenamiento versionado.
* Drive.

Lo importante es conservar:

* Ubicación.
* Versión.
* Fecha.
* Checksum.
* Metadata.

### Profiling y validación

Una vez disponibles los datasets, el siguiente paso será realizar el **profiling y validación** de:

* Columnas.
* Tipos de datos.
* Valores nulos.
* Duplicados.
* SMP.
* Geometrías.
* CRS.
* Relaciones entre datasets.

La idea es poder resolver una dirección como:

> **Corrientes 2500**

hasta obtener un único:

```text
SMP → Parcela → Información territorial relacionada
```

A partir de ahí, se relacionará o extraerá la información necesaria.

---

# Datos territoriales

## Parcelas

**Descripción:** Polígonos de las parcelas de la Ciudad Autónoma de Buenos Aires.

### Frente de parcelas

Contiene información correspondiente a los frentes de las parcelas de la Ciudad Autónoma de Buenos Aires, incluyendo:

* Nombres de las calles.
* Números de puerta correspondientes a cada parcela.
* Manzana.
* Sección.
* Otros datos asociados.

### Formatos disponibles

Ambos datasets están disponibles en:

* CSV
* XLSX
* SHP
* GeoJSON

### Campos del dataset

| Nombre                        | Tipo     | Identificador | Descripción                                                             |
| ----------------------------- | -------- | ------------- | ----------------------------------------------------------------------- |
| Identificador                 | number   | `id`          | Identificador único del registro de parcela.                            |
| Sección                       | string   | `seccion`     | Sección catastral donde se ubica la parcela.                            |
| Manzana                       | string   | `manzana`     | Identificador de la manzana catastral.                                  |
| Parcela                       | string   | `parcela`     | Código o número de parcela dentro de la manzana.                        |
| Sistema de Mensura Parcelaria | string   | `smp`         | Código compuesto de identificación catastral (sección-manzana-parcela). |
| Partida matriz                | number   | `partida_ma`  | Número de partida matriz asociado a la parcela.                         |
| Barrio                        | string   | `barrio`      | Barrio de la Ciudad Autónoma de Buenos Aires donde se ubica la parcela. |
| Comuna                        | string   | `comuna`      | Comuna correspondiente dentro de la Ciudad Autónoma de Buenos Aires.    |
| Geometría                     | geometry | `geometry`    | Representación geométrica del polígono de la parcela en formato WKT.    |

**Dataset para descargar:**
https://data.buenosaires.gob.ar/dataset/parcelas

---

# Código Urbanístico y Planeamiento Urbano

## Código Urbanístico

Texto consolidado del Código Urbanístico, incluyendo:

* Definiciones.
* Normas generales.
* Usos del suelo.
* Procedimientos aplicables.

**Versión actualizada al 31 de diciembre de 2024.**

### Texto consolidado — PDF

https://static.buenosaires.gob.ar/sites/default/files/2025-02/cur-cuerpo-principal_0.pdf

### Código Urbanístico actualizado — CSV

https://data.buenosaires.gob.ar/dataset/codigo-urbanistico/resource/d569079d-8d9c-48c3-8477-f28ebedfeac6

## Código Urbanístico — Anexo III

Conjunto de planos y mapas del Código Urbanístico que delimitan:

* Áreas.
* Usos del suelo.
* Protecciones.
* Riesgos específicos.

**Recurso:**

https://data.buenosaires.gob.ar/dataset/codigo-urbanistico/resource/01e44fcb-6404-4bbf-921a-837942e37dc4

## Código Urbanístico — Anexo IV

### Plancheta de Edificabilidad y Usos

Mapas técnicos que indican:

* Niveles de edificabilidad.
* Usos permitidos para cada zona.

**Recurso:**

https://data.buenosaires.gob.ar/dataset/codigo-urbanistico/resource/cc10307d-2072-4a71-a3e2-779c0fd38627

### Caso específico: Corrientes 2500

Para **Corrientes 2500** corresponde consultar:

> Plancheta 12 — `anexoiiii-plachetas (1)-14.pdf`

## Código de Planeamiento Urbano

https://ciudad3d.buenosaires.gob.ar/Normative/texto_cpu_al_21_de_dic_2018.pdf

---

# Contexto

## Usos del Suelo

### Documentación — Relevamiento Usos del Suelo 2022-2024

https://data.buenosaires.gob.ar/dataset/relevamiento-usos-suelo/resource/801aecc9-d361-4f83-8f61-08c9b76f987d

### Dataset — Relevamiento Usos del Suelo 2022-2024

https://data.buenosaires.gob.ar/dataset/relevamiento-usos-suelo/resource/3c7e5f10-577a-44ea-b614-82cc05f842aa

También disponible en:

* XLSX
* SHP

---

# Permisos para la venta de alimentos en el espacio público

Información sobre permisos de uso del espacio público para venta de alimentos otorgados por la Ciudad.

Incluye:

* Información del titular.
* Expediente.
* Disposición.
* Información geográfica de la ubicación del puesto.

### Dataset

https://data.buenosaires.gob.ar/dataset/venta-de-alimentos/resource/d1a83813-6d49-495f-931c-5a5a7d5153fb

### Aplicación al caso piloto

Con la dirección:

> **Corrientes 2500**

se puede determinar si existen permisos otorgados en la zona.

### Campos efectivamente disponibles

> **Atención:** en el listado de variables del dataset existe más información que la disponible efectivamente en el CSV.

Los campos disponibles son:

* N.º de expediente.
* Titular.
* DNI.
* Plaza.
* Calle y altura.
* Barrio.
* Comuna.
* N.º de Disposición y Resolución.
* Fecha de inicio.
* Vencimiento.
* Estado.

---

# Permisos de uso del espacio público — Área gastronómica

Información de los permisos de uso del espacio público para locales gastronómicos destinados a instalar:

* Decks.
* Mesas.
* Sillas.
* Elementos accesorios.

Estos elementos pueden ubicarse en:

* Veredas.
* Calzadas.

### Dataset

**Permisos de uso de espacio público y decks — CSV**

También disponible en XLSX.

El dataset contiene información sobre las autorizaciones otorgadas para el emplazamiento de áreas gastronómicas en el espacio público de la Ciudad Autónoma de Buenos Aires.

Incluye:

* Identificación del expediente electrónico.
* Datos del titular o solicitante.
* Nombre de fantasía del establecimiento.
* Localización territorial.
* Calle.
* Altura.
* Barrio.
* Comuna.
* Disposiciones.
* Resoluciones.
* Estado procesal del trámite.
* Plazos de vigencia temporal.

**Recurso:**

https://data.buenosaires.gob.ar/dataset/permisos-uso-espacio-publico-area-gastronomica/resource/4e430969-cc2f-4b42-8c3f-b30d00ec6ae7

---

# Trámites — En proceso

Está terminado el mapeo general de los requisitos dependiendo de la superficie a habilitar:

> **± 200 m²**

### Pendiente

Queda pendiente:

* Revisar cada requisito.
* Vincular cada requisito con la normativa correspondiente.
* Vincular documentación adicional cuando corresponda.

---

# Pasos previos

## Requisitos para ingresar a TAD

Para ingresar a la plataforma es necesario:

* Contar con usuario y clave miBA.

Para dudas sobre creación de cuenta o validación de identidad:

**Plataforma miBA**

También se puede consultar información sobre los niveles de seguridad de la clave miBA.

---

# Operación dentro de TAD

Para operar dentro de la plataforma:

1. Ingresar a la plataforma de Trámites a Distancia (TAD) con usuario y contraseña miBA.
2. Completar los datos personales.
3. Aceptar los términos y condiciones.

### Manual de usuario TAD

https://buenosaires.gob.ar/gcaba_historico/innovacionytransformaciondigital/tramites-distancia-tad

El manual se encuentra al final de la página.

---

# Trámites disponibles en TAD

Existen dos opciones de trámite:

## 1. Habilitación de actividad económica exprés

Debe tener una superficie total que **no supere los 200 m²**.

https://tad.buenosaires.gob.ar/tramitesadistancia/dctramite;idTipoTramite=2228;esTramiteExt=1;iniciaPasoCero=1

## 2. Habilitación de Actividad Económica

https://tad.buenosaires.gob.ar/tramitesadistancia/dctramite;idTipoTramite=2227;esTramiteExt=1;iniciaPasoCero=1

---

# Requisitos — Habilitación de Actividad Económica Exprés

## Requisitos obligatorios

El establecimiento:

* Debe tener una superficie total que no supere los 200 m².
* No debe comercializar explosivos, inflamables ni productos medicinales sin envasar.
* No debe estar ubicado en galerías, centros comerciales, paseos de compras, mercados o patios gastronómicos, estaciones de subte o tren, aeropuertos u otros complejos comerciales.
* No debe encontrarse en áreas especiales por ser históricas, culturales o ambientales, ni tener usos específicos establecidos en el Código Urbanístico, como áreas protegidas, patrimoniales o con restricciones particulares según ubicación.
* No debe estar en edificios catalogados por su valor histórico, arquitectónico o cultural ni en edificios con restricciones para su uso o modificación.
* Debe cumplir con las condiciones de accesibilidad establecidas en la normativa vigente.
* No debe tener entrepisos en las plantas a habilitar.
* No debe realizar actividades económicas que requieran la aplicación de normativas específicas, tales como farmacia, agencia de lotería, estudio profesional, entre otras.

## Pasos para realizar el trámite

### 1. Declarar la ubicación

Elegir un método para ingresar:

* Dirección.
* Número de partida.
* Datos catastrales.
* Ubicación especial.

### 2. Datos del titular o firmante

Ingresar el CUIT de la persona solicitante.

Puede tratarse de:

* Persona física.
* Persona jurídica.

### 3. Formularios del local

Completar:

* Datos del local.
* Conformidad de uso.
* Dimensiones.
* Tipo de superficie.
* Ventilación.
* Destino de uso.
* Otras características generales.

> **Importante:** esta información es vital para determinar si el local cumple con las normativas para la habilitación.

### 4. Rubros y actividades

Declarar:

* Rubro del negocio.
* Actividades que se realizarán en el local.

### 5. Confirmación

Revisar y verificar todos los datos antes de enviar el formulario.

Una vez completados todos los formularios, se generará automáticamente el:

> **Certificado de Aptitud Ambiental**

### Más información

https://buenosaires.gob.ar/tramites/habilitacion-de-actividad-economica-expres

---

# Requisitos — Habilitación de Actividad Económica

## Documentación requerida

### Formulario de conformación de la unidad de uso

Declaración Jurada donde se informa qué actividad comercial se desarrollará.

### Anexo Técnico

Debe estar firmado por un profesional responsable e incluir:

* Encomienda profesional con los datos correspondientes.
* Datos del profesional que firma.
* Información sobre la unidad de uso.
* Mixtura o área especial donde está ubicado el local.
* Croquis con la ubicación.
* Declaración Jurada donde se verifica el local.

### Consideraciones especiales

El profesional deberá considerar especialmente si el establecimiento:

* Está en galerías.
* Está en centros comerciales.
* Está en paseos de compras.
* Está en mercados.
* Está en patios gastronómicos.
* Está en estaciones de subte o tren.
* Está en aeropuertos.
* Está en otros complejos comerciales.
* Está en áreas especiales históricas, culturales o ambientales.
* Tiene usos específicos establecidos por el Código Urbanístico.
* Está en áreas protegidas o patrimoniales.
* Está en edificios catalogados por su valor histórico, arquitectónico o cultural.
* Está en edificios con restricciones para su uso o modificación.
* Pretende eximirse de condiciones de accesibilidad.

### Documentación adicional, cuando corresponda

La persona solicitante deberá presentar:

* Certificado de sobrecarga.
* Plano de Uso de Actividad Económica.
* Autorización de Emplazamiento.

> **Importante:** según la normativa vigente de la actividad económica que se quiera habilitar, se podrá solicitar documentación específica.

---

# Pasos para realizar el trámite

## 1. Iniciar la solicitud

Hacer clic en **“Iniciar trámite”**.

Acceder a la plataforma SSIT de la Agencia de Control Gubernamental utilizando usuario y contraseña miBA.

## 2. Nueva Autorización de Actividad Económica

Seleccionar:

> **Nueva Autorización de Actividad Económica**

## 3. Datos del titular o firmante

Ingresar el CUIT de la persona solicitante o firmante.

Puede tratarse de:

* Persona física.
* Persona jurídica.

## 4. Declarar la ubicación

Ingresar:

* Tipo de ubicación.
* Número de partida o matriz.
* Datos catastrales.
* Ubicación especial.
* Datos de contacto.

> **Importante:** al guardar la solicitud se generarán el **Número de Trámite** y el **Código de Seguridad**. Estos datos son indispensables para que el profesional pueda realizar el Anexo Técnico y certificarlo en su Consejo Profesional.

## 5. Solicitar el Certificado de Aptitud Ambiental

Para obtener esta certificación se debe ingresar a:

> **Impacto Ambiental — Certificado de Aptitud Ambiental (CAA)**

## 6. Finalización del trámite

La Dirección General de Habilitaciones y Permisos evaluará si el comercio cumple con:

* Requisitos.
* Documentación necesaria.

La Dirección podrá:

* Librar al uso.
* Aprobar.
* Observar.
* Rechazar la solicitud.

### En caso de ser librado al uso

Se podrá operar en el comercio y se enviará una oblea con un código QR para colocar en el local.

Cuando la lectura del código QR indique que se encuentra **librado al uso**, se tendrá acceso al:

> **Libro de Registro de Inspecciones Digital**

El acceso se realiza mediante usuario y clave miBA nivel 3.

> **Importante:** que el comercio esté librado al uso **no significa que cuente con la habilitación de actividad comercial**.

### Más información

https://buenosaires.gob.ar/tramites/autorizacion-de-actividades-economicas
