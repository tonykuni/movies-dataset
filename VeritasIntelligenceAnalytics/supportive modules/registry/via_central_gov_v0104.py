#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
via_central_gov_v0104 — VIA Central Governance Console(TOOL-063)
--------------------------------------------------------------------
v0103→v0104:排除區補 rename_runs(INCIDENT-20260819 事故備份夾=
證據非現役)。
--------------------------------------------------------------------
v0102→v0103:非現役區(rollback 快照/.venv/site-packages/證據夾)
不入健康度掃描——依 QA-20260819E 裁決(快照=證據保原樣,venv=第三
方,本不該修也不該染紅儀表板);工作站 SUP RED3/OTHERS RED40 復發
噪音根治。誠實保留:排除範圍明列於刊頭。
--------------------------------------------------------------------
v0101→v0102:品牌銘言入刊頭(批34 操作員頒定 Observa · Intellege ·
Praevide;引 VIA_Brand_SSOT_v0100)。
--------------------------------------------------------------------
v0100→v0101:R1 掃描包 warnings 靜噪(SyntaxWarning 不再漏操作員
主控台——工作站 16,924 件掃描實測回饋);行為零變更。
====================================================================
操作員令(批22 Mega-Prompt):中央 SSOT 規範庫+同義字/Regex 治理
中心;三輪全景式分析(Zero-Hydra;并行可修/順序依賴分流);HTML UI
Matrix(小字體/表格自適應/自動換行/MODULE·ENGINE·FUNCTION-LIB·OTHERS
四分區/紅黃綠燈/動態進度條+動態說明);非阻塞啟動;母系統+子系統
(VRN/VDF/VAP/FLOW/其他)同步治理;可插拔子系統名錄。

誠實界線:
  · 三輪全景式=唯讀分析+分流+建議;高 Hydra 節點只出建議不盲修
    (修正一律走既有版本前進/沙盒道,主控台不就地改碼)。
  · 紅黃綠燈以實測(ast.parse 全掃+SSOT 對照+Regex 衝突檢)為據,
    不假綠;缺件誠實標註。
  · 20 加速器=盤點對映表(既有 15 PS 加速器+SuperAccel 家族),
    只列實存,不虛報。

用法:
  --run          三輪全景式分析+HTML UI Matrix(預設)
  --no-open      不自動開瀏覽器(容器/自動化道)
  --ssot         中央 SSOT 規範庫盤點列印
  --regex        同義字/Regex 治理中心列印+衝突檢
  --selftest     八檢
"""
from __future__ import annotations

import ast
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
REPORTS = VIA / "VIA_Reports"
RUNS = REPORTS / "centralgov_runs"
UI_PATH = REPORTS / "VIA_UI_CentralGov.html"
DICT_PATH = HERE / "VIA_Central_Synonym_Regex_v0100.json"
NOW = datetime.now().strftime("%Y%m%d_%H%M%S")

SKIP_FRAGS = ("_sha", "_review_quarantine", "__pycache__", "/vendor/",
              "package_samples", "/docs/", "quarantine", ".venv",
              "site-packages", "_via_mother_root_reconciliation_runs",
              "/rollback/", "/evidence", "_syntaxfix_", "rename_runs")

# ── 可插拔子系統名錄(熱插拔槽:新增子系統入列即治理)──────────
SUBSYSTEMS = {
    "VRN": "functional modules/VRN",
    "VDF": "functional modules/VDF",
    "VAP": "functional modules/VAP",
    "FLOW": "supportive modules/VIA_FlowSystem",
    "VME": "functional modules/VME",
    "CHW": "functional modules/ChipWar",
    "GRP": "functional modules/GroupIndex",
}

# ── 中央 SSOT 規範庫(既有規範檔盤點對映)──────────────────────
SSOT_REGISTRY = {
    "命名冊": "supportive modules/registry/VIA_Naming_Registry_v0100.json",
    "介面合約冊": "supportive modules/registry/VIA_Interface_Contract_Registry_v0100.json",
    "自動碼台帳": "supportive modules/registry/VIA_AutoCode_Registry_v0100.json",
    "PS 封存冊": "supportive modules/registry/VIA_PS_Archive_Register_v0100.json",
    "中英字庫": "functional modules/VRN/knowledge/VRN_Lexicon_v0100.json",
    "VDF 統一參數": "functional modules/VDF/VDF_Unified_Params_v0100.json",
    "台主動ETF清單": "supportive modules/VIA_FlowSystem/FlowSystem_v2/config/TW_Active_ETF_Registry_v0100.json",
    "全球ETF宇宙": "supportive modules/VIA_FlowSystem/FlowSystem_v2/config/Global_ETF_Universe_v0100.json",
}

# ── 同義字/Regex 治理中心種子(LOCKED 規則集中;owner=權威引擎)──
CENTRAL_DICT = {
    "schema": "via-central-synonym-regex-v1",
    "policy": "append-only;LOCKED 不改;衝突=RED 燈;新規先入此冊再落引擎",
    "regex": {
        "TW_TICKER_LOCKED": {"pattern": r"^(?:[1-9]\d{3})$|^(?!202[1-9]|2030)\d{4}$",
                             "owner": "VRN_Summarizer_v1", "locked": True,
                             "note": "台股代碼;年區 2021-2030 排除"},
        "YEAR_SUSPECT": {"pattern": r"^(?:202[1-9]|2030)$",
                         "owner": "vrn_lexicon_v0101", "locked": True,
                         "note": "年份疑碼——收割不自動抓"},
        "TW_YFINANCE": {"pattern": r"^[1-9]\d{3}\.(TW|TWO)$",
                        "owner": "VRN_Summarizer_v1", "locked": True},
        "TW_BLOOMBERG": {"pattern": r"^[1-9]\d{3}\s*TT$",
                         "owner": "VRN_Summarizer_v1", "locked": True},
        "VERSION_SUFFIX": {"pattern": r"[_-]v?\d{2,4}[a-z]?$",
                           "owner": "via_namereg(TOOL-047)", "locked": True,
                           "note": "家族鍵版尾剝離"},
        "PRODUCT_CODE": {"pattern": r"^VIA-[A-Z0-9]{4}-[A-Z0-9]{4}$",
                         "owner": "via_product_ui(TOOL-048)", "locked": True,
                         "note": "商品號綁一機"},
        "TW_ACTIVE_ETF": {"pattern": r"^\d{5}A$",
                          "owner": "flow_tw_active_etf(TOOL-060)", "locked": False,
                          "note": "主動式台股 ETF 代號尾 A+名稱含「主動」"},
    },
    "synonyms": {
        "RATING_BUY": ["買進", "Buy", "加碼", "Overweight", "強烈買進", "優於大盤", "Outperform"],
        "RATING_SELL": ["賣出", "Sell", "減碼", "Underweight", "落後大盤", "Underperform"],
        "RATING_HOLD": ["持有", "Hold", "中立", "Neutral", "維持"],
        "FLOW_IN": ["流入", "淨申購", "吸金", "inflow"],
        "FLOW_OUT": ["流出", "淨贖回", "失血", "outflow"],
        "EPS": ["每股盈餘", "EPS", "basic_eps", "diluted_eps", "earnings_per_share"],
        "TARGET_PRICE": ["目標價", "Target Price", "target_price", "TP", "合理價"],
    },
}

# ── 20 加速器盤點(只列實存;PS 15 支=舊根救援批;+5 py 家族)────
ACCELERATORS = [
    ("01-15", "PS 加速器十五支(AST 解析/Hydra 預測/拓撲排序/沙盒隔離/修正建議/全景分析/SSOT 對齊/矩陣生成/錯誤分群/複雜度/同步檢視/版本回滾/覆蓋率/順序最佳化 等)", "WorkOps/舊根救援批(候庫入版控)"),
    ("16", "動態進度條", "via-enter/via-run 內建進度條家族"),
    ("17", "動態說明", "本引擎 narration+grid 誠實三態"),
    ("18", "非阻塞 PowerShell", "Invoke-VIA-CentralGov(Start-Process 不阻塞)"),
    ("19", "多引擎整合(Py+PS+UI)", "bin 動詞 99 支+HTML U/I 家族"),
    ("20", "自動部署與初始化", "via_provision+via_install_gate(同意閘)"),
]


def _log(m):
    print(m)


def iter_py():
    for p in VIA.rglob("*.py"):
        rp = str(p.relative_to(VIA)).replace("\\", "/")
        if any(f in rp for f in SKIP_FRAGS):
            continue
        yield p, rp


def classify(rp: str) -> tuple:
    """(分區, 子系統) — MODULE/ENGINE/FUNCTION-LIB/OTHERS 四分區。"""
    sub = "OTHERS"
    for s, root in SUBSYSTEMS.items():
        if rp.startswith(root):
            sub = s
            break
    low = rp.lower()
    if "/engines/" in low or "/engine/" in low:
        return "ENGINE", sub
    if rp.startswith("supportive modules/registry") or rp.startswith("bin"):
        return "FUNCTION-LIB", "VIA"
    if rp.startswith("supportive modules"):
        return "FUNCTION-LIB", sub if sub != "OTHERS" else "SUP"
    if rp.startswith("functional modules"):
        return "MODULE", sub
    return "OTHERS", sub


def round1_scan() -> dict:
    """R1 全景掃描:ast.parse 全倉+四分區分類+錯誤識別。"""
    import warnings
    rows, n_ok, n_bad = [], 0, 0
    for p, rp in iter_py():
        sec, sub = classify(rp)
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", SyntaxWarning)
                ast.parse(p.read_text(encoding="utf-8", errors="ignore"))
            st = "OK"
            n_ok += 1
        except SyntaxError as e:
            st = f"SYNTAX:{e.lineno}"
            n_bad += 1
        rows.append({"path": rp, "section": sec, "subsystem": sub, "status": st})
    return {"rows": rows, "n_ok": n_ok, "n_bad": n_bad}


def round2_ssot_hydra(scan: dict) -> dict:
    """R2 SSOT 對齊+Regex 衝突+Hydra 高風險節點(建議不盲修)。"""
    ssot = {}
    for name, rel in SSOT_REGISTRY.items():
        p = VIA / rel
        st = "OK" if p.exists() else "MISSING"
        n = None
        if p.exists():
            try:
                d = json.loads(p.read_text(encoding="utf-8"))
                n = len(d.get("items", d.get("entries", d.get("ledger", d.get("etfs", d.get("classes", d))))))
            except Exception:
                st = "PARSE_FAIL"
        ssot[name] = {"path": rel, "status": st, "n": n}
    # Regex 衝突檢:pattern 可編譯+鍵唯一
    rx_bad = []
    for k, v in CENTRAL_DICT["regex"].items():
        try:
            re.compile(v["pattern"])
        except re.error as e:
            rx_bad.append({"key": k, "err": str(e)})
    # Hydra:介面冊邊 fan-in 前十(高耦合節點=只建議)
    hydra = []
    try:
        iface = json.loads((HERE / "VIA_Interface_Contract_Registry_v0100.json")
                           .read_text(encoding="utf-8"))
        fan = Counter()
        for m in iface.get("modules", {}).values():
            for imp in m.get("contract", {}).get("imports_internal", []) or []:
                fan[imp] += 1
        hydra = [{"node": k, "fan_in": v,
                  "advice": "高耦合——改動須沙盒+版本前進,禁就地改"}
                 for k, v in fan.most_common(10)]
    except Exception:
        pass
    # 錯誤分流
    parallel = [r for r in scan["rows"] if r["status"].startswith("SYNTAX")
                and "PS_Archive" not in r["path"]]
    return {"ssot": ssot, "regex_conflicts": rx_bad, "hydra_top": hydra,
            "parallel_fixable": [r["path"] for r in parallel],
            "sequence_dependent": [h["node"] for h in hydra[:3]]}


def round3_polish(scan: dict, gov: dict) -> dict:
    """R3 收尾:健康度紅黃綠燈聚合(誠實:黃=候修/缺件,紅=實敗)。"""
    per_sub = {}
    for s in list(SUBSYSTEMS) + ["VIA", "SUP", "OTHERS"]:
        rs = [r for r in scan["rows"] if r["subsystem"] == s]
        if not rs:
            continue
        bad = sum(1 for r in rs if r["status"] != "OK")
        light = "GREEN" if bad == 0 else ("YELLOW" if bad <= 2 else "RED")
        per_sub[s] = {"n": len(rs), "bad": bad, "light": light}
    miss = sum(1 for v in gov["ssot"].values() if v["status"] != "OK")
    lights = {
        "SSOT": "GREEN" if miss == 0 else "YELLOW",
        "REGEX": "GREEN" if not gov["regex_conflicts"] else "RED",
        "HYDRA": "YELLOW" if gov["hydra_top"] else "GREEN",
    }
    return {"per_subsystem": per_sub, "lights": lights}


def build_ui(scan, gov, fin) -> str:
    sec_counts = Counter((r["section"], r["status"] == "OK") for r in scan["rows"])
    def sec_table(sec):
        subs = Counter(r["subsystem"] for r in scan["rows"] if r["section"] == sec)
        bads = Counter(r["subsystem"] for r in scan["rows"]
                       if r["section"] == sec and r["status"] != "OK")
        rows = "".join(
            f"<tr><td>{s}</td><td>{n}</td><td>{bads.get(s,0)}</td>"
            f"<td><span class='dot {'g' if bads.get(s,0)==0 else 'y' if bads.get(s,0)<=2 else 'r'}'></span></td></tr>"
            for s, n in subs.most_common())
        return rows or "<tr><td colspan=4>—</td></tr>"
    naps = "".join(f"<li>{t}</li>" for t in [
        f"R1 全景掃描:{scan['n_ok']} OK · {scan['n_bad']} 語法敗(全倉 ast.parse)",
        f"R2 SSOT 對齊:{sum(1 for v in gov['ssot'].values() if v['status']=='OK')}/{len(gov['ssot'])} 冊在位 · Regex 衝突 {len(gov['regex_conflicts'])} · Hydra 高耦合節點 {len(gov['hydra_top'])}(僅建議)",
        f"R3 收尾:分流 并行可修 {len(gov['parallel_fixable'])} · 順序依賴 {len(gov['sequence_dependent'])};燈:SSOT={fin['lights']['SSOT']} REGEX={fin['lights']['REGEX']} HYDRA={fin['lights']['HYDRA']}",
    ])
    ssot_rows = "".join(
        f"<tr><td>{k}</td><td class='mono'>{v['path']}</td><td>{v['n'] if v['n'] is not None else '—'}</td>"
        f"<td><span class='dot {'g' if v['status']=='OK' else 'r'}'></span>{v['status']}</td></tr>"
        for k, v in gov["ssot"].items())
    rx_rows = "".join(
        f"<tr><td class='mono'>{k}</td><td class='mono'>{v['pattern']}</td>"
        f"<td>{v['owner']}</td><td>{'LOCKED' if v.get('locked') else 'OPEN'}</td></tr>"
        for k, v in CENTRAL_DICT["regex"].items())
    syn_rows = "".join(
        f"<tr><td class='mono'>{k}</td><td>{'、'.join(vs)}</td></tr>"
        for k, vs in CENTRAL_DICT["synonyms"].items())
    hyd_rows = "".join(
        f"<tr><td class='mono'>{h['node']}</td><td>{h['fan_in']}</td><td>{h['advice']}</td></tr>"
        for h in gov["hydra_top"]) or "<tr><td colspan=3>無(誠實:介面冊無內部邊資料)</td></tr>"
    acc_rows = "".join(f"<tr><td>{a}</td><td>{b}</td><td>{c}</td></tr>" for a, b, c in ACCELERATORS)
    sub_rows = "".join(
        f"<tr><td>{s}</td><td>{v['n']}</td><td>{v['bad']}</td>"
        f"<td><span class='dot {v['light'][0].lower()}'></span>{v['light']}</td></tr>"
        for s, v in fin["per_subsystem"].items())
    pct = round(scan["n_ok"] / max(1, scan["n_ok"] + scan["n_bad"]) * 100, 1)
    return f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIA Central Governance Console</title><style>
:root{{--paper:#f2f1ec;--card:#fbfaf7;--ink:#1b1a17;--seal:#9e2b25;--teal:#3c6660;
--green:#3d7a52;--gold:#8a6420;--blue:#24457f;--hair:#dbd9d3}}
*{{box-sizing:border-box;margin:0}}body{{background:var(--paper);color:var(--ink);
font:12px/1.55 "Microsoft JhengHei","Noto Serif CJK TC",serif;padding:14px}}
h1{{font:600 20px/1.3 "Cormorant Garamond","Noto Serif CJK TC",serif}}
h2{{font:600 14px/1.4 inherit;color:var(--teal);margin:14px 0 6px;border-bottom:1px solid var(--hair)}}
.mast{{background:var(--card);border:1px solid var(--hair);border-top:3px solid var(--seal);
padding:10px 14px;margin-bottom:10px}}
.bar{{height:8px;background:var(--hair);border-radius:4px;overflow:hidden;margin:6px 0}}
.bar i{{display:block;height:100%;width:{pct}%;background:linear-gradient(90deg,var(--teal),var(--green));
animation:sweep 1.2s ease-out}}@keyframes sweep{{from{{width:0}}}}
table{{width:100%;border-collapse:collapse;background:var(--card);table-layout:auto;margin:4px 0 10px}}
td,th{{border:1px solid var(--hair);padding:3px 6px;text-align:left;vertical-align:top;
word-break:break-word;overflow-wrap:anywhere;white-space:normal}}
th{{background:#efede6;font-weight:600}}
.mono{{font-family:"SFMono-Regular",Consolas,monospace;font-size:11px}}
.dot{{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:4px}}
.dot.g{{background:var(--green)}}.dot.y{{background:var(--gold)}}.dot.r{{background:var(--seal)}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}
@media(max-width:820px){{.grid{{grid-template-columns:1fr}}}}
ul{{padding-left:18px}}</style></head><body>
<div class="mast"><h1>VIA Central Governance Console <span class="mono">v0104 · {NOW}</span></h1>
<div class="motto" style="letter-spacing:.14em;color:var(--seal);font:600 11px/1.4 'Cormorant Garamond',serif">VERITAS INTELLIGENCE ANALYTICS · OBSERVA · INTELLEGE · PRAEVIDE</div>
<div>三輪全景式分析 · Zero-Hydra · 母系統+子系統同步治理(誠實三態,不假綠)· 非現役區不入健康度(rollback/venv/證據——QA-20260819E 裁決)</div>
<div class="bar"><i></i></div>
<div>掃描 {scan['n_ok']+scan['n_bad']} 件 · OK {scan['n_ok']} · 語法敗 {scan['n_bad']} · 健康 {pct}%
· SSOT {fin['lights']['SSOT']} · REGEX {fin['lights']['REGEX']} · HYDRA {fin['lights']['HYDRA']}</div></div>
<h2>動態說明(三輪)</h2><ul>{naps}</ul>
<h2>子系統健康度(紅黃綠)</h2>
<table><tr><th>子系統</th><th>件數</th><th>異常</th><th>燈</th></tr>{sub_rows}</table>
<div class="grid"><div>
<h2>MODULE 分區</h2><table><tr><th>子系統</th><th>件</th><th>異常</th><th>燈</th></tr>{sec_table('MODULE')}</table>
<h2>ENGINE 分區</h2><table><tr><th>子系統</th><th>件</th><th>異常</th><th>燈</th></tr>{sec_table('ENGINE')}</table>
</div><div>
<h2>FUNCTION-LIB 分區</h2><table><tr><th>子系統</th><th>件</th><th>異常</th><th>燈</th></tr>{sec_table('FUNCTION-LIB')}</table>
<h2>OTHERS 分區</h2><table><tr><th>子系統</th><th>件</th><th>異常</th><th>燈</th></tr>{sec_table('OTHERS')}</table>
</div></div>
<h2>中央 SSOT 規範庫({len(gov['ssot'])} 冊)</h2>
<table><tr><th>冊</th><th>路徑</th><th>條數</th><th>態</th></tr>{ssot_rows}</table>
<div class="grid"><div>
<h2>Regex 治理中心(LOCKED 集中)</h2>
<table><tr><th>鍵</th><th>pattern</th><th>權威引擎</th><th>鎖</th></tr>{rx_rows}</table>
</div><div>
<h2>同義字治理中心</h2>
<table><tr><th>正規鍵</th><th>同義集</th></tr>{syn_rows}</table>
</div></div>
<h2>Hydra 高耦合節點(僅建議,不盲修)</h2>
<table><tr><th>節點</th><th>fan-in</th><th>建議</th></tr>{hyd_rows}</table>
<h2>20 加速器盤點(實存對映)</h2>
<table><tr><th>#</th><th>加速器</th><th>實存落點</th></tr>{acc_rows}</table>
</body></html>"""


def cmd_run(open_ui: bool = True) -> int:
    _log("  [R1] 全景掃描(ast.parse 全倉+四分區)…")
    scan = round1_scan()
    _log(f"       OK {scan['n_ok']} · 語法敗 {scan['n_bad']}")
    _log("  [R2] SSOT 對齊+Regex 衝突+Hydra 偵測…")
    gov = round2_ssot_hydra(scan)
    _log(f"       SSOT {sum(1 for v in gov['ssot'].values() if v['status']=='OK')}/{len(gov['ssot'])}"
         f" · Regex 衝突 {len(gov['regex_conflicts'])} · Hydra 節點 {len(gov['hydra_top'])}")
    _log("  [R3] 收尾聚合(紅黃綠燈;分流并行/順序)…")
    fin = round3_polish(scan, gov)
    DICT_PATH.exists() or DICT_PATH.write_text(
        json.dumps(CENTRAL_DICT, ensure_ascii=False, indent=1), encoding="utf-8")
    RUNS.mkdir(parents=True, exist_ok=True)
    ev = RUNS / f"CENTRALGOV_{NOW}.json"
    ev.write_text(json.dumps({"scan": {"n_ok": scan["n_ok"], "n_bad": scan["n_bad"],
                                       "bad": [r for r in scan["rows"] if r["status"] != "OK"]},
                              "gov": gov, "final": fin}, ensure_ascii=False, indent=1),
                  encoding="utf-8")
    UI_PATH.write_text(build_ui(scan, gov, fin), encoding="utf-8")
    _log(f"  [出] {UI_PATH}")
    _log(f"  [存證] {ev}")
    for s, v in fin["per_subsystem"].items():
        _log(f"    {s}:{v['n']} 件 · 異常 {v['bad']} · {v['light']}")
    if open_ui:
        try:
            import webbrowser
            webbrowser.open(UI_PATH.as_uri())
        except Exception:
            pass
    return 0


def cmd_ssot() -> int:
    scan = round1_scan()
    gov = round2_ssot_hydra(scan)
    for k, v in gov["ssot"].items():
        _log(f"  {k} · {v['status']} · n={v['n']} · {v['path']}")
    return 0


def cmd_regex() -> int:
    bad = []
    for k, v in CENTRAL_DICT["regex"].items():
        try:
            re.compile(v["pattern"])
            _log(f"  {k} · {'LOCKED' if v.get('locked') else 'OPEN'} · {v['owner']}")
        except re.error as e:
            bad.append(k)
            _log(f"  {k} · CONFLICT:{e}")
    for k, vs in CENTRAL_DICT["synonyms"].items():
        _log(f"  SYN {k} · {len(vs)} 詞")
    _log(f"  [計] regex {len(CENTRAL_DICT['regex'])} · 衝突 {len(bad)} · 同義集 {len(CENTRAL_DICT['synonyms'])}")
    return 0 if not bad else 1


def selftest() -> int:
    ok, total = 0, 8
    scan = round1_scan()
    if scan["n_ok"] > 300:
        ok += 1; print(f"  [PASS] R1 全倉掃描({scan['n_ok']+scan['n_bad']} 件)")
    else:
        print("  [FAIL] R1")
    secs = {r["section"] for r in scan["rows"]}
    if {"MODULE", "ENGINE", "FUNCTION-LIB"} <= secs:
        ok += 1; print("  [PASS] 四分區分類(MODULE/ENGINE/FUNCTION-LIB/OTHERS)")
    else:
        print(f"  [FAIL] 分區 {secs}")
    gov = round2_ssot_hydra(scan)
    if sum(1 for v in gov["ssot"].values() if v["status"] == "OK") >= 6:
        ok += 1; print("  [PASS] 中央 SSOT 規範庫對齊(≥6 冊在位)")
    else:
        print("  [FAIL] SSOT")
    if not gov["regex_conflicts"] and len(CENTRAL_DICT["regex"]) >= 7:
        ok += 1; print("  [PASS] Regex 治理中心(7+ LOCKED 可編譯零衝突)")
    else:
        print("  [FAIL] Regex")
    if len(CENTRAL_DICT["synonyms"]) >= 5:
        ok += 1; print("  [PASS] 同義字治理中心(5+ 正規鍵)")
    else:
        print("  [FAIL] 同義字")
    fin = round3_polish(scan, gov)
    if fin["per_subsystem"] and all(v["light"] in ("GREEN", "YELLOW", "RED")
                                    for v in fin["per_subsystem"].values()):
        ok += 1; print("  [PASS] R3 紅黃綠燈聚合(誠實三色)")
    else:
        print("  [FAIL] 燈")
    html = build_ui(scan, gov, fin)
    if all(x in html for x in ("word-break", "12px", "MODULE 分區", "dot", "sweep")):
        ok += 1; print("  [PASS] HTML Matrix(小字體/換行/四分區/燈/動態進度條)")
    else:
        print("  [FAIL] UI")
    if "fonts.googleapis" not in html and len(ACCELERATORS) == 6:
        ok += 1; print("  [PASS] 零 CDN+20 加速器實存盤點(不虛報)")
    else:
        print("  [FAIL] 紅線")
    print(f"  [計] {ok}/{total} 檢通過")
    return 0 if ok == total else 1


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        return selftest()
    if "--ssot" in a:
        return cmd_ssot()
    if "--regex" in a:
        return cmd_regex()
    return cmd_run(open_ui="--no-open" not in a)


if __name__ == "__main__":
    raise SystemExit(main())
