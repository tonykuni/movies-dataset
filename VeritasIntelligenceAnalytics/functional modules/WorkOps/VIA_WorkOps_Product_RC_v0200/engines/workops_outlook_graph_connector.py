# -*- coding: utf-8 -*-
"""ENG-051 Microsoft Graph Outlook connector.
Delegated user access only. Default scope is read-only. Optional draft creation requires
allow_draft_write=true and Mail.ReadWrite. No send method is implemented.
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
import argparse, base64, csv, hashlib, json, os, re, sys, time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote
import requests

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
OUT=ROOT/"out"; OUT.mkdir(parents=True,exist_ok=True)
CFG=ROOT/"config"/"outlook_graph.json"
RAW=OUT/"email_raw_graph.jsonl"; MAILS=OUT/"mails.csv"; FOLDERS=OUT/"folder_registry.json"; REPORT=OUT/"graph_sync_report.json"; ATTREG=OUT/"attachment_registry.jsonl"; ATTDIR=OUT/"attachments"
GRAPH="https://graph.microsoft.com/v1.0"

def jload(p,d):
    try:return json.loads(Path(p).read_text(encoding="utf-8-sig"))
    except Exception:return d
def atomic(p,o):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);t=Path(str(p)+".tmp")
    t.write_text(json.dumps(o,ensure_ascii=False,indent=2),encoding="utf-8");t.replace(p)
def cache_path(cfg):
    p=Path(cfg.get("token_cache_file","runtime/msal_token_cache.json"))
    return p if p.is_absolute() else ROOT/p
def delta_path(cfg):
    p=Path(cfg.get("delta_state_file","runtime/graph_delta_state.json"))
    return p if p.is_absolute() else ROOT/p

def _msal():
    try:
        import msal
        return msal
    except Exception as e:
        raise RuntimeError("MSAL_NOT_INSTALLED: pip install msal") from e

def get_token(cfg, interactive=False):
    if not cfg.get("client_id"):
        raise RuntimeError("GRAPH_CLIENT_ID_MISSING")
    msal=_msal()
    cp=cache_path(cfg);cp.parent.mkdir(parents=True,exist_ok=True)
    cache=msal.SerializableTokenCache()
    if cp.exists():
        try:cache.deserialize(cp.read_text(encoding="utf-8"))
        except Exception:pass
    app=msal.PublicClientApplication(
        cfg["client_id"],
        authority=f"https://login.microsoftonline.com/{cfg.get('tenant_id','organizations')}",
        token_cache=cache,
        enable_broker_on_windows=True if os.name=="nt" and cfg.get("auth_mode")=="interactive" else None
    )
    scopes=cfg.get("delegated_scopes_read",["Mail.Read","User.Read"])
    accounts=app.get_accounts()
    result=app.acquire_token_silent(scopes,account=accounts[0]) if accounts else None
    if not result:
        if cfg.get("auth_mode")=="interactive" or interactive:
            result=app.acquire_token_interactive(scopes=scopes)
        else:
            flow=app.initiate_device_flow(scopes=scopes)
            if "user_code" not in flow:raise RuntimeError("DEVICE_FLOW_INIT_FAILED: "+json.dumps(flow))
            print(flow.get("message","Open Microsoft sign-in and enter the displayed code."),flush=True)
            result=app.acquire_token_by_device_flow(flow)
    if cache.has_state_changed:
        cp.write_text(cache.serialize(),encoding="utf-8")
    if "access_token" not in (result or {}):
        raise RuntimeError("TOKEN_ACQUIRE_FAILED: "+json.dumps(result or {},ensure_ascii=False))
    return result["access_token"]

def req(token,url,method="GET",json_body=None,timeout=30):
    headers={"Authorization":f"Bearer {token}","Accept":"application/json","Prefer":'outlook.body-content-type="text"'}
    r=requests.request(method,url,headers=headers,json=json_body,timeout=timeout)
    if r.status_code>=400:
        raise RuntimeError(f"GRAPH_HTTP_{r.status_code}: {r.text[:1000]}")
    return r.json() if r.text else {}

def list_all_folders(token,cfg):
    timeout=cfg.get("request_timeout_seconds",30)
    queue=[(f"{GRAPH}/me/mailFolders?$top=100",None)]
    rows=[];visited=set()
    while queue:
        url,parent=queue.pop(0)
        while url:
            doc=req(token,url,timeout=timeout)
            for f in doc.get("value",[]):
                fid=f.get("id")
                if not fid or fid in visited:continue
                visited.add(fid)
                row={"id":fid,"displayName":f.get("displayName"),"parentFolderId":f.get("parentFolderId") or parent,
                     "childFolderCount":f.get("childFolderCount",0),"totalItemCount":f.get("totalItemCount",0),
                     "unreadItemCount":f.get("unreadItemCount",0)}
                rows.append(row)
                if int(f.get("childFolderCount") or 0)>0:
                    queue.append((f"{GRAPH}/me/mailFolders/{quote(fid,safe='')}/childFolders?$top=100",fid))
            url=doc.get("@odata.nextLink")
    return rows

def recipients(v):
    return [((x.get("emailAddress") or {}).get("address") or "") for x in (v or []) if (x.get("emailAddress") or {}).get("address")]

def normalized(msg,folder):
    sender=((msg.get("from") or {}).get("emailAddress") or {})
    body=msg.get("body") or {}
    return {
      "source_channel":"OUTLOOK_GRAPH","graph_id":msg.get("id"),"internet_message_id":msg.get("internetMessageId"),
      "conversation_id":msg.get("conversationId"),"subject":msg.get("subject") or "",
      "sender_name":sender.get("name") or "","sender_email":sender.get("address") or "",
      "to_list":recipients(msg.get("toRecipients")),"cc_list":recipients(msg.get("ccRecipients")),
      "received_time":msg.get("receivedDateTime"),"sent_time":msg.get("sentDateTime"),
      "body_text":body.get("content") if body.get("contentType","").lower()=="text" else msg.get("bodyPreview",""),
      "body_content_type":body.get("contentType"),"body_preview":msg.get("bodyPreview") or "",
      "has_attachments":bool(msg.get("hasAttachments")),"folder_id":folder.get("id"),
      "folder_name":folder.get("displayName"),"is_read":msg.get("isRead"),"last_modified":msg.get("lastModifiedDateTime"),
      "web_link":msg.get("webLink"),"ingested_at":datetime.now().astimezone().isoformat(timespec="seconds")
    }

def stable_hash(x):
    key="|".join(str(x.get(k) or "") for k in ("graph_id","last_modified","subject","received_time"))
    return hashlib.sha256(key.encode("utf-8")).hexdigest()

def safe_name(s):
    s=re.sub(r'[^A-Za-z0-9._ -]+','_',str(s or 'attachment'))
    return s[:180] or 'attachment'

def attachment_rows(token,msg,cfg):
    if not msg.get("hasAttachments") or not cfg.get("include_attachment_metadata",True): return []
    mid=msg.get("id")
    doc=req(token,f"{GRAPH}/me/messages/{quote(mid,safe='')}/attachments",timeout=cfg.get("request_timeout_seconds",30))
    rows=[]
    for a in doc.get("value",[]):
        rec={"message_graph_id":mid,"attachment_id":a.get("id"),"odata_type":a.get("@odata.type"),"name":a.get("name"),
             "content_type":a.get("contentType"),"size":a.get("size"),"is_inline":a.get("isInline"),"local_path":"",
             "ingested_at":datetime.now().astimezone().isoformat(timespec="seconds")}
        content=a.get("contentBytes")
        if cfg.get("include_attachment_content") and content and str(a.get("@odata.type","")).endswith("fileAttachment"):
            if int(a.get("size") or 0)<=int(cfg.get("max_attachment_bytes",10485760)):
                folder=ATTDIR/safe_name(mid);folder.mkdir(parents=True,exist_ok=True);fp=folder/safe_name(a.get("name"))
                fp.write_bytes(base64.b64decode(content));rec["local_path"]=str(fp)
        rows.append(rec)
    return rows

def sync_graph():
    cfg=jload(CFG,{})
    if not cfg.get("enabled"):
        doc={"engine_id":"ENG-051","gate":"DISABLED","message":"Enable config/outlook_graph.json after IT approval."}
        atomic(REPORT,doc);return doc
    if not (cfg.get("it_approval") or {}).get("acknowledged"):
        raise RuntimeError("IT_APPROVAL_NOT_ACKNOWLEDGED")
    token=get_token(cfg)
    all_folders=list_all_folders(token,cfg)
    selected=set(cfg.get("selected_folder_ids") or [])
    folders=[f for f in all_folders if cfg.get("folder_mode")=="all" or f["id"] in selected]
    atomic(FOLDERS,{"generated_at":datetime.now().astimezone().isoformat(timespec="seconds"),"folders":all_folders})
    ds=jload(delta_path(cfg),{})
    existing={}
    if RAW.exists():
        for ln in RAW.read_text(encoding="utf-8",errors="replace").splitlines():
            try:
                x=json.loads(ln);existing[x.get("graph_id")]=x
            except Exception:pass
    changed=0;deleted=0;pages=0;attachments=[]
    select="id,internetMessageId,conversationId,subject,receivedDateTime,sentDateTime,from,toRecipients,ccRecipients,hasAttachments,body,bodyPreview,parentFolderId,isRead,lastModifiedDateTime,webLink"
    for f in folders:
        fid=f["id"];url=ds.get(fid) or f"{GRAPH}/me/mailFolders/{quote(fid,safe='')}/messages/delta?$select={select}&$top={int(cfg.get('page_size',50))}"
        max_pages=int(cfg.get("max_pages_per_folder",20));n=0
        while url and n<max_pages:
            doc=req(token,url,timeout=cfg.get("request_timeout_seconds",30));n+=1;pages+=1
            for m in doc.get("value",[]):
                mid=m.get("id")
                if "@removed" in m:
                    if mid in existing:existing.pop(mid,None);deleted+=1
                    continue
                x=normalized(m,f);x["source_hash"]=stable_hash(x)
                if not existing.get(mid) or existing[mid].get("source_hash")!=x["source_hash"]:
                    existing[mid]=x;changed+=1
                    if x.get("has_attachments"):
                        attachments.extend(attachment_rows(token,m,cfg))
            if doc.get("@odata.deltaLink"):
                ds[fid]=doc["@odata.deltaLink"]
            url=doc.get("@odata.nextLink")
    dp=delta_path(cfg);dp.parent.mkdir(parents=True,exist_ok=True);atomic(dp,ds)
    with RAW.open("w",encoding="utf-8") as fh:
        for x in sorted(existing.values(),key=lambda z:z.get("received_time") or ""):
            fh.write(json.dumps(x,ensure_ascii=False)+"\n")
    with MAILS.open("w",encoding="utf-8-sig",newline="") as fh:
        cols=["ConversationID","Subject","BODY_SNIPPET","FolderPath","SenderEmail","To","CC","EventDate","InternetMessageID","GraphID"]
        w=csv.DictWriter(fh,fieldnames=cols);w.writeheader()
        for x in existing.values():
            w.writerow({"ConversationID":x.get("conversation_id"),"Subject":x.get("subject"),
                        "BODY_SNIPPET":x.get("body_text") or x.get("body_preview"),
                        "FolderPath":x.get("folder_name"),"SenderEmail":x.get("sender_email"),
                        "To":";".join(x.get("to_list") or []),"CC":";".join(x.get("cc_list") or []),
                        "EventDate":x.get("received_time"),"InternetMessageID":x.get("internet_message_id"),"GraphID":x.get("graph_id")})
    if attachments:
        with ATTREG.open("a",encoding="utf-8") as af:
            for a in attachments: af.write(json.dumps(a,ensure_ascii=False)+"\n")
    rep={"engine_id":"ENG-051","gate":"PASS","folders":len(folders),"messages":len(existing),"changed":changed,"deleted":deleted,"pages":pages,
         "attachments_seen":len(attachments),"synced_at":datetime.now().astimezone().isoformat(timespec="seconds")}
    atomic(REPORT,rep);return rep

def sync_mock(path):
    doc=jload(path,{})
    msgs=doc.get("messages",doc if isinstance(doc,list) else [])
    folder={"id":"MOCK-INBOX","displayName":"Inbox"}
    rows=[normalized(x,folder) for x in msgs]
    for x in rows:x["source_hash"]=stable_hash(x)
    atts=[]
    for src,x in zip(msgs,rows):
        for a in src.get("attachments",[]) or []:
            rec={"message_graph_id":x.get("graph_id"),"attachment_id":a.get("id"),"odata_type":a.get("@odata.type","#microsoft.graph.fileAttachment"),
                 "name":a.get("name"),"content_type":a.get("contentType"),"size":a.get("size",0),"is_inline":a.get("isInline",False),"local_path":"",
                 "ingested_at":datetime.now().astimezone().isoformat(timespec="seconds")}
            content=a.get("contentBytes")
            if content:
                folderp=ATTDIR/safe_name(x.get("graph_id"));folderp.mkdir(parents=True,exist_ok=True);fp=folderp/safe_name(a.get("name"))
                fp.write_bytes(base64.b64decode(content));rec["local_path"]=str(fp)
            atts.append(rec)
    if atts:
        with ATTREG.open("w",encoding="utf-8") as af:
            for a in atts:af.write(json.dumps(a,ensure_ascii=False)+"\n")
    with RAW.open("w",encoding="utf-8") as f:
        for x in rows:f.write(json.dumps(x,ensure_ascii=False)+"\n")
    with MAILS.open("w",encoding="utf-8-sig",newline="") as fh:
        cols=["ConversationID","Subject","BODY_SNIPPET","FolderPath","SenderEmail","To","CC","EventDate","InternetMessageID","GraphID"]
        w=csv.DictWriter(fh,fieldnames=cols);w.writeheader()
        for x in rows:w.writerow({"ConversationID":x["conversation_id"],"Subject":x["subject"],"BODY_SNIPPET":x["body_text"],
          "FolderPath":"Inbox","SenderEmail":x["sender_email"],"To":";".join(x["to_list"]),"CC":";".join(x["cc_list"]),
          "EventDate":x["received_time"],"InternetMessageID":x["internet_message_id"],"GraphID":x["graph_id"]})
    rep={"engine_id":"ENG-051","gate":"PASS_MOCK","messages":len(rows)}
    atomic(REPORT,rep);return rep

def create_draft(subject,body,to_list):
    cfg=jload(CFG,{})
    if not cfg.get("allow_draft_write"):raise RuntimeError("DRAFT_WRITE_DISABLED")
    token=get_token({**cfg,"delegated_scopes_read":cfg.get("delegated_scopes_draft",["Mail.ReadWrite","User.Read"])})
    payload={"subject":subject,"body":{"contentType":"Text","content":body},
             "toRecipients":[{"emailAddress":{"address":x}} for x in to_list]}
    doc=req(token,f"{GRAPH}/me/messages",method="POST",json_body=payload,timeout=cfg.get("request_timeout_seconds",30))
    return {"id":doc.get("id"),"subject":doc.get("subject"),"isDraft":doc.get("isDraft"),"webLink":doc.get("webLink")}

def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest="cmd",required=True)
    sub.add_parser("sync");m=sub.add_parser("mock-sync");m.add_argument("file")
    d=sub.add_parser("draft");d.add_argument("--subject",required=True);d.add_argument("--body",required=True);d.add_argument("--to",action="append",required=True)
    sub.add_parser("status")
    a=ap.parse_args()
    try:
        if a.cmd=="sync":out=sync_graph()
        elif a.cmd=="mock-sync":out=sync_mock(Path(a.file))
        elif a.cmd=="draft":out=create_draft(a.subject,a.body,a.to)
        else:out=jload(REPORT,{})
        print(json.dumps(out,ensure_ascii=False,indent=2));return 0
    except Exception as e:
        print(json.dumps({"engine_id":"ENG-051","gate":"FAIL_CLOSED","error":str(e)},ensure_ascii=False,indent=2))
        return 2
if __name__=="__main__":raise SystemExit(main())
