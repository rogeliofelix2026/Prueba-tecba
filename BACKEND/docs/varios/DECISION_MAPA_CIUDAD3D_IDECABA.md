# Decisión de mapa para el MVP — Ciudad 3D, IDECABA y mapa propio

Fecha de investigación: 13/10/2026.

## Decisión

**Para semana 2/3: mostrar un marcador en Leaflet o MapLibre y postergar el contorno catastral propio.** Se puede incluir un enlace externo a Ciudad 3D cuando resulte útil. No basar el MVP en un iframe no verificado ni asumir que Ciudad 3D devolverá a SGI un GeoJSON de la parcela consultada.

El requisito TECBA para el MVP exige visualización de ubicación y al menos una capa o información territorial relevante. Puede demostrarse ahora con el marcador, junto con el contexto urbanístico y los datos territoriales disponibles en el panel. Para afirmar que el mapa muestra una capa territorial, el Frontend debe visualizar datos/capa reales y citar su fuente; el texto de mixtura fuera del mapa no debería describirse como una capa cartográfica.

## ¿Qué es Ciudad 3D y por qué no elimina automáticamente nuestra necesidad de geometría?

La documentación oficial del GCBA describe Ciudad 3D como una plataforma de visualización 2D/3D del Código Urbanístico y de información por parcela. La descripción de arquitectura indica que el frontend consume APIs para representar información parcelaria. El repositorio público de GCBA documenta APIs de Catastro, Ciudad 3D y USIG, y tiles vectoriales/servicios OGC; no expone en el README un contrato público estable de deep link/iframe para que otra aplicación mande un SMP y reciba directamente el polígono parcelario.

Por tanto, Ciudad 3D es una aplicación completa (visualizador + servicios + datos), no un proveedor universal que dibuja cualquier parcela a partir de cualquier coordenada. Reutilizar o integrar su API requeriría confirmar endpoints soportados, autorización/uso, estabilidad, formato de respuesta, CORS y términos. No se debe raspar el HTML, replicar llamadas internas no documentadas ni depender de un URL interno no confirmado.

En el MVP sí puede ofrecerse como **enlace externo de consulta complementaria**:

- Sitio oficial: https://ciudad3d.buenosaires.gob.ar/
- Código fuente del frontend publicado por GCBA: https://github.com/gcba/Ciudad-3D
- Información oficial del producto: https://buenosaires.gob.ar/gcaba_historico/noticias/ciudad-3d-suma-nuevas-herramientas-para-seguir-impulsando-el-desarrollo

No se confirmó que la plataforma tenga un patrón de URL profundo estable que enfoque cualquier SMP específico; no prometer esa experiencia hasta probarla y documentarla.

## Alternativas

### A. Leaflet/MapLibre + coordenadas (recomendado ahora)

- Fácil de integrar con `location.latitude`/`longitude`.
- No requiere geometría parcelaria para colocar un marcador.
- Se puede añadir un enlace a USIG o Ciudad 3D.
- Limitación: no dibuja el lindero exacto de la parcela por sí solo.

### B. Leaflet/MapLibre + WMS externo de IDECABA

IDECABA publica geoservicios WMS para visualización de información geográfica y WFS para consultar/descargar atributos y datos. Un WMS puede dibujar una capa de parcelas desde otro servidor sin que SGI copie sus polígonos a su propia base, si el catálogo confirma que existe una capa adecuada, cubre la ubicación, acepta el consumo web y los términos/atribución son compatibles.

Estado de esta investigación: la página pública de Geoservicios confirma la disponibilidad de WMS/WFS, pero la consulta de catálogo realizada no verificó un layer público concreto de límites parcelarios apto para nuestro caso. No implementar una URL o nombre de layer supuesto. Próximo paso es inspeccionar el catálogo, pedir `GetCapabilities` al servicio pertinente y validar una parcela de prueba.

Portal y catálogo: https://idecaba.buenosaires.gob.ar/Recursos/Geoservicios

### C. WFS externo o descarga oficial de Parcelas + geometría propia

- WFS puede devolver geometría y atributos consultables, cuando la capa exista y el servicio permita esa operación.
- Alternativamente, el dataset oficial de Parcelas CABA puede procesarse y almacenar solamente las geometrías que realmente se necesiten en `parcel_geometries`.
- Es la opción más verificable si el sistema debe relacionar parcela, regla normativa y su origen en una única respuesta, aunque requiere integrar la capa correcta y mantener su versión.

### D. Embed de Ciudad 3D

No recomendado hasta verificar que exista soporte oficial de embedding. Un iframe puede mostrar otra web si ésta lo permite, pero no resuelve automáticamente navegación hacia el SMP de la consulta, sincronización de estado, accesibilidad, CORS de API, ni extracción de geometrías. Además, la aplicación embebida puede actualizar su URL/contrato fuera de nuestro control.

## Próxima tarea de Data/Backend si se necesita una capa territorial cartográfica en el sprint

1. Abrir el catálogo WMS/WFS de IDECABA y ubicar el servicio relacionado con catastro/parcelas.
2. Consultar `GetCapabilities` del servicio documentado; verificar `CRS`, nombre real de capa, cobertura y formato.
3. Probar en un cliente cartográfico la parcela de referencia Corrientes 2880 y comprobar que el lindero se alinea con las coordenadas de USIG.
4. Comprobar política de acceso, atribución, cuotas, CORS y estabilidad antes de integrarlo en la web.
5. Si sólo se necesita visualizar la capa, preferir WMS para no descargar ni mantener geometrías propias. Si hace falta seleccionar features, consultar atributos o vincular SMP a una regla, evaluar WFS o la descarga oficial.
6. Mantener una degradación clara: si el proveedor de la capa cae, el marcador y el resultado tabular continúan funcionando.

## Fuentes investigadas

- GCBA, explicación de Ciudad 3D: https://buenosaires.gob.ar/gcba_historico/noticias/ciudad-3d-suma-nuevas-herramientas-para-seguir-impulsando-el-desarrollo
- Repositorio de frontend Ciudad 3D: https://github.com/gcba/Ciudad-3D
- Portal IDECABA y geoservicios: https://idecaba.buenosaires.gob.ar/ y https://idecaba.buenosaires.gob.ar/Recursos/Geoservicios
- TECBA, Documento Sistema de Gestión Inteligente, apartados de mapa interactivo, stack y planificación semanal.
