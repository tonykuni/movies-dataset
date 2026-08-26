# -*- coding: utf-8 -*-
"""Localhost-only FastAPI product server."""
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
import json,os,subprocess,sys
from pathlib import Path
from typing import Any
from fastapi import FastAPI,HTTPException,UploadFile,File
from fastapi.responses import FileResponse,RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;OUT=ROOT/"out";UI=ROOT/"ui"
sys.path.insert(0,str(HERE))
from workops_project_registration import create as create_project, accept as accept_project
from workops_closure_intelligence import confirm as confirm_close
from workops_backup_restore import backup as do_backup
from workops_unified_search import search as do_search
from workops_onboarding import status as onboarding_status, complete as onboarding_complete
from workops_outlook_graph_connector import create_draft
from workops_milestone_manager import create as create_milestone, complete as complete_milestone
from workops_stakeholder_matrix import confirm as confirm_stakeholder_role

app=FastAPI(title="Veritas WorkOps Local API",version="2.0.0")
app.mount("/ui",StaticFiles(directory=str(UI)),name="ui")
app.mount("/out",StaticFiles(directory=str(OUT),check_dir=False),name="out")
app.mount("/templates",StaticFiles(directory=str(ROOT/"templates")),name="templates")

class ProjectCreate(BaseModel): name:str
class ProjectConfirm(BaseModel): conversation_id:str;project_id:str;folder:str="";product_codes:list[str]=[]
class FollowupBuild(BaseModel): language:str="zh-TW";template:str|None=None
class ClosureConfirm(BaseModel): project_id:str|None=None;case_id:str|None=None;reason:str
class DraftCreate(BaseModel): subject:str;body:str;to:list[str]
class OnboardingComplete(BaseModel): step:str
class MilestoneCreate(BaseModel): project_id:str;name:str;target_date:str;owner:str="";weight:float=1.0
class MilestoneComplete(BaseModel): milestone_id:str;evidence:str;actual_date:str=""
class StakeholderConfirm(BaseModel): project_id:str;stakeholder_id:str;role:str

class OutlookConfigUpdate(BaseModel):
    client_id:str=""
    tenant_id:str="organizations"
    enabled:bool=False
    it_acknowledged:bool=False
    it_reference:str=""
    allow_draft_write:bool=False
    folder_mode:str="all"


def j(path,default):
    try:return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except Exception:return default
def cmd(script,args,timeout=120):
    env=os.environ.copy();env["PYTHONPATH"]=str(HERE)
    r=subprocess.run([sys.executable,str(HERE/script),*args],cwd=ROOT,env=env,text=True,capture_output=True,timeout=timeout)
    try:o=json.loads(r.stdout) if r.stdout.strip() else {}
    except Exception:o={"stdout":r.stdout}
    if r.returncode!=0:raise HTTPException(500,detail={"engine":script,"stderr":r.stderr,"output":o})
    return o

@app.get("/")
def root():return RedirectResponse("/ui/workops_app.html")
@app.get("/api/status")
def status():
    return {"orchestrator":j(OUT/"orchestrator_status.json",{}),"diagnostics":j(OUT/"diagnostics.json",{}),"ssot":j(OUT/"ssot_status.json",{}),"onboarding":onboarding_status()}

@app.get("/api/config/outlook")
def get_outlook_config():
    c=j(ROOT/"config"/"outlook_graph.json",{})
    return {
      "client_id":c.get("client_id",""),"tenant_id":c.get("tenant_id","organizations"),"enabled":c.get("enabled",False),
      "it_acknowledged":(c.get("it_approval") or {}).get("acknowledged",False),
      "it_reference":(c.get("it_approval") or {}).get("ticket_or_reference",""),
      "allow_draft_write":c.get("allow_draft_write",False),"allow_send":c.get("allow_send",False),
      "folder_mode":c.get("folder_mode","all"),"read_scopes":c.get("delegated_scopes_read",[]),"draft_scopes":c.get("delegated_scopes_draft",[])
    }

@app.post("/api/config/outlook")
def set_outlook_config(x:OutlookConfigUpdate):
    p=ROOT/"config"/"outlook_graph.json";c=j(p,{})
    c["client_id"]=x.client_id.strip();c["tenant_id"]=x.tenant_id.strip() or "organizations";c["enabled"]=x.enabled
    c["allow_draft_write"]=x.allow_draft_write;c["allow_send"]=False;c["folder_mode"]=x.folder_mode
    it=c.setdefault("it_approval",{});it["acknowledged"]=x.it_acknowledged;it["ticket_or_reference"]=x.it_reference.strip()
    p.write_text(json.dumps(c,ensure_ascii=False,indent=2),encoding="utf-8")
    return get_outlook_config()

@app.post("/api/control-sheet/upload")
async def upload_control_sheet(file:UploadFile=File(...)):
    name=(file.filename or "").lower()
    data=await file.read()
    if len(data)>20*1024*1024: raise HTTPException(413,"Control sheet too large (>20 MB)")
    if name.endswith(".csv"):
        (OUT/"control_sheet.csv").write_bytes(data)
        return {"gate":"PASS","path":"out/control_sheet.csv","bytes":len(data)}
    if name.endswith(".xlsx"):
        try:
            import openpyxl,csv,io
            tmp=ROOT/"runtime"/"_control_sheet_upload.xlsx";tmp.parent.mkdir(exist_ok=True);tmp.write_bytes(data)
            wb=openpyxl.load_workbook(tmp,read_only=True,data_only=True);ws=wb.active
            rows=list(ws.iter_rows(values_only=True))
            if not rows:raise ValueError("empty workbook")
            with (OUT/"control_sheet.csv").open("w",encoding="utf-8-sig",newline="") as f:
                w=csv.writer(f);w.writerows([["" if v is None else v for v in r] for r in rows])
            try:tmp.unlink()
            except Exception:pass
            return {"gate":"PASS","path":"out/control_sheet.csv","rows":len(rows)}
        except Exception as e:raise HTTPException(400,f"XLSX conversion failed: {e}")
    raise HTTPException(400,"Only .csv or .xlsx is accepted")
@app.post("/api/sync")
def sync():return cmd("VIA_ENG126_WorkopsOrchestrator.py",["sync"],180)
@app.post("/api/refresh")
def refresh():return cmd("VIA_ENG126_WorkopsOrchestrator.py",["refresh"],180)
@app.get("/api/projects/cards")
def cards():return j(OUT/"project_cards.json",{"cards":[]})

@app.get("/api/projects/{project_id}/detail")
def project_detail(project_id:str):
    card=next((x for x in j(OUT/"project_cards.json",{"cards":[]}).get("cards",[]) if x.get("project_id")==project_id),None)
    work=[x for x in j(OUT/"unified_work_register.json",{"items":[]}).get("items",[]) if x.get("project_id")==project_id]
    timeline=next((x for x in j(OUT/"project_timeline.json",{"projects":[]}).get("projects",[]) if x.get("project_id")==project_id),{"events":[]})
    stakeholders=next((x for x in j(OUT/"stakeholder_matrix.json",{"projects":[]}).get("projects",[]) if x.get("project_id")==project_id),{"members":[]})
    milestones=next((x for x in j(OUT/"milestone_summary.json",{"projects":[]}).get("projects",[]) if x.get("project_id")==project_id),{"milestones":[]})
    topics=[x for x in j(OUT/"topic_episodes.json",{"threads":[]}).get("threads",[]) if x.get("project_id")==project_id]
    commitments=[x for x in j(OUT/"commitment_status.json",{"items":[]}).get("items",[]) if x.get("project_id")==project_id]
    return {"card":card,"work_items":work,"timeline":timeline,"stakeholders":stakeholders,"milestones":milestones,"topics":topics,"commitments":commitments}

@app.post("/api/milestones/create")
def milestone_create(x:MilestoneCreate):
    return create_milestone(x.project_id,x.name,x.target_date,x.owner,x.weight)

@app.post("/api/milestones/complete")
def milestone_complete(x:MilestoneComplete):
    return complete_milestone(x.milestone_id,x.evidence,x.actual_date)

@app.post("/api/stakeholders/confirm")
def stakeholder_confirm(x:StakeholderConfirm):
    return confirm_stakeholder_role(x.project_id,x.stakeholder_id,x.role)

@app.get("/api/escalations")
def escalations():
    return j(OUT/"escalation_candidates.json",{"items":[]})
@app.get("/api/today")
def today():return j(OUT/"today_queue.json",{"items":[]})
@app.get("/api/watchlist")
def watch():return j(OUT/"watchlist.json",{"items":[]})
@app.get("/api/accuracy")
def accuracy():return {"health":j(OUT/"project_health.json",{"items":[]}),"integrity":j(OUT/"evidence_integrity.json",{"items":[]}),"progress":j(OUT/"project_progress_estimate.json",{"items":[]})}
@app.get("/api/classification/candidates")
def candidates():return j(OUT/"project_candidates_calibrated.json",j(OUT/"project_candidates.json",{"items":[]}))
@app.post("/api/projects/create")
def project_create(x:ProjectCreate):
    if not x.name.strip():raise HTTPException(400,"Project name required")
    return create_project(x.name.strip())
@app.post("/api/classification/confirm")
def classification_confirm(x:ProjectConfirm):
    return accept_project(x.conversation_id,x.project_id,x.folder,x.product_codes)
@app.post("/api/followup/build")
def followup(x:FollowupBuild):
    args=["build","--language",x.language]
    if x.template:args+=["--template",x.template]
    return cmd("workops_followup_pack_builder.py",args)
@app.post("/api/closure/confirm")
def closure(x:ClosureConfirm):
    try:
        rc=confirm_close(project_id=x.project_id or "",case_id=x.case_id or "",reason=x.reason)
        return {"returncode":rc,"status":"CLOSED"}
    except SystemExit as e:raise HTTPException(409,str(e))
@app.get("/api/search")
def search(q:str,limit:int=50):return {"query":q,"items":do_search(q,limit)}
@app.post("/api/backup")
def backup():return do_backup()
@app.get("/api/diagnostics")
def diagnostics():return cmd("VIA_ENG113_WorkopsDiagnostics.py",["build"])
@app.get("/api/onboarding")
def onboarding():return onboarding_status()
@app.post("/api/onboarding/complete")
def onboarding_done(x:OnboardingComplete):return onboarding_complete(x.step)
@app.post("/api/drafts/create")
def draft(x:DraftCreate):
    try:return create_draft(x.subject,x.body,x.to)
    except Exception as e:raise HTTPException(403,str(e))

def main():
    import uvicorn
    cfg=j(ROOT/"config"/"system_config.json",{})
    s=cfg.get("server",{})
    uvicorn.run(app,host=s.get("host","127.0.0.1"),port=int(s.get("port",8775)),log_level="info")
if __name__=="__main__":main()
