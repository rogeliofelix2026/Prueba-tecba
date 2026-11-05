# Mapa de Usos CABA

Consulta de habilitación por rubro y dirección según el Código Urbanístico de la Ciudad de Buenos Aires.

Elegís qué querés habilitar, la calle, la altura y la superficie. El mapa detecta el Área de Mixtura de Usos de esa cuadra y te dice si se puede habilitar, con qué condiciones, si necesita aprobación del Consejo o si no se puede. También pinta toda la Ciudad según el rubro elegido y calcula qué porcentaje de la superficie lo admite.

## Contenido

| Archivo | Qué es |
|---|---|
| `index.html` | La aplicación completa (incluye el Cuadro de Usos N° 3.3) |
| `cu_raster.png` | Áreas de Mixtura de las 318.127 parcelas, en una imagen de 4,5 m por píxel |
| `calles.json` | Callejero de la Ciudad, para ubicar direcciones |
| `plano.jpg` | Plano oficial de Edificabilidad y Usos (Anexo IV) |
| `datos/cuadro_usos_3_3.csv` / `.json` | Cuadro de Usos 3.3 en formato abierto |

## Publicar en GitHub Pages

1. Creá un repositorio nuevo en GitHub (por ejemplo `mapa-usos-caba`), público.
2. Subí **todo el contenido de esta carpeta** a la raíz del repositorio: en la página del repo, *Add file → Upload files*, arrastrá los archivos y la carpeta `datos`, y confirmá con *Commit changes*.
3. Andá a *Settings → Pages*. En *Build and deployment*, elegí *Deploy from a branch*, rama `main` y carpeta `/ (root)`. Guardá.
4. En uno o dos minutos el sitio queda en `https://TU-USUARIO.github.io/mapa-usos-caba/`.

La aplicación tiene que abrirse desde ese enlace (o desde cualquier servidor web). Si abrís `index.html` con doble clic desde tu computadora, el navegador bloquea la carga de `calles.json` y de la capa de mixtura.

Para probarla en tu computadora antes de subirla: abrí una terminal en esta carpeta, ejecutá `python3 -m http.server` y entrá a `http://localhost:8000`.

## Fuentes

- Código Urbanístico, Ley 6.099 y modificatorias. Cuadro de Usos del Suelo N° 3.3, texto ordenado al 31/12/2024.
- Capa parcelaria del Código Urbanístico y callejero: Buenos Aires Data (data.buenosaires.gob.ar).
- Planchetas de Edificabilidad y Usos, Anexo IV, actualizado al 31/12/2024.

## Aviso

Herramienta orientativa. No reemplaza el Certificado Urbanístico ni la consulta al organismo competente. Las direcciones se ubican a mitad de cuadra, y los distritos especiales (APH, U, UP, etc.) tienen normativa propia.
