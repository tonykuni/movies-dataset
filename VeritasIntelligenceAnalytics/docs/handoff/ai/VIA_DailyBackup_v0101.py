#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VIA_DailyBackup v0101 — 薄尾(v0100 一字不動):check 不再對「沒有可驗證的檔」亮綠

操作員 2026-11-15:「整合全部測試收尾 VCGC」(附件 VCGC_RepairKit_v0100 的 backup_empty_reproduction:空範圍 → backup 0 檔 → check 仍 GREEN)。
沙盒重現(origin/main 355e2fa 的 docs/handoff/ai/VIA_DailyBackup_v0100.py):total = same + changed + missing = 0 時,
v0100 的判燈只看「zip 不符 / 缺檔比例 / 有變 / zip 不全 / git 前進」→ 全都不成立 → GREEN「備份完整 · 倉內 0 檔」。這是假綠。
本版只換 do_check 的判燈(其餘逐字照 v0100):
  · MANIFEST 裡可驗證的檔 = 0 → RED「備份 0 檔:沒有任何可驗證的檔 → 先 backup(範圍樣式全落空?)」
  · 有系統 0 檔,或 MANIFEST 記了 missing_patterns(範圍樣式一個檔都沒對到)→ 至少 YELLOW,列出系統與樣式數
  · 其餘照 v0100(RED / YELLOW 不會被本版降級)
不 import 他系統 · 零網路 · 不碰 TA-Lib · 不讀寫同意閘。用法同 v0100:backup | check | --selftest。
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
import importlib.util
import json
import sys
import time
from pathlib import Path

VERSION = "v0101"
HERE = Path(__file__).resolve().parent
PRIOR_NAME = "VIA_DailyBackup_v0100.py"
_spec = importlib.util.spec_from_file_location("VIA_DailyBackup_v0100", HERE / PRIOR_NAME)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules["VIA_DailyBackup_v0100"] = PRIOR
_spec.loader.exec_module(PRIOR)
_ORIG_CHECK = PRIOR.do_check
ENGINE = "VIA_DailyBackup " + VERSION


def _manifest(rec: dict):
    try:
        man = json.loads(Path(rec["manifest"]).read_text(encoding="utf-8"))
        if "systems" not in man:
            man = json.loads((Path(man.get("backup_dir", "")) / "MANIFEST.json").read_text(encoding="utf-8"))
        return man
    except (KeyError, OSError, ValueError):
        return None


def do_check(via: Path, out_root: Path, manifest_dir: Path) -> dict:
    rec = _ORIG_CHECK(via, out_root, manifest_dir)
    rec["engine"] = ENGINE
    if rec.get("lamp") == "RED" or "files" not in rec:
        return rec
    f = rec["files"]
    total = f.get("same", 0) + f.get("changed", 0) + f.get("missing", 0)
    man = _manifest(rec) or {}
    empty = sorted(k for k, s in (man.get("systems") or {}).items() if not s.get("count"))
    pats = {k: len(v) for k, v in (man.get("missing_patterns") or {}).items() if v}
    rec["coverage"] = {"verifiable_files": total, "empty_systems": empty, "missing_patterns": pats, "by": ENGINE}
    if total == 0:
        rec["lamp"] = "RED"
        rec["meaning"] = "備份 0 檔:MANIFEST 裡沒有任何可驗證的檔 → 先 backup(範圍樣式全落空?)· 不是「備份完整」"
    elif empty or pats:
        if rec["lamp"] == "GREEN":
            rec["lamp"] = "YELLOW"
            rec["meaning"] = "可開工 · 但:" + " / ".join(x for x in (
                ("%d 個系統 0 檔(%s)" % (len(empty), "·".join(empty)) if empty else ""),
                ("%d 個範圍樣式沒對到檔(%s)" % (sum(pats.values()), "·".join("%s %d" % kv for kv in sorted(pats.items()))) if pats else "")) if x)
        else:
            rec["meaning"] += " / 另:%d 個系統 0 檔 · %d 個範圍樣式沒對到檔" % (len(empty), sum(pats.values()))
    return rec


def install():
    PRIOR.do_check = do_check
    PRIOR.ENGINE = ENGINE


def selftest() -> int:
    import tempfile
    rc = PRIOR.selftest()                       # 前版自測用前版判燈(本版換裝前)
    install()
    ok = []

    def chk(n, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", n, (" · " + str(note)) if note else ""), flush=True)
    with tempfile.TemporaryDirectory(prefix="via_bk101_") as td:
        via = Path(td) / "VeritasIntelligenceAnalytics"; via.mkdir()
        out, md = via / PRIOR.BACKUP_ROOT_REL, via / PRIOR.MANIFEST_DIR_REL
        man = PRIOR.do_backup(via, out, md)
        old = _ORIG_CHECK(via, out, md)
        new = do_check(via, out, md)
        chk("ⓐ 空範圍:backup %d 檔 · v0100 check = %s(假綠重現)· 本版 = RED" % (man["total_files"], old.get("lamp")),
            man["total_files"] == 0 and old.get("lamp") == "GREEN" and new["lamp"] == "RED" and "0 檔" in new["meaning"])
        p = via / "supportive modules" / "registry" / "VIA_Policy_Laws_SSOT_v0100.json"; p.parent.mkdir(parents=True); p.write_text("{}", encoding="utf-8")
        time.sleep(1.1)                         # 備份夾以秒為名:同一秒第二次 backup 會撞名
        PRIOR.do_backup(via, out, md)
        part = do_check(via, out, md)
        chk("ⓑ 只有 1 檔:不再 GREEN → YELLOW · 列出 0 檔系統與沒對到的範圍樣式", part["lamp"] == "YELLOW" and part["coverage"]["verifiable_files"] == 1
            and part["coverage"]["empty_systems"] and part["coverage"]["missing_patterns"], part.get("meaning", "")[:120])
        p.write_text('{"x": 1}', encoding="utf-8")
        red = do_check(via, out, md)
        chk("ⓒ 前版判的黃 / 紅不被降級(檔變了 → 仍非綠)", red["lamp"] in ("YELLOW", "RED"))
    bad = len(ok) - sum(ok)
    print("[%s] VIA_DailyBackup %s --selftest · 本版 %d 項 · 不過 %d(v0100 rc %d)" % ("PASS" if not bad and rc == 0 else "FAIL", VERSION, len(ok), bad, rc), flush=True)
    return 0 if not bad and rc == 0 else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in argv or argv[:1] == ["selftest"]:
        return selftest()
    install()
    return PRIOR.main(argv)


if __name__ == "__main__":
    sys.exit(main())
