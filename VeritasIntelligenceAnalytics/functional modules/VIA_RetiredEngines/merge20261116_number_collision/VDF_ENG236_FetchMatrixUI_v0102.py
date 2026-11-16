#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
VDF_ENG236_FetchMatrixUI v0102 — v0101 薄尾(v0101 一字不動):自測 ④「讀庫失敗 → 沿用快取」改成密封(不受這台機器有沒有庫影響)。

實錄(2026-11-13 容器全量實跑 VDF_SystemManager v0171 test:VDF_ENG236 FAIL rc 1):v0101 自測 11/12,只紅 ④ 第二項。
根因:④ 呼叫 table_columns(tmp) 沒指定庫家 → ENG237 照 DataHome 冊 / 倉內 output_hub 退路找到一本真庫(VDF_Universe.duckdb)→
  讀庫「成功」,根本沒走到「讀庫失敗 → 沿用快取」那條路;自測想驗的分支沒被執行,不是程式壞。
  在桌機(有完整庫)同樣會紅;在沒有任何庫的機器才會綠 = 自測結果跟機器狀態綁在一起(不密封)。
本版:前版自測照跑照印;紅的只有 ④ 那兩項時,用一個空的暫存夾當庫家(--home,走 ENG237 正常解析)重驗:
  ④a 庫家是空夾 → 不當掉 · 寫原因;④b 同一空庫家 + 快取檔 → 沿用快取並標快取時間。兩項都過 → 判過;還有別的紅 → 照實紅。
  table_columns / build / 頁面 / 算法一字不動;本機真庫讀到什麼照印(不藏)。
VDF 自己的引擎;零網路 · 不寫庫 · 不用 TA-Lib · 不寫同意閘。用法同 v0101:build [--out 夾] [--db-check F] [--json] · --selftest
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)。本版不出網。"""
    return None if VIA_NET_TOOL_PATH is None else VIA_NET_TOOL_PATH
# ===== [VIA:NET-BRIDGE:END] =====

import contextlib
import importlib.util
import io
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

VERSION = "0102"
TAG = "VDF_ENG236_FetchMatrixUI v" + VERSION
HERE = Path(__file__).resolve().parent
_STEM = "VDF_ENG236_FetchMatrixUI"


def _vnum(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_v0102", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    return getattr(PRIOR, name)


def sealed_cache_checks() -> list:
    """④ 密封重驗:空暫存夾當庫家(ENG237 照 --home 解析)→ 讀不到表;再放快取檔 → 沿用快取。回 [(名, 過?, 註)]。"""
    m = PRIOR.PRIOR.build_model(PRIOR.PRIOR.load_books(), None, None)
    row = [r for s in m["sections"] for r in s["rows"]][0]
    out = []
    tmp = Path(tempfile.mkdtemp(prefix="vdf_eng236_v0102_"))
    try:
        home = tmp / "empty_home"
        home.mkdir()
        nocache = PRIOR.table_columns(tmp, home=str(home))
        out.append(("④a 庫家是空夾 → 不當掉 · 沒有表 · 寫原因", nocache["cols"] == {} and bool(nocache["why"]), nocache.get("why")))
        (tmp / PRIOR.COLS_CACHE).write_text(json.dumps({"ts": "2026-11-01T00:00:00", "source": "庫 x",
                                                        "tables": [{"db": row["db"], "table": row["table"], "columns": ["date", "close"]}]}), encoding="utf-8")
        cached = PRIOR.table_columns(tmp, home=str(home))
        out.append(("④b 同一空庫家 + 快取檔 → 沿用快取(標快取時間)",
                    cached["cols"].get((row["db"], row["table"])) == ["date", "close"] and cached["source"].startswith("快取 2026-11-01"), cached.get("source")))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return out


def selftest() -> int:
    print("=== %s · 薄尾自測(④ 讀庫失敗 → 快取 改密封重驗;前版自測照跑照印)===" % TAG, flush=True)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = PRIOR.selftest()
    out = buf.getvalue()
    print(out, end="")
    fails = [ln.strip() for ln in out.splitlines() if "[FAIL]" in ln]
    only4 = bool(fails) and all("④" in ln and ("快取" in ln or "不當掉" in ln) for ln in fails)
    sealed = sealed_cache_checks()
    for name, good, note in sealed:
        print("  [%s] %s%s" % ("OK" if good else "FAIL", name, (" · " + str(note)[:160]) if note else ""), flush=True)
    seal_ok = all(g for _, g, _ in sealed)
    with tempfile.TemporaryDirectory(prefix="vdf_eng236_v0102_live_") as td:
        live = PRIOR.table_columns(Path(td))
    print("  [資訊] 本機真庫讀表(不判燈,照印):%s" % (live.get("source") or live.get("why")), flush=True)
    good = (rc == 0 and seal_ok) or (only4 and seal_ok)
    print("[計] %s · 前版 %s · ④ 密封 %s · 合計 %s" % (
        TAG, "PASS" if rc == 0 else ("只紅 ④(自測不密封)" if only4 else "FAIL"), "OK" if seal_ok else "FAIL", "PASS" if good else "FAIL"), flush=True)
    return 0 if good else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] == ["--selftest"]:
        return selftest()
    return PRIOR.main(a)


if __name__ == "__main__":
    sys.exit(main())
