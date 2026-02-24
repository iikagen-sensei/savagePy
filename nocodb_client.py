# nocodb_client.py
# Cliente genérico para NocoDB. Lee la configuración de config.py.
# No necesitas modificar este archivo para añadir tablas nuevas.

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
            # Asegurarse de que Id siempre se incluye para poder consultar relaciones
            all_fields = list(dict.fromkeys(["Id"] + fields))
            params["fields"] = ",".join(all_fields)

        url = f"{NOCODB_URL}/api/v2/tables/{table_id}/records"
        r = requests.get(url, headers=HEADERS, params=params)
        r.raise_for_status()
        data = r.json()
        records.extend(data["list"])

        if data["pageInfo"]["isLastPage"]:
            break
        page += 1

    return records


def _get_related_records(table_id: str, link_field_id: str, row_id: int, fields: list[str] | None) -> list[dict]:
    """Obtiene los registros relacionados de un registro dado."""
    url = f"{NOCODB_URL}/api/v2/tables/{table_id}/links/{link_field_id}/records/{row_id}"
    params = {}
    if fields:
        params["fields"] = ",".join(fields)

    r = requests.get(url, headers=HEADERS, params=params)
    r.raise_for_status()
    return r.json().get("list", [])


def get_table(name: str, view_id: str | None = None) -> list[dict]:
    """
    Obtiene todos los registros de una tabla con sus relaciones resueltas.
    Si se pasa view_id, sobrescribe el view_id definido en config.py.

    Uso:
        powers = get_table("power")
        powers = get_table("power", view_id="vwxxxxxxxx")
        edges  = get_table("edge")
    """
    if name not in TABLE_CONFIG:
        raise ValueError(f"Tabla '{name}' no encontrada en config.py. "
                         f"Tablas disponibles: {list(TABLE_CONFIG.keys())}")

    cfg = TABLE_CONFIG[name]
    effective_view_id = view_id or cfg.get("view_id")
    records = _get_records(cfg["table_id"], effective_view_id, cfg.get("fields"))

    relations = cfg.get("relations", [])
    if not relations:
        return records

    for record in records:
        for rel in relations:
            count_field = rel.get("count_field", rel["key"])
            count = record.get(count_field, 0)

            if isinstance(count, int) and count == 0:
                record[rel["key"]] = []
                continue

            related = _get_related_records(
                table_id=cfg["table_id"],
                link_field_id=rel["link_field_id"],
                row_id=record["Id"],
                fields=rel.get("fields")
            )
            record[rel["key"]] = related

    return records


def get_characters(view_id: str | None = None, full: bool = False) -> list[dict]:
    """
    Devuelve lista de personajes.

    - Si ``full`` es False (valor por defecto) devuelve un "listado ligero" con
      únicamente los campos ``Id`` y ``name``. Este modo se usa para rellenar
      selectores en la interfaz y para operaciones que no necesitan el JSON
      completo.

    - Si ``full`` es True recupera todos los registros usando ``get_table`` y
      transforma cada fila para:
         * parsear el campo ``data`` (JSON que guarda toda la ficha)
         * generar ``id`` en minúsculas (convirtiendo ``Id``) para facilitar el
           acceso desde Jinja
         * construir ``image_url`` a partir del adjunto si existe
    """
    cfg = TABLE_CONFIG["character"]
    effective_view_id = view_id or cfg.get("view_id")

    if not full:
        params = {"limit": 100, "fields": "Id,name"}
        if effective_view_id:
            params["viewId"] = effective_view_id
        url = f"{NOCODB_URL}/api/v2/tables/{cfg['table_id']}/records"
        r = requests.get(url, headers=HEADERS, params=params)
        r.raise_for_status()
        return r.json().get("list", [])

    # modo completo: devolvemos registros enriquecidos
    # usar get_table permite aprovechar el comportamiento de relaciones, etc.
    import json as _json

    records = get_table("character", view_id)
    result: list[dict] = []
    for rec in records:
        raw_data = rec.get("data") or "{}"
        if isinstance(raw_data, str):
            character = _json.loads(raw_data)
        else:
            character = raw_data

        image_url = None
        attachments = rec.get("image") or []
        if attachments:
            signed_path = attachments[0].get("signedPath")
            if signed_path:
                image_url = f"{NOCODB_URL}/{signed_path}"

        result.append({
            "id": rec.get("Id"),
            "name": rec.get("name"),
            "data": character,
            "image_url": image_url,
        })
    return result


def get_character(record_id: int) -> dict:
    """
    Devuelve un personaje completo:
      - 'character': dict con todos los datos (parseado desde el campo 'data')
      - 'image_url': URL firmada de la imagen lista para usar en la plantilla
    """
    import json as _json
    cfg = TABLE_CONFIG["character"]
    url = f"{NOCODB_URL}/api/v2/tables/{cfg['table_id']}/records/{record_id}"
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    record = r.json()

    record = r.json()
    print("RECORD KEYS:", record.keys())
    print("DATA TYPE:", type(record.get("data")))
    print("DATA VALUE:", str(record.get("data"))[:100])        

    # Parsear el campo data (llega como string aunque sea tipo JSON en NocoDB)
    raw_data = record.get("data") or "{}"
    if isinstance(raw_data, str):
        character = _json.loads(raw_data)
    else:
        character = raw_data

    # Construir URL de imagen desde el adjunto
    image_url = None
    attachments = record.get("image") or []
    if attachments:
        signed_path = attachments[0].get("signedPath")
        if signed_path:
            image_url = f"{NOCODB_URL}/{signed_path}"

    return {"character": character, "image_url": image_url}



def get_bestiary_entries(view_id: str | None = None, full: bool = False) -> list[dict]:
    """
    Devuelve lista de entradas del bestiario.
    - full=False: solo Id, name, type, concept (para listados)
    - full=True: registros completos con data parseado e image_url
    """
    cfg = TABLE_CONFIG["bestiary"]
    effective_view_id = view_id or cfg.get("view_id")

    if not full:
        params = {"limit": 200, "fields": "Id,name,type,concept"}
        if effective_view_id:
            params["viewId"] = effective_view_id
        url = f"{NOCODB_URL}/api/v2/tables/{cfg['table_id']}/records"
        r = requests.get(url, headers=HEADERS, params=params)
        r.raise_for_status()
        return r.json().get("list", [])

    import json as _json
    records = get_table("bestiary", view_id)
    result = []
    for rec in records:
        raw_data = rec.get("data") or "{}"
        if isinstance(raw_data, str):
            creature = _json.loads(raw_data)
        else:
            creature = raw_data
        # data puede llegar como lista [{}] — extraer el primer elemento
        if isinstance(creature, list):
            creature = creature[0] if creature else {}

        image_url = None
        attachments = rec.get("image") or []
        if attachments:
            signed_path = attachments[0].get("signedPath")
            if signed_path:
                image_url = f"{NOCODB_URL}/{signed_path}"

        # wild_card puede venir del campo propio o del JSON
        wild_card = rec.get("wild_card") or creature.get("wild_card") or 0

        result.append({
            "id": rec.get("Id"),
            "name": rec.get("name"),
            "type": rec.get("type"),
            "concept": rec.get("concept"),
            "wild_card": bool(wild_card),
            "data": creature,
            "image_url": image_url,
        })
    return result


def get_bestiary_entry(record_id: int) -> dict:
    """
    Devuelve una criatura completa:
      - 'creature': dict con todos los datos (parseado desde el campo 'data')
      - 'image_url': URL firmada de la imagen
    """
    import json as _json
    cfg = TABLE_CONFIG["bestiary"]
    url = f"{NOCODB_URL}/api/v2/tables/{cfg['table_id']}/records/{record_id}"
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    record = r.json()

    raw_data = record.get("data") or "{}"
    if isinstance(raw_data, str):
        creature = _json.loads(raw_data)
    else:
        creature = raw_data
    # data puede llegar como lista [{}] — extraer el primer elemento
    if isinstance(creature, list):
        creature = creature[0] if creature else {}

    image_url = None
    attachments = record.get("image") or []
    if attachments:
        signed_path = attachments[0].get("signedPath")
        if signed_path:
            image_url = f"{NOCODB_URL}/{signed_path}"

    return {"creature": creature, "image_url": image_url}

if __name__ == "__main__":
    import json
    import sys

    table = sys.argv[1] if len(sys.argv) > 1 else "power"
    print(f"Consultando tabla: {table}")
    data = get_table(table)
    print(json.dumps(data, ensure_ascii=False, indent=2))
