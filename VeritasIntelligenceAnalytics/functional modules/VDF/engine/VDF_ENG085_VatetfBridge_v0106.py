#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VDF_ENG085_VatetfBridge v0106 — VATETF 應用端正主橋(薄尾:接 SUP_MDL755 Polars 表格層守門 · 記憶體不足轉 temp)
操作員 2026-09-29「go on add polars to all necessary engines 記憶體不足可用temp替代用」。

v0105 → v0106(側線 2026-09-29 c;主線批號由併線的手指定 L25):
  量到的:全價表複製成 VATETF 暫存庫(CTAS 16 處)(必要引擎名冊 N2,SUP_MDL755 NECESSARY)。
  本尾版在本引擎行程裝 FRAME 守門(SUP_MDL755 VIAPolarsFrame;鎖冊 frame 優先,R20c):之後開的每條 DuckDB 連線 → 溢寫夾改到
  受管 temp(VIA_TEMP_ROOT 或系統 temp 下的 VIA_spill/,跑完即刪;當掉留下的由 sweep 清);檔案庫上限收到「當下可用記憶體 × 0.5」
  (下限 512 MiB;VIA_FRAME_MEM_FRACTION 可調),記憶體不足時 DuckDB 改寫 temp、不吃光 RAM;記憶體庫只換溢寫夾(表資料不能溢寫,
  收上限會 Out of Memory)。有 polars 的境,Polars 串流也寫同一夾(POLARS_TEMP_DIR)。
  本引擎的重活在 DuckDB 裡(全歷史重算 / 整表複製),受管 temp + 上限就是它的「記憶體不足轉 temp」;GROUP BY / 排序 / join 整段可溢寫,
  視窗函數不能全溢寫 —— 實量 1000 萬列在 256 MiB 照過,預算下限 512 MiB 有兩倍餘裕。
  子行程(Codex #369 P1):v0105 的 _INSPECT(全表 count / max)與 _PREPARE(整表 CTAS 複製)經 subprocess 在家族境的新直譯器跑,
  父行程的守門碰不到 → guard_children() 把守門段(CHILD_MARK)接在這兩段腳本開頭:子行程載同一支 FRAME 正典,自己量預算、
  自己開受管 temp、跑完自己刪。adapter 不接:它是收容件原樣,讀 _PREPARE 已縮好的暫存庫、整表讀成 Python 紀錄,DuckDB 上限管不到那段。
  其餘照 v0105 一字不動(thin tail;__getattr__ 轉接;CLI 原樣交 v0105 的 main())。零網路 · 不安裝。
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
# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(VDF 全導入令;惰性載入=import 時零網路、零行為變更) =====
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT;網路只認 AegisNexus);缺席回 None(誠實)"""
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
# ===== [VIA:FRAME-BRIDGE:v0100] Polars 表格層橋(操作員 2026-09-29 記憶體不足可用temp替代用;graceful) =====
VIA_FRAME_PATH = None
try:
    import json as _fb_json
    from pathlib import Path as _fb_Path
    _fb_p = _fb_Path(__file__).resolve()
    while _fb_p.parent != _fb_p:
        _fb_sup = _fb_p / "supportive modules"
        if (_fb_sup / "registry").is_dir():
            _fb_locks = sorted((_fb_sup / "registry").glob("VIA_ToolVersion_Lock_v*.json"))
            _fb_rel = ((_fb_json.loads(_fb_locks[-1].read_text(encoding="utf-8")).get("frame") or {}).get("path")
                       if _fb_locks else None)
            _fb_hit = (_fb_p.parent / _fb_rel) if _fb_rel else None
            if _fb_hit is None or not _fb_hit.is_file():
                _fb_tails = sorted(_fb_sup.glob("SUP_MDL755_VIAPolarsFrame_v*.py"))
                _fb_hit = _fb_tails[-1] if _fb_tails else None
            VIA_FRAME_PATH = str(_fb_hit) if _fb_hit else None
            break
        _fb_p = _fb_p.parent
except Exception:
    VIA_FRAME_PATH = None


def _via_frame():
    """Polars 表格層惰性載入(鎖冊 frame 優先,缺則尾版);缺席回 None(誠實,引擎照舊跑)"""
    if VIA_FRAME_PATH is None:
        return None
    try:
        import importlib.util as _fb_ilu
        import sys as _fb_sys
        _fb_mod = _fb_sys.modules.get("VIA_FRAME")
        if _fb_mod is None or getattr(_fb_mod, "__file__", None) != VIA_FRAME_PATH:
            _fb_spec = _fb_ilu.spec_from_file_location("VIA_FRAME", VIA_FRAME_PATH)
            _fb_mod = _fb_ilu.module_from_spec(_fb_spec)
            _fb_spec.loader.exec_module(_fb_mod)
            _fb_sys.modules["VIA_FRAME"] = _fb_mod
        return _fb_mod
    except Exception:
        return None
# ===== [VIA:FRAME-BRIDGE:END] =====

import importlib.util
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_ENG085_VatetfBridge"


def _vnum(path: Path) -> int:
    m = re.search(r"_v(\d+)$", path.stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    return getattr(PRIOR, name)


CHILD_MARK = "# [VIA:FRAME-CHILD:v0100]"
CHILD_SCRIPTS = ("_INSPECT", "_PREPARE")     # v0105 在家族境子行程跑的 DuckDB 腳本:盤點(全表 count / max)· 整表複製(CTAS)


def child_preamble(tag: str = _STEM + ".child") -> str:
    """子行程開頭段:載本行程解到的同一支 FRAME 正典,在子行程自己的直譯器裝 DuckDB 守門(預算與受管 temp 都由子行程自己量、自己刪)。
    載不到 / 裝不上 = 照前一版跑,因由寫 stderr(不寫 stdout:前一版只讀 stdout 最後一行的 JSON)。"""
    return (f"{CHILD_MARK} 前一版腳本原樣接在本段後面;本段只在子行程裝 FRAME 守門(Codex #369 P1)\n"
            "try:\n"
            "    import importlib.util as _vf_u, sys as _vf_s\n"
            f"    _vf_spec = _vf_u.spec_from_file_location('VIA_FRAME', {str(VIA_FRAME_PATH)!r})\n"
            "    _vf_m = _vf_u.module_from_spec(_vf_spec)\n"
            "    _vf_spec.loader.exec_module(_vf_m)\n"
            "    _vf_s.modules['VIA_FRAME'] = _vf_m\n"
            f"    _vf_g = _vf_m.install_duckdb_guard({tag!r})\n"
            "except Exception as _vf_x:\n"
            "    _vf_g = {'state': 'FAIL', 'why': type(_vf_x).__name__ + ': ' + str(_vf_x)[:160]}\n"
            "if _vf_g.get('state') not in ('ON', 'OFF'):\n"
            "    import sys as _vf_s\n"
            "    _vf_s.stderr.write('[VIA:FRAME-CHILD] 子行程守門沒裝上,照前一版跑:' + str(_vf_g.get('why') or _vf_g.get('state')) + '\\n')\n"
            f"{CHILD_MARK}:END\n")


def guard_children() -> dict:
    """v0105 的 _INSPECT / _PREPARE 經 subprocess 在家族境新直譯器跑,父行程的守門碰不到(Codex #369 P1)
    → 把守門段接在兩段腳本開頭。冪等;FRAME 缺席或閥關 = 不接(照前一版跑)。"""
    if VIA_FRAME_PATH is None:
        return {"state": "ABSENT", "why": "SUP_MDL755 VIAPolarsFrame 不在(橋解不到)"}
    if os.environ.get("VIA_FRAME_GUARD", "").strip().lower() in ("off", "0", "no", "false"):
        return {"state": "OFF", "why": "VIA_FRAME_GUARD=off(操作員關掉守門;子行程照 DuckDB 預設)"}
    pre = child_preamble()
    for name in CHILD_SCRIPTS:
        text = getattr(PRIOR, name)
        if not text.startswith(CHILD_MARK):
            setattr(PRIOR, name, pre + text)
    return {"state": "ON", "scripts": list(CHILD_SCRIPTS), "frame": VIA_FRAME_PATH}


def guard() -> dict:
    """本引擎行程的 DuckDB 守門 + 家族境子行程的守門(guard_children);FRAME 缺席 = 照前一版跑(誠實回 ABSENT,不擋)。"""
    fr = _via_frame()
    if fr is None:
        return {"state": "ABSENT", "why": "SUP_MDL755 VIAPolarsFrame 不在(橋解不到)"}
    kids = guard_children()
    return dict(fr.install_duckdb_guard(_STEM), children=kids)


def main() -> int:
    guard()
    return PRIOR.main()


_CHILD_PROBE = r'''
import json, os, sys, duckdb
p = json.loads(sys.argv[1])
con = duckdb.connect(p["db"])
fr = sys.modules.get("VIA_FRAME")
st = (fr.guard_state() if fr else None) or {}
out = {"pid": os.getpid(), "guard": st.get("state"), "spill": st.get("spill"), "budget": st.get("budget"),
       "temp": con.execute("SELECT current_setting('temp_directory')").fetchone()[0],
       "limit": con.execute("SELECT current_setting('memory_limit')").fetchone()[0]}
con.close()
print(json.dumps(out))
'''


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + note) if note else ''}")

    print(f"=== {Path(__file__).stem} · 薄尾自測(FRAME 守門開著,再串 {PRIOR_PATH.stem} 全部檢)===")
    saved = os.environ.get("VIA_TEMP_ROOT")
    saved_guard = os.environ.pop("VIA_FRAME_GUARD", None)    # 量的是守門本身:操作員關掉的閥先放開,結束還原
    sandbox = tempfile.mkdtemp(prefix="via_frame_tail_")
    os.environ["VIA_TEMP_ROOT"] = sandbox
    fr = _via_frame()
    chk("① FRAME 橋:解到 SUP_MDL755 VIAPolarsFrame(鎖冊 frame 優先,缺則尾版)並載得進來",
        fr is not None and callable(getattr(fr, "install_duckdb_guard", None)), Path(VIA_FRAME_PATH or "-").name)
    rc = 1
    try:
        g = guard()
        import duckdb
        c = duckdb.connect(os.path.join(sandbox, "t.duckdb"))
        tdir = c.execute("SELECT current_setting('temp_directory')").fetchone()[0]
        c.close()
        chk("② 守門開:本行程新開的 DuckDB 連線 → 溢寫夾在受管 temp(VIA_TEMP_ROOT/VIA_spill)下;前一版全部檢在守門下照跑",
            g.get("state") == "ON" and tdir == g.get("spill") and Path(tdir).parent.name == "VIA_spill", tdir)
        again = guard_children()                                  # 冪等:再接一次不疊
        wrapped = all(getattr(PRIOR, n).startswith(CHILD_MARK) and getattr(PRIOR, n).count(CHILD_MARK + " ") == 1
                      for n in CHILD_SCRIPTS)
        kid = PRIOR._family_json(child_preamble() + _CHILD_PROBE, {"db": os.path.join(sandbox, "child.duckdb")})
        lim = fr._limit_bytes(kid.get("limit")) if kid.get("limit") else None
        os.environ["VIA_FRAME_GUARD"] = "off"                     # 閥關:不再接;子行程(child_env 帶著閥)也不裝
        try:
            off = guard_children()
            kid_off = PRIOR._family_json(child_preamble() + _CHILD_PROBE, {"db": os.path.join(sandbox, "child_off.duckdb")})
        finally:
            os.environ.pop("VIA_FRAME_GUARD", None)
        chk("③ 子行程守門:v0105 的 _INSPECT(盤點)· _PREPARE(整表複製)開頭接上 FRAME 守門段(只接一次);家族境子行程開的 DuckDB 連線"
            " → 溢寫夾在受管 temp、檔案庫上限收到子行程自己量的預算;閥 VIA_FRAME_GUARD=off 子行程也聽(Codex #369 P1)",
            (g.get("children") or {}).get("state") == "ON" and again.get("state") == "ON" and wrapped
            and kid.get("guard") == "ON" and kid.get("pid") not in (None, os.getpid()) and kid.get("temp") == kid.get("spill")
            and Path(str(kid.get("temp"))).parent == Path(sandbox, "VIA_spill")
            and lim is not None and bool(kid.get("budget")) and lim <= kid["budget"] * 1.05
            and off.get("state") == "OFF" and kid_off.get("guard") is None and "VIA_spill" not in str(kid_off.get("temp")),
            (f"子行程 pid {kid.get('pid')} · 夾 {Path(str(kid.get('temp'))).name} · 上限 {kid.get('limit')} · 閥關 {off.get('state')}"
             if kid.get("guard") else str(kid)[:160]))
        rc = PRIOR.selftest()
    finally:
        if fr is not None:
            fr.uninstall_duckdb_guard()
        if saved is None:
            os.environ.pop("VIA_TEMP_ROOT", None)
        else:
            os.environ["VIA_TEMP_ROOT"] = saved
        if saved_guard is not None:
            os.environ["VIA_FRAME_GUARD"] = saved_guard
        spill = Path(sandbox, "VIA_spill")
        left = sorted(p.name for p in spill.glob("*")) if spill.is_dir() else []
        shutil.rmtree(sandbox, ignore_errors=True)
    chk("④ 收:守門卸下、父子行程的溢寫夾都刪乾淨(零足跡)", not left, ", ".join(left[:3]))
    print(f"  {Path(__file__).stem} 薄尾 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'} · 前一版 rc={rc}")
    return rc if all(ok) else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv[1:] else main())
