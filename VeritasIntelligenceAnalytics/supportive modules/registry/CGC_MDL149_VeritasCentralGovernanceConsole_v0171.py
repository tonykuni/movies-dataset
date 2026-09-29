#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL149_VeritasCentralGovernanceConsole v0171 — 薄尾:第一步紅時放行「修第一步」的動詞(Codex #366 P1)· val 動詞(三系統驗證 SSOT)

① Codex 審查(PR #366 P1):v0170 第一步紅(鎖檔不在 / 位元被改 / 實測不過)時,對**每一個**動詞都在呼叫前一版之前回 rc2——
   連卡上建議的修法 `via-vcgc tools activate token … --apply` 與 NLP 的啟用令也擋:修第一步的鑰匙被鎖在門裡,
   只能繞過 VCGC 手改鎖冊。本尾版:第一步紅時只放行修它的動詞——`tools`(狀態)與 `tools activate token|nlp …`
   (乾跑與 --apply 都放);第一行照印紅燈與「放行修第一步」,讓人知道現在是在修第一步。其他動詞照停;`tools activate`
   別家(加速器 / 網路 / LAYOUT)照停。`help` 不放:它走到 v0161 的步驟門一樣會被第一步擋——不把走不通的路列成放行。
   第一步綠時與 v0170 一字不差。
② val [check|show …] := run --family core CGC_MDL246_ValidationSSOT <動詞…>(操作員 2026-09-29「三個系統的validation logic
   result validation logic cross checking機制寫入ssot」;冊 VIA_Validation_SSOT 尾版)。照 v0170 先過第一步;事件照 v0168 記。
其餘照 v0170(thin tail;__getattr__ 轉接)。只收 VCGC 呼叫(VIA_FROM_VCGC=YES)。零網路 · 不安裝。
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
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL149_VeritasCentralGovernanceConsole"


def _vnum(path: Path) -> int:
    match = re.search(r"_v(\d+)$", path.stem)
    return int(match.group(1)) if match else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location("vcgc_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    return getattr(PRIOR, name)


REPAIR_FAMILIES = ("token", "nlp")
VAL_ENGINE = "CGC_MDL246_ValidationSSOT"


def repair_verb(args: list) -> bool:
    """第一步紅時也放行的動詞:tools(狀態)· tools activate token|nlp …。"""
    if not args or args[0] != "tools":
        return False
    return len(args) == 1 or (len(args) >= 3 and args[1] == "activate" and args[2] in REPAIR_FAMILIES)


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] == ["val"]:
        return PRIOR.main(["run", "--family", "core", VAL_ENGINE] + (args[1:] or ["check"]))
    if os.environ.get("VIA_FROM_VCGC") != "YES" or not repair_verb(args):
        return PRIOR.main(argv)
    card = PRIOR.first_step()
    if card is None or not card["token"]["missing"]:
        return PRIOR.main(argv)                          # 第一步綠:與 v0170 一字不差
    stream = sys.stderr if "--json" in args else sys.stdout
    print(card["ai_line"], file=stream)
    print("[第一步 紅] 放行修第一步的動詞:" + " ".join(args[:3]) + "(其他動詞照停,修好之後第一步轉綠)", file=stream)
    return PRIOR.PRIOR.main(args)                        # 跳過 v0170 的紅燈停,直接給前前版(tools 由 v0165 接)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + note) if note else ''}")

    import contextlib
    import io
    red = {"token": {"missing": ["read"], "activate_hint": ["via-vcgc tools activate token X --apply"]},
           "ai_line": "[第一步 · 省Token] 紅 5/6"}
    green = {"token": {"missing": []}, "ai_line": "[第一步 · 省Token] 已啟用 6/6"}
    calls = {"prior": [], "prior2": []}
    saved = (PRIOR.first_step, PRIOR.main, PRIOR.PRIOR.main, os.environ.get("VIA_FROM_VCGC"))

    def run(argv, card):
        calls["prior"].clear()
        calls["prior2"].clear()
        PRIOR.first_step = lambda: card

        def v0170_main(a=None):                          # v0170 的行為:紅 → 停 rc2;綠 → 交前前版
            calls["prior"].append(list(a or []))
            return 2 if card["token"]["missing"] and (a or [""])[0] != "token" else 0
        PRIOR.main = v0170_main
        PRIOR.PRIOR.main = lambda a=None: calls["prior2"].append(list(a or [])) or 0
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            rc = main(argv)
        return rc, buf.getvalue()

    try:
        os.environ["VIA_FROM_VCGC"] = "YES"
        rc1, out1 = run(["tools"], red)
        chk("① 第一步紅 + tools(狀態)→ 放行:直接交前前版(v0169 → v0165 接 tools),不經 v0170 的紅燈停;第一行照印紅燈",
            rc1 == 0 and calls["prior2"] == [["tools"]] and not calls["prior"] and "放行修第一步" in out1 and "紅" in out1)
        rc2, _ = run(["tools", "activate", "token", "CGC_MDL158_X_v0117.py", "--apply"], red)
        ok2 = rc2 == 0 and calls["prior2"] == [["tools", "activate", "token", "CGC_MDL158_X_v0117.py", "--apply"]]
        rc3, _ = run(["tools", "activate", "nlp", "SUP_MDL866_X_v0106.py"], red)
        chk("② 第一步紅 + tools activate token … --apply / tools activate nlp … → 放行(卡上建議的修法走得通)",
            ok2 and rc3 == 0 and len(calls["prior2"]) == 1)
        rc4, _ = run(["tools", "activate", "network", "VeritasAegisNexus_v1653.py", "--apply"], red)
        rc5, _ = run(["status"], red)
        rc5b, _ = run(["help"], red)
        chk("③ 負控 第一步紅 + 別家的 activate / status / help → 不放行,照 v0170 停(rc2,前前版一次都沒被叫)",
            rc4 == 2 and rc5 == 2 and rc5b == 2 and not calls["prior2"])
        rc6, _ = run(["tools"], green)
        chk("④ 第一步綠 + tools → 與 v0170 一字不差(交 v0170,不走放行路)", rc6 == 0 and calls["prior"] == [["tools"]] and not calls["prior2"])
        run(["val"], green)
        v1 = list(calls["prior"])
        run(["val", "show", "VDF"], green)
        chk("⑤ val → run --family core CGC_MDL246_ValidationSSOT check;val show VDF 參數原樣轉;照 v0170 先過第一步",
            v1 == [["run", "--family", "core", VAL_ENGINE, "check"]]
            and calls["prior"] == [["run", "--family", "core", VAL_ENGINE, "show", "VDF"]])
        os.environ.pop("VIA_FROM_VCGC", None)
        rc7, _ = run(["tools"], red)
        chk("⑥ 門:沒經 via-vcgc(沒有 VIA_FROM_VCGC)→ 不走放行路,交 v0170(它照舊擋)", calls["prior"] == [["tools"]] and not calls["prior2"])
    finally:
        PRIOR.first_step, PRIOR.main, PRIOR.PRIOR.main = saved[0], saved[1], saved[2]
        if saved[3] is None:
            os.environ.pop("VIA_FROM_VCGC", None)
        else:
            os.environ["VIA_FROM_VCGC"] = saved[3]
    passed = all(ok)
    print(f"  {Path(__file__).stem} selftest {sum(ok)}/{len(ok)} {'PASS' if passed else 'FAIL'}")
    if not passed:
        return 1
    return PRIOR.selftest()                              # 串前一版(格子只跑尾版,前版的檢不能掉)


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
