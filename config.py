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
        "label": "Habilidades",
        "table_id": "mr9wckj7cenfu9e",
        "view_id": "vwoambz1ghunrsef",
        "glossary": False,
        "fields": None,
        "relations": []
    },

    "ancestry": {
        "label": "Linajes",
        "table_id": "m7idr6p4v8bnebf",
        "view_id": "vwblot2ljkdf3938",
        "glossary": True,
        "fields": ["name", "name_original", "traits"],
        "relations": []
    },

    "reference_book": {
        "label": "Libros",
        "table_id": "mlryzqjacylgxzm",
        "view_id": "vw8heesccct7o7r1",
        "glossary": False,
        "fields": ["title", "description"],
        "relations": []
    },   

    "power": {
        "label": "Poderes",
        "table_id": "mx88eizkev8cy9i",
        "view_id": "vw4f52nynn9mora5",
        "glossary": True,
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
        "label": "Ventajas",
        "table_id": "mxcix7utv40luu4",
        "view_id": "vwg00ejk8z9pgny7",
        "glossary": True,
        "fields": None,
        "relations": []
    },

    "hindrance": {
        "label": "Desventajas",
        "table_id": "makzrikm8hnw52b",
        "view_id": "vwlib841q174mps1",
        "glossary": True,
        "fields": None,
        "relations": []
    },

    "character": {
        "label": "Personajes",
        "table_id": "mxb6bj2wpwq1plw",
        "view_id": "vwnp34efxdp32d6y",
        "glossary": False,
        "fields": ["name", "data", "image"],
        "relations": []
    },

    "bestiary": {
        "label": "Bestiario",
        "table_id": "m1c3skvkx8mdwhl",
        "view_id": "vwvf9tunnwo0jfks",
        "glossary": False,
        "fields": ["name", "type", "concept", "wild_card", "data", "image"],
        "relations": []
    },

    "treasure": {
        "label": "Tesoros",
        "table_id": "m36nr536uiox6ev",
        "view_id": "vwyr4wd409u36rbv",
        "glossary": False,
        "fields": ["name", "type", "stat", "description", "ability", "rarity", "image"],
        "relations": []
    },

    "equipment": {
        "label": "Equipamiento",
        "table_id": "mkgk5mduy4fiowj",
        "view_id": "vwhf6fhj098okgey",
        "glossary": False,
        "fields": ["name", "name_original", "type", "traits", "notes", "cost", "weight", "source", "reference_book", "page_no"],
        "relations": []
    },

    "tag": {
        "label": "Etiquetas",
        "table_id": "mycq00kbyhr6l02",
        "view_id": "vwhf0w2oa8y3z25t",
        "glossary": False,
        "fields": ["name", "power_names", "comment"],
        "relations": []
    },

    "rule": {
        "label": "Reglas",
        "table_id": "mrswhf1k48zeu70",
        "view_id": "vwd3oesva04hk2kn",
        "glossary": False,
        "fields": ["name", "name_original", "description", "content", "source", "icon", "page_no", "reference_book"],
        "relations": []
    },

    "glossary": {
        "label": "Términos",
        "table_id": "mvsla4jg1wki983",
        "view_id": "vw3apc7adu4pp5s8",
        "glossary": True,
        "fields": ["name", "name_original"],
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
        "category": "sistema",
        "icon": "✦",
        "description": "Capacidades extraordinarias que permiten ejecutar efectos asombrosos",
        "image": "images/power.jpg",
        "docs":{
            "manual_print": {
                
                "label": "Manual de Poderes",
                "icon": "📖",
                "description": "Formato PDF en A4 para imprimir",
                "image": "images/book01.jpg",
                "template": "documents/powers_manual.html",
                "data_key": "powers",
            },
            "manual_docx": {
                "label": "Manual de Poderes (Word)",
                "icon": "📖",
                "description": "Documento en Word para editar y aplicar estilos propios",
                "image": "images/book01.jpg",
                "template": "documents/powers_template.docx",
                "data_key": "powers",
            },
            "cards_print":{
                "label": "Cartas de Poderes",
                "icon": "🂠",
                "description": "Formato tarjeta para imprimir",
                "image": "images/banner01.jpg",
                "template": "documents/power_cards.html",
                "data_key": "powers",
            },
            "cards_mobile":{
                "label": "Cartas Móvil",
                "icon": "📱",
                "description": "Optimizado para teléfono (108×240mm)",
                "image": "images/relic01.jpg",
                "template": "documents/power_cards_mobile.html",
                "data_key": "powers",
            },
            "tags_print": {
                "label": "Poderes por Trasfondo",
                "icon": "🏷",
                "description": "Lista de poderes disponibles por trasfondo arcano y dominio",
                "image": "images/book02.jpg",
                "template": "documents/power_tags.html",
                "data_key": "tags",
                "table_key": "tag",
            },
        },
    },
    "edge": {
        "label": "Ventajas", 
        "category": "sistema",
        "icon": "⚔",
        "description": "Aptitudes y rasgos extraordinarios de los personajes",
        "image": "images/edge.jpg",
        "docs": {
            "cards_mobile": {
                "label": "Cartas Móvil",
                "icon": "📱",
                "description": "Optimizado para teléfono (108×240mm)",
                "image": "images/relic01.jpg",
                "template": "documents/edge_cards_mobile.html",
                "data_key": "edges",
            },
        }
    },
    "hindrance": {
        "label": "Desventajas", 
        "category": "sistema",
        "icon": "☠",
        "description": "Rasgos negativos que impulsan el drama",
        "image": "images/hindrance.jpg",
        "docs": {
            "manual_docx": {
                "label": "Manual de Desventajas",
                "icon": "📖",
                "description": "Documento en Word para editar y aplicar estilos propios",
                "image": "images/book01.jpg",
                "template": "documents/hindrances_template.docx",
                "data_key": "hindrances",
            },
        }
    },
    "character": {
        "label": "Personajes", 
        "category": "ambientacion",
        "icon": "🧙",
        "description": "Héroes que pueblan un mundo de aventuras",
        "image": "images/character.jpg",
        "docs": {
            "character_sheet": {
                "label": "Ficha de Personaje",
                "icon": "📄",
                "description": "Ficha completa A4 doble cara, lista para imprimir",
                "image": "images/letter01.jpg",
                "template": "documents/character_sheet.html",
                "data_key": "characters",
            },
        }
    },
    "bestiary": {
        "label": "Bestiario", 
        "category": "ambientacion",
        "icon": "🐉",
        "description": "Criaturas y bestias antagonistas",
        "image": "images/bestiary.jpg",
        "docs": {
            "card_mobile": {
                "label": "Bestiario Móvil",
                "icon": "📱",
                "description": "Optimizado para teléfono (108×240mm)",
                "image": "images/relic01.jpg",
                "template": "documents/bestiary_mobile.html",
                "data_key": "creatures",
            },
        }
    },
    "treasure": {
        "label": "Tesoros", 
        "category": "ambientacion",
        "icon": "💎",
        "description": "Reliquias y objetos de gran relevancia",
        "image": "images/treasure.jpg",
        "docs": {
            "cards_print": {
                "label": "Tarjetas de Tesoro",
                "icon": "🃏",
                "description": "Formato tarjeta para imprimir (64×89mm)",
                "image": "images/banner01.jpg",
                "template": "documents/treasure_cards.html",
                "data_key": "treasures",
            },
        }
    },
    "equipment": {
        "label": "Equipo", 
        "category": "ambientacion",
        "icon": "⚔",
        "category": "ambientacion",
        "description": "Armas, armaduras y equipo de aventurero",
        "image": "images/edge.jpg",
        "docs": {
            "list_print": {
                "label": "Listado de Equipo",
                "icon": "📋",
                "description": "Formato PDF en A4 para imprimir",
                "image": "images/book01.jpg",
                "template": "documents/equipment_list.html",
                "data_key": "equipment",
            },
            "cards_print": {
                "label": "Cartas de Equipo",
                "icon": "🃏",
                "description": "Formato tarjeta para imprimir (64×89mm)",
                "image": "images/banner01.jpg",
                "template": "documents/equipment_cards.html",
                "data_key": "equipment",
            },
        }
    },
    "rule": {
        "label": "Reglas", 
        "category": "sistema",
        "icon": "⚖",
        "description": "Reglas modulares y opcionales",
        "image": "images/rule.jpg",
        "docs": {
            "manual_docx": {
                "label": "Compendio de Reglas",
                "icon": "📖",
                "description": "Formato en Word para editar y aplicar estilos propios",
                "image": "images/book01.jpg",
                "template": "documents/rules_template.md",
                "data_key": "rules",
            },
            "manual_print": {
                "label": "Compendio de Reglas",
                "icon": "📝",
                "description": "Formato PDF en A4 para imprimir",
                "image": "images/book02.jpg",
                "template": "documents/rules_manual.html",
                "data_key": "rules",
            },
        }
    },    
}
