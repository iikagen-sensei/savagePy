import requests
import json

# URL exacta de tu snippet
url = "http://localhost:8080/api/v2/tables/mr9wckj7cenfu9e/records"

# Parámetros de búsqueda (opcionales por ahora)
params = {
    "offset": 0,
    "limit": 25,
    "viewId": "vwqmlutdaqrsfe65"
}

# RECUERDA: Cambia esto por el token que generaste en el dashboard
headers = {
    "xc-token": "ljW7X40ljTpyjzyTTkuAoGAFQflYNIGX7z4MrZxW",
    "Content-Type": "application/json"
}

try:
    # Hacemos la petición pasando los parámetros
    response = requests.get(url, headers=headers, params=params)
    
    # Comprobamos si hay errores de autorización o de ruta
    response.raise_for_status()
    
    data = response.json()
    
    # Imprimimos de forma bonita (indentado) para ver la estructura
    print(json.dumps(data, indent=2))

except requests.exceptions.HTTPError as err:
    print(f"Error HTTP: {err}")
except Exception as e:
    print(f"Ha ocurrido un error: {e}")