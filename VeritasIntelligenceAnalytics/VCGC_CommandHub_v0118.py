#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VCGC_CommandHub_v0118.py — 薄尾(前版一字不動;原分支 v0105 撞 main 的 v0105、v0117 又撞開著的 PR #740,照「號取 本機 ∪ origin/main ∪ 開著的 PR 最大值之上」改發本號):合併指令 via-nlp(NLP · layout · markdown 唯一入口)

操作員 2026-11-25:「NLP layout markdown 在倉內整合成一支 · 合併指令 · 只增不減 · 用 VCGC 工具完成」。
  via-nlp [動詞 …] → SUP_MDL866_VIAUnifiedNLPOrchestrator 尾版(v0110 起是三者唯一入口);不給動詞 = hub-status。
  常用:hub-status · normalize <文字> · html <檔> · md-blocks <檔> · gle-status;前版動詞(reconstruct · unified · scan …)原樣轉交。
  舊名 via-nlp-fusion / via-layout / via-markdown / via-md 併入 via-nlp(印「舊名 → 新名」後照跑)。
用法同 v0104 | --selftest
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

import contextlib
import importlib.util
import io
import re
import sys
from pathlib import Path

VERSION = "v0118"
FAMILY = "VCGC_CommandHub"
HERE = Path(__file__).resolve().parent


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(FAMILY + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
def _find_p2(m):
    """沿前版鏈找 v0102(指令冊 COMMANDS · sys 轉派 SYS_ENTRY 定義在那一層)。"""
    seen = []
    while m is not None and m not in seen:
        seen.append(m)
        if "COMMANDS" in vars(m) and "SYS_ENTRY" in vars(m):
            return m
        nxt = vars(m).get("PRIOR")
        m = nxt if hasattr(nxt, "__dict__") else None
    raise ImportError("前版鏈上找不到指令冊(v0102 的 COMMANDS / SYS_ENTRY)")


P2 = _find_p2(PRIOR)                  # v0102(指令冊 · sys 轉派在這)


def __getattr__(name):
    return getattr(PRIOR, name)


P2.SYS_ENTRY["NLP"] = ("SUP_MDL866_VIAUnifiedNLPOrchestrator", "hub-status", {})
if "via-nlp" not in P2.CMD:
    P2.COMMANDS.append({
        "name": "via-nlp", "group": "系統入口", "title": "NLP · layout · markdown 唯一入口", "target": ["sys", "NLP"],
        "plugin": "SUP_MDL866 尾版(後端 744 · 743 · 745)",
        "help": "三者整合成一支:hub-status(後端掛載狀況)· normalize <文字> · html <檔> · md-blocks <檔> · gle-status;"
                "前版動詞 reconstruct · unified · scan · semantic · intake 原樣可用。不給動詞 = hub-status。",
        "examples": ["via-nlp", "via-nlp normalize ＡＢＣ１２３", "via-nlp md-blocks <檔>"],
        "ask": [("動詞(Enter = hub-status)", "normalize ＡＢＣ", "{}")],
        "replaces": ["via-nlp-fusion", "via-layout", "via-markdown", "via-md"]})
    P2.CMD["via-nlp"] = P2.COMMANDS[-1]
    for old in P2.COMMANDS[-1]["replaces"]:
        P2.LEGACY[old] = "via-nlp"
    _spec_mod = P2.P0                                   # 頂部指令表只「加一列」,不整張重建(前版各層改過的說明照留)
    if not any(r[0] == "via-nlp" for r in _spec_mod.SHORT_COMMANDS_SPEC):
        _c = P2.COMMANDS[-1]
        _spec_mod.SHORT_COMMANDS_SPEC = list(_spec_mod.SHORT_COMMANDS_SPEC) + [(_c["name"], _c["group"], _c["title"], _c["plugin"][:14])]


def main(argv: list[str] | None = None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    return PRIOR.main(a)


def selftest() -> int:
    ok = bad = 0

    def chk(name, cond, note=""):
        nonlocal ok, bad
        ok += bool(cond)
        bad += not cond
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}", flush=True)

    chk("① via-nlp 在指令冊、導到 sys NLP", P2.CMD.get("via-nlp", {}).get("target") == ["sys", "NLP"])
    t = P2.find_tail("SUP_MDL866_VIAUnifiedNLPOrchestrator", [P2.CODE_ROOT])
    chk("② 入口尾版找得到且 ≥ v0110(三合一)", t is not None and _vnum(t) >= 110, f"({t.name if t else None})")
    chk("③ 舊名併入 via-nlp、不撞新名", all(P2.LEGACY.get(o) == "via-nlp" for o in ("via-nlp-fusion", "via-layout", "via-markdown", "via-md"))
        and not ({"via-nlp-fusion", "via-layout", "via-markdown", "via-md"} & set(P2.CMD)))
    with contextlib.redirect_stdout(io.StringIO()) as buf:
        P2.cmd_names(ps=True)
    chk("④ names --ps 帶出 via-nlp 與舊名對照", "via-nlp|via-nlp" in buf.getvalue() and "via-md|via-nlp" in buf.getvalue())
    rows = [r[0] for r in P2.P0.SHORT_COMMANDS_SPEC]
    chk("④b 頂部指令表只加 via-nlp 一列(前版說明照留)", rows.count("via-nlp") == 1)
    chk("⑤ 加速器橋執行時生效", VIA_ACCEL is not None)
    with contextlib.redirect_stdout(io.StringIO()) as pb:
        rc = PRIOR.selftest()
    tl = [l for l in pb.getvalue().splitlines() if "[計]" in l]
    chk("⑥ 前版自測", rc == 0, f"({tl[-1].strip() if tl else rc})")
    print(f"  [計] {FAMILY} {VERSION} 自測 OK {ok} · FAIL {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
