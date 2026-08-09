# -*- coding: utf-8 -*-
from __future__ import annotations
import csv, io, json, sqlite3
from datetime import datetime, date
from pathlib import Path

HERE=Path(__file__).resolve().parent
WORKOPS=HERE.parent
OUT=WORKOPS/"out"

def now(): return datetime.now().astimezone().isoformat(timespec="seconds")
def today(): return date.today().isoformat()
def jload(p,d):
    try:return json.loads(Path(p).read_text(encoding="utf-8-sig"))
    except Exception:return d
def csvrows(p):
    p=Path(p)
    if not p.exists():return []
    try:
        with io.open(p,"r",encoding="utf-8-sig",errors="replace",newline="") as f:return list(csv.DictReader(f))
    except Exception:return []
def atomic_json(p,obj):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+".tmp")
    tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=1),encoding="utf-8");tmp.replace(p)
def append_hist(item,ev,detail=""):
    item.setdefault("history",[]).append({"ts":now(),"ev":ev,"detail":detail})
def wop_registry():
    return jload(OUT/"wop_registry.json",{}).get("projects",{}) or {}
def thr2wop():
    out={}
    for w,pr in wop_registry().items():
        for t in pr.get("thr",[]) or []: out[t]=w
    return out
def project_label(wop):
    pr=wop_registry().get(wop,{})
    return pr.get("label") or pr.get("display_name") or pr.get("name") or wop
def decision_rows():
    db=OUT/"decision_log.db"
    if db.exists():
        try:
            c=sqlite3.connect(db)
            rows=c.execute("SELECT decision_id,meeting_id,what,owner,due,status,source,created_at,updated_at,done_at,note FROM DECISIONS").fetchall()
            c.close()
            keys=["decision_id","meeting_id","what","owner","due","status","source","created_at","updated_at","done_at","note"]
            return [dict(zip(keys,r)) for r in rows]
        except Exception:pass
    rows=csvrows(OUT/"decision_log.csv");out=[]
    for r in rows:
        out.append({
          "decision_id":r.get("Decision ID") or r.get("決策ID") or r.get("decision_id") or "",
          "meeting_id":r.get("Meeting ID") or r.get("會議代碼") or "",
          "what":r.get("決議內容") or r.get("what") or "",
          "owner":r.get("負責人") or r.get("owner") or "",
          "due":r.get("截止日") or r.get("due") or "",
          "status":r.get("狀態") or r.get("Status") or r.get("status") or "",
          "source":r.get("來源(THR/CASE)") or r.get("關聯THR") or r.get("source") or "",
          "note":r.get("備註/障礙") or r.get("note") or ""
        })
    return out
def due_overdue(due,status=""):
    if not due or str(status).upper() in ("DONE","COMPLETED","FULFILLED","CLOSED","CANCELLED"):return False
    try:return str(due)[:10] < today()
    except Exception:return False
def wop_from_source(source):
    s=str(source or "")
    if s.startswith("WOP-"):return s
    if s.startswith("THR-"):return thr2wop().get(s,"")
    for t,w in thr2wop().items():
        if t and t in s:return w
    return ""
