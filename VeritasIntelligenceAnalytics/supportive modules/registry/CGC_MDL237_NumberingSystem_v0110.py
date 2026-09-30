#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL237_NumberingSystem v0110 — 薄尾:只登本批要有真基準 · 明列的檔也不收未提交(Codex #378 兩條 P1)

實測(Codex 對已併 PR #378 的審查,兩條都成立):
  · origin/main 不在的檢出(審查機 · 淺拷貝)裡,v0108 的 base_ref() 退回 "HEAD";批次一提交,`git diff HEAD` 就空,
    `--apply --scope` 回報「範圍 0 檔」當成功 —— 本批一列都沒登,卻像跑完了。
  · `--apply --scope <檔…>` 明列檔案時,v0109 把 dirty 設成空集合:明列的未提交檔照樣發號,違反 R04「先提交再編號」。
本版:
  ① real_base():merge-base HEAD 對 origin/main → main → origin/HEAD 依序找;都找不到 = None。
     `--apply --scope`(沒明列檔)沒有真基準就拒跑(rc 2,一列不寫),要嘛 git fetch origin main,要嘛 --base <ref> / 明列檔案。
  ② 明列檔案也算 dirty:未提交的明列檔擋下不發號、照列出(全都未提交 = rc 2,一列不寫)。
  ③ `scope` 乾跑也印基準是否為真。其餘照 v0109(六項註冊完整性 · 寫後自核還原)。只收 VCGC 呼叫。零網路。
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
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL237_NumberingSystem"
ENGINE = Path(__file__).stem


def _vnum(path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + ENGINE, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE_CANDIDATES = ("origin/main", "main", "origin/HEAD")


def __getattr__(name: str):
    return getattr(PRIOR, name)


def real_base(ref: str | None = None, git=None) -> str | None:
    """A real merge base, never a silent HEAD: the caller's ref, else merge-base with origin/main → main → origin/HEAD."""
    git = git or PRIOR._git
    if ref:
        return ref
    for cand in BASE_CANDIDATES:
        rc, out = git("merge-base", "HEAD", cand)
        if rc == 0 and (out or "").strip():
            return out.strip()
    return None


def scoped_apply(files=None, ref: str | None = None, build=None, out=sys.stdout, git=None, dirty=None) -> int:
    base = real_base(ref, git)
    if files is None and base is None:
        print("[編號 · 只登本批] RED · 沒有真基準(" + " / ".join(BASE_CANDIDATES) + " 都不在):不退回 HEAD 冒充跑完,一列不寫"
              " · 先 git fetch origin main,或給 --base <ref>,或明列 --scope <檔…>", file=out)
        return 2
    if files is not None:
        pending = (dirty if dirty is not None else PRIOR.dirty_files()) & set(files)
        if pending:
            print(f"[編號 · 只登本批] 明列的檔未提交不發號(先提交再編號)· {len(pending)} 支:" + " · ".join(sorted(pending)[:6]), file=out)
        files = [f for f in files if f not in pending]
        if not files:
            print("[編號 · 只登本批] 明列的檔全都未提交:一列不寫(rc 2)", file=out)
            return 2
    return PRIOR.scoped_apply(files, ref=base or ref, build=build, out=out)


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args:
        return selftest()
    gated = args[:1] in (["audit"], ["scope"]) or "--apply" in args
    if gated and os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False))
        return 2
    ref = args[args.index("--base") + 1] if "--base" in args and args.index("--base") + 1 < len(args) else None
    if args[:1] == ["scope"]:
        base = real_base(ref)
        raw, dirty = (PRIOR.scope_files(base) if base else set()), PRIOR.dirty_files()
        print(json.dumps({"via": "vcgc", "verb": "scope", "baseline": base or "ABSENT(沒有真基準;--apply --scope 會拒跑)",
                          "files": sorted(raw - dirty), "held_uncommitted": sorted(raw & dirty)}, ensure_ascii=False, indent=1))
        return 0 if base else 2
    if "--apply" in args and "--scope" in args:
        i = args.index("--scope")
        listed = [a for a in args[i + 1:] if not a.startswith("--") and a != ref]
        return scoped_apply(listed or None, ref=ref)
    return PRIOR.main(argv)


def selftest() -> int:
    import io
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    nobase = lambda *a: (1, "")                      # noqa: E731
    withbase = lambda *a: (0, "abc123\n") if a[-1] == "main" else (1, "")   # noqa: E731
    chk("① 真基準:origin/main 不在時找 main;全不在 = None(不退回 HEAD)",
        real_base(git=nobase) is None and real_base(git=withbase) == "abc123" and real_base("x", git=nobase) == "x")
    calls = []
    real_apply = PRIOR.scoped_apply
    PRIOR.scoped_apply = lambda files, ref=None, build=None, out=None: calls.append((files, ref)) or 0
    try:
        buf = io.StringIO()
        rc_none = scoped_apply(None, git=nobase, out=buf)
        refused = rc_none == 2 and not calls and "沒有真基準" in buf.getvalue()
        rc_listed = scoped_apply(["a.py", "b.py"], git=nobase, out=io.StringIO(), dirty={"a.py"})
        listed = rc_listed == 0 and calls == [(["b.py"], None)]
        calls.clear()
        rc_all = scoped_apply(["a.py"], git=nobase, out=io.StringIO(), dirty={"a.py"})
        rc_ok = scoped_apply(None, git=withbase, out=io.StringIO(), dirty=set())
    finally:
        PRIOR.scoped_apply = real_apply
    chk("② 沒明列檔又沒有真基準 → 拒跑 rc 2、一列不寫(Codex #378 P1)", refused, rc_none)
    chk("③ 明列的未提交檔擋下不發號,其餘照登(Codex #378 P1)", listed, calls[:1])
    chk("④ 明列的檔全未提交 → rc 2 一列不寫;有真基準照常交給 v0109", rc_all == 2 and calls == [(None, "abc123")] and rc_ok == 0, calls)
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑤ 加速器橋 · 網路橋在;不碰 TA-Lib", "VIA:ACCEL-BRIDGE" in text and "VIA:NET-BRIDGE" in text
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M))
    print(f"[編號 v0110] 本版 {sum(ok)}/{len(ok)}")
    if not all(ok):
        return 1
    return PRIOR.selftest()


if __name__ == "__main__":
    raise SystemExit(main())
