#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VRN2_MarketFetch v0111 — VRN-2 的市場資料擷取引擎(包住 VDF_TW_DataFetchEngine v036 · 不改它一字 · 用引擎擷取 · 不靠既有資料庫)。

動詞:
  --fetch  [--basic <VRN2_BasicInfo_latest.json>] [--tickers 2330,6488] [--out <market 夾>]
           v0102 只抓必要日期:① 最新(今天 - 7 天 ~ 今天)② 每份報告日前一個交易日(報告日 - 7 天 ~ 報告日 - 1 天)→ 依視窗分組各跑一次 VDF 引擎 daily
           ③ 年度財報 n-3 ~ n(n = 報告年)→ --datasets financial --quarters {y}Q4(已完成的年度)+ latest(最新一季)· 依年組分組各跑一次
           代號來源:基本資料冊 TICKER(4 碼)· 或 --tickers · 或 --scope <scope_in 夾>(檔名前四碼原則)
           以 VDF 引擎 --datasets daily --start(最早報告日 - 10 天 · 至少 --days)--end 今天 --output <market>/vdf 擷取(官方 TWSE / TPEX + Yahoo 還原)
           Python 優先用 %USERPROFILE%\\envs\\via_tw_fetch\\Scripts\\python.exe(VDF 包自己的環境)· 沒有就用本行程 Python(缺 yfinance / lxml → 回報交 VCGC)
  --fill   --basic <VRN2_BasicInfo_latest.json> --out <market 夾>
           讀 <market>/vdf/parquet/tw_universe + tw_equity_daily → 每檔:NAME · YFINANCE_TICKER · BLOOMBERG_TICKER · ADJ_CLOSE(最新)· ADJ_CLOSE_BEFORE_REPORT(報告日前最後一個交易日)·
           還原因子(報告日)→ TARGET_PRICE(ADJ)= TARGET_PRICE × 因子 · UPSIDE_PCT(ADJ)= TARGET_PRICE(ADJ)/ADJ_CLOSE - 1 → <market>/VRN2_Market_latest.json
           沒有的值寫 MISSING 與理由(不猜 · 不拿 Close 冒充 Adj Close)
  --selftest  三碼規則與 VRN2 Regex 對照 · 合成 parquet 填值 · 引擎在則跑其 28 項離線回歸(--with-vdf-tests)
  v0104 增量規則(操作員):① 價格 / 還原價每輪都重抓(最新視窗 + 各報告視窗 · Yahoo 還原因子會因除權息改變 · 引擎對本地既存日期全部重算)
                         ② 財報只補缺:已落盤的 (代號, 年度) 不再打 MOPS · 只跑有缺口的年組 · latest 一季只在最新 YTD 年度缺或已過新公告期限時才跑
  v0105 橋接根(第 57 / 58 輪實證):鎖冊 VIA_ToolVersion_Lock 的 network.path 相對於 movies-dataset · 引擎用 via_root(…/VeritasIntelligenceAnalytics)拼 → 多一層 → FileNotFoundError。
        解法不改引擎:在 %TEMP%/VIA_progress/vrn2_via_root 建橋接根:supportive modules/registry/VIA_ToolVersion_Lock_v0100.json(path 改絕對 · sha256 不變)+ VIA_SuperAccel_Module.py 轉接 → --via-root 指向它 · 引擎仍走鎖版網路工具並驗雜湊
  v0106 雜湊(第 59 輪實證 hash mismatch):工作樹 CRLF(git autocrlf)vs 鎖冊 LF 雜湊 → 比對正規化(CRLF→LF)雜湊 · 相同 = 內容一致只差行尾 → 橋接鎖冊用實際位元組雜湊;
        正規化後仍不同 = 網路工具真的換版 → 不繞過 · 報「鎖冊過期 · 交 VCGC 重鎖」· 並列出 network 夾裡最新版號供 VCGC 參考
  v0107(第 60 輪實證 no curl_bytes API):① 引擎優先 VDF_TW_AllInOne_v039(操作員附件 · 授權取代)· 無則 v036 ② 橋接根加「網路轉接模組」:對引擎提供 curl_bytes 契約
        (url, timeout, follow, headers → {state, data, http_status, headers, final_url})· 內部呼叫真正鎖版 VeritasAegisNexus(正規化雜湊照驗 · DENY 照傳 PermissionError · 不退 urllib)·
        真模組有 curl_bytes 直接轉;否則依名稱(curl / fetch / get / download / request)+ 可呼叫性探測;都沒有 → 明說「無可用抓取介面」
        ③ 橋接層失敗(介面不相容 · 非拒絕)→ 依操作員授權改獨立模式(v039 官方 TWSE/TPEx 直連)· 黃燈註記「獨立模式」;PermissionError / DENY 不退不繞
  v0110(讀到 v1652 真實介面 · 來源 github.com/tonykuni/movies-dataset 公開倉庫 · sha c2f401071adf 與鎖冊一致):
        轉接模組改一對一精準映射:ResilientHTTPClient(HttpConfig(timeout, max_retries)).request("GET", url, headers, allow_redirects=follow) → requests Response
        → {state OK, data=content, http_status, headers, final_url}· 合規層 get_scraping_strategy(url).allowed=False → state DENY(照傳 · 不繞)· 無 ResilientHTTPClient 才退 fetch_bytes(無轉址控制 · 註記)
        v0108 / v0109 為另一線版本 · 本線版號跳到 v0110
  v0111(第 62 輪實證 ⑥e「1500 秒沒有任何輸出 · 已停止」):① 引擎改 -u 串流 · 每 30 秒印心跳(引擎最後一行 + 已跑秒數)· 不再沉默被殺
        ② 加速器:依鎖冊 accelerator.path 匯入 VeritasCeleritas(可匯入 / 缺 · 不擋)· doctor 與貼包回報 ③ 鎖版網路工具版本 / sha 進貼包
  --doctor [--out <market 夾>]  v0103 診斷:Python 版本 · 引擎可否編譯 / 匯入 · VIA 網路橋偵測(def_via_bridges)· 必要套件 · 最近一次失敗尾端(last_error.txt)
"""
from __future__ import annotations

import datetime as _dt
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

VERSION = "v0111"
HERE = Path(__file__).resolve().parent
ENGINE_NAME = "VDF_TW_DataFetchEngine_v036.py"
_BASE = re.compile(r"^([1-9]\d{3})$")
_TYPES = [("STOCK", r"^([1-9]\d{3})"), ("ETF_EQUITY_ACTIVE", r"^(00\d{2,3}A)"), ("ETF_BOND_PASSIVE", r"^(00\d{2,3}B)"), ("ETF_BOND_ACTIVE", r"^(00\d{2,3}D)"), ("ETF_LEVERAGED", r"^(00\d{2,3}L)"),
          ("ETF_INVERSE", r"^(00\d{2,3}R)"), ("ETF_FUTURES", r"^(00\d{2,3}[UV])"), ("ETF_BALANCED", r"^(00\d{2,3}T)"), ("ETF_EQUITY_PASSIVE", r"^(00\d{2,3})")]   # v0101 VRN2 Regex v0103 九類


def ticker_type(code: str) -> tuple:
    """v0101 三種形式任一 → (類型 · 本地代碼)· 不合回 ('', '')。VRN-2 範圍只擷取 STOCK;ETF 只分類。"""
    s = (code or "").strip().upper()
    s = re.sub(r"(\.TWO?|\s+TT)$", "", s)
    for t, rx in _TYPES:
        m = re.match(rx + "$", s)
        if m:
            return t, m.group(1)
    return "", ""


def engine_path() -> Path | None:
    """v0107:優先 AllInOne v039(操作員授權取代)· 其次 v036 · 版號取最新。"""
    for pat in ("VDF_TW_AllInOne_v[0-9][0-9][0-9].py", "VDF_TW_DataFetchEngine_v[0-9][0-9][0-9].py"):
        c = sorted((HERE / "_vdf_fetch").glob(pat))
        if c:
            return c[-1]
    return None


def fetch_python() -> str:
    cand = Path(os.environ.get("USERPROFILE", str(Path.home()))) / "envs" / "via_tw_fetch" / "Scripts" / "python.exe"
    return str(cand) if cand.exists() else sys.executable


def forms(code: str, market: str) -> dict:
    code = str(code).strip()
    if not _BASE.match(code) or market not in ("TWSE", "TPEX"):
        return {}
    return {"ticker": code, "yfinance_ticker": code + (".TW" if market == "TWSE" else ".TWO"), "bloomberg_ticker": "%s TT" % code, "market": market}


def _tickers_from_basic(basic_path: Path) -> list:
    try:
        rows = json.loads(basic_path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return []
    out = []
    for r in rows:
        t = str(r.get("TICKER") or "").strip()
        m = _BASE.match(t) or re.match(r"^([1-9]\d{3})(?:\.TWO?|\s+TT)$", t)
        if m and m.group(1) not in out:
            out.append(m.group(1))
    return out


def _tickers_from_scope(scope: Path) -> list:
    out = []
    for p in sorted(scope.glob("*.pdf")):
        for m in re.finditer(r"(?<!\d)([1-9]\d{3})(?!\d)", p.name):
            c = m.group(1)
            if not (c[:2] in ("19", "20") and re.search(c + r"\d{4}", p.name)) and c not in out:
                out.append(c)
                break
    return out


def _dates_from_basic(basic_path: Path) -> list:
    try:
        rows = json.loads(basic_path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return []
    ds = []
    for r in rows:
        d = str(r.get("REPORT_DATE") or "")
        if re.match(r"^\d{4}-\d{2}-\d{2}$", d):
            ds.append(d)
    return ds


def via_root() -> Path:
    return Path(os.environ.get("VIA_ROOT") or str(HERE.parent.parent))


def accel_note(root: Path = None) -> str:
    """v0111 依鎖冊 accelerator.path 匯入 VeritasCeleritas(不綁版號 · 可匯入 / 缺 · 不擋)。"""
    try:
        root = Path(root) if root else via_root()
        lk = root / "supportive modules" / "registry" / "VIA_ToolVersion_Lock_v0100.json"
        if lk.exists():
            spec = json.loads(lk.read_text(encoding="utf-8-sig"))
            ent = spec.get("accelerator") or {}
            p = Path(ent.get("path", ""))
            if not p.is_absolute():
                p = (lk.parents[3] if len(lk.parents) > 3 else lk.parent) / p   # path 相對 movies-dataset
            if p.is_file():
                r = subprocess.run([sys.executable, "-W", "ignore", "-c", "import importlib.util,sys;sp=importlib.util.spec_from_file_location('acc',sys.argv[1]);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);print('ok')", str(p)], capture_output=True, text=True, timeout=120)
                return "加速器 %s %s" % (p.stem, "可匯入" if "ok" in r.stdout else "匯入失敗(%s)" % (r.stdout + r.stderr).strip()[-60:])
            return "加速器 鎖冊路徑不存在(%s)" % ent.get("version", "?")
    except Exception as exc:  # noqa: BLE001
        return "加速器 檢查失敗 %s" % type(exc).__name__
    return "加速器 鎖冊未找到"


def hasattr_curl_bytes(p: Path) -> bool:
    try:
        return "def curl_bytes" in p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False


ADAPTER = '# [VIA:ACCEL-BRIDGE:v0111]\n"""VIA_NetBridge_Adapter — VRN-2 橋接層(v0110):鎖版 VeritasAegisNexus(v1652 = 1.65.1 本體 + 疊加)→ VDF 引擎 curl_bytes 契約。\n精準映射:ResilientHTTPClient.request("GET", url, headers=, allow_redirects=follow) → requests Response。合規 allowed=False → DENY(不繞)。\n真模組:__REAL__(正規化 sha256 __SHA__)· 載入前照驗雜湊 · 不退 urllib。"""\nimport hashlib, importlib.util, sys\nfrom pathlib import Path\nREAL = Path(r"__REAL__"); REAL_SHA = "__SHA__"\n_b = REAL.read_bytes()\nif REAL_SHA and hashlib.sha256(_b.replace(b"\\r\\n", b"\\n")).hexdigest() != REAL_SHA and hashlib.sha256(_b).hexdigest() != REAL_SHA:\n    raise ValueError("鎖版網路工具雜湊不符(轉接層拒絕載入)")\n_sp = importlib.util.spec_from_file_location("via_locked_net_real", REAL); _m = importlib.util.module_from_spec(_sp); sys.modules[_sp.name] = _m; _sp.loader.exec_module(_m)\nCHOSEN = "ResilientHTTPClient" if hasattr(_m, "ResilientHTTPClient") and hasattr(_m, "HttpConfig") else ("fetch_bytes" if hasattr(_m, "fetch_bytes") else None)\n_clients = {}\ndef _client(timeout):\n    key = int(timeout or 35)\n    if key not in _clients:\n        _clients[key] = _m.ResilientHTTPClient(config=_m.HttpConfig(timeout=float(key), max_retries=2))\n    return _clients[key]\ndef _compliance(url):\n    try:\n        st = _m.get_scraping_strategy(url) if hasattr(_m, "get_scraping_strategy") else None\n    except Exception:  # noqa: BLE001\n        return None\n    return st\ndef curl_bytes(url, timeout=35, follow=False, headers=None, **kw):\n    if CHOSEN is None:\n        raise RuntimeError("鎖版網路工具沒有 ResilientHTTPClient / fetch_bytes 介面 · 可呼叫:%s" % [n for n in dir(_m) if not n.startswith("_") and callable(getattr(_m, n))][:20])\n    st = _compliance(url)\n    if st is not None and getattr(st, "allowed", True) is False:\n        return {"state": "DENY", "data": b"", "reason": "鎖版網路工具合規層:%s" % getattr(st, "reason", ""), "http_status": 0, "headers": {}, "final_url": url}\n    hdr = dict(headers or {})\n    if st is not None and getattr(st, "headers", None):\n        for k, v in dict(st.headers).items():\n            hdr.setdefault(k, v)\n    try:\n        if CHOSEN == "ResilientHTTPClient":\n            resp = _client(timeout).request("GET", url, headers=hdr, allow_redirects=bool(follow))\n            if resp is None:\n                return {"state": "ERROR", "data": b"", "reason": "ResilientHTTPClient 回 None(重試耗盡 / 連線失敗)", "http_status": 0, "headers": {}, "final_url": url}\n            code = int(getattr(resp, "status_code", 0) or 0)\n            if code in (401, 403):\n                return {"state": "DENY", "data": b"", "reason": "HTTP %d" % code, "http_status": code, "headers": dict(getattr(resp, "headers", {}) or {}), "final_url": getattr(resp, "url", url)}\n            return {"state": "OK", "data": bytes(resp.content or b""), "http_status": code, "headers": dict(getattr(resp, "headers", {}) or {}), "final_url": getattr(resp, "url", url)}\n        data = _m.fetch_bytes(url, timeout=int(timeout or 35), headers=hdr)\n        return {"state": "OK" if data else "ERROR", "data": bytes(data or b""), "http_status": 200 if data else 0, "headers": {}, "final_url": url, "note": "fetch_bytes 無轉址控制"}\n    except PermissionError as exc:\n        return {"state": "DENY", "data": b"", "reason": str(exc)[:120], "http_status": 0, "headers": {}, "final_url": url}\n    except Exception as exc:  # noqa: BLE001\n        return {"state": "ERROR", "data": b"", "reason": "%s: %s" % (type(exc).__name__, str(exc)[:120]), "http_status": 0, "headers": {}, "final_url": url}\n'


def shim_root(root: Path = None) -> tuple:
    """v0105 橋接根:解析鎖冊 network.path(試 root/path · root.parent/path · 絕對)→ 寫 TEMP 副本(絕對路徑 · 同 sha256)· 加速器轉接 · 回 (橋接根, 說明)。鎖冊不在 → 回 (None, 說明) 由引擎走 STANDALONE。"""
    root = root or via_root()
    support = root / "supportive modules"
    lock = support / "registry" / "VIA_ToolVersion_Lock_v0100.json"
    if not lock.is_file():
        return None, "鎖冊不在 %s → 引擎 STANDALONE(urllib)" % lock
    try:
        spec = json.loads(lock.read_text(encoding="utf-8-sig"))
    except Exception as exc:  # noqa: BLE001
        return None, "鎖冊讀取失敗 %s" % type(exc).__name__
    entry = spec.get("net", spec.get("network", {})) or {}
    raw = str(entry.get("path") or "")
    cands = [Path(raw)] if raw and Path(raw).is_absolute() else [root / raw, root.parent / raw, lock.parent.parent / raw, lock.parent.parent.parent / raw] if raw else []
    hit = next((c for c in cands if c.is_file()), None)
    if not hit:
        return None, "鎖冊 network.path 解析不到(試過 %s)" % " | ".join(str(c) for c in cands[:3])
    shim = Path(os.environ.get("TEMP") or os.environ.get("TMP") or "/tmp") / "VIA_progress" / "vrn2_via_root"
    reg = shim / "supportive modules" / "registry"; reg.mkdir(parents=True, exist_ok=True)
    spec2 = json.loads(json.dumps(spec))
    key = "net" if "net" in spec2 else "network"
    spec2.setdefault(key, {}).update(entry); spec2[key]["path"] = str(hit.resolve())
    import hashlib as _h
    want = (entry.get("sha256") or "").lower()
    raw_b = hit.read_bytes()
    actual = _h.sha256(raw_b).hexdigest(); norm = _h.sha256(raw_b.replace(b"\r\n", b"\n")).hexdigest()
    hash_note = ""
    if want and actual != want:
        if norm == want:
            spec2[key]["sha256"] = actual; hash_note = " · 雜湊只差行尾 CRLF(正規化後與鎖冊相同)→ 橋接鎖冊用實際位元組雜湊"
        else:
            newest = sorted(hit.parent.glob("VeritasAegisNexus_v*.py"))
            return None, "鎖冊過期:%s 內容與鎖冊雜湊不同(正規化後仍不同 · 不繞過)· network 夾最新 %s · 交 VCGC 重鎖後 ⑥e 才會通" % (hit.name, newest[-1].name if newest else "?")
    if not hasattr_curl_bytes(hit):                                            # v0107 真模組沒有 curl_bytes → 轉接模組
        netd = shim / "supportive modules" / "network"; netd.mkdir(parents=True, exist_ok=True)
        ad = netd / "VIA_NetBridge_Adapter_v0100.py"
        ad.write_text(ADAPTER.replace("__REAL__", str(hit.resolve())).replace("__SHA__", want or norm), encoding="utf-8")
        spec2[key]["path"] = str(ad.resolve()); spec2[key]["sha256"] = _h.sha256(ad.read_bytes()).hexdigest()
        spec2[key]["adapter_of"] = {"path": str(hit.resolve()), "sha256_normalized": norm, "lock_sha256": want}
        hash_note += " · 真模組無 curl_bytes → 轉接模組(介面轉換 · 雜湊照驗 · DENY 照傳)"
    (reg / "VIA_ToolVersion_Lock_v0100.json").write_text(json.dumps(spec2, ensure_ascii=False, indent=1), encoding="utf-8")
    acc = support / "VIA_SuperAccel_Module.py"
    if acc.is_file():
        (shim / "supportive modules" / "VIA_SuperAccel_Module.py").write_text("# [VIA:ACCEL-BRIDGE:v0111] 轉接 → 真實加速器\nimport sys as _s; _p = %r\nif _p not in _s.path: _s.path.insert(0, _p)\nfrom VIA_SuperAccel_Module import *  # noqa: F401,F403\n" % str(support), encoding="utf-8")
    return shim, "橋接根 %s · network → %s(sha %s)%s" % (shim, hit.name, (entry.get("sha256") or "")[:12], hash_note)


def _run_engine(eng: Path, py: str, tickers: list, extra: list, vdf: Path, timeout: int, standalone: bool = False) -> tuple:
    shim, _ = (None, "") if standalone else shim_root()
    via = [] if standalone else (["--via-root", str(shim)] if shim else ([] if "AllInOne" in eng.name else []))
    cmd = [py, "-u", "-W", "ignore", str(eng), "--tickers", ",".join(tickers), "--output", str(vdf)] + extra + via
    lines, t0, last_beat = [], time.time(), time.time()
    try:                                                                       # v0111 串流 + 心跳(每 30 秒)· 上層看門不再因沉默殺掉
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace", cwd=str(eng.parent), bufsize=1)
        import threading, queue as _q
        qq = _q.Queue()
        def _rd():
            for ln in p.stdout:
                qq.put(ln.rstrip("\n"))
            qq.put(None)
        threading.Thread(target=_rd, daemon=True).start()
        done = False
        while not done:
            try:
                ln = qq.get(timeout=1.0)
                if ln is None:
                    done = True
                else:
                    lines.append(ln)
            except _q.Empty:
                pass
            now = time.time()
            if now - last_beat >= 30:
                last_beat = now
                print("    [計]   引擎心跳 · %s · 已 %d 秒 · %s" % (eng.name, int(now - t0), (lines[-1][:100] if lines else "(尚無輸出)")), flush=True)
            if now - t0 > timeout:
                p.kill(); lines.append("逾時 %d 秒 · 已停止" % timeout)
                return 124, lines[-6:]
        rc = p.wait()
        if rc not in (0, 2):                                                   # v0103 失敗:完整尾端落盤
            try:
                (vdf / "last_error.txt").write_text("CMD: %s\n\n%s" % (" ".join(cmd), "\n".join(lines[-40:])), encoding="utf-8")
            except Exception:  # noqa: BLE001
                pass
        return rc, lines[-6:]
    except Exception as exc:  # noqa: BLE001
        return 1, ["%s: %s" % (type(exc).__name__, str(exc)[:120])]


def plan_windows(basic_rows: list, today: _dt.date, tickers_only: list = None) -> tuple:
    """v0102 必要日期:每份 (代號, 報告日) → 視窗 [報告日-7, 報告日-1];全部代號 → 最新視窗 [今天-7, 今天];財報 → 年組 {n-3..n 已完成年度 Q4} 依代號分組。"""
    daily, fin = {}, {}
    last_done_q4 = today.year - 1 if today.month >= 4 else today.year - 2            # Q4 財報約 3 月底公告 → 4 月後才算已完成
    for r in basic_rows:
        t = str(r.get("TICKER") or "").strip()
        m = _BASE.match(t) or re.match(r"^([1-9]\d{3})(?:\.TWO?|\s+TT)$", t)
        if not m:
            continue
        code = m.group(1)
        try:
            rd = _dt.date.fromisoformat(str(r.get("REPORT_DATE") or ""))
        except ValueError:
            continue
        key = ((rd - _dt.timedelta(days=7)).isoformat(), (rd - _dt.timedelta(days=1)).isoformat())
        daily.setdefault(key, set()).add(code)
        yrs = tuple("%dQ4" % y for y in range(rd.year - 3, rd.year + 1) if y <= last_done_q4)
        if yrs:
            fin.setdefault(yrs, set()).add(code)
    allt = sorted(set(c for v in daily.values() for c in v) | set(tickers_only or []))
    if allt:
        daily[((today - _dt.timedelta(days=7)).isoformat(), today.isoformat())] = set(allt)
    # 相近視窗合併(起日差 ≤ 14 天 → 合成一個視窗 · 減少跑次)
    merged = []
    for (s0, e0), ts in sorted(daily.items()):
        if merged and (_dt.date.fromisoformat(s0) - _dt.date.fromisoformat(merged[-1][0][0])).days <= 14:
            ps, pe = merged[-1][0]
            merged[-1] = ((ps, max(pe, e0)), merged[-1][1] | ts)
        else:
            merged.append(((s0, e0), set(ts)))
    return merged, fin, allt


def _fin_coverage(vdf: Path) -> set:
    """已落盤的 (代號, 年度) 集合(tw_financial parquet 分區 ticker=/year= · 只看目錄 · 不讀內容)。"""
    out = set()
    base = vdf / "parquet" / "tw_financial"
    if base.is_dir():
        for p in base.glob("ticker=*/year=*/data.parquet"):
            try:
                out.add((p.parent.parent.name.split("=", 1)[1], int(p.parent.name.split("=", 1)[1])))
            except (IndexError, ValueError):
                pass
    return out


def _latest_stale(vdf: Path, ticker: str, today: _dt.date) -> bool:
    """最新一季是否過期:上次抓的時間早於最近一個法定公告期限(3/31 · 5/15 · 8/14 · 11/14)→ 需重抓。"""
    p = vdf / "parquet" / "tw_financial" / ("ticker=%s" % ticker) / ("year=%d" % today.year) / "data.parquet"
    if not p.exists():
        return True
    mt = _dt.date.fromtimestamp(p.stat().st_mtime)
    dls = [_dt.date(today.year, 3, 31), _dt.date(today.year, 5, 15), _dt.date(today.year, 8, 14), _dt.date(today.year, 11, 14)]
    last_dl = max([d for d in dls if d <= today], default=None)
    return bool(last_dl and mt < last_dl)


def fetch(args: dict) -> dict:
    eng = engine_path()
    out = Path(args["out"]); vdf = out / "vdf"; vdf.mkdir(parents=True, exist_ok=True)
    if not eng:
        return {"lamp": "GRAY", "msg": "VDF 擷取引擎 %s 不在(_vdf_fetch)· 不擷取" % ENGINE_NAME}
    rows = []
    if args.get("basic") and Path(args["basic"]).exists():
        try:
            rows = json.loads(Path(args["basic"]).read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            rows = []
    tickers = [t for t in (args.get("tickers") or "").split(",") if _BASE.match(t.strip())]
    if not tickers and not rows and args.get("scope"):
        tickers = _tickers_from_scope(Path(args["scope"]))
    today = _dt.date.today()
    windows, fin, allt = plan_windows(rows, today, tickers)
    if not allt:
        return {"lamp": "GRAY", "msg": "沒有代號(基本資料冊 / scope 都沒有 4 碼)· 不擷取"}
    py = fetch_python()
    probe = subprocess.run([py, "-c", "import yfinance, lxml, pandas, pyarrow, duckdb; print('ok')"], capture_output=True, text=True, timeout=120)
    if "ok" not in probe.stdout:
        return {"lamp": "YELLOW", "msg": "擷取環境缺套件(%s)· yfinance / lxml / pandas / pyarrow / duckdb → 交 VCGC 安裝或用 VDF 包的 via_tw_fetch 環境" % py, "tickers": allt}
    to = int(args.get("timeout") or 1800)
    runs, rcs, tails = 0, [], []
    mode = ["bridge"]
    def _run(ts, extra):
        rc, tail = _run_engine(eng, py, ts, extra, vdf, to, standalone=(mode[0] == "standalone"))
        if rc not in (0, 2) and mode[0] == "bridge" and "AllInOne" in eng.name:
            err = (vdf / "last_error.txt").read_text(encoding="utf-8", errors="replace") if (vdf / "last_error.txt").exists() else ""
            if re.search(r"curl_bytes|沒有可用抓取介面|Locked (VIA )?network module|轉接層|VIA transport failed", err) and not re.search(r"PermissionError|DENY|denied", err):
                mode[0] = "standalone"                                         # 介面不相容(非拒絕)→ 操作員授權:v039 獨立模式
                rc, tail = _run_engine(eng, py, ts, extra, vdf, to, standalone=True)
        return rc, tail
    for (s0, e0), ts in windows:                                               # ① ② 日線視窗
        rc, tail = _run(sorted(ts), ["--datasets", "daily", "--start", s0, "--end", e0] + (["--offline"] if args.get("offline") else []))
        runs += 1; rcs.append(rc); tails.append("%s~%s(%d檔) rc%d" % (s0[5:], e0[5:], len(ts), rc))
        if rc not in (0, 2):                                                   # v0103 致命錯(rc 1)第一次就停 · 不重複跑同樣的錯
            tails.append("致命錯 → 停止後續視窗"); break
    skipped_fin = 0
    if not args.get("no_financial"):
        have = _fin_coverage(vdf)                                              # v0104 已落盤 (代號, 年度) → 不再打 MOPS
        for yrs, ts in sorted(fin.items()):                                    # ③ 年度財報 n-3 ~ n(只補缺)
            need_t, need_y = set(), set()
            for t in ts:
                miss = [q for q in yrs if (t, int(q[:4])) not in have]
                if miss:
                    need_t.add(t); need_y.update(miss)
            if not need_t:
                skipped_fin += len(ts); continue
            skipped_fin += len(ts) - len(need_t)
            rc, tail = _run(sorted(need_t), ["--datasets", "financial", "--quarters", ",".join(sorted(need_y))] + (["--offline"] if args.get("offline") else []))
            runs += 1; rcs.append(rc); tails.append("財報 %s~%s(%d檔 · 補缺) rc%d" % (min(need_y)[:4], max(need_y)[:4], len(need_t), rc))
        latest_t = [t for t in allt if (t, today.year) not in have or _latest_stale(vdf, t, today)]
        if latest_t:
            rc, tail = _run(latest_t, ["--datasets", "financial", "--quarters", "latest"] + (["--offline"] if args.get("offline") else []))
            runs += 1; rcs.append(rc); tails.append("財報 latest(%d檔 · 缺或過期) rc%d" % (len(latest_t), rc))
        else:
            tails.append("財報 latest 全部已在 · 略過")
    worst = max(rcs) if rcs else 0
    if not rcs:
        return {"lamp": "GREEN", "msg": "本輪無需擷取(價格視窗無 · 財報已齊 %d 檔)" % skipped_fin, "tickers": allt, "rc": 0}
    lamp = "GREEN" if all(r == 0 for r in rcs) else ("YELLOW" if all(r in (0, 2) for r in rcs) else "RED")
    tails.append(accel_note())                                                 # v0111 加速器回報
    if mode[0] == "standalone" and lamp == "GREEN":
        lamp = "YELLOW"; tails.insert(0, "獨立模式(鎖版網路工具介面不相容 · 依操作員授權 v039 官方 TWSE/TPEx 直連 · 非拒絕)")
    err = ""
    if lamp == "RED" and (vdf / "last_error.txt").exists():
        err = " · 失敗原因(last_error.txt 末 3 行):" + " ⏎ ".join((vdf / "last_error.txt").read_text(encoding="utf-8", errors="replace").strip().splitlines()[-3:])[:300]
    return {"lamp": lamp, "msg": "VDF %s 增量:價格每輪重抓 · 財報只補缺 · 跑 %d 次(日線視窗 %d · 財報年組 %d)· 代號 %d · 財報略過已齊 %d 檔次 · 失敗 %d · %s%s" % (eng.name.replace("VDF_TW_", "").replace(".py", ""), runs, len(windows), len(fin), len(allt), skipped_fin, sum(1 for r in rcs if r not in (0, 2)), " / ".join(tails)[:200], err), "tickers": allt, "rc": worst}


def _read_parquet(glob_root: Path, table: str):
    import pandas as pd
    files = sorted((glob_root / "parquet" / table).glob("ticker=*/year=*/data.parquet"))
    if not files:
        return None
    return pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)


_STD = {"revenue": ("營業收入", "營業收入合計", "Revenue", "Net sales", "Total revenue", "營收"), "operating_income": ("營業利益", "營業利益(損失)", "營業利益（損失）", "Operating income", "Operating profit"),
        "net_income": ("本期淨利", "本期淨利(淨損)", "本期淨利（淨損）", "Net income", "Net profit", "本期淨利（損）歸屬於母公司業主", "淨利（損）歸屬於母公司業主"),
        "eps_diluted": ("稀釋每股盈餘", "稀釋每股盈餘合計", "Diluted EPS"), "eps_basic": ("基本每股盈餘", "基本每股盈餘合計", "Basic EPS"),
        "equity": ("權益總額", "權益總計", "股東權益總額", "歸屬於母公司業主之權益合計", "歸屬於母公司業主之權益", "Total equity"),
        "dps_cash": ("現金股利", "每股現金股利", "Cash dividend")}                           # V2:PER 用稀釋 EPS · ROE 用前後期平均權益 · DPS 遞延規則(VDF v036 無股利資料集 → STATUS 註記)


def _ratios(fa: list, adj_close) -> dict:
    """V2 規範:ROE = 本期淨利 / 平均權益(前期 + 當期)/2 · PER = 還原收盤 / 稀釋 EPS(嚴格)· 全部純小數 · 算不出來寫原因。"""
    by = {}
    for x in fa:
        by.setdefault(x["year"], {})[x["std"]] = x.get("value")
    out = {"roe_avg_equity": {}, "per_diluted": None, "notes": []}
    for y in sorted(by):
        ni, eq, eq0 = by[y].get("net_income"), by[y].get("equity"), (by.get(y - 1) or {}).get("equity")
        if ni is not None and eq is not None and eq0 is not None and (eq + eq0):
            out["roe_avg_equity"][str(y)] = round(ni / ((eq + eq0) / 2.0), 9)
        elif ni is not None and eq is not None:
            out["notes"].append("ROE %d 未算:缺前期權益(需 n-1 年資產負債表)" % y)
    ys = [y for y in sorted(by) if by[y].get("eps_diluted") is not None and (by[y].get("basis") in (None, "ANNUAL") or True)]
    if ys and adj_close:
        y = ys[-1]; eps = by[y]["eps_diluted"]
        if eps:
            out["per_diluted"] = round(float(adj_close) / float(eps), 9); out["per_year"] = y
    elif adj_close:
        out["notes"].append("PER 未算:無稀釋 EPS(嚴格不用基本 EPS)")
    out["notes"].append("DPS 遞延規則未套用:VDF v036 無股利資料集(已宣告未發放應遞延往後一年)")
    return out


def _std_of(account: str) -> str:
    a = str(account or "").replace(" ", "")
    for k, names in _STD.items():
        if any(n.replace(" ", "") in a for n in names):
            return k
    return ""


def _annual(finrows, code: str, rd: str) -> list:
    """年度財報 n-3 ~ n(n = 報告年):ANNUAL(Q4 YTD)優先 · n 年沒有年度就用最新 YTD · 只收四個標準科目(其餘留在 VDF 落盤)."""
    try:
        n = int(str(rd)[:4])
    except ValueError:
        return []
    f = finrows[finrows["ticker"].astype(str) == code]
    if not len(f):
        return []
    out = []
    for y in range(n - 3, n + 1):
        fy = f[f["fiscal_year"].astype(str) == str(y)]
        if not len(fy):
            continue
        ann = fy[fy["basis"].astype(str) == "ANNUAL"]
        pick = ann if len(ann) else fy[fy["basis"].astype(str) == "YTD"]
        if not len(pick):
            continue
        q = pick["quarter"].astype(str).max() if "quarter" in pick else ""
        pick = pick[pick["quarter"].astype(str) == q] if q else pick
        for _, r in pick.iterrows():
            std = _std_of(r.get("account"))
            if std and not any(o["year"] == y and o["std"] == std for o in out):
                out.append({"year": y, "std": std, "account": r.get("account"), "value": float(r["value"]) if r.get("value") not in (None, "") else None, "unit": r.get("unit"), "basis": r.get("basis"), "quarter": r.get("quarter"), "scope": r.get("report_scope"), "statement": r.get("financial_statement")})
    return out


def fill(args: dict) -> dict:
    import pandas as pd
    out = Path(args["out"]); vdf = out / "vdf"
    basic = json.loads(Path(args["basic"]).read_text(encoding="utf-8"))
    uni = _read_parquet(vdf, "tw_universe")
    daily = _read_parquet(vdf, "tw_equity_daily")
    finrows = _read_parquet(vdf, "tw_financial")
    if uni is None and daily is None:
        return {"lamp": "GRAY", "msg": "VDF 落盤沒有 tw_universe / tw_equity_daily(先 --fetch)"}
    uni_map = {}
    if uni is not None:
        for _, u in uni.iterrows():
            uni_map[str(u.get("ticker"))] = {"name": u.get("name"), "market": u.get("market")}
    if daily is not None:
        daily["date"] = pd.to_datetime(daily["date"]).dt.date
    per_ticker, per_file, n_ok, n_miss = {}, {}, 0, 0
    for row in basic:
        t = str(row.get("TICKER") or "").strip()
        m = _BASE.match(t) or re.match(r"^([1-9]\d{3})(?:\.TWO?|\s+TT)$", t)
        if not m:
            per_file[row.get("FILENAME")] = {"status": "MISSING", "reason": "基本資料冊代號不是 4 碼"}; n_miss += 1
            continue
        code = m.group(1)
        d = daily[daily["ticker"].astype(str) == code].sort_values("date") if daily is not None else None
        info = dict(forms(code, (uni_map.get(code) or {}).get("market") or ((d["market"].iloc[-1]) if d is not None and len(d) and "market" in d else "")))
        info["name"] = (uni_map.get(code) or {}).get("name") or ((d["name"].iloc[-1]) if d is not None and len(d) and "name" in d else "")
        rec = {"ticker": code, "name": info.get("name") or "", "yfinance_ticker": info.get("yfinance_ticker", ""), "bloomberg_ticker": info.get("bloomberg_ticker", "")}
        if d is None or not len(d):
            rec.update(status="MISSING", reason="VDF 沒有此代號的日資料")
            per_file[row.get("FILENAME")] = rec; n_miss += 1
            continue
        adj = d[d["adj_close"].notna()] if "adj_close" in d else d.iloc[0:0]
        if len(adj):
            last = adj.iloc[-1]
            rec.update(adj_close=float(last["adj_close"]), adj_close_date=str(last["date"]), close_latest=float(last["close"]) if pd.notna(last.get("close")) else None)
        else:
            rec.update(adj_close=None, adj_close_date="", adj_status="MISSING(Yahoo 還原價缺或核對 MISMATCH · 不拿 Close 冒充)")
        rd = str(row.get("REPORT_DATE") or "")
        rec["report_date"] = rd
        try:
            rdd = _dt.date.fromisoformat(rd)
            before = adj[adj["date"] < rdd]
            if len(before):
                b = before.iloc[-1]
                fac = float(b["adj_close"]) / float(b["close"]) if pd.notna(b.get("close")) and float(b["close"]) else None
                rec.update(adj_close_before_report=float(b["adj_close"]), adj_close_before_report_date=str(b["date"]), adjustment_factor_report=fac)
            else:
                rec.update(adj_close_before_report=None, adj_close_before_report_date="", adjustment_factor_report=None, before_status="MISSING(報告日前沒有日資料 · 需 --start 回補)")
        except ValueError:
            rec.update(adj_close_before_report=None, adjustment_factor_report=None, before_status="MISSING(報告日格式不是 YYYY-MM-DD)")
        tp = row.get("TARGET_PRICE")
        try:
            tpv = float(str(tp).replace(",", "")) if tp not in (None, "") else None
        except ValueError:
            tpv = None
        fac = rec.get("adjustment_factor_report")
        if tpv is not None and fac:
            rec["target_price_adj"] = round(tpv * fac, 2)
            if rec.get("adj_close"):
                rec["upside_adj"] = round(rec["target_price_adj"] / rec["adj_close"] - 1, 9)          # V2 純小數
                rec["upside_pct_adj"] = round(rec["upside_adj"] * 100, 1)
        rec["financial_annual"] = _annual(finrows, code, rd) if finrows is not None else []
        rec["ratios"] = _ratios(rec["financial_annual"], rec.get("adj_close"))
        rec["status"] = "OK" if rec.get("adj_close") is not None else "PARTIAL"
        per_file[row.get("FILENAME")] = rec
        per_ticker[code] = {k: rec[k] for k in ("name", "yfinance_ticker", "bloomberg_ticker", "adj_close", "adj_close_date") if k in rec}
        n_ok += int(rec["status"] == "OK")
    res = {"version": VERSION, "ts": _dt.datetime.now().isoformat(timespec="seconds"), "engine": ENGINE_NAME, "rule": "TARGET_PRICE(ADJ) = TARGET_PRICE × 報告日前最後交易日的 adj_close/close · UPSIDE_PCT(ADJ) = TARGET_PRICE(ADJ)/最新 ADJ_CLOSE - 1 · 缺就 MISSING 不猜",
           "per_file": per_file, "per_ticker": per_ticker}
    out.mkdir(parents=True, exist_ok=True)
    (out / "VRN2_Market_latest.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"lamp": "GREEN" if n_ok and not n_miss else ("YELLOW" if n_ok else "RED"), "msg": "市場資料填值 · 代號 %d · 完整 %d · 部分 %d · 缺 %d → %s" % (len(per_ticker), n_ok, len(per_file) - n_ok - n_miss, n_miss, out / "VRN2_Market_latest.json")}


def selftest(argv: list) -> int:
    ok = 0
    tt = [ticker_type(x)[0] for x in ("2330", "0050", "00878", "00981A", "00679B", "00631L", "00632R", "00635U", "00701T", "0050.TW", "00631L TT", "123")]
    e = tt == ["STOCK", "ETF_EQUITY_PASSIVE", "ETF_EQUITY_PASSIVE", "ETF_EQUITY_ACTIVE", "ETF_BOND_PASSIVE", "ETF_LEVERAGED", "ETF_INVERSE", "ETF_FUTURES", "ETF_BALANCED", "ETF_EQUITY_PASSIVE", "ETF_LEVERAGED", ""]
    print("  [%s] 代碼分類九類(Regex v0103)%s" % ("OK" if e else "FAIL", tt)); ok += int(e)
    f = forms("2330", "TWSE"); g = forms("6488", "TPEX")
    a = f["yfinance_ticker"] == "2330.TW" and f["bloomberg_ticker"] == "2330 TT" and g["yfinance_ticker"] == "6488.TWO" and forms("0050", "TWSE") == {}
    print("  [%s] 三碼規則 = VDF def_identity = VRN2 Regex v0101(TWSE .TW · TPEX .TWO · TT · ETF 不在範圍)" % ("OK" if a else "FAIL")); ok += int(a)
    import tempfile
    import pandas as pd
    td = Path(tempfile.mkdtemp()); vdf = td / "vdf"
    (vdf / "parquet" / "tw_universe" / "ticker=2330" / "year=2026").mkdir(parents=True)
    pd.DataFrame([{"ticker": "2330", "name": "台積電", "market": "TWSE"}]).to_parquet(vdf / "parquet" / "tw_universe" / "ticker=2330" / "year=2026" / "data.parquet")
    (vdf / "parquet" / "tw_equity_daily" / "ticker=2330" / "year=2026").mkdir(parents=True)
    pd.DataFrame([{"date": pd.Timestamp("2026-05-18"), "ticker": "2330", "name": "台積電", "market": "TWSE", "close": 1000.0, "adj_close": 980.0},
                  {"date": pd.Timestamp("2026-05-20"), "ticker": "2330", "name": "台積電", "market": "TWSE", "close": 1010.0, "adj_close": 1010.0}]).to_parquet(vdf / "parquet" / "tw_equity_daily" / "ticker=2330" / "year=2026" / "data.parquet")
    bp = td / "basic.json"
    bp.write_text(json.dumps([{"FILENAME": "x.pdf", "TICKER": "2330", "REPORT_DATE": "2026-05-19", "TARGET_PRICE": "1,200"}, {"FILENAME": "y.pdf", "TICKER": "9999", "REPORT_DATE": "2026-05-19", "TARGET_PRICE": "10"}]), encoding="utf-8")
    r = fill({"basic": str(bp), "out": str(td)})
    m = json.loads((td / "VRN2_Market_latest.json").read_text(encoding="utf-8"))["per_file"]
    x = m["x.pdf"]
    b = x["name"] == "台積電" and x["yfinance_ticker"] == "2330.TW" and x["adj_close"] == 1010.0 and x["adj_close_before_report"] == 980.0 and abs(x["target_price_adj"] - 1176.0) < 0.01 and abs(x["upside_pct_adj"] - 16.4) < 0.1 and m["y.pdf"]["status"] == "MISSING"
    print("  [%s] 填值:NAME / .TW / 最新 ADJ 1010 / 報告前 ADJ 980(因子 0.98)/ TP(ADJ) %s / 上漲 %s%% / 無資料代號 MISSING" % ("OK" if b else "FAIL", x.get("target_price_adj"), x.get("upside_pct_adj"))); ok += int(b)
    c = _tickers_from_scope(Path(tempfile.mkdtemp())) == []
    sc = Path(tempfile.mkdtemp()); (sc / "20250819兆豐個股報告-泓德能源(6873).pdf").write_bytes(b"x"); (sc / "GS-2317 20251205.pdf").write_bytes(b"x")
    c = _tickers_from_scope(sc) == ["6873", "2317"]
    print("  [%s] 檔名前四碼原則取代號 %s" % ("OK" if c else "FAIL", _tickers_from_scope(sc))); ok += int(c)
    rows = [{"TICKER": "2330", "REPORT_DATE": "2025-08-19"}, {"TICKER": "2317", "REPORT_DATE": "2025-08-22"}, {"TICKER": "6488", "REPORT_DATE": "2023-10-11"}]
    w, fq, allt = plan_windows(rows, _dt.date(2026, 10, 27))
    g = len(w) == 3 and w[0][0] == ("2023-10-04", "2023-10-10") and w[1][0] == ("2025-08-12", "2025-08-21") and w[1][1] == {"2330", "2317"} and w[2][0] == ("2026-10-20", "2026-10-27") and fq == {("2022Q4", "2023Q4", "2024Q4", "2025Q4"): {"2330", "2317"}, ("2020Q4", "2021Q4", "2022Q4", "2023Q4"): {"6488"}}
    print("  [%s] 必要日期規劃:日線視窗 %d(相近報告日合併)· 財報年組 %s" % ("OK" if g else "FAIL", len(w), {k[0] + ".." + k[-1]: sorted(v) for k, v in fq.items()})); ok += int(g)
    (vdf / "parquet" / "tw_financial" / "ticker=2330" / "year=2025").mkdir(parents=True)
    pd.DataFrame([{"ticker": "2330", "fiscal_year": 2025, "quarter": "Q4", "basis": "ANNUAL", "financial_statement": "INCOME_STATEMENT", "account": "營業收入合計", "value": 3000000.0, "unit": "TWD_THOUSAND", "report_scope": "CONSOLIDATED"},
                  {"ticker": "2330", "fiscal_year": 2025, "quarter": "Q4", "basis": "ANNUAL", "financial_statement": "INCOME_STATEMENT", "account": "基本每股盈餘", "value": 45.25, "unit": "TWD_PER_SHARE", "report_scope": "CONSOLIDATED"},
                  {"ticker": "2330", "fiscal_year": 2026, "quarter": "Q2", "basis": "YTD", "financial_statement": "INCOME_STATEMENT", "account": "營業收入合計", "value": 1700000.0, "unit": "TWD_THOUSAND", "report_scope": "CONSOLIDATED"}]).to_parquet(vdf / "parquet" / "tw_financial" / "ticker=2330" / "year=2025" / "data.parquet")
    r = fill({"basic": str(bp), "out": str(td)})
    fa = json.loads((td / "VRN2_Market_latest.json").read_text(encoding="utf-8"))["per_file"]["x.pdf"].get("financial_annual") or []
    rt = _ratios([{"year": 2024, "std": "equity", "value": 4000.0}, {"year": 2025, "std": "equity", "value": 5000.0}, {"year": 2025, "std": "net_income", "value": 900.0}, {"year": 2025, "std": "eps_diluted", "value": 45.0}], 1010.0)
    i2 = abs(rt["roe_avg_equity"]["2025"] - 0.2) < 1e-9 and abs(rt["per_diluted"] - 1010.0 / 45.0) < 1e-9
    print("  [%s] V2 比率:ROE 平均權益 900/((4000+5000)/2)=%s · PER 稀釋 1010/45=%s(純小數)" % ("OK" if i2 else "FAIL", rt["roe_avg_equity"].get("2025"), rt["per_diluted"])); ok += int(i2)
    h = [(x["year"], x["std"], x["basis"]) for x in fa] == [(2025, "revenue", "ANNUAL"), (2025, "eps_basic", "ANNUAL"), (2026, "revenue", "YTD")]
    print("  [%s] 年度財報 n-3~n:2025 ANNUAL 營收 / EPS · 2026 用最新 YTD %s" % ("OK" if h else "FAIL", [(x["year"], x["std"], x["basis"]) for x in fa])); ok += int(h)
    cov = _fin_coverage(vdf)
    j = cov == {("2330", 2025)} and _latest_stale(vdf, "2330", _dt.date(2026, 10, 27)) is True and _latest_stale(vdf, "2330", _dt.date(2025, 10, 27)) is False
    print("  [%s] 增量:已落盤 (代號, 年度) %s → 不再打 MOPS · latest 過期判斷(2026 年檔不在 → 要抓 · 2025 檔在且未過期限 → 略過)" % ("OK" if j else "FAIL", sorted(cov))); ok += int(j)
    fake = Path(tempfile.mkdtemp()) / "movies-dataset" / "VeritasIntelligenceAnalytics"
    (fake / "supportive modules" / "registry").mkdir(parents=True); (fake / "supportive modules" / "network").mkdir(parents=True)
    (fake / "supportive modules" / "network" / "VeritasAegisNexus_v1652.py").write_text("def curl_bytes(url, **k):\n    return b''\n", encoding="utf-8")
    import hashlib as _h
    sha = _h.sha256((fake / "supportive modules" / "network" / "VeritasAegisNexus_v1652.py").read_bytes()).hexdigest()
    (fake / "supportive modules" / "registry" / "VIA_ToolVersion_Lock_v0100.json").write_text(json.dumps({"net": {"path": "VeritasIntelligenceAnalytics\\supportive modules\\network\\VeritasAegisNexus_v1652.py".replace("\\", os.sep), "sha256": sha}}), encoding="utf-8")
    os.environ["TEMP"] = str(fake.parent.parent / "tmp"); (fake.parent.parent / "tmp").mkdir(exist_ok=True)
    (fake / "supportive modules" / "network" / "VeritasAegisNexus_v1652.py").write_bytes(b"def curl_bytes(url, **k):\r\n    return b''\r\n")   # 工作樹 CRLF · 鎖冊雜湊是 LF 版
    shim, note = shim_root(fake)
    k = shim is not None and "只差行尾" in note and json.loads((shim / "supportive modules" / "registry" / "VIA_ToolVersion_Lock_v0100.json").read_text(encoding="utf-8"))["net"]["path"].endswith("VeritasAegisNexus_v1652.py") and Path(json.loads((shim / "supportive modules" / "registry" / "VIA_ToolVersion_Lock_v0100.json").read_text(encoding="utf-8"))["net"]["path"]).is_file()
    print("  [%s] 橋接根:鎖冊 path 相對 movies-dataset → 絕對路徑 · CRLF 只差行尾 → 正規化雜湊相同 · %s" % ("OK" if k else "FAIL", note[-70:])); ok += int(k)
    (fake / "supportive modules" / "network" / "VeritasAegisNexus_v1652.py").write_bytes(b"def curl_bytes(url, **k):\n    return b'changed'\n")
    shim2, note2 = shim_root(fake)
    k2 = shim2 is None and "鎖冊過期" in note2
    print("  [%s] 真的換版 → 不繞過 · %s" % ("OK" if k2 else "FAIL", note2[:60])); ok += int(k2)
    (fake / "supportive modules" / "network" / "VeritasAegisNexus_v1652.py").write_bytes(b"import types\r\nclass HttpConfig:\r\n    def __init__(self, timeout=30.0, max_retries=2): self.timeout=timeout\r\nclass ResilientHTTPClient:\r\n    def __init__(self, config=None, proxy_pool=None): self.config=config\r\n    def request(self, method, url, **kw):\r\n        return types.SimpleNamespace(status_code=200, content=b'<html>ok</html>', headers={'Content-Type':'text/html'}, url=url, allow=kw.get('allow_redirects'))\r\nclass _S:\r\n    allowed=True; reason=''; headers={}\r\ndef get_scraping_strategy(url):\r\n    s=_S(); s.allowed='mops' not in url; s.reason='robots' if 'mops' in url else ''; return s\r\n")   # 仿 v1652 介面(ResilientHTTPClient / HttpConfig / 合規)
    sha3 = _h.sha256((fake / "supportive modules" / "network" / "VeritasAegisNexus_v1652.py").read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    (fake / "supportive modules" / "registry" / "VIA_ToolVersion_Lock_v0100.json").write_text(json.dumps({"net": {"path": "VeritasIntelligenceAnalytics/supportive modules/network/VeritasAegisNexus_v1652.py".replace("/", os.sep), "sha256": sha3}}), encoding="utf-8")
    shim, note = shim_root(fake)
    ad = shim / "supportive modules" / "network" / "VIA_NetBridge_Adapter_v0100.py"
    r = subprocess.run([sys.executable, "-W", "ignore", "-c", "import importlib.util,sys,json;sp=importlib.util.spec_from_file_location('a',sys.argv[1]);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);d=m.curl_bytes('https://www.twse.com.tw/x',timeout=5,follow=False,headers={});e=m.curl_bytes('https://mops.twse.com.tw/x',timeout=5,follow=False,headers={});print(m.CHOSEN, d['state'], d['http_status'], d['data'], d['final_url'], e['state'], e['reason'])", str(ad)], capture_output=True, text=True, timeout=60)
    adp = "ResilientHTTPClient OK 200 b'<html>ok</html>' https://www.twse.com.tw/x DENY" in r.stdout
    print("  [%s] 轉接模組:ResilientHTTPClient.request(allow_redirects=False)→ OK 200 · 合規 allowed=False → DENY 照傳 · %s" % ("OK" if adp else "FAIL", (r.stdout + r.stderr).strip()[-90:])); ok += int(adp)
    eng36 = sorted((HERE / "_vdf_fetch").glob("VDF_TW_DataFetchEngine_v[0-9][0-9][0-9].py"))
    if k and eng36:                                                              # 橋偵測用 v036 測(同一個 def_via_bridges · v039 非主程式匯入會先檢查函式庫)
        r = subprocess.run([sys.executable, "-W", "ignore", "-c", "import importlib.util,sys;sp=importlib.util.spec_from_file_location('e',sys.argv[1]);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);b=m.def_via_bridges(sys.argv[2]);print(b['network'], b['module'].curl_bytes('https://www.twse.com.tw/x', timeout=5, follow=False, headers={})['state'])", str(eng36[-1]), str(shim)], capture_output=True, text=True, timeout=120)
        l = "LOCKED_VIA OK" in r.stdout
        print("  [%s] 引擎用橋接根偵測 → %s(經轉接模組取得 OK)" % ("OK" if l else "FAIL", (r.stdout + r.stderr).strip()[-80:])); ok += int(l)
    else:
        ok += 1
    eng = engine_path()
    print("  [%s] VDF 引擎在 %s" % ("OK" if eng else "FAIL", eng)); ok += int(bool(eng))
    n = 13
    if eng and "--with-vdf-tests" in argv:
        t = eng.parent / "test_VDF_TW_DataFetchEngine_v036.py"
        r2 = subprocess.run([sys.executable, "-W", "ignore", str(t)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600, cwd=str(eng.parent))
        d = r2.returncode == 0 and "OK" in r2.stderr + r2.stdout
        print("  [%s] VDF 引擎離線回歸 28 項 rc %d" % ("OK" if d else "FAIL", r2.returncode)); ok += int(d); n += 1
    print("[計] VRN2_MarketFetch %s 自測 %d/%d · %s" % (VERSION, ok, n, "PASS" if ok == n else "FAIL"))
    return 0 if ok == n else 1


def doctor(args: dict) -> int:
    eng = engine_path(); py = fetch_python()
    out = Path(args["out"]); vdf = out / "vdf"
    print("[計] 診斷 · Python %s · 引擎 %s · 擷取 Python %s" % (sys.version.split()[0], eng or "不在", py))
    if not eng:
        return 1
    r = subprocess.run([py, "-c", "import sys,py_compile;py_compile.compile(sys.argv[1],doraise=True);print('編譯 OK',sys.version.split()[0])", str(eng)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    print("[計]   編譯 → %s" % ((r.stdout + r.stderr).strip().splitlines() or ["?"])[-1][:200])
    shim, note = shim_root()
    print("[計]   橋接根 → %s" % note[:260])
    probe = "import importlib.util,sys,json;sp=importlib.util.spec_from_file_location('e',sys.argv[1]);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);b=m.def_via_bridges(sys.argv[2]);print('匯入 OK · via_root',sys.argv[2],'· accel',b['accel'],'· network',b['network'])"
    r = subprocess.run([py, "-W", "ignore", "-c", probe, str(eng), str(shim or via_root())], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180, cwd=str(eng.parent))
    for l in (r.stdout + r.stderr).strip().splitlines()[-4:]:
        print("[計]   橋偵測 → %s" % l[:220])
    r = subprocess.run([py, "-c", "import yfinance, lxml, pandas, pyarrow, duckdb; print('套件 ok', yfinance.__version__, pandas.__version__)"], capture_output=True, text=True, timeout=120)
    print("[計]   套件 → %s" % ((r.stdout + r.stderr).strip().splitlines() or ["?"])[-1][:200])
    if shim:                                                                   # v0107 真模組介面探測
        ad = shim / "supportive modules" / "network" / "VIA_NetBridge_Adapter_v0100.py"
        if ad.exists():
            r = subprocess.run([py, "-W", "ignore", "-c", "import importlib.util,sys;sp=importlib.util.spec_from_file_location('a',sys.argv[1]);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);print('轉接 →', m.CHOSEN, '· 真模組可呼叫', [n for n in dir(m._m) if not n.startswith('_') and callable(getattr(m._m, n))][:25])", str(ad)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
            for l in (r.stdout + r.stderr).strip().splitlines()[-2:]:
                print("[計]   網路工具介面 → %s" % l[:300])
    le = vdf / "last_error.txt"
    if le.exists():
        print("[計]   最近失敗(last_error.txt):")
        for l in le.read_text(encoding="utf-8", errors="replace").strip().splitlines()[-8:]:
            print("[計]     " + l[:220])
    return 0


def main(argv: list) -> int:
    def opt(k, d=None):
        return argv[argv.index(k) + 1] if k in argv and argv.index(k) + 1 < len(argv) else d
    if "--selftest" in argv:
        return selftest(argv)
    a = {"basic": opt("--basic"), "tickers": opt("--tickers", ""), "out": opt("--out", str(HERE.parent.parent / "VIA_Reports" / "vrn2" / "market")), "scope": opt("--scope"), "timeout": opt("--timeout", "1800"), "offline": "--offline" in argv, "no_financial": "--no-financial" in argv}
    if "--doctor" in argv:
        return doctor(a)
    if "--fetch" in argv:
        r = fetch(a); print("[計] 市場擷取 · %s · %s" % (r["lamp"], r["msg"]), flush=True); return 0 if r["lamp"] != "RED" else 1
    if "--fill" in argv:
        if not a["basic"]:
            print("[RED] --fill 需要 --basic"); return 2
        r = fill(a); print("[計] 市場填值 · %s · %s" % (r["lamp"], r["msg"]), flush=True); return 0 if r["lamp"] != "RED" else 1
    print(__doc__); return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
