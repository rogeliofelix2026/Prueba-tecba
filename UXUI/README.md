# UX/UI — Sistema de Gestión Inteligente

## Trabajo del área

El área **UX/UI** será responsable de definir la experiencia y la interfaz de usuario del Sistema de Gestión Inteligente.

Link https://www.figma.com/design/NPLuJrXhly0yruwQR5S5VD/INNOVA?node-id=80-1636&t=Gek9tKlTjZiQG0gA-0

El trabajo inicial incluye:

* Analizar las necesidades del usuario del MVP.
* Definir el flujo principal de navegación.
* Diseñar las pantallas necesarias para el MVP.
* Definir componentes y criterios visuales de la interfaz.
* Diseñar la experiencia relacionada con la consulta de información.
* Considerar la visualización de información territorial y el mapa.
* Documentar los diseños y criterios necesarios para el desarrollo.
* Trabajar en conjunto con Frontend y QA.

Los diseños y decisiones de UX/UI podrán evolucionar durante el desarrollo del MVP.

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

### 2. Ir a la rama de UX/UI

```bash
git checkout uxui
```

Si la rama todavía no existe:

```bash
git checkout -b uxui
git push -u origin uxui
```

### 3. Realizar el trabajo

Agregar o modificar los archivos correspondientes al área UX/UI.

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
git commit -m "Agrega flujo inicial del MVP"
```

### 6. Subir los cambios

```bash
git push origin uxui
```

### 7. Crear Pull Request

Desde GitHub:

**Pull requests → New pull request**

Seleccionar:

```text
base: main
compare: uxui
```

Agregar una breve descripción y crear el Pull Request.

### 8. Integración

El cambio será revisado por el equipo y, una vez aprobado, se integrará a `main`.

**No realizar Push directamente sobre `main`.**
