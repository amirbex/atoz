#!/usr/bin/env python3
"""Serve the local AtoZ content dashboard and its review/intake API."""
from __future__ import annotations
import argparse, html, json, os, re, sys, tempfile
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from content_copy_engine import build_carousel, evidence_note

DAYS=["شنبه","یکشنبه","دوشنبه","سه‌شنبه","چهارشنبه","پنج‌شنبه","جمعه"]
VALID_REVIEW={"pending","approved","revise"}
MAX_BODY=20_000

def load_json(path,default):
    try:return json.loads(path.read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError):return default

def atomic_json(path:Path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(prefix=f".{path.name}.",dir=path.parent)
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as f:json.dump(data,f,ensure_ascii=False,indent=2);f.write("\n")
        os.replace(name,path)
    except Exception:
        try:os.unlink(name)
        except OSError:pass
        raise

def draft_result(payload,system):
    def text(key,maximum):
        value=payload.get(key)
        if not isinstance(value,str):raise ValueError(f"فیلد {key} الزامی است.")
        value=value.strip()
        if not value or len(value)>maximum:raise ValueError(f"فیلد {key} خالی است یا از حد {maximum} نویسه فراتر رفته.")
        return value
    title=text("title",140);persona=text("persona",80);problem=text("problem",500);thesis=text("thesis",500)
    pillar=payload.get("pillar_id");allowed={p["id"] for p in system.get("content_pillars",[])}
    if pillar not in allowed:raise ValueError("ستون محتوا معتبر نیست.")
    fmt=payload.get("format_id","carousel")
    if fmt not in {"carousel","reel","post","article"}:raise ValueError("قالب محتوا معتبر نیست.")
    evidence=payload.get("evidence_level","hypothesis")
    if evidence not in {"verified","experience","hypothesis","fictional_example"}:raise ValueError("سطح شواهد معتبر نیست.")
    note=evidence_note(evidence)
    caption=f"{title}\n\n{thesis}\n\nبرای مخاطب «{persona}»: {problem}\n\n{note}\n\nمنبع، CTA و مقصد نهایی را پیش از انتشار به‌صورت دستی بررسی کنید."
    slides=[]
    if fmt=="carousel":
        pseudo_item={"content_id":"ATZ-I-DRAFT","topic":title,"audience_problem":problem,"core_message":thesis,"evidence_level":evidence}
        slides=build_carousel(pseudo_item,{"hook":title,"cta":{"label":"این نکته را ذخیره و در فرایند خود بررسی کنید."}})
    return {"title":title,"persona":persona,"pillar_id":pillar,"problem":problem,"core_message":thesis,"format_id":fmt,"evidence_level":evidence,"caption":caption,"evidence_note":note,"slides":slides,"status":"draft_for_owner_review","source_policy":"no invented sources, metrics, links or endorsements"}

class Handler(SimpleHTTPRequestHandler):
    server_version="AtoZContentStudio/1.0"
    def __init__(self,*args,directory=None,output=None,**kwargs):
        self.output=output
        super().__init__(*args,directory=str(ROOT),**kwargs)
    def log_message(self,fmt,*args):print(f"[content-studio] {self.address_string()} {fmt%args}")
    def end_headers(self):
        self.send_header("X-Content-Type-Options","nosniff")
        self.send_header("Referrer-Policy","same-origin")
        self.send_header("Cache-Control","no-cache")
        super().end_headers()
    def send_json(self,status,data):
        raw=json.dumps(data,ensure_ascii=False).encode("utf-8")
        self.send_response(status);self.send_header("Content-Type","application/json; charset=utf-8");self.send_header("Content-Length",str(len(raw)));self.end_headers();self.wfile.write(raw)
    def read_body(self):
        length=int(self.headers.get("Content-Length","0"))
        if length<0 or length>MAX_BODY:raise ValueError("درخواست بیش‌ازحد بزرگ است.")
        try:return json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError,json.JSONDecodeError) as exc:raise ValueError("بدنهٔ درخواست JSON معتبر نیست.") from exc
    def do_GET(self):
        path=urlparse(self.path).path
        if path=="/":self.send_response(302);self.send_header("Location","/content-engine/dashboard/");self.end_headers();return
        if path=="/api/health":self.send_json(200,{"status":"ok","workspace":"AtoZ Content Studio","publishing":False});return
        if path=="/api/bootstrap":
            plan_path=self.output/"plan.json"
            if not plan_path.is_file():self.send_json(503,{"error":"بستهٔ هفتهٔ اول هنوز ساخته نشده؛ tools/run_content_engine.py را اجرا کنید."});return
            plan=load_json(plan_path,{})
            reviews=load_json(self.output/"review-state.json",{})
            drafts=load_json(self.output/"intake-drafts.json",[])
            tokens=load_json(ROOT/"brand/tokens.json",{})
            system=load_json(ROOT/"brand/design-system.json",{})
            recipes=load_json(ROOT/"content-engine/motion-recipes.json",{}).get("recipes",[])
            manifest=load_json(self.output/"content-engine-manifest.json",{})
            for d in plan.get("deliveries",[]):
                path=self.output/d.get("day_name_fa","")/d.get("content_id","")/d.get("delivery_id","")/"reel.mp4"
                d["has_video"]=path.is_file()
            rel="/"+self.output.relative_to(ROOT).as_posix()
            self.send_json(200,{"plan":plan,"review_state":reviews,"intake_drafts":drafts,"tokens":tokens,"design_system":system,"recipes":recipes,"manifest":manifest,"output_base":rel});return
        return super().do_GET()
    def do_POST(self):
        path=urlparse(self.path).path
        try:payload=self.read_body()
        except ValueError as exc:self.send_json(400,{"error":str(exc)});return
        if not isinstance(payload,dict):self.send_json(400,{"error":"درخواست باید یک شیء JSON باشد."});return
        if path=="/api/review":
            cid=payload.get("content_id");decision=payload.get("status");note=payload.get("note","")
            if not isinstance(cid,str) or not re.fullmatch(r"ATZ-C-[0-9]{6}",cid):self.send_json(400,{"error":"شناسهٔ محتوای معتبر لازم است."});return
            if decision not in VALID_REVIEW:self.send_json(400,{"error":"وضعیت بازبینی معتبر نیست."});return
            plan=load_json(self.output/"plan.json",{})
            if cid not in {x.get("content_id") for x in plan.get("content_items",[])}:self.send_json(404,{"error":"این محتوا در برنامه پیدا نشد."});return
            if not isinstance(note,str) or len(note)>2000:self.send_json(400,{"error":"یادداشت بیش از ۲۰۰۰ نویسه است."});return
            state=load_json(self.output/"review-state.json",{})
            if decision=="pending":state.pop(cid,None)
            else:state[cid]={"status":decision,"note":note.strip(),"reviewed_at":datetime.now(timezone.utc).isoformat(timespec="seconds"),"review_channel":"local-dashboard","publication_triggered":False}
            atomic_json(self.output/"review-state.json",state)
            self.send_json(200,{"review_state":state,"message":"تصمیم فقط به‌صورت محلی ثبت شد؛ انتشار انجام نشده است."});return
        if path in {"/api/draft/preview","/api/draft"}:
            system=load_json(ROOT/"brand/design-system.json",{})
            try:draft=draft_result(payload,system)
            except ValueError as exc:self.send_json(400,{"error":str(exc)});return
            if path=="/api/draft/preview":self.send_json(200,draft);return
            drafts=load_json(self.output/"intake-drafts.json",[])
            number=1
            used={x.get("id") for x in drafts}
            while f"ATZ-I-{number:06d}" in used:number+=1
            draft["id"]=f"ATZ-I-{number:06d}"
            draft["created_at"]=datetime.now(timezone.utc).isoformat(timespec="seconds")
            draft["plan_id"]=load_json(self.output/"plan.json",{}).get("plan_id")
            drafts.insert(0,draft);atomic_json(self.output/"intake-drafts.json",drafts)
            folder=self.output/"intake"/draft["id"];folder.mkdir(parents=True,exist_ok=False)
            atomic_json(folder/"draft.json",draft)
            body=(f"# {draft['title']}\n\n**شناسهٔ intake:** `{draft['id']}`  \n**ستون:** `{draft['pillar_id']}`  \n**مخاطب اصلی:** {draft['persona']}  \n**قالب پیشنهادی:** `{draft['format_id']}`  \n**وضعیت:** draft برای بازبینی مالک  \n**سطح شواهد:** `{draft['evidence_level']}`\n\n## مسئله\n{draft['problem']}\n\n## پیام محوری\n{draft['core_message']}\n\n## کپشن اولیه\n{draft['caption']}\n\n> موتور منبع، عدد، نشانی یا تأیید را حدس نزده است. پیش از هر انتشار، ادعاها، شواهد و مجوزها را بازبینی کنید.\n")
            (folder/"brief.fa.md").write_text(body,encoding="utf-8")
            self.send_json(201,{"draft":draft});return
        self.send_json(404,{"error":"API endpoint ناشناخته است."})

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host",default="0.0.0.0")
    parser.add_argument("--port",type=int,default=int(os.environ.get("PORT","4173")))
    parser.add_argument("--out",type=Path,default=ROOT/"content-output/week-01")
    args=parser.parse_args();output=args.out.expanduser().resolve()
    try:output.relative_to(ROOT)
    except ValueError:parser.error("--out must be inside the repository workspace")
    handler=lambda *a,**kw:Handler(*a,output=output,**kw)
    server=ThreadingHTTPServer((args.host,args.port),handler)
    print(f"AtoZ Content Studio on http://{args.host}:{args.port}  ·  output: {output.relative_to(ROOT)}  ·  publication disabled")
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()

if __name__=="__main__":main()
