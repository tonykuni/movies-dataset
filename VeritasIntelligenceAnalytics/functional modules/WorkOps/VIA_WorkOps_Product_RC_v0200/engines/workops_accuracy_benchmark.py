# -*- coding: utf-8 -*-
"""ENG-055 Gold-set benchmark + confidence calibration error."""
from __future__ import annotations
import argparse,json,math
from collections import defaultdict
from datetime import datetime
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;OUT=ROOT/"out";RESULT=OUT/"accuracy_benchmark.json"
def jl(p):
    rows=[]
    if not Path(p).exists():return rows
    for ln in Path(p).read_text(encoding="utf-8",errors="replace").splitlines():
        try:rows.append(json.loads(ln))
        except Exception:pass
    return rows
def metric(gold,pred,field):
    pairs=[(g.get(field),pred.get(g.get("sample_id"),{}).get(field)) for g in gold if field in g]
    correct=sum(a==b for a,b in pairs);return {"n":len(pairs),"correct":correct,"accuracy":round(correct/len(pairs),4) if pairs else None}
def build(gold_path,pred_path):
    gold=jl(Path(gold_path));predrows=jl(Path(pred_path));pred={x.get("sample_id"):x for x in predrows}
    fields=["project_id","owner","state_code","due_date","close_ready"]
    metrics={f:metric(gold,pred,f) for f in fields}
    buckets=defaultdict(list)
    for g in gold:
        p=pred.get(g.get("sample_id"),{});c=p.get("confidence")
        if c is None:continue
        c=max(0,min(1,float(c)));b=min(9,int(c*10));ok=(g.get("project_id")==p.get("project_id"))
        buckets[b].append((c,1 if ok else 0))
    cal=[];ece=0;n=sum(len(v) for v in buckets.values())
    for b in range(10):
        vals=buckets.get(b,[])
        if not vals:continue
        conf=sum(x for x,_ in vals)/len(vals);acc=sum(y for _,y in vals)/len(vals)
        ece+=len(vals)/max(1,n)*abs(conf-acc)
        cal.append({"range":f"{b/10:.1f}-{(b+1)/10:.1f}","n":len(vals),"mean_confidence":round(conf,3),"actual_accuracy":round(acc,3)})
    doc={"version":"v0200","engine_id":"ENG-055","generated_at":datetime.now().astimezone().isoformat(timespec="seconds"),
         "gold_n":len(gold),"prediction_n":len(predrows),"field_metrics":metrics,"calibration_buckets":cal,"ece":round(ece,4) if n else None}
    RESULT.write_text(json.dumps(doc,ensure_ascii=False,indent=2),encoding="utf-8");return doc
def main():
    ap=argparse.ArgumentParser();ap.add_argument("gold");ap.add_argument("predictions");a=ap.parse_args()
    print(json.dumps(build(a.gold,a.predictions),ensure_ascii=False,indent=2));return 0
if __name__=="__main__":raise SystemExit(main())
