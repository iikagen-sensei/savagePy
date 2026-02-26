# savagePy — Generador de documentos Savage Worlds

Servidor web local que conecta con una base de datos **NocoDB** y genera documentos PDF y Word para partidas de Savage Worlds: manuales de poderes/ventajas/desventajas, cartas de referencia, bestiario, fichas de personaje y compendios de reglas modulares.

---

## Estructura del proyecto

```
savagePy/
│
├── app.py                  # Servidor Flask. Rutas y lógica principal.
├── config.py               # Configuración: NocoDB, tablas, y definición de documentos.
├── nocodb_client.py        # Cliente HTTP para NocoDB. No tocar salvo cambios de API.
├── docx_generator.py       # Prepara el contexto de datos para los templates Word.
│
├── .env                    # Variables de entorno — NO subir a git
├── .env.example            # Plantilla del .env
├── requirements.txt        # Dependencias del proyecto
├── savagePy.bat            # Lanzador para Windows/WSL (doble clic para arrancar)
│
├── templates/
│   │
│   ├── ui/                         # Interfaz web (lo que ve el usuario en el navegador)
│   │   ├── base.html               # Layout base: navbar, estilos globales de la UI
│   │   ├── index.html              # Página principal: listado de documentos
│   │   ├── glosario.html           # Glosario de traducciones (abre en nueva pestaña)
│   │   ├── characters.html         # Listado de personajes
│   │   ├── character_form.html     # Formulario para crear/editar personajes
│   │   ├── bestiary.html           # Listado de criaturas
│   │   ├── bestiary_form.html      # Formulario para crear/editar criaturas
│   │   ├── rules.html              # Listado de reglas modulares
│   │   └── rule_form.html          # Formulario para crear/editar reglas
│   │
│   └── documents/                  # Templates de documentos generables
│       ├── base_document.html      # Base compartida para documentos (herencia Jinja2)
│       ├── powers_manual.html      # PDF: manual completo de poderes
│       ├── power_cards.html        # PDF: cartas A4 de poderes
│       ├── power_cards_mobile.html # PDF: cartas móvil (108×192mm)
│       ├── edges_manual.html       # PDF: manual de ventajas
│       ├── edge_cards_mobile.html  # PDF: cartas móvil de ventajas
│       ├── hindrances_manual.html  # PDF: manual de desventajas
│       ├── bestiary_mobile.html    # PDF: bestiario móvil (108×192mm)
│       ├── character_sheet.html    # PDF: ficha de personaje A4
│       ├── treasure_cards.html     # PDF: tarjetas de tesoro (64×89mm)
│       ├── rules_manual.html       # PDF: compendio de reglas modulares
│       │
│       ├── powers_template.docx        # Plantilla Word de poderes (editable)
│       ├── edges_template.docx         # Plantilla Word de ventajas (editable)
│       ├── hindrances_template.docx    # Plantilla Word de desventajas (editable)
│       └── rules_template.docx         # Marcador para activar botón Word de reglas
│
├── static/
│   ├── ui.css              # Estilos de la interfaz web
│   └── images/             # Imágenes de tabs y documentos (256×256px)
│
├── README.md               # Este archivo
├── PDF_TEMPLATES.md        # Manual: cómo añadir nuevos documentos PDF
└── DOCX_TEMPLATES.md       # Manual: cómo usar y editar las plantillas Word
```

---

## Instalación

```bash
# 1. Clonar / descomprimir el proyecto
cd savagePy

# 2. Crear entorno virtual
python -m venv .venv

# 3. Activar entorno
.venv\Scripts\activate      # Windows
source .venv/bin/activate   # Linux / Mac / WSL

# 4. Instalar dependencias
pip install -r requirements.txt

# 5. Configurar variables de entorno
cp .env.example .env
# Editar .env con tu URL de NocoDB y token API

# 6. Arrancar
python app.py
# → http://localhost:5000
```

En Windows con WSL puedes usar el lanzador `savagePy.bat` directamente desde el explorador.

### WeasyPrint en WSL (Ubuntu)

WeasyPrint necesita algunas librerías del sistema:

```bash
sudo apt install libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b
```

### Pandoc (para el compendio de reglas en Word)

```bash
sudo apt install pandoc
pip install pypandoc --break-system-packages
```

---

## Configuración

Todo está en **`config.py`** y **`.env`**.

### `.env`

```
NOCODB_URL=http://localhost:8080
NOCODB_API_TOKEN=tu_token_aqui
NOCODB_BASE_ID=pw16bcxvn0pv0xb
```

### `config.py` — Tablas (`TABLE_CONFIG`)

Cada tabla de NocoDB tiene una entrada con:

- **`table_id`** — ID de la tabla en NocoDB
- **`view_id`** — vista por defecto que controla orden y filtros (las vistas deben tener el prefijo `pub:` en NocoDB para aparecer en el selector de la UI)
- **`fields`** — lista de campos a recuperar, o `None` para todos
- **`relations`** — relaciones anidadas (p.ej. modificadores de un poder)

### `config.py` — Documentos (`DOCUMENTS`)

Define qué documentos existen y cómo se muestran en la interfaz. El orden de las entradas determina el orden de las tabs. Para añadir un documento nuevo solo hay que añadir una entrada aquí y crear el template — ver `PDF_TEMPLATES.md`.

---

## Cómo funciona

### Flujo general

```
Usuario abre la web
  → elige tabla/vista y documento
  → pulsa ↓ PDF / ↓ Word

Flask recibe la petición
  → consulta NocoDB (respetando la vista seleccionada)
  → renderiza el template (HTML para PDF, .docx para Word)
  → devuelve el archivo para descargar
```

### Rutas principales

| Ruta | Descripción |
|---|---|
| `GET /` | Interfaz principal |
| `GET /preview/<doc_id>` | Previsualiza el documento en el navegador |
| `GET /download/<doc_id>/pdf` | Descarga PDF (WeasyPrint) |
| `GET /download/<doc_id>/docx` | Descarga Word (docxtpl o python-docx según el tipo) |
| `GET /download/<doc_id>/html` | Descarga HTML |
| `GET /api/views/<table_key>` | Vistas disponibles de una tabla |
| `GET /api/status` | Recuento de registros por tabla |
| `GET /characters` | Listado de personajes (filtrado por view_id de config) |
| `GET /bestiary` | Listado de criaturas (filtrado por view_id de config) |
| `GET /rules` | Listado de reglas modulares |
| `GET /glosario` | Glosario de traducciones (abre en nueva pestaña) |

Todos admiten `?view_id=<id>` para filtrar por vista.

### Añadir un documento nuevo

Solo dos pasos — ver `PDF_TEMPLATES.md` para el detalle completo:

1. Añadir la entrada en `DOCUMENTS` en `config.py`
2. Crear el template HTML en `templates/documents/`

El botón aparece automáticamente en la interfaz al reiniciar el servidor.

### Templates Word

Los archivos `*_template.docx` en `templates/documents/` son plantillas editables en Word. Puedes cambiar fuentes, colores y estilos sin tocar el código. Ver `DOCX_TEMPLATES.md` para la referencia completa de variables disponibles.

**Excepción — Reglas modulares**: el compendio de reglas se genera con `python-docx` + `pypandoc` directamente desde el Markdown almacenado en NocoDB, sin usar la plantilla. El archivo `rules_template.docx` existe solo para que aparezca el botón Word en la interfaz.

---

## Secciones de gestión

### Personajes y Bestiario

Accesibles desde el nav. Muestran siempre los registros filtrados por el `view_id` definido en `TABLE_CONFIG` — usa vistas de NocoDB para controlar qué aparece (p.ej. solo personajes completos, o criaturas de una campaña concreta).

### Reglas modulares

Accesible desde el nav. Permite crear y editar reglas con un editor Markdown enriquecido (EasyMDE). El campo `source` distingue entre reglas Oficiales, de Terceros y Propias. Las vistas `pub:` de NocoDB permiten filtrar qué reglas se incluyen en cada compendio descargable.

### Glosario

Enlace discreto en el footer. Abre en nueva pestaña una tabla con los nombres en español y original de poderes, ventajas, desventajas y habilidades. Permite ordenar por cualquier columna y filtrar con un buscador.

---

## Vistas de NocoDB

Las vistas permiten tener subconjuntos filtrados y ordenados de cada tabla — por ejemplo `pub:Bestiario fantasía` o `pub:Las minas malditas`. Solo aparecen en el selector las vistas cuyo nombre empiece por `pub:` (el prefijo se oculta en la UI).

El nombre de la vista seleccionada se pasa a los templates como `{{ view_name }}` y aparece en el footer de los documentos generados.
