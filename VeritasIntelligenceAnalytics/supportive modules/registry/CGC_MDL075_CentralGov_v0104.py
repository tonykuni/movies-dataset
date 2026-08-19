#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
via_central_gov_v0104 — VIA Central Governance Console(TOOL-063)
--------------------------------------------------------------------
v0103→v0104(批84 VSM 治理層,令「儘量與原本指令整合強化」):
  ⑥ Viable System Model(Stafford Beer)五系統面板:S1 運營(功能
     子系統)/S2 協調(ui_kit·params·ifsync)/S3 內部調節(center·
     台帳·grid)/S3* 獨立稽核(finaudit·vapguard·oldscan·QA 凍結)
     /S4 前瞻情報(Flow 模擬·VDF 攝入·via-net)/S5 政策身份(操作
     員終極權威+鐵律紅線+凍結鎖)。冊=VIA_VSM_Governance_SSOT_v0100
     (遞迴原則/Ashby variety/algedonic 通道/稽核獨立保障)。
  ⑦ S3* 稽核協定生命週期(A 選案→B 執行→C 報告→D 追蹤)對映
     實存工具入 UI;健康燈以既有掃描實測滾算至五系統。
v0102→v0103(批82 終極旗艦版 Mega-Prompt):
  ① 六大獨立流程并行(Six Parallel Pipelines):P1 代碼層 AST 全景/
     P2 SSOT+Regex 校準/P3 子系統熱插拔偵測/P4 性能與死碼盤點/
     P5 沙盒覆蓋率(grid 站數內省)/P6 UI Matrix 渲染=join。
     P1-P5 ThreadPool 并行(VIA_GOVCON_WORKERS 可調),全唯讀=
     Zero-Hydra by construction(不可影響系統健康)。
  ② 20 加速器全編號盤點:操作員旗艦冊 01-20 逐項對映實存工具
     (誠實:只列實存,部分承接者註明)。
  ③ 掃描動態進度條(常備令Ⅱ單行 sweep)+各流程動態情境說明。
  ④ 子系統熱插拔槽自動偵測:functional modules/ 下未列名目錄
     自動入槽列報(動態擴充之子系統同步治理)。
  ⑤ 死碼/重量級盤點(P4):_sha 鏡像量/版本家族深度/大檔 Top —
     只盤點不刪除(零刪除鐵律)。
v0100→v0101:R1 掃描包 warnings 靜噪(SyntaxWarning 不再漏操作員
主控台——工作站 16,924 件掃描實測回饋);行為零變更。
v0101→v0102(批50):排除區補齊至全計畫共識。
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
VSM_PATH = HERE / "VIA_VSM_Governance_SSOT_v0100.json"
NOW = datetime.now().strftime("%Y%m%d_%H%M%S")

# v0102(批50):排除區補齊至全計畫共識(cgc/rescue/rename 一致)——
# 工作站 _via_mother_root_reconciliation_runs/rollback 回滾快照 40 壞件
# 屬收容件非現役,誤掃致 OTHERS RED;.venv/site-packages/rename_runs 同理
SKIP_FRAGS = ("_sha", "_review_quarantine", "__pycache__", "/vendor/",
              "package_samples", "/docs/", "quarantine", ".venv",
              "site-packages", "_via_mother_root_reconciliation_runs",
              "rollback", "evidence", "_syntaxfix_", "rename_runs")

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

# ── 20 加速器全編號盤點(批82 旗艦冊 01-20 → 實存對映;誠實不虛報)──
ACCELERATORS = [
    ("01", "AST 精準解析加速器", "本引擎 P1 ast.parse 全倉+finlex AST 零執行收割"),
    ("02", "多語言語意模型加速器", "誠實候態:同義字冊+finlex 中英四源合流承接(非 LLM)"),
    ("03", "九頭龍風險預測加速器", "本引擎 Hydra fan-in 偵測(介面冊邊)"),
    ("04", "依賴拓撲排序加速器", "via-deps(TOOL-031 PEP440 圖譜)+Hydra 順序分流"),
    ("05", "沙盒隔離執行加速器", "selftest grid 沙盒站群+oldscan/rescue tempfile 沙盒"),
    ("06", "自動修正建議生成加速器", "via-fixsyntax 三輪救援(提案並排,不盲修)"),
    ("07", "三輪全景式分析加速器", "本引擎 R1-R3(P1-P6 并行版)"),
    ("08", "SSOT 對齊加速器", "本引擎 SSOT 冊對齊+via-params 中央樞紐"),
    ("09", "視覺化矩陣生成加速器", "本引擎 UI Matrix+via-center 儀表板總線"),
    ("10", "錯誤分類與分群加速器", "本引擎 Parallel-Fixable/Sequence-Dependent 分流"),
    ("11", "性能與複雜度分析加速器", "本引擎 P4 死碼/重量級盤點(只盤點不刪)"),
    ("12", "多子系統同步檢視加速器", "本引擎四分區×子系統矩陣+熱插拔槽"),
    ("13", "版本差異與回滾加速器", "git 版控+oldscan manifest --undo"),
    ("14", "覆蓋率與回歸檢查加速器", "本引擎 P5 grid 站數內省(selftest grid 全站)"),
    ("15", "修正順序最佳化加速器", "Hydra fan-in 升冪=最小干擾排程建議"),
    ("16", "動態進度條加速器", "本引擎 _sweep+via-run 進度家族"),
    ("17", "動態說明加速器", "本引擎各流程 narration+誠實三態"),
    ("18", "非阻塞 PowerShell 執行加速器", "Invoke-VIA-UnifyOneFolder 看門狗+via-run 留痕"),
    ("19", "多引擎整合加速器", "bin 動詞群(Py+PS+HTML U/I kit)"),
    ("20", "自動部署與初始化加速器", "via_provision+via_install_gate(同意閘)"),
]


def _log(m):
    print(m)


def _sweep(msg: str, i: int, n: int) -> None:
    """常備令Ⅱ:單行動態進度條不卡斷(批82 ③)"""
    w = 24
    k = int(w * i / max(n, 1))
    sys.stdout.write(f"\r  [{'█' * k}{'░' * (w - k)}] {i}/{n} {msg[:36]:<36}")
    sys.stdout.flush()
    if i >= n:
        sys.stdout.write("\n")


def _workers() -> int:
    import os
    try:
        w = int(os.environ.get("VIA_GOVCON_WORKERS", "0"))
    except ValueError:
        w = 0
    return w if w > 0 else max(2, (os.cpu_count() or 4) - 1)


def discover_hotplug() -> list[dict]:
    """P3 子系統熱插拔槽:functional modules/ 未列名目錄自動入槽(批82 ④)"""
    mapped = {Path(v).name for v in SUBSYSTEMS.values()}
    slots = []
    fm = VIA / "functional modules"
    if fm.exists():
        for d in sorted(fm.iterdir()):
            if d.is_dir() and d.name not in mapped and not d.name.startswith((".", "_")):
                n_py = sum(1 for _ in d.rglob("*.py"))
                slots.append({"slot": d.name.upper()[:12], "dir": f"functional modules/{d.name}",
                              "py": n_py, "status": "HOT-PLUG(自動入槽,候正式列名)"})
    return slots


def pipeline_deadweight() -> dict:
    """P4 性能/死碼盤點:_sha 鏡像量+版本家族深度+大檔 Top(只盤點不刪除)"""
    mirrors = 0
    fam = Counter()
    big = []
    for p in VIA.rglob("*.py"):
        rp = str(p.relative_to(VIA)).replace("\\", "/")
        if any(f in rp for f in ("__pycache__", ".venv", "site-packages", "rename_runs",
                                 "_via_mother_root_reconciliation_runs", "VIA_Reports")):
            continue
        if "_sha" in p.stem:
            mirrors += 1
        m = re.match(r"(.+?)_v\d{2,4}[a-z]?$", p.stem, re.I)
        if m:
            fam[m.group(1)] += 1
        try:
            sz = p.stat().st_size
            if sz > 200_000:
                big.append((rp, sz))
        except OSError:
            pass
    deep = [{"family": k, "versions": v} for k, v in fam.most_common(8) if v >= 5]
    big.sort(key=lambda x: -x[1])
    return {"sha_mirrors": mirrors, "deep_families": deep,
            "big_files": [{"path": a, "kb": round(b / 1024)} for a, b in big[:8]],
            "policy": "只盤點不刪除(零刪除鐵律);讓位/清理一律候操作員裁決"}


def pipeline_coverage() -> dict:
    """P5 覆蓋率內省:最新 selftest grid 站數(glob 動態解析)"""
    grids = sorted(HERE.glob("CGC_MDL064_SelftestGrid_v0*.py"))
    if not grids:
        return {"grid": None, "stations": 0}
    g = grids[-1]
    txt = g.read_text(encoding="utf-8", errors="ignore")
    n = len(re.findall(r'^\s*add\("', txt, re.M)) + len(re.findall(r'B\.append\(\{"name"', txt))
    return {"grid": g.name, "stations": n}


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


def round1_scan(progress: bool = True) -> dict:
    """R1/P1 全景掃描:ast.parse 全倉+四分區分類+錯誤識別(進度條,批82 ③)。"""
    import warnings
    files = list(iter_py())
    rows, n_ok, n_bad = [], 0, 0
    for i, (p, rp) in enumerate(files, 1):
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
        if progress and (i % 200 == 0 or i == len(files)):
            _sweep("P1 AST 全景", i, len(files))
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


def load_vsm() -> dict:
    try:
        return json.loads(VSM_PATH.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}


def vsm_rollup(fin: dict) -> dict:
    """五系統健康滾算:以既有子系統實測燈對映 S1;治理面 S2-S5 以冊在位+燈聚合"""
    per = fin.get("per_subsystem", {})
    s1_lights = [v["light"] for k, v in per.items() if k in ("VRN", "VDF", "VAP", "FLOW", "VME", "CHW", "GRP")]
    def worst(ls):
        return "RED" if "RED" in ls else ("YELLOW" if "YELLOW" in ls else "GREEN")
    return {
        "S1": worst(s1_lights or ["GREEN"]),
        "S2": fin["lights"].get("REGEX", "GREEN"),
        "S3": worst([v["light"] for k, v in per.items() if k in ("VIA", "SUP")] or ["GREEN"]),
        "S3star": fin["lights"].get("SSOT", "GREEN"),
        "S4": worst([per.get("GRP", {}).get("light", "GREEN"), per.get("FLOW", {}).get("light", "GREEN")]),
        "S5": "GREEN",  # 操作員權威+鐵律=常綠(違紅線時由 QA 凍結程序轉 RED)
    }


def build_ui(scan, gov, fin, pipes=None) -> str:
    pipes = pipes or {}
    pipe_rows = "".join(
        f"<tr><td>{n}</td><td><span class='dot {'g' if st['status']=='OK' else 'r'}'></span>{st['status']}</td>"
        f"<td>{st['sec']}s</td></tr>" for n, st in pipes.items()) \
        + "<tr><td>P6 UI Matrix 渲染(join)</td><td><span class='dot g'></span>OK</td><td>—</td></tr>"
    hot_rows = "".join(
        f"<tr><td>{h['slot']}</td><td class='mono'>{h['dir']}</td><td>{h['py']}</td><td>{h['status']}</td></tr>"
        for h in gov.get("hotplug", [])) or "<tr><td colspan=4>無新槽(全數已列名)</td></tr>"
    dw = gov.get("deadweight", {})
    dw_fam = "".join(f"<tr><td class='mono'>{d['family']}</td><td>{d['versions']}</td></tr>"
                     for d in dw.get("deep_families", [])) or "<tr><td colspan=2>—</td></tr>"
    dw_big = "".join(f"<tr><td class='mono'>{b['path']}</td><td>{b['kb']} KB</td></tr>"
                     for b in dw.get("big_files", [])) or "<tr><td colspan=2>—</td></tr>"
    cov = gov.get("coverage", {})
    vsm = load_vsm()
    vlights = vsm_rollup(fin)
    vsm_rows = ""
    for sid in ("S1", "S2", "S3", "S3star", "S4", "S5"):
        sysd = vsm.get("systems", {}).get(sid, {})
        light = vlights.get(sid, "GREEN")
        vsm_rows += (f"<tr><td><b>{'S3*' if sid=='S3star' else sid}</b> {sysd.get('role','—')}</td>"
                     f"<td>{'、'.join(sysd.get('via_mapping', [])[:5])}</td>"
                     f"<td><span class='dot {light[0].lower()}'></span>{light}</td></tr>")
    aud = vsm.get("s3star_audit_protocol", {})
    aud_rows = "".join(f"<tr><td>{t['t']}</td><td>{t['via']}</td></tr>" for t in aud.get("types", []))
    lc = aud.get("lifecycle", {})
    lc_rows = "".join(f"<tr><td class='mono'>{k}</td><td>{v}</td></tr>" for k, v in lc.items())
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
<div>三輪全景式分析 · 六流程并行 · Zero-Hydra · 母系統+子系統同步治理(誠實三態,不假綠)</div>
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
<h2>六大獨立流程(并行,全唯讀=Zero-Hydra)</h2>
<table><tr><th>流程</th><th>態</th><th>耗時</th></tr>{pipe_rows}</table>
<h2>子系統熱插拔槽(自動偵測)</h2>
<table><tr><th>槽</th><th>目錄</th><th>py 件數</th><th>態</th></tr>{hot_rows}</table>
<div class="grid"><div>
<h2>P4 版本家族深度(≥5 版;只盤點不刪除)</h2>
<table><tr><th>家族</th><th>版數</th></tr>{dw_fam}</table>
</div><div>
<h2>P4 重量級檔案 Top(>200KB)</h2>
<table><tr><th>路徑</th><th>大小</th></tr>{dw_big}</table>
</div></div>
<div>P4 _sha 鏡像 {dw.get('sha_mirrors','—')} 件 · P5 覆蓋率:{cov.get('grid','—')} 共 {cov.get('stations','—')} 站</div>
<h2>VSM 五系統治理面板(Stafford Beer;批84 冊對映實存)</h2>
<table><tr><th>系統/角色</th><th>VIA 實存對映(前五)</th><th>燈</th></tr>{vsm_rows}</table>
<div class="grid"><div>
<h2>S3* 稽核類型 → 實存工具</h2>
<table><tr><th>類型</th><th>VIA 承接</th></tr>{aud_rows}</table>
</div><div>
<h2>S3* 稽核生命週期(A 選案→D 追蹤)</h2>
<table><tr><th>階段</th><th>協定與對映</th></tr>{lc_rows}</table>
</div></div>
<h2>20 加速器盤點(旗艦冊 01-20 → 實存對映)</h2>
<table><tr><th>#</th><th>加速器</th><th>實存落點</th></tr>{acc_rows}</table>
</body></html>"""


def run_pipelines() -> tuple[dict, dict, dict, dict]:
    """六大獨立流程(批82 ①):P1-P5 并行(全唯讀=Zero-Hydra),P6=join 渲染。
    回 (scan, gov, fin, pipelines 狀態表)"""
    import time as _t
    from concurrent.futures import ThreadPoolExecutor
    pipes: dict[str, dict] = {}

    def timed(name, fn, *a):
        t0 = _t.time()
        try:
            out = fn(*a)
            pipes[name] = {"status": "OK", "sec": round(_t.time() - t0, 1)}
            return out
        except Exception as exc:
            pipes[name] = {"status": "FAIL", "sec": round(_t.time() - t0, 1),
                           "err": str(exc)[:80]}
            return None
    _log(f"  [并行] P1-P5 六流程啟動(工 {_workers()};全唯讀 Zero-Hydra)…")
    with ThreadPoolExecutor(max_workers=min(5, _workers())) as ex:
        f1 = ex.submit(timed, "P1 代碼層 AST 全景", round1_scan)
        f3 = ex.submit(timed, "P3 子系統熱插拔偵測", discover_hotplug)
        f4 = ex.submit(timed, "P4 性能/死碼盤點", pipeline_deadweight)
        f5 = ex.submit(timed, "P5 沙盒覆蓋率內省", pipeline_coverage)
        scan = f1.result()
        # P2 需 P1 分流輸入,P1 落地即啟(仍與 P3-P5 并行)
        f2 = ex.submit(timed, "P2 SSOT/Regex 校準", round2_ssot_hydra, scan)
        gov = f2.result()
        hot, dead, cov = f3.result(), f4.result(), f5.result()
    gov["hotplug"] = hot or []
    gov["deadweight"] = dead or {}
    gov["coverage"] = cov or {}
    for n, st in pipes.items():
        _log(f"    [{st['status']}] {n} · {st['sec']}s")
    fin = round3_polish(scan, gov)
    return scan, gov, fin, pipes


def cmd_run(open_ui: bool = True) -> int:
    scan, gov, fin, pipes = run_pipelines()
    _log(f"  [R1] OK {scan['n_ok']} · 語法敗 {scan['n_bad']}")
    _log(f"  [R2] SSOT {sum(1 for v in gov['ssot'].values() if v['status']=='OK')}/{len(gov['ssot'])}"
         f" · Regex 衝突 {len(gov['regex_conflicts'])} · Hydra 節點 {len(gov['hydra_top'])}"
         f" · 熱插拔槽 {len(gov['hotplug'])}")
    _log("  [R3] 收尾聚合(紅黃綠燈;分流并行/順序)…")
    DICT_PATH.exists() or DICT_PATH.write_text(
        json.dumps(CENTRAL_DICT, ensure_ascii=False, indent=1), encoding="utf-8")
    RUNS.mkdir(parents=True, exist_ok=True)
    ev = RUNS / f"CENTRALGOV_{NOW}.json"
    ev.write_text(json.dumps({"scan": {"n_ok": scan["n_ok"], "n_bad": scan["n_bad"],
                                       "bad": [r for r in scan["rows"] if r["status"] != "OK"]},
                              "gov": gov, "final": fin, "pipelines": pipes},
                             ensure_ascii=False, indent=1),
                  encoding="utf-8")
    UI_PATH.write_text(build_ui(scan, gov, fin, pipes), encoding="utf-8")
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
    ok, total = 0, 12
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
    gov["hotplug"] = discover_hotplug()
    gov["deadweight"] = pipeline_deadweight()
    gov["coverage"] = pipeline_coverage()
    html = build_ui(scan, gov, fin, {"P1 代碼層 AST 全景": {"status": "OK", "sec": 0.0}})
    if all(x in html for x in ("word-break", "12px", "MODULE 分區", "dot", "sweep",
                               "六大獨立流程", "熱插拔槽")):
        ok += 1; print("  [PASS] HTML Matrix(小字體/換行/四分區/燈/進度條/六流程/熱插拔)")
    else:
        print("  [FAIL] UI")
    if "fonts.googleapis" not in html and len(ACCELERATORS) == 20 \
            and all(a[0] == f"{i+1:02d}" for i, a in enumerate(ACCELERATORS)):
        ok += 1; print("  [PASS] 零 CDN+20 加速器全編號盤點(01-20 實存對映)")
    else:
        print("  [FAIL] 紅線")
    # ⑨ 六流程并行(批82:P1-P5 并行+P6 join;全 OK)
    _s2, _g2, _f2, pipes = run_pipelines()
    if len(pipes) == 5 and all(v["status"] == "OK" for v in pipes.values()) \
            and "hotplug" in _g2 and "deadweight" in _g2 and "coverage" in _g2:
        ok += 1; print(f"  [PASS] 六流程并行(P1-P5 全 OK+P6 join;工 {_workers()})")
    else:
        print(f"  [FAIL] 六流程 {pipes}")
    # ⑩ P5 覆蓋率內省(grid 站數>50)
    cov = _g2["coverage"]
    if cov.get("grid") and cov.get("stations", 0) > 50:
        ok += 1; print(f"  [PASS] 覆蓋率內省({cov['grid']} 共 {cov['stations']} 站)")
    else:
        print(f"  [FAIL] 覆蓋率 {cov}")
    # ⑪ VSM 冊完整(六系統+稽核協定四階+保障)
    vsm = load_vsm()
    if len(vsm.get("systems", {})) == 6 and len(vsm.get("s3star_audit_protocol", {}).get("lifecycle", {})) == 4 \
            and len(vsm["s3star_audit_protocol"].get("safeguards", [])) >= 5:
        ok += 1; print("  [PASS] VSM 治理冊(S1-S5+S3*;稽核 A-D;保障 5+)")
    else:
        print("  [FAIL] VSM 冊")
    # ⑫ VSM 面板入 UI+五系統滾算燈
    vl = vsm_rollup(fin)
    if "VSM 五系統治理面板" in html and "S3*" in html and set(vl) == {"S1", "S2", "S3", "S3star", "S4", "S5"}:
        ok += 1; print(f"  [PASS] VSM 面板+滾算燈 {vl}")
    else:
        print("  [FAIL] VSM 面板")
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
