import requests

NOCODB_URL = "http://localhost:8080"
API_TOKEN = "ljW7X40ljTpyjzyTTkuAoGAFQflYNIGX7z4MrZxW"  # Cambia esto
BASE_ID = "pw16bcxvn0pv0xb"
TABLE_POWER = "mx88eizkev8cy9i"
FIELD_MODIFIER_LINK = "c48d1ciqk7ee110"

HEADERS = {
    "xc-token": API_TOKEN,
    "Content-Type": "application/json"
}


def get_powers() -> list[dict]:
    """Obtiene todos los poderes paginando si es necesario."""
    powers = []
    page = 1
    page_size = 25

    while True:
        url = f"{NOCODB_URL}/api/v2/tables/{TABLE_POWER}/records"
        params = {"page": page, "limit": page_size}
        r = requests.get(url, headers=HEADERS, params=params)
        r.raise_for_status()
        data = r.json()
        powers.extend(data["list"])

        if data["pageInfo"]["isLastPage"]:
            break
        page += 1

    return powers


def get_modifiers_for_power(row_id: int) -> list[dict]:
    """Obtiene los modifiers completos de un power dado su rowId."""
    url = f"{NOCODB_URL}/api/v2/tables/{TABLE_POWER}/links/{FIELD_MODIFIER_LINK}/records/{row_id}"
    params = {"fields": "title,cost,description"}
    r = requests.get(url, headers=HEADERS, params=params)
    r.raise_for_status()
    data = r.json()
    return data.get("list", [])


def build_powers_json() -> list[dict]:
    """Construye el JSON completo de poderes con sus modifiers anidados."""
    powers = get_powers()
    result = []

    for power in powers:
        modifiers = []
        if power.get("modifier", 0) > 0:
            modifiers = get_modifiers_for_power(power["Id"])

        result.append({
            "name": power.get("name", ""),
            "name_original": power.get("name_original", ""),
            "rank": power.get("rank_name", ""),
            "cost": power.get("cost", ""),
            "range": power.get("range", ""),
            "range_roh": power.get("range_roh", ""),
            "duration": power.get("duration", ""),
            "page_no": power.get("page_no"),
            "source": power.get("reference_book", {}).get("title", ""),
            "description": power.get("description", ""),
            "modifiers": [
                {
                    "title": m.get("title", ""),
                    "cost": m.get("cost", ""),
                    "description": m.get("description", "")
                }
                for m in modifiers
            ]
        })

    return result


if __name__ == "__main__":
    import json
    powers = build_powers_json()
    print(json.dumps(powers, ensure_ascii=False, indent=2))