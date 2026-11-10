# FRONTEND — Sistema de Gestión Inteligente

## Trabajo del área

El área **Frontend** será responsable del desarrollo de la interfaz web del Sistema de Gestión Inteligente.

El trabajo inicial incluye:

* Desarrollar la interfaz del MVP.
* Implementar las pantallas y componentes definidos por UX/UI.
* Integrar el frontend con los servicios del backend.
* Mostrar la información de actividades, trámites, requisitos y ubicación.
* Implementar la visualización territorial y el mapa definido para el MVP.
* Mantener una interfaz responsive y usable.

### Base técnica inicial

La carpeta `app/` contiene la base técnica inicial proporcionada por el equipo Frontend.

La base fue iniciada con:

* Next.js
* React
* TypeScript
* Tailwind CSS

Esta base corresponde al punto de partida técnico del proyecto y no representa todavía la plataforma terminada.

---

## Trabajo con GitHub desde VS Code

Cada integrante debe trabajar en su **rama**, evitando realizar cambios directamente sobre `main`.

### 1. Actualizar el proyecto

Abrir el proyecto en VS Code y abrir:

**Terminal → New Terminal**

Ejecutar:

```bash
git checkout main
git pull origin main
```

### 2. Ir a la rama de Frontend

```bash
git checkout frontend
```

Si la rama todavía no existe:

```bash
git checkout -b frontend
git push -u origin frontend
```

### 3. Realizar el trabajo

Modificar o agregar los archivos correspondientes al área Frontend.

### 4. Revisar los cambios

```bash
git status
```

### 5. Guardar los cambios en Git

```bash
git add .
git commit -m "Descripción breve del cambio"
```

Ejemplo:

```bash
git commit -m "Agrega pantalla inicial del MVP"
```

### 6. Subir los cambios

```bash
git push origin frontend
```

### 7. Crear Pull Request

Desde GitHub:

**Pull requests → New pull request**

Seleccionar:

```text
base: main
compare: frontend
```

Agregar una breve descripción de lo realizado y crear el Pull Request.

### 8. Integración

El cambio será revisado por el equipo y, una vez aprobado, se integrará a `main`.

**No realizar Push directamente sobre `main`.**
