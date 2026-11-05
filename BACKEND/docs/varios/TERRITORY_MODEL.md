# Modelo territorial del MVP

## Entidad canónica

El territorio se integra mediante `parcels.id` y `parcels.smp`.

```text
USIG
  ↓
SMP / lat-lon
  ↓
parcels
  ├── urban_parcel_rules
  ├── parcel_special_districts
  └── land_use_observations
```

`seccion`, `manzana` y `parcela` no se almacenan como columnas independientes. Cuando se necesite presentarlos, pueden derivarse del SMP o del dataset de origen durante una etapa de transformación específica.

## `urban_parcel_rules`

Mantiene únicamente:

| Campo | Uso |
|---|---|
| `parcel_id` | FK a la parcela territorial canónica |
| `source_version_id` | Proveniencia de la versión del Código Urbanístico |
| `uso_1`, `uso_2`, `uso_3` | Áreas de Mixtura de Usos |

Los distritos especiales se encuentran en `parcel_special_districts`, una fila por combinación de grupo/código. No hay columnas repetitivas `dist_1_* ... dist_4_*`.

## `land_use_observations`

Es información observacional, no normativa. Se relaciona con la parcela mediante `parcel_id` y conserva solo los atributos utilizados como contexto del MVP.

## Geocoding cache

`geocoding_cache` conserva `smp` porque puede llegar desde USIG antes de que la parcela correspondiente haya sido ingerida. Cuando la parcela existe, `resolved_parcel_id` establece la relación interna.

El payload original de USIG queda en `response_json`, evitando multiplicar columnas derivadas que solo sirven para reconstruir la respuesta del proveedor.

## Proveniencia

```text
sources
   ↓
source_versions
   ↓
source_resources
```

La base guarda el modelo operativo; los archivos originales permanecen fuera de PostgreSQL.
