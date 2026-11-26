#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VDF_MDL008_FetchSystem v0114 — 薄尾(v0100–v0113 一字不動):main 收回 argv(v0113 漏了,呼叫端一叫就 TypeError)

桌機 2026-11-26 22:13 實錄(Start-VIA-VDF · ActivateVDF ②):lists_run_009 / lists_run_010 / lists_verify 全部
「TypeError: main() takes 0 positional arguments but 1 was given」→ 兩張清單沒產出 → 擷取流程整條 BLOCKED。
根因:v0110–v0112 的公開簽章是 main(argv=None),VDF 管理器 fetch 動詞載尾版後呼叫 main(args);v0113 改成 main()(TAILAPI 簽章退步)。
本版只把 main 改回 main(argv=None):--selftest / home 照 v0113,其餘原樣交 v0112 的 main(argv)。擷取家解析(資料家優先)照 v0113。
零網路自測;不設同意閘;不用 TA-Lib。
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
import inspect
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_MDL008_FetchSystem"
TAG = f"{_STEM} v0114"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(str(p)).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
P112 = PRIOR.PRIOR                                    # v0113 的前版(main(argv=None) 那一支)


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] == ["--selftest"]:
        return selftest()
    if args[:1] == ["home"]:
        p, why = PRIOR.resolve_home(None)
        print(f"[{TAG}] 擷取家 {p} · 來源 {why} · output_hub {'在' if (p / 'output_hub').is_dir() else '不在'}")
        return 0 if why.startswith(("資料家", "env")) else 2
    return P112.main(args)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f" · {str(note)[:300]}" if note and not cond else ""), flush=True)

    print(f"=== {TAG} · 薄尾自測(零網路)===", flush=True)
    chk("① 加速器真的載到(VIA_ACCEL is not None)", VIA_ACCEL is not None)
    chk("② 網路工具橋在位(載入不出網)", VIA_NET_TOOL_PATH is not None)
    sig = inspect.signature(main)
    chk("③ 簽章回到 main(argv=None)(跟 v0110–v0112 同;v0113 漏 argv)", list(sig.parameters) == ["argv"]
        and sig.parameters["argv"].default is None, str(sig))
    seen = []
    keep = P112.main
    try:
        P112.main = lambda a=None: seen.append(list(a or [])) or 0
        rc = main(["verify", "009"])
    finally:
        P112.main = keep
    chk("④ 呼叫端帶 argv(管理器 fetch 動詞的叫法)→ 原樣交 v0112 main(argv)、不 TypeError", rc == 0 and seen == [["verify", "009"]], seen)
    chk("⑤ 擷取家解析照 v0113(資料家優先)仍生效", PRIOR.BODY is not None and PRIOR.BODY.home_dir is PRIOR.home_dir)
    import contextlib
    import io
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            rc_p = PRIOR.selftest()
    except Exception as exc:  # noqa: BLE001
        rc_p = 1
        print(f"  [註] 前版自測丟例外:{type(exc).__name__}", flush=True)
    chk("⑥ 前版 v0113 自測照過(rc 0)", rc_p == 0, rc_p)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑦ 檔面:第 3 行加速器標記 · 雙橋 · glob 取前版 · 零 TA-Lib · 不設同意閘",
        src.splitlines()[2].startswith("# [VIA:ACCEL-BRIDGE") and "[VIA:NET-BRIDGE:v0100]" in src and "HERE.glob(_STEM" in src
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M)
        and not re.search(r"^\s*os\.environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", src, re.M))
    print(f"[selftest] {TAG} {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}", flush=True)
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
