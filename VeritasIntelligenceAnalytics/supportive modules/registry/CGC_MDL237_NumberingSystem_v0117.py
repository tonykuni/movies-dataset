#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL237_NumberingSystem v0117 — 薄尾:未知動詞 / 旗標一律拒跑(rc 2)· door 標籤報實際尾版

語意錯誤全景(2026-10-03,側線語意掃描 A1/A2)實測:
  A1 `run CGC_MDL237_NumberingSystem managr sync --apply --scope`(打錯字)→ v0114 只看 '--apply' / '--scope' 在不在 →
     照樣跑「只登本批」寫入;`foo` / `--aply` 之類 → 一路落到 v0100 build() 印整份預覽,看起來像成功。指令說的和做的不一致。
  A2 預覽 / 寫入回報的 "door" 與 SSOT 的 "engine" 寫死 v0100(v0100 的 ENGINE = 自己的檔名),實際跑的是尾版。
本版只加兩格(v0100–v0116 一字不動):
  ① main() 先驗參數:首詞須是已知動詞(audit · scope · tools · assets-plan · assets-view · manager)或已知旗標;
     非 manager 路徑上的 `--旗標` 須在已知表(--apply · --scope · --base · --json · --selftest);
     散落的位置參數只准出現在 --scope 之後(檔清單)· --base 之後(基準)· assets-plan 之後(候選冊)。
     不合 → 印中文 [拒跑] + 正確用法,rc 2,零寫入。manager 子命令原樣交 v0115 argparse(它自己會擋)。
  ② BASE(v0100)的 ENGINE 換成本尾版檔名:door 與 SSOT engine 欄報實際跑的版。
自測:先跑 v0116 全鏈自測,再驗拒跑 / 放行判法與「拒跑零寫入」。只收 VCGC 呼叫;零網路;不碰 TA-Lib。
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

import contextlib
import importlib.util
import io
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL237_NumberingSystem"
ENGINE = Path(__file__).stem
VERBS_V0117 = ("audit", "scope", "tools", "assets-plan", "assets-view", "manager")
FLAGS_V0117 = ("--apply", "--scope", "--base", "--json", "--selftest")
USAGE_V0117 = ("用法(經 via-vcgc run CGC_MDL237_NumberingSystem …):\n"
               "  (不帶參數)            全樹預覽,不寫\n"
               "  --apply --scope [檔…] [--base <ref>]   只登本批(寫入)\n"
               "  audit [--base <ref>] [--json]          只增稽核(遺失 / 改身分 / 重號)\n"
               "  scope [--base <ref>]                   列本批範圍,不寫\n"
               "  tools · assets-view · assets-plan [候選冊.json]\n"
               "  manager {plan|sync|conflicts|show} [--apply] [--candidates …] [--input …] [--owner …] [--out …]\n"
               "  --selftest")


def _vnum_v0117(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


def _load_v0117(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0117(p) < _vnum_v0117(__file__)), key=_vnum_v0117)
PRIOR = _load_v0117(PRIOR_PATH, _STEM + "_prior_for_" + ENGINE)        # v0116:可選依賴缺件不崩
BASE = PRIOR.BASE                                                       # v0100:build() · door
BASE.ENGINE = ENGINE                                                    # ② door / SSOT engine 報實際尾版


def __getattr__(name):
    return getattr(PRIOR, name)


def arg_problem_v0117(args) -> str:
    """回空字串 = 放行;否則回拒跑理由(中文)。manager 子命令交 v0115 argparse 自己擋。"""
    if not args or args[0] == "manager":
        return ""
    head = args[0]
    if not head.startswith("-") and head not in VERBS_V0117:
        return f"未知動詞 '{head}'(已知:{' · '.join(VERBS_V0117)})"
    bad = [a for a in args if a.startswith("-") and a not in FLAGS_V0117]
    if bad:
        return f"未知旗標 {' '.join(bad)}(已知:{' · '.join(FLAGS_V0117)})"
    if args.count("--base") > 1 or ("--base" in args and (args.index("--base") + 1 >= len(args)
                                                          or args[args.index("--base") + 1].startswith("-"))):
        return "--base 後面要接一個基準(分支 / 提交),且只能給一次"
    if head in ("tools", "assets-view") and len(args) > 1:
        return f"'{head}' 不收其他參數(收到:{' '.join(args[1:])})"
    if head == "assets-plan":
        return "" if len(args) <= 2 and not any(a.startswith("-") for a in args[1:]) else "assets-plan 只收一個候選冊路徑"
    if head == "--selftest" and len(args) > 1:
        return "--selftest 不和其他參數並用"
    if "--scope" in args and "--apply" not in args:
        return "--scope 只和 --apply 並用(只看範圍請用 scope 動詞)"
    stray, after_scope, skip = [], False, False
    for a in args[1:] if head in VERBS_V0117 else args:
        if skip:
            skip = False
        elif a == "--base":
            skip = True
        elif a == "--scope":
            after_scope = True
        elif not a.startswith("-") and not after_scope:
            stray.append(a)
    return f"多出的位置參數 {' '.join(stray)}(檔清單要放在 --scope 之後)" if stray else ""


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    why = arg_problem_v0117(args)
    if why:
        print(f"[拒跑] {ENGINE}:{why} · 零寫入\n{USAGE_V0117}")
        return 2
    if args == ["--selftest"]:
        return selftest()
    return PRIOR.main(args)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    rc116 = PRIOR.selftest()
    print(f"=== {ENGINE} · 薄尾自測(未知動詞 / 旗標拒跑 · door 報尾版)===")
    chk("① v0116 全鏈自測過(v0111 核心鏈 · 可選依賴缺件路徑)", rc116 == 0, f"rc {rc116}")
    reject = [["managr", "sync", "--apply"], ["managr", "sync", "--apply", "--scope"], ["--aply"], ["foo"],
              ["audit", "--jsn"], ["--apply", "x.py", "--scope"], ["--scope", "a.py"], ["tools", "x"],
              ["assets-plan", "a.json", "b.json"], ["--apply", "--scope", "--base"], ["--selftest", "--apply"],
              ["scope", "--base", "--json"], ["assets-view", "--apply"]]
    allow = [[], ["audit"], ["audit", "--base", "origin/main", "--json"], ["scope"], ["scope", "--base", "HEAD~1"],
             ["--apply", "--scope"], ["--apply", "--scope", "a.py", "b.py", "--base", "origin/main"],
             ["--apply", "--scope", "--base", "origin/main", "a.py"], ["tools"], ["assets-view"],
             ["assets-plan"], ["assets-plan", "book.json"], ["manager", "sync", "--apply", "--input", "x"], ["--selftest"]]
    rj = [a for a in reject if not arg_problem_v0117(a)]
    al = [a for a in allow if arg_problem_v0117(a)]
    chk(f"② 打錯字 / 未知旗標 / 散落參數 {len(reject)} 種全擋", not rj, rj)
    chk(f"③ 合法用法 {len(allow)} 種全放行(含 manager 交 argparse)", not al, al)
    calls = []
    real = PRIOR.main
    try:
        PRIOR.main = lambda a: calls.append(list(a)) or 0
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rcs = [main(a) for a in reject]
            rc_ok = main(["audit", "--json"])
    finally:
        PRIOR.main = real
    out = buf.getvalue()
    chk("④ 拒跑:rc 2 · 前版一次都沒進(零寫入)· 印中文理由與用法", set(rcs) == {2} and calls == [["audit", "--json"]]
        and rc_ok == 0 and out.count("[拒跑]") == len(reject) and "用法" in out, (set(rcs), calls))
    chk("⑤ door / SSOT engine 報實際尾版(BASE.ENGINE = 本檔名)", BASE.ENGINE == ENGINE, BASE.ENGINE)
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑥ 加速器橋 · 網路橋在 · 不碰 TA-Lib", "[VIA:ACCEL-BRIDGE" in text and "[VIA:NET-BRIDGE" in text
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M))
    print(f"  [計] {ENGINE} 本版 {sum(ok)}/{len(ok)} · v0116 {'PASS' if rc116 == 0 else 'FAIL'} · 合計 {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
