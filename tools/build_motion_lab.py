#!/usr/bin/env python3
"""Build a deterministic data-driven anatomy motion sample from AtoZ vectors."""
from __future__ import annotations
import argparse, json, os, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import build_week1_package as brand
import build_logo as brandmark

DATA_PATH=ROOT/"content-engine/motion-lab/break-even-data.json"
SOURCE_HTML=ROOT/"content-engine/motion-lab/break-even-anatomy.html"


def frame_svg(data:dict, step:int)->str:
    W,H=1080,1920;navy="#0A1931";gold="#FFB400";white="#FFFFFF";muted="#B7C4D5";line="#354C68"
    pieces=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',f'<rect width="{W}" height="{H}" fill="{navy}"/>',f'<rect x="0" y="0" width="{W}" height="20" fill="{gold}"/>']
    pieces.append(brand.brand_lockup_svg(70,52,270,"white"))
    pieces.append(brand.shaped_text("MOTION RECIPE · DATA-BOUND",1000,102,18,gold,"Montserrat-SemiBold.ttf",max_width=600)[0])
    pieces.append(brand.shaped_text(data["title_fa"],1000,210,45,white,"Vazirmatn-ExtraBold.ttf",max_width=890)[0])
    pieces.append(brand.shaped_text("مثال آموزشی فرضی؛ نه پیش‌بینی بازار",1000,285,24,muted,"Vazirmatn-Regular.ttf",max_width=870)[0])
    values=data["values"]
    rows=[("هزینهٔ ثابت دوره",values["fixed_cost"],"ریال · یک ماه فرضی"),("حاشیهٔ مشارکت هر سفارش",values["contribution_per_order"],"ریال · هر سفارش فرضی"),("محاسبهٔ ساده",None,"هزینهٔ ثابت ÷ حاشیهٔ مشارکت"),("نقطهٔ سربه‌سر",values["break_even_orders"],"سفارش · در ماه فرضی")]
    for idx,(label,value,unit) in enumerate(rows,1):
        y=415+(idx-1)*280;active=idx<=step
        fill="#142943" if active else "#0D1E35";stroke=gold if idx==4 and active else line;op="1" if active else ".42"
        pieces.append(f'<rect x="94" y="{y}" width="892" height="210" rx="22" fill="{fill}" stroke="{stroke}" stroke-width="{3 if idx==4 and active else 2}" opacity="{op}"/>')
        pieces.append(f'<circle cx="145" cy="{y+55}" r="25" fill="{gold if active else line}"/>')
        pieces.append(brand.shaped_text(f"{idx:02d}",153,y+64,16,navy if active else muted,"Montserrat-Bold.ttf",max_width=60)[0])
        pieces.append(brand.shaped_text(label,940,y+64,25,white if active else muted,"Vazirmatn-Bold.ttf",max_width=700)[0])
        if value is None: value_text="÷"
        else: value_text=f"{int(value):,}"
        font="Montserrat-Bold.ttf" if value is not None else "Vazirmatn-ExtraBold.ttf"
        pieces.append(brand.shaped_text(value_text,940,y+132,36,gold if active else "#74839A",font,max_width=700)[0])
        pieces.append(brand.shaped_text(unit,940,y+176,17,muted if active else "#65758B","Vazirmatn-Regular.ttf",max_width=700)[0])
    if step>=4:
        pieces.append(brand.shaped_text("۳۰۰٬۰۰۰٬۰۰۰ ÷ ۱۵۰٬۰۰۰ = ۲٬۰۰۰",960,1610,24,gold,"Vazirmatn-Bold.ttf",max_width=850)[0])
        pieces.append(brand.shaped_text("تمام اعداد نمونه‌اند؛ هزینه‌ها، ترکیب فروش و ظرفیت را با دادهٔ خود بسنجید.",960,1680,18,muted,"Vazirmatn-Regular.ttf",max_width=850)[0])
    pieces.append(f'<line x1="80" y1="1810" x2="1000" y2="1810" stroke="{line}" stroke-width="2"/>')
    pieces.append(brand.shaped_text("AtoZ  ·  FINANCE & MARKET  ·  REVIEW DRAFT",1000,1860,14,muted,"Montserrat-SemiBold.ttf",max_width=850)[0])
    pieces.append("</svg>")
    return "".join(pieces)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args();out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
    data=json.loads(DATA_PATH.read_text(encoding="utf-8"))
    html=SOURCE_HTML.read_text(encoding="utf-8")
    package_logo=Path(os.path.relpath(out.parent/"brand-assets/primary/white/horizontal.svg",out)).as_posix()
    html=html.replace("/logo/primary/white/horizontal.svg",package_logo)
    html=html.replace("/tools/fonts/Vazirmatn-Regular.ttf","../brand-assets/fonts/Vazirmatn-Regular.ttf")
    html=html.replace("/tools/fonts/Vazirmatn-Bold.ttf","../brand-assets/fonts/Vazirmatn-Bold.ttf")
    html=html.replace("/content-engine/dashboard/","../index.html")
    (out/"break-even-anatomy.html").write_text(html,encoding="utf-8")
    (out/"break-even-data.json").write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    frames=out/"frames";frames.mkdir(exist_ok=True)
    for step in range(5): (frames/f"frame-{step:02d}.svg").write_text(frame_svg(data,step),encoding="utf-8")
    storyboard={"composition_id":data["id"],"recipe_id":"anatomy-explode","fps":data["fps"],"duration_seconds":data["duration_seconds"],"frame_size":{"width":1080,"height":1920},"frame_stages":[{"at_seconds":round(i*data["duration_seconds"]/4,2),"step":i,"svg":f"frames/frame-{i:02d}.svg"} for i in range(5)],"controls":{"seekable":True,"keyboard":"ArrowLeft/ArrowRight","reduced_motion":"respect system preference"},"render":{"html":"break-even-anatomy.html","video":"break-even-anatomy.mp4","poster":"poster.png","video_engine":"ffmpeg concat from deterministic SVG keyframes"},"claims_policy":"hypothetical_example_only; no real business benchmark"}
    (out/"storyboard.json").write_text(json.dumps(storyboard,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (out/"hyperframes.manifest.json").write_text(json.dumps({"composition":"break-even-anatomy.html","timeline":"storyboard.json","data":"break-even-data.json","viewport":{"width":1080,"height":1920},"render_mode":"deterministic-frame-sequence","note":"Portable HTML/SVG scene handoff; HyperFrames runtime is an optional adapter and is not installed in this build."},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    cmd=["node",str(ROOT/"tools/render_motion_lab.mjs"),str(frames)]
    subprocess.run(cmd,cwd=ROOT/"tools",check=True)
    try:
        import imageio_ffmpeg
        ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as exc: raise SystemExit("imageio-ffmpeg is required to package the local MP4 preview") from exc
    output=out/"break-even-anatomy.mp4"
    inputs=[];filters=[]
    for i in range(5):
        inputs += ["-loop","1","-framerate",str(data["fps"]),"-t",str(data["duration_seconds"]/5),"-i",str(frames/f"frame-{i:02d}.png")]
        filters.append(f"[{i}:v]scale=540:960:force_original_aspect_ratio=decrease,pad=540:960:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={data['fps']},format=yuv420p[v{i}]")
    filters.append("".join(f"[v{i}]" for i in range(5))+"concat=n=5:v=1:a=0[v]")
    cmd=[ffmpeg,"-y",*inputs,"-filter_complex",";".join(filters),"-map","[v]","-an","-t",str(data["duration_seconds"]),"-r",str(data["fps"]),"-c:v","libx264","-preset","veryfast","-crf","24","-pix_fmt","yuv420p","-movflags","+faststart",str(output)]
    subprocess.run(cmd,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    poster=frames/"frame-04.png"
    (out/"poster.png").write_bytes(poster.read_bytes())
    print(f"Built seekable anatomy source and 8-second MP4 preview: {out}")

if __name__=="__main__":main()
