# config.py
import os
from dotenv import load_dotenv

load_dotenv()

NOCODB_URL = os.getenv("NOCODB_URL", "http://localhost:8080")
API_TOKEN  = os.getenv("NOCODB_API_TOKEN")
BASE_ID    = os.getenv("NOCODB_BASE_ID")

if not API_TOKEN:
    raise EnvironmentError("Falta NOCODB_API_TOKEN en el archivo .env")

# ── CONFIGURACIÓN DE TABLAS ────────────────────────────────────────────────
#
# Cada entrada define:
#   table_id  : ID de la tabla en NocoDB (obligatorio)
#   view_id   : ID de la vista a usar — ordena y filtra según NocoDB (opcional)
#   fields    : campos a recuperar, None = todos (el campo Id se añade siempre)
#   relations : lista de relaciones anidadas (opcional)
#
# Cada relación define:
#   key            : nombre de la clave en el JSON resultante
#   link_field_id  : ID del campo de enlace en la tabla padre
#   count_field    : campo del registro padre que indica cuántos relacionados hay
#   fields         : campos a recuperar de la tabla relacionada
#
TABLE_CONFIG = {

    "power": {
        "table_id": "mx88eizkev8cy9i",
        "view_id": "vw4f52nynn9mora5",   # Vista de NocoDB — cambia aquí el orden/filtro
        "fields": [
            "name", "name_original", "rank_name", "cost",
            "range", "range_roh", "duration", "page_no",
            "description", "reference_book", "modifier"
        ],
        "relations": [
            {
                "key": "modifiers",
                "link_field_id": "c48d1ciqk7ee110",
                "count_field": "modifier",        # campo numérico en el registro padre
                "fields": ["title", "cost", "description"]
            }
        ]
    },

    "edge": {
        "table_id": "mxcix7utv40luu4",
        "view_id": "vwg00ejk8z9pgny7",
        "fields": None,
        "relations": []
    },

    "hindrance": {
        "table_id": "makzrikm8hnw52b",
        "view_id": "vwlib841q174mps1",
        "fields": None,
        "relations": []
    },

    "skill": {
        "table_id": "mr9wckj7cenfu9e",
        "view_id": "vwoambz1ghunrsef",
        "fields": None,
        "relations": []
    },

    "ancestry": {
        "table_id": "m7idr6p4v8bnebf",
        "view_id": "vwblot2ljkdf3938",
        "fields": ["name", "name_original", "traits"],
        "relations": []
    },

    # Fichas de personaje — el JSON completo va en el campo 'data'
    # y la imagen como adjunto en el campo 'image'
    "character": {
        "table_id": "mxb6bj2wpwq1plw",
        "view_id": None,
        "fields": ["name", "data", "image"],
        "relations": []
    },

}
