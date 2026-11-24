#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0290 — 薄尾(v0289 以前一字不動):help 不再印 v0269 原生處理器的舊表頭(PR #722 的 v0288 改發本號)

來源:PR #722(2026-11-22)的 VRN_SystemManager_v0288「hide the v0269 help block」。合併 main 時 main 已有 v0289(v0288 號當時被
  #722 佔用,所以 main 跳號發 v0289,它的前版是 v0287)。#722 的 v0288 若原樣併進來會插到現役尾版 v0289 底下(重工守門 R1 紅),
  而且 v0289 的 help 是直接從 v0287 重綁的,v0288 的清理會被蓋掉 —— 所以照「同名 / 插號以 main 為準,分支內容改發新版號」改發 v0290。
本版做的事與 #722 v0288 相同:操作員 2026-11-22「hide the v0269 help block」——
  help 先印現役尾版一行,接著 v0269 原生處理器那一塊:拿掉 v0269 舊表頭與「轉交前版 v0268」舊句,「標準動詞(本版)」改「標準動詞」,
  換一句不帶版號的轉交說明;rc 說明 · v0278 synchronizer 段 · v0270 以後的動詞表照舊。動詞一個都不少(help 涵蓋檢查照 v0286 的尺)。
  version / health / verbs 照 v0289 的做法(v0287 的函式原樣重綁,只把鏈頭換成本版);其餘動詞(含 v0289 的 bridges 語法樹)一律交給 v0289。
零網路 · 不碰 TA-Lib · 不讀寫同意閘 · 不替別的系統設入口旗標。自測:python VRN_SystemManager_v0290.py --selftest
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
import re
import sys
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
FAMILY = "VRN_SystemManager"
TAG = "VRN_SystemManager v%04d" % int(re.search(r"_v(\d{4})$", Path(__file__).stem).group(1))


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0290", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
# 顯示函式的本體是 v0287。v0289 也把重綁過的 cmd_health 掛在自己模組上,所以要找「函式本體真的寫在這個模組」的那一版
# (函式的全域表就是該模組自己的;重綁過的函式全域表是另一份字典)。
def _defines(m, name: str) -> bool:
    f = vars(m).get(name)
    return getattr(f, "__globals__", None) is vars(m)


P287 = next(m for m in PRIOR.chain_modules() if _defines(m, "cmd_health") and _defines(m, "health_extra"))
P286 = P287.PRIOR
NATIVE = P287.NATIVE
NATIVE_FLOOR = P287.NATIVE_FLOOR
OLD_HEAD_RE = re.compile(r"^VRN_SystemManager v\d{4} · VRN 自己的入口")
OLD_FORWARD_RE = re.compile(r"^\s*其餘動詞:原樣轉交前版 VRN_SystemManager_v\d{4}\.py")


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def chain_modules() -> list:
    return [sys.modules[__name__]] + PRIOR.chain_modules()


_G = dict(vars(P287))
_G.update(TAG=TAG, __file__=__file__, __name__=__name__, PRIOR_PATH=PRIOR_PATH, chain_modules=chain_modules)
for _n in ("chain_report", "verb_table", "cmd_version", "health_extra", "cmd_health", "cmd_help", "cmd_verbs"):
    _f = vars(P287)[_n]
    _G[_n] = types.FunctionType(_f.__code__, _G, _n, _f.__defaults__, _f.__closure__)
    globals()[_n] = _G[_n]
_capture = P287._capture
_HELP0 = _G["cmd_help"]                               # v0287 的 help(重綁成本版鏈頭)


def clean_native_help(text: str) -> str:
    """只改第一個「──」段之前(v0269 原生處理器自己的那一塊):拿掉舊版號表頭與舊轉交句;其餘一行不動(同 #722 v0288)。"""
    out, head_done = [], False
    for ln in text.splitlines():
        if not head_done and ln.lstrip().startswith("──"):
            head_done = True
        if not head_done:
            if OLD_HEAD_RE.match(ln):
                continue
            if OLD_FORWARD_RE.match(ln):
                out.append("  舊動詞:鏈底原生處理器原樣轉交更舊的版(子行程);標準動詞加 --legacy 看前版原樣輸出")
                continue
            ln = ln.replace("標準動詞(本版):", "標準動詞:")
        out.append(ln)
    return "\n".join(out) + ("\n" if text.endswith("\n") else "")


def cmd_help() -> int:
    rc, out = _capture(_HELP0)
    first, _, rest = out.partition("\n")
    print(first)
    print(clean_native_help(rest), end="")
    return rc


_G["cmd_help"] = cmd_help                             # verbs / health 的 help 涵蓋檢查也看清理後的 help


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    if not args or args[:1] == ["help"]:
        return cmd_help()
    if args[:1] == ["version"] and "--legacy" not in args:
        return cmd_version(args[1:])
    if args[:1] == ["health"] and "--legacy" not in args:
        return cmd_health(args[1:])
    if args[:1] == ["verbs"]:
        return cmd_verbs(args[1:])
    return PRIOR.main(args)


def selftest() -> int:
    import json
    import os
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)[:300]) if note and not cond else ''}", flush=True)

    # v0289 的自測假設自己是磁碟上最新那一版:測它時給它看「到 v0289 為止」的版名(同 v0289 測 v0287 的作法),測完換回。
    real_cr = P286.chain_report
    with tempfile.TemporaryDirectory(prefix="via_vrn290_fam_") as fam:
        for p in HERE.glob(FAMILY + "_v*.py"):
            if 0 <= _vnum(p) <= _vnum(PRIOR_PATH):
                (Path(fam) / p.name).write_text("", encoding="utf-8")
        P286.chain_report = lambda mods=None, family_dir=None: real_cr(mods, fam if family_dir is None else family_dir)
        try:
            rc0, out0 = _capture(PRIOR.selftest)
        finally:
            P286.chain_report = real_cr
    print(f"=== {TAG} · 薄尾自測(help 不印 v0269 舊表頭 · 動詞不少 · 鏈頭 = 本版;零網路)===")
    chk("⓪ 直接前版 %s 自測過(整條前版鏈原封不動)" % PRIOR_PATH.name, rc0 == 0, out0[-300:])
    _, help_out = _capture(cmd_help)
    table = verb_table()
    chk("① help 第一行標本版", help_out.startswith(TAG), help_out[:120])
    chk("② help 不再出現 v0269 舊表頭與「轉交前版 v0268」舊句",
        not re.search(r"VRN_SystemManager v0269 · VRN 自己的入口|轉交前版 VRN_SystemManager_v0268", help_out),
        [ln for ln in help_out.splitlines() if "v0269" in ln or "v0268" in ln][:3])
    miss = P286.help_coverage(help_out, table)
    chk("③ 每個動詞仍列得到(help 涵蓋 = v0286 的尺)", not miss, miss)
    chk("④ 標準動詞行 · rc 行 · v0278 synchronizer 段 · v0270 以後動詞表都還在",
        "  標準動詞:help · version" in help_out and "  rc:0 綠" in help_out and "v0278 synchronizer" in help_out and "v0270 以後加的動詞" in help_out)
    fake = ("VRN_SystemManager v0269 · VRN 自己的入口(x)\n  標準動詞(本版):help · a\n  其餘動詞:原樣轉交前版 VRN_SystemManager_v0268.py;y\n"
            "  rc:0\n  ── z\n  標準動詞(本版):留\n")
    chk("⑤ 只改第一個「──」段之前;段後一行不動", clean_native_help(fake) ==
        "  標準動詞:help · a\n  舊動詞:鏈底原生處理器原樣轉交更舊的版(子行程);標準動詞加 --legacy 看前版原樣輸出\n  rc:0\n  ── z\n  標準動詞(本版):留\n")
    with tempfile.TemporaryDirectory(prefix="via_vrn290_") as td:
        keep = os.environ.get("VIA_VRN_SCAN_CACHE")
        os.environ["VIA_VRN_SCAN_CACHE"] = str(Path(td) / "cache.json")
        try:
            rvj, vj = _capture(cmd_version, ["--json"])
            rv, vout = _capture(cmd_version, [])
        finally:
            if keep is None:
                os.environ.pop("VIA_VRN_SCAN_CACHE", None)
            else:
                os.environ["VIA_VRN_SCAN_CACHE"] = keep
    try:
        vjd = json.loads(vj)
    except ValueError:
        vjd = {}
    me = "v%04d" % _vnum(__file__)
    chk("⑥ version --json:合法 JSON · live_tail = 本版 · 鏈完整且從本版算起",
        rvj == 0 and vjd.get("live_tail", {}).get("version") == me and vjd.get("chain", {}).get("complete") is True
        and (vjd.get("chain", {}).get("versions") or [None])[0] == me, vj[:200])
    chk("⑦ version 文字:第一行標本版", rv == 0 and vout.startswith("[%s] VRN · 現役尾版 VRN_SystemManager_%s.py" % (TAG, me)), vout[:200])
    got = {r["verb"]: r["top"] for r in table}
    chk("⑧ verbs:help / version / health / verbs 最新處理版 = 本版", all(got.get(v) == me for v in ("help", "version", "health", "verbs")), got)
    chk("⑨ 顯示函式本體找到 v0287(不是 v0289 的重綁)· v0289 · v0287 的名字原封不動", Path(P287.__file__).name == "VRN_SystemManager_v0287.py"
        and PRIOR.TAG == "VRN_SystemManager v0289" and P287.TAG.endswith("v0287")
        and vars(P287)["cmd_help"] is not cmd_help)
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    peer = [k for k in ("VIA_FROM_VCGC", "VIA_FROM_VDFSM") if re.search(r"environ(?:\[[\"']%s[\"']\]\s*=|\.setdefault\([\"']%s)" % (k, k), body)]
    chk("⑩ 系統獨立:不替別的系統設入口旗標 · 加速器橋在 · 不碰 TA-Lib · 不出網",
        not peer and "[VIA:ACCEL-BRIDGE:v0100]" in src and "talib" not in body.lower()
        and not re.search(r"^\s*(import|from)\s+(requests|urllib|socket|http)\b", src, re.M))
    pub = [n for n in dir(PRIOR) if not n.startswith("_") and callable(getattr(PRIOR, n, None))]
    chk("⑪ 尾版保有前版公開名稱(TAILAPI)", all(getattr(sys.modules[__name__], n, None) is not None for n in pub), "%d 支" % len(pub))
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
