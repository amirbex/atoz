#!/usr/bin/env python3
"""Assemble the rendered AtoZ brand-book slides into a shareable PDF."""
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
ROOT=Path(__file__).resolve().parents[1]
SLIDES=ROOT/"logo/brand-book/slides"
OUT=ROOT/"logo/brand-book/brand-book.pdf"
files=sorted(SLIDES.glob("slide-*.png"))
if len(files)!=16:
 raise SystemExit(f"Expected 16 rendered slides, found {len(files)}; run npm --prefix tools run render-brand first.")
W,H=1920,1080
pdf=canvas.Canvas(str(OUT),pagesize=(W,H),pageCompression=1)
for image in files:
 pdf.drawImage(ImageReader(str(image)),0,0,width=W,height=H,preserveAspectRatio=True,anchor="c",mask="auto")
 pdf.showPage()
pdf.save()
print(f"Wrote {OUT.relative_to(ROOT)} ({len(files)} pages)")
