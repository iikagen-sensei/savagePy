# Manual de plantillas Word (docxtpl)

Las plantillas `.docx` funcionan igual que los templates HTML de WeasyPrint: tú diseñas el aspecto en Word y el sistema rellena los datos automáticamente. Puedes editar el estilo cuando quieras y el documento generado reflejará los cambios.

---

## Cómo funciona

1. El sistema lee la plantilla `templates/documents/<nombre>_template.docx`
2. Sustituye los marcadores `{{ }}` con los datos reales de NocoDB
3. Repite los bloques `{% for %}` una vez por cada elemento
4. Devuelve el `.docx` generado para descargar

El motor es **docxtpl** (versión ≥ 0.16), que usa la misma sintaxis que Jinja2.

El botón **↓ Word** aparece automáticamente en la interfaz para cualquier documento que tenga su `_template.docx` correspondiente en `templates/documents/`.

---

## Sintaxis de marcadores

### Variables simples
```
{{ entrada.nombre }}
{{ entrada.descripcion }}
{{ titulo }}
```
El texto del marcador se sustituye por el valor. El **estilo del párrafo se conserva** — si el párrafo tenía fuente roja de 14pt, el resultado también la tendrá.

### Bucles
```
{% for bloque in bloques %}
    ... contenido que se repite ...
{% endfor %}
```
Los párrafos que contienen solo `{% for %}` o `{% endfor %}` **desaparecen** del resultado — no dejan líneas en blanco. Todo lo que esté entre ellos se repite una vez por cada elemento.

### Condicionales
```
{% if entrada.fuente %}
{{ entrada.fuente }}
{% endif %}
```
Si la condición es falsa, los párrafos intermedios no aparecen en el resultado.

### Combinar texto fijo y variable en un párrafo
```
Fuente: {{ entrada.fuente }}
```
El estilo del párrafo completo se aplica a todo el resultado.

---

## Dos formas de acceder a los datos

Cada `entrada` dentro de `bloque.entradas` tiene **dos tipos de campos**:

### Campos formateados (preparados por el sistema)
Listos para mostrar directamente, con etiqueta incluida o combinando varios campos de NocoDB:
```
{{ entrada.nombre }}          → "Armadura (Armor)"
{{ entrada.coste_label }}     → "Coste: 2 PP"
{{ entrada.fuente }}          → "SWADE p.155"
```

### Campos en crudo (tal cual vienen de NocoDB)
Los nombres de campo exactos de la base de datos, sin formatear:
```
{{ entrada.name }}            → "Armadura"
{{ entrada.name_original }}   → "Armor"
{{ entrada.cost }}            → "2"
{{ entrada.page_no }}         → "155"
```

Puedes mezclar ambos en la misma plantilla:
```
{{ entrada.cost }} Puntos de Poder    ← tú decides el texto
{{ entrada.coste_label }}             ← ya viene como "Coste: 2 PP"
```

---

## Estructura de datos disponible

### Variables de nivel superior (todos los templates)

| Variable | Contenido |
|---|---|
| `{{ titulo }}` | Nombre del documento ("Poderes", "Ventajas"…) |
| `{{ view_name }}` | Nombre de la vista de NocoDB seleccionada |
| `{{ bloques }}` | Lista de grupos (por rango, tipo…) con entradas formateadas |
| `{{ powers }}` / `{{ edges }}` / `{{ hindrances }}` | Lista completa en crudo sin agrupar |

Cada `bloque` dentro de `bloques`:

| Variable | Contenido |
|---|---|
| `{{ bloque.categoria }}` | Nombre del grupo ("Novato", "Mayor"…) |
| `{{ bloque.entradas }}` | Lista de entradas del grupo |

---

### Poderes (`powers_template.docx`)

Cada `entrada` dentro de `bloque.entradas`:

| Variable | Tipo | Contenido / Ejemplo |
|---|---|---|
| `{{ entrada.nombre }}` | formateado | `Armadura (Armor)` |
| `{{ entrada.coste_label }}` | formateado | `Coste: 2 PP` — vacío si no tiene |
| `{{ entrada.alcance_label }}` | formateado | `Alcance: Personal` — vacío si no tiene |
| `{{ entrada.duracion_label }}` | formateado | `Duración: 3 r.` — vacío si no tiene |
| `{{ entrada.fuente }}` | formateado | `SWADE p.155` |
| `{{ entrada.descripcion }}` | formateado | texto descriptivo completo |
| `{{ entrada.modificadores }}` | formateado | lista de modificadores — ver abajo |
| `{{ entrada.name }}` | crudo | `Armadura` |
| `{{ entrada.name_original }}` | crudo | `Armor` |
| `{{ entrada.rank_name }}` | crudo | `Novato` |
| `{{ entrada.cost }}` | crudo | `2` |
| `{{ entrada.range_roh }}` | crudo | alcance traducido |
| `{{ entrada.duration }}` | crudo | `3 r.` |
| `{{ entrada.page_no }}` | crudo | `155` |

Cada `m` dentro de `entrada.modificadores`:

| Variable | Contenido |
|---|---|
| `{{ m.titulo }}` | Nombre del modificador (+ coste entre paréntesis) |
| `{{ m.descripcion }}` | Descripción del modificador |

---

### Ventajas (`edges_template.docx`)

Cada `entrada` dentro de `bloque.entradas`:

| Variable | Tipo | Contenido |
|---|---|---|
| `{{ entrada.nombre }}` | formateado | nombre (+ original si existe) |
| `{{ entrada.requisitos_label }}` | formateado | `Requisitos: ...` — vacío si no tiene |
| `{{ entrada.fuente }}` | formateado | libro y página |
| `{{ entrada.descripcion }}` | formateado | descripción |
| `{{ entrada.title }}` | crudo | nombre en castellano |
| `{{ entrada.name_original }}` | crudo | nombre original |
| `{{ entrada.type }}` | crudo | tipo/categoría |
| `{{ entrada.requirements }}` | crudo | requisitos sin formatear |
| `{{ entrada.page_no }}` | crudo | número de página |

---

### Desventajas (`hindrances_template.docx`)

Cada `entrada` dentro de `bloque.entradas`:

| Variable | Tipo | Contenido |
|---|---|---|
| `{{ entrada.nombre }}` | formateado | nombre (+ original si existe) |
| `{{ entrada.fuente }}` | formateado | libro y página |
| `{{ entrada.descripcion }}` | formateado | descripción |
| `{{ entrada.Nombre }}` | crudo | nombre en castellano |
| `{{ entrada.name_original }}` | crudo | nombre original |
| `{{ entrada.type }}` | crudo | Mayor / Menor |
| `{{ entrada.page_no }}` | crudo | número de página |

---

## Iterar sin agrupación

Si no quieres la agrupación por categoría y prefieres recorrer todos los elementos directamente:

```
{% for p in powers %}
{{ p.name }}
{{ p.description }}
{% endfor %}
```

---

## Editar el estilo de una plantilla

1. Abre el `.docx` en Word
2. Verás los marcadores (`{{ entrada.nombre }}`, `{% for ... %}`, etc.) como texto normal
3. Selecciona el párrafo cuyo estilo quieres cambiar
4. Cambia la fuente, tamaño, color, sangría, espaciado… lo que quieras
5. Guarda el archivo **sin cambiar el texto del marcador**
6. La próxima descarga usará el nuevo estilo

Los párrafos con `{% for %}` y `{% endfor %}` desaparecen del resultado, así que su estilo no importa — puedes ponerlos en gris pequeño para que no molesten visualmente.

---

## Añadir una nueva plantilla Word

1. Crea `templates/documents/<doc_id>_template.docx` donde `doc_id` es el identificador del documento (`powers`, `edges`, `bestiary_mobile`…)
2. El botón **↓ Word** aparecerá automáticamente en la interfaz al reiniciar el servidor
3. Si el documento necesita preparación de datos especial, añade un `build_<doc_id>_context()` en `docx_generator.py`; si no, el sistema pasa los datos en crudo

---

## Notas importantes

- **No cambies el texto de los marcadores** — puedes cambiar el estilo del párrafo pero no el texto `{{ entrada.nombre }}`.
- **Variables vacías** muestran texto vacío pero el párrafo sigue apareciendo. Usa `{% if %}` si quieres que desaparezca.
- **Los saltos de línea** dentro de una variable se convierten en saltos de línea en Word automáticamente.
- **Tablas**: docxtpl soporta repetir filas de tabla con `{% for %}` dentro de una celda. Consulta la documentación oficial si necesitas layouts tabulares.
