#!/usr/bin/env python3
"""Validate generated AtoZ identity assets before review or handoff."""
from __future__ import annotations
import json
import struct
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def main():
    errors=[]
    def check(condition,message):
        if not condition: errors.append(message)
    tokens=json.loads((ROOT/"brand/tokens.json").read_text(encoding="utf-8"))
    system=json.loads((ROOT/"brand/design-system.json").read_text(encoding="utf-8"))
    index=json.loads((ROOT/"brand/asset-index.json").read_text(encoding="utf-8"))
    fonts=json.loads((ROOT/"brand/fonts/font-inventory.json").read_text(encoding="utf-8"))
    templates=json.loads((ROOT/"content-templates/template-manifest.json").read_text(encoding="utf-8"))
    check(tokens["meta"]["version"]=="2.0.0-draft","brand tokens version metadata missing")
    check(system["status"]=="asset_system_for_owner_review","identity system status missing")
    slides=sorted((ROOT/"brand/brand-book/slides").glob("slide-*.svg"))
    check(len(slides)==12,f"expected 12 book slide SVGs, found {len(slides)}")
    for svg in slides:
        check(svg.with_suffix(".png").is_file(),f"missing slide preview for {svg.name}")
    pdf=ROOT/"brand/brand-book/brand-book.pdf"
    check(pdf.is_file() and pdf.stat().st_size>100_000,"brand book PDF absent or unexpectedly small")
    check(index["book"]["slide_count"]==12,"asset index slide count mismatch")
    check(len(templates["templates"])==13,"expected 13 reusable template masters")
    for item in templates["templates"]:
        svg=ROOT/item["source_svg"]
        check(svg.is_file(),f"missing template source {item['source_svg']}")
        check(svg.with_suffix(".png").is_file(),f"missing template preview for {item['source_svg']}")
    for svg in list((ROOT/"brand").rglob("*.svg"))+list((ROOT/"content-templates").rglob("*.svg"))+list((ROOT/"logo-motion/source").glob("*.svg")):
        try: ET.parse(svg)
        except Exception as exc: errors.append(f"invalid SVG {svg.relative_to(ROOT)}: {exc}")
    check(fonts["font_count"]==57,f"font inventory mismatch: {fonts['font_count']}")
    check(any(r["family"]=="Dongol" and not r["persian_required_glyphs"]["zwnj"] for r in fonts["records"]),"Dongol ZWNJ limitation not documented")
    check(len(index["logo_motion"])==3,"asset index must point to all three motion exports")
    for rel in index["logo_motion"]:
        p=ROOT/rel
        check(p.is_file() and p.stat().st_size>10_000,f"missing/small motion output {rel}")
        if p.suffix==".mp4" and p.is_file():
            check(p.read_bytes()[:8][4:8]==b"ftyp",f"invalid MP4 signature: {rel}")
    check(index["phase"]=="foundational_identity_assets_only","asset phase scope marker missing")
    check(all((ROOT/p).is_file() for p in index["sheets"]),"asset index references missing design sheets")
    if errors:
        print("Identity asset validation FAILED:")
        for error in errors: print(f"- {error}")
        raise SystemExit(1)
    print(f"Identity asset validation passed: {len(slides)} book slides, {len(templates['templates'])} templates, {len(index['sheets'])} design sheets, {fonts['font_count']} font files audited, {len(index['logo_motion'])} motion exports.")

if __name__=="__main__":main()
