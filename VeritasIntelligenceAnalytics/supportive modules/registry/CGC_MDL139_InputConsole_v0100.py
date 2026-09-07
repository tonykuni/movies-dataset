#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL139_InputConsole v0100 — 左輸入/右矩陣 統一輸入主控台(批390)
====================================================================
操作員令(批390):「左面板有輸入介面,右面板是顯示介面;VDF 可新增查詢標的:總體經濟指標可分 PMI/通膨/就業…、
台灣股票分 TWSE/TPEX 可新增代碼;輸入介面項目類別拆細;起始日期個別可改;財報分當季/累計/年度、年起迄;
DEFAULT 都是最新;目前資料庫狀況;台股每日交易資訊及籌碼最後要對齊數量,作為更新股票清單及核對數量一致;
輸出資料都採 parquet 增量擷取、DuckDB 管理;所有系統輸入介面都在左側面板,右側面板用矩陣、有篩選、大到小排列;
儘量用 Windows U/I 下拉/勾選/全選/全不選;VRN 輸入可有資料夾、Windows I/O 拖曳式輸入、啟動、人機互動動畫、
高自動化;VRN 要看整體跑況 BASIC INFO / SUMMARY / FINANCIAL DATA(VERIFIED/FAIL);其他含輸入介面儘量簡單但
維持個別改動空間;VAP 也一樣」。
機制(Zero-Hydra:一冊一頁一橋;每一項目綁定母倉現役引擎與真旗標,引擎缺=誠實 PLANNED 不假跑):
  冊  VIA_InputConsole_Spec_v0100.json:families(vdf/vrn/vap)→ groups → items{engine(dir/glob/verb), params 種類}
      + user 段(操作員個別改動:台股代碼 TWSE/TPEX、逐項起始日、天數、宏觀類別、財報期別年起迄、VRN 報告夾、
      VAP 代碼/格式/設定;只增不減;changelog append-only);台股代碼/財報期別/VRN 路徑鏡寫 VDF_Input_Interface_Matrix 活冊
  頁  supportive modules/ui_support/VIA_UI_InputConsole_v0100.html(零 CDN;左 rail=輸入表單,右 main=矩陣 篩選/
      點欄排序(預設大到小)/勾選/全選/全不選;拖曳區+資料夾選擇(webkitdirectory=Windows 原生夾對話框);
      進度動畫=樞紐 /status 輪詢;同源樞紐 /console 在線=LIVE 可啟動,file:// 頁=SNAPSHOT 只看+印等價短令)
  橋  DeckServer 尾版:GET /console(注入權杖)/console_status;POST /console_run{item,params}/console_set{ops};
      啟動一律走白名單解析(resolve_argv)後 Popen;參數逐項驗證(代碼/日期/天數/車道/類別/資料夾必須存在)
  狀況 status:庫狀況(ENG073 架構冊快照+DuckDB 現值)、對齊(ENG081 ALIGN_latest)、台股清單(焦點冊∪操作員)、
      宏觀序列(macro_ssot 依類別)、VRN 跑況(每報告 BASIC INFO/SUMMARY/FINANCIAL DATA VERIFIED|FAIL|PENDING)、
      VAP 產出頁、各項目可跑態(READY/PLANNED/ENGINE_MISSING/NEED_DIR)→ VIA_Reports/console/CONSOLE_latest.json
紀律:只增不減;正本零觸碰;誠實三態;零 CDN;零網路(status/build 不觸網;run 只在操作員按啟動且項目 net=true 才給同意閘);
      尾版律(引擎 glob 尾版);預設 start=latest=不帶旗標=引擎增量律。
用法:python3 CGC_MDL139_InputConsole_v0100.py [build] [--open] | status [--json]
      | set k=v [k=v …](tw-add=2330:TWSE tw-remove=2330 start=<item>:YYYY-MM-DD|latest days=<item>:N
        macro-cats=Business,Prices macro-since=YYYY-MM-DD|latest fin-period=當季|累計|年度 fin-from=YYYY fin-to=YYYY
        vrn-dir=<夾> vrn-chain=a,b vap-code=2330 vap-formats=svg,html vap-profile=vap_spec_v1 vap-out=<夾>
        vap-data=<檔> vap-config=<檔> global-cats=a,b)
      | argv --item <id> [k=v …] [--json] | run --item <id> [k=v …] [--dry] | --selftest
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
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import datetime as _dt
import json
import os
import re
import socket
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
SPEC = HERE / "VIA_InputConsole_Spec_v0100.json"
UI_DIR = VIA / "supportive modules" / "ui_support"
OUT_PAGE = UI_DIR / "VIA_UI_InputConsole_v0100.html"      # 頁名穩定律(版本在引擎)
REPORTS = VIA / "VIA_Reports" / "console"
LOG = VIA / "logs" / "input_console.log"
MEGA = VIA / "functional modules" / "VDF" / "output_hub" / "mega"
DB_TW = MEGA / "vdf_tw_market.duckdb"
DB_GL = MEGA / "vdf_global_market.duckdb"
INPUT_MATRIX = VIA / "functional modules" / "VDF" / "VDF_Input_Interface_Matrix_v0100.json"
FOCUS = VIA / "functional modules" / "VDF" / "VDF_TW_Focus_Universe_v0100.json"
BRIDGE = "http://127.0.0.1:8765"
HUB_PORT = 8765
VERBS = ("build", "status", "set", "argv", "run")
CODE_RX = re.compile(r"^\d{4,6}[A-Z]?$")
DATE_RX = re.compile(r"^\d{4}-\d{2}-\d{2}$")
YM_RX = re.compile(r"^\d{4}-\d{2}$")
YEAR_RX = re.compile(r"^\d{4}$")
LANE_RX = re.compile(r"^L\d{1,2}$")
FRED_RX = re.compile(r"^[A-Z0-9_.\-]{2,40}$")
CAT_RX = re.compile(r"^[A-Za-z_]{1,32}$")
ITEM_RX = re.compile(r"^[a-z0-9_]{2,48}$")
PERIODS = ("單季", "累計", "年度", "當季")
GLOBAL_THEMES = ("Global", "ECB", "BOJ", "BOE", "OECD")
VERIFIED_STATES = ("EXACT_MATCH", "EXACT_MATCH_DB", "ROUNDING_ONLY", "ROUNDING_ONLY_DB", "DB_DERIVED")
FAIL_STATES = ("FORMULA_MISMATCH", "FORMULA_MISMATCH_DB", "PARSE_SUSPECT", "MISSING_SOURCE")


# ---------------------------------------------------------------- 基礎
def _ts() -> str:
    return _dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def _now() -> str:
    return _dt.datetime.now().isoformat(timespec="seconds")


def log_event(kind: str, msg: str, **kw) -> None:
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"ts": _now(), "kind": kind, "msg": msg, **kw}, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _write_text(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, p)


def _write_json(p: Path, obj) -> None:
    _write_text(p, json.dumps(obj, ensure_ascii=False, indent=1))


def newest(dirp: Path, pat: str) -> Path | None:
    hits = sorted(dirp.glob(pat)) if dirp.exists() else []
    return hits[-1] if hits else None


def load_spec(path: Path | None = None) -> dict:
    p = path or SPEC
    d = json.loads(p.read_text(encoding="utf-8-sig"))
    d.setdefault("user", {})
    u = d["user"]
    u.setdefault("tw_codes", {"TWSE": [], "TPEX": []})
    u.setdefault("starts", {})
    u.setdefault("days", {})
    u.setdefault("macro_cats", [])
    u.setdefault("macro_since", "latest")
    u.setdefault("fin", {"period": "年度", "year_from": "", "year_to": ""})
    u.setdefault("vrn_dir", "")
    u.setdefault("vrn_chain", [])
    u.setdefault("vap", {"code": "2330", "formats": "svg,html", "profile": "vap_spec_v1", "out": "VIA_Reports/vap_one", "data": "", "config": ""})
    u.setdefault("global_cats", [])
    u.setdefault("changelog", [])
    return d


def save_spec(d: dict, path: Path | None = None) -> None:
    _write_json(path or SPEC, d)


def items_index(spec: dict) -> dict:
    """item id → {family, group, item}"""
    out = {}
    for fam, f in spec.get("families", {}).items():
        for g in f.get("groups", []):
            for it in g.get("items", []):
                out[it["id"]] = {"family": fam, "group": g["id"], "item": it, "fam_python": f.get("python", "base")}
    return out


def hub_live(port: int = HUB_PORT, timeout: float = 0.3) -> str:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=timeout):
            return "LIVE"
    except OSError:
        return "SNAPSHOT"


def _duckdb():
    try:
        import duckdb
        return duckdb
    except Exception:
        return None


# ---------------------------------------------------------------- 家族境 python(MDL136 正本)
_ENV = {"m": None}


def family_python(fam: str, environ: dict | None = None) -> dict:
    """家族境 python 解析(MDL136 resolve_env_python 正本;base=本解譯器;缺 MDL136=誠實 base 退路)"""
    if fam in ("", "base", None):
        return {"python": sys.executable, "state": "BASE", "env": "base"}
    if _ENV["m"] is None:
        try:
            import importlib.util
            p = newest(HERE, "CGC_MDL136_EntryBridge_v0*.py")
            spec = importlib.util.spec_from_file_location("entrybridge_e139", p)
            m = importlib.util.module_from_spec(spec)
            sys.modules["entrybridge_e139"] = m
            spec.loader.exec_module(m)
            _ENV["m"] = m
        except Exception:
            _ENV["m"] = False
    m = _ENV["m"]
    if not m:
        return {"python": sys.executable, "state": "BASE_FALLBACK", "env": "", "hint": "MDL136 缺"}
    try:
        r = m.resolve_env_python(fam, environ=environ)
        return {"python": r.get("python") or sys.executable, "state": r.get("state", "?"), "env": r.get("env", ""), "hint": r.get("hint", "")}
    except Exception as exc:
        return {"python": sys.executable, "state": "BASE_FALLBACK", "env": "", "hint": str(exc)[:80]}


# ---------------------------------------------------------------- 宏觀序列冊 / 台股代碼冊
def macro_series(spec: dict) -> list:
    """macro_ssot series_registry(有 fred_id 者)→ [{key, fred_id, theme, sub, indicator, freq, cat}]"""
    rel = spec.get("families", {}).get("vdf", {})
    src = None
    for g in rel.get("groups", []):
        if g.get("id") == "macro":
            src = g.get("series_source")
    if not src:
        return []
    p = VIA / src
    if not p.exists():
        return []
    try:
        m = json.loads(p.read_text(encoding="utf-8-sig"))
    except Exception:
        return []
    out = []
    for k, v in (m.get("series_registry") or {}).items():
        if k.startswith("_") or not isinstance(v, dict) or not v.get("fred_id"):
            continue
        theme = str(v.get("macro_theme") or "")
        cat = "Global" if theme in GLOBAL_THEMES or k.split(".")[0] not in ("US",) else theme
        out.append({"key": k, "fred_id": str(v["fred_id"]), "theme": theme, "sub": str(v.get("sub_theme") or ""),
                    "indicator": str(v.get("indicator") or ""), "freq": str(v.get("freq") or ""), "cat": cat})
    return out


def macro_categories(spec: dict) -> list:
    for g in spec.get("families", {}).get("vdf", {}).get("groups", []):
        if g.get("id") == "macro":
            return list(g.get("categories") or [])
    return []


def macro_ids_for(spec: dict, cats: list) -> list:
    want = {c for c in cats if c}
    ids, seen = [], set()
    for s in macro_series(spec):
        if s["cat"] in want and s["fred_id"] not in seen:
            seen.add(s["fred_id"])
            ids.append(s["fred_id"])
    return ids


def focus_members() -> list:
    try:
        j = json.loads(FOCUS.read_text(encoding="utf-8-sig"))
        return [{"code": str(x.get("ticker")), "name": str(x.get("name") or ""), "market": str(x.get("market") or ""), "group": str(x.get("group") or ""), "source": "焦點冊"}
                for x in j.get("members", []) if x.get("ticker")]
    except Exception:
        return []


def tw_codes(spec: dict, names: dict | None = None) -> list:
    """台股清單=焦點冊 ∪ 操作員新增(user.tw_codes;TWSE/TPEX 分系);去重;names=code→name(tw_listings)"""
    rows, seen = [], set()
    for m in focus_members():
        if m["code"] in seen:
            continue
        seen.add(m["code"])
        rows.append(m)
    for mk in ("TWSE", "TPEX"):
        for c in spec.get("user", {}).get("tw_codes", {}).get(mk, []) or []:
            if c in seen:
                continue
            seen.add(c)
            rows.append({"code": c, "name": (names or {}).get(c, ""), "market": mk, "group": "", "source": "操作員"})
    if names:
        for r in rows:
            if not r["name"]:
                r["name"] = names.get(r["code"], "")
    return rows


# ---------------------------------------------------------------- 參數解析 → argv(白名單)
def _p(params: dict, k: str, default=""):
    v = params.get(k, default)
    return v if v is not None else default


def _date_ok(s: str) -> bool:
    if not DATE_RX.fullmatch(s or ""):
        return False
    try:
        _dt.date.fromisoformat(s)
        return True
    except ValueError:
        return False


def resolve_argv(spec: dict, item_id: str, params: dict | None = None, environ: dict | None = None, check_files: bool = True) -> dict:
    """項目+參數 → {ok, argv, family, python, net, state, note};引擎缺/PLANNED/參數不合=ok False 誠實"""
    params = dict(params or {})
    idx = items_index(spec)
    if not ITEM_RX.fullmatch(item_id or "") or item_id not in idx:
        return {"ok": False, "state": "UNKNOWN_ITEM", "note": f"項目不在冊:{item_id}", "argv": []}
    ent = idx[item_id]
    it, fam = ent["item"], ent["family"]
    user = spec.get("user", {})
    if it.get("state") == "PLANNED" or not it.get("engine"):
        return {"ok": False, "state": "PLANNED", "family": fam, "note": it.get("note", "引擎候上船"), "argv": []}
    eng = it["engine"]
    eng_dir = VIA / eng["dir"]
    ef = newest(eng_dir, eng["glob"])
    if check_files and not ef:
        return {"ok": False, "state": "ENGINE_MISSING", "family": fam, "note": f"引擎缺 {eng['glob']}(先 git pull)", "argv": []}
    pyfam = eng.get("python") or ent["fam_python"]
    py = family_python(pyfam, environ)
    argv = [py["python"], str(ef) if ef else str(eng_dir / eng["glob"]), *eng.get("verb", [])]
    notes = []
    for kind in it.get("params", []):
        if kind == "range":
            s, e = str(_p(params, "start")).strip(), str(_p(params, "end")).strip()
            if s and s != "latest":
                if not _date_ok(s):
                    return {"ok": False, "state": "BAD_PARAM", "note": "start 需 YYYY-MM-DD", "argv": []}
                e = e or _dt.date.today().isoformat()
                if not _date_ok(e) or s > e:
                    return {"ok": False, "state": "BAD_PARAM", "note": "end 需 YYYY-MM-DD 且 ≥ start", "argv": []}
                argv += ["--start", s, "--end", e]
            else:
                notes.append("start=latest(引擎增量律)")
        elif kind == "start":
            s = str(_p(params, "start")).strip()
            if s and s != "latest":
                if not _date_ok(s):
                    return {"ok": False, "state": "BAD_PARAM", "note": "start 需 YYYY-MM-DD", "argv": []}
                argv += ["--start", s]
        elif kind == "since":
            s = str(_p(params, "since") or _p(params, "start")).strip()
            if s and s != "latest":
                if not _date_ok(s):
                    return {"ok": False, "state": "BAD_PARAM", "note": "since 需 YYYY-MM-DD", "argv": []}
                argv += ["--since", s]
        elif kind == "since_ym":
            s = str(_p(params, "since") or _p(params, "start")).strip()
            if s and s != "latest":
                if DATE_RX.fullmatch(s):
                    s = s[:7]
                if not YM_RX.fullmatch(s):
                    return {"ok": False, "state": "BAD_PARAM", "note": "since 需 YYYY-MM", "argv": []}
                argv += ["--since", s]
        elif kind == "days":
            d = str(_p(params, "days")).strip()
            if d:
                if not d.isdigit() or not 1 <= int(d) <= 3650:
                    return {"ok": False, "state": "BAD_PARAM", "note": "days 需 1~3650 整數", "argv": []}
                argv += ["--days", str(int(d))]
        elif kind == "codes":
            raw = _p(params, "codes")
            codes = [c.strip().upper() for c in (raw.split(",") if isinstance(raw, str) else list(raw)) if c and c.strip()]
            if len(codes) > 200 or any(not CODE_RX.fullmatch(c) for c in codes):
                return {"ok": False, "state": "BAD_PARAM", "note": "codes 需 4~6 位代碼(≤200 個)", "argv": []}
            codes = list(dict.fromkeys(codes))
            style = it.get("codes_style", "positional")
            if codes:
                if style == "positional":
                    argv += codes
                elif style == "--tickers":
                    argv += ["--tickers", ",".join(codes)]
                elif style == "--ticker":
                    argv += ["--ticker", codes[0]]
                    if len(codes) > 1:
                        notes.append(f"單票旗標:只取 {codes[0]}(其餘 {len(codes) - 1} 個另跑)")
            else:
                notes.append("無代碼=引擎預設")
        elif kind == "only":
            raw = _p(params, "only")
            ids = [x.strip() for x in (raw.split(",") if isinstance(raw, str) else list(raw)) if x and x.strip()]
            if not ids:
                cats = _p(params, "cats")
                cats = [x.strip() for x in (cats.split(",") if isinstance(cats, str) else list(cats)) if x and x.strip()] or list(user.get("macro_cats") or [])
                ids = macro_ids_for(spec, cats)
                if cats and not ids:
                    return {"ok": False, "state": "BAD_PARAM", "note": f"類別 {cats} 無 FRED 序列(冊缺或類別名不合)", "argv": []}
            if any(not FRED_RX.fullmatch(x) for x in ids):
                return {"ok": False, "state": "BAD_PARAM", "note": "only 序列代碼不合", "argv": []}
            if ids:
                argv += ["--only", ",".join(dict.fromkeys(ids))]
            else:
                notes.append("無勾選類別=全冊")
        elif kind == "lanes":
            raw = _p(params, "lanes") or it.get("lanes_default", "")
            lanes = [x.strip().upper() for x in str(raw).split(",") if x.strip()]
            if not lanes or any(not LANE_RX.fullmatch(x) for x in lanes):
                return {"ok": False, "state": "BAD_PARAM", "note": "lanes 需 L1~L15", "argv": []}
            argv += ["--lane", ",".join(lanes)]
        elif kind == "cats":
            raw = _p(params, "cats") or ",".join(user.get("global_cats") or [])
            cats = [x.strip() for x in str(raw).split(",") if x.strip()]
            if any(not CAT_RX.fullmatch(x) for x in cats):
                return {"ok": False, "state": "BAD_PARAM", "note": "cats 需英文類別名", "argv": []}
            if cats:
                argv += ["--cats", ",".join(cats)]
        elif kind == "dir":
            raw = str(_p(params, "dir") or user.get("vrn_dir") or "").strip()
            cand = Path(raw) if raw else None
            if cand is not None and not cand.is_absolute():
                cand = VIA / cand
            if cand is None or not cand.is_dir():
                dflt = VIA / spec["families"]["vrn"]["input"]["dir_default"]
                if cand is None and dflt.is_dir():
                    cand = dflt
                    notes.append("dir=預設 input_reports")
                else:
                    return {"ok": False, "state": "NEED_DIR", "family": fam, "note": f"報告夾缺:{cand or dflt}(先拖曳/選夾或 set vrn-dir=)", "argv": []}
            argv += ["--dir", str(cand)]
        elif kind == "code":
            c = str(_p(params, "code") or user.get("vap", {}).get("code") or spec.get("defaults", {}).get("vap_code", "2330")).strip().upper()
            if not CODE_RX.fullmatch(c):
                return {"ok": False, "state": "BAD_PARAM", "note": "code 需 4~6 位代碼", "argv": []}
            argv.append(c)
        elif kind == "vapone":
            v = dict(user.get("vap") or {})
            v.update({k: params[k] for k in ("out", "formats", "profile", "data", "config") if params.get(k)})
            out = str(v.get("out") or "VIA_Reports/vap_one")
            outp = Path(out) if Path(out).is_absolute() else VIA / out
            fm = str(v.get("formats") or "svg,html")
            if not re.fullmatch(r"^[a-z]+(,[a-z]+)*$", fm):
                return {"ok": False, "state": "BAD_PARAM", "note": "formats 需 svg,html,png,pdf,plotly 逗號清單", "argv": []}
            prof = str(v.get("profile") or "vap_spec_v1")
            if prof not in ("vap_spec_v1", "seaborn_stack_v23"):
                return {"ok": False, "state": "BAD_PARAM", "note": "profile 僅 vap_spec_v1|seaborn_stack_v23", "argv": []}
            if "--render" in argv:
                cfg = str(v.get("config") or "")
                cfgp = Path(cfg) if cfg and Path(cfg).is_absolute() else (VIA / cfg if cfg else None)
                if cfgp is None or not cfgp.is_file():
                    return {"ok": False, "state": "NEED_CONFIG", "family": fam, "note": "vap-config=<stack config.json> 缺(先 --demo 產生 demo_config.json 可改)", "argv": []}
                argv.append(str(cfgp))
                data = str(v.get("data") or "")
                if data:
                    dp = Path(data) if Path(data).is_absolute() else VIA / data
                    if not dp.is_file():
                        return {"ok": False, "state": "NEED_DATA", "family": fam, "note": f"vap-data 檔缺 {dp}", "argv": []}
                    argv += ["--data", str(dp)]
            argv += ["--out", str(outp), "--formats", fm, "--profile", prof]
        elif kind in ("period", "years"):
            pass  # PLANNED 項目(財報)參數只入冊
    return {"ok": True, "state": "READY", "family": fam, "python": py, "net": bool(it.get("net")), "argv": argv, "note": ";".join(notes), "zh": it.get("zh", item_id)}


# ---------------------------------------------------------------- set(操作員個別改動;鏡寫活冊)
def _input_tool():
    try:
        import importlib.util
        p = newest(VIA / "functional modules" / "VDF", "vdf_input_matrix_v*.py")
        if not p:
            return None
        spec = importlib.util.spec_from_file_location("vdf_input_matrix_e139", p)
        m = importlib.util.module_from_spec(spec)
        sys.modules["vdf_input_matrix_e139"] = m
        spec.loader.exec_module(m)
        return m
    except Exception:
        return None


def _market_of(code: str, spec: dict) -> str:
    for m in focus_members():
        if m["code"] == code and m["market"] in ("TWSE", "TPEX"):
            return m["market"]
    duckdb = _duckdb()
    if duckdb and DB_TW.exists():
        try:
            con = duckdb.connect(str(DB_TW), read_only=True)
            try:
                r = con.execute("SELECT market FROM tw_listings WHERE code = ? LIMIT 1", [code]).fetchone()
            finally:
                con.close()
            if r and str(r[0]).upper() in ("TWSE", "TPEX"):
                return str(r[0]).upper()
        except Exception:
            pass
    return ""


def apply_set(spec: dict, kv: dict, matrix_path: Path | None = None, mirror: bool = True) -> list:
    """k=v 逐項套用到 user 段(驗證;只增不減;changelog);鏡寫 VDF_Input_Interface_Matrix(台股代碼/財報期別與起始/VRN 路徑)"""
    u = spec.setdefault("user", {})
    notes, mirrored = [], []
    tool = _input_tool() if mirror else None
    mp = matrix_path or INPUT_MATRIX
    md = None
    if tool and mp.exists():
        try:
            md = tool.load(mp)
        except Exception:
            md = None
    for k, v in kv.items():
        v = "" if v is None else str(v).strip()
        k = str(k).split("#", 1)[0]   # 同鍵多筆:tw-add#2=…(頁面多選移除亦同)
        if k == "tw-add":
            code, _, mk = v.partition(":")
            code = code.strip().upper()
            mk = mk.strip().upper()
            if not CODE_RX.fullmatch(code):
                notes.append(f"FAIL:tw-add 代碼不合 {v}")
                continue
            if mk not in ("TWSE", "TPEX"):
                mk = _market_of(code, spec) or "TWSE"
                if mk == "TWSE" and not any(m["code"] == code for m in focus_members()):
                    notes.append(f"NOTE:{code} 市場未知=暫列 TWSE(tw-add {code}:TPEX 可改)")
            tc = u.setdefault("tw_codes", {"TWSE": [], "TPEX": []})
            other = "TPEX" if mk == "TWSE" else "TWSE"
            if code in tc.get(other, []):
                tc[other].remove(code)
            if code in tc.setdefault(mk, []):
                notes.append(f"SKIP:{code} 已在 {mk}")
            else:
                tc[mk].append(code)
                notes.append(f"OK:{code} 入 {mk}")
            if md is not None:
                mirrored.append(tool.add_ticker(md, "TW_FIN", code))
        elif k == "tw-remove":
            code = v.upper()
            hit = False
            for mk in ("TWSE", "TPEX"):
                if code in u.get("tw_codes", {}).get(mk, []):
                    u["tw_codes"][mk].remove(code)
                    hit = True
            notes.append(f"OK:{code} 移出清單" if hit else f"SKIP:{code} 不在操作員清單(焦點冊成員不可移;族群冊治理)")
            if hit and md is not None:
                mirrored.append(tool.rm_ticker(md, "TW_FIN", code))
        elif k == "start":
            item, _, d = v.partition(":")
            if not ITEM_RX.fullmatch(item) or (d != "latest" and not _date_ok(d)):
                notes.append(f"FAIL:start 需 <item>:YYYY-MM-DD|latest({v})")
                continue
            if d == "latest":
                u.setdefault("starts", {}).pop(item, None)
            else:
                u.setdefault("starts", {})[item] = d
            notes.append(f"OK:start[{item}]={d}")
            if item in ("tw_revenue_backfill", "fin_statements") and md is not None and d != "latest":
                mirrored.append(tool.set_tw(md, "start", d))
        elif k == "days":
            item, _, n = v.partition(":")
            if not ITEM_RX.fullmatch(item) or not n.isdigit() or not 1 <= int(n) <= 3650:
                notes.append(f"FAIL:days 需 <item>:1~3650({v})")
                continue
            u.setdefault("days", {})[item] = int(n)
            notes.append(f"OK:days[{item}]={int(n)}")
        elif k == "macro-cats":
            cats = [x.strip() for x in v.split(",") if x.strip()]
            known = {c["id"] for c in macro_categories(spec)}
            bad = [c for c in cats if c not in known]
            if bad:
                notes.append(f"FAIL:未知宏觀類別 {bad}(有效 {sorted(known)})")
                continue
            u["macro_cats"] = cats
            notes.append(f"OK:macro_cats={cats or '全冊'}")
        elif k == "macro-since":
            if v != "latest" and not _date_ok(v):
                notes.append("FAIL:macro-since 需 YYYY-MM-DD|latest")
                continue
            u["macro_since"] = v
            notes.append(f"OK:macro_since={v}")
        elif k == "fin-period":
            if v not in PERIODS:
                notes.append(f"FAIL:fin-period 僅 {'/'.join(PERIODS)}")
                continue
            u.setdefault("fin", {})["period"] = v
            notes.append(f"OK:fin.period={v}")
            if md is not None:
                mirrored.append(tool.set_tw(md, "period", "單季" if v == "當季" else v))
        elif k in ("fin-from", "fin-to"):
            if v and not YEAR_RX.fullmatch(v):
                notes.append(f"FAIL:{k} 需 YYYY")
                continue
            u.setdefault("fin", {})["year_from" if k == "fin-from" else "year_to"] = v
            notes.append(f"OK:fin.{'year_from' if k == 'fin-from' else 'year_to'}={v or '最新'}")
            if k == "fin-from" and v and md is not None:
                mirrored.append(tool.set_tw(md, "start", f"{v}-01-01"))
        elif k == "vrn-dir":
            if v and not (Path(v).is_absolute() or (VIA / v).exists()):
                notes.append(f"NOTE:vrn-dir 相對路徑以母倉為根:{v}")
            u["vrn_dir"] = v
            notes.append(f"OK:vrn_dir={v or '預設 input_reports'}")
            if md is not None:
                mirrored.append(tool.set_vrn(md, "path", v))
        elif k == "vrn-chain":
            ids = [x.strip() for x in v.split(",") if x.strip()]
            idx = items_index(spec)
            bad = [x for x in ids if x not in idx]
            if bad:
                notes.append(f"FAIL:vrn-chain 未知項目 {bad}")
                continue
            u["vrn_chain"] = ids
            notes.append(f"OK:vrn_chain={ids or '預設鏈'}")
        elif k.startswith("vap-"):
            key = k[4:]
            if key not in ("code", "formats", "profile", "out", "data", "config"):
                notes.append(f"FAIL:未知 vap 鍵 {k}")
                continue
            if key == "code" and not CODE_RX.fullmatch(v.upper()):
                notes.append("FAIL:vap-code 需 4~6 位代碼")
                continue
            u.setdefault("vap", {})[key] = v.upper() if key == "code" else v
            notes.append(f"OK:vap.{key}={v}")
        elif k == "global-cats":
            cats = [x.strip() for x in v.split(",") if x.strip()]
            if any(not CAT_RX.fullmatch(x) for x in cats):
                notes.append("FAIL:global-cats 需英文類別名")
                continue
            u["global_cats"] = cats
            notes.append(f"OK:global_cats={cats or '全類'}")
        else:
            notes.append(f"FAIL:未知鍵 {k}")
    if md is not None and mirrored:
        try:
            tool.save(md, mp, op="console-set(批390)", note="; ".join(mirrored)[:300])
            notes.append(f"MIRROR:{len(mirrored)} 筆鏡寫 {mp.name}")
        except Exception as exc:
            notes.append(f"NOTE:鏡寫失敗 {str(exc)[:60]}")
    u.setdefault("changelog", []).append({"ts": _dt.datetime.now().strftime("%Y-%m-%d %H:%M"), "ops": {k: str(v) for k, v in kv.items()}, "notes": notes[:20]})
    return notes


# ---------------------------------------------------------------- VRN 跑況判準
def classify_report(row: dict, n_metrics: int, n_fin: int, has_sidecar: bool) -> dict:
    """單報告三態:BASIC INFO / SUMMARY / FINANCIAL DATA(VERIFIED|FAIL|PENDING)"""
    basic_ok = bool(row.get("ticker")) and bool(row.get("report_date")) and (row.get("target_price") is not None or row.get("price") is not None)
    basic = "OK" if basic_ok else "FAIL"
    summary = "OK" if str(row.get("summary_head") or "").strip() else "FAIL"
    us = str(row.get("upside_state") or "")
    ps = str(row.get("price_state") or "")
    if (us in VERIFIED_STATES or ps in ("P_CONFIRMED_DB",)) and (n_metrics > 0 or n_fin > 0):
        fin = "VERIFIED"
    elif us in FAIL_STATES or ps == "DB_NO_MATCH" or (n_metrics == 0 and n_fin == 0):
        fin = "FAIL"
    else:
        fin = "PENDING"
    overall = "GREEN" if basic == "OK" and summary == "OK" and fin == "VERIFIED" else ("RED" if basic == "FAIL" or fin == "FAIL" else "YELLOW")
    return {"basic": basic, "summary": summary, "financial": fin, "overall": overall, "sidecar": has_sidecar,
            "upside_state": us, "price_state": ps, "n_metrics": n_metrics, "n_financial": n_fin}


def vrn_stage_matrix(con, zones: Path) -> list:
    rows = []
    have = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
    if "vrn_report_basic" not in have:
        return rows
    cols = [r[0] for r in con.execute('DESCRIBE "vrn_report_basic"').fetchall()]
    met = {}
    if "vrn_report_metrics" in have:
        met = {r[0]: r[1] for r in con.execute("SELECT report_file, count(*) FROM vrn_report_metrics GROUP BY 1").fetchall()}
    fin = {}
    if "vrn_report_financial" in have:
        fin = {r[0]: r[1] for r in con.execute("SELECT report_file, count(*) FROM vrn_report_financial GROUP BY 1").fetchall()}
    fp = {}
    if "vrn_four_point_digest" in have:
        fp = {r[0]: r[1] for r in con.execute("SELECT report_file, qc FROM vrn_four_point_digest").fetchall()}
    for rec in con.execute('SELECT * FROM "vrn_report_basic" ORDER BY report_date DESC, report_file').fetchall():
        row = dict(zip(cols, rec))
        rf = str(row.get("report_file") or "")
        side = (zones / f"{Path(rf).stem}.json").exists() if zones.exists() else False
        c = classify_report(row, int(met.get(rf, 0)), int(fin.get(rf, 0)), side)
        rows.append({"report_file": rf, "ticker": row.get("ticker"), "name": row.get("name_official"), "broker": row.get("broker"), "report_date": row.get("report_date"),
                     "target_price": row.get("target_price"), "price": row.get("price"), "four_point_qc": fp.get(rf, ""), **c})
    return rows


# ---------------------------------------------------------------- 狀況
def _read_json(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def _list_dir(p: Path, exts: tuple, limit: int = 300) -> list:
    out = []
    if not p.is_dir():
        return out
    for f in sorted(p.iterdir()):
        if f.is_file() and f.suffix.lower() in exts:
            st = f.stat()
            out.append({"name": f.name, "kb": st.st_size // 1024, "mtime": _dt.datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M")})
            if len(out) >= limit:
                break
    return out


def status(spec: dict | None = None, do_print: bool = True, reports: Path = REPORTS, db_tw: Path = DB_TW, db_gl: Path = DB_GL, environ: dict | None = None, hub_fn=None) -> dict:
    spec = spec or load_spec()
    hub = (hub_fn or hub_live)()
    rep = {"schema": "VIA.InputConsole.status.v1", "ts": _now(), "hub": hub, "bridge": BRIDGE, "via": str(VIA), "verdict": "GREEN", "notes": [],
           "db": {"source": "", "tables": {}}, "align": None, "coverage": None, "localdb": None, "tw_codes": [], "macro": {}, "vrn": {}, "vap": {}, "items": {}}
    duckdb = _duckdb()
    # 庫狀況:ENG073 架構冊快照(尾版 JSON)+ DuckDB 現值(可用時覆蓋)
    arch = _read_json(HERE / "VIA_VDFArchitecture_v0100.json")
    tables = {}
    if arch and isinstance(arch.get("inventory"), dict):
        for dbk, inv in arch["inventory"].items():
            for t, v in (inv.get("tables") or {}).items():
                tables[t] = {"db": dbk, "rows": v.get("rows"), "max": v.get("max"), "min": v.get("min"), "lag_days": v.get("lag_days"), "source": f"ENG073 {arch.get('stamp', '')}"}
        rep["db"]["source"] = f"VIA_VDFArchitecture_v0100.json({arch.get('stamp', '')})"
    names = {}
    live_tables = {}
    if duckdb:
        for dbk, dbp in (("tw", db_tw), ("gl", db_gl)):
            if not dbp.exists():
                continue
            try:
                con = duckdb.connect(str(dbp), read_only=True)
            except Exception as exc:
                rep["notes"].append({"lamp": "YELLOW", "note": f"{dbp.name} 開啟失敗 {str(exc)[:60]}"})
                continue
            try:
                for t in [r[0] for r in con.execute("SHOW TABLES").fetchall()]:
                    try:
                        cols = {r[0].lower(): r[0] for r in con.execute(f'DESCRIBE "{t}"').fetchall()}
                        n = con.execute(f'SELECT count(*) FROM "{t}"').fetchone()[0]
                        ent = {"db": dbk, "rows": n, "source": "DuckDB 現值"}
                        dc = next((cols[c] for c in ("date", "obs_date", "as_of", "asof_date", "ym", "published") if c in cols), None)
                        if dc:
                            mx, mn = con.execute(f'SELECT max(CAST("{dc}" AS VARCHAR)), min(CAST("{dc}" AS VARCHAR)) FROM "{t}"').fetchone()
                            ent.update({"max": mx, "min": mn})
                            try:
                                ent["lag_days"] = (_dt.date.today() - _dt.date.fromisoformat(str(mx)[:10])).days if mx and len(str(mx)) >= 10 else None
                            except Exception:
                                ent["lag_days"] = None
                        live_tables[t] = ent
                    except Exception:
                        continue
                if dbk == "tw" and "tw_listings" in live_tables:
                    try:
                        names = {str(r[0]): str(r[1]) for r in con.execute("SELECT code, name FROM tw_listings").fetchall()}
                    except Exception:
                        names = {}
                if dbk == "tw":
                    zones = VIA / spec["families"]["vrn"]["input"]["sidecars"]
                    try:
                        rep["vrn"]["reports"] = vrn_stage_matrix(con, zones)
                    except Exception as exc:
                        rep["vrn"]["reports"] = []
                        rep["notes"].append({"lamp": "YELLOW", "note": f"VRN 跑況讀取失敗 {str(exc)[:60]}"})
            finally:
                con.close()
        if live_tables:
            tables.update(live_tables)
            rep["db"]["source"] = (rep["db"]["source"] + " + " if rep["db"]["source"] else "") + "DuckDB 現值"
    else:
        rep["notes"].append({"lamp": "YELLOW", "note": "duckdb 缺(base):庫狀況用 ENG073 快照;VRN 跑況需 via_vdf_312/via_vrn_312 python(via-py)"})
    rep["db"]["tables"] = tables
    if not tables:
        rep["notes"].append({"lamp": "YELLOW", "note": "庫狀況空:正典庫缺或 ENG073 尚未 build(via-vdfarch build)"})
    # 對齊/覆蓋/本機三庫
    rep["align"] = _read_json(VIA / "VIA_Reports" / "vdf" / "universe" / "ALIGN_latest.json")
    rep["coverage"] = (_read_json(VIA / "VIA_Reports" / "vdf" / "local_db" / "COVERAGE_latest.json") or {}).get("tables") or None
    ld = _read_json(VIA / "VIA_Reports" / "vdf" / "local_db" / "RUN_latest.json")
    rep["localdb"] = {"verdict": ld.get("verdict"), "mode": ld.get("mode"), "ts": ld.get("ts"), "summary": ld.get("summary")} if ld else None
    if rep["align"] is None:
        rep["notes"].append({"lamp": "GREY", "note": "對齊未跑:via-align check(ENG081)"})
    elif rep["align"].get("verdict") == "MISALIGNED":
        rep["notes"].append({"lamp": "YELLOW", "note": f"日交易×籌碼未對齊:{rep['align'].get('note', '')[:120]}"})
    # 台股清單 / 宏觀
    rep["tw_codes"] = tw_codes(spec, names)
    series = macro_series(spec)
    cats = macro_categories(spec)
    sel = list(spec.get("user", {}).get("macro_cats") or [])
    rep["macro"] = {"categories": [{**c, "n": sum(1 for s in series if s["cat"] == c["id"]), "selected": c["id"] in sel} for c in cats],
                    "selected": sel, "since": spec.get("user", {}).get("macro_since", "latest"), "series": series, "n_series": len(series),
                    "selected_ids": macro_ids_for(spec, sel) if sel else []}
    if not series:
        rep["notes"].append({"lamp": "YELLOW", "note": "宏觀序列冊 macro_ssot 缺(類別勾選無法展開)"})
    # VRN 輸入
    vin = spec["families"]["vrn"]["input"]
    ud = spec.get("user", {}).get("vrn_dir") or ""
    udp = (Path(ud) if Path(ud).is_absolute() else VIA / ud) if ud else VIA / vin["dir_default"]
    rep["vrn"].update({"dir": str(udp), "dir_exists": udp.is_dir(), "dir_files": _list_dir(udp, tuple(vin["extensions"])),
                       "incoming": str(VIA / vin["incoming"]), "incoming_files": _list_dir(VIA / vin["incoming"], tuple(vin["extensions"])),
                       "sidecars": len(list((VIA / vin["sidecars"]).glob("*.json"))) if (VIA / vin["sidecars"]).exists() else 0,
                       "chain": spec.get("user", {}).get("vrn_chain") or spec["families"]["vrn"].get("chain_default", []),
                       "stage_labels": vin.get("stage_labels", {})})
    rep["vrn"].setdefault("reports", [])
    rs = rep["vrn"]["reports"]
    rep["vrn"]["summary"] = {"reports": len(rs), "verified": sum(1 for r in rs if r["financial"] == "VERIFIED"), "fail": sum(1 for r in rs if r["financial"] == "FAIL"),
                             "basic_ok": sum(1 for r in rs if r["basic"] == "OK"), "summary_ok": sum(1 for r in rs if r["summary"] == "OK")}
    # VAP 產出
    pages = {"VIA_UI_Dashboard_v0100.html": "儀表板(ENG009)", "VIA_UI_StdDashboard_v0100.html": "標準儀表板(ENG014)", "VIA_UI_VapStack_v0100.html": "圖組索引(ENG015)"}
    rep["vap"] = {"pages": [{"page": p, "zh": z, "exists": (UI_DIR / p).exists(), "mtime": _dt.datetime.fromtimestamp((UI_DIR / p).stat().st_mtime).strftime("%Y-%m-%d %H:%M") if (UI_DIR / p).exists() else ""} for p, z in pages.items()],
                  "user": spec.get("user", {}).get("vap", {})}
    led = VIA / (spec.get("user", {}).get("vap", {}).get("out") or "VIA_Reports/vap_one") / "vap_one_ledger.jsonl"
    if led.exists():
        try:
            rep["vap"]["last_render"] = json.loads(led.read_text(encoding="utf-8").strip().splitlines()[-1])
        except Exception:
            pass
    # 項目可跑態
    idx = items_index(spec)
    user = spec.get("user", {})
    for iid, ent in idx.items():
        it = ent["item"]
        params = {"start": user.get("starts", {}).get(iid, "latest"), "days": str(user.get("days", {}).get(iid, "") or "")}
        if "since" in it.get("params", []):
            params["since"] = user.get("macro_since", "latest") if iid.startswith("macro") else user.get("starts", {}).get(iid, "latest")
        r = resolve_argv(spec, iid, params, environ)
        rep["items"][iid] = {"zh": it.get("zh"), "family": ent["family"], "group": ent["group"], "state": r["state"], "note": r.get("note", ""),
                             "python": (r.get("python") or {}).get("state", ""), "net": bool(it.get("net")), "params": it.get("params", []), "start": user.get("starts", {}).get(iid, "latest"),
                             "days": user.get("days", {}).get(iid, ""), "argv_preview": " ".join(Path(x).name if os.sep in str(x) or "/" in str(x) else str(x) for x in r.get("argv", []))}
    n_planned = sum(1 for v in rep["items"].values() if v["state"] == "PLANNED")
    n_missing = sum(1 for v in rep["items"].values() if v["state"] == "ENGINE_MISSING")
    if n_missing:
        rep["notes"].append({"lamp": "RED", "note": f"引擎缺 {n_missing} 項(先 git pull)"})
    if n_planned:
        rep["notes"].append({"lamp": "GREY", "note": f"PLANNED {n_planned} 項(財報三大報表候 MOPS 引擎上船;不假跑)"})
    lamps = [n["lamp"] for n in rep["notes"]]
    rep["verdict"] = "RED" if "RED" in lamps else ("YELLOW" if "YELLOW" in lamps else "GREEN")
    try:
        _write_json(reports / "CONSOLE_latest.json", rep)
    except Exception as exc:
        rep["notes"].append({"lamp": "YELLOW", "note": f"存證失敗 {str(exc)[:60]}"})
    log_event("STATUS", rep["verdict"], hub=hub, tables=len(tables), reports=len(rs))
    if do_print:
        print(f"[via-console status] {rep['verdict']} · 樞紐 {hub} · 庫表 {len(tables)}({rep['db']['source'] or '無'})· 台股清單 {len(rep['tw_codes'])} · 宏觀序列 {len(series)}"
              f" · VRN 報告 {len(rs)}(VERIFIED {rep['vrn']['summary']['verified']}/FAIL {rep['vrn']['summary']['fail']})· 項目 {len(idx)}(PLANNED {n_planned})")
        for n in rep["notes"]:
            print(f"  {n['lamp']:<7} {n['note']}")
        for iid, v in rep["items"].items():
            if v["state"] not in ("READY",):
                print(f"  {v['state']:<14} {iid:<22} {v['note'][:80]}")
        print(f"  存證 {reports / 'CONSOLE_latest.json'}")
    return rep


# ---------------------------------------------------------------- 頁面
CSS = r"""
:root{--bg:#f4f6f8;--paper:#fff;--paper2:#f9fafb;--ink:#202833;--ink2:#465365;--mut:#596778;--line:#dfe4ea;--line2:#edf0f3;--soft:#eef3f6;--acc:#315f7d;--acc2:#dce9f1;--ok:#2f7652;--warn:#765418;--bad:#a64f46;--grey:#6e7581;--rail-w:372px;--radius:8px}
*{box-sizing:border-box}html,body{margin:0;background:var(--bg);color:var(--ink);font:12px/1.45 "Segoe UI","Noto Sans TC",system-ui,sans-serif}
header.top{position:sticky;top:0;z-index:5;display:flex;align-items:center;gap:12px;padding:8px 14px;background:var(--paper);border-bottom:1px solid var(--line)}
header.top h1{font-size:14px;margin:0}header.top .lamp{padding:2px 8px;border-radius:12px;font-weight:600;font-size:11px}
.lamp.LIVE{background:#dff3e6;color:var(--ok)}.lamp.SNAPSHOT{background:#fbeccd;color:var(--warn)}.lamp.OFFLINE{background:#f6dcd9;color:var(--bad)}
header.top .sp{flex:1}header.top small{color:var(--mut)}
.wrap{display:flex;min-height:calc(100vh - 42px)}
aside.rail{width:var(--rail-w);min-width:var(--rail-w);background:var(--paper);border-right:1px solid var(--line);padding:10px;overflow:auto}
main.work{flex:1;min-width:0;padding:12px 16px;overflow:auto}
.tabs{display:flex;gap:4px;margin-bottom:8px;flex-wrap:wrap}.tabs button{border:1px solid var(--line);background:var(--paper2);padding:6px 10px;border-radius:6px;cursor:pointer;font-weight:600;min-height:32px}
.tabs button.on{background:var(--acc);color:#fff;border-color:var(--acc)}
.pane{display:none}.pane.on{display:block}
details.grp{border:1px solid var(--line);border-radius:var(--radius);margin:6px 0;background:var(--paper)}details.grp>summary{cursor:pointer;padding:6px 8px;font-weight:600;background:var(--soft);border-radius:var(--radius) var(--radius) 0 0}
.item{display:grid;grid-template-columns:1fr auto;gap:4px 6px;align-items:center;padding:6px 8px;border-top:1px solid var(--line2)}
.item .zh{font-weight:600}.item .note{grid-column:1/-1;color:var(--mut);font-size:11px}.item .ctl{grid-column:1/-1;display:flex;flex-wrap:wrap;gap:4px 8px;align-items:center}
.item input[type=date],.item input[type=number],.item input[type=text],.item select{border:1px solid var(--line);border-radius:4px;padding:3px 5px;font:inherit;min-height:26px}
.item input[type=number]{width:74px}.item input[type=text].dir{width:100%}
.badge{padding:1px 6px;border-radius:10px;font-size:10px;font-weight:600;background:var(--soft);color:var(--ink2)}.badge.READY{background:#dff3e6;color:var(--ok)}.badge.PLANNED{background:#e6e8eb;color:var(--grey)}.badge.ENGINE_MISSING,.badge.NEED_DIR,.badge.BAD_PARAM{background:#f6dcd9;color:var(--bad)}
button.run{border:1px solid var(--acc);background:var(--acc);color:#fff;border-radius:5px;padding:3px 9px;cursor:pointer;min-height:26px;font:inherit}button.run:disabled{opacity:.45;cursor:not-allowed}
button.sm{border:1px solid var(--line);background:var(--paper2);border-radius:5px;padding:2px 8px;cursor:pointer;min-height:24px;font:inherit}
.codes{display:grid;grid-template-columns:1fr 1fr;gap:4px}.codes label{display:flex;gap:4px;align-items:center;white-space:nowrap;font-size:11px}
.drop{border:1.5px dashed #b9c3cd;border-radius:var(--radius);padding:14px;text-align:center;color:var(--mut);margin:6px 0;cursor:pointer}.drop.hover{border-color:var(--acc);background:var(--acc2);color:var(--acc)}
.prog{margin:6px 0}.bar{height:8px;border-radius:4px;background:var(--line2);overflow:hidden;position:relative}.bar i{display:block;height:100%;width:100%;background:repeating-linear-gradient(45deg,var(--acc) 0 10px,var(--acc2) 10px 20px);animation:mv 1s linear infinite}
.bar.ok i{background:var(--ok);animation:none}.bar.fail i{background:var(--bad);animation:none}.bar.idle i{background:var(--line);animation:none}@keyframes mv{from{background-position:0 0}to{background-position:40px 0}}
pre.log{max-height:160px;overflow:auto;background:#1f2530;color:#d7dde6;padding:8px;border-radius:6px;font:11px/1.4 Consolas,"SFMono-Regular",monospace;white-space:pre-wrap}
.via-matrix-bar{display:flex;gap:6px;align-items:center;margin:6px 0;flex-wrap:wrap}.via-q{border:1px solid var(--line);border-radius:4px;padding:4px 6px;min-width:220px;font:inherit}.via-cnt{color:var(--mut)}
table.via-tbl{width:100%;border-collapse:collapse;background:var(--paper);font-size:11.5px}table.via-tbl th{position:sticky;top:0;background:var(--soft);text-align:left;padding:5px 6px;border-bottom:1px solid var(--line);cursor:pointer;user-select:none;white-space:nowrap}
table.via-tbl th.sd::after{content:" ▼"}table.via-tbl th.sa::after{content:" ▲"}table.via-tbl td{padding:4px 6px;border-bottom:1px solid var(--line2);white-space:nowrap}table.via-tbl td.num{text-align:right;font-variant-numeric:tabular-nums}
table.via-tbl tr.on{background:var(--acc2)}td.lamp-ok,td.lamp-verified,td.lamp-green,td.lamp-aligned,td.lamp-ready{color:var(--ok);font-weight:600}td.lamp-fail,td.lamp-red,td.lamp-misaligned{color:var(--bad);font-weight:600}td.lamp-pending,td.lamp-yellow,td.lamp-partial{color:var(--warn);font-weight:600}
.tbox{overflow:auto;max-height:70vh;border:1px solid var(--line);border-radius:var(--radius)}.kpi{display:flex;gap:10px;flex-wrap:wrap;margin:6px 0}.kpi div{background:var(--paper);border:1px solid var(--line);border-radius:6px;padding:6px 10px;min-width:120px}.kpi b{display:block;font-size:16px}
.cmd{background:var(--paper2);border:1px dashed var(--line);border-radius:6px;padding:6px 8px;font:11px Consolas,monospace;white-space:pre-wrap;word-break:break-all;margin-top:6px}
@media (max-width:900px){.wrap{flex-direction:column}aside.rail{width:auto;min-width:0;border-right:0;border-bottom:1px solid var(--line)}}
"""

JS = r"""
var B='__BRIDGE__';var SNAP=null;try{SNAP=JSON.parse(document.getElementById('snap').textContent);}catch(e){SNAP=null;}
var SPEC=SNAP?SNAP.spec:{},ST=SNAP?SNAP.status:{},USER=SNAP?SNAP.user:{},MODE='OFFLINE',CSRF=((document.querySelector('meta[name="via-csrf"]')||{}).content||'').trim(),SAME=location.origin===B;
var OPS={};var CHECK={};
function $(id){return document.getElementById(id);}function el(t,c,h){var e=document.createElement(t);if(c)e.className=c;if(h!=null)e.innerHTML=h;return e;}function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
function canRun(){return MODE==='LIVE'&&SAME&&/^[A-Za-z0-9_-]{20,200}$/.test(CSRF);}
function postJson(path,body){return fetch(B+path,{method:'POST',headers:{'Content-Type':'application/json','X-VIA-CSRF':CSRF},body:JSON.stringify(body)}).then(function(r){return r.json().then(function(j){j._http=r.status;return j;});});}
function setMode(m){MODE=m;var l=$('lamp');l.className='lamp '+m;l.textContent=m==='LIVE'?'LIVE 樞紐同源(可啟動)':(m==='SNAPSHOT'?'SNAPSHOT 快照(只看;啟動請 via 帶起樞紐後開 '+B+'/console)':'OFFLINE');document.querySelectorAll('button.run').forEach(function(b){b.disabled=!canRun();});}
function boot(){if(location.protocol==='file:'){fetch(B+'/probe',{mode:'no-cors',cache:'no-store'}).then(function(){location.replace(B+'/console'+(location.hash||''));}).catch(function(){setMode('SNAPSHOT');});return;}
 fetch(B+'/console_status',{cache:'no-store'}).then(function(r){return r.json();}).then(function(j){if(j&&j.schema){ST=j;}setMode('LIVE');renderAll();}).catch(function(){setMode(SNAP?'SNAPSHOT':'OFFLINE');});}
// ---- 右側矩陣通用件:篩選+排序(預設大到小)+勾選/全選/全不選 ----
function viaMatrix(host,cols,rows,opts){opts=opts||{};var state={q:'',sortKey:opts.defaultSort||(cols[0]&&cols[0].key),desc:opts.desc!==false,checked:{}};
 var wrap=el('div','via-matrix'),bar=el('div','via-matrix-bar'),q=el('input','via-q');q.type='search';q.placeholder='篩選(任一欄含字)';var cnt=el('span','via-cnt');bar.appendChild(q);bar.appendChild(cnt);
 function mkBtn(t,fn){var b=el('button','sm',t);b.type='button';b.addEventListener('click',fn);return b;}
 if(opts.select){bar.appendChild(mkBtn('全選',function(){visible().forEach(function(r){state.checked[rid(r)]=true;});render();}));bar.appendChild(mkBtn('全不選',function(){state.checked={};render();}));}
 (opts.extra||[]).forEach(function(x){bar.appendChild(mkBtn(x[0],x[1]));});
 var box=el('div','tbox'),tbl=el('table','via-tbl');box.appendChild(tbl);wrap.appendChild(bar);wrap.appendChild(box);host.innerHTML='';host.appendChild(wrap);
 q.addEventListener('input',function(){state.q=q.value.trim().toLowerCase();render();});
 function rid(r){return String(r[opts.idKey||cols[0].key]);}
 function visible(){var out=rows.filter(function(r){if(!state.q)return true;return cols.some(function(c){return String(r[c.key]==null?'':r[c.key]).toLowerCase().indexOf(state.q)>=0;});});
  var c=cols.filter(function(x){return x.key===state.sortKey;})[0]||cols[0];out.sort(function(a,b){var x=a[c.key],y=b[c.key];if(c.num){x=Number(x)||0;y=Number(y)||0;return state.desc?y-x:x-y;}x=String(x==null?'':x);y=String(y==null?'':y);return state.desc?y.localeCompare(x,'zh-Hant'):x.localeCompare(y,'zh-Hant');});return out;}
 function render(){var vis=visible(),h='<thead><tr>'+(opts.select?"<th class='sel'>✓</th>":'');cols.forEach(function(c){h+="<th data-k='"+c.key+"' class='"+(c.key===state.sortKey?(state.desc?'sd':'sa'):'')+"'>"+esc(c.zh)+'</th>';});h+='</tr></thead><tbody>';
  if(!vis.length)h+="<tr><td colspan='"+(cols.length+1)+"'>(空;誠實:尚無資料)</td></tr>";
  vis.forEach(function(r){var id=rid(r);h+="<tr data-id='"+esc(id)+"'"+(state.checked[id]?" class='on'":'')+'>'+(opts.select?"<td class='sel'><input type='checkbox'"+(state.checked[id]?' checked':'')+'></td>':'');cols.forEach(function(c){var v=r[c.key];h+="<td class='"+(c.num?'num':'')+(c.lamp?' lamp-'+String(v==null?'':v).toLowerCase():'')+"'>"+(c.num&&typeof v==='number'?v.toLocaleString('en-US'):esc(v))+'</td>';});h+='</tr>';});
  tbl.innerHTML=h+'</tbody>';cnt.textContent=vis.length+' / '+rows.length+(opts.select?' · 已選 '+Object.keys(state.checked).length:'');
  tbl.querySelectorAll('th[data-k]').forEach(function(th){th.addEventListener('click',function(){var k=th.getAttribute('data-k');if(state.sortKey===k)state.desc=!state.desc;else{state.sortKey=k;state.desc=true;}render();});});
  if(opts.select)tbl.querySelectorAll('tr[data-id] input').forEach(function(cb){cb.addEventListener('change',function(){var id=cb.closest('tr').getAttribute('data-id');if(cb.checked)state.checked[id]=true;else delete state.checked[id];render();});});}
 render();return {selected:function(){return Object.keys(state.checked);},setRows:function(rs){rows=rs;render();},state:state};}
// ---- 左側輸入 ----
function itemState(id){var it=(ST.items||{})[id]||{};return it.state||'?';}
function paramWidgets(it,ctl){var ps=it.params||[],id=it.id,st=(ST.items||{})[id]||{};
 if(ps.indexOf('range')>=0||ps.indexOf('start')>=0||ps.indexOf('since')>=0||ps.indexOf('since_ym')>=0){var lab=el('label',null,'起始 ');var d=el('input');d.type=ps.indexOf('since_ym')>=0?'month':'date';d.id='p_'+id+'_start';var cur=(USER.starts||{})[id]||'';if(cur)d.value=ps.indexOf('since_ym')>=0?cur.slice(0,7):cur;lab.appendChild(d);var lt=el('label',null,' <input type="checkbox" id="p_'+id+'_latest"'+(cur?'':' checked')+'> 最新(預設)');ctl.appendChild(lab);ctl.appendChild(lt);
  d.addEventListener('change',function(){if(d.value){$('p_'+id+'_latest').checked=false;OPS['start']=id+':'+(d.value.length===7?d.value+'-01':d.value);}});lt.querySelector('input').addEventListener('change',function(e){if(e.target.checked){d.value='';OPS['start']=id+':latest';}});
  if(ps.indexOf('range')>=0){var e2=el('label',null,' 迄 ');var de=el('input');de.type='date';de.id='p_'+id+'_end';e2.appendChild(de);ctl.appendChild(e2);}}
 if(ps.indexOf('days')>=0){var l2=el('label',null,'天數 ');var n=el('input');n.type='number';n.min=1;n.max=3650;n.id='p_'+id+'_days';n.value=(USER.days||{})[id]||'';n.placeholder='引擎預設';l2.appendChild(n);ctl.appendChild(l2);n.addEventListener('change',function(){if(n.value)OPS['days']=id+':'+n.value;});}
 if(ps.indexOf('codes')>=0){var l3=el('label',null,'代碼 ');var s=el('select');s.multiple=true;s.size=3;s.id='p_'+id+'_codes';(ST.tw_codes||[]).forEach(function(c){var o=el('option',null,esc(c.code+' '+(c.name||'')+' '+c.market));o.value=c.code;s.appendChild(o);});l3.appendChild(s);ctl.appendChild(l3);var b1=el('button','sm','全選'),b2=el('button','sm','全不選');b1.type=b2.type='button';b1.onclick=function(){Array.prototype.forEach.call(s.options,function(o){o.selected=true;});};b2.onclick=function(){Array.prototype.forEach.call(s.options,function(o){o.selected=false;});};ctl.appendChild(b1);ctl.appendChild(b2);}
 if(ps.indexOf('only')>=0){ctl.appendChild(el('span','note','類別勾選見「總體經濟」區塊;無勾選=全冊'));}
 if(ps.indexOf('lanes')>=0){var l4=el('label',null,'車道 ');var t=el('input');t.type='text';t.id='p_'+id+'_lanes';t.value=it.lanes_default||'';t.size=18;l4.appendChild(t);ctl.appendChild(l4);}
 if(ps.indexOf('cats')>=0){var l5=el('label',null,'類別(逗號) ');var t2=el('input');t2.type='text';t2.id='p_'+id+'_cats';t2.value=(USER.global_cats||[]).join(',');t2.size=22;t2.placeholder='空=全類';l5.appendChild(t2);ctl.appendChild(l5);}
 if(ps.indexOf('dir')>=0){ctl.appendChild(el('span','note','報告夾=左上 VRN 輸入區(預設 input_reports)'));}
 if(ps.indexOf('code')>=0){var l6=el('label',null,'代碼 ');var s2=el('select');s2.id='p_'+id+'_code';(ST.tw_codes||[]).forEach(function(c){var o=el('option',null,esc(c.code+' '+(c.name||'')));o.value=c.code;if(c.code===((USER.vap||{}).code||'2330'))o.selected=true;s2.appendChild(o);});l6.appendChild(s2);ctl.appendChild(l6);s2.addEventListener('change',function(){OPS['vap-code']=s2.value;});}
 if(ps.indexOf('vapone')>=0){ctl.appendChild(el('span','note','格式/設定/資料檔=左下 VAP 區塊(個別可改)'));}
 if(ps.indexOf('period')>=0){ctl.appendChild(el('span','note','期別/年起迄=財報區塊(入冊;引擎候上船)'));}
 var stv=st.state||'?';var bd=el('span','badge '+stv,stv);ctl.appendChild(bd);if(st.note)ctl.appendChild(el('span','note',esc(st.note)));}
function collectParams(it){var id=it.id,p={},ps=it.params||[];var g=function(x){var e=$('p_'+id+'_'+x);return e?e.value:'';};
 if(ps.indexOf('range')>=0||ps.indexOf('start')>=0||ps.indexOf('since')>=0||ps.indexOf('since_ym')>=0){var lt=$('p_'+id+'_latest');var v=g('start');p.start=(lt&&lt.checked)||!v?'latest':(v.length===7?v+'-01':v);if(ps.indexOf('since')>=0||ps.indexOf('since_ym')>=0)p.since=p.start;if(ps.indexOf('range')>=0&&g('end'))p.end=g('end');}
 if(ps.indexOf('days')>=0&&g('days'))p.days=g('days');
 if(ps.indexOf('codes')>=0){var s=$('p_'+id+'_codes');if(s)p.codes=Array.prototype.filter.call(s.options,function(o){return o.selected;}).map(function(o){return o.value;}).join(',');}
 if(ps.indexOf('only')>=0){p.cats=selectedMacro().join(',');p.since=$('macro_since')&&$('macro_since').value?$('macro_since').value:'latest';}
 if(ps.indexOf('lanes')>=0)p.lanes=g('lanes');if(ps.indexOf('cats')>=0)p.cats=g('cats');
 if(ps.indexOf('dir')>=0)p.dir=$('vrn_dir').value;if(ps.indexOf('code')>=0)p.code=g('code');
 if(ps.indexOf('vapone')>=0){p.out=$('vap_out').value;p.formats=Array.prototype.filter.call(document.querySelectorAll('#vap_fmt input'),function(c){return c.checked;}).map(function(c){return c.value;}).join(',');p.profile=$('vap_profile').value;p.data=$('vap_data').value;p.config=$('vap_config').value;}
 return p;}
function selectedMacro(){return Array.prototype.filter.call(document.querySelectorAll('#macro_cats input'),function(c){return c.checked;}).map(function(c){return c.value;});}
function runItem(it,params){if(!canRun()){showCmd(it,params);return;}var box=$('prog');box.innerHTML='<div class="prog"><div class="bar"><i></i></div><div id="prog_txt">啟動 '+esc(it.zh)+' …</div><pre class="log" id="prog_log"></pre></div>';
 postJson('/console_run',{item:it.id,params:params}).then(function(j){if(!j.ok){$('prog_txt').textContent='拒:'+(j.err||j.note||'');$('prog').querySelector('.bar').className='bar fail';return;}$('prog_txt').textContent='執行中 '+esc(it.zh)+'(run '+(j.run_id||'')+')';pollRun('console:'+it.id);}).catch(function(e){$('prog_txt').textContent='樞紐錯誤 '+e;});}
var POLL=null;function pollRun(tid){if(POLL)clearInterval(POLL);function tick(){fetch(B+'/status',{cache:'no-store'}).then(function(r){return r.json();}).then(function(s){var e=s[tid];if(!e)return;var bar=$('prog').querySelector('.bar');$('prog_log').textContent=e.tail||'';bar.className='bar '+(e.state==='running'?'':(e.state==='ok'?'ok':'fail'));$('prog_txt').textContent=(e.zh||tid)+' · '+e.state+' · '+(e.elapsed||0)+'s'+(e.pct!=null?' · '+e.pct+'%':'');renderRuns(s);if(e.state!=='running'){clearInterval(POLL);POLL=null;refreshStatus();}}).catch(function(){});}
 POLL=setInterval(tick,2000);tick();}
function showCmd(it,params){var kv=Object.keys(params).filter(function(k){return params[k];}).map(function(k){return k+'='+params[k];}).join(' ');$('prog').innerHTML='<div class="cmd">SNAPSHOT 模式無法啟動;工作站等價短令:\nvia-console run --item '+esc(it.id)+(kv?' '+esc(kv):'')+'\n(或輸入 via 帶起樞紐後開 '+B+'/console 直接按啟動)</div>';}
function refreshStatus(){if(MODE!=='LIVE')return;fetch(B+'/console_status',{cache:'no-store'}).then(function(r){return r.json();}).then(function(j){if(j&&j.schema){ST=j;renderMatrices();}}).catch(function(){});}
function saveOps(){var ops=Object.assign({},OPS);var mc=selectedMacro();ops['macro-cats']=mc.join(',');if($('macro_since').value)ops['macro-since']=$('macro_since').value;ops['fin-period']=$('fin_period').value;ops['fin-from']=$('fin_from').value;ops['fin-to']=$('fin_to').value;ops['vrn-dir']=$('vrn_dir').value;
 ops['vap-out']=$('vap_out').value;ops['vap-profile']=$('vap_profile').value;ops['vap-formats']=Array.prototype.filter.call(document.querySelectorAll('#vap_fmt input'),function(c){return c.checked;}).map(function(c){return c.value;}).join(',');if($('vap_data').value)ops['vap-data']=$('vap_data').value;if($('vap_config').value)ops['vap-config']=$('vap_config').value;
 if(!canRun()){$('save_out').innerHTML='<div class="cmd">SNAPSHOT:工作站等價短令\nvia-console set '+esc(Object.keys(ops).filter(function(k){return ops[k]!=='';}).map(function(k){return k+'='+ops[k];}).join(' '))+'</div>';return;}
 postJson('/console_set',{ops:ops}).then(function(j){$('save_out').innerHTML='<div class="cmd">'+esc((j.notes||[j.err||'?']).join('\n'))+'</div>';OPS={};refreshStatus();});}
function addCode(){var c=$('tw_new').value.trim().toUpperCase(),m=$('tw_mkt').value;if(!/^\d{4,6}[A-Z]?$/.test(c)){$('save_out').innerHTML='<div class="cmd">代碼需 4~6 位</div>';return;}var ops={'tw-add':c+':'+m};if(!canRun()){$('save_out').innerHTML='<div class="cmd">SNAPSHOT:via-console set tw-add='+c+':'+m+'</div>';return;}postJson('/console_set',{ops:ops}).then(function(j){$('save_out').innerHTML='<div class="cmd">'+esc((j.notes||[]).join('\n'))+'</div>';refreshStatus();});}
function renderRail(){var fams=['vdf','vrn','vap'];fams.forEach(function(f){var pane=$('pane_'+f),fam=(SPEC.families||{})[f]||{};pane.innerHTML='';
  if(f==='vdf'){var tw=el('details','grp','<summary>台灣股票代碼冊(TWSE/TPEX;可新增)</summary>');tw.open=true;var body=el('div','item');body.innerHTML='<div class="ctl"><input type="text" id="tw_new" placeholder="代碼 如 2330" size="10"> <select id="tw_mkt"><option>TWSE</option><option>TPEX</option></select> <button class="sm" type="button" onclick="addCode()">新增</button> <span class="note">焦點冊 '+((ST.tw_codes||[]).filter(function(c){return c.source==="焦點冊";}).length)+' + 操作員 '+((ST.tw_codes||[]).filter(function(c){return c.source==="操作員";}).length)+'(右側「台股清單」可篩選/排序)</span></div>';tw.appendChild(body);pane.appendChild(tw);
   var mc=el('details','grp','<summary>總體經濟指標類別(勾選=FRED --only 展開;全選/全不選)</summary>');mc.open=true;var mb=el('div','item');var h='<div class="ctl"><button class="sm" type="button" onclick="document.querySelectorAll(\'#macro_cats input\').forEach(function(c){c.checked=true;})">全選</button><button class="sm" type="button" onclick="document.querySelectorAll(\'#macro_cats input\').forEach(function(c){c.checked=false;})">全不選</button> 起始 <input type="date" id="macro_since" value="'+esc(((ST.macro||{}).since||'')==='latest'?'':(ST.macro||{}).since)+'"> <span class="note">空=最新(增量律)</span></div><div class="codes" id="macro_cats">';((ST.macro||{}).categories||[]).forEach(function(c){h+='<label><input type="checkbox" value="'+esc(c.id)+'"'+(c.selected?' checked':'')+'> '+esc(c.zh)+' <span class="badge">'+c.n+'</span></label>';});mb.innerHTML=h+'</div>';mc.appendChild(mb);pane.appendChild(mc);
   var fin=el('details','grp','<summary>財報(當季/累計/年度;年起迄;DEFAULT=最新)</summary>');fin.open=true;var fb=el('div','item');var uf=USER.fin||{};fb.innerHTML='<div class="ctl">期別 <select id="fin_period">'+['當季','累計','年度'].map(function(p){return '<option'+(uf.period===p?' selected':'')+'>'+p+'</option>';}).join('')+'</select> 年起 <input type="number" id="fin_from" min="2000" max="2100" value="'+esc(uf.year_from||'')+'" placeholder="最新"> 年迄 <input type="number" id="fin_to" min="2000" max="2100" value="'+esc(uf.year_to||'')+'" placeholder="最新"> <span class="badge PLANNED">三大報表 PLANNED</span><span class="note">誠實:母倉無現役財報擷取引擎(MOPS 候源);設定先入冊;月營收(ENG075/063)可跑</span></div>';fin.appendChild(fb);pane.appendChild(fin);}
  if(f==='vrn'){var vi=el('details','grp','<summary>VRN 輸入(資料夾/拖曳/Windows 選夾)</summary>');vi.open=true;var vb=el('div','item');var v=ST.vrn||{};vb.innerHTML='<div class="ctl"><input type="text" class="dir" id="vrn_dir" value="'+esc(USER.vrn_dir||'')+'" placeholder="報告夾路徑(空=預設 '+esc(v.dir||'input_reports')+')"></div><div class="ctl"><label class="sm">Windows 選夾 <input type="file" id="vrn_pick" webkitdirectory multiple hidden></label><label class="sm">選檔 <input type="file" id="vrn_files" multiple accept=".pdf,.docx" hidden></label><span class="note">選夾/拖曳=上傳至樞紐 incoming('+esc(v.incoming||'')+')並自動設為報告夾</span></div><div class="drop" id="drop">拖曳 PDF/DOCX 或整個資料夾到這裡<br><small>樞紐未開=只列檔名(誠實)</small></div><ul id="drop_out" class="note"></ul><div class="ctl">鏈 <input type="text" id="vrn_chain" value="'+esc((v.chain||[]).join(','))+'" size="46"> <button class="run" id="vrn_go" type="button">▶ 啟動整條鏈</button></div><div class="note">報告夾 '+(v.dir_exists?'在('+((v.dir_files||[]).length)+' 件)':'缺')+' · incoming '+((v.incoming_files||[]).length)+' 件 · 首頁 sidecar '+(v.sidecars||0)+'</div>';vi.appendChild(vb);pane.appendChild(vi);}
  if(f==='vap'){var va=el('details','grp','<summary>VAP 簡輸入(個別可改)</summary>');va.open=true;var vab=el('div','item');var uv=USER.vap||{};vab.innerHTML='<div class="ctl">格式 <span id="vap_fmt">'+['svg','html','png','pdf','plotly'].map(function(x){return '<label><input type="checkbox" value="'+x+'"'+((uv.formats||'svg,html').split(',').indexOf(x)>=0?' checked':'')+'> '+x+'</label>';}).join(' ')+'</span> 風格 <select id="vap_profile"><option'+(uv.profile==='vap_spec_v1'?' selected':'')+'>vap_spec_v1</option><option'+(uv.profile==='seaborn_stack_v23'?' selected':'')+'>seaborn_stack_v23</option></select></div><div class="ctl">輸出夾 <input type="text" id="vap_out" value="'+esc(uv.out||'VIA_Reports/vap_one')+'" size="28"> 資料檔 <input type="text" id="vap_data" value="'+esc(uv.data||'')+'" size="22" placeholder="parquet/csv(選配)"> 設定 <input type="text" id="vap_config" value="'+esc(uv.config||'')+'" size="22" placeholder="stack config.json(--render 必要)"></div>';va.appendChild(vab);pane.appendChild(va);}
  (fam.groups||[]).forEach(function(g){var d=el('details','grp','<summary>'+esc(g.zh)+'</summary>');d.open=(f!=='vdf'||g.id==='tw_equity'||g.id==='db');(g.items||[]).forEach(function(it){var row=el('div','item');row.appendChild(el('span','zh',esc(it.zh)));var b=el('button','run','▶ 啟動');b.type='button';b.disabled=!canRun()||itemState(it.id)!=='READY';b.addEventListener('click',function(){runItem(it,collectParams(it));});row.appendChild(b);var ctl=el('div','ctl');paramWidgets(it,ctl);row.appendChild(ctl);if(it.note)row.appendChild(el('span','note',esc(it.note)));d.appendChild(row);});pane.appendChild(d);});});
 var go=$('vrn_go');if(go){go.disabled=!canRun();go.addEventListener('click',function(){var ids=$('vrn_chain').value.split(',').map(function(x){return x.trim();}).filter(Boolean);chainRun(ids);});}
 setupDrop();var sv=$('save');sv.onclick=saveOps;}
function chainRun(ids){if(!ids.length)return;if(!canRun()){$('prog').innerHTML='<div class="cmd">SNAPSHOT:via-console run --item '+esc(ids.join(' ; via-console run --item '))+' dir='+esc($('vrn_dir').value)+'</div>';return;}var i=0;function next(){if(i>=ids.length){$('prog_txt').textContent='整條鏈完成';refreshStatus();return;}var id=ids[i++];var it=findItem(id);if(!it){next();return;}var p=collectParams(it);p.dir=$('vrn_dir').value;$('prog').innerHTML='<div class="prog"><div class="bar"><i></i></div><div id="prog_txt">鏈 '+i+'/'+ids.length+' '+esc(it.zh)+'</div><pre class="log" id="prog_log"></pre></div>';
  postJson('/console_run',{item:id,params:p}).then(function(j){if(!j.ok){$('prog_txt').textContent='鏈停於 '+id+':'+(j.err||j.note||'');$('prog').querySelector('.bar').className='bar fail';return;}var tid='console:'+id;var t=setInterval(function(){fetch(B+'/status',{cache:'no-store'}).then(function(r){return r.json();}).then(function(s){var e=s[tid];if(!e)return;$('prog_log').textContent=e.tail||'';$('prog_txt').textContent='鏈 '+i+'/'+ids.length+' '+esc(it.zh)+' · '+e.state+' · '+(e.elapsed||0)+'s';renderRuns(s);if(e.state!=='running'){clearInterval(t);if(e.state==='ok')next();else{$('prog').querySelector('.bar').className='bar fail';$('prog_txt').textContent+='(任一失敗即停;誠實)';refreshStatus();}}});},2000);});}
 next();}
function findItem(id){var r=null;Object.keys(SPEC.families||{}).forEach(function(f){((SPEC.families[f]||{}).groups||[]).forEach(function(g){(g.items||[]).forEach(function(it){if(it.id===id)r=it;});});});return r;}
// ---- 拖曳/選夾 → 樞紐 /intake(dest=vrn_incoming;base64 JSON;既有道) ----
function setupDrop(){var z=$('drop');if(!z)return;['dragenter','dragover'].forEach(function(ev){z.addEventListener(ev,function(e){e.preventDefault();z.classList.add('hover');});});['dragleave','drop'].forEach(function(ev){z.addEventListener(ev,function(e){e.preventDefault();z.classList.remove('hover');});});
 z.addEventListener('drop',function(e){collectDropped(e.dataTransfer,function(files){uploadFiles(files);});});z.addEventListener('click',function(){$('vrn_files').click();});
 $('vrn_files').addEventListener('change',function(){uploadFiles(Array.prototype.map.call(this.files,function(f){return {file:f,rel:f.name};}));});$('vrn_pick').addEventListener('change',function(){uploadFiles(Array.prototype.map.call(this.files,function(f){return {file:f,rel:f.webkitRelativePath||f.name};}));});
 $('vrn_pick').parentNode.addEventListener('click',function(){$('vrn_pick').click();});}
function collectDropped(dt,done){var items=dt&&dt.items,files=[];function walk(entry,path,cb){if(entry.isFile)entry.file(function(f){files.push({file:f,rel:path+f.name});cb();});else if(entry.isDirectory){var rd=entry.createReader();rd.readEntries(function(ents){var n=ents.length;if(!n)return cb();ents.forEach(function(en){walk(en,path+entry.name+'/',function(){if(--n===0)cb();});});});}else cb();}
 if(items&&items[0]&&items[0].webkitGetAsEntry){var pend=items.length;Array.prototype.forEach.call(items,function(it){var en=it.webkitGetAsEntry();if(!en){if(--pend===0)done(files);return;}walk(en,'',function(){if(--pend===0)done(files);});});}else{Array.prototype.forEach.call(dt.files,function(f){files.push({file:f,rel:f.name});});done(files);}}
function b64(file){return new Promise(function(res,rej){var r=new FileReader();r.onload=function(){res(String(r.result).split(',')[1]||'');};r.onerror=rej;r.readAsDataURL(file);});}
function uploadFiles(files){var ul=$('drop_out');ul.innerHTML='';files=files.filter(function(x){return /\.(pdf|docx)$/i.test(x.rel);});if(!files.length){ul.innerHTML='<li>無 PDF/DOCX</li>';return;}
 if(!canRun()){files.forEach(function(x){ul.appendChild(el('li',null,esc(x.rel)+' · '+Math.round(x.file.size/1024)+' KB(SNAPSHOT:只列檔名;請 via 帶起樞紐)'));});return;}
 var i=0;function next(){if(i>=files.length){$('vrn_dir').value=(ST.vrn||{}).incoming||'';OPS['vrn-dir']=$('vrn_dir').value;ul.appendChild(el('li',null,'完成 '+files.length+' 件 → 報告夾已設為 incoming;按「啟動整條鏈」'));return;}var x=files[i++];if(x.file.size>50*1024*1024){ul.appendChild(el('li',null,esc(x.rel)+' 逾 50MB 拒'));next();return;}
  b64(x.file).then(function(s){return postJson('/intake',{name:x.file.name,b64:s,dest:'vrn_incoming'});}).then(function(j){ul.appendChild(el('li',null,esc(x.rel)+' · '+(j._http===201?'新收':(j._http===200?'冪等(已在)':'拒 '+(j.err||'')))));next();}).catch(function(e){ul.appendChild(el('li',null,esc(x.rel)+' 失敗 '+e));next();});}
 next();}
// ---- 右側矩陣 ----
function renderMatrices(){var t=(ST.db||{}).tables||{};var rows=Object.keys(t).map(function(k){var v=t[k];return {table:k,db:v.db,rows:v.rows,max:v.max||'',lag:v.lag_days==null?'':v.lag_days,source:v.source||''};});
 $('kpi_db').innerHTML='<div><b>'+rows.length+'</b>庫表</div><div><b>'+esc(((ST.align||{}).verdict)||'未跑')+'</b>日交易×籌碼對齊</div><div><b>'+esc((ST.hub||''))+'</b>樞紐</div><div><b>'+esc(((ST.vrn||{}).summary||{}).reports||0)+'</b>VRN 報告</div><div><b>'+esc((ST.tw_codes||[]).length)+'</b>台股清單</div>';
 viaMatrix($('m_db'),[{key:'table',zh:'表'},{key:'db',zh:'庫'},{key:'rows',zh:'列數',num:true},{key:'max',zh:'最新日'},{key:'lag',zh:'滯後(日)',num:true},{key:'source',zh:'來源'}],rows,{defaultSort:'rows'});
 var al=ST.align||{};var drows=(al.dates||[]).map(function(d){return d;});viaMatrix($('m_align'),[{key:'date',zh:'日期'},{key:'px_n',zh:'價表票數',num:true},{key:'chip_n',zh:'籌碼票數',num:true},{key:'both',zh:'皆有',num:true},{key:'px_only',zh:'只有價',num:true},{key:'chip_only',zh:'只有籌碼',num:true},{key:'verdict',zh:'判定',lamp:true}],drows,{defaultSort:'date'});
 $('align_note').textContent=al.note?al.note:'(未跑:via-align check)';var mm=(al.mismatch||{});var mrows=[].concat((mm.px_only||[]).map(function(c){return {code:c,side:'只有價'};}),(mm.chip_only||[]).map(function(c){return {code:c,side:'只有籌碼'};}));viaMatrix($('m_align2'),[{key:'code',zh:'票/代碼'},{key:'side',zh:'缺的一側'}],mrows,{desc:false});
 var cm=viaMatrix($('m_codes'),[{key:'code',zh:'代碼'},{key:'name',zh:'名稱'},{key:'market',zh:'市場'},{key:'group',zh:'族群'},{key:'source',zh:'來源'}],ST.tw_codes||[],{select:true,desc:false,extra:[['移出勾選(操作員項)',function(){var sel=cm.selected();if(!sel.length)return;var ops={};sel.forEach(function(c,i){ops['tw-remove'+(i?'#'+i:'')]=c;});if(!canRun()){$('save_out').innerHTML='<div class="cmd">SNAPSHOT:via-console set '+sel.map(function(c){return 'tw-remove='+c;}).join(' ')+'</div>';return;}postJson('/console_set',{ops:ops}).then(function(j){$('save_out').innerHTML='<div class="cmd">'+esc((j.notes||[]).join('\n'))+'</div>';refreshStatus();});}]]});
 viaMatrix($('m_macro'),[{key:'cat',zh:'類別'},{key:'sub',zh:'子題'},{key:'fred_id',zh:'FRED'},{key:'indicator',zh:'指標'},{key:'freq',zh:'頻率'}],(ST.macro||{}).series||[],{desc:false,defaultSort:'cat'});
 var vr=(ST.vrn||{}).reports||[];viaMatrix($('m_vrn'),[{key:'report_file',zh:'報告'},{key:'ticker',zh:'代碼'},{key:'name',zh:'名稱'},{key:'broker',zh:'券商'},{key:'report_date',zh:'日期'},{key:'basic',zh:'BASIC INFO',lamp:true},{key:'summary',zh:'SUMMARY',lamp:true},{key:'financial',zh:'FINANCIAL DATA',lamp:true},{key:'n_metrics',zh:'指標數',num:true},{key:'n_financial',zh:'財表列',num:true},{key:'four_point_qc',zh:'四點 QC',lamp:true},{key:'overall',zh:'總判',lamp:true}],vr,{defaultSort:'report_date'});
 var vs=(ST.vrn||{}).summary||{};$('vrn_kpi').innerHTML='<div><b>'+(vs.reports||0)+'</b>報告</div><div><b>'+(vs.basic_ok||0)+'</b>BASIC INFO OK</div><div><b>'+(vs.summary_ok||0)+'</b>SUMMARY OK</div><div><b>'+(vs.verified||0)+'</b>FINANCIAL VERIFIED</div><div><b>'+(vs.fail||0)+'</b>FINANCIAL FAIL</div>';
 var inc=((ST.vrn||{}).incoming_files||[]).map(function(f){return Object.assign({where:'incoming'},f);}).concat(((ST.vrn||{}).dir_files||[]).map(function(f){return Object.assign({where:'報告夾'},f);}));viaMatrix($('m_vrn_files'),[{key:'name',zh:'檔名'},{key:'where',zh:'位置'},{key:'kb',zh:'KB',num:true},{key:'mtime',zh:'修改時間'}],inc,{defaultSort:'mtime'});
 viaMatrix($('m_vap'),[{key:'zh',zh:'產出'},{key:'page',zh:'頁'},{key:'exists',zh:'在位'},{key:'mtime',zh:'更新'}],(ST.vap||{}).pages||[],{desc:false});
 var its=ST.items||{};viaMatrix($('m_items'),[{key:'id',zh:'項目'},{key:'family',zh:'族'},{key:'zh',zh:'說明'},{key:'state',zh:'可跑態',lamp:true},{key:'start',zh:'起始'},{key:'net',zh:'觸網'},{key:'argv_preview',zh:'argv 預覽'}],Object.keys(its).map(function(k){return Object.assign({id:k},its[k]);}),{desc:false,defaultSort:'family'});
 if(MODE==='LIVE')fetch(B+'/status',{cache:'no-store'}).then(function(r){return r.json();}).then(renderRuns).catch(function(){});}
function renderRuns(s){var rows=Object.keys(s||{}).map(function(k){var e=s[k];return {task:k,zh:e.zh,state:e.state,started:e.started||'',elapsed:e.elapsed||0,pct:e.pct==null?'':e.pct,rc:e.rc==null?'':e.rc,tail:(e.tail||'').slice(-120)};}).filter(function(r){return r.state!=='idle';});viaMatrix($('m_runs'),[{key:'task',zh:'任務'},{key:'zh',zh:'說明'},{key:'state',zh:'狀態',lamp:true},{key:'started',zh:'開始'},{key:'elapsed',zh:'秒',num:true},{key:'pct',zh:'%',num:true},{key:'rc',zh:'rc'},{key:'tail',zh:'尾行'}],rows,{defaultSort:'started'});}
function renderAll(){renderRail();renderMatrices();var notes=(ST.notes||[]).map(function(n){return n.lamp+' '+n.note;}).join(' · ');$('notes').textContent=notes||'GREEN';$('stamp').textContent='狀況 '+(ST.ts||'')+' · 頁 '+(SNAP?SNAP.built:'');}
document.querySelectorAll('.tabs button').forEach(function(b){b.addEventListener('click',function(){var grp=b.parentNode;grp.querySelectorAll('button').forEach(function(x){x.classList.remove('on');});b.classList.add('on');var pfx=grp.getAttribute('data-panes');document.querySelectorAll('.pane[data-grp="'+pfx+'"]').forEach(function(p){p.classList.toggle('on',p.id===pfx+'_'+b.getAttribute('data-p'));});});});
renderAll();boot();
"""

PAGE = r"""<!DOCTYPE html>
<html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light"><meta name="via-csrf" content="">
<title>VIA 輸入主控台 · 左輸入/右矩陣(批390)</title><style>__CSS__</style></head>
<body>
<header class="top"><h1>VIA 輸入主控台 <small>左輸入 / 右矩陣 · 批390 · MDL139</small></h1><span id="lamp" class="lamp OFFLINE">…</span><span class="sp"></span><small id="notes"></small><small id="stamp"></small><button class="sm" id="save" type="button">儲存設定</button></header>
<div class="wrap">
<aside class="rail">
 <div class="tabs" data-panes="pane"><button class="on" data-p="vdf">VDF 資料</button><button data-p="vrn">VRN 報告</button><button data-p="vap">VAP 圖</button></div>
 <div class="pane on" id="pane_vdf" data-grp="pane"></div><div class="pane" id="pane_vrn" data-grp="pane"></div><div class="pane" id="pane_vap" data-grp="pane"></div>
 <div id="save_out"></div>
 <div id="prog"></div>
</aside>
<main class="work">
 <div class="kpi" id="kpi_db"></div>
 <div class="tabs" data-panes="mx"><button class="on" data-p="db">庫狀況</button><button data-p="align">日交易×籌碼對齊</button><button data-p="codes">台股清單</button><button data-p="macro">宏觀序列</button><button data-p="vrn">VRN 跑況</button><button data-p="vap">VAP 產出</button><button data-p="items">項目冊</button><button data-p="runs">執行狀態</button></div>
 <div class="pane on" id="mx_db" data-grp="mx"><div id="m_db"></div></div>
 <div class="pane" id="mx_align" data-grp="mx"><p class="note" id="align_note"></p><div id="m_align"></div><h3>最新日不一致清單</h3><div id="m_align2"></div></div>
 <div class="pane" id="mx_codes" data-grp="mx"><div id="m_codes"></div></div>
 <div class="pane" id="mx_macro" data-grp="mx"><div id="m_macro"></div></div>
 <div class="pane" id="mx_vrn" data-grp="mx"><div class="kpi" id="vrn_kpi"></div><div id="m_vrn"></div><h3>輸入檔</h3><div id="m_vrn_files"></div></div>
 <div class="pane" id="mx_vap" data-grp="mx"><div id="m_vap"></div></div>
 <div class="pane" id="mx_items" data-grp="mx"><div id="m_items"></div></div>
 <div class="pane" id="mx_runs" data-grp="mx"><div id="m_runs"></div></div>
</main>
</div>
<script id="snap" type="application/json">__SNAP__</script>
<script>__JS__</script>
</body></html>
"""

CDN_RX = re.compile(r"<(?:script|link)[^>]+(?:src|href)=[\"']https?://", re.I)


def spec_lite(spec: dict) -> dict:
    """頁內嵌冊(去引擎路徑細節;保留 id/zh/params/note/lanes_default/state)"""
    out = {"families": {}}
    for fam, f in spec.get("families", {}).items():
        out["families"][fam] = {"zh": f.get("zh"), "groups": [{"id": g["id"], "zh": g.get("zh"), "items": [{k: it[k] for k in ("id", "zh", "params", "note", "lanes_default", "state", "codes_style", "net") if k in it} for it in g.get("items", [])]} for g in f.get("groups", [])]}
        if fam == "vrn":
            out["families"][fam]["chain_default"] = f.get("chain_default", [])
    return out


def build(spec: dict | None = None, out: Path = OUT_PAGE, reports: Path = REPORTS, do_print: bool = True, st: dict | None = None, hub_fn=None) -> Path:
    spec = spec or load_spec()
    st = st or status(spec, do_print=False, reports=reports, hub_fn=hub_fn)
    snap = {"built": _now(), "spec": spec_lite(spec), "user": spec.get("user", {}), "status": st}
    js = json.dumps(snap, ensure_ascii=False, default=str).replace("</", "<\\/")
    page = PAGE.replace("__CSS__", CSS).replace("__SNAP__", js).replace("__JS__", JS.replace("__BRIDGE__", BRIDGE))
    assert not CDN_RX.search(page), "零 CDN 律"
    _write_text(out, page)
    log_event("BUILD", str(out), bytes=len(page))
    if do_print:
        print(f"[via-console build] {out}({len(page) // 1024} KB;零 CDN;樞紐 {st.get('hub')})· 看頁:via-open 主控台 · LIVE:{BRIDGE}/console")
    return out


# ---------------------------------------------------------------- run(前景;操作員按啟動)
def run(spec: dict, item_id: str, params: dict, dry: bool = False, runner=None) -> int:
    r = resolve_argv(spec, item_id, params)
    if not r["ok"]:
        print(f"[via-console run] {r['state']}:{r.get('note', '')}")
        return 2
    print(f"[via-console run] {r['zh']} · {'DRY ' if dry else ''}argv={' '.join(r['argv'])}" + (f" · {r['note']}" if r.get("note") else ""))
    if dry:
        return 0
    env = dict(os.environ)
    env.update({"PYTHONUTF8": "1", "VIA_NO_OPEN": "1", "PYTHONIOENCODING": "utf-8"})
    if r.get("net"):
        env["VIA_NET_CONSENT"] = "YES"
        env["VIA_SCRAPE_CONSENT"] = "YES"
    t0 = _dt.datetime.now()
    proc = (runner or subprocess.run)(r["argv"], cwd=str(VIA), env=env, stdin=subprocess.DEVNULL)
    rc = getattr(proc, "returncode", 0)
    log_event("RUN", item_id, rc=rc, secs=int((_dt.datetime.now() - t0).total_seconds()), argv=r["argv"][1:])
    print(f"[via-console run] {item_id} rc={rc}")
    return rc


# ---------------------------------------------------------------- 自測
def selftest() -> int:
    import tempfile
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    spec = load_spec()
    idx = items_index(spec)
    missing = [i for i, e in idx.items() if e["item"].get("state") != "PLANNED" and not newest(VIA / e["item"]["engine"]["dir"], e["item"]["engine"]["glob"])]
    chk("① 冊載入(三族;項目 ≥ 25;每項綁母倉現役引擎尾版;PLANNED 只財報三大報表)", len(idx) >= 25 and not missing and [i for i, e in idx.items() if e["item"].get("state") == "PLANNED"] == ["fin_statements"],
        f"(項目 {len(idx)};引擎缺 {missing})")
    r1 = resolve_argv(spec, "tw_history", {"start": "2024-01-01", "end": "2024-03-31"}, check_files=True)
    r2 = resolve_argv(spec, "tw_chips", {"days": "30"})
    r3 = resolve_argv(spec, "tw_revenue_codes", {"codes": "2330,2454,2330"})
    r4 = resolve_argv(spec, "tw_need", {"codes": "2330,2454", "start": "2023-01-01"})
    r5 = resolve_argv(spec, "vrn_fourpoint", {"codes": "2330,2454"})
    r6 = resolve_argv(spec, "tw_history", {"start": "2024-13-01"})
    r7 = resolve_argv(spec, "tw_prices_inc", {"start": "latest"})
    r8 = resolve_argv(spec, "fin_statements", {})
    r9 = resolve_argv(spec, "vrn_firstpage", {"dir": "/nonexistent_dir_xyz"})
    r10 = resolve_argv(spec, "tw_revenue_backfill", {"since": "2023-05-15"})
    r11 = resolve_argv(spec, "macro_lanes", {})
    chk("② 參數→argv 白名單(range 成對/days/codes 三風格 positional|--tickers|--ticker 去重/since_ym 截月/lanes 預設/latest 不帶旗標/壞日期 BAD_PARAM/PLANNED 不假跑/報告夾缺 NEED_DIR)",
        r1["ok"] and r1["argv"][-4:] == ["--start", "2024-01-01", "--end", "2024-03-31"] and r2["ok"] and r2["argv"][-2:] == ["--days", "30"]
        and r3["ok"] and r3["argv"][-2:] == ["2330", "2454"] and r4["ok"] and r4["argv"][-4:] == ["--start", "2023-01-01", "--tickers", "2330,2454"]
        and r5["ok"] and r5["argv"][-2:] == ["--ticker", "2330"] and "單票" in r5["note"] and not r6["ok"] and r6["state"] == "BAD_PARAM"
        and r7["ok"] and "--start" not in r7["argv"] and not r8["ok"] and r8["state"] == "PLANNED" and not r9["ok"] and r9["state"] == "NEED_DIR"
        and r10["ok"] and r10["argv"][-2:] == ["--since", "2023-05"] and r11["ok"] and r11["argv"][-2:] == ["--lane", "L8,L9,L10,L11,L14"],
        f"({[x['state'] for x in (r1, r2, r3, r4, r5, r6, r7, r8, r9, r10, r11)]})")
    series = macro_series(spec)
    ids_b = macro_ids_for(spec, ["Business"])
    ids_pl = macro_ids_for(spec, ["Prices", "Labor"])
    ro = resolve_argv(spec, "macro_fred", {"cats": "Business", "since": "2020-01-01"})
    chk("③ 宏觀類別展開(macro_ssot fred_id;Business=PMI/ISM ≥ 10;通膨+就業 ≥ 30;--only 逗號冊 + --since;未知類別誠實 BAD_PARAM)",
        len(series) > 100 and len(ids_b) >= 10 and len(ids_pl) >= 30 and ro["ok"] and "--only" in ro["argv"] and ro["argv"][ro["argv"].index("--only") + 1] == ",".join(ids_b) and ro["argv"][-2:] == ["--since", "2020-01-01"]
        and not resolve_argv(spec, "macro_fred", {"cats": "NoSuchCat"})["ok"], f"(序列 {len(series)};Business {len(ids_b)};Prices+Labor {len(ids_pl)})")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        sp = root / "spec.json"
        sp.write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
        s2 = load_spec(sp)
        mp = root / "matrix.json"
        mp.write_text(INPUT_MATRIX.read_text(encoding="utf-8-sig"), encoding="utf-8") if INPUT_MATRIX.exists() else None
        n1 = apply_set(s2, {"tw-add": "6488:TPEX", "tw-add#2": "2330", "start": "tw_history:2024-01-01", "days": "tw_chips:45", "macro-cats": "Business,Prices", "fin-period": "累計", "fin-from": "2022", "fin-to": "2026", "vrn-dir": "functional modules/VRN/input/incoming", "vap-code": "2317", "vap-formats": "svg,png"}, matrix_path=mp, mirror=INPUT_MATRIX.exists())
        n2 = apply_set(s2, {"tw-add": "6488:TPEX", "tw-remove": "6488", "macro-cats": "Nope", "fin-period": "半年", "start": "tw_history:latest"}, matrix_path=mp, mirror=INPUT_MATRIX.exists())
        codes = tw_codes(s2)
        u = s2["user"]
        mir = json.loads(mp.read_text(encoding="utf-8")) if mp.exists() else None
        chk("④ set 個別改動(TPEX 新增/焦點冊已含 2330 去重/起始日與天數逐項/宏觀類別驗證/財報期別與年起迄/VRN 夾/VAP;重複 SKIP;移除;未知類別與期別 FAIL;latest 清除;changelog 兩筆;鏡寫活冊 TW_FIN)",
            any(n.startswith("OK:6488 入 TPEX") for n in n1) and u["tw_codes"]["TPEX"] == [] and u["starts"].get("tw_history") is None and u["days"]["tw_chips"] == 45
            and u["macro_cats"] == ["Business", "Prices"] and u["fin"] == {"period": "累計", "year_from": "2022", "year_to": "2026"} and u["vrn_dir"].endswith("incoming")
            and u["vap"]["code"] == "2317" and u["vap"]["formats"] == "svg,png" and any(n.startswith("SKIP:6488 已在") for n in n2) and any("6488 移出" in n for n in n2)
            and any(n.startswith("FAIL:未知宏觀類別") for n in n2) and any(n.startswith("FAIL:fin-period") for n in n2) and len(u["changelog"]) == 2
            and not any(c["code"] == "6488" and c["source"] == "操作員" for c in codes) and (mir is None or ("6488" in mir["sections"]["TW_FIN"].get("removed_tickers", []) or "6488" not in mir["sections"]["TW_FIN"].get("tickers", []))
                                                                                            and mir["sections"]["TW_FIN"]["period_mode"] == "累計" and mir["sections"]["TW_FIN"]["start_date"] == "2022-01-01"),
            f"(n1 {n1[:6]};n2 {n2[:5]};user {json.dumps({k: u[k] for k in ('tw_codes', 'starts', 'days', 'fin')}, ensure_ascii=False)})")
        c_ok = classify_report({"ticker": "2330", "report_date": "2026-09-01", "target_price": 1200.0, "price": 1000.0, "summary_head": "台積電…", "upside_state": "EXACT_MATCH_DB", "price_state": "P_CONFIRMED_DB"}, 3, 5, True)
        c_fail = classify_report({"ticker": "2330", "report_date": "2026-09-01", "target_price": 1200.0, "price": 1000.0, "summary_head": "", "upside_state": "FORMULA_MISMATCH", "price_state": "DB_NO_MATCH"}, 0, 0, False)
        c_pend = classify_report({"ticker": "2330", "report_date": "2026-09-01", "target_price": 1200.0, "price": None, "summary_head": "x", "upside_state": "SINGLE_SOURCE", "price_state": ""}, 2, 0, True)
        chk("⑤ VRN 跑況判準(BASIC INFO/SUMMARY/FINANCIAL DATA:VERIFIED 需核對態+指標;FAIL=公式不符/無指標;其餘 PENDING;總判 GREEN/RED/YELLOW)",
            c_ok == {**c_ok, "basic": "OK", "summary": "OK", "financial": "VERIFIED", "overall": "GREEN"} and c_fail["financial"] == "FAIL" and c_fail["summary"] == "FAIL" and c_fail["overall"] == "RED"
            and c_pend["financial"] == "PENDING" and c_pend["overall"] == "YELLOW")
        rep_dir = root / "reports"
        st = status(s2, do_print=False, reports=rep_dir, db_tw=root / "no.duckdb", db_gl=root / "no_gl.duckdb", hub_fn=lambda: "SNAPSHOT")
        chk("⑥ status 結構(hub 三態/庫狀況 ENG073 快照或空誠實/台股清單 焦點冊≥100/宏觀類別 13 含計數/VRN 輸入+跑況摘要/VAP 頁/項目可跑態含 PLANNED;CONSOLE_latest.json 落檔)",
            st["hub"] == "SNAPSHOT" and st["schema"] == "VIA.InputConsole.status.v1" and len(st["tw_codes"]) >= 100 and len(st["macro"]["categories"]) == 13
            and all("n" in c for c in st["macro"]["categories"]) and "summary" in st["vrn"] and "reports" in st["vrn"] and len(st["vap"]["pages"]) == 3
            and st["items"]["fin_statements"]["state"] == "PLANNED" and st["items"]["tw_history"]["state"] == "READY" and (rep_dir / "CONSOLE_latest.json").exists(),
            f"(hub {st['hub']};表 {len(st['db']['tables'])};清單 {len(st['tw_codes'])};項目 {len(st['items'])})")
        out = root / "VIA_UI_InputConsole_v0100.html"
        build(s2, out=out, reports=rep_dir, do_print=False, st=st)
        page = out.read_text(encoding="utf-8")
        m = re.search(r'<script id="snap" type="application/json">(.*?)</script>', page, re.S)
        snap = json.loads(m.group(1).replace("<\\/", "</")) if m else None
        chk("⑦ 頁面(零 CDN;左 rail 三族分頁+右矩陣八頁;拖曳區/選夾 webkitdirectory/全選全不選/排序篩選/進度動畫;內嵌快照 JSON 可解析;CSRF meta 契約;同源樞紐 /console 道)",
            not CDN_RX.search(page) and 'class="rail"' in page and 'id="pane_vrn"' in page and 'id="mx_align"' in page and 'webkitdirectory' in page and 'id="drop"' in page
            and "全不選" in page and "viaMatrix" in page and "@keyframes mv" in page and snap is not None and snap["status"]["hub"] == "SNAPSHOT" and '<meta name="via-csrf" content="">' in page
            and "/console_run" in page and "/console_set" in page and "/console_status" in page and "dest:'vrn_incoming'" in page and page.count("<script") == 2,
            f"({len(page) // 1024} KB)")
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑧ 紀律宣告(只增不減/正本零觸碰/誠實三態/零 CDN/尾版律/Zero-Hydra/ACCEL-BRIDGE)",
        all(k in src for k in ("只增不減", "正本零觸碰", "誠實三態", "零 CDN", "尾版律", "Zero-Hydra", "ACCEL-BRIDGE")))
    print(f"  [計] 八檢 OK {8 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


# ---------------------------------------------------------------- CLI
def _kv(a: list) -> dict:
    out = {}
    for x in a:
        if "=" in x and not x.startswith("--"):
            k, _, v = x.partition("=")
            out[k.strip()] = v.strip()
    return out


def _arg(a: list, flag: str, default=None):
    if flag in a:
        i = a.index(flag)
        if i + 1 < len(a):
            return a[i + 1]
    return default


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== 輸入主控台(CGC_MDL139_InputConsole)· 八檢自測(零網路;臨時冊)===")
        return selftest()
    verb = next((x for x in a if x in VERBS), "build")   # 動詞白名單(旗標值不得誤判為動詞)
    as_json = "--json" in a
    try:
        spec = load_spec()
        if verb == "status":
            rep = status(spec, do_print=not as_json)
            if as_json:
                print(json.dumps(rep, ensure_ascii=False, indent=1, default=str))
            return 0 if rep["verdict"] != "RED" else 2
        if verb == "set":
            kv = _kv(a)
            if not kv:
                print(__doc__)
                return 2
            notes = apply_set(spec, kv)
            save_spec(spec)
            for n in notes:
                print(f"  {n}")
            return 0 if not any(n.startswith("FAIL") for n in notes) else 2
        if verb == "argv":
            item = _arg(a, "--item", "")
            r = resolve_argv(spec, item, _kv(a))
            print(json.dumps(r, ensure_ascii=False, indent=1, default=str) if as_json else (f"{r['state']} {' '.join(r['argv'])} {r.get('note', '')}"))
            return 0 if r["ok"] else 2
        if verb == "run":
            return run(spec, _arg(a, "--item", ""), _kv(a), dry="--dry" in a)
        out = build(spec)
        if "--open" in a:
            print(f"  [看頁] via-open 主控台(零跳出律;或 {BRIDGE}/console)")
        return 0
    except FileNotFoundError as exc:
        print(f"[FAIL] 冊缺 {exc}")
        return 3
    except BrokenPipeError:
        return 0


if __name__ == "__main__":
    sys.exit(main())
