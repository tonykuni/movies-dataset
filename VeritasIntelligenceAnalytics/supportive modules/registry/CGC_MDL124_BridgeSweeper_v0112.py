#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""CGC_MDL124_BridgeSweeper v0112 — 薄尾(v0111 一字不動):新動詞 `--effective`,加速器覆蓋以「生效」計

操作員 2026-11-25 21:05:「用一個 py 檔案導入加速器 100% 覆蓋並用 ps 檔啟動」(VCGC-REQ267)。
CLAUDE.md(REQ266)定的規則:標記不算數,要「語法樹看得到導入 + 執行時真的載到」。前版掃描器只看橋區塊字串,
本版在同一支掃描器上加一個動詞,一次量完、補完、出報告(凍結期規則:新需求掛既有引擎的新動詞,不另立引擎)。

  --effective [--apply] [--scope vcgc|all] [--no-html]
    PY 每支尾版(前版的排除規則照舊:凍結 · 唯讀 · 版史 · 具名豁免 · 未在冊 · 存證副本)分五態:
      EFFECTIVE   語法樹有 import VIA_SuperAccel_Module / VeritasCeleritas_v1141(或 SUP_MDL737 本體),
                  從檔案位置往上找得到那支模組,而且該模組在子行程實際 import 成功
      MARKER_ONLY 有 [VIA:ACCEL-BRIDGE] 標記,檔內卻沒有導入(假加速 = 黃)
      MISSING     標記與導入都沒有(紅)
      UNRESOLVED  有導入,但往上找不到模組,或模組 import 失敗(紅)
      AST_ERR     語法樹解析不過(紅;不注入)
    NET:只算真的出網的檔(前版 callers_only 判準),有沒有網路橋。
    PS :.ps1 尾版有沒有 PS-ACCEL 橋,往上找不找得到 VIA_PS_Accel_Module.ps1;有 pwsh 才實測點源,沒有照實標灰。
    --apply:只補 MISSING 與 MARKER_ONLY(PY ACCEL)與出網檔缺的 NET 橋;用前版 inject(注入前後都 py_compile,失敗原檔不動)。
      範圍預設 vcgc(不碰 functional modules/VDF · VRN · VAP · VQG,四系統互不干涉);--scope all 要操作員明說才帶。
      成功鎖帳本(VIA_SuccessLock_Ledger)點名的檔不動,標 LOCKED(黃:換版時帶橋)。.ps1 一律不改(改既有 .ps1 不在授權內)。
    輸出:VIA_Reports/vcgc/accel_cover/ACCEL_COVER_latest.{json,txt,html}(txt = ≤300 行貼回包,末行 NEXT:)。
    結束碼:0 綠 · 2 黃 · 1 紅。
其餘(--subsystems · --ps · --accel · --net · --selftest 前版十幾檢)照 v0111。零網路 · 零 TA-Lib · 不 import 他系統。
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
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import ast
import collections
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
STEM = "CGC_MDL124_BridgeSweeper"
VERSION = "v0112"


def _vnum_v0112(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum_v0112(p) < _vnum_v0112(__file__)), key=_vnum_v0112)
_spec = importlib.util.spec_from_file_location(STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
for _n, _v in vars(PRIOR).items():
    if not _n.startswith("__") and _n not in globals():
        globals()[_n] = _v

_BODY = PRIOR.scan.__globals__          # 本體全域:scan / inject / scan_ps 真正查的那一份(v0111 的 _excluded 已換裝在這裡)
ACCEPT = ("VIA_SuperAccel_Module", "VeritasCeleritas_v1141")
ACCEPT_RE = re.compile(r"^SUP_MDL737_SuperAccelModule_v\d+$")
MARK = "[VIA:ACCEL-BRIDGE"
SYS_OF = (("functional modules/VDF", "VDF"), ("functional modules/VRN", "VRN"), ("functional modules/VAP", "VAP"),
          ("functional modules/VQG", "VQG"))
SYSTEMS = ("VCGC", "VDF", "VRN", "VAP", "VQG")
OUT_REL = Path("VIA_Reports") / "vcgc" / "accel_cover"
LOCK_LEDGER = Path("docs") / "handoff" / "daily" / "VIA_SuccessLock_Ledger_v0100.jsonl"
BAD = ("MISSING", "UNRESOLVED", "AST_ERR")


def system_of(rel: str) -> str:
    r = rel.replace("\\", "/")
    for pre, name in SYS_OF:
        if r.startswith(pre + "/"):
            return name
    return "VCGC"


def accel_imports(src: str):
    """回 (語法樹看得到的加速器模組名集合, 錯誤字串或空)。只做 ast.parse,不執行。"""
    try:
        tree = ast.parse(src)
    except (SyntaxError, ValueError) as exc:
        return set(), "%s L%s" % (type(exc).__name__, getattr(exc, "lineno", "?"))
    mods = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            mods.update(a.name for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module:
            mods.add(n.module)
        elif isinstance(n, ast.Call) and n.args and isinstance(n.args[0], ast.Constant) and isinstance(n.args[0].value, str):
            f = n.func
            name = f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else "")
            if name in ("import_module", "__import__"):
                mods.add(n.args[0].value)
    return {m for m in mods if m in ACCEPT or ACCEPT_RE.match(m)}, ""


def resolve(p: Path, mod: str):
    """照橋的找法:從檔案位置往上,找 <夾>/supportive modules/<mod>.py(或同夾)。"""
    for d in [p.parent] + list(p.parents):
        for c in (d / "supportive modules" / (mod + ".py"), d / (mod + ".py")):
            if c.is_file():
                return c
    return None


def runtime_probe(sup: Path) -> dict:
    """子行程實際 import 每個可接受的加速器模組一次;回 {模組: 'ok' | 錯誤}。"""
    code = ("import json,sys\nsys.path.insert(0,sys.argv[1])\nr={}\nfor m in sys.argv[2:]:\n"
            "    try:\n        __import__(m); r[m]='ok'\n    except BaseException as e:\n        r[m]=type(e).__name__+': '+str(e)[:160]\n"
            "print('@@'+json.dumps(r))")
    try:
        cp = subprocess.run([sys.executable, "-B", "-c", code, str(sup), *ACCEPT], capture_output=True, text=True,
                            encoding="utf-8", errors="replace", timeout=300, env=dict(os.environ, PYTHONUTF8="1"))
        line = [x for x in cp.stdout.splitlines() if x.startswith("@@")]
        return json.loads(line[-1][2:]) if line else {m: "no output rc %s" % cp.returncode for m in ACCEPT}
    except (subprocess.TimeoutExpired, OSError, ValueError) as exc:
        return {m: type(exc).__name__ for m in ACCEPT}


def classify(p: Path, probe: dict) -> tuple:
    try:
        src = p.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return "AST_ERR", "讀取失敗 " + type(exc).__name__
    mods, err = accel_imports(src)
    if err:
        return "AST_ERR", err
    if mods:
        for m in sorted(mods):
            at = resolve(p, m)
            ok = probe.get(m, "ok" if ACCEPT_RE.match(m) else "沒測")
            if at is not None and ok == "ok":
                return "EFFECTIVE", m
        m = sorted(mods)[0]
        return "UNRESOLVED", "%s:%s" % (m, "往上找不到模組" if resolve(p, m) is None else "import 失敗 " + str(probe.get(m))[:80])
    if MARK in src:
        return "MARKER_ONLY", "只有標記,檔內沒有導入"
    return "MISSING", ""


def tool_bodies(via: Path) -> set:
    """加速器 / 網路工具本體(鎖冊 accelerator · network 兩支 + SuperAccel 轉接檔與 SUP_MDL737 本體):本體不導入自己,不算分母。"""
    out = set()
    try:
        lk = json.loads((via / "supportive modules" / "registry" / "VIA_ToolVersion_Lock_v0100.json").read_text(encoding="utf-8"))
        for k in ("accelerator", "network"):
            rel = str((lk.get(k) or {}).get("path") or "").replace("\\", "/")
            if rel:
                out.add(rel.split("/", 1)[1] if rel.startswith("VeritasIntelligenceAnalytics/") else rel)
    except (OSError, ValueError):
        pass
    return out


def is_tool_body(rel: str, bodies: set) -> bool:
    stem = Path(rel).stem
    return rel in bodies or stem in ACCEPT or bool(ACCEPT_RE.match(stem))


def locked_paths(via: Path) -> set:
    out = set()
    try:
        for line in (via / LOCK_LEDGER).read_text(encoding="utf-8").splitlines():
            try:
                out.add(str(json.loads(line).get("path") or "").replace("\\", "/"))
            except ValueError:
                continue
    except OSError:
        pass
    return out


def _progress(i: int, n: int, label: str) -> None:
    if n and (i == n or i % max(1, n // 50) == 0):
        pct = 100 * i // n
        sys.stderr.write("\r[%s] %-6s %3d%% |%-25s| %d/%d" % (STEM, label, pct, "#" * (pct // 4), i, n))
        if i == n:
            sys.stderr.write("\n")
        sys.stderr.flush()


def _pwsh_probe(mod: Path) -> str:
    exe = shutil.which("pwsh")
    if not exe:
        return "沒有 pwsh(沒量)"
    try:
        cp = subprocess.run([exe, "-NoProfile", "-NonInteractive", "-Command", ". '%s'; 'VIA-PS-OK'" % str(mod).replace("'", "''")],
                            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
        return "ok" if "VIA-PS-OK" in cp.stdout else ("rc %s" % cp.returncode)
    except (subprocess.TimeoutExpired, OSError) as exc:
        return type(exc).__name__


def effective(apply: bool = False, scope: str = "vcgc", write: bool = True, via: Path | None = None) -> dict:
    via = Path(via or _BODY["VIA"]).resolve()
    sup = via / "supportive modules"
    probe = runtime_probe(sup)
    locks = locked_paths(via)
    bodies = tool_bodies(via)
    t0 = datetime.now(timezone.utc)
    all_py = [p for p in via.rglob("*.py") if ".git" not in p.parts]
    rows, skipped = [], collections.Counter()
    for i, p in enumerate(all_py, 1):
        _progress(i, len(all_py), "PY")
        rel = str(p.relative_to(via)).replace("\\", "/")
        why = _BODY["_excluded"](p)
        if not why and is_tool_body(rel, bodies):
            why = "加速器 / 網路工具本體(不導入自己)"
        if why:
            skipped[why if len(why) < 40 else why[:40] + "…"] += 1
            continue
        st, note = classify(p, probe)
        rows.append({"file": rel, "sys": system_of(rel), "state": st, "note": note})
    # NET:只算真的出網的檔(前版判準)
    net = []
    for r in _BODY["scan"](".", "net", callers_only=True):
        rel = r["file"].replace("\\", "/")
        if r["state"] in ("HAS", "MISSING") and not is_tool_body(rel, bodies):
            net.append({"file": rel, "sys": system_of(rel), "state": r["state"]})
    # PS:尾版有沒有橋 · 模組找不找得到 · 有 pwsh 才實測
    ps_rows = _BODY["scan_ps"](".")
    hist = set(_BODY["_ps_history"](ps_rows)) if "_ps_history" in _BODY else set()
    ps_mod = sup / "VIA_PS_Accel_Module.ps1"
    ps_rt = _pwsh_probe(ps_mod) if ps_mod.is_file() else "模組不在"
    ps = []
    for r in ps_rows:
        rel = r["file"].replace("\\", "/")
        if r["state"] == "EXCLUDED" or r["file"] in hist or rel in hist:
            continue
        st = r["state"]
        if st == "HAS":
            st = "EFFECTIVE" if ps_rt == "ok" else ("UNRESOLVED" if ps_rt in ("模組不在",) or ps_rt.startswith("rc ") else "HAS_UNTESTED")
        ps.append({"file": rel, "sys": system_of(rel), "state": st})
    # 補:只補 PY ACCEL 的 MISSING / MARKER_ONLY 與出網檔缺的 NET 橋;範圍外與已鎖的不動
    acts = []
    if apply:
        todo = [r for r in rows if r["state"] in ("MISSING", "MARKER_ONLY")] + [dict(r, state="NET_MISSING") for r in net if r["state"] == "MISSING"]
        for j, r in enumerate(todo, 1):
            _progress(j, len(todo), "APPLY")
            if scope != "all" and r["sys"] != "VCGC":
                acts.append({"file": r["file"], "kind": r["state"], "result": "OUT_OF_SCOPE", "why": "%s 的檔由它自己的管理器處理" % r["sys"]})
                continue
            if r["file"] in locks:
                acts.append({"file": r["file"], "kind": r["state"], "result": "LOCKED", "why": "成功鎖點名;換版時帶橋"})
                continue
            kind = "net" if r["state"] == "NET_MISSING" else "accel"
            a = _BODY["inject"](r["file"], kind, True)
            acts.append({"file": r["file"], "kind": r["state"], "result": a["state"], "why": a.get("why", "")})
        done = {a["file"] for a in acts if a["result"] == "INJECTED"}
        for r in rows:
            if r["file"] in done:
                r["state"], r["note"] = classify(via / r["file"], probe)
        for r in net:
            if r["file"] in done:
                r["state"] = "HAS"
    for r in rows:
        if r["state"] in ("MISSING", "MARKER_ONLY") and r["file"] in locks:
            r["note"] = (r["note"] + " · " if r["note"] else "") + "成功鎖點名(換版時帶橋)"
    rep = summarize(rows, net, ps, skipped, probe, ps_rt, acts, apply, scope, len(all_py), t0, via)
    if write:
        write_outputs(rep, via)
    return rep


def summarize(rows, net, ps, skipped, probe, ps_rt, acts, apply, scope, n_all, t0, via) -> dict:
    per = {}
    for s in SYSTEMS:
        r = [x for x in rows if x["sys"] == s]
        c = collections.Counter(x["state"] for x in r)
        nn = [x for x in net if x["sys"] == s]
        pp = [x for x in ps if x["sys"] == s]
        pc = collections.Counter(x["state"] for x in pp)
        denom = len(r)
        pct = round(100.0 * c["EFFECTIVE"] / denom, 1) if denom else None
        lamp = ("GRAY" if not denom and not nn and not pp else
                "RED" if any(c[k] for k in BAD) or any(x["state"] == "MISSING" for x in nn) or pc["MISSING"] or pc["UNRESOLVED"] else
                "YELLOW" if c["MARKER_ONLY"] or pc["HAS_UNTESTED"] else "GREEN")
        per[s] = {"lamp": lamp, "py": denom, "effective": c["EFFECTIVE"], "marker_only": c["MARKER_ONLY"], "missing": c["MISSING"],
                  "unresolved": c["UNRESOLVED"], "ast_err": c["AST_ERR"], "pct": pct,
                  "net_callers": len(nn), "net_has": sum(1 for x in nn if x["state"] == "HAS"),
                  "ps": len(pp), "ps_has": len(pp) - pc["MISSING"], "ps_effective": pc["EFFECTIVE"]}
    lamps = [v["lamp"] for v in per.values()]
    lamp = "RED" if "RED" in lamps else "YELLOW" if "YELLOW" in lamps else "GREEN" if "GREEN" in lamps else "GRAY"
    tot_py = sum(v["py"] for v in per.values())
    tot_eff = sum(v["effective"] for v in per.values())
    return {"schema": "VIA.AccelCover.v1", "tool": "%s %s" % (STEM, VERSION), "at": t0.isoformat(timespec="seconds"),
            "secs": round((datetime.now(timezone.utc) - t0).total_seconds(), 1), "via": str(via), "apply": apply, "scope": scope,
            "lamp": lamp, "should_scan": n_all, "scanned": len(rows), "skipped": sum(skipped.values()),
            "skipped_why": dict(skipped.most_common(30)), "probe": probe, "ps_runtime": ps_rt,
            "total": {"py": tot_py, "effective": tot_eff, "pct": round(100.0 * tot_eff / tot_py, 2) if tot_py else None},
            "systems": per, "actions": acts,
            "not_green": [x for x in rows if x["state"] != "EFFECTIVE"] + [dict(x, state="NET_" + x["state"]) for x in net if x["state"] != "HAS"]
                         + [dict(x, state="PS_" + x["state"]) for x in ps if x["state"] != "EFFECTIVE"],
            "rc": 1 if lamp == "RED" else 2 if lamp in ("YELLOW", "GRAY") else 0}


LAMP_TXT = {"GREEN": "綠", "YELLOW": "黃", "RED": "紅", "GRAY": "灰"}


def paste_pack(rep: dict) -> str:
    t = rep["total"]
    out = ["# 加速器生效覆蓋 · %s · %s · 燈 %s · PY 生效 %s/%s(%s%%)· 應掃 %d · 已掃 %d · 略過 %d · %s%s"
           % (rep["tool"], rep["at"], LAMP_TXT[rep["lamp"]], t["effective"], t["py"], t["pct"], rep["should_scan"], rep["scanned"],
              rep["skipped"], "已補(範圍 %s)" % rep["scope"] if rep["apply"] else "只量不補", " · %ss" % rep["secs"]),
           "執行時載入:" + " · ".join("%s %s" % (k, v) for k, v in rep["probe"].items()) + " · PS 模組點源 " + rep["ps_runtime"],
           "| 燈 | 系統 | PY 生效 | 只有標記 | 缺 | 載不到 | AST 錯 | 出網檔有網路橋 | PS 有橋 |", "|---|---|---|---|---|---|---|---|---|"]
    for s, v in rep["systems"].items():
        out.append("| %s | %s | %s/%s(%s%%) | %s | %s | %s | %s | %s/%s | %s/%s |" % (
            LAMP_TXT[v["lamp"]], s, v["effective"], v["py"], v["pct"], v["marker_only"], v["missing"], v["unresolved"], v["ast_err"],
            v["net_has"], v["net_callers"], v["ps_has"], v["ps"]))
    ac = collections.Counter(a["result"] for a in rep["actions"])
    if rep["apply"]:
        out.append("補:" + (" · ".join("%s %d" % kv for kv in ac.most_common()) or "沒有要補的"))
    out.append("略過理由(前 8):" + " · ".join("%s %d" % kv for kv in list(rep["skipped_why"].items())[:8]))
    ng = rep["not_green"]
    if ng:
        out.append("## 非綠 %d 支(前 200)" % len(ng))
        out += ["%s %s %s %s" % (x["state"], x["sys"], x["file"], x.get("note", "")) for x in ng[:200]]
    s_bad = [s for s, v in rep["systems"].items() if v["lamp"] in ("RED", "YELLOW") and s != "VCGC"]
    if rep["lamp"] == "GREEN":
        nxt = "NEXT: 綠;不用動"
    elif not rep["apply"]:
        nxt = "NEXT: 加 --apply 補 VCGC 的缺口(VDF / VRN 等由各自管理器處理,或操作員明說 --scope all)"
    elif s_bad:
        nxt = "NEXT: VCGC 已補;%s 的缺口要操作員一句話「--scope all」或交給各系統自己的管理器" % "/".join(s_bad)
    else:
        nxt = "NEXT: 把貼回包貼回給 AI 判讀剩下的黃 / 紅"
    out = out[:299] + [nxt]
    return "\n".join(out) + "\n"


def _lamp_css(via: Path) -> str:
    books = sorted((via / "supportive modules" / "registry").glob("VIA_UI_FormatLock_v*.json"))
    try:
        return json.loads(books[-1].read_text(encoding="utf-8")).get("lamp_css", "")
    except (IndexError, OSError, ValueError):
        return ""


def render_html(rep: dict, via: Path) -> str:
    e = html.escape
    css = _lamp_css(via) or ".lamp{display:inline-block;width:12px;height:12px;border-radius:50%}"
    head = ("<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
            "<title>加速器生效覆蓋</title><style>%s body{font:11px/1.35 Arial,sans-serif;margin:10px;background:#f8fafc;color:#0f172a}"
            "h1{font-size:14px;margin:4px 0}h2{font-size:12px;margin:10px 0 4px}table{table-layout:fixed;width:100%%;border-collapse:collapse;background:#fff}"
            "th,td{border:1px solid #e2e8f0;padding:3px 6px;overflow-wrap:break-word;word-wrap:break-word;white-space:normal;text-align:left;vertical-align:top}"
            "th{background:#f1f5f9}td.n{text-align:right}col.l{width:34px}.m{color:#64748b}</style></head><body>" % css)
    t = rep["total"]
    body = ["<h1><span class='lamp %s'></span>加速器生效覆蓋 · PY %s/%s(%s%%)</h1>" % (rep["lamp"], t["effective"], t["py"], t["pct"]),
            "<div class='m'>%s · %s · 應掃 %d · 已掃 %d · 略過 %d · %s · 執行時載入:%s · PS 模組點源:%s</div>" % (
                e(rep["tool"]), e(rep["at"]), rep["should_scan"], rep["scanned"], rep["skipped"],
                "已補(範圍 %s)" % e(rep["scope"]) if rep["apply"] else "只量不補",
                e(" · ".join("%s %s" % kv for kv in rep["probe"].items())), e(rep["ps_runtime"])),
            "<h2>系統矩陣</h2><table><colgroup><col class='l'></colgroup><tr><th>燈</th><th>系統</th><th>PY 生效</th><th>只有標記</th><th>缺</th>"
            "<th>載不到</th><th>AST 錯</th><th>出網檔有網路橋</th><th>PS 有橋</th></tr>"]
    for s, v in rep["systems"].items():
        body.append("<tr><td><span class='lamp %s'></span></td><td>%s</td><td class='n'>%s/%s(%s%%)</td><td class='n'>%s</td><td class='n'>%s</td>"
                    "<td class='n'>%s</td><td class='n'>%s</td><td class='n'>%s/%s</td><td class='n'>%s/%s</td></tr>" % (
                        v["lamp"], s, v["effective"], v["py"], v["pct"], v["marker_only"], v["missing"], v["unresolved"], v["ast_err"],
                        v["net_has"], v["net_callers"], v["ps_has"], v["ps"]))
    body.append("</table>")
    if rep["actions"]:
        body.append("<h2>補橋動作 %d</h2><table><colgroup><col class='l'></colgroup><tr><th>燈</th><th>結果</th><th>類</th><th>檔</th><th>說明</th></tr>" % len(rep["actions"]))
        for a in rep["actions"][:500]:
            lp = "GREEN" if a["result"] == "INJECTED" else "RED" if a["result"] == "SKIP" else "YELLOW" if a["result"] == "LOCKED" else "GRAY"
            body.append("<tr><td><span class='lamp %s'></span></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
                lp, e(a["result"]), e(a["kind"]), e(a["file"]), e(a["why"])))
        body.append("</table>")
    body.append("<h2>非綠 %d 支</h2><table><colgroup><col class='l'></colgroup><tr><th>燈</th><th>狀態</th><th>系統</th><th>檔</th><th>說明</th></tr>" % len(rep["not_green"]))
    for x in rep["not_green"][:800]:
        lp = "RED" if x["state"].split("_")[-1] in ("MISSING", "UNRESOLVED", "ERR") else "YELLOW" if "MARKER" in x["state"] or "UNTESTED" in x["state"] else "GRAY"
        body.append("<tr><td><span class='lamp %s'></span></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
            lp, e(x["state"]), e(x["sys"]), e(x["file"]), e(x.get("note", ""))))
    body.append("</table><h2>略過理由(應掃 − 已掃)</h2><table><tr><th>理由</th><th>支數</th></tr>")
    body += ["<tr><td>%s</td><td class='n'>%d</td></tr>" % (e(k), v) for k, v in rep["skipped_why"].items()]
    body.append("</table></body></html>")
    return head + "\n".join(body)


def write_outputs(rep: dict, via: Path) -> None:
    out = via / OUT_REL
    out.mkdir(parents=True, exist_ok=True)
    (out / "ACCEL_COVER_latest.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "ACCEL_COVER_latest.txt").write_text(paste_pack(rep), encoding="utf-8")
    if not rep.get("no_html"):
        (out / "ACCEL_COVER_latest.html").write_text(render_html(rep, via), encoding="utf-8")


def selftest() -> int:
    ok = []

    def chk(n, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + n + ((" · " + str(note)[:240]) if note and not cond else ""), flush=True)

    print("[計] %s %s 自測開始(本版 10 項 · 前版 %s 在子行程)" % (STEM, VERSION, PRIOR_PATH.name), flush=True)
    with tempfile.TemporaryDirectory(prefix="mdl124v112_") as td:
        via = Path(td) / "VIA"
        (via / "supportive modules").mkdir(parents=True)
        (via / "supportive modules" / "VIA_SuperAccel_Module.py").write_text("X = 1\n", encoding="utf-8")
        d = via / "supportive modules" / "registry"
        d.mkdir()
        files = {
            "eff.py": "# " + MARK + ":v0111]\ntry:\n    import VIA_SuperAccel_Module as VIA_ACCEL\nexcept Exception:\n    VIA_ACCEL = None\n",
            "cel.py": "import importlib\n_sa = importlib.import_module('VeritasCeleritas_v1141')\n",
            "mark.py": "# " + MARK + ":v0111]\nx = 1\n",
            "miss.py": "x = 1\n",
            "bad.py": "def (:\n"}
        for k, v in files.items():
            (d / k).write_text(v, encoding="utf-8")
        probe = {"VIA_SuperAccel_Module": "ok", "VeritasCeleritas_v1141": "ok"}
        got = {k: classify(d / k, probe)[0] for k in files}
        chk("T1 五態分類:生效 · 只有標記 · 缺 · 載不到 · AST 錯", got == {"eff.py": "EFFECTIVE", "cel.py": "UNRESOLVED", "mark.py": "MARKER_ONLY",
                                                         "miss.py": "MISSING", "bad.py": "AST_ERR"}, got)
        chk("T2 模組 import 失敗 → 載不到(標記與導入都在也不算生效)",
            classify(d / "eff.py", {"VIA_SuperAccel_Module": "ImportError"})[0] == "UNRESOLVED")
        chk("T3 子行程實測真的 import 得到樹內的加速器模組", runtime_probe(via / "supportive modules").get("VIA_SuperAccel_Module") == "ok")
        chk("T4 系統歸屬:VDF / VRN / VAP / VQG 以外都是 VCGC",
            [system_of(x) for x in ("functional modules/VDF/a.py", "functional modules/VRN/b.py", "supportive modules/c.py", "x.py")] == ["VDF", "VRN", "VCGC", "VCGC"])
        keep = _BODY["VIA"]
        _BODY["VIA"] = via
        try:
            for k in ("mark.py", "miss.py"):
                a = _BODY["inject"]("supportive modules/registry/" + k, "accel", True)
                assert a["state"] == "INJECTED", a
            after = {k: classify(d / k, probe)[0] for k in ("mark.py", "miss.py")}
        except AssertionError as exc:
            after = {"err": str(exc)}
        finally:
            _BODY["VIA"] = keep
        chk("T5 前版 inject 補上後,只有標記 / 缺 → 生效", after == {"mark.py": "EFFECTIVE", "miss.py": "EFFECTIVE"}, after)
        rep = summarize([{"file": "a.py", "sys": "VCGC", "state": "EFFECTIVE", "note": ""}, {"file": "functional modules/VDF/b.py", "sys": "VDF", "state": "MARKER_ONLY", "note": ""}],
                        [], [], collections.Counter({"版史": 3}), probe, "沒有 pwsh(沒量)", [], False, "vcgc", 5, datetime.now(timezone.utc), via)
        pk = paste_pack(rep)
        chk("T6 貼回包:三數(應掃 5 · 已掃 2 · 略過 3)· 黃燈 · 末行 NEXT:",
            "應掃 5 · 已掃 2 · 略過 3" in pk and rep["lamp"] == "YELLOW" and pk.strip().splitlines()[-1].startswith("NEXT:") and len(pk.splitlines()) <= 300, pk[:200])
        h = render_html(rep, Path(keep))
        chk("T7 頁面:燈在第一欄 · 鎖定色票(紅燈慢閃)· 長字換行 · 固定表寬", "<td><span class='lamp" in h and "via-blink" in h
            and "overflow-wrap:break-word" in h and "table-layout:fixed" in h)
    cp = subprocess.run([sys.executable, "-B", str(PRIOR_PATH), "--selftest"], capture_output=True, text=True, encoding="utf-8",
                        errors="replace", timeout=900)
    fails = [x.strip() for x in cp.stdout.splitlines() if "[FAIL]" in x]
    tree = [x for x in fails if "真樹" in x]          # 前版量「真樹」現況的檢查(例:VDF 檔缺網路橋)= 樹的狀態,不是程式錯
    if tree:
        print("  [注] 前版只因真樹現況紅(照實列出,由該系統處理):" + " | ".join(x[:160] for x in tree), flush=True)
    chk("T8 前版 %s 自測照過(子行程;真樹現況類另列)" % PRIOR_PATH.name, cp.returncode == 0 or (fails and len(tree) == len(fails)), fails[:3])
    src = Path(__file__).read_text(encoding="utf-8")
    chk("T9 第 3 行加速器標記且載入生效(VIA_ACCEL 非空)· 零 TA-Lib · 不 import 他系統",
        src.splitlines()[2].strip() == "# [VIA:ACCEL-BRIDGE:v0111]" and VIA_ACCEL is not None
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M) and not re.search(r"^\s*(import|from)\s+(VDF|VRN|VQG|VAP)", src, re.M),
        "VIA_ACCEL %s" % (VIA_ACCEL is not None))
    bd = tool_bodies(Path(_BODY["VIA"]))
    chk("T10 加速器 / 網路工具本體豁免(鎖冊兩支 + SUP_MDL737 + 轉接檔),一般檔不豁免",
        all(is_tool_body(x, bd) for x in ("supportive modules/VeritasCeleritas_v1141.py", "supportive modules/network/VeritasAegisNexus_v1652.py",
                                          "supportive modules/SUP_MDL737_SuperAccelModule_v0110.py", "supportive modules/VIA_SuperAccel_Module.py"))
        and not is_tool_body("supportive modules/registry/CGC_SystemManager_v0120.py", bd), sorted(bd))
    n = sum(ok)
    print("[計] %s %s 自測 %d/%d · %s" % (STEM, VERSION, n, len(ok), "PASS" if n == len(ok) else "FAIL"), flush=True)
    return 0 if n == len(ok) else 1


def main() -> int:
    a = sys.argv[1:]
    if "--effective" in a:
        if "--selftest" in a:
            return selftest()
        scope = a[a.index("--scope") + 1] if "--scope" in a else "vcgc"
        if scope not in ("vcgc", "all"):
            print("[%s] --scope 只收 vcgc | all" % STEM)
            return 1
        rep = effective(apply="--apply" in a, scope=scope)
        if "--no-html" in a:
            (Path(_BODY["VIA"]) / OUT_REL / "ACCEL_COVER_latest.html").unlink(missing_ok=True)
        sys.stdout.write(paste_pack(rep))
        print("[%s] 頁面 %s" % (STEM, OUT_REL / "ACCEL_COVER_latest.html"))
        return rep["rc"]
    if "--selftest" in a and "--prior" not in a and len(a) == 1:
        return selftest()
    return PRIOR.main()


if __name__ == "__main__":
    raise SystemExit(main())
