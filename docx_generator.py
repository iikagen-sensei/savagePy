"""
docx_generator.py
Renderiza un template .docx con docxtpl + prepara el contexto de datos.
Los templates usan sintaxis Jinja2 estándar: {{ }}, {% %}, {% endfor %}.
"""
import io
from pathlib import Path


def render_docx_template(template_path: Path, context: dict) -> bytes:
    from docxtpl import DocxTemplate
    tpl = DocxTemplate(template_path)
    tpl.render(context)
    buf = io.BytesIO()
    tpl.save(buf)
    return buf.getvalue()


def build_powers_context(data: list, titulo: str = "Poderes", view_name: str = "") -> dict:
    # Datos en crudo — usa {{ p.name }}, {{ p.cost }}, {{ p.description }}...
    # Datos agrupados y formateados — usa {{ entrada.nombre }}, {{ entrada.coste_label }}...
    grupos = {}
    for p in data:
        cat = p.get("rank_name") or "Sin rango"
        grupos.setdefault(cat, []).append(p)

    bloques = []
    for cat, items in grupos.items():
        entradas = []
        for p in items:
            nombre = p.get("name", "")
            if p.get("name_original"):
                nombre += f" ({p['name_original']})"
            ref = p.get("reference_book") or {}
            fuente = ref.get("title", "")
            if p.get("page_no"):
                fuente += f" p.{p['page_no']}"
            mods = []
            for m in (p.get("modifiers") or []):
                t = m.get("title", "")
                if m.get("cost"):
                    t += f" ({m['cost']})"
                mods.append({"titulo": t, "descripcion": m.get("description", "")})
            entradas.append({
                # Campos formateados (labels)
                "nombre":          nombre,
                "coste_label":     f"Coste: {p['cost']} PP" if p.get("cost") else "",
                "alcance_label":   f"Alcance: {p.get('range_roh') or p.get('range', '')}" if (p.get("range_roh") or p.get("range")) else "",
                "duracion_label":  f"Duración: {p['duration']}" if p.get("duration") else "",
                "fuente":          fuente,
                "descripcion":     p.get("description", ""),
                "modificadores":   mods,
                # Campos en crudo (nombres tal cual vienen de NocoDB)
                **p,
            })
        bloques.append({"categoria": cat, "entradas": entradas})

    return {"titulo": titulo, "view_name": view_name, "bloques": bloques, "powers": data}


def build_edges_context(data: list, titulo: str = "Ventajas", view_name: str = "") -> dict:
    # Datos en crudo — usa {{ e.title }}, {{ e.requirements }}, {{ e.description }}...
    # Datos agrupados y formateados — usa {{ entrada.nombre }}, {{ entrada.requisitos_label }}...
    grupos = {}
    for e in data:
        cat = e.get("type") or e.get("rank_name") or "General"
        grupos.setdefault(cat, []).append(e)

    bloques = []
    for cat, items in grupos.items():
        entradas = []
        for e in items:
            nombre = e.get("title") or e.get("name") or ""
            if e.get("name_original"):
                nombre += f" ({e['name_original']})"
            ref = e.get("reference_book") or {}
            fuente = ref.get("title", "")
            if e.get("page_no"):
                fuente += f" p.{e['page_no']}"
            entradas.append({
                # Campos formateados (labels)
                "nombre":           nombre,
                "requisitos_label": f"Requisitos: {e['requirements']}" if e.get("requirements") else "",
                "fuente":           fuente,
                "descripcion":      e.get("description", ""),
                # Campos en crudo
                **e,
            })
        bloques.append({"categoria": cat, "entradas": entradas})

    return {"titulo": titulo, "view_name": view_name, "bloques": bloques, "edges": data}


def build_hindrances_context(data: list, titulo: str = "Desventajas", view_name: str = "") -> dict:
    # Datos en crudo — usa {{ h.Nombre }}, {{ h.type }}, {{ h.description }}...
    # Datos agrupados y formateados — usa {{ entrada.nombre }}, {{ entrada.fuente }}...
    grupos = {}
    for h in data:
        cat = h.get("type") or "General"
        grupos.setdefault(cat, []).append(h)

    bloques = []
    for cat, items in grupos.items():
        entradas = []
        for h in items:
            nombre = h.get("Nombre") or h.get("name") or h.get("title") or ""
            if h.get("name_original"):
                nombre += f" ({h['name_original']})"
            ref = h.get("reference_book") or {}
            fuente = ref.get("title", "")
            if h.get("page_no"):
                fuente += f" p.{h['page_no']}"
            entradas.append({
                # Campos formateados (labels)
                "nombre":      nombre,
                "fuente":      fuente,
                "descripcion": h.get("description", ""),
                # Campos en crudo
                **h,
            })
        bloques.append({"categoria": cat, "entradas": entradas})

    return {"titulo": titulo, "view_name": view_name, "bloques": bloques, "hindrances": data}


CONTEXT_BUILDERS = {
    "powers":     build_powers_context,
    "edges":      build_edges_context,
    "hindrances": build_hindrances_context,
}
