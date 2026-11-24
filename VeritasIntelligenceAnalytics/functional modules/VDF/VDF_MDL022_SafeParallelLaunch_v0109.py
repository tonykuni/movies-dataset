#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VDF_MDL022_SafeParallelLaunch v0109 — 薄尾:起始日對範圍冊 + 跑完用 Rich 印「已抓資料分類矩陣」;前版一字不動

操作員 2026-11-22:「建立一個 PY 啟動指令 三流程同步啟動 輸出 2018~今的資料 … 增量擷取不要重複 · 後續指令都要用到加速器 ·
抓出來的資料矩陣分類顯示 RICH」。前版鏈(v0100–v0108)已經是那一支:降壓等靜 → 固定 3 道 → 橋閘(加速器 + 網路工具 100%)
→ 不重複擷取計畫 → ActivateVDF 增量擷取(庫裡有的不重抓)→ parquet 只寫新鍵 → 資料範圍矩陣 → 總經 → 收尾 → 官方對帳。
本版只加兩件事,其餘全部轉給 v0108:
  ① run --start YYYY-MM-DD:開跑前讀 VDF 範圍冊(FetchGroups 尾版 `start`,只讀)的各大類起始日;
     有大類比 --start 晚 → 印 YELLOW 一行 + 逐類點名改冊的那一行(FetchGroups start --category X --set … --apply)。
     本檔不寫冊、不改擷取引擎(操作員令:起始日只改範圍冊)。--start 照舊交給前版的資料矩陣那一道。
  ② run 跑完(不帶 --dry)與新動詞 matrix:讀 ENG240 的 VDF_DataScope_latest.json,用 Rich 印
     大類 × 族群 × 表(列數 · 起 · 訖 · 鍵數 · 起始前 · 重複列 · 多餘 % · 燈)+ 大類小計。Rich 不在 → 同欄位純文字(誠實註明)。
     matrix 零寫入;--brief 只印大類小計;--all 連 NODATA 的表也逐列印(預設每個族群合成一列)。
用法:run [--via-db <via_database> | --data-home <夾>] [--start 2018-01-01] [--no-open] [--dry] … · matrix [--brief] [--all] · check · --selftest
rc:同前版(0 綠 · 2 黃 · 1 紅);matrix 照矩陣總燈(NODATA / YELLOW = 2 · RED = 1)。不代設同意閘;不碰 TA-Lib。
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
except Exception:  # noqa: BLE001
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)。啟動器自己不連網,連網的是各擷取引擎。"""
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
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
STEM = "VDF_MDL022_SafeParallelLaunch"
VERSION = "v0109"
TAG = f"{STEM} {VERSION}"
FG_GLOB = "VDF_MDL012_FetchGroups_v*.py"
MATRIX_JSON = VIA / "VIA_Reports" / "vdf" / "datamatrix" / "VDF_DataScope_latest.json"
LAMP_RC = {"GREEN": 0, "RED": 1}
LAMP_STYLE = {"GREEN": "green", "YELLOW": "yellow", "RED": "bold red", "NODATA": "dim", "LOCKED": "magenta"}
START_RE = re.compile(r"^\s*([A-Z][A-Z_]+)\s+.*?起始日\s+(\d{4}-\d{2}-\d{2})")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location("vdf_launch_prior_for_" + VERSION, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):
    """尾版律 TAILAPI:前版公開名稱經本檔轉接。"""
    return getattr(PRIOR, name)


def _opt(args: list, flag: str, default=None):
    return args[args.index(flag) + 1] if flag in args and args.index(flag) + 1 < len(args) else default


# ─────────────── ① 起始日對範圍冊(只讀) ───────────────
def start_check(want: str, runner=None) -> tuple:
    """讀 FetchGroups 尾版 `start`(只列,不帶 --apply)的各大類起始日,對 --start。回 (燈, 行, {大類: 起始日})。"""
    if not DATE_RE.match(want or ""):
        return "RED", [f"[{TAG}] --start 要 YYYY-MM-DD,收到 {want!r}(零寫入,不往下跑)"], {}
    fgs = sorted((p for p in HERE.glob(FG_GLOB) if _vnum(p) >= 0), key=_vnum)
    if not fgs:
        return "YELLOW", [f"[{TAG}] 起始日沒對到:{FG_GLOB} 不在"], {}
    cmd = [sys.executable, "-B", str(fgs[-1]), "start"]
    env = dict(os.environ, VIA_FROM_VDFSM="YES", PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    try:
        cp = (runner or subprocess.run)(cmd, cwd=str(HERE), env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
        out = cp.stdout or ""
    except Exception as exc:  # noqa: BLE001
        return "YELLOW", [f"[{TAG}] 起始日沒對到:{type(exc).__name__}: {str(exc)[:120]}"], {}
    starts = {m.group(1): m.group(2) for m in (START_RE.match(x) for x in out.splitlines()) if m}
    if not starts:
        return "YELLOW", [f"[{TAG}] 起始日沒對到:{fgs[-1].name} start 沒印出大類起始日"], {}
    late = {c: s for c, s in starts.items() if s > want}
    if not late:
        return "GREEN", [f"[{TAG}] 起始日 GREEN · 範圍冊各大類都從 {want} 或更早開始 · " + " · ".join(f"{c} {s}" for c, s in starts.items())], starts
    lines = [f"[{TAG}] 起始日 YELLOW · 範圍冊有 {len(late)} 類比 --start {want} 晚(只改範圍冊,不改引擎;本檔不代寫):"]
    lines += [f"    {c} 現在 {s} → py \"{fgs[-1].name}\" start --category {c} --set {want} --apply" for c, s in late.items()]
    return "YELLOW", lines, starts


# ─────────────── ② Rich 分類矩陣(零寫入) ───────────────
def load_matrix(path=None) -> dict:
    p = Path(path) if path else MATRIX_JSON
    if not p.is_file():
        return {"lamp": "NODATA", "missing": str(p), "rows": [], "categories": [], "totals": {}}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return {"lamp": "RED", "missing": f"{p}:{type(exc).__name__}", "rows": [], "categories": [], "totals": {}}


def _n(v) -> str:
    return "—" if v in (None, "") else (f"{v:,}" if isinstance(v, int) else str(v))


def matrix_rows(d: dict, show_all: bool = False) -> list:
    """表列:有資料的表逐列;全是 NODATA 的族群合成一列(--all 則逐列)。依 大類 → 族群 → 表 排。"""
    out, nod = [], {}
    for r in d.get("rows", []):
        key = (r.get("category") or "", r.get("group") or "—")
        if r.get("state") == "NODATA" and not show_all:
            nod.setdefault(key, []).append(r)
            continue
        out.append({"cat": key[0], "grp": key[1], "table": f"{r.get('db') or ''}:{r.get('table') or ''}", "rows": r.get("rows"),
                    "min": r.get("min_date"), "max": r.get("max_date"), "keys": r.get("keys"), "pre": r.get("pre_start"),
                    "dup": r.get("dup_rows"), "excess": r.get("excess_pct"), "lamp": r.get("lamp") or "—"})
    seen = {(x["cat"], x["grp"]) for x in out}
    for key, rs in nod.items():
        out.append({"cat": key[0], "grp": key[1], "table": f"(NODATA {len(rs)} 表" + (",同族群另有表有資料)" if key in seen else ")"),
                    "rows": None, "min": None, "max": None, "keys": None, "pre": None, "dup": None, "excess": None, "lamp": "NODATA"})
    order = {c.get("category"): i for i, c in enumerate(d.get("categories", []))}
    gorder = {}
    for r in d.get("rows", []):
        gorder.setdefault((r.get("category") or "", r.get("group") or "—"), len(gorder))
    return sorted(out, key=lambda x: (order.get(x["cat"], 99), x["cat"], gorder.get((x["cat"], x["grp"]), 999), x["lamp"] == "NODATA", x["table"]))


COLS = (("大類", "cat"), ("族群", "grp"), ("庫:表", "table"), ("列數", "rows"), ("起", "min"), ("訖", "max"), ("鍵數", "keys"),
        ("起始前", "pre"), ("重複列", "dup"), ("多餘%", "excess"), ("燈", "lamp"))
CAT_COLS = (("大類", "category"), ("名稱", "zh"), ("表", "tables"), ("列數", "rows"), ("多餘", "excess"), ("起始前", "pre_start"),
            ("重複列", "dup_rows"), ("NODATA", "nodata"), ("多餘%", "excess_pct"), ("燈", "lamp"))


def render(d: dict, console=None, brief: bool = False, show_all: bool = False, force_plain: bool = False) -> int:
    """印矩陣;回 rc(照矩陣總燈)。console 給 = 印到它(自測用);Rich 不在或 force_plain = 同欄位純文字。"""
    lamp = d.get("lamp") or "NODATA"
    head = (f"VDF 已抓資料分類矩陣 · 總燈 {lamp} · 範圍起始 {d.get('start') or '—'} · 量測 {d.get('at') or '—'}"
            f" · 資料家 {d.get('home') or '—'}")
    if d.get("missing"):
        head += f" · 讀不到 {d['missing']}(先跑 run,或 VDF_SystemManager datamatrix)"
    t = d.get("totals") or {}
    foot = ("合計 表 {} · 擷取列 {} · 多餘 {}({}%)· NODATA {} · 未分類 {} · 控制表入湖 {}".format(
        _n(t.get("tables")), _n(t.get("rows_fetch")), _n(t.get("excess_fetch")), _n(t.get("excess_pct_fetch")),
        _n(t.get("nodata")), _n(t.get("unmapped")), _n(t.get("control_in_lake"))))
    cats = d.get("categories") or []
    rows = [] if brief else matrix_rows(d, show_all)
    rich = None
    if not force_plain:
        try:
            from rich.console import Console
            from rich.table import Table
            from rich import box
            rich = (Console, Table, box)
        except Exception:  # noqa: BLE001
            rich = None
    if rich:
        Console, Table, box = rich
        con = console or Console(highlight=False)
        con.print(f"[bold]{head}[/bold]")
        ct = Table(title="大類小計", box=box.SIMPLE_HEAVY, show_lines=False)
        for lab, _k in CAT_COLS:
            ct.add_column(lab, justify="right" if lab in ("表", "列數", "多餘", "起始前", "重複列", "NODATA", "多餘%") else "left")
        for c in cats:
            ct.add_row(*[_n(c.get(k)) for _l, k in CAT_COLS[:-1]], f"[{LAMP_STYLE.get(c.get('lamp'), '')}]{c.get('lamp') or '—'}[/]")
        con.print(ct)
        if rows:
            mt = Table(title="大類 × 族群 × 表", box=box.MINIMAL_DOUBLE_HEAD)
            for lab, _k in COLS:
                mt.add_column(lab, justify="right" if lab in ("列數", "鍵數", "起始前", "重複列", "多餘%") else "left",
                              overflow="fold")
            prev = None
            for x in rows:
                st = LAMP_STYLE.get(x["lamp"], "")
                cat = x["cat"] if x["cat"] != prev else ""
                prev = x["cat"]
                mt.add_row(cat, *[_n(x[k]) for _l, k in COLS[1:-1]], f"[{st}]{x['lamp']}[/]", style="dim" if x["lamp"] == "NODATA" else None)
            con.print(mt)
        con.print(foot)
    else:
        w = (console.file if console is not None and hasattr(console, "file") else sys.stdout)
        print(head + ("" if force_plain else "(Rich 不在 → 純文字;裝 rich 走 VCGC 安裝閘)"), file=w)
        print(" | ".join(lab for lab, _k in CAT_COLS), file=w)
        for c in cats:
            print(" | ".join(_n(c.get(k)) for _l, k in CAT_COLS), file=w)
        if rows:
            print(" | ".join(lab for lab, _k in COLS), file=w)
            for x in rows:
                print(" | ".join(_n(x[k]) for _l, k in COLS), file=w)
        print(foot, file=w)
    return LAMP_RC.get(lamp, 2)


def matrix_cmd(args: list) -> int:
    """`matrix [--file <json>] [--brief] [--all] [--plain]`:零寫入,只讀上一輪的 VDF_DataScope_latest.json。"""
    return render(load_matrix(_opt(args, "--file")), brief="--brief" in args, show_all="--all" in args, force_plain="--plain" in args)


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    if args[:1] == ["matrix"]:
        return matrix_cmd(args[1:])
    if args[:1] == ["run"] and "--start" in args:
        lamp, lines, _st = start_check(_opt(args, "--start", ""))
        for ln in lines:
            print(ln, flush=True)
        if lamp == "RED":
            return 1
    rc = PRIOR.main(args)
    if args[:1] == ["run"] and "--dry" not in args:
        print(f"=== {TAG} · 已抓資料分類矩陣(Rich · 讀 {MATRIX_JSON.name})===", flush=True)
        render(load_matrix())
    if args[:1] in ([], ["help"], ["-h"], ["--help"]):
        print(f"  {TAG}:run … [--start YYYY-MM-DD](先對範圍冊起始日)· 跑完印 Rich 分類矩陣 · matrix [--brief] [--all] [--plain](零寫入)")
    return rc


def selftest() -> int:
    import io
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)[:300]) if note and not cond else ''}")

    rc0 = PRIOR.selftest()
    print(f"=== {TAG} · 薄尾自測(起始日對範圍冊 · Rich 分類矩陣;假子行程 · 暫存夾 · 零網路)===")
    chk("⓪ 前版 %s 自測過" % PRIOR_PATH.stem, rc0 == 0, f"rc {rc0}")
    fg_out = ("  TW_MARKET  台股 · 主動式台股 ETF     起始日 2018-01-01(預設 2022-07-01)· 族群 TW_PRICE_VOL\n"
              "  FIN        財報                    起始日 2021-01-01(預設 2021-01-01)· 族群 TW_FIN\n"
              "  MACRO      總經                    起始日 1990-01-01(預設 1990-01-01)· 族群 CN_MACRO\n")
    seen = []

    def fake(cmd, **k):
        seen.append((cmd, k))
        return subprocess.CompletedProcess(cmd, 0, fg_out, "")
    l1, lines1, st1 = start_check("2018-01-01", runner=fake)
    chk("① 有大類比 --start 晚 → YELLOW · 點名那一類與改冊指令(--apply 只印不跑)",
        l1 == "YELLOW" and len(st1) == 3 and any("FIN 現在 2021-01-01" in x and "--set 2018-01-01 --apply" in x for x in lines1)
        and not any("TW_MARKET 現在" in x for x in lines1), lines1)
    chk("② 叫的是 FetchGroups 尾版 `start`(不帶 --apply)· 子行程帶 VDF 自己的入口標記",
        seen and Path(seen[0][0][2]).name.startswith("VDF_MDL012_FetchGroups_v") and seen[0][0][3:] == ["start"]
        and seen[0][1]["env"].get("VIA_FROM_VDFSM") == "YES", seen[:1])
    l2, lines2, _ = start_check("1980-01-01", runner=fake)
    l3, lines3, _ = start_check("2018/01/01", runner=fake)
    l4, _, _ = start_check("2018-01-01", runner=lambda c, **k: subprocess.CompletedProcess(c, 0, "nothing", ""))
    chk("③ --start 比全部都早 → 每類都點名(YELLOW)· 錯形日期 → RED 零寫入 · 讀不到 → YELLOW(不假綠)",
        l2 == "YELLOW" and l3 == "RED" and l4 == "YELLOW" and "YYYY-MM-DD" in lines3[0], (l2, l3, l4))
    l5, _, _ = start_check("2026-12-31", runner=fake)
    chk("③b 範圍冊全部早於 --start → GREEN", l5 == "GREEN", l5)
    fixture = {"lamp": "YELLOW", "start": "2018-01-01", "at": "2026-11-22T00:00:00Z", "home": "/tmp/x",
               "totals": {"tables": 4, "rows_fetch": 1200, "excess_fetch": 12, "excess_pct_fetch": 1.0, "nodata": 2, "unmapped": 0, "control_in_lake": 0},
               "categories": [{"category": "TW_MARKET", "zh": "台股", "tables": 3, "rows": 1200, "excess": 12, "pre_start": 2, "dup_rows": 10,
                               "nodata": 1, "excess_pct": 1.0, "lamp": "YELLOW"},
                              {"category": "MACRO", "zh": "總經", "tables": 1, "rows": 0, "excess": 0, "pre_start": 0, "dup_rows": 0, "nodata": 1,
                               "excess_pct": 0.0, "lamp": "NODATA"}],
               "rows": [{"category": "TW_MARKET", "group": "TW_PRICE_VOL", "db": "vdf_tw_market.duckdb", "table": "tw_daily_prices", "rows": 1200,
                         "min_date": "2018-01-02", "max_date": "2026-11-20", "keys": 1950, "pre_start": 2, "dup_rows": 10, "excess_pct": 1.0,
                         "state": "OK", "lamp": "YELLOW"},
                        {"category": "TW_MARKET", "group": "TW_PRICE_VOL", "db": "vdf_tw_market.duckdb", "table": "tw_trading_daily", "rows": 0,
                         "state": "NODATA", "lamp": "NODATA"},
                        {"category": "TW_MARKET", "group": "TW_INDEX", "db": "VDF_TWIndex_Daily.duckdb", "table": "tw_index_daily", "rows": 0,
                         "state": "NODATA", "lamp": "NODATA"},
                        {"category": "MACRO", "group": "US_MACRO", "db": "us.duckdb", "table": "us_macro", "rows": 0, "state": "NODATA", "lamp": "NODATA"}]}
    rows = matrix_rows(fixture)
    chk("④ 矩陣列:有資料逐表 · 全 NODATA 的族群合成一列 · 同族群另有表有資料也照實註明 · 大類照冊排序",
        [r["grp"] for r in rows] == ["TW_PRICE_VOL", "TW_PRICE_VOL", "TW_INDEX", "US_MACRO"]
        and rows[0]["table"].endswith("tw_daily_prices") and "同族群另有表有資料" in rows[1]["table"] and rows[-1]["cat"] == "MACRO", rows)
    chk("④b --all → 每張表一列(含 NODATA)", len(matrix_rows(fixture, show_all=True)) == 4)
    try:
        from rich.console import Console
        has_rich = True
    except Exception:  # noqa: BLE001
        has_rich = False
    if has_rich:
        buf = io.StringIO()
        con = Console(file=buf, width=200, color_system=None, highlight=False)
        rc_r = render(fixture, console=con)
        txt = buf.getvalue()
        chk("⑤ Rich:大類小計 + 大類 × 族群 × 表 · 欄位(列數 · 起 · 訖 · 重複列)· 數字千分位 · 合計行 · rc 照總燈(YELLOW = 2)",
            rc_r == 2 and "大類小計" in txt and "大類 × 族群 × 表" in txt and "tw_daily_prices" in txt and "1,200" in txt
            and "2018-01-02" in txt and "重複列" in txt and "合計 表 4" in txt, txt[:600])
        buf2 = io.StringIO()
        rc_b = render(fixture, console=Console(file=buf2, width=200, color_system=None), brief=True)
        chk("⑥ --brief 只印大類小計", rc_b == 2 and "大類小計" in buf2.getvalue() and "大類 × 族群 × 表" not in buf2.getvalue())
    else:
        chk("⑤ Rich 不在 → 這一檢 SKIP(缺依賴 = 黃,不算綠)", False, "rich 沒裝:走 VCGC 安裝閘 CGC_MDL056 rich")
    class _W:  # noqa: N801
        file = io.StringIO()
    rc_p = render(fixture, console=_W, force_plain=True)
    ptxt = _W.file.getvalue()
    chk("⑦ 純文字退路:同欄位 · 同合計 · 同 rc", rc_p == 2 and "tw_daily_prices" in ptxt and "合計 表 4" in ptxt and " | " in ptxt, ptxt[:300])
    with tempfile.TemporaryDirectory(prefix="mdl022_v0109_") as td:
        miss = load_matrix(Path(td) / "none.json")
        bad = Path(td) / "bad.json"
        bad.write_text("{not json", encoding="utf-8")
        broken = load_matrix(bad)
        good = Path(td) / "good.json"
        good.write_text(json.dumps(fixture, ensure_ascii=False), encoding="utf-8")
        before = sorted(p.name for p in Path(td).iterdir())
        _W.file = io.StringIO()
        rc_g = render(load_matrix(good), console=_W, force_plain=True)
        after = sorted(p.name for p in Path(td).iterdir())
    chk("⑧ 讀檔:不在 = NODATA(rc 2)· 壞檔 = RED(rc 1)· 好檔照讀 · matrix 零寫入",
        miss["lamp"] == "NODATA" and broken["lamp"] == "RED" and rc_g == 2 and before == after
        and render(miss, console=_W, force_plain=True) == 2 and render(broken, console=_W, force_plain=True) == 1)
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    import ast
    tree = ast.parse(src)
    imported = {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    chk("⑨ 兩座標準橋在(語法樹真的匯入加速器)· 不碰 TA-Lib · 不寫同意閘 · 不寫範圍冊(--apply 只出現在印給人看的字串)",
        "VIA_SuperAccel_Module" in imported and "# ===== [VIA:NET-BRIDGE:v0100]" in src and "def _via_net" in src
        and "talib" not in imported and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", body)
        and not re.search(r"\[[^\]]*\"--apply\"[^\]]*\]", body))
    pub = [n for n in dir(PRIOR) if not n.startswith("_") and callable(getattr(PRIOR, n, None))]
    chk("⑩ 尾版保有前版公開名稱(TAILAPI)", all(getattr(sys.modules[__name__], n, None) is not None for n in pub), f"{len(pub)} 支")
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · 合計 {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
