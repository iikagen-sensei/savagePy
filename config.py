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

    "reference_book": {
        "table_id": "mlryzqjacylgxzm",
        "view_id": "vw8heesccct7o7r1",
        "fields": ["title", "description"],
        "relations": []
    },   

    "power": {
        "table_id": "mx88eizkev8cy9i",
        "view_id": "vw4f52nynn9mora5",
        "fields": [
            "name", "name_original", "rank_name", "cost",
            "range", "range_roh", "duration", "page_no",
            "description", "reference_book", "modifier"
        ],
        "relations": [
            {
                "key": "modifiers",
                "link_field_id": "c48d1ciqk7ee110",
                "count_field": "modifier",
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

    "character": {
        "table_id": "mxb6bj2wpwq1plw",
        "view_id": "vwnp34efxdp32d6y",
        "fields": ["name", "data", "image"],
        "relations": []
    },

    "bestiary": {
        "table_id": "m1c3skvkx8mdwhl",
        "view_id": "vwvf9tunnwo0jfks",
        "fields": ["name", "type", "concept", "wild_card", "data", "image"],
        "relations": []
    },

    "treasure": {
        "table_id": "m36nr536uiox6ev",
        "view_id": "vwyr4wd409u36rbv",
        "fields": ["name", "type", "stat", "description", "ability", "rarity", "image"],
        "relations": []
    },

    "rule": {
        "table_id": "mrswhf1k48zeu70",
        "view_id": "vwd3oesva04hk2kn",
        "fields": ["name", "name_original", "description", "content", "source", "icon", "page_no", "reference_book"],
        "relations": []
    },

}

# ── CONFIGURACIÓN DE DOCUMENTOS ────────────────────────────────────────────
#
# Agrupa los documentos por tabla. El orden de las entradas determina
# el orden en que aparecen en la interfaz.
#
# Cada tabla define:
#   label       : nombre visible en la barra de tabs
#   icon        : emoji para la barra de tabs
#   docs        : documentos generables para esta tabla
#
# Cada documento define:
#   label       : nombre visible en el panel
#   icon        : emoji para el panel
#   description : texto descriptivo visible en la interfaz
#   template    : archivo HTML en templates/documents/
#   data_key    : nombre de la variable que recibe los datos en el template
#

DOCUMENTS = {
    "power": {
        "label": "Poderes",
        "icon": "✦",
        "description": "Capacidades extraordinarias que permiten ejecutar efectos asombrosos",
        "image": "images/power.jpg",
        "docs": [
            {
                "id": "powers_print",
                "label": "Manual de Poderes",
                "icon": "📖",
                "description": "Formato PDF en A4 para imprimir",
                "image": "images/book01.jpg",
                "template": "documents/powers_manual.html",
                "data_key": "powers",
            },
            {
                "id": "powers_manual_docx",
                "label": "Manual de Poderes (Word)",
                "icon": "📖",
                "description": "Documento en Word para editar y aplicar estilos propios",
                "image": "images/book01.jpg",
                "template": "documents/powers_template.docx",
                "data_key": "powers",
            },
            {
                "id": "cards",
                "label": "Cartas de Poderes",
                "icon": "🂠",
                "description": "Formato tarjeta para imprimir",
                "image": "images/banner01.jpg",
                "template": "documents/power_cards.html",
                "data_key": "powers",
            },
            {
                "id": "cards_mobile",
                "label": "Cartas Móvil",
                "icon": "📱",
                "description": "Optimizado para teléfono (108×240mm)",
                "image": "images/relic01.jpg",
                "template": "documents/power_cards_mobile.html",
                "data_key": "powers",
            },
        ]
    },
    "edge": {
        "label": "Ventajas",
        "icon": "⚔",
        "description": "Aptitudes y rasgos extraordinarios de los personajes",
        "image": "images/edge.jpg",
        "docs": [
            {
                "id": "edge_cards_mobile",
                "label": "Cartas Móvil",
                "icon": "📱",
                "description": "Optimizado para teléfono (108×240mm)",
                "image": "images/relic01.jpg",
                "template": "documents/edge_cards_mobile.html",
                "data_key": "edges",
            },
        ]
    },
    "hindrance": {
        "label": "Desventajas",
        "icon": "☠",
        "description": "Rasgos negativos que impulsan el drama",
        "image": "images/hindrance.jpg",
        "docs": [
            {
                "id": "hindrances",
                "label": "Manual de Desventajas",
                "icon": "📖",
                "description": "Documento en Word para editar y aplicar estilos propios",
                "image": "images/book01.jpg",
                "template": "documents/hindrances_template.docx",
                "data_key": "hindrances",
            },
        ]
    },
    "character": {
        "label": "Personajes",
        "icon": "🧙",
        "description": "Héroes que pueblan un mundo de aventuras",
        "image": "images/character.jpg",
        "docs": [
            {
                "id": "character_sheet",
                "label": "Ficha de Personaje",
                "icon": "📄",
                "description": "Ficha completa A4 doble cara, lista para imprimir",
                "image": "images/letter01.jpg",
                "template": "documents/character_sheet.html",
                "data_key": None,
            },
        ]
    },
    "bestiary": {
        "label": "Bestiario",
        "icon": "🐉",
        "description": "Criaturas y bestias antagonistas",
        "image": "images/bestiary.jpg",
        "docs": [
            {
                "id": "bestiary_mobile",
                "label": "Bestiario Móvil",
                "icon": "📱",
                "description": "Optimizado para teléfono (108×240mm)",
                "image": "images/relic01.jpg",
                "template": "documents/bestiary_mobile.html",
                "data_key": "creatures",
            },
        ]
    },
    "treasure": {
        "label": "Tesoros",
        "icon": "💎",
        "description": "Reliquias y objetos de gran relevancia",
        "image": "images/treasure.jpg",
        "docs": [
            {
                "id": "treasure_cards",
                "label": "Tarjetas de Tesoro",
                "icon": "🃏",
                "description": "Formato tarjeta para imprimir (64×89mm)",
                "image": "images/banner01.jpg",
                "template": "documents/treasure_cards.html",
                "data_key": "treasures",
            },
        ]
    },
    "rule": {
        "label": "Reglas",
        "icon": "⚖",
        "description": "Reglas modulares y opcionales",
        "image": "images/rule.jpg",
        "docs": [
            {
                "id": "rules",
                "label": "Compendio de Reglas",
                "icon": "📖",
                "description": "Formato en Word para editar y aplicar estilos propios",
                "image": "images/book01.jpg",
                "template": "documents/rules_template.md",
                "data_key": "rules",
            },
            {
                "id": "rules_print",
                "label": "Compendio de Reglas",
                "icon": "📝",
                "description": "Formato PDF en A4 para imprimir",
                "image": "images/book02.jpg",
                "template": "documents/rules_manual.html",
                "data_key": "rules",
            },
        ]
    },    
}
