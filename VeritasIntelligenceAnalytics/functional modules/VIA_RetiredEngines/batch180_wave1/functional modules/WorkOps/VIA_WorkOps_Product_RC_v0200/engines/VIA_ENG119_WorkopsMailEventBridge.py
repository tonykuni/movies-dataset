# -*- coding: utf-8 -*-
"""ENG-061 bridge normalized Outlook mail into the standalone Follow-up State contract.
Conservative parser: machine tokens > explicit multilingual status phrases > UNKNOWN.
Only conversations already confirmed to a Project are promoted to the WOP map.
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
from datetime import datetime
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;OUT=ROOT/"out";PARAMS=HERE/"mail_event_bridge_params.json"
MAIL=OUT/"email_raw_graph.jsonl";MEM=OUT/"classification_memory.jsonl";PROJECTS=OUT/"project_registry.jsonl"
STATUS=OUT/"reply_status.json";EVENTS=OUT/"reply_events.jsonl";WOP=OUT/"wop_registry.json";REPORT=OUT/"mail_event_bridge_report.json"
def jload(p,d):
    try:return json.loads(Path(p).read_text(encoding="utf-8-sig"))
    except Exception:return d
def jl(p):
    rows=[]
    if not Path(p).exists():return rows
    for ln in Path(p).read_text(encoding="utf-8",errors="replace").splitlines():
        try:rows.append(json.loads(ln))
        except Exception:pass
    return rows
def latest_projects():
    cur={}
    for r in jl(PROJECTS):
        pid=r.get("project_id")
        if pid:
            x=cur.get(pid,{})
            if r.get("event")=="RENAME" and x.get("display_name"):x.setdefault("aliases",[]).append(x["display_name"])
            x.update({k:v for k,v in r.items() if v is not None});cur[pid]=x
    return cur
def project_map():
    m={}
    for r in jl(MEM):
        if r.get("decision")=="ACCEPT" and r.get("conversation_id") and r.get("project_id"):
            m[r["conversation_id"]]=r["project_id"]
    return m
def parse_status(text,p):
    low=text.lower()
    # Exact machine-token pass first.
    for code,vals in p.get("status_tokens",{}).items():
        for v in vals:
            if v.startswith("[") and v.lower() in low:return code,float(p.get("machine_token_confidence",0.95)),v
    for code,vals in p.get("status_tokens",{}).items():
        for v in vals:
            if not v.startswith("[") and v.lower() in low:return code,float(p.get("minimum_keyword_confidence",0.65)),v
    return "UNKNOWN",0.0,""
def extract_date(text):
    patterns=[r"\b(20\d{2})[-/](\d{1,2})[-/](\d{1,2})\b",r"\b(\d{1,2})[-/](\d{1,2})[-/](20\d{2})\b"]
    for i,pat in enumerate(patterns):
        m=re.search(pat,text)
        if not m:continue
        if i==0:y,mo,d=m.groups()
        else:mo,d,y=m.groups()
        try:return f"{int(y):04d}-{int(mo):02d}-{int(d):02d}"
        except Exception:pass
    return ""
def extract_label(text,labels):
    for lab in labels:
        m=re.search(rf"(?im)^\s*{re.escape(lab)}\s*[:：]\s*(.+?)\s*$",text)
        if m:return m.group(1).strip()[:500]
    return ""
def build():
    p=jload(PARAMS,{});pm=project_map();projects=latest_projects()
    latest={}
    for x in jl(MAIL):
        conv=x.get("conversation_id")
        if not conv:continue
        if conv not in latest or (x.get("received_time") or "") >= (latest[conv].get("received_time") or ""):latest[conv]=x
    statuses={};events=[];wop={}
    for conv,x in latest.items():
        pid=pm.get(conv)
        if not pid:continue
        pr=projects.get(pid,{})
        text=(x.get("subject") or "")+"\n"+(x.get("body_text") or x.get("body_preview") or "")
        code,conf,matched=parse_status(text,p);eta=extract_date(text)
        reason=extract_label(text,["Reason","原因","延遲原因","延迟原因"])
        planb=extract_label(text,["Plan B","備案","备选方案","Alternative"])
        nexta=extract_label(text,["Next Action","下一步","后续行动","後續行動"])
        ev={"thr":conv,"conv":conv,"project_id":pid,"mail_date":x.get("received_time"),"subject":x.get("subject"),
            "sender":x.get("sender_email"),"status":code,"confidence":conf,"matched_signal":matched,
            "eta":eta,"reason":reason,"plan_b":planb,"next_action":nexta,
            "evidence":x.get("internet_message_id") or x.get("graph_id"),"source_hash":x.get("source_hash")}
        events.append(ev);statuses[conv]={"status":code,"mail_date":x.get("received_time"),"confidence":conf,"project_id":pid}
        wop[conv]={"wop_id":pid,"id":pid,"name":pr.get("display_name") or pid,"display_name":pr.get("display_name") or pid}
    STATUS.write_text(json.dumps({"version":"v0200","status":statuses},ensure_ascii=False,indent=2),encoding="utf-8")
    with EVENTS.open("w",encoding="utf-8") as f:
        for e in events:f.write(json.dumps(e,ensure_ascii=False)+"\n")
    WOP.write_text(json.dumps({"version":"v0200","registry":wop},ensure_ascii=False,indent=2),encoding="utf-8")
    rep={"engine_id":"ENG-061","gate":"PASS","confirmed_conversations":len(events),"unknown":sum(e["status"]=="UNKNOWN" for e in events)}
    REPORT.write_text(json.dumps(rep,ensure_ascii=False,indent=2),encoding="utf-8");return rep
def main():
    ap=argparse.ArgumentParser();ap.add_argument("command",nargs="?",default="build",choices=["build","status"]);a=ap.parse_args()
    print(json.dumps(build() if a.command=="build" else jload(REPORT,{}),ensure_ascii=False,indent=2));return 0
if __name__=="__main__":raise SystemExit(main())
