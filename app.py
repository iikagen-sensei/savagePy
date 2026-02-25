# app.py
# Interfaz web para el generador de documentos Savage Worlds.
# Uso: python app.py  →  abre http://localhost:5000

from flask import Flask, render_template, jsonify, send_file, Response, request, redirect, url_for
from pathlib import Path
import io
import subprocess
import tempfile
import json
import requests as req
from config import NOCODB_URL, API_TOKEN, TABLE_CONFIG, DOCUMENTS
from nocodb_client import get_table, get_characters, get_character, get_bestiary_entries, get_bestiary_entry
from jinja2 import Environment, FileSystemLoader

app = Flask(__name__)

TEMPLATES_DIR = Path(__file__).parent / "templates"
DOCUMENTS_DIR = TEMPLATES_DIR / "documents"



def _resolve_view_name(table_key: str, view_id: str | None) -> str:
    """Devuelve el título legible de una vista dado su ID, o cadena vacía."""
    if not view_id:
        return ""
    try:
        table_id = TABLE_CONFIG[table_key]["table_id"]
        headers = {"xc-token": API_TOKEN}
        url = f"{NOCODB_URL}/api/v2/meta/tables/{table_id}/views"
        r = req.get(url, headers=headers, timeout=5)
        r.raise_for_status()
        PREFIX = "pub:"
        for v in r.json().get("list", []):
            if v["id"] == view_id:
                return v["title"].removeprefix(PREFIX).strip()
    except Exception:
        pass
    return ""


def render_document(doc_id: str, view_id: str | None = None) -> str:
    """Renderiza un documento y devuelve el HTML como string."""
    # Buscar el documento en cualquier tabla
    doc = None
    table_key = None
    for t_key, t_cfg in DOCUMENTS.items():
        if doc_id in t_cfg["docs"]:
            doc = t_cfg["docs"][doc_id]
            table_key = t_key
            break
    if not doc:
        raise ValueError(f"Documento '{doc_id}' no encontrado")

    # Obtener datos según el tipo de tabla
    if table_key == "bestiary":
        data = get_bestiary_entries(view_id=view_id, full=True)
    else:
        data = get_table(table_key, view_id=view_id)

    view_name = _resolve_view_name(table_key, view_id)

    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    template = env.get_template(doc["template"])
    return template.render(**{doc["data_key"]: data}, view_name=view_name, nocodb_url=NOCODB_URL)


# ── RUTAS ──────────────────────────────────────────────────────────────────

def _docs_with_docx_template() -> set:
    """Devuelve el conjunto de doc_ids que tienen un _template.docx en templates/."""
    return {p.stem.replace("_template", "") for p in DOCUMENTS_DIR.glob("*_template.docx")}


@app.route("/")
def index():
    return render_template("ui/index.html", documents=DOCUMENTS, docx_docs=_docs_with_docx_template())


@app.route("/api/status")
def status():
    """Devuelve el estado de NocoDB: cuántos registros hay en cada tabla."""
    headers = {"xc-token": API_TOKEN}
    counts = {}
    for key, cfg in TABLE_CONFIG.items():
        try:
            url = f"{NOCODB_URL}/api/v2/tables/{cfg['table_id']}/records?limit=1"
            r = req.get(url, headers=headers, timeout=5)
            r.raise_for_status()
            counts[key] = r.json()["pageInfo"]["totalRows"]
        except Exception:
            counts[key] = None
    return jsonify(counts)


@app.route("/api/views/<table_key>")
def get_views(table_key: str):
    """Devuelve las vistas disponibles de una tabla desde NocoDB."""
    if table_key not in TABLE_CONFIG:
        return jsonify({"error": "Tabla no encontrada"}), 404
    table_id = TABLE_CONFIG[table_key]["table_id"]
    headers = {"xc-token": API_TOKEN}
    try:
        url = f"{NOCODB_URL}/api/v2/meta/tables/{table_id}/views"
        r = req.get(url, headers=headers, timeout=5)
        r.raise_for_status()
        PREFIX = "pub:"  # Solo se muestran vistas cuyo nombre empiece por "pub:"
        all_views = r.json().get("list", [])
        views = [
            {"id": v["id"], "title": v["title"].removeprefix(PREFIX).strip()}
            for v in all_views
            if v["title"].startswith(PREFIX)
        ]
        return jsonify(views)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/preview/<doc_id>")
def preview(doc_id: str):
    """Previsualiza el documento en el navegador."""
    view_id = request.args.get("view_id") or None
    try:
        html = render_document(doc_id, view_id=view_id)
    except ValueError:
        return "Documento no encontrado", 404
    return Response(html, mimetype="text/html")


@app.route("/download/<doc_id>/html")
def download_html(doc_id: str):
    """Descarga el documento como HTML."""
    view_id = request.args.get("view_id") or None
    try:
        html = render_document(doc_id, view_id=view_id)
    except ValueError:
        return "Documento no encontrado", 404
    return Response(
        html,
        mimetype="text/html",
        headers={"Content-Disposition": f"attachment; filename={doc_id}.html"}
    )


@app.route("/download/<doc_id>/docx")
def download_docx(doc_id: str):
    """Descarga el documento como Word usando la plantilla templates/<doc_id>_template.docx."""
    from docx_generator import render_docx_template, CONTEXT_BUILDERS

    view_id = request.args.get("view_id") or None

    # Buscar doc y tabla
    doc = None
    table_key = None
    for t_key, t_cfg in DOCUMENTS.items():
        if doc_id in t_cfg["docs"]:
            doc = t_cfg["docs"][doc_id]
            table_key = t_key
            break
    if not doc:
        return "Documento no encontrado", 404

    template_path = TEMPLATES_DIR / f"{doc_id}_template.docx"
    if not template_path.exists():
        return f"No existe plantilla Word para '{doc_id}'. Añade templates/{doc_id}_template.docx", 404

    if table_key == "bestiary":
        data = get_bestiary_entries(view_id=view_id, full=True)
    else:
        data = get_table(table_key, view_id=view_id)

    view_name = _resolve_view_name(table_key, view_id)

    builder = CONTEXT_BUILDERS.get(doc_id)
    if builder:
        context = builder(data, titulo=doc["label"], view_name=view_name)
    else:
        context = {doc["data_key"]: data, "view_name": view_name, "titulo": doc["label"]}

    docx_bytes = render_docx_template(template_path, context)

    filename = f"{doc_id}{'_' + view_name if view_name else ''}.docx"
    return send_file(
        io.BytesIO(docx_bytes),
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        as_attachment=True,
        download_name=filename
    )


@app.route("/download/<doc_id>/pdf")
def download_pdf(doc_id: str):
    """Descarga el documento como PDF."""
    view_id = request.args.get("view_id") or None
    try:
        from weasyprint import HTML
    except ImportError:
        return "WeasyPrint no instalado. Ejecuta: pip install weasyprint", 500
    try:
        html = render_document(doc_id, view_id=view_id)
    except ValueError:
        return "Documento no encontrado", 404
    pdf_bytes = HTML(string=html, base_url=str(TEMPLATES_DIR)).write_pdf()
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"{doc_id}.pdf"
    )


# ── PERSONAJES ────────────────────────────────────────────────────────────

@app.route("/preview/characters")
def preview_characters():
    """Previsualiza las fichas de todos los personajes de una vista."""
    view_id = request.args.get("view_id") or None
    try:
        char_list = get_characters(view_id=view_id)
    except Exception as e:
        return f"Error al cargar personajes: {e}", 500
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    template = env.get_template("documents/character_sheet.html")
    # Renderizar cada personaje y concatenar
    pages = []
    for record in char_list:
        result = get_character(record["Id"])
        if not result["character"]:
            continue
        pages.append(template.render(
            character=result["character"],
            image_url=result["image_url"]
        ))
    if not pages:
        return "No hay personajes con datos en esta vista", 404
    combined = "\n".join(pages)
    return Response(combined, mimetype="text/html")


@app.route("/download/characters/pdf")
def download_characters_pdf():
    """Descarga las fichas de todos los personajes de una vista como un solo PDF."""
    view_id = request.args.get("view_id") or None
    try:
        from weasyprint import HTML as WeasyprintHTML
    except ImportError:
        return "WeasyPrint no instalado. Ejecuta: pip install weasyprint", 500
    try:
        char_list = get_characters(view_id=view_id)
    except Exception as e:
        return f"Error al cargar personajes: {e}", 500
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    template = env.get_template("documents/character_sheet.html")
    pages = []
    for record in char_list:
        result = get_character(record["Id"])
        if not result["character"]:
            continue  # saltar registros sin datos
        pages.append(template.render(
            character=result["character"],
            image_url=result["image_url"]
        ))
    if not pages:
        return "No hay personajes con datos en esta vista", 404
    combined = "\n".join(pages)
    pdf_bytes = WeasyprintHTML(string=combined, base_url=str(TEMPLATES_DIR)).write_pdf()
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name="personajes.pdf"
    )


# ── GESTIÓN DE PERSONAJES ─────────────────────────────────────────────────

@app.route("/characters")
def characters_list():
    """Lista todos los personajes obteniendo todos los datos necesarios para
    la vista de gestión.

    Anteriormente se usaba ``get_characters()`` en modo ligero, lo que
    devolvía solo ``Id`` y ``name``; la plantilla esperaba también campos
    como ``data`` y ``image_url`` y se producían errores (caracteres sin
    imagen y rutas de edición con identificadores vacíos). Ahora solicitamos
    los registros en el modo completo.
    """
    try:
        chars = get_characters(full=True)
    except Exception as e:
        chars = []
    return render_template("ui/characters.html", characters=chars)


@app.route("/characters/new")
def character_new():
    """Formulario de nuevo personaje."""
    return render_template("ui/character_form.html", record_id=None, character=None, image_url=None)


@app.route("/characters/<int:record_id>/edit")
def character_edit(record_id: int):
    """Formulario de edición de personaje existente."""
    try:
        result = get_character(record_id)
    except Exception as e:
        return f"Error al cargar personaje: {e}", 500
    return render_template("ui/character_form.html",
                           record_id=record_id,
                           character=result["character"],
                           image_url=result["image_url"])


@app.route("/characters/save", methods=["POST"])
def character_save():
    """Guarda o actualiza un personaje en NocoDB."""
    import base64
    record_id = request.form.get("record_id") or None
    character_json = request.form.get("character_json", "{}")
    image_file = request.files.get("image")

    cfg = TABLE_CONFIG["character"]
    headers = {"xc-token": API_TOKEN}

    # Preparar datos del registro
    record_data = {
        "name": json.loads(character_json).get("name", "Sin nombre"),
        "data": character_json
    }

    try:
        if record_id:
            # Actualizar registro existente
            url = f"{NOCODB_URL}/api/v2/tables/{cfg['table_id']}/records"
            record_data["Id"] = int(record_id)
            r = req.patch(url, headers=headers, json=record_data)
        else:
            # Crear registro nuevo
            url = f"{NOCODB_URL}/api/v2/tables/{cfg['table_id']}/records"
            r = req.post(url, headers=headers, json=record_data)
        r.raise_for_status()
        saved_id = int(record_id) if record_id else r.json().get("Id", r.json()[0].get("Id") if isinstance(r.json(), list) else None)

        # Subir imagen si se proporcionó
        if image_file and image_file.filename:
            img_headers = {"xc-token": API_TOKEN}
            # 1. Subir fichero al storage de NocoDB
            upload_url = f"{NOCODB_URL}/api/v2/storage/upload"
            files = {"file": (image_file.filename, image_file.stream, image_file.mimetype)}
            upload_r = req.post(upload_url, headers=img_headers, files=files)
            upload_r.raise_for_status()
            attachment = upload_r.json()
            if isinstance(attachment, list):
                attachment = attachment[0]
            # 2. Asociar el attachment al campo image del registro
            patch_url = f"{NOCODB_URL}/api/v2/tables/{cfg['table_id']}/records"
            patch_data = {"Id": saved_id, "image": [attachment]}
            req.patch(patch_url, headers={**img_headers, "Content-Type": "application/json"}, json=patch_data)

    except Exception as e:
        return f"Error al guardar: {e}", 500

    return redirect(url_for("characters_list"))


@app.route("/characters/<int:record_id>/delete", methods=["POST"])
def character_delete(record_id: int):
    """Elimina un personaje."""
    cfg = TABLE_CONFIG["character"]
    headers = {"xc-token": API_TOKEN}
    try:
        url = f"{NOCODB_URL}/api/v2/tables/{cfg['table_id']}/records"
        r = req.delete(url, headers=headers, json={"Id": record_id})
        r.raise_for_status()
    except Exception as e:
        return f"Error al eliminar: {e}", 500
    return redirect(url_for("characters_list"))


@app.route("/api/form-data")
def form_data():
    """Devuelve todos los datos necesarios para el formulario de personaje."""
    try:
        skills     = get_table("skill")
        edges      = get_table("edge")
        hindrances = get_table("hindrance")
        powers     = get_table("power")
        ancestries = get_table("ancestry")
        return jsonify({
            "skills":     skills,
            "edges":      edges,
            "hindrances": hindrances,
            "powers":     powers,
            "ancestries": ancestries,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── GESTIÓN DE BESTIARIO ──────────────────────────────────────────────────

@app.route("/bestiary")
def bestiary_list():
    """Lista todas las criaturas del bestiario."""
    try:
        creatures = get_bestiary_entries(full=True)
    except Exception as e:
        creatures = []
    return render_template("ui/bestiary.html", creatures=creatures)


@app.route("/bestiary/new")
def bestiary_new():
    """Formulario de nueva criatura."""
    return render_template("ui/bestiary_form.html", record_id=None, creature=None, image_url=None)


@app.route("/bestiary/<int:record_id>/edit")
def bestiary_edit(record_id: int):
    """Formulario de edición de criatura existente."""
    try:
        result = get_bestiary_entry(record_id)
    except Exception as e:
        return f"Error al cargar criatura: {e}", 500
    return render_template("ui/bestiary_form.html",
                           record_id=record_id,
                           creature=result["creature"],
                           image_url=result["image_url"])


@app.route("/bestiary/save", methods=["POST"])
def bestiary_save():
    """Guarda o actualiza una criatura en NocoDB."""
    record_id = request.form.get("record_id") or None
    creature_json = request.form.get("creature_json", "{}")
    image_file = request.files.get("image")

    cfg = TABLE_CONFIG["bestiary"]
    headers = {"xc-token": API_TOKEN}

    parsed = json.loads(creature_json)
    record_data = {
        "name":    parsed.get("name", "Sin nombre"),
        "type":    parsed.get("type", ""),
        "concept": parsed.get("concept", ""),
        "data":    creature_json,
    }

    try:
        if record_id:
            record_data["Id"] = int(record_id)
            r = req.patch(f"{NOCODB_URL}/api/v2/tables/{cfg['table_id']}/records",
                          headers=headers, json=record_data)
        else:
            r = req.post(f"{NOCODB_URL}/api/v2/tables/{cfg['table_id']}/records",
                         headers=headers, json=record_data)
        r.raise_for_status()
        saved_id = int(record_id) if record_id else (
            r.json()[0].get("Id") if isinstance(r.json(), list) else r.json().get("Id")
        )

        if image_file and image_file.filename:
            upload_url = f"{NOCODB_URL}/api/v2/storage/upload"
            files = {"file": (image_file.filename, image_file.stream, image_file.mimetype)}
            upload_r = req.post(upload_url, headers={"xc-token": API_TOKEN}, files=files)
            upload_r.raise_for_status()
            attachment = upload_r.json()
            if isinstance(attachment, list):
                attachment = attachment[0]
            req.patch(f"{NOCODB_URL}/api/v2/tables/{cfg['table_id']}/records",
                      headers=headers, json={"Id": saved_id, "image": [attachment]})

    except Exception as e:
        return f"Error al guardar: {e}", 500

    return redirect(url_for("bestiary_list"))


@app.route("/bestiary/<int:record_id>/delete", methods=["POST"])
def bestiary_delete(record_id: int):
    """Elimina una criatura del bestiario."""
    cfg = TABLE_CONFIG["bestiary"]
    headers = {"xc-token": API_TOKEN}
    try:
        r = req.delete(f"{NOCODB_URL}/api/v2/tables/{cfg['table_id']}/records",
                       headers=headers, json={"Id": record_id})
        r.raise_for_status()
    except Exception as e:
        return f"Error al eliminar: {e}", 500
    return redirect(url_for("bestiary_list"))


@app.route("/api/form-data/bestiary")
def form_data_bestiary():
    """Datos para el formulario de criatura (habilidades, ventajas, etc.)."""
    try:
        # Usar view_id de config para respetar orden y filtros de NocoDB
        skills     = get_table("skill",     view_id=TABLE_CONFIG["skill"]["view_id"])
        edges      = get_table("edge",      view_id=TABLE_CONFIG["edge"]["view_id"])
        hindrances = get_table("hindrance", view_id=TABLE_CONFIG["hindrance"]["view_id"])
        powers     = get_table("power",     view_id=TABLE_CONFIG["power"]["view_id"])
        return jsonify({
            "skills":     skills,
            "edges":      edges,
            "hindrances": hindrances,
            "powers":     powers,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("🎲 Savage Worlds Generator")
    print("   http://localhost:5000")
    app.run(debug=True, port=5000)