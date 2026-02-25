# Manual para añadir nuevos documentos PDF

Añadir un documento PDF al sistema son dos pasos: registrarlo en `config.py` y crear el template HTML en `templates/documents/`. No hay que tocar ningún otro archivo.

---

## Paso 1 — Registrar el documento en `config.py`

Abre `config.py` y localiza el diccionario `DOCUMENTS`. Añade una entrada en la tabla que corresponda a los datos que quieres mostrar:

```python
DOCUMENTS = {
    "power": {
        "label": "Poderes",
        "icon": "✦",
        "docs": {
            "powers":       {...},
            "cards_mobile": {...},
            "cards_tablet": {          # ← nuevo documento
                "label":       "Cartas Tablet",
                "icon":        "📱",
                "description": "Optimizado para tablet (190×120mm)",
                "template":    "documents/power_cards_tablet.html",
                "data_key":    "powers",
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
| `description` | Texto descriptivo visible bajo el nombre |
| `template` | Path del archivo HTML relativo a `templates/` |
| `data_key` | Nombre de la variable con la que el template recibe los datos |

**`data_key` según la tabla:**

| Tabla (`DOCUMENTS` key) | `data_key` habitual |
|---|---|
| `power` | `"powers"` |
| `edge` | `"edges"` |
| `hindrance` | `"hindrances"` |
| `bestiary` | `"creatures"` |
| `treasure` | `"treasures"` |

Una vez añadido, al reiniciar el servidor aparecerá en la interfaz con los botones Ver / ↓ PDF automáticamente.

---

## Paso 2 — Crear el template HTML

Crea `templates/documents/<nombre>.html`. Lo más fácil es copiar uno existente como base:

```bash
cp templates/documents/power_cards_mobile.html templates/documents/power_cards_tablet.html
```

### Estructura básica

```html
{% extends "documents/base_document.html" %}
{% block content %}
{% for item in powers %}
  <!-- tu layout aquí -->
{% endfor %}
{% endblock %}
```

O sin herencia si prefieres un documento completamente autónomo:

```html
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <style>
    @page {
      size: 190mm 120mm;   /* ← tamaño de página */
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

{{ view_name }}   {# nombre de la vista seleccionada #}
```

Para ver todos los campos disponibles de cada tabla consulta directamente NocoDB, o inspecciona el primer registro en el servidor con `print()` temporal en `render_document()`.

---

## Paso 3 — Ajustar el tamaño de página en el CSS

El tamaño se define en la regla `@page` del CSS del template. WeasyPrint lo respeta exactamente.

### Tamaños habituales

| Formato | `size` en CSS |
|---|---|
| Móvil | `108mm 192mm` |
| Tablet apaisada | `190mm 120mm` |
| A5 | `148mm 210mm` |
| A4 portrait | `210mm 297mm` |
| A4 landscape | `297mm 210mm` |
| Carta US | `216mm 279mm` |
| Tarjeta de juego | `64mm 89mm` |

### Márgenes

```css
@page {
  size: 148mm 210mm;
  margin: 10mm;
  /* o por lado: */
  margin: 10mm 12mm 10mm 12mm;  /* arriba derecha abajo izquierda */
}
```

Para documentos tipo carta sin márgenes en la página pero con padding interno en cada carta:

```css
@page { size: 64mm 89mm; margin: 0; }

.card {
  padding: 4mm;
  page-break-after: always;  /* cada carta en su propia página */
}
```

---

## El bestiario es un caso especial

El bestiario usa `get_bestiary_entries()` en lugar de `get_table()` porque cada criatura necesita cargar sus relaciones. `render_document` lo detecta automáticamente cuando la tabla es `"bestiary"`:

```python
if table_key == "bestiary":
    data = get_bestiary_entries(view_id=view_id, full=True)
else:
    data = get_table(table_key, view_id=view_id)
```

Si creas un `bestiary_tablet` solo tienes que registrarlo en `DOCUMENTS["bestiary"]["docs"]` y crear el template — no hay que tocar la lógica de datos.

---

## Ejemplo completo: Bestiario Tablet

### 1. Registro en `config.py`

```python
"bestiary": {
    "label": "Bestiario",
    "icon": "🐉",
    "docs": {
        "bestiary_mobile": {...},
        "bestiary_tablet": {
            "label":       "Bestiario Tablet",
            "icon":        "📱",
            "description": "Formato A5 apaisado para tablet",
            "template":    "documents/bestiary_tablet.html",
            "data_key":    "creatures",
        },
    }
},
```

### 2. Template `templates/documents/bestiary_tablet.html`

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
    .creature-body { padding: 8mm; }
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
```

WeasyPrint **no soporta**:
- `position: fixed` (usar `position: running()` para headers/footers repetidos)
- `flexbox` en contextos paginados (usar `display: table` o bloques normales)
- JavaScript
- Animaciones / transiciones

---

## Resumen rápido

```
1. config.py → DOCUMENTS   añadir entrada con label, icon, description, template, data_key
2. templates/documents/    crear el archivo HTML con @page y el bucle Jinja2
3. Reiniciar servidor      el botón aparece solo
```
