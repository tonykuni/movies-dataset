#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_MDL009_TWStockList v0102 — 薄尾:網路工具橋補成 AST 真橋(模組層 VIA_NET_TOOL_PATH + def _via_net())

CGC_MDL230 工具覆蓋矩陣 ③「VDF 全件 · 網路工具橋」把 v0101 判「不一致」:標記在,但模組層沒有自己的 def _via_net()
(v0101 從前版抄進 globals,AST 讀不到)。操作員令「所有的 VDF 都要加最新的網路工具 · 100% 覆蓋」→ 本版只補正典 _via_net()
(與 v0100 逐字同一份:統包 via_net_unified 尾版 → SUP_MDL740 尾版 → 鎖冊 network),並把 fetch_json 的換網鏈接到本版
(MDL010 以本家族尾版為 CORE、MDL008 fixture 換的是尾版命名空間)。年區代碼中英文名稱局部識別 · 欄位聯集等全部照 v0101。
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

import json
import os
import re
import sys
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path

TAG = "VDF_MDL009_TWStockList v" + Path(__file__).stem.rsplit("_v", 1)[-1]
KEY_COLS = ("date", "ticker", "yf_ticker", "bloomberg_ticker", "name")
STATUSES = ("ACTIVE", "NEW", "DELISTED")
MASS_DELIST_MIN, MASS_DELIST_RATIO = 20, 0.05
SSOT_STOCK_RX = re.compile(r"^(?!0)(?!202[1-9])(?!2030)([1-9]\d{3})$")     # MDL001 鎖定律(全碼)
SRC = {"twse_quote": "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL",
       "twse_basic": "https://openapi.twse.com.tw/v1/opendata/t187ap03_L",
       "tpex_quote": "https://www.tpex.org.tw/openapi/v1/tpex_mainboard_daily_close_quotes",
       "tpex_basic": "https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap03_O"}
OUT_DIR, STEM, TABLE = "0-1-TWStockList", "tw_stock_list", "tw_stock_list"
MIN_DEFAULT = {"TWSE": 500, "TPEX": 300}


import importlib.util
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_MDL009_TWStockList"


def _vnum_v0102(p) -> int:
    m = re.search(r"_v(\d+)$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0102(p) < _vnum_v0102(__file__)), key=_vnum_v0102)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
for _n, _v in vars(PRIOR).items():                     # 共用核心 *_v0100 · v0101 的識別 / 聯集全部沿用
    if not _n.startswith("__") and _n not in globals():
        globals()[_n] = _v

TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"


def _forward_via_net_v0102():
    """前版的 _via_net 一律轉回本模組的 _via_net:fixture / MDL010 換的是尾版命名空間,v0101 的 run → collect 也要看得到。"""
    return globals()["_via_net"]()


PRIOR._via_net = _forward_via_net_v0102


def fetch_json_v0100(url: str):
    """同名接手:網路入口跟著本模組的 _via_net(MDL010 寫 CORE._via_net、fixture 換尾版命名空間都要生效)。"""
    keep = PRIOR._via_net
    PRIOR._via_net = globals()["_via_net"]
    try:
        return PRIOR.fetch_json_v0100(url)
    finally:
        PRIOR._via_net = keep


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"]:
        return selftest()
    PRIOR.TAG = TAG                                    # v0101 的 main / run_v0101 讀的是它自己的 TAG(再往下蓋 v0100)→ 報告與輸出記本版
    return PRIOR.main(args)


def selftest() -> int:
    import ast
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    rc0 = PRIOR.selftest()
    print(f"=== {TAG} · 薄尾自測(網路工具橋 AST 真橋 · 換網鏈)===")
    chk("① v0101 自測過(年區代碼中英文名稱局部識別 · 欄位聯集 · v0100 七項)", rc0 == 0, f"rc {rc0}")
    text = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(text)
    def _net_assign(n):
        return isinstance(n, ast.Assign) and any(getattr(t, "id", "") == "VIA_NET_TOOL_PATH" for t in n.targets)
    assign = any(_net_assign(n) or (isinstance(n, ast.Try) and any(_net_assign(s) for s in n.body)) for n in tree.body)
    fn = any(isinstance(n, ast.FunctionDef) and n.name == "_via_net" for n in tree.body)
    chk("② AST:模組層 VIA_NET_TOOL_PATH 指派 + def _via_net()(CGC_MDL230 ③ 真橋判準)", assign and fn)

    class _Net:
        def http_json(self, url, timeout=30):
            return {"state": "OK", "data": [{"probe": url}]}
    real = globals()["_via_net"]
    try:
        globals()["_via_net"] = lambda: _Net()
        st, data = fetch_json_v0100(SRC["twse_basic"])
    finally:
        globals()["_via_net"] = real
    try:
        globals()["_via_net"] = lambda: _Net()
        st2, data2 = PRIOR.fetch_json_v0100(SRC["twse_quote"])          # 經 v0101 的 run → collect 走的那一條
    finally:
        globals()["_via_net"] = real
    chk("③ 換網鏈:本模組 _via_net 換掉 → 本版與 v0101 的 fetch_json 都用到它(子行程 fixture / MDL010 換網生效);呼叫後還原",
        st == "OK" and data == [{"probe": SRC["twse_basic"]}] and st2 == "OK" and data2 == [{"probe": SRC["twse_quote"]}]
        and PRIOR._via_net is _forward_via_net_v0102)
    import contextlib
    import io
    import json
    import os
    import tempfile

    class _Net2:
        def http_json(self, url, timeout=30):
            d = {SRC["twse_quote"]: [{"Code": "2330", "Name": "台積電"}], SRC["tpex_quote"]: [{"SecuritiesCompanyCode": "6488", "CompanyName": "環球晶"}]}
            return {"state": "OK", "data": d.get(url, [])}
    keep_tag, keep_env = PRIOR.TAG, os.environ.get("VIA_FROM_VDFSM")
    with tempfile.TemporaryDirectory() as tmp:
        cwd = os.getcwd()
        try:
            globals()["_via_net"] = lambda: _Net2()
            os.environ["VIA_FROM_VDFSM"] = "YES"
            os.chdir(tmp)
            with contextlib.redirect_stdout(io.StringIO()) as out5:
                rc5 = main(["run", "--date", "2026-10-01", "--min", "1"])
            rep5 = json.loads((Path(tmp) / OUT_DIR / "verify_report.json").read_text(encoding="utf-8"))
        finally:
            os.chdir(cwd)
            globals()["_via_net"] = real
            PRIOR.TAG = keep_tag
            if keep_env is None:
                os.environ.pop("VIA_FROM_VDFSM", None)
            else:
                os.environ["VIA_FROM_VDFSM"] = keep_env
    chk("⑤ 經 main 跑:報告 engine 與輸出首行都記本版(不是 v0101;PR #444 Codex P2)",
        rc5 == 0 and rep5.get("engine") == TAG and out5.getvalue().startswith(f"[{TAG}]"), (rep5.get("engine"), out5.getvalue()[:40]))
    saved = {k: os.environ.pop(k, None) for k in ("VIA_FROM_VDFSM", "VIA_FROM_VCGC")}
    try:
        with contextlib.redirect_stdout(io.StringIO()) as buf:
            rc_x = main(["run"])
    finally:
        for k, v in saved.items():
            if v is not None:
                os.environ[k] = v
    chk("④ 沒有總控入口 → rc 2;共用核心 *_v0100 照出(MDL010 用);不碰 TA-Lib;不寫同意閘",
        rc_x == 2 and "VDF System Manager" in buf.getvalue() and all(callable(globals().get(n)) for n in
        ("entry_ok_v0100", "fetch_json_v0100", "keyed_row_v0100", "diff_v0100", "write_outputs_v0100", "load_previous_v0100", "lamp_v0100", "print_report_v0100"))
        and "[VIA:ACCEL-BRIDGE" in text and not re.search(r"^\s*(import|from)\s+talib", text, re.M)
        and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", text))
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · v0101 {'PASS' if rc0 == 0 else 'FAIL'} · 合計 {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
