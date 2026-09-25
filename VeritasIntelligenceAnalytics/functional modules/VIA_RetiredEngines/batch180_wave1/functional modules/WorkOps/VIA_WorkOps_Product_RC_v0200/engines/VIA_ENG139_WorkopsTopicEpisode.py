# -*- coding: utf-8 -*-
"""ENG-066 Thread -> new-content -> topic episode reconstruction using CPU-light lexical continuity."""
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
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from workops_autocode import next_code
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;OUT=ROOT/"out";PARAMS=HERE/"topic_episode_params.json";RESULT=OUT/"topic_episodes.json";LINK=OUT/"topic_episode_link_registry.jsonl"
def j(p,d):
    try:return json.loads(Path(p).read_text(encoding="utf-8-sig"))
    except Exception:return d
def jl(p):
    rows=[]
    if not p.exists():return rows
    for ln in p.read_text(encoding="utf-8",errors="replace").splitlines():
        try:rows.append(json.loads(ln))
        except Exception:pass
    return rows
def strip_quote(text,markers):
    pos=len(text)
    for m in markers:
        q=text.find(m)
        if q>=0:pos=min(pos,q)
    return text[:pos].strip()
def toks(s):return {x.lower() for x in re.findall(r"[A-Za-z0-9\u4e00-\u9fff]{2,}",s or "")}
def jac(a,b):
    A=toks(a);B=toks(b);return len(A&B)/max(1,len(A|B))
def topic_id(conv,first_graph_id):
    key=f"{conv}|{first_graph_id}"
    for r in jl(LINK):
        if r.get("key")==key:return r.get("topic_episode_id")
    tid=next_code("TPC")
    with LINK.open("a",encoding="utf-8") as f:f.write(json.dumps({"key":key,"topic_episode_id":tid,"ts":datetime.now().astimezone().isoformat(timespec="seconds")},ensure_ascii=False)+"\n")
    return tid
def build():
    p=j(PARAMS,{});threads=defaultdict(list)
    for x in jl(OUT/"email_raw_graph.jsonl"):
        if x.get("conversation_id"):threads[x["conversation_id"]].append(x)
    projects={r.get("conversation_id"):r.get("project_id") for r in jl(OUT/"classification_memory.jsonl") if r.get("decision")=="ACCEPT"}
    allrows=[]
    for conv,msgs in threads.items():
        msgs.sort(key=lambda x:x.get("received_time") or "");episodes=[];current=None
        for m in msgs:
            content=strip_quote(m.get("body_text") or m.get("body_preview") or "",p.get("quote_markers",[]))
            candidate=(m.get("subject") or "")+"\n"+content
            if current is None or jac(current["aggregate_text"],candidate)<float(p.get("same_topic_jaccard",.35)):
                current={"topic_episode_id":"","conversation_id":conv,"project_id":projects.get(conv),"messages":[],"aggregate_text":candidate}
                episodes.append(current)
            else:current["aggregate_text"]+="\n"+candidate
            current["messages"].append({"graph_id":m.get("graph_id"),"internet_message_id":m.get("internet_message_id"),"received_time":m.get("received_time"),
                                        "subject":m.get("subject"),"body_new_content":content})
        for e in episodes:
            first=e["messages"][0].get("graph_id") or e["messages"][0].get("internet_message_id") or "FIRST"
            e["topic_episode_id"]=topic_id(conv,first)
            # Name from dominant subject; derived title, stable ID.
            subs=[x["subject"] for x in e["messages"] if x.get("subject")]
            e["topic_title"]=subs[0] if subs else e["topic_episode_id"];e["message_count"]=len(e["messages"]);e.pop("aggregate_text",None)
        allrows.append({"conversation_id":conv,"project_id":projects.get(conv),"topic_count":len(episodes),
                        "review_required":len(episodes)>=int(p.get("mixed_topic_review_threshold",3)),"episodes":episodes})
    doc={"version":"v0200","engine_id":"ENG-066","generated_at":datetime.now().astimezone().isoformat(timespec="seconds"),"threads":allrows}
    RESULT.write_text(json.dumps(doc,ensure_ascii=False,indent=2),encoding="utf-8");return doc
def main():
    argparse.ArgumentParser().parse_args();print(json.dumps(build(),ensure_ascii=False,indent=2));return 0
if __name__=="__main__":raise SystemExit(main())
