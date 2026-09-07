import logging
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class _HTMLToMarkdown(HTMLParser):
    """Converteix HTML simple a text pla per marcar amb format MD."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self._text = []
        self._in_paragraph = False
        self._in_list_item = False
        self._bold = 0
        self._italic = 0
        self._skip_depth = 0  # per saltar html/head/body

    def handle_starttag(self, tag, attrs):
        if tag in ("html", "head", "body", "meta", "link", "style"):
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        if tag == "p":
            if self._in_paragraph:
                self._text.append("\n\n")
            self._in_paragraph = True
        elif tag == "br":
            self._text.append("\n")
        elif tag == "li":
            self._text.append("\n- ")
            self._in_list_item = True
        elif tag == "b" or tag == "strong":
            self._bold += 1
            self._text.append("**")
        elif tag == "i" or tag == "em":
            self._italic += 1
            self._text.append("*")
        elif tag == "u":
            pass  # MD no te subratllat
        elif tag in ("ul", "ol"):
            self._text.append("\n")

    def handle_endtag(self, tag):
        if tag in ("html", "head", "body", "meta", "link", "style"):
            self._skip_depth -= 1
            return
        if self._skip_depth:
            return
        if tag == "p":
            self._text.append("\n\n")
            self._in_paragraph = False
        elif tag == "li":
            self._in_list_item = False
        elif tag == "b" or tag == "strong":
            self._bold -= 1
            self._text.append("**")
        elif tag == "i" or tag == "em":
            self._italic -= 1
            self._text.append("*")

    def handle_data(self, data):
        if self._skip_depth:
            return
        self._text.append(data)

    def get_text(self) -> str:
        result = "".join(self._text)
        result = result.replace("\n\n\n", "\n\n")
        result = result.replace("  ", " ")
        return result.strip()


def _html_to_md(html_content: str) -> str:
    """Converteix HTML de les notes a text net per MD."""
    if not html_content:
        return ""
    parser = _HTMLToMarkdown()
    try:
        parser.feed(html_content)
        return parser.get_text()
    except Exception:
        return html_content


def _format_date(iso_date: str) -> str:
    """Formata data ISO a DD/MM/YYYY HH:MM."""
    if not iso_date:
        return ""
    try:
        dt = datetime.fromisoformat(iso_date)
        return dt.strftime("%d/%m/%Y %H:%M")
    except ValueError:
        return iso_date


def _note_to_md(note: dict[str, Any]) -> str:
    """Converteix una nota a format Markdown."""
    title = note.get("title", "Sense títol")
    created = _format_date(note.get("created_at", ""))
    updated = _format_date(note.get("updated_at", ""))
    note_id = note.get("id", "?")

    lines = []
    lines.append(f"## {title}")
    lines.append("")

    meta_parts = []
    if created:
        meta_parts.append(f"🕐 Creat: {created}")
    if updated:
        meta_parts.append(f"🔄 Actualitzat: {updated}")
    meta_parts.append(f"🆔 ID: {note_id}")
    lines.append(f"*{', '.join(meta_parts)}*")
    lines.append("")

    request = _html_to_md(note.get("request", ""))
    solution = _html_to_md(note.get("solution", ""))
    examples = _html_to_md(note.get("examples", ""))

    if request:
        lines.append("### 📋 Petició")
        lines.append("")
        lines.append(request)
        lines.append("")
    if solution:
        lines.append("### ✅ Solució")
        lines.append("")
        lines.append(solution)
        lines.append("")
    if examples:
        lines.append("### 📝 Exemples")
        lines.append("")
        lines.append(examples)
        lines.append("")

    return "\n".join(lines).strip()


def export_notes_to_md(
    notes: list[dict[str, Any]],
    output_path: Path,
    all_in_one: bool = True,
) -> str:
    """Exporta notes a Markdown.

    Si all_in_one=True, genera un sol fitxer amb totes les notes.
    Si all_in_one=False, genera un fitxer per nota.
    Retorna el path del fitxer(s) generat.
    """
    if all_in_one:
        return _export_all_in_one(notes, output_path)
    else:
        return _export_separate(notes, output_path)


def _export_all_in_one(notes: list[dict[str, Any]], output_path: Path) -> str:
    """Exporta totes les notes en un sol fitxer MD."""
    now = datetime.now().strftime("%d/%m/%Y %H:%M")

    lines = []
    lines.append("# 📚 JMEJCat - Notes Exportades")
    lines.append("")
    lines.append(f"*Exportat el: {now}* — *Total: {len(notes)} notes*")
    lines.append("")
    lines.append("---")
    lines.append("")

    for i, note in enumerate(notes):
        md = _note_to_md(note)
        lines.append(md)
        if i < len(notes) - 1:
            lines.append("")
            lines.append("---")
            lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    logger.info(f"MD exportat a {output_path} ({len(notes)} notes)")
    return str(output_path)


def _export_separate(notes: list[dict[str, Any]], output_dir: Path) -> str:
    """Exporta cada nota com a fitxer MD separat."""
    output_dir.mkdir(parents=True, exist_ok=True)
    for note in notes:
        md = _note_to_md(note)
        title_slug = note.get("title", "nota").replace("/", "_").replace("\\", "_")[:50]
        filepath = output_dir / f"{title_slug}_{note.get('id', '0')}.md"
        filepath.write_text(md, encoding="utf-8")
    logger.info(f"MD exportat a {output_dir} ({len(notes)} fitxers)")
    return str(output_dir)
