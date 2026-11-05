# Fix de resolución y caché de SMP

## Causa

USIG puede geocodificar una altura que no corresponde a una puerta oficial porque el geocoder usa interpolación entre puertas existentes. En esos casos, `/smp` puede responder `ErrorPuertaInexistente` aunque la geocodificación de la dirección haya sido exitosa.

Ejemplo del caso probado:

- Entrada: `Corrientes 2100`
- Calle normalizada: `CORRIENTES AV.` (`3174`)
- Altura normalizada: `2100`
- `/smp?cod_calle=3174&altura=2100`: `ErrorPuertaInexistente`
- Reverse geocoding: `puerta = CORRIENTES AV. 2092`
- Reverse geocoding: `parcela = 09-061-013`

## Resolución implementada

El backend mantiene el flujo existente y agrega fallback únicamente cuando el SMP directo no es válido:

1. Intenta `/smp` con la altura solicitada.
2. Si no obtiene un SMP válido, toma la puerta oficial devuelta por `reverse_geocoding.puerta` y vuelve a consultar `/smp` con esa altura.
3. Si ese segundo intento tampoco resuelve el SMP, usa `reverse_geocoding.parcela` siempre que tenga formato SMP válido.
4. El valor bruto original de `USIG` continúa disponible en `usig_raw.smp`.
5. La procedencia de la resolución queda registrada en `usig_raw.smp_resolution`.

## Compatibilidad con caché existente

Las filas antiguas con `smp = NULL` pero con una `reverse_geocoding.parcela` válida se reparan automáticamente al leerlas.

Además se incluye una migración SQL que permite reparar esas filas en lote sin llamar nuevamente a USIG.

## Pruebas

La suite pasa completa:

`24 passed`

También se agregó cobertura específica para:

- SMP directo válido.
- Fallback por puerta oficial.
- Fallback final por parcela.

## Resultado esperado para `Corrientes 2100`

```json
{
  "smp": "09-061-013",
  "usig_raw": {
    "smp": {
      "tipo_resultado": "ErrorPuertaInexistente"
    },
    "smp_resolution": {
      "status": "resolved",
      "source": "usig_smp_official_door",
      "requested_height": 2100,
      "official_door_height": 2092
    }
  }
}
```
