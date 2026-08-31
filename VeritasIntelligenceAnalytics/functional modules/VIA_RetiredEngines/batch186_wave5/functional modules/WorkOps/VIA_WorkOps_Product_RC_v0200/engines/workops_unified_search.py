# -*- coding: utf-8 -*-
"""ENG-056 Unified local search across SSOT sidecars."""
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
import argparse,csv,json,re
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;OUT=ROOT/"out"
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
def current_projects():
    cur={}
    for r in jl(OUT/"project_registry.jsonl"):
        if r.get("project_id"):
            x=cur.get(r["project_id"],{});x.update(r);cur[r["project_id"]]=x
    return list(cur.values())
def search(q,limit=50):
    q=(q or "").strip().lower()
    if not q:return []
    sources=[
      ("PROJECT",current_projects()),
      ("EMAIL",jl(OUT/"email_raw_graph.jsonl")),
      ("COMMITMENT",jload(OUT/"commitment_status.json",{"items":[]}).get("items",[])),
      ("WORK_ITEM",jload(OUT/"unified_work_register.json",{"items":[]}).get("items",[])),
      ("ATTACHMENT",jl(OUT/"attachment_intelligence.jsonl")),
      ("TOPIC",jload(OUT/"topic_episodes.json",{"threads":[]}).get("threads",[])),
      ("LESSON",jl(OUT/"lesson_registry.jsonl"))
    ]
    res=[]
    for typ,rows in sources:
        for r in rows:
            text=" ".join(str(v) for v in r.values()).lower()
            if q in text:
                score=2 if any(str(v).lower()==q for v in r.values()) else 1
                res.append({"type":typ,"score":score,"id":r.get("project_id") or r.get("work_item_id") or r.get("commitment_id") or r.get("internet_message_id") or r.get("lesson_id"),
                            "title":r.get("display_name") or r.get("project_name") or r.get("subject") or r.get("title") or r.get("commitment_text") or r.get("situation") or "",
                            "record":r})
    return sorted(res,key=lambda x:-x["score"])[:limit]
def main():
    ap=argparse.ArgumentParser();ap.add_argument("query");ap.add_argument("--limit",type=int,default=50);a=ap.parse_args()
    print(json.dumps({"query":a.query,"items":search(a.query,a.limit)},ensure_ascii=False,indent=2));return 0
if __name__=="__main__":raise SystemExit(main())
