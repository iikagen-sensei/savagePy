# app.py
from flask import Flask, render_template, jsonify, send_file, Response, request, redirect, url_for
from pathlib import Path
import io
import json
import requests as req
from config import NOCODB_URL, API_TOKEN, TABLE_CONFIG, DOCUMENTS
from nocodb_client import get_table, get_characters, get_character, get_bestiary_entries, get_bestiary_entry, get_rules, get_rule, get_reference_books
from jinja2 import Environment, FileSystemLoader
import markdown as _markdown_lib

app = Flask(__name__)

TEMPLATES_DIR = Path(__file__).parent / "templates"
DOCUMENTS_DIR = TEMPLATES_DIR / "documents"


def _find_doc(doc_id: str):
    """Busca un documento en DOCUMENTS por su id. Devuelve (doc, table_key) o (None, None)."""
    for t_key, t_cfg in DOCUMENTS.items():
        for doc in t_cfg["docs"]:
            if doc["id"] == doc_id:
                return doc, t_key
    return None, None


def _doc_type(doc: dict) -> str:
    """Devuelve 'html', 'docx' o 'md' según la extensión del template."""
    return Path(doc["template"]).suffix.lstrip(".")


def _make_jinja_env() -> Environment:
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    env.filters["markdown"] = lambda text: _markdown_lib.markdown(text or "", extensions=["tables", "nl2br"])
    return env


def _resolve_view_name(table_key: str, view_id: str | None) -> str:
    if not view_id:
        return ""
    try:
        table_id = TABLE_CONFIG[table_key]["table_id"]
        headers = {"xc-token": API_TOKEN}
        url = f"{NOCODB_URL}/api/v2/meta/tables/{table_id}/views"
        r = req.get(url, headers=headers, timeout=5)
        r.raise_for_status()
        for v in r.json().get("list", []):
            if v["id"] == view_id:
                return v["title"].removeprefix("pub:").strip()
    except Exception:
        pass
    return ""


def _get_data(table_key: str, view_id: str | None):
    if table_key == "bestiary":
        return get_bestiary_entries(view_id=view_id, full=True)
    return get_table(table_key, view_id=view_id)


def render_document(doc_id: str, view_id: str | None = None) -> str:
    """Renderiza un documento HTML y devuelve el string."""
    doc, table_key = _find_doc(doc_id)
    if not doc:
        raise ValueError(f"Documento '{doc_id}' no encontrado")
    data = _get_data(table_key, view_id)
    view_name = _resolve_view_name(table_key, view_id)
    env = _make_jinja_env()
    template = env.get_template(doc["template"])
    return template.render(**{doc["data_key"]: data}, view_name=view_name, nocodb_url=NOCODB_URL)


# ── RUTAS ──────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("ui/index.html", documents=DOCUMENTS)


@app.route("/api/status")
def status():
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
    if table_key not in TABLE_CONFIG:
        return jsonify({"error": "Tabla no encontrada"}), 404
    table_id = TABLE_CONFIG[table_key]["table_id"]
    headers = {"xc-token": API_TOKEN}
    try:
        url = f"{NOCODB_URL}/api/v2/meta/tables/{table_id}/views"
        r = req.get(url, headers=headers, timeout=5)
        r.raise_for_status()
        PREFIX = "pub:"
        views = [
            {"id": v["id"], "title": v["title"].removeprefix(PREFIX).strip()}
            for v in r.json().get("list", [])
            if v["title"].startswith(PREFIX)
        ]
        return jsonify(views)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/preview/<doc_id>")
def preview(doc_id: str):
    view_id = request.args.get("view_id") or None
    try:
        html = render_document(doc_id, view_id=view_id)
    except ValueError:
        return "Documento no encontrado", 404
    return Response(html, mimetype="text/html")


@app.route("/download/<doc_id>/html")
def download_html(doc_id: str):
    view_id = request.args.get("view_id") or None
    try:
        html = render_document(doc_id, view_id=view_id)
    except ValueError:
        return "Documento no encontrado", 404
    return Response(html, mimetype="text/html",
                    headers={"Content-Disposition": f"attachment; filename={doc_id}.html"})


@app.route("/download/<doc_id>/pdf")
def download_pdf(doc_id: str):
    view_id = request.args.get("view_id") or None
    doc, table_key = _find_doc(doc_id)
    if not doc:
        return "Documento no encontrado", 404
    if _doc_type(doc) != "html":
        return "Este documento no tiene formato PDF", 400
    try:
        from weasyprint import HTML
    except ImportError:
        return "WeasyPrint no instalado", 500
    try:
        html = render_document(doc_id, view_id=view_id)
    except ValueError:
        return "Documento no encontrado", 404
    pdf_bytes = HTML(string=html, base_url=str(TEMPLATES_DIR)).write_pdf()
    view_name = _resolve_view_name(table_key, view_id)
    filename = f"{doc_id}{'_' + view_name if view_name else ''}.pdf"
    return send_file(io.BytesIO(pdf_bytes), mimetype="application/pdf",
                     as_attachment=True, download_name=filename)


@app.route("/download/<doc_id>/docx")
def download_docx(doc_id: str):
    from docx_generator import render_docx_template, render_md_template
    view_id = request.args.get("view_id") or None
    doc, table_key = _find_doc(doc_id)
    if not doc:
        return "Documento no encontrado", 404

    dtype = _doc_type(doc)
    if dtype not in ("docx", "md"):
        return "Este documento no tiene formato Word", 400

    data = _get_data(table_key, view_id)
    view_name = _resolve_view_name(table_key, view_id)
    template_path = DOCUMENTS_DIR / Path(doc["template"]).name
    context = {doc["data_key"]: data, "view_name": view_name, "titulo": doc["label"]}
    filename = f"{doc_id}{'_' + view_name if view_name else ''}.docx"

    if dtype == "md":
        docx_bytes = render_md_template(template_path, context)
    else:
        docx_bytes = render_docx_template(template_path, context)

    return send_file(io.BytesIO(docx_bytes),
                     mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                     as_attachment=True, download_name=filename)


# ── PERSONAJES ────────────────────────────────────────────────────────────

@app.route("/preview/characters")
def preview_characters():
    view_id = request.args.get("view_id") or None
    try:
        char_list = get_characters(view_id=view_id)
    except Exception as e:
        return f"Error al cargar personajes: {e}", 500
    env = _make_jinja_env()
    template = env.get_template("documents/character_sheet.html")
    pages = []
    for record in char_list:
        result = get_character(record["Id"])
        if not result["character"]:
            continue
        pages.append(template.render(character=result["character"], image_url=result["image_url"]))
    if not pages:
        return "No hay personajes con datos en esta vista", 404
    return Response("\n".join(pages), mimetype="text/html")


@app.route("/download/characters/pdf")
def download_characters_pdf():
    view_id = request.args.get("view_id") or None
    try:
        from weasyprint import HTML as WeasyprintHTML
    except ImportError:
        return "WeasyPrint no instalado", 500
    try:
        char_list = get_characters(view_id=view_id)
    except Exception as e:
        return f"Error al cargar personajes: {e}", 500
    env = _make_jinja_env()
    template = env.get_template("documents/character_sheet.html")
    pages = []
    for record in char_list:
        result = get_character(record["Id"])
        if not result["character"]:
            continue
        pages.append(template.render(character=result["character"], image_url=result["image_url"]))
    if not pages:
        return "No hay personajes con datos en esta vista", 404
    pdf_bytes = WeasyprintHTML(string="\n".join(pages), base_url=str(TEMPLATES_DIR)).write_pdf()
    return send_file(io.BytesIO(pdf_bytes), mimetype="application/pdf",
                     as_attachment=True, download_name="personajes.pdf")


# ── GESTIÓN DE PERSONAJES ─────────────────────────────────────────────────

@app.route("/characters")
def characters_list():
    try:
        chars = get_characters(full=True, view_id=TABLE_CONFIG["character"]["view_id"])
    except Exception:
        chars = []
    return render_template("ui/characters.html", characters=chars)


@app.route("/characters/new")
def character_new():
    return render_template("ui/character_form.html", record_id=None, character=None, image_url=None)


@app.route("/characters/<int:record_id>/edit")
def character_edit(record_id: int):
    try:
        result = get_character(record_id)
    except Exception as e:
        return f"Error al cargar personaje: {e}", 500
    return render_template("ui/character_form.html", record_id=record_id,
                           character=result["character"], image_url=result["image_url"])


@app.route("/characters/save", methods=["POST"])
def character_save():
    record_id = request.form.get("record_id") or None
    character_json = request.form.get("character_json", "{}")
    image_file = request.files.get("image")
    cfg = TABLE_CONFIG["character"]
    headers = {"xc-token": API_TOKEN}
    record_data = {"name": json.loads(character_json).get("name", "Sin nombre"), "data": character_json}
    try:
        if record_id:
            record_data["Id"] = int(record_id)
            r = req.patch(f"{NOCODB_URL}/api/v2/tables/{cfg['table_id']}/records", headers=headers, json=record_data)
        else:
            r = req.post(f"{NOCODB_URL}/api/v2/tables/{cfg['table_id']}/records", headers=headers, json=record_data)
        r.raise_for_status()
        saved_id = int(record_id) if record_id else (r.json()[0].get("Id") if isinstance(r.json(), list) else r.json().get("Id"))
        if image_file and image_file.filename:
            upload_r = req.post(f"{NOCODB_URL}/api/v2/storage/upload", headers={"xc-token": API_TOKEN},
                                files={"file": (image_file.filename, image_file.stream, image_file.mimetype)})
            upload_r.raise_for_status()
            attachment = upload_r.json()
            if isinstance(attachment, list):
                attachment = attachment[0]
            req.patch(f"{NOCODB_URL}/api/v2/tables/{cfg['table_id']}/records",
                      headers=headers, json={"Id": saved_id, "image": [attachment]})
    except Exception as e:
        return f"Error al guardar: {e}", 500
    return redirect(url_for("characters_list"))


@app.route("/characters/<int:record_id>/delete", methods=["POST"])
def character_delete(record_id: int):
    cfg = TABLE_CONFIG["character"]
    headers = {"xc-token": API_TOKEN}
    try:
        r = req.delete(f"{NOCODB_URL}/api/v2/tables/{cfg['table_id']}/records", headers=headers, json={"Id": record_id})
        r.raise_for_status()
    except Exception as e:
        return f"Error al eliminar: {e}", 500
    return redirect(url_for("characters_list"))


@app.route("/api/form-data")
def form_data():
    try:
        return jsonify({
            "skills":     get_table("skill"),
            "edges":      get_table("edge"),
            "hindrances": get_table("hindrance"),
            "powers":     get_table("power"),
            "ancestries": get_table("ancestry"),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── GESTIÓN DE BESTIARIO ──────────────────────────────────────────────────

@app.route("/bestiary")
def bestiary_list():
    try:
        creatures = get_bestiary_entries(full=True, view_id=TABLE_CONFIG["bestiary"]["view_id"])
    except Exception:
        creatures = []
    return render_template("ui/bestiary.html", creatures=creatures)


@app.route("/bestiary/new")
def bestiary_new():
    return render_template("ui/bestiary_form.html", record_id=None, creature=None, image_url=None)


@app.route("/bestiary/<int:record_id>/edit")
def bestiary_edit(record_id: int):
    try:
        result = get_bestiary_entry(record_id)
    except Exception as e:
        return f"Error al cargar criatura: {e}", 500
    return render_template("ui/bestiary_form.html", record_id=record_id,
                           creature=result["creature"], image_url=result["image_url"])


@app.route("/bestiary/save", methods=["POST"])
def bestiary_save():
    record_id = request.form.get("record_id") or None
    creature_json = request.form.get("creature_json", "{}")
    image_file = request.files.get("image")
    cfg = TABLE_CONFIG["bestiary"]
    headers = {"xc-token": API_TOKEN}
    parsed = json.loads(creature_json)
    record_data = {"name": parsed.get("name", "Sin nombre"), "type": parsed.get("type", ""),
                   "concept": parsed.get("concept", ""), "data": creature_json}
    try:
        if record_id:
            record_data["Id"] = int(record_id)
            r = req.patch(f"{NOCODB_URL}/api/v2/tables/{cfg['table_id']}/records", headers=headers, json=record_data)
        else:
            r = req.post(f"{NOCODB_URL}/api/v2/tables/{cfg['table_id']}/records", headers=headers, json=record_data)
        r.raise_for_status()
        saved_id = int(record_id) if record_id else (r.json()[0].get("Id") if isinstance(r.json(), list) else r.json().get("Id"))
        if image_file and image_file.filename:
            upload_r = req.post(f"{NOCODB_URL}/api/v2/storage/upload", headers={"xc-token": API_TOKEN},
                                files={"file": (image_file.filename, image_file.stream, image_file.mimetype)})
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
    cfg = TABLE_CONFIG["bestiary"]
    headers = {"xc-token": API_TOKEN}
    try:
        r = req.delete(f"{NOCODB_URL}/api/v2/tables/{cfg['table_id']}/records", headers=headers, json={"Id": record_id})
        r.raise_for_status()
    except Exception as e:
        return f"Error al eliminar: {e}", 500
    return redirect(url_for("bestiary_list"))


@app.route("/api/form-data/bestiary")
def form_data_bestiary():
    try:
        return jsonify({
            "skills":     get_table("skill",     view_id=TABLE_CONFIG["skill"]["view_id"]),
            "edges":      get_table("edge",      view_id=TABLE_CONFIG["edge"]["view_id"]),
            "hindrances": get_table("hindrance", view_id=TABLE_CONFIG["hindrance"]["view_id"]),
            "powers":     get_table("power",     view_id=TABLE_CONFIG["power"]["view_id"]),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/form-data/rules")
def form_data_rules():
    try:
        return jsonify({"books": get_reference_books()})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── GESTIÓN DE REGLAS ─────────────────────────────────────────────────────

@app.route("/rules")
def rules_list():
    try:
        rules = get_rules()
    except Exception:
        rules = []
    return render_template("ui/rules.html", rules=rules)


@app.route("/rules/new")
def rule_new():
    return render_template("ui/rule_form.html", record_id=None, rule=None)


@app.route("/rules/<int:record_id>/edit")
def rule_edit(record_id: int):
    try:
        rule = get_rule(record_id)
    except Exception as e:
        return f"Error al cargar regla: {e}", 500
    return render_template("ui/rule_form.html", record_id=record_id, rule=rule)


@app.route("/rules/save", methods=["POST"])
def rule_save():
    record_id = request.form.get("record_id") or None
    cfg = TABLE_CONFIG["rule"]
    headers = {"xc-token": API_TOKEN}
    ref_book_id = request.form.get("reference_book_id", "").strip()
    record_data = {
        "name":          request.form.get("name", ""),
        "name_original": request.form.get("name_original", ""),
        "description":   request.form.get("description", ""),
        "content":       request.form.get("content", ""),
        "source":        request.form.get("source", "Propio"),
        "icon":          request.form.get("icon", ""),
        "page_no":       int(request.form.get("page_no")) if request.form.get("page_no", "").strip() else None,
    }
    if ref_book_id:
        record_data["nc_a70b___reference_book_id"] = int(ref_book_id)
    try:
        url = f"{NOCODB_URL}/api/v2/tables/{cfg['table_id']}/records"
        if record_id:
            record_data["Id"] = int(record_id)
            r = req.patch(url, headers=headers, json=record_data)
        else:
            r = req.post(url, headers=headers, json=record_data)
        if not r.ok:
            return f"Error al guardar: {r.text}", 500
    except Exception as e:
        return f"Error al guardar: {e}", 500
    return redirect(url_for("rules_list"))


@app.route("/rules/<int:record_id>/delete", methods=["POST"])
def rule_delete(record_id: int):
    cfg = TABLE_CONFIG["rule"]
    headers = {"xc-token": API_TOKEN}
    try:
        r = req.delete(f"{NOCODB_URL}/api/v2/tables/{cfg['table_id']}/records",
                       headers=headers, json={"Id": record_id})
        r.raise_for_status()
    except Exception as e:
        return f"Error al eliminar: {e}", 500
    return redirect(url_for("rules_list"))


# ── GLOSARIO ───────────────────────────────────────────────────────────────

@app.route("/glosario")
def glosario():
    tabs = [
        ("power",     "Poderes"),
        ("edge",      "Ventajas"),
        ("hindrance", "Desventajas"),
        ("skill",     "Habilidades"),
    ]
    data = {}
    for key, _ in tabs:
        records = get_table(key)
        data[key] = [
            {"name": r.get("name") or "", "name_original": r.get("name_original")}
            for r in records if r.get("name")
        ]
    return render_template("ui/glosario.html", tabs=tabs, data=data)


if __name__ == "__main__":
    print("🎲 Savage Worlds Generator")
    print("   http://localhost:5000")
    app.run(debug=True, port=5000)
