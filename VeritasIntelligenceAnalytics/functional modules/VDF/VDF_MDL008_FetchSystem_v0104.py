#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_MDL008_FetchSystem v0104 — 薄尾:網路工具 AST 真橋 · 冊 v0103 · fill --progress 動態百分比 · fill-matrix 詳細矩陣(Rich · AST 位置)

操作員 2026-10-03:「所有的 VDF 都要加最新的網路工具」「現在這個指令撰寫適用 PS 檔案也要加速模組及動態進度條百分比
DETAILED MATRIX SUMMARY BY RICH WITH AST POSITION」。
  ① 模組層 VIA_NET_TOOL_PATH + def _via_net()(CGC_MDL230 ③ 真橋判準;v0103 只有標記 → 不一致)。
  ② 冊 VDF_FetchSystem_SSOT_v0103.json(MDL009 → v0102);子行程從本版起(讀冊 v0103)。
  ③ fill … --progress:逐支執行,每支前後印一行機讀進度 `##VIA-PROGRESS## {json}`(i · n · pct · id · rc · sec),
     PS 啟動器 Invoke-VDF-FetchFill 讀它畫 Write-Progress 百分比;報告多帶每支的 AST 位置(冊上擷取函式 名@行)。
  ④ fill-matrix <報告.json> [--plain]:詳細矩陣摘要 —— 有 rich 用 Rich 表格(每支:群組 · 檔 · AST 位置 · 補前理由 · rc · 秒 ·
     輸出合格 · 補後燈),沒有 rich 照實退成純文字(同欄同列,不冒充)。
fill 其餘(只抓不足 · 清單第一步 · 雙閘 rc 4 零寫 · ABSENT 列 pip)照 v0103。不碰 TA-Lib;不讀寫同意閘。
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
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import contextlib
import importlib.util
import io
import json
import os
import re
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_MDL008_FetchSystem"
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"
PROGRESS_TAG_V0104 = "##VIA-PROGRESS##"


def _vnum_v0104(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0104(p) < _vnum_v0104(__file__)), key=_vnum_v0104)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
V0102 = PRIOR.PRIOR                                    # 冊 / 子行程鏈
V0101 = PRIOR.V0101                                    # 入口 · 監控 · 資料庫層
BASE = PRIOR.BASE                                      # v0100 本體


def __getattr__(name):
    return getattr(PRIOR, name)


BOOK_V0103 = HERE / "VDF_FetchSystem_SSOT_v0103.json"
_RUN_V0102 = V0102.run_v0102


def load_book_v0104(path: Path = BOOK_V0103) -> dict:
    return V0102.PRIOR._LOAD_BOOK_V0100(path)


def run_v0104(*args, **kwargs):
    """同 v0102 run;子行程改從本版起(v0102 的 __file__ 在這一次呼叫內指向本版 → 子行程讀冊 v0103),呼叫完還原。"""
    keep = V0102.__dict__.get("__file__")
    V0102.__dict__["__file__"] = str(Path(__file__).resolve())
    try:
        return _RUN_V0102(*args, **kwargs)
    finally:
        V0102.__dict__["__file__"] = keep


def _install_v0104() -> None:
    V0101.load_book_v0101, V0101.BOOK_V0101 = load_book_v0104, BOOK_V0103
    V0101.run_v0101 = V0102.run_v0102 = run_v0104
    BASE.load_book, BASE.run = load_book_v0104, run_v0104


_install_v0104()


def ast_positions_v0104(row: dict) -> str:
    """冊上擷取函式的 AST 位置(名@行);冊沒列 = 「—」。"""
    return " · ".join(f"{f['name']}@{f['line']}" for f in row.get("fetch_functions") or []) or "—"


def _emit_v0104(i: int, n: int, eid: str, phase: str, rc=None, sec=None, emit=print) -> None:
    pct = round(100.0 * i / n, 1) if n else 100.0
    emit(f"[進度] {i}/{n} {pct:.1f}% · {eid} {'開始' if phase == 'start' else '完成 rc ' + str(rc) + ' · ' + str(sec) + 's'}")   # PS Invoke-VIAPython 協定(真百分比)
    emit(PROGRESS_TAG_V0104 + " " + json.dumps({"i": i, "n": n, "pct": pct, "id": eid, "phase": phase, "rc": rc, "sec": sec}, ensure_ascii=False))


def fill_v0104(book: dict, home: Path, mode: str = "live", max_age_h: float = 20.0, force: bool = False, ids: list | None = None,
               group: str | None = None, apply: bool = False, timeout: int | None = None, progress: bool = False, emit=print) -> dict:
    """v0103 fill 同一判準;差別:逐支跑(每支前後一行進度)· 報告帶 AST 位置。"""
    home = Path(home)
    before = PRIOR.gaps_v0103(book, home, mode, max_age_h, force, ids, group)
    rows = PRIOR.select_v0103(book, before)
    by = {r["id"]: r for r in book["engines"]}
    rep = {"engine": TAG, "mode": mode, "home": str(home), "max_age_h": max_age_h, "apply": apply,
           "at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "before": before, "selected": [r["id"] for r in rows],
           "absent": [g for g in before if g["absent"]], "runs": [], "verify": [], "after": [], "db": None,
           "ast": {r["id"]: {"file": r["file"], "kind": r.get("kind"), "positions": ast_positions_v0104(r)} for r in book["engines"]}}
    if not apply or not rows:
        rep["rc"] = 0
        return rep
    if mode == "live" and not BASE.gate_open():
        rep["rc"], rep["gated"] = 4, True
        return rep
    home.mkdir(parents=True, exist_ok=True)
    order = BASE.ordered(rows)
    n = len(order)
    for i, r in enumerate(order):
        if progress:
            _emit_v0104(i, n, r["id"], "start", emit=emit)
        res = run_v0104([r], mode, home, logs=home.parent / "_logs", timeout=timeout or BASE.CHILD_TIMEOUT_S)
        rep["runs"] += res
        if progress:
            _emit_v0104(i + 1, n, r["id"], "done", res[0]["rc"] if res else None, res[0]["sec"] if res else None, emit=emit)
    rep["verify"] = BASE.verify(rows, home)
    rep["after"] = PRIOR.gaps_v0103(book, home, mode, max_age_h, False, ids, group)
    try:
        rep["db"] = V0101.db_v0101(home)
    except ImportError:
        rep["db"] = {"error": "ABSENT:duckdb"}
    except Exception as e:  # 資料庫層照實回報
        rep["db"] = {"error": f"{type(e).__name__}: {str(e)[:120]}"}
    rep["rc"] = 0 if all(x["rc"] == 0 for x in rep["runs"]) and all(v["ok"] for v in rep["verify"]) else 1
    rd = home.parent / "_reports"
    rd.mkdir(parents=True, exist_ok=True)
    rep["report"] = str(rd / f"fill_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json")
    Path(rep["report"]).write_text(json.dumps(rep, ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8")
    return rep


def matrix_rows_v0104(rep: dict) -> list:
    """詳細矩陣的列:每支一列(補前 · 執行 · 驗收 · 補後 · AST 位置)。"""
    runs = {x["id"]: x for x in rep.get("runs") or []}
    after = {g["id"]: g for g in rep.get("after") or []}
    ver = {}
    for v in rep.get("verify") or []:
        ver.setdefault(v["id"], []).append(v)
    out = []
    for g in rep.get("before") or []:
        x, a, vs = runs.get(g["id"]), after.get(g["id"]), ver.get(g["id"], [])
        ast_ = (rep.get("ast") or {}).get(g["id"], {})
        if g["absent"]:
            state = "ABSENT"
        elif x is None:
            state = "GATED" if rep.get("gated") and g["id"] in rep.get("selected", []) else ("PLAN" if g["id"] in rep.get("selected", []) else "FRESH")
        else:
            state = {0: "OK", 2: "NODATA", 3: "ABSENT", 4: "GATED", 124: "TIMEOUT"}.get(x["rc"], "FAIL")
        out.append({"id": g["id"], "mdl": g["mdl"], "group": g["group"], "file": ast_.get("file", ""), "ast": ast_.get("positions", "—"),
                    "before": ("缺 " + ",".join(g["absent"])) if g["absent"] else (" · ".join(g["reasons"]) or "新鮮"),
                    "state": state, "rc": None if x is None else x["rc"], "sec": None if x is None else x["sec"],
                    "outputs": f"{sum(v['ok'] for v in vs)}/{len(vs)}" if vs else "—",
                    "after": "—" if a is None else ("仍不足" if a["need"] else "足")})
    return out


def render_matrix_v0104(rep: dict, plain: bool = False, file=None) -> str:
    """有 rich → Rich 表格 + 摘要;沒有 rich 或 --plain → 同欄純文字。回傳用的是哪一種。"""
    rows = matrix_rows_v0104(rep)
    n_run = len(rep.get("runs") or [])
    ok_run = sum(1 for x in rep.get("runs") or [] if x["rc"] == 0)
    vs = rep.get("verify") or []
    d = rep.get("db") or {}
    summary = (f"模式 {rep.get('mode')} · 輸出根 {rep.get('home')} · 要抓 {len(rep.get('selected') or [])} · 執行 {n_run} · 成功 {ok_run}"
               f"({(100.0 * ok_run / n_run) if n_run else 100.0:.1f}%)· 輸出 {sum(v['ok'] for v in vs)}/{len(vs)} · "
               f"補後仍不足 {sum(1 for r in rows if r['after'] == '仍不足')} · 資料庫 視圖 {d.get('views')} 鍵欄 {len(d.get('keyed_views') or [])}"
               + (" · 雙閘沒開(零寫)" if rep.get("gated") else "") + f" · 報告 {rep.get('report') or '—'} · 總判 {'PASS' if rep.get('rc') == 0 else 'FAIL' if rep.get('rc') == 1 else 'rc ' + str(rep.get('rc'))}")
    cols = ("#", "引擎", "群組", "檔", "AST 位置", "補前", "狀態", "rc", "秒", "輸出", "補後")
    if not plain:
        try:
            from rich.console import Console
            from rich.table import Table
            from rich.panel import Panel
        except ImportError:
            plain = True
    if not plain:
        style = {"OK": "green", "FRESH": "green", "PLAN": "cyan", "GATED": "yellow", "ABSENT": "yellow", "NODATA": "yellow", "FAIL": "red", "TIMEOUT": "red"}
        t = Table(title="VDF 擷取系統 · 補缺詳細矩陣", show_lines=False, header_style="bold")
        for c in cols:
            t.add_column(c, overflow="fold", no_wrap=c in ("#", "rc", "秒", "輸出"))
        for i, r in enumerate(rows, 1):
            t.add_row(str(i), r["mdl"], r["group"], r["file"], r["ast"], r["before"], f"[{style.get(r['state'], 'white')}]{r['state']}[/]",
                      "" if r["rc"] is None else str(r["rc"]), "" if r["sec"] is None else f"{r['sec']:.1f}", r["outputs"], r["after"])
        con = Console(file=file, width=200)
        con.print(t)
        con.print(Panel(summary, title="摘要", border_style="green" if rep.get("rc") == 0 else "red"))
        return "rich"
    out = file or sys.stdout
    print("VDF 擷取系統 · 補缺詳細矩陣(純文字;rich 不在 → py -3 -m pip install rich 可得彩色表)", file=out)
    print(" | ".join(cols), file=out)
    for i, r in enumerate(rows, 1):
        print(" | ".join([str(i), r["mdl"], r["group"], r["file"], r["ast"], r["before"], r["state"], "" if r["rc"] is None else str(r["rc"]),
                          "" if r["sec"] is None else f"{r['sec']:.1f}", r["outputs"], r["after"]]), file=out)
    print("摘要:" + summary, file=out)
    return "plain"


def _arg_v0104(rest: list, flag: str):
    return rest[rest.index(flag) + 1] if flag in rest and rest.index(flag) + 1 < len(rest) else None


def fill_main_v0104(rest: list) -> int:
    """v0103 fill 的參數律 + --progress;每支前後印進度行,結尾印詳細矩陣。"""
    book = load_book_v0104()
    known = {r["id"] for r in book["engines"]}
    vals = {_arg_v0104(rest, f) for f in ("--home", "--mode", "--max-age-h", "--group")}
    ids = [a for a in rest if not a.startswith("--") and a not in vals]
    bad = [i for i in ids if i not in known]
    mode = _arg_v0104(rest, "--mode") or "live"
    grp = _arg_v0104(rest, "--group")
    try:
        age = float(_arg_v0104(rest, "--max-age-h") or PRIOR.FILL_MAX_AGE_H_V0103)
    except ValueError:
        age = -1.0
    flags = ("--home", "--mode", "--max-age-h", "--group", "--all", "--apply", "--json", "--progress", "--plain")
    unknown = [a for a in rest if a.startswith("--") and a not in flags]
    if bad or unknown or mode not in BASE.MODES or age < 0 or (grp and grp not in V0101.GROUPS_V0101):
        print(f"[拒跑] {TAG}:fill 參數不對(冊上沒有 {bad} · 不認得 {unknown} · --mode 只收 {'/'.join(BASE.MODES)} · "
              f"--group 只收 {'/'.join(V0101.GROUPS_V0101)} · --max-age-h 要 ≥ 0)")
        return 2
    if "--apply" in rest:
        core = [m for m in V0101.CORE_PACKAGES_V0101 if importlib.util.find_spec(m) is None]
        if core:
            print(f"[ABSENT] {TAG}:本直譯器缺核心套件 {', '.join(core)} —— 不代裝;自己裝:py -3 -m pip install {' '.join(core)}")
            return 3
    emit = (lambda s: print(s, flush=True))
    rep = fill_v0104(book, BASE.home_dir(_arg_v0104(rest, "--home")), mode, age, "--all" in rest, ids, grp, "--apply" in rest,
                     progress="--progress" in rest, emit=emit)
    if "--json" in rest:
        print(json.dumps({"vdf_fetch_fill": rep}, ensure_ascii=False, default=str))
    else:
        PRIOR._print_fill_v0103(rep)
        render_matrix_v0104(rep, plain="--plain" in rest)          # 計畫 / 閘關 / 執行都出詳細矩陣(狀態欄分 PLAN · GATED · OK …)
    return rep["rc"]


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"]:
        return selftest()
    if args[:1] in (["fill"], ["fill-matrix"]):
        if not V0101.entry_ok_v0101():
            print(f"[VDF_MDL008] 拒絕。VDF 擷取系統由 VDF System Manager 總控:"
                  f"python \"functional modules/VDF/VDF_SystemManager_v0128.py\" fetch {' '.join(args)}(VCGC 也可呼叫)")
            return 2
        if args[0] == "fill-matrix":
            src = [a for a in args[1:] if not a.startswith("--")]
            if len(src) != 1 or not Path(src[0]).is_file():
                print(f"[拒跑] {TAG}:fill-matrix 要給一份 fill 報告(_reports/fill_*.json)")
                return 2
            rep = json.loads(Path(src[0]).read_text(encoding="utf-8"))
            render_matrix_v0104(rep, plain="--plain" in args)
            return int(rep.get("rc") or 0)
        with V0101._approved_call_v0101():
            return fill_main_v0104(args[1:])
    return PRIOR.main(args)


def selftest() -> int:
    import ast
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    V0102.run_v0102 = _RUN_V0102                       # 前版自測驗的是前版自己的冊與子行程(冊 v0102 · MDL009 v0101)
    V0102._install_v0102()
    try:
        rc0 = PRIOR.selftest()
    finally:
        _install_v0104()                               # 前版自測結尾會重裝它們那一套;本版再蓋回
    print(f"=== {TAG} · 薄尾自測(網路工具真橋 · 冊 v0103 · 進度百分比 · 詳細矩陣)===")
    chk("① v0103 自測過(fill 補缺:只抓不足 · 清單第一步 · 雙閘 · 冊 / 子行程鏈)", rc0 == 0, f"rc {rc0}")
    text = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(text)

    def _net_assign(n):
        return isinstance(n, ast.Assign) and any(getattr(t, "id", "") == "VIA_NET_TOOL_PATH" for t in n.targets)
    chk("② AST:模組層 VIA_NET_TOOL_PATH 指派 + def _via_net()(CGC_MDL230 ③ 真橋)",
        any(_net_assign(n) or (isinstance(n, ast.Try) and any(_net_assign(s) for s in n.body)) for n in tree.body)
        and any(isinstance(n, ast.FunctionDef) and n.name == "_via_net" for n in tree.body))
    book = load_book_v0104()
    old = V0102.PRIOR._LOAD_BOOK_V0100(HERE / "VDF_FetchSystem_SSOT_v0102.json")
    e9 = next(r for r in book["engines"] if r["id"] == "009")
    defs = {(n.name, n.lineno) for n in ast.walk(ast.parse((HERE / e9["file"]).read_text(encoding="utf-8"))) if isinstance(n, ast.FunctionDef)}
    chk("③ 冊 v0103:MDL009 → v0102 · AST 位置對得上 · 其餘 34 支與冊 v0102 相同",
        e9["file"] == "VDF_MDL009_TWStockList_v0102.py" and all((f["name"], f["line"]) in defs for f in e9["fetch_functions"])
        and [r for r in book["engines"] if r["id"] != "009"] == [r for r in old["engines"] if r["id"] != "009"])
    lines = []
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp) / "dict"
        rep = fill_v0104(book, home, "fixture", ids=["009", "010", "001u"], apply=True, timeout=900, progress=True, emit=lines.append)
        prog = [json.loads(s.split(" ", 1)[1]) for s in lines if s.startswith(PROGRESS_TAG_V0104)]
        done = [p for p in prog if p["phase"] == "done"]
        log9 = (home.parent / "_logs" / "009_fixture.log")
        human = [s for s in lines if s.startswith("[進度] ")]
        chk("④ fill --progress:每支前後一行機讀進度 + 一行「[進度] i/n」(PS Invoke-VIAPython 真百分比協定)· 百分比遞增到 100 · rc 0 · 子行程跑的是 MDL009 v0102",
            rep["rc"] == 0 and len(prog) == 6 and len(human) == 6 and human[-1].startswith("[進度] 3/3 100.0%") and [p["pct"] for p in done] == sorted(p["pct"] for p in done) and done[-1]["pct"] == 100.0
            and log9.is_file() and "VDF_MDL009_TWStockList_v0102.py" in log9.read_text(encoding="utf-8"), [p["pct"] for p in done])
        buf = io.StringIO()
        how = render_matrix_v0104(json.loads(Path(rep["report"]).read_text(encoding="utf-8")), plain=True, file=buf)
        txt = buf.getvalue()
        chk("⑤ 詳細矩陣(純文字路徑):每支一列 · AST 位置(名@行)· 狀態 OK · 摘要含成功率 / 輸出 / 資料庫 / 總判",
            how == "plain" and "fetch_json_v0100@" in txt and "| OK |" in txt and "總判 PASS" in txt and "100.0%" in txt, txt.splitlines()[2][:90])
        has_rich = importlib.util.find_spec("rich") is not None
        if has_rich:
            buf2 = io.StringIO()
            how2 = render_matrix_v0104(json.loads(Path(rep["report"]).read_text(encoding="utf-8")), file=buf2)
            chk("⑥ Rich 路徑:rich 在 → Rich 表格(同欄)+ 摘要框", how2 == "rich" and "補缺詳細矩陣" in buf2.getvalue() and "摘要" in buf2.getvalue())
        else:
            chk("⑥ Rich 路徑:本直譯器沒有 rich → 照實退純文字(不冒充;工作站 pip install rich 後走 Rich 表)",
                render_matrix_v0104({"before": [], "rc": 0}, file=io.StringIO()) == "plain")
    saved = {k: os.environ.pop(k, None) for k in ("VIA_FROM_VDFSM", "VIA_FROM_VCGC")}
    try:
        with contextlib.redirect_stdout(io.StringIO()) as buf3:
            rc_x = main(["fill-matrix", "nope.json"])
            os.environ["VIA_FROM_VDFSM"] = "YES"
            rc_bad = main(["fill-matrix", "nope.json"])
    finally:
        os.environ.pop("VIA_FROM_VDFSM", None)
        for k, v in saved.items():
            if v is not None:
                os.environ[k] = v
    chk("⑦ 入口:沒有總控標記 → rc 2;fill-matrix 找不到報告 → rc 2", rc_x == 2 and rc_bad == 2 and "VDF System Manager" in buf3.getvalue())
    chk("⑧ 加速器橋 · 網路橋在;不碰 TA-Lib;不寫同意閘", "[VIA:ACCEL-BRIDGE" in text and "[VIA:NET-BRIDGE" in text
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M) and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", text))
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · v0103 {'PASS' if rc0 == 0 else 'FAIL'} · 合計 {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
