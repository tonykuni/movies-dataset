#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_ENG065_DbImport v0102 — 薄尾:匯入前先過亂碼問題解碼器(VDF_ENG235_MojibakeRepair)再合併匯入

操作員令(2026-10-12):「先把它修正為非亂碼 再回朔到擷取他的工具加上亂碼問題解碼器 解取實用一次 輸出實用一次」。
本引擎是 tw__<表>.parquet / gl__<表>.parquet 單元檔進 DuckDB 的那道門(檔名協定見 v0101)。本版在 run_import 之前:
  VIA_MOJIBAKE_FIX ≠ 0(預設開)→ 叫 ENG235 fix <資料夾> --apply --units-only:單元檔文字欄的可逆亂碼先修回正字
  (原檔備份到 <資料夾>/_pre_mojibake/;U+FFFD 不可逆者照實列出、不動),再照 v0101 匯入(anti-join 只補缺列、既有零觸碰)。
  ENG235 缺席 = 誠實印一行、照 v0101 直接匯入。VIA_MOJIBAKE_FIX=0 = 關掉(舊行為)。
其餘(檔名協定 · 雙庫路由 · upsert_select · 冪等)照 v0101。零網路。
用法:python3 VDF_ENG065_DbImport_v0102.py import <資料夾> | --selftest
[接回 main 修正 2026-10-20 · PR #546 審查 P1] 修復有任一檔失敗(ENG235 回 action=FAIL:重寫 parquet / 更新 DuckDB 炸了或列數核對不過)→
  不匯入、rc 1、印出哪幾檔與原因(原本丟掉修復報告照樣匯入,亂碼原樣進庫還回成功)。要硬匯入 = 操作員明示 VIA_MOJIBAKE_FIX=0。自測 ⑦。
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
# ===== [VIA:LIB-BRIDGE:v0100] 三庫正典橋(批597;缺席大聲拋,不 graceful) =====
import sys as _lb_sys
from functools import partial as _lb_partial
from pathlib import Path as _lb_Path
_lb_p = _lb_Path(__file__).resolve()
while _lb_p.parent != _lb_p:
    if (_lb_p / "supportive modules").is_dir():
        _lb_sys.path.insert(0, str(_lb_p / "supportive modules"))
        break
    _lb_p = _lb_p.parent
import VIA_LibCanon as _LIB          # 正典缺席=大聲拋,不假裝有(LL151)
# ===== [VIA:LIB-BRIDGE:END] =====
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
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEM = "VDF_ENG065_DbImport"
TAG = "v0102"


def _vnum(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
PRIOR = _load(PRIOR_PATH, STEM + "_prior_for_" + Path(__file__).stem)
_REPAIR = {"mod": None, "why": None}


def __getattr__(name):
    return getattr(PRIOR, name)


def _repair():
    """亂碼修復引擎尾版(同夾 VDF_ENG235_MojibakeRepair_v*.py);缺 = None 並記原因。"""
    if _REPAIR["mod"] is None and _REPAIR["why"] is None:
        hits = [p for p in HERE.glob("VDF_ENG235_MojibakeRepair_v*.py") if _vnum(p) >= 0]
        if not hits:
            _REPAIR["why"] = "VDF_ENG235_MojibakeRepair_v*.py 不在"
        else:
            try:
                _REPAIR["mod"] = _load(max(hits, key=_vnum), "mojibake_repair_for_" + TAG)
            except Exception as exc:
                _REPAIR["why"] = "ENG235 載入炸 %s: %s" % (type(exc).__name__, str(exc)[:80])
    return _REPAIR["mod"]


def pre_fix(folder) -> dict:
    """匯入前修單元檔(只動 <前綴>__<表>.parquet);回 ENG235 的報告(或 {state: OFF/ABSENT})。"""
    if os.environ.get("VIA_MOJIBAKE_FIX", "1") == "0":
        return {"state": "OFF", "note": "VIA_MOJIBAKE_FIX=0 → 不修,照 v0101 匯入"}
    m = _repair()
    if m is None:
        print("  [亂碼解碼器] %s → 照 v0101 直接匯入(誠實)" % _REPAIR["why"])
        return {"state": "ABSENT", "note": _REPAIR["why"]}
    rep = m.fix(folder, apply=True, backup_dir=folder, units_only=True)
    rep["state"] = rep.get("lamp")
    print("  [亂碼解碼器] ENG235 fix --apply --units-only · %s · 單元 %d · 已改 %d 值(檔 %d)· 不可逆 %d(照實,不猜)· 備份 %s/_pre_mojibake" % (
        rep.get("lamp"), len(rep.get("targets", [])), rep.get("changed_values", 0), rep.get("files_rewritten", 0), rep.get("unrecoverable", 0), folder))
    return rep


def run_import(folder: str, dbs=None) -> int:
    rep = pre_fix(folder)
    bad = [t for t in rep.get("targets") or [] if t.get("action") == "FAIL"]
    if bad:
        print("  [亂碼解碼器] 修復失敗 %d 檔 → 不匯入(免得原亂碼進庫);修好再跑,或操作員明示 VIA_MOJIBAKE_FIX=0 照舊匯入:%s" % (
            len(bad), " · ".join("%s(%s)" % (Path(t.get("file") or "?").name, t.get("why") or "?") for t in bad[:5])))
        return 1
    return PRIOR.run_import(folder, dbs)


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        return selftest()
    if args and args[0] == "import" and len(args) > 1:
        return run_import(args[1])
    print(__doc__)
    return 0


def selftest() -> int:
    import io
    import contextlib
    import shutil
    import tempfile
    p = f = 0

    def chk(name, cond, note=""):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s%s" % (name, (" · " + str(note)[:300]) if note else ""))

    print("=== %s %s · 薄尾自測(匯入前先修亂碼;暫存庫 · 零網路)===" % (STEM, TAG))
    import duckdb
    td = Path(tempfile.mkdtemp(prefix="pv_vdf065_"))
    keep_env = os.environ.get("VIA_MOJIBAKE_FIX")
    keep_out = os.environ.get("VIA_MOJIBAKE_OUT")
    os.environ["VIA_MOJIBAKE_OUT"] = str(td / "out")
    try:
        zh = ["台積電", "鴻海", "聯發科"]
        moj = [s.encode("cp950").decode("latin-1") for s in zh]

        def make(folder: Path):
            folder.mkdir(parents=True, exist_ok=True)
            con = duckdb.connect()
            con.execute("CREATE TABLE a(code VARCHAR, name VARCHAR, n INTEGER)")
            con.executemany("INSERT INTO a VALUES (?, ?, ?)", [("2330", moj[0], 1), ("2317", moj[1], 2), ("2454", moj[2], 3)])
            con.execute("COPY a TO '%s' (FORMAT PARQUET, COMPRESSION ZSTD)" % str(folder / "tw__demo.parquet").replace("'", "''"))
            con.close()
            return {"tw": folder / "vdf_tw_market.duckdb", "gl": folder / "vdf_global_market.duckdb"}

        chk("① ENG235 尾版載得到 · 前版鏈 = v0101", _repair() is not None and PRIOR_PATH.name == "VDF_ENG065_DbImport_v0101.py", _REPAIR["why"])
        f1 = td / "u1"
        dbs = make(f1)
        os.environ.pop("VIA_MOJIBAKE_FIX", None)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = run_import(str(f1), dbs)
        con = duckdb.connect(str(dbs["tw"]), read_only=True)
        got = [r[0] for r in con.execute("SELECT name FROM demo ORDER BY n").fetchall()]
        con.close()
        chk("② 預設開:匯入前單元檔亂碼修回正字 → DuckDB 表是正字 · 備份 _pre_mojibake 在 · rc 0 · 印 [亂碼解碼器] 行",
            rc == 0 and got == zh and (f1 / "_pre_mojibake" / "tw__demo.parquet").is_file() and "[亂碼解碼器]" in buf.getvalue(), (rc, got, buf.getvalue()[-200:]))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc2 = run_import(str(f1), dbs)
        con = duckdb.connect(str(dbs["tw"]), read_only=True)
        n = con.execute("SELECT COUNT(*) FROM demo").fetchone()[0]
        con.close()
        chk("③ 重跑冪等:再修 0 值 · anti-join 0 新增 · 列數不變", rc2 == 0 and n == 3 and "已改 0 值" in buf.getvalue(), buf.getvalue()[-200:])
        f2 = td / "u2"
        dbs2 = make(f2)
        os.environ["VIA_MOJIBAKE_FIX"] = "0"
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc3 = run_import(str(f2), dbs2)
        con = duckdb.connect(str(dbs2["tw"]), read_only=True)
        got3 = [r[0] for r in con.execute("SELECT name FROM demo ORDER BY n").fetchall()]
        con.close()
        chk("④ VIA_MOJIBAKE_FIX=0:不修,照 v0101 匯入(亂碼原樣進庫;舊行為)· 沒有備份夾", rc3 == 0 and got3 == moj and not (f2 / "_pre_mojibake").exists(), got3)
        f3 = td / "u3"
        dbs3 = make(f3)
        os.environ.pop("VIA_MOJIBAKE_FIX", None)

        class _FailRepair:
            @staticmethod
            def fix(folder, **kw):
                return {"lamp": "RED", "targets": [{"file": str(Path(folder) / "tw__demo.parquet"), "action": "FAIL", "why": "OSError: disk full"}],
                        "changed_values": 0, "files_rewritten": 0, "unrecoverable": 0}
        keep_rep = dict(_REPAIR)
        _REPAIR.update(mod=_FailRepair, why=None)
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                rc5 = run_import(str(f3), dbs3)
        finally:
            _REPAIR.clear()
            _REPAIR.update(keep_rep)
        chk("⑦ 修復失敗(ENG235 回 action=FAIL)→ 不匯入 · rc 1 · 庫檔沒建 · 印出失敗檔與原因",
            rc5 == 1 and not dbs3["tw"].exists() and "修復失敗 1 檔" in buf.getvalue() and "tw__demo.parquet(OSError: disk full)" in buf.getvalue(), (rc5, buf.getvalue()[-200:]))
        body = Path(__file__).read_text(encoding="utf-8")
        chk("⑤ 橋在(ACCEL · LIB · NET)· 零網路 · 不碰 TA-Lib · 不載 VCGC 程式 · 匯入正典仍是 upsert_select(前版)",
            all(x in body for x in ("[VIA:ACCEL-BRIDGE:v0100]", "[VIA:LIB-BRIDGE:v0100]", "[VIA:NET-BRIDGE:v0100]"))
            and all(x not in body for x in ("import " + "requests", "import " + "urllib", "import " + "talib", "CGC_MDL" + "1", "CGC_MDL" + "2")) and "upsert_select" in src_of_prior())
    finally:
        if keep_env is None:
            os.environ.pop("VIA_MOJIBAKE_FIX", None)
        else:
            os.environ["VIA_MOJIBAKE_FIX"] = keep_env
        if keep_out is None:
            os.environ.pop("VIA_MOJIBAKE_OUT", None)
        else:
            os.environ["VIA_MOJIBAKE_OUT"] = keep_out
        shutil.rmtree(td, ignore_errors=True)
    print("  ── 前版鏈自測(原樣印出;VIA_SKIP_PRIOR_SELFTEST=1 略過)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("⑥ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    print("[計] %s_%s 自測 %d/%d · %s" % (STEM, TAG, p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


def src_of_prior() -> str:
    return PRIOR_PATH.read_text(encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
