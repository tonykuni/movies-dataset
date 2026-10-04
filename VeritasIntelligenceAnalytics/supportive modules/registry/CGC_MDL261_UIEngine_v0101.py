#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""CGC_MDL261_UIEngine v0101 — 薄尾:全滑鼠輸入(VCGC 兩個位置 · VDF 三大類)· 右面板多頁(首頁三矩陣 · 結果 · 末頁細節矩陣)· 元件註冊 / 版本鎖

操作員 2026-10-04:「左輸入功能區、右顯示、多頁式:第一頁 輸入摘要去重矩陣 · 引擎工具功能矩陣 · 運作結果矩陣;其他頁都是結果;
  最後頁把 WORKFLOW · 邏輯 · REGEX 等所有細節矩陣放最後一頁,非常詳細、小字體、自動優化 LAYOUT、響應式。
  VCGC 輸入只有系統存放位置及資料庫兩個位置;避免用鍵盤,全用滑鼠:WINDOW I/O 拖曳式 · 下拉選單 · 打勾;介面全部自適應;
  顯示所有元件都有註冊及版本號鎖住。VDF 分大類輸入(台股 · 主動式 ETF 清單全抓 量價 / 籌碼 / 月營收;財報單獨擷取 2330 3324 NVDA 預設)」
  「分類後的參數都有 DEFAULT 可增減;起始日可分大群改,不可單獨改」「自動跳出 HTML U/I 不走 SERVER;自適應銜接各種模板設計風格」。
  · 內建標準範本換成本版(左 = 輸入功能區、右 = 多頁顯示);頁上沒有任何文字輸入框(只有下拉 · 打勾 · 拖放 · 按鈕)。
    拖放:瀏覽器不給完整路徑(安全限制)→ 拿檔名 / 夾名對引擎掃到的候選位置;對不到照實說,改用下拉或 PS 啟動器 -Pick(Windows 原生選夾窗)。
  · 套用不走伺服器:頁上「匯出輸入」下載 VIA_UI_Input.json → PS 啟動器 Start-VIA-UIEngine-v0101.ps1 自動從「下載」夾匯入
    (本檔 import:位置 · 範本 · 主題 · 勾選族群 → ui_config.json 工作副本;起始日 / 成員 / as-of → VDF_MDL012 ui-import 寫成員帳本)→ 重產 → 自動開。
  · 元件矩陣:每支元件 尾版號 · sha256 · 編號(編號冊)· 註冊(元件註冊冊)· 鎖(工具鎖冊路徑 / 交接收據 sha 相符且 rc 0)→ 燈。
  · VDF 資料:直接叫 VDF_MDL012 尾版的 gather(同一份族群快照;拿不到退 VDF_FetchGroups_SNAPSHOT_latest.json)。
其餘(參數疊層 · 自訂範本 Jinja 沙盒 / 逐變數代換 · DuckDB 顯式 · serve)全照 v0100;預設仍 file://,不需伺服器(L100)。
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

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 全導入令;graceful 零行為變更) =====
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
    """統包唯一網路工具惰性載入;本檔零網路,橋只為全樹一致。"""
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

import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import os
import platform
import re
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIOR_PATH = HERE / "CGC_MDL261_UIEngine_v0100.py"
_spec = importlib.util.spec_from_file_location("CGC_MDL261_UIEngine_v0100_for_v0101", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    """薄尾轉接:本版沒蓋的公開名稱照前版(TAILAPI)。"""
    return getattr(PRIOR, name)


VIA = PRIOR.VIA
TAG = f"CGC_MDL261_UIEngine v{Path(__file__).stem.rsplit('_v', 1)[-1]}"
PRIOR.TAG = TAG
VDF = VIA / "functional modules" / "VDF"
REG = VIA / "supportive modules" / "registry"
NUMBER_DIR = REG / "VIA_NumberBooks"
EVID = VIA / "docs" / "handoff" / "evidence"
UI_INPUT_SCHEMA = "VIA_UI_Input/1"
IMPORT_KEYS = {"locations", "active_template", "run_groups"}
THEME_KEYS = {"primary_color", "bg_color", "mode", "font_size"}
LAYOUT_KEYS = {"sidebar_width", "show_sidebar", "show_header", "density"}
_SNAPSHOT_V0100 = PRIOR.snapshot

for _n in dir(PRIOR):
    if not _n.startswith("__") and _n not in globals():
        globals()[_n] = getattr(PRIOR, _n)


def _tail(folder: Path, glob: str) -> Path | None:
    hits = [p for p in folder.glob(glob) if re.search(r"_v\d+$", p.stem)]
    return max(hits, key=lambda p: int(p.stem.rsplit("_v", 1)[1])) if hits else None


def _rel(p: Path) -> str:
    try:
        return Path(p).resolve().relative_to(VIA.resolve()).as_posix()
    except ValueError:
        return str(p)


def _sha(p: Path) -> str:
    try:
        return hashlib.sha256(Path(p).read_bytes()).hexdigest()
    except OSError:
        return ""


# ---------- VDF 族群快照(同一份) ----------
def vdf_snapshot(home: Path | None, as_of: str | None = None) -> dict:
    t = _tail(VDF, "VDF_MDL012_FetchGroups_v*.py")
    if t and home:
        try:
            sp = importlib.util.spec_from_file_location("vdf_mdl012_for_mdl261", t)
            m = importlib.util.module_from_spec(sp)
            sys.modules[sp.name] = m
            with contextlib.redirect_stdout(io.StringIO()):
                sp.loader.exec_module(m)
            g = m.V0101.gather if hasattr(m, "V0101") else m.gather
            snap = g(home, as_of)
            snap["_from"] = t.name
            return snap
        except Exception as exc:
            err = f"{type(exc).__name__}: {str(exc)[:160]}"
        else:
            err = ""
    else:
        err = "沒有輸出根(資料庫位置)" if not home else "VDF_MDL012 不在"
    p = VIA / "VIA_Reports" / "vdf" / "ui" / "VDF_FetchGroups_SNAPSHOT_latest.json"
    if p.is_file():
        snap = json.loads(p.read_text(encoding="utf-8"))
        snap["_from"] = f"{p.name}(即時取不到:{err})"
        return snap
    return {"_from": f"NODATA({err})", "groups": [], "categories": [], "engines": []}


# ---------- 位置候選(滑鼠下拉 / 拖放比對) ----------
def location_candidates(cfg: dict, home: Path | None, duck: dict) -> dict:
    sys_c, db_c = [], []

    def add(lst, p, why):
        p = Path(p)
        if p.is_dir() and str(p) not in [x["path"] for x in lst]:
            lst.append({"path": str(p), "name": p.name, "why": why})
    loc = cfg.get("locations") or {}
    if loc.get("system_root"):
        add(sys_c, loc["system_root"], "目前設定")
    add(sys_c, VIA, "本倉(本引擎所在)")
    add(sys_c, VIA.parent, "倉上一層")
    for base in (Path.home() / "OneDrive" / "Documents", Path.home() / "Documents"):
        add(sys_c, base / "VeritasIntelligenceAnalytics", "使用者文件夾")
        add(sys_c, base / "movies-dataset" / "VeritasIntelligenceAnalytics", "使用者文件夾 · 倉")
    if loc.get("db_root"):
        add(db_c, loc["db_root"], "目前設定")
    if home:
        add(db_c, home, "VDF 輸出根")
    for s in sys_c:
        add(db_c, Path(s["path"]) / "via_database" / "vdf_fetch", "系統位置下 via_database")
    for d in duck.get("dbs", []):
        add(db_c, Path(d["db"]).parent, f"有 {Path(d['db']).name}")
    add(db_c, VDF / "output_hub", "VDF output_hub(預設)")
    return {"system": sys_c, "db": db_c, "selected": {"system_root": loc.get("system_root") or (sys_c[0]["path"] if sys_c else ""),
                                                      "db_root": loc.get("db_root") or (str(home) if home else (db_c[0]["path"] if db_c else ""))}}


def member_candidates() -> dict:
    tw, intl = [], []
    p = VDF / "VDF_TW_Focus_Universe_v0100.json"
    if p.is_file():
        for m in json.loads(p.read_text(encoding="utf-8")).get("members", []):
            tw.append({"code": str(m.get("ticker")), "name": m.get("name", ""), "group": m.get("group", "")})
    g = REG / "VIA_Global_Universe_v0100.json"
    if g.is_file():
        for c in json.loads(g.read_text(encoding="utf-8")).get("categories", []):
            if c.get("cat") in ("us_jp", "etf", "idx"):
                for s in c.get("symbols") or []:
                    intl.append({"code": s, "name": c.get("zh", ""), "group": c.get("cat")})
    return {"TW": tw, "INTL": intl}


# ---------- 元件註冊 · 版本鎖 ----------
def component_files(vdf: dict) -> list:
    rows = []

    def add(p, kind):
        if p and Path(p).is_file() and _rel(p) not in [r["path"] for r in rows]:
            rows.append({"path": _rel(p), "kind": kind})
    add(Path(__file__), "U/I 引擎")
    add(_tail(REG, "CGC_MDL149_VeritasCentralGovernanceConsole_v*.py"), "VCGC 入口")
    for fam in ("CGC_MDL135_EnvGovernance", "CGC_MDL137_RunGate", "CGC_MDL237_NumberingSystem", "CGC_MDL240_EnvManager"):
        add(_tail(REG, fam + "_v*.py"), "治理")
    for fam in ("VDF_MDL012_FetchGroups", "VDF_MDL008_FetchSystem", "VDF_MDL011_AkshareFetcher", "VDF_MDL009_TWStockList",
                "VDF_MDL010_ActiveETFList", "VDF_SystemManager"):
        add(_tail(VDF, fam + "_v*.py"), "VDF 模組")
    for e in vdf.get("engines", []):
        if e.get("file"):
            add(VDF / e["file"], "VDF 引擎")
    for ps in ("Start-VIA-UIEngine-v*.ps1", "Invoke-VDF-FetchGroupsUI-v*.ps1", "Invoke-VDF-FetchFill-v*.ps1"):
        add(max(VIA.glob(ps), default=None, key=lambda p: p.name), "PS 啟動器")
    for book in ("VDF_FetchGroups_SSOT_v*.json", "VDF_FetchSystem_SSOT_v*.json", "VDF_AkshareSelection_MacroShipping_v*.json"):
        add(_tail(VDF, book), "正本冊")
    add(_tail(VIA / "supportive modules" / "ui_support", "VIA_UI_EngineConfig_v*.json"), "正本冊")
    for book in ("VIA_Workflow_VDF_SSOT_v*.json", "VIA_Workflow_VCGC_SSOT_v*.json", "VIA_Requirements_SSOT_v*.json", "VIA_Central_Synonym_Regex_v*.json"):
        add(_tail(REG, book), "正本冊")
    return rows


def component_matrix(vdf: dict) -> list:
    files = component_files(vdf)
    want = {r["path"] for r in files}
    numbers = {}
    if NUMBER_DIR.is_dir():
        for p in NUMBER_DIR.glob("VIA_NumberBook_*.jsonl"):
            if p.name.startswith(("VIA_NumberBook_FNC", "VIA_NumberBook_PRMT", "VIA_NumberBook_PLCY", "VIA_NumberBook_FM", "VIA_NumberBook_TST", "VIA_NumberBook_LGC")):
                continue
            for ln in p.open(encoding="utf-8"):
                if '"source"' not in ln:
                    continue
                m = re.search(r'"source":"([^"]+)"', ln) or re.search(r'"source": "([^"]+)"', ln)
                if m and m.group(1).replace("\\", "/") in want:
                    try:
                        r = json.loads(ln)
                        numbers[r["source"].replace("\\", "/")] = r.get("code")
                    except ValueError:
                        pass
    reg = {}
    ci = REG / "VIA_Component_Inventory_SSOT_v0100.json"
    if ci.is_file():
        for r in json.loads(ci.read_text(encoding="utf-8")).get("records", []):
            if r.get("category") in ("module", "engine", "system", "tool", "package") and r.get("source", "").replace("\\", "/") in want:
                reg[r["source"].replace("\\", "/")] = r.get("code")
    locks = {}
    tl = REG / "VIA_ToolVersion_Lock_v0100.json"
    if tl.is_file():
        for k, v in json.loads(tl.read_text(encoding="utf-8")).items():
            if isinstance(v, dict) and v.get("path"):
                locks[v["path"].replace("\\", "/").split("VeritasIntelligenceAnalytics/", 1)[-1]] = f"工具鎖冊 {k}"
    receipts = {}
    for p in EVID.glob("*.json") if EVID.is_dir() else []:
        try:
            r = json.loads(p.read_text(encoding="utf-8"))
        except ValueError:
            continue
        if r.get("rc") != 0 or not r.get("target_marker_seen"):
            continue
        for dep, sha in (r.get("dependencies") or {}).items():
            receipts.setdefault(dep.replace("\\", "/"), []).append((sha, r.get("case"), r.get("completed_at")))
    out = []
    for f in files:
        p = VIA / f["path"]
        sha = _sha(p)
        ver = re.search(r"_v(\d+)", p.stem)
        lock = locks.get(f["path"], "")
        if not lock:
            hit = [(c, t) for s, c, t in receipts.get(f["path"], []) if s == sha]
            stale = [c for s, c, t in receipts.get(f["path"], []) if s != sha]
            lock = f"收據鎖 {hit[-1][0]}" if hit else (f"收據過期 {stale[-1]}" if stale else "")
        num, rg = numbers.get(f["path"]), reg.get(f["path"])
        ok = sum(bool(x) for x in (num, rg, lock and not lock.startswith("收據過期")))
        out.append({"component": p.name, "kind": f["kind"], "version": "v" + ver.group(1) if ver else "", "sha12": sha[:12],
                    "number": num or "", "registry": rg or "", "lock": lock or "未鎖", "state": "GREEN" if ok == 3 else ("YELLOW" if ok else "RED"),
                    "path": f["path"]})
    return out


def tool_matrix() -> list:
    rows = [{"tool": "Python", "kind": "直譯器", "version": platform.python_version(), "state": "GREEN", "note": sys.executable}]
    for mod, kind in (("duckdb", "資料庫"), ("polars", "資料框"), ("jinja2", "範本"), ("rich", "終端矩陣"), ("akshare", "擷取")):
        try:
            m = importlib.import_module(mod)
            rows.append({"tool": mod, "kind": kind, "version": getattr(m, "__version__", "?"), "state": "GREEN", "note": ""})
        except Exception:
            rows.append({"tool": mod, "kind": kind, "version": "", "state": "NODATA" if mod in ("jinja2", "akshare") else "RED",
                         "note": "本境沒裝" + ("(選用:沒有就退逐變數代換)" if mod == "jinja2" else "")})
    acc = getattr(VIA_ACCEL, "celeritas", None)
    try:
        c = acc() if callable(acc) else None
        rows.append({"tool": "加速器", "kind": "SuperAccel", "version": Path(getattr(c, "__file__", "") or "").name, "state": "GREEN" if c else "YELLOW", "note": "VIA_SuperAccel_Module"})
    except Exception as exc:
        rows.append({"tool": "加速器", "kind": "SuperAccel", "version": "", "state": "YELLOW", "note": type(exc).__name__})
    rows.append({"tool": "網路工具", "kind": "NetUnified", "version": Path(VIA_NET_TOOL_PATH or "").name, "state": "GREEN" if VIA_NET_TOOL_PATH else "RED", "note": "本頁零網路;擷取經 MDL008 改道"})
    return rows


FUNCTIONS = [
    ("U/I 引擎", "build / serve / config / templates / duck / import", "產頁 · 本機只讀樞紐 · 參數 · 範本 · DuckDB 盤點 · 匯入滑鼠輸入"),
    ("VDF_MDL012", "groups / members / add / remove / start / asof / run / monitor / query / optimize / ui / ui-import", "族群 · 成員 · 大類起始日 · 擷取 · 監控 · 最佳化"),
    ("PS 啟動器", "Start-VIA-UIEngine-v0101 [-Install] [-Pick] [-Template] [-NoImport]", "環境檢查 / 照 LKGC 安裝 → 匯入下載夾的輸入 → 產頁 → 自動開"),
]


def snapshot_v0101(cfg: dict, home: Path | None) -> dict:
    loc = cfg.get("locations") or {}
    if loc.get("db_root"):
        home = Path(loc["db_root"])
        cfg = copy.deepcopy(cfg)
        roots = cfg.setdefault("duckdb", {}).setdefault("roots", [])
        if "{home}" not in roots:
            roots.insert(0, "{home}")
    snap = _SNAPSHOT_V0100(cfg, home)
    vdf = vdf_snapshot(home)
    snap["vdf"] = vdf
    snap["locations"] = location_candidates(cfg, home, snap["duckdb"])
    snap["members_pick"] = member_candidates()
    snap["components"] = component_matrix(vdf)
    snap["tools"] = tool_matrix()
    snap["functions"] = [{"module": a, "verbs": b, "what": c} for a, b, c in FUNCTIONS]
    t = date.today()
    snap["date_options"] = sorted({"1990-01-01", "2000-01-01", "2010-01-01", "2015-01-01", "2018-01-01", "2020-01-01", "2021-01-01",
                                   "2022-07-01", "2023-01-01", "2024-01-01", "2025-01-01",
                                   (t - timedelta(days=365)).isoformat(), (t - timedelta(days=3 * 365)).isoformat(),
                                   (t - timedelta(days=5 * 365)).isoformat()})
    d, asofs = t, []
    while len(asofs) < 10:
        d -= timedelta(days=1)
        if d.weekday() < 5:
            asofs.append(d.isoformat())
    snap["asof_options"] = ["latest"] + asofs
    snap["templates"] = [x["name"] for x in PRIOR.list_templates(cfg)]
    snap["run_groups"] = cfg.get("run_groups") or []
    snap["input_schema"] = UI_INPUT_SCHEMA
    return snap


PRIOR.snapshot = snapshot_v0101


# ---------- 匯入滑鼠輸入(不走伺服器) ----------
def plan_import(data: dict, cfg_work: dict) -> tuple:
    """回 (新工作副本, 說明列, 拒絕列, VDF 部分)。只收白名單鍵。"""
    errs, lines = [], []
    if data.get("schema") != UI_INPUT_SCHEMA:
        return cfg_work, lines, [f"schema 不是 {UI_INPUT_SCHEMA}"], None
    new = copy.deepcopy(cfg_work)
    for k, v in data.items():
        if k in ("schema", "vdf", "exported_at", "from"):
            continue
        if k == "theme" and isinstance(v, dict):
            for tk, tv in v.items():
                if tk in THEME_KEYS and re.fullmatch(r"[#\w.\- ]{1,40}", str(tv)):
                    if (new.get("theme") or {}).get(tk) != tv:
                        new.setdefault("theme", {})[tk] = tv
                        lines.append(f"[主題] {tk} → {tv}")
                else:
                    errs.append(f"主題鍵不收:{tk}")
        elif k == "layout" and isinstance(v, dict):
            for lk, lv in v.items():
                if lk in LAYOUT_KEYS and (isinstance(lv, bool) or re.fullmatch(r"[\w.\-]{1,20}", str(lv))):
                    if (new.get("layout") or {}).get(lk) != lv:
                        new.setdefault("layout", {})[lk] = lv
                        lines.append(f"[版面] {lk} → {lv}")
                else:
                    errs.append(f"版面鍵不收:{lk}")
        elif k == "locations" and isinstance(v, dict):
            for lk in ("system_root", "db_root"):
                if v.get(lk):
                    if not Path(v[lk]).is_dir():
                        errs.append(f"{lk} 夾不在:{v[lk]}")
                    elif (new.get("locations") or {}).get(lk) != v[lk]:
                        new.setdefault("locations", {})[lk] = v[lk]
                        lines.append(f"[位置] {lk} → {v[lk]}")
        elif k == "active_template":
            if v and not PRIOR.find_template(v, new or PRIOR.load_config()):
                errs.append(f"範本不在:{v}")
            elif new.get("active_template") != v:
                new["active_template"] = v
                lines.append(f"[範本] → {v or '內建標準'}")
        elif k == "run_groups" and isinstance(v, list):
            vv = [str(x) for x in v if re.fullmatch(r"[A-Z_]{2,30}", str(x))]
            if new.get("run_groups") != vv:
                new["run_groups"] = vv
                lines.append(f"[勾選族群] {','.join(vv)}")
        else:
            errs.append(f"不收的鍵:{k}")
    vdf = data.get("vdf") if isinstance(data.get("vdf"), dict) else None
    return new, lines, errs, vdf


def cmd_import(path: str, apply: bool) -> int:
    data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    work = json.loads(PRIOR.WORK_CONFIG.read_text(encoding="utf-8")) if PRIOR.WORK_CONFIG.is_file() else {}
    new, lines, errs, vdf = plan_import(data, work)
    for e in errs:
        print(f"  [拒絕] {e}")
    for ln in lines:
        print(f"  {ln}")
    rc = 2 if errs else 0
    if apply and lines:
        PRIOR.WORK_DIR.mkdir(parents=True, exist_ok=True)
        PRIOR.WORK_CONFIG.write_text(json.dumps(new, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"[import] 參數工作副本 {PRIOR.WORK_CONFIG}")
    if vdf:
        t = _tail(VDF, "VDF_MDL012_FetchGroups_v*.py")
        tmp = PRIOR.WORK_DIR / "_vdf_ui_input.json"
        PRIOR.WORK_DIR.mkdir(parents=True, exist_ok=True)
        tmp.write_text(json.dumps(dict(vdf, schema=UI_INPUT_SCHEMA), ensure_ascii=False), encoding="utf-8")
        argv = [sys.executable, str(t), "ui-import", str(tmp)] + (["--apply"] if apply else [])
        r = subprocess.run(argv, capture_output=True, text=True, env=dict(os.environ, VIA_FROM_VCGC="YES", PYTHONIOENCODING="utf-8"), timeout=600)
        print("[import · VDF] " + (r.stdout or r.stderr).strip().replace("\n", "\n  "))
        rc = max(rc, r.returncode)
    if not apply:
        print("[import] 只列計畫(--apply 才寫)")
    return rc


# ---------- 內建標準範本(v0101 版面) ----------
BUILTIN_V0101 = r"""<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
*{box-sizing:border-box}html,body{margin:0;height:100%}
body{background:var(--via-bg);color:var(--via-fg);font:var(--via-fs)/1.35 var(--via-font)}
.app{display:grid;grid-template-columns:var(--via-sidebar) minmax(0,1fr);min-height:100vh}
.app.noside{grid-template-columns:minmax(0,1fr)}.app.noside .side{display:none}
.side{background:var(--via-card);border-right:1px solid rgba(127,127,127,.22);padding:10px;display:flex;flex-direction:column;gap:4px;min-width:0;overflow:auto;max-height:100vh;position:sticky;top:0}
.side h3{margin:10px 0 2px;font-size:10.5px;letter-spacing:1px;color:var(--via-muted);text-transform:uppercase}
.brand{font-weight:600;font-size:14px;color:var(--via-primary)}
.box{border:1px solid rgba(127,127,127,.22);border-radius:7px;padding:6px 8px}
.box b{font-size:12px}
select{width:100%;padding:3px 5px;border:1px solid rgba(127,127,127,.35);border-radius:5px;background:var(--via-card);color:var(--via-fg);font:inherit}
.drop{border:1.5px dashed rgba(127,127,127,.45);border-radius:6px;padding:6px;text-align:center;color:var(--via-muted);font-size:11px;margin-top:4px}
.drop.on{border-color:var(--via-primary);color:var(--via-primary);background:color-mix(in srgb,var(--via-primary) 8%,transparent)}
.chk{display:flex;align-items:center;gap:5px;margin:2px 0;cursor:pointer}.chk input{margin:0}
.chips{display:flex;flex-wrap:wrap;gap:4px;margin:4px 0}.chip{border:1px solid rgba(127,127,127,.35);border-radius:10px;padding:1px 7px;font-size:11px;cursor:pointer;user-select:none}
.chip.on{background:color-mix(in srgb,var(--via-primary) 18%,transparent);border-color:var(--via-primary)}
.btn{background:var(--via-primary);color:#fff;border:0;border-radius:5px;padding:5px 10px;font:inherit;cursor:pointer;margin:3px 3px 0 0}.btn.o{background:none;color:var(--via-primary);border:1px solid var(--via-primary)}
.sw{display:inline-block;width:18px;height:18px;border-radius:4px;margin:2px;cursor:pointer;border:1px solid rgba(127,127,127,.4)}
.side .nav a{display:block;padding:2px 6px;color:var(--via-fg);text-decoration:none;border-radius:4px}.side .nav a:hover{background:color-mix(in srgb,var(--via-primary) 10%,transparent)}.absent{opacity:.45}
.main{display:flex;flex-direction:column;min-width:0}
.top{display:flex;justify-content:space-between;align-items:center;gap:8px;padding:8px 14px;border-bottom:1px solid rgba(127,127,127,.22);background:var(--via-card);flex-wrap:wrap}
.top.hide{display:none}
.tabs{display:flex;gap:4px;flex-wrap:wrap;padding:6px 14px 0}.tabs button{padding:3px 9px;border:1px solid rgba(127,127,127,.3);border-radius:5px;background:none;color:var(--via-fg);font:inherit;cursor:pointer}
.tabs button.on{border-color:var(--via-primary);background:color-mix(in srgb,var(--via-primary) 14%,transparent)}
.pg{display:none;padding:10px 14px}.pg.on{display:block}
.mx{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,420px),1fr));gap:10px}
.mx.d{font-size:11px}.mx.d td,.mx.d th{padding:2px 4px}
.card{background:var(--via-card);border:1px solid rgba(127,127,127,.22);border-radius:8px;padding:8px 10px;min-width:0}
.card h4{margin:0 0 6px;font-size:12px}.card .scroll{max-height:440px;overflow:auto}
.wide{grid-column:1/-1}
table{border-collapse:collapse;width:100%}th,td{padding:3px 5px;border-bottom:1px solid rgba(127,127,127,.18);text-align:left;vertical-align:top;word-break:break-word}
th{color:var(--via-muted);font-weight:500;position:sticky;top:0;background:var(--via-card)}td.n{text-align:right;font-variant-numeric:tabular-nums}
.b{display:inline-block;padding:0 6px;border-radius:8px;font-size:10.5px;white-space:nowrap}
.b-OK,.b-GREEN{background:rgba(63,185,132,.18);color:#2f9e6e}.b-YELLOW,.b-LOCKED,.b-RUNNING{background:rgba(224,179,65,.2);color:#b7861b}
.b-RED,.b-ERR{background:rgba(224,108,96,.2);color:#c2483d}.b-NODATA,.b-NODATE{background:rgba(140,153,166,.2);color:var(--via-muted)}
.mut{color:var(--via-muted)}pre{white-space:pre-wrap;margin:0;font:10.5px/1.35 ui-monospace,Consolas,monospace}
svg.wf .bx{fill:var(--via-card);stroke:var(--via-primary)}svg.wf text{fill:var(--via-fg);font-size:11px}svg.wf line{stroke:var(--via-muted)}
@media (max-width:900px){.app{grid-template-columns:1fr}.side{position:static;max-height:none}}
</style></head>
<body><div class="app" id="app"><aside class="side" id="side"></aside>
<div class="main"><div class="top" id="top"></div><div class="tabs" id="tabs"></div><div id="pages"></div></div></div>
<script>
(function(){
var S=window.VIA||{},C=window.VIA_CONFIG||{},V=S.vdf||{},$=function(s){return document.querySelector(s)},$$=function(s){return Array.prototype.slice.call(document.querySelectorAll(s))};
var esc=function(v){return v===null||v===undefined?'':String(v).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})};
var B=function(s){return '<span class="b b-'+esc(s)+'">'+esc(s)+'</span>'},N=function(v){return v===null||v===undefined||v===''?'':Number(v).toLocaleString()};
var KEY='via.ui.engine.v0101',st={};try{st=JSON.parse(localStorage.getItem(KEY)||'{}')}catch(e){}var save=function(){try{localStorage.setItem(KEY,JSON.stringify(st))}catch(e){}};
function T(rows,cols){if(!rows||!rows.length)return '<div class="mut">(無資料)</div>';var h='<table><tr>'+cols.map(function(c){return '<th>'+esc(c[1])+'</th>'}).join('')+'</tr>';
 rows.forEach(function(r){h+='<tr>'+cols.map(function(c){var v=r[c[0]];return c[2]==='b'?'<td>'+B(v)+'</td>':c[2]==='n'?'<td class="n">'+N(v)+'</td>':'<td>'+esc(Array.isArray(v)?v.join(' · '):v)+'</td>'}).join('')+'</tr>'});return h+'</table>'}
var G={};(V.groups||[]).forEach(function(g){G[g.id]=g});var CATS=V.categories||[],L=C.layout||{},LOC=S.locations||{system:[],db:[],selected:{}};
st.loc=st.loc||{};st.start=st.start||{};st.mem=st.mem||{};st.run=st.run||(S.run_groups&&S.run_groups.length?S.run_groups:Object.keys(G));
CATS.forEach(function(c){if(!st.start[c.id])st.start[c.id]=c.start});
['TW_FIN','INTL_FIN'].forEach(function(k){if(G[k]&&!st.mem[k])st.mem[k]=(G[k].members||[]).slice()});
function opt(list,sel,lab){return list.map(function(x){var v=typeof x==='string'?x:x.path;return '<option value="'+esc(v)+'"'+(v===sel?' selected':'')+'>'+esc(lab?lab(x):v)+'</option>'}).join('')}
// ---- 左:輸入功能區(全滑鼠)----
var h='<div class="brand">'+esc(C.app_title||'VIA')+'</div><div class="mut">'+esc(S.tool||'')+' · '+esc(S.built||'')+'</div>';
h+='<h3>VCGC 位置(只有兩個)</h3><div class="box"><b>系統存放位置</b><select id="l_sys">'+opt(LOC.system,st.loc.system_root||LOC.selected.system_root,function(x){return x.name+' · '+x.why+' — '+x.path})+'</select>'
 +'<div class="drop" id="d_sys">把資料夾拖進來(Windows 檔案總管)</div></div>'
 +'<div class="box"><b>資料庫位置</b><select id="l_db">'+opt(LOC.db,st.loc.db_root||LOC.selected.db_root,function(x){return x.name+' · '+x.why+' — '+x.path})+'</select>'
 +'<div class="drop" id="d_db">把 .duckdb 檔或資料夾拖進來</div></div>';
h+='<h3>VDF 大類(起始日只能按大類)</h3>';
CATS.forEach(function(c){var ds=(S.date_options||[]).slice();if(ds.indexOf(c.default_start)<0)ds.push(c.default_start);ds.sort();
 h+='<div class="box"><b>'+esc(c.zh)+'</b><div class="mut">'+esc(c.note||'')+'</div><label class="mut">起始日</label><select class="c_start" data-c="'+c.id+'">'
  +ds.map(function(d){return '<option value="'+d+'"'+(d===st.start[c.id]?' selected':'')+'>'+d+(d===c.default_start?'(預設)':'')+'</option>'}).join('')+'</select>';
 c.groups.forEach(function(gid){var g=G[gid]||{};h+='<label class="chk"><input type="checkbox" class="c_run" value="'+gid+'"'+(st.run.indexOf(gid)>=0?' checked':'')+'>'+(g.membership==='FIXED_ALL'?'🔒 ':'')+esc(g.zh||gid)+(g.membership==='FIXED_ALL'?' <span class="mut">全部</span>':'')+'</label>';
  if(gid==='TW_FIN'||gid==='INTL_FIN'){var pool=gid==='TW_FIN'?((S.members_pick||{}).TW||[]):((S.members_pick||{}).INTL||[]);
   h+='<div class="chips" id="ch_'+gid+'"></div><select class="m_add" data-g="'+gid+'"><option value="">+ 加入(下拉選)</option>'+pool.map(function(m){return '<option value="'+esc(m.code)+'">'+esc(m.code+' '+(m.name||''))+'</option>'}).join('')+'</select>'}});
 h+='</div>'});
h+='<h3>as-of(全族群同一天)</h3><select id="asof">'+(S.asof_options||['latest']).map(function(d){return '<option'+(d===(st.asof||(V.asof_setting||'latest'))?' selected':'')+'>'+d+'</option>'}).join('')+'</select>';
h+='<h3>範本 · 外觀</h3><select id="tpl"><option value="">內建標準範本</option>'+(S.templates||[]).map(function(t){return '<option'+(t===(st.tpl||C.active_template)?' selected':'')+'>'+esc(t)+'</option>'}).join('')+'</select>'
 +'<div>'+['#3B82F6','#0F766E','#C2410C','#7C3AED','#334155','#B91C1C'].map(function(c){return '<span class="sw" data-c="'+c+'" style="background:'+c+'"></span>'}).join('')+'</div>'
 +'<select id="fs"><option value="11px">字級 小</option><option value="12.5px">字級 中</option><option value="14px">字級 大</option></select>'
 +'<select id="mode"><option value="auto">主題 跟系統</option><option value="light">淺色</option><option value="dark">深色</option></select>';
h+='<h3>套用(不走伺服器)</h3><button class="btn" id="b_exp">匯出輸入</button><button class="btn o" id="b_cmd">複製套用指令</button><button class="btn o" id="b_run">複製擷取指令</button><button class="btn o" id="b_rst">還原預設</button>'
 +'<div class="mut" id="msg">匯出 → 下載夾的 VIA_UI_Input.json;再按一次啟動器即自動匯入、重產、跳出</div>';
h+='<h3>回母系統 · 其他系統</h3><div class="nav">'+((S.nav||{}).parent||[]).concat((S.nav||{}).systems||[]).map(function(x){return x.exists?'<a href="'+esc(x.href)+'">'+esc(x.label)+'</a>':'<a class="absent">'+esc(x.label)+' · ABSENT</a>'}).join('')+'</div>';
h+='<h3>Live log</h3><pre class="card scroll" style="max-height:200px">'+esc(((V.live||{}).lines||[]).slice(-40).join('\n')||'(無日誌)')+'</pre>';
$('#side').innerHTML=h;
function chips(){['TW_FIN','INTL_FIN'].forEach(function(k){var el=document.getElementById('ch_'+k);if(!el)return;var d=(G[k]||{}).default_members||[];
 var all=(st.mem[k]||[]).concat(d.filter(function(x){return (st.mem[k]||[]).indexOf(x)<0}));
 el.innerHTML=all.map(function(x){return '<span class="chip'+((st.mem[k]||[]).indexOf(x)>=0?' on':'')+'" data-g="'+k+'" data-v="'+esc(x)+'">'+esc(x)+(d.indexOf(x)>=0?' ★':'')+'</span>'}).join('')||'<span class="mut">(無)</span>';
 $$('#ch_'+k+' .chip').forEach(function(c){c.onclick=function(){var a=st.mem[k],v=c.dataset.v,i=a.indexOf(v);if(i>=0)a.splice(i,1);else a.push(v);save();chips();mx1()}})})}
chips();
$$('.c_start').forEach(function(s){s.onchange=function(){st.start[s.dataset.c]=s.value;save();mx1()}});
$$('.c_run').forEach(function(s){s.onchange=function(){st.run=$$('.c_run').filter(function(x){return x.checked}).map(function(x){return x.value});save();mx1()}});
$$('.m_add').forEach(function(s){s.onchange=function(){if(!s.value)return;var a=st.mem[s.dataset.g];if(a.indexOf(s.value)<0)a.push(s.value);s.value='';save();chips();mx1()}});
$('#l_sys').onchange=function(){st.loc.system_root=this.value;save();mx1()};$('#l_db').onchange=function(){st.loc.db_root=this.value;save();mx1()};
$('#asof').onchange=function(){st.asof=this.value;save();mx1()};$('#tpl').onchange=function(){st.tpl=this.value;save()};
var R=document.documentElement;function look(){if(st.pc)R.style.setProperty('--via-primary',st.pc);if(st.fs)R.style.setProperty('--via-fs',st.fs);if(st.mode&&st.mode!=='auto')R.setAttribute('data-theme',st.mode);else R.removeAttribute('data-theme')}
$$('.sw').forEach(function(s){s.onclick=function(){st.pc=s.dataset.c;save();look()}});$('#fs').value=st.fs||((C.theme||{}).font_size)||'12.5px';$('#fs').onchange=function(){st.fs=this.value;save();look()};
$('#mode').value=st.mode||((C.theme||{}).mode)||'auto';$('#mode').onchange=function(){st.mode=this.value;save();look()};look();
function dropz(id,list,key){var d=$(id);['dragenter','dragover'].forEach(function(e){d.addEventListener(e,function(ev){ev.preventDefault();d.classList.add('on')})});
 d.addEventListener('dragleave',function(){d.classList.remove('on')});
 d.addEventListener('drop',function(ev){ev.preventDefault();d.classList.remove('on');var f=ev.dataTransfer.files&&ev.dataTransfer.files[0];if(!f){return}
  var nm=f.name,hit=null;(list||[]).forEach(function(x){if(!hit&&(x.name===nm||x.path.split(/[\\/]/).pop()===nm))hit=x});
  if(!hit&&key==='db_root'){((S.duckdb||{}).dbs||[]).forEach(function(db){if(!hit&&db.name===nm){var p=db.db.replace(/[\\/][^\\/]+$/,'');hit={path:p,name:p.split(/[\\/]/).pop()}}})}
  if(hit){st.loc[key]=hit.path;save();(key==='system_root'?$('#l_sys'):$('#l_db')).value=hit.path;d.textContent='對到:'+hit.path;mx1()}
  else d.textContent='「'+nm+'」沒對到候選(瀏覽器不給完整路徑)→ 用下拉,或啟動器 -Pick 開 Windows 選夾窗'})}
dropz('#d_sys',LOC.system,'system_root');dropz('#d_db',LOC.db,'db_root');
function input(){var cats={};CATS.forEach(function(c){cats[c.id]={start:st.start[c.id]}});var mem={};Object.keys(st.mem).forEach(function(k){mem[k]=st.mem[k]});
 return {schema:S.input_schema||'VIA_UI_Input/1',exported_at:new Date().toISOString(),from:S.tool,locations:{system_root:st.loc.system_root||LOC.selected.system_root,db_root:st.loc.db_root||LOC.selected.db_root},
  run_groups:st.run,active_template:st.tpl||null,theme:{primary_color:st.pc||(C.theme||{}).primary_color,font_size:st.fs||(C.theme||{}).font_size,mode:st.mode||(C.theme||{}).mode||'auto'},
  vdf:{categories:cats,members:mem,as_of:st.asof||V.asof_setting||'latest'}}}
$('#b_exp').onclick=function(){var a=document.createElement('a');a.href=URL.createObjectURL(new Blob([JSON.stringify(input(),null,1)],{type:'application/json'}));a.download='VIA_UI_Input.json';a.click();$('#msg').textContent='已下載 VIA_UI_Input.json → 再按一次啟動器(自動匯入 · 重產 · 跳出)'};
$('#b_cmd').onclick=function(){var t='.\\Start-VIA-UIEngine-v0101.ps1';if(navigator.clipboard)navigator.clipboard.writeText(t);$('#msg').textContent='已複製:'+t+'(PS 視窗按滑鼠右鍵貼上)'};
$('#b_run').onclick=function(){var t='.\\Start-VIA-UIEngine-v0101.ps1 -Run';if(navigator.clipboard)navigator.clipboard.writeText(t);$('#msg').textContent='已複製:'+t+'(先匯出輸入;live 先在 PS 視窗開雙閘;右鍵貼上)'};
$('#b_rst').onclick=function(){st={};save();location.reload()};
// ---- 右:多頁 ----
var pages=[['p1','① 輸入 · 引擎 · 運作']];CATS.forEach(function(c){pages.push(['c_'+c.id,c.zh])});pages.push(['pdb','🦆 DuckDB']);pages.push(['penv','🧰 環境']);pages.push(['pz','細節矩陣(全部)']);
$('#tabs').innerHTML=pages.map(function(p){return '<button data-pg="'+p[0]+'">'+esc(p[1])+'</button>'}).join('');
$('#pages').innerHTML=pages.map(function(p){return '<section class="pg" id="'+p[0]+'"></section>'}).join('');
var D=S.duckdb||{dbs:[]},E=S.env||{};
$('#top').innerHTML='<b>'+esc(C.app_title||'VIA')+'</b><span>as-of '+esc(V.as_of||'')+' · DuckDB '+B(D.locked?'LOCKED':(D.n_dbs?'OK':'NODATA'))+' · LKGC '+B(E.lkgc||'NODATA')+' · VDF '+esc(V._from||'')+'</span>';
if(L.show_header===false)$('#top').classList.add('hide');if(L.show_sidebar===false)$('#app').classList.add('noside');
function mx1(){var I=input(),rows=[],seen={};
 function add(item,cat,val,where,src){var k=item+'|'+val;if(seen[k]){seen[k].where.push(where);seen[k].dup++;return}seen[k]={item:item,cat:cat,val:val,where:[where],dup:1,src:src};rows.push(seen[k])}
 add('系統存放位置','VCGC',I.locations.system_root,'VCGC','下拉 / 拖放');add('資料庫位置','VCGC',I.locations.db_root,'VCGC','下拉 / 拖放');add('as-of','全族群',I.vdf.as_of,'全部','下拉');
 CATS.forEach(function(c){add('起始日','大類',I.vdf.categories[c.id].start,c.zh,'下拉(只按大類)')});
 I.run_groups.forEach(function(g){add('勾選族群','族群',g,((G[g]||{}).category)||'','打勾')});
 Object.keys(I.vdf.members).forEach(function(k){I.vdf.members[k].forEach(function(m){add('成員',k,m,(G[k]||{}).zh||k,'方塊 / 下拉')})});
 (V.groups||[]).forEach(function(g){if(g.membership!=='FIXED_ALL'&&g.id!=='TW_FIN'&&g.id!=='INTL_FIN')add('成員數',g.id,(g.n===null||g.n===undefined)?'全部':g.n+' 個',g.zh,'冊 / 帳本(明細在細節頁)')});
 rows.forEach(function(r){r.where=r.where.join(' · ')});
 $('#m_in').innerHTML='<div class="mut">'+rows.length+' 項(去重後;同值多處 = 重複次數 > 1)</div>'+T(rows,[['item','輸入'],['cat','類'],['val','值'],['where','出現在'],['dup','次','n'],['src','來源']])}
var eng=(V.engines||[]).map(function(e){return {c:e.id,k:'擷取引擎',v:(e.file||'').split('/').pop(),a:e.run_args,s:e.state}});
var tools=(S.tools||[]).map(function(t){return {c:t.tool,k:t.kind,v:t.version,a:t.note,s:t.state}});
var fns=(S.functions||[]).map(function(f){return {c:f.module,k:'功能',v:f.verbs,a:f.what,s:'GREEN'}});
var runs=[];(V.groups||[]).forEach(function(g){var s=g.summary||{};runs.push({w:'族群',id:g.zh,r:s.rows_asof,m:s.max_date,s:s.worst||'NODATA',n:JSON.stringify(s.states||{})})});
(V.fg_runs||[]).forEach(function(r){runs.push({w:'族群執行',id:r.run_id,r:'',m:r.as_of,s:'GREEN',n:r.groups+' · '+r.rc})});
(V.vake_runs||[]).forEach(function(r){runs.push({w:'AkShare 執行',id:r.run_id,r:r.rows_new,m:r.finished,s:(r.fail?'YELLOW':'GREEN'),n:'ok '+r.ok+' / fail '+r.fail})});
$('#p1').innerHTML='<div class="mx"><div class="card"><h4>輸入摘要去重矩陣</h4><div class="scroll" id="m_in"></div></div>'
 +'<div class="card"><h4>引擎 · 工具 · 功能矩陣</h4><div class="scroll">'+T(eng.concat(tools,fns),[['c','元件'],['k','類'],['v','版本 / 檔'],['a','參數 / 說明'],['s','燈','b']])+'</div></div>'
 +'<div class="card wide"><h4>運作結果矩陣</h4><div class="scroll">'+T(runs,[['w','類'],['id','項'],['r','筆數','n'],['m','最晚 / 時間'],['s','燈','b'],['n','註']])+'</div></div></div>';
mx1();
CATS.forEach(function(c){var html='<div class="mx">';c.groups.forEach(function(gid){var g=G[gid];if(!g)return;var s=g.summary||{};
 html+='<div class="card"><h4>'+esc(g.zh)+' '+B(s.worst||'NODATA')+' <span class="mut">起始 '+esc(c.start)+' · as-of '+esc(V.as_of)+' · '+esc(g.membership)+(g.n===null?' · 全部':' · '+g.n+' 個')+'</span></h4><div class="scroll">'
  +T(g.rows,[['table_name','表 / 函式'],['rows_asof','≤as-of','n'],['min_date','最早'],['max_date','最晚'],['lag_days','落後','n'],['state','燈','b'],['note','註']])+'</div></div>'});
 $('#c_'+c.id).innerHTML=html+'</div>'});
$('#pdb').innerHTML='<div class="mx">'+(D.dbs||[]).map(function(d){return '<div class="card"><h4>'+esc(d.name)+' '+B(d.state)+' <span class="mut">'+esc(d.mb)+' MB · '+d.tables.length+' 表</span></h4><div class="scroll">'
 +T(d.tables.map(function(t){return {t:t.table,k:t.kind,r:t.rows!==null?t.rows:t.est_rows,c:t.columns.length,d:t.date_col?(t.min_date+' → '+t.max_date):''}}),[['t','表'],['k','類'],['r','列','n'],['c','欄','n'],['d','日期']])+'</div></div>'}).join('')+'</div>';
$('#penv').innerHTML='<div class="mx"><div class="card"><h4>照測過的版本(LKGC)</h4>'+T([E],[['lkgc','判定','b'],['eligible','可用'],['ts','時間'],['path','檔']])+'</div><div class="card"><h4>工具</h4>'+T(S.tools,[['tool','工具'],['version','版本'],['state','燈','b'],['note','註']])+'</div></div>';
var wf=(V.workflow||{}),steps=(wf.steps||[]).map(function(s){return {c:s.code,n:s.name,e:s.engine,v:s.verb,ev:s.evidence}});
var order=String((wf.plan||{}).order||'').split('→').map(function(x){return x.trim()}).filter(Boolean);
var svg='<svg class="wf" viewBox="0 0 '+Math.max(600,order.length*150)+' 56" width="100%">'+order.map(function(o,i){var x=6+i*150;return '<rect class="bx" x="'+x+'" y="8" width="132" height="34" rx="6"/><text x="'+(x+66)+'" y="30" text-anchor="middle">'+esc(o.slice(0,20))+'</text>'+(i?'<line x1="'+(x-18)+'" y1="25" x2="'+(x-2)+'" y2="25"/>':'')}).join('')+'</svg>';
$('#pz').innerHTML='<div class="card wide"><h4>流程 workflow chart · '+esc(wf.code||'')+' '+esc(wf.name||'')+'</h4>'+svg+'</div><div class="mx d" style="margin-top:10px">'
 +'<div class="card"><h4>工作流步驟</h4><div class="scroll">'+T(steps,[['c','代碼'],['n','步'],['e','正主'],['v','動詞'],['ev','證據']])+'</div></div>'
 +'<div class="card"><h4>元件 · 註冊 · 版本鎖</h4><div class="scroll">'+T(S.components,[['component','元件'],['kind','類'],['version','版'],['sha12','sha256'],['number','編號'],['registry','註冊碼'],['lock','鎖'],['state','燈','b']])+'</div></div>'
 +'<div class="card"><h4>輸入輸出參數邏輯</h4><div class="scroll">'+T(V.io,[['group','族群'],['membership','名單'],['input','輸入'],['engines','引擎'],['asof_args','日期參數'],['output','輸出'],['cadence','頻率']])+'</div></div>'
 +'<div class="card"><h4>regex</h4><div class="scroll">'+T(V.regex,[['scope','範圍'],['name','名'],['pattern','式'],['use','用途']])+'</div></div>'
 +'<div class="card"><h4>同義字</h4><div class="scroll">'+T(V.synonyms,[['key','鍵'],['canonical','正典'],['aliases','同義字']])+'</div></div>'
 +'<div class="card"><h4>編號</h4><div class="scroll">'+T(V.numbering,[['code','編號'],['kind','類'],['name','名'],['version','版']])+'</div></div>'
 +'<div class="card"><h4>SSOT 冊</h4><div class="scroll">'+T(V.ssot,[['book','冊'],['version','版'],['sha12','sha'],['mtime','時間'],['state','狀態']])+'</div></div>'
 +'<div class="card"><h4>大類起始日規則</h4><div>'+esc(V.start_rule||'')+'</div>'+T(CATS,[['id','大類'],['zh','名稱'],['start','目前起始日'],['default_start','預設'],['groups','族群']])+'</div>'
 +'<div class="card wide"><h4>有效參數(疊層 '+esc((S.config_layers||[]).join(' ← '))+')</h4><pre class="scroll">'+esc(JSON.stringify(C,null,1))+'</pre></div></div>';
function show(id){$$('.pg').forEach(function(p){p.classList.toggle('on',p.id===id)});$$('.tabs [data-pg]').forEach(function(b){b.classList.toggle('on',b.dataset.pg===id)});st.page=id;save()}
$$('.tabs [data-pg]').forEach(function(b){b.onclick=function(){show(b.dataset.pg)}});show(st.page&&document.getElementById(st.page)?st.page:'p1');
if((V.live||{}).running)setTimeout(function(){location.reload()},15000);
})();
</script></body></html>
"""
PRIOR.BUILTIN = BUILTIN_V0101


# ---------- 自測 ----------
def selftest() -> int:
    import shutil
    import tempfile
    res = []

    def chk(name, cond, note=""):
        res.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f" · {str(note)[:300]}" if note and not cond else ""))

    keep_b, keep_s = PRIOR.BUILTIN, PRIOR.snapshot
    PRIOR.BUILTIN, PRIOR.snapshot = PRIOR.__dict__.get("_BUILTIN_V0100", PRIOR.BUILTIN), _SNAPSHOT_V0100
    buf = io.StringIO()
    try:
        src = PRIOR_PATH.read_text(encoding="utf-8")
        m = re.search(r'BUILTIN = r"""(.*?)"""\n', src, re.S)
        if m:
            PRIOR.BUILTIN = m.group(1)
        with contextlib.redirect_stdout(buf):
            prior_rc = PRIOR.selftest()
    finally:
        PRIOR.BUILTIN, PRIOR.snapshot = keep_b, keep_s
        PRIOR.TAG = TAG
    chk("① v0100 自測照過(9 檢;用 v0100 自己的內建範本)", prior_rc == 0, buf.getvalue()[-300:])
    tmp = Path(tempfile.mkdtemp(prefix="mdl261v1_"))
    keep = (PRIOR.WORK_DIR, PRIOR.WORK_CONFIG)
    try:
        PRIOR.WORK_DIR = tmp / "work"
        PRIOR.WORK_CONFIG = PRIOR.WORK_DIR / "ui_config.json"
        home = tmp / "home"
        (home / "output_hub" / "mega").mkdir(parents=True)
        duck = PRIOR._duck()
        c = duck.connect(str(home / "output_hub" / "mega" / "demo.duckdb"))
        c.execute("CREATE TABLE prices(date DATE, ticker VARCHAR, close DOUBLE)")
        c.execute("INSERT INTO prices VALUES ('2026-10-02','2330',1)")
        c.close()
        cfg = PRIOR.load_config(sets=[f"locations.db_root={home}"])
        snap, out, rep = PRIOR.build(cfg, home, tmp / "ui" / "page.html")
        page = out.read_text(encoding="utf-8")
        script = page[page.index("<script>(function"):] if "<script>(function" in page else page
        chk("② 全滑鼠:內建頁沒有任何文字輸入框 / 文字區(只有下拉 · 打勾 · 拖放 · 按鈕)",
            not re.search(r"<input[^>]*type=\"?(text|search|number|date)", page) and "<textarea" not in page
            and "type=\"checkbox\"" in page and "<select" in page and "drop" in page)
        chk("③ 左面板:VCGC 只兩個位置(系統存放 · 資料庫)+ 拖放區 · VDF 大類起始日下拉(只按大類)· 財報成員方塊 + 下拉加入",
            page.count('id="l_sys"') == 1 and page.count('id="l_db"') == 1 and "d_sys" in page and "d_db" in page
            and "c_start" in page and "ch_'+gid" in page and "m_add" in page)
        cats = {x["id"]: x for x in snap["vdf"].get("categories", [])}
        chk("④ VDF 快照直接取 MDL012 尾版(三大類 · 財報預設 2330 3324 / NVDA)",
            {"TW_MARKET", "FIN", "MACRO"} <= set(cats) and any(g["id"] == "TW_FIN" and g["members"][:2] == ["2330", "3324"] for g in snap["vdf"]["groups"])
            and any(g["id"] == "INTL_FIN" and "NVDA" in g["members"] for g in snap["vdf"]["groups"]), snap["vdf"].get("_from"))
        chk("⑤ 右面板:第一頁三矩陣(輸入摘要去重 · 引擎工具功能 · 運作結果)· 每大類一頁結果 · DuckDB · 環境 · 末頁細節矩陣(流程圖在最上)",
            all(k in page for k in ("輸入摘要去重矩陣", "引擎 · 工具 · 功能矩陣", "運作結果矩陣", "細節矩陣(全部)", "workflow chart", "元件 · 註冊 · 版本鎖")))
        comp = {r["component"]: r for r in snap["components"]}
        me = comp.get(Path(__file__).name, {})
        chk("⑥ 元件矩陣:本檔 · VCGC 入口 · MDL012 · MDL008 · 引擎 · PS 啟動器 · 正本冊都列;每列 版號 · sha · 編號 · 註冊 · 鎖 · 燈",
            me.get("version") == "v0101" and len(me.get("sha12", "")) == 12 and any(k.startswith("VDF_MDL012_FetchGroups") for k in comp)
            and any(k.startswith("CGC_MDL149_") for k in comp) and any(r["kind"] == "PS 啟動器" for r in snap["components"])
            and all(r["state"] in ("GREEN", "YELLOW", "RED") for r in snap["components"]), list(comp)[:6])
        locs = snap["locations"]
        chk("⑦ 位置候選:資料庫位置含設定的輸出根與有 .duckdb 的夾 · 系統位置含本倉", str(home) in [x["path"] for x in locs["db"]]
            and str(VIA) in [x["path"] for x in locs["system"]] and locs["selected"]["db_root"] == str(home), locs["selected"])
        data = {"schema": UI_INPUT_SCHEMA, "locations": {"system_root": str(VIA), "db_root": str(home)}, "active_template": None,
                "run_groups": ["TW_PRICE_VOL", "TW_FIN"], "theme": {"primary_color": "#0F766E", "evil": "x"}, "layout": {"sidebar_width": "300px"},
                "hack": 1}
        new, lines, errs, vdf = plan_import(data, {})
        chk("⑧ 匯入:只收白名單(位置 · 範本 · 勾選族群 · 主題 · 版面);其他鍵照實拒絕;不存在的夾拒絕",
            new["locations"]["db_root"] == str(home) and new["theme"]["primary_color"] == "#0F766E" and "evil" not in new["theme"]
            and new["run_groups"] == ["TW_PRICE_VOL", "TW_FIN"] and any("hack" in e for e in errs) and any("evil" in e for e in errs)
            and plan_import({"schema": UI_INPUT_SCHEMA, "locations": {"db_root": str(tmp / "nope")}}, {})[2], (lines, errs))
        chk("⑨ 零 CDN / 零 fetch / 不需伺服器(file://)", not re.search(r'(src|href)="https?://', page) and "fetch(" not in script
            and "XMLHttpRequest" not in page)
    finally:
        PRIOR.WORK_DIR, PRIOR.WORK_CONFIG = keep
        shutil.rmtree(tmp, ignore_errors=True)
    ok = sum(res)
    print(f"[計] {TAG} 本版 {ok}/{len(res)} · v0100 {'PASS' if prior_rc == 0 else 'FAIL'} · 合計 {'PASS' if ok == len(res) else 'FAIL'}")
    return 0 if ok == len(res) else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv == ["--selftest"]:
        return selftest()
    if argv and argv[0] == "import":
        if len(argv) < 2:
            print("用法:import <VIA_UI_Input.json> [--apply]")
            return 2
        return cmd_import(argv[1], "--apply" in argv)
    return PRIOR.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
