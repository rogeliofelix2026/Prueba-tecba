# TAREAS - BI, Data & Machine Learning (Semana 1)

## 1. Análisis de las fuentes

* **IDECABA:** <https://idecaba.buenosaires.gob.ar/> $\rightarrow$ **(SE DESCARTA)**
* **BA Data:** <https://data.buenosaires.gob.ar/dataset/> $\rightarrow$ **(QUEDA)**
  * Datasets específicos a revisar:
    * [Permisos de uso de espacio público - Área gastronómica](https://data.buenosaires.gob.ar/dataset/permisos-uso-espacio-publico-area-gastronomica)
    * [Oferta de establecimientos gastronómicos](https://data.buenosaires.gob.ar/dataset/oferta-establecimientos-gastronomicos)
* **Ciudad 3D:** <https://ciudad3d.buenosaires.gob.ar/> $\rightarrow$ **(QUEDA)**
* **Cuadro de rubros habilitados en la Ciudad:** `PE-DIS-MJGGC-DGIUR-1487-22-ANX.pdf` $\rightarrow$ **(QUEDA)**

## 2. Identificación de variables territoriales, de actividad y de trámites

* **Variables territoriales:** Dirección, latitud, longitud, Sección-Manzana-Parcela (SMP), y usos de suelo.
* **Variables de actividad:** Cuadro de usos del suelo.
* **Variables de trámites:** Alta de actividades económicas, transmisión, redistribución de usos, ampliación y/o disminución de rubros y/o superficie, revocación y exención de autorización.

## 3. Primeras transformaciones y relaciones

1. **Geolocalización:** A partir de la dirección y la altura provistas por el usuario, se obtendrán la latitud y longitud para ubicar el punto geográfico en el mapa.
2. **Análisis de factibilidad:** Se identificará el área de uso correspondiente para determinar qué rubros están permitidos y validar si el rubro consultado por el ciudadano es apto para esa ubicación.
3. **Orientación de trámites:** Finalmente, se estructurará y presentará toda la información necesaria para que el usuario pueda iniciar su trámite correspondiente.

## 4. Documentación de problemas de calidad o disponibilidad

* **Inconsistencias de rubros:** El principal inconveniente detectado es que las nomenclaturas de los rubros a veces no coinciden exactamente con el cuadro de usos, dificultad que se planea resolver mediante una tabla de equivalencias.
* **Complejidad territorial:** La determinación automática de las áreas de uso y su correcta representación visual en el mapa también representan un desafío técnico a superar.

## Pendientes de GitHub (A chequear estado)

* [Issue #56](https://github.com/InnovaLab-2C-2026-Equipo-7/sistema-gestion-inteligente/issues/56)
* [Issue #57](https://github.com/InnovaLab-2C-2026-Equipo-7/sistema-gestion-inteligente/issues/57)