#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VDF_MDL013_ActivateVDF v0114 — 薄尾:一鍵全程 —— 同步到 main → 兩張清單 → 擷取改走族群分道並行 → 引擎 / 資料庫 / 核對 → 總覽頁多「同步 · 分道擷取 · 操作入口」

操作員令(2026-10-21):「INTEGRATE ALL INTO ONE CODE TO HANDLE THE REMAINING WORKS TO ENSURE DATA CAN BE FETCH FAST AND CORRECTLY
FOR THE SOURCE AND I CAN OPERATE IN HTML U/I.」
疊在 main 的 v0113(資料庫清點獨立核對)之上;v0100 … v0113 一字不動。本版(只在本版的一輪裡生效;前版自測照舊):
  ⓪ --sync:起跑前先經 VDF 自己的工作站同步 VDF_MDL014_WorkstationSync 尾版 `--apply`(備份分岔 · VDF 工作樹移到最新 main ·
     VDF 資料夾接過去 · 交接案真的重跑 · 只交 VDF 收據);紅(rc ≠ 0,含「不是 VDF 的工作樹」rc 2)→ 停在擷取之前,不在錯的樹上抓資料。
     --sync-case 可多次(預設 qg_onebridge · vdf_ws_manager_design · vdf_ws_eng093_lists);--sync-only 只同步不啟動。
  ① 擷取流程(流程一)改走 VDF_MDL012_FetchGroups 尾版 `run --groups ALL --jobs auto --no-lists-first`:依 DuckDB 庫分道、
     3~5 流程同時跑(CPU · DRAM · TEMP 守門);清單 009 · 010 已由 ② 先跑過,所以 --no-lists-first。
     --groups / --jobs 可改;--no-lanes 回 v0100 的逐列 `fetch run`。rc 4 = GATED(雙閘沒開,零子行程)· rc 5 = 清單紅沒起道 · rc 1 = 有道紅。
  ② 總覽頁(VIA_Reports/vdf/activate/ACTIVATE_VDF_latest.html)多三塊:「⓪ 同步」卡(分岔 / 備份 / 工作樹 / 資料接點 / 交接 / 收據分支 → 開 PR 連結)·
     「分道擷取」(道 · 引擎 · 結束一行)· 「操作入口」(VDF 操作頁 · 資料庫檢查 · 獨立核對 · 跨來源對照 · 問參數頁與重跑指令)。本輪 JSON / 頁頭標 v0114。
  ③ 資料家(操作員 2026-10-21 令「VDF資料庫位於 C:\Users\tonyk\OneDrive\Documents\VeritasIntelligenceAnalytics\via_01_vdf」):
     VDF 自己的冊 VDF_DataHome_SSOT 尾版(本夾)登記操作員的家;--db-home / VIA_VDF_DB_HOME 沒給時,冊上在這台機器存在的家就是
     本輪資料庫家(家本身或底下唯一放 .duckdb 的夾);擷取家沒給時照冊上 fetch_home,沒寫就由家底下唯一的 output_hub 上一層推。
     冊上的家在這台機器不在 → 不猜、照前版(倉內 output_hub)並標黃。run / plan 都印 [資料家] 一行;總覽頁操作入口卡也列。
  用法(工作站,站在 VDF 工作樹裡;PowerShell 或 cmd 都一樣):
    python "<VDF 工作樹>\VeritasIntelligenceAnalytics\functional modules\VDF\ActivateVDF.py" run --sync --refill-apply
  PS 一鍵 Invoke-VDF-Activate v0105 的參數表是固定的(沒有 --sync / --lanes 直通),要經 PS 一鍵走本版要另一次 L70 許可改 .ps1;本線不改 .ps1。
VDF 自己的模組:不匯入他系統程式;同意閘不讀不寫(只原樣傳給子行程);不碰 TA-Lib;不裝套件、不寫環境;不推 main、不 force(同步那一步照 MDL014 的規矩)。
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
    """統包唯一網路工具惰性載入;本檔的連網全經 MDL008 子行程改道。"""
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

import copy
import html
import importlib.util
import json
import os
import re
import sys
import warnings
from pathlib import Path

HERE = Path(__file__).resolve().parent
import subprocess
import time

_STEM = "VDF_MDL013_ActivateVDF"
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"
SCHEMA_V0114 = "VDF_ActivateVDF_v0114"


def _vnum_v0114(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0114(p) < _vnum_v0114(__file__)), key=_vnum_v0114)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
with warnings.catch_warnings():                    # 同 v0102:前版鏈只擋載入那一刻的編譯警告
    warnings.simplefilter("ignore", SyntaxWarning)
    warnings.simplefilter("ignore", DeprecationWarning)
    _spec.loader.exec_module(PRIOR)
V0100 = PRIOR.V0100
DBM, FLM = PRIOR.DBM, PRIOR.FLM                    # v0106(清點 / 總覽卡)· v0101(流程:run_step · run_flows · flow_fetch 包裝)


def __getattr__(name):
    return getattr(PRIOR, name)


SYNC_GLOB_V0114 = "VDF_MDL014_WorkstationSync_v*.py"
SYNC_CASES_V0114 = ("qg_onebridge", "vdf_ws_manager_design", "vdf_ws_eng093_lists")
FG_FAMILY_V0114 = "VDF_MDL012_FetchGroups"
ASK_GLOB_V0114 = "VDF_ENG093_LaunchConsole_v*.py"
OPERATE_LINKS_V0114 = (("VDF 操作頁(U/I)", "VDF_UI_latest.html"), ("資料庫檢查(db check)", "DB_CHECK_latest.html"),
                       ("獨立核對(db verify)", "VERIFY_latest.html"), ("跨來源對照(xsrc)", "xsrc/VDF_XSRC_latest.html"),
                       ("表頭彙整", "HEADER_MATRIX_latest.html"), ("全景", "PANORAMA_latest.html"))
DATA_HOME_GLOB_V0114 = "VDF_DataHome_SSOT_v*.json"
_RUN14 = {"on": False, "sync": None, "homes": None}
_FLOW_FETCH_ORIG = FLM._FLOW_FETCH_V0100           # v0101 流程包裝裡真正跑擷取的那支(= v0100 flow_fetch:逐列 fetch run)
_RENDER_PREV = V0100.render_html                   # v0106 的總覽頁(含資料庫清點)


# ---------------------------------------------------------------- 參數(本版的旗標先摘掉,其餘照 v0100 parse)
def parse(argv: list):
    import argparse
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--sync", action="store_true")
    ap.add_argument("--sync-case", action="append", default=None)
    ap.add_argument("--sync-only", action="store_true")
    ap.add_argument("--no-lanes", action="store_true")
    ap.add_argument("--groups", default="ALL")
    ap.add_argument("--jobs", default="auto")
    mine, rest = ap.parse_known_args(argv)
    opt = V0100.parse(rest)
    opt.sync, opt.sync_only = bool(mine.sync or mine.sync_only), bool(mine.sync_only)
    opt.sync_cases = list(mine.sync_case or SYNC_CASES_V0114)
    opt.lanes, opt.groups, opt.jobs = not mine.no_lanes, str(mine.groups or "ALL"), str(mine.jobs or "auto")
    opt.rest_argv = rest
    return opt


# ---------------------------------------------------------------- ⓪ 同步(VDF_MDL014 尾版 --apply;本檔只派、只讀它印的)
def sync_path(folder: Path = HERE) -> Path | None:
    hits = [p for p in folder.glob(SYNC_GLOB_V0114) if _vnum_v0114(p) >= 0]
    return max(hits, key=_vnum_v0114) if hits else None


def run_sync(cases: list, py: str | None = None, log_dir: Path | None = None, folder: Path = HERE, timeout: float = 7200) -> dict:
    """派 VDF_MDL014_WorkstationSync 尾版 --apply --case …;回 {lamp, rc, secs, path, lines, branch, pr_url, summary, note, log}。
    印出的幾類行([倉] [備份] [VDF MAIN] [資料] [交接] [收據] NEXT [計])照抄進 lines;收據分支與開 PR 連結另外抓出來。"""
    p = sync_path(folder)
    rec = {"step": "sync", "path": p.name if p else None, "cases": list(cases), "lines": [], "branch": None, "pr_url": None, "log": None}
    if p is None:
        return dict(rec, rc=None, lamp="RED", secs=0, summary="", note=f"{SYNC_GLOB_V0114} 不在 {folder}")
    args = [py or sys.executable, str(p), "--apply"] + [x for c in cases for x in ("--case", c)]
    env = dict(os.environ, VIA_NO_OPEN="1", PYTHONIOENCODING="utf-8")
    t0 = time.time()
    try:
        r = subprocess.run(args, cwd=str(folder), env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
        rc, out = r.returncode, (r.stdout or "") + (("\n" + r.stderr) if r.stderr else "")
        note = ""
    except subprocess.TimeoutExpired as exc:
        rc, out, note = None, str(exc.stdout or ""), f"逾時 {timeout}s"
    secs = round(time.time() - t0, 1)
    if log_dir is not None:
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            lp = log_dir / "sync.log"
            lp.write_text(out, encoding="utf-8")
            rec["log"] = str(lp)
        except OSError:
            pass
    keep = ("[倉]", "[備份]", "[VDF MAIN]", "[資料]", "[交接]", "[收據]", "NEXT:", "[計]")
    lines = [ln.strip() for ln in out.splitlines() if any(k in ln for k in keep)]
    m = re.search(r"\[收據\].*?→ 分支 (\S+)", out)
    branch = m.group(1) if m else None
    m2 = re.search(r"NEXT: 開 PR ([^\s(（]+)", out)
    summ = next((ln for ln in reversed(lines) if ln.startswith("[計]")), lines[-1] if lines else "")
    if rc == 2:
        note = note or next((ln for ln in lines if "[VDF MAIN]" in ln), "rc 2:不是 VDF 的工作樹(MDL014 不接手別人的工作樹)")
    elif rc not in (0, None) and not note:
        note = "同步有紅(交接案紅或資料接不上),看 sync.log"
    lamp = "GREEN" if rc == 0 else "RED"
    return dict(rec, rc=rc, lamp=lamp, secs=secs, lines=lines[:24], branch=branch, pr_url=(m2.group(1) if m2 else None), summary=summ[:240], note=note)


# ---------------------------------------------------------------- ① 擷取流程改走族群分道並行(FetchGroups 尾版 run)
# ---------------------------------------------------------------- ③ 資料家(VDF 自己的冊;只讀;不猜不在的路徑)
def data_home_book(folder: Path = HERE) -> tuple:
    """→ (冊尾版路徑或 None, homes 列表);冊壞 → [{"error": …}]。"""
    p = V0100.tail(folder, DATA_HOME_GLOB_V0114)
    if not p:
        return None, []
    try:
        return p, list(json.loads(p.read_text(encoding="utf-8")).get("homes") or [])
    except Exception as e:                        # noqa: BLE001 — 冊壞照實回報,不讓一鍵倒
        return p, [{"error": f"{type(e).__name__}: {e}"}]


def _db_dir(root: Path) -> tuple:
    """冊上的家 → 真正放庫檔的夾:家本身直接有 .duckdb 就是它;底下所有 .duckdb 同一個夾 → 那個夾;散在多夾 → 家本身。→ (夾, 庫檔數)"""
    files = [f for f in root.rglob("*.duckdb") if not f.name.endswith(".wal")]
    if any(f.parent == root for f in files):
        return root, len(files)
    parents = {f.parent for f in files}
    return (next(iter(parents)) if len(parents) == 1 else root), len(files)


def resolve_homes(opt, folder: Path = HERE, env: dict | None = None) -> dict:
    """資料庫家:--db-home > VIA_VDF_DB_HOME > 冊上在這台機器存在的家;擷取家:--fetch-home > VIA_VDF_FETCH_HOME > 冊上 fetch_home
    > 家底下唯一的 output_hub 上一層;都沒有 → 照前版。冊上定到的寫回 opt.db_home / opt.fetch_home(前版流程照 opt 帶 --home)。"""
    env = os.environ if env is None else env
    out = {"db_home": None, "db_from": None, "fetch_home": None, "fetch_from": None, "book": None, "dbs": None, "lamp": "GREEN", "note": ""}
    book, homes = data_home_book(folder)
    out["book"] = book.name if book else None
    if getattr(opt, "db_home", None):
        out["db_home"], out["db_from"] = str(opt.db_home), "--db-home"
    elif env.get("VIA_VDF_DB_HOME"):
        out["db_home"], out["db_from"] = env["VIA_VDF_DB_HOME"], "VIA_VDF_DB_HOME"
    if getattr(opt, "fetch_home", None):
        out["fetch_home"], out["fetch_from"] = str(opt.fetch_home), "--fetch-home"
    elif env.get("VIA_VDF_FETCH_HOME"):
        out["fetch_home"], out["fetch_from"] = env["VIA_VDF_FETCH_HOME"], "VIA_VDF_FETCH_HOME"
    bad = next((h for h in homes if h.get("error")), None)
    if bad:
        out["lamp"], out["note"] = "YELLOW", f"資料家冊讀不到:{bad['error']} → 照前版"
        return out
    hit = next((h for h in homes if h.get("db_home") and Path(h["db_home"]).is_dir()), None)
    if hit:
        root = Path(hit["db_home"])
        if not out["db_home"]:
            d, n = _db_dir(root)
            out["db_home"], out["db_from"], out["dbs"] = str(d), f"冊 {hit.get('id')}", n
            opt.db_home = str(d)
            if n == 0:
                out["lamp"], out["note"] = "YELLOW", f"冊上的家 {root} 底下沒有 .duckdb(第一次擷取後才有)"
        if not out["fetch_home"]:
            fh = hit.get("fetch_home")
            hubs = sorted({f.parent.parent for f in root.rglob("*.duckdb") if f.parent.name == "output_hub"})
            if fh and Path(fh).is_dir():
                out["fetch_home"], out["fetch_from"] = str(fh), f"冊 {hit.get('id')}"
            elif len(hubs) == 1:
                out["fetch_home"], out["fetch_from"] = str(hubs[0]), f"冊 {hit.get('id')} 的 output_hub 上一層"
            if out["fetch_home"]:
                opt.fetch_home = out["fetch_home"]
    elif homes and not out["db_home"]:
        out["lamp"], out["note"] = "YELLOW", "冊上的家在這台機器不在:" + " · ".join(str(h.get("db_home")) for h in homes) + " → 照前版(倉內 output_hub)"
    elif not book:
        out["note"] = "沒有資料家冊 → 照前版(--db-home / VIA_VDF_DB_HOME / 倉內 output_hub)"
    return out


def homes_line(h: dict) -> str:
    db = f"{h['db_home']}({h['db_from']}" + (f";庫檔 {h['dbs']}" if h.get("dbs") is not None else "") + ")" if h.get("db_home") else "倉內 output_hub(前版預設)"
    fh = f"{h['fetch_home']}({h['fetch_from']})" if h.get("fetch_home") else "擷取冊預設"
    return f"[資料家] {h['lamp']} · 庫 {db} · 擷取家 {fh} · 冊 {h.get('book') or '—'}" + (f" · {h['note']}" if h.get("note") else "")


def flow_fetch_lanes(opt, res, gate, log_dir, lists: dict, manager=None, py=None) -> dict:
    """本版一輪且 --lanes(預設開):清單就緒 → `engine run VDF_MDL012_FetchGroups run --groups … --jobs … --no-lists-first`;
    否則照前版逐列 fetch run。"""
    if not (_RUN14["on"] and getattr(opt, "lanes", False)):
        return _FLOW_FETCH_ORIG(opt, res, gate, log_dir, lists, manager, py)
    if not lists.get("lists_ready"):
        return {"flow": "fetch", "lamp": "BLOCKED", "steps": [], "lanes": True, "note": "兩張清單不在 → 不擷取(清單是所有擷取的開頭)"}
    args = ["engine", "run", FG_FAMILY_V0114, "run", "--groups", str(getattr(opt, "groups", "ALL") or "ALL"), "--mode", opt.mode,
            "--jobs", str(getattr(opt, "jobs", "auto") or "auto"), "--no-lists-first"]
    if opt.dry:
        args.append("--dry")
    if opt.fetch_home:
        args += ["--home", opt.fetch_home]
    if opt.timeout:
        args += ["--timeout", str(int(opt.timeout))]
    st = FLM.run_step("fetch_lanes", args, V0100.flow_env(res, "fetch"), log_dir, gate, None, manager, py)
    plan, result = [], ""
    try:
        for ln in Path(st["log"]).read_text(encoding="utf-8", errors="replace").splitlines() if st.get("log") else []:
            s = ln.strip()
            if s.startswith("道 ") or s.startswith("併道 "):
                plan.append(s)
            elif s.startswith("[run · 並行] 結束") or s.startswith("[GATED]") or s.startswith("[停]"):
                result = s
    except OSError:
        pass
    lamp = st["lamp"]
    note = {4: "雙閘沒開(操作員的手)→ 零子行程", 5: "清單引擎紅 → 擷取道沒起(清單是全部引擎的前提)", 1: "有擷取道紅,看 fetch_lanes.log",
            2: "找不到 VDF_MDL008_FetchSystem 尾版"}.get(st.get("rc"), "")
    if st.get("rc") == 0:
        note = "分道並行:%d 道%s" % (len([x for x in plan if x.startswith("道 ")]), (" · --dry 只列計畫" if opt.dry else ""))
    return {"flow": "fetch", "lamp": lamp, "steps": [st], "lanes": True, "groups": args[5], "jobs": args[9], "plan": plan[:12],
            "result": result[:300] or st.get("summary", ""), "note": note}


# ---------------------------------------------------------------- ② 總覽頁三塊
def _lamp_html(x) -> str:
    c = {"GREEN": "#1a7f37", "YELLOW": "#9a6700", "GATED": "#0969da", "BLOCKED": "#6e7781"}.get(x, "#cf222e")
    return f'<span class="lamp" style="background:{c}">{html.escape(str(x))}</span>'


def operate_links(ui_dir: Path) -> list:
    """→ [(名, 相對路徑或 None)];連結只給檔在的。"""
    out = []
    for z, n in OPERATE_LINKS_V0114:
        p = ui_dir / n
        out.append((z, os.path.relpath(p, V0100.REPORT_DIR) if p.exists() else None))
    return out


def sections_v0114(card: dict, ui_dir: Path) -> str:
    sync = card.get("sync")
    fetch = next((f for f in card.get("flows") or [] if f.get("flow") == "fetch"), None)
    parts = []
    if sync:
        body = "".join(f"<li>{html.escape(x)}</li>" for x in sync.get("lines") or []) or "<li>—</li>"
        pr = (f'<br><a href="{html.escape(sync["pr_url"])}">開 PR:{html.escape(sync["branch"] or "")}</a>' if sync.get("pr_url") else
              (f"<br>收據分支 {html.escape(sync['branch'])}" if sync.get("branch") else ""))
        note = f'<br><span class="mut">{html.escape(sync["note"])}</span>' if sync.get("note") else ""
        parts.append(f'<div class="card"><b>⓪ 同步到 main</b> {_lamp_html(sync["lamp"])} · {html.escape(str(sync.get("path")))} · {sync.get("secs")}s'
                     f'<ul>{body}</ul>{pr}{note}</div>')
    if fetch and fetch.get("lanes"):
        plan = "".join(f"<li>{html.escape(x)}</li>" for x in fetch.get("plan") or []) or "<li>—</li>"
        parts.append(f'<div class="card"><b>① 分道擷取</b> {_lamp_html(fetch["lamp"])} · 族群 {html.escape(str(fetch.get("groups")))} · 流程 {html.escape(str(fetch.get("jobs")))}'
                     f'<ul>{plan}</ul><span class="mut">{html.escape(fetch.get("result") or fetch.get("note") or "")}</span></div>')
    links = "".join(f'<li><a href="{html.escape(h)}">{html.escape(z)}</a></li>' if h else f"<li>{html.escape(z)} — 還沒產生</li>"
                    for z, h in operate_links(ui_dir))
    ask = V0100.tail(HERE, ASK_GLOB_V0114)
    cmds = [f'python "{HERE / "ActivateVDF.py"}" run --sync --refill-apply',
            (f'python "{ask}" ask --open' if ask else "VDF_ENG093_LaunchConsole 尾版不在")]
    hm = card.get("homes")
    hm_html = (f'<br>{_lamp_html(hm["lamp"])} <span class="mut">{html.escape(homes_line(hm))}</span>' if hm else "")
    parts.append(f'<div class="card"><b>操作入口</b><ul>{links}</ul>{hm_html}<span class="mut">問參數頁(勾步驟 → 啟動)· 重跑一鍵:</span>'
                 + "".join(f'<pre style="white-space:pre-wrap;margin:4px 0">{html.escape(c)}</pre>' for c in cmds) + "</div>")
    return '<div class="grid" id="via-v0114">' + "".join(parts) + "</div>"


def render_html(card: dict, ui_dir: Path) -> str:
    h = _RENDER_PREV(card, ui_dir)
    if not _RUN14["on"] or card.get("schema") != SCHEMA_V0114:
        return h
    sec = sections_v0114(card, ui_dir)
    i = h.find('<div class="wrap"><table>')
    return (h[:i] + sec + h[i:]) if i >= 0 else h.replace("</body>", sec + "</body>")


V0100.render_html = render_html

_ACTIVATE_V0113 = PRIOR.activate


def activate(opt, manager: Path | None = None, py: str | None = None, temp: Path | None = None) -> dict:
    """同 v0113 activate;本輪擷取走分道並行、JSON / 頁頭標 v0114、總覽頁多三塊、跑完印分道與操作入口。"""
    keep_tag, prev, keep_fetch = PRIOR.TAG, DBM._WRITE_REPORT_V0100, FLM._FLOW_FETCH_V0100

    def _stamp_then_write(c, u=None):
        c["sync"], c["homes"] = _RUN14["sync"], _RUN14["homes"]
        c["schema"], c["tag"] = SCHEMA_V0114, TAG
        return prev(c, u) if u is not None else prev(c)
    PRIOR.TAG = TAG
    DBM._WRITE_REPORT_V0100 = _stamp_then_write
    FLM._FLOW_FETCH_V0100 = flow_fetch_lanes
    _RUN14["on"] = True
    try:
        card = _ACTIVATE_V0113(opt, manager, py, temp)
    finally:
        PRIOR.TAG, DBM._WRITE_REPORT_V0100, FLM._FLOW_FETCH_V0100 = keep_tag, prev, keep_fetch
        _RUN14["on"] = False
    f = next((x for x in card.get("flows") or [] if x.get("flow") == "fetch" and x.get("lanes")), None)
    if f:
        print(f"  [分道擷取] {f['lamp']} · {f.get('result') or f.get('note')}", flush=True)
    ui_dir = V0100.VIA / "VIA_Reports" / "vdf"
    have = [z for z, h in operate_links(ui_dir) if h]
    print(f"  [操作入口] 總覽 {card.get('report', {}).get('html')} · 頁在:{' · '.join(have) or '—'}", flush=True)
    return card


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["--selftest"]:
        return selftest()
    opt = parse(argv)
    if opt.verb != "run":
        rc = V0100.main(opt.rest_argv)
        if opt.verb == "plan":
            print(f"  ⓪ 同步 {'開' if opt.sync else '關'}(--sync:{getattr(sync_path(), 'name', None)} --apply --case {' '.join(opt.sync_cases)})")
            print(f"  ① 擷取 {'分道並行 ' + FG_FAMILY_V0114 + ' run --groups ' + opt.groups + ' --jobs ' + opt.jobs if opt.lanes else '逐列 fetch run(--no-lanes)'}")
            print("  ③ " + homes_line(resolve_homes(opt)))
        return rc
    if opt.sync:
        s = run_sync(opt.sync_cases, log_dir=V0100.REPORT_DIR / "logs" / "sync")
        _RUN14["sync"] = s
        print(f"=== {TAG} · ⓪ 同步到 main({s.get('path')})===", flush=True)
        for ln in s["lines"]:
            print("  " + ln, flush=True)
        print(f"  [同步] {s['lamp']} · rc {s['rc']} · {s['secs']}s" + (f" · {s['note']}" if s.get("note") else "") + (f" · 收據分支 {s['branch']}" if s.get("branch") else ""), flush=True)
        if s["lamp"] != "GREEN":
            print("  [停] 同步紅 → 不在這棵樹上擷取(先照上面的 [VDF MAIN] / [交接] 處理)", flush=True)
            return 1
        if opt.sync_only:
            return 0
    _RUN14["homes"] = resolve_homes(opt)
    print("  " + homes_line(_RUN14["homes"]), flush=True)
    card = activate(opt)
    return {"GREEN": 0, "YELLOW": 2, "INTERRUPTED": 130}.get(card["lamp"], 1)


# ---------------------------------------------------------------- 自測
def selftest() -> int:
    import contextlib
    import io
    import shutil
    import tempfile
    import types
    p = f = 0

    def chk(name, cond, note=""):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s%s" % (name, (" · " + str(note)[:300]) if note else ""))

    print(f"=== {TAG} · 薄尾自測(同步 · 分道擷取 · 總覽三塊;沙盒 · 零網路 · 不碰真倉)===")
    o1 = parse(["run", "--sync", "--sync-case", "a", "--sync-case", "b", "--groups", "TW_CHIP", "--jobs", "3", "--mode", "block", "--dry", "--no-open"])
    o2 = parse(["run"])
    o3 = parse(["plan", "--sync-only", "--no-lanes"])
    chk("① 參數:本版旗標摘掉再交 v0100 parse(其餘照舊);預設 分道開 · ALL · auto · 不同步;--sync-only 隱含 --sync;--no-lanes 關分道",
        o1.sync and o1.sync_cases == ["a", "b"] and o1.groups == "TW_CHIP" and o1.jobs == "3" and o1.mode == "block" and o1.dry and o1.no_open and o1.lanes
        and o1.rest_argv == ["run", "--mode", "block", "--dry", "--no-open"]
        and not o2.sync and o2.lanes and o2.groups == "ALL" and o2.jobs == "auto" and o2.sync_cases == list(SYNC_CASES_V0114)
        and o3.verb == "plan" and o3.sync and o3.sync_only and not o3.lanes, (o1.rest_argv, o2.sync_cases))
    td = Path(tempfile.mkdtemp(prefix="vdfact114_"))
    try:
        fake = td / "VDF_MDL014_WorkstationSync_v9999.py"
        fake.write_text("import os, sys, pathlib\n"
                        "pathlib.Path('argv.txt').write_text(' '.join(sys.argv[1:]), encoding='utf-8')\n"
                        "rc = int(os.environ.get('FAKE_SYNC_RC', '0'))\n"
                        "if rc == 2:\n"
                        "    print('=== X · 停 ===\\n  [VDF MAIN] 本檔所在的工作樹 /x/vrn-feature 不是 VDF 的工作樹(預設 /y)—— 不接手別人的工作樹')\n"
                        "    sys.exit(2)\n"
                        "print('  [倉] 原 checkout /x · HEAD abc · 落後 origin/main 253 提交 · 本機獨有 133 提交')\n"
                        "print('  [備份] 不需要:已在 origin/workstation-20261020')\n"
                        "print('  [VDF MAIN] /y(本檔就在 VDF 工作樹裡)· 已在 · 乾淨')\n"
                        "print('  [資料] functional modules/VDF/output_hub:已接上(目錄接點)→ /x/hub')\n"
                        "print('  [交接] qg_onebridge rc %d · 標記 True' % (0 if rc == 0 else 1))\n"
                        "print('  [收據] 3 檔 → 分支 vdf-workstation-receipts-T1')\n"
                        "print('NEXT: 開 PR https://github.com/o/r/pull/new/vdf-workstation-receipts-T1(或把這行貼給 AI)')\n"
                        "print('[計] VDF_MDL014_WorkstationSync v0101 · 交接 %s · 資料 OK · %s' % (('全綠', 'PASS') if rc == 0 else ('有紅', 'FAIL')))\n"
                        "sys.exit(rc)\n", encoding="utf-8")
        s0 = run_sync(["c1", "c2"], log_dir=td / "logs", folder=td)
        argv_seen = (td / "argv.txt").read_text(encoding="utf-8")
        os.environ["FAKE_SYNC_RC"] = "1"
        s1 = run_sync(["c1"], folder=td)
        os.environ["FAKE_SYNC_RC"] = "2"
        s2 = run_sync(["c1"], folder=td)
        os.environ.pop("FAKE_SYNC_RC", None)
        s3 = run_sync(["c1"], folder=td / "nowhere")
        chk("② 同步:派 MDL014 尾版 --apply --case …(在它的夾裡跑)· 綠 = 抓到收據分支與開 PR 連結 · 八類行照抄 · sync.log 落在給的夾;"
            "交接紅 → RED 帶說明;rc 2(不是 VDF 工作樹)→ RED 帶那一行;尾版不在 → RED",
            s0["lamp"] == "GREEN" and argv_seen == "--apply --case c1 --case c2" and s0["branch"] == "vdf-workstation-receipts-T1"
            and s0["pr_url"] == "https://github.com/o/r/pull/new/vdf-workstation-receipts-T1" and s0["path"] == fake.name
            and any(x.startswith("[備份]") for x in s0["lines"]) and s0["summary"].startswith("[計]") and Path(s0["log"]).is_file()
            and s1["lamp"] == "RED" and s1["rc"] == 1 and "有紅" in s1["note"]
            and s2["lamp"] == "RED" and s2["rc"] == 2 and "不是 VDF 的工作樹" in s2["note"]
            and s3["lamp"] == "RED" and s3["rc"] is None and "不在" in s3["note"], (s0, s1.get("note"), s2.get("note")))
    finally:
        os.environ.pop("FAKE_SYNC_RC", None)
        shutil.rmtree(td, ignore_errors=True)

    calls = []
    td = Path(tempfile.mkdtemp(prefix="vdfact114b_"))
    try:
        def fake_step(name, args, env, log_dir, gate=None, timeout=None, manager=None, py=None):
            calls.append((name, list(args), env.get("VDF_T_FLOW")))
            lg = td / f"{name}_{len(calls)}.log"
            lg.write_text("[run · 並行] 族群 X · 道 2\n  道 vdf_tw_market          族群 TW · 庫 a.duckdb · 引擎 e054 → e057\n  道 parquet  族群 INTL_FIN · 庫 — · 引擎 006\n"
                          + {4: "[GATED] 雙閘沒開\n", 5: "[停] 清單引擎失敗 ['009'] → 後面的擷取不起\n"}.get(fake_step.rc, "[run · 並行] 結束 · 失敗 0/7 · 牆鐘 12s\n"),
                          encoding="utf-8")
            return {"step": name, "args": args, "rc": fake_step.rc, "lamp": V0100.lamp_of(fake_step.rc), "secs": 1, "log": str(lg), "summary": "x"}
        fake_step.rc = 0
        orig_calls = []
        keep = (FLM.run_step, V0100.flow_env)
        FLM.run_step, V0100.flow_env = fake_step, lambda res, flow, base_env=None: {"VDF_T_FLOW": flow}
        g = globals()
        keep_orig = g["_FLOW_FETCH_ORIG"]
        g["_FLOW_FETCH_ORIG"] = lambda *a, **k: (orig_calls.append(1), {"flow": "fetch", "lamp": "GREEN", "steps": [], "orig": True})[1]
        ready, not_ready = {"lists_ready": True}, {"lists_ready": False}
        try:
            _RUN14["on"] = True
            oA = types.SimpleNamespace(lanes=True, groups="ALL", jobs="auto", mode="live", dry=False, fetch_home=None, timeout=None)
            rA = flow_fetch_lanes(oA, {}, None, td, ready)
            oB = types.SimpleNamespace(lanes=True, groups="TW_CHIP,TW_FIN", jobs="3", mode="block", dry=True, fetch_home="/h", timeout=900.5)
            rB = flow_fetch_lanes(oB, {}, None, td, ready)
            rC = flow_fetch_lanes(oA, {}, None, td, not_ready)
            n_after_c = len(calls)
            fake_step.rc = 4
            rD = flow_fetch_lanes(oA, {}, None, td, ready)
            fake_step.rc = 5
            rE = flow_fetch_lanes(oA, {}, None, td, ready)
            fake_step.rc = 0
            rF = flow_fetch_lanes(types.SimpleNamespace(lanes=False, mode="live", dry=False, fetch_home=None, timeout=None), {}, None, td, ready)
            _RUN14["on"] = False
            rG = flow_fetch_lanes(oA, {}, None, td, ready)
        finally:
            _RUN14["on"] = False
            FLM.run_step, V0100.flow_env = keep
            g["_FLOW_FETCH_ORIG"] = keep_orig
        a_args = calls[0][1]
        chk("③ 分道擷取:清單就緒 → engine run FetchGroups run --groups --mode --jobs --no-lists-first(擷取流程環境)· --dry / --home / --timeout 照帶 ·"
            " 道的計畫與結束一行抓進結果;清單沒就緒 BLOCKED 零派;rc 4 GATED · rc 5 RED(清單紅沒起道);--no-lanes 或不在本版一輪 → 前版逐列",
            rA["lamp"] == "GREEN" and rA["lanes"] and a_args == ["engine", "run", FG_FAMILY_V0114, "run", "--groups", "ALL", "--mode", "live", "--jobs", "auto", "--no-lists-first"]
            and calls[0][2] == "fetch" and len(rA["plan"]) == 2 and rA["result"].startswith("[run · 並行] 結束") and "2 道" in rA["note"]
            and calls[1][1][5] == "TW_CHIP,TW_FIN" and calls[1][1][9] == "3" and "--dry" in calls[1][1] and calls[1][1][-4:] == ["--home", "/h", "--timeout", "900"]
            and rC["lamp"] == "BLOCKED" and n_after_c == 2 and rD["lamp"] == "GATED" and "雙閘" in rD["note"] and rE["lamp"] == "RED" and "清單引擎紅" in rE["note"]
            and rF.get("orig") and rG.get("orig") and len(orig_calls) == 2 and len(calls) == 4, (a_args, rB.get("steps") and calls[1][1], rC, rD.get("note"), len(calls)))
    finally:
        shutil.rmtree(td, ignore_errors=True)

    td = Path(tempfile.mkdtemp(prefix="vdfact114c_"))
    try:
        ui = td / "ui"
        ui.mkdir()
        (ui / "VDF_UI_latest.html").write_text("x", encoding="utf-8")
        (ui / "xsrc").mkdir()
        (ui / "xsrc" / "VDF_XSRC_latest.html").write_text("x", encoding="utf-8")
        card = {"schema": SCHEMA_V0114, "sync": {"lamp": "GREEN", "path": "VDF_MDL014_WorkstationSync_v0101.py", "secs": 3.2, "lines": ["[備份] 不需要"],
                                                 "branch": "vdf-workstation-receipts-T1", "pr_url": "https://github.com/o/r/pull/new/vdf-workstation-receipts-T1", "note": ""},
                "flows": [{"flow": "fetch", "lamp": "GREEN", "lanes": True, "groups": "ALL", "jobs": "auto", "plan": ["道 a", "道 b"], "result": "[run · 並行] 結束 · 失敗 0/7"}],
                "homes": {"db_home": "D:/via_01_vdf", "db_from": "冊 workstation", "dbs": 7, "fetch_home": None, "fetch_from": None, "book": "VDF_DataHome_SSOT_v0100.json", "lamp": "GREEN", "note": ""}}
        sec = sections_v0114(card, ui)
        g = globals()
        keep_r = g["_RENDER_PREV"]
        g["_RENDER_PREV"] = lambda c, u: '<html><body><div class="wrap"><table></table></div></body></html>'
        try:
            _RUN14["on"] = True
            on_ = render_html(card, ui)
            off_schema = render_html(dict(card, schema="VDF_ActivateVDF_v0113"), ui)
            _RUN14["on"] = False
            off_ = render_html(card, ui)
        finally:
            _RUN14["on"] = False
            g["_RENDER_PREV"] = keep_r
        chk("④ 總覽三塊:同步卡(燈 · 行 · 開 PR 連結)· 分道擷取(道 · 結束)· 操作入口(檔在的才連結;沒產生的照實說;問參數頁與重跑指令)·"
            " 只在本版一輪且本版 schema 時插在總表前;否則頁照前版",
            'id="via-v0114"' in sec and "⓪ 同步到 main" in sec and "pull/new/vdf-workstation-receipts-T1" in sec and "[備份] 不需要" in sec
            and "① 分道擷取" in sec and "道 a" in sec and "結束 · 失敗 0/7" in sec and "操作入口" in sec
            and 'href="%s"' % html.escape(os.path.relpath(ui / "VDF_UI_latest.html", V0100.REPORT_DIR)) in sec
            and 'href="%s"' % html.escape(os.path.relpath(ui / "xsrc" / "VDF_XSRC_latest.html", V0100.REPORT_DIR)) in sec and "資料庫檢查(db check) — 還沒產生" in sec
            and "ask --open" in sec and "run --sync --refill-apply" in sec and "[資料家] GREEN · 庫 D:/via_01_vdf(冊 workstation;庫檔 7)" in sec
            and on_.index('id="via-v0114"') < on_.index('<div class="wrap">') and 'via-v0114' not in off_ and 'via-v0114' not in off_schema, sec[:300])
    finally:
        shutil.rmtree(td, ignore_errors=True)

    acts, g = [], globals()
    keep_a, keep_s = g["activate"], g["run_sync"]
    g["activate"] = lambda opt, *a, **k: (acts.append(opt), {"lamp": "GREEN", "report": {"html": "h"}, "flows": []})[1]
    g["run_sync"] = lambda cases, **k: {"lamp": g["_FAKE_SYNC_LAMP"], "rc": 0 if g["_FAKE_SYNC_LAMP"] == "GREEN" else 2, "secs": 1, "path": "m", "lines": [], "branch": None, "note": "n"}
    try:
        g["_FAKE_SYNC_LAMP"] = "RED"
        with contextlib.redirect_stdout(io.StringIO()):
            rc_red = main(["run", "--sync", "--no-open"])
        g["_FAKE_SYNC_LAMP"] = "GREEN"
        with contextlib.redirect_stdout(io.StringIO()):
            rc_ok = main(["run", "--sync", "--no-open"])
            rc_only = main(["run", "--sync-only"])
            rc_plain = main(["run", "--no-open"])
        chk("⑤ 主流程:--sync 紅 → rc 1 且不啟動(不在錯的樹上抓);綠 → 接著啟動(opt 帶 sync / lanes);--sync-only 只同步 rc 0;不帶 --sync 直接啟動",
            rc_red == 1 and rc_ok == 0 and rc_only == 0 and rc_plain == 0 and len(acts) == 2
            and acts[0].sync and acts[0].lanes and not acts[1].sync, (rc_red, rc_ok, rc_only, rc_plain, len(acts)))
    finally:
        g["activate"], g["run_sync"] = keep_a, keep_s
        g.pop("_FAKE_SYNC_LAMP", None)
    td = Path(tempfile.mkdtemp(prefix="vdfact114h_"))
    try:
        home = td / "home"
        hub = home / "functional modules" / "VDF" / "output_hub"
        hub.mkdir(parents=True)
        (hub / "a.duckdb").write_bytes(b"x")
        (hub / "b.duckdb").write_bytes(b"x")
        (td / "VDF_DataHome_SSOT_v0100.json").write_text(json.dumps({"homes": [{"id": "gone", "db_home": str(td / "nope")}, {"id": "ws", "db_home": str(home)}]}), encoding="utf-8")
        (td / "VDF_DataHome_SSOT_v0099.json").write_text(json.dumps({"homes": [{"id": "old", "db_home": str(td)}]}), encoding="utf-8")
        ns = lambda **k: types.SimpleNamespace(**dict({"db_home": None, "fetch_home": None}, **k))   # noqa: E731
        oa = ns()
        ra = resolve_homes(oa, td, {})
        ob = ns()
        rb = resolve_homes(ob, td, {"VIA_VDF_DB_HOME": "/e", "VIA_VDF_FETCH_HOME": "/f"})
        oc = ns(db_home="/x")
        rc_ = resolve_homes(oc, td, {})
        gone = td / "gone"
        gone.mkdir()
        (gone / "VDF_DataHome_SSOT_v0100.json").write_text(json.dumps({"homes": [{"id": "ws", "db_home": str(td / "nope")}]}), encoding="utf-8")
        od = ns()
        rd = resolve_homes(od, gone, {})
        empty = td / "empty"
        empty.mkdir()
        re_ = resolve_homes(ns(), empty, {})
        broken = td / "broken"
        broken.mkdir()
        (broken / "VDF_DataHome_SSOT_v0100.json").write_text("{", encoding="utf-8")
        rf = resolve_homes(ns(), broken, {})
        scat = td / "scat"
        for sub in ("p/output_hub", "q/output_hub"):
            (scat / sub).mkdir(parents=True)
            (scat / sub / "z.duckdb").write_bytes(b"x")
        (td / "scat_book").mkdir()
        (td / "scat_book" / "VDF_DataHome_SSOT_v0100.json").write_text(json.dumps({"homes": [{"id": "s", "db_home": str(scat), "fetch_home": str(scat / "p")}]}), encoding="utf-8")
        og = ns()
        rg = resolve_homes(og, td / "scat_book", {})
        bk, bh = data_home_book(HERE)
        chk("⑦ 資料家:冊尾版(v0100 蓋 v0099)· 在的家才算(不在的跳過)· 庫檔都在同一夾 → 家定到那個夾、擷取家 = output_hub 上一層、寫回 opt;"
            " --db-home / 環境優先且不改 opt;冊上的家都不在 → YELLOW 說不在;沒冊 → 照前版;冊壞 → YELLOW 不倒;散在多夾 → 家本身、擷取家照冊上 fetch_home;"
            " 本夾正本冊有操作員的 via_01_vdf",
            ra["db_home"] == str(hub) and ra["db_from"] == "冊 ws" and ra["dbs"] == 2 and oa.db_home == str(hub) and ra["lamp"] == "GREEN"
            and ra["fetch_home"] == str(hub.parent) and oa.fetch_home == str(hub.parent) and "output_hub 上一層" in ra["fetch_from"] and ra["book"] == "VDF_DataHome_SSOT_v0100.json"
            and rb["db_home"] == "/e" and rb["db_from"] == "VIA_VDF_DB_HOME" and rb["fetch_home"] == "/f" and ob.db_home is None and ob.fetch_home is None
            and rc_["db_home"] == "/x" and rc_["db_from"] == "--db-home" and oc.db_home == "/x" and rc_["fetch_home"] == str(hub.parent)
            and rd["lamp"] == "YELLOW" and "不在" in rd["note"] and rd["db_home"] is None and od.db_home is None
            and re_["lamp"] == "GREEN" and re_["db_home"] is None and "沒有資料家冊" in re_["note"]
            and rf["lamp"] == "YELLOW" and "讀不到" in rf["note"] and rf["db_home"] is None
            and rg["db_home"] == str(scat) and rg["dbs"] == 2 and rg["fetch_home"] == str(scat / "p") and og.fetch_home == str(scat / "p")
            and bk is not None and any(str(h.get("db_home", "")).endswith("via_01_vdf") for h in bh)
            and "[資料家] GREEN · 庫 " + str(hub) + "(冊 ws;庫檔 2)" in homes_line(ra) and "不在" in homes_line(rd),
            (ra, rb, rc_, rd, re_, rf, rg, bk))
    finally:
        shutil.rmtree(td, ignore_errors=True)

    g = globals()
    keep_act, keep_w, keep_tag, keep_ff = g["_ACTIVATE_V0113"], DBM._WRITE_REPORT_V0100, PRIOR.TAG, FLM._FLOW_FETCH_V0100
    written, inner = [], []

    def fake_write(c, u=None):
        written.append(dict(c))
        return c

    def fake_act(opt, manager=None, py=None, temp=None):
        inner.append((_RUN14["on"], FLM._FLOW_FETCH_V0100 is flow_fetch_lanes, PRIOR.TAG))
        DBM._WRITE_REPORT_V0100({"lamp": "GREEN", "flows": [], "report": {"html": "h"}})
        return {"lamp": "GREEN", "flows": [], "report": {"html": "h"}}
    DBM._WRITE_REPORT_V0100, g["_ACTIVATE_V0113"] = fake_write, fake_act
    _RUN14["sync"], _RUN14["homes"] = {"lamp": "GREEN", "path": "m"}, {"db_home": "/x", "lamp": "GREEN"}
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            activate(types.SimpleNamespace(db_home=None, fetch_home=None))
        after = (_RUN14["on"], DBM._WRITE_REPORT_V0100 is fake_write, FLM._FLOW_FETCH_V0100 is keep_ff, PRIOR.TAG == keep_tag)
    finally:
        g["_ACTIVATE_V0113"], DBM._WRITE_REPORT_V0100, PRIOR.TAG, FLM._FLOW_FETCH_V0100 = keep_act, keep_w, keep_tag, keep_ff
        _RUN14["sync"] = _RUN14["homes"] = None
        _RUN14["on"] = False
    chk("⑧ activate 蓋章:前版寫 JSON 前把同步結果 · 資料家 · 本版 schema / tag 蓋進卡;那一輪裡分道擷取與本版 TAG 生效;跑完全部還原",
        len(written) == 1 and written[0].get("sync") == {"lamp": "GREEN", "path": "m"} and written[0].get("homes") == {"db_home": "/x", "lamp": "GREEN"}
        and written[0].get("schema") == SCHEMA_V0114 and written[0].get("tag") == TAG and inner == [(True, True, TAG)] and after == (False, True, True, True),
        (written, inner, after))
    src = Path(__file__).read_text(encoding="utf-8")
    imports = re.findall(r"^\s*(?:import|from)\s+([A-Za-z_][\w.]*)", src, re.M)
    chk("⑥ 加速器橋 · 網路橋在;不匯入他系統程式;不碰 TA-Lib;同意閘不寫;前版鏈總覽頁已換上本版包裝;不在本輪時擷取仍是前版那支",
        "VIA:ACCEL-BRIDGE" in src and "def _via_net" in src and V0100.render_html is render_html and FLM._FLOW_FETCH_V0100 is _FLOW_FETCH_ORIG
        and not [x for x in imports if x.startswith(("CGC_", "VRN_", "VRN2_", "VCGC"))]
        and not re.search(r"^\s*(import|from)\s+" + "talib", src, re.M)
        and not re.search(r"\[[\"']VIA_(NET|SCRAPE)_" + r"CONSENT[\"']\]\s*=(?!=)", src))
    print(f"  [計] {TAG} 本版 {p}/{p + f} · {'PASS' if not f else 'FAIL'}")
    if f:
        return 1
    if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1":
        return 0
    V0100.render_html = _RENDER_PREV                 # 前版自測看它自己的頁;跑完換回本版
    try:
        rc1 = PRIOR.selftest()
    finally:
        V0100.render_html = render_html
    return rc1 if rc1 in (0, 1, 2, 3) else 1


if __name__ == "__main__":
    raise SystemExit(main())
