# TAREAS - Sistema de Gestión Inteligente (TECBA)

## BI, Data & Machine Learning

### 1. Identificación de fuentes de información potencialmente útiles para el caso piloto
* **IDECABA:** [https://idecaba.buenosaires.gob.ar/](https://idecaba.buenosaires.gob.ar/)
* **BA Data:** [https://data.buenosaires.gob.ar/dataset/](https://data.buenosaires.gob.ar/dataset/)
* **Ciudad 3D:** [https://ciudad3d.buenosaires.gob.ar/](https://ciudad3d.buenosaires.gob.ar/)
* **Documentación complementaria:** Cuadro de rubros habilitados en la Ciudad (`PE-DIS-MJGGC-DGIUR-1487-22-ANX.pdf`).

### 2. Análisis de estructura, disponibilidad y calidad de la información
A nivel de información urbanística se cuenta con la **Plancheta 12**, que señala en qué lugares se pueden construir o habilitar emprendimientos comerciales ligados a la gastronomía, sector correspondiente al caso piloto (abrir una cafetería en Av. Corrientes 2500). El rubro específico corresponde a **1.5 Alimentación general y gastronomía**.

### 3. Relación entre actividad, ubicación, territorio y trámites
El flujo secuencial propuesto es el siguiente:
1. La persona indica que quiere abrir una cafetería y consulta los trámites necesarios.
2. Mediante la herramienta de IA (chatbot), se le consulta la dirección exacta donde desea realizar la apertura.
3. A partir de la dirección, se vincula con la información urbanística correspondiente (ej. Plancheta 12 del código urbanístico).
4. La plataforma determina si el comercio puede instalarse en dicha ubicación, mostrando las actividades comerciales permitidas.
5. Una vez confirmada la factibilidad, se despliegan los pasos y trámites necesarios para avanzar con la gestión.

### 4. Campos o dimensiones comunes identificadas
1. Dirección
2. Latitud y longitud (para la georreferenciación en el mapa)
3. Área de uso de suelo (para verificar la habilitación del rubro)
4. SMP (Sección - Manzana - Parcela)
5. Partida horizontal (Unidad funcional a habilitar)
6. Rubro comercial

---

## Núcleo Funcional
Consultar qué quiero hacer y dónde $\rightarrow$ interpretar $\rightarrow$ integrar fuentes $\rightarrow$ relacionar actividad + territorio + trámites $\rightarrow$ organizar pasos $\rightarrow$ visualizar en mapa $\rightarrow$ responder con IA respaldada por información oficial.

### Flujo Operativo del MVP
Ingresar necesidad y ubicación $\rightarrow$ interpretar actividad y ubicación $\rightarrow$ consultar al menos 3 fuentes $\rightarrow$ integrar información territorial, de contexto y de trámites $\rightarrow$ visualizar ubicación en mapa $\rightarrow$ presentar requisitos, documentación y pasos $\rightarrow$ permitir preguntas mediante IA $\rightarrow$ mostrar las fuentes oficiales utilizadas.

---

## Fuentes de Información Oficiales
* **IDECABA:** [https://idecaba.buenosaires.gob.ar/](https://idecaba.buenosaires.gob.ar/)
* **BA Data:** [https://data.buenosaires.gob.ar/dataset/](https://data.buenosaires.gob.ar/dataset/)
* **Ciudad 3D:** [https://ciudad3d.buenosaires.gob.ar/](https://ciudad3d.buenosaires.gob.ar/)
* **Trámites GCBA:** [https://buenosaires.gob.ar/gobierno/tramites](https://buenosaires.gob.ar/gobierno/tramites)

---

## Caso Piloto MVP
* **Consulta de usuario:** *"Quiero abrir una cafetería en Av. Corrientes 2500. ¿Qué tengo que hacer?"*
* **Enlaces de referencia:**
  * [Trámites y Servicios GCBA - Ref. 83](https://buenosaires.gob.ar/inicio/tramites-y-servicios/83)
  * [Habilitación de Actividad Económica](https://buenosaires.gob.ar/tramites/habilitacion-de-actividad-economica)

---

## Marco Normativo
* **Ley 6.101** (Habilitaciones) y sus modificatorias.
* **Resolución 96/AGC/2025**.
* **Resolución 345/AGC/2021**.
* **Código Urbanístico** (Ley 6.099 y modificatorias).
* **Código de Edificación** (Ley 6.100 y modificatorias).

### Disposiciones Urbanísticas Relevantes
* **Áreas de Renovación Urbana linderas a Autopistas (RUA):** Zonas longitudinales destinadas a localizar usos comerciales y de equipamiento a escala vecinal, compatibles con el uso vial de la autopista y el área de mixtura adyacente. No se admite subdivisión parcelaria.
* **Área de Alta Mixtura de Usos del Suelo 4:** Áreas y corredores destinados a residencia, depósitos, equipamiento, servicios y comercios de afluencia masiva según el Cuadro de Usos del Suelo N° 3.3 (Ley 6.361). Se detallan superficies máximas, necesidad de consulta al Consejo "C", y requerimientos de estacionamiento, bicicletas y módulos de carga/descarga.
* **Rubro principal:** 1.5 Alimentación general y gastronomía.

### Restricciones (Rubros No Permitidos en la Zona de Aplicación)
Se permiten los usos de suelo del Cuadro N° 3.3 para el Área de Alta Mixtura de Usos del Suelo (4) **a excepción de**:
* **Categoría Comercial:** Comercio mayorista con/sin depósito; Materiales de Construcción Clase II y III.
* **Categoría Transporte:** Estación Intermedia; Garaje para camiones con/sin servicio y abastecimiento.
* **Categoría Depósitos:** Todos.
* **Categoría Diversiones Públicas, Cultura, Culto y Recreación:** Sala de loto/familiar/salón; Bingo; Calesita; Club Deportivo al aire libre; Cancha de Golf; Estudio de Televisión; Estación de Radio/Televisión; Locales de Baile Clase C; Polígono de Tiro.
* **Categoría Educación:** Todos.
* **Categoría Establecimientos de Sanidad:** Clínica Veterinaria; Servicios de traslado sanitario; Sanatorio; Maternidad; Clínica; Institutos privados con/sin internación; Hogares de Niñas, Niños y Adolescentes; Hospitales de todas las clases.
* **Categoría Servicios:** Escuela/Pensionado para Pequeños Animales; Empresas de Servicios de Seguridad (con/sin polígono de tiro).

*Nota para parcelas mayores a $2.500 \, \text{m}^2$: Al menos el veinte por ciento ($20\%$) de la superficie de suelo se destinará a uso comercial con acceso desde la vía pública, contemplando guarda/estacionamiento vehicular y espacio de carga y descarga según corresponda.*