# Manual para añadir nuevos documentos PDF

Añadir un documento PDF al sistema son tres pasos: registrarlo en `app.py`, crear el template HTML en `templates/` y ajustar el CSS para el tamaño de página. No hay que tocar ningún otro archivo.

---

## Paso 1 — Registrar el documento en `app.py`

Abre `app.py` y localiza el diccionario `DOCUMENTS`. Añade una entrada en la tabla que corresponda a los datos que quieres mostrar:

```python
DOCUMENTS = {
    "power": {
        "label": "Poderes",
        "icon": "✦",
        "docs": {
            "powers":           {...},
            "cards_mobile":     {...},
            "cards_tablet":     {          # ← nuevo documento
                "label": "Cartas Tablet",
                "icon":  "📱",
                "template": "power_cards_tablet.html",
                "data_key": "powers",
            },
        }
    },
    ...
}
```

Los campos de cada documento:

| Campo | Descripción |
|---|---|
| `label` | Nombre que aparece en la interfaz |
| `icon` | Emoji que aparece junto al nombre |
| `template` | Nombre del archivo HTML en `templates/` |
| `data_key` | Nombre de la variable con la que el template recibe los datos |

**`data_key` según la tabla:**

| Tabla (`DOCUMENTS` key) | `data_key` habitual |
|---|---|
| `power` | `"powers"` |
| `edge` | `"edges"` |
| `hindrance` | `"hindrances"` |
| `bestiary` | `"creatures"` |

Una vez añadido, al reiniciar el servidor aparecerá en la interfaz con los botones Ver / ↓ PDF automáticamente.

---

## Paso 2 — Crear el template HTML

Crea `templates/<nombre>.html`. Lo más fácil es copiar uno existente como base:

```bash
cp templates/power_cards_mobile.html templates/power_cards_tablet.html
```

### Estructura básica

```html
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <style>
    @page {
      size: 148mm 210mm;   /* ← tamaño de página */
      margin: 0;
    }
    /* ... resto del CSS ... */
  </style>
</head>
<body>
{% for item in powers %}
  <!-- tu layout aquí -->
{% endfor %}
</body>
</html>
```

### Variables disponibles en el template

El template recibe los datos bajo el nombre que definiste en `data_key`, más `view_name`:

```html
{% for p in powers %}
  {{ p.name }}
  {{ p.description }}
  {{ p.rank_name }}
{% endfor %}

{{ view_name }}   ← nombre de la vista seleccionada
```

Para ver todos los campos disponibles de cada tabla visita `/api/debug/<tabla>` con el servidor en marcha (`/api/debug/power`, `/api/debug/edge`, etc.).

---

## Paso 3 — Ajustar el tamaño de página en el CSS

El tamaño se define en la regla `@page` del CSS del template. WeasyPrint lo respeta exactamente.

### Tamaños habituales

| Formato | `size` en CSS |
|---|---|
| Móvil (actual) | `108mm 192mm` |
| Tablet 7" apaisada | `190mm 120mm` |
| Tablet 10" | `148mm 210mm` (A5) |
| A4 portrait | `210mm 297mm` |
| A4 landscape | `297mm 210mm` |
| Carta US | `216mm 279mm` |
| Tarjeta de juego | `63mm 88mm` |

### Márgenes

```css
@page {
  size: 148mm 210mm;
  margin: 10mm;          /* todos iguales */
  /* o por lado: */
  margin: 10mm 12mm 10mm 12mm;  /* arriba derecha abajo izquierda */
}
```

Para documentos de tipo "card" sin márgenes en la página pero con padding interno en cada carta:

```css
@page { size: 108mm 192mm; margin: 0; }

.card {
  padding: 5mm;
  page-break-after: always;  /* cada carta en su propia página */
}
```

---

## El bestiario es un caso especial

El bestiario usa `get_bestiary_entries()` en lugar de `get_table()`, porque cada criatura necesita cargar sus relaciones (habilidades, poderes, equipo…). `render_document` ya lo detecta automáticamente cuando la tabla es `"bestiary"`:

```python
if table_key == "bestiary":
    data = get_bestiary_entries(view_id=view_id, full=True)
else:
    data = get_table(table_key, view_id=view_id)
```

Si creas un `bestiary_tablet` solo tienes que registrarlo en `DOCUMENTS["bestiary"]["docs"]` y crear el template — no hay que tocar la lógica de datos.

---

## Ejemplo completo: Bestiario Tablet

### 1. Registro en `app.py`

```python
"bestiary": {
    "label": "Bestiario",
    "icon": "🐉",
    "docs": {
        "bestiary_mobile": {...},
        "bestiary_tablet": {           # ← nuevo
            "label": "Bestiario Tablet",
            "icon":  "📱",
            "template": "bestiary_tablet.html",
            "data_key": "creatures",
        },
    }
},
```

### 2. Template `templates/bestiary_tablet.html`

```html
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <style>
    @page { size: 210mm 148mm; margin: 0; }  /* A5 apaisado */

    body { font-family: 'EB Garamond', serif; }

    .creature {
      width: 210mm;
      height: 148mm;
      page-break-after: always;
      display: grid;
      grid-template-columns: 80mm 1fr;
    }
    .creature-image {
      width: 80mm;
      height: 148mm;
      object-fit: cover;
    }
    .creature-body {
      padding: 8mm;
    }
    /* ... */
  </style>
</head>
<body>
{% for creature in creatures %}
{% set c = creature.data %}
<div class="creature">
  {% if creature.image_url %}
  <img class="creature-image" src="{{ creature.image_url }}">
  {% endif %}
  <div class="creature-body">
    <h1>{{ c.name }}</h1>
    <p>{{ c.description }}</p>
    <!-- stats, habilidades... -->
  </div>
</div>
{% endfor %}
</body>
</html>
```

---

## Trucos CSS útiles para WeasyPrint

```css
/* Salto de página forzado */
.card { page-break-after: always; }

/* Evitar que un bloque se parta entre páginas */
.stat-block { page-break-inside: avoid; }

/* Footer en todas las páginas */
@page {
  @bottom-center {
    content: "Savage Worlds · " string(view-name);
    font-size: 8pt;
    color: #888;
    border-top: 0.5pt solid #ccc;
  }
}

/* Imagen de fondo en página */
@page { background-image: url("bg_texture.png"); }

/* Fuentes web (requieren conexión al generar, o usar fuentes locales) */
@import url('https://fonts.googleapis.com/css2?family=Cinzel');
```

WeasyPrint **no soporta**:
- `position: fixed` (usar `position: running()` para headers/footers repetidos)
- `flexbox` en contextos paginados (usar `display: table` o bloques normales)
- JavaScript
- Animaciones / transiciones

---

## Resumen rápido

```
1. app.py → DOCUMENTS  añadir entrada con label, icon, template, data_key
2. templates/           crear el archivo HTML con @page y el bucle Jinja2
3. Reiniciar servidor   el botón aparece solo
```
