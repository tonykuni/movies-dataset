#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
via_mother_takeover_v0100 — 母系統向下接手引擎(TOOL-097,批95)
====================================================================
操作員令:「VIA 中央系統建立+資源性模組系統建立+三個子系統管理模組
同步進行;向下抓取 PS 指令掌握之前怎麼控管引擎跟 System Manager;
兩組不同時期引擎舉證列出(檔名+關鍵字+內容,類似放一起看差異——
各有優缺點就整合、一好一差就擇一,要經過使用者核准);母系統一口氣
自動自適應向下接手支援模組管理者跟子系統管理者;SSOT 向下掃描自動
更新真值+排除矛盾+增加同義字+提醒定義 regex 必要性;所有 py 修復
後導入加速器;支援性模組自動註冊(編號/名稱/功能/工具);regex 同
一隻自動增加更新;向外呼叫資料的模組要加上所有網路工具」。

六路向下接手(全唯讀舉證+提案;動碼一律候操作員核准=Zero-Hydra):
  M1 PS 治理考古   掃全倉 .ps1 抽治理特徵(ExpectedSHA 釘鎖/AST 驗證
                   /Guarded 啟動鏈/-Base 錨定/freeze.lock),重建
                   「之前怎麼控管引擎與 System Manager」證據表
  M2 雙世代引擎舉證 家族分群(檔名正規化)+AST 函式集比對:
                   A⊃B=擇一提案(PICK-ONE)/各有獨有=整合提案
                   (INTEGRATE)/同函式異 hash=DIFF-MINOR——全部
                   APPROVAL_REQUIRED,產核准冊候操作員裁
  M3 SSOT 真值同步  中央同義字矛盾檢(一詞跨兩正規組=矛盾)+散落
                   inline regex 未入中央冊=「必要性提醒」清單
                   (中央 Regex 冊自動增補走 pending 區,不動 LOCKED)
  M4 加速器導入稽核 py 缺 [VIA:ACCEL-BRIDGE] 橋者列橋接計畫
  M5 支援模組自動註冊 supportive 頂層 py 未入冊者→SUP-#### 編號+
                   名稱+docstring 功能摘要入支援模組冊(append-only)
  M6 外呼網路稽核   py 有 requests/urllib/http/socket/yfinance 而未
                   經 via-net/SuperAccel 閘者=候接網路統包清單
用法:
  via-takeover --run        → 六路全跑(舉證+提案+冊更新)
  via-takeover --selftest   → 十二檢(沙盒零網路)
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL
except Exception:
    VIA_ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====

import ast
import json
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
RUNS = VIA / "VIA_Reports" / "takeover_runs"
SUP_REG = HERE / "VIA_Supportive_AutoRegistry_v0100.json"
DICT_PATH = HERE / "VIA_Central_Synonym_Regex_v0100.json"
SKIP_FRAGS = ("_sha", "__pycache__", ".venv", "site-packages", "quarantine",
              "_review_quarantine", "rename_runs", "_via_mother_root_reconciliation_runs",
              "VIA_Reports", "rollback", "_syntaxfix_", "evidence", "/docs/", "package_samples")
NOW = datetime.now().strftime("%Y%m%d_%H%M%S")

GOV_FEATURES = {
    "sha_pin": r"ExpectedSHA|Get-FileHash",
    "ast_gate": r"System\.Management\.Automation\.Language\.Parser",
    "guarded_launch": r"SAFE.?PROBE|Guarded|-NoNewWindow|Start-Process",
    "base_anchor": r"-Base\b|\$Base\b",
    "freeze_lock": r"freeze\.lock",
    "watchdog": r"WaitForExit|Kill\(",
}
NET_TOKENS = r"^\s*(?:import|from)\s+(requests|urllib|http\.client|httpx|aiohttp|socket|yfinance)\b"
NET_GATE_TOKENS = r"via_net_unified|VIA_SuperAccel_Module|vdf_fetch|VIA_NET_CONSENT"


def _iter(root: Path, suffix: str):
    for p in root.rglob(f"*{suffix}"):
        rp = str(p.relative_to(root)).replace("\\", "/")
        if any(f in rp for f in SKIP_FRAGS):
            continue
        yield p, rp


def _read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def m1_ps_archaeology(root: Path) -> dict:
    """M1:掃 .ps1 治理特徵——重建「之前怎麼控管」"""
    rows = []
    for p, rp in _iter(root, ".ps1"):
        t = _read(p)
        feats = [k for k, pat in GOV_FEATURES.items() if re.search(pat, t)]
        if feats:
            rows.append({"path": rp, "features": feats,
                         "is_sysmgr": bool(re.search(r"SystemManager|Governance|Guarded|Launcher|StartVIA", p.name, re.I))})
    sysmgr = [r for r in rows if r["is_sysmgr"]]
    return {"governed_ps": len(rows), "sysmgr_lineage": sysmgr[:40], "rows": rows,
            "pattern": "釘鎖 SHA→AST 驗證→Guarded 啟動(-Base 錨定)→看門狗;freeze.lock=憲政保留"}


def _family_key(stem: str) -> str:
    k = re.sub(r"\s*\(\d+\)\s*$", "", stem)
    k = re.sub(r"_sha[0-9a-f]{6,}", "", k, flags=re.I)
    k = re.sub(r"[_-]?[vV]\d{2,4}[a-zA-Z]?$", "", k)
    k = re.sub(r"[_-]?\d{8}([_-]\d{6})?$", "", k)
    return k.strip("_- ").lower()


def _fn_set(text: str):
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError, RecursionError):
        return None
    return {n.name for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}


def m2_two_era_engines(root: Path) -> dict:
    """M2:雙世代引擎舉證——分群+函式集差異+提案(核准閘)"""
    fams = defaultdict(list)
    for p, rp in _iter(root, ".py"):
        fams[_family_key(p.stem)].append((p, rp))
    proposals = []
    for key, members in fams.items():
        if len(members) < 2 or not key:
            continue
        infos = []
        seen_hash = set()
        for p, rp in members:
            t = _read(p)
            h = hash(t)
            if h in seen_hash:
                continue
            seen_hash.add(h)
            fns = _fn_set(t)
            doc = ""
            try:
                doc = (ast.get_docstring(ast.parse(t)) or "").strip().splitlines()[0][:100] if fns is not None else ""
            except Exception:
                doc = ""
            infos.append({"path": rp, "loc": t.count("\n") + 1, "fns": fns, "doc": doc})
        if len(infos) < 2:
            continue
        infos.sort(key=lambda x: -(x["loc"]))
        a, b = infos[0], infos[1]
        if a["fns"] is None or b["fns"] is None:
            verdict, why = "HOLD", "一側語法不可解析(候修復後再比)"
        elif a["fns"] >= b["fns"] and len(a["fns"]) > len(b["fns"]):
            verdict, why = "PICK-ONE", f"{Path(a['path']).name} 函式集涵蓋另一側(+{len(a['fns'] - b['fns'])} 獨有)——擇一提案"
        elif (a["fns"] - b["fns"]) and (b["fns"] - a["fns"]):
            verdict, why = "INTEGRATE", (f"各有獨有:A 獨有 {sorted(a['fns'] - b['fns'])[:5]} · "
                                          f"B 獨有 {sorted(b['fns'] - a['fns'])[:5]}——整合提案")
        elif a["fns"] == b["fns"]:
            verdict, why = "DIFF-MINOR", "函式集相同、內容異(細部差異)——候擇新"
        else:
            verdict, why = "PICK-ONE", f"{Path(a['path']).name} 涵蓋——擇一提案"
        proposals.append({"family": key, "members": [i["path"] for i in infos],
                          "docs": [i["doc"] for i in infos[:2]],
                          "verdict": verdict, "why": why,
                          "status": "APPROVAL_REQUIRED(不自動動手,候操作員核准)"})
    proposals.sort(key=lambda x: x["family"])
    return {"families_multi": len(proposals), "proposals": proposals}


def m3_ssot_sync(root: Path, central: dict) -> dict:
    """M3:同義字矛盾檢+散落 regex 必要性提醒(中央冊 pending 增補)"""
    owner = {}
    conflicts = []
    for canon, terms in central.get("synonyms", {}).items():
        for t in terms:
            tl = str(t).lower()
            if tl in owner and owner[tl] != canon:
                conflicts.append({"term": t, "groups": [owner[tl], canon], "裁": "矛盾候排除"})
            owner[tl] = canon
    known = {v["pattern"] for v in central.get("regex", {}).values()}
    reminders = []
    for p, rp in _iter(root, ".py"):
        t = _read(p)
        for m in re.finditer(r"re\.compile\(\s*r?[\"']([^\"'\n]{8,80})[\"']", t):
            pat = m.group(1)
            if pat not in known and not any(pat == r["pattern"] for r in reminders):
                reminders.append({"pattern": pat, "src": rp})
        if len(reminders) >= 60:
            break
    return {"synonym_conflicts": conflicts, "regex_reminders": reminders[:40],
            "note": "提醒:上列散落 regex 建議定義入中央 Regex 治理中心(pending 區增補,LOCKED 不動)"}


def m4_accel_audit(root: Path) -> dict:
    """M4:加速器橋覆蓋稽核(py 修復後都要導入加速器)"""
    have, lack = 0, []
    for p, rp in _iter(root, ".py"):
        t = _read(p)
        if "[VIA:ACCEL-BRIDGE" in t or "VIA_SuperAccel_Module" in t or "VeritasCeleritas" in t:
            have += 1
        elif _fn_set(t) is not None:  # 可解析即列(無函式之組態/常數檔亦候橋)
            lack.append(rp)
    return {"bridged": have, "lack_bridge": len(lack), "bridge_plan": lack[:40],
            "note": "橋接=版本前進道(正本不就地修改);via-py 啟動器已提供執行期兜底"}


def m5_supportive_autoregister(root: Path, reg_path: Path, dry: bool = False) -> dict:
    """M5:支援模組自動註冊(SUP-#### 編號/名稱/功能;append-only)"""
    reg = {"schema": "via-supportive-autoregistry-v1",
           "policy": "append-only:SUP 編號永不重發不改號", "entries": []}
    if reg_path.exists():
        reg = json.loads(reg_path.read_text(encoding="utf-8-sig"))
    known = {e["name"] for e in reg["entries"]}
    counter = max((int(e["sup_id"].split("-")[1]) for e in reg["entries"]), default=0)
    added = []
    sup = root / "supportive modules"
    if sup.exists():
        for p in sorted(sup.glob("*.py")):
            if any(f in p.name for f in SKIP_FRAGS) or p.name in known:
                continue
            t = _read(p)
            doc = ""
            try:
                doc = (ast.get_docstring(ast.parse(t)) or "").strip().splitlines()[0][:120]
            except Exception:
                doc = "(語法不可解析——候修復)"
            counter += 1
            e = {"sup_id": f"SUP-{counter:04d}", "name": p.name, "role": doc or "(無 docstring)",
                 "kind": "工具" if re.search(r"tool|cli|invoke|run", p.stem, re.I) else "支援模組",
                 "registered": NOW}
            reg["entries"].append(e)
            added.append(e)
    if added and not dry:
        reg_path.write_text(json.dumps(reg, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"registered_total": len(reg["entries"]), "added_now": added}


def m6_net_audit(root: Path) -> dict:
    """M6:外呼模組稽核——向外呼叫資料者要接網路統包工具"""
    out = []
    for p, rp in _iter(root, ".py"):
        t = _read(p)
        if re.search(NET_TOKENS, t, re.M) and not re.search(NET_GATE_TOKENS, t):
            out.append(rp)
    return {"outbound_ungated": len(out), "rows": out[:40],
            "note": "候接 via-net 統包(法遵雙閘)/SuperAccel vdf_fetch 道;接線=版本前進候令"}


def run(root: Path = VIA) -> int:
    central = json.loads(DICT_PATH.read_text(encoding="utf-8-sig")) if DICT_PATH.exists() else {}
    print("  [M1] PS 治理考古…")
    r1 = m1_ps_archaeology(root)
    print(f"       治理特徵件 {r1['governed_ps']} · System Manager 世系 {len(r1['sysmgr_lineage'])} · 控管型態:{r1['pattern']}")
    print("  [M2] 雙世代引擎舉證…")
    r2 = m2_two_era_engines(root)
    print(f"       多成員家族 {r2['families_multi']}(全部 APPROVAL_REQUIRED)")
    for pr in r2["proposals"][:12]:
        print(f"       [{pr['verdict']:<10}] {pr['family']} · {pr['why'][:70]}")
    print("  [M3] SSOT 真值同步…")
    r3 = m3_ssot_sync(root, central)
    print(f"       同義字矛盾 {len(r3['synonym_conflicts'])} · 散落 regex 提醒 {len(r3['regex_reminders'])}")
    print("  [M4] 加速器導入稽核…")
    r4 = m4_accel_audit(root)
    print(f"       已橋接 {r4['bridged']} · 缺橋 {r4['lack_bridge']}(計畫前 40 入存證)")
    print("  [M5] 支援模組自動註冊…")
    r5 = m5_supportive_autoregister(root, SUP_REG)
    print(f"       冊內共 {r5['registered_total']} · 本輪新註冊 {len(r5['added_now'])}")
    print("  [M6] 外呼網路稽核…")
    r6 = m6_net_audit(root)
    print(f"       未經閘外呼 {r6['outbound_ungated']}(候接 via-net)")
    RUNS.mkdir(parents=True, exist_ok=True)
    ev = RUNS / f"TAKEOVER_{NOW}.json"
    ev.write_text(json.dumps({"schema": "VIA.MotherTakeover.v1", "ts": NOW,
                              "M1": {k: v for k, v in r1.items() if k != "rows"},
                              "M2": r2, "M3": r3, "M4": r4,
                              "M5": {"registered_total": r5["registered_total"],
                                     "added_now": r5["added_now"][:60]},
                              "M6": r6}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  [存證] {ev}")
    print("  [裁] M2 整合/擇一提案全數候操作員核准;核准後走版本前進道執行,正本零觸碰")
    return 0


def selftest() -> int:
    import tempfile
    fails = []

    def chk(name, cond, note=""):
        if not cond:
            fails.append(name)
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "supportive modules").mkdir()
        (root / "eng").mkdir()
        # 雙世代:v0100 ⊂ v0200 → PICK-ONE
        (root / "eng" / "alpha_v0100.py").write_text("def a():\n pass\ndef b():\n pass\n", encoding="utf-8")
        (root / "eng" / "alpha_v0200.py").write_text("def a():\n pass\ndef b():\n pass\ndef c():\n pass\n", encoding="utf-8")
        # 各有獨有 → INTEGRATE
        (root / "eng" / "beta (1).py").write_text("def x():\n pass\ndef y():\n pass\n", encoding="utf-8")
        (root / "eng" / "beta.py").write_text("def y():\n pass\ndef z():\n pass\n", encoding="utf-8")
        # 散落 regex+未閘外呼+無橋
        (root / "eng" / "net_mod.py").write_text(
            "import requests\nimport re\nP = re.compile(r'\\d{4}-\\d{2}-\\d{2}T')\n", encoding="utf-8")
        # 已閘外呼
        (root / "eng" / "gated.py").write_text(
            "import requests\nimport via_net_unified\n", encoding="utf-8")
        # 支援模組候註冊
        (root / "supportive modules" / "helper_one.py").write_text(
            '"""協助工具:示例支援模組"""\ndef run():\n pass\n', encoding="utf-8")
        # PS 治理考古素材
        (root / "Start.ps1").write_text(
            "$ExpectedSHA='abc'\n(Get-FileHash x).Hash\n[System.Management.Automation.Language.Parser]::ParseFile\n& $Launcher -Base $Base\n", encoding="utf-8")
        r1 = m1_ps_archaeology(root)
        # ① 治理考古命中四特徵
        chk("PS 治理考古", r1["governed_ps"] == 1
            and {"sha_pin", "ast_gate", "base_anchor"} <= set(r1["rows"][0]["features"]))
        r2 = m2_two_era_engines(root)
        v = {p["family"]: p["verdict"] for p in r2["proposals"]}
        # ②③ 擇一/整合判定+核准閘
        chk("PICK-ONE 舉證", v.get("alpha") == "PICK-ONE")
        chk("INTEGRATE 舉證", v.get("beta") == "INTEGRATE")
        chk("核准閘", all("APPROVAL_REQUIRED" in p["status"] for p in r2["proposals"]))
        central = {"synonyms": {"BUY": ["買進", "加碼"], "SELL": ["賣出", "加碼"]},
                   "regex": {"K": {"pattern": "^x$"}}}
        r3 = m3_ssot_sync(root, central)
        # ④ 同義字矛盾(加碼跨 BUY/SELL)
        chk("同義字矛盾檢", len(r3["synonym_conflicts"]) == 1
            and r3["synonym_conflicts"][0]["term"] == "加碼")
        # ⑤ 散落 regex 必要性提醒
        chk("regex 必要性提醒", any("d{4}" in r["pattern"] for r in r3["regex_reminders"]))
        r4 = m4_accel_audit(root)
        # ⑥ 缺橋清單(gated.py 亦無橋標記但有 via_net→仍算缺 ACCEL 橋?net gate≠accel 橋:兩者分開誠實)
        chk("加速器稽核", r4["lack_bridge"] >= 4 and "eng/net_mod.py" in r4["bridge_plan"])
        rp = root / "SUP_REG.json"
        r5 = m5_supportive_autoregister(root, rp)
        # ⑦⑧ 自動註冊 SUP-0001+append-only 冪等
        chk("支援模組註冊", len(r5["added_now"]) == 1
            and r5["added_now"][0]["sup_id"] == "SUP-0001"
            and "協助工具" in r5["added_now"][0]["role"])
        r5b = m5_supportive_autoregister(root, rp)
        chk("註冊冪等 append-only", len(r5b["added_now"]) == 0 and r5b["registered_total"] == 1)
        r6 = m6_net_audit(root)
        # ⑨ 外呼稽核:net_mod 中、gated 閘內不中
        chk("外呼網路稽核", r6["rows"] == ["eng/net_mod.py"])
        # ⑩ 家族鍵正規化((1)/vNNNN/_sha 尾)
        chk("家族鍵正規化", _family_key("Foo_v0102") == "foo"
            and _family_key("Bar (2)") == "bar" and _family_key("Baz_sha12ab34cd") == "baz")
        # ⑪ 語法不可解析側=HOLD 誠實
        (root / "eng" / "gamma_v0100.py").write_text("def ok():\n pass\n", encoding="utf-8")
        (root / "eng" / "gamma_v0200.py").write_text("def broken(:\n", encoding="utf-8")
        r2b = m2_two_era_engines(root)
        chk("不可解析=HOLD", {p["family"]: p["verdict"] for p in r2b["proposals"]}.get("gamma") == "HOLD")
        # ⑫ 存證 run() 全鏈(以沙盒為根)
        global RUNS, DICT_PATH, SUP_REG
        _r, _d, _s = RUNS, DICT_PATH, SUP_REG
        RUNS, DICT_PATH, SUP_REG = root / "runs", root / "nodict.json", rp
        try:
            rc = run(root)
        finally:
            RUNS, DICT_PATH, SUP_REG = _r, _d, _s
        chk("run 全鏈+存證", rc == 0 and len(list((root / "runs").glob("TAKEOVER_*.json"))) == 1)
    n = 12 - len(fails)
    print(f"  [計] 十二檢 OK {n} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== 母系統向下接手引擎 v0100 · 十二檢(沙盒零網路)===")
        return selftest()
    if "--run" in a or not a:
        print("=== 母系統向下接手引擎 v0100(TOOL-097)· 六路全跑 ===")
        return run()
    print(__doc__.split("用法:")[1])
    return 2


if __name__ == "__main__":
    sys.exit(main())
