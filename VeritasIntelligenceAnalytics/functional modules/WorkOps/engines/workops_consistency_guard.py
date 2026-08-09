# -*- coding: utf-8 -*-
r"""Veritas WorkOps Cross-Ledger Consistency Guard v0100(ENG-052;與外部套件對照碼同號)
VIA 升籍 2026-08-11:原件存 candidates/eng050_053_external_v0100/。
Checks WOP/THR/DEC/MLS/CMT/CLS/dependency coherence. Report-only; never repairs canon.
"""
from __future__ import annotations
import argparse,html,json
from collections import defaultdict
from workops_control_common import *

RESULT=OUT/"consistency_report.json"; HTML=OUT/"Consistency_Report.html"
CFG=WORKOPS/"config"/"consistency_rules.json"

def finding(rows,code,wop="",native="",detail="",evidence=""):
    sev=(jload(CFG,{}).get("rules",{}) or {}).get(code,"WARN")
    rows.append({"severity":sev,"code":code,"wop":wop or "","native_id":native or "",
                 "detail":detail,"evidence":evidence})

def cycle_find(nodes,edges):
    adj=defaultdict(list)
    for a,b in edges: adj[a].append(b)
    temp=set();perm=set();stack=[];cycles=[]
    def visit(n):
        if n in perm:return
        if n in temp:
            if n in stack:
                i=stack.index(n);cycles.append(stack[i:]+[n])
            return
        temp.add(n);stack.append(n)
        for x in adj.get(n,[]):visit(x)
        stack.pop();temp.discard(n);perm.add(n)
    for n in nodes:visit(n)
    return cycles

def build():
    rows=[];reg=wop_registry();known=set(reg);t2w=thr2wop()
    milestones=(jload(OUT/"milestones.json",{}).get("items",{}) or {})
    commitments=(jload(OUT/"commitments.json",{}).get("items",{}) or {})
    closures=(jload(OUT/"closures.json",{}).get("items",{}) or {})
    closed_wops={x.get("wop") for x in closures.values() if x.get("wop")}
    decisions=decision_rows()
    rs=jload(OUT/"reply_status.json",{});reply=(rs.get("status",{}) or {})
    pending=csvrows(OUT/"pending.csv")
    links=jload(OUT/"timeline_links.json",{"links":[]}).get("links",[]) or []

    for cid,c in closures.items():
        w=c.get("wop","")
        if w and w not in known:finding(rows,"closed_unknown_wop",w,cid,"Closure points to unknown WOP","closures.json")
    for mid,m in milestones.items():
        w=m.get("wop","")
        if w not in known:finding(rows,"milestone_unknown_wop",w,mid,"Milestone points to unknown WOP","milestones.json")
        if m.get("status")=="COMPLETED" and not m.get("evidence"):
            finding(rows,"completed_milestone_no_evidence",w,mid,"Completed milestone has no evidence","milestones.json")
        if w in closed_wops and m.get("status")!="COMPLETED":
            finding(rows,"closed_has_open_milestone",w,mid,"Closed WOP still has non-completed milestone","milestones.json")
    seen_sources=defaultdict(list)
    for cid,c in commitments.items():
        w=c.get("wop","")
        if w not in known:finding(rows,"commitment_unknown_wop",w,cid,"Commitment points to unknown WOP","commitments.json")
        if w in closed_wops and c.get("status") not in ("FULFILLED","CANCELLED"):
            finding(rows,"closed_has_open_commitment",w,cid,"Closed WOP still has active commitment","commitments.json")
        if c.get("source_ref"):seen_sources[c["source_ref"]].append(cid)
    for src,ids in seen_sources.items():
        if len(ids)>1:finding(rows,"duplicate_commitment_source","",",".join(ids),f"Multiple commitments share source {src}","commitments.json")
    for d in decisions:
        w=wop_from_source(d.get("source"))
        if w in closed_wops and d.get("status")!="DONE":
            finding(rows,"closed_has_open_decision",w,d.get("decision_id",""),"Closed WOP still has open decision","decision_log")
    for thr in reply:
        if thr.startswith("THR-") and thr not in t2w:
            finding(rows,"reply_thread_unmapped","",thr,"Reply state exists but THR is not mapped to a WOP","reply_status.json")
    for p in pending:
        thr=p.get("ThrID") or p.get("THR") or ""
        if thr and thr in reply:
            finding(rows,"pending_thread_already_replied",t2w.get(thr,""),thr,
                    f"Pending queue still contains thread with parsed reply status={reply[thr].get('status','')}","pending.csv + reply_status.json")
    msids=set(milestones);edges=[]
    for x in links:
        a=x.get("from");b=x.get("to")
        if a not in msids:finding(rows,"dependency_missing_milestone","",a,"Dependency source milestone missing","timeline_links.json")
        if b not in msids:finding(rows,"dependency_missing_milestone","",b,"Dependency target milestone missing","timeline_links.json")
        if a in msids and b in msids:edges.append((a,b))
    for cyc in cycle_find(msids,edges):
        w=milestones.get(cyc[0],{}).get("wop","") if cyc else ""
        finding(rows,"dependency_cycle",w," → ".join(cyc),"Milestone dependency cycle detected","timeline_links.json")
    # Closure candidates must not coexist with obvious blockers.
    for c in jload(OUT/"closure_candidates.json",{}).get("candidates",[]) or []:
        w=c.get("wop","");thrlist=(reg.get(w,{}) or {}).get("thr",[]) or []
        blockers=[t for t in thrlist if (reply.get(t,{}) or {}).get("status") in ("卡關","需要協助","BLOCKED","NEED_HELP")]
        active_cmt=[cid for cid,x in commitments.items() if x.get("wop")==w and x.get("status") not in ("FULFILLED","CANCELLED")]
        if blockers or active_cmt:
            finding(rows,"closure_candidate_has_blocker",w,w,
                    f"Closure candidate has blockers threads={blockers[:4]} commitments={active_cmt[:4]}",
                    "closure_candidates.json")
    nerr=sum(x["severity"]=="ERROR" for x in rows);nwarn=sum(x["severity"]=="WARN" for x in rows)
    gate="FAIL" if nerr else "WARN" if nwarn else "PASS"
    doc={"version":"v0100","engine_id":"ENG-052","generated_at":now(),"gate":gate,
         "errors":nerr,"warnings":nwarn,"finding_count":len(rows),"findings":rows,
         "governance":"REPORT_ONLY / NO_AUTO_FIX"}
    atomic_json(RESULT,doc)
    trs="".join(f"<tr><td>{html.escape(x['severity'])}</td><td>{html.escape(x['code'])}</td><td>{html.escape(x['wop'])}</td><td>{html.escape(x['native_id'])}</td><td>{html.escape(x['detail'])}</td></tr>" for x in rows)
    HTML.write_text(f"""<!doctype html><meta charset='utf-8'><title>WorkOps Consistency</title>
<style>body{{font:14px system-ui;margin:30px;background:#f2f2f3;color:#1d1f20}}.card{{background:white;padding:18px;border-radius:10px}}table{{width:100%;border-collapse:collapse}}td,th{{padding:8px;border-bottom:1px solid #ddd;text-align:left}}</style>
<div class=card><h2>ENG-052 Cross-Ledger Consistency</h2><p>Gate <b>{gate}</b> · ERROR {nerr} · WARN {nwarn}</p>
<table><tr><th>Severity</th><th>Rule</th><th>WOP</th><th>ID</th><th>Detail</th></tr>{trs or '<tr><td colspan=5>PASS — no findings</td></tr>'}</table></div>""",encoding="utf-8")
    return doc

def main():
    argparse.ArgumentParser().parse_args();d=build()
    print(json.dumps({k:d[k] for k in ("engine_id","gate","errors","warnings","finding_count")},ensure_ascii=False,indent=2))
if __name__=="__main__":main()
