#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0174 — 薄尾(操作員 2026-10-11「自動實測優化整個流程」)。
  auto 動詞(一條指令):實跑 layout → restore → basicinfo → 讀表工具實測 → 量 KPI → 依實測決策 → 寫新版調校設定(下一輪生效)→ 跟上一輪比 · 變差自動回滾
  決策(保守 · 有門檻才動 · 每條附證據):
    ① 原生救回順序:讀表器依實測救回率排序 · 試 ≥15 次 0 救回 → 停用(至少留 2 個)
    ② 雙讀(TableRepair,每張約 6 秒):它救回的表快速讀表器也救得回 ≥90%,或它自己救回率 <10% → 關(restore 原生救回接手 · 品質不降)
    ③ 擷取後復健:修好 + 改回正文 <3% → 關
    ④ 預算:救回 / OCR 預算用完還有表沒試完 → 放寬 ×1.5(上限)
    ⑤ 回滾:上一輪改了設定,這一輪端到端成果變差 → 退回上一版設定
  設定冊 knowledge\\VRN_AutoTune_Config_v####.json(內容沒變不出新版)· 台帳 knowledge\\VRN_AutoTune_Ledger.jsonl(只增不減)
  layout / restore / basicinfo 單獨跑也套同一份設定(並印出生效設定 · 透明)
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
import time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"
TAG = "v0174"


def _vnum_v0174(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0174(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0174(p) < _vnum_v0174(__file__)), key=_vnum_v0174)
PRIOR = _load_v0174(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


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
FAST = ["pymupdf_lines", "pymupdf_text", "pdfplumber_lines", "pdfplumber_text"]
DEFAULT = {"rescue_order": ["pymupdf_lines", "pymupdf_text", "pdfplumber_lines", "pdfplumber_text", "camelot_lattice", "camelot_stream", "tabula_lattice", "tabula_stream", "img2table"],
           "disabled_backends": [], "tr_dual": "on", "postextract": "on", "rescue_budget": 600, "ocr_budget": 300, "ocr_dpi": 200, "basic_ocr_budget": 180, "bench_budget": 300}
CAP = {"rescue_budget": 1500, "ocr_budget": 900, "basic_ocr_budget": 600}


# ───────── 設定冊(版本化 SSOT)· 台帳(只增不減)─────────
def cfg_files(home: Path = None) -> list:
    home = home or _home()
    return sorted((home / "knowledge").glob("VRN_AutoTune_Config_v*.json"), key=_vnum_v0174)


def load_cfg(home: Path = None) -> tuple:
    fs = cfg_files(home)
    if not fs:
        return dict(DEFAULT), ""
    try:
        d = json.loads(fs[-1].read_text(encoding="utf-8"))
        return dict(DEFAULT, **(d.get("config") or {})), fs[-1].name
    except (OSError, ValueError):
        return dict(DEFAULT), ""


def save_cfg(cfg: dict, decisions: list, home: Path = None) -> str:
    home = home or _home()
    fs = cfg_files(home)
    cur, _ = load_cfg(home)
    if fs and cur == cfg:
        return ""
    nv = "v%04d" % ((_vnum_v0174(fs[-1]) + 1) if fs else 100)
    p = home / "knowledge" / ("VRN_AutoTune_Config_%s.json" % nv)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"schema": "VIA.VRN.AutoTune.v1", "version": nv, "prior": fs[-1].name if fs else "", "ts": datetime.datetime.now().isoformat(timespec="seconds"),
                             "rule": "auto 依實測決策 · 有門檻才動 · 變差自動回滾;layout / restore / basicinfo 都套", "config": cfg, "decisions": decisions}, ensure_ascii=False, indent=1), encoding="utf-8")
    return p.name


def ledger_path(home: Path = None) -> Path:
    return (home or _home()) / "knowledge" / "VRN_AutoTune_Ledger.jsonl"


def ledger_read(home: Path = None) -> list:
    p = ledger_path(home)
    out = []
    if p.exists():
        for ln in p.read_text(encoding="utf-8").splitlines():
            try:
                out.append(json.loads(ln))
            except ValueError:
                continue
    return out


def ledger_append(rec: dict, home: Path = None) -> None:
    p = ledger_path(home)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")


# ───────── 套設定(import 時 · 子程序也套)─────────
CFG, CFG_FILE = load_cfg()
if CFG.get("postextract") == "off":
    os.environ["VIA_VRN_POSTEXTRACT_OFF"] = "1"
_PREV_TR = _resolve("tr_check_v160")


def tr_check_v174(*a, **k):
    if CFG.get("tr_dual") == "off":
        return None
    return _PREV_TR(*a, **k) if _PREV_TR else None


_mtr = _owner("tr_check_v160")
if _mtr is not None:
    setattr(_mtr, "tr_check_v160", tr_check_v174)
_PREV_TH = _resolve("toolhub")
_ORIG_BACKENDS = []


def toolhub_v174():
    m = _PREV_TH() if _PREV_TH else None
    if m is not None:
        if not _ORIG_BACKENDS:
            _ORIG_BACKENDS.extend(m.TABLE_BACKENDS)
        order = [b for b in CFG.get("rescue_order", []) if b in _ORIG_BACKENDS and b not in CFG.get("disabled_backends", [])]
        order += [b for b in _ORIG_BACKENDS if b not in order and b not in CFG.get("disabled_backends", [])]
        m.TABLE_BACKENDS = order
    return m


_mth = _owner("toolhub")
if _mth is not None:
    setattr(_mth, "toolhub", toolhub_v174)
_PREV_L2 = _resolve("l2_one")


def l2_one_v174(row: dict) -> dict:
    r = _PREV_L2(row)
    if isinstance(r, dict) and CFG.get("tr_dual") == "off":
        for t in r.get("tools", []) or []:
            t["tool"] = t.get("tool", "").replace("→ 雙讀(TableRepair)", "→ 雙讀關閉(自動調校)")
    return r


_ml2 = _owner("l2_one")
if _ml2 is not None:
    setattr(_ml2, "l2_one", l2_one_v174)
_LAST = {}
_PREV_LR = _resolve("layout_run_v158")


def layout_run_v174(d, opts):
    o = _PREV_LR(d, opts)
    _LAST["layout_rows"] = o.get("rows") or []
    return o


_mlr = _owner("layout_run_v158")
if _mlr is not None:
    setattr(_mlr, "layout_run_v158", layout_run_v174)


def cfg_line() -> str:
    return "[計] 自動調校設定 %s · 雙讀 %s · 擷取後復健 %s · 原生救回順序 %s%s · 預算 救回 %d 秒 / OCR %d 秒 / BASIC OCR %d 秒" % (
        CFG_FILE or "(預設 · 還沒調過)", CFG["tr_dual"], CFG["postextract"], ">".join(b for b in CFG["rescue_order"] if b not in CFG["disabled_backends"])[:120],
        (" · 停用 " + ",".join(CFG["disabled_backends"])) if CFG["disabled_backends"] else "", CFG["rescue_budget"], CFG["ocr_budget"], CFG["basic_ocr_budget"])


# ───────── KPI ─────────
def kpi_layout(d: Path, rows_live: list) -> dict:
    k = Counter()
    tr_ms = 0
    for p in sorted(d.glob("*.json")) if d else []:
        try:
            s = (json.loads(p.read_text(encoding="utf-8")).get("summary") or {})
        except (OSError, ValueError):
            continue
        k["files"] += 1
        k["step2_ok"] += 1 if (s.get("text_ok") and s.get("table_ok")) else 0
        k["tables"] += s.get("tables", 0)
        k["tables_ok"] += s.get("tables_ok", 0)
        k["secs"] += s.get("secs") or 0
        for t in s.get("tools") or []:
            if "雙讀(TableRepair)" in t.get("tool", ""):
                k["tr_tried"] += 1
                k["tr_ok"] += 1 if t.get("ok") else 0
                tr_ms += t.get("ms", 0)
        for iss, n in (s.get("verify_issues") or {}).items():
            k["issue:" + iss.split(" ")[0]] += n
    for r in rows_live or []:
        pe = r.get("pe") or {}
        for kk in ("tried", "fixed", "text"):
            k["pe_" + kk] += pe.get(kk, 0)
        k["pe_ms"] += pe.get("ms", 0)
    k["tr_ms_avg"] = tr_ms // max(k["tr_tried"], 1)
    return dict(k)


def kpi_restore(rep: Path) -> dict:
    p = rep / "restore" / "RESTORE_SUMMARY_latest.json"
    if not p.exists():
        return {}
    s = json.loads(p.read_text(encoding="utf-8"))
    c = s.get("counts") or {}
    ok_tables = 0
    flat_ok = 0
    for f in (rep / "restore").glob("*.json"):
        if f.name.startswith("RESTORE_"):
            continue
        try:
            dj = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for t in dj.get("tables", []):
            ok_tables += 1 if t.get("status") == "還原無誤" else 0
            flat_ok += 1 if t.get("status") == "還原無誤" and str(t.get("method", "")).startswith("文中表格") else 0
    tot = sum(c.get(k, 0) for k in ("t_native", "t_reverify", "t_rescued", "t_ocr", "t_fail")) + c.get("flat_tables", 0)
    return {"docs": s.get("docs", 0), "docs_ok": s.get("docs_ok", 0), "tables_total": tot, "tables_restored_ok": ok_tables, "native": c.get("t_native", 0), "reverify": c.get("t_reverify", 0),
            "rescued": c.get("t_rescued", 0), "flat": c.get("flat_tables", 0), "flat_ok": flat_ok, "ocr_cand": c.get("t_ocr", 0), "failed": c.get("t_fail", 0),
            "calc_pass": (s.get("calc") or {}).get("PASS", 0), "calc_fail": (s.get("calc") or {}).get("FAIL", 0), "rescue_secs": s.get("rescue_secs", 0), "ocr_secs": s.get("ocr_secs", 0),
            "rescued_by": s.get("rescued_by") or {}, "sentences": c.get("sentence", 0), "dropped": sum((s.get("dropped") or {}).values())}


def kpi_basic(rep: Path) -> dict:
    p = rep / "basicinfo" / "BASIC_INFO_latest.json"
    if not p.exists():
        return {}
    d = json.loads(p.read_text(encoding="utf-8"))
    c = Counter(f["status"] for r in d.get("records", []) for f in r["fields"].values())
    red = Counter(k for r in d.get("records", []) for k, f in r["fields"].items() if f["status"] == "RED")
    return {"docs": len(d.get("records", [])), "green": c.get("GREEN", 0), "yellow": c.get("YELLOW", 0), "red": c.get("RED", 0), "gray": c.get("GRAY", 0), "red_fields": dict(red),
            "ocr_docs": sum(1 for r in d.get("records", []) if r.get("stage") == "NON-OCR + OCR")}


# ───────── 讀表工具實測(沒過的財務表 · 雙讀救回的表)─────────
def auto_bench(d: Path, th, budget: int) -> dict:
    vt = _resolve("_ORIG_VT") or _resolve("verify_table")
    real = _resolve("_real_table") or (lambda rows, v: True)
    failed, trset = [], []
    for p in sorted(d.glob("*.json")) if d else []:
        try:
            j = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        row = j.get("row") or {}
        picked = list(row.get("picked") or [])
        if not row.get("mini") or not Path(row["mini"]).exists():
            continue
        for pi, pg in enumerate(j.get("pages", [])):
            orig = int(pg.get("page") or pi + 1)
            local = (picked.index(orig) + 1) if orig in picked else pi + 1
            for b in pg.get("blocks", []):
                if b.get("kind") != "table" or not str(b.get("sub", "")).startswith(("財務表", "估值表")):
                    continue
                v = b.get("verify") or {}
                if "TableRepair" in str(b.get("engine", "")) or str(v.get("native", "")).startswith("雙讀一致"):
                    trset.append((row["mini"], local, b))
                elif not v.get("ok"):
                    failed.append((row["mini"], local, b))
    backs = list(_ORIG_BACKENDS or getattr(th, "TABLE_BACKENDS", []))
    pr = {r["id"]: r["status"] for r in th.probe_tools()}
    tool_of = lambda k: {"pymupdf": "pymupdf", "pdfplumber": "pdfplumber", "camelot": "camelot", "tabula": "tabula", "img2table": "img2table"}[k.split("_")[0]]  # noqa: E731
    by = {k: {"tried": 0, "ok": 0, "ms": 0, "installed": pr.get(tool_of(k)) == "ok"} for k in backs}
    import pdfplumber  # noqa: WPS433
    t0 = time.time()

    def one(mini, local, b, ks):
        hit = []
        bb = [float(b["x0"]) - 3, max(0.0, float(b["top"]) - 42), float(b["x1"]) + 3, float(b["bottom"]) + 3]
        with pdfplumber.open(mini) as pdf:
            pp = pdf.pages[local - 1]
            for kk in ks:
                if not by[kk]["installed"] or time.time() - t0 > budget:
                    continue
                r = th.nonocr_tables(mini, local, bb, kk)
                by[kk]["tried"] += 1
                by[kk]["ms"] += r.get("ms", 0)
                best, bov = None, -1.0
                for t in (r.get("tables") or []) if r.get("status") == "ok" else []:
                    tb = t.get("bbox") or bb
                    ov = max(0.0, min(tb[2], b["x1"]) - max(tb[0], b["x0"])) * max(0.0, min(tb[3], b["bottom"]) - max(tb[1], b["top"]))
                    if ov > bov:
                        best, bov = t, ov
                if best and best["rows"]:
                    try:
                        vv = vt(dict(b, rows=best["rows"]), pp)
                        if vv.get("ok") and real(best["rows"], vv):
                            by[kk]["ok"] += 1
                            hit.append(kk)
                    except Exception:  # noqa: BLE001
                        pass
        return hit
    f_done = f_resc = 0
    for mini, local, b in failed[:60]:
        if time.time() - t0 > budget * 0.7:
            break
        f_done += 1
        f_resc += 1 if one(mini, local, b, backs) else 0
    alt_n = alt_cov = 0
    for mini, local, b in trset[:30]:
        if time.time() - t0 > budget:
            break
        alt_n += 1
        alt_cov += 1 if one(mini, local, b, [k for k in FAST if k in by]) else 0
    return {"failed_total": len(failed), "failed_done": f_done, "failed_rescued": f_resc, "tr_total": len(trset), "tr_done": alt_n, "tr_alt_cover": alt_cov, "by": by, "secs": int(time.time() - t0)}


# ───────── 決策(保守 · 有門檻才動 · 附證據)· 回滾 ─────────
def decide(cfg: dict, lay: dict, res: dict, bench: dict, prev: dict = None, applied: bool = False) -> tuple:
    new = json.loads(json.dumps(cfg))
    dec = []

    def change(key, val, why, ev):
        if new.get(key) != val:
            dec.append({"key": key, "old": new.get(key), "new": val, "why": why, "evidence": ev})
            new[key] = val
    by = (bench or {}).get("by") or {}
    tried_any = {k: v for k, v in by.items() if v.get("installed") and v.get("tried")}
    if tried_any:
        ranked = sorted(tried_any, key=lambda k: (-(by[k]["ok"] / max(by[k]["tried"], 1)), by[k]["ms"] / max(by[k]["tried"], 1)))
        order = ranked + [k for k in new["rescue_order"] if k not in ranked]
        dis = sorted(set(new["disabled_backends"]) | {k for k in ranked if by[k]["tried"] >= 15 and by[k]["ok"] == 0})
        keep = [k for k in order if k not in dis]
        if len(keep) < 2:
            dis = [k for k in dis if k not in order[:2]]
        change("rescue_order", order, "依實測救回率排序(高 → 低 · 同率比速度)", " · ".join("%s %d/%d %dms" % (k, by[k]["ok"], by[k]["tried"], by[k]["ms"] // max(by[k]["tried"], 1)) for k in ranked))
        change("disabled_backends", dis, "試 ≥15 次 0 救回 → 停用(至少留 2 個)", ",".join(dis) or "—")
    trt, tro = lay.get("tr_tried", 0), lay.get("tr_ok", 0)
    tn, tc = (bench or {}).get("tr_done", 0), (bench or {}).get("tr_alt_cover", 0)
    if cfg.get("tr_dual") == "on" and trt >= 20 and ((tn >= 10 and tc / tn >= 0.9) or tro / trt < 0.10):
        change("tr_dual", "off", "雙讀救回的表快速讀表器也救得回 ≥90%,或雙讀自己救回率 <10% → 關(restore 原生救回接手)",
               "雙讀 %d/%d(%.0f%%)· 平均 %d ms · 快速讀表器覆蓋雙讀救回的表 %d/%d" % (tro, trt, 100.0 * tro / trt, lay.get("tr_ms_avg", 0), tc, tn))
    pt = lay.get("pe_tried", 0)
    if cfg.get("postextract") == "on" and pt >= 50 and (lay.get("pe_fixed", 0) + lay.get("pe_text", 0)) / pt < 0.03:
        change("postextract", "off", "修好 + 改回正文 <3% → 關", "試 %d · 修好 %d · 改回正文 %d · %d ms" % (pt, lay.get("pe_fixed", 0), lay.get("pe_text", 0), lay.get("pe_ms", 0)))
    if res:
        if res.get("rescue_secs", 0) >= 0.95 * cfg["rescue_budget"] and res.get("failed", 0) > 0:
            change("rescue_budget", min(int(cfg["rescue_budget"] * 1.5), CAP["rescue_budget"]), "救回預算用完還有表沒試完 → 放寬", "用 %d 秒 · 仍失敗 %d" % (res["rescue_secs"], res["failed"]))
        if res.get("ocr_secs", 0) >= 0.95 * cfg["ocr_budget"] and res.get("failed", 0) > 0:
            change("ocr_budget", min(int(cfg["ocr_budget"] * 1.5), CAP["ocr_budget"]), "OCR 預算用完還有表沒試完 → 放寬", "用 %d 秒 · 仍失敗 %d" % (res["ocr_secs"], res["failed"]))
    if prev and applied and prev.get("changed"):                     # 這一輪用的設定 = 上一輪結尾的決策 → 比這一輪 vs 上一輪
        pr, cu = prev.get("restore") or {}, res or {}
        worse = (cu.get("tables_restored_ok", 0) < pr.get("tables_restored_ok", 0) - max(2, 0.02 * pr.get("tables_restored_ok", 0))) or cu.get("docs_ok", 0) < pr.get("docs_ok", 0)
        if worse:
            for c in prev["changed"]:
                if c.get("key") in new:
                    dec.append({"key": c["key"], "old": new[c["key"]], "new": c.get("old"), "why": "回滾:上一輪改了設定後端到端成果變差", "evidence": "還原無誤的表 %s → %s · 還原後無誤的報告 %s → %s" % (
                        pr.get("tables_restored_ok"), cu.get("tables_restored_ok"), pr.get("docs_ok"), cu.get("docs_ok"))})
                    new[c["key"]] = c.get("old")
    return new, dec


def _pct(a, b):
    return "%d/%d(%.0f%%)" % (a, b, 100.0 * a / b) if b else "—"


def auto_run(runner=None, skip_layout: bool = False, layout_extra: list = None) -> dict:
    runner = runner or (lambda a: PRIOR.main(a))
    print(cfg_line(), flush=True)
    T, RC = {}, {}
    steps = [] if skip_layout else [("layout", ["layout"] + list(layout_extra or []))]
    steps += [("restore", ["restore", "--rescue-budget", str(CFG["rescue_budget"]), "--ocr-budget", str(CFG["ocr_budget"]), "--ocr-dpi", str(CFG["ocr_dpi"])]),
              ("basicinfo", ["basicinfo", "--ocr-budget", str(CFG["basic_ocr_budget"])])]
    for name, a in steps:
        t0 = time.time()
        try:
            RC[name] = runner(a)
        except Exception as exc:  # noqa: BLE001
            RC[name] = "例外 %s" % type(exc).__name__
        T[name] = int(time.time() - t0)
    d = _resolve("_latest_l2_dir")("")
    rep = _rep()
    lay, res, bas = kpi_layout(d, _LAST.get("layout_rows")), kpi_restore(rep), kpi_basic(rep)
    th = (_resolve("toolhub") or (lambda: None))()
    t0 = time.time()
    bench = auto_bench(d, th, CFG["bench_budget"]) if (th is not None and d) else {}
    T["bench"] = int(time.time() - t0)
    led = ledger_read()
    prev = led[-1] if led else None
    applied = bool(prev and prev.get("next_config") and prev["next_config"] == CFG_FILE)
    new, dec = decide(CFG, lay, res, bench, prev, applied)
    nxt = save_cfg(new, dec) if dec else ""
    rec = {"ts": datetime.datetime.now().isoformat(timespec="seconds"), "config_file": CFG_FILE, "config": CFG, "applied_prev_decisions": applied, "changed": dec, "next_config": nxt,
           "times": T, "rc": RC, "layout": lay, "restore": res, "basic": bas, "bench": {k: v for k, v in (bench or {}).items() if k != "by"}, "bench_by": (bench or {}).get("by", {})}
    ledger_append(rec)
    page = _resolve("_page")
    out = rep / "auto"
    out.mkdir(parents=True, exist_ok=True)
    pv = prev or {}
    pl, prs, pb = pv.get("layout") or {}, pv.get("restore") or {}, pv.get("basic") or {}

    def row(name, cur, old, better="up", fmt=None):
        if cur is None:
            return ("GRAY", [name, "—", "—", "—", ""])
        if old is None:
            return ("GRAY", [name, fmt(cur) if fmt else cur, "—(第一輪)", "—", ""])
        dlt = cur - old
        good = dlt >= 0 if better == "up" else dlt <= 0
        return ("GREEN" if good else "RED", [name, fmt(cur) if fmt else cur, fmt(old) if fmt else old, ("+%s" % dlt) if dlt > 0 else str(dlt), "越高越好" if better == "up" else "越低越好"])
    rows = [row("第二步成功(份)", lay.get("step2_ok"), pl.get("step2_ok")), row("表格通過(layout)", lay.get("tables_ok"), pl.get("tables_ok")),
            row("還原無誤的表(端到端)", res.get("tables_restored_ok"), prs.get("tables_restored_ok")), row("仍失敗的表", res.get("failed"), prs.get("failed"), "down"),
            row("OCR 候選的表", res.get("ocr_cand"), prs.get("ocr_cand"), "down"), row("算術不符(期)", res.get("calc_fail"), prs.get("calc_fail"), "down"),
            row("還原後無誤的報告", res.get("docs_ok"), prs.get("docs_ok")), row("BASIC INFO 綠燈格", bas.get("green"), pb.get("green")), row("BASIC INFO 紅燈格", bas.get("red"), pb.get("red"), "down"),
            row("總耗時(秒)", sum(T.values()), sum((pv.get("times") or {}).values()) if pv.get("times") else None, "down")]
    rows += [("YELLOW", ["決策 · " + x["key"], json.dumps(x["new"], ensure_ascii=False)[:80], json.dumps(x["old"], ensure_ascii=False)[:80], "下一輪生效", x["why"] + " · " + x["evidence"]]) for x in dec] or \
            [("GRAY", ["決策", "設定不變", "—", "—", "沒有指標達到調整門檻"])]
    if page:
        (out / "AUTO_latest.html").write_text(page("自動實測優化 · 實跑 → 量 KPI → 依實測決策 → 下一輪生效 · 變差自動回滾", "本輪設定 %s · 下一輪 %s · 台帳 %s · 第 %d 輪" % (
            html.escape(CFG_FILE or "預設"), html.escape(nxt or "不變"), html.escape(str(ledger_path())), len(led) + 1), ["項目", "本輪", "上輪", "差", "說明"], rows), encoding="utf-8")
    rec["html"] = str(out / "AUTO_latest.html")
    rec["prev"] = pv
    rec["round"] = len(led) + 1
    return rec


def _inject(args: list) -> list:
    a = list(args)
    if a[:1] == ["restore"]:
        for k, v in (("--rescue-budget", CFG["rescue_budget"]), ("--ocr-budget", CFG["ocr_budget"]), ("--ocr-dpi", CFG["ocr_dpi"])):
            if k not in a:
                a += [k, str(v)]
    if a[:1] == ["basicinfo"] and "--ocr-budget" not in a:
        a += ["--ocr-budget", str(CFG["basic_ocr_budget"])]
    return a


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    if "--selftest" in args[:2]:
        return selftest()
    if args[:1] == ["auto"]:
        o = auto_run(skip_layout="--skip-layout" in args, layout_extra=(["--dir", args[args.index("--dir") + 1]] if "--dir" in args and args.index("--dir") + 1 < len(args) else []))
        lay, res, bas, b = o["layout"], o["restore"], o["basic"], o["bench"]
        pv = o["prev"]
        print("[計] 自動實測優化 · 第 %d 輪 · 本輪設定 %s%s · 耗時 %s · 總 %d 秒" % (o["round"], o["config_file"] or "預設", " · 已套上一輪決策" if o["applied_prev_decisions"] else "",
                                                                         " · ".join("%s %ds" % kv for kv in o["times"].items()), sum(o["times"].values())))
        print("[計] 第二步成功 %s · 表格通過(layout)%s · 雙讀 %s 平均 %d ms · 擷取後復健 修好 %d · 改回正文 %d / 試 %d" % (
            _pct(lay.get("step2_ok", 0), lay.get("files", 0)), _pct(lay.get("tables_ok", 0), lay.get("tables", 0)), _pct(lay.get("tr_ok", 0), lay.get("tr_tried", 0)), lay.get("tr_ms_avg", 0),
            lay.get("pe_fixed", 0), lay.get("pe_text", 0), lay.get("pe_tried", 0)))
        if res:
            print("[計] 端到端還原無誤的表 %s(原生 %d · 重驗 %d · 救回 %d · 文中表 %d)· OCR 候選 %d · 仍失敗 %d · 算術 過 %d / 不符 %d · 還原後無誤的報告 %s" % (
                _pct(res["tables_restored_ok"], res["tables_total"]), res["native"], res["reverify"], res["rescued"], res["flat_ok"], res["ocr_cand"], res["failed"], res["calc_pass"], res["calc_fail"],
                _pct(res["docs_ok"], res["docs"])))
        if bas:
            print("[計] BASIC INFO · 綠 %d · 黃 %d · 紅 %d · 灰 %d · 動用 OCR %d 份 · 紅燈欄 %s" % (bas["green"], bas["yellow"], bas["red"], bas["gray"], bas["ocr_docs"],
                                                                                            " · ".join("%s %d" % kv for kv in Counter(bas.get("red_fields") or {}).most_common(4)) or "—"))
        if b:
            print("[計] 讀表工具實測 · 沒過的財務表 %d(測 %d · 任一救回 %d)· 雙讀救回的表 %d(測 %d · 快速讀表器也救得回 %d)· " % (b.get("failed_total", 0), b.get("failed_done", 0), b.get("failed_rescued", 0),
                  b.get("tr_total", 0), b.get("tr_done", 0), b.get("tr_alt_cover", 0)) + " · ".join("%s %d/%d" % (k, v["ok"], v["tried"]) for k, v in (o.get("bench_by") or {}).items() if v.get("tried")))
        if pv:
            pr = pv.get("restore") or {}
            print("[計] 跟上一輪比 · 還原無誤的表 %s → %s · 還原後無誤的報告 %s → %s · 總耗時 %s → %d 秒" % (pr.get("tables_restored_ok", "—"), res.get("tables_restored_ok", "—"), pr.get("docs_ok", "—"),
                                                                                       res.get("docs_ok", "—"), sum((pv.get("times") or {}).values()) or "—", sum(o["times"].values())))
        for x in o["changed"]:
            print("[計] 決策 · %s:%s → %s · %s · %s" % (x["key"], json.dumps(x["old"], ensure_ascii=False)[:60], json.dumps(x["new"], ensure_ascii=False)[:60], x["why"], x["evidence"][:160]))
        if not o["changed"]:
            print("[計] 決策 · 設定不變(沒有指標達到調整門檻)")
        print("[計] 下一輪設定 %s · 台帳 %s" % (o["next_config"] or "不變", ledger_path()))
        print("  [U/I] %s" % o["html"])
        return 0
    if args[:1] in (["layout"], ["restore"], ["basicinfo"]):
        print(cfg_line(), flush=True)
        args = _inject(args)
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
    global CFG, CFG_FILE
    keep_cfg, keep_file = dict(CFG), CFG_FILE
    td = Path(tempfile.mkdtemp(prefix="vrn174-"))
    saved = {k: os.environ.get(k) for k in ("VIA_SPILL_DIR", "VIA_VRN_HEALTH_OUT", "VIA_VRN_POSTEXTRACT_OFF")}
    keep_home = globals()["_home"]
    try:
        home = td / "VRN"
        globals()["_home"] = lambda: home  # noqa: E731
        c0, f0 = load_cfg(home)
        n1 = save_cfg(dict(DEFAULT, tr_dual="off"), [{"key": "tr_dual"}], home)
        n2 = save_cfg(dict(DEFAULT, tr_dual="off"), [{"key": "tr_dual"}], home)
        c1, f1 = load_cfg(home)
        chk("① 設定冊:沒有 → 預設;寫 v0100;內容沒變不出新版;讀回尾版", f0 == "" and c0 == DEFAULT and n1 == "VRN_AutoTune_Config_v0100.json" and n2 == "" and c1["tr_dual"] == "off" and f1 == n1)
        by = {"pymupdf_lines": {"tried": 30, "ok": 12, "ms": 30 * 200, "installed": True}, "pdfplumber_text": {"tried": 30, "ok": 12, "ms": 30 * 90, "installed": True},
              "camelot_stream": {"tried": 20, "ok": 3, "ms": 20 * 1500, "installed": True}, "tabula_lattice": {"tried": 20, "ok": 0, "ms": 20 * 3000, "installed": True},
              "img2table": {"tried": 0, "ok": 0, "ms": 0, "installed": False}}
        lay = {"tr_tried": 107, "tr_ok": 26, "tr_ms_avg": 6392, "pe_tried": 164, "pe_fixed": 3, "pe_text": 13, "pe_ms": 221000}
        res = {"rescue_secs": 600, "ocr_secs": 120, "failed": 9, "tables_restored_ok": 300, "docs_ok": 20}
        bench = {"by": by, "tr_done": 20, "tr_alt_cover": 19}
        new, dec = decide(dict(DEFAULT), lay, res, bench)
        keys = [x["key"] for x in dec]
        chk("② 決策:救回順序 依救回率 → 同率比速度(pdfplumber_text 90ms 排在 pymupdf_lines 前)· tabula_lattice 20 次 0 救回 → 停用 · 雙讀 快速讀表器覆蓋 19/20 → 關 · 復健 16/164 ≥3% → 留 · 救回預算用完 → 900",
            new["rescue_order"][:3] == ["pdfplumber_text", "pymupdf_lines", "camelot_stream"] and new["disabled_backends"] == ["tabula_lattice"] and new["tr_dual"] == "off"
            and new["postextract"] == "on" and new["rescue_budget"] == 900 and "ocr_budget" not in keys)
        prev = {"next_config": "X", "changed": [{"key": "tr_dual", "old": "on", "new": "off"}], "restore": {"tables_restored_ok": 320, "docs_ok": 22}}
        nb, db = decide(dict(DEFAULT, tr_dual="off"), {}, {"tables_restored_ok": 300, "docs_ok": 20, "rescue_secs": 10, "ocr_secs": 10, "failed": 0}, {}, prev, applied=True)
        nn, dn = decide(dict(DEFAULT, tr_dual="off"), {}, {"tables_restored_ok": 300, "docs_ok": 20, "rescue_secs": 10, "ocr_secs": 10, "failed": 0}, {}, prev, applied=False)
        chk("③ 回滾:上一輪關雙讀 → 這一輪還原無誤的表 320 → 300、報告 22 → 20 變差 → 雙讀退回 on;沒套上那批決策(applied=False)→ 不回滾",
            nb["tr_dual"] == "on" and any("回滾" in x["why"] for x in db) and nn["tr_dual"] == "off" and not dn)
        CFG = dict(DEFAULT, tr_dual="off", rescue_order=["pdfplumber_text", "pymupdf_lines"], disabled_backends=["tabula_lattice"])
        tr_none = tr_check_v174(1, 2) is None
        th = toolhub_v174()
        order_ok = th is None or (th.TABLE_BACKENDS[:2] == ["pdfplumber_text", "pymupdf_lines"] and "tabula_lattice" not in th.TABLE_BACKENDS and "camelot_stream" in th.TABLE_BACKENDS)
        inj = _inject(["restore"])
        chk("④ 套設定:雙讀關 → tr_check 回 None(restore 接手)· 讀表器順序照設定 · 停用的不跑 · restore 自動帶預算參數", tr_none and order_ok and inj[:3] == ["restore", "--rescue-budget", "600"])
        CFG = dict(DEFAULT)
        CFG_FILE = ""
        rep = td / "rep"
        os.environ["VIA_VRN_HEALTH_OUT"] = str(rep)
        stage = td / "VIA_progress" / "ps_x" / "spill" / "vrn_stage_r1" / "layout_l2"
        stage.mkdir(parents=True)
        for i in range(3):
            (stage / ("%d.json" % i)).write_text(json.dumps({"row": {"file": "%d.pdf" % i, "code": "2330"}, "pages": [], "summary": {"text_ok": True, "table_ok": i < 2, "tables": 4, "tables_ok": 3, "secs": 10,
                                                             "tools": [{"tool": "單讀(pdfplumber) → 雙讀(TableRepair)", "ok": i == 0, "ms": 6000}], "verify_issues": {"無期間表頭": 1}}}), encoding="utf-8")
        os.environ["VIA_SPILL_DIR"] = str(td / "VIA_progress" / "ps_new" / "spill")
        (rep / "restore").mkdir(parents=True)
        (rep / "restore" / "RESTORE_SUMMARY_latest.json").write_text(json.dumps({"docs": 3, "docs_ok": 1, "counts": {"t_native": 8, "t_reverify": 1, "t_rescued": 1, "t_ocr": 1, "t_fail": 1, "flat_tables": 0},
                                                                                "calc": {"PASS": 10, "FAIL": 1}, "rescue_secs": 30, "ocr_secs": 20}), encoding="utf-8")
        (rep / "restore" / "01_x.json").write_text(json.dumps({"tables": [{"status": "還原無誤", "method": "原生"}] * 10 + [{"status": "未過", "method": "原生(未過)"}] * 2}), encoding="utf-8")
        (rep / "basicinfo").mkdir()
        (rep / "basicinfo" / "BASIC_INFO_latest.json").write_text(json.dumps({"records": [{"stage": "NON-OCR", "fields": {"A": {"status": "GREEN"}, "B": {"status": "RED"}}}]}), encoding="utf-8")
        calls = []
        o1 = auto_run(runner=lambda a: calls.append(a[0]) or 0)
        o2 = auto_run(runner=lambda a: calls.append(a[0]) or 0)
        led = ledger_read(home)
        chk("⑤ auto 一條指令:layout → restore(帶預算)→ basicinfo → KPI(第二步 %d/%d · 表 %d/%d · 雙讀 %d/%d · 還原無誤 %d/%d · BASIC 綠 %d 紅 %d)→ 台帳 2 輪 · 第 2 輪跟第 1 輪比 · HTML" % (
            o1["layout"]["step2_ok"], o1["layout"]["files"], o1["layout"]["tables_ok"], o1["layout"]["tables"], o1["layout"]["tr_ok"], o1["layout"]["tr_tried"], o1["restore"]["tables_restored_ok"],
            o1["restore"]["tables_total"], o1["basic"]["green"], o1["basic"]["red"]),
            calls == ["layout", "restore", "basicinfo"] * 2 and o1["layout"]["step2_ok"] == 2 and o1["layout"]["tr_tried"] == 3 and o1["restore"]["tables_restored_ok"] == 10 and len(led) == 2
            and o2["round"] == 2 and o2["prev"].get("ts") and Path(o2["html"]).exists())
    finally:
        CFG, CFG_FILE = keep_cfg, keep_file
        globals()["_home"] = keep_home
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(td, ignore_errors=True)
    me = Path(__file__).read_text(encoding="utf-8")
    chk("⑥ 正本加速器橋 · 自帶多程序墊片", "import VeritasCeleritas_v1141" in me and _job_entry.__module__ in ("__main__", __name__))
    print("  ── 前版鏈自測(原樣印出)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("⑦ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    print("[計] VRN_SystemManager_v0174 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
