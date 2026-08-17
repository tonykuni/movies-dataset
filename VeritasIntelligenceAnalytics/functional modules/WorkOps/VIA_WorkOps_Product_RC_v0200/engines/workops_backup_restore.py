# -*- coding: utf-8 -*-
"""ENG-057 Backup, verify, and restore-to-staging. Token cache excluded by default."""
from __future__ import annotations
import argparse,fnmatch,hashlib,json,zipfile
from datetime import datetime
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;CFG=ROOT/"config"/"privacy_policy.json"
def jload(p,d):
    try:return json.loads(Path(p).read_text(encoding="utf-8-sig"))
    except Exception:return d
def sha(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()
def excluded(rel,patterns):
    s=str(rel).replace("\\","/")
    return any(fnmatch.fnmatch(s,p) for p in patterns)
def backup():
    cfg=jload(CFG,{});patterns=cfg.get("backup_exclusions",[]);stamp=datetime.now().strftime("%Y%m%d_%H%M%S")
    root=ROOT/"backups";root.mkdir(exist_ok=True);zp=root/f"VIA_WorkOps_Backup_{stamp}.zip";manifest=[]
    include_roots=["config","out","ssot","registry","templates"]
    with zipfile.ZipFile(zp,"w",zipfile.ZIP_DEFLATED) as z:
        for d in include_roots:
            p=ROOT/d
            if not p.exists():continue
            for f in p.rglob("*"):
                if not f.is_file():continue
                rel=f.relative_to(ROOT)
                if excluded(rel,patterns):continue
                z.write(f,rel);manifest.append({"path":str(rel).replace("\\","/"),"sha256":sha(f),"bytes":f.stat().st_size})
        z.writestr("BACKUP_MANIFEST.json",json.dumps({"created_at":datetime.now().astimezone().isoformat(timespec="seconds"),"files":manifest},ensure_ascii=False,indent=2))
    return {"gate":"PASS","backup":str(zp),"sha256":sha(zp),"files":len(manifest)}
def verify(zpath):
    zpath=Path(zpath);issues=[]
    with zipfile.ZipFile(zpath) as z:
        m=json.loads(z.read("BACKUP_MANIFEST.json"))
        for x in m["files"]:
            data=z.read(x["path"]);h=hashlib.sha256(data).hexdigest()
            if h!=x["sha256"]:issues.append(x["path"])
    return {"gate":"PASS" if not issues else "FAIL","issues":issues,"sha256":sha(zpath)}
def restore(zpath):
    zpath=Path(zpath);v=verify(zpath)
    if v["gate"]!="PASS":raise RuntimeError("BACKUP_VERIFY_FAILED")
    target=ROOT/"restore_staging"/zpath.stem
    if target.exists():raise RuntimeError("RESTORE_STAGING_ALREADY_EXISTS")
    target.mkdir(parents=True)
    with zipfile.ZipFile(zpath) as z:z.extractall(target)
    return {"gate":"STAGED_REVIEW_REQUIRED","staging":str(target),"canonical_mutation":False}
def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest="cmd",required=True);sub.add_parser("backup")
    v=sub.add_parser("verify");v.add_argument("zip");r=sub.add_parser("restore");r.add_argument("zip");a=ap.parse_args()
    o=backup() if a.cmd=="backup" else verify(a.zip) if a.cmd=="verify" else restore(a.zip)
    print(json.dumps(o,ensure_ascii=False,indent=2));return 0
if __name__=="__main__":raise SystemExit(main())
