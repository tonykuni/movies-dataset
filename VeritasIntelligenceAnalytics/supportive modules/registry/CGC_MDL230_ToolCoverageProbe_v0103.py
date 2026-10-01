#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL230_ToolCoverageProbe v0103 — 覆蓋矩陣 + PS 模板章面 + PY AST 分類說明目錄 + 只增帳本 + 淺色緊湊自動跳出頁

v0102 → v0103(操作員 R38 2026-10-01:「以成功的部份編號註冊鎖定不動 專注VCGC VCGC-VDF VCGC-VRN 每個PY擋都要加入加速器
AST分類 說明 PS擋要加加速器模板 整個結果矩陣全部整則只增不減 不衝突 用VCGC 監控系統更完善化用他呈現自動跳出 淺色 字小一點
LAYOUT緊湊 自動最佳化HTML U/I」):

  ⑥ PS 加速器模板章面:章字由正主 CGC_MDL183 定(CELERITAS-TEMPLATE-JOIN),未還的理由原樣引用 VIA_CeleritasPolicy_PaidDebt 尾版
     not_paid(雜湊被登錄 / 凍結鎖在旁 / 正本 / 封存 …= 具名豁免,本支不另判);第二讀法 = pwsh Parser 頂層真的點源 PS7 模板。
     只有 VCGC / VDF / VRN 三組判燈(操作員「專注」),其餘組照實列數、標 INFO。
  ⑦ PY AST 分類與說明目錄(VCGC / VDF / VRN / UI):分類尺 = VIA_VRN_PluginHub_SSOT 尾版 ast_categories(L05 同一把尺);
     說明 = 模組 docstring 第一行,沒有就由 AST 推導並標「推導」—— 不寫進原檔(免得為補說明動上百支檔)。
  版號尾碼:v0136A 是 v0136 的後繼(排序 = 版號, 尾碼),舊的進版史不再被當尾版。
  只增帳本:matrix --ledger 每輪追加一行到 VIA_ToolCoverage_Ledger_v0100.jsonl(git merge=union,不衝突,不改舊行)。
  頁:淺色 · 12px · 緊湊;matrix --open 有桌面就自動跳出;JSON 也是 SYNCHRONIZER(CGC_MDL241)的來源 toolcov。
其餘(①–⑤、豁免、前次對照)照 v0102。只讀 · 零網路 · 不安裝(--ledger 只追加帳本一行)。

用法:
  python CGC_MDL230_ToolCoverageProbe_v0103.py matrix [--open] [--ledger] [--json] [--baseline <json>] [--no-pwsh]
  python CGC_MDL230_ToolCoverageProbe_v0103.py probe …(照 v0101)
  python CGC_MDL230_ToolCoverageProbe_v0103.py --selftest
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
import collections
import hashlib
import html
import importlib.util
import json
import os
import re
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
SIDES = tuple(_PRIOR.SIDES) + (("ps_tpl", "⑥ PS 加速器模板章(尾版)"),)
TPL_FILE = "VeritasCeleritas.PS7.ps1"


def __getattr__(name: str):
    """Every public name of the prior version stays reachable here."""
    return getattr(_PRIOR, name)


# ── 版號尾碼:v0136A 是 v0136 的後繼 ───────────────────────────────────────
def _ps_tails(root: Path, exclude: set, fam_rx: str) -> tuple:
    rx = re.compile(fam_rx)
    allps = []
    for r, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in exclude]
        allps += [Path(r) / f for f in files if f.endswith(".ps1")]

    def key(m):
        return int(m.group("v")), (m.groupdict().get("s") or "")

    best = {}
    for p in allps:
        m = rx.match(str(p.relative_to(root)).replace("\\", "/"))
        if m:
            best[m.group("fam")] = max(best.get(m.group("fam"), (-1, "")), key(m))
    tails, history = [], 0
    for p in allps:
        m = rx.match(str(p.relative_to(root)).replace("\\", "/"))
        if m and key(m) != best[m.group("fam")]:
            history += 1
        else:
            tails.append(p)
    return sorted(tails), history


_PRIOR._ps_tails = _ps_tails          # v0102 的 matrix 也照新排序認尾版


# ── 第二讀法:PS 剖析器(加讀模板章)──────────────────────────────────────
_PS_PROBE = r"""
param([string]$ListFile)
$L = [System.Management.Automation.Language.Parser]
$out = foreach ($f in (Get-Content -LiteralPath $ListFile -Encoding utf8)) {
  $t = $null; $e = $null; $real = $false; $tpl = $false; $lib = $true
  try {
    $a = $L::ParseFile($f, [ref]$t, [ref]$e)
    $blocks = @($a.BeginBlock, $a.ProcessBlock, $a.EndBlock) | Where-Object { $_ }
    foreach ($b in $blocks) {
      foreach ($s in $b.Statements) {
        $x = $s.Extent.Text
        if ($s -is [System.Management.Automation.Language.TryStatementAst] -and $x -match 'VIA_PS_Accel_Module\.ps1') {
          $dots = $s.FindAll({ param($n) $n -is [System.Management.Automation.Language.CommandAst] -and $n.InvocationOperator -eq 'Dot' }, $true)
          if (@($dots).Count -gt 0) { $real = $true }
        }
        $isAccel = ($s -is [System.Management.Automation.Language.TryStatementAst] -and $x -match 'VIA_PS_Accel_Module\.ps1')
        $isDecl = ($s -is [System.Management.Automation.Language.FunctionDefinitionAst]) -or ($s -is [System.Management.Automation.Language.AssignmentStatementAst]) -or
                  ($s -is [System.Management.Automation.Language.PipelineAst] -and $x -match '^\s*(Set-StrictMode|Set-Alias|Export-ModuleMember)\b')
        if (-not $isDecl -and -not $isAccel) { $lib = $false }
        if ($x -match 'VeritasCeleritas\.PS7\.ps1') {
          $dots = $s.FindAll({ param($n) $n -is [System.Management.Automation.Language.CommandAst] -and $n.InvocationOperator -eq 'Dot' }, $true)
          if (@($dots).Count -gt 0) { $tpl = $true }
        }
      }
    }
    if ($lib -and ((Get-Content -LiteralPath $f -Raw) -match 'PS-TEMPLATE:v\d+-lib\]')) { $tpl = $true }
    [pscustomobject]@{ f = $f; err = @($e).Count; real = $real; tpl = $tpl }
  } catch { [pscustomobject]@{ f = $f; err = -1; real = $false; tpl = $false } }
}
@($out) | ConvertTo-Json -Compress -AsArray
"""
_PARSED: dict = {}


def ps_parse(files: list, no_pwsh: bool = False) -> tuple:
    """{abs path: {err, real, tpl}} via one pwsh Parser call (cached for the ⑥ side); ({}, why) when absent."""
    exe = None if no_pwsh else _PRIOR._pwsh()
    if not exe or not files:
        _PARSED.clear()
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
            _PARSED.clear()
            return {}, f"pwsh 剖析失敗 {type(exc).__name__}(文字判讀)"
    res = {str(Path(r["f"])): {"err": r["err"], "real": bool(r["real"]), "tpl": bool(r.get("tpl"))} for r in rows}
    _PARSED.clear()
    _PARSED.update(res)
    return res, f"pwsh Parser({Path(exe).name})"


_PRIOR.ps_parse = ps_parse


# ── ⑥ PS 模板章面 ────────────────────────────────────────────────────────
def paid_debt(folder: Path = HERE) -> tuple:
    """Owner's not-paid reasons {rel: reason} from the newest PaidDebt book (quoted as-is)."""
    hits = sorted(folder.glob("VIA_CeleritasPolicy_PaidDebt_v*.json"), key=lambda p: (_vnum(p), p.name))
    if not hits:
        return {}, "(PaidDebt 不在)"
    d = json.loads(hits[-1].read_text(encoding="utf-8"))
    out = {}
    for why, files in ((d.get("not_paid") or {}).get("by_reason") or {}).items():
        for f in files:
            out[f] = why
    return out, hits[-1].name


def ps_tpl_side(root: Path, ssot: dict, tails: list, no_pwsh: bool = False, debt: dict | None = None) -> dict:
    spec = ssot["ps_tpl"]
    mark = ssot["ast"]["ps_tpl_mark"].encode()
    focus = set(spec["lamp_groups"])
    if debt is None:
        debt, _ = paid_debt()
    if not _PARSED and not no_pwsh:
        ps_parse(tails)
    cells, info = {}, collections.Counter()
    for p in tails:
        rel = str(p.relative_to(root)).replace("\\", "/")
        grp = _PRIOR.group_of(rel, ssot)
        c = cells.setdefault(grp, _PRIOR._blank())
        c["n"] += 1
        data = p.read_bytes()
        have = mark in data
        pr = _PARSED.get(str(p))
        real = (pr["tpl"] and pr["err"] == 0) if pr else (have and (TPL_FILE.encode() in data or re.search(rb"PS-TEMPLATE:v\d+-lib\]", data) is not None))
        why = None
        e = _PRIOR.exempt_of(rel, "ps_accel", ssot)
        if e:
            why = f"{e['id']} · {e['why']} · 改由:{e['verified_by']}"
        for x in spec["exempt_rx"]:
            if not why and re.search(x["rx"], "/" + rel):
                why = f"{x['id']} · {x['why']} · 改由:{x['verified_by']}"
        if not why and rel in debt:
            why = f"PaidDebt 未還:{debt[rel]}(正主原樣)"
        if why and not (have and real):
            c["exempt"] += 1
            c["ex"].setdefault(why, []).append(rel)
            continue
        c["have"] += bool(have)
        c["ast"] += bool(real)
        if not have:
            c["miss"].append(rel)
        elif pr and pr["err"] != 0:
            c["perr"].append(rel)
        elif not real:
            c["disagree"].append(rel)
    order = [g["id"] for g in ssot["groups"]]
    rows, tot = [], _PRIOR._blank()
    for grp in order:
        c = cells.get(grp)
        if not c:
            continue
        r = _PRIOR._row("ps_tpl", dict(SIDES)["ps_tpl"], grp, c, ssot)
        if grp not in focus:
            r["lamp"] = "INFO"
            info["n"] += c["n"]
            info["miss"] += len(c["miss"])
        else:
            for k in ("n", "have", "ast", "exempt"):
                tot[k] += c[k]
            for k in ("miss", "disagree", "perr"):
                tot[k] += c[k]
            for k, v in c["ex"].items():
                tot["ex"].setdefault(k, []).extend(v)
        rows.append(r)
    return {"rows": rows, "total": _PRIOR._summ(tot), "out_of_scope": dict(info)}


# ── ⑦ PY AST 分類與說明目錄 ──────────────────────────────────────────────
def categories(folder: Path = HERE) -> list:
    hits = sorted(folder.glob("VIA_VRN_PluginHub_SSOT_v*.json"), key=lambda p: (_vnum(p), p.name))
    if not hits:
        return [{"cat": "工具", "rx": "."}]
    return json.loads(hits[-1].read_text(encoding="utf-8"))["ast_categories"]


def classify_names(names: list, cats: list) -> collections.Counter:
    c = collections.Counter()
    for n in names:
        for x in cats:
            if re.search(x["rx"], n, re.I):
                c[x["cat"]] += 1
                break
    return c


def describe(text: str, cats: list) -> dict:
    """One file: AST category counts, primary category, description (docstring, else derived and marked)."""
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError):
        return {"parse": False, "primary": "—", "cats": {}, "n_fn": 0, "n_cls": 0, "desc": "(剖析不過)", "derived": True}
    fns = [n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    cls = [n.name for n in tree.body if isinstance(n, ast.ClassDef)]
    cnt = classify_names(fns + cls, cats)
    named = [(k, v) for k, v in cnt.most_common() if k != "工具"]
    primary = named[0][0] if named else ("工具" if cnt else "設定 / 資料")
    doc = ast.get_docstring(tree)
    if doc and doc.strip():
        return {"parse": True, "primary": primary, "cats": dict(cnt), "n_fn": len(fns), "n_cls": len(cls),
                "desc": doc.strip().splitlines()[0][:160], "derived": False}
    lead = ""
    for ln in text.splitlines()[:12]:
        s = ln.strip()
        if s.startswith("#") and not s.startswith("#!") and "coding" not in s and "[VIA:" not in s and len(s) > 3:
            lead = s.lstrip("# ").strip()
            break
    top = [n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))][:4]
    desc = lead or (f"{primary}:" + "、".join(top) if top else f"{primary}(無頂層定義)")
    return {"parse": True, "primary": primary, "cats": dict(cnt), "n_fn": len(fns), "n_cls": len(cls),
            "desc": "推導 · " + desc[:150], "derived": True}


def catalog(root: Path, ssot: dict, live: set | None, sw) -> dict:
    cats = categories()
    groups = set(ssot["catalog"]["groups"])
    rows, by = [], collections.defaultdict(lambda: {"n": 0, "doc": 0, "cats": collections.Counter()})
    for p in sorted(root.rglob("*.py")):
        rel = str(p.relative_to(root)).replace("\\", "/")
        if sw.classify(rel) == "SKIP" or (live is not None and str(p) not in live):
            continue
        grp = _PRIOR.group_of(rel, ssot)
        if grp not in groups:
            continue
        try:
            d = describe(p.read_text(encoding="utf-8", errors="ignore"), cats)
        except OSError:
            continue
        rows.append({"file": rel, "group": grp, **d})
        b = by[grp]
        b["n"] += 1
        b["doc"] += not d["derived"]
        b["cats"][d["primary"]] += 1
    summary = {g: {"n": v["n"], "doc": v["doc"], "doc_pct": round(v["doc"] * 100 / max(v["n"], 1), 1),
                   "cats": dict(v["cats"].most_common())} for g, v in by.items()}
    return {"rows": rows, "summary": summary, "n": len(rows), "doc": sum(v["doc"] for v in by.values())}


# ── 合併 ─────────────────────────────────────────────────────────────────
def matrix(root: Path = VIA, ssot: dict | None = None, no_pwsh: bool = False) -> dict:
    root = Path(root)
    ssot_name = "(呼叫端給)"
    if ssot is None:
        ssot, ssot_name = _PRIOR.load_ssot()
    _PARSED.clear()
    rep = _PRIOR.matrix(root, ssot=ssot, no_pwsh=no_pwsh)
    if rep.get("verdict") == "NODATA":
        return rep
    rep["ssot"] = ssot_name
    m117, _ = _PRIOR._tail_module(HERE, "CGC_MDL117_AccelCoverage_v*.py", "_mdl230_mdl117_v3")
    sw, _ = _PRIOR._tail_module(HERE, "via_bridge_sweeper_v*.py", "_mdl230_sweeper_v3")
    tails, _ = _ps_tails(root, set(m117.EXCLUDE_DIRS), ssot["ast"]["ps_family_rx"])
    debt, debt_name = paid_debt() if root.resolve() == VIA.resolve() else ({}, "(沙盒)")
    side = ps_tpl_side(root, ssot, tails, no_pwsh=no_pwsh, debt=debt)
    rep["rows"] += side["rows"]
    rep["totals"]["ps_tpl"] = side["total"]
    rep["ps_tpl_out_of_scope"] = side["out_of_scope"]
    rep["rulers"]["ps_tpl"] = f"CGC_MDL183 章字 · {debt_name}"
    live, _ = sw._live_set(root)
    rep["catalog"] = catalog(root, ssot, live, sw)
    t = rep["totals"]
    rep["verdict"] = "RED" if any(v["miss"] for v in t.values()) else (
        "AMBER" if any(v["disagree"] or v.get("perr") for v in t.values()) else "GREEN")
    rep["engine"] = ENGINE_TAG
    return rep


# ── 只增帳本 ─────────────────────────────────────────────────────────────
def ledger_line(rep: dict) -> dict:
    tot = {s: {"pct": v["pct"], "have": v["have"], "elig": v["elig"], "miss": len(v["miss"]),
               "disagree": len(v["disagree"]), "perr": len(v.get("perr", []))} for s, v in rep["totals"].items()}
    body = json.dumps(tot, ensure_ascii=False, sort_keys=True)
    return {"ts_utc": rep["ts_utc"], "engine": rep["engine"], "verdict": rep["verdict"], "totals": tot,
            "use_pct": rep["use"]["pct"], "doc": [rep["catalog"]["doc"], rep["catalog"]["n"]],
            "sha12": hashlib.sha256(body.encode()).hexdigest()[:12]}


def ledger_append(rep: dict, path: Path | None = None) -> Path:
    ssot, _ = _PRIOR.load_ssot()
    path = Path(path) if path else VIA / ssot["ledger"]["path"]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(ledger_line(rep), ensure_ascii=False, sort_keys=True) + "\n")
    return path


def ledger_tail(path: Path | None = None, n: int = 8) -> list:
    ssot, _ = _PRIOR.load_ssot()
    path = Path(path) if path else VIA / ssot["ledger"]["path"]
    if not path.is_file():
        return []
    out = []
    for ln in path.read_text(encoding="utf-8").splitlines()[-n:]:
        try:
            out.append(json.loads(ln))
        except json.JSONDecodeError:
            continue
    return out


# ── 頁:淺色 · 12px · 緊湊 ───────────────────────────────────────────────
_CSS = """
:root{--bg:#f6f7f9;--fg:#1f2328;--mut:#656d76;--card:#fff;--line:#e3e6ea;--g:#1a7f37;--y:#9a6700;--r:#cf222e;--gb:#dafbe1;--yb:#fff8c5;--rb:#ffebe9;--ib:#eef1f4}
*{box-sizing:border-box}html{color-scheme:light}body{margin:0;background:var(--bg);color:var(--fg);font:12px/1.4 system-ui,-apple-system,"Noto Sans TC","Microsoft JhengHei",sans-serif}
main{max-width:1240px;margin:0 auto;padding:10px 12px 28px}h1{font-size:15px;margin:0 0 2px}h2{font-size:13px;margin:12px 0 4px}
.mut{color:var(--mut);font-size:11px}.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:6px;margin:8px 0}
.k{background:var(--card);border:1px solid var(--line);border-radius:6px;padding:5px 8px;font-size:11px}.k b{font-size:15px;display:block}
.wrap{overflow-x:auto;background:var(--card);border:1px solid var(--line);border-radius:6px}
table{border-collapse:collapse;width:100%;min-width:640px}th,td{padding:2px 6px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{font-weight:600;color:var(--mut);font-size:11px;position:sticky;top:0;background:var(--card)}td.n{text-align:right;font-variant-numeric:tabular-nums}
.l{display:inline-block;min-width:44px;text-align:center;border-radius:4px;padding:0 4px;font-weight:600;font-size:10px}
.GREEN{color:var(--g);background:var(--gb)}.AMBER{color:var(--y);background:var(--yb)}.RED{color:var(--r);background:var(--rb)}.INFO,.NODATA{color:var(--mut);background:var(--ib)}
details{margin:3px 0;background:var(--card);border:1px solid var(--line);border-radius:5px;padding:2px 8px}summary{cursor:pointer;font-size:11px}
code{font-size:11px;word-break:break-all}ul{margin:2px 0;padding-left:16px}.d{color:var(--mut)}.scroll{max-height:420px;overflow:auto}
"""


def render_html(rep: dict, delta: dict | None = None, ledger: list | None = None) -> str:
    e = html.escape
    delta = delta or {}

    def lamp(x):
        return f'<span class="l {e(x)}">{e(x)}</span>'

    kp = []
    for side, title in SIDES:
        t = rep["totals"][side]
        d = delta.get(side)
        was = f'<span class="mut">前 {d["pct"][0]}% · 缺 {d["miss"][0]} →</span> ' if d else ""
        kp.append(f'<div class="k">{e(title)}<b>{t["pct"]}%</b>{was}有 {t["have"]}/{t["elig"]} · 缺 {len(t["miss"])} · 真 {t["ast"]} · 豁免 {t["exempt"]}</div>')
    u, cg = rep["use"], rep["catalog"]
    kp.append(f'<div class="k">⑤ 真用加速 API<b>{u["pct"]}%</b>掛橋 {u["bridged"]} · 真呼叫 {u["use"]}(掛橋 ≠ 加速)</div>')
    kp.append(f'<div class="k">⑦ PY 說明(原檔 docstring)<b>{round(cg["doc"] * 100 / max(cg["n"], 1), 1)}%</b>{cg["doc"]}/{cg["n"]} · 其餘由 AST 推導</div>')
    body = []
    for side, title in SIDES:
        rs = [r for r in rep["rows"] if r["side"] == side]
        trs = "".join(
            f'<tr><td>{lamp(r["lamp"])}</td><td>{e(rep["groups"].get(r["group"], r["group"]))}</td><td class="n">{r["n"]}</td>'
            f'<td class="n">{r["have"]}</td><td class="n">{r["ast"]}</td><td class="n">{r["exempt"]}</td><td class="n">{len(r["miss"])}</td>'
            f'<td class="n">{len(r["disagree"])}</td><td class="n">{len(r.get("perr", []))}</td><td class="n">{r["pct"]}%</td></tr>' for r in rs)
        t = rep["totals"][side]
        det = ""
        for label, items in (("缺件(可補)", t["miss"]), ("兩法不一致", t["disagree"]), ("剖析錯誤(既有)", t.get("perr", []))):
            if items:
                det += (f'<details open><summary>{e(label)} {len(items)}</summary><ul>'
                        + "".join(f"<li><code>{e(x)}</code></li>" for x in items[:200]) + "</ul></details>")
        for why, items in t["ex"].items():
            det += (f'<details><summary>豁免 {len(items)} · {e(why)}</summary><ul>'
                    + "".join(f"<li><code>{e(x)}</code></li>" for x in items[:200]) + "</ul></details>")
        if side == "ps_tpl" and rep.get("ps_tpl_out_of_scope"):
            o = rep["ps_tpl_out_of_scope"]
            det += f'<p class="mut">範圍外(INFO,不判燈):{o.get("n", 0)} 支 · 未接章 {o.get("miss", 0)}</p>'
        body.append(f'<h2>{e(title)}</h2><div class="wrap"><table><thead><tr><th>燈</th><th>組</th><th>件</th><th>有(正主)</th>'
                    f'<th>真(第二讀法)</th><th>豁免</th><th>缺</th><th>不一致</th><th>剖析錯</th><th>覆蓋</th></tr></thead>'
                    f'<tbody>{trs}</tbody></table></div>{det}')
    srows = "".join(
        f'<tr><td>{e(rep["groups"].get(g, g))}</td><td class="n">{v["n"]}</td><td class="n">{v["doc"]}</td><td class="n">{v["doc_pct"]}%</td>'
        f'<td>{e(" · ".join(f"{k} {n}" for k, n in list(v["cats"].items())[:6]))}</td></tr>' for g, v in cg["summary"].items())
    crow = "".join(
        f'<tr><td><code>{e(r["file"])}</code></td><td>{e(r["group"])}</td><td>{e(r["primary"])}</td><td class="n">{r["n_fn"]}</td>'
        f'<td class="{"d" if r["derived"] else ""}">{e(r["desc"])}</td></tr>' for r in cg["rows"])
    body.append(f'<h2>⑦ PY AST 分類與說明目錄</h2><div class="wrap"><table><thead><tr><th>組</th><th>件</th><th>原檔說明</th>'
                f'<th>說明率</th><th>主分類分佈</th></tr></thead><tbody>{srows}</tbody></table></div>'
                f'<details><summary>逐檔 {cg["n"]} 支(灰字 = AST 推導,非原檔說明)</summary><div class="wrap scroll"><table><thead><tr>'
                f'<th>檔</th><th>組</th><th>主分類</th><th>函式</th><th>說明</th></tr></thead><tbody>{crow}</tbody></table></div></details>')
    if ledger:
        lrow = "".join(
            f'<tr><td>{e(x.get("ts_utc", ""))}</td><td>{lamp(x.get("verdict", "NODATA"))}</td>'
            + "".join(f'<td class="n">{(x.get("totals", {}).get(s) or {}).get("pct", "—")}%</td>' for s, _ in SIDES)
            + f'<td><code>{e(x.get("sha12", ""))}</code></td></tr>' for x in reversed(ledger))
        body.append(f'<h2>只增帳本(最近 {len(ledger)} 輪)</h2><div class="wrap"><table><thead><tr><th>UTC</th><th>燈</th>'
                    + "".join(f"<th>{e(t.split(' ')[0])}</th>" for _, t in SIDES) + f'<th>sha12</th></tr></thead><tbody>{lrow}</tbody></table></div>')
    r = rep["rulers"]
    return (f'<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>工具覆蓋矩陣</title><style>{_CSS}</style></head><body><main>'
            f'<h1>VIA 工具覆蓋矩陣 {lamp(rep["verdict"])}</h1>'
            f'<div class="mut">{e(rep["engine"])} · {e(rep["ts_utc"])} · 冊 {e(rep["ssot"])} · 正主 PY {e(r["py"])} / PS {e(r["ps"])} / 模板章 {e(r.get("ps_tpl", ""))}'
            f' · PS 讀法 {e(r["ps_reader"])} · 非活樹 PY {rep["nonlive_py"]} · PS 版史 {rep["ps_history"]}(不計)</div>'
            f'<div class="kpis">{"".join(kp)}</div>{"".join(body)}'
            f'<p class="mut">燈:RED = 有非豁免缺件 · AMBER = 正主說有、第二讀法讀不到或剖析錯 · GREEN = 全有且一致 · INFO = 範圍外不判。只讀 · 零網路 · 不安裝。</p>'
            f'</main></body></html>')


def write_matrix(rep: dict, out: Path = OUT, baseline: Path | None = None, ledger: list | None = None) -> dict:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    jp, hp, cp = out / "COVERAGE_MATRIX_latest.json", out / "COVERAGE_MATRIX_latest.html", out / "AST_CATALOG_latest.json"
    base = None
    src = Path(baseline) if baseline else jp
    if src.is_file():
        try:
            base = json.loads(src.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            base = None
    delta = _PRIOR.compare(rep, base)
    for side in ("ps_tpl",):
        b, c = (base or {}).get("totals", {}).get(side), rep["totals"].get(side)
        if b and c:
            delta[side] = {"pct": [b["pct"], c["pct"]], "miss": [len(b["miss"]), len(c["miss"])]}
    cat = rep.get("catalog") or {}
    slim = dict(rep, catalog={k: v for k, v in cat.items() if k != "rows"}, delta=delta, baseline=(str(src) if base else None))
    jp.write_text(json.dumps(slim, ensure_ascii=False, indent=1), encoding="utf-8")
    cp.write_text(json.dumps(cat, ensure_ascii=False, indent=1), encoding="utf-8")
    hp.write_text(render_html(rep, delta, ledger), encoding="utf-8")
    return {"json": str(jp), "html": str(hp), "catalog": str(cp), "delta": delta}


def open_page(path: str) -> str:
    """Pop the page up when there is a desktop; say so honestly when there is none (container / CI)."""
    if os.environ.get("VIA_NO_OPEN") == "1":
        return "略過(VIA_NO_OPEN=1)"
    if sys.platform != "win32" and not os.environ.get("DISPLAY") and sys.platform != "darwin":
        return "略過(無桌面)"
    try:
        import webbrowser
        return "已開" if webbrowser.open(Path(path).resolve().as_uri()) else "略過(瀏覽器沒回應)"
    except Exception as exc:  # noqa: BLE001 — 開頁失敗不影響判讀,照實印
        return f"略過({type(exc).__name__})"


def _print(rep: dict) -> None:
    print(f"=== {ENGINE_TAG} · 工具覆蓋矩陣 · {rep['verdict']} ===")
    r = rep["rulers"]
    print(f"  正主 PY {r['py']} · PS {r['ps']} · 模板章 {r.get('ps_tpl', '')} · PS 讀法 {r['ps_reader']}")
    for side, title in SIDES:
        t = rep["totals"][side]
        lamp = "RED" if t["miss"] else ("AMBER" if t["disagree"] or t.get("perr") else "GREEN")
        print(f"  [{lamp:<5}] {title:<20} 件 {t['n']:>5} · 有 {t['have']:>5}/{t['elig']:<5} {t['pct']:>5}% · 真 {t['ast']:>5}"
              f" · 豁免 {t['exempt']:>4} · 缺 {len(t['miss'])} · 不一致 {len(t['disagree'])} · 剖析錯 {len(t.get('perr', []))}")
        for x in (t["miss"] + t["disagree"] + t.get("perr", []))[:10]:
            print(f"      {x}")
    o = rep.get("ps_tpl_out_of_scope") or {}
    print(f"  [INFO ] ⑥ 範圍外(不判燈)PS {o.get('n', 0)} 支 · 未接章 {o.get('miss', 0)}")
    u, c = rep["use"], rep["catalog"]
    print(f"  [INFO ] ⑤ 真用加速 API 掛橋 {u['bridged']} · 真呼叫 {u['use']}({u['pct']}%)")
    print(f"  [INFO ] ⑦ PY AST 目錄 {c['n']} 支 · 原檔說明 {c['doc']}({round(c['doc'] * 100 / max(c['n'], 1), 1)}%)· "
          + " · ".join(f"{g} {v['doc_pct']}%" for g, v in c["summary"].items()))


# ── 自測 ─────────────────────────────────────────────────────────────────
def selftest() -> int:
    rc = _PRIOR.selftest()
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' · ' + note) if note else ''}")

    ssot, _ = _PRIOR.load_ssot()
    sw, _ = _PRIOR._tail_module(HERE, "via_bridge_sweeper_v*.py", "_mdl230_sweeper_st3")
    tpl = ("# CELERITAS-TEMPLATE-JOIN v1\nif ($PSVersionTable.PSVersion.Major -ge 7) { try { $f = Join-Path $PSScriptRoot "
           "'supportive modules\\ps7\\VeritasCeleritas.PS7.ps1'; . $f -RestoreOnly } catch { } }\n")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "Run-A-v0136.ps1").write_text("Write-Host (\n", encoding="utf-8")
        (root / "Run-A-v0136A.ps1").write_text("Write-Host ok\n", encoding="utf-8")
        tails, hist = _ps_tails(root, set(), ssot["ast"]["ps_family_rx"])
        chk("㉘ 版號尾碼:v0136A 是 v0136 的後繼(舊的進版史)", [p.name for p in tails] == ["Run-A-v0136A.ps1"] and hist == 1)
        vrn = root / "functional modules" / "VRN"
        vrn.mkdir(parents=True)
        (vrn / "Run-B-v0100.ps1").write_text("Write-Host b\n", encoding="utf-8")
        (vrn / "Run-C-v0100.ps1").write_text(tpl + "Write-Host c\n", encoding="utf-8")
        (vrn / "Run-D_shaabcdef12.ps1").write_text("Write-Host d\n", encoding="utf-8")
        (root / "functional modules" / "VAP").mkdir(parents=True)
        (root / "functional modules" / "VAP" / "Run-E-v0100.ps1").write_text("Write-Host e\n", encoding="utf-8")
        _PARSED.clear()
        tails, _ = _ps_tails(root, set(), ssot["ast"]["ps_family_rx"])
        side = ps_tpl_side(root, ssot, tails, no_pwsh=True, debt={"functional modules/VRN/Run-X.ps1": "雜湊被登錄"})
        t = side["total"]
        chk("㉙ ⑥ 模板章:VRN 缺章列缺 · 有章列有 · _sha 快照副本豁免 · VAP 範圍外 INFO 不計",
            t["miss"] == ["functional modules/VRN/Run-B-v0100.ps1"] and t["have"] == 1 and t["exempt"] == 1
            and any(r["group"] == "VAP" and r["lamp"] == "INFO" and len(r["miss"]) == 1 for r in side["rows"])
            and "functional modules/VAP/Run-E-v0100.ps1" not in t["miss"])
        d1 = describe('"""Load the books."""\ndef load_x():\n    pass\ndef selftest():\n    pass\n', categories())
        d2 = describe("# 表格還原小工具\ndef merge_cells():\n    pass\n", categories())
        chk("㉚ ⑦ AST 分類 + 說明:有 docstring 用原文;沒有就推導並標「推導」",
            d1["desc"] == "Load the books." and not d1["derived"] and d1["primary"] in ("擷取", "自測")
            and d2["derived"] and d2["desc"].startswith("推導 · 表格還原") and d2["primary"] == "表格")
        rep = matrix(root, ssot=ssot, no_pwsh=True)
        led = root / "ledger.jsonl"
        ledger_append(rep, led)
        first = led.read_bytes()
        ledger_append(rep, led)
        chk("㉛ 只增帳本:追加不改舊行(第一行位元組不變 · 兩行)",
            led.read_bytes().startswith(first) and len(led.read_text(encoding="utf-8").splitlines()) == 2)
        w = write_matrix(rep, out=root / "out", ledger=ledger_tail(led))
        page = Path(w["html"]).read_text(encoding="utf-8")
        chk("㉜ 頁:淺色(無深色媒體查詢)· 12px · 緊湊 · 五面 + ⑦ 目錄 + 帳本 · 零外部資源",
            "prefers-color-scheme" not in page and "font:12px" in page and page.count("<table>") == 8
            and "http://" not in page and "https://" not in page and "<script" not in page)
        os.environ["VIA_NO_OPEN"] = "1"
        chk("㉝ 自動跳出:沒桌面 / 關掉時照實說略過,不報錯", open_page(w["html"]).startswith("略過"))
        os.environ.pop("VIA_NO_OPEN", None)
    sync = sorted(HERE.glob("VIA_UI_TemplateSync_SSOT_v*.json"), key=lambda p: (_vnum(p), p.name))[-1]
    src = [s for s in json.loads(sync.read_text(encoding="utf-8"))["sources"] if s["id"] == ssot["ui"]["sync_source_id"]]
    chk("㉞ SYNCHRONIZER 來源:TemplateSync 尾版接 toolcov → COVERAGE_MATRIX_latest.json",
        bool(src) and src[0]["path"].endswith("COVERAGE_MATRIX_latest.json"), sync.name)
    real = matrix()
    t = real["totals"]
    chk("㉟ 真樹:六面非豁免缺件 0(⑥ 只判 VCGC / VDF / VRN)", all(not t[s]["miss"] for s, _ in SIDES),
        " · ".join(f"{s} {t[s]['have']}/{t[s]['elig']}" for s, _ in SIDES))
    chk("㊱ 真樹:兩法一致 · 剖析錯 0", all(not t[s]["disagree"] and not t[s].get("perr") for s, _ in SIDES),
        f"PS 讀法 {real['rulers']['ps_reader']}")
    ok = rc == 0 and all(results)
    print(f"  [{ENGINE_TAG} 模板章 · AST 目錄 · 只增帳本 · 淺色頁] 自測 {sum(results)}/{len(results)} {'PASS' if ok else 'FAIL'}")
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
    if "--ledger" in a:
        lp = ledger_append(rep)
        print(f"  [帳本] 追加 1 行 → {lp.name}(只增)")
    w = write_matrix(rep, baseline=bl, ledger=ledger_tail())
    if "--json" in a:
        print(json.dumps({"verdict": rep["verdict"], "ledger": ledger_line(rep), "delta": w["delta"]}, ensure_ascii=False, indent=1))
    else:
        _print(rep)
    for side, d in w["delta"].items():
        print(f"  [前次 → 本次] {side} 覆蓋 {d['pct'][0]}% → {d['pct'][1]}%" + (f" · 缺 {d['miss'][0]} → {d['miss'][1]}" if "miss" in d else ""))
    if "--open" in a:
        print(f"  [頁] {open_page(w['html'])} · {w['html']}")
    print(f"[ToolMatrix] 總判 {rep['verdict']} · HTML {w['html']} · JSON {w['json']} · 目錄 {w['catalog']}")
    return 0 if rep["verdict"] != "RED" else 1


if __name__ == "__main__":
    sys.exit(main())
