# -*- coding: utf-8 -*-
"""ENG-041 Daily Operating Rhythm.
Builds a time-of-day operating plan from Today, Watchlist, follow-up pack and commitment status.
Advisory only: no send/escalate/close actions are executed here.
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
import argparse, json
from datetime import datetime, timedelta
from pathlib import Path
try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None

HERE=Path(__file__).resolve().parent
WORKOPS=HERE.parent
OUT=WORKOPS/"out"
PARAMS=HERE/"daily_operating_rhythm_params.json"
TODAY=OUT/"today_queue.json"
WATCH=OUT/"watchlist.json"
PACK=OUT/"daily_followup_pack.json"
CMT=OUT/"commitment_status.json"
PLAN=OUT/"daily_operating_plan.json"
EVENTS=OUT/"daily_rhythm_events.jsonl"

def loadj(p,d):
    try:return json.loads(Path(p).read_text(encoding="utf-8-sig"))
    except Exception:return d
def atomic(p,o):
    Path(p).parent.mkdir(parents=True,exist_ok=True)
    t=Path(str(p)+".tmp");t.write_text(json.dumps(o,ensure_ascii=False,indent=2),encoding="utf-8");t.replace(p)
def append(p,o):
    Path(p).parent.mkdir(parents=True,exist_ok=True)
    with Path(p).open("a",encoding="utf-8") as f:f.write(json.dumps(o,ensure_ascii=False)+"\n")
def now_local(override=""):
    if override:
        return datetime.fromisoformat(override)
    tz=ZoneInfo("Asia/Taipei") if ZoneInfo else None
    return datetime.now(tz=tz) if tz else datetime.now()
def hm(s):
    h,m=[int(x) for x in s.split(":")]
    return h*60+m
def current_phase(now,p):
    cur=now.hour*60+now.minute
    for key,d in p.get("dayparts",{}).items():
        if hm(d["start"])<=cur<hm(d["end"]): return key
    return "eod" if cur>=hm(p["dayparts"]["eod"]["start"]) else "morning"
def key_of(x):
    return x.get("project_id") or x.get("case_id") or x.get("thr") or x.get("commitment_id") or ""
def unique(rows):
    seen=set();out=[]
    for x in rows:
        k=(key_of(x),x.get("kind") or x.get("state_code") or x.get("status"))
        if k in seen:continue
        seen.add(k);out.append(x)
    return out
def action(label_zh,label_cn,label_en,src,kind):
    return {
      "kind":kind,
      "project_id":src.get("project_id"),"case_id":src.get("case_id"),"thr":src.get("thr"),
      "commitment_id":src.get("commitment_id"),"project_name":src.get("project_name") or src.get("display_name") or "",
      "level":src.get("level",0),"priority_score":src.get("priority_score",0),
      "state_code":src.get("state_code") or src.get("status"),
      "due":src.get("due") or src.get("due_at") or src.get("eta") or "",
      "waiting_hours":src.get("waiting_hours",0),
      "recommended_action":{"zh-TW":label_zh,"zh-CN":label_cn,"en":label_en}
    }
def build(override_now=""):
    p=loadj(PARAMS,{})
    now=now_local(override_now)
    today=loadj(TODAY,{"items":[]}).get("items",[])
    watch=loadj(WATCH,{"items":[]}).get("items",[])
    follow=loadj(PACK,{"items":[]}).get("items",[])
    cmts=loadj(CMT,{"items":[]}).get("items",[])
    phase=current_phase(now,p)
    buckets={"morning":[],"pre_noon":[],"afternoon":[],"eod":[]}
    # Morning: high risk first.
    for x in sorted(today,key=lambda z:(-int(z.get("level",0)),-int(z.get("priority_score",0)))):
        if int(x.get("level",0))>=5:
            buckets["morning"].append(action("立即處理重大風險","立即处理重大风险","Handle critical risk now",x,"CRITICAL"))
        elif int(x.get("level",0))==4:
            buckets["morning"].append(action("確認警示案件下一步","确认警示事项下一步","Confirm next action for warning item",x,"WARNING"))
        if x.get("state_code")=="OVERDUE":
            buckets["morning"].append(action("先處理逾期事項","先处理逾期事项","Address overdue item first",x,"OVERDUE"))
        elif x.get("state_code")=="BLOCKED":
            buckets["morning"].append(action("確認卡關原因與 Plan B","确认受阻原因与 Plan B","Confirm blocker and Plan B",x,"BLOCKED"))
    # Before noon: waiting/missing/commitments.
    for x in today:
        if float(x.get("waiting_hours") or 0)>=24:
            buckets["pre_noon"].append(action("中午前取得回覆或確認 ETA","中午前取得回复或确认 ETA","Get reply or confirmed ETA before noon",x,"WAITING"))
        if x.get("missing_fields"):
            buckets["pre_noon"].append(action("補齊必要控制資訊","补齐必要控制信息","Complete required control information",x,"MISSING_CONTROL"))
    for c in cmts:
        if c.get("status") in ("DUE_SOON","OVERDUE","BROKEN"):
            buckets["pre_noon"].append(action("確認承諾是否能如期兌現","确认承诺是否能如期兑现","Confirm commitment can be fulfilled",c,"COMMITMENT"))
    # Afternoon: recovery and dependency clearing.
    for x in today:
        if x.get("state_code") in ("BLOCKED","OVERDUE","NEED_HELP","AT_RISK"):
            buckets["afternoon"].append(action("推進復原方案／Plan B","推进恢复方案／Plan B","Drive recovery plan / Plan B",x,"RECOVERY"))
        if "owner" in (x.get("missing_fields") or []):
            buckets["afternoon"].append(action("確認責任人","确认责任人","Confirm owner",x,"OWNER"))
    # EOD: batch drafts, close, tomorrow.
    for x in follow:
        buckets["eod"].append(action("預覽並準備追蹤草稿","预览并准备跟踪草稿","Review and prepare follow-up draft",x,"FOLLOWUP_DRAFT"))
    for x in today:
        if x.get("close_candidate"):
            buckets["eod"].append(action("確認是否可結案","确认是否可结案","Confirm whether item can close",x,"CLOSE"))
    for c in cmts:
        if c.get("status") in ("OVERDUE","BROKEN"):
            buckets["eod"].append(action("記錄未兌現原因與新承諾","记录未兑现原因与新承诺","Record miss reason and revised commitment",c,"BROKEN_COMMITMENT"))
    limit=int(p.get("limits",{}).get("phase_items",8))
    for k in buckets:
        buckets[k]=unique(buckets[k])[:limit]
    labels={k:v.get("label",{}) for k,v in p.get("dayparts",{}).items()}
    doc={
      "version":"v0100","engine_id":"ENG-041","generated_at":now.isoformat(timespec="seconds"),
      "current_phase":phase,"phase_labels":labels,
      "summary":{k:len(v) for k,v in buckets.items()},
      "phases":buckets,
      "governance":p.get("governance",{})
    }
    atomic(PLAN,doc)
    append(EVENTS,{"event":"PLAN_BUILT","ts":doc["generated_at"],"current_phase":phase,"summary":doc["summary"]})
    return doc
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("command",nargs="?",default="build",choices=["build","status"])
    ap.add_argument("--now",default="",help="Testing/preview ISO local time, e.g. 2026-08-09T16:45:00")
    a=ap.parse_args()
    if a.command=="build":print(json.dumps(build(a.now),ensure_ascii=False,indent=2))
    else:print(json.dumps(loadj(PLAN,{}),ensure_ascii=False,indent=2))
    return 0
if __name__=="__main__":raise SystemExit(main())
