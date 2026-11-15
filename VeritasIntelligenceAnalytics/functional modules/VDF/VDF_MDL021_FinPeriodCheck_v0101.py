#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_MDL021_FinPeriodCheck v0101 — 財報期別核對:累計(年初至今)· 單季 · 年度 三者互相對帳(金額一律百萬元)

v0100 → v0101(v0100 已隨 PR 652 發布,一字不動;本版是完整新版,不是薄尾):
  ① PR 652 Codex P1:交易所 tw_financial_mops 讀 unit 欄換算(ENG082 存仟元),yfinance 原幣元也換到同一尺度;每股類不換。
  ② PR 652 Codex P2:科目名先正規化(全形括號 / 空白)再對照 —— 正式標籤「基本每股盈餘（元）」認得。
  ③ PR 652 Codex P2:指定的代號整檔沒有財報列 → 照列黃「整檔沒有財報列」,總燈不會綠。
  ④ 操作員 2026-11-15:「金額部分用百萬元為單位,小數點後不設限,但顯示要有千分位號,小數點後一位,顯示才規範」→
     單位 · 換算 · 金額容差 · 顯示格式放 VDF 新冊 VDF_FinPeriod_SSOT 尾版(fin_period 段,疊在 VDF_DataPlane_SSOT 尾版
     fin_period 之上);VDF_DataPlane_SSOT_v0102 不動(MDL020 v0102 自測釘它)。

操作員 2026-11-15:「3017 3324 NVDA 財報累計 單季 年度測試」。
  台股交易所 MOPS 損益表是「年初至今累計」(VDF_ENG082 存 tw_financial_mops · basis=YTD);yfinance 給單季與年度(tw_financial ·
  Period_Type quarterly / annual)。美股(NVDA)會計年度不是曆年(年度結束在 1 月底)。本支把三種期別對齊到「會計年度 × 季」再互核:
    單季 = 累計拆:Q1 = YTD1 · Qn = YTDn − YTDn-1
    K1 年度 = 第 4 季累計(兩邊都有才比)
    K2 年度 = 四個單季加總(單季用報的;沒有就用累計拆出來的)
    K3 累計拆出的單季 = 報的單季(兩邊都有才比)
    EPS 季加總與年度只看差幾 %(各季加權股數不同,本來就不會剛好相等;超過 3% 才黃)
  金額一律換成百萬元(交易所仟元 ÷1,000 · yfinance 原幣元 ÷1,000,000;每股類不換);存值小數不設限,顯示千分位 · 小數一位(EPS 兩位)。
  容差:金額 max(0.001 百萬元, 0.5%)· EPS max(0.01, 0.5%)。缺期照實列「缺」,不補不猜。
資料來源(唯讀):資料家正典庫 vdf_tw_market 的 tw_financial_mops / tw_financial(有就讀);或 --file 給 csv / parquet(長表:ticker ·
  period_end · kind(YTD | Q | FY)· item · value [· unit])。會計年度結束月與科目對照放 VDF 自己的冊 VDF_DataPlane_SSOT 尾版(fin_period 段);
  金額單位 · 換算 · 金額容差 · 顯示格式放 VDF_FinPeriod_SSOT 尾版(fin_period 段,疊上去);冊上沒有用內建。
用法:run [--home 資料家] [--tickers 3017,3324,NVDA] [--file 長表] [--fy-end NVDA=1] | --selftest
輸出:VIA_Reports/vdf/VDF_FIN_PERIOD_CHECK_latest.html / .json(卡片 = 每檔大概 · 矩陣 = 年 × 季 × 科目明細)。
零網路(擷取由 ENG082 · 同意閘操作員設)· 不碰 TA-Lib · 不寫任何庫。
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

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)。本支零外呼。"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import html
import json
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
TAG = "VDF_MDL021_FinPeriodCheck v" + Path(__file__).stem.rsplit("_v", 1)[-1]
OUT = VIA / "VIA_Reports" / "vdf"
DEFAULT = {"fy_end_month": {"NVDA": 1}, "default_fy_end_month": 12,
           "items": {"revenue": {"mops": ["營業收入合計", "營業收入"], "yf": "Revenue"},
                     "net_income": {"mops": ["本期淨利(淨損)", "本期淨利", "本期稅後淨利(淨損)"], "yf": "Net_Income"},
                     "eps": {"mops": ["基本每股盈餘(元)", "基本每股盈餘"], "yf": "EPS"}},
           "tol": {"amount_abs": 0.001, "amount_rel": 0.005, "eps_abs": 0.01, "eps_rel": 0.005, "eps_sum_warn": 0.03},
           "amount_unit": "百萬元", "display": {"amount": "千分位 · 小數一位", "eps": "小數兩位"},
           "unit_scale": {"仟元": 0.001, "千元": 0.001, "百萬元": 1.0, "元": 1e-6}, "unit_scale_blank": 1e-6, "yfinance_scale": 1e-6}
LAYER_GLOB = "VDF_FinPeriod_SSOT_v*.json"           # 金額單位層(v0101 起;疊在 VDF_DataPlane_SSOT 尾版 fin_period 之上)
LAMP_RANK = {"RED": 3, "YELLOW": 2, "GREEN": 1, "GRAY": 0}


def _tail_section(pattern: str, getter) -> tuple:
    for b in sorted(HERE.glob(pattern), key=lambda p: p.stem, reverse=True):
        try:
            fp = getter(json.loads(b.read_text(encoding="utf-8")))
        except (OSError, ValueError, AttributeError):
            fp = None
        if fp:
            return fp, b.name
    return None, None


def params() -> tuple:
    """VDF 自己的冊:VDF_DataPlane_SSOT 尾版 fin_period(會計年度 · 科目 · EPS 容差)→ 疊 VDF_FinPeriod_SSOT 尾版 fin_period
    (金額單位 · 換算 · 金額容差 · 顯示);容差逐鍵疊,不整段蓋。都沒有用內建。"""
    pm, src = dict(DEFAULT), []
    base, b1 = _tail_section("VDF_DataPlane_SSOT_v*.json", lambda d: (d.get("params") or {}).get("fin_period"))
    layer, b2 = _tail_section(LAYER_GLOB, lambda d: d.get("fin_period"))
    for sec, name in ((base, b1), (layer, b2)):
        if sec:
            tol = {**pm["tol"], **(sec.get("tol") or {})}
            pm.update(sec)
            pm["tol"] = tol
            src.append(name)
    return pm, " + ".join(src) or "內建預設"


def _scale(unit, pm: dict):
    """單位 → 換成百萬元的倍數;空白當元;不認得回 None(那列不比)。"""
    if unit is None or str(unit).strip() == "":
        return float(pm.get("unit_scale_blank", 1e-6))
    return (pm.get("unit_scale") or {}).get(str(unit).strip())


def fiscal(d: date, fye: int) -> tuple:
    """期末日 → (會計年度, 季)。fye = 會計年度結束月(曆年 12 · NVDA 1)。"""
    fy = d.year if d.month <= fye else d.year + 1
    if fye == 12:
        fy = d.year
    fq = ((d.month - fye - 1) % 12) // 3 + 1
    return fy, fq


def _d(s) -> date | None:
    m = re.match(r"(\d{4})-?(\d{2})-?(\d{2})", str(s or ""))
    if m:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    m = re.match(r"(\d{4})Q([1-4])", str(s or ""))
    if m:
        return date(int(m.group(1)), int(m.group(2)) * 3, 28)
    return None


def canon_ticker(t) -> str:
    """代號正規化(兩邊同一把尺):去 .TW / .TWO 後綴 · 去空白 · 大寫。--file 長表 · 正典庫 · --tickers 都經這裡。"""
    return re.sub(r"\.TWO?$", "", str(t).strip(), flags=re.I).upper()


def normalize(rows: list, pm: dict) -> dict:
    """長表列 {ticker, period_end, kind(YTD|Q|FY), item, value} → {(ticker, item): {fy: {"YTD": {q: v}, "Q": {q: v}, "FY": v}}}"""
    out = {}
    for r in rows:
        d = _d(r.get("period_end"))
        if d is None or r.get("value") is None:
            continue
        t = canon_ticker(r["ticker"])
        fye = int((pm["fy_end_month"] or {}).get(t, pm["default_fy_end_month"]))
        fy, fq = fiscal(d, fye)
        slot = out.setdefault((t, r["item"]), {}).setdefault(fy, {"YTD": {}, "Q": {}, "FY": None})
        k = str(r["kind"]).upper()
        if k == "FY":
            slot["FY"] = float(r["value"])
        elif k in ("YTD", "Q"):
            slot[k][fq] = float(r["value"])
    return out


# 金額一律換成「百萬元」再比(操作員 2026-11-15「金額部分用百萬元為單位,小數點後不設限」);存值不四捨五入,只有顯示才規範。
# 換算表正本在 VDF_FinPeriod_SSOT 尾版 fin_period.unit_scale(_scale 讀 pm);這裡留同值給舊呼叫者對照。
UNIT_SCALE = {"仟元": 0.001, "千元": 0.001, "百萬元": 1.0, "元": 1e-6, "": 1e-6, None: 1e-6}


def norm_label(s) -> str:
    """科目名正規化:全形括號 / 冒號 → 半形 · 去空白(ENG082 照原文存「基本每股盈餘（元）」)。"""
    return re.sub(r"\s+", "", str(s or "").replace("（", "(").replace("）", ")").replace("：", ":"))


def _close(a, b, item, tol) -> bool:
    if item == "eps":
        return abs(a - b) <= max(tol["eps_abs"], tol["eps_rel"] * abs(b))
    return abs(a - b) <= max(tol["amount_abs"], tol["amount_rel"] * abs(b))


def check(series: dict, pm: dict) -> list:
    """每檔 × 科目 × 會計年度:拆單季 · K1 / K2 / K3 · 缺期照列。"""
    tol = pm["tol"]
    res = []
    for (t, item), years in sorted(series.items()):
        for fy, s in sorted(years.items()):
            ytd, q, fyv = s["YTD"], dict(s["Q"]), s["FY"]
            derived = {}
            for n in range(1, 5):
                if n in ytd and (n == 1 or (n - 1) in ytd):
                    derived[n] = ytd[n] - (ytd[n - 1] if n > 1 else 0.0)
            single = {n: q.get(n, derived.get(n)) for n in range(1, 5) if n in q or n in derived}
            checks = []
            if fyv is not None and 4 in ytd:
                checks.append(("K1 年度 = 第 4 季累計", "GREEN" if _close(ytd[4], fyv, item, tol) else "RED", "Q4 累計 %s · 年度 %s" % (ytd[4], fyv)))
            if fyv is not None and len(single) == 4:
                s4 = sum(single.values())
                if item == "eps":
                    gap = abs(s4 - fyv) / abs(fyv) if fyv else 0.0
                    checks.append(("K2 EPS 四季加總 ≈ 年度(加權股數不同)", "GREEN" if gap <= tol["eps_sum_warn"] else "YELLOW", "四季和 %.4f · 年度 %s · 差 %.2f%%" % (s4, fyv, gap * 100)))
                else:
                    checks.append(("K2 年度 = 四個單季加總", "GREEN" if _close(s4, fyv, item, tol) else "RED", "四季和 %s · 年度 %s" % (round(s4, 4), fyv)))
            for n in sorted(set(q) & set(derived)):
                if item != "eps":
                    checks.append(("K3 Q%d 累計拆出 = 報的單季" % n, "GREEN" if _close(derived[n], q[n], item, tol) else "RED", "拆 %s · 報 %s" % (round(derived[n], 4), q[n])))
            missing = [("Q%d" % n) for n in range(1, 5) if n not in single] + ([] if fyv is not None or 4 in ytd else ["年度"])
            lamp = max([c[1] for c in checks] + (["YELLOW"] if missing else []) + (["GRAY"] if not checks and not missing else []), key=lambda x: LAMP_RANK[x]) if (checks or missing) else "GRAY"
            res.append({"ticker": t, "item": item, "fy": fy, "ytd": ytd, "q_reported": q, "q_derived": derived, "single": single, "fy_value": fyv,
                        "checks": [{"name": a, "lamp": b, "note": c} for a, b, c in checks], "missing": missing, "lamp": lamp})
    return res


def read_db(home: Path, tickers: list, pm: dict) -> tuple:
    """資料家正典庫(唯讀):tw_financial_mops(累計)+ tw_financial(單季 / 年度)→ 長表列。庫不在 / 表不在照實回。"""
    import duckdb
    dbs = [p for pat in ("vdf_tw_market.duckdb", "*/vdf_tw_market.duckdb", "*/*/vdf_tw_market.duckdb", "*/*/*/vdf_tw_market.duckdb") for p in Path(home).glob(pat)]
    if not dbs:
        return [], "資料家沒有 vdf_tw_market.duckdb"
    con = duckdb.connect(str(sorted(dbs, key=lambda p: ("mega" not in p.parts, -p.stat().st_size))[0]), read_only=True)
    rows, notes = [], []
    try:
        tabs = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
        codes = [re.sub(r"\.TWO?$", "", t, flags=re.I) for t in tickers]
        if "tw_financial_mops" in tabs:
            mops_map = {norm_label(lab): key for key, v in pm["items"].items() for lab in v.get("mops") or []}
            mcols = {r[0] for r in con.execute("DESCRIBE tw_financial_mops").fetchall()}
            ucol = "unit" if "unit" in mcols else "NULL"
            q = "SELECT code, period, item, value, %s FROM tw_financial_mops WHERE basis = 'YTD' AND code IN (%s)" % (ucol, ",".join("?" * len(codes)))
            for code, period, item, val, unit in con.execute(q, codes).fetchall():
                key = mops_map.get(norm_label(item))
                if key is None or val is None:
                    continue
                if key != "eps":                                   # 金額:交易所仟元 → 百萬元;每股類照元
                    scale = _scale(unit, pm)
                    if scale is None:
                        notes.append("不認得的單位 %s(%s)· 這列不比" % (unit, item))
                        continue
                    val = float(val) * scale
                rows.append({"ticker": code, "period_end": period, "kind": "YTD", "item": key, "value": val})
        else:
            notes.append("沒有 tw_financial_mops(交易所累計)")
        if "tw_financial" in tabs:
            yf = {v["yf"]: k for k, v in pm["items"].items() if v.get("yf")}
            cols = [r[0] for r in con.execute("DESCRIBE tw_financial").fetchall()]
            want = [c for c in yf if c in cols]
            if want:
                q = "SELECT Ticker, Period, Period_Type, %s FROM tw_financial WHERE regexp_replace(upper(Ticker), '\\.TWO?$', '') IN (%s)" % (
                    ", ".join('"%s"' % c for c in want), ",".join("?" * len(codes)))
                for r in con.execute(q, [c.upper() for c in codes]).fetchall():
                    kind = "FY" if str(r[2]).lower().startswith("annual") else "Q"
                    for i, c in enumerate(want):
                        if r[3 + i] is not None:
                            v = float(r[3 + i]) if yf[c] == "eps" else float(r[3 + i]) * float(pm.get("yfinance_scale", 1e-6))   # yfinance 原幣元 → 百萬元
                            rows.append({"ticker": re.sub(r"\.TWO?$", "", str(r[0]), flags=re.I), "period_end": r[1], "kind": kind, "item": yf[c], "value": v})
        else:
            notes.append("沒有 tw_financial(單季 / 年度)")
    finally:
        con.close()
    return rows, " · ".join(notes) or "ok"


def read_file(path: Path, pm: dict | None = None) -> list:
    """長表(csv / parquet)。有 unit 欄就換成百萬元(不認得的單位那列不比);沒有 unit 欄 = 當作已是百萬元。"""
    pm = pm or params()[0]
    import duckdb
    rel = "read_parquet('%s')" % str(path).replace("'", "''") if str(path).endswith(".parquet") else "read_csv_auto('%s')" % str(path).replace("'", "''")
    con = duckdb.connect()
    try:
        cols = {r[0] for r in con.execute("DESCRIBE SELECT * FROM %s" % rel).fetchall()}
        cur = con.execute("SELECT ticker, period_end, kind, item, value, %s FROM %s" % ("unit" if "unit" in cols else "NULL", rel))
        out = []
        for t, pe, k, it, v, u in cur.fetchall():
            if v is not None and it != "eps" and "unit" in cols:
                sc = _scale(u, pm)
                if sc is None:
                    continue
                v = float(v) * sc
            out.append({"ticker": t, "period_end": pe, "kind": k, "item": it, "value": v})
        return out
    finally:
        con.close()


def _e(x) -> str:
    return html.escape("" if x is None else str(x))


def _chip(lp) -> str:
    c = {"RED": "#dc2626", "YELLOW": "#f59e0b", "GREEN": "#16a34a"}.get(lp, "#9ca3af")
    return '<span style="display:inline-block;border-radius:5px;padding:0 6px;font-size:10.5px;color:#fff;background:%s">%s</span>' % (c, _e(lp))


def _fmt(v, item) -> str:
    """顯示規範(操作員 2026-11-15):金額(百萬元)千分位 · 小數一位;EPS 小數兩位。只管顯示,存值不動。"""
    if v is None:
        return "—"
    return ("%.2f" % v) if item == "eps" else format(v, ",.1f")


def page(res: list, meta: dict) -> str:
    css = ("body{font-family:system-ui,'Noto Sans TC',sans-serif;background:#f8f7f2;color:#26312f;max-width:1320px;margin:0 auto;padding:18px 16px}"
           ".h1{font-size:10.5px;letter-spacing:.14em;color:#6b7468}.h2{font-size:21px;font-weight:600;margin:2px 0}.h3{font-size:11.5px;color:#55605a}"
           ".sec{background:#fffefb;border:1px solid #dedfd5;border-radius:8px;padding:14px 16px;margin:14px 0}"
           ".cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:10px}.card{background:#fffefb;border:1px solid #dedfd5;border-radius:8px;padding:10px 12px}"
           ".scroll{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:11.5px}th,td{border-bottom:1px solid #e1e4dc;padding:5px 7px;text-align:right;white-space:nowrap}"
           "th{background:#eeeee7;font-size:10.5px}td.l,th.l{text-align:left}.small{font-size:10.5px;color:#6b7468}")
    p = ['<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
         '<meta name="via-page" content="VDF_FIN_PERIOD_CHECK"><title>VDF 財報期別核對</title><style>%s</style></head><body>' % css,
         '<div class="h1">VERITAS INTELLIGENCE ANALYTICS</div><div class="h2">VeritasDataForge</div>'
         '<div class="h3">財報期別核對 · 累計(年初至今)· 單季 · 年度 · 卡片看大概 · 矩陣看明細</div>']
    p.append('<p class="small">來源:%s · 冊 %s · %s</p>' % (_e(meta.get("source")), _e(meta.get("params")), _e(meta.get("ts"))))
    cards = []
    for t in sorted({r["ticker"] for r in res}):
        rs = [r for r in res if r["ticker"] == t]
        lamp = max((r["lamp"] for r in rs), key=lambda x: LAMP_RANK[x])
        fys = sorted({r["fy"] for r in rs})
        bad = sum(1 for r in rs for c in r["checks"] if c["lamp"] == "RED")
        miss = sum(len(r["missing"]) for r in rs)
        cards.append('<div class="card">%s <b>%s</b><div class="small">會計年度 %s · 對帳 %d 項 · 紅 %d · 缺期 %d</div></div>' % (
            _chip(lamp), _e(t), _e(" · ".join(map(str, fys))), sum(len(r["checks"]) for r in rs), bad, miss))
    p.append('<div class="sec"><b>卡片(每檔)</b><div class="cards">%s</div></div>' % "".join(cards))
    rows = []
    for r in res:
        it = r["item"]
        rows.append("<tr><td class='l'>%s</td><td class='l'>%s</td><td>%s</td>%s%s<td>%s</td><td class='l'>%s</td></tr>" % (
            _chip(r["lamp"]), _e("%s · %s" % (r["ticker"], it)), _e(r["fy"]),
            "".join("<td>%s</td>" % _fmt(r["ytd"].get(n), it) for n in range(1, 5)),
            "".join("<td>%s%s</td>" % (_fmt(r["single"].get(n), it), "" if n in r["q_reported"] or n not in r["q_derived"] else "<span class='small'>拆</span>") for n in range(1, 5)),
            _fmt(r["fy_value"], it),
            _e(" · ".join("%s %s(%s)" % (c["lamp"], c["name"], c["note"]) for c in r["checks"]) + ((" · 缺 " + "/".join(r["missing"])) if r["missing"] else ""))))
    p.append('<div class="sec"><b>矩陣(檔 × 科目 × 會計年度)</b><div class="scroll"><table><thead><tr><th class="l">燈</th><th class="l">檔 · 科目</th><th>會計年度</th>'
             '<th>累計 Q1</th><th>累計 Q2</th><th>累計 Q3</th><th>累計 Q4</th><th>單季 Q1</th><th>單季 Q2</th><th>單季 Q3</th><th>單季 Q4</th><th>年度</th><th class="l">對帳</th></tr></thead>'
             '<tbody>%s</tbody></table></div><p class="small">金額單位:百萬元(千分位 · 小數一位;EPS 元 · 小數兩位)· 「拆」= 由累計拆出的單季(沒有報的單季時才用)</p></div>' % "".join(rows))
    p.append("</body></html>")
    return "".join(p)


def run(rows: list, meta: dict, out_dir: Path = OUT) -> dict:
    pm, src = params()
    res = check(normalize(rows, pm), pm)
    have = {canon_ticker(r["ticker"]) for r in res}
    for t in meta.get("tickers") or []:                       # 指定了卻整檔沒資料:照列缺、不讓總燈變綠(兩邊同一把尺 canon_ticker)
        tt = canon_ticker(t)
        if tt and tt not in have:
            res.append({"ticker": tt, "item": "—", "fy": "—", "ytd": {}, "q_reported": {}, "q_derived": {}, "single": {}, "fy_value": None,
                        "checks": [], "missing": ["整檔沒有財報列"], "lamp": "YELLOW"})
    meta = dict(meta, params=src, ts=datetime.now(timezone.utc).isoformat(timespec="seconds"), tag=TAG)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "VDF_FIN_PERIOD_CHECK_latest.json").write_text(json.dumps({"meta": meta, "results": res}, ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8")
    (out_dir / "VDF_FIN_PERIOD_CHECK_latest.html").write_text(page(res, meta), encoding="utf-8")
    lamp = max([r["lamp"] for r in res] or ["GRAY"], key=lambda x: LAMP_RANK[x])
    return {"lamp": lamp, "results": res, "page": str(out_dir / "VDF_FIN_PERIOD_CHECK_latest.html")}


def _opt(a, k):
    return a[a.index(k) + 1] if k in a and a.index(k) + 1 < len(a) else None


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"]:
        return selftest()
    if args[:1] != ["run"]:
        print("[%s] 用法:run [--home 資料家] [--tickers 3017,3324,NVDA] [--file 長表] | --selftest" % TAG)
        return 2
    tickers = (_opt(args, "--tickers") or "3017,3324,NVDA").split(",")
    if _opt(args, "--file"):
        rows, src = read_file(Path(_opt(args, "--file"))), "--file " + _opt(args, "--file")
    else:
        home = _opt(args, "--home") or __import__("os").environ.get("VIA_VDF_DB_HOME")
        if not home:
            print("[%s] GRAY · 沒有資料家(--home 或 env VIA_VDF_DB_HOME)也沒有 --file" % TAG)
            return 2
        rows, src = read_db(Path(home), tickers, params()[0])
        src = "資料家 %s · %s" % (home, src)
    if not rows:
        print("[%s] GRAY · 沒讀到 %s 的財報列(%s)" % (TAG, ",".join(tickers), src))
        return 2
    r = run(rows, {"source": src, "tickers": tickers})
    print("[%s] %s · %s · %s" % (TAG, r["lamp"], src, r["page"]))
    for x in r["results"]:
        print("  [%-6s] %-5s %-10s FY%s · %s%s" % (x["lamp"], x["ticker"], x["item"], x["fy"], " · ".join("%s %s" % (c["lamp"], c["name"][:2]) for c in x["checks"]) or "—",
                                             (" · 缺 " + "/".join(x["missing"])) if x["missing"] else ""))
    return {"GREEN": 0, "YELLOW": 2, "GRAY": 2}.get(r["lamp"], 1)


def fixture_rows() -> list:
    """自測夾具:3017 / 3324 用「交易所累計 + 年度」形狀、NVDA 用「單季 + 年度 · 會計年度 1 月底結束」形狀;數字是示例,非真財報。"""
    rows = []
    for code, base in (("3017", 30000.0), ("3324", 10000.0)):
        qs = [base, base * 1.1, base * 1.2, base * 1.3]
        ni = [x * 0.12 for x in qs]
        eps = [round(x / 1000, 2) for x in ni]
        acc = 0.0
        for i, v in enumerate(qs, 1):
            acc += v
            rows.append({"ticker": code, "period_end": "2024Q%d" % i, "kind": "YTD", "item": "revenue", "value": acc})
        acc = 0.0
        for i, v in enumerate(ni, 1):
            acc += v
            rows.append({"ticker": code, "period_end": "2024Q%d" % i, "kind": "YTD", "item": "net_income", "value": acc})
        acc = 0.0
        for i, v in enumerate(eps, 1):
            acc = round(acc + v, 2)
            rows.append({"ticker": code, "period_end": "2024Q%d" % i, "kind": "YTD", "item": "eps", "value": acc})
        rows += [{"ticker": code, "period_end": "2024-12-31", "kind": "FY", "item": "revenue", "value": sum(qs)},
                 {"ticker": code, "period_end": "2024-12-31", "kind": "FY", "item": "net_income", "value": sum(ni)},
                 {"ticker": code, "period_end": "2024-12-31", "kind": "FY", "item": "eps", "value": round(sum(eps), 2)}]
    for end, v in (("2024-04-28", 26044.0), ("2024-07-28", 30040.0), ("2024-10-27", 35082.0), ("2025-01-26", 39331.0)):
        rows.append({"ticker": "NVDA", "period_end": end, "kind": "Q", "item": "revenue", "value": v})
    rows.append({"ticker": "NVDA", "period_end": "2025-01-26", "kind": "FY", "item": "revenue", "value": 130497.0})
    return rows


def selftest() -> int:
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)[:260]) if note and not cond else ""), flush=True)

    pm, _src = params()
    chk("① 會計年度:曆年 2024-03-31 → FY2024 Q1 · 2024-12-31 → Q4;NVDA(1 月底結束)2024-04-28 → FY2025 Q1 · 2025-01-26 → FY2025 Q4 · 2024-10-27 → Q3",
        fiscal(date(2024, 3, 31), 12) == (2024, 1) and fiscal(date(2024, 12, 31), 12) == (2024, 4) and fiscal(date(2024, 4, 28), 1) == (2025, 1)
        and fiscal(date(2025, 1, 26), 1) == (2025, 4) and fiscal(date(2024, 10, 27), 1) == (2025, 3))
    res = check(normalize(fixture_rows(), pm), pm)
    by = {(r["ticker"], r["item"], r["fy"]): r for r in res}
    r = by[("3017", "revenue", 2024)]
    chk("② 3017 累計拆單季:Q1 = 累計 Q1 · Q2 = 累計 Q2 − 累計 Q1 … · K1 年度 = Q4 累計 · K2 年度 = 四季和 · 全綠(示例數字)",
        abs(r["single"][2] - 33000.0) < 1e-6 and r["lamp"] == "GREEN" and {c["name"][:2] for c in r["checks"]} == {"K1", "K2"}, r)
    r = by[("3324", "eps", 2024)]
    chk("③ 3324 EPS:累計拆單季 · 四季和 ≈ 年度(差 ≤ 3% 綠)", r["lamp"] == "GREEN" and any(c["name"].startswith("K2 EPS") for c in r["checks"]), r["checks"])
    r = by[("NVDA", "revenue", 2025)]
    chk("④ NVDA(會計年度 1 月底)單季 4 個 → FY2025 · 四季和 130,497 = 年度 → 綠", r["lamp"] == "GREEN" and len(r["single"]) == 4, r)
    bad = fixture_rows()
    for x in bad:
        if x["ticker"] == "NVDA" and x["period_end"] == "2024-07-28":
            x["value"] = 31040.0
    bad = [x for x in bad if not (x["ticker"] == "3324" and x["item"] == "revenue" and x["period_end"] == "2024Q3")]
    bad.append({"ticker": "3017", "period_end": "2024-06-30", "kind": "Q", "item": "revenue", "value": 33500.0})
    rb = {(r["ticker"], r["item"], r["fy"]): r for r in check(normalize(bad, pm), pm)}
    chk("⑤ 抓錯:NVDA Q2 錯 1,000 → K2 紅 · 3324 缺 Q3 累計 → Q3 / Q4 拆不出、照列缺期(黃)· 3017 報的 Q2 單季 ≠ 累計拆出 → K3 紅",
        rb[("NVDA", "revenue", 2025)]["lamp"] == "RED" and "Q3" in rb[("3324", "revenue", 2024)]["missing"] and rb[("3324", "revenue", 2024)]["lamp"] in ("YELLOW", "RED")
        and any(c["name"].startswith("K3 Q2") and c["lamp"] == "RED" for c in rb[("3017", "revenue", 2024)]["checks"]), [rb[("NVDA", "revenue", 2025)]["checks"], rb[("3324", "revenue", 2024)]["missing"]])
    with tempfile.TemporaryDirectory() as td:
        out = run(fixture_rows(), {"source": "夾具(示例數字,非真財報)"}, Path(td))
        pg = Path(out["page"]).read_text(encoding="utf-8")
        chk("⑥ 頁面:卡片(3017 · 3324 · NVDA)+ 矩陣(累計 Q1–Q4 · 單季 Q1–Q4 · 年度 · 對帳)· VeritasDataForge 不空格 · 不載外部腳本",
            all(t in pg for t in ("3017", "3324", "NVDA")) and "累計 Q4" in pg and "單季 Q1" in pg and "VeritasDataForge" in pg and "<script" not in pg.lower())
        import duckdb
        h = Path(td) / "home" / "output_hub" / "mega"
        h.mkdir(parents=True)
        c = duckdb.connect(str(h / "vdf_tw_market.duckdb"))
        c.execute("CREATE TABLE tw_financial_mops(date VARCHAR, code VARCHAR, statement VARCHAR, basis VARCHAR, item VARCHAR, value DOUBLE, period VARCHAR)")
        c.execute("ALTER TABLE tw_financial_mops ADD COLUMN unit VARCHAR")
        c.execute("INSERT INTO tw_financial_mops VALUES ('2024-03-31','3017','IS','YTD','營業收入合計',100,'2024Q1','仟元'),('2024-06-30','3017','IS','YTD','營業收入合計',210,'2024Q2','仟元'),"
                  "('2024-06-30','3017','BS','POINT','資產總計',999,'2024Q2','仟元'),('2024-06-30','3017','IS','YTD','基本每股盈餘（元）',2.85,'2024Q2','元')")
        c.execute('CREATE TABLE tw_financial("Ticker" VARCHAR, "Period" VARCHAR, "Period_Type" VARCHAR, "Revenue" DOUBLE, "Net_Income" DOUBLE, "EPS" DOUBLE)')
        c.execute("INSERT INTO tw_financial VALUES ('3017.TW','2024-06-30','quarterly',110000,NULL,NULL)")
        c.close()
        rows, note = read_db(Path(td) / "home", ["3017", "3324", "NVDA"], pm)
        rr = {(r["ticker"], r["item"], r["fy"]): r for r in check(normalize(rows, pm), pm)}
        chk("⑦ 讀正典庫(唯讀):交易所累計只取 basis=YTD 損益(資產負債不混)· 交易所仟元 → 百萬元再跟 yfinance 比(Q2 拆 0.11 = 報 0.11 → K3 綠)"
            "· 全形「基本每股盈餘（元）」認得、每股不乘 · 3017.TW 去後綴對上 · 金額都換成百萬元(仟元 ÷1,000 · 元 ÷1,000,000)",
            len(rows) == 4 and abs(rr[("3017", "revenue", 2024)]["single"][2] - 0.11) < 1e-9 and any(c["name"].startswith("K3 Q2") and c["lamp"] == "GREEN" for c in rr[("3017", "revenue", 2024)]["checks"])
            and rr[("3017", "eps", 2024)]["ytd"].get(2) == 2.85, (rows, note))
        part = run([x for x in fixture_rows() if x["ticker"] == "3017"], {"source": "夾具", "tickers": ["3017", "3324", "NVDA"]}, Path(td) / "o2")
        miss = [r for r in part["results"] if r["missing"] == ["整檔沒有財報列"]]
        suf = run([dict(x, ticker="3017.TW") for x in fixture_rows() if x["ticker"] == "3017"], {"source": "夾具", "tickers": ["3017.TW"]}, Path(td) / "o3")
        chk("⑨ 指定 3017 · 3324 · NVDA 但只有 3017 的資料 → 3324 / NVDA 照列「整檔沒有財報列」· 總燈不是綠;"
            "長表與 --tickers 都寫 3017.TW → 兩邊同一把尺,不誤報缺、總燈綠(PR 653 Codex P2)",
            sorted(r["ticker"] for r in miss) == ["3324", "NVDA"] and part["lamp"] != "GREEN"
            and suf["lamp"] == "GREEN" and not [r for r in suf["results"] if r["missing"] == ["整檔沒有財報列"]] and {r["ticker"] for r in suf["results"]} == {"3017"},
            (part["lamp"], [r["ticker"] for r in miss], suf["lamp"], [(r["ticker"], r["missing"]) for r in suf["results"]]))
        chk("⑩ 顯示規範:金額千分位 · 小數一位(26,044.0 · 0.1)· EPS 小數兩位(2.85)· 存值不四捨五入",
            _fmt(26044.0, "revenue") == "26,044.0" and _fmt(0.11, "revenue") == "0.1" and _fmt(2.85, "eps") == "2.85" and rr[("3017", "revenue", 2024)]["single"][2] != 0.1)
        lf = Path(td) / "long.csv"
        lf.write_text("ticker,period_end,kind,item,value,unit\n3017,2024Q1,YTD,revenue,100,仟元\n3017,2024Q2,YTD,revenue,210000,元\n"
                      "3017,2024Q3,YTD,revenue,9,美分\n3017,2024Q2,YTD,eps,2.85,元\n", encoding="utf-8")
        fr = {(x["period_end"], x["item"]): x["value"] for x in read_file(lf, pm)}
        chk("⑪ 單位層冊:VDF_FinPeriod_SSOT 尾版疊在 VDF_DataPlane_SSOT 尾版之上(金額單位百萬元 · 金額容差 0.001 · EPS 容差照底冊)"
            "· --file 有 unit 欄照換(仟元 100 → 0.1 · 元 210,000 → 0.21 · 不認得的單位那列不比 · EPS 不換)· v0100 檔還在",
            pm.get("amount_unit") == "百萬元" and pm["tol"]["amount_abs"] == 0.001 and pm["tol"]["eps_abs"] == 0.01 and "VDF_FinPeriod_SSOT_v" in _src
            and "VDF_DataPlane_SSOT_v" in _src and abs(fr[("2024Q1", "revenue")] - 0.1) < 1e-12 and abs(fr[("2024Q2", "revenue")] - 0.21) < 1e-12
            and ("2024Q3", "revenue") not in fr and fr[("2024Q2", "eps")] == 2.85 and (HERE / "VDF_MDL021_FinPeriodCheck_v0100.py").is_file(), (_src, pm.get("tol"), fr))
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑧ 獨立:不匯入他系統 · 不碰 TA-Lib · 庫只唯讀開 · 兩座橋在",
        not re.search(r"^\s*(import|from)\s+(talib|CGC_|VRN_|VQG_|VAP_)", text, re.M) and "read_only=True" in text
        and "[VIA:ACCEL-BRIDGE:v0100]" in text and "[VIA:NET-BRIDGE:v0100]" in text)
    n = sum(ok)
    print("[計] %s 自測 %d/%d · %s" % (TAG, n, len(ok), "PASS" if n == len(ok) else "FAIL"), flush=True)
    return 0 if n == len(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
