#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_ENG023_MDL011DailyFetcher v0100 — 薄尾:補 --selftest 門(VRN 鏈跑器量得到;正常執行一字不變)
自測查:本體檔在、語法樹可解析;入口 `_cli_main` 與類別 VRN_MDL011_DailyFetcher 的公開方法都在;
本體可安全載入(載入只做 import,零網路零寫檔;在暫存夾內進行);
再用合成輸入實跑純函式 `_validate_date` / `_shape_of` / `_to_yf_ticker` 退路 /
`fetch_daily_all` 未來日期早退(日期關卡在任何抓取之前,不碰網路)。
無版號原檔 VRN_ENG023_MDL011DailyFetcher.py 原封不動留作歷史(L04);本檔只是薄尾轉接。
"""
from __future__ import annotations
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

import __future__ as _fut
import ast
import importlib.util
import os
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEM = Path(__file__).stem.rsplit("_v", 1)[0]
BODY = HERE / (STEM + ".py")          # 本體 = 同夾無版號原檔(不釘版號)
_BODY_MOD = None
_NO_FORWARD = {"__path__", "__wrapped__"}


def _load_body():
    """惰性載入本體(本體頂層會載 pandas/yfinance/共用小工具正典,故不在 import 本尾時就載)。"""
    global _BODY_MOD
    if _BODY_MOD is None:
        name = "_via_body_" + STEM
        spec = importlib.util.spec_from_file_location(name, str(BODY))
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        try:
            spec.loader.exec_module(mod)
        except BaseException:
            sys.modules.pop(name, None)
            raise
        _BODY_MOD = mod
    return _BODY_MOD


def __getattr__(name: str):
    """PEP 562:本尾沒有的名字一律轉給本體(惰性載入)。"""
    if name in _NO_FORWARD:
        raise AttributeError(name)
    return getattr(_load_body(), name)


def _run_normal() -> None:
    """正常執行:與原檔 `if __name__ == "__main__": sys.exit(_cli_main())` 同一條路。"""
    sys.exit(_load_body()._cli_main())


def _isolated(tree: ast.Module, names: set, ns: dict) -> dict:
    """從本體語法樹只抽出指定的頂層定義,在隔離命名空間 exec(不跑本體其餘任何一行)。"""
    picked = []
    for nd in tree.body:
        if isinstance(nd, (ast.FunctionDef, ast.ClassDef)) and nd.name in names:
            picked.append(nd)
        elif isinstance(nd, ast.Assign) and any(isinstance(t, ast.Name) and t.id in names for t in nd.targets):
            picked.append(nd)
        elif isinstance(nd, ast.AnnAssign) and isinstance(nd.target, ast.Name) and nd.target.id in names:
            picked.append(nd)
    code = compile(ast.Module(body=picked, type_ignores=[]), str(BODY) + "#isolated", "exec",
                   flags=_fut.annotations.compiler_flag, dont_inherit=True)
    exec(code, ns)
    return ns


def _selftest() -> int:
    sys.dont_write_bytecode = True
    marks: list = []

    def chk(name: str, ok: bool, note: str = "") -> None:
        marks.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}" + (f" — {note}" if note else ""), flush=True)

    print(f"=== {STEM} v0100 自測(本體 {BODY.name})===", flush=True)
    # ① 本體在、語法樹可解析
    tree = None
    try:
        tree = ast.parse(BODY.read_text(encoding="utf-8"), filename=str(BODY))
        chk("本體檔在且語法樹可解析", True, f"{BODY.name}")
    except (OSError, SyntaxError) as exc:
        chk("本體檔在且語法樹可解析", False, f"{type(exc).__name__}: {exc}")
    if tree is None:
        print(f"  [計] {STEM} v0100 自測 {sum(marks)}/{len(marks)} · FAIL", flush=True)
        return 1

    # ② 入口與公開 API(語法樹層,不必載入)
    top_fn = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
    cls = next((n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "VRN_MDL011_DailyFetcher"), None)
    meths = {n.name for n in cls.body if isinstance(n, ast.FunctionDef)} if cls else set()
    need_m = {"__init__", "run", "fetch_daily_all", "_to_yf_ticker", "_resolve_batch",
              "_fetch_yf_prices", "_fetch_tw_chips"}
    chk("語法樹:類別 VRN_MDL011_DailyFetcher 與公開方法齊", cls is not None and need_m <= meths,
        "缺 " + ",".join(sorted(need_m - meths)) if need_m - meths else "7 個方法都在")
    main_calls = set()
    for nd in tree.body:
        if isinstance(nd, ast.If) and "__main__" in ast.dump(nd.test):
            main_calls = {c.func.id for c in ast.walk(nd) if isinstance(c, ast.Call) and isinstance(c.func, ast.Name)}
    chk("語法樹:入口 _cli_main 在,且原檔 __main__ 呼叫它", "_cli_main" in top_fn and "_cli_main" in main_calls,
        f"__main__ 呼叫 {sorted(main_calls)}")

    # ③ 安全載入本體(暫存夾當工作目錄;本體頂層只 import,零網路零寫檔)
    mod = None
    missing = ""
    old_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as td:
        os.chdir(td)
        try:
            mod = _load_body()
            chk("本體可載入且入口可呼叫", callable(getattr(mod, "_cli_main", None)),
                f"VERSION={getattr(getattr(mod, 'VRN_MDL011_DailyFetcher', None), 'VERSION', '?')}")
        except ModuleNotFoundError as exc:
            missing = exc.name or str(exc)
            print(f"  ModuleNotFoundError: No module named '{missing}'", flush=True)
            print(f"  [略] 載入本體需要 {missing}(缺件≠壞掉 L16);下列功能檢改走隔離命名空間", flush=True)
        except Exception as exc:
            chk("本體可載入且入口可呼叫", False, f"{type(exc).__name__}: {str(exc)[:160]}")
        finally:
            os.chdir(old_cwd)

    # ④ 功能檢:合成輸入 → 讀碼推得的期望值
    if mod is not None:
        ns = vars(mod)
        how = "已載入本體"
    else:
        ns = _isolated(tree, {"_validate_date", "_shape_of"},
                       {"datetime": datetime, "pd": None, "Dict": dict, "Optional": object})
        how = "隔離命名空間 exec 抽出原始碼(本體未載入)"
    vd = ns["_validate_date"]
    past = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
    got = (vd("20200230")["reason"].startswith("invalid_date:"), vd("29991231")["reason"],
           vd("19000101")["reason"], vd(past)["ok"])
    chk(f"_validate_date 四種日期({how})",
        got == (True, "date_in_future", "date_too_old", True), repr(got))
    so = ns["_shape_of"]
    got2 = (so([1, 2, 3]), so(None), so({"a": 1}))
    chk(f"_shape_of list/None/dict({how})",
        got2 == ({"type": "list", "len": 3}, None, {"type": "dict"}), repr(got2))
    if mod is not None:
        if getattr(mod, "pd", None) is not None:
            df = mod.pd.DataFrame({"a": [1, 2], "b": [3, 4]})
            got3 = so(df)
            chk("_shape_of DataFrame", got3 == {"type": "DataFrame", "shape": [2, 2], "columns": ["a", "b"]},
                repr(got3))
        else:
            print("  [略] _shape_of DataFrame 需要 pandas(缺件≠壞掉 L16)", flush=True)
        f = object.__new__(mod.VRN_MDL011_DailyFetcher)   # 不走 __init__:不建 MDL010 註冊表
        f.cfg = dict(mod._DEFAULTS)
        f._registry = None
        got4 = (f._to_yf_ticker("2330"), f._to_yf_ticker("AAPL"), f._resolve_batch(["2330"])[0]["meta"])
        chk("_to_yf_ticker / _resolve_batch 無註冊表退路",
            got4 == ("2330.TW", "AAPL", {"yf": "2330.TW"}), repr(got4))
        r = f.fetch_daily_all(["2330"], "29991231")
        chk("fetch_daily_all 未來日期在抓取前早退(不碰網路)",
            r.get("ok") is False and r.get("error") == "date_in_future" and r["meta"]["codes_in"] == 1,
            f"ok={r.get('ok')} error={r.get('error')}")
    else:
        print("  [略] _to_yf_ticker / _resolve_batch / fetch_daily_all 需要載入本體(上方缺件)", flush=True)

    k, n = sum(marks), len(marks)
    ok = k == n
    print(f"  [計] {STEM} v0100 自測 {k}/{n} · {'PASS' if ok else 'FAIL'}", flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv[1:]:
        sys.exit(_selftest())
    _run_normal()
