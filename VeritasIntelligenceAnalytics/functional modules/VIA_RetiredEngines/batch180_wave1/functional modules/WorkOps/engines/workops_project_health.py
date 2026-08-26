# -*- coding: utf-8 -*-
r"""Veritas WorkOps Explainable Project Health & Progress v0100(ENG-053;與外部套件對照碼同號)
VIA 升籍 2026-08-11:原件存 candidates/eng050_053_external_v0100/。
Evidence-based derived scores. Every score exposes factors and penalties.
Health confidence means source coverage, NOT predictive/model accuracy.
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
import argparse,json
from collections import defaultdict
from workops_control_common import *
CFG=WORKOPS/"config"/"project_health_params.json"; RESULT=OUT/"project_health.json"

def ratio(done,total):
    return (done/total) if total else None
def cap(each,n,capv):return min(each*n,capv)
def build():
    cfg=jload(CFG,{})
    reg=wop_registry();t2w=thr2wop()
    ms=(jload(OUT/"milestones.json",{}).get("items",{}) or {})
    cm=(jload(OUT/"commitments.json",{}).get("items",{}) or {})
    dec=decision_rows();rs=jload(OUT/"reply_status.json",{});rstat=rs.get("status",{}) or {};flags=rs.get("flags",{}) or {}
    timeline=jload(OUT/"timeline.json",{});impact=timeline.get("impact",[]) or []
    consistency=jload(OUT/"consistency_report.json",{"findings":[]}).get("findings",[]) or []
    pending=csvrows(OUT/"pending.csv")
    by_ms=defaultdict(list);by_cm=defaultdict(list);by_dec=defaultdict(list);by_thr=defaultdict(list);by_pending=defaultdict(list)
    for mid,x in ms.items():by_ms[x.get("wop","")].append((mid,x))
    for cid,x in cm.items():by_cm[x.get("wop","")].append((cid,x))
    for x in dec:by_dec[wop_from_source(x.get("source"))].append(x)
    for t,s in rstat.items():by_thr[t2w.get(t,"")].append((t,s))
    for p in pending:
        t=p.get("ThrID") or "";by_pending[t2w.get(t,"")].append(p)
    impact_wops=defaultdict(int)
    for x in impact:
        bid=x.get("blocked","")
        w=ms.get(bid,{}).get("wop","")
        if w:impact_wops[w]+=1
    cons_err=defaultdict(int)
    for x in consistency:
        if x.get("severity")=="ERROR" and x.get("wop"):cons_err[x["wop"]]+=1
    out=[]
    weights=cfg.get("progress_weights",{});pen=cfg.get("health_penalties",{})
    for w,pr in reg.items():
        factors={};evidence=[]
        xms=by_ms.get(w,[])
        factors["milestones"]=ratio(sum(x[1].get("status")=="COMPLETED" for x in xms),len(xms))
        xcm=[x for x in by_cm.get(w,[]) if x[1].get("status")!="CANCELLED"]
        factors["commitments"]=ratio(sum(x[1].get("status")=="FULFILLED" for x in xcm),len(xcm))
        xd=by_dec.get(w,[])
        factors["decisions"]=ratio(sum(x.get("status")=="DONE" for x in xd),len(xd))
        xt=by_thr.get(w,[])
        factors["threads"]=ratio(sum(x[1].get("status") in ("已完成","DONE","COMPLETED") for x in xt),len(xt))
        avail={k:v for k,v in factors.items() if v is not None}
        den=sum(float(weights.get(k,0)) for k in avail)
        progress=round(100*sum(float(weights.get(k,0))*v for k,v in avail.items())/den,1) if den else None
        source_coverage=round(100*len(avail)/max(1,len(weights)),1)
        # Explainable health penalties
        overdue_ms=sum(due_overdue(x.get("due",""),x.get("status","")) for _,x in xms)
        blocked_thr=sum(x[1].get("status") in ("卡關","需要協助","BLOCKED","NEED_HELP") for x in xt)
        risk_thr=sum(bool(flags.get(t,{}).get("risk")) for t,_ in xt)
        overdue_dec=sum(due_overdue(x.get("due",""),x.get("status","")) for x in xd)
        overdue_cm=sum(due_overdue(x.get("due",""),x.get("status","")) for _,x in xcm)
        dep=int(impact_wops.get(w,0));ce=int(cons_err.get(w,0))
        t3=0
        for p in by_pending.get(w,[]):
            try:t3+=int(p.get("WaitingDays") or 0)>=7
            except Exception:pass
        deductions=[
          ("overdue_milestone",cap(pen.get("overdue_milestone_each",12),overdue_ms,pen.get("overdue_milestone_cap",30)),overdue_ms),
          ("blocked_thread",cap(pen.get("blocked_thread_each",10),blocked_thr,pen.get("blocked_thread_cap",20)),blocked_thr),
          ("risk_thread",cap(pen.get("risk_thread_each",15),risk_thr,pen.get("risk_thread_cap",30)),risk_thr),
          ("overdue_decision",cap(pen.get("overdue_decision_each",8),overdue_dec,pen.get("overdue_decision_cap",20)),overdue_dec),
          ("overdue_commitment",cap(pen.get("overdue_commitment_each",10),overdue_cm,pen.get("overdue_commitment_cap",30)),overdue_cm),
          ("dependency_impact",cap(pen.get("dependency_impact_each",8),dep,pen.get("dependency_impact_cap",20)),dep),
          ("consistency_error",cap(pen.get("consistency_error_each",15),ce,pen.get("consistency_error_cap",30)),ce),
          ("t3_wait",cap(pen.get("t3_wait_each",5),t3,pen.get("t3_wait_cap",15)),t3)
        ]
        health=max(0,round(100-sum(x[1] for x in deductions),1))
        lv=next((x for x in cfg.get("levels",[]) if health>=x["min"]),{"level":5,"state":"CRITICAL"})
        for name,deduct,count in deductions:
            if count:evidence.append({"factor":name,"count":count,"deduction":deduct})
        out.append({"wop":w,"project_name":pr.get("label") or w,"progress_pct":progress,
                    "progress_factors":factors,"source_coverage_pct":source_coverage,
                    "health_score":health,"level":lv["level"],"state":lv["state"],
                    "penalties":evidence,"next_priority":evidence[0]["factor"] if evidence else "maintain",
                    "governance_note":"source_coverage is data coverage, not model accuracy"})
    doc={"version":"v0100","engine_id":"ENG-053","generated_at":now(),"count":len(out),
         "critical":sum(x["level"]==5 for x in out),"warning_or_worse":sum(x["level"]>=4 for x in out),"items":out}
    atomic_json(RESULT,doc);return doc
def main():
    argparse.ArgumentParser().parse_args();d=build()
    print(json.dumps({k:d[k] for k in ("engine_id","count","critical","warning_or_worse")},ensure_ascii=False,indent=2))
if __name__=="__main__":main()
