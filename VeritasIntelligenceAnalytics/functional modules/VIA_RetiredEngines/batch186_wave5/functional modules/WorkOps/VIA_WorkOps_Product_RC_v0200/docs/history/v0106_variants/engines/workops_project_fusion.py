# -*- coding: utf-8 -*-
"""ENG-032 Project Fusion Classifier.
Signals: confirmed memory, folder, product code, subject, body, stakeholder.
Output is only ranked candidates; never auto-promotes.
"""
from __future__ import annotations
import argparse,csv,json,re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

HERE=Path(__file__).resolve().parent
WORKOPS=HERE.parent
OUT=WORKOPS/"out"
PARAMS=HERE/"project_fusion_params.json"
MAILS=OUT/"mails.csv"
CONTROL=OUT/"control_sheet.csv"
MEM=OUT/"classification_memory.jsonl"
REG=OUT/"project_registry.jsonl"
CAND=OUT/"project_candidates.json"

def loadj(p,d):
    try:return json.loads(Path(p).read_text(encoding="utf-8-sig"))
    except Exception:return d
def loadjl(p):
    out=[]
    if not Path(p).exists(): return out
    for ln in Path(p).read_text(encoding="utf-8",errors="replace").splitlines():
        try: out.append(json.loads(ln))
        except Exception: pass
    return out
def readcsv(p):
    if not Path(p).exists(): return []
    with Path(p).open("r",encoding="utf-8-sig",errors="replace",newline="") as f:
        return list(csv.DictReader(f))
def pick(r,names):
    for n in names:
        v=r.get(n)
        if v not in (None,""): return str(v)
    return ""
def toks(s):
    return {x.lower() for x in re.findall(r"[A-Za-z0-9\u4e00-\u9fff]{2,}",s or "")}
def sim(a,b):
    A=toks(a); B=toks(b)
    return len(A&B)/max(1,len(A|B))
def control_sheet_rows():
    return readcsv(CONTROL)

def latest_projects():
    d={}
    for r in loadjl(REG):
        if r.get("project_id"): d[r["project_id"]]=r
    return d
def confirmed_memory():
    byconv={}; byfolder={}; bycode={}
    for r in loadjl(MEM):
        if r.get("decision")!="ACCEPT": continue
        pid=r.get("project_id")
        if not pid: continue
        if r.get("conversation_id"): byconv[r["conversation_id"]]=pid
        for f in r.get("folders",[]): byfolder[str(f).lower()]=pid
        for c in r.get("product_codes",[]): bycode[str(c).upper()]=pid
    return byconv,byfolder,bycode
def extract_codes(text,pats):
    x=[]
    for p in pats:
        x.extend(re.findall(p,text or "",flags=re.I))
    return sorted({str(v).upper().replace(" ","") for v in x})
def atomic(p,obj):
    Path(p).parent.mkdir(parents=True,exist_ok=True)
    t=Path(str(p)+".tmp"); t.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding="utf-8"); t.replace(p)
def classify():
    p=loadj(PARAMS,{})
    f=p["field_aliases"]; w=p["weights"]; th=p["thresholds"]
    projects=latest_projects()
    byconv,byfolder,bycode=confirmed_memory()
    groups=defaultdict(list)
    for r in readcsv(MAILS):
        conv=pick(r,f["conversation"]) or f"ROW-{len(groups)+1}"
        groups[conv].append(r)
    results=[]
    for conv,rr in groups.items():
        subject=" ".join(pick(x,f["subject"]) for x in rr)
        body=" ".join(pick(x,f["body"]) for x in rr)
        folder=" ".join(pick(x,f["folder"]) for x in rr).strip()
        people=" ".join(pick(x,f["sender"])+" "+pick(x,f["to"])+" "+pick(x,f["cc"]) for x in rr)
        codes=extract_codes(subject+" "+body,p.get("product_code_patterns",[]))
        scores=defaultdict(float); evidence=defaultdict(list)
        if conv in byconv:
            pid=byconv[conv]; scores[pid]+=w["confirmed_memory"]; evidence[pid].append("confirmed conversation memory")
        for k,pid in byfolder.items():
            if k and k in folder.lower():
                scores[pid]+=w["outlook_folder"]; evidence[pid].append(f"folder:{k}")
        for code in codes:
            if code in bycode:
                pid=bycode[code]; scores[pid]+=w["product_code"]; evidence[pid].append(f"product:{code}")
        # Control Sheet = high-confidence structured anchor.
        # Supported columns are intentionally loose: ProjectID/ProjectName/ProductCode/Folder/Keywords.
        for cr in control_sheet_rows():
            cpid=(cr.get("ProjectID") or cr.get("project_id") or "").strip()
            cname=(cr.get("ProjectName") or cr.get("project_name") or cr.get("Name") or "").strip()
            cprod=(cr.get("ProductCode") or cr.get("product_code") or "").strip().upper().replace(" ","")
            cfolder=(cr.get("Folder") or cr.get("folder") or "").strip().lower()
            ckeys=(cr.get("Keywords") or cr.get("keywords") or "").strip()
            # Only link to a registered project id; otherwise the row still influences naming after registration.
            if cpid and cpid in projects:
                matched=0.0
                why=[]
                if cprod and cprod in codes: matched=max(matched,1.0); why.append(f"control product:{cprod}")
                if cfolder and cfolder in folder.lower(): matched=max(matched,0.95); why.append(f"control folder:{cfolder}")
                sn=sim(subject,cname+" "+ckeys)
                if sn>0: matched=max(matched,min(0.9,sn)); why.append(f"control subject:{sn:.2f}")
                if matched:
                    scores[cpid]+=w["control_sheet"]*matched
                    evidence[cpid].extend(why)
        for pid,pr in projects.items():
            label=(pr.get("display_name") or "")+" "+" ".join(pr.get("aliases") or [])
            s1=sim(subject,label); s2=sim(body,label)
            if s1:
                scores[pid]+=w["subject"]*s1; evidence[pid].append(f"subject:{s1:.2f}")
            if s2:
                scores[pid]+=w["body"]*s2; evidence[pid].append(f"body:{s2:.2f}")
            sp=sim(people," ".join(pr.get("stakeholders") or []))
            if sp:
                scores[pid]+=w["stakeholder"]*sp; evidence[pid].append(f"stakeholder:{sp:.2f}")
        ranked=[]
        for pid,raw in sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:int(th.get("top_n",4))]:
            score=min(0.99, round(raw,3))
            ranked.append({"project_id":pid,"display_name":projects.get(pid,{}).get("display_name",pid),
                           "score":score,"evidence":evidence[pid]})
        best=ranked[0]["score"] if ranked else 0
        if best>=th.get("strong_candidate",0.8): gate="REVIEW_STRONG"
        elif best>=th.get("review_candidate",0.45): gate="REVIEW"
        else: gate="NEW_OR_UNCERTAIN"
        results.append({"conversation_id":conv,"subject":subject[:160],"folder":folder,"product_codes":codes,
                        "candidate_count":len(ranked),"candidates":ranked,"gate":gate,
                        "user_confirmation_required":True})
    doc={"version":"v0100","engine_id":"ENG-032","generated_at":datetime.now().isoformat(timespec="seconds"),
         "count":len(results),"items":results}
    atomic(CAND,doc)
    return doc
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("command",nargs="?",default="classify",choices=["classify","status"])
    a=ap.parse_args()
    d=classify() if a.command=="classify" else loadj(CAND,{})
    print(json.dumps(d,ensure_ascii=False,indent=2) if a.command=="classify" else f"ENG-032 candidates: {d.get('count',0)}")
    return 0
if __name__=="__main__": raise SystemExit(main())
