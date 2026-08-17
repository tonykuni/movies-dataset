# -*- coding: utf-8 -*-
"""ENG-033 Project Registration Engine.
Immutable PRJ IDs, user-owned display names, append-only registry and classification memory.
"""
from __future__ import annotations
import argparse,json
from datetime import datetime
from pathlib import Path
from workops_autocode import next_code

HERE=Path(__file__).resolve().parent
WORKOPS=HERE.parent
OUT=WORKOPS/"out"
REG=OUT/"project_registry.jsonl"
MEM=OUT/"classification_memory.jsonl"

def loadjl(p):
    rows=[]
    if not Path(p).exists(): return rows
    for ln in Path(p).read_text(encoding="utf-8",errors="replace").splitlines():
        try:rows.append(json.loads(ln))
        except Exception:pass
    return rows
def append(p,obj):
    OUT.mkdir(parents=True,exist_ok=True)
    with Path(p).open("a",encoding="utf-8") as f:f.write(json.dumps(obj,ensure_ascii=False)+"\n")
def current(pid):
    rows=[r for r in loadjl(REG) if r.get("project_id")==pid]
    if not rows:return None
    cur={}
    for r in rows:
        cur.update({k:v for k,v in r.items() if v is not None})
    return cur
def create(name, aliases=None, product_codes=None, folders=None, stakeholders=None):
    pid=next_code("PRJ")
    now=datetime.now().isoformat(timespec="seconds")
    obj={"event":"CREATE","ts":now,"project_id":pid,"display_name":name.strip(),
         "aliases":aliases or [],"product_codes":product_codes or [],"folders":folders or [],
         "stakeholders":stakeholders or [],"status":"ACTIVE","human_confirmed":True}
    append(REG,obj); return obj
def rename(pid,name):
    if not current(pid): raise SystemExit("unknown project_id")
    obj={"event":"RENAME","ts":datetime.now().isoformat(timespec="seconds"),
         "project_id":pid,"display_name":name.strip(),"human_confirmed":True}
    append(REG,obj); return obj
def accept(conv,pid,folder="",product_codes=None):
    if not current(pid): raise SystemExit("unknown project_id")
    obj={"event":"CLASSIFICATION_CONFIRM","ts":datetime.now().isoformat(timespec="seconds"),
         "conversation_id":conv,"project_id":pid,"decision":"ACCEPT","folders":[folder] if folder else [],
         "product_codes":product_codes or [],"human_confirmed":True}
    append(MEM,obj); return obj
def list_projects():
    ids=sorted({r.get("project_id") for r in loadjl(REG) if r.get("project_id")})
    return [current(x) for x in ids]
def main():
    ap=argparse.ArgumentParser()
    sub=ap.add_subparsers(dest="cmd",required=True)
    c=sub.add_parser("create"); c.add_argument("name")
    r=sub.add_parser("rename"); r.add_argument("project_id"); r.add_argument("name")
    a=sub.add_parser("accept"); a.add_argument("conversation_id"); a.add_argument("project_id"); a.add_argument("--folder",default=""); a.add_argument("--product",action="append",default=[])
    sub.add_parser("list")
    x=ap.parse_args()
    if x.cmd=="create": out=create(x.name)
    elif x.cmd=="rename": out=rename(x.project_id,x.name)
    elif x.cmd=="accept": out=accept(x.conversation_id,x.project_id,x.folder,x.product)
    else: out=list_projects()
    print(json.dumps(out,ensure_ascii=False,indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
