#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VDF_MDL022_SafeParallelLaunch v0111 — 薄尾(v0100–v0110 一字不動):桌機 2026-11-26 22:12 實跑後的修正 + Rich 摘要矩陣 + 進度檔

桌機實錄(Start-VIA-VDF · 9.4 分 · 總 RED):
  ① 名稱反解 / 官方對帳都「略過:沒給資料家(--data-home / --via-db)」—— launch 沒帶 --data-home,v0106 / v0108 兩步就不做。
  ② 總經核對 12 項 NODATA「VAKE 庫不在(~\VAKE\db\vake.duckdb)」—— VAKE 實際在資料家 vake\,MDL016 只認 env VAKE_ROOT。
  ③ parquet sync 錯 2:tw__tw_trading_daily / gl__sentiment_daily「鍵欄不在既有 parquet(欄位改過)」—— 正典庫欄位變了、parquet 沒跟上。
  ④ 跑完印整張矩陣(每表重複兩次、上千行),看不出哪一步紅、為什麼紅。
  ⑤ 擷取流程 BLOCKED 的根因是 MDL008 v0113 main 簽章(已出 v0114 修),不在本檔。
本版(只換裝,不改前版邏輯):
  ① run 沒給 --data-home / --via-db → 用 v0110 effective_home(主流程同一個解析器)解析一次,補上 --data-home,全程同一個資料家。
  ② 資料家底下有 vake\ 且 env VAKE_ROOT 沒設 → 本行程與子行程設 VAKE_ROOT=<資料家>\vake(跟 MDL012 v0112 擷取道同一處)。
  ③ ⓪ 多一步:VDF 管理器 parquet align --apply(--dry 時唯讀),欄位對不上的 parquet 先照正典 DataFrame 對齊,再讓 sync 跑。
  ④ 跑完不印上千行全表(要看加 --matrix-all),改印「詳細摘要矩陣」(Rich;沒裝 Rich 照欄位純文字):
       流程 × 燈 × rc × 秒 × 最後一行;紅 / 黃逐項列「原因 → 下一步」;再加大類小計。
  ⑤ 進度檔 VIA_Reports\vdf\launch\LAUNCH_PROGRESS.json:每支流程起 / 完都寫(總數 · 完成 · 跑中 · 百分比 · 已耗 · 預估剩餘),
     PS 啟動器只讀它畫進度條(所有數字在這裡算好)。
  ⑥ 新動詞 summary:重印上一輪的詳細摘要矩陣(讀 VDF_Launch_latest.json;零寫入)。
執行中不量 CPU / DRAM、不減道(v0106 操作員裁定):開跑前一次降壓(BELOW_NORMAL + IO LOW · 執行緒 / DuckDB 上限)後直接 3 道同步跑。
不代設同意閘;不碰 TA-Lib。
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

import importlib.util
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
STEM = "VDF_MDL022_SafeParallelLaunch"
VERSION = "v0111"
TAG = f"{STEM} {VERSION}"
LAUNCH_DIR = VIA / "VIA_Reports" / "vdf" / "launch"
PROGRESS = LAUNCH_DIR / "LAUNCH_PROGRESS.json"
LATEST = LAUNCH_DIR / "VDF_Launch_latest.json"
STAGE_RECEIPT = VIA / "VIA_Reports" / "vdf" / "stage_merge" / "STAGE_MERGE_latest.json"
HINTS = (                                               # 最後一行 / 日誌常見字串 → 下一步(只給方向,不代修別的系統)
    (r"main\(\) takes 0 positional", "MDL008 v0113 main 漏 argv → 已出 VDF_MDL008_FetchSystem v0114,git pull 後重跑"),
    (r"兩張清單不在|清單 RED", "清單引擎沒產出(多半是上一條)→ 修好清單再跑;擷取不會在沒有清單時硬跑"),
    (r"鍵欄 .* 不在既有 parquet|欄位改過", "正典庫欄位變了 → 本版 ⓪ 已先跑 parquet align --apply,重跑即可"),
    (r"VAKE 庫不在", "VAKE_ROOT 沒指資料家 → 本版自動設 <資料家>\\vake(資料家底下要有 vake\\)"),
    (r"沒給資料家", "本版自動補 --data-home(用主流程同一個解析器)"),
    (r"inventory\.duckdb", "資料範圍矩陣讀到空的 inventory.duckdb → 不是 VDF 擷取表,屬清點庫;看 VDF_DataScope_latest.html 的未分類"),
    (r"未分類|UNMAPPED", "冊上沒有族群要的表 → 不是錯,是範圍冊沒登;要納管就登族群冊"),
    (r"同意閘|GATED", "出網要你在自己的視窗開兩道同意閘(本工具不代設)"),
)


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(str(p)).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(f"{STEM}_prior_for_{VERSION}", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ───────── ① ② 參數與環境 ─────────
def with_home(args: list) -> list:
    a = list(args)
    if "--data-home" in a or "--via-db" in a:
        return a
    h = PRIOR.effective_home(a)
    return a + ["--data-home", h] if h else a


def vake_env(home, env=None) -> dict:
    """資料家底下有 vake\\ 而 VAKE_ROOT 沒設 → {VAKE_ROOT: <資料家>\\vake};已設 / 沒有 vake\\ → {}。"""
    env = os.environ if env is None else env
    if env.get("VAKE_ROOT") or not home:
        return {}
    v = Path(home) / "vake"
    return {"VAKE_ROOT": str(v)} if v.is_dir() else {}


# ───────── ③ ⓪ 多一步 parquet align ─────────
def stage_steps(args: list) -> list:
    steps = list(_STAGE_BEFORE(args))
    mgr = PRIOR._tail("VDF_SystemManager_v*.py")
    home = PRIOR.effective_home(args)
    if mgr is not None and home:
        cmd = [sys.executable, "-X", "utf8", str(mgr), "parquet", "align", "--home", home] + ([] if "--dry" in args else ["--apply"])
        steps.append(("parquet 欄位對齊正典", cmd))
    return steps


_STAGE_BEFORE = PRIOR.stage_steps


# ───────── ⑤ 進度檔 ─────────
STATE = {"t0": None, "phase": ""}


def progress(jobs: dict | None = None, phase: str | None = None, final_rc=None, path: Path | None = None) -> dict:
    """寫進度檔(PS 只讀它畫進度條):數字全在這裡算。"""
    path = path or PROGRESS
    if phase is not None:
        STATE["phase"] = phase
    t0 = STATE["t0"] or time.time()
    jobs = jobs or {}
    total = len(jobs)
    done = sum(1 for j in jobs.values() if j.get("state") in ("DONE", "FAILED", "SKIP"))
    running = [k for k, j in jobs.items() if j.get("state") == "RUN"]
    el = time.time() - t0
    eta = round(el / done * (total - done), 1) if done and total > done else (0.0 if total and done >= total else None)
    d = {"at": _now(), "phase": STATE["phase"], "total": total, "done": done, "running": running,
         "pct": round(done / total * 100, 1) if total else 0.0, "elapsed_s": round(el, 1), "eta_s": eta,
         "current": ", ".join(running) or STATE["phase"], "final_rc": final_rc,
         "jobs": {k: {"title": j.get("title", ""), "state": j.get("state"), "lamp": j.get("lamp"), "sec": j.get("sec")} for k, j in jobs.items()}}
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.name + f".{os.getpid()}.tmp")
        tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
        os.replace(tmp, path)
    except OSError:
        pass
    return d


def _supervisor_classes() -> list:
    out = []
    for m in list(sys.modules.values()):
        f = Path(str(getattr(m, "__file__", "") or "")).name
        cls = vars(m).get("Supervisor") if f.startswith(STEM + "_v") else None
        if isinstance(cls, type) and cls not in out:
            out.append(cls)
    return out


def install_progress() -> list:
    """每一個前版監工類的 _start / _finish 包一層:原樣做完再寫進度檔。"""
    done = []
    for cls in _supervisor_classes():
        if getattr(cls, "_v0111_wrapped", False):
            continue
        s0, f0 = cls._start, cls._finish

        def _start(self, jid, _s0=s0):
            r = _s0(self, jid)
            progress(self.jobs, phase="③ 並行流程")
            return r

        def _finish(self, jid, rc, _f0=f0):
            r = _f0(self, jid, rc)
            progress(self.jobs)
            return r
        cls._start, cls._finish, cls._v0111_wrapped = _start, _finish, True
        done.append(cls)
    return done


# ───────── ④ 詳細摘要矩陣 ─────────
def hint_for(text: str) -> str:
    for pat, h in HINTS:
        if re.search(pat, text or ""):
            return h
    return ""


def summary_rows(rep: dict, stage: dict | None = None) -> tuple:
    rows, issues = [], []
    for j in (rep.get("run") or {}).get("jobs") or []:
        last = str(j.get("last") or "")
        rows.append({"id": j.get("id"), "title": str(j.get("title") or "")[:34], "lamp": j.get("lamp") or "—", "rc": j.get("rc"),
                     "sec": j.get("sec"), "last": last[:110]})
        if j.get("lamp") in ("RED", "YELLOW"):
            log_tail = ""
            lp = j.get("log")
            if lp and Path(lp).is_file():
                try:
                    log_tail = "\n".join(Path(lp).read_text(encoding="utf-8", errors="replace").splitlines()[-60:])
                except OSError:
                    log_tail = ""
            issues.append({"id": j.get("id"), "lamp": j.get("lamp"), "why": last[:140], "next": hint_for(last + "\n" + log_tail) or "看該流程日誌 " + str(lp or "")})
    if stage:
        n = sum(t.get("merged", 0) or 0 for d in stage.get("dbs") or [] for t in d.get("tables") or [])
        rows.insert(0, {"id": "⓪ 併入", "title": "暫存只補缺併入資料家", "lamp": stage.get("lamp", "—"), "rc": stage.get("rc"),
                        "sec": None, "last": f"庫 {len(stage.get('dbs') or [])} · 已併 {n:,} 列"})
    return rows, issues


LAMP_STYLE = {"GREEN": "green", "YELLOW": "yellow", "RED": "bold red"}


def render_summary(rep: dict, stage: dict | None = None, console=None, force_plain: bool = False) -> str:
    rows, issues = summary_rows(rep, stage)
    head = f"VDF 啟動詳細摘要 · 總燈 {rep.get('lamp', '—')} · {rep.get('at', '')} · 耗時 {(rep.get('run') or {}).get('wall_s', '—')}s"
    try:
        if force_plain:
            raise ImportError
        from rich.console import Console
        from rich.table import Table
    except ImportError:
        out = [head, f"{'流程':<12}{'燈':<8}{'rc':>4} {'秒':>8}  最後一行"]
        out += [f"{str(r['id']):<12}{r['lamp']:<8}{str(r['rc']):>4} {str(r['sec'] or '—'):>8}  {r['last']}" for r in rows]
        if issues:
            out.append("要處理(紅 / 黃):")
            out += [f"  [{i['lamp']}] {i['id']} · {i['why']}\n      → {i['next']}" for i in issues]
        out.append("(純文字:這台沒裝 Rich;欄位與 Rich 版相同)")
        txt = "\n".join(out)
        print(txt, flush=True)
        return txt
    con = console or Console()
    t = Table(title=head, show_lines=False, header_style="bold")
    for c, kw in (("流程", {}), ("說明", {}), ("燈", {}), ("rc", {"justify": "right"}), ("秒", {"justify": "right"}), ("最後一行", {"overflow": "fold"})):
        t.add_column(c, **kw)
    for r in rows:
        t.add_row(str(r["id"]), r["title"], f"[{LAMP_STYLE.get(r['lamp'], 'dim')}]{r['lamp']}[/]", str(r["rc"]), str(r["sec"] or "—"), r["last"])
    con.print(t)
    if issues:
        it = Table(title="要處理(紅 / 黃):原因 → 下一步", header_style="bold")
        for c in ("流程", "燈", "原因", "下一步"):
            it.add_column(c, overflow="fold")
        for i in issues:
            it.add_row(str(i["id"]), f"[{LAMP_STYLE.get(i['lamp'], 'dim')}]{i['lamp']}[/]", i["why"], i["next"])
        con.print(it)
    return head


def _load(p: Path) -> dict:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def summary_cmd(args: list) -> int:
    rep = _load(LATEST)
    if not rep:
        print(f"[{TAG}] NODATA · 還沒有上一輪的 {LATEST.name}")
        return 2
    render_summary(rep, _load(STAGE_RECEIPT), force_plain="--plain" in args)
    if "--matrix-all" in args or "--brief" in args:
        PRIOR.PRIOR.render(PRIOR.PRIOR.load_matrix(), brief="--brief" in args)
    return {"GREEN": 0, "YELLOW": 2}.get(rep.get("lamp"), 1)


# ───────── 主流程 ─────────
def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    if args[:1] == ["summary"]:
        return summary_cmd(args[1:])
    if args[:1] == ["launch"]:
        rest = args[1:]
        if "--skip-preflight" in rest:                  # PS 已先跑過 launch --check;背景這支直接開跑(預設起日照 launch)
            rest = [a for a in rest if a not in ("--skip-preflight", "--plain", "--check")]
            if "--start" not in rest:
                rest += ["--start", "2018-01-01"]
            return main(["run", *rest])
        return PRIOR.launch(rest, runner=main)
    if args[:1] != ["run"]:
        return PRIOR.main(args)
    args = with_home(PRIOR.norm_args(args))
    home = PRIOR.effective_home(args)
    for k, v in vake_env(home).items():
        os.environ[k] = v
        print(f"[{TAG}] {k} → {v}(資料家的 VAKE;MDL016 總經核對與擷取道同一處)", flush=True)
    STATE["t0"] = time.time()
    progress({}, phase="⓪ 擷取家 · 暫存併入 · parquet 對齊")
    install_progress()
    v109 = PRIOR.PRIOR
    keep_render, keep_stage = v109.render, PRIOR.stage_steps
    full = "--matrix-all" in args
    v109.render = (lambda d, **k: keep_render(d, **k)) if full else (lambda d, **k: keep_render(d, brief=True))
    PRIOR.stage_steps = stage_steps
    try:
        rc = PRIOR.main([a for a in args if a != "--matrix-all"])
    finally:
        v109.render, PRIOR.stage_steps = keep_render, keep_stage
    rep = _load(LATEST)
    progress((rep.get("run") or {}).get("jobs") and {j["id"]: j for j in rep["run"]["jobs"]} or {}, phase="完成", final_rc=rc)
    print(f"=== {TAG} · 詳細摘要矩陣(Rich)===", flush=True)
    if rep:
        render_summary(rep, _load(STAGE_RECEIPT))
    return rc


def selftest() -> int:
    import contextlib
    import io
    import subprocess
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f" · {str(note)[:300]}" if note and not cond else ""), flush=True)

    print(f"=== {TAG} · 薄尾自測(暫存夾 · 假子行程;不擷取)===", flush=True)
    chk("① 加速器真的載到(VIA_ACCEL is not None)", VIA_ACCEL is not None)
    chk("② 網路工具橋在位(載入不出網)", VIA_NET_TOOL_PATH is not None)
    keep_res = PRIOR.RESOLVER
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        home = td / "via_database" / "vdf_database"
        (home / "vake" / "db").mkdir(parents=True)
        try:
            PRIOR.RESOLVER = lambda arg=None, env=None: (home, "使用者文件夾")
            a = with_home(["run", "--start", "2018-01-01"])
            b = with_home(["run", "--data-home", "X"])
            st = stage_steps(["run", "--data-home", str(home)])
            st_dry = stage_steps(["run", "--dry", "--data-home", str(home)])
        finally:
            PRIOR.RESOLVER = keep_res
        chk("③ 沒給資料家 → 用主流程解析器補 --data-home(名稱反解 · 官方對帳不再略過);給了就不動",
            a[-2:] == ["--data-home", str(home)] and b == ["run", "--data-home", "X"], (a, b))
        chk("④ VAKE_ROOT:資料家有 vake\\ 且沒設 → 指資料家;已設 / 沒有 vake\\ → 不動",
            vake_env(home, {}) == {"VAKE_ROOT": str(home / "vake")} and vake_env(home, {"VAKE_ROOT": "/x"}) == {}
            and vake_env(td, {}) == {})
        chk("⑤ ⓪ 多 parquet align:--apply(--dry 唯讀)· 前面兩步(擷取家 · 併入)照舊",
            [t for t, _ in st][-1] == "parquet 欄位對齊正典" and "--apply" in st[-1][1] and "--apply" not in st_dry[-1][1]
            and [t for t, _ in st][:2] == ["擷取家", "暫存併入資料家"], [t for t, _ in st])
        pp = td / "p.json"
        STATE["t0"] = time.time() - 100
        jobs = {"gate": {"title": "g", "state": "DONE", "lamp": "GREEN", "sec": 10}, "fetch": {"title": "f", "state": "RUN"},
                "sync": {"title": "s", "state": "WAIT"}, "macro": {"title": "m", "state": "FAILED", "lamp": "RED", "sec": 3}}
        d = progress(jobs, phase="③", path=pp)
        saved = json.loads(pp.read_text(encoding="utf-8"))
        chk("⑥ 進度檔:總 4 · 完成 2(含失敗)· 跑中 fetch · 50% · 預估剩餘 ≈ 已耗 / 完成 × 剩下 · 原子寫",
            saved["total"] == 4 and saved["done"] == 2 and saved["running"] == ["fetch"] and saved["pct"] == 50.0
            and saved["eta_s"] is not None and 90 <= saved["eta_s"] <= 110 and d == saved, saved)
        log = td / "fetch.log"
        log.write_text("x\nTypeError: main() takes 0 positional arguments but 1 was given\n", encoding="utf-8")
        rep = {"lamp": "RED", "at": "t", "run": {"wall_s": 5, "jobs": [
            {"id": "gate", "title": "⓪a", "lamp": "GREEN", "rc": 0, "sec": 1, "last": "ok"},
            {"id": "fetch", "title": "①", "lamp": "RED", "rc": 1, "sec": 2, "last": "[分道擷取] BLOCKED · 兩張清單不在", "log": str(log)},
            {"id": "sync", "title": "②", "lamp": "RED", "rc": 1, "sec": 3, "last": "略過 鍵欄 ['src'] 不在既有 parquet(欄位改過?)"}]}}
        rows, issues = summary_rows(rep, {"lamp": "GREEN", "rc": 0, "dbs": [{"tables": [{"merged": 5}, {"merged": 7}]}]})
        chk("⑦ 摘要矩陣:⓪ 併入列在最前(已併 12 列)· 每支流程一列 · 紅 / 黃逐項給下一步(日誌裡的根因優先:fetch → MDL008 v0114)",
            rows[0]["id"] == "⓪ 併入" and "12" in rows[0]["last"] and len(rows) == 4 and [i["id"] for i in issues] == ["fetch", "sync"]
            and "v0114" in issues[0]["next"] and "align" in issues[1]["next"], (rows, issues))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            render_summary(rep, None, force_plain=True)
        chk("⑧ 沒 Rich 照欄位純文字(同欄位 · 照實註明)", "要處理" in buf.getvalue() and "純文字" in buf.getvalue())
    seen = []
    keep_main = globals()["main"]
    try:
        globals()["main"] = lambda a=None: seen.append(list(a)) or 0
        keep_main(["launch", "--skip-preflight", "--data-home", "D"])
    finally:
        globals()["main"] = keep_main
    chk("⑧b launch --skip-preflight → 直接 run(不重做開跑前檢查)· 沒給起日補 2018-01-01 · 其他參數原樣",
        seen == [["run", "--data-home", "D", "--start", "2018-01-01"]], seen)
    classes = install_progress()
    chk("⑨ 前版鏈的監工類 _start / _finish 都包上進度(重複裝不會包兩層)",
        _supervisor_classes() and all(getattr(c, "_v0111_wrapped", False) for c in _supervisor_classes()) and install_progress() == [], classes)
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            rc_p = PRIOR.selftest()
    except Exception as exc:  # noqa: BLE001
        rc_p = 1
        print(f"  [註] 前版自測丟例外:{type(exc).__name__}", flush=True)
    alone = subprocess.run([sys.executable, str(PRIOR_PATH), "--selftest"], capture_output=True, text=True, timeout=900).returncode
    chk("⑩ 前版鏈自測在本版下的結果 = 單獨跑 v0110 的結果(本版不讓前版變壞)", (rc_p == 0) == (alone == 0) and rc_p in (0, 2), (rc_p, alone))
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑪ 檔面:第 3 行加速器標記 · 雙橋 · glob 取前版 · 零 TA-Lib · 不設同意閘",
        src.splitlines()[2].startswith("# [VIA:ACCEL-BRIDGE") and "[VIA:NET-BRIDGE:v0100]" in src and "HERE.glob(STEM" in src
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M)
        and not re.search(r"^\s*os\.environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", src, re.M))
    print(f"[selftest] {TAG} {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}" + ("" if rc_p == 0 else " · 前版自測本來就黃(缺 rich)"), flush=True)
    if not all(ok):
        return 1
    return 0 if rc_p == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
