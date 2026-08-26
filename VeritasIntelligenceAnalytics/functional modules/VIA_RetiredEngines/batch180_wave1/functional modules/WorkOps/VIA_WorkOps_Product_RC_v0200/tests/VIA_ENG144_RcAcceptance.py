# -*- coding: utf-8 -*-
"""Release Candidate acceptance tests. No network and no Outlook mutation."""
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
import base64,json,os,shutil,subprocess,sys,tempfile
from pathlib import Path

SRC=Path(__file__).resolve().parents[1]
def run(eng,root,script,*args,timeout=20):
    env=os.environ.copy();env["PYTHONPATH"]=str(eng)
    r=subprocess.run([sys.executable,str(eng/script),*args],cwd=root,env=env,capture_output=True,text=True,timeout=timeout)
    if r.returncode!=0:raise RuntimeError(f"{script} failed\n{r.stdout}\n{r.stderr}")
    try:return json.loads(r.stdout) if r.stdout.strip() else {}
    except Exception:return {"stdout":r.stdout}

def main():
    root=Path(tempfile.mkdtemp(prefix="via_workops_rc_"))/"app";shutil.copytree(SRC,root)
    out=root/"out";shutil.rmtree(out,ignore_errors=True);out.mkdir();eng=root/"engines"
    csvbytes=b"ProductCode,Status\nPSU-1234,Blocked\n"
    mock={"messages":[
      {"id":"G1","internetMessageId":"<m1>","conversationId":"C1","subject":"India PSU-1234 validation","receivedDateTime":"2026-08-07T07:00:00+00:00","sentDateTime":"2026-08-07T07:00:00+00:00","from":{"emailAddress":{"name":"India QA","address":"qa@example.com"}},"toRecipients":[{"emailAddress":{"address":"user@example.com"}}],"ccRecipients":[{"emailAddress":{"address":"manager@example.com"}}],"hasAttachments":True,"attachments":[{"id":"A1","name":"validation.csv","contentType":"text/csv","size":len(csvbytes),"contentBytes":base64.b64encode(csvbytes).decode()}],"body":{"contentType":"text","content":"[BLOCKED]\nReason: Fixture unavailable\nETA: 2026-08-12\nPlan B: Parallel validation\nNext Action: Prepare alternate fixture"},"bodyPreview":"Blocked","isRead":True,"lastModifiedDateTime":"2026-08-07T07:00:00+00:00"},
      {"id":"G2","internetMessageId":"<m2>","conversationId":"C2","subject":"Approval complete","receivedDateTime":"2026-08-09T06:00:00+00:00","sentDateTime":"2026-08-09T06:00:00+00:00","from":{"emailAddress":{"name":"Approver","address":"approver@example.com"}},"toRecipients":[{"emailAddress":{"address":"user@example.com"}}],"ccRecipients":[],"hasAttachments":False,"body":{"contentType":"text","content":"[COMPLETED]"},"bodyPreview":"Completed","isRead":True,"lastModifiedDateTime":"2026-08-09T06:00:00+00:00"}
    ]}
    mf=root/"runtime/mock.json";mf.parent.mkdir(exist_ok=True);mf.write_text(json.dumps(mock),encoding="utf-8")
    run(eng,root,"workops_outlook_graph_connector.py","mock-sync",str(mf))
    (out/"project_registry.jsonl").write_text(json.dumps({"event":"CREATE","project_id":"PRJ-20260809-000001","display_name":"India PSU Transfer","status":"ACTIVE","product_codes":["PSU-1234"]})+"\n"+json.dumps({"event":"CREATE","project_id":"PRJ-20260809-000002","display_name":"Approval Project","status":"ACTIVE"})+"\n")
    (out/"classification_memory.jsonl").write_text(json.dumps({"event":"CLASSIFICATION_CONFIRM","conversation_id":"C1","project_id":"PRJ-20260809-000001","decision":"ACCEPT","folders":["Inbox"],"product_codes":["PSU-1234"]})+"\n"+json.dumps({"event":"CLASSIFICATION_CONFIRM","conversation_id":"C2","project_id":"PRJ-20260809-000002","decision":"ACCEPT","folders":["Inbox"],"product_codes":[]})+"\n")
    sequence=[
      ("VIA_ENG106_WorkopsAttachmentIntelligence.py",()),("VIA_ENG139_WorkopsTopicEpisode.py",()),("VIA_ENG119_WorkopsMailEventBridge.py",("build",)),
      ("workops_followup_state.py",("state","--no-open")),("VIA_ENG123_WorkopsMissingInformationGuard.py",("scan",)),
      ("workops_followup_pack_builder.py",("build","--language","zh-TW")),("workops_project_card_aggregator.py",("build",)),
      ("workops_stakeholder_matrix.py",("build",)),("workops_milestone_manager.py",("build",)),
      ("VIA_ENG114_WorkopsEvidenceIntegrityGuard.py",("build",)),("workops_project_fusion.py",("classify",)),
      ("VIA_ENG111_WorkopsConfidenceCalibrator.py",("build",)),("workops_progress_estimator.py",("build",)),
      ("workops_project_health.py",("build",)),("workops_closure_intelligence.py",("detect",)),
      ("VIA_ENG142_WorkopsWatchlistPrioritizer.py",("build",)),("VIA_ENG135_WorkopsSmartEscalation.py",()),
      ("workops_unified_work_register.py",("build",)),("workops_timeline_dependency.py",("build",)),
      ("VIA_ENG128_WorkopsProcessMiningKpiBridge.py",("build",)),("VIA_ENG136_WorkopsSsotStore.py",("snapshot",)),
      ("workops_module_lifecycle_manager.py",("health",)),("VIA_ENG113_WorkopsDiagnostics.py",("build",))
    ]
    for s,args in sequence:run(eng,root,s,*args)
    att1=json.loads((out/"attachment_intelligence.jsonl").read_text().splitlines()[0])["sys_attachment_id"]
    topic1=json.load(open(out/"topic_episodes.json"))["threads"][0]["episodes"][0]["topic_episode_id"]
    run(eng,root,"VIA_ENG106_WorkopsAttachmentIntelligence.py");run(eng,root,"VIA_ENG139_WorkopsTopicEpisode.py")
    att2=json.loads((out/"attachment_intelligence.jsonl").read_text().splitlines()[0])["sys_attachment_id"]
    topic2=json.load(open(out/"topic_episodes.json"))["threads"][0]["episodes"][0]["topic_episode_id"]
    assert att1==att2 and topic1==topic2
    b=run(eng,root,"workops_backup_restore.py","backup")
    assert run(eng,root,"workops_backup_restore.py","verify",b["backup"])["gate"]=="PASS"
    assert run(eng,root,"workops_backup_restore.py","restore",b["backup"])["gate"]=="STAGED_REVIEW_REQUIRED"
    health=run(eng,root,"workops_module_lifecycle_manager.py","health")
    assert health["gate"]=="PASS"
    cards=json.load(open(out/"project_cards.json"))
    assert cards["count"]==2
    print(json.dumps({"gate":"PASS","project_cards":cards["count"],"modules":health["count"],"stable_attachment_id":att1,"stable_topic_id":topic1,"ssot_mode":json.load(open(out/"ssot_status.json"))["mode"]},ensure_ascii=False,indent=2))
if __name__=="__main__":main()
