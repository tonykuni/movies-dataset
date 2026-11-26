#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VDF_ENG074_FredMacroSSOT v0108 — 薄尾(v0100–v0107 一字不動):退役序列不擷取、不算失敗

操作員 2026-11-26 令「FRED 退役序列標記」。桌機實錄:190 條裡 27 條每一輪都列 PARKED(HTTP 400 Bad Request;多為 ISM / NAPM
等 FRED 已不提供的 id),[紅冊] 每次都亮,真正新壞掉的序列混在裡面看不出來。
本版讀 VDF 自己的退役冊 VDF_FredRetired_SSOT 尾版(同夾):
  · run 前把冊上的 fred_id 從序列清單拿掉(零請求),印「[退役] N 條」;
  · run 跑完(閘開才會跑到)把這些序列在序列冊記 RETIRED(不再是 PARKED → status 紅冊不再列它們);
  · 新動詞 retired:列退役冊(唯讀)。
要恢復:出退役冊新版把 id 拿掉。母冊 VIA_VDF_SSOT_b360(intake)不動;本體走法同 v0106 _impl(含 v0104 換上的 VCGC 掃描閘(MDL224))。
自測零網路(假本體);不設同意閘;不用 TA-Lib。
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
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VDF = HERE.parent
STEM = "VDF_ENG074_FredMacroSSOT"
TAG = f"{STEM} v0108"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(str(p)).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(f"{STEM}_prior_for_v0108", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def body_module(impl=None):
    """本體:先走 v0106 _impl(含 v0104 換上的 VCGC 掃描閘(MDL224));那條路載不起來(例如拿掉 VCGC 的副本)→ 退路:
    直接載本家族最新的本體檔(有 load_series · ssot_path 的那一版),用本體自己的閘(同判法:兩道都要 YES,沒同意照樣關)。"""
    try:
        return (impl or PRIOR._impl)(), "v0106 _impl"
    except Exception as exc:  # noqa: BLE001 — 跨系統退路(重工守門 R10)
        why = f"{type(exc).__name__}"
    for p in sorted(HERE.glob(STEM + "_v*.py"), key=_vnum, reverse=True):
        if _vnum(p) >= _vnum(__file__):
            continue
        src = p.read_text(encoding="utf-8", errors="replace")
        if "def load_series" in src and "def ssot_path" in src:
            sp = importlib.util.spec_from_file_location(f"{STEM}_body_fallback_v0108", p)
            m = importlib.util.module_from_spec(sp)
            sys.modules[sp.name] = m
            sp.loader.exec_module(m)
            return m, f"退路 {p.name}(_impl 載不起來:{why})"
    raise RuntimeError("找不到 FRED 本體")


def retired_book(book_dir: Path = VDF) -> tuple:
    hits = sorted(Path(book_dir).glob("VDF_FredRetired_SSOT_v*.json"), key=_vnum)
    if not hits:
        return {}, None
    try:
        d = json.loads(hits[-1].read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}, hits[-1].name
    return {s["fred_id"]: s for s in d.get("series") or [] if s.get("fred_id") and s.get("state", "RETIRED") == "RETIRED"}, hits[-1].name


def install(body, retired: dict, book: str | None) -> dict:
    """本體 load_series 換成「拿掉退役 id」的版本;回記錄(拿掉的 meta)。"""
    seen = {"dropped": [], "book": book}
    orig = body.load_series

    def load_series():
        series, src = orig()
        keep = [m for m in series if m.get("fred_id") not in retired]
        seen["dropped"] = [m for m in series if m.get("fred_id") in retired]
        if seen["dropped"]:
            print(f"  [退役] {len(seen['dropped'])} 條不擷取(冊 {book};零請求 · 不算 FAIL / PARKED)", flush=True)
        return keep, src
    body.load_series = load_series
    seen["orig"] = orig
    return seen


def mark_retired(body, seen: dict, retired: dict) -> int:
    n = 0
    for meta in seen.get("dropped") or []:
        try:
            body.upsert_registry(meta, "RETIRED", retired.get(meta.get("fred_id"), {}).get("reason", "RETIRED"))
            n += 1
        except Exception as exc:  # noqa: BLE001 — 序列冊寫不進照實說,不擋擷取結果
            print(f"  [註] 序列冊記 RETIRED 失敗:{type(exc).__name__}", flush=True)
            break
    return n


def main() -> int:
    a = sys.argv[1:]
    if a[:1] == ["--selftest"] or "--selftest" in a:
        return selftest()
    if a[:1] == ["retired"]:
        r, book = retired_book()
        print(f"[{TAG}] 退役冊 {book or '(沒有)'} · {len(r)} 條:" + " · ".join(sorted(r)))
        return 0
    body, how = body_module()
    if not how.startswith("v0106"):
        print(f"  [註] {how}", flush=True)
    retired, book = retired_book()
    seen = install(body, retired, book)
    try:
        rc = body.main()
    finally:
        body.load_series = seen["orig"]
    verb = body.parse_verb(a)[0] if callable(getattr(body, "parse_verb", None)) else "run"
    if verb == "run" and seen.get("dropped") and body.gate_open():
        n = mark_retired(body, seen, retired)
        print(f"  [退役] 序列冊記 RETIRED {n} 條", flush=True)
    return rc


def selftest() -> int:
    import tempfile
    import types
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f" · {str(note)[:300]}" if note and not cond else ""), flush=True)

    print(f"=== {TAG} · 薄尾自測(假本體;零網路)===", flush=True)
    chk("① 加速器真的載到(VIA_ACCEL is not None)", VIA_ACCEL is not None)
    chk("② 網路工具橋在位(載入不出網)", VIA_NET_TOOL_PATH is not None)
    real, book = retired_book()
    chk("③ 真冊:退役冊在、27 條(桌機 2026-11-26 實錄)", book and len(real) == 27 and "NAPM" in real, (book, len(real)))
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        (td / "VDF_FredRetired_SSOT_v0100.json").write_text(json.dumps({"series": [{"fred_id": "OLD", "reason": "r"},
                                                                                 {"fred_id": "KEEPME", "state": "ACTIVE"}]}), encoding="utf-8")
        r, b = retired_book(td)
        reg = []
        body = types.SimpleNamespace(load_series=lambda: ([{"fred_id": "OLD"}, {"fred_id": "CPI"}, {"fred_id": "KEEPME"}], "src"),
                                     upsert_registry=lambda meta, st, note="": reg.append((meta["fred_id"], st, note)))
        seen = install(body, r, b)
        got, _ = body.load_series()
        chk("④ 冊上的 id 從清單拿掉(state 不是 RETIRED 的列不算)· 其餘照舊", [m["fred_id"] for m in got] == ["CPI", "KEEPME"]
            and [m["fred_id"] for m in seen["dropped"]] == ["OLD"], got)
        n = mark_retired(body, seen, r)
        chk("⑤ 序列冊把退役的記 RETIRED(附理由)", n == 1 and reg == [("OLD", "RETIRED", "r")], reg)
        body.load_series = seen["orig"]
        chk("⑥ 跑完換回本體原 load_series", body.load_series()[0][0]["fred_id"] == "OLD")
        chk("⑦ 沒有退役冊 → 一條都不拿掉", retired_book(td / "none") == ({}, None))
    try:
        impl = PRIOR._impl()
        chk("⑧ 走得到本體(v0106 _impl:load_series · upsert_registry · main · gate_open 都在)",
            all(callable(getattr(impl, n, None)) for n in ("load_series", "upsert_registry", "main", "gate_open")))
    except Exception as exc:  # noqa: BLE001
        chk("⑧ 走得到本體", False, f"{type(exc).__name__}: {exc}")
    def boom():
        raise ImportError("VCGC 掃描閘不在")
    fb, how = body_module(boom)
    chk("⑧b 跨系統退路:_impl 載不起來(拿掉 VCGC)→ 改載本體、用本體自己的閘(沒同意 = 關)",
        how.startswith("退路") and callable(getattr(fb, "load_series", None)) and fb.gate_open({}) is False, how)
    import contextlib
    import io
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            rc_p = PRIOR.selftest()
    except Exception as exc:  # noqa: BLE001
        rc_p = 1
        print(f"  [註] 前版鏈自測丟例外:{type(exc).__name__}", flush=True)
    chk("⑨ 前版 v0107 自測照過(rc 0)", rc_p == 0, rc_p)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑩ 檔面:第 3 行加速器標記 · 雙橋 · glob 取前版 · 零 TA-Lib · 不設同意閘",
        src.splitlines()[2].startswith("# [VIA:ACCEL-BRIDGE") and "[VIA:NET-BRIDGE:v0100]" in src and "HERE.glob(STEM" in src
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M)
        and not re.search(r"^\s*os\.environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", src, re.M))
    print(f"[selftest] {TAG} {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}", flush=True)
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
