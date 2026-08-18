#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vrn_method_kernel_v0100 — VRN 方法核(TOOL-071)
====================================================================
操作員令(批43,2026-08-19):「以下應統一成 VRN 的『五區抽取、
雙層保存、官方對照、算術勾稽、證據仲裁』方法。核心原則:券商報告
內容保留原貌,TWSE/TPEX 官方資料作為實績 SSOT;任何差異不得直接
覆寫原始資料。」
定位:
  ① 方法冊=knowledge/VRN_Method_SSOT_v0100.json(def01-20 全文
     立冊,入 TOOL-069 中央參數樞紐);本核=方法的可執行函式庫,
     供 MDL006/007/008 及後續引擎統一 import,不各自再造。
  ② 雙層保存 FieldRecord:raw_value 永不覆寫(唯讀 property),
     normalized/official/calculated/difference/validation_status/
     evidence 七層並存。
  ③ 混合容忍 def15:max(abs_tol, rel_tol×max(|A|,|B|));
     PASS≤Tol<WARN≤3×Tol<FAIL;百分比走百分點差。
  ④ 成長率 def11:轉盈/轉虧/雙負/零基/缺基六態,零基禁極小值。
  ⑤ 單季換算 def18:IS/CF 可減,BS 禁(期末存量),EPS 近似標註。
  ⑥ 仲裁 def17:八情境查表;官方 canonical 券商保留,預估不仲裁。
  ⑦ --audit:五引擎(MDL002/006/007/008+xcheck)方法符合度矩陣
     (唯讀掃描,誠實 rich 呈現);--selftest 十二檢(含方法文自帶
     算例:1450/1200=20.8333%、35.2 vs 35.16=0.04 百分點)。
用法:
  via-method --selftest     → 十二檢
  via-method --audit        → 五引擎方法符合度矩陣(唯讀)
  via-method --show DEF     → 印方法冊條目(如 --show def15)
"""
from __future__ import annotations

import json
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
METHOD_PATH = HERE / "knowledge" / "VRN_Method_SSOT_v0100.json"


def load_method() -> dict:
    return json.loads(METHOD_PATH.read_text(encoding="utf-8-sig"))


# ── 雙層保存(def01):raw 永不覆寫 ───────────────────────────
@dataclass
class FieldRecord:
    """七層並存;raw_value 建構後唯讀(券商原貌保留鐵律)"""
    _raw_value: object = None
    raw_unit: str = ""
    normalized_value: float | None = None
    normalized_unit: str = ""
    unit_multiplier: float = 1.0
    currency: str = "TWD"
    official_value: float | None = None
    calculated_value: float | None = None
    difference: float | None = None
    validation_status: str = "REVIEW_REQUIRED"
    evidence: dict = field(default_factory=dict)  # page/bbox/table/row_col/url/data_date

    @property
    def raw_value(self):
        return self._raw_value

    @raw_value.setter
    def raw_value(self, _):
        raise AttributeError("raw_value 永不覆寫(def01;券商報告原貌保留)")


# ── 混合容忍與三態判定(def15)────────────────────────────────
def mixed_tolerance(a: float, b: float, abs_tol: float, rel_tol: float) -> float:
    return max(abs_tol, rel_tol * max(abs(a), abs(b)))


def judge(a: float | None, b: float | None, abs_tol: float = 0.05,
          rel_tol: float = 0.005) -> tuple[str, float | None]:
    """回 (PASS/WARN/FAIL/NOT_COMPUTABLE, diff)"""
    if a is None or b is None:
        return "NOT_COMPUTABLE", None
    tol = mixed_tolerance(a, b, abs_tol, rel_tol)
    diff = abs(a - b)
    if diff <= tol:
        return "PASS", diff
    if diff <= 3 * tol:
        return "WARN", diff
    return "FAIL", diff


def pct_point_diff(reported_pct: float, recalc_pct: float) -> float:
    """百分比走百分點差(35.2 vs 35.16 → 0.04 個百分點,非 0.11%)"""
    return round(abs(reported_pct - recalc_pct), 6)


# ── 上漲空間重算(def03)──────────────────────────────────────
def upside_pct(target: float | None, current: float | None) -> float | None:
    if not target or not current or current == 0:
        return None
    return round((target - current) / current * 100, 4)


# ── 成長率六態(def11)────────────────────────────────────────
def growth(cur: float | None, base: float | None) -> tuple[str, float | None]:
    """絕對值分母;轉盈/轉虧另態;零基/缺基不可計算(禁極小值)"""
    if base is None:
        return "NOT_COMPUTABLE_NULL_BASE", None
    if base == 0:
        return "NOT_COMPUTABLE_ZERO_BASE", None
    if cur is None:
        return "NOT_COMPUTABLE_NULL_BASE", None
    g = round((cur - base) / abs(base) * 100, 4)
    if base < 0 and cur >= 0:
        return "TURNAROUND_TO_PROFIT", g
    if base >= 0 and cur < 0:
        return "TURNAROUND_TO_LOSS", g
    if base < 0 and cur < 0:
        return "NEG_TO_NEG_ANNOTATED", g
    return "NORMAL", g


# ── 單季換算(def18)──────────────────────────────────────────
QUARTER_ALLOWED = {"IS": True, "CF": True, "BS": False, "EPS": "APPROX", "RATIO": False}


def derive_quarter(stmt_type: str, cumulative: float | None,
                   prev_cumulative: float | None) -> tuple[str, float | None]:
    """回 (態, 值):IS/CF=OK;BS/RATIO=NOT_ALLOWED(期末存量/比率不可減);
    EPS=APPROX 近似參考(加權股數不同)"""
    allowed = QUARTER_ALLOWED.get(stmt_type.upper())
    if allowed is False or allowed is None:
        return "NOT_ALLOWED", None
    if cumulative is None or prev_cumulative is None:
        return "NOT_COMPUTABLE_NULL_BASE", None
    v = round(cumulative - prev_cumulative, 6)
    return ("APPROX" if allowed == "APPROX" else "OK"), v


# ── 損益勾稽(def07;符號正規化)────────────────────────────────
def gross_profit_check(revenue: float, cost: float, reported_gp: float,
                       abs_tol: float = 0.5, rel_tol: float = 0.005) -> tuple[str, float]:
    """成本正列=減/負列=加(不得重複負號)"""
    calc = revenue - cost if cost >= 0 else revenue + cost
    state, diff = judge(reported_gp, calc, abs_tol, rel_tol)
    return state, calc


def balance_identity(assets: float, liabilities: float, equity: float,
                     abs_tol: float = 1.0, rel_tol: float = 0.001) -> tuple[str, float]:
    """def08:資產=負債+權益;差額僅四捨五入=容忍"""
    state, _ = judge(assets, liabilities + equity, abs_tol, rel_tol)
    return state, round(assets - (liabilities + equity), 6)


def cashflow_identity(end_cash: float, begin_cash: float, op_cf: float,
                      inv_cf: float, fin_cf: float, fx_effect: float | None,
                      abs_tol: float = 1.0, rel_tol: float = 0.005) -> tuple[str, float | None]:
    """def09:缺匯率影響=INCOMPLETE_COMPONENTS(不可假設為零)"""
    if fx_effect is None:
        return "INCOMPLETE_COMPONENTS", None
    delta = end_cash - begin_cash
    total = op_cf + inv_cf + fin_cf + fx_effect
    state, diff = judge(delta, total, abs_tol, rel_tol)
    return state, diff


def free_cash_flow(op_cf: float, capex: float) -> float:
    """def09:capex 用絕對值扣(已負列不得重複負號)"""
    return round(op_cf - abs(capex), 6)


# ── 評等三層(def03)──────────────────────────────────────────
RATING_NORMALIZE = {
    "買進": "BUY", "逢低買進": "BUY", "Buy": "BUY", "Overweight": "OUTPERFORM",
    "優於大盤": "OUTPERFORM", "Outperform": "OUTPERFORM", "增持": "OUTPERFORM",
    "持有": "HOLD", "中立": "NEUTRAL", "Hold": "HOLD", "Neutral": "NEUTRAL",
    "減持": "UNDERPERFORM", "劣於大盤": "UNDERPERFORM", "賣出": "SELL", "Sell": "SELL",
}
RATING_ACTIONS = ["INITIATE", "UPGRADE", "DOWNGRADE", "MAINTAIN", "SUSPEND", "NOT_RATED"]


def rating_layers(raw: str, action_hint: str = "") -> dict:
    act = "MAINTAIN"
    for a, kws in [("INITIATE", ["初次", "Initiat"]), ("UPGRADE", ["調升", "上調", "Upgrade"]),
                   ("DOWNGRADE", ["調降", "下調", "Downgrade"]), ("MAINTAIN", ["維持", "Maintain"]),
                   ("SUSPEND", ["暫停", "Suspend"]), ("NOT_RATED", ["未評", "Not Rated", "NR"])]:
        if any(k in (action_hint or raw) for k in kws):
            act = a
            break
    return {"rating_raw": raw, "rating_normalized": RATING_NORMALIZE.get(raw.strip(), "REVIEW_REQUIRED"),
            "rating_action": act}


# ── 缺值語意(def16)──────────────────────────────────────────
def parse_value(raw: str) -> tuple[str, object]:
    """回 (態, 值):NULL/ZERO/DASH/NA/NM/NUM/MULTIPLE/PCT;
    (123)→-123;1.2x 保存倍數;12.3%→0.123"""
    s = str(raw).strip()
    if s == "":
        return "NULL", None
    if s in ("-", "—", "－"):
        return "DASH", None
    if s.upper() in ("N/A", "NA"):
        return "NA", None
    if s.upper() == "NM":
        return "NM", None
    m = re.fullmatch(r"\(([0-9,.]+)\)", s)
    if m:
        return "NUM", -float(m.group(1).replace(",", ""))
    m = re.fullmatch(r"([0-9,.]+)\s*[x×倍]", s)
    if m:
        return "MULTIPLE", float(m.group(1).replace(",", ""))
    m = re.fullmatch(r"(-?[0-9,.]+)\s*%", s)
    if m:
        return "PCT", round(float(m.group(1).replace(",", "")) / 100, 6)
    try:
        v = float(s.replace(",", "").replace("，", ""))
        return ("ZERO", 0.0) if v == 0 else ("NUM", v)
    except ValueError:
        return "NULL", None


# ── 證據仲裁(def17)──────────────────────────────────────────
def arbitrate(case: str) -> str:
    m = load_method()
    table = m["def17_arbitration"]
    return table.get(case, "REVIEW_REQUIRED(仲裁表外情境,候人工)")


# ── rich 矩陣(缺席降級)──────────────────────────────────────
def rich_matrix(title, columns, rows, state_col=None) -> bool:
    try:
        from rich import box
        from rich.console import Console
        from rich.table import Table
        t = Table(title=title, box=box.SIMPLE_HEAVY, title_style="bold",
                  header_style="bold cyan", pad_edge=False)
        for c in columns:
            t.add_column(c, overflow="fold", no_wrap=False)
        for r in rows:
            cells = [str(x) if x is not None else "—" for x in r]
            if state_col is not None and state_col < len(cells):
                s = cells[state_col]
                color = ("green" if s.startswith(("OK", "PASS", "IN", "APPROX"))
                         else "red" if s.startswith(("FAIL", "MISS")) else "yellow")
                cells[state_col] = f"[{color}]{s}[/{color}]"
            t.add_row(*cells)
        Console().print(t)
        return True
    except Exception:
        print(f"  ── {title}(rich 缺席,純文字降級)──")
        for r in rows:
            print("  " + " | ".join(str(x) for x in r))
        return False


# ── 五引擎方法符合度稽核(唯讀)────────────────────────────────
AUDIT_TARGETS = [
    ("MDL002 LayoutExtractor", "VRN_MDL002_LayoutExtractor.py"),
    ("MDL006 Consolidator", "VRN_MDL006_ConsolidatorAndPhaseValidator.py"),
    ("MDL007 APIDataFetcher", "VRN_MDL007_APIDataFetcher.py"),
    ("MDL008 CrossValidator", "VRN_MDL008_CrossValidator.py"),
    ("panorama_xcheck", "panorama_xcheck_v1*.py"),
]
AUDIT_MARKS = [
    ("Ticker鎖", r"TW_TICKER_REGEX"),
    ("年區排除", r"202\[1-9\]"),
    ("容忍分段/公式", r"tol(?:erance|_large|_small)|compare_tol"),
    ("官方來源", r"mops|MOPS|twse|TWSE"),
    ("不覆寫/保留", r"保留|不覆寫|canonical|append-only"),
    ("單位正規化", r"to_million|normalize_to_million|UNIT_MULT"),
    ("自驗HTML", r"SelfVerif|self_verify"),
]


def audit() -> int:
    rows = []
    n_gap = 0
    for name, pat in AUDIT_TARGETS:
        hits = sorted(HERE.glob(pat)) if "*" in pat else ([HERE / pat] if (HERE / pat).exists() else [])
        if not hits:
            rows.append([name, "MISSING", "—"])
            n_gap += 1
            continue
        text = hits[-1].read_text(encoding="utf-8", errors="replace")
        marks = [m for m, rx in AUDIT_MARKS if re.search(rx, text)]
        gaps = [m for m, rx in AUDIT_MARKS if not re.search(rx, text)]
        state = "IN-METHOD" if len(marks) >= 5 else "PARTIAL"
        if state != "IN-METHOD":
            n_gap += 1
        rows.append([f"{name}({hits[-1].name})", state,
                     f"具 {len(marks)}/7:{','.join(marks)}" + (f" · 缺:{','.join(gaps)}" if gaps else "")])
    rich_matrix("五引擎方法符合度矩陣(唯讀稽核;方法冊 def01-20 為準)",
                ["引擎", "態", "方法標記"], rows, state_col=1)
    m = load_method()
    print(f"  [冊] {METHOD_PATH.name} · 支柱:{'/'.join(m['method_pillars'])}")
    print(f"  [計] IN-METHOD {len(rows) - n_gap} · PARTIAL/MISSING {n_gap}(誠實;缺項候版更補齊,正本不就地改)")
    return 0


# ── 十二檢自測(方法文自帶算例為 fixture)───────────────────────
def selftest() -> int:
    t0 = time.time()
    fails = []

    def chk(name, cond, note=""):
        state = "OK" if cond else "FAIL"
        if not cond:
            fails.append(name)
        print(f"  [{state}] {name} {note}")

    m = load_method()
    # ① 方法冊在位且 20 def 齊
    defs = [k for k in m if k.startswith("def")]
    chk("方法冊 def01-20 齊備", len({k.split("_")[0] for k in defs}) == 20,
        f"({len(defs)} 條目)")

    # ② raw_value 永不覆寫(def01)
    fr = FieldRecord(_raw_value="1,450", raw_unit="元")
    try:
        fr.raw_value = 9999
        immut = False
    except AttributeError:
        immut = True
    chk("raw_value 永不覆寫", immut and fr.raw_value == "1,450")

    # ③ 上漲空間算例(def03):(1450-1200)/1200=20.8333%
    u = upside_pct(1450, 1200)
    chk("上漲空間重算算例", abs(u - 20.8333) < 0.001, f"({u}%)")

    # ④ 21% 合理四捨五入 PASS、25% 標記(def03+def15 百分點差)
    ok21 = judge(21.0, u, abs_tol=0.5, rel_tol=0.0)[0] == "PASS"
    bad25 = judge(25.0, u, abs_tol=0.5, rel_tol=0.0)[0] == "FAIL"
    chk("21% PASS / 25% 標記", ok21 and bad25)

    # ⑤ 毛利率算例(def15):35.2 vs 35.16=0.04 百分點(非 0.11%)
    d = pct_point_diff(35.2, 35.16)
    chk("百分點差算例", abs(d - 0.04) < 1e-9, f"({d} 百分點)")

    # ⑥ 混合容忍三態(def15):PASS/WARN/FAIL
    s1 = judge(1000.0, 1000.4, 0.5, 0.0)[0]
    s2 = judge(1000.0, 1001.2, 0.5, 0.0)[0]
    s3 = judge(1000.0, 1002.0, 0.5, 0.0)[0]
    chk("混合容忍 PASS/WARN/FAIL", (s1, s2, s3) == ("PASS", "WARN", "FAIL"))

    # ⑦ 成長率六態(def11):轉盈/轉虧/零基禁算
    chk("成長率六態", growth(5, -10)[0] == "TURNAROUND_TO_PROFIT"
        and growth(-5, 10)[0] == "TURNAROUND_TO_LOSS"
        and growth(-3, -6)[0] == "NEG_TO_NEG_ANNOTATED"
        and growth(5, 0)[0] == "NOT_COMPUTABLE_ZERO_BASE"
        and growth(5, None)[0] == "NOT_COMPUTABLE_NULL_BASE"
        and growth(12, 10) == ("NORMAL", 20.0))

    # ⑧ 單季換算(def18):IS 可減、BS 禁、EPS 近似
    chk("單季換算閘", derive_quarter("IS", 100, 40) == ("OK", 60)
        and derive_quarter("BS", 100, 40)[0] == "NOT_ALLOWED"
        and derive_quarter("EPS", 3.0, 1.2)[0] == "APPROX"
        and derive_quarter("RATIO", 1, 1)[0] == "NOT_ALLOWED")

    # ⑨ 損益/資產/現金流勾稽(def07/08/09;符號正規化+缺匯率誠實)
    gp_pos = gross_profit_check(1000, 700, 300)[0] == "PASS"      # 成本正列
    gp_neg = gross_profit_check(1000, -700, 300)[0] == "PASS"     # 成本負列
    bs = balance_identity(1000, 600, 400)[0] == "PASS"
    cf_inc = cashflow_identity(50, 10, 30, -20, 25, None)[0] == "INCOMPLETE_COMPONENTS"
    cf_ok = cashflow_identity(50, 10, 30, -20, 25, 5)[0] == "PASS"
    fcf = free_cash_flow(100, -30) == 70.0 and free_cash_flow(100, 30) == 70.0
    chk("三表勾稽+符號正規化", gp_pos and gp_neg and bs and cf_inc and cf_ok and fcf)

    # ⑩ 缺值語意(def16):NULL≠0、(123)→-123、1.2x 倍數、12.3%→0.123
    chk("缺值語意", parse_value("")[0] == "NULL" and parse_value("0") == ("ZERO", 0.0)
        and parse_value("(123)") == ("NUM", -123.0)
        and parse_value("1.2x") == ("MULTIPLE", 1.2)
        and parse_value("12.3%") == ("PCT", 0.123)
        and parse_value("N/A")[0] == "NA")

    # ⑪ 評等三層+仲裁表(def03/def17)
    r = rating_layers("優於大盤", "維持")
    arb1 = arbitrate("券商歷史實績≠官方實績")
    arb2 = arbitrate("券商預估≠他券商預估")
    chk("評等三層+仲裁表", r["rating_normalized"] == "OUTPERFORM"
        and r["rating_action"] == "MAINTAIN"
        and "官方值 canonical" in arb1 and "不仲裁" in arb2
        and "候人工" in arbitrate("未知情境"))

    # ⑫ 驗證狀態字彙+fail-closed 條款在冊(def19)
    chk("狀態字彙+fail-closed", len(m["def19_validation_statuses"]) == 11
        and "fail-closed" in m["def19_trust_score"]["fail_closed"])

    n = 12 - len(fails)
    print(f"  [計] 十二檢 OK {n} · FAIL {len(fails)} · {round(time.time() - t0, 1)}s")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== VRN 方法核 v0100 · 十二檢(方法文算例 fixture)===")
        return selftest()
    if "--audit" in args:
        print("=== VRN 方法核 v0100 · 五引擎方法符合度稽核(唯讀)===")
        return audit()
    if "--show" in args:
        i = args.index("--show")
        key = args[i + 1] if i + 1 < len(args) else ""
        m = load_method()
        hits = {k: v for k, v in m.items() if key.lower() in k.lower()}
        print(json.dumps(hits or {"_": f"「{key}」零命中(誠實)"}, ensure_ascii=False, indent=1))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
