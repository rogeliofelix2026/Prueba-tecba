# DATA — Sistema de Gestión Inteligente

## Trabajo del área

El área **DATA** será responsable del trabajo relacionado con los datos y las fuentes de información utilizadas por el Sistema de Gestión Inteligente.

El trabajo inicial incluye:

* Identificar y analizar las fuentes de información necesarias para el MVP.
* Analizar los formatos y estructura de los datos.
* Preparar y organizar los datos que serán utilizados por el sistema.
* Participar en la integración de las fuentes seleccionadas.
* Validar la consistencia de los datos utilizados.
* Colaborar con Backend, Frontend, UX/UI y QA cuando sea necesario.

El alcance y las herramientas específicas del área se irán definiendo durante el desarrollo del MVP.

---

## Trabajo con GitHub desde VS Code

Cada integrante debe trabajar en su **rama**, evitando realizar cambios directamente sobre `main`.

### 1. Actualizar el proyecto

Abrir el proyecto en VS Code y abrir:

**Terminal → New Terminal**

```bash
git checkout main
git pull origin main
```

### 2. Ir a la rama de Data

```bash
git checkout data
```

Si la rama todavía no existe:

```bash
git checkout -b data
git push -u origin data
```

### 3. Realizar el trabajo

Agregar o modificar los archivos correspondientes al área DATA.

### 4. Revisar los cambios

```bash
git status
```

### 5. Guardar los cambios

```bash
git add .
git commit -m "Descripción breve del cambio"
```

Ejemplo:

```bash
git commit -m "Agrega análisis inicial de fuentes"
```

### 6. Subir los cambios

```bash
git push origin data
```

### 7. Crear Pull Request

Desde GitHub:

**Pull requests → New pull request**

Seleccionar:

```text
base: main
compare: data
```

Agregar una breve descripción y crear el Pull Request.

### 8. Integración

El cambio será revisado por el equipo y, una vez aprobado, se integrará a `main`.

**No realizar Push directamente sobre `main`.**
