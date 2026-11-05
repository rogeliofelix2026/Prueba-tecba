# Geometría parcelaria bajo demanda — v0.3.4

## Qué hace y qué no hace USIG

La geocodificación de USIG devuelve dirección normalizada, coordenadas, datos útiles y SMP. La documentación pública de GeoCoder 2.2 describe `/geocoding`, `/reversegeocoding` y `/smp`; no documenta un endpoint de polígono parcelario. La geometría debe leerse de una fuente que realmente publique polígonos, en este caso **Parcelas (GeoJSON/SHP)** de Buenos Aires Data.

Fuente oficial:

- https://data.buenosaires.gob.ar/dataset/juqdkmgo-156/resource/8d8ffe66-9eb9-4f12-8f23-e1586a2d888d
- https://ws.usig.buenosaires.gob.ar/geocoder/2.2

## Configurar una fuente local

1. Descargá el recurso oficial **Parcelas (SHP)** o **Parcelas (GeoJSON)**. No lo importes completo a `public.parcel_geometries`.
2. Para consultas eficientes repetidas, se recomienda convertirlo a un GeoPackage e indexar el atributo SMP. Con GDAL/OGR instalado:

```bash
ogr2ogr -f GPKG data/parcelas.gpkg data/parcelas.geojson -nln parcelas
sqlite3 data/parcelas.gpkg "CREATE INDEX IF NOT EXISTS idx_parcelas_smp ON parcelas(smp);"
```

Si partís del ZIP SHP, indicá a `ogr2ogr` el `.shp` extraído y verificá cuál es el nombre exacto del campo SMP (`smp` es el nombre publicado en el recurso GeoJSON). En producción no conviene consultar un GeoJSON grande sin índice en cada miss. El proveedor hace una única consulta `smp IN (...)` con valores exactos (sin aplicar `UPPER(smp)`), para evitar escanear la fuente repetidas veces y permitir que un índice de GeoPackage pueda usarse.

3. Instalá las dependencias geoespaciales incluidas en `requirements.txt`.
4. Configurá en `.env`:

```dotenv
PARCEL_GEOMETRY_SOURCE_PATH=data/parcelas.gpkg
PARCEL_GEOMETRY_SOURCE_LAYER=parcelas
PARCEL_GEOMETRY_SOURCE_VERSION_ID=2
PARCEL_GEOMETRY_CACHE_ON_RESOLVE=true
```

`PARCEL_GEOMETRY_SOURCE_LAYER` debe coincidir con la capa real del GeoPackage. `PARCEL_GEOMETRY_SOURCE_VERSION_ID` debe ser el ID de `source_versions` que pertenece a `sources.code = 'parcelas'` y representa ese archivo; el `2` del ejemplo es el ID observado en el diagnóstico compartido y se debe confirmar antes de usarlo. Es obligatorio cuando se configura una fuente local: el backend no deduce la versión del archivo ni etiqueta silenciosamente geometrías antiguas con el último `source_version_id` activo. Si no se configura, se devuelve `PARCEL_GEOMETRY_SOURCE_VERSION_NOT_CONFIGURED`; si el ID no pertenece a `sources.code='parcelas'`, no se guarda la geometría bajo una versión distinta. También se puede configurar una ruta absoluta montada en el contenedor. La fuente debe corresponder a una versión catastral que el equipo considere válida.

## Cómo se integra al flujo

- Primero, USIG normaliza/geocodifica la dirección y determina el SMP.
- PostgreSQL resuelve `parcels`, barrio/comuna y `urban_parcel_rules` por ese SMP.
- Si la parcela no tiene geometría cacheada, el proveedor lee **solo el feature de ese SMP** desde la fuente configurada.
- La aplicación inserta/actualiza únicamente esa geometría en `public.parcel_geometries`, con `source_version_id` de `sources.code='parcelas'`, `loaded_at` y checksum cuando la columna existe.
- La respuesta se vuelve a leer de PostGIS. `geometry_source_version_id` permite comprobar la procedencia. `geometry` solo se incluye en el JSON cuando `include_geometry=true`; la caché no obliga a serializar un polígono grande en respuestas de texto.

Si la fuente no está configurada, la consulta principal sigue resolviendo por SMP y atributos tabulares, pero advierte `PARCEL_GEOMETRY_SOURCE_NOT_CONFIGURED`. Si falta el ID de versión asociado al archivo, avisa `PARCEL_GEOMETRY_SOURCE_VERSION_NOT_CONFIGURED`. Si la fuente no contiene el SMP o devuelve una geometría ambigua/inválida, se conserva el resultado territorial y se agrega una advertencia. El servicio no crea un polígono sintético a partir del punto de geocodificación.

## Cuándo pasa a PostgreSQL

Solo al primer acceso a una parcela sin geometría cacheada, o cuando la fuente/versionado cambie y se fuerce una actualización futura. Los 318.046 registros de `parcels` no se copian automáticamente. La tabla `parcel_geometries` mantiene la clave única por `parcel_id`, por lo que múltiples consultas a la misma parcela reutilizan el polígono.

## Nulls legítimos

- `query.address_extracted`: null si el usuario ya mandó `address_input` explícitamente.
- `surface_m2`, `street_width_m`, `frontage_m`: null si el usuario no los informa y la fuente no los provee. El área del lote/parcela no equivale a la superficie comercial habilitable.
- `territory.parcel.geometry`: null de forma intencional si `include_geometry=false`; revisá `geometry_status`, `geometry_cached` y `geometry_source_version_id`.
- `territory.land_use=[]`: no hay datos cargados en `land_use_observations` en el diagnóstico compartido. RUS es contexto observacional opcional, no la fuente normativa que decide por sí sola la compatibilidad. La compatibilidad principal usa `urban_parcel_rules` + `activity_use_rules`.
- `annex_ii_activity_name_verified`: null no impide usar el tipo de trámite si el mapeo aprobado existe, pero conviene completar ese campo para auditoría.

La clasificación de trámite no equivale a una habilitación concedida. La fuente oficial indica que DDRR con/sin planos queda sujeta a revisión técnica final y que las licencias no permiten comenzar hasta la aprobación oficial.
