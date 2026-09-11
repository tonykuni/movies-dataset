# -*- coding: utf-8 -*-
# VIA_TWTickerRegex.py  v0100  (2026-09-07)
# VeritasIntelligenceAnalytics / FNC field-regex family
# 台股代號 Regex 整合驗證模組: 一般股 / 特別股 / 8 類 ETF (含外幣計價變體) x 3 種格式 (Plain / yfinance / Bloomberg)
# 治理: 只增不減 -- SECTION A 為原始定義逐字保留 (含已知缺陷者標 DORMANT), SECTION B 為新增/修正, SECTION C 為註冊表+分類器+自測
import re
import sys
import os
import json
import html
import datetime

# =====================================================================
# SECTION A: 原始定義 (逐字保留, 只增不減)
# =====================================================================
# --- 一般上市櫃公司代號 (純4位數字, 首位非0) ---
TW_StockTickerRegex = re.compile(r"^([1-9]\d{3})$")
TW_YFinance_StockTickerRegex = re.compile(r"^([1-9]\d{3})\.(TW|TWO)$")
TW_BBG_StockTickerRegex = re.compile(r"^([1-9]\d{3})\sTT$")
# --- 主動式 ETF 代號 (00開頭 + 3位數字 + A股票型或D債券型結尾) ---
TW_ActiveETFRegex = re.compile(r"^(00\d{3}[AD])$")
TW_YFinance_ActiveETFRegex = re.compile(r"^(00\d{3}[AD])\.(TW|TWO)$")
TW_BBG_ActiveETFRegex = re.compile(r"^(00\d{3}[AD])\sTT$")
# --- 傳統債券型 ETF (00開頭 + 3位數字 + B結尾) ---
TW_BondETFRegex = re.compile(r"^(00\d{3}B)$")
TW_YFinance_BondETFRegex = re.compile(r"^(00\d{3}B)\.(TW|TWO)$")
TW_BBG_BondETFRegex = re.compile(r"^(00\d{3}B)\sTT$")
# --- 槓桿型 ETF (00開頭 + 3位數字 + L結尾) ---
TW_LeverageETFRegex = re.compile(r"^(00\d{3}L)$")
TW_YFinance_LeverageETFRegex = re.compile(r"^(00\d{3}L)\.(TW|TWO)$")
TW_BBG_LeverageETFRegex = re.compile(r"^(00\d{3}L)\sTT$")
# --- 反向型 ETF (00開頭 + 3位數字 + R結尾) ---
TW_ReverseETFRegex = re.compile(r"^(00\d{3}R)$")
TW_YFinance_ReverseETFRegex = re.compile(r"^(00\d{3}R)\.(TW|TWO)$")
TW_BBG_ReverseETFRegex = re.compile(r"^(00\d{3}R)\sTT$")
# --- 期貨型 ETF (00開頭 + 3位數字 + U台幣計價或V外幣計價結尾) ---
TW_FuturesETFRegex = re.compile(r"^(00\d{3}[UV])$")
TW_YFinance_FuturesETFRegex = re.compile(r"^(00\d{3}[UV])\.(TW|TWO)$")
TW_BBG_FuturesETFRegex = re.compile(r"^(00\d{3}[UV])\sTT$")
# --- 平衡型 / 累積型 ETF (00開頭 + 3位數字 + T結尾) ---
TW_BalancedETFRegex = re.compile(r"^(00\d{3}T)$")
TW_YFinance_BalancedETFRegex = re.compile(r"^(00\d{3}T)\.(TW|TWO)$")
TW_BBG_BalancedETFRegex = re.compile(r"^(00\d{3}T)\sTT$")
# --- (補充) 傳統被動型 台股/海外股票 ETF (純5位數字, 如 0050, 006208) ---
# [DORMANT v0100] 缺陷: 只吃 5 碼 (00xxx); 0050 為 4 碼、006208/009800 為 6 碼 → 皆 miss。
#                 保留原名不動, 修正版見 SECTION B 的 *_v2。
TW_PassiveEquityETFRegex = re.compile(r"^(00\d{3})$")
TW_YFinance_PassiveEquityETFRegex = re.compile(r"^(00\d{3})\.(TW|TWO)$")
TW_BBG_PassiveEquityETFRegex = re.compile(r"^(00\d{3})\sTT$")

# =====================================================================
# SECTION B: 新增 / 修正 (v0100)  依據: 證交所「中華民國證券市場編碼原則」2024-11-18 新制
#   一般股票 ETF: 00 + 2~4 碼流水 (4~6 碼全數字), 外幣計價第六碼 K
#   槓桿 L (外幣 M) / 反向 R (外幣 S) / 債券 B (外幣 C) / 期貨 U (外幣 V) / 主動 A,D / 平衡 T
# =====================================================================
# B1 被動型股票 ETF 修正版: 4~6 碼全數字 (0050 / 00878 / 009800 / 006208 / 004001)
TW_PassiveEquityETFRegex_v2 = re.compile(r"^(00\d{2,4})$")
TW_YFinance_PassiveEquityETFRegex_v2 = re.compile(r"^(00\d{2,4})\.(TW|TWO)$")
TW_BBG_PassiveEquityETFRegex_v2 = re.compile(r"^(00\d{2,4})\sTT$")
# B2 外幣計價變體
TW_FXPassiveEquityETFRegex = re.compile(r"^(00\d{3}K)$")
TW_YFinance_FXPassiveEquityETFRegex = re.compile(r"^(00\d{3}K)\.(TW|TWO)$")
TW_BBG_FXPassiveEquityETFRegex = re.compile(r"^(00\d{3}K)\sTT$")
TW_FXLeverageETFRegex = re.compile(r"^(00\d{3}M)$")
TW_YFinance_FXLeverageETFRegex = re.compile(r"^(00\d{3}M)\.(TW|TWO)$")
TW_BBG_FXLeverageETFRegex = re.compile(r"^(00\d{3}M)\sTT$")
TW_FXReverseETFRegex = re.compile(r"^(00\d{3}S)$")
TW_YFinance_FXReverseETFRegex = re.compile(r"^(00\d{3}S)\.(TW|TWO)$")
TW_BBG_FXReverseETFRegex = re.compile(r"^(00\d{3}S)\sTT$")
TW_FXBondETFRegex = re.compile(r"^(00\d{3}C)$")
TW_YFinance_FXBondETFRegex = re.compile(r"^(00\d{3}C)\.(TW|TWO)$")
TW_BBG_FXBondETFRegex = re.compile(r"^(00\d{3}C)\sTT$")
# B3 特別股 (4碼 + 英文字母, 如 2881A / 2882B / 1312A)
TW_PreferredStockRegex = re.compile(r"^([1-9]\d{3}[A-Z])$")
TW_YFinance_PreferredStockRegex = re.compile(r"^([1-9]\d{3}[A-Z])\.(TW|TWO)$")
TW_BBG_PreferredStockRegex = re.compile(r"^([1-9]\d{3}[A-Z])\sTT$")
# B4 Bloomberg 寬鬆格式: 允許 "2330 TT Equity" (yellow-key) 與多空白
TW_BBG_AnyTickerLooseRegex = re.compile(r"^(00\d{2,4}|00\d{3}[A-DKLMRSTUV]|[1-9]\d{3}[A-Z]?)\s+TT(?:\s+Equity)?$", re.IGNORECASE)

# =====================================================================
# SECTION C: 註冊表 (優先序) + 分類器 + 三態推導 + 自測 + HTML 報告
# =====================================================================
REGISTRY = [
    # (class_id, 中文, 第六碼, plain, yfinance, bloomberg)
    ("STOCK",          "一般上市櫃公司",      "-",    TW_StockTickerRegex,               TW_YFinance_StockTickerRegex,               TW_BBG_StockTickerRegex),
    ("PREFERRED",      "特別股",              "A-Z",  TW_PreferredStockRegex,            TW_YFinance_PreferredStockRegex,            TW_BBG_PreferredStockRegex),
    ("ETF_ACTIVE",     "主動式 ETF",          "A/D",  TW_ActiveETFRegex,                 TW_YFinance_ActiveETFRegex,                 TW_BBG_ActiveETFRegex),
    ("ETF_BOND",       "債券型 ETF",          "B",    TW_BondETFRegex,                   TW_YFinance_BondETFRegex,                   TW_BBG_BondETFRegex),
    ("ETF_BOND_FX",    "債券型 ETF (外幣)",   "C",    TW_FXBondETFRegex,                 TW_YFinance_FXBondETFRegex,                 TW_BBG_FXBondETFRegex),
    ("ETF_LEVERAGE",   "槓桿型 ETF",          "L",    TW_LeverageETFRegex,               TW_YFinance_LeverageETFRegex,               TW_BBG_LeverageETFRegex),
    ("ETF_LEVERAGE_FX","槓桿型 ETF (外幣)",   "M",    TW_FXLeverageETFRegex,             TW_YFinance_FXLeverageETFRegex,             TW_BBG_FXLeverageETFRegex),
    ("ETF_REVERSE",    "反向型 ETF",          "R",    TW_ReverseETFRegex,                TW_YFinance_ReverseETFRegex,                TW_BBG_ReverseETFRegex),
    ("ETF_REVERSE_FX", "反向型 ETF (外幣)",   "S",    TW_FXReverseETFRegex,              TW_YFinance_FXReverseETFRegex,              TW_BBG_FXReverseETFRegex),
    ("ETF_FUTURES",    "期貨型 ETF (台幣U/外幣V)", "U/V", TW_FuturesETFRegex,            TW_YFinance_FuturesETFRegex,                TW_BBG_FuturesETFRegex),
    ("ETF_BALANCED",   "平衡型 ETF",          "T",    TW_BalancedETFRegex,               TW_YFinance_BalancedETFRegex,               TW_BBG_BalancedETFRegex),
    ("ETF_PASSIVE_FX", "被動股票 ETF (外幣)", "K",    TW_FXPassiveEquityETFRegex,        TW_YFinance_FXPassiveEquityETFRegex,        TW_BBG_FXPassiveEquityETFRegex),
    ("ETF_PASSIVE",    "被動股票 ETF (v2)",   "數字", TW_PassiveEquityETFRegex_v2,       TW_YFinance_PassiveEquityETFRegex_v2,       TW_BBG_PassiveEquityETFRegex_v2),
]

def classify(ticker):
    """回傳 dict(cls, code, venue, fmt) 或 None。fmt ∈ PLAIN / YF / BBG。venue ∈ TW / TWO / None。"""
    s = ticker.strip()
    for cls, _zh, _sfx, p_plain, p_yf, p_bbg in REGISTRY:
        m = p_plain.match(s)
        if m:
            return {"cls": cls, "code": m.group(1), "venue": None, "fmt": "PLAIN"}
        m = p_yf.match(s)
        if m:
            return {"cls": cls, "code": m.group(1), "venue": m.group(2), "fmt": "YF"}
        m = p_bbg.match(s)
        if m:
            return {"cls": cls, "code": m.group(1), "venue": None, "fmt": "BBG"}
    return None

def derive(code, venue="TW"):
    """三態推導: plain / yfinance / bloomberg。venue 未知時預設 TW (上市); 上櫃請傳 TWO。"""
    return {"plain": code, "yfinance": f"{code}.{venue}", "bloomberg": f"{code} TT"}

# ---------- 自測樣本: (輸入, 預期 class 或 None, 說明) ----------
CASES = [
    ("2330", "STOCK", "台積電 plain"), ("2330.TW", "STOCK", "yfinance 上市"), ("6488.TWO", "STOCK", "yfinance 上櫃"), ("2330 TT", "STOCK", "Bloomberg"),
    ("2881A", "PREFERRED", "富邦特"), ("2882B.TW", "PREFERRED", "國泰特乙 yfinance"),
    ("00981A", "ETF_ACTIVE", "主動統一台股增長"), ("00981A.TW", "ETF_ACTIVE", "主動 yfinance"), ("00981A TT", "ETF_ACTIVE", "主動 Bloomberg"), ("00980D", "ETF_ACTIVE", "主動債券型 D"),
    ("00679B", "ETF_BOND", "元大美債20年"), ("00687B.TW", "ETF_BOND", "國泰20年美債"), ("00679C", "ETF_BOND_FX", "債券外幣 C (假設碼)"),
    ("00631L", "ETF_LEVERAGE", "0050正2"), ("00663M", "ETF_LEVERAGE_FX", "槓桿外幣 M (假設碼)"),
    ("00632R", "ETF_REVERSE", "0050反1"), ("00664S", "ETF_REVERSE_FX", "反向外幣 S (假設碼)"),
    ("00635U", "ETF_FUTURES", "期元大S&P黃金"), ("00682V", "ETF_FUTURES", "期貨外幣 V (假設碼)"),
    ("00980T", "ETF_BALANCED", "凱基美國Top股債平衡"),
    ("00643K", "ETF_PASSIVE_FX", "深證中小 外幣受益憑證"),
    ("0050", "ETF_PASSIVE", "4碼 (原regex miss)"), ("00878", "ETF_PASSIVE", "5碼"), ("006208", "ETF_PASSIVE", "6碼舊制 (原regex miss)"), ("009800", "ETF_PASSIVE", "6碼新制 2024-11-18 起"), ("004001", "ETF_PASSIVE", "6碼新制第二階段"),
    ("0050.TW", "ETF_PASSIVE", "4碼 yfinance"), ("009800 TT", "ETF_PASSIVE", "6碼 Bloomberg"),
    # 負樣本
    ("0330", None, "首位0 非ETF前綴"), ("233", None, "3碼"), ("23300", None, "5碼純數字非00開頭"), ("2330.TWX", None, "錯後綴"),
    ("00981a", None, "小寫字母 (嚴格格式拒收)"), ("2330TT", None, "BBG 無空白"), ("00981AB", None, "雙字母"), ("0098000", None, "7碼"),
    ("00980X", None, "未定義第六碼 X"), ("2330.TW ", "STOCK", "尾端空白 strip 後可解"), ("", None, "空字串"),
]

def run_selftest():
    rows, ok = [], True
    for inp, exp, note in CASES:
        r = classify(inp)
        got = r["cls"] if r else None
        passed = (got == exp)
        ok &= passed
        rows.append({"input": inp, "expected": exp, "got": got, "code": (r or {}).get("code"), "venue": (r or {}).get("venue"),
                     "fmt": (r or {}).get("fmt"), "pass": passed, "note": note, "kind": "TEST"})
    # 互斥性: 每個正樣本在 plain 層只能命中一個 class
    for inp, exp, _ in CASES:
        if exp is None:
            continue
        s = inp.strip()
        hits = [cls for cls, _z, _s, pp, py, pb in REGISTRY if pp.match(s) or py.match(s) or pb.match(s)]
        passed = (len(hits) == 1)
        ok &= passed
        rows.append({"input": inp, "expected": "1 hit", "got": f"{len(hits)} hit(s): {','.join(hits)}", "code": None, "venue": None, "fmt": None,
                     "pass": passed, "note": "互斥性", "kind": "EXCLUSIVE"})
    # 三態推導往返
    for code, venue in (("2330", "TW"), ("6488", "TWO"), ("0050", "TW"), ("00981A", "TW")):
        d = derive(code, venue)
        back = [classify(d["plain"]), classify(d["yfinance"]), classify(d["bloomberg"])]
        passed = all(b and b["code"] == code for b in back) and back[1]["venue"] == venue
        ok &= passed
        rows.append({"input": code, "expected": "3/3 往返", "got": json.dumps(d), "code": code, "venue": venue, "fmt": "DERIVE",
                     "pass": passed, "note": "三態推導", "kind": "DERIVE"})
    # 診斷: 原始 DORMANT regex 的已知缺陷 (預期 miss, 僅記錄, 不計入 FAIL)
    for inp in ("0050", "006208", "009800"):
        rows.append({"input": inp, "expected": "miss (已知缺陷)", "got": "hit" if TW_PassiveEquityETFRegex.match(inp) else "miss",
                     "code": None, "venue": None, "fmt": "PLAIN", "pass": True, "note": "原 TW_PassiveEquityETFRegex ^(00\\d{3})$ → DORMANT", "kind": "DIAG"})
    # 寬鬆 BBG
    for inp, exp in (("2330 TT Equity", True), ("00981A  tt equity", True), ("2330 TT Corp", False)):
        got = bool(TW_BBG_AnyTickerLooseRegex.match(inp))
        ok &= (got == exp)
        rows.append({"input": inp, "expected": str(exp), "got": str(got), "code": None, "venue": None, "fmt": "BBG-LOOSE", "pass": got == exp, "note": "Bloomberg 寬鬆", "kind": "TEST"})
    return ok, rows

def write_html(path, ok, rows, mod_path):
    n_all = sum(1 for r in rows if r["kind"] != "DIAG")
    n_pass = sum(1 for r in rows if r["kind"] != "DIAG" and r["pass"])
    verdict = "PASS" if ok else "FAIL"
    color = "#5a9e6f" if ok else "#c96b5a"
    tr = []
    for r in rows:
        bg = "" if r["pass"] else ' style="background:#3a2320"'
        tr.append(f'<tr{bg}><td>{html.escape(r["kind"])}</td><td><code>{html.escape(str(r["input"]))}</code></td><td>{html.escape(str(r["expected"]))}</td>'
                  f'<td>{html.escape(str(r["got"]))}</td><td>{html.escape(str(r["code"] or ""))}</td><td>{html.escape(str(r["venue"] or ""))}</td>'
                  f'<td>{html.escape(str(r["fmt"] or ""))}</td><td>{"✔" if r["pass"] else "✘"}</td><td>{html.escape(r["note"])}</td></tr>')
    reg = "".join(f'<tr><td>{c}</td><td>{z}</td><td>{s}</td><td><code>{html.escape(pp.pattern)}</code></td><td><code>{html.escape(py.pattern)}</code></td><td><code>{html.escape(pb.pattern)}</code></td></tr>'
                  for c, z, s, pp, py, pb in REGISTRY)
    doc = f"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><title>VIA TW Ticker Regex 整合驗證 v0100</title>
<style>body{{font-family:Segoe UI,Microsoft JhengHei,sans-serif;background:#1e1f24;color:#e6e6e6;margin:24px}}
h1{{font-size:20px}} .badge{{display:inline-block;padding:6px 14px;border-radius:6px;background:{color};color:#fff;font-weight:700}}
table{{border-collapse:collapse;width:100%;font-size:13px;margin-top:12px}} th,td{{border:1px solid #444;padding:5px 8px;text-align:left;vertical-align:top}}
th{{background:#2c2d33}} code{{color:#f0c36d}} .meta{{color:#aaa;font-size:12px}}</style></head><body>
<h1>VeritasIntelligenceAnalytics · TW Ticker Regex 整合驗證 v0100 <span class="badge">{verdict} {n_pass}/{n_all}</span></h1>
<div class="meta">{datetime.datetime.now():%Y-%m-%d %H:%M:%S} · 模組 {html.escape(mod_path)} · 治理: 只增不減 (SECTION A 原樣保留, 缺陷者標 DORMANT)</div>
<h2>註冊表 (分類優先序 上→下)</h2>
<table><tr><th>class</th><th>類別</th><th>第六碼</th><th>Plain</th><th>yfinance</th><th>Bloomberg</th></tr>{reg}</table>
<h2>驗證結果</h2>
<table><tr><th>kind</th><th>input</th><th>expected</th><th>got</th><th>code</th><th>venue</th><th>fmt</th><th>✔</th><th>note</th></tr>{"".join(tr)}</table>
</body></html>"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(doc)

if __name__ == "__main__":
    out_html = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "VIA_TWTickerRegex_Report.html")
    ok, rows = run_selftest()
    write_html(out_html, ok, rows, os.path.abspath(__file__))
    with open(os.path.splitext(out_html)[0] + ".json", "w", encoding="utf-8") as f:
        json.dump({"verdict": "PASS" if ok else "FAIL", "rows": rows}, f, ensure_ascii=False, indent=1)
    n = sum(1 for r in rows if r["kind"] != "DIAG")
    p = sum(1 for r in rows if r["kind"] != "DIAG" and r["pass"])
    print(f"[VIA_TWTickerRegex] {'PASS' if ok else 'FAIL'} {p}/{n}  report={out_html}")
    for r in rows:
        if not r["pass"]:
            print(f"  FAIL {r['kind']:9} {r['input']!r:14} expected={r['expected']} got={r['got']}")
    sys.exit(0 if ok else 1)
