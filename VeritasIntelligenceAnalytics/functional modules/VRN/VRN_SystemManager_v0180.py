#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0180 — 薄尾(操作員 2026-10-11 FINANCIAL DATA 最終欄位:DATE / FILENAME / TICKER / YFINANCE TICKER / BLOOMBERG TICKER / NAME / ENGLISH NAME /
   FINANCIAL STATEMENT / ACCOUNT / UNIT(MN · 小數點兩位)/ VALUE(小數點兩位)/ 歷史與預估加減測試(2 選 1)/ 歷史與預估除法測試(2 選 1)/ THREE LIGHT NAME)。
  findata2 動詞(auto 自動接在後面):一格一列(長表)· DATE = 期間期末日 · 金額一律換算百萬(千元 ÷1000 · 億 ×100 · bn ×1000)· 每股 元/股 · 比率 % · 倍數 x ·
  每列連到它參與的加減法 / 除法測試(歷史 / 預估 · PASS / FAIL / 未驗)· 三燈:有測且全過 GREEN · 任一不符 RED · 沒測到 / 沒對到科目 / 單位預設 YELLOW
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
TAG = "v0180"


def _vnum_v0180(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0180(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0180(p) < _vnum_v0180(__file__)), key=_vnum_v0180)
PRIOR = _load_v0180(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


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
COLS4 = ["DATE", "FILENAME", "TICKER", "YF_TICKER", "BBG_TICKER", "NAME", "ENGLISH_NAME", "FINANCIAL_STATEMENT", "ACCOUNT", "UNIT", "VALUE", "ADDSUB_TEST", "DIV_TEST", "THREE_LIGHT"]
EXTRA4 = ["REPORT_DATE", "PERIOD_RAW", "ACCOUNT_ZH", "ACCOUNT_RAW", "EPS_CLASS", "TABLE", "UNIT_SRC", "VALUE_RAW"]
_MON = {m: i for i, m in enumerate(["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"], 1)}
_STMT = {"IS": "損益表(Income Statement)", "BS": "資產負債表(Balance Sheet)", "CF": "現金流量表(Cash Flow)", "RATIO": "財務比率(Ratios)", "PS": "每股數據(Per Share)",
         "VAL": "評價(Valuation)"}
PARTS = {"毛利 = 營收 − 成本": {"revenue", "cogs", "gross_profit"}, "營益 = 毛利 − 營業費用": {"gross_profit", "opex", "operating_income"},
         "稅前 = 營益 + 業外": {"operating_income", "nonop_income", "pretax_income"}, "淨利 ≈ 稅前 − 稅(− 少數)": {"pretax_income", "tax", "net_income", "minority_interest"},
         "資產 = 負債 + 權益": {"total_assets", "total_liabilities", "equity"}, "毛利率 = 毛利 / 營收": {"gross_margin", "gross_profit", "revenue"},
         "營益率 = 營益 / 營收": {"operating_margin", "operating_income", "revenue"}, "淨利率 = 淨利 / 營收": {"net_margin", "net_income", "revenue"}}
_PER_SHARE = re.compile(r"(?i)\beps\b|\bdps\b|\bbvps\b|每股|per share")
_RATIO = re.compile(r"(?i)margin|growth|ratio|roe|roa|yield|payout|率|%|yoy|qoq")
_MULT = re.compile(r"(?i)\bp/?e\b|\bp/?b\b|ev/ebitda|本益比|股價淨值比|倍")


def period_date(per: str) -> str:
    """期間 → 期末日(台股會計年度 = 曆年):2025F → 2025-12-31 · 4Q25E → 2025-12-31 · 1H26 → 2026-06-30 · Dec-24A → 2024-12-31 · 2024/12 → 2024-12-31。"""
    s = re.sub(r"\s+", "", str(per or "")).upper().replace("(", "").replace(")", "")
    end = lambda y, mo: (datetime.date(y + (mo // 12), mo % 12 + 1, 1) - datetime.timedelta(days=1)).isoformat()  # noqa: E731
    m = re.search(r"([1-4])Q(\d{2})|(\d{2})Q([1-4])|Q([1-4])[-']?(\d{2,4})", s)
    if m:
        q, y = (m.group(1), m.group(2)) if m.group(1) else ((m.group(4), m.group(3)) if m.group(3) else (m.group(5), m.group(6)))
        y = int(y) % 100 + 2000
        return end(y, int(q) * 3)
    m = re.search(r"([12])H(\d{2,4})", s)
    if m:
        return end(int(m.group(2)) % 100 + 2000, 6 if m.group(1) == "1" else 12)
    m = re.search(r"(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)[A-Z]*[-'.]?(\d{2,4})", s)
    if m:
        return end(int(m.group(2)) % 100 + 2000, _MON[m.group(1)])
    m = re.search(r"((?:19|20)\d{2})[/.-](\d{1,2})(?!\d)", s)
    if m and 1 <= int(m.group(2)) <= 12:
        return end(int(m.group(1)), int(m.group(2)))
    m = re.search(r"(?:FY)?((?:19|20)\d{2})|FY(\d{2})", s)
    if m:
        return end(int(m.group(1) or ("20" + m.group(2))), 12)
    return ""


def table_unit(t: dict) -> tuple:
    """表的金額單位 → (乘數換成百萬, 幣別, 來源)。"""
    hdr = " ".join(str(c) for r in (t.get("raw_rows") or [])[:2] for c in r[:2]) + " " + " ".join(str(x) for x in (t.get("notes") or [])[:3])
    cur = "US$" if re.search(r"(?i)US\$|USD", hdr) else "NT$"
    if re.search(r"(?i)\b(bn|billion)\b|十億", hdr):
        return 1000.0, cur, "表頭 bn"
    if re.search(r"千元|(?i:thousand|'000|\(000\))", hdr):
        return 0.001, cur, "表頭 千元"
    if re.search(r"億", hdr):
        return 100.0, cur, "表頭 億"
    if re.search(r"(?i)\$\s*m\b|\bmn\b|\bm\b|million|百萬", hdr):
        return 1.0, cur, "表頭 百萬"
    return 1.0, cur, "表頭沒寫 → 預設百萬"


def _lex_book() -> dict:
    home = (_home or (lambda: HERE))()
    fs = []
    for d in (home / "SSOT", home / "knowledge"):
        fs += list(d.glob("VRN_FinLexicon_SSOT_v*.json")) if d.is_dir() else []
    fs = sorted(fs, key=_vnum_v0180)
    out = {}
    if fs:
        try:
            for r in json.loads(fs[-1].read_text(encoding="utf-8")).get("rows", []):
                out[r["std"]] = {"zh": (r.get("zh") or [""])[0], "cat": r.get("cat", "")}
        except (OSError, ValueError, KeyError):
            pass
    return out


def row_unit(std: str, label: str, cat: str, mult: float, cur: str, src: str) -> tuple:
    lab = "%s %s" % (std, label)
    if cat == "PS" or _PER_SHARE.search(lab):
        return "%s/股" % cur, 1.0, "每股"
    if _MULT.search(lab):
        return "x", 1.0, "倍數"
    if cat == "RATIO" or _RATIO.search(lab):
        return "%", 1.0, "比率"
    return "%s MN" % cur, mult, src


def _dec(x) -> int:
    t = ("%.6f" % abs(float(x))).rstrip("0")
    return min(len(t.split(".")[1]) if "." in t else 0, 4)


def _tolp(target, *ops) -> float:
    """容許誤差依顯示精度:整數 → 1.5 · 一位小數 → 0.15 …(億 / bn 小數字的表不再被「至少 1」放過)· 再跟 1.5% 相對誤差取大。"""
    d = max((_dec(v) for v in (target,) + ops if isinstance(v, (int, float))), default=0)
    return max(1.5 * 10 ** (-d), abs(target) * 0.015)


def fin_tests_v180(rows: list) -> list:
    out = fin_tests_v180._prev(rows)
    M = defaultdict(dict)
    for r in rows:
        if r.get("std"):
            for c in r.get("cells") or []:
                if isinstance(c.get("value"), (int, float)) and c["period"] not in M[r["std"]]:
                    M[r["std"]][c["period"]] = float(c["value"])
    g = lambda k, p: M.get(k, {}).get(p)  # noqa: E731
    for x in out:
        if x.get("kind") != "加減法":
            continue
        p = x["period"]
        if x["rule"] == "毛利 = 營收 − 成本":
            t, c, ops = g("gross_profit", p), g("revenue", p) - abs(g("cogs", p)), (g("revenue", p), g("cogs", p))
        elif x["rule"] == "營益 = 毛利 − 營業費用":
            t, c, ops = g("operating_income", p), g("gross_profit", p) - abs(g("opex", p)), (g("gross_profit", p), g("opex", p))
        elif x["rule"] == "稅前 = 營益 + 業外":
            t, c, ops = g("pretax_income", p), g("operating_income", p) + g("nonop_income", p), (g("operating_income", p), g("nonop_income", p))
        elif x["rule"] == "資產 = 負債 + 權益":
            t, c, ops = g("total_assets", p), g("total_liabilities", p) + g("equity", p), (g("total_liabilities", p), g("equity", p))
        else:
            continue
        x["status"] = "PASS" if abs(c - t) <= _tolp(t, *ops) else "FAIL"
        x["detail"] = "%s vs %s(容許 %.3g)" % (t, round(c, 4), _tolp(t, *ops))
    return out


def _patch_v(name: str, fn):
    import functools
    mo = _owner(name)
    if mo is None or getattr(vars(mo)[name], "_v180", False):
        return None
    prev = vars(mo)[name]
    functools.update_wrapper(fn, prev)
    fn._v180 = True
    fn._prev = prev
    setattr(mo, name, fn)
    return prev


_patch_v("fin_tests", fin_tests_v180)


def findata2_run(basic2: dict = None) -> dict:
    rep = _rep()
    lex = _lex_book()
    if basic2 is None:
        bp = rep / "basicinfo" / "BASIC_INFO_V2_latest.json"
        basic2 = {}
        if bp.exists():
            for r in json.loads(bp.read_text(encoding="utf-8")).get("records", []):
                fd = r.get("fields") or {}
                basic2[(fd.get("FILENAME") or {}).get("value")] = {k: (fd.get(k) or {}).get("value") for k in ("TICKER", "YF_TICKER", "BBG_TICKER", "NAME_DB", "NAME_EN_DB", "REPORT_DATE")}
    eps_c, fin_t = _resolve("eps_classify"), _resolve("fin_tests")
    ptype = _resolve("ptype") or (lambda p: "歷史")
    dbe = (_resolve("db_eps") or (lambda: {}))()
    out = []
    for f in sorted((rep / "restore").glob("*.json")) if (rep / "restore").is_dir() else []:
        if f.name.startswith("RESTORE_"):
            continue
        dj = json.loads(f.read_text(encoding="utf-8"))
        meta = dj.get("document_meta") or {}
        fn = meta.get("file") or f.stem
        b = basic2.get(fn) or {}
        code = str(b.get("TICKER") or meta.get("ticker") or "")
        for t in dj.get("tables", []):
            if t.get("status") == "未過" or not t.get("rows"):
                continue
            rows = t["rows"]
            mult, cur, usrc = table_unit(t)
            ec = {i: c for i, c, _ in (eps_c(rows, code, dbe) if eps_c else [])}
            tests = fin_t(rows) if fin_t else []
            res = defaultdict(lambda: {"加減法": [], "除法": []})
            for x in tests:
                parts = PARTS.get(x["rule"]) or ({re.sub(r" 成長.*$", "", x["rule"])} | {k for k, v in (_resolve("_GROWTH_BASE") or {}).items() if v == re.sub(r" 成長.*$", "", x["rule"])})
                for s in parts:
                    res[(s, x["period"])][x["kind"]].append(x["status"])
            for i, r in enumerate(rows):
                std = r.get("std") or ""
                acc = {"DILUTED_EPS": "diluted_eps", "BASIC_EPS": "basic_eps"}.get(ec.get(i), std) or re.sub(r"\s+", " ", str(r.get("label_raw") or "")).strip()   # 未分 → 維持 eps(EPS_CLASS 欄記未分)
                cat = (lex.get(std) or {}).get("cat") or r.get("cat") or ""
                unit, k, src = row_unit(std, str(r.get("label_raw") or ""), cat, mult, cur, usrc)
                for c in r.get("cells") or []:
                    v = c.get("value")
                    if not isinstance(v, (int, float)):
                        continue
                    pt = ptype(c.get("period"))
                    tr = res.get((std, c.get("period"))) or {"加減法": [], "除法": []}
                    cell = lambda kind: "%s·%s" % (pt, "FAIL" if "FAIL" in tr[kind] else ("PASS" if "PASS" in tr[kind] else "未驗"))  # noqa: E731
                    a, dv = cell("加減法"), cell("除法")
                    light = "RED" if ("FAIL" in a or "FAIL" in dv) else ("GREEN" if ("PASS" in a or "PASS" in dv) and std and "預設" not in src else "YELLOW")
                    out.append({"DATE": period_date(c.get("period")), "FILENAME": fn, "TICKER": code, "YF_TICKER": b.get("YF_TICKER") or "", "BBG_TICKER": b.get("BBG_TICKER") or (code + " TT" if code else ""),
                                "NAME": b.get("NAME_DB") or "", "ENGLISH_NAME": b.get("NAME_EN_DB") or "", "FINANCIAL_STATEMENT": _STMT.get(cat, (t.get("category") or "其他")),
                                "ACCOUNT": acc, "UNIT": unit, "VALUE": round(float(v) * k, 2), "ADDSUB_TEST": a, "DIV_TEST": dv, "THREE_LIGHT": light,
                                "REPORT_DATE": b.get("REPORT_DATE") or "", "PERIOD_RAW": c.get("period"), "ACCOUNT_ZH": (lex.get(std) or {}).get("zh", ""), "ACCOUNT_RAW": r.get("label_raw"),
                                "EPS_CLASS": ec.get(i, ""), "TABLE": t.get("id"), "UNIT_SRC": src, "VALUE_RAW": v})
    od = rep / "findata"
    od.mkdir(parents=True, exist_ok=True)
    (od / "FINANCIAL_DATA_FINAL_latest.json").write_text(json.dumps({"columns": COLS4, "extra": EXTRA4, "rows": out}, ensure_ascii=False, default=str), encoding="utf-8")
    cp = od / "FINANCIAL_DATA_FINAL_latest.csv"
    with cp.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS4 + EXTRA4)
        w.writeheader()
        w.writerows(out)
    try:
        import duckdb  # noqa: WPS433
        duckdb.connect().execute("copy (select * from read_csv_auto('%s', header=true, all_varchar=true)) to '%s' (format parquet)" % (str(cp).replace("'", "''"), str(cp.with_suffix(".parquet")).replace("'", "''")))
    except Exception:  # noqa: BLE001
        pass
    page = _resolve("_page")
    if page:
        (od / "FINANCIAL_DATA_FINAL_latest.html").write_text(page("FINANCIAL DATA(最終欄位 · 一格一列 · 金額百萬 · 小數點兩位 · 每列三燈)", "%d 列 · 前 3000 列(完整在 CSV / parquet)" % len(out),
                                                                  COLS4, [(r["THREE_LIGHT"], [html.escape(str(r[k])) for k in COLS4]) for r in out[:3000]]), encoding="utf-8")
    L = Counter(r["THREE_LIGHT"] for r in out)
    T = Counter((kind, r[col].split("·")[0], r[col].split("·")[1]) for r in out for kind, col in (("加減", "ADDSUB_TEST"), ("除法", "DIV_TEST")))
    return {"rows": len(out), "lights": dict(L), "T": {"%s|%s|%s" % k: v for k, v in T.items()}, "units": dict(Counter(r["UNIT"] for r in out)),
            "unit_default": sum(1 for r in out if "預設" in r["UNIT_SRC"]), "unmapped": len({r["ACCOUNT"] for r in out if not r["ACCOUNT_ZH"] and not r["EPS_CLASS"]}),
            "no_date": sum(1 for r in out if not r["DATE"]), "html": str(od / "FINANCIAL_DATA_FINAL_latest.html")}


def _lines_v180(o: dict) -> list:
    T = Counter()
    for k, v in (o.get("T") or {}).items():
        T[tuple(k.split("|"))] = v
    L = ["[計] FINANCIAL DATA(最終 · 一格一列)· %d 列 · 三燈 GREEN %d · YELLOW %d · RED %d · 單位 %s · 單位預設百萬 %d 列 · 未對到標準科目 %d 種 · 沒有期末日 %d 列" % (
        o["rows"], o["lights"].get("GREEN", 0), o["lights"].get("YELLOW", 0), o["lights"].get("RED", 0), " · ".join("%s %d" % kv for kv in Counter(o["units"]).most_common(4)),
        o["unit_default"], o["unmapped"], o["no_date"])]
    for kind in ("加減", "除法"):
        L.append("[計] %s測試(每列 2 選 1)· 歷史 PASS %d / FAIL %d / 未驗 %d · 預估 PASS %d / FAIL %d / 未驗 %d" % (kind, T[(kind, "歷史", "PASS")], T[(kind, "歷史", "FAIL")], T[(kind, "歷史", "未驗")],
                                                                                         T[(kind, "預估", "PASS")], T[(kind, "預估", "FAIL")], T[(kind, "預估", "未驗")]))
    return L


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    if "--selftest" in args[:2]:
        return selftest()
    if args[:1] == ["findata2"] or (args[:1] in (["auto"], ["findata"]) and "--resume" not in args):
        rc = PRIOR.main(args) if args[:1] != ["findata2"] else 0
        o = findata2_run()
        L = _lines_v180(o)
        for l in L:
            print(l)
        print("  [U/I] %s" % o["html"])
        if args[:1] == ["auto"]:
            pk = _rep() / "auto" / "VRN_AI_PACK_latest.md"
            if pk.exists():
                old = [l for l in pk.read_text(encoding="utf-8").splitlines() if l.strip()]
                nxt = [l for l in old if l.startswith("NEXT:")] or ["NEXT: 依本包修 → 再跑 auto"]
                pk.write_text("\n".join(([l for l in old if not l.startswith("NEXT:")] + L)[:299] + nxt[:1]) + "\n", encoding="utf-8")
                ac = _resolve("aiverb_compress")
                if ac:
                    print("[計] AI 包(含 FINANCIAL DATA 最終)· %s" % ac(pk, nxt[0].replace("NEXT: ", ""))[1])
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
    R0 = lambda lab, std, vals: {"label_raw": lab, "std": std, "cells": [{"period": k, "value": v} for k, v in vals.items()]}  # noqa: E731
    ft = _resolve("fin_tests")([R0("Rev", "revenue", {"2025F": 12.0}), R0("COGS", "cogs", {"2025F": -7.0}), R0("GP", "gross_profit", {"2025F": 4.5})])
    ft2 = _resolve("fin_tests")([R0("Rev", "revenue", {"2025F": 36828}), R0("COGS", "cogs", {"2025F": -25460}), R0("GP", "gross_profit", {"2025F": 11369})])
    chk("⓪ 容許誤差依顯示精度:億表 12 − 7 = 5 vs 4.5 → 不符(舊版「至少 1」會放過)· 百萬整數表 36828 − 25460 = 11368 vs 11369 → 四捨五入差 1 照過",
        ft and ft[0]["status"] == "FAIL" and ft2 and ft2[0]["status"] == "PASS")
    pd = {x: period_date(x) for x in ("2025F", "2024A", "FY25", "4Q25E", "1Q26", "25Q2", "1H26", "Dec-24A", "Mar-25", "2024/06", "2025(F)", "NT$m")}
    chk("① DATE = 期間期末日:%s" % " · ".join("%s→%s" % kv for kv in list(pd.items())[:9]),
        pd["2025F"] == "2025-12-31" and pd["2024A"] == "2024-12-31" and pd["FY25"] == "2025-12-31" and pd["4Q25E"] == "2025-12-31" and pd["1Q26"] == "2026-03-31" and pd["25Q2"] == "2025-06-30"
        and pd["1H26"] == "2026-06-30" and pd["Dec-24A"] == "2024-12-31" and pd["Mar-25"] == "2025-03-31" and pd["2024/06"] == "2024-06-30" and pd["2025(F)"] == "2025-12-31" and pd["NT$m"] == "")
    u = [table_unit({"raw_rows": [[h, "2025F"]]})[0] for h in ("(NT$ 千元)", "單位:億元", "NT$bn", "NT$m", "Item")]
    chk("② 金額一律換算百萬:千元 ×0.001 · 億 ×100 · bn ×1000 · NT$m ×1 · 沒寫 → 預設 ×1(標黃)", u == [0.001, 100.0, 1000.0, 1.0, 1.0] and "預設" in table_unit({"raw_rows": [["Item"]]})[2])
    chk("③ 每股 / 比率 / 倍數不換算:EPS → NT$/股 · 毛利率 → % · 本益比 → x · 營收 → NT$ MN",
        row_unit("eps", "EPS", "IS", 100.0, "NT$", "")[0] == "NT$/股" and row_unit("gross_margin", "Gross margin %", "RATIO", 100, "NT$", "")[0] == "%"
        and row_unit("", "P/E (x)", "", 100, "NT$", "")[0] == "x" and row_unit("revenue", "營業收入", "IS", 100.0, "NT$", "表頭 億")[:2] == ("NT$ MN", 100.0))
    td = Path(tempfile.mkdtemp(prefix="vrn180-"))
    saved = os.environ.get("VIA_VRN_HEALTH_OUT")
    try:
        os.environ["VIA_VRN_HEALTH_OUT"] = str(td / "rep")
        (td / "rep" / "restore").mkdir(parents=True)
        R = lambda lab, std, vals: {"label_raw": lab, "std": std, "cells": [{"period": k, "value": v} for k, v in vals.items()]}  # noqa: E731
        rows = [R("營業收入", "revenue", {"2024A": 10.0, "2025F": 12.0}), R("營業成本", "cogs", {"2024A": -6.0, "2025F": -7.0}), R("營業毛利", "gross_profit", {"2024A": 4.0, "2025F": 4.5}),
                R("毛利率", "gross_margin", {"2024A": 40.0, "2025F": 37.5}), R("EPS", "eps", {"2024A": 2.5, "2025F": 3.0})]
        (td / "rep" / "restore" / "01_x.json").write_text(json.dumps({"document_meta": {"file": "X.pdf", "ticker": "6488"},
                                                                     "tables": [{"id": "T1", "status": "還原無誤", "category": "財務表(損益)", "raw_rows": [["單位:億元", "2024A", "2025F"]], "rows": rows}]}, ensure_ascii=False), encoding="utf-8")
        o = findata2_run(basic2={"X.pdf": {"TICKER": "6488", "YF_TICKER": "6488.TWO", "BBG_TICKER": "6488 TT", "NAME_DB": "環球晶", "NAME_EN_DB": "GlobalWafers", "REPORT_DATE": "2025-05-19"}})
        js = json.loads((td / "rep" / "findata" / "FINANCIAL_DATA_FINAL_latest.json").read_text(encoding="utf-8"))["rows"]
        hdr = (td / "rep" / "findata" / "FINANCIAL_DATA_FINAL_latest.csv").read_text(encoding="utf-8-sig").splitlines()[0].split(",")
        g = {(r["ACCOUNT"], r["PERIOD_RAW"]): r for r in js}
        rv, gp25, gm25, ep = g[("revenue", "2025F")], g[("gross_profit", "2025F")], g[("gross_margin", "2025F")], g[("eps", "2024A")]
        chk("④ 一格一列 · 欄序照規格 · 營收 12 億 → 1200.00 NT$ MN · DATE 2025-12-31 · 名稱 環球晶 / GlobalWafers · 6488.TWO", hdr[:14] == COLS4 and rv["VALUE"] == 1200.0 and rv["UNIT"] == "NT$ MN"
            and rv["DATE"] == "2025-12-31" and rv["NAME"] == "環球晶" and rv["ENGLISH_NAME"] == "GlobalWafers" and rv["YF_TICKER"] == "6488.TWO")
        chk("⑤ 測試連到每一列(2 選 1):2024A 毛利 4 = 10 − 6 → 歷史·PASS · GREEN;2025F 毛利 4.5 ≠ 12 − 7 = 5 → 預估·FAIL · RED;毛利率 37.5 vs 4.5 / 12 = 37.5%% → 預估·PASS 但營收 / 毛利那條加減不符 → 毛利率列 %s" % gm25["THREE_LIGHT"],
            g[("gross_profit", "2024A")]["ADDSUB_TEST"] == "歷史·PASS" and g[("gross_profit", "2024A")]["THREE_LIGHT"] == "GREEN" and gp25["ADDSUB_TEST"] == "預估·FAIL" and gp25["THREE_LIGHT"] == "RED"
            and gm25["DIV_TEST"] == "預估·PASS")
        chk("⑥ EPS 不換算(NT$/股 · 2.50)· 沒有可測的恆等式 → 加減 / 除法 歷史·未驗 → YELLOW(沒測到 ≠ 通過)",
            ep["UNIT"] == "NT$/股" and ep["VALUE"] == 2.5 and ep["ADDSUB_TEST"] == "歷史·未驗" and ep["THREE_LIGHT"] == "YELLOW")
    finally:
        if saved is None:
            os.environ.pop("VIA_VRN_HEALTH_OUT", None)
        else:
            os.environ["VIA_VRN_HEALTH_OUT"] = saved
        shutil.rmtree(td, ignore_errors=True)
    me = Path(__file__).read_text(encoding="utf-8")
    chk("⑦ 最新有版號加速器橋 [VIA:ACCEL-BRIDGE:v0111] · 自帶多程序墊片", "[VIA:ACCEL-BRIDGE:v0111]" in me and _job_entry.__module__ in ("__main__", __name__))
    print("  ── 前版鏈自測(原樣印出)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("⑧ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    print("[計] VRN_SystemManager_v0180 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
