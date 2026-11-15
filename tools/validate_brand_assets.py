#!/usr/bin/env python3
"""Validate the current AtoZ generated identity package and its contract."""
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
LOGO=ROOT/"logo"
errors=[]
def require(condition,message):
 if not condition: errors.append(message)

try:
 system=json.loads((ROOT/"brand/design-system.json").read_text(encoding="utf-8"))
 index=json.loads((ROOT/"brand/asset-index.json").read_text(encoding="utf-8"))
 manifest=json.loads((LOGO/"motion/motion-manifest.json").read_text(encoding="utf-8"))
 fonts=json.loads((ROOT/"brand/fonts/font-inventory.json").read_text(encoding="utf-8"))
 templates=json.loads((ROOT/"content-templates/template-manifest.json").read_text(encoding="utf-8"))
except Exception as exc:
 raise SystemExit(f"Cannot read generated manifests: {exc}")
require(system["master"]["name"]=="AtoZ","master brand is not AtoZ")
require(not system["master"]["persian_wordmark"],"Persian AtoZ wordmark is enabled")
require(len(system["subbrands"])==5,"expected five sub-brands")
require(len(system["content_pillars"])==6,"expected six content pillars")
require(manifest["source_format"].startswith("SVG"),"motion source format missing")
require(len(manifest["brands"])==6,"expected master plus five sub-brand motion sets")
svg_files=list(LOGO.rglob("*.svg"))+list((ROOT/"content-templates").rglob("*.svg"))
for file in svg_files:
 try: ET.parse(file)
 except Exception as exc: errors.append(f"invalid SVG {file.relative_to(ROOT)}: {exc}")
require(len(list((LOGO/"brand-book/slides").glob("slide-*.svg")))==16,"brand book must contain 16 SVG slides")
require(set(p.name for p in (LOGO/"motion").iterdir() if p.is_dir())=={"atoz","blog","tools","book","pb","solicitor"},"unexpected motion brand folders")
motions=list((LOGO/"motion").glob("*/*.svg"))
require(len(motions)==48,f"expected 48 motion SVGs, found {len(motions)}")
require((LOGO/"brand-book/brand-book.pdf").exists(),"brand book PDF missing")
require(len(templates["templates"])==13,"expected 13 blank visual templates")
require(fonts["font_count"]==8,"expected an 8-file approved font subset")
require(index["font_audit"]["files_audited"]==fonts["font_count"],"asset index font count is stale")
require(not (LOGO/"fa").exists() and not (LOGO/"en").exists(),"legacy locale logo directories remain")
if errors:
 print("AtoZ asset validation failed:")
 for error in errors: print(" -",error)
 raise SystemExit(1)
print(f"Validated {len(svg_files)} SVGs, {len(motions)} motion sources, 16 brand-book pages, 13 templates and {fonts['font_count']} fonts.")
