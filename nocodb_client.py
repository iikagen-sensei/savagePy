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


if __name__ == "__main__":
    import json
    import sys

    table = sys.argv[1] if len(sys.argv) > 1 else "power"
    print(f"Consultando tabla: {table}")
    data = get_table(table)
    print(json.dumps(data, ensure_ascii=False, indent=2))