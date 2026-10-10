#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_SystemManager v0150 — 薄尾:引擎輸入 · 參數 · 輸出 DataFrame 矩陣 + 成功紀錄 + 管理員動詞全通(操作員令 2026-10-10)。
  engine matrix [--sources] [--launch] [--json]
      一支引擎一列(pandas DataFrame;缺 pandas 照實退純表):編號 · 版本 · 中央編號 · 來源(TWSE/TPEx/yfinance)· 啟動前閘 ·
      輸入(CLI 旗標 / 動詞 / 環境變數 / 同意閘)· SSOT 冊 · 輸出(SQL 表 / 檔 / 表頭冊)· 加速器橋 · 網路橋 · 可啟動 / 自測 ·
      上次成功(資料輸出 DATA 與跑測 TEST 分開列:時間 · 版本 · 參數 · 列數 · 出處)。
      備料卡 = CGC_MDL253 prep(不另寫);成功紀錄只讀:docs/handoff/evidence 收據 · registry/VDF_Extend_Ledger.jsonl ·
      VIA_Reports/vdf/central_lists/MARKET_LISTS_latest.json · VIA_Reports/vdf_chain/VDFCHAIN_*.json · VIA_Reports/vdf/RESULT_engine_launch_latest.json。
      --launch 先跑 engine launch(載入 + 自測)再填可啟動欄;否則讀上次的啟動結果檔。
      產出 VIA_Reports/vdf/ENGINE_MATRIX_latest.{csv,html,json}(VIA_VDF_HEALTH_OUT 可改夾)。
  除錯(使用者實測 2026-10-10 找到的三件):
    ① matrix / policy / update / ps / start / test / register 在冊上卻只印 v0100 用法(v0119 的 _facade 直跳 v0104,跳過 v0105–v0118 的 main)
       → 本版直接轉給擁有版:matrix → v0113 · policy/update/ps → v0111(流程閘 MDL211)· start/test/register → v0108(ENG119;啟動只看狀態 · 註冊不 --apply)。
    ② 未知動詞清單停在 v0128 → 本版列全鏈真動詞。
    ③ chain 預設名單是 VRN 的(extract / fn / table / tidy 在 VDF 無同名函式 → 假紅)→ 改 VDF 自己的函式名。
其餘動詞照前版鏈。只收 VIA_FROM_VCGC=YES(啟動器 / VCGC)。不抓網、不代設同意閘、不碰 TA-Lib。
"""
from __future__ import annotations

# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: F401
except ImportError:
    VIA_ACCEL = None
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
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

# ===== [VIA:LIB-BRIDGE:v0100] 三庫正典橋(批597;缺席大聲拋,不 graceful) =====
import sys as _lb_sys
from pathlib import Path as _lb_Path
_lb_p = _lb_Path(__file__).resolve()
while _lb_p.parent != _lb_p:
    if (_lb_p / "supportive modules").is_dir():
        _lb_sys.path.insert(0, str(_lb_p / "supportive modules"))
        break
    _lb_p = _lb_p.parent
import VIA_LibCanon as _LIB          # 正典缺席=大聲拋,不假裝有(LL151)
# ===== [VIA:LIB-BRIDGE:END] =====

import datetime
import html
import importlib.util
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
_STEM = "VDF_SystemManager"
TAG = "v0150"
VERBS_ALL = ("status", "catalog", "links", "records", "engines", "bridges", "tools", "read", "sync", "page", "launch", "record",
             "matrix", "measure", "universe", "engine", "params", "prep", "start", "test", "register", "policy", "update", "ps",
             "fetch", "activate", "refill", "table", "fn", "health", "dormant", "panorama", "ui", "chain", "config", "quote", "extend")
ENGINE_SUBS = ("list", "check", "card", "tools", "prep", "params", "run", "launch", "sources", "matrix")
LEGACY_OWNERS = {"matrix": "VDF_SystemManager_v0113.py", "policy": "VDF_SystemManager_v0111.py", "update": "VDF_SystemManager_v0111.py",
                 "ps": "VDF_SystemManager_v0111.py", "start": "VDF_SystemManager_v0108.py", "test": "VDF_SystemManager_v0108.py",
                 "register": "VDF_SystemManager_v0108.py", "record": "VDF_SystemManager_v0109.py"}
CHAIN_NAMES_VDF = ["health", "sm_health", "sm_dormant", "table_matrix", "table_status", "fn_status", "panorama", "ui", "config_set",
                   "quote", "extend", "activate", "refill", "fetch_v0128", "universe", "engine", "engine_run", "launch", "sources", "engine_matrix"]
_EID_RX = re.compile(r"\bVDF_((?:ENG|MDL)\d{3})_[A-Za-z0-9]+|\b((?:ENG|MDL)\d{3})\b")


def _vnum_v0150(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0150(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0150(p) < _vnum_v0150(__file__)), key=_vnum_v0150)
PRIOR = _load_v0150(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


def _out() -> Path:
    return PRIOR._out()


# ---------- ① 舊動詞轉擁有版 ----------
def legacy(verb: str, args: list) -> int:
    owner = HERE / LEGACY_OWNERS[verb]
    if not owner.is_file():
        print("[%s %s] %s 的擁有版 %s 不在" % (_STEM, TAG, verb, owner.name))
        return 3
    mod = _load_v0150(owner, "_vdf_sm_v0150_owner_" + owner.stem)
    keep = sys.argv[:]
    sys.argv = [str(owner), verb] + list(args)          # 擁有版看 sys.argv[1:] 裡有沒有自己的動詞
    try:
        return int(mod.main() or 0)
    finally:
        sys.argv = keep


# ---------- ② 未知動詞 ----------
def verb_problem(args: list) -> str:
    if not args or args[0].startswith("-") or args[0] in VERBS_ALL:
        if args[:1] == ["engine"] and args[1:2] and not args[1].startswith("-") and args[1] not in ENGINE_SUBS:
            return "engine 未知子動詞 '%s'(已知:%s)" % (args[1], " · ".join(ENGINE_SUBS))
        return ""
    return "未知動詞 '%s'(已知:%s;engine 子動詞:%s)" % (args[0], " · ".join(VERBS_ALL), " · ".join(ENGINE_SUBS))


# ---------- ③ chain:從真尾版往下走(v0142 的 chain 從 v0142 自己起算,看不到 v0143 以後的函式 → 假紅) ----------
def _chain_v0150() -> list:
    import types as _types
    top = sys.modules.get("__main__")
    start = top if (top is not None and Path(getattr(top, "__file__", "") or "x").stem.startswith(_STEM + "_v")
                    and _vnum_v0150(top.__file__) >= _vnum_v0150(__file__)) else sys.modules[__name__]
    out, mod, seen = [], start, set()          # 從真正在跑的尾版起算(之後的新尾版也看得到)
    while isinstance(mod, _types.ModuleType) and id(mod) not in seen:
        seen.add(id(mod))
        v = vars(mod)
        nxt = next((v[k] for k in ("PRIOR", "_PRIOR", "PRIOR_MOD", "prior", "_prior") if isinstance(v.get(k), _types.ModuleType)), None)
        out.append((Path(v.get("__file__", "?")).stem, mod))
        if nxt is None and any(k in v for k in ("PRIOR", "_PRIOR", "PRIOR_MOD")):
            out.append(("(%s 的 PRIOR 不是模組:%s)" % (Path(v.get("__file__", "?")).stem, type(v.get("PRIOR") or v.get("_PRIOR") or v.get("PRIOR_MOD")).__name__), None))
        mod = nxt
    return out


def chain_report_v0150(names) -> dict:
    chain = _chain_v0150()
    rows = [{"version": s, "getattr": False, "defs": 0, "has": []} if m is None else
            {"version": s, "getattr": "__getattr__" in vars(m), "has": [n for n in names if n in vars(m)],
             "defs": sum(1 for k, x in vars(m).items() if callable(x) and getattr(x, "__module__", None) == m.__name__ and not k.startswith("__"))}
            for s, m in chain]
    found = {n: next((s for s, m in chain if m is not None and n in vars(m)), None) for n in names}
    broken = None
    for i, r in enumerate(rows):
        if not r["getattr"] and i < len(rows) - 1:
            above = {m for rr in rows[:i + 1] for m in rr["has"]}
            need = [n for n in names if n not in above and n in {m for rr in rows[i + 1:] for m in rr["has"]}]
            if need:
                broken = {"at": r["version"], "blocks": need}
            break
    missing = [n for n, s in found.items() if not s]
    return {"verb": "chain", "tail": chain[0][0] if chain else Path(__file__).stem, "depth": len(rows), "rows": rows, "found": found, "missing": missing,
            "broken": broken, "lamp": "RED" if (missing or broken) else "GREEN"}


# ---------- ⑤ 成功紀錄(只讀) ----------
def _eids(text: str) -> set:
    return {a or b for a, b in _EID_RX.findall(text or "")}


def _rows_in(obj):
    for k in ("rows", "store_rows", "added", "row_count"):
        if isinstance(obj, dict) and isinstance(obj.get(k), int):
            return obj[k]
    return None


SKIPPED: list = []                       # 讀不到的紀錄檔(照列在矩陣摘要,不默吞)


def _skip(path, exc) -> None:
    SKIPPED.append("%s:%s" % (Path(str(path)).name, type(exc).__name__))


def history(via: Path | None = None) -> list:
    """一筆一 dict:eid · kind(DATA 資料有寫出 / TEST 只跑測)· ok · ts · version · args · rows · src。讀不到的來源記進 SKIPPED(不猜)。"""
    via = via or VIA
    out = []
    SKIPPED.clear()
    for f in sorted((via / "docs" / "handoff" / "evidence").glob("*.json")):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            _skip(f, exc)
            continue
        cmd = [str(x) for x in (d.get("command") or [])]
        text = " ".join(cmd)
        ids = _eids(text)
        if "fetch" in cmd and "card" in cmd:
            nxt = cmd[cmd.index("card") + 1:cmd.index("card") + 2]
            ids |= {"MDL" + n.zfill(3) for n in nxt if n.isdigit()}
        ver = (re.findall(r"_v(\d{4})\.py", text) or [""])[-1]
        for e in ids:
            out.append({"eid": e, "kind": "TEST", "ok": d.get("rc") == 0, "ts": d.get("completed_at") or "", "version": ("v" + ver) if ver else "",
                        "args": " ".join(cmd[1:])[:120], "rows": None, "src": "evidence/" + f.name})
    led = via / "functional modules" / "VDF" / "registry" / "VDF_Extend_Ledger.jsonl"
    if led.is_file():
        for line in led.read_text(encoding="utf-8").splitlines():
            try:
                d = json.loads(line)
            except ValueError as exc:
                _skip(led, exc)
                continue
            out.append({"eid": "SM.extend", "kind": "DATA", "ok": d.get("lamp") == "GREEN", "ts": d.get("ts") or "", "version": "v0148",
                        "args": "days=%s universe=%s n=%s" % (d.get("days"), d.get("universe_src"), d.get("n")), "rows": d.get("store_rows"),
                        "src": "registry/VDF_Extend_Ledger.jsonl"})
    ml = via / "VIA_Reports" / "vdf" / "central_lists" / "MARKET_LISTS_latest.json"
    if ml.is_file():
        try:
            d = json.loads(ml.read_text(encoding="utf-8"))
            lists = d.get("lists") or {}
            for name, v in (lists.items() if isinstance(lists, dict) else []):
                for key in ("engine", "history_engine"):
                    p = v.get(key) or ""
                    for e in _eids(p):
                        ver = (re.findall(r"_v(\d{4})\.py", p) or [""])[-1]
                        rows = v.get("rows") if key == "engine" else (v.get("holdings_dates") or {}).get("rows")
                        out.append({"eid": e, "kind": "DATA", "ok": v.get("state") == "GREEN" or bool(rows), "ts": d.get("ts") or "",
                                    "version": ("v" + ver) if ver else "", "args": "list=%s table=%s state=%s" % (name, v.get("table"), v.get("state")),
                                    "rows": rows, "src": "VIA_Reports/vdf/central_lists/MARKET_LISTS_latest.json"})
        except (OSError, ValueError, AttributeError) as exc:
            _skip(ml, exc)
    for f in sorted((via / "VIA_Reports" / "vdf_chain").glob("VDFCHAIN_2*.json"))[-30:]:
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            _skip(f, exc)
            continue
        for s in d.get("stages") or []:
            text = " ".join(str(s.get(k) or "") for k in ("name", "detail", "evidence"))
            for e in _eids(text):
                out.append({"eid": e, "kind": "DATA" if _rows_in(s) else "TEST", "ok": s.get("state") == "GREEN", "ts": d.get("generated") or "",
                            "version": "", "args": "chain %s since=%s" % (s.get("id"), d.get("since")), "rows": _rows_in(s), "src": "vdf_chain/" + f.name})
    rl = via / "VIA_Reports" / "vdf" / "RESULT_engine_launch_latest.json"
    if rl.is_file():
        try:
            d = json.loads(rl.read_text(encoding="utf-8"))
            for p in d.get("per") or []:
                v = re.findall(r"_v(\d{4})\.py", p.get("path") or "")
                out.append({"eid": p.get("eid"), "family": p.get("family"), "kind": "TEST", "ok": p.get("launchable") and p.get("selftest_lamp") in ("GREEN", "—"),
                            "ts": d.get("ts") or "", "version": ("v" + v[-1]) if v else "", "args": "engine launch (載入 + --selftest)", "rows": None,
                            "src": "VIA_Reports/vdf/RESULT_engine_launch_latest.json"})
        except (OSError, ValueError) as exc:
            _skip(rl, exc)
    return out


def _last(hist: list, eid: str, kind: str, family: str | None = None) -> dict | None:
    rows = [h for h in hist if h["eid"] == eid and h["kind"] == kind and h["ok"] and (not h.get("family") or not family or h["family"] == family)]
    return max(rows, key=lambda h: str(h["ts"])) if rows else None


def _fmt_last(h: dict | None) -> str:
    if not h:
        return "—"
    return "%s · %s%s · %s%s" % (str(h["ts"])[:19], h["version"] or "?", (" · %s 列" % h["rows"]) if h.get("rows") is not None else "",
                                  h["args"][:60], " · " + h["src"])


# ---------- ④ 矩陣 ----------
def launch_paths(paths: list) -> dict:
    """依路徑逐支啟動驗收(同號異名、同名異夾都不會解析失敗);判法與 v0149 engine launch 同一套,結果寫同一個檔。"""
    inv = PRIOR._inv()
    by = {r["path"]: r for r in inv.engines("VDF")}
    per = []
    for path in paths:
        r = by.get(path)
        if r is None:
            per.append({"eid": "?", "family": Path(path).stem, "path": path, "gate": "ABSENT", "launchable": False,
                        "load": {"rc": "ABSENT", "secs": 0, "tail": ["不在引擎冊"]}, "selftest": None, "selftest_lamp": "—"})
            continue
        g = inv.gate(r, "VDF")
        ld = PRIOR.load_probe(VIA / path) if g.get("lamp") != "RED" else {"rc": "GATE", "secs": 0, "tail": g.get("block") or []}
        st = None
        if ld["rc"] == 0 and "--selftest" in (r.get("flags") or []):
            st = PRIOR.run_path(VIA / path, ["--selftest"], timeout=float(os.environ.get("VIA_VDF_LAUNCH_TIMEOUT") or 600), capture=True)
        lamp = "—" if st is None else ("GREEN" if st["rc"] == 0 else "NODATA" if st["rc"] == 2 else "RED")
        per.append({"eid": r["eid"], "family": r["family"], "path": path, "gate": g.get("lamp"), "launchable": ld["rc"] == 0,
                    "load": ld, "selftest": st, "selftest_lamp": lamp})
    o = {"via": "vdf", "verb": "engine launch", "tag": "%s %s" % (_STEM, TAG), "ts": datetime.datetime.now().isoformat(timespec="seconds"),
         "n": len(per), "launchable": sum(1 for p in per if p["launchable"]),
         "selftest": {k: sum(1 for p in per if p["selftest_lamp"] == k) for k in ("GREEN", "NODATA", "RED", "—")}, "missing": [], "per": per}
    o["lamp"] = "RED" if o["launchable"] < o["n"] else ("GREEN" if not (o["selftest"]["RED"] or o["selftest"]["NODATA"]) else "YELLOW")
    o["result"] = save_launch(o)
    return o


def save_launch(o: dict) -> str:
    """啟動結果依路徑合併進 RESULT_engine_launch_latest.json(部分重測只蓋那幾支,其他支的上次結果保留並帶各自時間)。"""
    f = _out() / "RESULT_engine_launch_latest.json"
    old = {}
    if f.is_file():
        try:
            prev = json.loads(f.read_text(encoding="utf-8"))
            old = {p["path"]: dict(p, ts=p.get("ts") or prev.get("ts")) for p in prev.get("per") or [] if p.get("path")}
        except (OSError, ValueError) as exc:
            _skip(f, exc)
    for p in o["per"]:
        old[p["path"]] = dict(p, ts=o["ts"])
    per = sorted(old.values(), key=lambda p: (str(p.get("eid")), p["path"]))
    merged = dict(o, per=per, n=len(per), launchable=sum(1 for p in per if p.get("launchable")),
                  selftest={k: sum(1 for p in per if p.get("selftest_lamp") == k) for k in ("GREEN", "NODATA", "RED", "—")}, merged=True)
    try:
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps(merged, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
        return str(f)
    except OSError as exc:
        return "寫不出:%s" % exc


_OWN_PREFIX = ("VDF_", "VIA_", "CGC_", "SUP_", "VRN_", "FLOW_", "via_")


def launch_state(path: str, lp: dict | None) -> str:
    """可啟動欄:是 · 否(程式錯)· 已取代(_rebuilds_superseded 版史)· 缺件 X(第三方套件不在本境;不是壞、不代裝)· 未測。"""
    if lp is None:
        return "未測"
    if lp.get("launchable"):
        return "是"
    if "_rebuilds_superseded" in path:
        return "已取代"
    tail = " ".join((lp.get("load") or {}).get("tail") or [])
    m = re.search(r"No module named '([A-Za-z0-9_.]+)'", tail)
    if m and not m.group(1).startswith(_OWN_PREFIX):
        return "缺件 " + m.group(1).split(".")[0]
    return "否"


def _bridges(path: Path) -> tuple:
    try:
        t = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False, False
    return "[VIA:ACCEL-BRIDGE:" in t, "[VIA:NET-BRIDGE:" in t


def engine_matrix(only_sources: bool = False, run_launch: bool = False, cards: list | None = None, hist: list | None = None) -> dict:
    inv = PRIOR._inv()
    if cards is None:
        cards = inv.prep_v0102("VDF", write=False)["cards"]
    src = {s["path"]: s["sources"] for s in PRIOR.sources()}
    if only_sources:
        cards = [c for c in cards if c["path"] in src]
    launch_by = {}
    if run_launch:
        launch_by = {p["path"]: p for p in launch_paths([c["path"] for c in cards])["per"]}
    else:
        rl = _out() / "RESULT_engine_launch_latest.json"
        if rl.is_file():
            try:
                launch_by = {p["path"]: p for p in json.loads(rl.read_text(encoding="utf-8")).get("per") or []}
            except (OSError, ValueError):
                launch_by = {}
    hist = history() if hist is None else hist
    rows = []
    for c in cards:
        par, outp, ssot = c.get("params") or {}, c.get("outputs") or {}, c.get("ssot") or {}
        acc, net = _bridges(VIA / c["path"])
        lp = launch_by.get(c["path"])
        rows.append({
            "編號": c["eid"], "家族": c["family"], "版本": c.get("version") or "—", "中央編號": c.get("code") or "未編號",
            "來源": "+".join(src.get(c["path"], [])) or "—", "啟動前閘": (c.get("gate") or {}).get("lamp") or "—", "備料燈": c.get("lamp") or "—",
            "輸入_旗標": " ".join(par.get("flags") or []) or "—", "輸入_動詞": " ".join(par.get("verbs") or []) or "—",
            "輸入_環境": " ".join(par.get("env") or []) or "—", "同意閘": " ".join(par.get("consent") or []) or "—",
            "SSOT冊": " · ".join("%s(%s)" % (b.get("book"), b.get("state")) for b in ssot.get("books") or []) or "—",
            "輸出_表": " ".join(outp.get("sql_tables") or []) or "—", "輸出_檔": " ".join(outp.get("files") or []) or "—",
            "輸出_表頭冊": " ".join("%s≥%s" % (h.get("table"), h.get("min_rows")) for h in outp.get("header_tables") or []) or "—",
            "加速器橋": "有" if acc else "缺", "網路橋": "有" if net else "缺",
            "可啟動": launch_state(c["path"], lp), "自測": lp["selftest_lamp"] if lp else "未測",
            "上次成功_資料": _fmt_last(_last(hist, c["eid"], "DATA", c["family"])),
            "上次成功_跑測": _fmt_last(_last(hist, c["eid"], "TEST", c["family"])),
            "短令": (c.get("launch") or {}).get("short") or "", "路徑": c["path"],
        })
    mgr = [h for h in hist if h["eid"] == "SM.extend"]
    o = {"via": "vdf", "verb": "engine matrix", "tag": "%s %s" % (_STEM, TAG), "ts": datetime.datetime.now().isoformat(timespec="seconds"),
         "n": len(rows), "columns": list(rows[0].keys()) if rows else [], "rows": rows,
         "manager_runs": mgr[-10:], "history_n": len(hist), "history_skipped": list(SKIPPED),
         "summary": {"有來源": sum(1 for r in rows if r["來源"] != "—"), "加速器橋缺": sum(1 for r in rows if r["加速器橋"] == "缺"),
                     "網路橋缺": sum(1 for r in rows if r["網路橋"] == "缺"), "可啟動": sum(1 for r in rows if r["可啟動"] == "是"),
                     "不能起": sum(1 for r in rows if r["可啟動"] == "否"), "已取代": sum(1 for r in rows if r["可啟動"] == "已取代"),
                     "缺件": sum(1 for r in rows if r["可啟動"].startswith("缺件")), "自測紅": sum(1 for r in rows if r["自測"] == "RED"),
                     "有資料成功紀錄": sum(1 for r in rows if r["上次成功_資料"] != "—"),
                     "有跑測成功紀錄": sum(1 for r in rows if r["上次成功_跑測"] != "—")}}
    o["files"] = write_matrix(o)
    return o


def _frame(rows: list):
    try:
        import pandas as pd
    except ImportError:
        return None
    return pd.DataFrame(rows)


def write_matrix(o: dict) -> dict:
    out = _out()
    out.mkdir(parents=True, exist_ok=True)
    files = {"json": out / "ENGINE_MATRIX_latest.json", "csv": out / "ENGINE_MATRIX_latest.csv", "html": out / "ENGINE_MATRIX_latest.html"}
    files["json"].write_text(json.dumps(o, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    df = _frame(o["rows"])
    if df is not None:
        df.to_csv(files["csv"], index=False, encoding="utf-8-sig")
        table = df.to_html(index=False, escape=True, classes="m", border=0)
    else:
        import csv
        with files["csv"].open("w", encoding="utf-8-sig", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=o["columns"])
            w.writeheader()
            w.writerows(o["rows"])
        table = "<table class='m'><tr>%s</tr>%s</table>" % ("".join("<th>%s</th>" % html.escape(c) for c in o["columns"]),
                                                              "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % html.escape(str(r[c])) for c in o["columns"]) for r in o["rows"]))
    for word, color in (("缺", "#dc2626"), ("否", "#dc2626"), ("已取代", "#6b7280"), ("RED", "#dc2626"), ("YELLOW", "#b45309"), ("NODATA", "#0891b2"), ("GREEN", "#16a34a")):
        table = table.replace("<td>%s</td>" % word, "<td style='color:%s;font-weight:600'>%s</td>" % (color, word))
    s = o["summary"]
    page = ("<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
            "<title>VDF 引擎矩陣</title><style>body{font:13px/1.45 system-ui,sans-serif;margin:16px;background:#fafafa;color:#111}"
            "h1{font-size:18px}.k{display:inline-block;margin:0 14px 8px 0}.w{overflow:auto;max-height:80vh;border:1px solid #ddd;background:#fff}"
            "table.m{border-collapse:collapse;font-size:12px}table.m th{position:sticky;top:0;background:#f1f5f9;text-align:left}"
            "table.m td,table.m th{padding:4px 6px;border-bottom:1px solid #eee;vertical-align:top;white-space:nowrap;max-width:360px;overflow:hidden;text-overflow:ellipsis}"
            "</style></head><body><h1>VDF 引擎 · 輸入 / 參數 / 輸出 矩陣</h1><div>%s · %s · %d 支</div><div>%s</div><div class='w'>%s</div>"
            "<p>上次成功_資料 = 有寫出資料的紀錄;上次成功_跑測 = 載入 / 自測 / 收據 rc0(不代表有資料)。紀錄只讀,讀不到的來源略過不猜。</p></body></html>"
            % (html.escape(o["tag"]), html.escape(o["ts"]), o["n"], "".join("<span class='k'>%s <b>%s</b></span>" % (html.escape(k), v) for k, v in s.items()), table))
    files["html"].write_text(page, encoding="utf-8")
    return {k: str(v) for k, v in files.items()}


def _print_matrix(o: dict) -> None:
    cols = ["編號", "版本", "中央編號", "來源", "啟動前閘", "加速器橋", "網路橋", "可啟動", "自測"]
    df = _frame(o["rows"])
    if df is not None:
        import pandas as pd
        with pd.option_context("display.max_rows", 500, "display.width", 200, "display.unicode.east_asian_width", True):
            print(df[cols + ["上次成功_資料"]].assign(上次成功_資料=df["上次成功_資料"].str.slice(0, 40)).to_string(index=False))
    else:
        for r in o["rows"]:
            print("  " + " · ".join(str(r[c]) for c in cols))
    if o["manager_runs"]:
        h = o["manager_runs"][-1]
        print("  [管理員 extend 上次] %s · %s · %s 列 · %s" % (h["ts"], h["args"], h["rows"], "GREEN" if h["ok"] else "非綠"))
    print("[計] VDF 引擎矩陣 %d 支 · %s · 紀錄 %d 筆%s" % (o["n"], " · ".join("%s %s" % kv for kv in o["summary"].items()), o["history_n"],
                                                     (" · 讀不到 %d:%s" % (len(o["history_skipped"]), ", ".join(o["history_skipped"][:5]))) if o["history_skipped"] else ""))
    print("  [檔] %s" % " · ".join(o["files"].values()))


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args[:2]:
        return selftest()
    why = verb_problem(args)
    if why:
        print("[拒跑] %s %s:%s" % (_STEM, TAG, why))
        return 2
    if args[:1] and args[0] in LEGACY_OWNERS and os.environ.get("VIA_FROM_VCGC") == "YES":
        return legacy(args[0], args[1:])
    if args[:1] == ["chain"]:
        names = args[1:] or CHAIN_NAMES_VDF
        o = chain_report_v0150(names)
        PRIOR._print_chain(o)
        return 1 if o["lamp"] == "RED" else 0
    if args[:2] == ["engine", "launch"] and os.environ.get("VIA_FROM_VCGC") == "YES":
        rest = args[2:]
        inv = PRIOR._inv()
        rows = inv.engines("VDF")
        paths, missing = [], []
        if "--sources" in rest:
            paths += [s["path"] for s in PRIOR.sources(rows)]
        for k in [a for a in rest if not a.startswith("--")]:
            one, cands = inv.resolve(rows, k)
            (paths.append(one["path"]) if one else missing.append({"key": k, "candidates": [c.get("family") for c in (cands or [])]}))
        o = launch_paths(list(dict.fromkeys(paths)))
        o["missing"] = missing
        if missing:
            o["lamp"] = "RED"
        print(json.dumps(o, ensure_ascii=False, indent=1, default=str)) if "--json" in rest else PRIOR._print_launch(o)
        return 0 if o["lamp"] in ("GREEN", "YELLOW") else 1
    if args[:2] == ["engine", "matrix"]:
        if os.environ.get("VIA_FROM_VCGC") != "YES":
            print("[VDF] 拒絕。只能經 via-vcgc / VDF 啟動器(VIA_FROM_VCGC=YES)。")
            return 2
        o = engine_matrix(only_sources="--sources" in args, run_launch="--launch" in args)
        print(json.dumps({k: v for k, v in o.items() if k != "rows"}, ensure_ascii=False, indent=1, default=str)) if "--json" in args else _print_matrix(o)
        return 1 if o["summary"]["不能起"] else 0
    return PRIOR.main(args)


def selftest() -> int:
    import shutil
    import tempfile
    p = f = 0

    def chk(name, cond, note=""):
        nonlocal p, f
        if cond:
            p += 1
        else:
            f += 1
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · %s" % (note,)) if note != "" else ""))

    keep = {k: os.environ.get(k) for k in ("VIA_FROM_VCGC", "VIA_VDF_HEALTH_OUT", "VIA_NO_OPEN")}
    td = Path(tempfile.mkdtemp(prefix="vdfsm150-"))
    os.environ.update({"VIA_VDF_HEALTH_OUT": str(td / "out"), "VIA_FROM_VCGC": "YES", "VIA_NO_OPEN": "1"})
    try:
        why = verb_problem(["zz_no_such_verb"])
        chk("① 未知動詞 rc2 · 清單是全鏈(含 quote / extend / health / ui / engine)", main(["zz_no_such_verb"]) == 2
            and all(v in why for v in ("quote", "extend", "health", "ui", "engine", "activate")) and verb_problem(["engine", "zz"]) != "")
        chk("② matrix → v0113(共用管理員清單)rc0;policy → v0111(流程閘)rc0", main(["matrix"]) == 0 and main(["policy"]) == 0)
        o = chain_report_v0150(CHAIN_NAMES_VDF)
        chk("③ chain 從真尾版 v0150 起算 · 用 VDF 自己的函式名 → 全找到(quote / extend / engine_run / engine_matrix 都在)",
            o["lamp"] != "RED" and _vnum_v0150(o["tail"]) >= 150 and o["found"].get("engine_matrix"), (o["lamp"], o["missing"]))
        fake = td / "via"
        (fake / "docs" / "handoff" / "evidence").mkdir(parents=True)
        (fake / "functional modules" / "VDF" / "registry").mkdir(parents=True)
        ev = fake / "docs" / "handoff" / "evidence"
        ev.joinpath("a.json").write_text(json.dumps({"command": ["x.py", "run", "VDF_ENG055_OmniFetch_v0122.py", "--selftest"], "rc": 0,
                                                      "completed_at": "2026-10-05T01:00:00"}), encoding="utf-8")
        ev.joinpath("b.json").write_text(json.dumps({"command": ["x.py", "run", "VDF_ENG055_OmniFetch_v0121.py"], "rc": 1,
                                                      "completed_at": "2026-10-06T01:00:00"}), encoding="utf-8")
        ev.joinpath("c.json").write_text(json.dumps({"command": ["x.py", "run", "VDF_SystemManager", "fetch", "card", "11"], "rc": 0,
                                                      "completed_at": "2026-10-07T01:00:00"}), encoding="utf-8")
        (fake / "functional modules" / "VDF" / "registry" / "VDF_Extend_Ledger.jsonl").write_text(
            json.dumps({"ts": "2026-10-10T08:00:00", "days": 35, "universe_src": "X", "n": 2, "store_rows": 10, "lamp": "GREEN"}) + "\n", encoding="utf-8")
        h = history(fake)
        last = _last(h, "ENG055", "TEST")
        chk("④ 成功紀錄:取最新的 rc0(不取較新的 rc1)· fetch card 11 → MDL011 · extend 帳 = DATA 帶列數",
            last is not None and last["version"] == "v0122" and _last(h, "MDL011", "TEST") is not None
            and any(x["eid"] == "SM.extend" and x["kind"] == "DATA" and x["rows"] == 10 for x in h), (last or {}).get("version"))
        card = {"eid": "ENG056", "family": "VDF_ENG056_ChipBackfill", "version": "v0106", "path": "functional modules/VDF/engine/VDF_ENG056_ChipBackfill_v0106.py",
                "code": "VIA-VDF-ENG069", "lamp": "YELLOW", "gate": {"lamp": "GREEN"}, "params": {"flags": ["--selftest"], "verbs": [], "env": [], "consent": []},
                "ssot": {"books": []}, "outputs": {"sql_tables": ["tw_chip"], "files": [], "header_tables": []}, "launch": {"short": "via-vdfeng ENG056"}}
        m = engine_matrix(run_launch=True, cards=[card], hist=h)
        r0 = m["rows"][0]
        files_ok = all(Path(x).is_file() for x in m["files"].values())
        chk("⑤ engine matrix:一列含輸入 / 輸出 / 雙橋 / 可啟動 / 自測 · 寫出 csv + html + json", m["n"] == 1 and r0["輸出_表"] == "tw_chip"
            and r0["加速器橋"] == "有" and r0["網路橋"] == "有" and r0["可啟動"] == "是" and r0["自測"] == "GREEN" and files_ok, (r0["可啟動"], r0["自測"], files_ok))
        lp = launch_paths(["functional modules/VDF/NO_SUCH.py"])
        merged = json.loads((td / "out" / "RESULT_engine_launch_latest.json").read_text(encoding="utf-8"))
        chk("⑥a 啟動結果依路徑合併:先前 ENG056 那支仍在 · 新測的 NO_SUCH 加進來", {p["path"] for p in merged["per"]} >= {card["path"], "functional modules/VDF/NO_SUCH.py"})
        chk("⑥ launch_paths:冊上沒有的路徑 = 不能起(不猜)", lp["launchable"] == 0 and lp["lamp"] == "RED")
        miss = {"launchable": False, "load": {"tail": ["ModuleNotFoundError: No module named 'polars'"]}}
        own = {"launchable": False, "load": {"tail": ["ModuleNotFoundError: No module named 'VDF_MDL101_OutputManager'"]}}
        chk("⑥b 可啟動欄分類:缺第三方套件 = 缺件(不是壞)· 缺自家模組 = 否 · _rebuilds_superseded = 已取代",
            launch_state("x/VDF_MDL011.py", miss) == "缺件 polars" and launch_state("x/VDF_A.py", own) == "否"
            and launch_state("x/_rebuilds_superseded/VDF_A.py", own) == "已取代" and launch_state("x", None) == "未測")
        body = Path(__file__).read_text(encoding="utf-8")
        chk("⑦ 三橋 · 不碰 TA-Lib · 不代設同意閘", all(t in body for t in ("[VIA:ACCEL-BRIDGE:v0100]", "[VIA:NET-BRIDGE:v0100]", "[VIA:LIB-BRIDGE:v0100]"))
            and "import " + "talib" not in body and 'environ["VIA_NET_' + 'CONSENT"] = "' not in body)
        print("  ── 前版鏈自測(原樣印出)──")
        prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
        chk("⑧ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    finally:
        for k, v in keep.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(td, ignore_errors=True)
    print("[計] VDF_SystemManager_v0150 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
