#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""CGC_MDL158_VIAPanoramaAuditRepair v0116 — 薄尾:免修名冊沿 CGC_MDL156 薄尾鏈找正主(R33 SDD 自測抓到的既有回歸)

R33 SDD 自測(CGC_MDL245 selftests,經 VCGC run)實錄:v0115 自測 45 檢 FAIL 2(⑱ ㉒)。根因:v0115 以 AST 只讀 CGC_MDL156
「最新那支」的 _ACCEL_EXEMPT / _TREE_EXEMPT;R20c 起 MDL156 v0111 是薄尾(常數留在 v0110 本體、經 __getattr__ 轉接),
最新那支讀不到常數 → 名冊退回內建底線 1 條 → VIA_HTML_UI / VIA_Central_Governance / new modules engines / _patches 的豁免全失效
(全景把正典件當成可修)。本尾版:沿 MDL156 版號由新到舊,取**第一支真的定義這兩個常數的**(薄尾不重寫 = 沿用前版,
與 __getattr__ 轉接同一個意思),名冊與理由對照都讀它;出處照實寫進報告。仍是 ast.literal_eval,不執行 MDL156。
其餘一字不動,轉給 v0115(L04 舊版留作版史)。只收 VCGC 呼叫(VIA_FROM_VCGC=YES)的規矩照前一版。
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

import ast
import importlib.util
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL158_VIAPanoramaAuditRepair"


def _vnum(path: Path) -> int:
    m = re.search(r"_v(\d+)$", path.stem)
    return int(m.group(1)) if m else -1


_PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum,
                  default=HERE / "CGC_MDL158_VIAPanoramaAuditRepair_v0115.py")   # the prior this tail was cut from (⑭ follows the chain)
_spec = importlib.util.spec_from_file_location("panorama_prior_for_" + Path(__file__).stem, _PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    return getattr(PRIOR, name)


_NAMES = ("_ACCEL_EXEMPT", "_TREE_EXEMPT")


def _roster_owner() -> Path | None:
    """Newest CGC_MDL156 version that really defines the roster literals (a thin tail forwards to the one before it)."""
    for p in sorted(HERE.glob("CGC_MDL156_VIAAcceleratorControl_v*.py"), key=_vnum, reverse=True):
        try:
            tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            continue
        if any(isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id in _NAMES for t in n.targets) for n in tree.body):
            return p
    return None


def _load_exempt_roster() -> tuple:
    """批658 L30 一個出處:免修名冊的正主是 CGC_MDL156(_ACCEL_EXEMPT + _TREE_EXEMPT);v0116 起沿薄尾鏈找到真正定義它的那一版。
    讀碼不執行(ast.literal_eval);讀不到就退回內建底線,並把用了哪一把尺寫進報告。"""
    base = list(PRIOR._EXEMPT_TEMPLATE)
    seen = {k for k, _ in base}
    owner = _roster_owner()
    if owner is None:
        return tuple(base), "內建底線(CGC_MDL156 沒有一版定義名冊)"
    newest = max(HERE.glob("CGC_MDL156_VIAAcceleratorControl_v*.py"), key=_vnum)
    for node in ast.parse(owner.read_text(encoding="utf-8", errors="replace")).body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in _NAMES for t in node.targets):
            try:
                for item in ast.literal_eval(node.value):
                    k, w = str(item[0]), str(item[1])
                    if k not in seen:
                        seen.add(k)
                        base.append((k, w))
            except Exception:
                continue
    src = owner.name if owner == newest else f"{owner.name}(尾版 {newest.name} 是薄尾,沿用這一版的名冊)"
    return tuple(base), src


def _exempt_same_as_mdl156() -> bool:
    """對照 CGC_MDL156 名冊正主(沿薄尾鏈)的理由字串;對照件不在=ABSENT 不當綠。"""
    owner = _roster_owner()
    if owner is None:
        return False
    txt = owner.read_text(encoding="utf-8", errors="replace")
    return all(why in txt for _, why in PRIOR._EXEMPT_TEMPLATE)


PRIOR._load_exempt_roster, PRIOR._exempt_same_as_mdl156 = _load_exempt_roster, _exempt_same_as_mdl156
PRIOR._EXEMPT_ROSTER, PRIOR._EXEMPT_SRC = _load_exempt_roster()


# The token-saving surface this tail serves (CLAUDE.md reading rule; VCGC status step 2 reads these names off the tail):
# read / slice / digest / pack, each with --if-etag (304 when nothing changed). The bodies stay in v0115; these are explicit forwarders.
TOKEN_VERBS = ("read", "slice", "digest", "pack")
USAGE = "via-panorama read <檔或夾> | slice <檔> <名> | digest [日誌] [--if-etag ETAG] | pack [夾] [--if-etag ETAG]"


def pack_payload(root, limit: int = 200) -> dict:
    return PRIOR.pack_payload(root, limit)


def digest_log(text: str) -> dict:
    return PRIOR.digest_log(text)


def main() -> int:
    if sys.argv[1:] == ["--selftest"]:
        return selftest()
    return PRIOR.main()


def selftest() -> int:
    owner = _roster_owner()
    ok = [owner is not None and len(PRIOR._EXEMPT_ROSTER) > len(PRIOR._EXEMPT_TEMPLATE)]
    print(f"  [{'OK' if ok[0] else 'FAIL'}] R33 名冊沿 MDL156 薄尾鏈找正主 · {PRIOR._EXEMPT_SRC} · {len(PRIOR._EXEMPT_ROSTER)} 條")
    ok.append(PRIOR.template_exempt("VIA_HTML_UI/a.py") != "" and PRIOR.template_exempt("functional modules/VRN/VRN_ENG085_x_v0100.py") == "")
    print(f"  [{'OK' if ok[1] else 'FAIL'}] 名冊件照樣免修 · 非名冊件照樣可修")
    ok.append(all(v in TOKEN_VERBS for v in ("read", "slice", "digest", "pack")) and callable(PRIOR.pack_payload) and callable(PRIOR.digest_log))
    print(f"  [{'OK' if ok[2] else 'FAIL'}] 省 Token 介面照樣在尾版上(read · slice · digest · pack · --if-etag;轉給 v0115)")
    rc = PRIOR.selftest()
    return 0 if all(ok) and rc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
