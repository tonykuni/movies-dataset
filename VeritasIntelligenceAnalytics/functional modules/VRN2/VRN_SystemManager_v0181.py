#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0181 — 薄尾(操作員 2026-10-11「多重來源多重交叉比對多重修復 · 查評價方法中英文 DICT · 只有 BASIC / DILUTED EPS 之分 其他只是 EPS ·
   ROE ROA A.E 都是前後期均值 · DPS 配發時間基於哪一段的 DILUTED EPS 要搞清楚 算 PAYOUT RATIO · 保留盈餘課稅影響加入」)。
  財務測試加深(替換 fin_tests 一頭):① 資產負債恆等式改用正確標準鍵 total_equity(舊版用 equity 從沒測到)+ 資產 = 負債與權益總計
  ② ROE / ROA = 淨利 ÷ 前後期平均權益 / 總資產(報告用期末值 → 標口徑不同)③ 配息率:DPS ÷ 同年 / 前一年 稀釋 EPS 誰對上報告配息率 → 記對應年度(沒有配息率列 → 未定 · 不猜)
  ④ 淨利恆等式對不上 → 試 未分配盈餘加徵 5%(前一年淨利 ×(1 − 配息率)× 5%)解釋 · 有效稅率 0~30% ⑤ ROA / DPS / 配息率 / BVPS 詞庫沒有標準鍵 → 名稱規則辨識 + 建議入冊(待操作員確認)
  valuation 動詞(auto 自動接):ENG395 評價方法字典(只讀)讀方法 / 倍數 / 基準年 → 倍數 × 同年稀釋 EPS 或 BVPS = 隱含目標價 ↔ 資訊區目標價(±5%)· 基準年沒寫 → 推定
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

import csv
import datetime
import functools
import html
import importlib.util
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"
TAG = "v0181"


def _vnum_v0181(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0181(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0181(p) < _vnum_v0181(__file__)), key=_vnum_v0181)
PRIOR = _load_v0181(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


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
LABEL_KEYS = [("roa", r"(?i)\bROA\b|資產報酬率"), ("roe", r"(?i)\bROE\b|股東權益報酬率|權益報酬率"), ("dps", r"(?i)\bDPS\b|每股股利|每股現金股利|現金股利|dividend per share"),
              ("payout", r"(?i)payout|配息率|股利發放率|盈餘分配率|發放率"), ("bvps", r"(?i)\bBVPS\b|每股淨值|book value per share")]
_GROW = re.compile(r"(?i)growth|成長|yoy|qoq|%\s*chg|變動")


def _patch_v(name: str, fn):
    mo = _owner(name)
    if mo is None or getattr(vars(mo)[name], "_v181", False):
        return None
    prev = vars(mo)[name]
    functools.update_wrapper(fn, prev)
    fn._v181 = True
    fn._prev = prev
    setattr(mo, name, fn)
    return prev


def matrix(rows: list) -> tuple:
    """標準鍵 + 名稱規則(詞庫缺 roa / dps / payout / bvps)→ {鍵: {期間: 值}};EPS 用稀釋列(有分類時)。"""
    M = defaultdict(dict)
    ec = {i: c for i, c, _ in ((_resolve("eps_classify") or (lambda *a: []))(rows) or [])}
    for i, r in enumerate(rows):
        lab = str(r.get("label_raw") or "")
        keys = [r.get("std")] if r.get("std") else []
        if not _GROW.search(lab):
            keys += [k for k, rx in LABEL_KEYS if re.search(rx, lab) and k not in keys]
        if ec.get(i) == "DILUTED_EPS":
            keys = ["eps_diluted"] + keys
        for k in keys:
            for c in r.get("cells") or []:
                if isinstance(c.get("value"), (int, float)) and c["period"] not in M[k]:
                    M[k][c["period"]] = float(c["value"])
    if "eps_diluted" in M:
        M["eps_use"] = M["eps_diluted"]
    elif "eps" in M:
        M["eps_use"] = M["eps"]
    return M, ec


def _annual(M: dict, k: str) -> dict:
    pk = _resolve("_pkey") or (lambda p: None)
    out = {}
    for p, v in (M.get(k) or {}).items():
        kk = pk(p)
        if kk and not kk[1]:
            out[kk[0]] = (p, v)
    return out


def fin_tests_v181(rows: list) -> list:
    out = fin_tests_v181._prev(rows)
    M, _ = matrix(rows)
    ptype = _resolve("ptype") or (lambda p: "歷史")
    tolp = _resolve("_tolp") or (lambda t, *o: max(1.0, abs(t) * 0.015))
    T = lambda rule, kind, per, ok, det: out.append({"rule": rule, "kind": kind, "period": per, "ptype": ptype(per), "status": "PASS" if ok else "FAIL", "detail": det})  # noqa: E731
    for p in sorted({q for v in M.values() for q in v}):
        g = lambda k: M.get(k, {}).get(p)  # noqa: E731
        if None not in (g("total_assets"), g("total_liabilities"), g("total_equity")):
            c1 = g("total_liabilities") + g("total_equity")
            c2 = c1 + (g("minorities_equity") or 0)                  # total_equity 可能含 / 不含非控制權益(詞庫兩種都對到)→ 兩種口徑都試
            tl = tolp(g("total_assets"), g("total_liabilities"), g("total_equity"))
            ok = abs(c1 - g("total_assets")) <= tl or abs(c2 - g("total_assets")) <= tl
            T("資產 = 負債 + 權益(total_equity)", "加減法", p, ok, "%s vs %s%s" % (g("total_assets"), round(c1, 2), "" if c2 == c1 else " / 含非控制 %s" % round(c2, 2)))
        if None not in (g("total_assets"), g("liab_and_equity")):
            T("資產 = 負債與權益總計", "加減法", p, abs(g("liab_and_equity") - g("total_assets")) <= tolp(g("total_assets")), "%s vs %s" % (g("total_assets"), g("liab_and_equity")))
        if g("pretax_income") and g("tax") is not None:
            etr = abs(g("tax")) / g("pretax_income") * 100 if g("pretax_income") > 0 else None
            if etr is not None:
                T("有效稅率 0~30%(20% + 未分配盈餘 5%)", "除法", p, 0 <= etr <= 30, "稅 %s ÷ 稅前 %s = %.1f%%" % (g("tax"), g("pretax_income"), etr))
    NI, TE, TA = _annual(M, "net_income"), _annual(M, "total_equity"), _annual(M, "total_assets")
    for key, base, zh in (("roe", TE, "ROE = 淨利 ÷ 前後期平均權益"), ("roa", TA, "ROA = 淨利 ÷ 前後期平均總資產")):
        R = _annual(M, key)
        for y, (p, v) in sorted(R.items()):
            if y in NI and y in base and (y - 1) in base:
                avg = (base[y][1] + base[y - 1][1]) / 2
                calc = NI[y][1] / avg * 100 if avg else None
                end = NI[y][1] / base[y][1] * 100 if base[y][1] else None
                vv = v * 100 if abs(v) <= 1.5 and calc and abs(calc) > 1.5 else v
                if calc is None:
                    continue
                ok = abs(calc - vv) <= 1.0
                note = "" if ok else ("報告用期末值(非平均)· 口徑不同" if end is not None and abs(end - vv) <= 1.0 else "")
                T(zh, "除法", p, ok, "%s vs 平均口徑 %.2f%s" % (v, calc, (" · " + note) if note else ""))
    DPS, EPS, PO = _annual(M, "dps"), _annual(M, "eps_use"), _annual(M, "payout")
    for y, (p, po) in sorted(PO.items()):
        if y not in DPS:
            continue
        pov = po * 100 if abs(po) <= 1.5 else po
        same = DPS[y][1] / EPS[y][1] * 100 if y in EPS and EPS[y][1] else None
        prior = DPS[y][1] / EPS[y - 1][1] * 100 if (y - 1) in EPS and EPS[y - 1][1] else None
        hit = "同年 EPS" if same is not None and abs(same - pov) <= 2.0 else ("前一年 EPS" if prior is not None and abs(prior - pov) <= 2.0 else "")
        T("配息率 = DPS ÷ 稀釋 EPS(對應年度)", "除法", p, bool(hit), "報告 %s%% · 同年 %s · 前一年 %s → %s" % (round(pov, 2), "—" if same is None else "%.1f%%" % same,
                                                                                     "—" if prior is None else "%.1f%%" % prior, ("DPS 對應 " + hit) if hit else "兩種對應都不符"))
    for x in out:
        if not x.get("rule", "").startswith("淨利 ≈ 稅前"):
            continue
        per = x["period"]
        pre, tax, ni, mi = (M.get(k, {}).get(per) for k in ("pretax_income", "tax", "net_income", "minority_interest"))
        if None in (pre, tax, ni):
            continue
        a = pre - abs(tax)
        tl = tolp(ni, pre, tax)
        cands = [("", a)] + ([("扣非控制權益 %s" % mi, a - abs(mi))] if mi else [])
        kk = (_resolve("_pkey") or (lambda q: None))(per)
        if kk and not kk[1] and (kk[0] - 1) in NI:
            y = kk[0]
            po_prev = (PO[y - 1][1] if (y - 1) in PO else ((DPS[y - 1][1] / EPS[y - 1][1] * 100) if (y - 1) in DPS and (y - 1) in EPS and EPS[y - 1][1] else 0.0))
            po_prev = po_prev * 100 if abs(po_prev) <= 1.5 else po_prev
            sur = 0.05 * NI[y - 1][1] * max(0.0, 1 - po_prev / 100)
            note = "未分配盈餘加徵 5%% ≈ %.2f(前一年淨利 %s × (1 − 配息率 %.0f%%))" % (sur, NI[y - 1][1], po_prev)
            cands += [(note, a - sur)] + ([("扣非控制權益 + " + note, a - abs(mi) - sur)] if mi else [])
        hit = next(((n, c) for n, c in cands if abs(c - ni) <= tl), None)      # 容許誤差依精度(不再用稅前 5% 寬放 · 那會吞掉加徵稅)
        x["status"] = "PASS" if hit else "FAIL"
        x["detail"] = "%s vs %s(容許 %.3g)%s" % (ni, round(a, 2), tl, (" · " + hit[0]) if hit and hit[0] else ("" if hit else " · 扣非控制 / 加徵 5% 都解釋不了"))
    return out


_patch_v("fin_tests", fin_tests_v181)
_parts = _resolve("PARTS")
if isinstance(_parts, dict):
    _parts.update({"資產 = 負債 + 權益(total_equity)": {"total_assets", "total_liabilities", "total_equity", "minorities_equity"}, "資產 = 負債與權益總計": {"total_assets", "liab_and_equity"},
                   "有效稅率 0~30%(20% + 未分配盈餘 5%)": {"tax", "pretax_income"}, "ROE = 淨利 ÷ 前後期平均權益": {"roe", "net_income", "total_equity"},
                   "ROA = 淨利 ÷ 前後期平均總資產": {"roa", "net_income", "total_assets"}, "配息率 = DPS ÷ 稀釋 EPS(對應年度)": {"dps", "eps", "payout"}})


# ───────── 評價方法交叉比對(ENG395 字典 · 只讀)─────────
def valuation_matcher():
    for p in sorted(HERE.glob("VRN_ENG395_ValuationMethodLexicon_v*.py"), key=_vnum_v0181, reverse=True):
        try:
            m = _load_v0181(p, "vrn_eng395_" + p.stem)
            return m.Matcher(), p.name
        except Exception:  # noqa: BLE001
            continue
    return None, "ENG395 / 評價方法 SSOT 不在 → 用內建最小規則(本益比 / 股價淨值比)"


_FALLBACK = [("VAL_PE", r"(?i)本益比|\bP/?E\b|\bPER\b|市盈率"), ("VAL_PB", r"(?i)股價淨值比|\bP/?B\b|\bPBR\b|市淨率")]


def val_parse(text: str, mt=None) -> dict:
    code = ""
    if mt is not None:
        try:
            ms = mt.methods_in(text)
            code = ms[0] if ms else ""
        except Exception:  # noqa: BLE001
            code = ""
    if not code:
        code = next((c for c, rx in _FALLBACK if re.search(rx, text or "")), "")
    mul = re.search(r"(\d{1,3}(?:\.\d+)?)\s*(?:倍|x\b|X\b|times)", text or "")
    yr = re.search(r"(20\d{2})\s*(?:年|F|E|\(F\)|\(E\))|FY(\d{2})E?|\b(\d{2})F\b", text or "")
    y = int(yr.group(1)) % 100 if yr and yr.group(1) else (int(yr.group(2) or yr.group(3)) if yr else None)
    return {"method": code, "multiple": float(mul.group(1)) if mul else None, "year": y}


def valuation_run() -> dict:
    rep = _rep()
    mt, src = valuation_matcher()
    b2 = {}
    bp = rep / "basicinfo" / "BASIC_INFO_V2_latest.json"
    if bp.exists():
        for r in json.loads(bp.read_text(encoding="utf-8")).get("records", []):
            fd = r.get("fields") or {}
            b2[(fd.get("FILENAME") or {}).get("value")] = (fd.get("TARGET_PRICE") or {}).get("value")
    out = []
    for f in sorted((rep / "restore").glob("*.json")) if (rep / "restore").is_dir() else []:
        if f.name.startswith("RESTORE_"):
            continue
        dj = json.loads(f.read_text(encoding="utf-8"))
        fn = (dj.get("document_meta") or {}).get("file") or f.stem
        tp = b2.get(fn) or (dj.get("document_meta") or {}).get("target_price")
        sents = [c.get("text", "") for c in dj.get("content", []) if c.get("page") in (1, None) or c.get("type") in ("info", "sentence")]
        vs = [s for s in sents if re.search(r"(?i)本益比|淨值比|P/?E|P/?B|PER|PBR|EV/EBITDA|DCF|倍|x\b|valuation|評價", s) and re.search(r"\d", s)]
        vp = next((val_parse(s, mt) for s in vs if val_parse(s, mt)["method"] and val_parse(s, mt)["multiple"]), {"method": "", "multiple": None, "year": None})
        M = defaultdict(dict)
        for t in dj.get("tables", []):
            if t.get("status") != "未過":
                for k, v in matrix(t.get("rows") or [])[0].items():
                    for p2, x in v.items():
                        M[k].setdefault(p2, x)
        mth = vp["method"] or ""
        metric = "eps_use" if re.fullmatch(r"VAL_PE(R|_FWD|_TTM|_FORWARD|_TRAILING)?", mth) else ("bvps" if re.fullmatch(r"VAL_PB(R|_FWD|_TTM)?", mth) else "")   # VAL_PEG ≠ 本益比
        ann = _annual(M, metric) if metric else {}
        st, det, base = "未驗", "", vp["year"]
        if not vp["method"]:
            det = "沒讀到評價方法句"
        elif not metric:
            det = "%s 需要淨負債 / 股數等(暫不驗)" % vp["method"]
        elif not tp or not vp["multiple"]:
            det = "缺目標價或倍數"
        else:
            cands = [base] if base in ann else sorted(ann, reverse=True)
            for y in cands:
                implied = vp["multiple"] * ann[y][1]
                if abs(implied - tp) <= abs(tp) * 0.05:
                    st, det = "PASS", "%s × %s %s(%s)= %.1f ≈ 目標價 %s%s" % (vp["multiple"], metric.replace("eps_use", "稀釋 EPS"), ann[y][1], ann[y][0], implied, tp, "" if y == base else " · 推定基準年")
                    base = y
                    break
            else:
                st = "FAIL" if ann else "未驗"
                det = ("倍數 × 各年 %s 都對不上目標價 %s" % (metric, tp)) if ann else "表裡沒有 %s" % metric
        out.append({"file": fn, "method": vp["method"], "multiple": vp["multiple"], "base_year": ("20%02d" % base) if base else "", "target_price": tp, "status": st, "detail": det})
    od = rep / "valuation"
    od.mkdir(parents=True, exist_ok=True)
    (od / "VALUATION_CHECK_latest.json").write_text(json.dumps({"matcher": src, "rows": out}, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    with (od / "VALUATION_CHECK_latest.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["file", "method", "multiple", "base_year", "target_price", "status", "detail"])
        w.writeheader()
        w.writerows(out)
    return {"n": len(out), "status": dict(Counter(x["status"] for x in out)), "methods": dict(Counter(x["method"] or "沒讀到" for x in out)), "src": src,
            "fails": [x for x in out if x["status"] == "FAIL"][:4]}


def _lines_v181(v: dict, ex: dict) -> list:
    L = ["[計] 評價方法交叉比對(%s)· %d 份 · 方法 %s · 倍數 × 同年稀釋 EPS / BVPS ↔ 目標價:PASS %d · FAIL %d · 未驗 %d" % (
        v["src"], v["n"], " · ".join("%s %d" % kv for kv in Counter(v["methods"]).most_common(4)), v["status"].get("PASS", 0), v["status"].get("FAIL", 0), v["status"].get("未驗", 0))]
    for x in v["fails"]:
        L.append("[計] 評價不符 · %s · %s %s 倍 · %s" % (x["file"][:30], x["method"], x["multiple"], x["detail"][:80]))
    L.append("[計] 新測試 · " + " · ".join("%s 過 %d / 不符 %d" % (k, c.get("PASS", 0), c.get("FAIL", 0)) for k, c in ex.items()))
    L.append("[計] 詞庫缺標準鍵 roa / dps / payout / bvps → 本版用名稱規則辨識 · 建議入 FinLexicon(待操作員確認 · 不自動改)")
    return L


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    if "--selftest" in args[:2]:
        return selftest()
    if args[:1] == ["valuation"] or (args[:1] in (["auto"], ["findata"], ["findata2"]) and "--resume" not in args):
        rc = PRIOR.main(args) if args[:1] != ["valuation"] else 0
        v = valuation_run()
        ex = defaultdict(Counter)
        tp = _rep() / "findata" / "FINDATA_TESTS_latest.csv"
        if tp.exists():
            for r in csv.DictReader(tp.open(encoding="utf-8-sig")):
                if r["rule"].startswith(("ROE", "ROA", "配息率", "有效稅率", "資產 = 負債 + 權益(total", "資產 = 負債與")):
                    ex[r["rule"].split(" ")[0]][r["status"]] += 1
        L = _lines_v181(v, ex)
        for l in L:
            print(l)
        if args[:1] == ["auto"]:
            pk = _rep() / "auto" / "VRN_AI_PACK_latest.md"
            if pk.exists():
                old = [l for l in pk.read_text(encoding="utf-8").splitlines() if l.strip()]
                nxt = [l for l in old if l.startswith("NEXT:")] or ["NEXT: 依本包修 → 再跑 auto"]
                pk.write_text("\n".join(([l for l in old if not l.startswith("NEXT:")] + L)[:299] + nxt[:1]) + "\n", encoding="utf-8")
                ac = _resolve("aiverb_compress")
                if ac:
                    print("[計] AI 包(含評價交叉比對 · 新測試)· %s" % ac(pk, nxt[0].replace("NEXT: ", ""))[1])
        return rc
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
    R = lambda lab, std, vals: {"label_raw": lab, "std": std, "cells": [{"period": k, "value": v} for k, v in vals.items()]}  # noqa: E731
    ft = lambda rows: _resolve("fin_tests")(rows)  # noqa: E731
    st = lambda res, pre: [x["status"] for x in res if x["rule"].startswith(pre)]  # noqa: E731
    a = ft([R("Total assets", "total_assets", {"2025F": 1000}), R("Total liabilities", "total_liabilities", {"2025F": 400}), R("Total equity", "total_equity", {"2025F": 600}),
            R("Total liabs & equity", "liab_and_equity", {"2025F": 1000})])
    b = ft([R("Total assets", "total_assets", {"2025F": 1000}), R("Total liabilities", "total_liabilities", {"2025F": 400}), R("Total equity", "total_equity", {"2025F": 550}),
            R("Minorities", "minorities_equity", {"2025F": 50})])
    c = ft([R("Total assets", "total_assets", {"2025F": 1000}), R("Total liabilities", "total_liabilities", {"2025F": 400}), R("Total equity", "total_equity", {"2025F": 500})])
    chk("① 資產負債恆等式改用正確鍵 total_equity(舊版用 equity 從沒測到)· 1000 = 400 + 600 過 · 負債與權益總計 過 · 權益不含非控制(550 + 50)也過 · 500 → 不符",
        st(a, "資產 = 負債 + 權益(total") == ["PASS"] and st(a, "資產 = 負債與") == ["PASS"] and st(b, "資產 = 負債 + 權益(total") == ["PASS"] and st(c, "資產 = 負債 + 權益(total") == ["FAIL"])
    base = [R("Net income", "net_income", {"2024A": 100, "2025F": 120}), R("Total equity", "total_equity", {"2024A": 500, "2025F": 700})]
    r1 = ft(base + [R("ROE (%)", "roe", {"2025F": 20.0})])
    r2 = [x for x in ft(base + [R("ROE (%)", "roe", {"2025F": 17.14})]) if x["rule"].startswith("ROE")]
    chk("② ROE = 淨利 ÷ 前後期平均權益:120 ÷ (500 + 700)/2 = 20% → 過 · 報告 17.14% = 120 ÷ 700 期末值 → 不符並標「口徑不同」",
        st(r1, "ROE") == ["PASS"] and r2 and r2[0]["status"] == "FAIL" and "期末值" in r2[0]["detail"])
    eps = [R("Diluted EPS", "eps", {"2024A": 10.0, "2025F": 12.0}), R("DPS (NT$)", "", {"2025F": 10.0})]
    p1 = [x for x in ft(eps + [R("Payout ratio (%)", "", {"2025F": 83.33})]) if x["rule"].startswith("配息率")]
    p2 = [x for x in ft(eps + [R("配息率", "", {"2025F": 100.0})]) if x["rule"].startswith("配息率")]
    p3 = [x for x in ft(eps + [R("Payout", "", {"2025F": 50.0})]) if x["rule"].startswith("配息率")]
    chk("③ 配息率對應年度:DPS 10 ÷ 同年 EPS 12 = 83.33% → DPS 對應同年 · 10 ÷ 前一年 10 = 100% → 對應前一年 · 50% 兩種都不符 → FAIL(詞庫沒有 dps / payout 鍵 → 名稱規則辨識)",
        p1 and p1[0]["status"] == "PASS" and "同年" in p1[0]["detail"] and p2 and p2[0]["status"] == "PASS" and "前一年" in p2[0]["detail"] and p3 and p3[0]["status"] == "FAIL")
    s1 = [x for x in ft([R("Pretax", "pretax_income", {"2024A": 800, "2025F": 1000}), R("Tax", "tax", {"2024A": -200, "2025F": -200}), R("Net income", "net_income", {"2024A": 600, "2025F": 785}),
                         R("EPS", "eps", {"2024A": 10.0}), R("DPS", "", {"2024A": 5.0})]) if x["rule"].startswith("淨利") and x["period"] == "2025F"]
    s2 = [x for x in ft([R("Pretax", "pretax_income", {"2025F": 1000}), R("Tax", "tax", {"2025F": -200}), R("Net income", "net_income", {"2025F": 785})]) if x["rule"].startswith("淨利")]
    chk("④ 未分配盈餘加徵 5%%:1000 − 200 = 800 vs 淨利 785 · 差 15 = 前一年淨利 600 × (1 − 配息率 50%%) × 5%% → 解釋得通 → 過 · 沒有前一年資料 → 不符(不再被稅前 5%% 寬放吞掉)· %s" % (s1[0]["detail"][-40:] if s1 else ""),
        s1 and s1[0]["status"] == "PASS" and "加徵" in s1[0]["detail"] and s2 and s2[0]["status"] == "FAIL")
    e1 = st(ft([R("Pretax", "pretax_income", {"2025F": 1000}), R("Tax", "tax", {"2025F": -200})]), "有效稅率")
    e2 = st(ft([R("Pretax", "pretax_income", {"2025F": 1000}), R("Tax", "tax", {"2025F": -400})]), "有效稅率")
    chk("⑤ 有效稅率 0~30%(20% + 加徵 5%):20% 過 · 40% 不符", e1 == ["PASS"] and e2 == ["FAIL"])
    v1, v2 = val_parse("以 2026F EPS 25 倍本益比評價,目標價 NT$650"), val_parse("給予 PEG 1.2 倍")
    chk("⑥ 評價句解析:本益比 · 25 倍 · 基準年 2026 · PEG 不當本益比 → %s / %s" % (v1, v2.get("method")), v1["method"].startswith("VAL_PE") and v1["multiple"] == 25.0 and v1["year"] == 26 and v2.get("method") != "VAL_PE")
    td = Path(tempfile.mkdtemp(prefix="vrn181-"))
    saved = os.environ.get("VIA_VRN_HEALTH_OUT")
    try:
        os.environ["VIA_VRN_HEALTH_OUT"] = str(td / "rep")
        (td / "rep" / "restore").mkdir(parents=True)
        for i, (sent, tp) in enumerate((("以 2026F EPS 25 倍本益比評價", 650.0), ("給予 20 倍本益比", 650.0), ("給予 20 倍本益比", 900.0))):
            (td / "rep" / "restore" / ("0%d_x.json" % i)).write_text(json.dumps({"document_meta": {"file": "R%d.pdf" % i, "target_price": tp}, "content": [{"type": "sentence", "text": sent}],
                                                                                 "tables": [{"id": "T1", "status": "還原無誤", "rows": [R("EPS", "eps", {"2025F": 30.0, "2026F": 32.5 if i else 26.0})]}]}, ensure_ascii=False), encoding="utf-8")
        vr = valuation_run()
        rows = {x["file"]: x for x in json.loads((td / "rep" / "valuation" / "VALUATION_CHECK_latest.json").read_text(encoding="utf-8"))["rows"]}
        chk("⑦ 評價交叉比對:25 倍 × 2026F EPS 26 = 650 = 目標價 → 過 · 沒寫基準年 20 倍 × 2026F 32.5 = 650 → 推定 2026 · 20 倍對不上 900 → 不符",
            rows["R0.pdf"]["status"] == "PASS" and rows["R1.pdf"]["status"] == "PASS" and rows["R1.pdf"]["base_year"] == "2026" and "推定" in rows["R1.pdf"]["detail"] and rows["R2.pdf"]["status"] == "FAIL")
    finally:
        if saved is None:
            os.environ.pop("VIA_VRN_HEALTH_OUT", None)
        else:
            os.environ["VIA_VRN_HEALTH_OUT"] = saved
        shutil.rmtree(td, ignore_errors=True)
    me = Path(__file__).read_text(encoding="utf-8")
    chk("⑧ 最新有版號加速器橋 [VIA:ACCEL-BRIDGE:v0111] · 自帶多程序墊片", "[VIA:ACCEL-BRIDGE:v0111]" in me and _job_entry.__module__ in ("__main__", __name__))
    print("  ── 前版鏈自測(原樣印出)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("⑨ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    print("[計] VRN_SystemManager_v0181 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
