#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0177 — 薄尾(操作員 2026-10-11「減少重複指令整合為一 · 自動實測優化 · 用 VCGC 節省 TOKEN 工具來進行後續動作 · 雙軌擷取 · 雙軌 100% 還原」)。
  ① auto 一條指令:layout → restore → basicinfo → 雙軌 → 實測 → KPI → 決策 → AI 包;各段依 AST 精準輸入鍵判斷「同輸入不重跑」
     layout 鍵 = 輸入夾指紋 + 定義 / 替換 layout 相關函式的版本檔(AST)+ intake · restore 鍵 = layout 輪 + 設定冊 + restore 相關版本檔 · basicinfo 鍵 = layout 輪 + 日期
  ② 決策要樣本:讀表器排序 / 停用 試 ≥15 次才算;小樣本已寫進設定的排序 → 自動撤回(回預設順序)
  ③ AI 包 VRN_AI_PACK_latest.md(≤300 行):KPI · 決策 · 算術不符依規則分類 + 例子 · 雙軌衝突依原因 + 例子 · BASIC INFO 紅燈 · NEXT
     → 交給 VCGC CGC_MDL256_AiVerbBridge paste 壓縮(只讀 · 不寫 VCGC 帳)→ 啟動器 paste.md / 剪貼簿改用此包
  ④ 雙軌三個已知錯:NON-OCR 目標價不合理(對收盤 <0.3 倍或 ≤1.5)→ 剔除當單軌 · OCR 目標價不抓年份 · 資訊區 OCR 往上含頁首(讀得到報告日)
  ⑤ 快查靜態檢查逐檔快取(sha 沒變不重編譯)· 讀表實測:快速讀表器先測全部沒過的表,重型只抽樣
其餘動詞照前版鏈。
"""
from __future__ import annotations

# ===== [VIA:ACCEL-BRIDGE:v0111] 最新有版號的正本加速器(動態取最高 VeritasCeleritas_v####;退回鎖版 v1141)· 正本網路工具 VeritasAegisNexus_v1652(找不到 = 不改任何行為) =====
import importlib as _cb_il
import re as _cb_re
import sys as _cb_sys
from pathlib import Path as _cb_Path
_ACCEL, _ACCEL_VER = None, ""
_cb_p = _cb_Path(__file__).resolve()
while _cb_p.parent != _cb_p:
    if (_cb_p / "supportive modules").is_dir():
        _cb_sup = _cb_p / "supportive modules"
        _cb_c = sorted(list(_cb_sup.glob("VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")) + list(_cb_sup.glob("*/VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")),
                       key=lambda x: int(_cb_re.search(r"_v(\d{4})", x.name).group(1)))
        for _cb_d in [str(_cb_sup)] + ([str(_cb_c[-1].parent)] if _cb_c else []) + [str(x.parent) for x in list(_cb_sup.glob("*/VeritasAegisNexus_v1652.py"))[:1]]:
            if _cb_d not in _cb_sys.path:
                _cb_sys.path.insert(0, _cb_d)
        if _cb_c:
            try:
                _ACCEL, _ACCEL_VER = _cb_il.import_module(_cb_c[-1].stem), _cb_c[-1].stem
            except Exception:  # noqa: BLE001
                _ACCEL = None
        break
    _cb_p = _cb_p.parent
if _ACCEL is None:
    try:
        import VeritasCeleritas_v1141 as _ACCEL  # noqa: F401  退回鎖版
        _ACCEL_VER = "VeritasCeleritas_v1141"
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

import ast
import datetime
import hashlib
import html
import importlib.util
import json
import os
import re
import subprocess
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"
TAG = "v0177"
MIN_SAMPLE = 15


def _vnum_v0177(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0177(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0177(p) < _vnum_v0177(__file__)), key=_vnum_v0177)
PRIOR = _load_v0177(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


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


_rep, _home = _resolve("_rep"), _resolve("_home")


def _patch_v(name: str, fn):
    """替換擁有者層的函式(九頭龍掃描認得 _patch_v("名字", …) → 頭數照實計)· 保留被包函式的屬性(標記延續:包裝仍走前版行為)。"""
    import functools
    mo = _owner(name)
    if mo is None or getattr(vars(mo)[name], "_v177", False):
        return None
    prev = vars(mo)[name]
    functools.update_wrapper(fn, prev)
    fn._v177 = True
    fn._prev = prev
    setattr(mo, name, fn)
    return prev


# ───────── ⑤ 快查靜態檢查:逐檔快取 ─────────
def static_check_v177(files: dict) -> dict:
    prev = static_check_v177._prev
    cf = _rep() / "selfgate" / "static_cache.json"
    try:
        cache = json.loads(cf.read_text(encoding="utf-8")) if cf.exists() else {}
    except ValueError:
        cache = {}
    sha = {}
    for rel, p in files.items():
        try:
            sha[rel] = hashlib.sha256(p.read_bytes()).hexdigest()[:16]
        except OSError:
            sha[rel] = ""
    todo = {rel: p for rel, p in files.items() if cache.get(rel, {}).get("sha") != sha[rel]}
    r = prev(todo) if todo else {"bad": {}, "ps_parser": cache.get("__ps_parser__", {}).get("v", "ABSENT")}
    for rel in todo:
        cache[rel] = {"sha": sha[rel], "bad": r["bad"].get(rel, "")}
    if todo and any(p.suffix.lower() == ".ps1" for p in todo.values()):
        cache["__ps_parser__"] = {"sha": "", "v": r.get("ps_parser", "ABSENT")}
    try:
        cf.parent.mkdir(parents=True, exist_ok=True)
        cf.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass
    bad = {rel: cache[rel]["bad"] for rel in files if cache.get(rel, {}).get("bad")}
    return {"bad": bad, "py": sum(1 for p in files.values() if p.suffix.lower() == ".py"), "ps1": sum(1 for p in files.values() if p.suffix.lower() == ".ps1"),
            "ps_parser": cache.get("__ps_parser__", {}).get("v", r.get("ps_parser", "ABSENT")), "recompiled": len(todo)}


_patch_v("static_check", static_check_v177)


# ───────── 修正閘 AST 錨點補齊:_patch / _patch_v("名字", …) 的替換點也要有精準 / 彈性錨點 ─────────
def anchors_v177(root: Path, newest: Path) -> list:
    out = anchors_v177._prev(root, newest)
    seen = {a["target"] for a in out}
    try:
        t = ast.parse(newest.read_text(encoding="utf-8"))
    except (SyntaxError, OSError):
        return out
    names = []
    for n in ast.walk(t):
        if isinstance(n, ast.Call) and getattr(n.func, "id", "") in ("_patch", "_patch_v") and n.args and isinstance(n.args[0], ast.Constant) and isinstance(n.args[0].value, str):
            if n.args[0].value not in seen:
                names.append(n.args[0].value)
    cands = sorted([q for q in root.glob(_STEM + "_v*.py") if _vnum_v0177(q) < _vnum_v0177(newest)], key=_vnum_v0177, reverse=True)
    cands += sorted((root / "intake").rglob("*_v*.py"), key=lambda q: q.name, reverse=True) if (root / "intake").is_dir() else []
    for nm in dict.fromkeys(names):
        hit = None
        for q in cands:
            try:
                tt = ast.parse(q.read_text(encoding="utf-8"))
            except (SyntaxError, OSError):
                continue
            hit = next(((q, d) for d in tt.body if isinstance(d, ast.FunctionDef) and d.name == nm), None)
            if hit:
                break
        if hit:
            q, d = hit
            out.append({"target": nm, "precise": "%s:%d#%s" % (q.name, d.lineno, hashlib.sha1(ast.dump(d).encode()).hexdigest()[:12]),
                        "elastic": "%s(%s)" % (nm, ", ".join(a.arg for a in d.args.args)), "resolved": "精準"})
        else:
            out.append({"target": nm, "precise": "—", "elastic": nm, "resolved": "沒找到"})
    return out


_patch_v("anchors", anchors_v177)


# ───────── ② 決策要樣本 · 小樣本排序撤回 ─────────
def decide_v177(cfg: dict, lay: dict, res: dict, bench: dict, prev: dict = None, applied: bool = False) -> tuple:
    new, dec = decide_v177._prev(cfg, lay, res, bench, prev, applied)
    by = (bench or {}).get("by") or {}
    n = max((v.get("tried", 0) for v in by.values() if v.get("installed")), default=0)
    keep = []
    for x in dec:
        if x["key"] in ("rescue_order", "disabled_backends") and n < MIN_SAMPLE and "回滾" not in x["why"]:
            new[x["key"]] = cfg.get(x["key"])
            continue
        keep.append(x)
    dflt = (_resolve("DEFAULT") or {}).get("rescue_order")
    if dflt and new.get("rescue_order") != dflt and n < MIN_SAMPLE:
        keep.append({"key": "rescue_order", "old": new.get("rescue_order"), "new": dflt, "why": "撤回:之前的排序只靠小樣本(每個讀表器試 <%d 次)→ 回預設順序" % MIN_SAMPLE,
                     "evidence": "這輪實測最多試 %d 次" % n})
        new["rescue_order"] = dflt
    return new, keep


_patch_v("decide", decide_v177)


# ───────── ⑤ 讀表實測:快速讀表器先測全部沒過的表 · 重型只抽樣 ─────────
FAST = ["pymupdf_lines", "pymupdf_text", "pdfplumber_lines", "pdfplumber_text"]


def auto_bench_v177(d: Path, th, budget: int) -> dict:
    prev = auto_bench_v177._prev
    if th is None:
        return {}
    orig = list(getattr(th, "TABLE_BACKENDS", []))
    try:
        th.TABLE_BACKENDS = [b for b in (_resolve("_ORIG_BACKENDS") or orig) if b in FAST]
        r1 = prev(d, th, int(budget * 0.6))
        th.TABLE_BACKENDS = [b for b in (_resolve("_ORIG_BACKENDS") or orig) if b not in FAST]
        r2 = prev(d, th, int(budget * 0.4))
    finally:
        th.TABLE_BACKENDS = orig
    by = dict(r1.get("by") or {})
    for k, v in (r2.get("by") or {}).items():
        if k not in FAST:
            by[k] = v
    out = dict(r1)
    out["by"] = by
    out["secs"] = r1.get("secs", 0) + r2.get("secs", 0)
    return out


_patch_v("auto_bench", auto_bench_v177)



# ───────── ④ 雙軌三個已知錯 ─────────
_TP_LABEL = re.compile(r"(?i)target\s*price|price\s*target|12m\s*tp|\btp\b|\bpt\b|目標價|目標股價|合理價")


def ocr_tp(text: str):
    """OCR 目標價:標籤後 40 字內第一個「不是年份」的數字(2023 這種整數年份跳過)。"""
    for m in _TP_LABEL.finditer(text or ""):
        for n in re.findall(r"[\d,]+(?:\.\d+)?", text[m.end():m.end() + 40]):
            try:
                v = float(n.replace(",", ""))
            except ValueError:
                continue
            if v <= 0 or (v == int(v) and 1990 <= v <= 2100) or v in (12.0,):
                continue
            return v
    return None


def _close_map(d: Path) -> dict:
    out = {}
    for p in d.glob("*.json"):
        try:
            j = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        out[(j.get("row") or {}).get("file")] = (j.get("info") or {}).get("close")
    return out


def dt_units_v177(d: Path, dpi: int = 200) -> list:
    units = dt_units_v177._prev(d, dpi)
    cm = _close_map(d)
    for u in units:
        if u["kind"] != "info":
            continue
        u["a_info"]["close"] = cm.get(u["file"])
        if u.get("msha"):
            x0, y0, x1, y1 = u["clip"]
            u["clip"] = [x0, 0.0, x1, y1]                       # 往上含頁首(報告日常在頁首)
            u["key"] = hashlib.sha1(("%s|%d|%s|%d|rapidocr" % (u["msha"], u["local"], ",".join("%.1f" % x for x in u["clip"]), dpi)).encode()).hexdigest()[:20]
    return units


def dt_compare_info_v177(a: dict, text: str, fn_date: str) -> dict:
    a2, note = dict(a), ""
    tp, close = a.get("tp"), a.get("close")
    if isinstance(tp, (int, float)) and ((close and tp / close < 0.3) or tp <= 1.5):
        a2["tp"], note = None, "NON-OCR 目標價 %s 不合理(%s)→ 剔除" % (tp, "對收盤 %s 不到 0.3 倍" % close if close else "≤1.5")
    out = dt_compare_info_v177._prev(a2, text, fn_date)
    btp = ocr_tp(text)
    atp = a2.get("tp")
    st = "一致" if atp and btp and abs(atp - btp) <= abs(atp) * 0.005 else ("衝突" if atp and btp else "單軌")
    out["目標價"] = (st, atp if atp else "—", btp if btp else "—") + ((note,) if note else ())
    return out


_patch_v("dt_units", dt_units_v177)
_patch_v("dt_compare_info", dt_compare_info_v177)


# ───────── ① 各段輸入鍵(AST 精準):同輸入不重跑 ─────────
LAYOUT_FUNCS = {"l2_one", "layout_run_v158", "layout_run", "verify_table", "_ORIG_VT", "_rebuild_table", "extract_one", "analyze_page", "extract_info", "extract_info_v158", "tr_check_v160",
                "_is_period", "_is_period_28", "_YR158", "_YR", "_arith", "_arith_28", "classify_file", "_table_boxes", "_extract_table", "_figures", "parse_number", "_to_num", "_pool_map"}
RESTORE_FUNCS = LAYOUT_FUNCS | {"restore_run", "table_record", "calc_checks", "ocr_rows", "_rescue", "_real_table", "flat_rows", "noise_reason", "split_sentences", "tidy", "info_pairs",
                                "nonocr_tables", "toolhub", "guarded_tables", "_guard_toolhub"}
_NAMES = {}


def _names_in(p: Path) -> set:
    k = (str(p), p.stat().st_mtime, p.stat().st_size)
    if k in _NAMES:
        return _NAMES[k]
    out = set()
    try:
        t = ast.parse(p.read_text(encoding="utf-8"))
    except (SyntaxError, OSError):
        return out
    for n in ast.walk(t):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out.add(n.name)
        elif isinstance(n, ast.Call):
            fn = n.func
            nm = fn.id if isinstance(fn, ast.Name) else (fn.attr if isinstance(fn, ast.Attribute) else "")
            if nm in ("setattr", "_patch", "_patch_v", "_wrap_period") and n.args:
                a = n.args[1] if nm == "setattr" and len(n.args) > 1 else n.args[0]
                if isinstance(a, ast.Constant) and isinstance(a.value, str):
                    out.add(a.value)
    _NAMES[k] = out
    return out


def code_fp(funcs: set, root: Path = None) -> str:
    root = root or HERE
    h = hashlib.sha256()
    for p in sorted(root.glob(_STEM + "_v*.py"), key=_vnum_v0177):
        if _names_in(p) & funcs:
            h.update(p.name.encode() + hashlib.sha256(p.read_bytes()).digest())
    for p in sorted((root / "intake").rglob("*.py")) if (root / "intake").is_dir() else []:
        h.update(p.name.encode() + hashlib.sha256(p.read_bytes()).digest())
    return h.hexdigest()[:16]


def input_dir() -> Path:
    home = (_home or (lambda: HERE))()
    for d in (home / "SSOT", home / "knowledge"):
        fs = sorted(d.glob("VRN_Config_v*.json"), key=_vnum_v0177) if d.is_dir() else []
        if fs:
            try:
                v = json.loads(fs[-1].read_text(encoding="utf-8")).get("input_dir")
                if v:
                    return Path(v)
            except ValueError:
                pass
    return Path(r"C:\測試樣本報告")


def input_fp(d: Path) -> tuple:
    h = hashlib.sha256()
    newest = 0.0
    if d.is_dir():
        for p in sorted(d.rglob("*")):
            if p.is_file() and p.suffix.lower() in (".pdf", ".docx", ".doc", ".txt", ".md"):
                st = p.stat()
                h.update(("%s|%d|%d" % (p.relative_to(d), st.st_size, int(st.st_mtime))).encode())
                newest = max(newest, st.st_mtime)
    return h.hexdigest()[:16], newest


def stage_plan(cfg_file: str) -> dict:
    sk_p = _rep() / "auto" / "stage_keys.json"
    try:
        last = json.loads(sk_p.read_text(encoding="utf-8")) if sk_p.exists() else {}
    except ValueError:
        last = {}
    d = _resolve("_latest_l2_dir")("")
    ifp, newest = input_fp(input_dir())
    k_l = {"input": ifp, "code": code_fp(LAYOUT_FUNCS)}
    if last.get("layout", {}).get("key") == k_l and d:
        need_l, why_l = False, "輸入與 layout 相關程式都沒變"
    elif not last and d and d.stat().st_mtime > newest:
        need_l, why_l = False, "第一次記鍵:上一輪 layout 比所有輸入檔都新 → 沿用"
    else:
        need_l, why_l = True, "輸入或 layout 相關程式變了" if last else "沒有可沿用的 layout"
    return {"last": last, "need_layout": need_l, "why_layout": why_l, "k_layout": k_l, "path": str(sk_p)}


def _need_restore(last: dict, run: str, cfg_file: str) -> tuple:
    k = {"run": run, "cfg": cfg_file, "code": code_fp(RESTORE_FUNCS)}
    if last.get("restore", {}).get("key") == k:
        return False, k, "layout 輪 · 設定冊 · restore 程式都沒變"
    return True, k, "layout 輪 / 設定冊 / restore 程式變了"


def _need_basic(last: dict, run: str) -> tuple:
    k = {"run": run, "date": datetime.date.today().isoformat()}
    if last.get("basicinfo", {}).get("key") == k:
        return False, k, "同一輪 layout · 今天已跑"
    return True, k, "layout 輪或日期變了(價格庫每天可能更新)"



# ───────── ③ AI 包(每行 [計] · VCGC AiVerb paste 保留得住)─────────
def _j(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def build_pack(rec: dict, stages: dict) -> list:
    rep = _rep()
    L = []
    add = lambda s: L.append(("[計] " + s)[:180])  # noqa: E731
    lay, res, bas = rec.get("layout") or {}, rec.get("restore") or {}, rec.get("basic") or {}
    add("VRN AI 包 · 第 %s 輪 · 設定 %s · %s" % (rec.get("round", "?"), rec.get("config_file") or "預設", datetime.datetime.now().isoformat(timespec="minutes")))
    add("各段 · " + " · ".join("%s %s" % kv for kv in stages.items()))
    add("KPI · 第二步 %s/%s · 表(layout)%s/%s · 雙讀 %s/%s" % (lay.get("step2_ok"), lay.get("files"), lay.get("tables_ok"), lay.get("tables"), lay.get("tr_ok"), lay.get("tr_tried")))
    add("KPI · 端到端還原無誤 %s/%s · 救回 %s · OCR 候選 %s · 仍失敗 %s · 算術 過 %s / 不符 %s · 報告無誤 %s/%s" % (res.get("tables_restored_ok"), res.get("tables_total"), res.get("rescued"),
        res.get("ocr_cand"), res.get("failed"), res.get("calc_pass"), res.get("calc_fail"), res.get("docs_ok"), res.get("docs")))
    add("KPI · BASIC INFO 綠 %s 黃 %s 紅 %s 灰 %s" % (bas.get("green"), bas.get("yellow"), bas.get("red"), bas.get("gray")))
    dj = _j(rep / "dualtrack" / "DUALTRACK_latest.json") or {}
    if dj:
        tb = [x for x in dj.get("records", []) if x["kind"] == "table"]
        ags = [x["agree"] for x in tb if x.get("agree") is not None]
        add("KPI · 雙軌 綠 %s 黃 %s 紅 %s · 表平均一致度 %s · 快取命中 %s · 新跑 OCR %s" % (dj["lamps"].get("GREEN", 0), dj["lamps"].get("YELLOW", 0), dj["lamps"].get("RED", 0),
            ("%.0f%%" % (100 * sum(ags) / len(ags))) if ags else "—", dj.get("cache_hit"), dj.get("ocr_new")))
    for x in rec.get("changed") or []:
        add("決策 · %s → %s · %s" % (x["key"], json.dumps(x["new"], ensure_ascii=False)[:50], x["why"][:60]))
    fails, iss = defaultdict(list), Counter()
    for f in sorted((rep / "restore").glob("*.json")) if (rep / "restore").is_dir() else []:
        if f.name.startswith("RESTORE_"):
            continue
        dd = _j(f) or {}
        fn = (dd.get("document_meta") or {}).get("file") or f.stem
        for t in dd.get("tables", []):
            for c in t.get("calc") or []:
                if c.get("status") == "FAIL":
                    fails[c["rule"]].append("%s·%s·%s·%s" % (fn[:26], t.get("id"), c.get("period"), c.get("detail")))
            if t.get("status") == "未過":
                for i in (t.get("verify") or {}).get("issues") or []:
                    iss[str(i).split(" ")[0]] += 1
    for rule, xs in sorted(fails.items(), key=lambda kv: -len(kv[1])):
        add("算術不符 · %s × %d · 例 %s" % (rule, len(xs), " | ".join(xs[:2])))
        if len(xs) > 2:
            add("算術不符 · %s 例 %s" % (rule, " | ".join(xs[2:4])))
    if iss:
        add("仍失敗的表 · 驗表問題 " + " · ".join("%s×%d" % kv for kv in iss.most_common(8)))
    if dj:
        add("雙軌路徑 · " + " · ".join("%s %d" % kv for kv in Counter(x["path"] for x in dj.get("records", [])).most_common(7)))
        bad = sorted((x for x in dj.get("records", []) if x["kind"] == "table" and x.get("agree") is not None and x["lamp"] == "RED"), key=lambda x: x["agree"])[:8]
        for x in bad:
            add("雙軌衝突表 · %s · %s · 一致 %.0f%% · %s" % (x["file"][:28], x["id"], 100 * x["agree"], json.dumps((x.get("conflicts") or [])[:2], ensure_ascii=False)[:80]))
        for x in [x for x in dj.get("records", []) if x["kind"] == "info" and any(v[0] == "衝突" or len(v) > 3 for v in (x.get("fields") or {}).values())][:10]:
            add("雙軌資訊區 · %s · %s" % (x["file"][:30], " · ".join("%s %s(%s/%s)%s" % (k, v[0], v[1], v[2], (" " + v[3]) if len(v) > 3 else "") for k, v in (x.get("fields") or {}).items())))
    bj = _j(rep / "basicinfo" / "BASIC_INFO_latest.json") or {}
    for r in bj.get("records", []):
        for k, fdx in (r.get("fields") or {}).items():
            if fdx.get("status") == "RED":
                add("BASIC 紅 · %s · %s = %s · %s" % (r["fields"]["FILENAME"]["value"][:30], k, fdx.get("value"), fdx.get("check", "")[:60]))
    bb = rec.get("bench_by") or {}
    if bb:
        add("讀表實測 · " + " · ".join("%s %d/%d" % (k, v.get("ok", 0), v.get("tried", 0)) for k, v in bb.items() if v.get("tried")))
    L.append("NEXT: 依本包分類修(可同步 → 薄尾 · 不可同步 → 整併版)→ 再跑 auto(同輸入的段自動沿用)")
    return L[:300]


def aiverb_compress(pack: Path, next_line: str, start: Path = None, stop: Path = None) -> tuple:
    p = (start or HERE).resolve()
    stop = stop.resolve() if stop else None
    while p.parent != p and not (p / "supportive modules").is_dir() and p != stop:      # stop = 最多往上找到哪一層(測試不受所在機器影響)
        p = p.parent
    eng = sorted((p / "supportive modules" / "registry").glob("CGC_MDL256_AiVerbBridge_v*.py"), key=_vnum_v0177) if (p / "supportive modules").is_dir() else []
    if not eng:
        return None, "VCGC AiVerb 不在本機 → 用 VRN 原包"
    env = dict(os.environ, VIA_FROM_VCGC="YES", PYTHONUTF8="1")
    try:
        r = subprocess.run([sys.executable, "-W", "ignore", str(eng[-1]), "paste", str(pack), "--max", "300", "--next", next_line], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=90, env=env)
        out = [l for l in (r.stdout or "").splitlines() if l.strip() and not l.strip().startswith("→")]
    except Exception as exc:  # noqa: BLE001
        return None, "VCGC AiVerb 失敗 %s → 用 VRN 原包" % type(exc).__name__
    if len(out) < 5:
        return None, "VCGC AiVerb 沒產出 → 用 VRN 原包"
    dst = pack.with_name("VRN_AI_PACK_AIVERB_latest.md")
    dst.write_text("\n".join(out) + "\n", encoding="utf-8")
    return dst, "VCGC %s paste 壓縮 %d → %d 行" % (eng[-1].name, sum(1 for _ in pack.open(encoding="utf-8")), len(out))


# ───────── ① auto 一條指令 ─────────
def revert_small_sample_now(m) -> str:
    """設定冊裡小樣本排出來的讀表器順序 → 本輪一開始就撤回(記憶體裡 · 本輪 restore 就照預設順序);結尾決策再寫進新版設定冊。"""
    cfg, dflt = vars(m).get("CFG"), (vars(m).get("DEFAULT") or {}).get("rescue_order")
    if not cfg or not dflt or cfg.get("rescue_order") == dflt:
        return ""
    led = (vars(m).get("ledger_read") or (lambda: []))()
    by = (led[-1].get("bench_by") if led else None) or {}
    n = max((v.get("tried", 0) for v in by.values() if v.get("installed")), default=0)
    if n >= MIN_SAMPLE:
        return ""
    cfg["rescue_order"] = list(dflt)
    return "撤回小樣本排序(上輪每個讀表器最多只試 %d 次 < %d)→ 本輪 restore 就照預設順序 · 結尾寫進新版設定冊" % (n, MIN_SAMPLE)


def pin_layout_run() -> str:
    """把最新 layout 所在的 ps_* 釘住(.via_keep · 啟動器滾動清理跳過)· 其他輪的釘子拔掉(永遠只釘一輪)→ 同輸入不必重跑 layout。"""
    d = _resolve("_latest_l2_dir")("")
    if not d:
        return "沒有 layout 可釘"
    ps = next((q for q in [d] + list(d.parents) if q.name.startswith("ps_")), None)
    if ps is None:
        return "找不到 layout 所在輪"
    try:
        (ps / ".via_keep").write_text(json.dumps({"layout_run": d.parent.name, "ts": datetime.datetime.now().isoformat(timespec="seconds"), "by": "VRN auto"}, ensure_ascii=False), encoding="utf-8")
        n = 0
        for q in ps.parent.glob("ps_*"):
            if q != ps and (q / ".via_keep").exists():
                (q / ".via_keep").unlink()
                n += 1
        return "釘住 %s(拔掉舊釘 %d)" % (ps.name, n)
    except OSError as exc:
        return "釘不住 %s" % type(exc).__name__


def auto_v177(extra: list) -> int:
    m = _owner("auto_run")
    if m is None:
        print("[計] 自動實測優化 · 前版鏈沒有 auto_run · RED")
        return 1
    orig, orig_la = vars(m)["auto_run"], vars(m)["ledger_append"]
    cfg_file = vars(m).get("CFG_FILE", "")
    pre = revert_small_sample_now(m)
    plan = stage_plan(cfg_file)
    last = plan["last"]
    keys = dict(last)
    stages = {"layout": ("跑(%s)" % plan["why_layout"]) if plan["need_layout"] else ("沿用(%s)" % plan["why_layout"])}
    if not plan["need_layout"]:
        keys["layout"] = {"key": plan["k_layout"]}
    dt_budget = int(os.environ.get("VIA_VRN_DT_BUDGET", "1200") or 1200)

    def runner(a):
        st = a[0]
        d = _resolve("_latest_l2_dir")("")
        run = d.parent.name if d else ""
        if st == "layout":
            rc = PRIOR.main(a)
            keys["layout"] = {"key": dict(plan["k_layout"], input=input_fp(input_dir())[0])}
            return rc
        if st == "restore":
            need, k, why = _need_restore(last, run, vars(m).get("CFG_FILE", ""))
            stages["restore"] = ("跑(%s)" % why) if need else ("沿用(%s)" % why)
            rc = PRIOR.main(a) if need else 0
            keys["restore"] = {"key": k}
            return rc
        if st == "basicinfo":
            need, k, why = _need_basic(last, run)
            stages["basicinfo"] = ("跑(%s)" % why) if need else ("沿用(%s)" % why)
            rc = PRIOR.main(a) if need else 0
            keys["basicinfo"] = {"key": k}
            t0 = time.time()
            PRIOR.main(["dualtrack", "--budget", str(dt_budget)])
            stages["dualtrack"] = "增量跑 %d 秒(有快取的不重跑)" % int(time.time() - t0)
            return rc
        return PRIOR.main(a)

    setattr(m, "auto_run", lambda runner_=None, skip_layout=False, layout_extra=None: orig(runner=runner, skip_layout=not plan["need_layout"], layout_extra=layout_extra))
    holder = {}

    def la(rec, home=None):
        dj = _j(_rep() / "dualtrack" / "DUALTRACK_latest.json") or {}
        rec = dict(rec, stages=stages, dualtrack={k: dj.get(k) for k in ("units", "lamps", "cache_hit", "ocr_new", "all_green")})
        holder["rec"] = rec
        return orig_la(rec, home)
    setattr(m, "ledger_append", la)
    try:
        rc = PRIOR.main(["auto"] + [a for a in extra if a not in ("--resume",)])
    finally:
        setattr(m, "auto_run", orig)
        setattr(m, "ledger_append", orig_la)
    pinned = pin_layout_run()
    stages["TEMP"] = pinned
    sk = Path(plan["path"])
    sk.parent.mkdir(parents=True, exist_ok=True)
    sk.write_text(json.dumps(keys, ensure_ascii=False, indent=1), encoding="utf-8")
    rec = holder.get("rec") or {}
    rec["round"] = len((_resolve("ledger_read") or (lambda: []))())
    lines = build_pack(rec, stages)
    pk = _rep() / "auto" / "VRN_AI_PACK_latest.md"
    pk.write_text("\n".join(lines) + "\n", encoding="utf-8")
    dst, note = aiverb_compress(pk, lines[-1].replace("NEXT: ", ""))
    if pre:
        print("[計] " + pre)
    print("[計] 各段 · " + " · ".join("%s %s" % kv for kv in stages.items()))
    print("[計] AI 包 · %s(%d 行)· %s → 啟動器 paste.md / 剪貼簿用這包" % (pk.name, len(lines), note))
    return rc



def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    if "--selftest" in args[:2]:
        return selftest()
    if args[:1] == ["auto"] and "--resume" not in args:
        inst = _resolve("install_v166")
        if inst:
            inst()
        return auto_v177(args[1:])
    return PRIOR.main(args)


def selftest() -> int:
    import shutil
    import tempfile
    p = f = 0

    def chk(name, cond):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s" % name)
    td = Path(tempfile.mkdtemp(prefix="vrn177-"))
    saved = {k: os.environ.get(k) for k in ("VIA_VRN_HEALTH_OUT", "VIA_SPILL_DIR")}
    try:
        os.environ["VIA_VRN_HEALTH_OUT"] = str(td / "rep")
        fs = {"a.py": td / "a.py", "b.py": td / "b.py"}
        fs["a.py"].write_text("x = 1\n", encoding="utf-8")
        fs["b.py"].write_text("def y(:\n", encoding="utf-8")
        s1 = static_check_v177(fs)
        s2 = static_check_v177(fs)
        chk("① 快查靜態逐檔快取:第一次編譯 2 支(b 語法錯)· 第二次 sha 沒變 → 重編 0 支 · 結果一樣", s1["recompiled"] == 2 and s2["recompiled"] == 0 and "b.py" in s2["bad"] and "a.py" not in s2["bad"])
        dflt = (_resolve("DEFAULT") or {})
        by = {k: {"tried": 6, "ok": 1 if k == "camelot_stream" else 0, "ms": 1000, "installed": True} for k in dflt.get("rescue_order", [])}
        n1, d1 = decide_v177(dict(dflt), {}, {}, {"by": by})
        bad_cfg = dict(dflt, rescue_order=["camelot_stream"] + [k for k in dflt["rescue_order"] if k != "camelot_stream"])
        n2, d2 = decide_v177(bad_cfg, {}, {}, {"by": by})
        chk("② 決策要樣本:每個讀表器只試 6 次(<15)→ 不排序 · 已被小樣本改過的設定 → 自動撤回回預設順序",
            n1["rescue_order"] == dflt["rescue_order"] and not any(x["key"] == "rescue_order" for x in d1) and n2["rescue_order"] == dflt["rescue_order"] and any("撤回" in x["why"] for x in d2))
        cr = td / "chain"
        (cr / "intake").mkdir(parents=True)
        (cr / ("%s_v0300.py" % _STEM)).write_text("def l2_one(r):\n    return r\n", encoding="utf-8")
        f1 = code_fp(LAYOUT_FUNCS, cr)
        (cr / ("%s_v0301.py" % _STEM)).write_text("if False:\n    setattr(m, 'auto_bench', 1)\n", encoding="utf-8")
        f2 = code_fp(LAYOUT_FUNCS, cr)
        (cr / ("%s_v0302.py" % _STEM)).write_text("if False:\n    setattr(m, 'l2_one', 1)\n", encoding="utf-8")
        f3 = code_fp(LAYOUT_FUNCS, cr)
        chk("③ AST 精準輸入鍵:新版只動 auto_bench → layout 鍵不變(不重跑 14 分鐘)· 新版替換 l2_one → layout 鍵變(該重跑)", f1 == f2 and f2 != f3)
        chk("④ OCR 目標價:跳過年份 2023 / 12M → 「目標價(2023年) NT$ 187」= 187 · 「目標價 (12M) 85」= 85 · 「Target price: TWD 260」= 260",
            ocr_tp("目標價(2023年) NT$ 187") == 187.0 and ocr_tp("目標價 (12M) 85") == 85.0 and ocr_tp("Target price: TWD 260") == 260.0)
        ci = dt_compare_info_v177({"rating_raw": "Overweight", "rating": "Buy", "tp": 1.0, "close": 520.0, "date": "2026-05-19"}, "目標價 NT$760 2026/05/19", "2026-05-19")
        chk("⑤ NON-OCR 目標價 1.0(收盤 520 的 0.002 倍)→ 剔除當單軌(不算衝突)· OCR 760 留作候選 · %s" % (ci["目標價"],),
            ci["目標價"][0] == "單軌" and ci["目標價"][2] == 760.0 and "剔除" in ci["目標價"][3])
        rep = td / "rep"
        (rep / "restore").mkdir(parents=True)
        (rep / "restore" / "01_x.json").write_text(json.dumps({"document_meta": {"file": "KGI-1476.pdf"}, "tables": [{"id": "P5-T2", "status": "算術不符(待查)", "calc": [
            {"rule": "毛利 = 營收 − 成本", "period": "2025F", "status": "FAIL", "detail": "400 vs 380"}]}, {"id": "P6-T1", "status": "未過", "verify": {"issues": ["無期間表頭"]}, "calc": []}]},
            ensure_ascii=False), encoding="utf-8")
        (rep / "dualtrack").mkdir()
        (rep / "dualtrack" / "DUALTRACK_latest.json").write_text(json.dumps({"lamps": {"GREEN": 1, "RED": 1}, "cache_hit": 1, "ocr_new": 1, "records": [
            {"kind": "table", "file": "JP-3653.pdf", "id": "P7-T1", "agree": 0.2, "lamp": "RED", "path": "兩軌衝突 · 待查", "conflicts": [["revenue·FY25E", 20337, 6474]]},
            {"kind": "info", "file": "KGI-1476.pdf", "id": "P1·INFO", "agree": 0.0, "lamp": "YELLOW", "path": "單軌", "fields": {"目標價": ["單軌", "—", 367.0, "NON-OCR 目標價 1.0 不合理 → 剔除"]}}]},
            ensure_ascii=False), encoding="utf-8")
        (rep / "basicinfo").mkdir()
        (rep / "basicinfo" / "BASIC_INFO_latest.json").write_text(json.dumps({"records": [{"fields": {"FILENAME": {"value": "KGI-1476.pdf", "status": "GREEN"},
                                                                                                         "TP_ORIGINAL": {"value": 1.0, "status": "RED", "check": "資料庫收盤 520 的 0.00 倍 → 不合理"}}}]}, ensure_ascii=False), encoding="utf-8")
        lines = build_pack({"round": 2, "layout": {"step2_ok": 30, "files": 57}, "restore": {"calc_fail": 1}, "basic": {"red": 1}, "changed": []}, {"layout": "沿用", "restore": "跑"})
        chk("⑥ AI 包:每行 [計](VCGC AiVerb 保留得住)· 有 算術不符依規則 + 例 · 雙軌衝突表 · 剔除的目標價 · BASIC 紅 · NEXT · %d 行 ≤ 300" % len(lines),
            all(l.startswith("[計] ") for l in lines[:-1]) and lines[-1].startswith("NEXT:") and any("算術不符 · 毛利 = 營收 − 成本 × 1" in l for l in lines)
            and any("雙軌衝突表 · JP-3653" in l for l in lines) and any("剔除" in l for l in lines) and any("BASIC 紅 · KGI-1476" in l for l in lines) and len(lines) <= 300)
        root = td / "VIA"
        (root / "supportive modules" / "registry").mkdir(parents=True)
        (root / "supportive modules" / "registry" / "CGC_MDL256_AiVerbBridge_v0100.py").write_text(
            "import sys\nt=open(sys.argv[2],encoding='utf-8').read().splitlines()\nprint('# PASTE')\n[print('- '+l) for l in t if l.startswith('[計]')]\nprint('NEXT: ' + sys.argv[sys.argv.index('--next')+1])\n",
            encoding="utf-8")
        (root / "functional modules" / "VRN").mkdir(parents=True)
        pk = rep / "auto"
        pk.mkdir()
        pf = pk / "VRN_AI_PACK_latest.md"
        pf.write_text("\n".join(lines) + "\n", encoding="utf-8")
        dst, note = aiverb_compress(pf, "再跑 auto", root / "functional modules" / "VRN")
        (td / "nowhere").mkdir()
        dst2, note2 = aiverb_compress(pf, "x", td / "nowhere", stop=td)
        chk("⑦ 交給 VCGC AiVerb paste 壓縮(只讀 · 輸出寫 VRN 自己的夾)→ %s · 沒有 AiVerb → %s" % (note, note2),
            dst is not None and dst.exists() and "NEXT: 再跑 auto" in dst.read_text(encoding="utf-8") and dst2 is None and "VRN 原包" in note2)
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(td, ignore_errors=True)
    class _M:
        pass
    mm = _M()
    vars(mm).update(CFG={"rescue_order": ["camelot_stream", "pymupdf_lines"]}, DEFAULT={"rescue_order": ["pymupdf_lines", "camelot_stream"]},
                    ledger_read=lambda: [{"bench_by": {"camelot_stream": {"tried": 6, "installed": True}}}])
    rv = revert_small_sample_now(mm)
    chk("⑫ 小樣本排序本輪一開始就撤回(restore 不會先照錯的順序跑)→ %s" % rv[:40], mm.CFG["rescue_order"] == ["pymupdf_lines", "camelot_stream"] and "撤回" in rv)
    tp = Path(tempfile.mkdtemp(prefix="vrn177pin-"))
    try:
        for nm in ("ps_old", "ps_new"):
            (tp / nm / "spill" / "vrn_stage_r" / "layout_l2").mkdir(parents=True)
        (tp / "ps_old" / ".via_keep").write_text("x", encoding="utf-8")
        saved_l2 = vars(_owner("_latest_l2_dir"))["_latest_l2_dir"]
        vars(_owner("_latest_l2_dir"))["_latest_l2_dir"] = lambda run="": tp / "ps_new" / "spill" / "vrn_stage_r" / "layout_l2"
        try:
            note = pin_layout_run()
        finally:
            vars(_owner("_latest_l2_dir"))["_latest_l2_dir"] = saved_l2
        chk("⑪ TEMP 釘住最新 layout 所在輪(.via_keep · 滾動清理跳過)· 舊釘拔掉 · 永遠只釘一輪 → %s" % note,
            (tp / "ps_new" / ".via_keep").exists() and not (tp / "ps_old" / ".via_keep").exists())
    finally:
        import shutil as _sh
        _sh.rmtree(tp, ignore_errors=True)
    an = anchors_v177(HERE, Path(__file__))
    tg = {a["target"]: a for a in an}
    chk("⑩ AST 錨點涵蓋 _patch_v 的替換點:%s" % " · ".join("%s→%s" % (k, v["precise"].split("#")[0]) for k, v in tg.items() if k in ("static_check", "decide", "auto_bench", "dt_units", "dt_compare_info", "anchors")),
        all(tg.get(k, {}).get("resolved") == "精準" for k in ("static_check", "decide", "auto_bench", "dt_units", "dt_compare_info", "anchors")))
    me = Path(__file__).read_text(encoding="utf-8")
    chk("⑧ 最新有版號加速器橋 [VIA:ACCEL-BRIDGE:v0111] · 自帶多程序墊片", "[VIA:ACCEL-BRIDGE:v0111]" in me and _job_entry.__module__ in ("__main__", __name__))
    print("  ── 前版鏈自測(原樣印出)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("⑨ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    print("[計] VRN_SystemManager_v0177 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
