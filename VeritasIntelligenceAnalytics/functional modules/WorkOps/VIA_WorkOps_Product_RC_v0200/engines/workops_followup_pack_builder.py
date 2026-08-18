# -*- coding: utf-8 -*-
"""ENG-034 Batch Follow-up Pack Builder.
Selects due/risky items, chooses a coexisting template + language, and produces draft specs only.
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全引擎導入令 2026-08-18;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # accel_map/fetch/pip_install/run_fast
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
import argparse,json,re
from datetime import datetime, timezone
from pathlib import Path
from workops_autocode import next_code

HERE=Path(__file__).resolve().parent
WORKOPS=HERE.parent
OUT=WORKOPS/"out"
ROOT=HERE.parents[4] if len(HERE.parents) >= 5 else WORKOPS
TEMPLATES=WORKOPS.parent.parent.parent.parent / "templates"
# Drop-in package layout fallback
if not TEMPLATES.exists():
    TEMPLATES=HERE.parent.parent.parent / "templates"
if not TEMPLATES.exists():
    TEMPLATES=HERE.parent / "templates"

PARAMS=HERE/"followup_pack_params.json"
STATE=OUT/"followup_state.json"
PROJECTS=OUT/"project_registry.jsonl"
PACK=OUT/"daily_followup_pack.json"

def loadj(p,d):
    try:return json.loads(Path(p).read_text(encoding="utf-8-sig"))
    except Exception:return d
def loadjl(p):
    rows=[]
    if not Path(p).exists(): return rows
    for ln in Path(p).read_text(encoding="utf-8",errors="replace").splitlines():
        try: rows.append(json.loads(ln))
        except Exception: pass
    return rows
def atomic(p,obj):
    Path(p).parent.mkdir(parents=True,exist_ok=True)
    t=Path(str(p)+".tmp"); t.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding="utf-8"); t.replace(p)
def latest_projects():
    cur={}
    for r in loadjl(PROJECTS):
        pid=r.get("project_id")
        if not pid: continue
        old=cur.get(pid,{})
        aliases=list(dict.fromkeys((old.get("aliases") or [])+(r.get("aliases") or [])))
        old.update({k:v for k,v in r.items() if v is not None})
        old["aliases"]=aliases
        cur[pid]=old
    return cur
def template_registry():
    base=loadj(TEMPLATES/"template_registry.json",{"templates":[],"default_language":"zh-TW","default_template":"progress_followup"})
    user=loadj(TEMPLATES/"user"/"template_registry.user.json",{"templates":[]})
    merged=list(base.get("templates",[]))
    bykey={x.get("key"):i for i,x in enumerate(merged) if x.get("key")}
    for x in user.get("templates",[]):
        k=x.get("key")
        if not k: continue
        if k in bykey: merged[bykey[k]]=x
        else: merged.append(x)
    return {**base,"templates":merged}
def template_by_key(key):
    reg=template_registry()
    meta=next((x for x in reg.get("templates",[]) if x.get("key")==key),None)
    if not meta:return None,None
    rel=Path(meta["file"])
    candidates=[TEMPLATES/"user"/rel,TEMPLATES/rel] if not rel.is_absolute() else [rel]
    for pth in candidates:
        if pth.exists(): return meta,loadj(pth,{})
    return meta,{}
def render(s, ctx):
    for k,v in ctx.items(): s=s.replace("{{"+k+"}}",str(v))
    return s
def build(language=None, template_override=None):
    p=loadj(PARAMS,{})
    st=loadj(STATE,{"cards":[]})
    projects=latest_projects()
    reg=template_registry()
    language=language or reg.get("default_language","zh-TW")
    allowed=set(p.get("selection",{}).get("include_levels",[3,4,5]))
    rows=[]
    for c in st.get("cards",[]):
        if c.get("closed"): continue
        if int(c.get("level",0)) not in allowed and not c.get("close_candidate"): continue
        pid=c.get("project_id","")
        pr=projects.get(pid,{})
        state=c.get("state_code","UNKNOWN")
        key=(template_override or pr.get("default_template") or
             p.get("template_selection",{}).get("state_defaults",{}).get(state) or reg.get("default_template"))
        meta,tpl=template_by_key(key)
        if not tpl: continue
        lang=pr.get("default_language") or language
        if lang not in reg.get("supported_languages",[{}]):
            # supported_languages can be objects
            codes=[x.get("code") for x in reg.get("supported_languages",[]) if isinstance(x,dict)]
            if lang not in codes: lang=reg.get("default_language","zh-TW")
        ctx={"project_name":c.get("project_name") or pr.get("display_name") or pid}
        subject=render(tpl.get("subject",{}).get(lang) or tpl.get("subject",{}).get("en",""),ctx)
        intro=render(tpl.get("intro",{}).get(lang) or tpl.get("intro",{}).get("en",""),ctx)
        rows.append({
          "followup_id":next_code("FUP"),
          "project_id":pid,"case_id":c.get("case_id"),"thr":c.get("thr"),
          "project_name":ctx["project_name"],"state_code":state,"level":c.get("level"),
          "language":lang,"template_key":key,"template_id":meta.get("template_id") if meta else "",
          "subject":subject,"intro":intro,"questions":tpl.get("questions",[]),
          "voting_options":tpl.get("outlook_voting_options",{}).get(lang,[]),
          "human_send_confirmation":True,"send_allowed":False
        })
        if len(rows)>=int(p.get("selection",{}).get("max_items",80)): break
    doc={"version":"v0100","engine_id":"ENG-034","generated_at":datetime.now().isoformat(timespec="seconds"),
         "language":language,"count":len(rows),"items":rows}
    atomic(PACK,doc); return doc
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("command",nargs="?",default="build",choices=["build","status"])
    ap.add_argument("--language",choices=["zh-TW","zh-CN","en"],default=None)
    ap.add_argument("--template",default=None)
    a=ap.parse_args()
    if a.command=="build": print(json.dumps(build(a.language,a.template),ensure_ascii=False,indent=2))
    else:
        d=loadj(PACK,{})
        print(f"ENG-034 pack: {d.get('count',0)} · language={d.get('language','')}")
    return 0
if __name__=="__main__": raise SystemExit(main())
