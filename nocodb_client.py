# nocodb_client.py
# Cliente genérico para NocoDB. Lee la configuración de config.py.
# No necesitas modificar este archivo para añadir tablas nuevas.

import json as _json
import requests
from config import NOCODB_URL, API_TOKEN, TABLE_CONFIG

HEADERS = {
    "xc-token": API_TOKEN,
    "Content-Type": "application/json"
}


def _get_records(table_id: str, view_id: str | None, fields: list[str] | None) -> list[dict]:
    """Obtiene todos los registros de una tabla/vista paginando automáticamente."""
    records = []
    page = 1
    while True:
        params = {"page": page, "limit": 25}
        if view_id:
            params["viewId"] = view_id
        if fields:
            all_fields = list(dict.fromkeys(["Id"] + fields))
            params["fields"] = ",".join(all_fields)
        r = requests.get(f"{NOCODB_URL}/api/v2/tables/{table_id}/records", headers=HEADERS, params=params)
        r.raise_for_status()
        data = r.json()
        records.extend(data["list"])
        if data["pageInfo"]["isLastPage"]:
            break
        page += 1
    return records


def _get_related_records(table_id: str, link_field_id: str, row_id: int, fields: list[str] | None) -> list[dict]:
    """Obtiene los registros relacionados de un registro dado."""
    params = {"fields": ",".join(fields)} if fields else {}
    r = requests.get(f"{NOCODB_URL}/api/v2/tables/{table_id}/links/{link_field_id}/records/{row_id}",
                     headers=HEADERS, params=params)
    r.raise_for_status()
    return r.json().get("list", [])


def _get_record(table_key: str, record_id: int) -> dict:
    """Obtiene un registro individual por Id."""
    cfg = TABLE_CONFIG[table_key]
    r = requests.get(f"{NOCODB_URL}/api/v2/tables/{cfg['table_id']}/records/{record_id}", headers=HEADERS)
    r.raise_for_status()
    return r.json()


def _parse_attachment_url(attachments: list) -> str | None:
    """Extrae la URL firmada del primer adjunto si existe."""
    if attachments:
        signed_path = attachments[0].get("signedPath")
        if signed_path:
            return f"{NOCODB_URL}/{signed_path}"
    return None


def get_table(name: str, view_id: str | None = None) -> list[dict]:
    """
    Obtiene todos los registros de una tabla con sus relaciones resueltas.
    Si se pasa view_id, sobrescribe el view_id definido en config.py.

    Uso:
        powers = get_table("power")
        powers = get_table("power", view_id="vwxxxxxxxx")
        rules  = get_table("rule")
    """
    if name not in TABLE_CONFIG:
        raise ValueError(f"Tabla '{name}' no encontrada en config.py. "
                         f"Tablas disponibles: {list(TABLE_CONFIG.keys())}")

    cfg = TABLE_CONFIG[name]
    effective_view_id = view_id or cfg.get("view_id")
    records = _get_records(cfg["table_id"], effective_view_id, cfg.get("fields"))

    for record in records:
        for rel in cfg.get("relations", []):
            count = record.get(rel.get("count_field", rel["key"]), 0)
            if isinstance(count, int) and count == 0:
                record[rel["key"]] = []
                continue
            record[rel["key"]] = _get_related_records(
                cfg["table_id"], rel["link_field_id"], record["Id"], rel.get("fields")
            )

    return records


# ── PERSONAJES ────────────────────────────────────────────────────────────
# Necesitan funciones propias porque transforman el campo `data` (JSON en string)
# y construyen image_url desde los adjuntos.

def get_characters(view_id: str | None = None, full: bool = False) -> list[dict]:
    """
    Devuelve lista de personajes.
    - full=False: solo Id y name (para listados y selectores)
    - full=True: registros completos con data parseado e image_url
    """
    cfg = TABLE_CONFIG["character"]
    effective_view_id = view_id or cfg.get("view_id")

    if not full:
        params = {"limit": 100, "fields": "Id,name"}
        if effective_view_id:
            params["viewId"] = effective_view_id
        r = requests.get(f"{NOCODB_URL}/api/v2/tables/{cfg['table_id']}/records", headers=HEADERS, params=params)
        r.raise_for_status()
        return r.json().get("list", [])

    cfg = TABLE_CONFIG["character"]
    # Forzamos los campos mínimos necesarios independientemente de la vista
    records = _get_records(cfg["table_id"], effective_view_id, ["name", "data", "image"])
    result = []
    for rec in records:
        raw = rec.get("data") or "{}"
        character = _json.loads(raw) if isinstance(raw, str) else raw
        if not character:
            continue
        result.append({
            "id": rec.get("Id"),
            "name": rec.get("name"),
            "data": character,
            "image_url": _parse_attachment_url(rec.get("image") or []),
        })
    return result


def get_character(record_id: int) -> dict:
    """Devuelve un personaje completo con data parseado e image_url."""
    record = _get_record("character", record_id)
    raw = record.get("data") or "{}"
    character = _json.loads(raw) if isinstance(raw, str) else raw
    return {
        "character": character,
        "image_url": _parse_attachment_url(record.get("image") or []),
    }


# ── BESTIARIO ─────────────────────────────────────────────────────────────
# Igual que personajes: transforman data (JSON) e image_url.

def get_bestiary_entries(view_id: str | None = None, full: bool = False) -> list[dict]:
    """
    Devuelve lista de criaturas.
    - full=False: solo Id, name, type, concept (para listados)
    - full=True: registros completos con data parseado e image_url
    """
    cfg = TABLE_CONFIG["bestiary"]
    effective_view_id = view_id or cfg.get("view_id")

    if not full:
        params = {"limit": 200, "fields": "Id,name,type,concept"}
        if effective_view_id:
            params["viewId"] = effective_view_id
        r = requests.get(f"{NOCODB_URL}/api/v2/tables/{cfg['table_id']}/records", headers=HEADERS, params=params)
        r.raise_for_status()
        return r.json().get("list", [])

    result = []
    for rec in get_table("bestiary", view_id):
        raw = rec.get("data") or "{}"
        creature = _json.loads(raw) if isinstance(raw, str) else raw
        if isinstance(creature, list):
            creature = creature[0] if creature else {}
        wild_card = rec.get("wild_card") or creature.get("wild_card") or 0
        result.append({
            "id": rec.get("Id"),
            "name": rec.get("name"),
            "type": rec.get("type"),
            "concept": rec.get("concept"),
            "wild_card": bool(wild_card),
            "data": creature,
            "image_url": _parse_attachment_url(rec.get("image") or []),
        })
    return result


def get_bestiary_entry(record_id: int) -> dict:
    """Devuelve una criatura completa con data parseado e image_url."""
    record = _get_record("bestiary", record_id)
    raw = record.get("data") or "{}"
    creature = _json.loads(raw) if isinstance(raw, str) else raw
    if isinstance(creature, list):
        creature = creature[0] if creature else {}
    return {
        "creature": creature,
        "image_url": _parse_attachment_url(record.get("image") or []),
    }


if __name__ == "__main__":
    import sys
    table = sys.argv[1] if len(sys.argv) > 1 else "power"
    print(f"Consultando tabla: {table}")
    import json
    print(json.dumps(get_table(table), ensure_ascii=False, indent=2))
