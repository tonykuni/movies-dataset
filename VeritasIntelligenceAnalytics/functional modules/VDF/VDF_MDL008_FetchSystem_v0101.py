#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_MDL008_FetchSystem v0101 — 薄尾:獨立運作,由 VDF System Manager 總控 · 第一步兩支清單引擎

操作員 2026-10-03:「改為獨立運作由 VDF SYSTEM MANAGER 總控」。
v0100 只收 VCGC 呼叫(VIA_FROM_VCGC=YES)。本版入口改成:
  ① VDF 管理員發的總控標記 VIA_FROM_VDFSM=YES(VDF_SystemManager v0128 起;不經 VCGC 也能跑)
  ② VCGC 呼叫照收(VIA_FROM_VCGC=YES)
  兩者皆無 = 拒絕,並指向總控入口。v0100 的冊 · 路徑改寫 · 三種網路模式 · 輸出契約 · 整合測試一字不動;
本版只在「入口通過」的這一次呼叫內,讓 v0100 的入口檢查看到已核准(呼叫結束即還原環境)。
同意閘(VIA_NET_CONSENT / VIA_SCRAPE_CONSENT)是另一層,照舊由鎖版網路工具判,本支不讀不寫。不碰 TA-Lib。
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
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_MDL008_FetchSystem"
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"
ENTRY_VDFSM = "VIA_FROM_VDFSM"                       # VDF 管理員總控標記


def _vnum_v0101(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


def _load_v0101(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0101(p) < _vnum_v0101(__file__)), key=_vnum_v0101)
PRIOR = _load_v0101(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


# ---------------------------------------------------------------- 第一步兩支清單引擎(冊 v0101)
BOOK_V0101 = HERE / "VDF_FetchSystem_SSOT_v0101.json"
_LOAD_BOOK_V0100 = PRIOR.load_book
_FIX_ROUTE_V0100 = PRIOR._fix_route
_RUN_V0100 = PRIOR.run
FIX_ETF_BOOK_V0101 = [("00981A", "主動群益台灣強棒", "國內成分證券主動式交易所交易基金(股票)"),
                      ("00980A", "主動野村臺灣優選", "國內成分證券主動式交易所交易基金(股票)"),
                      ("00402A", "主動安聯美國科技", "國外成分證券主動式交易所交易基金(股票)"),
                      ("0050", "元大台灣50", "國內成分證券指數股票型基金"), ("00679B", "元大美債20年", "國外成分債券指數股票型基金")]


def load_book_v0101(path: Path = BOOK_V0101) -> dict:
    return _LOAD_BOOK_V0100(path)


def fix_route_v0101(url: str):
    """v0100 樣本網 + ETF 冊 t187ap47_L(官方欄名;主動 3 · 被動 / 債券 2)。"""
    if "t187ap47_l" in str(url).lower():
        return [{"出表日期": "1151003", "基金代號": c, "基金簡稱": n, "基金名稱": n + "證券投資信託基金", "基金類型": t}
                for c, n, t in FIX_ETF_BOOK_V0101]
    return _FIX_ROUTE_V0100(url)


def run_v0101(rows, mode, home, logs=None, timeout=PRIOR.CHILD_TIMEOUT_S, args_key="run_args"):
    """同 v0100 run,但子行程從本版起(冊 v0101 與 ETF 冊樣本在子行程裡也生效)。"""
    import subprocess
    import time
    logs = logs or (Path(home).parent / "_logs")
    logs.mkdir(parents=True, exist_ok=True)
    out = []
    for r in PRIOR.ordered(rows):
        log = logs / f"{r['id']}_{mode}.log"
        t0 = time.time()
        miss = missing_v0101(r)
        if miss:                                                   # 缺套件 = 照實 ABSENT,不起子行程(不代裝)
            txt = f"[MDL008] {r['mdl']} ABSENT:本直譯器缺 {', '.join(miss)}(不代裝;工作站裝齊才跑)\n[MDL008] {r['mdl']} rc=3\n"
            log.write_text(txt, encoding="utf-8")
            out.append({"id": r["id"], "mdl": r["mdl"], "rc": 3, "sec": 0.0, "log": str(log), "tail": txt.strip().splitlines()[-2:], "absent": miss})
            continue
        env = dict(os.environ, VIA_FROM_VCGC="YES", VIA_FROM_VDFSM="YES", PYTHONIOENCODING="utf-8")
        env.update({k: str(v).replace("{home}", str(home)) for k, v in (r.get("env") or {}).items()})
        try:
            p = subprocess.run([sys.executable, "-X", "utf8", str(Path(__file__)), "_child", r["id"], str(home), mode, "--",
                                *r.get(args_key, [])], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               text=True, encoding="utf-8", errors="replace", timeout=timeout, env=env, cwd=str(Path(home).parent))
            rc, txt = p.returncode, p.stdout
        except subprocess.TimeoutExpired as e:
            rc, txt = 124, (e.stdout or "") if isinstance(e.stdout, str) else ""
        log.write_text(txt, encoding="utf-8")
        tail = [ln for ln in txt.splitlines() if ln.strip()][-3:]
        out.append({"id": r["id"], "mdl": r["mdl"], "rc": rc, "sec": round(time.time() - t0, 1), "log": str(log), "tail": tail})
    return out


def missing_v0101(row: dict) -> list:
    return [m for m in row.get("requires") or [] if importlib.util.find_spec(m) is None]


GROUPS_V0101 = ("TWSE/TPEX", "YFINANCE", "FED", "AKSHARE", "OTHERS")
TICKER_COLS_V0101 = ("ticker", "Ticker", "code", "Code", "symbol", "Symbol", "證券代號", "公司代號", "stock_id")


def list_v0101(book: dict, group: str | None = None) -> list:
    out = []
    for r in book["engines"]:
        if group and r["group"] != group:
            continue
        out.append({"id": r["id"], "mdl": r["mdl"], "kind": r["kind"], "group": r["group"], "file": r["file"],
                    "exists": (HERE / r["file"]).is_file(), "doc": r.get("doc", ""), "tables": r.get("tables") or [],
                    "run_args": r.get("run_args"), "missing": missing_v0101(r)})
    return out


def card_v0101(row: dict) -> dict:
    """單引擎卡:AST(說明首句 · 定義數 · 匯入 · 擷取函式)+ VCGC 整組(CGC_MDL253 params 卡:SSOT 冊 · regex · 同義字 · 工作流步)。"""
    import ast as _ast
    path = HERE / row["file"]
    src = path.read_text(encoding="utf-8", errors="replace")
    tree = _ast.parse(src)
    imps = sorted({(n.module if isinstance(n, _ast.ImportFrom) else a.name).split(".")[0] for n in _ast.walk(tree)
                   if isinstance(n, (_ast.Import, _ast.ImportFrom)) for a in (n.names if isinstance(n, _ast.Import) else [n])
                   if (n.module if isinstance(n, _ast.ImportFrom) else a.name)})
    card = {"id": row["id"], "mdl": row["mdl"], "kind": row["kind"], "group": row["group"], "file": row["file"],
            "ast": {"doc": (_ast.get_docstring(tree) or "").strip().splitlines()[0][:200] if _ast.get_docstring(tree) else "",
                    "defs": sum(isinstance(n, (_ast.FunctionDef, _ast.AsyncFunctionDef, _ast.ClassDef)) for n in _ast.walk(tree)),
                    "imports": imps, "bridges": {"accel": "[VIA:ACCEL-BRIDGE" in src, "net": "[VIA:NET-BRIDGE" in src}},
            "fetch_functions": row.get("fetch_functions") or [], "tables": row.get("tables") or [], "outputs": row.get("outputs") or [],
            "run": row.get("run_args"), "test": row.get("test_args"), "requires": row.get("requires") or [], "missing": missing_v0101(row),
            "launch": f"python \"functional modules/VDF/VDF_SystemManager_v0128.py\" fetch run {row['id']} --apply"}
    try:
        reg = HERE.parents[1] / "supportive modules" / "registry"
        inv = _load_v0101(sorted(reg.glob("CGC_MDL253_ToolingInventory_v*.py"), key=_vnum_v0101)[-1], "vdf_card_inventory_v0101")
        fam = re.sub(r"_v\d{4}$", "", Path(row["file"]).stem)
        rows = inv.PRIOR.engines("VDF") if hasattr(inv, "PRIOR") and hasattr(inv.PRIOR, "engines") else []
        hit, _ = inv.PRIOR.resolve(rows, fam) if rows else (None, [])
        if hit is not None:
            c = inv.params_card_v0101(hit, "VDF")
            card["vcgc"] = {"lamp": c.get("lamp"), "ssot": c.get("ssot"), "regex": c.get("regex"), "synonyms": c.get("synonyms"),
                            "workflow": c.get("workflow"), "env": c.get("env"), "code": c.get("code"), "chain": c.get("chain")}
        else:
            card["vcgc"] = {"lamp": "NODATA", "why": f"VCGC 引擎盤點沒有 {fam}(MDL 大引擎走子系統根;SSOT 由本冊管)"}
    except Exception as exc:
        card["vcgc"] = {"lamp": "ABSENT", "why": f"{type(exc).__name__}: {str(exc)[:120]}"}
    return card


def status_v0101(book: dict, home: Path) -> list:
    """單引擎獨立監控:最後一次執行(rc · 何時 · 模式)· 輸出新鮮度 · 燈。"""
    import time
    logs = Path(home).parent / "_logs"
    out = []
    for r in book["engines"]:
        hits = sorted(logs.glob(f"{r['id']}_*.log"), key=lambda q: q.stat().st_mtime) if logs.is_dir() else []
        rc, when, mode = None, None, None
        if hits:
            txt = hits[-1].read_text(encoding="utf-8", errors="replace")
            m = re.findall(r"\[MDL008\] \S+ rc=(-?\d+)", txt)
            rc = int(m[-1]) if m else None
            when = round((time.time() - hits[-1].stat().st_mtime) / 3600, 1)
            mode = hits[-1].stem.rsplit("_", 1)[-1]
        ages = [round((time.time() - (Path(home) / o["path"]).stat().st_mtime) / 3600, 1) for o in r.get("outputs") or []
                if (Path(home) / o["path"]).is_file()]
        miss = missing_v0101(r)
        lamp = ("ABSENT" if miss else "NODATA" if rc is None else "RED" if rc in (1, 124) else
                "YELLOW" if rc in (2, 3, 4) or (ages and max(ages) > 36) else "GREEN")
        out.append({"id": r["id"], "mdl": r["mdl"], "group": r["group"], "lamp": lamp, "last_rc": rc, "last_run_h": when, "mode": mode,
                    "output_age_h": max(ages) if ages else None, "missing": miss})
    return out


def db_v0101(home: Path) -> dict:
    """接資料庫 + 最佳化:輸出根下所有 parquet 掛成 DuckDB 視圖(零複製);有代號欄的再出 k_ 鍵欄視圖
    (開頭 date · ticker · yf_ticker · bloomberg_ticker · name 取自兩份清單);temp 當溢寫記憶體;附最佳化報告。"""
    import duckdb
    home = Path(home)
    dbp = home / "vdf_fetch.duckdb"
    tmp = home / "_tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(dbp))
    con.execute(f"SET temp_directory='{tmp.as_posix()}'")
    con.execute("SET preserve_insertion_order=false")
    lists = [p for p in (home / "0-1-TWStockList" / "tw_stock_list_latest.parquet", home / "0-2-ActiveETFList" / "active_etf_list_latest.parquet") if p.is_file()]
    if lists:
        union = " UNION ALL BY NAME ".join(f"SELECT date, ticker, yf_ticker, bloomberg_ticker, name FROM read_parquet('{p.as_posix()}')" for p in lists)
        con.execute(f"CREATE OR REPLACE VIEW master_list AS {union}")
    views, keyed, files = [], [], []
    for p in sorted(home.rglob("*.parquet")):
        rel = p.relative_to(home)
        if rel.parts[0] in ("_tmp",) or "_archive" in rel.parts:
            continue
        name = re.sub(r"[^0-9A-Za-z_]", "_", "__".join(rel.with_suffix("").parts))[:120]
        con.execute(f"CREATE OR REPLACE VIEW v_{name} AS SELECT * FROM read_parquet('{p.as_posix()}')")
        views.append("v_" + name)
        meta = con.execute(f"SELECT COUNT(*) FROM read_parquet('{p.as_posix()}')").fetchone()[0]
        cols = [c[0] for c in con.execute(f"DESCRIBE SELECT * FROM read_parquet('{p.as_posix()}')").fetchall()]
        codec = con.execute(f"SELECT DISTINCT compression FROM parquet_metadata('{p.as_posix()}')").fetchall()
        files.append({"file": str(rel), "rows": meta, "bytes": p.stat().st_size, "codec": sorted({c[0] for c in codec})})
        tc = next((c for c in TICKER_COLS_V0101 if c in cols), None)
        if lists and tc and rel.parts[0] not in ("0-1-TWStockList", "0-2-ActiveETFList"):
            con.execute(f"CREATE OR REPLACE VIEW k_{name} AS SELECT m.date, m.ticker, m.yf_ticker, m.bloomberg_ticker, m.name, x.* "
                        f"FROM read_parquet('{p.as_posix()}') x LEFT JOIN master_list m "
                        f"ON regexp_replace(CAST(x.\"{tc}\" AS VARCHAR), '\\.(TW|TWO)$', '') = m.ticker")
            keyed.append("k_" + name)
    con.close()
    small = [f for f in files if f["bytes"] < 64 * 1024]
    plain = [f for f in files if f["codec"] and not set(f["codec"]) & {"ZSTD"}]
    advice = ["視圖不複製:每份 parquet 掛 v_ 視圖,DuckDB 只存目錄,省一倍空間、永遠是最新檔",
              "鍵欄 k_ 視圖:開頭 date · ticker · yf_ticker · bloomberg_ticker · name 取自 MDL009 / MDL010 清單(一份清單,所有表同一把鑰匙)",
              "清單表 DuckDB 增量:date + ticker 反連接,同日重跑零新列(省下載 · 省 API · 省時間)",
              "temp_directory = 輸出根/_tmp:大表 join / 排序溢寫到磁碟,記憶體不爆(操作員令:用 temp 當記憶體)",
              f"壓縮:{len(plain)} 份不是 ZSTD → 下次寫入改 compression='zstd'(通常再省 30–60%)",
              f"碎檔:{len(small)} 份 < 64 KB → AkShare 走 VAKE compact(合併分片 · 舊片入 _archive 不刪);其他引擎改月分區寫入"]
    return {"db": str(dbp), "views": len(views), "keyed_views": keyed, "master_list": bool(lists), "files": files, "advice": advice}


def integration_test_v0101(rows: list) -> dict:
    """MDL(fixture 網全鏈跑 + 輸出契約)· ENG 與 MDL011(各自離線自測,全封網)· 缺套件 ABSENT 照實 · 倉內零寫入。"""
    import tempfile
    before = PRIOR._git_dirty()
    with tempfile.TemporaryDirectory(prefix="vdf_fetch_it_") as tmp:
        home = Path(tmp) / "dict"
        mdl = [r for r in rows if r.get("test_mode") == "fixture"]
        eng = [dict(r, needs=[]) for r in rows if r.get("test_mode") == "block" and r.get("test_args")]
        runs = run_v0101(mdl, "fixture", home, logs=Path(tmp) / "_logs", timeout=900)
        ver = PRIOR.verify(mdl, home)
        tests = run_v0101(eng, "block", Path(tmp) / "eng_dict", logs=Path(tmp) / "_logs", args_key="test_args", timeout=900)
        try:
            dbrep = db_v0101(home)
        except Exception as exc:
            dbrep = {"error": f"{type(exc).__name__}: {exc}"}
    leaked = sorted(x for x in PRIOR._git_dirty() - before if "functional modules/VDF/" in x or "C:\\" in x)
    ok_runs = all(x["rc"] == 0 for x in runs)
    ok_eng = all(x["rc"] in (0, 2, 3) for x in tests)
    return {"runs": runs, "verify": ver, "tests": tests, "db": dbrep, "repo_writes": leaked,
            "pass": ok_runs and all(v["ok"] for v in ver) and ok_eng and not leaked and bool(dbrep.get("keyed_views"))}


def _print_test_v0101(rep: dict) -> None:
    print(f"[VDF 擷取系統 · 整合測試 v0101] {'PASS' if rep['pass'] else 'FAIL'}")
    print("  ── MDL(fixture 離線網 · 全鏈)")
    for x in rep["runs"]:
        print(f"  [{'OK' if x['rc'] == 0 else 'rc' + str(x['rc'])}] {x['mdl']:8} {x['sec']:6.1f}s · {(x['tail'] or [''])[-1][:100]}")
    ok_v = sum(v["ok"] for v in rep["verify"])
    print(f"  [輸出] {ok_v}/{len(rep['verify'])} 檔合格")
    print("  ── ENG / MDL011(各自離線自測 · 全封網)")
    for x in rep["tests"]:
        lab = {0: "OK", 2: "NODATA", 3: "ABSENT"}.get(x["rc"], "rc" + str(x["rc"]))
        print(f"  [{lab:6}] {x['mdl'][:34]:34} {x['sec']:6.1f}s" + (f" · 缺 {','.join(x['absent'])}" if x.get("absent") else ""))
    d = rep["db"]
    print(f"  [資料庫] 視圖 {d.get('views')} · 鍵欄視圖 {len(d.get('keyed_views') or [])} · 主清單 {d.get('master_list')}" + (f" · {d['error']}" if d.get("error") else ""))
    print(f"  [倉內寫入] {len(rep['repo_writes'])} 檔" + ("" if not rep["repo_writes"] else " · " + " · ".join(rep["repo_writes"][:4])))


def child_v0101(eid: str, home: str, mode: str, argv: list) -> int:
    """同 v0100 child,但引擎在真的模組物件裡跑(sys.modules['__main__'] = 它):
    薄尾用 sys.modules[__name__] 自我引用時才會拿到自己(實測 ENG078 / ENG231 在 v0100 的 dict 命名空間裡撞 AttributeError)。"""
    import types
    row = next(r for r in load_book_v0101()["engines"] if r["id"] == eid)
    path = HERE / row["file"]
    home_p = Path(home)
    home_p.mkdir(parents=True, exist_ok=True)
    os.chdir(home_p)
    body, mains, n = PRIOR.compile_engine(path, home_p)
    if mode == "live" and not PRIOR.gate_open():
        print(f"[MDL008] {row['mdl']} GATED:鎖版網路工具雙閘未開 —— 零出網、零寫檔(不是壞掉)", flush=True)
        return 4
    fake = PRIOR.install_mode(mode)
    sys.argv = [str(path), *argv]
    sys.path.insert(0, str(path.parent))
    mod = types.ModuleType("__main__")
    mod.__file__ = str(path)
    g = mod.__dict__
    g["__builtins__"] = __builtins__
    keep_main = sys.modules.get("__main__")
    print(f"[MDL008] {row['mdl']} {row['file']} · 舊路徑改寫 {n} 處 → {home_p} · 網路 {mode}", flush=True)
    rc = 0
    try:
        g["__name__"] = "__vdf_fetch_body__"
        sys.modules["__vdf_fetch_body__"] = mod
        exec(body, g)
        if fake is not None:
            g["_via_net"] = lambda: fake
        g["__name__"] = "__main__"
        sys.modules["__main__"] = mod
        exec(mains, g)
    except SystemExit as e:
        rc = e.code if isinstance(e.code, int) else (0 if e.code in (None, "") else 1)
    except Exception as e:
        print(f"[MDL008] 例外 {type(e).__name__}: {e}", flush=True)
        rc = 1
    finally:
        if keep_main is not None:
            sys.modules["__main__"] = keep_main
    print(f"[MDL008] {row['mdl']} rc={rc} · 網路計數 {json.dumps(PRIOR.FIX_STATS, ensure_ascii=False)}", flush=True)
    return rc


def _install_v0101() -> None:
    PRIOR.load_book = load_book_v0101
    PRIOR._fix_route = fix_route_v0101
    PRIOR.run = run_v0101


def _restore_v0100() -> None:
    PRIOR.load_book, PRIOR._fix_route, PRIOR.run = _LOAD_BOOK_V0100, _FIX_ROUTE_V0100, _RUN_V0100


_install_v0101()


def entry_ok_v0101() -> str:
    """回入口來源('VDFSM' / 'VCGC');空字串 = 沒有核准的入口。"""
    if os.environ.get(ENTRY_VDFSM) == "YES":
        return "VDFSM"
    if os.environ.get("VIA_FROM_VCGC") == "YES":
        return "VCGC"
    return ""


@contextlib.contextmanager
def _approved_call_v0101():
    """只在這一次呼叫內讓 v0100 的入口檢查看到已核准;結束還原(不留在環境裡)。"""
    had = "VIA_FROM_VCGC" in os.environ
    keep = os.environ.get("VIA_FROM_VCGC")
    os.environ["VIA_FROM_VCGC"] = "YES"
    try:
        yield
    finally:
        if had:
            os.environ["VIA_FROM_VCGC"] = keep
        else:
            os.environ.pop("VIA_FROM_VCGC", None)


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] == ["_child"]:                         # 子行程協定(父行程已過入口);v0101 用真模組物件跑
        i = args.index("--") if "--" in args else len(args)
        return child_v0101(args[1], args[2], args[3], args[i + 1:])
    if args == ["--selftest"]:
        return selftest()
    if not entry_ok_v0101():
        print(f"[VDF_MDL008] 拒絕。VDF 擷取系統由 VDF System Manager 總控:"
              f"python \"functional modules/VDF/VDF_SystemManager_v0128.py\" fetch {' '.join(args) or 'list'}(VCGC 也可呼叫)")
        return 2
    verb = args[0] if args else "list"
    rest = args[1:]
    home = PRIOR.home_dir(rest[rest.index("--home") + 1] if "--home" in rest and rest.index("--home") + 1 < len(rest) else None)
    book = load_book_v0101()
    if verb == "list":
        grp = rest[rest.index("--group") + 1] if "--group" in rest and rest.index("--group") + 1 < len(rest) else None
        if grp and grp not in GROUPS_V0101:
            print(f"[拒跑] {TAG}:--group 只收 {' · '.join(GROUPS_V0101)}")
            return 2
        rows = list_v0101(book, grp)
        if "--json" in rest:
            print(json.dumps({"vdf_fetch_system": rows, "groups": GROUPS_V0101}, ensure_ascii=False))
        else:
            print(f"[VDF 擷取系統] 總控 VDF_SystemManager · 冊 {BOOK_V0101.name} · {len(rows)} 支 · 第一步 MDL009 全台股 · MDL010 主動式 ETF")
            for g in GROUPS_V0101:
                gr = [r for r in rows if r["group"] == g]
                if gr:
                    print(f"  ── {g}({len(gr)})")
                for r in gr:
                    print(f"   {'✓' if r['exists'] else '✗'} {r['id']:7} {r['mdl'][:34]:34} {'缺 ' + ','.join(r['missing']) if r['missing'] else ''} {r['doc'][:60]}")
        return 0 if all(r["exists"] for r in rows) else 1
    if verb == "card":
        hit = [r for r in book["engines"] if rest and r["id"] in (rest[0], rest[0].replace("MDL", "0").lower())] or \
              [r for r in book["engines"] if rest and rest[0].upper().replace("VDF_", "") in r["mdl"].upper()]
        if len(hit) != 1:
            print(f"[拒跑] {TAG}:card 要給一支(id 或 MDL / ENG 號);命中 {len(hit)}")
            return 2
        c = card_v0101(hit[0])
        print(json.dumps({"engine_card": c}, ensure_ascii=False, indent=None if "--json" in rest else 1))
        return 0
    if verb == "status":
        st = status_v0101(book, home)
        if "--json" in rest:
            print(json.dumps({"fetch_status": st}, ensure_ascii=False))
        else:
            print(f"[VDF 擷取系統 · 單引擎監控] 輸出根 {home}")
            for x in st:
                print(f"  [{x['lamp']:6}] {x['id']:7} {x['mdl'][:30]:30} {x['group']:10} rc {x['last_rc']} · 上次 {x['last_run_h']} h 前 {x['mode'] or ''}"
                      f" · 輸出 {x['output_age_h']} h" + (f" · 缺 {','.join(x['missing'])}" if x["missing"] else ""))
        return 1 if any(x["lamp"] == "RED" for x in st) else 0
    if verb == "db":
        try:
            rep = db_v0101(home)
        except ImportError:
            print(f"[ABSENT] {TAG}:duckdb 不在本直譯器(不代裝)")
            return 3
        print(json.dumps({"vdf_fetch_db": rep}, ensure_ascii=False) if "--json" in rest else
              "\n".join([f"[VDF 擷取系統 · 資料庫] {rep['db']} · 視圖 {rep['views']} · 鍵欄視圖 {len(rep['keyed_views'])} · 主清單 {'有' if rep['master_list'] else '無(先跑 MDL009 / 010)'}"]
                        + ["  [最佳化] " + a for a in rep["advice"]]))
        return 0
    if verb == "test":
        with _approved_call_v0101():
            rep = integration_test_v0101(book["engines"])
        _print_test_v0101(rep)
        return 0 if rep["pass"] else 1
    with _approved_call_v0101():
        return PRIOR.main(args)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    _restore_v0100()
    try:
        rc0 = PRIOR.selftest()
    finally:
        _install_v0101()
    print(f"=== {TAG} · 薄尾自測(獨立運作 · 由 VDF System Manager 總控 · 第一步兩支清單引擎)===")
    chk("① v0100 自測過(冊 · 改寫 · 雙閘 · live 路由)", rc0 == 0, f"rc {rc0}")
    saved = {k: os.environ.pop(k, None) for k in (ENTRY_VDFSM, "VIA_FROM_VCGC")}
    try:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc_none = main(["list"])
            os.environ[ENTRY_VDFSM] = "YES"
            rc_sm = main(["list"])
            leaked = "VIA_FROM_VCGC" in os.environ
            os.environ.pop(ENTRY_VDFSM, None)
            os.environ["VIA_FROM_VCGC"] = "YES"
            rc_vc = main(["list"])
            os.environ.pop("VIA_FROM_VCGC", None)
        out = buf.getvalue()
        chk("② 沒有入口 → rc2 並指向 VDF 管理員總控;VDF 管理員標記 → rc0;VCGC 呼叫照收 rc0", rc_none == 2 and rc_sm == 0 and rc_vc == 0
            and "VDF System Manager 總控" in out, (rc_none, rc_sm, rc_vc))
        chk("③ 核准只在呼叫內:呼叫結束不留 VIA_FROM_VCGC 在環境裡", not leaked)
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    book = load_book_v0101()
    order = [r["id"] for r in PRIOR.ordered(book["engines"])]
    import ast as _ast
    miss = []
    for r in book["engines"]:
        defs = {(n.name, n.lineno) for n in _ast.walk(_ast.parse((HERE / r["file"]).read_text(encoding="utf-8", errors="replace")))
                if isinstance(n, (_ast.FunctionDef, _ast.AsyncFunctionDef))}
        miss += [f"{r['id']}:{f['name']}" for f in r["fetch_functions"] if (f["name"], f["line"]) not in defs]
    chk("⑤ 冊 v0101:第一步 = MDL009 全台股 · MDL010 主動式 ETF;MDL001–007 全部排在後面 · 擷取函式 AST 定位一致",
        order[:2] == ["009", "010"] and all(set(r["needs"]) >= {"009", "010"} for r in book["engines"][2:]) and not miss, (order[:3], miss))
    fx = fix_route_v0101("https://openapi.twse.com.tw/v1/opendata/t187ap47_L")
    chk("⑥ fixture 加 ETF 冊樣本(官方欄名)· 其他路由照 v0100", len(fx) == 5 and fx[0]["基金代號"] == "00981A"
        and fix_route_v0101("https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL") == _FIX_ROUTE_V0100("https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"))
    text = Path(__file__).read_text(encoding="utf-8")
    chk("④ 加速器橋 · 網路橋在;不碰 TA-Lib;不寫同意閘", "[VIA:ACCEL-BRIDGE" in text and "[VIA:NET-BRIDGE" in text
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M) and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", text))
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · v0100 {'PASS' if rc0 == 0 else 'FAIL'} · 合計 {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
