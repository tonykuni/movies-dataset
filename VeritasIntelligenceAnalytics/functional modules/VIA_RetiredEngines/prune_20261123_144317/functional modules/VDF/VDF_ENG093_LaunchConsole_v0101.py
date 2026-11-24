#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ===== VDF_ENG093_LaunchConsole_v0101(側線 2026-09-23;主線批號由併線的手指定 L25)=====
# v0100→v0101 操作員令(工作站看過 v0100 的頁之後):「每道上限檔數刪除 · 要抓就全抓 · 導入網路工具 · 起始日期 YYYY-MM-DD ·
#   截止日期自動帶入今天 · 方便打勾方格自動 · 逐一引擎邊測邊修正到成功 · 並將輸入參數(要找的資料)用大矩陣顯示出來完整」:
#   ① 問參數頁:拿掉檔數上限欄(送 limit 直接拒;全市場全抓)· 起始日期 date 欄 · 截止日期=今天(自動、不收)·
#      要抓的資料矩陣:每一步一列(打勾方格預設全勾)× 要抓的資料 × 引擎尾版 × 實際參數(隨起始日變)× 觸網 × 網路工具橋 × 加速器橋 ×
#      鏈/依賴 × 逾時 × 自測;步冊逐格委派 CGC_MDL125、鏈委派 CGC_MDL134,步清單讀自啟動器($steps 那一行),本台不另寫。
#   ② 逐一引擎自測台:頁上一鍵,背景一支一支跑 --selftest(子行程拿掉同意閘變數、零跳出、只寫暫存);跑的時候不收「啟動」。
#   ③ 狀況頁:多「本次輸入參數」與「各步結果」(CGC_MDL134 最近一次非 PLAN 報告;紅步帶紀錄檔)。
#   決定檔改為 since · until · steps · dry · noheal(啟動器 Invoke-VIA-VdfFetch v0107 的 -Since / -Steps 接)。v0100 留作版史 L04.
# 操作員 2026-09-23 令:「給我一個指令含進入環境一件開啟 VDF 的 POWERSHELL CODE 實測 · 應先跳出 HTML U/I 問我要不要改參數啟動 ·
#   然後看到資料庫狀況」。這支是那個指令(Open-VIA-VDF-v*.ps1)背後的兩頁:
#   ask    —— 啟動前:參數(預設讀自啟動器 Invoke-VIA-VdfFetch 尾版的 param 區塊,不另寫一份)· 啟動就緒(VDF_SystemManager launch)·
#             資料庫狀況(目錄新鮮度 · 分類燈 · 增量缺口);你按「用預設參數啟動 / 用上面的參數啟動 / 不啟動」,決定寫成一個 JSON 交回 PowerShell。
#   status —— 抓完之後:先委派 CGC_MDL123 重點目錄,再把分類燈(CGC_MDL153 db_summary)與增量缺口(VDF_ENG089 plan)排成一頁。
# 逐格委派正主,本支一條判準都不自己寫(Zero-Hydra / LL316)。本機頁只綁 127.0.0.1、一次性權杖、同源 POST、每欄驗證;
# 同意閘只讀不寫(擷取車道 CGC_MDL134 在自己的子行程開閘;直呼類才要操作員開閘二)。零 CDN、零網路。
# 開頁:本支只在帶 --open 時試 webbrowser(house 零跳出律;短令冊設的 VIA_NO_OPEN=1 會讓它靜默不開)。
#   一鍵腳本 Open-VIA-VDF 不帶 --open:它從 stdout 取「頁:」那一行(網址或絕對路徑,已 flush),交給短令冊的 via-open
#   (只走瀏覽器 exe、永不經 .html 預設程式 = VS Code)。那一令是操作員親手打的,打了就該跳(批474 B:分界線是誰要求的)。
"""
VDF_ENG093_LaunchConsole — VDF 一鍵啟動台(問參數頁 + 資料庫狀況頁)
用法見 USAGE(python VDF_ENG093_LaunchConsole_v0100.py help)。
"""
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
# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import contextlib
import hmac
import html
import importlib.util
import io
import json
import os
import re
import secrets
import sys
import tempfile
import threading
from datetime import date, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
REPORTS = VIA / "VIA_Reports"
OUT_DIR = REPORTS / "vdf_console"
VERSION = Path(__file__).stem.rsplit("_v", 1)[-1]
DATE_MIN = date(1990, 1, 1)
BODY_MAX = 8192
ACTIONS = ("launch", "cancel")
MODES = ("default", "custom")
FLAGS = ("dry", "noheal")
SELFTEST_TIMEOUT = 300

# 正主(尾版律現解;本台一條規則都不自己寫)
OWNERS = {
    "gate":    (("functional modules", "VDF", "engine"), "VDF_ENG089_IncrementalFetchGate_v*.py"),
    "door":    (("functional modules", "VDF"), "VDF_SystemManager_v*.py"),
    "summary": (("supportive modules", "registry"), "CGC_MDL153_WorkflowComposer_v*.py"),
    "home":    (("supportive modules", "registry"), "CGC_MDL123_DataHome_v*.py"),
    "fixall":  (("supportive modules", "registry"), "CGC_MDL125_FixAll_v0*.py"),     # 步冊(與 CGC_MDL134 取它的樣式同)
    "lanes":   (("supportive modules", "registry"), "CGC_MDL134_ParallelLanes_v*.py"),
}
_OWN: dict = {}


def _newest(folder: Path, pat: str):
    hits = sorted(p for p in folder.glob(pat) if "__pycache__" not in p.parts)
    return hits[-1] if hits else None


def _load(tag: str, path: Path):
    spec = importlib.util.spec_from_file_location(tag, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[tag] = mod
    with contextlib.redirect_stdout(io.StringIO()):
        spec.loader.exec_module(mod)
    return mod


def owner(key: str):
    """正主尾版;不在 → None(因由在 _OWN[key]['why']);載入就炸 → None + BROKEN 因由(兩件事不壓成一態)。"""
    st = _OWN.setdefault(key, {"mod": None, "why": "", "src": ""})
    if st["mod"] is not None or st["why"]:
        return st["mod"]
    rel, pat = OWNERS[key]
    p = _newest(VIA.joinpath(*rel), pat)
    if not p:
        st["why"] = "/".join(rel) + "/" + pat + " 缺"
        return None
    st["src"] = p.name
    try:
        st["mod"] = _load("vdf_eng093_" + key, p)
    except Exception as exc:
        st["why"] = f"BROKEN {type(exc).__name__}:{str(exc)[:80]}"
    return st["mod"]


def _quiet(fn, *a, **k):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        return fn(*a, **k)


# ---------------------------------------------------------------- 參數:預設與步清單讀自啟動器正本
def launcher_defaults(text: str | None = None) -> dict:
    """預設值與步清單都不在這裡另寫一份:讀尾版 Invoke-VIA-VdfFetch-v*.ps1——param() 的 -Since(沒有就 -Year → 該年 1/1)
    與步清單那一行(v0107 起叫 `$stepBook = "..."`——PowerShell 變數不分大小寫,叫 $steps 會蓋掉 -Steps 參數;舊版叫 `$steps`,兩個都認)。
    讀不到就講明,退回 2023-01-01、步清單空。"""
    src = ""
    if text is None:
        p = _newest(VIA, "Invoke-VIA-VdfFetch-v*.ps1")
        src = p.name if p else ""
        try:
            text = p.read_text(encoding="utf-8", errors="replace") if p else ""
        except Exception:
            text = ""
    text = text or ""
    out = {"since": "2023-01-01", "steps": [], "dry": False, "noheal": False, "launcher": src,
           "from_launcher": False, "steps_from_launcher": False, "why": ""}
    m_since = re.search(r'\[string\]\s*\$Since\s*=\s*"(\d{4}-\d{2}-\d{2})"', text)
    m_year = re.search(r'\[string\]\s*\$Year\s*=\s*"(\d{4})"', text)
    if m_since:
        out.update(since=m_since.group(1), from_launcher=True)
    elif m_year:
        out.update(since=m_year.group(1) + "-01-01", from_launcher=True)
    m_steps = re.search(r'^\s*\$(?:stepBook|steps)\s*=\s*"([a-z0-9_,]+)"', text, re.M)
    if m_steps:
        out.update(steps=[s for s in m_steps.group(1).split(",") if s], steps_from_launcher=True)
    whys = []
    if not text:
        whys.append("啟動器不在,暫用 2023-01-01")
    else:
        if not out["from_launcher"]:
            whys.append("啟動器 param() 讀不到起始日預設,暫用 2023-01-01")
        if not out["steps_from_launcher"]:
            whys.append("啟動器讀不到步清單($stepBook / $steps 那一行)")
    out["why"] = ";".join(whys)
    return out


def validate(body: dict, defaults: dict, allowed_steps: list, today: date | None = None) -> tuple:
    """頁上交回來的決定逐欄驗證;不認得的鍵、越界的值一律拒絕並點名欄位(絕不靜默吞掉)。
    v0101:沒有檔數上限了(要抓就全抓,送 limit 直接拒);起始日 YYYY-MM-DD;截止日一律今天(不收);步只收啟動器步清單裡的。"""
    today = today or date.today()
    if not isinstance(body, dict):
        return False, {"field": "body", "why": "不是 JSON 物件"}
    allowed = {"t", "action", "mode", "since", "steps", "dry", "noheal"}
    extra = sorted(set(body) - allowed)
    if extra:
        return False, {"field": ",".join(extra), "why": "不認得的欄位" + (";沒有檔數上限了:要抓就全抓" if "limit" in extra else "")}
    action = body.get("action")
    if action not in ACTIONS:
        return False, {"field": "action", "why": "只收 launch / cancel"}
    if action == "cancel":
        return True, {"action": "cancel"}
    mode = body.get("mode", "custom")
    if mode not in MODES:
        return False, {"field": "mode", "why": "只收 default / custom"}
    if not allowed_steps:
        return False, {"field": "steps", "why": "啟動器步清單讀不到,不能啟動(看頁上的說明)"}
    if mode == "default":
        return True, {"action": "launch", "mode": "default", "since": str(defaults["since"]), "until": today.isoformat(),
                      "steps": list(allowed_steps), "dry": bool(defaults["dry"]), "noheal": bool(defaults["noheal"])}
    since = str(body.get("since", "")).strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", since):
        return False, {"field": "since", "why": "起始日要 YYYY-MM-DD"}
    try:
        d0 = date.fromisoformat(since)
    except ValueError:
        return False, {"field": "since", "why": "起始日不是真的日期"}
    if not (DATE_MIN <= d0 <= today):
        return False, {"field": "since", "why": f"起始日要在 {DATE_MIN.isoformat()} 到今天 {today.isoformat()} 之間"}
    steps = body.get("steps")
    if not isinstance(steps, list):
        return False, {"field": "steps", "why": "步要是清單"}
    if not steps:
        return False, {"field": "steps", "why": "至少勾一步"}
    if any(not isinstance(x, str) for x in steps):
        return False, {"field": "steps", "why": "步名要是字串"}
    unknown = [x for x in steps if x not in allowed_steps]
    if unknown:
        return False, {"field": "steps", "why": "不認得的步:" + ",".join(unknown[:5])}
    if len(set(steps)) != len(steps):
        return False, {"field": "steps", "why": "同一步勾了兩次"}
    flags = {}
    for k in FLAGS:
        v = body.get(k, False)
        if not isinstance(v, bool):
            return False, {"field": k, "why": "只收 true / false"}
        flags[k] = v
    picked = set(steps)
    return True, {"action": "launch", "mode": "custom", "since": since, "until": today.isoformat(),
                  "steps": [s for s in allowed_steps if s in picked], **flags}


# ---------------------------------------------------------------- 要抓的資料:步 × 引擎 × 實際參數(逐格委派)
def _fixall_with_since(since: str):
    """CGC_MDL125 步冊在模組載入時讀 VIA_HIST_SINCE / VIA_REV_SINCE / VIA_HIST_LIMIT(常數)。
    要照這個起始日算出每一步真正會跑的 argv,就在暫時的環境下另載一份;環境只在這裡動,出來逐一還原(同意閘一個都不碰)。"""
    rel, pat = OWNERS["fixall"]
    p = _newest(VIA.joinpath(*rel), pat)
    if not p:
        return None, "/".join(rel) + "/" + pat + " 缺"
    keep = {k: os.environ.get(k) for k in ("VIA_HIST_SINCE", "VIA_REV_SINCE", "VIA_HIST_LIMIT")}
    try:
        os.environ["VIA_HIST_SINCE"] = since
        os.environ["VIA_REV_SINCE"] = since[:7]
        os.environ.pop("VIA_HIST_LIMIT", None)   # 要抓就全抓:頁上顯示的 argv 不帶 --limit
        return _load("vdf_eng093_fixall_" + re.sub(r"\D", "", since), p), p.name
    except Exception as exc:
        return None, f"BROKEN {type(exc).__name__}:{str(exc)[:80]}"
    finally:
        for k, v in keep.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def steps_matrix(since: str, steps: list | None) -> dict:
    """每一步:要抓的資料(中文名)· 引擎尾版 · 實際參數(照這個起始日算)· 觸網 · 逾時,全取自 CGC_MDL125 步冊;
    鏈與依賴取自 CGC_MDL134 assign;橋只看標記(L102 ① 與 L69 的判準本身就是標記)。本台一條規則都不自己寫。"""
    today = date.today().isoformat()
    out = {"since": since, "until": today, "rows": [], "src": {}, "why": ""}
    m, src = _fixall_with_since(since)
    if m is None:
        out["why"] = "步冊讀不到:" + src
        return out
    out["src"]["fixall"] = src
    try:
        book = {s["id"]: s for s in _quiet(m.plan)}
    except Exception as exc:
        out["why"] = f"步冊 plan() 炸了:{type(exc).__name__}"
        return out
    chains = {}
    ln = owner("lanes")
    if ln is not None and hasattr(ln, "assign"):
        try:
            chains = {s["id"]: s for s in _quiet(ln.assign, list(book.values()))}
            out["src"]["lanes"] = _OWN["lanes"]["src"]
        except Exception:
            chains = {}
    hist_since, rev_since = str(getattr(m, "HIST_SINCE", since)), str(getattr(m, "REV_SINCE", since[:7]))
    for sid in (steps or list(book)):
        s = book.get(sid)
        if s is None:
            out["rows"].append({"id": sid, "zh": "", "missing": True})
            continue
        argv = [str(a) for a in (s.get("argv") or [])]
        eng = next((a for a in argv if a.endswith(".py")), "")
        ep = Path(eng) if eng else None
        try:
            body = ep.read_text(encoding="utf-8", errors="replace") if ep and ep.exists() else ""
        except Exception:
            body = ""
        rest = argv[argv.index(eng) + 1:] if eng in argv else argv[1:]
        toks = [{"t": a, "k": ("since" if a == hist_since else "since_month" if a == rev_since else "until" if a == today else "")}
                for a in rest]
        ch = chains.get(sid) or {}
        out["rows"].append({
            "id": sid, "zh": s.get("zh", ""), "why": s.get("why", ""), "net": bool(s.get("net")), "to": s.get("to"),
            "engine": ep.name if ep else "", "engine_path": str(ep) if ep else "", "engine_ok": bool(ep and ep.exists()),
            "args": toks, "chain": ch.get("chain", ""), "after": list(ch.get("after") or []),
            "accel": "[VIA:ACCEL-BRIDGE" in body, "netbridge": "[VIA:NET-BRIDGE" in body, "missing": False})
    return out


def _st_state(rc) -> str:
    """rc → 燈(L16 誠實 rc:0 綠 · 1 紅 · 2 沒料/過期 · 3 缺件 · 4 閘關)。"""
    return {0: "OK", 1: "FAIL", 2: "NODATA", 3: "ABSENT", 4: "GATED"}.get(rc, "FAIL")


def _child_env(environ: dict | None = None) -> dict:
    """自測子行程的環境:拿掉所有名字裡有 CONSENT 的變數(只會更離線,不代開任何閘)· 零跳出 · UTF-8。"""
    env = {k: v for k, v in (os.environ if environ is None else environ).items() if "CONSENT" not in str(k).upper()}
    env["VIA_NO_OPEN"] = "1"
    env.setdefault("PYTHONIOENCODING", "utf-8")
    return env


def engine_selftest(path: str, timeout: int = SELFTEST_TIMEOUT, environ: dict | None = None) -> dict:
    """單支引擎 --selftest。子行程環境拿掉所有同意閘變數(只會更離線,不代開任何閘)、零跳出;自測律 L17 本來就只寫暫存。
    environ 可注入(自測用注入的環境驗「同意閘變數有被拿掉」,不去動本行程的環境)。"""
    import subprocess
    import time
    p = Path(path)
    if not p.exists():
        return {"state": "ABSENT", "rc": None, "sec": 0, "last": "引擎檔不在"}
    env = _child_env(environ)
    t0 = time.monotonic()
    try:
        r = subprocess.run([sys.executable, str(p), "--selftest"], cwd=str(p.parent), env=env, capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"state": "TIMEOUT", "rc": None, "sec": round(time.monotonic() - t0, 1), "last": f"逾 {timeout}s 已停"}
    except Exception as exc:
        return {"state": "FAIL", "rc": None, "sec": round(time.monotonic() - t0, 1), "last": f"起不來:{type(exc).__name__}"}
    lines = [ln.strip() for ln in (r.stdout + "\n" + r.stderr).splitlines() if ln.strip()]
    tail = next((ln for ln in reversed(lines) if any(k in ln for k in ("計", "OK", "FAIL", "PASS", "passed", "all_pass"))),
                lines[-1] if lines else "")
    return {"state": _st_state(r.returncode), "rc": r.returncode, "sec": round(time.monotonic() - t0, 1), "last": tail[:160]}


def lanes_result(rep_dir: Path | None = None) -> dict:
    """CGC_MDL134 最近一次真跑(或 DRY)的逐步結果。PLAN 報告不算(啟動器第 ⑥ 步的 plan 也會落一份)。資料夾取正主的 REP 常數。"""
    if rep_dir is None:
        ln = owner("lanes")
        rep_dir = getattr(ln, "REP", None) if ln is not None else None
    if not rep_dir or not Path(rep_dir).exists():
        return {"state": "ABSENT", "why": "還沒有擷取道報告(CGC_MDL134)"}
    for p in sorted(Path(rep_dir).glob("LANES_*.json"), reverse=True):
        try:
            rep = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if rep.get("state") == "PLAN":
            continue
        return {"state": rep.get("state"), "file": p.name, "stamp": rep.get("stamp"), "dry": rep.get("dry"), "online": rep.get("online"),
                "n_ok": rep.get("n_ok"), "n_fail": rep.get("n_fail"), "n_skip": rep.get("n_skip"), "sec": rep.get("sec"),
                "note": rep.get("note", ""), "steps": rep.get("steps") or []}
    return {"state": "ABSENT", "why": "只有 PLAN 報告,還沒真跑過"}


# ---------------------------------------------------------------- 資料庫狀況:逐格委派
def read_catalog(path: Path | None = None):
    g = owner("gate")
    p = Path(path) if path else (Path(getattr(g, "CATALOG")) if g is not None and getattr(g, "CATALOG", None)
                                 else REPORTS / "datahome" / "DATAHOME_CATALOG_latest.json")
    try:
        return json.loads(p.read_text(encoding="utf-8-sig")), p
    except Exception:
        return None, p


def tables_from_catalog(cat: dict, today: date | None = None) -> tuple:
    """目錄(CGC_MDL123)→ CGC_MDL153 db_summary 吃的形狀 {表: rows/max/lag_days};同名表在兩本庫 → 取最新那一本,另列。"""
    today = today or date.today()
    out, dup = {}, []
    for db in (cat or {}).get("dbs") or []:
        for t in db.get("tables") or []:
            name = str(t.get("table") or "")
            if not name:
                continue
            hi = str(t.get("hi") or "")[:10]
            lag = None
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}", hi):
                try:
                    lag = (today - date.fromisoformat(hi)).days
                except ValueError:
                    lag = None
            row = {"rows": int(t.get("rows") or 0), "max": hi, "lag_days": lag, "db": db.get("name") or ""}
            if name in out:
                dup.append(name)
                if (row["max"], row["rows"]) <= (out[name]["max"], out[name]["rows"]):
                    continue
            out[name] = row
    return out, sorted(set(dup))


def db_state(catalog_path: Path | None = None, refresh: bool = False) -> dict:
    res = {"ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "why": [], "refresh": None}
    if refresh:
        h = owner("home")
        if h is None:
            res["refresh"] = {"state": "ABSENT", "why": _OWN["home"]["why"]}
        else:
            try:
                r = _quiet(h.catalog, write=True, do_print=False)
                res["refresh"] = {"state": "OK", "dbs": len((r or {}).get("dbs") or []), "src": _OWN["home"]["src"]}
            except Exception as exc:
                res["refresh"] = {"state": "BROKEN", "why": f"{type(exc).__name__}:{str(exc)[:120]}"}
    cat, p = read_catalog(catalog_path)
    res["catalog_path"] = str(p)
    g = owner("gate")
    if g is not None and hasattr(g, "catalog_freshness"):
        try:
            res["fresh"] = g.catalog_freshness(cat)
        except Exception as exc:
            res["fresh"] = {"state": "BROKEN", "why": f"{type(exc).__name__}:{str(exc)[:120]}"}
    else:
        res["fresh"] = {"state": "ABSENT", "why": _OWN.get("gate", {}).get("why", "")}
    tables, dup = tables_from_catalog(cat) if cat else ({}, [])
    res["tables"], res["dup"] = tables, dup
    s = owner("summary")
    if s is not None and hasattr(s, "db_summary") and cat:
        try:
            res["summary"] = s.db_summary(tables=tables)
        except Exception as exc:
            res["summary"] = {"verdict": "BROKEN", "why": f"{type(exc).__name__}:{str(exc)[:120]}", "categories": []}
    else:
        res["summary"] = {"verdict": "ABSENT", "categories": [], "why": "目錄不在" if not cat else _OWN.get("summary", {}).get("why", "")}
    if g is not None and hasattr(g, "plan") and cat:
        saved = getattr(g, "CATALOG", None)
        try:
            if catalog_path:
                g.CATALOG = Path(catalog_path)
            res["plan"] = _quiet(g.plan)
        except Exception as exc:
            res["plan"] = {"state": "BROKEN", "why": f"{type(exc).__name__}:{str(exc)[:120]}"}
        finally:
            if catalog_path:
                g.CATALOG = saved
    else:
        res["plan"] = {"state": "ABSENT", "why": "目錄不在" if not cat else _OWN.get("gate", {}).get("why", "")}
    res["dbs"] = [{"name": d.get("name"), "tables": d.get("tables") or []} for d in ((cat or {}).get("dbs") or [])]
    res["verdict"], res["rc"] = verdict(res)
    return res


def verdict(res: dict) -> tuple:
    """整頁一句話:目錄不在=ABSENT rc3;分類紅/黃或目錄過期=STALE rc2(資料落後不是壞掉);全綠=GREEN rc0。"""
    sv = str((res.get("summary") or {}).get("verdict") or "")
    fr = str((res.get("fresh") or {}).get("state") or "")
    if sv == "ABSENT" or fr == "ABSENT":
        return "ABSENT", 3
    if sv.startswith("BROKEN") or fr.startswith("BROKEN"):
        return "BROKEN", 1
    if sv in ("RED", "YELLOW") or fr in ("STALE", "UNKNOWN"):
        return "STALE", 2
    return "GREEN", 0


def readiness() -> dict:
    d = owner("door")
    if d is None or not hasattr(d, "read_launch"):
        return {"state": "ABSENT", "why": _OWN.get("door", {}).get("why", "")}
    try:
        r = _quiet(d.read_launch, probe=False)
    except Exception as exc:
        return {"state": "BROKEN", "why": f"{type(exc).__name__}:{str(exc)[:120]}"}
    c = r.get("consent") or {}
    py = r.get("python") or {}
    hl = r.get("hist_limit") or {}
    return {"state": r.get("state"), "rc": r.get("rc"), "src": _OWN["door"]["src"],
            "python": {"state": py.get("state"), "path": py.get("python"), "source": py.get("source")},
            "gates": {"VIA_NET_CONSENT": c.get("VIA_NET_CONSENT"), "VIA_SCRAPE_CONSENT": c.get("VIA_SCRAPE_CONSENT")},
            "hist_limit": {"set": hl.get("set"), "n": hl.get("n"), "launcher": hl.get("launcher"), "restores": hl.get("launcher_restores")},
            "next": [str(x) for x in (r.get("next") or [])][:6], "why": r.get("why")}


# ---------------------------------------------------------------- 頁(零 CDN · 零外部資源 · 淺深兩色)
_CSS = """
:root{--bg:#fbfbfa;--fg:#1d1d1b;--muted:#6b6b66;--card:#ffffff;--line:#e4e3de;--g:#1f7a3f;--y:#9a6b00;--r:#b3261e;--n:#5c5c57;--acc:#2f5dab}
@media (prefers-color-scheme:dark){:root{--bg:#161615;--fg:#ecebe6;--muted:#a3a29c;--card:#1f1f1d;--line:#34332f;--g:#5cc47f;--y:#e0b04a;--r:#f08a80;--n:#a3a29c;--acc:#8fb0ec}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.55 system-ui,"Segoe UI","Microsoft JhengHei",sans-serif}
main{max-width:1180px;margin:0 auto;padding:20px 16px 40px}h1{font-size:20px;margin:0 0 4px}h2{font-size:15px;margin:0 0 10px}
.sub{color:var(--muted);font-size:13px;margin-bottom:16px}.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px;margin:0 0 14px}
table{width:100%;border-collapse:collapse;font-size:13px}th,td{text-align:left;padding:5px 8px;border-bottom:1px solid var(--line);vertical-align:top;word-break:break-all}
th{color:var(--muted);font-weight:600}.num{text-align:right;font-variant-numeric:tabular-nums}
.chip{display:inline-block;min-width:58px;text-align:center;border-radius:999px;padding:1px 8px;font-size:12px;font-weight:600;border:1px solid currentColor}
.GREEN,.FRESH,.OK,.PASS{color:var(--g)}.YELLOW,.STALE,.UNKNOWN,.SKIP,.PART,.PLAN{color:var(--y)}.RED,.BROKEN,.FAIL,.TIMEOUT,.BLOCKED{color:var(--r)}.ABSENT,.NODATA,.GATED{color:var(--n)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px 16px}label{display:block;font-size:13px;color:var(--muted)}
input[type=number],input[type=date],input[type=text]{width:100%;padding:6px 8px;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--fg);font:inherit}
.chk{display:flex;gap:8px;align-items:center;color:var(--fg);margin-top:6px}.btns{display:flex;flex-wrap:wrap;gap:10px;margin-top:14px}
button{font:inherit;padding:8px 14px;border-radius:8px;border:1px solid var(--line);background:var(--card);color:var(--fg);cursor:pointer}
button.primary{background:var(--acc);border-color:var(--acc);color:#fff}button:disabled{opacity:.5;cursor:default}
.msg{margin-top:12px;font-size:13px}.muted{color:var(--muted)}ul{margin:6px 0 0 18px;padding:0}code{font-size:12px}
input:disabled,input[readonly]{opacity:.8}.dt{display:flex;gap:6px}.dt input[type=text]{flex:1}.dt input[type=date]{width:40px;flex:none;padding:6px 4px}.dt input[type=date]::-webkit-datetime-edit{display:none}.scroll{overflow-x:auto}.mx{font-size:12.5px}.mx td,.mx th{padding:5px 6px}.mx code{font-size:11.5px;word-break:break-all}.tok{background:rgba(47,93,171,.14);border-radius:4px;padding:0 3px}.ok{color:var(--g);font-weight:600}.bad{color:var(--r);font-weight:600}
"""


def _e(x) -> str:
    return html.escape("" if x is None else str(x))


def _chip(state) -> str:
    s = str(state or "NODATA")
    cls = re.sub(r"[^A-Z]", "", s.upper())[:12] or "NODATA"
    return f"<span class='chip {cls}'>{_e(s)}</span>"


def _db_cards(st: dict, gap_rows: int) -> str:
    fr = st.get("fresh") or {}
    age = fr.get("age_h")   # 欄名照 VDF_ENG089 catalog_freshness(catalog_ts / age_h)
    age_txt = (f" · {round(age * 60)} 分鐘前" if isinstance(age, (int, float)) and age < 1
               else (f" · {age:g} 小時前" if isinstance(age, (int, float)) else ""))
    head = (f"<div class='card'><h2>資料庫目錄 {_chip(fr.get('state'))}</h2>"
            f"<div class='muted'>目錄時間 {_e(fr.get('catalog_ts') or '-')}"
            + age_txt
            + f" · 來源 CGC_MDL123(<code>{_e(st.get('catalog_path'))}</code>)</div>"
            + (f"<div class='msg'>{_e(fr.get('why'))}</div>" if fr.get("why") else "") + "</div>")
    sm = st.get("summary") or {}
    rows = "".join(
        f"<tr><td>{_e(c.get('cat'))}</td><td>{_chip(c.get('lamp'))}</td><td class='num'>{_e(c.get('n'))}</td>"
        f"<td class='num'>{int(c.get('rows') or 0):,}</td><td>{_e(c.get('newest') or '-')}</td>"
        f"<td class='num'>{_e(c.get('worst_lag') if c.get('worst_lag') is not None else '?')}</td></tr>"
        for c in (sm.get("categories") or []))
    cats = (f"<div class='card'><h2>分類燈 {_chip(sm.get('verdict'))}</h2>"
            + (f"<table><tr><th>類別</th><th>燈</th><th class='num'>表</th><th class='num'>列</th><th>最新日</th><th class='num'>最壞滯後(日)</th></tr>{rows}</table>"
               if rows else f"<div class='muted'>{_e(sm.get('why') or '沒有可分類的表')}</div>")
            + "<div class='muted' style='margin-top:6px'>分類與燈號門檻:CGC_MDL153 db_summary(本頁不另算)</div></div>")
    pl = st.get("plan") or {}
    gaps = pl.get("gaps") or []
    grow = "".join(
        f"<tr><td>{_e(g.get('db'))}</td><td>{_e(g.get('table'))}</td><td>{_e(g.get('have'))}</td>"
        f"<td class='num'>{_e(g.get('missing_days'))}</td></tr>" for g in gaps[:gap_rows])
    plan = (f"<div class='card'><h2>增量缺口 {_chip(pl.get('state'))}</h2>"
            + (f"<div class='muted'>自 {_e(pl.get('since'))} 起 · 表 {_e(pl.get('n_tables'))} · 有缺口 {_e(pl.get('n_gap'))} · 齊 {_e(pl.get('n_covered'))}"
               f" · 紀錄表 {len(pl.get('records') or [])} · 哨兵 {len(pl.get('sentinels') or [])}</div>"
               if pl.get("state") not in ("ABSENT",) else f"<div class='muted'>{_e(pl.get('why'))}</div>")
            + (f"<table style='margin-top:8px'><tr><th>庫</th><th>表</th><th>現有</th><th class='num'>缺(日)</th></tr>{grow}</table>" if grow else "")
            + (f"<div class='muted'>另 {len(gaps) - gap_rows} 張沒列</div>" if len(gaps) > gap_rows else "")
            + "<div class='muted' style='margin-top:6px'>缺口與哨兵判讀:VDF_ENG089 plan(本頁不另算)</div></div>")
    return head + cats + plan


def _yes(flag, yes="✓", no="✗") -> str:
    return f"<span class='{'ok' if flag else 'bad'}'>{yes if flag else no}</span>"


def _matrix_rows(mx: dict, allowed: list) -> str:
    rows = ""
    for r in mx.get("rows") or []:
        rid = _e(r["id"])
        if r.get("missing"):
            rows += (f"<tr><td><input type='checkbox' class='stp' value='{rid}' disabled></td><td><b>{rid}</b></td>"
                     f"<td colspan='9' class='bad'>步冊(CGC_MDL125)裡沒有這一步,不能跑</td><td>-</td></tr>")
            continue
        can = r.get("engine_ok") and r["id"] in allowed
        args = " ".join(f"<span class='tok' data-k='{_e(t['k'])}'>{_e(t['t'])}</span>" if t.get("k") else _e(t["t"])
                        for t in r.get("args") or [])
        kinds = {t.get("k") for t in r.get("args") or []}
        rng = ("<span data-k='since'>" + _e(mx.get("since")) + "</span> → " + _e(mx.get("until")) if "since" in kinds
               else "<span data-k='since_month'>" + _e(str(mx.get("since"))[:7]) + "</span> → 本月" if "since_month" in kinds
               else "<span class='muted'>引擎自管(抓到最新)</span>")
        net = ("是" if r.get("net") else "<span class='muted'>否</span>")
        nb = _yes(r.get("netbridge")) if (r.get("net") or r.get("netbridge")) else "<span class='muted'>不觸網</span>"
        dep = _e(r.get("chain") or "-") + ((" · 等 " + _e(", ".join(r.get("after") or []))) if r.get("after") else "")
        rows += (f"<tr><td><input type='checkbox' class='stp' value='{rid}'{' checked' if can else ' disabled'}></td>"
                 f"<td><b>{rid}</b></td><td>{_e(r.get('zh'))}<div class='muted'>{_e(r.get('why'))}</div></td>"
                 f"<td><code>{_e(r.get('engine') or '(缺)')}</code></td><td><code>{args or '<span class=muted>(無參數)</span>'}</code></td>"
                 f"<td>{rng}</td><td>{net}</td><td>{nb}</td><td>{_yes(r.get('accel'))}</td><td>{dep}</td>"
                 f"<td class='num'>{_e(r.get('to'))}</td><td id='st_{rid}'><span class='muted'>未測</span></td></tr>")
    return rows


def render_ask(ctx: dict, token: str) -> str:
    d, st, rd, mx, allowed = ctx["defaults"], ctx["db"], ctx["ready"], ctx["matrix"], ctx["allowed"]
    gates = rd.get("gates") or {}
    hl = rd.get("hist_limit") or {}
    nxt = "".join(f"<li>{_e(x)}</li>" for x in (rd.get("next") or []))
    today = date.today().isoformat()
    src = mx.get("src") or {}
    why = " · ".join(x for x in (d.get("why"), mx.get("why")) if x)
    return f"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>VDF 一鍵啟動</title><style>{_CSS}</style></head><body><main>
<h1>VDF 一鍵啟動</h1><div class="sub">VDF_ENG093 v{_e(VERSION)} · {_e(ctx['ts'])} · 先看要抓什麼、資料庫缺什麼,再按啟動。按下之後擷取在 PowerShell 視窗裡跑,進度印在那裡。</div>
<div class="card"><h2>啟動參數</h2>
<div class="muted" style="margin-bottom:8px">預設與步清單讀自啟動器 <code>{_e(d.get('launcher') or '(不在)')}</code>{(' · <span class="bad">' + _e(why) + '</span>') if why else ''}</div>
<div class="grid">
<div><label for="since">起始日期(YYYY-MM-DD)</label><div class="dt"><input id="since" type="text" inputmode="numeric" maxlength="10" placeholder="YYYY-MM-DD" value="{_e(d['since'])}"><input id="since_pick" type="date" min="{DATE_MIN.isoformat()}" max="{today}" value="{_e(d['since'])}" title="日曆挑日期" aria-label="日曆挑日期"></div><div class="muted">直接打 YYYY-MM-DD,或按右邊日曆挑</div></div>
<div><label for="until">截止日期(自動帶入今天)</label><input id="until" type="text" value="{today}" readonly><div class="muted">各引擎一律抓到最新</div></div>
<div><label>檔數</label><div style="padding:6px 0"><b>全市場,沒有上限</b><div class="muted">要抓就全抓</div></div></div>
<div><label class="chk"><input id="dry" type="checkbox"{' checked' if d.get('dry') else ''}> 只看計畫,不抓(-Dry)</label>
<label class="chk"><input id="noheal" type="checkbox"{' checked' if d.get('noheal') else ''}> 不做倉庫自癒(-NoHeal)</label></div>
</div>
<div class="msg" id="sum"></div>
<div class="btns"><button class="primary" id="b_default">用預設參數啟動(全部步 · 起 {_e(d['since'])})</button><button id="b_custom">用下面勾的啟動</button><button id="b_cancel">不啟動</button></div>
<div class="msg" id="msg" role="status"></div></div>
<div class="card"><h2>要抓的資料(輸入參數矩陣)</h2>
<div class="muted">每一列是一步:要抓的資料、跑哪支引擎尾版、實際帶的參數(藍底隨上面的起始日變)、觸網與否、兩道橋、在哪條鏈、逾時秒數。
步冊 CGC_MDL125 <code>{_e(src.get('fixall') or '-')}</code> · 鏈 CGC_MDL134 <code>{_e(src.get('lanes') or '-')}</code>;橋的判準是標記本身(L103 · L102 ① · L69)。</div>
<div class="btns"><button id="b_all">全選</button><button id="b_none">全不選</button><button id="b_test">逐一引擎自測(離線 · 只寫暫存)</button><span class="muted" id="tsum" style="align-self:center"></span></div>
<div class="scroll"><table class="mx" style="margin-top:8px"><tr><th></th><th>步</th><th>要抓的資料</th><th>引擎</th><th>實際參數</th><th>起 → 訖</th><th>觸網</th><th>網路工具</th><th>加速器</th><th>鏈 · 依賴</th><th class="num">逾時 s</th><th>自測</th></tr>
{_matrix_rows(mx, allowed)}</table></div></div>
<div class="card"><h2>啟動就緒 {_chip(rd.get('state'))}</h2><div class="muted">來源 {_e(rd.get('src') or rd.get('why') or '-')}(VDF 子系統管理對接口 launch;只讀)</div>
<table style="margin-top:8px"><tr><th>項</th><th>現況</th></tr>
<tr><td>家族境 python</td><td>{_chip((rd.get('python') or {}).get('state'))} <code>{_e((rd.get('python') or {}).get('path'))}</code></td></tr>
<tr><td>同意閘</td><td>VIA_NET_CONSENT {_chip(gates.get('VIA_NET_CONSENT'))} · VIA_SCRAPE_CONSENT {_chip(gates.get('VIA_SCRAPE_CONSENT'))}<div class="muted">擷取車道在自己的子行程開閘(CGC_MDL134),所以這裡沒開也能抓;直呼 via-price / via-chip 才要你在視窗開閘二。本頁只讀,不代開。</div></td></tr>
<tr><td>視窗限量</td><td>{'VIA_HIST_LIMIT=' + _e(hl.get('n')) + '(這一跑會清成全市場)' if hl.get('set') else '未設(全市場)'}</td></tr>
</table>{('<div style="margin-top:8px"><b>下一步</b><ul>' + nxt + '</ul></div>') if nxt else ''}</div>
<h2 style="margin:18px 0 10px">啟動前的資料庫狀況</h2>{_db_cards(st, 12)}
</main><script>
const T={json.dumps(token)};
const q=id=>document.getElementById(id);
const boxes=()=>[...document.querySelectorAll("input.stp")];
const esc=s=>String(s==null?"":s).replace(/[&<>"']/g,c=>({{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}}[c]));
let testing=false;
function lock(on){{["b_default","b_custom"].forEach(i=>q(i).disabled=on||testing);q("b_cancel").disabled=on;}}
function sync(){{
  const v=q("since").value||"";
  document.querySelectorAll("[data-k=since]").forEach(e=>e.textContent=v);
  document.querySelectorAll("[data-k=since_month]").forEach(e=>e.textContent=v.slice(0,7));
  const n=boxes().filter(b=>b.checked).length;
  q("sum").textContent="已勾 "+n+"/"+boxes().length+" 步 · 起 "+v+" → 訖 "+q("until").value+"(今天)· 全市場,沒有檔數上限";
}}
q("since").addEventListener("input",()=>{{const v=q("since").value;if(/^\d{{4}}-\d{{2}}-\d{{2}}$/.test(v))q("since_pick").value=v;sync();}});
q("since_pick").addEventListener("change",()=>{{if(q("since_pick").value){{q("since").value=q("since_pick").value;sync();}}}});
boxes().forEach(b=>b.addEventListener("change",sync));sync();
q("b_all").onclick=()=>{{boxes().forEach(b=>{{if(!b.disabled)b.checked=true;}});sync();}};
q("b_none").onclick=()=>{{boxes().forEach(b=>b.checked=false);sync();}};
function post(path,body){{body.t=T;return fetch(path,{{method:"POST",headers:{{"Content-Type":"application/json"}},body:JSON.stringify(body)}}).then(r=>r.json().then(j=>({{ok:r.ok,j}})));}}
function send(body){{
  lock(true);q("msg").textContent="送出中…";
  post("/decide",body).then(({{ok,j}})=>{{
     if(ok){{q("msg").textContent=j.decision.action==="cancel"?"已選「不啟動」。本頁可以關了。":"已送出:回 PowerShell 視窗看擷取進度。跑完會自動開資料庫狀況頁(含各步結果)。本頁可以關了。";}}
     else{{q("msg").textContent="沒收:"+(j.field||"")+" "+(j.why||"");lock(false);}}
   }}).catch(e=>{{q("msg").textContent="送不出去:"+e;lock(false);}});
}}
q("b_default").onclick=()=>send({{action:"launch",mode:"default"}});
q("b_custom").onclick=()=>{{
  const steps=boxes().filter(b=>b.checked).map(b=>b.value);
  if(!steps.length){{q("msg").textContent="至少勾一步";return;}}
  if(!/^\\d{{4}}-\\d{{2}}-\\d{{2}}$/.test(q("since").value)){{q("msg").textContent="起始日要 YYYY-MM-DD";return;}}
  send({{action:"launch",mode:"custom",since:q("since").value,steps,dry:q("dry").checked,noheal:q("noheal").checked}});
}};
q("b_cancel").onclick=()=>send({{action:"cancel"}});
function poll(){{
  fetch("/selftest?t="+encodeURIComponent(T)).then(r=>r.json()).then(j=>{{
    const done=j.done||{{}};let ok=0,bad=0;
    for(const [id,r] of Object.entries(done)){{
      const c=q("st_"+id);if(r.state==="OK")ok++;else bad++;
      if(c)c.innerHTML="<span class='chip "+esc(r.state)+"'>"+esc(r.state)+"</span> <span class='muted'>rc="+esc(r.rc)+" · "+esc(r.sec)+"s</span><div class='muted'>"+esc(r.last)+"</div>";
    }}
    if(j.running_id){{const c=q("st_"+j.running_id);if(c)c.innerHTML="<span class='muted'>測試中…</span>";}}
    q("tsum").textContent="自測 "+Object.keys(done).length+"/"+(j.total||0)+" · 綠 "+ok+" · 非綠 "+bad+(j.running?" · 進行中(跑完才能啟動)":"");
    if(j.running){{setTimeout(poll,700);}}else{{testing=false;q("b_test").disabled=false;lock(false);}}
  }}).catch(()=>{{testing=false;q("b_test").disabled=false;lock(false);}});
}}
q("b_test").onclick=()=>{{
  testing=true;q("b_test").disabled=true;lock(false);
  post("/selftest",{{}}).then(({{ok,j}})=>{{if(!ok){{q("tsum").textContent="沒開始:"+(j.why||"");testing=false;q("b_test").disabled=false;lock(false);return;}}poll();}});
}};
</script></body></html>"""


def _decision_card(dec: dict | None) -> str:
    if not dec:
        return ""
    if dec.get("action") != "launch":
        return f"<div class='card'><h2>本次輸入參數</h2><div class='muted'>這次沒有啟動({_e(dec.get('action'))})</div></div>"
    steps = dec.get("steps") or []
    return (f"<div class='card'><h2>本次輸入參數</h2><table><tr><th>項</th><th>值</th></tr>"
            f"<tr><td>模式</td><td>{'預設' if dec.get('mode') == 'default' else '自訂(頁上勾的)'}</td></tr>"
            f"<tr><td>起 → 訖</td><td>{_e(dec.get('since'))} → {_e(dec.get('until'))}(截止=今天)</td></tr>"
            f"<tr><td>步({len(steps)})</td><td><code>{_e(', '.join(steps))}</code></td></tr>"
            f"<tr><td>檔數</td><td>全市場,沒有上限</td></tr>"
            f"<tr><td>只看計畫 · 不自癒</td><td>{'是' if dec.get('dry') else '否'} · {'是' if dec.get('noheal') else '否'}</td></tr>"
            f"<tr><td>決定時間</td><td>{_e(dec.get('ts'))}</td></tr></table></div>")


def _lanes_card(lr: dict | None, dec: dict | None) -> str:
    if not lr:
        return ""
    if lr.get("state") == "ABSENT":
        return f"<div class='card'><h2>各步結果 {_chip('ABSENT')}</h2><div class='muted'>{_e(lr.get('why'))}</div></div>"
    picked = set((dec or {}).get("steps") or [])
    rows = ""
    for s in lr.get("steps") or []:
        mark = "" if not picked or s.get("id") in picked else " <span class='muted'>(這次沒勾)</span>"
        rows += (f"<tr><td><b>{_e(s.get('id'))}</b>{mark}</td><td>{_e(s.get('zh'))}</td><td>{_e(s.get('chain'))}</td><td>{_chip(s.get('state'))}</td>"
                 f"<td class='num'>{_e(s.get('rc'))}</td><td class='num'>{_e(s.get('sec'))}</td><td>{_e(s.get('note'))}"
                 + (f"<div class='muted'><code>{_e(s.get('log'))}</code></div>" if s.get("log") else "") + "</td></tr>")
    head = (f"<div class='muted'>CGC_MDL134 <code>{_e(lr.get('file'))}</code> · {_e(lr.get('stamp'))} · {'DRY' if lr.get('dry') else 'LIVE'} · "
            f"{'線上' if lr.get('online') else '離線'} · 綠 {_e(lr.get('n_ok'))} · 紅 {_e(lr.get('n_fail'))} · 略 {_e(lr.get('n_skip'))} · {_e(lr.get('sec'))}s"
            + (f" · {_e(lr.get('note'))}" if lr.get("note") else "") + "</div>")
    stale = ""
    try:   # 報告比本次決定早 = 那是上一次跑的結果(例如這次根本沒起跑),講明,不冒充這一次
        if dec and dec.get("ts") and lr.get("stamp") and datetime.strptime(str(lr["stamp"]), "%Y%m%d_%H%M%S") < datetime.strptime(str(dec["ts"]), "%Y-%m-%d %H:%M:%S"):
            stale = "<div class='bad' style='margin-top:6px'>這份報告比本次決定早:是上一次跑的結果,不是這一次的(這次可能沒起跑或還沒跑完)。</div>"
    except Exception:
        stale = ""
    return (f"<div class='card'><h2>各步結果 {_chip(lr.get('state'))}</h2>{head}{stale}"
            f"<div class='scroll'><table style='margin-top:8px'><tr><th>步</th><th>資料</th><th>鏈</th><th>燈</th><th class='num'>rc</th><th class='num'>秒</th><th>說明 · 紀錄檔</th></tr>{rows}</table></div>"
            f"<div class='muted' style='margin-top:6px'>紅的那一步照紀錄檔修;這一頁只排版,燈號由 CGC_MDL134 判。</div></div>")


def render_status(st: dict, dec: dict | None = None, lr: dict | None = None) -> str:
    dbs = ""
    n = 0
    for d in st.get("dbs") or []:
        for t in d.get("tables") or []:
            if n >= 80:
                break
            n += 1
            dbs += (f"<tr><td>{_e(d.get('name'))}</td><td>{_e(t.get('table'))}</td><td class='num'>{int(t.get('rows') or 0):,}</td>"
                    f"<td>{_e(t.get('lo') or '-')}</td><td>{_e(t.get('hi') or '-')}</td><td>{_e(t.get('err') or '')}</td></tr>")
    rf = st.get("refresh") or {}
    return f"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>VDF 資料庫狀況</title><style>{_CSS}</style></head><body><main>
<h1>VDF 資料庫狀況 {_chip(st.get('verdict'))}</h1><div class="sub">VDF_ENG093 v{_e(VERSION)} · {_e(st.get('ts'))}{(' · 目錄剛重點:' + _e(rf.get('state')) + (' ' + _e(rf.get('why')) if rf.get('why') else '')) if rf else ''}</div>
{_decision_card(dec)}{_lanes_card(lr, dec)}
{_db_cards(st, 30)}
<div class="card"><h2>逐表(前 80 張)</h2>{('<table><tr><th>庫</th><th>表</th><th class="num">列</th><th>最早</th><th>最新</th><th>錯</th></tr>' + dbs + '</table>') if dbs else '<div class="muted">目錄裡沒有表</div>'}
{('<div class="muted" style="margin-top:6px">同名表出現在兩本以上的庫:' + _e(', '.join(st.get('dup') or [])) + '(分類取最新那一本)</div>') if st.get('dup') else ''}</div>
<div class="muted">資料來源:CGC_MDL123 目錄 · CGC_MDL153 分類 · VDF_ENG089 缺口與新鮮度 · CGC_MDL134 各步結果(逐格委派,本頁不另算)。</div>
</main></body></html>"""


# ---------------------------------------------------------------- 問:本機頁(127.0.0.1 · 一次性權杖 · 同源 POST)
def _write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".ask_", suffix=".json", dir=str(path.parent))
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def make_server(page: str, token: str, defaults: dict, allowed: list, port: int = 0, engines: dict | None = None, runner=None):
    """本機頁伺服器。v0101 多一條 /selftest:逐一引擎自測在背景一支一支跑(不並行、不搶庫),跑的時候不收「啟動」。"""
    engines = dict(engines or {})
    runner = runner or engine_selftest
    state = {"decision": None, "event": threading.Event(),
             "st": {"running": False, "running_id": "", "done": {}, "total": len(engines), "stop": False, "thread": None}}

    def _selftest_all():
        st = state["st"]
        try:
            for sid, path in engines.items():
                if st["stop"]:
                    break
                st["running_id"] = sid
                try:
                    st["done"][sid] = runner(path)
                except Exception as exc:
                    st["done"][sid] = {"state": "FAIL", "rc": None, "sec": 0, "last": f"測試台自己炸了:{type(exc).__name__}"}
        finally:
            st["running"], st["running_id"] = False, ""

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            return

        def _hdr(self, code: int, ctype: str, n: int):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(n))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Security-Policy",
                             "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'self'; "
                             "form-action 'none'; frame-ancestors 'none'; base-uri 'none'")
            self.end_headers()

        def _send(self, code: int, obj):
            b = (json.dumps(obj, ensure_ascii=False) if not isinstance(obj, str) else obj).encode("utf-8")
            self._hdr(code, "application/json; charset=utf-8" if not isinstance(obj, str) else "text/plain; charset=utf-8", len(b))
            self.wfile.write(b)

        def _host_ok(self) -> bool:
            return self.headers.get("Host", "") == f"127.0.0.1:{self.server.server_port}"

        def _tok_ok(self, got) -> bool:
            return hmac.compare_digest(str(got or ""), token)

        def do_GET(self):
            u = urlparse(self.path)
            if not self._host_ok():
                return self._send(403, "host")
            if u.path == "/decide":
                return self._send(405, "POST only")
            if u.path not in ("/", "/selftest"):
                return self._send(404, "not found")
            if not self._tok_ok((parse_qs(u.query).get("t") or [""])[0]):
                return self._send(403, "token")
            if u.path == "/selftest":
                st = state["st"]
                return self._send(200, {"running": st["running"], "running_id": st["running_id"], "done": st["done"], "total": st["total"]})
            b = page.encode("utf-8")
            self._hdr(200, "text/html; charset=utf-8", len(b))
            self.wfile.write(b)

        def do_POST(self):
            u = urlparse(self.path)
            if u.path not in ("/decide", "/selftest"):
                return self._send(404, {"why": "not found"})
            if not self._host_ok() or self.headers.get("Origin", "") != f"http://127.0.0.1:{self.server.server_port}":
                return self._send(403, {"field": "origin", "why": "只收本頁同源送出"})
            if not self.headers.get("Content-Type", "").startswith("application/json"):
                return self._send(415, {"field": "content-type", "why": "只收 JSON"})
            n = int(self.headers.get("Content-Length") or 0)
            if n <= 0 or n > BODY_MAX:
                return self._send(413, {"field": "body", "why": "空的或太大"})
            try:
                body = json.loads(self.rfile.read(n).decode("utf-8"))
            except Exception:
                return self._send(400, {"field": "body", "why": "不是 JSON"})
            if not isinstance(body, dict) or not self._tok_ok(body.get("t", "")):
                return self._send(403, {"field": "t", "why": "權杖不對"})
            if state["decision"] is not None:
                return self._send(409, {"field": "action", "why": "已經決定過了"})
            st = state["st"]
            if u.path == "/selftest":
                if st["running"]:
                    return self._send(409, {"field": "selftest", "why": "自測還在跑"})
                if not engines:
                    return self._send(409, {"field": "selftest", "why": "沒有可測的引擎"})
                st.update(running=True, done={}, stop=False, total=len(engines))
                st["thread"] = threading.Thread(target=_selftest_all, daemon=True)
                st["thread"].start()
                return self._send(200, {"ok": True, "total": len(engines)})
            ok, res = validate(body, defaults, allowed)
            if not ok:
                return self._send(400, res)
            if res.get("action") == "launch" and st["running"]:
                return self._send(409, {"field": "selftest", "why": "引擎自測還在跑,跑完再啟動(免得兩邊搶同一本庫)"})
            res["ts"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            res["source"] = "ui"
            state["decision"] = res
            self._send(200, {"ok": True, "decision": res})
            state["event"].set()

    srv = ThreadingHTTPServer(("127.0.0.1", port), H)
    srv.daemon_threads = True
    return srv, state


def serve_ask(page: str, token: str, defaults: dict, allowed: list, out: Path, open_browser: bool, timeout: int,
              port: int = 0, engines: dict | None = None, runner=None) -> tuple:
    srv, state = make_server(page, token, defaults, allowed, port, engines, runner)
    url = f"http://127.0.0.1:{srv.server_port}/?t={token}"
    th = threading.Thread(target=srv.serve_forever, daemon=True)
    th.start()
    # 一定要 flush:在 Invoke-VIAPython 底下 stdout 導到檔(區塊緩衝),不 flush 這行要等行程結束才落檔——
    # Open-VIA-VDF 就拿不到網址去 via-open,操作員也看不到網址(頁不跳、等滿逾時)。自測 ⑨ 把這件事釘住。
    print(f"  [VDF 啟動台] 頁:{url}", flush=True)
    print("  [VDF 啟動台] 等你在頁上選「用預設參數啟動 / 用下面勾的啟動 / 不啟動」" + (f"(最多 {timeout // 60} 分鐘)" if timeout >= 60 else ""), flush=True)
    if open_browser:
        try:
            import webbrowser
            if not webbrowser.open(url):   # 零跳出閘 VIA_NO_OPEN=1(SUP_MDL737)會讓它靜默回 False
                print("  [VDF 啟動台] 沒開成瀏覽器(零跳出閘或沒有瀏覽器):via-open <上面的網址>,或手動貼進瀏覽器", flush=True)
        except Exception as exc:
            print(f"  [VDF 啟動台] 沒開成瀏覽器({type(exc).__name__}):via-open <上面的網址>,或手動貼進瀏覽器", flush=True)
    got = state["event"].wait(timeout if timeout > 0 else None)
    st = state["st"]
    st["stop"] = True                      # 決定了(或逾時):還沒測的不再開;正在測的那一支跑完就停,不留孤兒行程
    if st.get("thread") is not None:
        st["thread"].join(SELFTEST_TIMEOUT + 5)
    srv.shutdown()
    srv.server_close()
    decision = state["decision"] if got and state["decision"] else {"action": "timeout", "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "source": "ui"}
    if st["done"]:
        decision["selftest"] = st["done"]
    _write_json(out, decision)
    return decision, url


# ---------------------------------------------------------------- 動詞
def _arg(a: list, flag: str, default=None):
    if flag in a:
        i = a.index(flag)
        if i + 1 < len(a) and not a[i + 1].startswith("--"):
            return a[i + 1]
    return default


def cmd_ask(a: list) -> int:
    out = Path(_arg(a, "--out") or (OUT_DIR / "ASK_DECISION_latest.json"))
    timeout = int(_arg(a, "--timeout", "900"))
    port = int(_arg(a, "--port", "0"))
    cat = _arg(a, "--catalog")
    d = launcher_defaults()
    mx = steps_matrix(d["since"], d["steps"] or None)
    allowed = [s for s in d["steps"] if any(r["id"] == s and not r.get("missing") and r.get("engine_ok") for r in mx["rows"])]
    ctx = {"ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "defaults": d, "matrix": mx, "allowed": allowed,
           "db": db_state(Path(cat) if cat else None), "ready": readiness()}
    token = secrets.token_urlsafe(24)
    page = render_ask(ctx, token)
    engines = {r["id"]: r["engine_path"] for r in mx["rows"] if not r.get("missing") and r.get("engine_ok")}
    decision, _url = serve_ask(page, token, d, allowed, out, open_browser=("--open" in a), timeout=timeout, port=port, engines=engines)
    act = decision.get("action")
    if act == "launch":
        steps = decision.get("steps") or []
        print(f"  [VDF 啟動台] 決定:啟動 · 起 {decision['since']} → 訖 {decision['until']}(今天)· 步 {len(steps)}/{len(allowed)}:"
              f"{','.join(steps)} · 全市場無上限 · {'只看計畫' if decision['dry'] else '真跑'}{' · 不自癒' if decision['noheal'] else ''}"
              f"({decision.get('mode')})→ {out}", flush=True)
        return 0
    if act == "cancel":
        print(f"  [VDF 啟動台] 決定:不啟動 → {out}", flush=True)
        return 0
    print(f"  [VDF 啟動台] 逾時沒收到決定 → 不啟動(NODATA)· {out}", flush=True)
    return 2


def cmd_status(a: list) -> int:
    cat = _arg(a, "--catalog")
    out_dir = Path(_arg(a, "--out-dir") or OUT_DIR)
    dec_p = _arg(a, "--decision")
    dec = None
    if dec_p:
        try:
            dec = json.loads(Path(dec_p).read_text(encoding="utf-8"))
        except Exception:
            dec = None
    lanes_dir = _arg(a, "--lanes-dir")
    lr = lanes_result(Path(lanes_dir) if lanes_dir else None)
    st = db_state(Path(cat) if cat else None, refresh=("--refresh" in a))
    out_dir.mkdir(parents=True, exist_ok=True)
    page = out_dir / "VDF_DB_STATUS_latest.html"
    page.write_text(render_status(st, dec, lr), encoding="utf-8")
    _write_json(out_dir / "VDF_DB_STATUS_latest.json", {**{k: v for k, v in st.items() if k not in ("dbs",)}, "decision": dec,
                                                         "lanes": {k: v for k, v in lr.items() if k != "steps"}})
    fr, sm, pl = st.get("fresh") or {}, st.get("summary") or {}, st.get("plan") or {}
    if lr.get("state") != "ABSENT":
        print(f"  [擷取結果] {lr.get('state')} · 綠 {lr.get('n_ok')} · 紅 {lr.get('n_fail')} · 略 {lr.get('n_skip')} · {lr.get('file')}", flush=True)
        for s in lr.get("steps") or []:
            if s.get("state") != "OK":
                print(f"     [{s.get('state'):<5}] {s.get('id')} · rc {s.get('rc')} · {str(s.get('note') or '')[:110]}", flush=True)
    print(f"  [VDF 資料庫狀況] {st['verdict']} · 目錄 {fr.get('state')} {fr.get('catalog_ts') or ''} · 分類 {sm.get('verdict')} · "
          f"缺口 {pl.get('n_gap', '-')}/{pl.get('n_tables', '-')}")
    for c in (sm.get("categories") or [])[:9]:
        print(f"     [{c.get('lamp'):<6}] {c.get('cat')} · 表 {c.get('n')} · 最新 {c.get('newest') or '-'} · 最壞滯後 {c.get('worst_lag') if c.get('worst_lag') is not None else '?'} 日")
    # 頁路徑獨佔一行、絕對路徑、flush:Open-VIA-VDF 從這一行取路徑交給 via-open(只走瀏覽器 exe,不經 .html 預設程式)
    print(f"  [VDF 資料庫狀況] 頁:{page.resolve()}", flush=True)
    if "--json" in a:
        print(json.dumps({k: v for k, v in st.items() if k not in ("dbs", "tables")}, ensure_ascii=False, indent=1, default=str))
    if "--open" in a:
        try:
            import webbrowser
            if not webbrowser.open(page.resolve().as_uri()):   # 零跳出閘 VIA_NO_OPEN=1 會讓它靜默回 False
                print("  [VDF 資料庫狀況] 沒開成瀏覽器(零跳出閘或沒有瀏覽器):via-open <上面的頁>", flush=True)
        except Exception as exc:
            print(f"  [VDF 資料庫狀況] 沒開成瀏覽器({type(exc).__name__}):via-open <上面的頁>", flush=True)
    return st["rc"]


USAGE = f"""VDF_ENG093_LaunchConsole v{VERSION} — VDF 一鍵啟動台
  ask    [--open] [--out <決定.json>] [--timeout 900] [--port 0] [--catalog <目錄.json>]
         起本機頁(127.0.0.1 · 一次性權杖 · 同源 POST):起始日期(YYYY-MM-DD)· 截止日期=今天 · 沒有檔數上限(要抓就全抓)·
         要抓的資料矩陣(步 × 引擎 × 實際參數 × 兩道橋;逐格委派 CGC_MDL125 / CGC_MDL134)· 逐一引擎自測 · 啟動就緒 · 啟動前資料庫狀況;
         你選「用預設參數啟動 / 用下面勾的啟動 / 不啟動」→ 寫決定檔(since · until · steps · dry · noheal)→ rc0;逾時 rc2(不啟動)
  status [--refresh] [--open] [--out-dir <夾>] [--catalog <目錄.json>] [--decision <決定.json>] [--lanes-dir <夾>] [--json]
         (--refresh 先委派 CGC_MDL123 重點目錄)→ 本次輸入參數 · 各步結果(CGC_MDL134 最近一次跑)· 分類燈 · 增量缺口 · 逐表
         → VIA_Reports/vdf_console/VDF_DB_STATUS_latest.html;rc:0 全綠 · 2 落後或過期 · 3 沒有目錄 · 1 正主壞
  --selftest
  --open 才試開瀏覽器(house 零跳出律;VIA_NO_OPEN=1 時靜默不開)。兩個動詞都把「頁:<網址或絕對路徑>」獨佔一行印出並 flush,
         一鍵啟動腳本 Open-VIA-VDF 取那一行交給 via-open(只走瀏覽器 exe)"""


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a or "--self-test" in a:
        return selftest()
    verb = a[0] if a else ""
    if verb == "ask":
        return cmd_ask(a[1:])
    if verb == "status":
        return cmd_status(a[1:])
    print(USAGE)
    return 0 if verb in ("help", "-h", "--help") else 2


# ---------------------------------------------------------------- 自測(零網路 · 只寫暫存 · 正負控)
def selftest() -> int:
    import ast
    import socket
    import subprocess
    import time
    import urllib.error
    import urllib.request
    okn, bad, nod = [], [], []

    def chk(name, cond, why=""):
        (okn if cond else bad).append(name)
        print(("  ✓ " + name) if cond else f"  [FAIL] {name} — {why}")

    print(f"🧪 VDF_ENG093_LaunchConsole v{VERSION} --selftest(零網路 · 只寫暫存)")
    src = Path(__file__).read_text(encoding="utf-8")
    need = ["main", "cmd_ask", "cmd_status", "validate", "render_ask", "render_status", "serve_ask", "tables_from_catalog", "db_state",
            "launcher_defaults", "steps_matrix", "lanes_result", "engine_selftest"]
    miss = [n for n in need if n not in globals()]
    chk(f"① 宣告符號齊備({len(need)} 個)", not miss, f"缺 {miss}")
    chk("② 橋接件完好(ACCEL/NET)", "[VIA:ACCEL-BRIDGE:" in src and "[VIA:NET-BRIDGE:" in src, "檔頭橋標記不全")

    d_real = launcher_defaults()
    d_syn = launcher_defaults('param(\n    [string]$Since = "2024-02-03",\n    [string]$Year = "2023"\n)\n$stepBook = "a_1,b_2"\n')
    d_old = launcher_defaults('param(\n    [string]$Year = "2022"\n)\n$steps = "c_3"\n')
    d_neg = launcher_defaults("param([switch]$Dry)")
    real_ok = (not d_real["launcher"]) or (d_real["from_launcher"] and d_real["steps_from_launcher"] and len(d_real["steps"]) >= 1)
    chk("③ 預設起始日與步清單讀自啟動器正本(-Since 優先,沒有退 -Year 的 1/1;$stepBook 那一行,舊版 $steps 也認)· 負控:讀不到就講明並退 2023-01-01、步清單空",
        real_ok and d_syn["since"] == "2024-02-03" and d_syn["steps"] == ["a_1", "b_2"]
        and d_old["since"] == "2022-01-01" and d_old["steps"] == ["c_3"]
        and not d_neg["from_launcher"] and d_neg["since"] == "2023-01-01" and d_neg["steps"] == [] and bool(d_neg["why"]),
        f"real {d_real} syn {d_syn} neg {d_neg}")

    dfl = {"since": "2023-01-01", "steps": ["hist_2023", "fred", "global"], "dry": False, "noheal": False}
    allowed = ["hist_2023", "global", "fred"]
    today = date(2026, 9, 23)
    ok1, r1 = validate({"action": "launch", "mode": "custom", "since": "2024-03-15", "steps": ["fred", "hist_2023"], "dry": True, "noheal": False},
                       dfl, allowed, today)
    ok2, r2 = validate({"action": "launch", "mode": "default", "since": "1999-01-01", "steps": ["fred"]}, dfl, allowed, today)
    negs = [({"action": "launch", "mode": "custom", "since": "2024/03/15", "steps": ["fred"]}, "since"),
            ({"action": "launch", "mode": "custom", "since": "2024-02-30", "steps": ["fred"]}, "since"),
            ({"action": "launch", "mode": "custom", "since": "2026-09-24", "steps": ["fred"]}, "since"),
            ({"action": "launch", "mode": "custom", "since": "1989-12-31", "steps": ["fred"]}, "since"),
            ({"action": "launch", "mode": "custom", "since": "2024-03-15", "steps": []}, "steps"),
            ({"action": "launch", "mode": "custom", "since": "2024-03-15", "steps": "fred"}, "steps"),
            ({"action": "launch", "mode": "custom", "since": "2024-03-15", "steps": ["nope"]}, "steps"),
            ({"action": "launch", "mode": "custom", "since": "2024-03-15", "steps": ["fred", "fred"]}, "steps"),
            ({"action": "launch", "mode": "custom", "since": "2024-03-15", "steps": ["fred"], "dry": "yes"}, "dry"),
            ({"action": "launch", "mode": "custom", "since": "2024-03-15", "steps": ["fred"], "limit": 100}, "limit"),
            ({"action": "launch", "mode": "custom", "year": "2024", "steps": ["fred"]}, "year"),
            ({"action": "launch", "mode": "custom", "since": "2024-03-15", "until": "2025-01-01", "steps": ["fred"]}, "until"),
            ({"action": "launch", "mode": "custom", "since": "2024-03-15", "steps": ["fred"], "consent": True}, "consent"),
            ({"action": "rm -rf"}, "action")]
    neg_res = [validate(b, dfl, allowed, today) for b, _f in negs]
    neg_ok = all((not r[0]) and r[1].get("field") == f for r, (_b, f) in zip(neg_res, negs))
    lim_msg = "全抓" in (neg_res[9][1].get("why") or "")
    ok3, r3 = validate({"action": "launch", "mode": "default"}, dfl, [], today)
    chk(f"④ 參數驗證:正控(自訂 2024-03-15 · 兩步依啟動器順序排 · 截止=今天;預設模式忽略頁上亂填)· 負控 {len(negs)} 條逐欄點名"
        "(日期格式/假日期/未來/太早/空步/非清單/不認得/重複/旗標型別/送 limit 被拒且講明全抓/year/until/consent/亂動作)· 步清單讀不到=不能啟動",
        ok1 and r1 == {"action": "launch", "mode": "custom", "since": "2024-03-15", "until": "2026-09-23", "steps": ["hist_2023", "fred"],
                       "dry": True, "noheal": False}
        and ok2 and r2["since"] == "2023-01-01" and r2["steps"] == allowed and r2["until"] == "2026-09-23"
        and neg_ok and lim_msg and (not ok3) and r3.get("field") == "steps",
        f"{r1} {r2} neg {[(r[1].get('field'), f) for r, (_b, f) in zip(neg_res, negs)]} lim {lim_msg} r3 {r3}")

    # ⑤⑨⑪ 要真的連得上回送介面(只綁得上不算:網路命名空間裡 lo 沒起時綁得上、連不上)
    try:
        _ls = socket.socket()
        _ls.bind(("127.0.0.1", 0))
        _ls.listen(1)
        socket.create_connection(_ls.getsockname(), timeout=2).close()
        _ls.close()
        loop_ok = True
    except OSError:
        loop_ok = False
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))   # 本機往返不走任何代理(不改環境變數)

    def req(base, method, path, body=None, origin=None, ctype="application/json"):
        data = json.dumps(body).encode("utf-8") if body is not None else None
        r = urllib.request.Request(base + path, data=data, method=method)
        r.add_header("Origin", origin if origin is not None else base)
        if data is not None:
            r.add_header("Content-Type", ctype)
        try:
            with opener.open(r, timeout=5) as resp:
                return resp.status, resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode("utf-8", "replace")

    real_today = date.today().isoformat()
    if not loop_ok:
        nod.append("⑤")
        print("  ⑤ 本機頁往返 — NODATA(本境沒有回送介面)")
    else:
        td = Path(tempfile.mkdtemp(prefix="eng093_"))
        tok = "T" + secrets.token_urlsafe(12)
        srv, state = make_server("<!doctype html><p>ok</p>", tok, dfl, allowed)
        base = f"http://127.0.0.1:{srv.server_port}"
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        try:
            codes = (req(base, "GET", "/")[0], req(base, "GET", "/?t=" + tok)[0], req(base, "GET", "/decide")[0],
                     req(base, "POST", "/decide", {"t": "x", "action": "cancel"})[0],
                     req(base, "POST", "/decide", {"t": tok, "action": "cancel"}, origin="http://evil.example")[0])
            p_since, pb = req(base, "POST", "/decide", {"t": tok, "action": "launch", "mode": "custom", "since": "abc", "steps": ["fred"]})
            p_lim, pl = req(base, "POST", "/decide", {"t": tok, "action": "launch", "mode": "custom", "since": "2024-01-02", "steps": ["fred"], "limit": 5})
            p_ok, _po = req(base, "POST", "/decide", {"t": tok, "action": "launch", "mode": "custom", "since": "2024-01-02", "steps": ["global"], "dry": True, "noheal": False})
            p_again, _ = req(base, "POST", "/decide", {"t": tok, "action": "cancel"})
        finally:
            srv.shutdown()
            srv.server_close()
        dec = state["decision"] or {}
        chk("⑤ 本機頁往返:無權杖 403 · 帶權杖 200 · GET /decide 405 · 錯權杖 403 · 跨源 403 · 壞起始日 400 點名 since · 送 limit 400 點名 limit · 正確 200 · 第二次 409",
            codes == (403, 200, 405, 403, 403) and (p_since, p_lim, p_ok, p_again) == (400, 400, 200, 409)
            and '"since"' in pb and '"limit"' in pl and dec.get("since") == "2024-01-02" and dec.get("steps") == ["global"]
            and dec.get("until") == real_today and dec.get("dry") is True,
            f"{codes} {(p_since, p_lim, p_ok, p_again)} dec {dec}")
        # ⑥ 逾時誠實:沒人按 → action=timeout、決定檔照寫(PowerShell 靠它判斷不啟動)
        out6 = td / "ask.json"
        with contextlib.redirect_stdout(io.StringIO()):
            d6, _u = serve_ask("<p>x</p>", "t6", dfl, allowed, out6, open_browser=False, timeout=1)
        j6 = json.loads(out6.read_text(encoding="utf-8")) if out6.exists() else {}
        chk("⑥ 逾時 → action=timeout 且決定檔照寫(不啟動)", d6.get("action") == "timeout" and j6.get("action") == "timeout", f"{d6} {j6}")

    # ⑦ 資料庫狀況委派 + 本次輸入參數 + 各步結果(合成目錄與合成擷取道報告,全在暫存)
    td7 = Path(tempfile.mkdtemp(prefix="eng093c_"))
    t0 = date.today()
    d1 = t0.fromordinal(t0.toordinal() - 1).isoformat()
    d30 = t0.fromordinal(t0.toordinal() - 30).isoformat()
    cat = {"ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "dbs": [
        {"name": "vdf_tw_market.duckdb", "path": "x", "tables": [
            {"table": "tw_daily_prices", "rows": 1000, "date_col": "date", "lo": "2023-01-03", "hi": d1, "err": ""},
            {"table": "tw_chip_daily", "rows": 500, "date_col": "date", "lo": "2023-01-03", "hi": d30, "err": ""}]},
        {"name": "legacy.duckdb", "path": "y", "tables": [
            {"table": "tw_daily_prices", "rows": 10, "date_col": "date", "lo": "2020-01-02", "hi": "2020-12-31", "err": ""}]}]}
    cp = td7 / "cat.json"
    cp.write_text(json.dumps(cat), encoding="utf-8")
    lanes = td7 / "lanes"
    lanes.mkdir()
    (lanes / "LANES_20260101_000000.json").write_text(json.dumps({"state": "PART", "stamp": "20260101_000000", "steps": [
        {"id": "hist_2023", "zh": "舊的", "state": "OK"}]}), encoding="utf-8")
    (lanes / "LANES_20260102_000000.json").write_text(json.dumps({"state": "PART", "stamp": "20260102_000000", "dry": False, "online": True,
        "n_ok": 1, "n_fail": 1, "n_skip": 0, "sec": 12.5, "steps": [
            {"id": "hist_2023", "zh": "台股史深", "chain": "tw", "state": "OK", "rc": 0, "sec": 9.1, "note": ""},
            {"id": "fred", "zh": "FRED 宏觀", "chain": "gl", "state": "FAIL", "rc": 1, "sec": 3.4, "note": "FRED 鑰缺", "log": "VIA_Reports/lanes/RUN_x/fred.log"}]}),
        encoding="utf-8")
    (lanes / "LANES_20260103_000000.json").write_text(json.dumps({"state": "PLAN", "stamp": "20260103_000000", "steps": []}), encoding="utf-8")
    decp = td7 / "dec.json"
    decp.write_text(json.dumps({"action": "launch", "mode": "custom", "since": "2024-03-15", "until": "2026-09-23",
                                "steps": ["hist_2023", "fred"], "dry": False, "noheal": False, "ts": "2026-09-23 10:00:00"}), encoding="utf-8")
    tbl, dup = tables_from_catalog(cat, t0)
    st7 = db_state(cp)
    gate_ok = owner("gate") is not None and owner("summary") is not None
    buf7 = io.StringIO()
    with contextlib.redirect_stdout(buf7):
        rc7 = cmd_status(["--catalog", str(cp), "--out-dir", str(td7 / "out"), "--decision", str(decp), "--lanes-dir", str(lanes)])
    page7 = td7 / "out" / "VDF_DB_STATUS_latest.html"
    txt7 = page7.read_text(encoding="utf-8") if page7.exists() else ""
    m7 = re.search(r"^\s*\[VDF 資料庫狀況\] 頁:(.+?)\s*$", buf7.getvalue(), re.M)
    line7 = bool(m7) and Path(m7.group(1)).is_absolute() and Path(m7.group(1)).resolve() == page7.resolve()
    lr7 = lanes_result(lanes)
    absent = db_state(td7 / "no_such_catalog.json")
    if not gate_ok:
        nod.append("⑦")
        print("  ⑦ 資料庫狀況委派 — NODATA(正主不在:" + str({k: v.get("why") for k, v in _OWN.items() if v.get("why")}) + ")")
    else:
        chk("⑦ 資料庫狀況:同名表取最新那一本 · 分類燈委派 CGC_MDL153 · 缺口委派 VDF_ENG089 · 頁上有「本次輸入參數」與「各步結果」"
            "(取最近一次非 PLAN 報告,紅步帶紀錄檔)· 主控台印紅步 · 「頁:」獨佔一行絕對路徑 · 負控:目錄不在=ABSENT rc3",
            line7 and tbl["tw_daily_prices"]["db"] == "vdf_tw_market.duckdb" and dup == ["tw_daily_prices"]
            and any(c.get("cat") == "籌碼" and c.get("lamp") == "RED" for c in (st7.get("summary") or {}).get("categories") or [])
            and (st7.get("plan") or {}).get("state") == "OK" and rc7 == 2 and "本次輸入參數" in txt7 and "各步結果" in txt7
            and "2024-03-15" in txt7 and "fred.log" in txt7 and lr7.get("file") == "LANES_20260102_000000.json" and "上一次跑的結果" in txt7
            and "[FAIL ] fred" in buf7.getvalue() and absent["verdict"] == "ABSENT" and absent["rc"] == 3,
            f"line {line7} rc {rc7} lanes {lr7.get('file')} absent {absent['verdict']} out {buf7.getvalue()[-300:]!r}")

    # ⑩ 要抓的資料矩陣:逐格委派 CGC_MDL125 步冊 + CGC_MDL134 鏈;參數照起始日算;全抓(不帶 --limit);負控:不認得的步=缺列
    keep = os.environ.get("VIA_HIST_SINCE")
    mx = steps_matrix("2024-02-03", d_real["steps"] or None)
    mx_neg = steps_matrix("2024-02-03", ["no_such_step"])
    env_back = os.environ.get("VIA_HIST_SINCE") == keep
    rows = {r["id"]: r for r in mx["rows"]}
    if not mx["rows"] or "fixall" not in mx["src"]:
        nod.append("⑩")
        print("  ⑩ 要抓的資料矩陣 — NODATA(步冊不在:" + str(mx.get("why")) + ")")
    else:
        h, rv = rows.get("hist_2023") or {}, rows.get("revenue_backfill") or {}
        hk = {t["k"]: t["t"] for t in h.get("args") or [] if t.get("k")}
        rk = {t["k"]: t["t"] for t in rv.get("args") or [] if t.get("k")}
        order_ok = (not d_real["steps"]) or [r["id"] for r in mx["rows"]] == d_real["steps"]
        chk("⑩ 要抓的資料矩陣:列序=啟動器步清單 · 引擎尾版都在 · hist_2023 帶起始日與今天 · 月營收帶起始月 · 沒有一步帶 --limit(全抓)"
            " · 觸網/鏈取自正主 · 環境用完即還原 · 負控:不認得的步=缺列",
            order_ok and all(r.get("engine_ok") for r in mx["rows"]) and hk.get("since") == "2024-02-03" and hk.get("until") == real_today
            and rk.get("since_month") == "2024-02" and not any(t["t"] == "--limit" for r in mx["rows"] for t in r.get("args") or [])
            and h.get("net") is True and bool(h.get("chain")) and env_back and mx_neg["rows"] and mx_neg["rows"][0].get("missing") is True,
            f"order {order_ok} hist {hk} rev {rk} env {env_back} neg {mx_neg['rows'][:1]}")

    # ⑧ 零寫同意閘(AST)· 兩頁零外部資源(零 CDN)
    tree = ast.parse(src)
    writes = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AugAssign)):
            for t in (node.targets if isinstance(node, ast.Assign) else [node.target]):
                if isinstance(t, ast.Subscript) and "CONSENT" in ast.dump(t):
                    writes.append(getattr(node, "lineno", 0))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in ("putenv", "setdefault", "update"):
            if "CONSENT" in ast.dump(node):
                writes.append(getattr(node, "lineno", 0))
    ctx = {"ts": "t", "defaults": {**dfl, "launcher": "x", "from_launcher": True}, "matrix": mx, "allowed": allowed, "db": st7,
           "ready": {"state": "OK", "gates": {}, "hist_limit": {}}}
    pages = render_ask(ctx, "tok") + render_status(st7, json.loads(decp.read_text(encoding="utf-8")), lr7)
    ext = re.findall(r"(?:src|href)\s*=\s*[\"']?(https?://[^\"' >]+)", pages)
    chk("⑧ 本檔零寫同意閘(AST)· 兩頁零外部資源(零 CDN)· 問參數頁沒有檔數上限欄", not writes and not ext and "id=\"limit\"" not in pages,
        f"寫閘行 {writes} 外部 {ext[:3]}")

    # ⑨ 呼叫端拿得到網址:stdout 導到檔(同 Invoke-VIAPython:區塊緩衝)時,「頁:網址」要在還沒決定之前就落檔
    if not loop_ok:
        nod.append("⑨")
        print("  ⑨ 導檔 stdout 先見網址 — NODATA(本境沒有回送介面)")
    else:
        td9 = Path(tempfile.mkdtemp(prefix="eng093p_"))
        so9, se9, dec9 = td9 / "stdout.txt", td9 / "stderr.txt", td9 / "ask.json"
        env9 = {k: v for k, v in os.environ.items() if k != "PYTHONUNBUFFERED"}   # 不讓環境替本檔 flush:照 Invoke-VIAPython 的樣子跑
        env9["PYTHONIOENCODING"] = "utf-8"
        seen9, code9, rc9, why9 = False, None, None, ""
        with open(so9, "wb") as fo, open(se9, "wb") as fe:
            p9 = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "ask", "--out", str(dec9), "--timeout", "60", "--catalog", str(cp)],
                                  stdout=fo, stderr=fe, env=env9)
            try:
                m9, t_end = None, time.monotonic() + 120
                while m9 is None and p9.poll() is None and time.monotonic() < t_end:
                    m9 = re.search(r"頁:(http://127\.0\.0\.1:(\d+)/\?t=([A-Za-z0-9_\-]+))", so9.read_text(encoding="utf-8", errors="replace"))
                    if m9 is None:
                        time.sleep(0.1)
                seen9 = m9 is not None and not dec9.exists()
                if m9:
                    b9 = f"http://127.0.0.1:{m9.group(2)}"
                    code9, _ = req(b9, "POST", "/decide", {"t": m9.group(3), "action": "cancel"})
                rc9 = p9.wait(timeout=30)
            except Exception as exc:
                why9 = f"{type(exc).__name__}: {exc}"
            finally:
                if p9.poll() is None:
                    p9.kill()
                    p9.wait()
        j9 = json.loads(dec9.read_text(encoding="utf-8")) if dec9.exists() else {}
        chk("⑨ stdout 導到檔(同 Invoke-VIAPython)·「頁:網址」在決定之前就落檔 · 頁上送「不啟動」→ 200 · rc 0 · 決定檔 cancel",
            seen9 and code9 == 200 and rc9 == 0 and j9.get("action") == "cancel",
            f"先見網址 {seen9} 送出 {code9} rc {rc9} 決定 {j9} {why9} stderr 末段 {se9.read_text(encoding='utf-8', errors='replace')[-200:]!r}")

    # ⑪ 逐一引擎自測台:背景一支一支跑 · 跑的時候不收「啟動」(409)· 跑完才收(假引擎,不真跑)
    if not loop_ok:
        nod.append("⑪")
        print("  ⑪ 逐一引擎自測台 — NODATA(本境沒有回送介面)")
    else:
        def fake(path):
            time.sleep(0.3)
            return {"state": "OK" if path.endswith("a.py") else "FAIL", "rc": 0 if path.endswith("a.py") else 1, "sec": 0.3, "last": "假"}
        tok11 = "S" + secrets.token_urlsafe(12)
        srv11, st11 = make_server("<p>x</p>", tok11, dfl, allowed, engines={"hist_2023": "/x/a.py", "fred": "/x/b.py"}, runner=fake)
        b11 = f"http://127.0.0.1:{srv11.server_port}"
        threading.Thread(target=srv11.serve_forever, daemon=True).start()
        try:
            s_start, _ = req(b11, "POST", "/selftest", {"t": tok11})
            s_busy, sb = req(b11, "POST", "/decide", {"t": tok11, "action": "launch", "mode": "default"})
            t_end, j11 = time.monotonic() + 10, {}
            while time.monotonic() < t_end:
                c, body = req(b11, "GET", "/selftest?t=" + tok11)
                j11 = json.loads(body) if c == 200 else {}
                if j11 and not j11.get("running"):
                    break
                time.sleep(0.1)
            s_notok, _ = req(b11, "GET", "/selftest?t=wrong")
            s_after, _ = req(b11, "POST", "/decide", {"t": tok11, "action": "launch", "mode": "default"})
        finally:
            srv11.shutdown()
            srv11.server_close()
        done = j11.get("done") or {}
        chk("⑪ 逐一引擎自測台:開跑 200 · 跑的時候按啟動 409(點名 selftest)· 兩支都有結果(綠一紅一)· 錯權杖 403 · 跑完才收啟動 200",
            s_start == 200 and s_busy == 409 and '"selftest"' in sb and (done.get("hist_2023") or {}).get("state") == "OK"
            and (done.get("fred") or {}).get("state") == "FAIL" and s_notok == 403 and s_after == 200,
            f"start {s_start} busy {s_busy} done {done} notok {s_notok} after {s_after}")

    # ⑫ 單支引擎自測器:rc → 燈 · 逾時 TIMEOUT · 子行程環境拿掉 CONSENT 變數(注入的環境,不碰本行程)
    td12 = Path(tempfile.mkdtemp(prefix="eng093s_"))
    (td12 / "ok.py").write_text("import os\nn = sum(1 for k in os.environ if 'CONSENT' in k.upper())\n"
                                "print('noise')\nprint(f'  [計] OK 3 · FAIL 0 · env={n}')\n", encoding="utf-8")
    (td12 / "bad.py").write_text("import sys\nprint('boom')\nsys.exit(1)\n", encoding="utf-8")
    (td12 / "slow.py").write_text("import time\ntime.sleep(5)\n", encoding="utf-8")
    probe = {"PATH": os.environ.get("PATH", ""), "X_CONSENT_PROBE": "1", "y_consent_probe": "1", "KEEP_ME": "1"}
    ce = _child_env(probe)
    e_ok, e_bad, e_slow = engine_selftest(str(td12 / "ok.py")), engine_selftest(str(td12 / "bad.py")), engine_selftest(str(td12 / "slow.py"), timeout=1)
    e_abs = engine_selftest(str(td12 / "nope.py"))
    chk("⑫ 單支引擎自測器:rc0=OK(取「計」那一行)· rc1=FAIL · 逾時=TIMEOUT · 檔不在=ABSENT · 子行程環境零 CONSENT 變數、零跳出",
        e_ok["state"] == "OK" and "env=0" in e_ok["last"] and e_bad["state"] == "FAIL" and e_slow["state"] == "TIMEOUT"
        and e_abs["state"] == "ABSENT" and not any("CONSENT" in k.upper() for k in ce) and ce.get("KEEP_ME") == "1" and ce.get("VIA_NO_OPEN") == "1",
        f"{e_ok} {e_bad} {e_slow} {e_abs} env {sorted(ce)}")

    rc = 1 if bad else (2 if nod else 0)
    print(f"[計] OK {len(okn)} · FAIL {len(bad)} · NODATA {len(nod)} → rc={rc} ({ {0: 'GREEN', 1: 'RED', 2: 'NODATA'}[rc] })")
    return rc


if __name__ == "__main__":
    sys.exit(main())
