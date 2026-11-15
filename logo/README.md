# AtoZ logo system

`logo/primary/` contains the master mark and lockups in color, monochrome and white modes. `logo/subbrands/` contains five aligned sub-brand lockups and original pictograms. `logo/motion/` contains standalone animated SVGs and the responsive gallery. `logo/brand-book/` contains the 16-page book in SVG, PNG, PDF and HTML formats. Quick use rules are in `guidelines-fa.md`.

The Latin AtoZ spelling is invariant. Persian is reserved for the dedicated founder name/title line only. Do not edit generated SVG/PNG exports manually; rebuild with `python3 tools/build_brand_assets.py` and `npm --prefix tools run render-brand`.
