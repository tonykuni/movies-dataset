#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SUP_MDL740_NetUnified_v0104 — 統包唯一網路工具 · AegisNexus 後端版(TOOL-080)
====================================================================
批130 操作員令(2026-08-24):「將原本網路工具移除,導入這個」
(送達 VeritasAegisNexus.py 網路核心 4521 行:ResilientHTTP/反爬/
CloudflareBypass/yFinance 盾/台股資料源/robots ComplianceReactor)。
  ① 後端切換 — http_json/http_text/probe 車道實作核心改委派
     AegisNexus(fetch_json/fetch_text;取代原 stdlib 內建道=「移除
     原本、導入這個」);AegisNexus 缺席/回 None=退原 stdlib 後備
     (graceful 零斷)。yf_download/gsheet_csv/akshare_call 保留。
  ② 雙閘不動 — 最外層法遵雙閘 VIA_NET_CONSENT 保留(紅線:換工具
     不等於移除同意閘;AegisNexus 自帶 ComplianceReactor robots/
     管轄權 rps 疊加=法遵更嚴)。閘閉=DENY 零外呼恆真。
  ③ 誠實註 — AegisNexus 內部抓取道 verify=False(其既定 TLS 行為,
     操作員自有市場資料工具);統包不改其內部,誠實登錄於總冊。
批125 原令:「所有網路模組整合為一」。
  ① 整合總冊 — VIA_NetModules_Integration_Register(glob 最新版):
     全樹網路模組清點分類(CANONICAL/SHIM/BRIDGED/LEGACY_INERT/
     SELF_NET);--modules 檢閱;legacy 收容件能力由本器車道涵蓋。
  ② 六車道 — v0101 四車道+gsheet_csv(Google Sheet 公開表→CSV 匯出
     URL 建構+閘控抓取;v4.2 生態 GSheetConnector 道)+akshare_call
     (akshare 函數閘控呼叫;套件缺=SKIP 誠實)。
====================================================================
批124 操作員令(2026-08-24):「網路工具全部放在同一個引擎整合在一起
測試無誤,並改名稱依照我們的規定」。
  ① 正名 — 命名冊(TOOL-047)規則 <SYS>_<MDL><NNN>_<Camel>:本件=
     SUP_MDL740_NetUnified(SUP_MDL 計數 739 之次號,先發先得);
     via_net_unified_v0101 為橋容轉接件(NET-BRIDGE glob 不斷鏈)。
  ② 四車道整合 — 各引擎網路動作統一委派本器(單一引擎):
     http_json(url)/http_text(url)/probe(url)/yf_download(tickers)
     全數法遵雙閘 fail-closed;閘閉=DENY 零網路,錯誤=FAIL 誠實。
     ENG050 擷取單/ENG047 美細目/ENG049 五日線 http 與 yf 道皆可
     經 NET-BRIDGE 取本器車道(graceful:統包缺席時引擎自道不變)。
批66 原令(2026-08-19):「都要導入網路工具及加速器註冊與其他
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
import re
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


# ── 批130 AegisNexus 網路核心後端(送達件;動態最新;缺=退 stdlib)──
_AEGIS_CACHE = {"mod": None}


def _resolve_aegis_path():
    """定位 VeritasAegisNexus 網路核心(上溯 network 目錄+os.listdir 重試;
    抗容器 overlay 檔案系統 race;缺=None)"""
    import os
    try:
        _p = Path(__file__).resolve()
        _dirs = []
        while _p.parent != _p:
            _nd = _p / "supportive modules" / "network"
            if _nd.exists():
                _dirs.append(_nd)
                break
            _p = _p.parent
        _dirs.append(Path(os.path.dirname(os.path.abspath(__file__))))
        for _nd in _dirs:
            for _ in range(5):             # 重試抗 overlay glob/listdir race
                try:
                    _c = sorted(f for f in os.listdir(str(_nd))
                                if f.startswith("via_aegis_netcore_v") and f.endswith(".py"))
                except Exception:
                    _c = []
                if _c:
                    return str(_nd / _c[-1])
    except Exception:
        pass
    return None


VIA_AEGIS_PATH = _resolve_aegis_path()      # 模組載入當下固定(檔案此刻必可見=最穩)


def _aegis():
    """VeritasAegisNexus 網路核心惰性載入(路徑載入即固定;缺/壞=None 退 stdlib;
    不快取 None=容 race 後重試)"""
    if _AEGIS_CACHE["mod"] is not None:
        return _AEGIS_CACHE["mod"]
    _path = VIA_AEGIS_PATH or _resolve_aegis_path()   # 後備即時重解析
    if not _path or not Path(_path).exists():
        return None
    try:
        import importlib.util as _ilu
        import sys as _sys
        spec = _ilu.spec_from_file_location("VIA_AEGIS_NETCORE", _path)
        mod = _ilu.module_from_spec(spec)
        _sys.modules["VIA_AEGIS_NETCORE"] = mod   # 先掛名再 exec(dataclass/自參照 import 需要)
        spec.loader.exec_module(mod)
        _AEGIS_CACHE["mod"] = mod
        return mod
    except Exception:
        return None


# ── 批124 四車道(單一引擎統包;法遵雙閘 fail-closed)──────────
def _deny_if_closed() -> dict | None:
    g = gate_state()
    if not g["open"]:
        why = ("閘一未開" if not g["gate1_net_consent"]
               else "閘二未開" if not g["gate2_scrape_token_set"] else "閘閉")
        return {"state": "DENY", "note": f"fail-closed:{why}(誠實拒絕,零網路)"}
    return None


def http_json(url: str, timeout: int = 30) -> dict:
    """車道①:JSON 端點(TWSE/TPEX/Cnyes/FRED 類);雙閘先行;
    後端=AegisNexus.fetch_json(批130);缺/回 None=退 stdlib"""
    d = _deny_if_closed()
    if d:
        return d
    ax = _aegis()
    if ax is not None and hasattr(ax, "fetch_json"):
        try:
            data = ax.fetch_json(url, timeout=timeout)
            if data is not None:
                return {"state": "OK", "data": data, "via": "AegisNexus"}
        except Exception:
            pass
    try:
        import urllib.request
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 VIA/NetUnified"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return {"state": "OK", "data": json.loads(r.read().decode("utf-8", "replace")),
                    "via": "stdlib"}
    except Exception as exc:
        msg = str(exc)
        return {"state": "FAIL", "note": msg[:160],
                "blocked_by_policy": ("403" in msg or "CONNECT" in msg or "Tunnel" in msg)}


def http_text(url: str, timeout: int = 30) -> dict:
    """車道②:文本抓取(走 SuperAccel.fetch 快取/重試道;缺席=標準庫)"""
    d = _deny_if_closed()
    if d:
        return d
    try:
        ax = _aegis()
        if ax is not None and hasattr(ax, "fetch_text"):
            body = ax.fetch_text(url, timeout=timeout)
            if body:
                return {"state": "OK", "data": body, "via": "AegisNexus"}
        if VIA_ACCEL is not None and hasattr(VIA_ACCEL, "fetch"):
            body = VIA_ACCEL.fetch(url, timeout=timeout)
            if body is not None:
                return {"state": "OK", "data": body, "via": "SuperAccel"}
        import urllib.request
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 VIA/NetUnified"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return {"state": "OK", "data": r.read().decode("utf-8", "replace"), "via": "stdlib"}
    except Exception as exc:
        msg = str(exc)
        return {"state": "FAIL", "note": msg[:160],
                "blocked_by_policy": ("403" in msg or "CONNECT" in msg or "Tunnel" in msg)}


def probe(url: str, timeout: int = 15) -> dict:
    """車道③:預檢單點探測(ENG050 preflight 統包道);雙閘先行"""
    d = _deny_if_closed()
    if d:
        return {**d, "reachable": False}
    r = http_text(url, timeout=timeout)
    return {"state": r["state"], "reachable": r["state"] == "OK",
            "blocked_by_policy": r.get("blocked_by_policy", False),
            "note": r.get("note", "")}


def yf_download(tickers: list[str], period: str = "5d") -> dict:
    """車道④:yfinance 批次(auto_adjust=False 保 Adj);雙閘先行"""
    d = _deny_if_closed()
    if d:
        return d
    try:
        import yfinance as yf
    except ImportError:
        return {"state": "SKIP", "note": "yfinance 未裝(誠實)"}
    try:
        df = yf.download(tickers, period=period, interval="1d", auto_adjust=False,
                         progress=False, threads=True, group_by="ticker")
        return {"state": "OK", "data": df}
    except Exception as exc:
        return {"state": "FAIL", "note": str(exc)[:160]}


def yahoo_chart(tickers: list[str], start_epoch: int, end_epoch: int,
                pause_s: float = 0.4) -> dict:
    """車道④b(v0104;批136):Yahoo chart API 直連後備——本容器 yfinance 之
    curl_cffi 與代理 TLS 不合(curl 35 reset 存證),改走 http_json 既有後端
    (AegisNexus 優先/stdlib 後備;同意閘先行);逐標的節流,誠實列敗。"""
    d = _deny_if_closed()
    if d:
        return d
    import time as _t
    rows, failed = [], []
    for t in tickers:
        url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{t}"
               f"?period1={start_epoch}&period2={end_epoch}&interval=1d&events=div%2Csplits")
        r = http_json(url)
        try:
            res = r["data"]["chart"]["result"][0]
            ts = res["timestamp"]
            q = res["indicators"]["quote"][0]
            adj = res["indicators"].get("adjclose", [{}])[0].get("adjclose") or q["close"]
            for i, tt in enumerate(ts):
                if q["close"][i] is None:
                    continue
                rows.append({"date": _t.strftime("%Y-%m-%d", _t.gmtime(tt)), "ticker": t,
                             "open": q["open"][i], "high": q["high"][i],
                             "low": q["low"][i], "close": q["close"][i],
                             "adj_close": adj[i], "volume": q["volume"][i]})
        except Exception as exc:
            failed.append({"ticker": t, "note": (str(r.get("note", "")) or str(exc))[:80]})
        _t.sleep(pause_s)
    state = "OK" if rows else ("FAIL" if failed else "EMPTY")
    return {"state": state, "rows": rows, "failed": failed,
            "note": f"{len(set(x['ticker'] for x in rows))} 標的成·{len(failed)} 敗(chart 直連後備)"}


GSHEET_RX = re.compile(r"docs\.google\.com/spreadsheets/d/([A-Za-z0-9_-]+)")


def gsheet_csv_url(url: str) -> str | None:
    """車道⑤前置:Google Sheet URL→CSV 匯出 URL(零網路純解析)"""
    m = GSHEET_RX.search(url or "")
    if not m:
        return None
    gid = "0"
    mg = re.search(r"[#&?]gid=(\d+)", url)
    if mg:
        gid = mg.group(1)
    return f"https://docs.google.com/spreadsheets/d/{m.group(1)}/export?format=csv&gid={gid}"


def gsheet_csv(url: str, timeout: int = 30) -> dict:
    """車道⑤:Google Sheet 讀取(公開/共享表;雙閘先行)"""
    cu = gsheet_csv_url(url)
    if cu is None:
        return {"state": "FAIL", "note": "非 Google Sheet URL(解析零命中)"}
    d = _deny_if_closed()
    if d:
        return d
    r = http_text(cu, timeout=timeout)
    return {**r, "csv_url": cu}


def akshare_call(fn_name: str, **kwargs) -> dict:
    """車道⑥:AkShare 函數呼叫(BDI 類 CN 源;雙閘先行;套件缺=SKIP)"""
    d = _deny_if_closed()
    if d:
        return d
    try:
        import akshare as ak
    except ImportError:
        return {"state": "SKIP", "note": "akshare 未裝(誠實)"}
    fn = getattr(ak, fn_name, None)
    if fn is None:
        return {"state": "FAIL", "note": f"akshare 無此函數 {fn_name}"}
    try:
        return {"state": "OK", "data": fn(**kwargs)}
    except Exception as exc:
        return {"state": "FAIL", "note": str(exc)[:160]}


def load_net_register() -> dict | None:
    hits = sorted((VIA / "supportive modules" / "registry")
                  .glob("VIA_NetModules_Integration_Register_v*.json"))
    return json.loads(hits[-1].read_text(encoding="utf-8-sig")) if hits else None


def cmd_modules() -> int:
    reg = load_net_register()
    if reg is None:
        print("  [FAIL] 整合總冊缺")
        return 1
    print(f"=== 網路模組整合總冊({reg['ts']})· {reg['counts']['total']} 件 ===")
    print(f"  {json.dumps(reg['counts'], ensure_ascii=False)}")
    print(f"  政策:{reg['policy'][:120]}…")
    return 0


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
    # ⑪ 批124 四車道 fail-closed(未設閘=DENY 零網路)
    saved11 = {k: os.environ.pop(k, None) for k in (CONSENT_ENV, SCRAPE_CONSENT_ENV)}
    lane_denied = (http_json("http://x.local")["state"] == "DENY"
                   and http_text("http://x.local")["state"] == "DENY"
                   and probe("http://x.local")["reachable"] is False
                   and yf_download(["NVDA"])["state"] == "DENY")
    for k, v in saved11.items():
        if v is not None:
            os.environ[k] = v
    chk("四車道 fail-closed(http_json/text/probe/yf)", lane_denied)
    # ⑮ 批130 AegisNexus 後端(載入+車道 via 標記+閘閉仍 DENY)
    ax = _aegis()
    saved15 = {k: os.environ.pop(k, None) for k in (CONSENT_ENV, SCRAPE_CONSENT_ENV)}
    hj15 = http_json("http://x.local")
    for k, v in saved15.items():
        if v is not None:
            os.environ[k] = v
    chk("AegisNexus 後端載入+閘閉仍 DENY(後端不繞閘)",
        ax is not None and hasattr(ax, "fetch_json") and hj15["state"] == "DENY")
    # ⑯ ComplianceReactor 法遵層在位(送達件自帶)
    chk("AegisNexus ComplianceReactor 法遵層在位",
        ax is not None and (hasattr(ax, "ComplianceReactor")
                            or hasattr(ax, "compliance_status_report")
                            or hasattr(ax, "net_status_report")))
    # ⑬ 批125 gsheet 車道(URL 建構零網路+未開閘 DENY)
    cu = gsheet_csv_url("https://docs.google.com/spreadsheets/d/ABC_123-xyz/edit#gid=42")
    saved13 = {k: os.environ.pop(k, None) for k in (CONSENT_ENV, SCRAPE_CONSENT_ENV)}
    g13 = gsheet_csv("https://docs.google.com/spreadsheets/d/ABC/edit")
    a13 = akshare_call("bdi_index")
    for k, v in saved13.items():
        if v is not None:
            os.environ[k] = v
    chk("gsheet URL 建構+雙車道 fail-closed",
        cu == "https://docs.google.com/spreadsheets/d/ABC_123-xyz/export?format=csv&gid=42"
        and g13["state"] == "DENY" and a13["state"] == "DENY"
        and gsheet_csv_url("https://example.com/x") is None)
    # ⑭ 批125 整合總冊在位+分類齊
    reg14 = load_net_register()
    chk("整合總冊(CANONICAL/SHIM/BRIDGED/LEGACY/SELF 分類)",
        reg14 is not None and reg14["counts"]["total"] >= 50
        and reg14["counts"]["CANONICAL"] >= 1)
    # ⑫ 批124 正名對映(SUP_MDL740 正典+橋容 shim 在位)
    chk("正名 SUP_MDL740+橋容 shim",
        Path(__file__).name.startswith("SUP_MDL740_NetUnified")
        or (HERE / "via_net_unified_v0101.py").exists())
    n = 16 - len(fails)
    print(f"  [計] 十六檢 OK {n} · FAIL {len(fails)} · {round(time.time() - t0, 1)}s")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 統包唯一網路工具 SUP_MDL740 v0103 · 十六檢自測(零網路)===")
        return selftest()
    if "--status" in args:
        print("=== 統包唯一網路工具 SUP_MDL740 v0103 · 盤點(TOOL-080)===")
        print(json.dumps(inventory(), ensure_ascii=False, indent=1))
        return 0
    if "--modules" in args:
        return cmd_modules()
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
        print("=== 統包唯一網路工具 SUP_MDL740 v0103 · fetch(法遵雙閘)===")
        return fetch(url)
    print(__doc__.split("用法:")[1])
    return 0


if __name__ == "__main__":
    sys.exit(main())
