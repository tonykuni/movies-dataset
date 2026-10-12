#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_SystemManager v0156 — 薄尾:啟動就緒的短令檢查沿 Register 點源鏈讀(問參數頁「啟動器/鏈缺:Register via-vdffetch」假紅修正)

工作站實錄(2026-10-12 14:59 問參數頁):「啟動就緒 RED · 來源 VDF_SystemManager_v0155.py · [修] 這些是樹上的檔,不是設定:git pull…」。
根因:v0104 read_launch ④ 只讀 Register-VIA-Commands 尾版一檔找 `function global:via-vdffetch {` 等 16 個啟動短令;
  短令冊自 v0244 起是薄尾(`. (Join-Path $PSScriptRoot "…vNNNN.ps1")` 往回接),16 個短令全在 v0243 → 尾版單檔永遠找不到 → 假紅(容器也一樣)。
本版:v0104 本體代答前,把它的 `_src` 換成「Register 冊沿點源鏈讀」的讀器(尾版 → 前版 …;只讀不執行;防環;不是 Register 的檔照舊),
  判準不變(標記本身 `function global:<短令> {`);代答完還原。`all` 的 ready 步也走本版門(v0155 的 READY 指到本版)。
鏈的讀法 = VCGC 唯一入口控制 v0106 命令冊鏈讀的同一條正則(抄尺不抄程式;本檔不載 VCGC 程式,L120 三系統獨立)。
其餘(all · 問參數頁 · 子行程 · 不代設同意閘 · 零網路 · 不碰 TA-Lib)照 v0155。
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)。本檔零網路。"""
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

import contextlib
import importlib.util
import io
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA_ROOT = HERE.parents[1]
_STEM = "VDF_SystemManager"
TAG = "v0156"
BOOK_RX_V0156 = re.compile(r"^Register-VIA-Commands-v\d{4}\.ps1$")
DOT_RX_V0156 = re.compile(r"""^\s*\.\s*\(?\s*(?:Join-Path\s+\$PSScriptRoot\s+)?["']?(?:\$PSScriptRoot[\\/])?(Register-VIA-Commands-v\d{4}\.ps1)""", re.M)


def _vnum_v0156(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0156(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0156(p) < _vnum_v0156(__file__)), key=_vnum_v0156)
PRIOR = _load_v0156(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


# ---------------------------------------------------------------- Register 冊沿點源鏈讀(只讀不執行;防環)
def _read_text(p) -> str:
    try:
        return Path(p).read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def register_chain(book: Path) -> list:
    """短令冊 + 它沿 dot-source 往回接的每一本(尾版在前;同夾;只讀;互相點源也不會無限迴圈)。"""
    book = Path(book)
    out, seen, todo = [], set(), [book]
    while todo:
        p = todo.pop(0)
        key = p.name.lower()
        if key in seen or not p.is_file():
            continue
        seen.add(key)
        out.append(p)
        for name in DOT_RX_V0156.findall(_read_text(p)):
            q = p.parent / name
            if q.name.lower() not in seen:
                todo.append(q)
    return out


def register_chain_text(book: Path) -> str:
    return "\n".join(_read_text(p) for p in register_chain(book))


def _src_chain(p) -> str:
    """v0104 `_src` 的替身:Register 冊 → 整條鏈的文字;其他檔照舊讀單檔。"""
    q = Path(p) if p else None
    if q is not None and BOOK_RX_V0156.match(q.name):
        return register_chain_text(q)
    return _read_text(q) if q is not None else ""


def read_launch(probe: bool = False, environ=None) -> dict:
    """啟動就緒(只量不動手;同意閘永不代設):v0104 本體代答,但短令檢查沿 Register 點源鏈讀;本體缺席照 v0155 回 ABSENT。"""
    m, why = PRIOR._door_v0104()
    if m is None or not callable(getattr(m, "read_launch", None)):
        return PRIOR.read_launch(probe=probe, environ=environ)
    orig = getattr(m, "_src", None)
    m._src = _src_chain
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            r = m.read_launch(probe=probe, environ=environ)
    finally:
        if orig is not None:
            m._src = orig
    r = dict(r)
    r["via"] = TAG
    r["door"] = "v0104 本體代答(v0156;短令沿 Register 點源鏈讀)"
    return r


PRIOR.READY = read_launch          # v0155 `all` 的 ready 步走本版門(自測前版鏈時換回)


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args[:2]:
        return selftest()
    return PRIOR.main(args)


def selftest() -> int:
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

    print("=== %s %s · 薄尾自測(啟動就緒短令沿 Register 點源鏈讀)===" % (_STEM, TAG))
    td = Path(tempfile.mkdtemp(prefix="pv_vdf156_"))
    try:
        b1, b2, b3 = (td / ("Register-VIA-Commands-v%04d.ps1" % i) for i in (1, 2, 3))
        b1.write_text("function global:via-vdffetch {\n  param()\n}\n", encoding="utf-8")
        b2.write_text('. (Join-Path $PSScriptRoot "Register-VIA-Commands-v0001.ps1")\nfunction global:via-x {}\n', encoding="utf-8")
        b3.write_text('. (Join-Path $PSScriptRoot "Register-VIA-Commands-v0002.ps1")\n# 薄尾:這裡沒有 via-vdffetch\n', encoding="utf-8")
        ch = register_chain(b3)
        chk("① 鏈讀:尾版 v0003 → v0002 → v0001(尾版在前 · 只同夾 · 只讀)", [x.name for x in ch] == [b3.name, b2.name, b1.name], [x.name for x in ch])
        rx = re.compile(r"function global:" + re.escape("via-vdffetch") + r"\s*\{")
        chk("② 薄尾單檔找不到 via-vdffetch,沿鏈讀找得到(v0104 ④ 的同一條判準)",
            rx.search(_read_text(b3)) is None and rx.search(_src_chain(b3)) is not None)
        la, lb = td / "Register-VIA-Commands-v0010.ps1", td / "Register-VIA-Commands-v0011.ps1"
        la.write_text('. (Join-Path $PSScriptRoot "Register-VIA-Commands-v0011.ps1")\n', encoding="utf-8")
        lb.write_text('. (Join-Path $PSScriptRoot "Register-VIA-Commands-v0010.ps1")\n', encoding="utf-8")
        other = td / "Invoke-VIA-X-v0100.ps1"
        other.write_text("param()\n", encoding="utf-8")
        chk("③ 防環(互相點源 = 2 本)· 不是 Register 的檔照舊讀單檔 · 缺檔回空字串",
            len(register_chain(la)) == 2 and _src_chain(other) == "param()\n" and _src_chain(td / "nope.ps1") == "" and _src_chain(None) == "")
        rd = read_launch(probe=False)
        la_ = rd.get("launchers") or {}
        chk("④ 真樹:read_launch 由本版門代答,16 個啟動短令沿鏈全找到(cmds_missing 空)· why 不再含「Register via-vdffetch」· 同意閘只讀",
            str(rd.get("door", "")).startswith("v0104 本體代答(v0156") and la_.get("cmds", {}).get("via-vdffetch") is True and not la_.get("cmds_missing")
            and "Register via-vdffetch" not in str(rd.get("why", "")) and all(k in rd for k in ("state", "consent", "python", "hist_limit")),
            {k: rd.get(k) for k in ("state", "why", "door")} | {"missing": la_.get("cmds_missing")})
        m, _ = PRIOR._door_v0104()
        chk("⑤ 代答完 v0104 本體的 _src 還原(不留替身)· v0155 的 READY 指到本版門(all 的 ready 步走本版)",
            m is not None and getattr(m, "_src", None) is not _src_chain and PRIOR.READY is read_launch)
        buf = io.StringIO()
        keep_no_open = os.environ.get("VIA_NO_OPEN")
        os.environ["VIA_NO_OPEN"] = "1"
        try:
            with contextlib.redirect_stdout(buf):
                rc_dry = main(["all", "--dry", "--jobs", "9"])
        finally:
            if keep_no_open is None:
                os.environ.pop("VIA_NO_OPEN", None)
            else:
                os.environ["VIA_NO_OPEN"] = keep_no_open
        chk("⑥ all --dry 經本版 main 直通 v0155(列 9 步 · rc 0 · 不寫檔)", rc_dry == 0 and all(s in buf.getvalue() for s in PRIOR.STEPS_V0155), buf.getvalue()[:200])
        body = Path(__file__).read_text(encoding="utf-8")
        chk("⑦ 橋在(__future__ 之後)· 不碰 TA-Lib · 不代設同意閘 · 不載入 VCGC 程式 · 本檔不起子行程 · 零網路",
            all(x in body for x in ("[VIA:ACCEL-BRIDGE:v0100]", "[VIA:NET-BRIDGE:v0100]")) and body.index("from __future__") < body.index("[VIA:ACCEL-BRIDGE:v0100]")
            and "import " + "talib" not in body and 'environ["VIA_NET_' + 'CONSENT"] = "' not in body and "CGC_MDL" + "1" not in body
            and "import " + "subprocess" not in body and "url" + "lib" not in body and "req" + "uests" not in body)
    finally:
        shutil.rmtree(td, ignore_errors=True)
    print("  ── 前版鏈自測(原樣印出;VIA_SKIP_PRIOR_SELFTEST=1 略過)──")
    PRIOR.READY = PRIOR.read_launch          # 前版自測用它自己的門
    try:
        prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    finally:
        PRIOR.READY = read_launch
    chk("⑧ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    print("[計] %s_%s 自測 %d/%d · %s" % (_STEM, TAG, p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
