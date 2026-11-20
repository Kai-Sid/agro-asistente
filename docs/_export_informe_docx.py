"""Genera docs/INFORME_FURPS_OWASP.docx desde INFORME_FURPS_OWASP.md."""

from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt

ROOT = Path(__file__).resolve().parent
MD = ROOT / "INFORME_FURPS_OWASP.md"
OUT = ROOT / "INFORME_FURPS_OWASP.docx"
OUT_FALLBACK = ROOT / "INFORME_FURPS_OWASP_actualizado.docx"
OUT_DOWNLOADS = Path.home() / "Downloads" / "INFORME_FURPS_OWASP_Agro_Asistente.docx"
OUT_DOWNLOADS_V2 = Path.home() / "Downloads" / "INFORME_FURPS_OWASP_Agro_Asistente_v2.docx"

IMG_RE = re.compile(r"^!\[([^\]]*)\]\(([^)]+)\)$")
CAPTION_RE = re.compile(r"^\*(Figura .+)\*$")


def _add_runs(paragraph, text: str) -> None:
    parts = re.split(r"(\*\*[^*]+\*\*|`[^`]+`)", text)
    for part in parts:
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            run = paragraph.add_run(part[2:-2])
            run.bold = True
        elif part.startswith("`") and part.endswith("`"):
            run = paragraph.add_run(part[1:-1])
            run.font.name = "Consolas"
            run.font.size = Pt(9)
        else:
            paragraph.add_run(part)


def _set_cell(cell, text: str, bold: bool = False) -> None:
    cell.text = ""
    p = cell.paragraphs[0]
    run = p.add_run(text)
    run.bold = bold
    run.font.size = Pt(9)


def _add_image(doc: Document, rel_path: str, alt: str) -> None:
    path = (ROOT / rel_path).resolve()
    if not path.exists():
        p = doc.add_paragraph()
        run = p.add_run(f"[Imagen no encontrada: {rel_path}]")
        run.italic = True
        return
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    run.add_picture(str(path), width=Inches(6.2))
    if alt:
        cap = doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = cap.add_run(alt)
        r.italic = True
        r.font.size = Pt(9)


def main() -> None:
    lines = MD.read_text(encoding="utf-8").splitlines()
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)

    i = 0
    while i < len(lines):
        line = lines[i].rstrip()

        if not line:
            i += 1
            continue

        img_match = IMG_RE.match(line.strip())
        if img_match:
            alt, rel = img_match.group(1), img_match.group(2)
            _add_image(doc, rel, alt)
            i += 1
            if i < len(lines) and CAPTION_RE.match(lines[i].strip()):
                cap = doc.add_paragraph()
                cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                r = cap.add_run(CAPTION_RE.match(lines[i].strip()).group(1))
                r.italic = True
                r.font.size = Pt(9)
                i += 1
            continue

        if CAPTION_RE.match(line.strip()):
            cap = doc.add_paragraph()
            cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = cap.add_run(CAPTION_RE.match(line.strip()).group(1))
            r.italic = True
            r.font.size = Pt(9)
            i += 1
            continue

        if line.startswith("```"):
            block: list[str] = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                block.append(lines[i])
                i += 1
            i += 1
            p = doc.add_paragraph()
            run = p.add_run("\n".join(block))
            run.font.name = "Consolas"
            run.font.size = Pt(8)
            continue

        if line.startswith("|") and i + 1 < len(lines) and re.match(
            r"^\|[\s\-:|]+\|$", lines[i + 1].strip()
        ):
            rows: list[list[str]] = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                raw = lines[i].strip()
                if re.match(r"^\|[\s\-:|]+\|$", raw):
                    i += 1
                    continue
                cells = [c.strip() for c in raw.strip("|").split("|")]
                rows.append(cells)
                i += 1
            if not rows:
                continue
            table = doc.add_table(rows=len(rows), cols=len(rows[0]))
            table.style = "Table Grid"
            for r_idx, row in enumerate(rows):
                for c_idx, val in enumerate(row):
                    clean = re.sub(r"\*\*|`", "", val)
                    _set_cell(table.rows[r_idx].cells[c_idx], clean, bold=(r_idx == 0))
            doc.add_paragraph()
            continue

        if line.startswith("# "):
            p = doc.add_heading(line[2:].strip(), level=0)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            i += 1
            continue
        if line.startswith("## "):
            doc.add_heading(line[3:].strip(), level=1)
            i += 1
            continue
        if line.startswith("### "):
            doc.add_heading(line[4:].strip(), level=2)
            i += 1
            continue
        if line == "---":
            i += 1
            continue

        if re.match(r"^[-*]\s+", line):
            p = doc.add_paragraph(style="List Bullet")
            _add_runs(p, re.sub(r"^[-*]\s+", "", line))
            i += 1
            continue

        if re.match(r"^\d+\.\s+", line):
            p = doc.add_paragraph(style="List Number")
            _add_runs(p, re.sub(r"^\d+\.\s+", "", line))
            i += 1
            continue

        p = doc.add_paragraph()
        _add_runs(p, line)
        i += 1

    targets = [OUT_DOWNLOADS, OUT_DOWNLOADS_V2, OUT, OUT_FALLBACK]
    saved = []
    for target in targets:
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            doc.save(target)
            saved.append(target)
        except PermissionError:
            continue
    if not saved:
        raise PermissionError("No se pudo escribir el DOCX (archivos bloqueados)")
    for path in saved:
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
