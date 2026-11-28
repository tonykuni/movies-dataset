#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""CGC_MDL058_Lessons v0104 — 薄尾:自測不吃本機狀態(前版自測改在暫存帳上跑;本機帳的預載規則另列 INFO)

實錄(2026-11-28,交接閘 VCGC 紅列 lessons_lock):v0103 自測鏈到 v0101 的「預載規則完備」(t08)直接讀本機帳
VIA_Lessons_Ledger_v0100.json,要它有 ≥15 條 ROOT_CAUSE。這本帳是 .gitignore 的執行產物(只在各台機器上長),
容器裡那本只有 VCGC_FAIL 列、沒有操作員手記的根因規則 → 自測紅,而且會往真帳寫東西的風險也在。
CLAUDE.md 補強三:「自測一律在暫存夾造資料;這台剛好沒資料才會過 / 才會紅都不算」。
本版(v0103 以前一字不動):
  ① 自測時把帳指到暫存夾一本合成帳(15 條合成根因規則 · 只增旗標),跑 v0103 整條前版自測;跑完還原,真帳一個位元不動。
  ② 本機帳另列一行 INFO:讀得懂 · 只增旗標 · 根因規則幾條(容器多半 0 → 照實印,不當綠、不當紅;主機另驗)。
  操作員 2026-11-28「前版鏈比照裁定甲」:本版自測驗本版與直接前版 v0103(v0103 再帶它自己的鏈)。
其餘(簽名 · 重複出錯 · 鎖 · 原子寫入 · 報告)全照 v0103;ledger_lock · record_event 由本版明寫轉出(同一支)。零網路。
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

import hashlib
import importlib.util
import json
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEM = "CGC_MDL058_Lessons"


def _vnum(path: Path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location(STEM + "_prior_for_" + Path(__file__).stem, PRIOR)
_PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _PRIOR
_spec.loader.exec_module(_PRIOR)
_STORE = _PRIOR._STORE                     # v0101:LEDGER 住在這一層(v0103 的讀寫都看它)
ledger_lock = _PRIOR.ledger_lock           # 跨行程鎖照 v0103(本版明寫轉出;CGC_MDL224 ⑥ 認尾版有這把鎖)
record_event = _PRIOR.record_event
N_SYNTH = 15


def __getattr__(name: str):
    return getattr(_PRIOR, name)


def synth_ledger() -> dict:
    """合成帳:只增旗標 + 15 條根因規則(sig · cause · fix 都有、編號不重)。"""
    rules = [{"kind": "ROOT_CAUSE", "id": f"RC-T{i:02d}", "sig": f"synthetic-sig-{i}", "cause": f"synthetic-cause-{i}",
              "fix": f"synthetic-fix-{i}", "match": None, "source": "selftest"} for i in range(1, N_SYNTH + 1)]
    return {"schema": "VIA.Lessons.v1", "append_only": True, "entries": rules}


def real_ledger_info(path: Path | None = None) -> dict:
    """本機帳的現況(只讀):在不在 · 讀得懂 · 只增旗標 · 根因規則數 · 總列數。"""
    p = Path(path or _STORE.LEDGER)
    if not p.is_file():
        return {"present": False}
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return {"present": True, "readable": False, "why": type(exc).__name__}
    ents = d.get("entries") if isinstance(d, dict) else None
    if not isinstance(ents, list):
        return {"present": True, "readable": False, "why": "no entries"}
    return {"present": True, "readable": True, "append_only": d.get("append_only") is True, "entries": len(ents),
            "rules": sum(1 for e in ents if isinstance(e, dict) and e.get("kind") == "ROOT_CAUSE")}


def _digest(p: Path) -> str | None:
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None


def selftest() -> int:
    real = Path(_STORE.LEDGER)
    before = _digest(real)
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td) / "VIA_Lessons_Ledger_v0100.json"
        tmp.write_text(json.dumps(synth_ledger(), ensure_ascii=False, indent=1), encoding="utf-8")
        _STORE.LEDGER = tmp
        try:
            rc = _PRIOR.selftest()               # v0103 整條前版鏈,帳在暫存夾
        finally:
            _STORE.LEDGER = real
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print(f"=== {STEM} v0104 薄尾加檢(自測不吃本機狀態)===")
    chk("① 前版 v0103 自測在暫存合成帳上過(簽名 · 重複出錯 · 只增 · 鎖 · 原子寫入 · 預載規則)", rc == 0, f"rc {rc}")
    chk("② 真帳一個位元不動、帳路徑已還原", _digest(real) == before and Path(_STORE.LEDGER) == real)
    s = synth_ledger()
    ids = [e["id"] for e in s["entries"]]
    chk("③ 合成帳:15 條根因規則 · 不重號 · sig/cause/fix 全有", len(ids) == N_SYNTH == len(set(ids))
        and all(e["sig"] and e["cause"] and e["fix"] for e in s["entries"]))
    chk("③ b 跨行程鎖與記錄照 v0103(ledger_lock · record_event 就是前版那兩支)",
        ledger_lock is _PRIOR.ledger_lock and record_event is _PRIOR.record_event)
    info = real_ledger_info()
    print(f"  [INFO] 本機帳(gitignored 執行產物,不進自測判定):{info}")
    text = Path(__file__).read_text(encoding="utf-8")
    chk("④ 加速器橋在且執行時載到 · 不碰 TA-Lib", "[VIA:ACCEL-BRIDGE" in text and VIA_ACCEL is not None
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M))
    print(f"  [計] CGC_MDL058 v0104 {sum(ok)}/{len(ok)} · 前版 {'PASS' if rc == 0 else 'FAIL'} · 合計 {'PASS' if rc == 0 and all(ok) else 'FAIL'}")
    return 0 if rc == 0 and all(ok) else 1


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        return selftest()
    return _PRIOR.main()


if __name__ == "__main__":
    raise SystemExit(main())
