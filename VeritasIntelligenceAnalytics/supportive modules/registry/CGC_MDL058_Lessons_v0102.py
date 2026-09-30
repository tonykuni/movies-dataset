#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""CGC_MDL058_Lessons v0102 — 薄尾:VCGC 中樞失敗事件自動進教訓帳 · 同一簽名再出現標「重複出錯」

操作員 R32:「all of the action and feedback through the hub will trigger … logging function with lesson learned engine」。
VCGC 主控台 v0168 起每個動作記事件;結果類 FAIL 的事件呼叫本支 record_event(ev):
  · 簽名 = 動詞 + 錯誤訊息正規化(拿掉時間 · 路徑 · 數字 · 雜湊),同一個坑不會開兩張單;
  · 帳目 kind=VCGC_FAIL,只增:第一次 = 新簽名;第二次起帶 repeat_of(第一筆 id)與 count —— 報告裡「重複出錯榜」一眼看到;
  · 修好後由操作員 / AI 用 --record 現象 --cause 根因 --fix 解法 記根因(同 v0100 手記規矩,三件齊才收)。
報告(無參數)在 v0101 的輸出後多印「VCGC 失敗事件 · 重複出錯榜」。其餘整支照 v0101(thin tail;__getattr__ 轉接)。
只收 VCGC 呼叫(VIA_FROM_VCGC=YES)的規矩照前一版。
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

import importlib.util
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEM = "CGC_MDL058_Lessons"


def _vnum(path: Path) -> int:
    m = re.search(r"_v(\d+)$", path.stem)
    return int(m.group(1)) if m else -1


PRIOR = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location(STEM + "_prior_for_" + Path(__file__).stem, PRIOR)
_PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _PRIOR
_spec.loader.exec_module(_PRIOR)
ENGINE = Path(__file__).stem


def __getattr__(name: str):
    return getattr(_PRIOR, name)


def signature(verb: str, error: str, rc) -> str:
    e = str(error or "")
    e = re.sub(r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}", "<ts>", e)
    e = re.sub(r"([A-Za-z]:)?[\\/][^\s'\"]+", "<path>", e)
    e = re.sub(r"\b[0-9a-f]{7,40}\b", "<sha>", e)
    e = re.sub(r"\d+", "<n>", e)
    return f"{verb} · rc={rc} · {e.strip()[:120] or '(無例外訊息)'}"


def record_event(ev: dict, save: bool = True) -> dict:
    ledger = _PRIOR.load_ledger()
    sig = signature(ev.get("verb"), ev.get("error"), ev.get("rc"))
    prior = [e for e in ledger["entries"] if e.get("kind") == "VCGC_FAIL" and e.get("sig") == sig]
    n = sum(1 for e in ledger["entries"] if e.get("kind") == "VCGC_FAIL") + 1
    row = {"kind": "VCGC_FAIL", "id": f"VF-{n:03d}", "sig": sig, "verb": ev.get("verb"), "args": ev.get("args"), "rc": ev.get("rc"),
           "head": ev.get("head"), "ts": datetime.now().strftime("%Y%m%d_%H%M%S"), "source": "vcgc-hub",
           "count": len(prior) + 1}
    if prior:
        row["repeat_of"] = prior[0]["id"]
    ledger["entries"].append(row)
    if save:
        _PRIOR.save_ledger(ledger)
    return {"id": row["id"], "sig": sig, "count": row["count"], "repeat": bool(prior)}


def repeat_board(entries: list) -> list:
    c = Counter(e.get("sig") for e in entries if e.get("kind") == "VCGC_FAIL")
    return [(s, n) for s, n in c.most_common() if n > 1]


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        return selftest()
    rc = _PRIOR.main()
    if "--record" not in a and "-h" not in a and "--help" not in a:
        ents = _PRIOR.load_ledger()["entries"]
        fails = [e for e in ents if e.get("kind") == "VCGC_FAIL"]
        board = repeat_board(ents)
        print(f"── VCGC 失敗事件 {len(fails)} 筆 · 重複出錯 {len(board)} 種 ──")
        for s, n in board[:10]:
            print(f"  ×{n} {s}")
    return rc


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    s1 = signature("run", "FileNotFoundError: C:\\x\\a_v0101.py at 2026-09-28 10:00:01 line 12", 1)
    s2 = signature("run", "FileNotFoundError: /tmp/b_v0200.py at 2026-09-29 11:11:11 line 99", 1)
    chk("簽名把時間 · 路徑 · 數字拿掉:同一個坑同一張單", s1 == s2, s1)
    store = {"schema": "VIA.Lessons.v1", "append_only": True, "entries": []}
    keep_load, keep_save = _PRIOR.load_ledger, _PRIOR.save_ledger
    _PRIOR.load_ledger, _PRIOR.save_ledger = (lambda: store), (lambda d: None)
    try:
        r1 = record_event({"verb": "run", "error": "KeyError: 'x'", "rc": 1})
        r2 = record_event({"verb": "run", "error": "KeyError: 'x'", "rc": 1})
        r3 = record_event({"verb": "status", "error": "", "rc": 1})
    finally:
        _PRIOR.load_ledger, _PRIOR.save_ledger = keep_load, keep_save
    chk("第一次 = 新簽名;第二次 = 重複出錯(帶 repeat_of、count 2)", not r1["repeat"] and r2["repeat"] and r2["count"] == 2
        and store["entries"][1]["repeat_of"] == store["entries"][0]["id"])
    chk("只增:三筆都在,原帳目不改", len(store["entries"]) == 3 and store["entries"][0]["count"] == 1)
    chk("重複出錯榜", repeat_board(store["entries"]) == [(r1["sig"], 2)])
    if not all(ok):
        return 1
    return _PRIOR.cmd_selftest()


if __name__ == "__main__":
    sys.exit(main())
