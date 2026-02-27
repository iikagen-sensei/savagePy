"""
docx_generator.py
Renderiza templates .docx (docxtpl) y .md (Jinja2 + pypandoc).
Los templates reciben los datos en crudo directamente desde NocoDB.
No hay preparación de contexto — el template decide qué mostrar y cómo.
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


def render_md_template(template_path: Path, context: dict) -> bytes:
    """
    Renderiza un template .md con Jinja2, luego convierte el Markdown
    resultante a .docx con pypandoc.
    """
    import pypandoc
    import tempfile
    import os
    from jinja2 import Environment, FileSystemLoader

    env = Environment(loader=FileSystemLoader(str(template_path.parent)))
    template = env.get_template(template_path.name)
    md_content = template.render(**context)

    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        pypandoc.convert_text(md_content, "docx", format="md",
                              outputfile=tmp_path, extra_args=["--standalone"])
        with open(tmp_path, "rb") as f:
            return f.read()
    finally:
        os.unlink(tmp_path)
