"""VPL-C00 · Environment Arrangement (with Veritas supportive tools).

"善用支援工具,跟 Veritas 一起安排環境."

Instead of a naive pip install, VeritasPulse provisions its venv THROUGH the
VIA supportive ecosystem:

  1. HardGate scan      — VIA_Supportive_Runtime_HardGate_Bridge
                          (Celeritas parallel LOCKED, Aegis network LOCKED)
  2. Env snapshot       — VIA_EnvManager.def_scan_all_envs()
  3. Gated plan         — VIA_EnvManager.def_plan_install_request() per dep
                          (risk routing, via_core whitelist, conflict-aware)
  4. Health record      — VIS_InstallHealthRegistry.def_write_health_registry()
  5. VIA-locked HTML report of the whole arrangement.

PLAN-ONLY by default (planner-only, append-only). Execution is opt-in and even
then defers to EnvManager's own gatekeeper commands. Degrades gracefully when
the supportive modules aren't reachable (e.g. a fresh machine / sandbox).
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
import importlib.util
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from .. import theme as T

# Default location of Tony's supportive modules
DEFAULT_SUPPORTIVE_ROOT = Path(
    r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module"
)

# VeritasPulse dependency manifest — pinned, numpy golden rule honoured.
VPL_DEPS = [
    ("numpy",       ">=1.24,<2.0", "array core · golden rule"),
    ("python-pptx", "==1.0.2",     "PPT generation engine"),
    ("matplotlib",  ">=3.7,<3.11", "chart auto-optimize"),
    ("Pillow",      ">=10.0",      "image sizing for deck"),
    ("duckdb",      ">=1.0,<2.0",  "warehouse query engine"),
    ("pyarrow",     ">=14,<25",    "Parquet columnar storage"),
    ("openpyxl",    ">=3.1",       "Excel transcript template"),
]
# Optional (best-effort): weasyprint for server-side PDF. On Windows it needs the
# GTK runtime; if absent, minutes still ship as HTML and PDF is produced via the
# app's browser print button. Not forced into the core arrangement.
VPL_DEPS_OPTIONAL = [("weasyprint", ">=60", "server-side minutes PDF (needs GTK on Windows)"),
                     ("pikepdf", ">=8", "PDF optimization (linearize/compress)")]

# Supportive modules + their lock posture (mirrors the HardGate role map)
SUPPORTIVE = {
    "VIA_EnvManager":            {"role": "ENV_HEALTH_GATE",   "lock": None},
    "VIS_InstallHealthRegistry": {"role": "HEALTH_REGISTRY",   "lock": None},
    "VeritasCeleritas":          {"role": "ACCELERATOR",       "lock": "PARALLEL_LOCKED"},
    "VeritasAegisNexus":         {"role": "NETWORK",           "lock": "NETWORK_LOCKED"},
}


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _load(module_name: str, root: Path):
    """Optional import of a supportive module from `root`. Returns module or None."""
    path = root / f"{module_name}.py"
    if not path.exists():
        return None
    try:
        spec = importlib.util.spec_from_file_location(module_name, str(path))
        mod = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = mod
        spec.loader.exec_module(mod)
        return mod
    except BaseException:
        return None


def arrange(supportive_root: str | os.PathLike | None = None,
            preferred_env: str = "vpl_core",
            out_dir: str = "output",
            execute: bool = False) -> dict:
    root = Path(supportive_root) if supportive_root else DEFAULT_SUPPORTIVE_ROOT
    os.makedirs(out_dir, exist_ok=True)

    envm = _load("VIA_EnvManager", root)
    health = _load("VIS_InstallHealthRegistry", root)

    report = {
        "generated_at": _now(),
        "supportive_root": str(root),
        "veritas_available": envm is not None,
        "planner_only": not execute,
        "locks": {"network_io": "LOCKED", "parallel_accelerator": "LOCKED"},
        "supportive": {},
        "decisions": [],
        "summary": {"approved": 0, "blocked": 0, "deps": len(VPL_DEPS)},
    }

    # 1. HardGate posture (we never activate Celeritas/Aegis here)
    for name, meta in SUPPORTIVE.items():
        p = root / f"{name}.py"
        report["supportive"][name] = {
            "role": meta["role"], "lock": meta["lock"], "exists": p.exists(),
        }

    # 2. env snapshot (best-effort)
    if envm is not None:
        try:
            scan = envm.def_scan_all_envs()
            report["env_scan"] = {"ok": scan.get("ok"),
                                  "env_count": scan.get("env_count"),
                                  "conflict_count": scan.get("conflict_count"),
                                  "html_report": scan.get("html_report")}
        except Exception as exc:
            report["env_scan"] = {"ok": False, "error": str(exc)}

    # 3. gated plan per dependency
    records = []
    for pkg, ver, reason in VPL_DEPS:
        if envm is not None:
            try:
                plan = envm.def_plan_install_request(
                    pkg, requested_version=ver, reason=reason,
                    preferred_env=preferred_env)
                dec = plan.get("decision", {})
                approved = bool(dec.get("approved"))
                row = {"package": pkg, "version": ver, "reason": reason,
                       "risk": dec.get("risk_level", "LOW"),
                       "approved": approved,
                       "target_env": dec.get("target_env", ""),
                       "blocked_reason": dec.get("blocked_reason", ""),
                       "ps_commands": dec.get("powershell_commands", []),
                       "via_veritas": True}
            except Exception as exc:
                row = {"package": pkg, "version": ver, "reason": reason,
                       "risk": "LOW", "approved": False,
                       "blocked_reason": f"PLAN_ERROR: {exc}", "via_veritas": True}
        else:
            # graceful fallback — record the intended pinned install, flag bypass
            row = {"package": pkg, "version": ver, "reason": reason,
                   "risk": "LOW", "approved": True, "target_env": preferred_env,
                   "blocked_reason": "", "ps_commands": [],
                   "via_veritas": False,
                   "note": "Veritas EnvManager not reachable — pinned fallback"}

        report["decisions"].append(row)
        report["summary"]["approved" if row["approved"] else "blocked"] += 1
        status = "PASS" if row["approved"] else "WARN"
        records.append({
            "name": f"{pkg}{ver}",
            "status": status,
            "path": row.get("target_env", preferred_env),
            "message": row["reason"] if row["approved"] else row.get("blocked_reason", ""),
            "detail": {"risk": row["risk"], "via_veritas": row["via_veritas"]},
        })

    # 4. record into VIS_InstallHealthRegistry (or local JSON fallback)
    reg_path = os.path.join(out_dir, "vpl_install_health.json")
    if health is not None:
        try:
            health.def_write_health_registry(
                reg_path,
                [health.def_make_record(r["name"], r["status"], r["path"],
                                        r["message"], r["detail"]) for r in records],
                metadata={"product": "VeritasPulse", "preferred_env": preferred_env,
                          "arranged_with_veritas": envm is not None})
            report["health_registry"] = reg_path
        except Exception as exc:
            report["health_registry_error"] = str(exc)
            _local_registry(reg_path, records)
            report["health_registry"] = reg_path
    else:
        _local_registry(reg_path, records)
        report["health_registry"] = reg_path

    # 5. HTML report
    html_path = os.path.join(out_dir, "vpl_env_arrangement.html")
    Path(html_path).write_text(_render_html(report), encoding="utf-8")
    report["html"] = html_path

    json_path = os.path.join(out_dir, "vpl_env_arrangement.json")
    Path(json_path).write_text(json.dumps(report, ensure_ascii=False, indent=2),
                               encoding="utf-8")
    return report


def _local_registry(path, records):
    payload = {"schema": "VIS_INSTALL_HEALTH_REGISTRY_V1_LOCAL", "generated": _now(),
               "records": records,
               "summary": {"total": len(records),
                           "ok": sum(1 for r in records if r["status"] in ("PASS", "OK")),
                           "warn": sum(1 for r in records if r["status"] == "WARN")}}
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                          encoding="utf-8")


def _render_html(rep: dict) -> str:
    veritas = rep["veritas_available"]
    badge = ("ARRANGED WITH VERITAS" if veritas
             else "FALLBACK · VERITAS NOT REACHABLE")
    badge_col = T.ACCENT if veritas else T.AMBER
    rows = []
    for d in rep["decisions"]:
        col = T.ACCENT if d["approved"] else T.AMBER
        state = "APPROVED" if d["approved"] else "HOLD"
        detail = d["reason"] if d["approved"] else d.get("blocked_reason", "")
        rows.append(
            f"<tr><td class='mono'>{d['package']}{d['version']}</td>"
            f"<td>{d['risk']}</td><td class='mono'>{d.get('target_env','') or '—'}</td>"
            f"<td style='color:#{col};font-weight:700'>{state}</td>"
            f"<td>{detail}</td></tr>")
    sup = []
    for name, m in rep["supportive"].items():
        lock = m["lock"] or "—"
        lc = T.RUST if m["lock"] else T.INK_FAINT
        ex = T.ACCENT if m["exists"] else T.RUST
        sup.append(
            f"<tr><td class='mono'>{name}</td><td>{m['role']}</td>"
            f"<td style='color:#{lc}'>{lock}</td>"
            f"<td style='color:#{ex}'>{'found' if m['exists'] else 'missing'}</td></tr>")
    s = rep["summary"]
    return f"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">
<title>VeritasPulse · Env Arrangement</title>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@400;500;600&family=DM+Mono&display=swap" rel="stylesheet">
<style>
body{{font-family:'DM Sans',sans-serif;background:#{T.BG};color:#{T.INK};margin:0;padding:34px 30px;max-width:1080px;margin:auto}}
.mono{{font-family:'DM Mono',monospace;font-size:12px}}
header{{display:flex;align-items:flex-end;gap:14px;border-bottom:2px solid #{T.INK};padding-bottom:16px;margin-bottom:22px}}
.logo{{font-family:'Syne',sans-serif;font-weight:800;font-size:26px;letter-spacing:-.02em;display:flex;align-items:center;gap:10px}}
.dot{{width:11px;height:11px;border-radius:3px;background:#{T.ACCENT};box-shadow:0 0 0 4px #{T.ACCENT}22}}
.badge{{margin-left:auto;font-family:'DM Mono',monospace;font-size:11px;letter-spacing:.08em;color:#fff;background:#{badge_col};padding:5px 11px;border-radius:6px}}
.lead{{display:flex;gap:12px;margin-bottom:22px}}
.b{{background:#{T.PANEL};border:1px solid #{T.LINE};border-radius:10px;padding:13px 16px;flex:1}}
.b .k{{font-family:'DM Mono',monospace;font-size:9px;letter-spacing:.12em;text-transform:uppercase;color:#{T.INK_FAINT}}}
.b .v{{font-family:'Syne',sans-serif;font-weight:700;font-size:24px;margin-top:4px}}
h2{{font-family:'Syne',sans-serif;font-size:15px;margin:26px 0 10px}}
table{{width:100%;border-collapse:collapse;background:#{T.PANEL};border:1px solid #{T.LINE};border-radius:10px;overflow:hidden;font-size:13px}}
th{{background:#{T.PANEL_ALT};text-align:left;font-family:'DM Mono',monospace;font-size:9px;letter-spacing:.1em;text-transform:uppercase;color:#{T.INK_FAINT};padding:9px 12px}}
td{{padding:9px 12px;border-top:1px solid #{T.LINE}}}
.note{{background:#{T.ACCENT}14;border:1px solid #{T.ACCENT}55;border-left:4px solid #{T.ACCENT};border-radius:6px;padding:12px 14px;font-size:12.5px;margin-top:18px;color:#2a4430}}
footer{{margin-top:28px;padding-top:14px;border-top:1px solid #{T.LINE};font-family:'DM Mono',monospace;font-size:9.5px;color:#{T.INK_FAINT}}}
</style></head><body>
<header><div class="logo"><span class="dot"></span>VeritasPulse</div>
<span class="badge">{badge}</span></header>
<div class="lead">
<div class="b"><div class="k">Dependencies</div><div class="v">{s['deps']}</div></div>
<div class="b"><div class="k">Approved</div><div class="v" style="color:#{T.ACCENT}">{s['approved']}</div></div>
<div class="b"><div class="k">On hold</div><div class="v" style="color:#{T.AMBER}">{s['blocked']}</div></div>
<div class="b"><div class="k">Mode</div><div class="v" style="font-size:15px">{'PLAN-ONLY' if rep['planner_only'] else 'EXECUTE'}</div></div>
</div>
<h2>Supportive modules · lock posture</h2>
<table><tr><th>Module</th><th>Role</th><th>Lock</th><th>State</th></tr>{''.join(sup)}</table>
<h2>Dependency plan · gated by EnvManager</h2>
<table><tr><th>Package</th><th>Risk</th><th>Target env</th><th>Decision</th><th>Note</th></tr>{''.join(rows)}</table>
<div class="note">Network I/O (Aegis) and parallel accelerator (Celeritas) remain <b>LOCKED</b>.
This is a {'plan' if rep['planner_only'] else 'executed arrangement'} recorded to the
install-health registry; nothing is patched automatically.</div>
<footer>VeritasPulse · arranged with Veritas supportive tools · {rep['generated_at']} · VIA Visual Lock v1</footer>
</body></html>"""


def deploy(supportive_root: str | os.PathLike | None = None,
           preferred_env: str = "vpl_core", out_dir: str = "output",
           dry_run: bool = True) -> dict:
    """AUTO DEPLOY — but only AFTER a conflict-risk verification gate passes.

    Gate (all must pass): Veritas reachable for verification · every dependency
    approved · env scan conflict-free · base-VIA conflict check clean · numpy
    golden rule. If clean and not dry_run, installs are executed THROUGH
    EnvManager's governed executor; otherwise the gated PS commands are emitted.
    """
    root = Path(supportive_root) if supportive_root else DEFAULT_SUPPORTIVE_ROOT
    rep = arrange(root, preferred_env, out_dir, execute=False)
    envm = _load("VIA_EnvManager", root)

    gate = {"checks": [], "passed": True}
    def add(name, ok, detail):
        gate["checks"].append({"check": name, "ok": bool(ok), "detail": detail})
        if not ok:
            gate["passed"] = False

    # 1. verification only meaningful if EnvManager is reachable
    add("Veritas reachable (verification available)", envm is not None,
        "EnvManager loaded" if envm is not None else "not reachable — cannot verify conflicts")
    # 2. every dependency approved by the gatekeeper
    holds = [d["package"] for d in rep["decisions"] if not d["approved"]]
    add("all dependencies approved", not holds, f"holds: {holds}" if holds else "no holds")
    # 3. env scan conflict-free
    cc = rep.get("env_scan", {}).get("conflict_count")
    add("env scan conflict-free", cc in (0, None), f"conflict_count={cc}")
    # 4. base VIA conflict check
    base = None
    if envm is not None and hasattr(envm, "def_get_base_via_conflicts"):
        try:
            bc = envm.def_get_base_via_conflicts()
            base = (bc.get("conflict_count", 0) if isinstance(bc, dict)
                    else (len(bc) if bc else 0))
        except Exception as exc:
            base = f"err:{exc}"
    add("base VIA conflict check", base in (0, None), f"base_conflicts={base}")
    # 5. numpy golden rule guard
    np_bad = [d for d in rep["decisions"] if d["package"] == "numpy" and "<2.0" not in d["version"]]
    add("numpy golden rule (<2.0)", not np_bad, "numpy pinned <2.0")

    actions, executed = [], False
    if gate["passed"] and not dry_run and envm is not None and hasattr(envm, "def_execute_install_request"):
        executed = True
        for d in rep["decisions"]:
            try:
                res = envm.def_execute_install_request(
                    d["package"], requested_version=d["version"], preferred_env=preferred_env)
                actions.append({"package": d["package"], "executed": True, "result": str(res)[:160]})
            except Exception as exc:
                actions.append({"package": d["package"], "executed": False, "error": str(exc)})
    else:
        actions = [{"package": d["package"], "executed": False,
                    "ps_commands": d.get("ps_commands", [])} for d in rep["decisions"]]

    drep = {"generated_at": _now(), "gate": gate, "gate_passed": gate["passed"],
            "deployed": executed, "dry_run": dry_run, "actions": actions,
            "arrangement_html": rep.get("html"),
            "verdict": ("DEPLOYED" if executed else
                        ("READY (dry-run · gate passed)" if gate["passed"] else "BLOCKED · conflicts unverified"))}
    Path(os.path.join(out_dir, "vpl_deploy.json")).write_text(
        json.dumps(drep, ensure_ascii=False, indent=2), encoding="utf-8")
    Path(os.path.join(out_dir, "vpl_deploy.html")).write_text(
        _render_deploy_html(drep), encoding="utf-8")
    return drep


def _render_deploy_html(d: dict) -> str:
    passed = d["gate_passed"]
    col = T.ACCENT if passed else T.RUST
    checks = "".join(
        f"<tr><td>{c['check']}</td><td style='color:#{T.ACCENT if c['ok'] else T.RUST};font-weight:700'>"
        f"{'PASS' if c['ok'] else 'FAIL'}</td><td class='mono'>{c['detail']}</td></tr>"
        for c in d["gate"]["checks"])
    return f"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">
<title>VeritasPulse · Auto Deploy</title>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@800&family=DM+Sans&family=DM+Mono&display=swap" rel="stylesheet">
<style>body{{font-family:'DM Sans';background:#{T.BG};color:#{T.INK};max-width:920px;margin:auto;padding:34px 30px}}
.mono{{font-family:'DM Mono';font-size:11.5px}}
h1{{font-family:'Syne';font-weight:800;font-size:24px;display:flex;align-items:center;gap:11px}}
.dot{{width:12px;height:12px;border-radius:3px;background:#{T.ACCENT};box-shadow:0 0 0 4px #{T.ACCENT}22}}
.verdict{{margin-left:auto;font-family:'DM Mono';font-size:13px;color:#fff;background:#{col};padding:6px 14px;border-radius:7px}}
table{{width:100%;border-collapse:collapse;background:#{T.PANEL};border:1px solid #{T.LINE};border-radius:10px;overflow:hidden;margin-top:18px;font-size:13px}}
th{{background:#{T.PANEL_ALT};text-align:left;font-family:'DM Mono';font-size:9px;letter-spacing:.1em;text-transform:uppercase;color:#{T.INK_FAINT};padding:9px 12px}}
td{{padding:9px 12px;border-top:1px solid #{T.LINE}}}
.note{{background:#{col}14;border:1px solid #{col}55;border-left:4px solid #{col};border-radius:6px;padding:12px 14px;font-size:12.5px;margin-top:18px}}</style></head><body>
<h1><span class="dot"></span>Auto Deploy · 衝突風險驗證<span class="verdict">{d['verdict']}</span></h1>
<table><tr><th>Verification gate</th><th>Result</th><th>Detail</th></tr>{checks}</table>
<div class="note">{'✓ 驗證通過 — ' + ('已透過 EnvManager 治理執行布建。' if d['deployed'] else '乾跑模式:閘門通過,實際布建請以 dry_run=False 執行(經 EnvManager)。') if passed else '✗ 未通過衝突驗證 — 不自動布建。請先讓 Veritas EnvManager 可達並解決衝突。'}</div>
<footer style="margin-top:26px;font-family:'DM Mono';font-size:9.5px;color:#{T.INK_FAINT}">VeritasPulse · 無衝突風險驗證後才自動布建 · {d['generated_at']}</footer>
</body></html>"""


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(DEFAULT_SUPPORTIVE_ROOT))
    ap.add_argument("--env", default="vpl_core")
    ap.add_argument("--out", default="output")
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--deploy", action="store_true", help="run conflict-gated auto-deploy")
    ap.add_argument("--live", action="store_true", help="with --deploy: execute (not dry-run)")
    a = ap.parse_args()
    if a.deploy:
        d = deploy(a.root, a.env, a.out, dry_run=not a.live)
        print(json.dumps({"verdict": d["verdict"], "gate_passed": d["gate_passed"],
                          "deployed": d["deployed"], "html": "output/vpl_deploy.html"},
                         ensure_ascii=False, indent=2))
    else:
        r = arrange(a.root, a.env, a.out, a.execute)
        print(json.dumps({"veritas": r["veritas_available"],
                          "approved": r["summary"]["approved"],
                          "blocked": r["summary"]["blocked"],
                          "health_registry": r.get("health_registry"),
                          "html": r.get("html")}, ensure_ascii=False, indent=2))
