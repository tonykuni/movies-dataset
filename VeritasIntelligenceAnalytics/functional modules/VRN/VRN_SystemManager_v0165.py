#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0165 — 薄尾(操作員 2026-10-10 實跑:第二步 30/57 但三區頁 / 工具帳沒出、STEP2 是 v0157 格式 = 收尾中途崩、錯誤被吞)。
  ① 錯誤不再被吞:任何例外印一行 [計] 失敗 · 型別 · 訊息 · 檔:行(函式),完整 Traceback 寫 VIA_Reports\\vrn\\layout\\LAST_ERROR.txt
  ② 收尾各步隔離:寫頁(STEP1/2 · XCHECK · STEP3)· OCR 探測 / 執行 · 安裝請求 · SUMMARIZER 閘 · TEMP 清舊 · 資料庫對照 任一步出錯只記紅,其他照跑完
  ③ 逾時一律判失敗(第二步不過 · 紅燈):前版只加註記,年度頁沒跑完反而讓表格項目「空集合 = 過」→ 灌水
  ④ l2report:唯讀讀上一輪 TEMP 的逐檔結果(不用重跑):文字沒過的檔與原因(覆蓋 / 分類 / 全影像 · 漏字片段)· 表格未過原因 · 逾時 · 藏在文字的表 · 工具效益
其餘動詞照前版鏈。
"""
from __future__ import annotations

# ===== [VIA:ACCEL-BRIDGE:v0110] 正本加速器 VeritasCeleritas_v1141 · 正本網路工具 VeritasAegisNexus_v1652(找不到 = 不改任何行為) =====
import sys as _cb_sys
from pathlib import Path as _cb_Path
_cb_p = _cb_Path(__file__).resolve()
while _cb_p.parent != _cb_p:
    if (_cb_p / "supportive modules").is_dir():
        _cb_sup = _cb_p / "supportive modules"
        for _cb_d in [_cb_sup] + [x.parent for x in list(_cb_sup.glob("*/VeritasAegisNexus_v1652.py"))[:1]]:
            if str(_cb_d) not in _cb_sys.path:
                _cb_sys.path.insert(0, str(_cb_d))
        break
    _cb_p = _cb_p.parent
try:
    import VeritasCeleritas_v1141 as _ACCEL  # noqa: F401  正本加速器
except Exception:  # noqa: BLE001
    _ACCEL = None


def _net():
    """正本網路工具(只在需要出網時載入;本引擎不出網)。"""
    try:
        import VeritasAegisNexus_v1652 as _NET  # noqa: WPS433
        return _NET
    except Exception:  # noqa: BLE001
        return None
# ===== [VIA:ACCEL-BRIDGE:END] =====

import datetime
import html
import importlib.util
import json
import os
import re
import sys
import tempfile
import traceback
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"
TAG = "v0165"


def _vnum_v0165(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0165(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0165(p) < _vnum_v0165(__file__)), key=_vnum_v0165)
PRIOR = _load_v0165(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


def _owner(name):
    import types
    mod, seen = PRIOR, set()
    while isinstance(mod, types.ModuleType) and id(mod) not in seen:
        seen.add(id(mod))
        if name in vars(mod):
            return mod
        mod = vars(mod).get("PRIOR")
    return None


def _resolve(name):
    m = _owner(name)
    return vars(m)[name] if m else None


def _job_entry(kind, item):
    return _resolve("_job")(kind, item)


def _init_entry(*args):
    return _resolve("_init_entry")(*args)


_rep = _resolve("_rep")
_ERR = []


def _where(exc: BaseException) -> str:
    tb = traceback.extract_tb(exc.__traceback__)
    last = tb[-1] if tb else None
    return "%s:%s(%s)" % (Path(last.filename).name, last.lineno, last.name) if last else "?"


def _record(stage: str, exc: BaseException) -> None:
    _ERR.append({"stage": stage, "type": type(exc).__name__, "msg": str(exc)[:200], "where": _where(exc), "tb": "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))})


# ───────── ② 收尾各步隔離:任一步出錯只記紅,回安全預設,其他照跑 ─────────
_SAFE = {"write_pages": lambda *a, **k: {}, "_step2_page": lambda *a, **k: "", "_step3_page": lambda *a, **k: "", "_xcheck_page": lambda *a, **k: "",
         "ocr_probe": lambda *a, **k: {"avail": {}, "missing": []}, "ocr_stage": lambda *a, **k: {}, "tool_request": lambda *a, **k: {},
         "summarizer_gate": lambda *a, **k: {"allowed": 0, "total": 0, "files": {}, "path": "", "rule": "收尾失敗,閘未算"}, "temp_gc": lambda *a, **k: {"cleaned": 0, "freed_mb": 0.0, "kept": 0},
         "db_check": lambda *a, **k: {}}
_STAGE_ZH = {"write_pages": "寫頁(STEP1 / STEP2 / XCHECK)", "_step2_page": "STEP2 頁", "_step3_page": "STEP3 頁", "_xcheck_page": "XCHECK 頁", "ocr_probe": "OCR 工具探測", "ocr_stage": "OCR 執行",
             "tool_request": "安裝請求單", "summarizer_gate": "SUMMARIZER 閘", "temp_gc": "TEMP 清舊", "db_check": "資料庫對照"}


def _guard(name: str):
    m = _owner(name)
    if not m:
        return False
    fn = vars(m)[name]
    if getattr(fn, "_vrn_guarded", False):
        return True

    def wrapped(*a, **k):
        try:
            return fn(*a, **k)
        except Exception as exc:  # noqa: BLE001
            _record(_STAGE_ZH.get(name, name), exc)
            return _SAFE[name](*a, **k)
    wrapped._vrn_guarded = True
    wrapped.__name__ = getattr(fn, "__name__", name)
    setattr(m, name, wrapped)
    return True


_GUARDED = {n: _guard(n) for n in _SAFE}


# ───────── ③ 逾時一律判失敗 ─────────
_PREV_L2 = _resolve("l2_one")


def l2_one_v165(row: dict) -> dict:
    r = _PREV_L2(row)
    if isinstance(r, dict) and r.get("timeout"):
        r["step2_ok"] = False
        r["table_ok"] = False
        r["lamp"] = "RED"
        if not any("逾時" in n for n in r.get("notes", [])):
            r.setdefault("notes", []).append("逾時 → 第二步不過")
    return r


_ml2 = _owner("l2_one")
if _ml2:
    setattr(_ml2, "l2_one", l2_one_v165)


# ───────── ④ l2report:唯讀讀上一輪 TEMP 逐檔結果 ─────────
def _latest_l2_dir(run: str = "") -> Path | None:
    roots = []
    if os.environ.get("VIA_SPILL_DIR"):
        sp = Path(os.environ["VIA_SPILL_DIR"])
        roots += [sp] + ([sp.parents[1]] if len(sp.parents) > 1 else [])     # 啟動器每輪換新 spill → 上一輪在兄弟夾(…\VIA_progress\ps_*\spill)
    roots.append(Path(tempfile.gettempdir()) / "VIA_progress")
    roots = list(dict.fromkeys(roots))
    cands = []
    for r in roots:
        if r.is_dir():
            cands += [d for d in r.glob("vrn_stage_*/layout_l2") if d.is_dir()] + [d for d in r.glob("ps_*/spill/vrn_stage_*/layout_l2") if d.is_dir()]
    if run:
        cands = [d for d in cands if run in str(d)]
    cands = [d for d in cands if any(d.glob("*.json"))]
    return max(cands, key=lambda d: max(p.stat().st_mtime for p in d.glob("*.json"))) if cands else None


def l2report(run: str = "") -> dict:
    d = _latest_l2_dir(run)
    if not d:
        return {"err": "找不到任何一輪的 layout_l2 結果(TEMP\\VIA_progress\\…\\vrn_stage_*\\layout_l2)"}
    rows = []
    for p in sorted(d.glob("*.json")):
        try:
            j = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        s = j.get("summary") or {}
        miss = [sn for pg in j.get("pages", []) for sn in (pg.get("coverage") or {}).get("miss_snippets", [])][:3]
        unclassified = [b.get("id") for pg in j.get("pages", []) for b in pg.get("blocks", []) if b.get("kind") == "text" and not b.get("sub")][:4]
        why = []
        if s.get("image_only"):
            why.append("全影像(無文字層)")
        if s.get("cov_min", 100) < 99.5:
            why.append("覆蓋 %.2f%%(漏字:%s)" % (s.get("cov_min", 0), " / ".join(x[:24] for x in miss) or "—"))
        if s.get("classified", 100) < 99.9:
            why.append("分類 %.1f%%(未分類區:%s)" % (s.get("classified", 0), ",".join(str(x) for x in unclassified) or "—"))
        rows.append({"file": s.get("file", p.stem), "text_ok": s.get("text_ok"), "table_ok": s.get("table_ok"), "step2_ok": s.get("step2_ok"), "timeout": s.get("timeout"), "secs": s.get("secs"),
                     "tables": s.get("tables", 0), "tables_ok": s.get("tables_ok", 0), "hidden": s.get("hidden_tables", 0), "tools": s.get("tools", []), "verify_issues": s.get("verify_issues", {}),
                     "text_why": "; ".join(why), "notes": s.get("notes", []), "lamp": s.get("lamp", "")})
    agg = defaultdict(lambda: {"n": 0, "ok": 0, "ms": 0})
    for r in rows:
        for t in r["tools"] or []:
            a = agg[t["tool"]]
            a["n"] += 1
            a["ok"] += 1 if t["ok"] else 0
            a["ms"] += t["ms"]
    issues = Counter()
    for r in rows:
        for k, v in (r["verify_issues"] or {}).items():
            issues[k.split(" ")[0]] += v
    out = {"dir": str(d), "n": len(rows), "text_bad": [r for r in rows if not r["text_ok"]], "timeouts": [r for r in rows if r["timeout"]], "hidden": sum(r["hidden"] for r in rows),
           "tables": sum(r["tables"] for r in rows), "tables_ok": sum(r["tables_ok"] for r in rows), "step2": sum(1 for r in rows if r["step2_ok"]), "tools": dict(agg), "issues": issues.most_common(8),
           "slowest": sorted(rows, key=lambda r: -(r["secs"] or 0))[:5], "rows": rows}
    page = _resolve("_page")
    if page:
        hp = _rep() / "layout" / "L2REPORT_latest.html"
        hp.parent.mkdir(parents=True, exist_ok=True)
        hp.write_text(page("上一輪第二步逐檔結果(唯讀 · 讀 TEMP)", "%s · 檔 %d · 第二步過 %d · 文字沒過 %d · 逾時 %d · 表 %d 過 %d · 藏在文字的表 %d" % (html.escape(str(d)), out["n"], out["step2"], len(out["text_bad"]), len(out["timeouts"]), out["tables"], out["tables_ok"], out["hidden"]),
                               ["檔", "文字", "文字沒過原因", "表格", "逾時", "秒", "藏表", "註"],
                               [("RED" if r["timeout"] else ("GREEN" if r["step2_ok"] else "YELLOW"), [r["file"], "✓" if r["text_ok"] else "✗", r["text_why"] or "—", "%d/%d" % (r["tables_ok"], r["tables"]), "是" if r["timeout"] else "—", r["secs"] or 0, r["hidden"], "; ".join(r["notes"])[:160]]) for r in rows]), encoding="utf-8")
        out["html"] = str(hp)
    return out


def _print_errors() -> None:
    for e in _ERR[:8]:
        print("[計] 收尾失敗 · %s · %s: %s · %s" % (e["stage"], e["type"], e["msg"][:120], e["where"]))
    if _ERR:
        p = _rep() / "layout" / "LAST_ERROR.txt"
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("\n\n".join("== %s · %s\n%s" % (e["stage"], datetime.datetime.now().isoformat(timespec="seconds"), e["tb"]) for e in _ERR), encoding="utf-8")
            print("[計] 完整錯誤 %s" % p)
        except OSError:
            pass


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    if "--selftest" in args[:2]:
        return selftest()
    if args[:1] == ["l2report"]:
        o = l2report(args[args.index("--run") + 1] if "--run" in args and args.index("--run") + 1 < len(args) else "")
        if o.get("err"):
            print("[計] l2report · %s · RED" % o["err"])
            return 1
        print("[計] l2report · %s · 檔 %d · 第二步過 %d · 文字沒過 %d · 逾時 %d · 表 %d 過 %d · 藏在文字的表 %d" % (o["dir"], o["n"], o["step2"], len(o["text_bad"]), len(o["timeouts"]), o["tables"], o["tables_ok"], o["hidden"]))
        for r in o["text_bad"][:10]:
            print("[計] 文字沒過 · %s · %s" % (r["file"][:50], r["text_why"] or ("; ".join(r["notes"])[:120] or "—")))
        for r in o["timeouts"][:5]:
            print("[計] 逾時 · %s · %s 秒" % (r["file"][:50], r["secs"]))
        if o["tools"]:
            print("[計] 工具效益(每表)· " + " · ".join("%s %d 表 過 %.0f%% 平均 %d ms" % (k, v["n"], 100.0 * v["ok"] / max(v["n"], 1), v["ms"] / max(v["n"], 1)) for k, v in sorted(o["tools"].items(), key=lambda kv: -kv[1]["n"])[:5]))
        else:
            print("[計] 工具效益 · 這一輪的結果沒有工具帳(跑的是 v0163 之前的 l2)")
        print("[計] 表格未過原因 · " + (" · ".join("%s×%d" % kv for kv in o["issues"]) or "—"))
        print("[計] 最慢 · " + " · ".join("%s %ss" % (r["file"][:24], r["secs"]) for r in o["slowest"]))
        if o.get("html"):
            print("  [U/I] %s" % o["html"])
        return 0
    try:
        rc = PRIOR.main(args)
    except Exception as exc:  # noqa: BLE001
        _record("主流程", exc)
        print("[計] 失敗 · VRN %s 中途例外 · %s: %s · %s" % (args[0] if args else "", type(exc).__name__, str(exc)[:160], _where(exc)))
        rc = 1
    _print_errors()
    return rc


def selftest() -> int:
    import shutil
    p = f = 0

    def chk(name, cond):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s" % name)
    chk("① 收尾 %d 步都已隔離(寫頁 · OCR · 閘 · TEMP 清舊 · 資料庫對照 …)" % sum(_GUARDED.values()), sum(_GUARDED.values()) >= 8)
    m = _owner("summarizer_gate")
    _ERR.clear()
    g = vars(m)["summarizer_gate"](None, None)
    chk("② 隔離生效:SUMMARIZER 閘拿到壞資料 → 不崩 · 回安全預設 · 記一筆紅(型別 · 檔:行)", g.get("allowed") == 0 and _ERR and _ERR[-1]["stage"] == "SUMMARIZER 閘" and ":" in _ERR[-1]["where"])
    td = Path(tempfile.mkdtemp(prefix="vrn165-"))
    try:
        l2d = td / "VIA_progress" / "ps_x" / "spill" / "vrn_stage_r1" / "layout_l2"
        l2d.mkdir(parents=True)
        mk = lambda name, **kw: {"summary": dict({"file": name, "text_ok": True, "table_ok": True, "step2_ok": True, "cov_min": 100.0, "classified": 100.0, "tables": 2, "tables_ok": 2, "secs": 10, "tools": [{"tool": "單讀(pdfplumber)", "ms": 50, "ok": True}]}, **kw),  # noqa: E731
                                 "pages": [{"coverage": {"miss_snippets": ["Source: KGI"]}, "blocks": [{"kind": "text", "id": "P1·F·09", "sub": ""}]}]}
        (l2d / "a.json").write_text(json.dumps(mk("A.pdf")), encoding="utf-8")
        (l2d / "b.json").write_text(json.dumps(mk("B.pdf", text_ok=False, step2_ok=False, cov_min=98.7)), encoding="utf-8")
        (l2d / "c.json").write_text(json.dumps(mk("C.pdf", text_ok=False, step2_ok=False, classified=97.0)), encoding="utf-8")
        (l2d / "d.json").write_text(json.dumps(mk("D.pdf", timeout=True, step2_ok=False, secs=301)), encoding="utf-8")
        saved = os.environ.get("VIA_SPILL_DIR")
        (td / "VIA_progress" / "ps_new" / "spill").mkdir(parents=True)
        os.environ["VIA_SPILL_DIR"] = str(td / "VIA_progress" / "ps_new" / "spill")     # 模擬啟動器:本輪 spill 是新的空夾,上一輪在兄弟夾
        try:
            o = l2report()
        finally:
            if saved is None:
                os.environ.pop("VIA_SPILL_DIR", None)
            else:
                os.environ["VIA_SPILL_DIR"] = saved
        tb = {r["file"]: r["text_why"] for r in o["text_bad"]}
        chk("③ l2report 唯讀讀上一輪:文字沒過 2(B 覆蓋 98.70% · 漏字 Source: KGI;C 分類 97.0% · 未分類區 P1·F·09)· 逾時 1 · 工具帳彙總", len(tb) == 2 and "98.70%" in tb["B.pdf"] and "Source: KGI" in tb["B.pdf"] and "P1·F·09" in tb["C.pdf"] and len(o["timeouts"]) == 1 and o["tools"]["單讀(pdfplumber)"]["n"] == 4)
    finally:
        shutil.rmtree(td, ignore_errors=True)
    fake = {"timeout": True, "step2_ok": True, "table_ok": True, "lamp": "GREEN", "notes": []}
    global _PREV_L2
    keep = _PREV_L2
    _PREV_L2 = lambda row: dict(fake)  # noqa: E731
    try:
        r = l2_one_v165({})
    finally:
        _PREV_L2 = keep
    chk("④ 逾時一律判失敗:第二步不過 · 表格不過 · 紅燈 · 註明", r["step2_ok"] is False and r["table_ok"] is False and r["lamp"] == "RED" and any("逾時" in n for n in r["notes"]))
    me = Path(__file__).read_text(encoding="utf-8")
    chk("⑤ 正本加速器橋 · 自帶多程序墊片", "import VeritasCeleritas_v1141" in me and _job_entry.__module__ in ("__main__", __name__))
    _ERR.clear()
    print("  ── 前版鏈自測(原樣印出)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("⑥ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    print("[計] VRN_SystemManager_v0165 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
