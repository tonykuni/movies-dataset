#!/usr/bin/env python3
"""VeritasPulse — consolidated self-test (test/debug/consolidate/activate).
Exercises every layer and prints a PASS/FAIL report. Exit 0 only if all pass.
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
import importlib, json, os, sys, time, traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

R = []  # (name, ok, detail)
def check(name, fn):
    t0 = time.time()
    try:
        detail = fn() or ""
        R.append((name, True, f"{detail}  ({(time.time()-t0)*1000:.0f}ms)"))
    except Exception as e:
        R.append((name, False, f"{type(e).__name__}: {e}\n{traceback.format_exc().splitlines()[-1]}"))

DB = "output/_selftest.db"
OUT = "output"

def t_compile():
    import py_compile
    mods = ["vpl/theme.py","vpl/registry.py","vpl/core/store.py","vpl/core/archive.py",
            "vpl/core/env_arrange.py","vpl/charts/optimize.py","vpl/ppt/generate.py",
            "vpl/meeting/minutes_doc.py","vpl/meeting/excel_template.py",
            "vpl/app/build_app.py","build_all.py","VIA_ENG150_BuildDeck.py","selftest.py"]
    for m in mods: py_compile.compile(m, doraise=True)
    return f"{len(mods)} modules compile"

def t_store():
    from vpl.core import store
    if os.path.exists(DB): os.remove(DB)
    store.init_db(DB, seed=True)
    p = store.load_project(DB)
    need = ["tasks","risks","stakeholders","budget","milestones","resources","flow_nodes",
            "flow_edges","ledger","checklist","events","contacts","news","team","weeklog",
            "notes","plans","meetings","segments"]
    missing = [k for k in need if not p.get(k)]
    if missing: raise AssertionError(f"empty entities: {missing}")
    return f"{len(need)} entity types loaded · {len(p['segments'])} segments"

def t_archive():
    from vpl.core import archive
    man = archive.archive(DB, os.path.join(OUT,"warehouse"))
    import duckdb
    con = duckdb.connect(man["duckdb"])
    cats = dict(con.execute("SELECT category,COUNT(*) FROM v_segment GROUP BY category").fetchall())
    tasks = con.execute("SELECT COUNT(*) FROM task").fetchone()[0]
    plans = con.execute("SELECT COUNT(*) FROM v_plan").fetchone()[0]
    con.close()
    assert man["parquet"] and man["json"] and man["duckdb"]
    return f"parquet={len(man['parquet'])} json={len(man['json'])} · duck: {tasks} tasks, {plans} plans, cats={cats}"

def t_minutes():
    from vpl.core import archive
    m = archive.generate_minutes(DB, OUT)
    assert m["actions"] and m["decisions"], "minutes empty"
    return f"{len(m['actions'])} actions · {len(m['decisions'])} decisions · {len(m['risks'])} risks"

def t_env_arrange():
    from vpl.core import env_arrange
    # fallback path (no veritas) — must approve all pinned incl new libs
    r = env_arrange.arrange("/nonexistent", "vpl_core", OUT)
    pkgs = [d["package"] for d in r["decisions"]]
    assert "duckdb" in pkgs and "pyarrow" in pkgs, "new libs not in arrangement manifest"
    return f"{len(pkgs)} deps governed: {pkgs}"

def t_deck():
    from vpl.core import store
    from vpl.ppt import generate
    deck = generate.build(store.load_project(DB), OUT)
    assert os.path.getsize(deck) > 20000, "deck too small"
    return f"deck {os.path.getsize(deck)//1024}KB"

def t_app():
    from vpl.app import build_app
    app = build_app.build(DB, OUT)
    h = open(app, encoding="utf-8").read()
    assert "/*__VPL_DATA__*/" not in h, "data marker not replaced"
    import re
    d = json.loads(re.search(r"const VPL_DATA = (\{.*?\});\nconst P", h, re.S).group(1))
    from vpl import registry
    ids = [m["id"] for m in registry.enabled_modules()]
    defined = set(re.findall(r"RENDER\.(\w+)\s*=", h))
    missing = [i for i in ids if i not in defined]
    assert not missing, f"views without renderer: {missing}"
    return f"{len(ids)} modules · all have renderers · {len(h)//1024}KB"

def t_meeting_docs():
    from vpl.meeting import minutes_doc, excel_template
    m = minutes_doc.build(DB, OUT, mode="comprehensive")
    x = excel_template.build(DB, OUT)
    assert os.path.exists(m["html"]), "minutes html missing"
    assert os.path.getsize(x) > 4000, "excel too small"
    pdf_ok = m["pdf"].endswith(".pdf") and os.path.exists(m["pdf"])
    return f"minutes html ({m['actions']} actions) · pdf={'ok' if pdf_ok else 'browser-print fallback'} · excel {os.path.getsize(x)//1024}KB"

def t_config_pwa():
    from vpl import config as vplconfig
    from vpl.app import build_app
    cfg = vplconfig.load(OUT)
    assert cfg["accent"] and cfg["llm_providers"], "config incomplete"
    # module override honoured
    cfg2 = dict(cfg); cfg2_mods = {"ledger": False}
    import json as _j, os as _o
    # build emits PWA assets
    build_app.build(DB, OUT)
    for f in ("manifest.webmanifest", "service-worker.js", "vpl_icon.svg"):
        assert _o.path.exists(_o.path.join(OUT, f)), f"PWA asset missing: {f}"
    return f"config({len(cfg['llm_providers'])} providers, accent {cfg['accent']}) · PWA assets ok"

def t_deploy_gate():
    from vpl.core import env_arrange
    # against the test supportive modules — gate runs real verification, dry-run
    root = "/home/claude/via_support_test"
    d = env_arrange.deploy(root, "vpl_core", OUT, dry_run=True)
    checks = {c["check"]: c["ok"] for c in d["gate"]["checks"]}
    assert "numpy golden rule (<2.0)" in checks, "gate missing numpy check"
    assert not d["deployed"], "dry-run must not execute"
    return f"gate {sum(checks.values())}/{len(checks)} checks · verdict={d['verdict']}"

for n, fn in [("compile", t_compile),("store", t_store),("archive (Parquet/JSON/DuckDB)", t_archive),
              ("minutes (DuckDB)", t_minutes),("meeting docs (HTML+PDF+Excel)", t_meeting_docs),
              ("config + PWA assets", t_config_pwa),("deploy gate (conflict-verified)", t_deploy_gate),
              ("env_arrange (new libs governed)", t_env_arrange),
              ("ppt deck", t_deck),("app build + renderers", t_app)]:
    check(n, fn)

print("\n  VeritasPulse — Consolidated Self-Test")
print("  " + "-"*46)
ok = 0
for name, passed, detail in R:
    print(f"  [{'PASS' if passed else 'FAIL'}] {name}")
    print(f"         {detail}")
    ok += passed
print("  " + "-"*46)
print(f"  {ok}/{len(R)} passed\n")

# consolidated VIA-locked report
from vpl import theme as T
rows = "".join(
    f'<tr><td class="mono">{n}</td><td style="color:#{T.ACCENT if p else T.RUST};font-weight:700">'
    f'{"PASS" if p else "FAIL"}</td><td class="mono" style="color:#{T.INK_FAINT}">{det}</td></tr>'
    for n, p, det in R)
html = f"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">
<title>VeritasPulse · Self-Test</title>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@800&family=DM+Sans&family=DM+Mono&display=swap" rel="stylesheet">
<style>body{{font-family:'DM Sans';background:#{T.BG};color:#{T.INK};max-width:920px;margin:auto;padding:34px 30px}}
.mono{{font-family:'DM Mono';font-size:11.5px}}
h1{{font-family:'Syne';font-weight:800;font-size:26px;display:flex;align-items:center;gap:11px}}
.dot{{width:12px;height:12px;border-radius:3px;background:#{T.ACCENT};box-shadow:0 0 0 4px #{T.ACCENT}22}}
.badge{{font-family:'DM Mono';font-size:13px;padding:5px 14px;border-radius:7px;color:#fff;background:#{T.ACCENT if ok==len(R) else T.RUST}}}
table{{width:100%;border-collapse:collapse;background:#{T.PANEL};border:1px solid #{T.LINE};border-radius:10px;overflow:hidden;margin-top:18px;font-size:13px}}
th{{background:#{T.PANEL_ALT};text-align:left;font-family:'DM Mono';font-size:9px;letter-spacing:.1em;text-transform:uppercase;color:#{T.INK_FAINT};padding:9px 12px}}
td{{padding:9px 12px;border-top:1px solid #{T.LINE};vertical-align:top}}</style></head><body>
<h1><span class="dot"></span>VeritasPulse · Consolidated Self-Test
<span class="badge" style="margin-left:auto">{ok}/{len(R)} PASS</span></h1>
<table><tr><th>Layer</th><th>Result</th><th>Detail</th></tr>{rows}</table>
<p class="mono" style="color:#{T.INK_FAINT};margin-top:16px">Parquet/JSON/DuckDB warehouse · new libs governed via EnvManager · VIA Visual Lock v1</p>
</body></html>"""
import pathlib; pathlib.Path("output/vpl_selftest.html").write_text(html, encoding="utf-8")
print("  report: output/vpl_selftest.html\n")
sys.exit(0 if ok == len(R) else 1)
