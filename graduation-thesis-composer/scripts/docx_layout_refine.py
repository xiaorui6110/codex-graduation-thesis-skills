#!/usr/bin/env python3
"""Refine DOCX layout for thesis delivery using direct OOXML paragraph/run normalization."""

from __future__ import annotations

import argparse
from copy import deepcopy
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}


def w_tag(name: str) -> str:
    return f"{{{W_NS}}}{name}"


def get_style_maps(styles_root: ET.Element) -> tuple[str | None, dict[int, str]]:
    normal_id: str | None = None
    heading_ids: dict[int, str] = {}
    for style in styles_root.findall("w:style", NS):
        if style.attrib.get(w_tag("type")) != "paragraph":
            continue
        sid = style.attrib.get(w_tag("styleId"))
        if not sid:
            continue
        name_el = style.find("w:name", NS)
        name = (name_el.attrib.get(w_tag("val")) if name_el is not None else "") or ""
        lowered = name.lower()
        if lowered == "normal" and normal_id is None:
            normal_id = sid
        m = re.search(r"heading\s*([1-6])", lowered)
        if m:
            heading_ids[int(m.group(1))] = sid
    return normal_id, heading_ids


def get_or_create(parent: ET.Element, child_tag: str) -> ET.Element:
    child = parent.find(child_tag, NS)
    if child is None:
        child = ET.SubElement(parent, w_tag(child_tag.split(":")[1]))
    return child


def remove_child(parent: ET.Element, child_tag: str) -> None:
    child = parent.find(child_tag, NS)
    if child is not None:
        parent.remove(child)


def apply_body_paragraph(p: ET.Element, normal_id: str | None) -> None:
    ppr = get_or_create(p, "w:pPr")
    if normal_id:
        pstyle = get_or_create(ppr, "w:pStyle")
        pstyle.set(w_tag("val"), normal_id)

    ind = get_or_create(ppr, "w:ind")
    ind.set(w_tag("firstLineChars"), "200")
    ind.set(w_tag("leftChars"), "0")
    if w_tag("firstLine") in ind.attrib:
        del ind.attrib[w_tag("firstLine")]

    spacing = get_or_create(ppr, "w:spacing")
    spacing.set(w_tag("before"), "0")
    spacing.set(w_tag("after"), "0")
    spacing.set(w_tag("line"), "360")
    spacing.set(w_tag("lineRule"), "auto")

    jc = get_or_create(ppr, "w:jc")
    jc.set(w_tag("val"), "both")

    remove_child(ppr, "w:keepNext")


def apply_heading_paragraph(p: ET.Element, level: int, style_id: str) -> None:
    ppr = get_or_create(p, "w:pPr")
    pstyle = get_or_create(ppr, "w:pStyle")
    pstyle.set(w_tag("val"), style_id)

    ind = get_or_create(ppr, "w:ind")
    ind.set(w_tag("firstLineChars"), "0")
    ind.set(w_tag("leftChars"), "0")
    if w_tag("firstLine") in ind.attrib:
        del ind.attrib[w_tag("firstLine")]

    spacing = get_or_create(ppr, "w:spacing")
    if level == 1:
        spacing.set(w_tag("before"), "240")
        spacing.set(w_tag("after"), "120")
    elif level == 2:
        spacing.set(w_tag("before"), "160")
        spacing.set(w_tag("after"), "80")
    else:
        spacing.set(w_tag("before"), "120")
        spacing.set(w_tag("after"), "40")
    spacing.set(w_tag("line"), "360")
    spacing.set(w_tag("lineRule"), "auto")

    jc = get_or_create(ppr, "w:jc")
    jc.set(w_tag("val"), "left")

    get_or_create(ppr, "w:keepNext")


def cleanup_runs(p: ET.Element) -> None:
    for rpr in p.findall(".//w:rPr", NS):
        for tag in ("w:color", "w:highlight", "w:shd", "w:u"):
            child = rpr.find(tag, NS)
            if child is not None:
                rpr.remove(child)


def paragraph_text(p: ET.Element) -> str:
    texts = []
    for t in p.findall(".//w:t", NS):
        texts.append(t.text or "")
    return "".join(texts).strip()


def is_heading(style_id: str | None, heading_ids: dict[int, str]) -> int | None:
    if not style_id:
        return None
    for level, sid in heading_ids.items():
        if sid == style_id:
            return level
    return None


def refine_layout(input_docx: Path, output_docx: Path) -> None:
    with zipfile.ZipFile(input_docx, "r") as zin:
        entries = {name: zin.read(name) for name in zin.namelist()}

    styles_root = ET.fromstring(entries["word/styles.xml"])
    normal_id, heading_ids = get_style_maps(styles_root)

    doc_root = ET.fromstring(entries["word/document.xml"])
    body = doc_root.find("w:body", NS)
    if body is None:
        raise RuntimeError("invalid document.xml: missing w:body")

    original_paras = body.findall("w:p", NS)
    cleaned_paras: list[ET.Element] = []
    for p in original_paras:
        ppr = p.find("w:pPr", NS)
        style_id = None
        if ppr is not None:
            pstyle = ppr.find("w:pStyle", NS)
            if pstyle is not None:
                style_id = pstyle.attrib.get(w_tag("val"))

        has_sectpr = p.find("w:pPr/w:sectPr", NS) is not None
        has_drawing = p.find(".//w:drawing", NS) is not None
        text = paragraph_text(p)
        if (not text) and (not has_drawing) and (not has_sectpr):
            continue

        heading_level = is_heading(style_id, heading_ids)
        if heading_level is not None:
            apply_heading_paragraph(p, heading_level, heading_ids[heading_level])
        else:
            apply_body_paragraph(p, normal_id)
        cleanup_runs(p)
        cleaned_paras.append(p)

    sect_nodes = [deepcopy(node) for node in body.findall("w:sectPr", NS)]
    for child in list(body):
        body.remove(child)
    for p in cleaned_paras:
        body.append(p)
    for sect in sect_nodes:
        body.append(sect)

    entries["word/document.xml"] = ET.tostring(doc_root, encoding="utf-8", xml_declaration=True)
    output_docx.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_docx, "w", zipfile.ZIP_DEFLATED) as zout:
        for name, data in entries.items():
            zout.writestr(name, data)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-docx", required=True, help="Input DOCX path")
    parser.add_argument("--output-docx", required=True, help="Output DOCX path")
    args = parser.parse_args()

    refine_layout(Path(args.input_docx).resolve(), Path(args.output_docx).resolve())
    print(f"Refined DOCX generated: {Path(args.output_docx).resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

