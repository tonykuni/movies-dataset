#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
via_net_unified_v0100 — 統包唯一網路工具(TOOL-080)
====================================================================
操作員令(批66,2026-08-19):「都要導入網路工具及加速器註冊與其他
爬蟲工具與網路工具整合唯一工具功能只增不減但受到法遵機制制約」。
原則:
  ① 唯一工具統包 — 批65 收容之爬蟲雙引擎包(webscraping_dualengine
     _v20260819:Playwright Py/JS 引擎+治理控制器+法遵模組+報告
     分類器)與既有網路道(SuperAccel.fetch 同意閘)統包一口;
     功能只增不減:各件原樣在位,本器只調度不改寫。
  ② 法遵雙閘 fail-closed — 任何真實網路動作須同時過:
     閘一:VIA_NET_CONSENT=YES(同意閘鐵律,永不代設);
     閘二:包內法遵(VIA_SCRAPE_CONSENT=I_ACCEPT_RESPONSIBLE_
     SCRAPING + def_validate_consent 用途/法源審查)。
     任一閘閉=誠實拒絕零網路;爬蟲引擎僅盤點在位性不啟動。
  ③ 零網路動詞常開 — --check(法遵預檢)/--scan-terms(條款禁令
     掃描)/--redact(PII 遮罩)/--classify(報告 40 型分類)全程
     本地,無閘也可用。
  ④ 誠實三態 — 引擎缺/Node 缺/pypi 缺=SKIP 誠實;不虛報能力。
用法:
  via-net --status                → 統包盤點(引擎/法遵/閘態)
  via-net --check <url>           → 法遵預檢(零網路,判 allow/deny)
  via-net --scan-terms <檔>       → 條款文本禁令掃描
  via-net --redact <檔>           → PII 遮罩(partial)
  via-net --classify <標題>       → 報告 40 型分類
  via-net --fetch <url>           → 雙閘全開才走 SuperAccel.fetch
  via-net --selftest              → 十檢(零網路)
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全引擎導入令 2026-08-18;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # accel_map/fetch/pip_install/run_fast
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import importlib.util
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent            # supportive modules/network
VIA = HERE.parent.parent
PKG = VIA / "functional modules" / "VRN" / "webscraping_dualengine_v20260819"
MOTTO = "VERITAS INTELLIGENCE ANALYTICS · OBSERVA · INTELLEGE · PRAEVIDE"
CONSENT_ENV = "VIA_NET_CONSENT"                    # 閘一(鐵律)
SCRAPE_CONSENT_ENV = "VIA_SCRAPE_CONSENT"         # 閘二(包內法遵 token)


def _load(name: str, path: Path):
    """動態載入(先掛 sys.modules 再 exec;SyntaxWarning 抑制)"""
    import warnings
    if not path.exists():
        return None, f"{path.name} 缺(誠實)"
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            spec.loader.exec_module(mod)
    except Exception as exc:
        sys.modules.pop(name, None)
        return None, f"{path.name} 匯入敗:{str(exc)[:60]}"
    return mod, path.name


def load_compliance():
    """法遵模組:動態最新(v0101 容器修版優先;嚴禁寫死版號)"""
    hits = sorted(PKG.glob("VIA_WebScraping_Compliance*.py"))
    hits = [h for h in hits if "SSOT" not in h.name]
    if not hits:
        return None, "法遵模組缺"
    return _load("via_net_compliance_dyn", hits[-1])


def load_classifier():
    return _load("via_net_classifier_dyn", PKG / "VIA_Investment_Report_Classifier.py")


def gate_state() -> dict:
    """雙閘態(fail-closed;永不代設)"""
    g1 = os.environ.get(CONSENT_ENV, "")
    g2 = os.environ.get(SCRAPE_CONSENT_ENV, "")
    return {"gate1_net_consent": g1 == "YES",
            "gate2_scrape_token_set": bool(g2),
            "gate1_raw": g1 or "(未設)",
            "open": g1 == "YES" and bool(g2)}


def inventory() -> dict:
    """統包盤點(在位性;零網路零啟動)"""
    comp, comp_name = load_compliance()
    cls, cls_name = load_classifier()
    inv = {
        "package_dir": str(PKG.relative_to(VIA)) if PKG.exists() else "(缺)",
        "compliance": comp_name if comp else f"FAIL:{comp_name}",
        "classifier": cls_name if cls else f"FAIL:{cls_name}",
        "engines": {},
        "superaccel": bool(VIA_ACCEL),
        "gates": gate_state(),
    }
    for eng in ["VIA_Unified_WebScraping_Playwright_Engine.py",
                "VIA_WebScraping_Playwright_Engine.js",
                "VIA_WebScraping_DualEngine_Governance_Controller.py"]:
        inv["engines"][eng] = (PKG / eng).exists()
    try:
        import playwright  # noqa: F401
        inv["playwright_py"] = True
    except ImportError:
        inv["playwright_py"] = False
    return inv


def check_url(url: str) -> dict:
    """法遵預檢(零網路):雙閘態+法遵模組 consent 審查"""
    comp, comp_name = load_compliance()
    g = gate_state()
    out = {"url": url, "gates": g, "verdict": "DENY", "findings": []}
    if comp is None:
        out["findings"].append({"code": "COMPLIANCE_MISSING", "note": comp_name})
        return out
    token = os.environ.get(SCRAPE_CONSENT_ENV, "")
    findings = comp.def_validate_consent(token, purpose="research",
                                         authorization_basis="operator")
    out["findings"] = [{"code": f.code, "severity": f.severity, "message": f.evidence}
                       for f in findings]
    blocking = [f for f in findings if f.severity in ("BLOCK", "ERROR", "CRITICAL")]
    if g["open"] and not blocking:
        out["verdict"] = "ALLOW(候實際 robots/條款線上確認)"
    else:
        out["verdict"] = "DENY(fail-closed:" + \
            ("閘一未開" if not g["gate1_net_consent"] else
             "閘二未開" if not g["gate2_scrape_token_set"] else "法遵 finding 阻擋") + ")"
    return out


def fetch(url: str) -> int:
    """雙閘全開才走 SuperAccel.fetch(不繞過既有同意閘機制)"""
    pre = check_url(url)
    if not pre["verdict"].startswith("ALLOW"):
        print(f"  [DENY] {pre['verdict']}(誠實拒絕,零網路)")
        for f in pre["findings"]:
            print(f"         · {f.get('code')}:{str(f.get('message'))[:70]}")
        return 1
    if VIA_ACCEL is None or not hasattr(VIA_ACCEL, "fetch"):
        print("  [SKIP] SuperAccel 缺席(誠實;統包不自建網路道)")
        return 1
    r = VIA_ACCEL.fetch(url)
    if r is None:
        print("  [DENY] SuperAccel 同意閘拒絕(既有機制,本器不繞過)")
        return 1
    print(f"  [OK] fetch 完成 · {len(r) if hasattr(r, '__len__') else '?'} bytes")
    return 0


def selftest() -> int:
    t0 = time.time()
    fails = []

    def chk(name, cond, note=""):
        state = "OK" if cond else "FAIL"
        if not cond:
            fails.append(name)
        print(f"  [{state}] {name} {note}")

    # ① 包在位:11 件收容齊
    n_files = len(list(PKG.glob("*"))) if PKG.exists() else 0
    chk("爬蟲雙引擎包收容在位", n_files >= 11, f"({n_files} 件)")
    # ② 法遵模組動態載入(v0101 容器修版)
    comp, comp_name = load_compliance()
    chk("法遵模組動態載入", comp is not None, f"({comp_name})")
    if comp is None:
        print("  [計] 十檢中止(法遵缺=fail-closed)")
        return 1
    # ③ consent 空 token=審查 finding 非空(fail-closed)
    f3 = comp.def_validate_consent("", "research", "operator")
    chk("法遵 consent 空token審查", len(f3) > 0)
    # ④ PII 遮罩:email+台灣手機
    red, stats = comp.def_redact_pii(
        "聯絡 tony.huang@yuanta.com.tw 或 0912-345-678", mode="partial")
    chk("PII 遮罩(email/手機)",
        "tony.huang@yuanta.com.tw" not in red and "0912-345-678" not in red
        and sum(stats.values()) >= 2)
    # ⑤ 條款禁令掃描
    scan = comp.def_scan_terms_text("本網站禁止任何自動化爬蟲擷取行為。")
    chk("條款禁令偵測", bool(scan.get("prohibition_hits") or scan.get("hits")
                             or json.dumps(scan, ensure_ascii=False).find("禁止") >= 0))
    # ⑥ 台灣身分證/Luhn 驗證器
    chk("TW ID+Luhn 驗證器",
        comp.def_tw_id_valid("A123456789") and not comp.def_tw_id_valid("A123456780")
        and comp.def_luhn_valid("4111111111111111") and not comp.def_luhn_valid("4111111111111112"))
    # ⑦ 報告分類器 40 型
    cls, cls_name = load_classifier()
    ok7 = cls is not None
    if ok7:
        r_morn = cls.def_classify_investment_report("兆豐晨報 20251205", "")
        r_co = cls.def_classify_investment_report("華南投顧-2606-裕民 個股更新報告", "目標價 70 元")
        r_unk = cls.def_classify_investment_report("MS-2308 Update", "")
        ok7 = (r_morn.report_scope in ("CONTAINER", "MARKET")
               and r_co.report_scope in ("COMPANY", "COMPANY_OR_TOPIC")
               and r_unk.report_type_code == "UNCLASSIFIED_RESEARCH")  # UNKNOWN 誠實不擋
    chk("報告分類器(晨會=容器/個股=COMPANY)", ok7, f"({cls_name})")
    # ⑧ 雙閘 fail-closed:未設環境=DENY
    saved = {k: os.environ.pop(k, None) for k in (CONSENT_ENV, SCRAPE_CONSENT_ENV)}
    pre = check_url("https://example.com")
    denied = pre["verdict"].startswith("DENY")
    for k, v in saved.items():
        if v is not None:
            os.environ[k] = v
    chk("雙閘 fail-closed(未設=DENY)", denied)
    # ⑨ 統包盤點誠實(引擎在位性+playwright 誠實)
    inv = inventory()
    chk("統包盤點(引擎三件+誠實旗標)",
        all(inv["engines"].values()) and isinstance(inv["playwright_py"], bool))
    # ⑩ SuperAccel 橋掛載(graceful 兩態皆過,誠實記)
    chk("SuperAccel 橋 graceful", VIA_ACCEL is None or hasattr(VIA_ACCEL, "fetch"),
        "(掛載)" if VIA_ACCEL else "(缺席 graceful)")
    n = 10 - len(fails)
    print(f"  [計] 十檢 OK {n} · FAIL {len(fails)} · {round(time.time() - t0, 1)}s")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 統包唯一網路工具 v0100 · 十檢自測(零網路)===")
        return selftest()
    if "--status" in args:
        print("=== 統包唯一網路工具 v0100 · 盤點(TOOL-080)===")
        print(json.dumps(inventory(), ensure_ascii=False, indent=1))
        return 0
    if "--check" in args:
        i = args.index("--check")
        url = args[i + 1] if i + 1 < len(args) else ""
        print(json.dumps(check_url(url), ensure_ascii=False, indent=1))
        return 0
    if "--classify" in args:
        i = args.index("--classify")
        title = args[i + 1] if i + 1 < len(args) else ""
        cls, _ = load_classifier()
        if cls is None:
            print("  [FAIL] 分類器缺")
            return 1
        r = cls.def_classify_investment_report(title, "")
        print(json.dumps({"type": r.report_type_code, "zh": r.report_type_zh,
                          "scope": r.report_scope, "confidence": r.confidence},
                         ensure_ascii=False, indent=1))
        return 0
    if "--scan-terms" in args or "--redact" in args:
        comp, comp_name = load_compliance()
        if comp is None:
            print(f"  [FAIL] {comp_name}")
            return 1
        key = "--scan-terms" if "--scan-terms" in args else "--redact"
        i = args.index(key)
        p = Path(args[i + 1]) if i + 1 < len(args) else None
        if not p or not p.exists():
            print(f"  [FAIL] 檔不存在:{p}")
            return 1
        text = p.read_text(encoding="utf-8", errors="replace")
        if key == "--scan-terms":
            print(json.dumps(comp.def_scan_terms_text(text), ensure_ascii=False, indent=1))
        else:
            red, stats = comp.def_redact_pii(text, mode="partial")
            print(red)
            print(f"  [計] 遮罩統計 {json.dumps(stats, ensure_ascii=False)}")
        return 0
    if "--fetch" in args:
        i = args.index("--fetch")
        url = args[i + 1] if i + 1 < len(args) else ""
        print("=== 統包唯一網路工具 v0100 · fetch(法遵雙閘)===")
        return fetch(url)
    print(__doc__.split("用法:")[1])
    return 0


if __name__ == "__main__":
    sys.exit(main())
