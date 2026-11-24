#!/usr/bin/env python3
"""Shared AtoZ mark geometry and HarfBuzz text-to-SVG helpers.

Canonical asset generation lives in tools/build_brand_assets.py. This module
is intentionally small: downstream artwork builders import its stable vector
mark and outlined-text primitives.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.boundsPen import BoundsPen
import uharfbuzz as hb

ROOT=Path(__file__).resolve().parents[1]
TOKENS_PATH=ROOT/"brand/tokens.json"
FONTS_DIR=ROOT/"tools/fonts"
TOKENS=json.loads(TOKENS_PATH.read_text(encoding="utf-8"))
BRAND_NAME=TOKENS["brand"]["name_latin_display"]
GOLD=TOKENS["color"]["innovation_gold"]["hex"]
VARIANTS={name:{"mark":v["mark"],"dot":v["dot"],"main":v["wordmark_main"],"accent":v["wordmark_accent"]} for name,v in TOKENS["logo"]["variants"].items()}
GEOMETRY=TOKENS["logo"]["geometry"]
SYM_X0,SYM_Y0,SYM_W,SYM_H=GEOMETRY["symbol_bbox"]
DOT=tuple(GEOMETRY["gold_dot"])
MARK_PATH=GEOMETRY["mark_path"]
MARK_TRANSFORM=GEOMETRY["mark_transform"]
_font_cache={}

def symbol_group(variant,dot_override=None):
 """Return the shared vector A/Z growth mark, with an optional dot color."""
 v=VARIANTS[variant];cx,cy,r=DOT;dot=dot_override or v["dot"]
 return f'<path d="{MARK_PATH}" transform="{MARK_TRANSFORM}" fill="{v["mark"]}"/><circle cx="{cx}" cy="{cy}" r="{r}" fill="{dot}"/>'

def _load_font(font_file):
 if font_file not in _font_cache:
  path=FONTS_DIR/font_file
  ttfont=TTFont(path)
  face=hb.Face(hb.Blob.from_file_path(str(path)))
  font=hb.Font(face);font.scale=(face.upem,face.upem)
  _font_cache[font_file]=(ttfont,font,face.upem)
 return _font_cache[font_file]

def shape_run(font_file,text,size,direction="ltr",script=None,language=None):
 """Shape one text run; return glyph paths, advance width and local bounds."""
 ttfont,font,upem=_load_font(font_file)
 buf=hb.Buffer();buf.add_str(text);buf.direction=direction
 if script:buf.script=script
 if language:buf.language=language
 hb.shape(font,buf)
 order=ttfont.getGlyphOrder();glyph_set=ttfont.getGlyphSet();s=size/upem
 glyphs=[];cursor=0.0;x0=y0=float("inf");x1=y1=float("-inf")
 for info,pos in zip(buf.glyph_infos,buf.glyph_positions):
  name=order[info.codepoint];gx=cursor+pos.x_offset*s;gy=-pos.y_offset*s
  pen=SVGPathPen(glyph_set);glyph_set[name].draw(pen);d=pen.getCommands()
  if d:
   glyphs.append((d,gx,gy,s))
   bounds_pen=BoundsPen(glyph_set);glyph_set[name].draw(bounds_pen)
   if bounds_pen.bounds:
    bx0,by0,bx1,by1=bounds_pen.bounds
    x0=min(x0,gx+bx0*s);x1=max(x1,gx+bx1*s)
    y0=min(y0,gy-by1*s);y1=max(y1,gy-by0*s)
  cursor+=pos.x_advance*s
 if x0==float("inf"):x0=y0=x1=y1=0.0
 return glyphs,cursor,(x0,y0,x1,y1)

def line_svg(runs,rtl=False):
 """Outline one or more text runs. Returns (SVG fragment, width, height)."""
 shaped=[]
 for run in runs:
  glyphs,width,bbox=shape_run(run["font"],run["text"],run["size"],run.get("direction","ltr"),run.get("script"),run.get("language"))
  shaped.append((run,glyphs,width,bbox))
 offsets=[]
 if rtl:
  total=sum(width for _,_,width,_ in shaped)+sum(run.get("gap_after",0) for run,_,_,_ in shaped[:-1])
  x=total
  for run,glyphs,width,bbox in shaped:
   x-=width;offsets.append(x);x-=run.get("gap_after",0)
  total_w=total
 else:
  x=0.0
  for run,glyphs,width,bbox in shaped:
   offsets.append(x);x+=width+run.get("gap_after",0)
  total_w=x-(shaped[-1][0].get("gap_after",0) if shaped else 0)
 parts=[];y0=float("inf");y1=float("-inf")
 for (run,glyphs,width,bbox),ox in zip(shaped,offsets):
  for d,gx,gy,s in glyphs:
   parts.append(f'<path d="{d}" fill="{run["fill"]}" transform="translate({ox+gx:.2f} {gy:.2f}) scale({s:.5f} {-s:.5f})"/>')
  y0=min(y0,bbox[1]);y1=max(y1,bbox[3])
 if y0==float("inf"):y0=y1=0.0
 body="".join(parts)
 if y0!=0.0:body=f'<g transform="translate(0 {-y0:.2f})">{body}</g>'
 return body,total_w,y1-y0

def scale_to_width(runs,target_width,rtl=False):
 """Scale all run sizes and gaps to a target rendered width."""
 _,width,_=line_svg(runs,rtl=rtl);factor=target_width/width if width else 1.0
 output=[]
 for run in runs:
  item=dict(run);item["size"]*=factor
  if "gap_after" in item:item["gap_after"]*=factor
  output.append(item)
 return output

def main():
 from build_brand_assets import main as build_current_brand
 build_current_brand()

if __name__=="__main__":main()
