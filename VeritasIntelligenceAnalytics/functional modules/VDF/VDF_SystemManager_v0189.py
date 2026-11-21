#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF SystemManager v0189 — 薄尾(v0188 以前一字不動):monitor 的過期判斷改成「每一格看它自己用到的收據」(PR 712 Codex P2)

  v0188 的資料庫格取 DB_STATUS_MATRIX / DB_CHECK 裡「比較新」的那份算年齡,parquet 收據的年齡完全沒算 →
  只要一份收據剛更新,其餘已過期的證據也被標成新的、綠燈照留。本版:每一格取它用到的每份收據裡「最舊」的年齡;
  任一份超過 48 小時 → 綠降黃並標過期;格上寫最舊那份的時間。輸出驗證格本來就只看 VERIFY 一份,照 v0188。
  其餘(九格 · 唯讀動詞 · 鎖定模板頁 · 不出網 · 不寫別系統的檔)全照 v0188。用法同 v0188:monitor [--lanes N] [--json] · --selftest
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)。本版兩扇門都不出網。"""
    return None if VIA_NET_TOOL_PATH is None else VIA_NET_TOOL_PATH
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import json
import os
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
FAMILY = "VDF_SystemManager"
TAG = "VDF_SystemManager v0189"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0189", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
_FROM_RECEIPTS_V0188 = PRIOR.from_receipts


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def from_receipts(base: Path) -> dict:
    """每一格只看自己用到的收據;年齡取最舊那份;任一份過期 → 綠降黃。"""
    rows = _FROM_RECEIPTS_V0188(base)               # 燈與內容照 v0188 算
    stale_h = PRIOR.STALE_H
    srcs = {"OUTPUT_CHECK": ["VERIFY_latest.json"],
            "DB": ["DB_STATUS_MATRIX_latest.json", "DB_CHECK_latest.json", "VDF_PARQUET_VIEW_latest.json"]}
    for cell, names in srcs.items():
        r = rows.get(cell)
        if not r or r.get("lamp") == "GRAY":
            continue
        ages = [(n, PRIOR._rjson(base / n)[1]) for n in names if (base / n).is_file()]
        ages = [(n, a) for n, a in ages if a is not None]
        if not ages:
            continue
        oldest_n, oldest = max(ages, key=lambda x: x[1])
        line = re.sub(r" · 收據 \d+h 前( · 過期\(>\d+h\))?", "", r["line"])
        line += f" · 最舊收據 {oldest_n} {oldest:.0f}h 前"
        lamp = r["lamp"]
        if oldest > stale_h:
            line += f" · 過期(>{stale_h:.0f}h)"
            if lamp == "GREEN":
                lamp = "YELLOW"
        rows[cell] = dict(r, lamp=lamp, line=line, oldest_receipt=oldest_n, oldest_age_h=round(oldest, 1))
    return rows


PRIOR.from_receipts = from_receipts                # v0188 的 monitor 取模組全域 from_receipts → 換上本版


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] == ["--selftest"]:
        return selftest()
    PRIOR.TAG = TAG                                  # 畫面 / 收據 / 頁寫實際跑的尾版(自測時前版保留原名)
    return PRIOR.main(a)


def selftest() -> int:
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note and not cond else ''}")

    keep = PRIOR.from_receipts
    PRIOR.from_receipts = _FROM_RECEIPTS_V0188
    try:
        rc0 = PRIOR.selftest()
    finally:
        PRIOR.from_receipts = keep
    print(f"=== {TAG} · 薄尾自測(每一格看自己的收據年齡;暫存夾 · 零網路)===")
    chk("⓪ 直接前版 %s 自測過" % PRIOR_PATH.name, rc0 == 0, f"rc {rc0}")
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        (d / "VERIFY_latest.json").write_text(json.dumps({"lamp": "PASS", "rows_compared": 5, "mismatches": []}), encoding="utf-8")
        (d / "DB_STATUS_MATRIX_latest.json").write_text(json.dumps({"lamp": "GREEN", "db_found": 2, "db_total": 2, "tables": 3}), encoding="utf-8")
        (d / "DB_CHECK_latest.json").write_text(json.dumps({"lamp": "GREEN", "summary": {"GREEN": 3}}), encoding="utf-8")
        (d / "VDF_PARQUET_VIEW_latest.json").write_text(json.dumps({"lamp": "GREEN", "start": "202201", "end": "202611", "counts": {"book": 3}}), encoding="utf-8")
        r = from_receipts(d)
        chk("① 全部新鮮 → 輸出驗證綠 · 資料庫綠", r["OUTPUT_CHECK"]["lamp"] == "GREEN" and r["DB"]["lamp"] == "GREEN", r)
        old = time.time() - 72 * 3600
        os.utime(d / "DB_CHECK_latest.json", (old, old))
        r = from_receipts(d)
        chk("② 狀態矩陣剛更新 · db check 72h 前 → 資料庫降黃(不再被較新的那份蓋過)· 標最舊那份",
            r["DB"]["lamp"] == "YELLOW" and "DB_CHECK_latest.json" in r["DB"]["line"] and "過期" in r["DB"]["line"], r["DB"])
        now = time.time()
        os.utime(d / "DB_CHECK_latest.json", (now, now))
        os.utime(d / "VDF_PARQUET_VIEW_latest.json", (old, old))
        r = from_receipts(d)
        chk("③ 只有 parquet 收據過期 → 資料庫也降黃(v0188 完全沒算 parquet 年齡)", r["DB"]["lamp"] == "YELLOW"
            and "VDF_PARQUET_VIEW_latest.json" in r["DB"]["line"], r["DB"])
        chk("④ 輸出驗證只看 VERIFY 自己(別的收據過期不影響它)", r["OUTPUT_CHECK"]["lamp"] == "GREEN", r["OUTPUT_CHECK"])
        (d / "DB_CHECK_latest.json").write_text(json.dumps({"lamp": "RED", "summary": {"RED": 1}}), encoding="utf-8")
        chk("⑤ 紅照紅(過期只把綠降黃,不把紅洗成黃)", from_receipts(d)["DB"]["lamp"] == "RED")
    chk("⑥ 換裝:v0188 的 monitor 叫到的 from_receipts = 本版", PRIOR.from_receipts is from_receipts)
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    peer = [k for k in ("VIA_FROM_VCGC", "VIA_FROM_VRN") if re.search(r"environ(?:\[[\"']%s[\"']\]\s*=|\.setdefault\([\"']%s)" % (k, k), body)]
    chk("⑦ 系統獨立:不設他系統的入口旗標(本檔是 VDF 自己的入口;VCGC 只支援不干涉)", not peer, peer)
    chk("⑧ 加速器橋 · 網路橋在;不出網 · 不碰 TA-Lib", "[VIA:ACCEL-BRIDGE:v0100]" in src and "[VIA:NET-BRIDGE:v0100]" in src
        and "_via_net()." not in body and "talib" not in body.lower())
    pub = [n for n in dir(PRIOR) if not n.startswith("_") and callable(getattr(PRIOR, n, None))]
    chk("⑨ 尾版保有前版公開名稱(TAILAPI)", all(getattr(sys.modules[__name__], n, None) is not None for n in pub), f"{len(pub)} 支")
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
