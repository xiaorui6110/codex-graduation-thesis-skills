#!/usr/bin/env python3
"""Render Markdown thesis text into a DOCX using an existing DOCX as layout template."""

from __future__ import annotations

import argparse
from copy import deepcopy
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
XML_NS = "http://www.w3.org/XML/1998/namespace"
NS = {"w": W_NS}


def w_tag(name: str) -> str:
    return f"{{{W_NS}}}{name}"


def parse_markdown_blocks(text: str) -> list[dict[str, str | int]]:
    blocks: list[dict[str, str | int]] = []
    paragraph_lines: list[str] = []

    def flush_paragraph() -> None:
        if not paragraph_lines:
            return
        merged = "".join(line.strip() for line in paragraph_lines).strip()
        paragraph_lines.clear()
        if merged:
            blocks.append({"type": "paragraph", "text": merged})

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            flush_paragraph()
            continue

        heading = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if heading:
            flush_paragraph()
            blocks.append(
                {
                    "type": "heading",
                    "level": len(heading.group(1)),
                    "text": heading.group(2).strip(),
                }
            )
            continue

        if line.lstrip().startswith(">"):
            content = re.sub(r"^\s*>\s?", "", line)
            paragraph_lines.append(content)
            continue

        paragraph_lines.append(line)

    flush_paragraph()
    return blocks


def style_maps(styles_root: ET.Element) -> tuple[str | None, dict[int, str]]:
    normal_style_id: str | None = None
    heading_style_ids: dict[int, str] = {}

    for style in styles_root.findall("w:style", NS):
        style_type = style.attrib.get(w_tag("type"))
        if style_type != "paragraph":
            continue
        style_id = style.attrib.get(w_tag("styleId"))
        if not style_id:
            continue
        name_el = style.find("w:name", NS)
        name_val = (name_el.attrib.get(w_tag("val")) if name_el is not None else "") or ""
        lowered = name_val.lower()

        if normal_style_id is None and lowered == "normal":
            normal_style_id = style_id
        heading_match = re.search(r"heading\s*([1-6])", lowered)
        if heading_match:
            heading_style_ids[int(heading_match.group(1))] = style_id

    return normal_style_id, heading_style_ids


def build_paragraph(text: str, style_id: str | None) -> ET.Element:
    p = ET.Element(w_tag("p"))
    if style_id:
        p_pr = ET.SubElement(p, w_tag("pPr"))
        p_style = ET.SubElement(p_pr, w_tag("pStyle"))
        p_style.set(w_tag("val"), style_id)

    run = ET.SubElement(p, w_tag("r"))
    text_el = ET.SubElement(run, w_tag("t"))
    if text[:1].isspace() or text[-1:].isspace():
        text_el.set(f"{{{XML_NS}}}space", "preserve")
    text_el.text = text
    return p


def render_docx(template_docx: Path, markdown_path: Path, output_docx: Path) -> None:
    markdown_text = markdown_path.read_text(encoding="utf-8")
    blocks = parse_markdown_blocks(markdown_text)

    with zipfile.ZipFile(template_docx, "r") as zin:
        source_entries = {name: zin.read(name) for name in zin.namelist()}

    styles_root = ET.fromstring(source_entries["word/styles.xml"])
    normal_style, heading_styles = style_maps(styles_root)

    doc_root = ET.fromstring(source_entries["word/document.xml"])
    body = doc_root.find("w:body", NS)
    if body is None:
        raise RuntimeError("Invalid DOCX: word/document.xml has no w:body")

    sect_pr = None
    for child in list(body):
        if child.tag == w_tag("sectPr"):
            sect_pr = deepcopy(child)
        body.remove(child)

    for block in blocks:
        text = str(block["text"])
        if block["type"] == "heading":
            level = int(block["level"])
            style_id = heading_styles.get(level) or heading_styles.get(min(level, 4)) or normal_style
            body.append(build_paragraph(text, style_id))
        else:
            body.append(build_paragraph(text, normal_style))

    if sect_pr is not None:
        body.append(sect_pr)

    source_entries["word/document.xml"] = ET.tostring(doc_root, encoding="utf-8", xml_declaration=True)

    output_docx.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_docx, "w", zipfile.ZIP_DEFLATED) as zout:
        for name, data in source_entries.items():
            zout.writestr(name, data)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--template-docx", required=True, help="Reference DOCX path")
    parser.add_argument("--markdown", required=True, help="Markdown thesis path")
    parser.add_argument("--output-docx", required=True, help="Output DOCX path")
    args = parser.parse_args()

    render_docx(
        template_docx=Path(args.template_docx).resolve(),
        markdown_path=Path(args.markdown).resolve(),
        output_docx=Path(args.output_docx).resolve(),
    )
    print(f"DOCX generated: {Path(args.output_docx).resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

