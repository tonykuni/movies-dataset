#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL224_TestAuto v0106 — 薄尾:PS 站的「章在」驗整條點源鏈(尾版 + 它點源進來的前版),不只尾版那一支

實錄(2026-10-11 VCGC 全功能串測 P-ui_cmds 紅 rc 1「PS 入口少了串測步:function global:via-op-run · via-groups · via-duck · Get-VIAUiDbRoot」):
Register-VIA-Commands 自 v0270 起是 PS 薄尾——每版只加自己的短令,開頭一行 `. (Join-Path $PSScriptRoot "Register-VIA-Commands-v0274.ps1")`
接前版;站冊 P-ui_cmds 的 must 仍在鏈上(via-op-run · via-groups · via-duck 在 v0269,Get-VIAUiDbRoot 在 v0273),
v0101 的 ps_check 只讀尾版那一支的文字 → 永遠「少了」。
本版:ps_check 先照 v0105 挑站 deps 指的最新版號檔,再沿點源行(行首 `.` 接同夾 *.ps1)把鏈上每一支的文字接起來對 must;
章全在才交給 v0101 的 pwsh 語法檢(尾版那一支;沒 pwsh 照實黃);少章照舊 RED 並附鏈長。
鏈最多 64 支 · 同檔只讀一次(互相點源不迴圈)· 不在的檔略過不猜 · ABSENT 照前版。
v0101–v0105 一字不動(換裝進本體模組)。只收 VCGC 呼叫;零網路;不碰 TA-Lib。
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
# ===== [VIA:NET-BRIDGE:END] =====

import contextlib
import importlib.util
import io
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = Path(__file__).stem
_STEM = "CGC_MDL224_TestAuto"
CHAIN_LIMIT_V0106 = 64
# 點源行:行首 `.`(dot-source)後面同一行出現的第一個 *.ps1 檔名(Join-Path 形 · "$PSScriptRoot\x.ps1" 形 · 純相對形都認)
DOT_RX_V0106 = re.compile(r"(?m)^\s*\.\s+[^\r\n]*?([A-Za-z0-9_][A-Za-z0-9_.\-]*\.ps1)")


def _vnum_v0106(path) -> int:
    m = re.search(r"[-_]v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0106(p) < _vnum_v0106(__file__)), key=_vnum_v0106)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + ENGINE, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)          # v0105:PS 入口多支 · PS 站驗自己的檔
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BODY = PRIOR.BODY
_PS_CHECK_V0101 = PRIOR._PS_CHECK_V0101                 # 本體原版:尾版文字對 must + pwsh 語法檢
pick_ps_v0105 = PRIOR.pick_ps_v0105


def __getattr__(name: str):
    return getattr(PRIOR, name)


def ps_chain(path: Path, limit: int = CHAIN_LIMIT_V0106) -> list:
    """尾版 + 它點源進來的同夾 .ps1(遞迴;同檔一次;不在的略過;最多 limit 支)。"""
    out, seen, todo = [], set(), [Path(path)]
    while todo and len(out) < limit:
        p = todo.pop(0)
        if not p.is_file():
            continue
        key = p.resolve()
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
        text = p.read_text(encoding="utf-8", errors="replace")
        for m in DOT_RX_V0106.finditer(text):
            q = p.parent / m.group(1)
            if q.is_file() and q.resolve() not in seen:
                todo.append(q)
    return out


def ps_chain_text(path: Path) -> str:
    return "\n".join(q.read_text(encoding="utf-8", errors="replace") for q in ps_chain(path))


def ps_check(via: Path, rel: str, must: list) -> dict:
    """同 v0105 挑檔;章對整條點源鏈;章全在才做尾版 pwsh 語法檢(v0101)。"""
    try:
        _, inv = BODY.load_inventory(via)
    except Exception:
        inv = None
    st = next((s for s in (inv or {}).get("stations") or [] if s.get("kind") == "ps" and list(s.get("must") or []) == list(must or [])), None)
    if st and st.get("deps"):
        dep = st["deps"][0]
        p = pick_ps_v0105(via, dep if "*" in dep else dep[:-4] + "*.ps1")
        if p is not None:
            rel = p.name
    path = Path(via) / rel
    if not rel or not path.is_file():
        return _PS_CHECK_V0101(via, rel, must)                                   # ABSENT 照前版
    chain = ps_chain(path)
    text = "\n".join(q.read_text(encoding="utf-8", errors="replace") for q in chain)
    missing = [m for m in must if not re.search(m, text)]
    if missing:
        return {"lamp": "RED", "rc": 1, "last": "PS 入口少了串測步:" + " · ".join(missing) + f"(點源鏈 {len(chain)} 支都找過)"}
    res = _PS_CHECK_V0101(via, rel, [])                                          # 章全在 → 只做尾版語法檢(沒 pwsh 照實黃)
    res["last"] = f"{res.get('last', '')} · 章在點源鏈上({len(chain)} 支:{' → '.join(q.name for q in chain[:4])}{' …' if len(chain) > 4 else ''})"
    return res


BODY.ps_check = ps_check                                  # 本體 run 的 PS 站經模組全域 ps_check → 走本版(v0105 的換裝被本版蓋過)
PRIOR.ps_check = ps_check


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args:
        return selftest()
    return PRIOR.main(args)


def selftest() -> int:
    print(f"=== {ENGINE} · 薄尾自測(PS 站的章驗整條點源鏈)===")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = PRIOR.selftest()
    print("  ── 前版鏈自測(摘末行)── " + (buf.getvalue().strip().splitlines() or ["(無輸出)"])[-1])
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)[:220]) if note and not cond else ''}")

    chk("① 前版鏈自測過(v0105 → … → v0101);本版換裝還在(BODY.ps_check 是本版)", rc == 0 and BODY.ps_check is ps_check, f"rc {rc}")
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        (t / "Register-X-v0001.ps1").write_text("function global:via-alpha { 1 }\n", encoding="utf-8")
        (t / "Register-X-v0002.ps1").write_text('# tail\n. (Join-Path $PSScriptRoot "Register-X-v0001.ps1")\nfunction global:via-beta { 2 }\n', encoding="utf-8")
        (t / "Register-X-v0003.ps1").write_text('. "$PSScriptRoot\\Register-X-v0002.ps1"\nif (Test-Path $x) { . $x }\n. .\\Register-X-nothere.ps1\n', encoding="utf-8")
        names = [p.name for p in ps_chain(t / "Register-X-v0003.ps1")]
        text = ps_chain_text(t / "Register-X-v0003.ps1")
        chk("② 點源鏈:三種寫法都接到(Join-Path · $PSScriptRoot 反斜線 · 相對);不在的略過;章在前版也找得到",
            names == ["Register-X-v0003.ps1", "Register-X-v0002.ps1", "Register-X-v0001.ps1"] and "via-alpha" in text and "via-beta" in text, names)
        (t / "Register-Y-v0001.ps1").write_text('. (Join-Path $PSScriptRoot "Register-Y-v0002.ps1")\nfunction global:via-one { 1 }\n', encoding="utf-8")
        (t / "Register-Y-v0002.ps1").write_text('. (Join-Path $PSScriptRoot "Register-Y-v0001.ps1")\n. (Join-Path $PSScriptRoot "Register-Y-v0002.ps1")\n', encoding="utf-8")
        loop = [p.name for p in ps_chain(t / "Register-Y-v0002.ps1")]
        chk("③ 互相點源 / 點源自己不迴圈(同檔一次)", loop == ["Register-Y-v0002.ps1", "Register-Y-v0001.ps1"], loop)
        r_ok = ps_check(t, "Register-X-v0003.ps1", ["function global:via-alpha", "function global:via-beta"])
        r_no = ps_check(t, "Register-X-v0003.ps1", ["function global:via-alpha", "function global:via-gamma"])
        r_abs = ps_check(t, "Register-X-v0009.ps1", ["function global:via-alpha"])
        chk("④ ps_check:章散在鏈上 → 不是 RED(沒 pwsh 照實黃,有 pwsh 才綠)· 少一章 → RED 只點名少的那章並附鏈長 · 檔不在 → ABSENT 照前版",
            r_ok["lamp"] in ("GREEN", "YELLOW") and "少了" not in r_ok["last"] and "點源鏈上" in r_ok["last"]
            and r_no["lamp"] == "RED" and "via-gamma" in r_no["last"] and "via-alpha" not in r_no["last"] and "3 支" in r_no["last"]
            and r_abs["last"].startswith("ABSENT"), (r_ok["last"][:80], r_no["last"][:80], r_abs["last"][:40]))
    via = BODY.VIA
    _, inv = BODY.load_inventory(via)
    st = next((s for s in (inv or {}).get("stations") or [] if s.get("id") == "P-ui_cmds"), {})
    res = ps_check(via, "", st.get("must") or [])
    chk("⑤ 實樹 P-ui_cmds:Register-VIA-Commands 尾版的點源鏈把 v0269 / v0273 的章都接到 → 不是 RED(沒 pwsh 照實黃)",
        bool(st) and res["lamp"] in ("GREEN", "YELLOW") and "少了" not in res["last"] and "Register-VIA-Commands-v" in res["last"], res["last"][:160])
    src_text = Path(__file__).read_text(encoding="utf-8")
    chk("⑥ 加速器橋 · 網路橋在 · 不碰 TA-Lib · 不直派子行程", "[VIA:ACCEL-BRIDGE" in src_text and "[VIA:NET-BRIDGE" in src_text
        and not re.search(r"^\s*(import|from)\s+talib", src_text, re.M) and not re.search(r"^\s*(import|from)\s+sub" + "process", src_text, re.M))
    print(f"  [{ENGINE}] 薄尾 {sum(ok)}/{len(ok)} {'PASS' if all(ok) and rc == 0 else 'FAIL'}")
    return 0 if rc == 0 and all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
