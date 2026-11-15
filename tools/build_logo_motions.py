#!/usr/bin/env python3
"""Build editable, silent logo-motion sources and MP4 preview exports."""
from __future__ import annotations
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import build_identity_assets as A
import build_logo as logo

OUT=ROOT/"logo-motion"
SOURCE=OUT/"source"
EXPORTS=OUT/"exports"
TIMELINES=OUT/"timelines"
TMP=ROOT/".brand-build/motion"
FPS=30


def mark_group(x,y,width,dark=False,clip_progress=1.0,opacity=1.0,scale_factor=1.0):
    width=width*scale_factor
    scale=width/logo.SYM_W
    height=logo.SYM_H*scale
    variant="white" if dark else "color"
    body=logo.symbol_group(variant,dot_override=A.GOLD if dark else None)
    clip=f'<defs><clipPath id="reveal"><rect x="0" y="0" width="{max(0,min(1,clip_progress))*logo.SYM_W:.2f}" height="{logo.SYM_H+40}"/></clipPath></defs>'
    g=(f'<g transform="translate({x-logo.SYM_X0*scale:.2f} {y-logo.SYM_Y0*scale:.2f}) scale({scale:.6f})" opacity="{opacity:.4f}">'
       f'{clip}<g clip-path="url(#reveal)">{body}</g></g>')
    return g, height, scale


def common_bg(W,H,bg):
    return A.rect(0,0,W,H,bg)


def move_dot_path(progress, start, end):
    # A hand-tuned cubic in the design grid; move the accent point toward the logo's existing growth dot.
    t=max(0,min(1,progress))
    c1=(start[0]+(end[0]-start[0])*.30,start[1])
    c2=(start[0]+(end[0]-start[0])*.68,end[1]+(start[1]-end[1])*.15)
    u=1-t
    x=u**3*start[0]+3*u*u*t*c1[0]+3*u*t*t*c2[0]+t**3*end[0]
    y=u**3*start[1]+3*u*u*t*c1[1]+3*u*t*t*c2[1]+t**3*end[1]
    path=f'M{start[0]} {start[1]} C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {end[0]} {end[1]}'
    return path,(x,y)


def frame_svg(kind,t):
    """t in [0,1]; build one still frame from the declared animation timeline."""
    if kind=="growth-reveal":
        W,H=1920,1080; bg=A.SURFACE
        x,y,mw=750,200,360
        p=max(0,min(1,t/.68)); ease=1-(1-p)**3
        op=min(1,max(0,(t-.05)/.35))
        mark,_,scale=mark_group(x,y,mw,False,ease,op,.82+.18*ease)
        start=(315,760); end=(x+1292.5*scale,y+87*scale)
        path,(dx,dy)=move_dot_path(ease,start,end)
        stroke=f'<path d="{path}" fill="none" stroke="{A.GOLD}" stroke-width="6" stroke-linecap="round" pathLength="1" stroke-dasharray="1" stroke-dashoffset="{1-ease:.4f}"/>'
        dot_scale=min(1,max(.15,(t-.08)/.25))
        moving=f'<circle cx="{dx:.2f}" cy="{dy:.2f}" r="{13*dot_scale:.2f}" fill="{A.GOLD}" opacity="{op:.4f}"/>'
        textp=max(0,min(1,(t-.55)/.25)); textop=1-(1-textp)**3
        name=A.en("AtoZfnb.info",960,715,42,A.NAVY,A.LATIN_BOLD,width=700,align="center")
        pers=A.fa("آ تو ز اف‌ان‌بی",960,785,28,A.NAVY,A.FA_BOLD,width=520,align="center")
        title=A.en("GROWTH · SYSTEMS · F&B",960,890,17,A.MUTED,A.LATIN_SEMI,width=600,align="center")
        b=[common_bg(W,H,bg),A.en("A  →  Z",150,130,18,A.MUTED,A.LATIN_SEMI,width=250),stroke,moving,mark,
           f'<g opacity="{textop:.4f}">{name}{pers}{title}</g>',A.rule(150,945,1770,945,A.BORDER,2),
           A.fa("نقطهٔ طلایی، مسیر صعودی و تثبیت نام برند",1760,965,18,A.MUTED,A.FA_REG,width=920)]
        return W,H,A.svg_doc(W,H,"".join(b),None,"Growth reveal motion frame")

    if kind=="brand-lockup":
        W,H=1920,1080; bg=A.NAVY
        x,y,mw=555,330,315
        p=max(0,min(1,t/.50)); ease=1-(1-p)**3
        op=min(1,max(0,(t-.1)/.45))
        mark,mark_h,scale=mark_group(x,y,mw,True,ease,op,.82+.18*ease)
        start=(265,825); end=(x+1292.5*scale,y+87*scale)
        path,(dx,dy)=move_dot_path(ease,start,end)
        stroke=f'<path d="{path}" fill="none" stroke="{A.GOLD}" stroke-width="5" stroke-linecap="round" pathLength="1" stroke-dasharray="1" stroke-dashoffset="{1-ease:.4f}" opacity=".95"/>'
        # Reveal the outlined lockup alongside the emblem.
        tp=max(0,min(1,(t-.42)/.36)); top=1-(1-tp)**3
        tx=1010+(1-top)*120
        latin=A.en("AtoZfnb.info",tx,450,63,A.WHITE,A.LATIN_BOLD,width=760)
        pers=A.fa("آ تو ز اف‌ان‌بی",tx+640,548,30,A.GOLD,A.FA_BOLD,width=640)
        tagline=A.fa("از دانش تا سیستم؛ از سیستم تا رشد",tx+640,635,24,"#CBD5E1",A.FA_REG,width=670)
        b=[common_bg(W,H,bg),stroke,mark,f'<g opacity="{top:.4f}">{latin}{pers}{tagline}</g>',
           A.rule(145,905,1775,905,"#334155",2),A.en("BRAND INTRO / OUTRO",145,930,15,"#CBD5E1",A.LATIN_SEMI,width=500),
           A.fa("خروجی بی‌صدا · زمان ۴ ثانیه · ۳۰ فریم‌برثانیه",1775,927,16,"#CBD5E1",A.FA_REG,width=680)]
        return W,H,A.svg_doc(W,H,"".join(b),None,"Brand lockup motion frame")

    # Vertical outro
    W,H=1080,1920; bg=A.NAVY
    p=max(0,min(1,t/.40)); ease=1-(1-p)**3
    op=min(1,max(0,(t-.08)/.40))
    x,y,mw=340,440,390
    mark,_,scale=mark_group(x,y,mw,True,ease,op,.75+.25*ease)
    start=(110,1110); end=(x+1292.5*scale,y+87*scale)
    path,(dx,dy)=move_dot_path(ease,start,end)
    stroke=f'<path d="{path}" fill="none" stroke="{A.GOLD}" stroke-width="5" pathLength="1" stroke-dasharray="1" stroke-dashoffset="{1-ease:.4f}" stroke-linecap="round"/>'
    tp=max(0,min(1,(t-.38)/.3)); top=1-(1-tp)**3
    name=A.en("AtoZfnb.info",540,1070,48,A.WHITE,A.LATIN_BOLD,width=820,align="center")
    pers=A.fa("آ تو ز اف‌ان‌بی",540,1150,32,A.GOLD,A.FA_BOLD,width=640,align="center")
    tagline=A.fa("[[دعوت به اقدام قابل‌ویرایش]]",540,1350,26,"#CBD5E1",A.FA_REG,width=820,align="center")
    handle=A.en("@atozfnb.info",540,1460,24,"#CBD5E1",A.LATIN_SEMI,width=480,align="center")
    b=[common_bg(W,H,bg),stroke,mark,f'<circle cx="{dx:.1f}" cy="{dy:.1f}" r="12" fill="{A.GOLD}" opacity="{op:.4f}"/>',
       f'<g opacity="{top:.4f}">{name}{pers}{tagline}{handle}</g>',
       A.rule(120,1695,960,1695,"#334155",2),A.en("LOGO OUTRO · VERTICAL",120,1735,15,"#CBD5E1",A.LATIN_SEMI,width=500),
       A.fa("نسخهٔ پایانی عمودی · بی‌صدا",960,1730,17,"#CBD5E1",A.FA_REG,width=540)]
    return W,H,A.svg_doc(W,H,"".join(b),None,"Vertical logo outro motion frame")


def source_svg(kind,duration):
    if kind=="growth-reveal": W,H=1920,1080
    elif kind=="brand-lockup": W,H=1920,1080
    else: W,H=1080,1920
    # Animated editable SVG built from the same outline mark and wordmark; MP4 is generated from deterministic frames.
    base=frame_svg(kind,1.0)
    start=frame_svg(kind,0.0)
    # Use SMIL for source preview; frame rendering avoids browser/capture dependencies.
    if kind=="growth-reveal":
        x,y,mw=750,200,360
    elif kind=="brand-lockup":x,y,mw=555,330,315
    else:x,y,mw=340,440,390
    s= mw/logo.SYM_W
    local=f'<g transform="translate({x-logo.SYM_X0*s:.2f} {y-logo.SYM_Y0*s:.2f}) scale({s:.6f})">'
    body=logo.symbol_group("white",dot_override=A.GOLD) if kind!="growth-reveal" else logo.symbol_group("color")
    static=local+body+'</g>'
    clip=f'<defs><clipPath id="mark-reveal"><rect x="0" y="0" width="0" height="{logo.SYM_H+40}"><animate attributeName="width" from="0" to="{logo.SYM_W}" dur="{duration*.5:.2f}s" begin="0s" fill="freeze"/></rect></clipPath></defs>'
    animated=f'<g clip-path="url(#mark-reveal)">{static}</g>'
    # For a browser preview, scale/opacity and label animate separately; reduced-motion visitors see a static frame.
    txt=(A.en("AtoZfnb.info",960 if W>H else 540,H*.61,48,A.WHITE if kind!="growth-reveal" else A.NAVY,A.LATIN_BOLD,width=760,align="center")+
         A.fa("آ تو ز اف‌ان‌بی",960 if W>H else 540,H*.68,30,A.GOLD if kind!="growth-reveal" else A.NAVY,A.FA_BOLD,width=620,align="center"))
    style=f'''<style>@keyframes revealText{{from{{opacity:0;transform:translateY(22px)}}to{{opacity:1;transform:translateY(0)}}}} .wordmark{{opacity:0;animation:revealText .75s cubic-bezier(.22,1,.36,1) {duration*.48:.2f}s forwards;transform-box:fill-box;transform-origin:center}} @media(prefers-reduced-motion:reduce){{.wordmark{{animation:none;opacity:1}}}}</style>'''
    desc=f'<desc>Silent logo motion source, {duration:g} seconds; the mark reveals toward the gold growth point.</desc>'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><title>AtoZ.FnB {kind}</title>{desc}{style}'
            f'<rect width="100%" height="100%" fill="{A.SURFACE if kind=="growth-reveal" else A.NAVY}"/>{clip}{animated}<g class="wordmark">{txt}</g></svg>')


def main():
    SOURCE.mkdir(parents=True,exist_ok=True);EXPORTS.mkdir(parents=True,exist_ok=True);TIMELINES.mkdir(parents=True,exist_ok=True)
    if TMP.exists():shutil.rmtree(TMP)
    TMP.mkdir(parents=True)
    jobs=[("growth-reveal",3.6,1920,1080,["path draw","mark reveal","gold point lands","wordmark resolves"]),
          ("brand-lockup",4.0,1920,1080,["growth point moves","symbol resolves","Latin lockup appears","Persian signature settles"]),
          ("vertical-outro",4.2,1080,1920,["symbol reveal","gold point settles","editable CTA placeholder","brand handle holds"])]
    manifest=[]
    for slug,duration,w,h,beats in jobs:
        source=SOURCE/f"{slug}.svg";source.write_text(source_svg(slug,duration),encoding="utf-8")
        nframes=round(duration*FPS)
        frdir=TMP/slug;frdir.mkdir(parents=True,exist_ok=True)
        for i in range(nframes):
            t=i/max(1,nframes-1)
            _,_,svg=frame_svg(slug,t)
            (frdir/f"frame-{i:04d}.svg").write_text(svg,encoding="utf-8")
        manifest.append({"id":slug,"duration_seconds":duration,"fps":FPS,"width":w,"height":h,"audio":"none","beats":beats,"source_svg":str(source.relative_to(ROOT)),"export_mp4":str((EXPORTS/f"{slug}.mp4").relative_to(ROOT)),"status":"owner_review"})
    (TIMELINES/"motion-spec.json").write_text(json.dumps({"version":"1.0.0-draft","motions":manifest,"motion_policy":A.SYSTEM["motion_identity"]},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    # Render temporary frames with Sharp, then encode silent H.264 previews.
    subprocess.run(["node",str(ROOT/"tools/render_identity_assets.mjs"),str(TMP)],check=True,cwd=ROOT)
    try:
        import imageio_ffmpeg
        ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as exc:
        raise RuntimeError("Install tools/requirements.txt to render the MP4 previews") from exc
    for item in manifest:
        seq=TMP/item["id"]/"frame-%04d.png"
        out=ROOT/item["export_mp4"]
        subprocess.run([ffmpeg,"-y","-framerate",str(FPS),"-i",str(seq),"-an","-c:v","libx264","-preset","medium","-crf","19","-pix_fmt","yuv420p","-movflags","+faststart",str(out)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        # Use the final clean frame as a poster/thumbnail.
        poster=TMP/item["id"]/f"frame-{round(item['duration_seconds']*FPS)-1:04d}.png"
        shutil.copy2(poster,EXPORTS/f"{item['id']}-poster.png")
    shutil.rmtree(TMP)
    print(f"Built {len(manifest)} logo-motion videos and source SVGs.")

if __name__=="__main__":main()
