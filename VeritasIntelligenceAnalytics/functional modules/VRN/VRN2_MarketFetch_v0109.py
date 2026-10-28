#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111] 市場排程沿用宿主加速器；鎖版網路由轉接契約呼叫。
# [VIA:ACCEL-BRIDGE:v0111]
"""VRN2_MarketFetch v0109：沿用 v0107 增量視窗；全年財報、嚴格轉接及證據側錄。
鎖冊存在而無法驗證或轉接時停止。鎖冊不存在才可使用 VDF 的獨立模式。
--fetch / --fill / --doctor 介面不變；財務契約自測由新版啟動器整合執行。
"""
from __future__ import annotations

import datetime as _dt
import json
import os
import re
import subprocess
import sys
from pathlib import Path

VERSION = "v0109"
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


def hasattr_curl_bytes(p: Path) -> bool:
    try:
        return "def curl_bytes" in p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False


ADAPTER = '# [VIA:ACCEL-BRIDGE:v0111]\n"""鎖版網路工具契約轉接：雜湊驗證、單次呼叫、顯式重新導向控制。"""\nimport hashlib, importlib.util, inspect, sys\nfrom pathlib import Path\nREAL=Path(__REAL_LITERAL__)\nREAL_SHA="__SHA__"\nORDER=("curl_bytes","fetch_bytes","http_get","get_bytes","fetch","get","request","curl")\nraw=REAL.read_bytes()\nif REAL_SHA not in (hashlib.sha256(raw).hexdigest(),hashlib.sha256(raw.replace(b"\\r\\n",b"\\n")).hexdigest()):\n    raise ValueError("鎖版網路工具雜湊不符")\nsp=importlib.util.spec_from_file_location("vrn2_locked_network",REAL)\n_m=importlib.util.module_from_spec(sp);sys.modules[sp.name]=_m;sp.loader.exec_module(_m)\nCHOSEN=next((n for n in ORDER if callable(getattr(_m,n,None))),None)\ndef curl_bytes(url, timeout=35, follow=False, headers=None, **kw):\n    if not CHOSEN: raise RuntimeError("鎖版網路工具沒有已知可用抓取介面")\n    fn=getattr(_m,CHOSEN);params=inspect.signature(fn).parameters\n    values={"url":url,"timeout":timeout,"headers":headers or {}}\n    follow_key=next((n for n in ("follow","allow_redirects","follow_redirects") if n in params),None)\n    if not follow_key: raise RuntimeError("鎖版工具未宣告重新導向控制；契約不相容，請提供正式介面")\n    values[follow_key]=follow\n    if CHOSEN=="request" and "method" in params: values["method"]="GET"\n    supplied={k:v for k,v in values.items() if k in params or any(p.kind==p.VAR_KEYWORD for p in params.values())}\n    inspect.signature(fn).bind(**supplied)\n    result=fn(**supplied) # TypeError 或 PermissionError 直接上傳，不重試其他參數/傳輸\n    if not isinstance(result,dict):\n        raise RuntimeError("鎖版介面須提供含 state/http_status 的字典，不推測傳輸成功")\n    d=dict(result);state=str(d.get("state") or "").upper()\n    if state in ("DENY","DENIED","BLOCKED") or str(d.get("http_status",d.get("status_code"))) in ("401","403"):\n        raise PermissionError("鎖版網路工具 DENY")\n    if state!="OK": raise RuntimeError("VIA transport failed: "+state)\n    status=d.get("http_status",d.get("status_code"))\n    if status is None: raise RuntimeError("鎖版回應缺 HTTP 狀態")\n    d["http_status"]=int(status)\n    if d["http_status"]>=400: raise RuntimeError("HTTP "+str(status))\n    data=d.get("data",d.get("body",d.get("content")))\n    if isinstance(data,str): data=data.encode("utf-8")\n    if not isinstance(data,(bytes,bytearray)): raise RuntimeError("鎖版回應缺位元組資料")\n    d["data"]=bytes(data);d.setdefault("headers",{})\n    return d\n'


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
    if not want:
        return None, "鎖冊缺 sha256；交 VCGC 重鎖"
    if want and actual != want:
        if norm == want:
            spec2[key]["sha256"] = actual; hash_note = " · 雜湊只差行尾 CRLF(正規化後與鎖冊相同)→ 橋接鎖冊用實際位元組雜湊"
        else:
            newest = sorted(hit.parent.glob("VeritasAegisNexus_v*.py"))
            return None, "鎖冊過期:%s 內容與鎖冊雜湊不同(正規化後仍不同 · 不繞過)· network 夾最新 %s · 交 VCGC 重鎖後 ⑥e 才會通" % (hit.name, newest[-1].name if newest else "?")
    if not hasattr_curl_bytes(hit):                                            # v0107 真模組沒有 curl_bytes → 轉接模組
        netd = shim / "supportive modules" / "network"; netd.mkdir(parents=True, exist_ok=True)
        ad = netd / "VIA_NetBridge_Adapter_v0101.py"
        ad.write_text(ADAPTER.replace("__REAL_LITERAL__", repr(str(hit.resolve()))).replace("__SHA__", want or norm), encoding="utf-8")
        spec2[key]["path"] = str(ad.resolve()); spec2[key]["sha256"] = _h.sha256(ad.read_bytes()).hexdigest()
        spec2[key]["adapter_of"] = {"path": str(hit.resolve()), "sha256_normalized": norm, "lock_sha256": want}
        hash_note += " · 真模組無 curl_bytes → 轉接模組(介面轉換 · 雜湊照驗 · DENY 照傳)"
    (reg / "VIA_ToolVersion_Lock_v0100.json").write_text(json.dumps(spec2, ensure_ascii=False, indent=1), encoding="utf-8")
    acc = support / "VIA_SuperAccel_Module.py"
    if acc.is_file():
        (shim / "supportive modules" / "VIA_SuperAccel_Module.py").write_text("# [VIA:ACCEL-BRIDGE:v0111] 轉接 → 真實加速器\nimport sys as _s; _p = %r\nif _p not in _s.path: _s.path.insert(0, _p)\nfrom VIA_SuperAccel_Module import *  # noqa: F401,F403\n" % str(support), encoding="utf-8")
    return shim, "橋接根 %s · network → %s(sha %s)%s" % (shim, hit.name, (entry.get("sha256") or "")[:12], hash_note)


def _run_engine(eng: Path, py: str, tickers: list, extra: list, vdf: Path, timeout: int, standalone: bool = False) -> tuple:
    if not (via_root()/"supportive modules"/"registry"/"VIA_ToolVersion_Lock_v0100.json").is_file() and "--offline" not in extra:
        raise PermissionError("出網前缺鎖版網路工具；停止，不走獨立 urllib")
    shim, note = (None, "") if standalone else shim_root()
    lock_exists=(via_root()/"supportive modules"/"registry"/"VIA_ToolVersion_Lock_v0100.json").exists()
    if lock_exists and (standalone or shim is None):
        raise PermissionError("鎖冊存在但無有效橋接；停止，不以獨立連線繞過: "+note)
    via = [] if standalone else (["--via-root", str(shim)] if shim else ([] if "AllInOne" in eng.name else []))
    runner=HERE/"VRN2_InstrumentedRunner_v0100.py"
    if not runner.is_file():raise RuntimeError("缺 AST 動詞稽核外掛；不執行未覆蓋的外部引擎")
    import hashlib
    prefix=[py,"-W","ignore",str(runner),"--engine",str(eng),"--sha256",hashlib.sha256(eng.read_bytes()).hexdigest(),"--report",str(vdf/"VRN2_VerbCoverage_latest.json"),"--"]
    cmd = prefix+[ "--tickers", ",".join(tickers), "--output", str(vdf)] + extra + via
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout, cwd=str(eng.parent))
        lines = (r.stdout + r.stderr).strip().splitlines()
        if r.returncode not in (0, 2):                                         # v0103 失敗:完整尾端落盤
            try:
                (vdf / "last_error.txt").write_text("CMD: %s\n\n%s" % (" ".join(cmd), "\n".join(lines[-40:])), encoding="utf-8")
            except Exception:  # noqa: BLE001
                pass
        return r.returncode, lines[-6:]
    except subprocess.TimeoutExpired:
        return 124, ["逾時"]


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
    """實際讀取年度內容；目錄存在不等於全年三表完整。"""
    data=_read_parquet(vdf,"tw_financial")
    if data is None: return set()
    out=set()
    for (ticker,year),group in data.groupby(["ticker","fiscal_year"]):
        mask=(group["basis"].eq("ANNUAL") | (group["basis"].eq("YTD") & group["quarter"].astype(str).isin(["4","4.0"])) | (group["basis"].eq("POINT") & group["date"].astype(str).str[:10].str.endswith("12-31")))
        valid=group[mask & group["value"].notna()]
        statements=set(valid["financial_statement"].astype(str))
        if {"BALANCE_SHEET","INCOME_STATEMENT","CASH_FLOW"}.issubset(statements):out.add((str(ticker),int(year)))
    return out


def _latest_stale(vdf: Path, ticker: str, today: _dt.date) -> bool:
    """來源快取 TTL 是取資料策略，不能拿固定法定期限推斷公司已公告。"""
    frame=_read_parquet(vdf,"tw_financial")
    if frame is None:return True
    rows=frame[frame["ticker"].astype(str)==ticker]
    if rows.empty or "fetched_at" not in rows:return True
    import pandas as pd
    times=pd.to_datetime(rows["fetched_at"],errors="coerce",utc=True).dropna()
    if times.empty:return True
    age=(pd.Timestamp.now(tz="UTC")-times.max()).total_seconds()
    return not (0<=age<24*3600)


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
        if rc not in (0, 2) and mode[0] == "bridge" and "AllInOne" in eng.name and not (via_root()/"supportive modules"/"registry"/"VIA_ToolVersion_Lock_v0100.json").exists():
            err = (vdf / "last_error.txt").read_text(encoding="utf-8", errors="replace") if (vdf / "last_error.txt").exists() else ""
            if re.search(r"curl_bytes|沒有可用抓取介面|Locked (VIA )?network module|轉接層|VIA transport failed", err) and not re.search(r"PermissionError|DENY|denied", err):
                mode[0] = "standalone"                                         # 介面不相容(非拒絕)→ 操作員授權:v039 獨立模式
                rc, tail = _run_engine(eng, py, ts, extra, vdf, to, standalone=True)
        return rc, tail
    coverage_file=out/"VRN2_FetchCoverage_v0100.json"
    coverage=json.loads(coverage_file.read_text(encoding="utf-8")) if coverage_file.is_file() else {}
    for (s0, e0), ts in windows:                                               # ① ② 日線視窗
        window_key="|".join([s0,e0,",".join(sorted(ts))])
        if coverage.get(window_key)==today.isoformat():
            tails.append("已核對完成視窗快取 "+s0+"/"+e0);continue
        rc, tail = _run(sorted(ts), ["--datasets", "daily", "--start", s0, "--end", e0] + (["--offline"] if args.get("offline") else []))
        if rc==0:
            coverage[window_key]=today.isoformat()
            coverage_file.write_text(json.dumps(coverage),encoding="utf-8")
        runs += 1; rcs.append(rc); tails.append("%s~%s(%d檔) rc%d" % (s0[5:], e0[5:], len(ts), rc))
        if rc not in (0, 2):                                                   # v0103 致命錯(rc 1)第一次就停 · 不重複跑同樣的錯
            tails.append("致命錯 → 停止後續視窗"); break
    if any(r not in (0,2) for r in rcs):
        return {"lamp":"RED","msg":"市場擷取致命錯已停止，未繼續重試財報："+" / ".join(tails),"tickers":allt,"rc":max(rcs)}
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
        latest_t = [t for t in allt if _latest_stale(vdf, t, today)]
        if latest_t:
            rc, tail = _run(latest_t, ["--datasets", "financial", "--quarters", "latest"] + (["--offline"] if args.get("offline") else []))
            runs += 1; rcs.append(rc); tails.append("財報 latest(%d檔 · 缺或過期) rc%d" % (len(latest_t), rc))
        else:
            tails.append("財報 latest 全部已在 · 略過")
    worst = max(rcs) if rcs else 0
    if not rcs:
        return {"lamp": "GREEN", "msg": "本輪無需擷取(價格視窗無 · 財報已齊 %d 檔)" % skipped_fin, "tickers": allt, "rc": 0}
    lamp = "GREEN" if all(r == 0 for r in rcs) else ("YELLOW" if all(r in (0, 2) for r in rcs) else "RED")
    if mode[0] == "standalone" and lamp == "GREEN":
        lamp = "YELLOW"; tails.insert(0, "獨立模式(鎖版網路工具介面不相容 · 依操作員授權 v039 官方 TWSE/TPEx 直連 · 非拒絕)")
    err = ""
    if lamp == "RED" and (vdf / "last_error.txt").exists():
        err = " · 失敗原因(last_error.txt 末 3 行):" + " ⏎ ".join((vdf / "last_error.txt").read_text(encoding="utf-8", errors="replace").strip().splitlines()[-3:])[:300]
    return {"lamp": lamp, "msg": "VDF %s 增量:價格每輪重抓 · 財報只補缺 · 跑 %d 次(日線視窗 %d · 財報年組 %d)· 代號 %d · 財報略過已齊 %d 檔次 · 失敗 %d · %s%s" % (eng.name.replace("VDF_TW_", "").replace(".py", ""), runs, len(windows), len(fin), len(allt), skipped_fin, sum(1 for r in rcs if r not in (0, 2)), " / ".join(tails)[:200], err), "tickers": allt, "rc": worst}


def _read_parquet(glob_root: Path, table: str):
    import pandas as pd
    files=sorted((glob_root/"parquet"/table).glob("ticker=*/year=*/data.parquet"))
    if not files:
        direct=glob_root/(table+".parquet")
        files=[direct] if direct.is_file() else []
    if not files: return None
    return pd.concat([pd.read_parquet(f) for f in files],ignore_index=True)



_STD = {"revenue": ("營業收入", "營業收入合計", "Revenue", "Net sales", "Total revenue", "營收"), "operating_income": ("營業利益", "營業利益(損失)", "營業利益（損失）", "Operating income", "Operating profit"),
        "net_income": ("本期淨利", "本期淨利(淨損)", "本期淨利（淨損）", "Net income", "Net profit", "本期淨利（損）歸屬於母公司業主", "淨利（損）歸屬於母公司業主"),
        "eps_diluted": ("稀釋每股盈餘", "稀釋每股盈餘合計", "Diluted EPS"), "eps_basic": ("基本每股盈餘", "基本每股盈餘合計", "Basic EPS"),
        "equity": ("權益總額", "權益總計", "股東權益總額", "歸屬於母公司業主之權益合計", "歸屬於母公司業主之權益", "Total equity"),
        "dps_cash": ("現金股利", "每股現金股利", "Cash dividend")}                           # V2:PER 用稀釋 EPS · ROE 用前後期平均權益 · DPS 遞延規則(VDF v036 無股利資料集 → STATUS 註記)


def _ratios(fa: list, adj_close) -> dict:
    """舊欄相容；只有全年同範圍數據才可計算，實際三年欄由財務契約接管。"""
    from VRN2_FinanceContract_v0101 import normalized_fact
    by={}
    for row in fa:
        f=normalized_fact(row,True)
        if f: by.setdefault(f["year"],{})[f["std"]]=f
    roe={}
    for y,vals in by.items():
        ni=vals.get("net_income");eq=vals.get("equity");prev=by.get(y-1,{}).get("equity")
        if ni and eq and prev and ni["scope"] and len({f["scope"] for f in (ni,eq,prev)})==1 and eq["value"]+prev["value"]>0:
            roe[str(y)]=ni["value"]/((eq["value"]+prev["value"])/2)
    return {"roe_avg_equity":roe,"per_diluted":None,"notes":["PER 三年矩陣由財務契約計算；須驗證每股股數基準"]}



def _std_of(account: str) -> str:
    a = str(account or "").replace(" ", "")
    for k, names in _STD.items():
        if any(n.replace(" ", "") in a for n in names):
            return k
    return ""


def _annual(finrows, code: str, rd: str) -> list:
    """只收完整年度：損益/現金流 ANNUAL 或 Q4 全年 YTD；資產負債只收 12/31 POINT。"""
    from VRN2_FinanceContract_v0101 import std_item
    f=finrows[finrows["ticker"].astype(str)==code]
    out=[]
    for _,r in f.iterrows():
        basis=str(r.get("basis") or ""); q=str(r.get("quarter") or "").replace(".0","")
        end=str(r.get("date") or "")[:10]
        if not (basis=="ANNUAL" or basis=="YTD" and q=="4" or basis=="POINT" and end.endswith("12-31")): continue
        std=std_item(r.get("account"))
        if not std: continue
        try: value=float(r["value"]); year=int(r["fiscal_year"])
        except (ValueError,TypeError): continue
        if not __import__("math").isfinite(value): continue
        out.append({"year":year,"std":std,"value":value,"unit":r.get("unit"),"basis":"ANNUAL","original_basis":basis,"quarter":q,"scope":r.get("report_scope"),"source":r.get("source"),"currency":r.get("currency") or "TWD","account":r.get("account"),"statement":r.get("financial_statement")})
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
                rec.update(close_before_report=float(b["close"]), adj_close_before_report=float(b["adj_close"]), adj_close_before_report_date=str(b["date"]), adjustment_factor_report=fac)
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
        # 已驗證證據檔可由 VDF/VCGC 提供；無證據不把候選交易日當成已核對。
        evidence_path=out/"VRN2_VerifiedEvidence.json"
        evidence=json.loads(evidence_path.read_text(encoding="utf-8-sig")) if evidence_path.is_file() else {}
        ev=(evidence.get("per_file") or {}).get(row.get("FILENAME")) or {}
        for key in ("dividend_events","filing_deadlines","per_share_split_factor","previous_trading_day_verified","target_price_anchor_verified"):
            if key in ev: rec[key]=ev[key]
        rec["upside_pct_adj"]=rec.get("upside_adj")  # 相容鍵也一律為純小數
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
    from VRN2_FinanceContract_v0101 import number, report_flag, HEADERS
    cases=[ticker_type("2330.TW")==("STOCK","2330"),ticker_type("6488.TWO")==("STOCK","6488"),
           forms("2330","TWSE")["bloomberg_ticker"]=="2330 TT",abs(number("23.6747897%")-.236747897)<1e-12,
           len(HEADERS)==39,report_flag("2026-10-29",_dt.date(2026,10,28)).startswith("未來")]
    print("[計] VRN2_MarketFetch v0109 自測 %d/6 · %s"%(sum(cases),"PASS" if all(cases) else "FAIL"))
    return 0 if all(cases) else 1


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
        ad = shim / "supportive modules" / "network" / "VIA_NetBridge_Adapter_v0101.py"
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
    if os.environ.get("VIA_VRN2_MARKET_HOME"):
        a["out"]=os.environ["VIA_VRN2_MARKET_HOME"]
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
