"""VPL-APP · single-file application generator.

Reads the SQLite store + module registry, serialises to JSON, injects into
template.html at the /*__VPL_DATA__*/ marker, writes a self-contained app.
Data-driven: more data -> richer views; the registry controls which views ship.
"""
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
import json
import os
from pathlib import Path
from ..core import store
from .. import registry
from .. import config as vplconfig

TEMPLATE = Path(__file__).with_name("template.html")
MARKER = "/*__VPL_DATA__*/{}"

PWA_MANIFEST = {
    "name": "VeritasPulse", "short_name": "VeritasPulse", "start_url": ".",
    "display": "standalone", "background_color": "#f5f4f0", "theme_color": "#5e7032",
    "icons": [{"src": "vpl_icon.svg", "sizes": "any", "type": "image/svg+xml"}],
}
PWA_ICON = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 192 192">'
            '<rect width="192" height="192" rx="42" fill="#5e7032"/>'
            '<circle cx="96" cy="96" r="30" fill="none" stroke="#f5f4f0" stroke-width="12"/>'
            '<circle cx="96" cy="96" r="8" fill="#f5f4f0"/></svg>')
SW_JS = ("const C='vpl-v1';self.addEventListener('install',e=>{self.skipWaiting()});"
         "self.addEventListener('activate',e=>e.waitUntil(clients.claim()));"
         "self.addEventListener('fetch',e=>{e.respondWith(caches.open(C).then(c=>"
         "c.match(e.request).then(r=>r||fetch(e.request).then(n=>{try{c.put(e.request,n.clone())}catch(_){}"
         "return n}).catch(()=>r))))});")


def _modules(cfg):
    out = []
    for m in registry.MODULES:
        on = cfg["modules"].get(m["id"], m.get("enabled", True))
        if on:
            out.append(m)
    return out


def build(db_path: str, out_dir: str = "output",
          out_name: str = "VeritasPulse_App.html", project_id: int = 1) -> str:
    os.makedirs(out_dir, exist_ok=True)
    store.init_db(db_path, seed=True)
    cfg = vplconfig.load(out_dir)
    project = store.load_project(db_path, project_id)
    data = {
        "project": project,
        "modules": _modules(cfg),
        "groups": registry.GROUP_LABEL,
        "config": cfg,
    }
    payload = json.dumps(data, ensure_ascii=False)
    html = TEMPLATE.read_text(encoding="utf-8").replace(MARKER, payload, 1)
    out = os.path.join(out_dir, out_name)
    Path(out).write_text(html, encoding="utf-8")
    if cfg.get("pwa"):
        Path(os.path.join(out_dir, "manifest.webmanifest")).write_text(
            json.dumps(PWA_MANIFEST, ensure_ascii=False, indent=2), encoding="utf-8")
        Path(os.path.join(out_dir, "vpl_icon.svg")).write_text(PWA_ICON, encoding="utf-8")
        Path(os.path.join(out_dir, "service-worker.js")).write_text(SW_JS, encoding="utf-8")
    return out


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="output/veritaspulse.db")
    ap.add_argument("--out", default="output")
    a = ap.parse_args()
    path = build(a.db, a.out)
    print(f"[VPL] app: {path}")
