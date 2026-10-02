#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL224_TestAuto v0104 — 薄尾:AI 功能卡改讀尾版(盤點 card 與紀錄冊 book 不再釘死 v0100)

實測(2026-10-02,VCGC-REQ127「IMPLEMENT IT TO VCGC MAIN.」):v0101 的 discover() 與 items_now() 把
VIA_AI_FunctionCard_SSOT_v0100.json 寫死(PINVER):VCGC `functions` 早已照 glob 取尾版(v0101),串測卻還在核 v0100 ——
卡上新增的必用步(本批 `daily`)串測看不到,盤點冊替它登的覆蓋反被判 GONE = 紅。本尾版只換兩格(本體在自己命名空間呼叫):
  ① discover():card 改取 VIA_AI_FunctionCard_SSOT_v*.json 尾版的 must_use;其餘(動詞 · 座位 · 交接案 · 工作流 · PS · 家族)照本體。
  ② items_now():紀錄冊 book:VIA_AI_FunctionCard_SSOT 改記尾版的檔名 · 版號 · sha16(鍵不變;換版照只增記一筆)。
  交接冊 / 座位冊 v0100 是就地增的冊,照舊。其餘照 v0103(逐站落本機暫存 · 中斷接續)。零網路;不用 TA-Lib。
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

import importlib.util
import json
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = Path(__file__).stem
_STEM = "CGC_MDL224_TestAuto"
VNUM_RX = re.compile(r"[_-]v(\d+)$")
CARD_GLOB = "VIA_AI_FunctionCard_SSOT_v*.json"


def _vnum(path) -> int:
    m = VNUM_RX.search(Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + ENGINE, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def _body():
    m, seen = PRIOR, set()
    while m is not None and id(m) not in seen:
        seen.add(id(m))
        if all(callable(vars(m).get(n)) for n in ("discover", "items_now", "coverage")):
            return m
        m = vars(m).get("PRIOR")
    return None


BODY = _body()
_DISCOVER0 = BODY.discover
_ITEMS0 = BODY.items_now


def __getattr__(name: str):
    return getattr(PRIOR, name)


def card_path(via: Path):
    return BODY.newest(Path(via) / "supportive modules" / "registry", CARD_GLOB)


def discover(via: Path = BODY.VIA) -> dict:
    found = _DISCOVER0(via)
    p = card_path(via)
    card = (BODY._read_json(p, {}) or {}) if p is not None else {}
    found["card"] = {s.get("id"): s.get("cmd", "") for s in card.get("must_use") or [] if s.get("id")}
    return found


def items_now(via: Path, found: dict) -> dict:
    out = _ITEMS0(via, found)
    p = card_path(via)
    if p is not None:
        out["book:VIA_AI_FunctionCard_SSOT"] = {"kind": "book", "file": p.name, "version": "v%04d" % _vnum(p),
                                               "sha16": BODY.sha16(p)}
    return out


BODY.discover = discover                           # 本體 run / 自測 / v0102 的 PRIOR.discover 都經模組全域 → 走本版
BODY.items_now = items_now


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args:
        return selftest()
    return PRIOR.main(args)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)[:200]) if note and not cond else ''}")

    BODY.discover, BODY.items_now = _DISCOVER0, _ITEMS0   # 前版自測驗的是本體原裝:先還原,跑完再裝回本版
    try:
        rc = PRIOR.selftest()
    finally:
        BODY.discover, BODY.items_now = discover, items_now
    print(f"=== {ENGINE} · 薄尾自測(功能卡改讀尾版)===")
    with tempfile.TemporaryDirectory() as tmp:
        via = Path(tmp)
        reg = via / "supportive modules" / "registry"
        reg.mkdir(parents=True)
        (reg / "VIA_AI_FunctionCard_SSOT_v0100.json").write_text(json.dumps({"must_use": [{"id": "a", "cmd": "x"}]}), encoding="utf-8")
        (reg / "VIA_AI_FunctionCard_SSOT_v0102.json").write_text(
            json.dumps({"must_use": [{"id": "a", "cmd": "x"}, {"id": "daily", "cmd": "y"}]}), encoding="utf-8")
        found = discover(via)
        items = items_now(via, found)
        orig = _DISCOVER0(via)
    chk("① discover:card 取尾版 v0102(a · daily);本體原裝只看 v0100(a)",
        set(found.get("card") or {}) == {"a", "daily"} and set(orig.get("card") or {}) == {"a"}, (found.get("card"), orig.get("card")))
    book = items.get("book:VIA_AI_FunctionCard_SSOT") or {}
    chk("② items_now:紀錄冊記尾版檔名 · 版號(鍵不變)", book.get("file") == "VIA_AI_FunctionCard_SSOT_v0102.json"
        and book.get("version") == "v0102" and len(book.get("sha16", "")) == 16, book)
    chk("③ 本體的 discover / items_now 已換成本版;前版自測跑完換裝還在", BODY.discover is discover and BODY.items_now is items_now)
    real = card_path(BODY.VIA)
    want = {s.get("id") for s in ((BODY._read_json(real, {}) or {}).get("must_use") or []) if s.get("id")} if real else set()
    chk("④ 真樹:盤點 card = 功能卡尾版的必用步", real is not None and set(discover(BODY.VIA).get("card") or {}) == want,
        real.name if real else "ABSENT")
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑤ 加速器橋在;不碰 TA-Lib", "[VIA:ACCEL-BRIDGE" in text and not re.search(r"^\s*(import|from)\s+talib", text, re.M))
    print(f"  [{ENGINE}] 薄尾 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}")
    return rc if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
