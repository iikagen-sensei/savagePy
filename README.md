# savagePy — Generador de documentos Savage Worlds

Servidor web local que conecta con una base de datos **NocoDB** y genera documentos PDF y Word para partidas de Savage Worlds: manuales de poderes/ventajas/desventajas, cartas de referencia, bestiario y fichas de personaje.

---

## Estructura del proyecto

```
savagePy/
│
├── app.py                  # Servidor Flask. Rutas y lógica principal.
├── config.py               # Configuración: NocoDB URL, token, tablas y vistas.
├── nocodb_client.py        # Cliente HTTP para NocoDB. No tocar salvo cambios de API.
├── docx_generator.py       # Prepara el contexto de datos para los templates Word.
│
├── .env                    # Variables de entorno — NO subir a git
├── .env.example            # Plantilla del .env
├── requirements.txt        # Dependencias del proyecto
│
├── templates/
│   │
│   ├── ui/                 # Interfaz web (lo que ve el usuario en el navegador)
│   │   ├── base.html       # Layout base: navbar, estilos globales de la UI
│   │   ├── index.html      # Página principal: listado de documentos
│   │   ├── characters.html # Listado de personajes
│   │   └── character_form.html  # Formulario para crear/editar personajes
│   │
│   ├── base.html           # Base para templates de documentos (herencia Jinja2)
│   │
│   ├── powers_manual.html          # PDF: manual completo de poderes
│   ├── power_cards.html            # PDF: cartas A4 de poderes
│   ├── power_cards_mobile.html     # PDF: cartas móvil (108×192mm)
│   ├── edges_manual.html           # PDF: manual de ventajas
│   ├── edge_cards_mobile.html      # PDF: cartas móvil de ventajas
│   ├── hindrances_manual.html      # PDF: manual de desventajas
│   ├── bestiary_mobile.html        # PDF: bestiario móvil (108×192mm)
│   │
│   ├── powers_template.docx        # Plantilla Word de poderes (editable)
│   ├── edges_template.docx         # Plantilla Word de ventajas (editable)
│   └── hindrances_template.docx    # Plantilla Word de desventajas (editable)
│
├── static/
│   └── ui.css              # Estilos de la interfaz web
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

### WeasyPrint en WSL (Ubuntu)

WeasyPrint necesita algunas librerías del sistema:

```bash
sudo apt install libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b
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

### `config.py` — Tablas

Cada tabla de NocoDB tiene una entrada en `TABLE_CONFIG` con:

- **`table_id`** — ID de la tabla en NocoDB
- **`view_id`** — ID de la vista que controla orden y filtros (las vistas deben tener el prefijo `pub:` en NocoDB para aparecer en el selector)
- **`fields`** — lista de campos a recuperar, o `None` para todos
- **`relations`** — relaciones anidadas (p.ej. modificadores de un poder)

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
| `GET /download/<doc_id>/docx` | Descarga Word (docxtpl) |
| `GET /api/views/<table_key>` | Vistas disponibles de una tabla |
| `GET /api/status` | Recuento de registros por tabla |
| `GET /api/debug/<table_key>` | Primer registro en crudo (útil para ver campos) |

Todos admiten `?view_id=<id>` para filtrar por vista.

### Registro de documentos (`app.py`)

El diccionario `DOCUMENTS` en `app.py` define qué documentos existen. Para añadir uno nuevo basta con añadir una entrada — ver `PDF_TEMPLATES.md` para el proceso completo.

### Templates Word

Los archivos `*_template.docx` en `templates/` son plantillas editables en Word. Puedes cambiar fuentes, colores y estilos sin tocar el código. Ver `DOCX_TEMPLATES.md` para la referencia completa de variables disponibles.

---

## El bestiario

El bestiario tiene lógica propia en `nocodb_client.py` (`get_bestiary_entries`) porque cada criatura necesita cargar múltiples relaciones anidadas (habilidades especiales, poderes, equipo…). Los datos de imagen se resuelven también aquí.

El formulario de alta/edición de criaturas está en `templates/ui/` y se accede desde la interfaz principal.

---

## Vistas de NocoDB

Las vistas permiten tener subconjuntos filtrados y ordenados de cada tabla — por ejemplo `pub:Bestiario fantasía` o `pub:Villanos`. Solo aparecen en el selector las vistas cuyo nombre empiece por `pub:` (el prefijo se oculta en la UI).

El nombre de la vista seleccionada se pasa a los templates como `{{ view_name }}` y aparece en el footer de los documentos generados.
