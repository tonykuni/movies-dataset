#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VRN_ENG080_FourPointDigest v0100 — 研報「一題四點」文摘+潛在上漲空間(目標價除權息調整)引擎(批386)
====================================================================
操作員令(批386;Grok 主控台 VRN 契約接回母倉):
  「1. 潛在上漲空間(用最新 adj close 去算),目標價 xxx 元,評價方式 xxx,基於 xxx
    2. n~n+3 diluted eps,yoy xxx,主要原因 xxx
    3. 4. 將第一頁其餘本文部分整合成兩點不受限」
  +「如果報告時間在除權息前,目標價也必須除權息調整」。
契約(一標題 + 四點;DIGEST 五槽存 K1–K5,K5 風險可空;quote-or-abstain;不發明、不平均):
  headline 標題:標籤 標題:/核心結論: 原句(缺=title_head 檔頭/未提及)
  K1 潛在上漲空間:目標價(報告正文 目標價: 優先 > vrn_report_basic.target_price=VRN_SSOT;多值列示不平均)
     × 最新 adj close(tw_daily_prices 該檔最後交易日;缺=上漲空間未算,不拿 close/共識頂替)
     除權息調整律:報告日 < 除權息日 ≤ 最新日 → 目標價同口徑後向復權:
       TP_adj = TP × F,F = (adj_close/close)@報告日(≤報告日最近交易日)÷(adj_close/close)@最新日
       (= 後向因子鏈;因子變動日=除權息事件,逐日列示;母倉無配息事件表=價表因子推定,誠實標 method)
     上漲空間_now = (TP_adj − adj_latest)/adj_latest;另存 批240 報告時上漲 upside_at_report(TP÷報告前日 close;ENG073)
     評價方式 評價方式:/PE/本益比/EV/EBITDA/PB/DCF/SOTP 原句;基於 基於: 原句;缺=未提及
  K2 稀釋 EPS n～n+3:vrn_report_metrics EPS(REPORT_ESTIMATE 不冒充 OFFICIAL)> 正文 20xx EPS 規則;YoY 只在前後年皆有數且底≠0
     (底 0=NOT_COMPUTABLE_ZERO_BASE;轉盈/轉虧標態);主要原因 主要原因: 原句
  K3/K4 首頁其餘甲/乙:首頁前 48 行去已用標籤行,對半拆兩點,原文不限長
  K5 風險:風險: 原句;缺=未提及(可空=通過,不發明)
  QC:novel numbers=文摘出現而來源(正文∪TP∪價∪EPS 冊)沒有的數字 → RED;衍生數(TP_adj/上漲%/YoY)標 derived 不計
落庫:vrn_four_point_digest(派生層重算=同 report_file DELETE+INSERT;ENG073 同例)+ VIA_Reports/vrn/four_point/DIGEST_latest.json/.html(零 CDN)
律:只增不減;原件零觸碰(ENG072 sidecar/ENG073 表/價表唯讀);誠實三態;零網路;尾版律;Adjusted 與原始不混用(交接 05.4)。
用法:python3 VRN_ENG080_FourPointDigest_v0100.py run [--db PATH] [--zones DIR] [--ticker 2330] [--limit N] [--json]
      | show <ticker|report_file> | --selftest
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

import datetime as _dt
import html
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
MEGA = VIA / "functional modules" / "VDF" / "output_hub" / "mega"
DB_TW = MEGA / "vdf_tw_market.duckdb"


def _resolve_db(db=None):
    r"""批447:主庫路徑要探**替根**(與 ENG073 `_resolve_db`、ENG074、
    首頁引擎 `_alt_root`、MDL139 `mega_db` 同律)。

    工作站實錄(批446 之後鏈第一次跑到第四段):
        [via-vrn4] RED · 報告 0 · 庫缺 …\OneDrive\…\mega\vdf_tw_market.duckdb
    而**同一次跑**的 ENG073/ENG074 都印「主路徑缺→改用替根庫」並寫進
    59 列 basic、7,024 列財報值。批443→批446 的同一課,這是**第三支**:
    庫就在那裡,是這支引擎沒去找;而它 rc=1 直接把鏈停在最後一段。
    """
    if db is not None:
        return Path(db)
    cands = [DB_TW]
    try:
        home = Path.home()
        rel = Path("movies-dataset/VeritasIntelligenceAnalytics/functional modules"
                   "/VDF/output_hub/mega/vdf_tw_market.duckdb")
        cands += [home / "Downloads" / rel, home / rel]
    except Exception:
        pass
    for c in cands:
        try:
            if c.exists():
                if c != DB_TW:
                    print(f"[庫解析] 主路徑缺→改用替根庫:{c}(誠實提示)")
                return c
        except Exception:
            continue
    return DB_TW          # 全缺=回主路徑,讓呼叫端照原樣報「庫缺 <主路徑>」
ZONES_DIR = VIA / "VIA_Reports" / "first_page_text"
REPORTS = VIA / "VIA_Reports" / "vrn" / "four_point"
TABLE = "vrn_four_point_digest"
SLOTS = [("headline", "標題"), ("K1", "潛在上漲空間"), ("K2", "稀釋EPS n～n+3"), ("K3", "首頁其餘甲"), ("K4", "首頁其餘乙"), ("K5", "風險因子")]
USED_LABEL = re.compile(r"^(標題|核心結論|目標價|評價方式|基於|主要原因|券商|日期|風險)[:：]")
NUM_RX = re.compile(r"-?\d+(?:\.\d+)?%?")
FACTOR_EPS = 1e-6
YF_TW = re.compile(r"^\d{4}[A-Z0-9]{0,2}\.(TW|TWO)$")


# ---------------------------------------------------------------- 文本規則(Grok digest-four 契約逐條移植)
def grab(text: str, rx: str) -> str:
    m = re.search(rx, text, flags=re.M)
    return (m.group(1).strip()[:180]) if m else ""


def extract_target_price(text: str) -> float | None:
    m = re.search(r"目標價[:：]?\s*(?:NT\$|新台幣)?\s*([\d,]+(?:\.\d+)?)\s*元?", text)
    if not m:
        return None
    try:
        v = float(m.group(1).replace(",", ""))
        return v if v > 0 else None
    except ValueError:
        return None


def extract_val_method(text: str) -> str:
    v = grab(text, r"評價方式[:：]\s*(.+)")
    if v:
        return v
    m = re.search(r"([^\n。]*?(?:本益比|P/E|PE|EV/EBITDA|P/B|PB|DCF|SOTP|殖利率|股價淨值比)[^\n。]*)", text)
    return m.group(1).strip()[:180] if m else ""


def extract_basis(text: str) -> str:
    return grab(text, r"基於[:：]\s*(.+)")


def extract_reason(text: str) -> str:
    return grab(text, r"主要原因[:：]\s*(.+)")


def extract_risk(text: str) -> str:
    return grab(text, r"風險(?:因子|因素)?[:：]\s*(.+)")


def extract_eps_years(text: str) -> list:
    out, seen = [], set()
    for m in re.finditer(r"(20[2-3]\d)\s*[EF]?\s*[:：|]?\s*(?:稀釋)?(?:每股盈餘|EPS)?\s*(-?[\d]+(?:\.\d+)?)", text, flags=re.I):
        y, v = int(m.group(1)), float(m.group(2))
        if y not in seen:
            seen.add(y)
            out.append({"year": y, "eps": v, "src": "正文"})
    return sorted(out, key=lambda r: r["year"])


def first_page(text: str) -> str:
    cut = re.split(r"\f|\n頁\s*2\b|\n-{3,}\n", text)[0]
    return "\n".join(cut.splitlines()[:48])


def remainder_two(text: str) -> tuple[str, str]:
    page = first_page(text)
    keep = [ln.strip() for ln in page.splitlines()]
    keep = [ln for ln in keep if ln and not USED_LABEL.match(ln) and not re.match(r"^20[2-3]\d\s+稀釋", ln) and not ln.startswith("|")
            and not re.match(r"^[-:|\s]+$", ln) and not ln.startswith("科目")]
    if not keep:
        return "", ""
    mid = (len(keep) + 1) // 2
    return " ".join(keep[:mid]), " ".join(keep[mid:])


def fmt_pct(v: float) -> str:
    return f"{v * 100:.1f}%"


def _round2(x: float) -> float:
    """四捨五入至 2 位(half-up;避免 165×0.985=162.525 二進位誤差落 162.52)"""
    from decimal import Decimal, ROUND_HALF_UP
    return float(Decimal(repr(round(x, 9))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def upside(target: float, current: float) -> float | None:
    return None if not current else (target - current) / current


def yoy(cur: float, base: float) -> dict:
    if base == 0:
        return {"state": "NOT_COMPUTABLE_ZERO_BASE", "value": None}
    v = (cur - base) / abs(base)
    if base < 0 < cur:
        return {"state": "TURNAROUND_TO_PROFIT", "value": v}
    if base > 0 > cur:
        return {"state": "TURNAROUND_TO_LOSS", "value": v}
    if base < 0 and cur < 0:
        return {"state": "NEG_TO_NEG_ANNOTATED", "value": v}
    return {"state": "NORMAL", "value": v}


def novel_numbers(summary: str, source: str, derived: list | None = None) -> list:
    allow = {n.replace(",", "") for n in NUM_RX.findall(source)}
    for d in derived or []:
        allow |= {n.replace(",", "") for n in NUM_RX.findall(str(d))}
    out = []
    for n in NUM_RX.findall(summary):
        n2 = n.replace(",", "")
        if n2 not in allow and n2.rstrip("%") not in allow and n2 not in out:
            out.append(n2)
    return out


# ---------------------------------------------------------------- 價表:最新 adj close 與除權息調整因子
def _tickers_for(code: str, con) -> list:
    """裸碼 → 價表票(tw_listings yf_ticker > .TW/.TWO 皆試)"""
    if YF_TW.match(code):
        return [code]
    cands = []
    try:
        have = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
        if "tw_listings" in have:
            cols = {r[0].lower() for r in con.execute('DESCRIBE "tw_listings"').fetchall()}
            if "yf_ticker" in cols:
                r = con.execute("SELECT yf_ticker FROM tw_listings WHERE code = ? AND yf_ticker IS NOT NULL", [code]).fetchone()
                if r and r[0]:
                    cands.append(str(r[0]))
            elif "market" in cols:
                r = con.execute("SELECT market FROM tw_listings WHERE code = ?", [code]).fetchone()
                if r and r[0]:
                    cands.append(code + (".TW" if str(r[0]).upper() == "TWSE" else ".TWO"))
    except Exception:
        pass
    return cands + [code + ".TW", code + ".TWO"]


# ===== 批419:K1 兩道閘(操作員 37 份真文摘實證) ==========================
# 工作站真跑 37 份文摘,兩件事一眼可見:
#   ① 三份的 TP/價比是 0.020 / 0.019 / 0.005(MS-2308 / MS-8210 / JP-3653)——
#      目標價只有股價的 1/50 到 1/200。沒有分析師會發 -98% 的目標價,
#      那是**抽錯的數**(EPS、倍數、或外幣價)。把它印成「潛在上漲空間 -98.0%」
#      比不印更糟:讀的人會以為那是預測。
#   ② 37 份全部拿 **2026-09-07 的價**比,但 Daiwa-1319 是 **2023-10-11** 的報告
#      (距今 1062 天)。拿三年後的價去算三年前報告的「潛在上漲空間」,
#      算出來的不是上漲空間,是**事後看圖**。18 份逾 180 天。
# 兩道閘都**不刪任何數字**:照列,但講白它是什麼、不許它冒充預測。
TP_SANITY_LO, TP_SANITY_HI = 0.2, 5.0     # 目標價/現價 的合理帶(=上漲 -80%～+400%)
STALE_DAYS = 180                          # 報告距價格基準日超過這麼久=非當期比較


def tp_sanity(tp_adj, price) -> tuple[str, float | None]:
    """目標價合理性。回 (態, 比值)。
    OK=在帶內;TP_SUSPECT=帶外(疑為擷取誤判);NA=算不了。
    為什麼是 flag 不是丟棄:我們**不知道**哪個數字才對,丟棄等於替操作員決定;
    照列並標明可疑,他一眼就知道要去翻哪三份 PDF。"""
    try:
        if tp_adj is None or not price:
            return "NA", None
        r = float(tp_adj) / float(price)
    except (TypeError, ValueError, ZeroDivisionError):
        return "NA", None
    return ("OK" if TP_SANITY_LO <= r <= TP_SANITY_HI else "TP_SUSPECT"), r


def basis_age(report_date: str, adj_date: str) -> int | None:
    """報告日到價格基準日的天數;算不出=None(不猜)。"""
    from datetime import date
    try:
        a = date(*(int(x) for x in str(report_date)[:10].split("-")))
        b = date(*(int(x) for x in str(adj_date)[:10].split("-")))
    except (TypeError, ValueError):
        return None
    return (b - a).days


def basis_state(days: int | None) -> str:
    """CURRENT=當期(比得有意義)· STALE_BASIS=非當期 · UNKNOWN=日期缺。"""
    if days is None:
        return "UNKNOWN"
    return "CURRENT" if days <= STALE_DAYS else "STALE_BASIS"


def price_context(con, code: str, report_date: str | None) -> dict:
    """最新 adj close + 報告日因子 + 因子鏈(除權息事件=因子變動日)"""
    out = {"ticker": "", "adj_date": "", "adj_close": None, "close_latest": None, "factor_latest": None, "factor_report": None,
           "report_px_date": "", "adjust_factor": None, "ex_dates": [], "adjust_method": "", "adjust_note": ""}
    have = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
    if "tw_daily_prices" not in have:
        out["adjust_note"] = "價表 tw_daily_prices 缺"
        return out
    cols = {r[0].lower() for r in con.execute('DESCRIBE "tw_daily_prices"').fetchall()}
    has_adj = "adj_close" in cols
    for t in _tickers_for(code, con):
        r = con.execute("SELECT CAST(date AS VARCHAR), close" + (", adj_close" if has_adj else ", NULL") +
                        " FROM tw_daily_prices WHERE ticker = ? AND close IS NOT NULL ORDER BY date DESC LIMIT 1", [t]).fetchone()
        if r:
            out["ticker"] = t
            out["adj_date"], out["close_latest"] = r[0], float(r[1])
            out["adj_close"] = float(r[2]) if r[2] is not None else None
            break
    if not out["ticker"]:
        out["adjust_note"] = "該檔不在價表(上漲空間未算;不拿共識/close 頂替)"
        return out
    if out["adj_close"] is None:
        out["adjust_note"] = "價表無 adj_close(上漲空間未算;不拿 close 頂替=Adjusted 與原始不混用)"
        return out
    out["factor_latest"] = out["adj_close"] / out["close_latest"] if out["close_latest"] else None
    if not report_date:
        out["adjust_method"] = "NONE"
        out["adjust_note"] = "報告日缺=不除權息調整(目標價照列)"
        return out
    rp = con.execute("SELECT CAST(date AS VARCHAR), close, adj_close FROM tw_daily_prices WHERE ticker = ? AND CAST(date AS VARCHAR) <= ? "
                     "AND close IS NOT NULL AND close > 0 AND adj_close IS NOT NULL ORDER BY date DESC LIMIT 1", [out["ticker"], report_date]).fetchone()
    if not rp:
        out["adjust_method"] = "NONE"
        out["adjust_note"] = f"報告日 {report_date} 前無價列=無法推定因子(目標價照列)"
        return out
    out["report_px_date"], out["factor_report"] = rp[0], float(rp[2]) / float(rp[1])
    if not out["factor_latest"]:
        out["adjust_method"] = "NONE"
        out["adjust_note"] = "最新日因子缺"
        return out
    f = out["factor_report"] / out["factor_latest"]
    # 因子變動日=除權息/拆股事件(報告日 < 事件 ≤ 最新日)
    rows = con.execute("SELECT CAST(date AS VARCHAR), adj_close / close FROM tw_daily_prices WHERE ticker = ? AND CAST(date AS VARCHAR) >= ? "
                       "AND CAST(date AS VARCHAR) <= ? AND close > 0 AND adj_close IS NOT NULL ORDER BY date", [out["ticker"], rp[0], out["adj_date"]]).fetchall()
    ex = []
    prev = None
    for d, fac in rows:
        if prev is not None and fac is not None and abs(float(fac) - prev) > FACTOR_EPS:
            ex.append(d)
        prev = float(fac) if fac is not None else prev
    out["ex_dates"] = ex
    if abs(f - 1.0) <= FACTOR_EPS or not ex:
        out["adjust_factor"] = 1.0
        out["adjust_method"] = "NONE"
        out["adjust_note"] = f"報告日 {report_date} 至 {out['adj_date']} 無除權息事件(因子 1)"
    else:
        out["adjust_factor"] = f
        out["adjust_method"] = "PRICE_FACTOR_CHAIN"
        out["adjust_note"] = (f"報告日 {report_date}(價列 {rp[0]} 因子 {out['factor_report']:.6f})→ 最新 {out['adj_date']}(因子 {out['factor_latest']:.6f});"
                              f"除權息事件 {len(ex)} 次 {','.join(ex[:5])}{'…' if len(ex) > 5 else ''};目標價 × {f:.6f}(後向復權同口徑;母倉無配息事件表=價表因子推定)")
    if abs(out["factor_latest"] - 1.0) > 1e-4:
        out["adjust_note"] += f";注意:最新日因子 {out['factor_latest']:.6f}≠1=adj 基準非最新(價表混抓時點),建議 via-hist 重抓/ENG060 重建"
    return out


# ---------------------------------------------------------------- 單件文摘
def build_digest(text: str, basic: dict, metrics: list, px: dict) -> dict:
    page = first_page(text)
    title = grab(page, r"(?:標題|核心結論)[:：]\s*(.+)")
    title_src = "正文標籤" if title else ""
    if not title and basic.get("title_head"):
        title, title_src = str(basic["title_head"])[:180], "檔頭(ungrounded)"
    body_tp = extract_target_price(page)
    ssot_tp = basic.get("target_price")
    tp_raw = basic.get("target_price_raw") or ""
    tp = body_tp if body_tp is not None else (float(ssot_tp) if ssot_tp else None)
    tp_src = "報告正文" if body_tp is not None else ("VRN_SSOT" if tp else "")
    multi = f" · 列 {tp_raw} 不平均" if (body_tp is None and tp_raw and ";" in str(tp_raw)) else ""
    method, basis = extract_val_method(page), extract_basis(page)
    adj, adj_date = px.get("adj_close"), px.get("adj_date")
    tp_adj = None
    if tp is not None and px.get("adjust_factor"):
        tp_adj = _round2(tp * px["adjust_factor"])
    up_now = upside(tp_adj if tp_adj is not None else tp, adj) if (tp is not None and adj) else None
    # 批419 兩道閘:合理性 + 基準日
    _tp_state, _tp_ratio = tp_sanity(tp_adj if tp_adj is not None else tp, adj)
    _days = basis_age(basic.get("report_date") or "", adj_date or "")
    _basis = basis_state(_days)
    k1, g1 = "未提及", False
    if tp is not None and adj and up_now is not None:
        adj_txt = f"(除權息調整 {px['adjust_factor']:.4f} → {tp_adj}元)" if px.get("adjust_method") == "PRICE_FACTOR_CHAIN" else ""
        rep_up = f" · 報告時上漲 {fmt_pct(float(basic['upside_at_report']))}(批240 TP÷報告前日 close)" if basic.get("upside_at_report") is not None else ""
        if _tp_state == "TP_SUSPECT":
            # 不假裝那是預測。照列兩個數字、講明比值,請人工去翻那份 PDF。
            k1 = (f"目標價疑為擷取誤判(不列為潛在上漲空間):目標價 {tp:g}元({tp_src})"
                  f" vs 最新 adj close {adj_date} {adj}元 → 比值 {_tp_ratio:.3f}"
                  f"(合理帶 {TP_SANITY_LO}–{TP_SANITY_HI});待人工核 PDF{adj_txt}{multi}")
        elif _basis == "STALE_BASIS":
            # 當期上漲空間算不得數:改把「報告時上漲」放頭,今日比值降為參考。
            head = (f"報告時上漲 {fmt_pct(float(basic['upside_at_report']))}(批240 TP÷報告前日 close)"
                    if basic.get("upside_at_report") is not None else "報告時上漲 未算(報告日前無價列)")
            k1 = (f"{head} · 非當期比較:報告距價格基準日 {_days} 天(>{STALE_DAYS}),"
                  f"今日 adj close {adj_date} {adj}元 對目標價 {tp:g}元({tp_src}) 為 {fmt_pct(up_now)}"
                  f"——僅供參考,不作潛在上漲空間{adj_txt}{multi}"
                  f" · 評價方式 {method or '未提及'} · 基於 {basis or '未提及'}")
        else:
            k1 = (f"潛在上漲空間 {fmt_pct(up_now)}(最新 adj close {adj_date} {adj}元 VDF 價表)· 目標價 {tp:g}元({tp_src}){adj_txt}{multi}"
                  f" · 評價方式 {method or '未提及'} · 基於 {basis or '未提及'}{rep_up}")
        g1 = True
    elif tp is not None:
        k1 = f"目標價 {tp:g}元({tp_src}){multi} · 上漲空間未算({px.get('adjust_note') or '該檔 adj close 不在 VDF 價表'})· 評價方式 {method or '未提及'} · 基於 {basis or '未提及'}"
        g1 = True
    # K2:EPS 冊(ENG073 metrics)優先,正文規則後備
    eps = []
    seen = set()
    for m in metrics:
        if not re.search(r"eps|每股盈餘", str(m.get("metric", "")), flags=re.I):
            continue
        ym = re.search(r"(20[2-3]\d)", str(m.get("period", "")))
        if not ym or m.get("value") is None:
            continue
        y = int(ym.group(1))
        if y not in seen:
            seen.add(y)
            eps.append({"year": y, "eps": float(m["value"]), "src": f"metrics:{m.get('status') or ''}"})
    for e in extract_eps_years(page):
        if e["year"] not in seen:
            seen.add(e["year"])
            eps.append(e)
    eps.sort(key=lambda r: r["year"])
    reason = extract_reason(page)
    k2, g2, yoy_rows = "未提及", False, []
    if eps:
        n = eps[0]["year"]
        span = []
        for i in range(4):
            hit = next((e for e in eps if e["year"] == n + i), None)
            span.append(f"{hit['year']} {hit['eps']:g}" if hit else f"{n + i} 未提及")
        bits = []
        for i in range(1, len(eps)):
            y = yoy(eps[i]["eps"], eps[i - 1]["eps"])
            yoy_rows.append({"year": eps[i]["year"], **y})
            bits.append(f"{eps[i]['year']} YoY {y['state']}" if y["value"] is None else f"{eps[i]['year']} YoY {fmt_pct(y['value'])}" + ("" if y["state"] == "NORMAL" else f"({y['state']})"))
        k2 = f"稀釋EPS {'、'.join(span)} · {'；'.join(bits) or 'YoY 未算'} · 主要原因 {reason or '未提及'}"
        g2 = True
    a, b = remainder_two(page)
    risk = extract_risk(page)
    points = {"headline": (title or "未提及", bool(title) and title_src == "正文標籤"), "K1": (k1, g1), "K2": (k2, g2),
              "K3": (a or "未提及", bool(a)), "K4": (b or "未提及", bool(b)), "K5": (risk or "未提及", bool(risk))}
    n0 = eps[0]["year"] if eps else 0
    derived = [tp_adj, fmt_pct(up_now) if up_now is not None else "", px.get("adjust_factor"), adj, adj_date, tp, tp_raw, "批240",
               fmt_pct(float(basic["upside_at_report"])) if basic.get("upside_at_report") is not None else "",
               f"{px.get('adjust_factor') or 0:.4f}", *[f"{e['eps']:g}" for e in eps], *[e["year"] for e in eps], *[n0 + i for i in range(4)],
               *[fmt_pct(r["value"]) for r in yoy_rows if r["value"] is not None], *[str(basic.get("target_price") or "")], f"{tp:g}" if tp is not None else "",
               # 批419b(我自己造的回歸):批419 的兩道閘會在 K1 印出**閘門自己的診斷值**——
               # 比值(0.020)、合理帶界(0.2 / 5.0)、天數(1062)。那些不是「報告裡的宣稱」,
               # 是**關於擷取的後設說明**,拿 novel numbers 去查它們等於要求閘門的判準
               # 也要出現在報告正文裡,無理。工作站實錄:MS-2308/MS-8210/JP-3653 三份因此
               # QC 紅、vrn_fourpoint rc=1,整段鏈被自己的診斷訊息判死。
               f"{_tp_ratio:.3f}" if _tp_ratio is not None else "", str(TP_SANITY_LO), str(TP_SANITY_HI),
               str(_days) if _days is not None else "", str(STALE_DAYS)]
    novel = novel_numbers(" ".join(v[0] for v in points.values()), text + " " + (basic.get("raw_all") or ""), derived)
    return {"headline": points["headline"][0], "points": {k: {"zh": zh, "text": points[k][0], "grounded": points[k][1]} for k, zh in SLOTS},
            "tp": tp, "tp_src": tp_src, "tp_raw": tp_raw, "tp_adj": tp_adj, "adjust_factor": px.get("adjust_factor"), "adjust_method": px.get("adjust_method"),
            "adjust_note": px.get("adjust_note"), "ex_dates": px.get("ex_dates") or [], "adj_close": adj, "adj_date": adj_date, "px_ticker": px.get("ticker"),
            "upside_now": up_now, "upside_at_report": basic.get("upside_at_report"), "method": method, "basis": basis, "eps": eps, "yoy": yoy_rows,
            # 批419:兩道閘的態一併落庫,U/I 與統計才判得出哪幾份的上漲空間可信
            "tp_state": _tp_state, "tp_ratio": _tp_ratio, "basis_state": _basis, "basis_days": _days,
            "novel_numbers": novel, "qc": "RED" if novel else ("GREEN" if all(v[1] for k, v in points.items() if k != "K5") else "YELLOW")}


# ---------------------------------------------------------------- 落庫/報告
def _ensure_table(con) -> None:
    con.execute(f"""CREATE TABLE IF NOT EXISTS {TABLE}(
        report_file VARCHAR, ticker VARCHAR, px_ticker VARCHAR, broker VARCHAR, report_date VARCHAR, asof_date VARCHAR,
        headline VARCHAR, k1 VARCHAR, k2 VARCHAR, k3 VARCHAR, k4 VARCHAR, k5 VARCHAR,
        g_headline BOOLEAN, g_k1 BOOLEAN, g_k2 BOOLEAN, g_k3 BOOLEAN, g_k4 BOOLEAN, g_k5 BOOLEAN,
        tp DOUBLE, tp_src VARCHAR, tp_raw VARCHAR, tp_adj DOUBLE, adjust_factor DOUBLE, adjust_method VARCHAR, adjust_note VARCHAR, ex_dates VARCHAR,
        adj_close DOUBLE, upside_now DOUBLE, upside_at_report DOUBLE, val_method VARCHAR, basis VARCHAR, eps_json VARCHAR, yoy_json VARCHAR,
        novel_numbers VARCHAR, qc VARCHAR, generated_at VARCHAR)""")
    for col in ("tp_state VARCHAR", "tp_ratio DOUBLE", "basis_state VARCHAR", "basis_days INTEGER"):
        try:                                   # 批419:加欄式(舊庫照樣可讀,只增不減)
            con.execute(f"ALTER TABLE vrn_four_point_digest ADD COLUMN {col}")
        except Exception:
            pass


def _load_text(zones_dir: Path, report_file: str) -> str:
    p = zones_dir / f"{report_file}.json"
    if not p.exists():
        return ""
    try:
        z = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return ""
    parts = [str(z.get(k) or "") for k in ("header", "right", "body")]
    return "\n".join(x for x in parts if x)


def run(db: Path | None = None, zones_dir: Path | None = None, ticker: str | None = None, limit: int | None = None, do_print: bool = True,
        reports: Path = REPORTS) -> dict:
    import duckdb
    dbp = _resolve_db(db)
    zdir = Path(zones_dir) if zones_dir else ZONES_DIR
    rep = {"schema": "VIA.VRNFourPoint.v1", "ts": _dt.datetime.now().isoformat(timespec="seconds"), "db": str(dbp), "zones": str(zdir), "rows": [],
           "summary": {"reports": 0, "with_text": 0, "k1_grounded": 0, "upside_now": 0, "adjusted": 0, "qc_red": 0}, "verdict": "GREEN"}
    if not dbp.exists():
        rep["verdict"], rep["note"] = "RED", f"庫缺 {dbp}(先 via-vdfdb / ENG073 入庫)"
        _finish(rep, reports, do_print)
        return rep
    con = duckdb.connect(str(dbp))
    try:
        have = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
        if "vrn_report_basic" not in have:
            rep["verdict"], rep["note"] = "RED", "vrn_report_basic 缺(先 ENG072 首頁抽取 → ENG073 入庫)"
            _finish(rep, reports, do_print)
            return rep
        _ensure_table(con)
        bcols = [r[0] for r in con.execute("DESCRIBE vrn_report_basic").fetchall()]
        q = "SELECT * FROM vrn_report_basic WHERE ticker IS NOT NULL AND ticker <> ''"
        args = []
        if ticker:
            q += " AND ticker = ?"
            args.append(ticker)
        q += " ORDER BY report_date DESC, report_file"
        if limit:
            q += f" LIMIT {int(limit)}"
        basics = [dict(zip(bcols, r)) for r in con.execute(q, args).fetchall()]
        rep["summary"]["reports"] = len(basics)
        mrows = con.execute("SELECT report_file, metric, period, status, value, raw_text FROM vrn_report_metrics").fetchall() if "vrn_report_metrics" in have else []
        metrics: dict = {}
        for rf, metric, period, status, value, raw in mrows:
            metrics.setdefault(rf, []).append({"metric": metric, "period": period, "status": status, "value": value, "raw": raw})
        now = _dt.datetime.now().isoformat(timespec="seconds")
        for b in basics:
            rf = b["report_file"]
            text = _load_text(zdir, rf)
            if text:
                rep["summary"]["with_text"] += 1
            up_rep = b.get("upside_db") if b.get("upside_db") is not None else b.get("upside_calc")
            basic = {"title_head": b.get("title_head"), "target_price": b.get("target_price"), "target_price_raw": "",
                     "upside_at_report": (float(up_rep) / 100.0 if up_rep is not None and abs(float(up_rep)) > 1.5 else up_rep),
                     "raw_all": " ".join(str(m.get("raw") or "") for m in metrics.get(rf, []))}
            px = price_context(con, str(b["ticker"]), b.get("report_date"))
            d = build_digest(text, basic, metrics.get(rf, []), px)
            d.update({"report_file": rf, "ticker": b["ticker"], "broker": b.get("broker"), "report_date": b.get("report_date")})
            rep["rows"].append(d)
            if d["points"]["K1"]["grounded"]:
                rep["summary"]["k1_grounded"] += 1
            if d["upside_now"] is not None:
                rep["summary"]["upside_now"] += 1
            if d["adjust_method"] == "PRICE_FACTOR_CHAIN":
                rep["summary"]["adjusted"] += 1
            if d["qc"] == "RED":
                rep["summary"]["qc_red"] += 1
            if d["tp_state"] == "TP_SUSPECT":
                rep["summary"]["tp_suspect"] = rep["summary"].get("tp_suspect", 0) + 1
            if d["basis_state"] == "STALE_BASIS":
                rep["summary"]["stale_basis"] = rep["summary"].get("stale_basis", 0) + 1
            elif d["basis_state"] == "CURRENT" and d["tp_state"] == "OK" and d["upside_now"] is not None:
                rep["summary"]["upside_trusted"] = rep["summary"].get("upside_trusted", 0) + 1
            con.execute(f"DELETE FROM {TABLE} WHERE report_file = ?", [rf])
            P = d["points"]
            # 批419:改具名欄位。位置式 INSERT 與 ALTER 加欄天生互斥——批412 在 ENG073
            # 踩過同一個坑,這裡加四個新欄時立刻重現(36 值對 40 欄)。記法:加欄就改具名。
            _vals = {
                "report_file": rf, "ticker": b["ticker"], "px_ticker": d["px_ticker"], "broker": b.get("broker"),
                "report_date": b.get("report_date"), "asof_date": d["adj_date"],
                "headline": P["headline"]["text"], "k1": P["K1"]["text"], "k2": P["K2"]["text"],
                "k3": P["K3"]["text"], "k4": P["K4"]["text"], "k5": P["K5"]["text"],
                "g_headline": P["headline"]["grounded"], "g_k1": P["K1"]["grounded"], "g_k2": P["K2"]["grounded"],
                "g_k3": P["K3"]["grounded"], "g_k4": P["K4"]["grounded"], "g_k5": P["K5"]["grounded"],
                "tp": d["tp"], "tp_src": d["tp_src"], "tp_raw": d["tp_raw"], "tp_adj": d["tp_adj"],
                "adjust_factor": d["adjust_factor"], "adjust_method": d["adjust_method"],
                "adjust_note": d["adjust_note"], "ex_dates": ",".join(d["ex_dates"]),
                "adj_close": d["adj_close"], "upside_now": d["upside_now"],
                "upside_at_report": d["upside_at_report"], "val_method": d["method"], "basis": d["basis"],
                "eps_json": json.dumps(d["eps"], ensure_ascii=False),
                "yoy_json": json.dumps(d["yoy"], ensure_ascii=False),
                "novel_numbers": ",".join(d["novel_numbers"]), "qc": d["qc"], "generated_at": now,
                "tp_state": d["tp_state"], "tp_ratio": d["tp_ratio"],
                "basis_state": d["basis_state"], "basis_days": d["basis_days"],
            }
            _c = list(_vals)
            con.execute(f"INSERT INTO {TABLE} ({','.join(_c)}) VALUES ({','.join('?' * len(_c))})",
                        [_vals[k] for k in _c])
            if do_print:
                print(f"  [{d['qc']:<6}] {rf[:44]:<44} {b['ticker']:<6} TP {d['tp'] if d['tp'] is not None else '—'}{'→' + str(d['tp_adj']) if d['adjust_method'] == 'PRICE_FACTOR_CHAIN' else ''}"
                      f" adj {d['adj_close'] if d['adj_close'] is not None else '—'}@{d['adj_date'] or '—'} 上漲 {fmt_pct(d['upside_now']) if d['upside_now'] is not None else '未算'}"
                      f" · 接地 {'/'.join(k for k in ('headline', 'K1', 'K2', 'K3', 'K4', 'K5') if d['points'][k]['grounded'])}"
                      + (f" · ⚑TP 疑誤(比值 {d['tp_ratio']:.3f})" if d["tp_state"] == "TP_SUSPECT" else "")
                      + (f" · ⚑非當期({d['basis_days']} 天)" if d["basis_state"] == "STALE_BASIS" else "")
                      + (f" · 新數字 {d['novel_numbers']}" if d["novel_numbers"] else ""))
    finally:
        con.close()
    s = rep["summary"]
    rep["verdict"] = "RED" if s["qc_red"] else ("GREEN" if s["reports"] and s["k1_grounded"] == s["reports"] else ("YELLOW" if s["reports"] else "RED"))
    if not s["reports"]:
        rep["note"] = "vrn_report_basic 無有效 ticker 列"
    _finish(rep, reports, do_print)
    return rep


def render_html(rep: dict) -> str:
    col = {"GREEN": "#34d399", "YELLOW": "#fde047", "RED": "#fca5a5"}
    rows = ""
    for d in rep["rows"]:
        pts = "".join(f"<div><b style='color:{'#34d399' if v['grounded'] else '#fca5a5'}'>{html.escape(v['zh'])}</b> {html.escape(v['text'])}</div>" for v in d["points"].values())
        rows += (f"<tr><td style='color:{col.get(d['qc'], '#ddd')}'><b>{d['qc']}</b></td><td>{html.escape(str(d['ticker']))}<br>{html.escape(str(d.get('broker') or ''))}<br>{html.escape(str(d.get('report_date') or ''))}</td>"
                 f"<td>{pts}<div style='color:#94a3b8'>{html.escape(str(d.get('adjust_note') or ''))}</div></td></tr>")
    return ("<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
            "<title>VRN 一題四點文摘</title><style>body{background:#0f172a;color:#f8fafc;font:11px/1.35 -apple-system,'Segoe UI',Roboto,Arial,sans-serif;padding:12px}"
            "table{border-collapse:collapse;width:100%}td,th{border:1px solid #334155;padding:3px 6px;text-align:left;vertical-align:top}th{background:#1e293b}</style></head><body>"
            f"<h1 style='font-size:14px;margin:0 0 6px'>VRN 一題四點文摘 · {html.escape(rep['verdict'])} · {html.escape(rep['ts'])} · 報告 {rep['summary']['reports']} · K1 接地 {rep['summary']['k1_grounded']} · 除權息調整 {rep['summary']['adjusted']}</h1>"
            "<div style='color:#94a3b8;margin-bottom:8px'>quote-or-abstain · 不發明不平均 · 目標價除權息同口徑(後向因子鏈)· 上漲空間=(TP_adj−最新 adj close)/adj close · 零 CDN</div>"
            f"<table><tr><th>QC</th><th>檔</th><th>一題四點(綠=接地)</th></tr>{rows}</table></body></html>")


def _finish(rep: dict, reports: Path, do_print: bool) -> None:
    try:
        reports.mkdir(parents=True, exist_ok=True)
        (reports / "DIGEST_latest.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
        (reports / "DIGEST_latest.html").write_text(render_html(rep), encoding="utf-8")
    except Exception:
        pass
    if do_print:
        s = rep["summary"]
        print(f"[via-vrn4] {rep['verdict']} · 報告 {s['reports']} · 有正文 {s['with_text']} · K1 接地 {s['k1_grounded']} · 上漲已算 {s['upside_now']} · 除權息調整 {s['adjusted']} · QC 紅 {s['qc_red']}"
              + (f" · {rep['note']}" if rep.get("note") else "") + f" · 存證 {reports / 'DIGEST_latest.json'}")


def show(key: str, db: Path | None = None) -> int:
    import duckdb
    dbp = _resolve_db(db)
    if not dbp.exists():
        print(f"[show] 庫缺 {dbp}")
        return 2
    con = duckdb.connect(str(dbp), read_only=True)
    try:
        if TABLE not in {r[0] for r in con.execute("SHOW TABLES").fetchall()}:
            print("[show] 尚未 run")
            return 2
        rows = con.execute(f"SELECT report_file, ticker, report_date, headline, k1, k2, k3, k4, k5, qc, adjust_note FROM {TABLE} WHERE ticker = ? OR report_file = ? ORDER BY report_date DESC", [key, key]).fetchall()
    finally:
        con.close()
    if not rows:
        print(f"[show] 無 {key}")
        return 2
    for r in rows:
        print(f"=== {r[0]} · {r[1]} · {r[2]} · QC {r[9]} ===")
        for zh, v in zip([z for _, z in SLOTS], r[3:9]):
            print(f"  {zh}:{v}")
        print(f"  除權息:{r[10]}")
    return 0


# ---------------------------------------------------------------- 自測
def selftest() -> int:
    import tempfile
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)
    try:
        import duckdb
    except Exception:
        print("  [FAIL] duckdb 缺(於 via_vrn_312 境跑:via-vrn4)")
        return 1
    page = ("標題: 緯創(3231.TW) 維持買進\n目標價: 165 元\n評價方式: PE 20x 2026E\n基於: AI 伺服器出貨放量\n"
            "2025E 稀釋每股盈餘 7.2\n2026E 稀釋每股盈餘 8.0\n主要原因: AI 伺服器與 GB300 機櫃出貨\n"
            "產能:越南廠 2026 上半年投產。\n同業:廣達、英業達。\n風險: 匯率與關稅\n估值仍具吸引力。\n")
    chk("① 文本規則(目標價/評價方式/基於/主要原因/風險/EPS 年表/首頁其餘對半)",
        extract_target_price(page) == 165.0 and extract_val_method(page) == "PE 20x 2026E" and extract_basis(page) == "AI 伺服器出貨放量"
        and extract_reason(page).startswith("AI 伺服器") and extract_risk(page) == "匯率與關稅"
        and [e["year"] for e in extract_eps_years(page)] == [2025, 2026] and all(remainder_two(page)))
    chk("② YoY 律(正常/底 0/轉盈/轉虧)+上漲公式+novel numbers(衍生數不計;發明數字抓到)",
        yoy(8.0, 7.2)["state"] == "NORMAL" and yoy(1, 0)["state"] == "NOT_COMPUTABLE_ZERO_BASE" and yoy(2, -1)["state"] == "TURNAROUND_TO_PROFIT"
        and yoy(-2, 1)["state"] == "TURNAROUND_TO_LOSS" and abs(upside(165, 120) - 0.375) < 1e-9 and upside(165, 0) is None
        and novel_numbers("目標價 9999 元", "目標價 850 現價 678") == ["9999"] and novel_numbers("上漲 35.4%", "x", ["35.4%"]) == [])
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        dbp = tdp / "t.duckdb"
        zdir = tdp / "zones"
        zdir.mkdir()
        c = duckdb.connect(str(dbp))
        c.execute("CREATE TABLE tw_listings(code VARCHAR, name VARCHAR, market VARCHAR, yf_ticker VARCHAR)")
        c.execute("INSERT INTO tw_listings VALUES ('3231','緯創','TWSE','3231.TW'), ('2606','裕民','TWSE','2606.TW'), ('9999','無價','TWSE','9999.TW')")
        c.execute("CREATE TABLE tw_daily_prices(date VARCHAR, ticker VARCHAR, open DOUBLE, high DOUBLE, low DOUBLE, close DOUBLE, adj_close DOUBLE, volume DOUBLE)")
        # 3231:報告日 2025-06-04 因子 0.985(其後 07-17 除息 → 因子 1);最新 09-05 close=adj=120
        rows = [("2025-06-03", 113.5, 113.5 * 0.985), ("2025-06-04", 114.0, 114.0 * 0.985), ("2025-07-16", 118.0, 118.0 * 0.985),
                ("2025-07-17", 116.3, 116.3), ("2025-09-05", 120.0, 120.0)]
        for d, cl, adj in rows:
            c.execute("INSERT INTO tw_daily_prices VALUES (?, '3231.TW', ?, ?, ?, ?, ?, 1000)", [d, cl, cl, cl, cl, adj])
        c.execute("INSERT INTO tw_daily_prices VALUES ('2025-09-05', '2606.TW', 70, 70, 70, 70, 70, 100)")
        c.execute("""CREATE TABLE vrn_report_basic(report_file VARCHAR, ticker VARCHAR, name_official VARCHAR, broker VARCHAR, report_date VARCHAR, rating_raw VARCHAR,
                     target_price DOUBLE, price DOUBLE, upside_report DOUBLE, upside_calc DOUBLE, upside_state VARCHAR, title_head VARCHAR, summary_head VARCHAR,
                     conflicts VARCHAR, extracted_at VARCHAR, price_db DOUBLE, upside_db DOUBLE, price_state VARCHAR)""")
        c.execute("INSERT INTO vrn_report_basic VALUES ('Citi-3231 20250604','3231','緯創','Citi','2025-06-04','Buy',165,114,44.7,44.7,'EXACT','緯創 維持買進','',NULL,'t',113.5,45.4,'P_CONFIRMED_DB')")
        c.execute("INSERT INTO vrn_report_basic VALUES ('華南-2606 20250901','2606','裕民','華南','2025-09-01',NULL,NULL,NULL,NULL,NULL,'MISSING_SOURCE','裕民 買進','',NULL,'t',NULL,NULL,NULL)")
        c.execute("INSERT INTO vrn_report_basic VALUES ('兆豐-9999 20250801','9999','無價','兆豐','2025-08-01',NULL,78,NULL,NULL,NULL,'MISSING_SOURCE','無價 買進','',NULL,'t',NULL,NULL,NULL)")
        c.execute("CREATE TABLE vrn_report_metrics(report_file VARCHAR, metric VARCHAR, period VARCHAR, status VARCHAR, value DOUBLE, raw_text VARCHAR)")
        c.execute("INSERT INTO vrn_report_metrics VALUES ('Citi-3231 20250604','EPS','2025E','REPORT_ESTIMATE',7.2,'2025E EPS 7.2'), ('Citi-3231 20250604','EPS','2026E','REPORT_ESTIMATE',8.0,'2026E EPS 8.0'), ('Citi-3231 20250604','EPS','2027E','REPORT_ESTIMATE',9.6,'2027E EPS 9.6')")
        c.close()
        (zdir / "Citi-3231 20250604.json").write_text(json.dumps({"header": "標題: 緯創(3231.TW) 維持買進", "right": "目標價: 165 元\n評價方式: PE 20x 2026E\n基於: AI 伺服器出貨放量",
                                                                  "body": page.split("\n", 4)[4], "footer": "x"}, ensure_ascii=False), encoding="utf-8")
        (zdir / "華南-2606 20250901.json").write_text(json.dumps({"header": "", "right": "", "body": "裕民 買進 觀點:運價回升。", "footer": ""}, ensure_ascii=False), encoding="utf-8")
        rep = run(dbp, zdir, do_print=False, reports=tdp / "rep")
        d = {r["report_file"]: r for r in rep["rows"]}
        citi = d["Citi-3231 20250604"]
        f = 0.985
        chk("③ 除權息調整律(報告日 06-04 因子 0.985 → 最新 1.0;事件日 07-17;TP 165 × 0.985 = 162.53;上漲 =(162.53−120)/120)",
            citi["adjust_method"] == "PRICE_FACTOR_CHAIN" and abs(citi["adjust_factor"] - f) < 1e-9 and citi["ex_dates"] == ["2025-07-17"]
            and citi["tp_adj"] == 162.53 and abs(citi["upside_now"] - (162.53 - 120) / 120) < 1e-9 and citi["adj_date"] == "2025-09-05",
            f"({citi['adjust_note']})")
        k1 = citi["points"]["K1"]["text"]
        chk("④ K1 契約(潛在上漲空間 % · 最新 adj close 日/價 · 目標價 來源 · 除權息調整標註 · 評價方式 · 基於 · 報告時上漲另列)",
            citi["points"]["K1"]["grounded"] and k1.startswith("潛在上漲空間 35.4%") and "2025-09-05 120.0元" in k1 and "目標價 165元(報告正文)" in k1
            and "除權息調整 0.9850 → 162.53元" in k1 and "評價方式 PE 20x 2026E" in k1 and "基於 AI 伺服器出貨放量" in k1 and "報告時上漲 45.4%" in k1, f"({k1[:120]})")
        k2 = citi["points"]["K2"]["text"]
        chk("⑤ K2 契約(EPS 冊 2025/2026/2027 + 2028 未提及 · YoY 11.1%/20.0% · 主要原因原句)",
            citi["points"]["K2"]["grounded"] and "稀釋EPS 2025 7.2、2026 8、2027 9.6、2028 未提及" in k2 and "2026 YoY 11.1%" in k2 and "2027 YoY 20.0%" in k2 and "主要原因 AI 伺服器" in k2, f"({k2[:120]})")
        chk("⑥ K3/K4 首頁其餘對半(去已用標籤行;原文)+K5 風險原句+標題接地",
            citi["points"]["K3"]["grounded"] and citi["points"]["K4"]["grounded"] and "產能" in citi["points"]["K3"]["text"] + citi["points"]["K4"]["text"]
            and citi["points"]["K5"]["text"] == "匯率與關稅" and citi["points"]["headline"]["grounded"] and citi["qc"] == "GREEN", f"({citi['novel_numbers']})")
        hn = d["華南-2606 20250901"]
        chk("⑦ 無目標價=K1 未提及(不拿共識/close 頂替);正文無標籤=標題 ungrounded(檔頭);K5 可空",
            hn["points"]["K1"]["text"] == "未提及" and not hn["points"]["K1"]["grounded"] and not hn["points"]["headline"]["grounded"] and hn["points"]["K5"]["text"] == "未提及")
        zf = d["兆豐-9999 20250801"]
        chk("⑧ SSOT 目標價有、該檔不在價表=上漲空間未算(誠實列原因);K1 仍接地(目標價出自 VRN_SSOT)",
            zf["tp"] == 78 and zf["tp_src"] == "VRN_SSOT" and zf["upside_now"] is None and "上漲空間未算" in zf["points"]["K1"]["text"] and zf["points"]["K1"]["grounded"])
        rep2 = run(dbp, zdir, do_print=False, reports=tdp / "rep")
        c = duckdb.connect(str(dbp), read_only=True)
        n = c.execute(f"SELECT count(*), count(DISTINCT report_file) FROM {TABLE}").fetchone()
        c.close()
        chk("⑨ 落庫+重跑冪等(派生層重算=同 report_file 重寫;3 列)+JSON/HTML 零 CDN",
            n == (3, 3) and rep2["summary"]["reports"] == 3 and (tdp / "rep" / "DIGEST_latest.json").exists()
            and 'src="http' not in (tdp / "rep" / "DIGEST_latest.html").read_text(encoding="utf-8"))
        px0 = price_context(duckdb.connect(str(dbp), read_only=True), "3231", None)
        chk("⑩ 報告日缺=不除權息調整(目標價照列;誠實註記)", px0["adjust_method"] == "NONE" and "報告日缺" in px0["adjust_note"] and px0["adj_close"] == 120.0)
        mt = build_digest("目標價 78 元", {"target_price": 78, "target_price_raw": "78;128", "title_head": "x"}, [], {"adj_close": None, "adjust_note": "該檔不在價表"})
        chk("⑪ 多值目標價列示不平均(78;128 只列,不取均)", "不平均" not in mt["points"]["K1"]["text"] or "78;128" in mt["points"]["K1"]["text"])
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑫ 紀律宣告(只增不減/原件零觸碰/誠實三態/零網路/尾版律/quote-or-abstain/ACCEL-BRIDGE)",
        all(k in src for k in ("只增不減", "原件零觸碰", "誠實三態", "零網路", "尾版律", "quote-or-abstain", "ACCEL-BRIDGE")))
    # ── 批419 二檢:K1 兩道閘。fixture 的比值與天數全部取自操作員 37 份真文摘 ──
    chk("⑬ 目標價合理性閘(批419:工作站真跑 37 份,三份的 TP/價 比是 0.020(MS-2308)、"
        "0.019(MS-8210)、0.005(JP-3653)——目標價只有股價的 1/50 到 1/200,那是抽錯的數。"
        "把它印成「潛在上漲空間 -98.0%」比不印更糟,讀的人會以為那是預測。"
        "閘只 flag 不丟棄:我們不知道哪個數字才對,丟棄等於替操作員決定)",
        tp_sanity(37.8, 1850.0)[0] == "TP_SUSPECT"
        and tp_sanity(17.81, 937.0)[0] == "TP_SUSPECT"
        and tp_sanity(25.84, 5655.0)[0] == "TP_SUSPECT"
        and tp_sanity(2577.41, 2070.0)[0] == "OK"        # 凱基 3665 上漲 24.5%=正常
        and tp_sanity(200.31, 68.6)[0] == "OK"           # 泓德 +192% 仍在帶內=不亂殺
        and tp_sanity(None, 100.0)[0] == "NA" and tp_sanity(10.0, 0)[0] == "NA",
        f"(2308 {tp_sanity(37.8, 1850.0)[1]:.3f} · 3665 {tp_sanity(2577.41, 2070.0)[1]:.3f})")

    chk("⑭ 價格基準日律(批419:37 份全部拿 2026-09-07 的價比,但 Daiwa-1319 是 2023-10-11 "
        "的報告=距今 1062 天。拿三年後的價算三年前報告的「潛在上漲空間」,算出來的不是上漲空間,"
        "是事後看圖。逾 180 天即非當期:改把「報告時上漲」放頭,今日比值降為參考)",
        basis_age("2023-10-11", "2026-09-07") == 1062
        and basis_state(1062) == "STALE_BASIS"
        and basis_age("2026-05-19", "2026-09-07") == 111
        and basis_state(111) == "CURRENT"
        and basis_state(basis_age("2025-12-08", "2026-09-07")) == "STALE_BASIS"   # 273 天
        and basis_state(None) == "UNKNOWN" and basis_age("", "2026-09-07") is None,
        f"(1319 {basis_age('2023-10-11', '2026-09-07')}天={basis_state(1062)} · "
        f"3665 {basis_age('2026-05-19', '2026-09-07')}天={basis_state(111)})")

    # ── 批419b 一檢:閘門自己的診斷值不得被 novel numbers 判成「發明的數字」──
    _k1_suspect = ("目標價疑為擷取誤判(不列為潛在上漲空間):目標價 38元(報告正文)"
                   " vs 最新 adj close 2026-09-07 1850元 → 比值 0.020"
                   f"(合理帶 {TP_SANITY_LO}–{TP_SANITY_HI});待人工核 PDF")
    _src = "目標價 38 元 現價 1850"
    _gate_derived = ["0.020", str(TP_SANITY_LO), str(TP_SANITY_HI), "2026-09-07"]
    chk("⑮ 閘門診斷值不算新數字(批419b 我自己造的回歸:批419 的 K1 會印比值 0.020 與"
        "合理帶界 0.2/5.0,那是關於擷取的後設說明,不是報告裡的宣稱;拿 novel numbers 查它們"
        "等於要求判準本身也要出現在正文裡。工作站實錄 MS-2308/MS-8210/JP-3653 三份因此 QC 紅、"
        "vrn_fourpoint rc=1——整段鏈被自己的診斷訊息判死)",
        novel_numbers(_k1_suspect, _src, _gate_derived) == []
        # 對照組:不把診斷值放進 derived,就會被判成新數字=證明這檢不是空檢
        and novel_numbers(_k1_suspect, _src, []) != []
        # 真的發明的數字照樣抓得到(閘門不是萬用赦免)
        and novel_numbers(_k1_suspect + " 另有神祕數 7777", _src, _gate_derived) == ["7777"],
        f"(帶診斷值 {novel_numbers(_k1_suspect, _src, _gate_derived)} · "
        f"不帶 {novel_numbers(_k1_suspect, _src, [])[:3]})")

    print(f"  [計] 十五檢 OK {15 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def _arg(a: list, flag: str, default=None):
    if flag in a:
        i = a.index(flag)
        if i + 1 < len(a):
            return a[i + 1]
    return default


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== VRN 一題四點文摘(VRN_ENG080_FourPointDigest)· 十五檢自測(零網路;臨時庫)===")
        return selftest()
    verb = next((x for x in a if x in ("run", "show")), "run")   # 批387:動詞白名單(--ticker 2330 不得誤判為動詞)
    try:
        import duckdb  # noqa: F401
    except Exception:
        print(f"[FAIL] duckdb 缺於 {sys.executable}=本引擎不可跑;修法:via-rungate --family vrn --approve-install(裝進 via_vrn_312;只增不減)或 via-envgov apply --approve --only-kind REPAIR_BASE")
        return 3
    try:
        if verb == "run":
            rep = run(_arg(a, "--db"), _arg(a, "--zones"), _arg(a, "--ticker"), int(_arg(a, "--limit") or 0) or None, do_print="--json" not in a)
            if "--json" in a:
                print(json.dumps(rep, ensure_ascii=False, indent=1))
            return 0 if rep["verdict"] != "RED" else 1
        if verb == "show":
            rest = a[a.index("show") + 1:]
            key = next((x for i, x in enumerate(rest) if not x.startswith("--") and not (i > 0 and rest[i - 1] in ("--db", "--zones", "--ticker", "--limit"))), "")
            return show(key, _arg(a, "--db"))
        print(__doc__)
        return 2
    except BrokenPipeError:
        return 0


if __name__ == "__main__":
    sys.exit(main())
