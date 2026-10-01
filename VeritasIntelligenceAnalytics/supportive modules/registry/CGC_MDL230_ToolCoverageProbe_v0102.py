#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL230_ToolCoverageProbe v0102 — 全樹工具覆蓋矩陣(AST · PS 剖析器互核)+ HTML U/I 矩陣報告

v0101 → v0102(操作員 R37 2026-10-01:「PS檔案都要加加速器模組及HTML U/I MATRIX REPORT PY都要加加速器
探針 AST加高加速器覆蓋率 VDF都要加網路工具 允許一切授權」):

新動詞 matrix:一張矩陣把四個面一次量清楚,每面按組(VDF / VRN / VAP / HTML·U/I·MATRIX·REPORT / VCGC / 支援 / 根)分列:
  ① PY 加速器橋   ② 觸網 PY 網路工具橋   ③ VDF 全件網路工具橋(操作員點名:VDF 都要加)   ④ PS 加速器模組橋(尾版)
  另加 ⑤ 真用面:掛橋的 PY 裡,AST 讀得到真呼叫加速 API 的有幾支(掛橋 ≠ 加速)。
燈由正主判(L05 不立第二把尺):PY 標記 / 觸網判準 = via_bridge_sweeper 尾版(ACCEL_MARK · NET_MARK · NET_IMPORT_RX ·
classify 豁免圈),PS 標記 / 排除夾 = CGC_MDL117 尾版(PS_MARK · EXCLUDE_DIRS)。本支只加第二讀法:
  PY = Python ast(橋是不是模組層真程式碼,而不是註解或字串裡的字);PS = pwsh Parser(頂層 try 真的 dot-source
  VIA_PS_Accel_Module.ps1;沒有 pwsh 就文字判讀並標明)。兩法不一致 = AMBER,不冒充覆蓋。
具名豁免(正本 / 自指 / 凍結來源)一律附理由與「改由誰驗」,來自 VIA_ToolCoverageMatrix_SSOT 尾版(本支不另寫第二份)。
輸出 VIA_Reports/toolprobe/COVERAGE_MATRIX_latest.{json,html};有前次就逐面列「前次 → 本次」。
只讀 · 零網路 · 不安裝;probe 等其餘動詞照 v0101。

用法:
  python CGC_MDL230_ToolCoverageProbe_v0102.py matrix [--json] [--baseline <COVERAGE_MATRIX_*.json>] [--no-pwsh]
  python CGC_MDL230_ToolCoverageProbe_v0102.py probe …(照 v0101)
  python CGC_MDL230_ToolCoverageProbe_v0102.py --selftest
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import ast
import html
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEM = "CGC_MDL230_ToolCoverageProbe"


def _vnum(path: Path) -> int:
    match = re.search(r"_v(\d+)$", path.stem)
    return int(match.group(1)) if match else -1


def _prior() -> Path:
    mine = _vnum(Path(__file__))
    older = [p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < mine]
    if not older:
        raise ImportError(f"{STEM}: no version below v{mine:04d}")
    return max(older, key=_vnum)


PRIOR = _prior()
_spec = importlib.util.spec_from_file_location(f"{STEM}_prior_for_v{_vnum(Path(__file__)):04d}", PRIOR)
_PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _PRIOR
_spec.loader.exec_module(_PRIOR)

for _name, _value in vars(_PRIOR).items():
    if not _name.startswith("__") and _name not in globals():
        globals()[_name] = _value

VIA = _PRIOR.VIA
OUT = VIA / "VIA_Reports" / "toolprobe"
ENGINE_TAG = f"{STEM} v{_vnum(Path(__file__)):04d}"
SIDES = (("py_accel", "① PY 加速器橋"), ("py_net", "② 觸網 PY · 網路工具橋"),
         ("vdf_net", "③ VDF 全件 · 網路工具橋"), ("ps_accel", "④ PS 加速器模組橋(尾版)"))
SWEEP_RING = {"EXEMPT_INTAKE": "via_bridge_sweeper 收件圈(正本 / 收容夾)",
              "EXEMPT_SELF": "via_bridge_sweeper 自指圈(加速器 / 網路工具本體與清掃器)",
              "EXEMPT_LEGACY_NET": "via_bridge_sweeper 網路工具本體夾",
              "EXEMPT_TEMPLATE": "via_bridge_sweeper 正典 U/I TEMPLATE(manifest sha256 守)"}


def __getattr__(name: str):
    """Every public name of the prior version stays reachable here."""
    return getattr(_PRIOR, name)


def _tail_module(folder: Path, pattern: str, name: str):
    """Load the newest file matching pattern (the owner's ruler); None if absent."""
    hits = sorted(folder.glob(pattern), key=lambda p: (_vnum(p), p.name))
    if not hits:
        return None, "(不在)"
    spec = importlib.util.spec_from_file_location(name, hits[-1])
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod, hits[-1].name


def load_ssot(folder: Path = HERE) -> tuple:
    hits = sorted(folder.glob("VIA_ToolCoverageMatrix_SSOT_v*.json"), key=lambda p: (_vnum(p), p.name))
    if not hits:
        raise FileNotFoundError("VIA_ToolCoverageMatrix_SSOT 不在")
    return json.loads(hits[-1].read_text(encoding="utf-8")), hits[-1].name


def group_of(rel: str, ssot: dict) -> str:
    for g in ssot["groups"]:
        if re.search(g["rx"], rel):
            return g["id"]
    return "ROOT"


def exempt_of(rel: str, side: str, ssot: dict) -> dict | None:
    for e in ssot["exempt"]:
        if side in e["sides"] and e["match"] in rel:
            return e
    return None


# ── 第二讀法:Python ast ─────────────────────────────────────────────────
def py_ast(text: str, ssot: dict) -> dict:
    """AST reading of one .py: is each bridge real module-level code, does it touch the net, does it call accel."""
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError):
        return {"parse": False, "accel": False, "net": False, "need": False, "use": False}
    mods = set(ssot["ast"]["py_net_need_mods"])
    safe = set(ssot["ast"].get("py_net_safe") or [])
    use_names = set(ssot["ast"]["py_use"]["names"])
    use_of = ssot["ast"]["py_use"]["attr_of"]
    accel = net_assign = net_fn = False

    def _imports_accel(node) -> bool:
        if isinstance(node, ast.Import):
            return any(a.name == "VIA_SuperAccel_Module" for a in node.names)
        if isinstance(node, ast.ImportFrom):
            return node.module == "VIA_SuperAccel_Module" or any(a.name == "VIA_SuperAccel_Module" for a in node.names)
        return False

    def _assigns_net(node) -> bool:
        return isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "VIA_NET_TOOL_PATH" for t in node.targets)

    for node in tree.body:
        if isinstance(node, ast.Try):
            for sub in node.body:
                accel = accel or _imports_accel(sub)
                net_assign = net_assign or _assigns_net(sub)
        accel = accel or _imports_accel(node)
        net_assign = net_assign or _assigns_net(node)
        if isinstance(node, ast.FunctionDef) and node.name == "_via_net":
            net_fn = True
    need = use = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) and any(a.name.split(".")[0] in mods and a.name not in safe for a in node.names):
            need = True
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and (node.module or "").split(".")[0] in mods \
                and node.module not in safe and not all(f"{node.module}.{a.name}" in safe for a in node.names):
            need = True
        elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == use_of:
            use = True
        elif isinstance(node, ast.Call):
            fn = node.func
            if (isinstance(fn, ast.Name) and fn.id in use_names) or (isinstance(fn, ast.Attribute) and fn.attr in use_names):
                use = True
    return {"parse": True, "accel": accel, "net": net_assign and net_fn, "need": need, "use": use}


# ── 第二讀法:PS 剖析器 ──────────────────────────────────────────────────
_PS_PROBE = r"""
param([string]$ListFile)
$L = [System.Management.Automation.Language.Parser]
$out = foreach ($f in (Get-Content -LiteralPath $ListFile -Encoding utf8)) {
  $t = $null; $e = $null; $real = $false
  try {
    $a = $L::ParseFile($f, [ref]$t, [ref]$e)
    $blocks = @($a.BeginBlock, $a.ProcessBlock, $a.EndBlock) | Where-Object { $_ }
    foreach ($b in $blocks) {
      foreach ($s in $b.Statements) {
        if ($s -is [System.Management.Automation.Language.TryStatementAst] -and $s.Extent.Text -match 'VIA_PS_Accel_Module\.ps1') {
          $dots = $s.FindAll({ param($n) $n -is [System.Management.Automation.Language.CommandAst] -and $n.InvocationOperator -eq 'Dot' }, $true)
          if (@($dots).Count -gt 0) { $real = $true }
        }
      }
    }
    [pscustomobject]@{ f = $f; err = @($e).Count; real = $real }
  } catch { [pscustomobject]@{ f = $f; err = -1; real = $false } }
}
@($out) | ConvertTo-Json -Compress -AsArray
"""


def _pwsh() -> str | None:
    cand = os.environ.get("VIA_PWSH") or shutil.which("pwsh")
    return cand if cand and Path(cand).exists() else None


def ps_parse(files: list, no_pwsh: bool = False) -> tuple:
    """{abs path: {err, real}} via one pwsh Parser call; ({}, why) when pwsh is absent or fails."""
    exe = None if no_pwsh else _pwsh()
    if not exe or not files:
        return {}, ("pwsh 不在(文字判讀)" if not exe else "無檔")
    with tempfile.TemporaryDirectory() as td:
        lst, scr = Path(td) / "files.txt", Path(td) / "probe.ps1"
        lst.write_text("\n".join(str(f) for f in files), encoding="utf-8")
        scr.write_text(_PS_PROBE, encoding="utf-8")
        try:
            cp = subprocess.run([exe, "-NoProfile", "-NonInteractive", "-File", str(scr), "-ListFile", str(lst)],
                                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
            rows = json.loads(cp.stdout.strip() or "[]")
        except (subprocess.SubprocessError, OSError, json.JSONDecodeError) as exc:
            return {}, f"pwsh 剖析失敗 {type(exc).__name__}(文字判讀)"
    return {str(Path(r["f"])): {"err": r["err"], "real": bool(r["real"])} for r in rows}, f"pwsh Parser({Path(exe).name})"


# ── 量測 ─────────────────────────────────────────────────────────────────
def _ps_tails(root: Path, exclude: set, fam_rx: str) -> tuple:
    rx = re.compile(fam_rx)
    allps = []
    for r, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in exclude]
        allps += [Path(r) / f for f in files if f.endswith(".ps1")]
    best = {}
    for p in allps:
        m = rx.match(str(p.relative_to(root)).replace("\\", "/"))
        if m:
            k = m.group("fam")
            best[k] = max(best.get(k, -1), int(m.group("v")))
    tails, history = [], 0
    for p in allps:
        m = rx.match(str(p.relative_to(root)).replace("\\", "/"))
        if m and int(m.group("v")) != best[m.group("fam")]:
            history += 1
        else:
            tails.append(p)
    return sorted(tails), history


def _blank():
    return {"n": 0, "have": 0, "ast": 0, "exempt": 0, "miss": [], "disagree": [], "perr": [], "ex": {}}


def matrix(root: Path = VIA, ssot: dict | None = None, no_pwsh: bool = False) -> dict:
    root = Path(root)
    ssot_name = "(呼叫端給)"
    if ssot is None:
        ssot, ssot_name = load_ssot()
    sw, sw_name = _tail_module(HERE, "via_bridge_sweeper_v*.py", "_mdl230_sweeper")
    m117, m117_name = _tail_module(HERE, "CGC_MDL117_AccelCoverage_v*.py", "_mdl230_mdl117")
    if sw is None or m117 is None:
        return {"verdict": "NODATA", "why": f"正主不在:sweeper {sw_name} · MDL117 {m117_name}"}
    live, live_how = sw._live_set(root)
    cells = {s: {} for s, _ in SIDES}
    use = {"bridged": 0, "use": 0, "files": []}
    nonlive = 0

    def cell(side, grp):
        return cells[side].setdefault(grp, _blank())

    def put(side, rel, grp, have, real, ring_why=None, perr=False):
        c = cell(side, grp)
        c["n"] += 1
        e = exempt_of(rel, side, ssot)
        why = ring_why or (e and f"{e['id']} · {e['why']} · 改由:{e['verified_by']}")
        if why and not (have and real):                  # 豁免件:兩法都說有才算有,否則照豁免列(不進分母)
            c["exempt"] += 1
            c["ex"].setdefault(why, []).append(rel)
            return
        c["have"] += bool(have)
        c["ast"] += bool(real)
        if not have:
            c["miss"].append(rel)
        elif perr:
            c["perr"].append(rel)
        elif not real:
            c["disagree"].append(rel)

    for p in sorted(root.rglob("*.py")):
        rel = str(p.relative_to(root)).replace("\\", "/")
        cls = sw.classify(rel)
        if cls == "SKIP":
            continue
        if live is not None and str(p) not in live:
            nonlive += 1
            continue
        try:
            t = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        grp = group_of(rel, ssot)
        a = py_ast(t, ssot)
        ring = SWEEP_RING.get(cls) if cls != "ACTIVE" else None
        has_accel = sw.ACCEL_MARK in t or "VIA_SuperAccel_Module" in t
        put("py_accel", rel, grp, has_accel, a["accel"], ring)
        if has_accel and a["accel"]:
            use["bridged"] += 1
            if a["use"]:
                use["use"] += 1
                use["files"].append(rel)
        need = bool(sw.NET_IMPORT_RX.search(t)) or a["need"]
        note = ssot["ast"].get("py_net_note")
        if need and note and note in t and not a["need"]:
            ring_n = ring or "檔內 NET-BRIDGE:NOTE 具名豁免(只用非觸網子模組;AST 亦讀不到觸網 import)"
            put("py_net", rel, grp, False, False, ring_n)
        elif need:
            put("py_net", rel, grp, sw.NET_MARK in t, a["net"], ring)
        if rel.startswith("functional modules/VDF/"):
            put("vdf_net", rel, "VDF", sw.NET_MARK in t, a["net"], ring)
    tails, history = _ps_tails(root, set(m117.EXCLUDE_DIRS), ssot["ast"]["ps_family_rx"])
    parsed, ps_how = ps_parse(tails, no_pwsh=no_pwsh)
    for p in tails:
        rel = str(p.relative_to(root)).replace("\\", "/")
        data = p.read_bytes()
        have = any(mk in data for mk in m117.PS_MARK)
        pr = parsed.get(str(p))
        if pr is None:
            real, perr = have and b"VIA_PS_Accel_Module.ps1" in data, False
        else:
            real, perr = pr["real"] and pr["err"] == 0, pr["err"] != 0
        put("ps_accel", rel, group_of(rel, ssot), have, real, perr=perr)
    order = [g["id"] for g in ssot["groups"]]
    rows, totals = [], {}
    for side, title in SIDES:
        tot = _blank()
        for grp in order:
            c = cells[side].get(grp)
            if not c:
                continue
            for k in ("n", "have", "ast", "exempt"):
                tot[k] += c[k]
            tot["miss"] += c["miss"]
            tot["disagree"] += c["disagree"]
            tot["perr"] += c["perr"]
            for k, v in c["ex"].items():
                tot["ex"].setdefault(k, []).extend(v)
            rows.append(_row(side, title, grp, c, ssot))
        totals[side] = _summ(tot)
    verdict = "RED" if any(t["miss"] for t in totals.values()) else (
        "AMBER" if any(t["disagree"] or t["perr"] for t in totals.values()) else "GREEN")
    return {"engine": ENGINE_TAG, "ts_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
            "verdict": verdict, "ssot": ssot_name, "rulers": {"py": sw_name, "ps": m117_name, "live": live_how,
                                                             "ps_reader": ps_how},
            "rows": rows, "totals": totals, "nonlive_py": nonlive, "ps_history": history,
            "use": {"bridged": use["bridged"], "use": use["use"],
                    "pct": round(use["use"] * 100 / max(use["bridged"], 1), 1)},
            "groups": {g["id"]: g["zh"] for g in ssot["groups"]}}


def _summ(c: dict) -> dict:
    elig = c["n"] - c["exempt"]
    return {"n": c["n"], "have": c["have"], "ast": c["ast"], "exempt": c["exempt"], "elig": elig,
            "pct": round(c["have"] * 100 / max(elig, 1), 1), "miss": sorted(c["miss"]),
            "disagree": sorted(c["disagree"]), "perr": sorted(c.get("perr", [])), "ex": {k: sorted(v) for k, v in sorted(c["ex"].items())}}


def _row(side, title, grp, c, ssot):
    s = _summ(c)
    lamp = "RED" if s["miss"] else ("AMBER" if s["disagree"] or s["perr"] else "GREEN")
    return {"side": side, "title": title, "group": grp, "lamp": lamp, **s}


def compare(cur: dict, base: dict | None) -> dict:
    if not base or "totals" not in base:
        return {}
    out = {}
    for side, _ in SIDES:
        b, c = base["totals"].get(side), cur["totals"].get(side)
        if b and c:
            out[side] = {"pct": [b["pct"], c["pct"]], "miss": [len(b["miss"]), len(c["miss"])],
                         "have": [b["have"], c["have"]], "ast": [b["ast"], c["ast"]]}
    if base.get("use"):
        out["use"] = {"pct": [base["use"]["pct"], cur["use"]["pct"]], "use": [base["use"]["use"], cur["use"]["use"]]}
    return out


# ── HTML U/I 矩陣報告 ────────────────────────────────────────────────────
_CSS = """
:root{--bg:#f7f7f5;--fg:#1d1d1f;--mut:#6b6b70;--card:#fff;--line:#deded9;--g:#1e8e3e;--y:#b26a00;--r:#c5221f;--gb:#e6f4ea;--yb:#fef3e0;--rb:#fce8e6}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#151517;--fg:#ececee;--mut:#9a9aa2;--card:#1f1f22;--line:#333338;--g:#5bd47a;--y:#f0b552;--r:#ff7a70;--gb:#17301f;--yb:#33280f;--rb:#3a1a18}}
:root[data-theme="dark"]{--bg:#151517;--fg:#ececee;--mut:#9a9aa2;--card:#1f1f22;--line:#333338;--g:#5bd47a;--y:#f0b552;--r:#ff7a70;--gb:#17301f;--yb:#33280f;--rb:#3a1a18}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.5 system-ui,-apple-system,"Noto Sans TC","Microsoft JhengHei",sans-serif}
main{max-width:1180px;margin:0 auto;padding:20px 16px 48px}h1{font-size:20px;margin:0 0 4px}h2{font-size:16px;margin:24px 0 8px}
.mut{color:var(--mut)}.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px;margin:14px 0}
.k{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px 12px}.k b{font-size:22px;display:block}
.wrap{overflow-x:auto;background:var(--card);border:1px solid var(--line);border-radius:10px}
table{border-collapse:collapse;width:100%;min-width:720px}th,td{padding:6px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{font-weight:600;color:var(--mut);font-size:12px}td.n{text-align:right;font-variant-numeric:tabular-nums}
.l{display:inline-block;min-width:58px;text-align:center;border-radius:6px;padding:1px 6px;font-weight:600;font-size:12px}
.GREEN{color:var(--g);background:var(--gb)}.AMBER{color:var(--y);background:var(--yb)}.RED{color:var(--r);background:var(--rb)}.NODATA{color:var(--mut)}
details{margin:6px 0;background:var(--card);border:1px solid var(--line);border-radius:8px;padding:6px 10px}summary{cursor:pointer}
code{font-size:12px;word-break:break-all}ul{margin:6px 0;padding-left:20px}
"""


def render_html(rep: dict, delta: dict | None = None) -> str:
    e = html.escape
    delta = delta or {}

    def lamp(x):
        return f'<span class="l {e(x)}">{e(x)}</span>'

    kp = []
    for side, title in SIDES:
        t = rep["totals"][side]
        d = delta.get(side)
        was = f'<span class="mut">前次 {d["pct"][0]}% · 缺 {d["miss"][0]} →</span> ' if d else ""
        kp.append(f'<div class="k">{e(title)}<b>{t["pct"]}%</b>{was}有 {t["have"]}/{t["elig"]} · 缺 {len(t["miss"])}'
                  f' · AST 真 {t["ast"]} · 豁免 {t["exempt"]}</div>')
    u, du = rep["use"], delta.get("use")
    kp.append(f'<div class="k">⑤ 真用加速 API(AST)<b>{u["pct"]}%</b>'
              + (f'<span class="mut">前次 {du["pct"][0]}% →</span> ' if du else "")
              + f'掛橋 {u["bridged"]} 支中真呼叫 {u["use"]} 支(掛橋 ≠ 加速)</div>')
    body = []
    for side, title in SIDES:
        rs = [r for r in rep["rows"] if r["side"] == side]
        trs = "".join(
            f'<tr><td>{lamp(r["lamp"])}</td><td>{e(rep["groups"].get(r["group"], r["group"]))}</td>'
            f'<td class="n">{r["n"]}</td><td class="n">{r["have"]}</td><td class="n">{r["ast"]}</td>'
            f'<td class="n">{r["exempt"]}</td><td class="n">{len(r["miss"])}</td><td class="n">{len(r["disagree"])}</td>'
            f'<td class="n">{len(r["perr"])}</td>'
            f'<td class="n">{r["pct"]}%</td></tr>' for r in rs)
        t = rep["totals"][side]
        det = ""
        for label, items in (("缺件(可補)", t["miss"]), ("兩法不一致(標記在、AST / 剖析器讀不到)", t["disagree"]),
                             ("剖析錯誤(既有;檔案本身語法錯,不是橋的問題)", t["perr"])):
            if items:
                det += (f'<details open><summary>{e(label)} {len(items)}</summary><ul>'
                        + "".join(f"<li><code>{e(x)}</code></li>" for x in items[:200]) + "</ul></details>")
        for why, items in t["ex"].items():
            det += (f'<details><summary>豁免 {len(items)} · {e(why)}</summary><ul>'
                    + "".join(f"<li><code>{e(x)}</code></li>" for x in items[:200]) + "</ul></details>")
        body.append(f'<h2>{e(title)}</h2><div class="wrap"><table><thead><tr><th>燈</th><th>組</th><th>件</th><th>有標記(正主)</th>'
                    f'<th>AST/剖析器真</th><th>豁免</th><th>缺</th><th>不一致</th><th>剖析錯</th><th>覆蓋</th></tr></thead>'
                    f'<tbody>{trs}</tbody></table></div>{det}')
    r = rep["rulers"]
    return (f'<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>工具覆蓋矩陣</title><style>{_CSS}</style></head><body><main>'
            f'<h1>VIA 工具覆蓋矩陣 {lamp(rep["verdict"])}</h1>'
            f'<div class="mut">{e(rep["engine"])} · {e(rep["ts_utc"])} · 冊 {e(rep["ssot"])} · 正主 PY {e(r["py"])} / PS {e(r["ps"])}'
            f' · 活樹 {e(r["live"])} · PS 讀法 {e(r["ps_reader"])} · 非活樹 PY {rep["nonlive_py"]} · PS 版史 {rep["ps_history"]}(不計)</div>'
            f'<div class="kpis">{"".join(kp)}</div>{"".join(body)}'
            f'<p class="mut">燈:RED = 有非豁免缺件 · AMBER = 正主說有、第二讀法讀不到 · GREEN = 全有且一致。只讀 · 零網路 · 不安裝。</p>'
            f'</main></body></html>')


def write_matrix(rep: dict, out: Path = OUT, baseline: Path | None = None) -> dict:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    jp, hp = out / "COVERAGE_MATRIX_latest.json", out / "COVERAGE_MATRIX_latest.html"
    base = None
    src = Path(baseline) if baseline else jp
    if src.is_file():
        try:
            base = json.loads(src.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            base = None
    delta = compare(rep, base)
    rep = dict(rep, delta=delta, baseline=(str(src) if base else None))
    jp.write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    hp.write_text(render_html(rep, delta), encoding="utf-8")
    return {"json": str(jp), "html": str(hp), "delta": delta}


def _print(rep: dict) -> None:
    print(f"=== {ENGINE_TAG} · 工具覆蓋矩陣 · {rep['verdict']} ===")
    print(f"  正主 PY {rep['rulers']['py']} · PS {rep['rulers']['ps']} · {rep['rulers']['live']} · PS 讀法 {rep['rulers']['ps_reader']}")
    for side, title in SIDES:
        t = rep["totals"][side]
        lamp = "RED" if t["miss"] else ("AMBER" if t["disagree"] or t["perr"] else "GREEN")
        print(f"  [{lamp:<5}] {title:<22} 件 {t['n']:>5} · 有 {t['have']:>5}/{t['elig']:<5} {t['pct']:>5}% · AST真 {t['ast']:>5}"
              f" · 豁免 {t['exempt']:>4} · 缺 {len(t['miss'])} · 不一致 {len(t['disagree'])} · 剖析錯 {len(t['perr'])}")
        for x in t["miss"][:10]:
            print(f"      缺 {x}")
        for x in t["disagree"][:10]:
            print(f"      不一致 {x}")
        for x in t["perr"][:10]:
            print(f"      剖析錯(既有) {x}")
    u = rep["use"]
    print(f"  [INFO ] ⑤ 真用加速 API(AST) 掛橋 {u['bridged']} · 真呼叫 {u['use']}({u['pct']}%;掛橋 ≠ 加速)")


# ── 自測 ─────────────────────────────────────────────────────────────────
def selftest() -> int:
    rc = _PRIOR.selftest()
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' · ' + note) if note else ''}")

    ssot, ssot_name = load_ssot()
    sw, _ = _tail_module(HERE, "via_bridge_sweeper_v*.py", "_mdl230_sweeper_st")
    bridged = sw.ACCEL_BRIDGE + "\nx = VIA_ACCEL.accel_map if VIA_ACCEL else None\n"
    chk("⑮ AST:模組層 try 內 import VIA_SuperAccel_Module = 真橋;真用 VIA_ACCEL.* 讀得到",
        py_ast(bridged, ssot)["accel"] and py_ast(bridged, ssot)["use"])
    fake = '"""說明裡寫了 [VIA:ACCEL-BRIDGE 但沒有程式碼"""\nimport os\n'
    chk("⑯ 負控:標記只在字串裡 → AST 讀不到真橋", not py_ast(fake, ssot)["accel"] and sw.ACCEL_MARK in fake)
    inner = "def f():\n    import requests\n    return requests\n"
    chk("⑰ AST 觸網:函式內 import requests 也算(regex 只看行首,AST 看得到)",
        py_ast(inner, ssot)["need"] and not py_ast("import json\n", ssot)["need"])
    chk("⑱ AST 網路橋:VIA_NET_TOOL_PATH + def _via_net 才算真", py_ast(sw.NET_BRIDGE, ssot)["net"]
        and not py_ast("VIA_NET_TOOL_PATH = None\n", ssot)["net"])
    chk("⑲ 分組:VIA_HTML_UI / *Matrix* / *Report* 歸 HTML·U/I·MATRIX·REPORT;VDF 歸 VDF",
        group_of("VIA_HTML_UI/ci/x.py", ssot) == "UI" and group_of("supportive modules/registry/CGC_MDL093_GovernanceMatrix_v0100.py", ssot) == "UI"
        and group_of("functional modules/VDF/engine/VDF_ENG001_X_v0100.py", ssot) == "VDF")
    ex = exempt_of("supportive modules/intake/pkg/a.py", "py_accel", ssot)
    chk("⑳ 豁免附理由與改由誰驗;非豁免夾不豁免", bool(ex and ex["why"] and ex["verified_by"])
        and exempt_of("functional modules/VRN/VRN_ENG394_LayoutRestore_v0101.py", "py_accel", ssot) is None)
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "functional modules" / "VDF").mkdir(parents=True)
        (root / "functional modules" / "VDF" / "VDF_ENG001_A_v0100.py").write_text(sw.ACCEL_BRIDGE + sw.NET_BRIDGE + "import urllib.request\n", encoding="utf-8")
        (root / "functional modules" / "VDF" / "VDF_ENG002_B_v0100.py").write_text(sw.ACCEL_BRIDGE + "x = 1\n", encoding="utf-8")
        (root / "supportive modules").mkdir()
        (root / "supportive modules" / "fake_mark.py").write_text("# [VIA:ACCEL-BRIDGE (註解冒充)\n", encoding="utf-8")
        (root / "supportive modules" / "url_only.py").write_text(
            sw.ACCEL_BRIDGE + "# ===== [VIA:NET-BRIDGE:NOTE] 只剖析 URL =====\nfrom urllib.parse import urlparse\n", encoding="utf-8")
        (root / "Run-X-v0100.ps1").write_text("Write-Host old\n", encoding="utf-8")
        (root / "Run-X-v0101.ps1").write_text("Write-Host new\n", encoding="utf-8")
        rep = matrix(root, ssot=ssot, no_pwsh=True)
        t = rep["totals"]
        chk("㉑ 沙盒:VDF 沒網路橋的那支列缺;有橋且 AST 真的不列",
            t["vdf_net"]["miss"] == ["functional modules/VDF/VDF_ENG002_B_v0100.py"] and t["vdf_net"]["have"] == 1)
        chk("㉒ 沙盒:註解冒充標記 → 兩法不一致(AMBER)不算覆蓋", t["py_accel"]["disagree"] == ["supportive modules/fake_mark.py"])
        chk("㉓ 沙盒:PS 只算尾版(v0101 列缺,v0100 進版史)",
            t["ps_accel"]["miss"] == ["Run-X-v0101.ps1"] and rep["ps_history"] == 1 and rep["verdict"] == "RED")
        chk("㉓b 沙盒:只用 urllib.parse 且寫了 NET-BRIDGE:NOTE → 具名豁免,不列缺",
            "supportive modules/url_only.py" not in t["py_net"]["miss"] and t["py_net"]["exempt"] == 1
            and not py_ast("from urllib.parse import urlparse\n", ssot)["need"] and py_ast("from urllib import request\n", ssot)["need"])
        w = write_matrix(rep, out=root / "out")
        page = Path(w["html"]).read_text(encoding="utf-8")
        chk("㉔ HTML 矩陣報告:四面 + 真用面 · 燈 · 零外部資源", page.count("<table>") == 4 and "真用加速 API" in page
            and "http://" not in page and "https://" not in page and "<script" not in page)
        (root / "functional modules" / "VDF" / "VDF_ENG002_B_v0100.py").write_text(sw.ACCEL_BRIDGE + sw.NET_BRIDGE, encoding="utf-8")
        w2 = write_matrix(matrix(root, ssot=ssot, no_pwsh=True), out=root / "out")
        chk("㉕ 前次 → 本次:補橋後 VDF 網路覆蓋 50% → 100%", w2["delta"].get("vdf_net", {}).get("pct") == [50.0, 100.0])
    real = matrix()
    t = real["totals"]
    chk("㉖ 真樹:PY 加速器 · 觸網 PY · VDF 全件 · PS 尾版 四面非豁免缺件 0",
        all(not t[s]["miss"] for s, _ in SIDES),
        " · ".join(f"{s} {t[s]['have']}/{t[s]['elig']}" for s, _ in SIDES) + f" · PS 讀法 {real['rulers']['ps_reader']}")
    chk("㉗ 真樹:兩法一致(AST / 剖析器不一致 0)", all(not t[s]["disagree"] for s, _ in SIDES),
        " · ".join(f"{s} {len(t[s]['disagree'])}" for s, _ in SIDES))
    ok = rc == 0 and all(results)
    print(f"  [{ENGINE_TAG} 覆蓋矩陣 · AST · PS 剖析器] 自測 {sum(results)}/{len(results)} {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a:
        return selftest()
    if not a or a[0] != "matrix":
        return _PRIOR.main(a)
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc(PSGATE-1:先從 VCGC 跑過流程)"}, ensure_ascii=False))
        return 2
    bl = Path(a[a.index("--baseline") + 1]) if "--baseline" in a and a.index("--baseline") + 1 < len(a) else None
    rep = matrix(no_pwsh="--no-pwsh" in a)
    if rep.get("verdict") == "NODATA":
        print(f"[ToolMatrix] NODATA · {rep['why']}")
        return 1
    w = write_matrix(rep, baseline=bl)
    if "--json" in a:
        print(json.dumps({"verdict": rep["verdict"], "totals": {k: {kk: (len(vv) if isinstance(vv, (list, dict)) else vv)
                                                                   for kk, vv in v.items()} for k, v in rep["totals"].items()},
                          "use": rep["use"], "delta": w["delta"]}, ensure_ascii=False, indent=1))
    else:
        _print(rep)
    for side, d in w["delta"].items():
        print(f"  [前次 → 本次] {side} 覆蓋 {d['pct'][0]}% → {d['pct'][1]}%" + (f" · 缺 {d['miss'][0]} → {d['miss'][1]}" if "miss" in d else ""))
    print(f"[ToolMatrix] 總判 {rep['verdict']} · HTML {w['html']} · JSON {w['json']}")
    return 0 if rep["verdict"] != "RED" else 1


if __name__ == "__main__":
    sys.exit(main())
