# -*- coding: utf-8 -*-
"""ENG-058 Diagnostics + IT governance evidence."""
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
import argparse,html,importlib.util,json,platform,sys
from datetime import datetime
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;OUT=ROOT/"out";JSONP=OUT/"diagnostics.json";HTMLP=OUT/"diagnostics.html"
def jload(p,d):
    try:return json.loads(Path(p).read_text(encoding="utf-8-sig"))
    except Exception:return d
def exists(rel):return (ROOT/rel).exists()
def build():
    oc=jload(ROOT/"config"/"outlook_graph.json",{});ss=jload(OUT/"ssot_status.json",{});mr=jload(OUT/"module_registry_snapshot.json",{})
    deps={x:bool(importlib.util.find_spec(x)) for x in ("fastapi","uvicorn","requests","msal","duckdb","pyarrow","polars")}
    checks=[
      {"name":"Python >=3.12","ok":sys.version_info>=(3,12),"detail":platform.python_version()},
      {"name":"Localhost-only config","ok":jload(ROOT/"config"/"system_config.json",{}).get("server",{}).get("host")=="127.0.0.1","detail":"127.0.0.1"},
      {"name":"Outlook IT acknowledgement","ok":bool((oc.get("it_approval") or {}).get("acknowledged")) if oc.get("enabled") else True,"detail":"disabled" if not oc.get("enabled") else "enabled"},
      {"name":"Auto send disabled","ok":not oc.get("allow_send",False),"detail":str(oc.get("allow_send",False))},
      {"name":"SSOT available","ok":bool(ss.get("mode")),"detail":ss.get("mode","not snapshotted")},
      {"name":"Module registry health","ok":mr.get("gate") in ("PASS",None),"detail":mr.get("gate","not checked")},
      {"name":"UI product shell","ok":exists("ui/workops_app.html"),"detail":"ui/workops_app.html"}
    ]
    gate="PASS" if all(x["ok"] for x in checks) else "READY_WITH_WARNINGS"
    doc={"version":"v0200","engine_id":"ENG-058","generated_at":datetime.now().astimezone().isoformat(timespec="seconds"),
         "gate":gate,"checks":checks,"dependencies":deps,"privacy":jload(ROOT/"config"/"privacy_policy.json",{}),
         "outlook_permissions":{"read_scopes":oc.get("delegated_scopes_read"),"draft_scopes":oc.get("delegated_scopes_draft"),
                                "allow_draft_write":oc.get("allow_draft_write"),"allow_send":oc.get("allow_send")}}
    JSONP.write_text(json.dumps(doc,ensure_ascii=False,indent=2),encoding="utf-8")
    rows="".join(f"<tr><td>{html.escape(x['name'])}</td><td>{'PASS' if x['ok'] else 'WARN'}</td><td>{html.escape(x['detail'])}</td></tr>" for x in checks)
    HTMLP.write_text(f"""<!doctype html><meta charset=utf-8><title>WorkOps Diagnostics</title><style>body{{font:14px system-ui;max-width:1100px;margin:30px auto}}table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #ddd;padding:8px}}</style><h1>Veritas WorkOps Diagnostics</h1><p>Gate: <b>{gate}</b></p><table><tr><th>Check</th><th>Status</th><th>Detail</th></tr>{rows}</table>""",encoding="utf-8")
    return doc
def main():
    ap=argparse.ArgumentParser();ap.add_argument("command",nargs="?",default="build",choices=["build","status"]);a=ap.parse_args()
    print(json.dumps(build() if a.command=="build" else jload(JSONP,{}),ensure_ascii=False,indent=2));return 0
if __name__=="__main__":raise SystemExit(main())
