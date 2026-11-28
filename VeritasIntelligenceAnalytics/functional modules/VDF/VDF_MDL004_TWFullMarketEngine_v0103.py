#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VDF_MDL004_TWFullMarketEngine v0103 — 薄尾(v0100–v0102 一字不動):v0102 自測 ⓪ 釘「自己的檔」造成的假紅

2026-11-28 主機 vv 與容器同樣實錄:v0102 自測 9/10,不過的是 ⓪
  「v0101:沒有 bare except · 例外處理數跟 v0100 一樣(bare 0 · 例外處理 29 · 前版 28)」。
根因:v0102 是 v0101 全文 + 參數解耦橋(VIA_GovernanceApply v0100 產生);⓪ 是 v0101 寫的檢查,
  它數的是「__file__ 自己」的例外處理數,v0102 原樣抄過來後數到的是 v0102 —— 多出的那 1 處是參數解耦橋裡
  讀參數冊的 `except Exception`(缺冊 / 缺鍵 = 原值),不是業務邏輯被改。行為沒錯,是舊檢查換了檔就過時。
本版只做一件事:把 ⓪ 換成照版本算的檢查 ——
  v0102 不能有 bare except;參數解耦橋區塊「以外」的例外處理數 = v0100(只改型別、沒增刪);橋區塊裡的全部有型別。
  再在子行程實跑 v0102 自測,確認它不過的只有那一行 ⓪;有任何別的一行不過 → 照實紅,不放水。
其餘照 v0102(`__getattr__` 轉接 · --offline-probe · 受治理的 main)。資料不離開本機;零網路;不碰 TA-Lib;不設同意閘。
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
except Exception:  # noqa: BLE001
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
    except Exception:  # noqa: BLE001
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import ast
import importlib.util
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FAMILY = "VDF_MDL004_TWFullMarketEngine"
TAG = "VDF_MDL004_TWFullMarketEngine v0103"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0103", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)                 # v0102(v0101 全文 + 參數解耦橋)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


GOV_BEGIN = "# ===== [VIA:GOV-PARAM:v0100]"
GOV_END = "# ===== [VIA:GOV-PARAM:END]"
STALE_SIG = "⓪ v0101:沒有 bare except"


def _handlers(text: str) -> list:
    return [h for h in ast.walk(ast.parse(text)) if isinstance(h, ast.ExceptHandler)]


def gov_block(text: str) -> tuple:
    """參數解耦橋區塊的行號範圍(1 起算,含頭尾);沒有區塊 → (0, -1)。"""
    lines = text.splitlines()
    b = next((i + 1 for i, ln in enumerate(lines) if ln.startswith(GOV_BEGIN)), 0)
    e = next((i + 1 for i, ln in enumerate(lines) if ln.startswith(GOV_END) and i + 1 > b), -1) if b else -1
    return b, e


def handler_audit(cur: Path, base: Path) -> dict:
    """照版本算:cur 沒有 bare;橋區塊以外的例外處理數 = base;橋區塊裡的全部有型別。"""
    ct = cur.read_text(encoding="utf-8")
    b, e = gov_block(ct)
    hs = _handlers(ct)
    inside = [h for h in hs if b <= h.lineno <= e]
    outside = [h for h in hs if not (b <= h.lineno <= e)]
    n_base = len(_handlers(base.read_text(encoding="utf-8"))) if base.is_file() else -1
    bare = sum(1 for h in hs if h.type is None)
    ok = bare == 0 and len(outside) == n_base and all(h.type is not None for h in inside) and b > 0
    return {"ok": ok, "bare": bare, "outside": len(outside), "inside": len(inside), "base": n_base, "block": (b, e)}


def prior_fails(path: Path | None = None) -> tuple:
    """子行程實跑 v0102 自測;回 (只有舊 ⓪ 那一行不過?, 其他不過的行)。跑不起來 / 有別的紅 → False(照實)。"""
    p = path or PRIOR_PATH
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    for k in ("VIA_NET_CONSENT", "VIA_SCRAPE_CONSENT"):
        env.pop(k, None)
    try:
        cp = subprocess.run([sys.executable, str(p), "--selftest"], capture_output=True, text=True, encoding="utf-8",
                            errors="replace", timeout=900, stdin=subprocess.DEVNULL, env=env, cwd=str(HERE))
    except subprocess.TimeoutExpired:
        return False, ["v0102 自測逾時"]
    fails = [ln.strip() for ln in (cp.stdout + cp.stderr).splitlines() if "[FAIL]" in ln]
    other = [ln for ln in fails if STALE_SIG not in ln]
    return (cp.returncode == 0) or (bool(fails) and not other), other


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:240]) if note and not cond else ""), flush=True)

    print(f"[計] {TAG} 自測開始(本版 4 項 · 前版 {PRIOR_PATH.name} 在子行程實跑 · 零網路)", flush=True)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("T1 加速器真的載到(VIA_ACCEL is not None)· 第 3 行標記 · 網路橋在 __future__ 之下",
        VIA_ACCEL is not None and src.splitlines()[2] == "# [VIA:ACCEL-BRIDGE:v0111]" and VIA_NET_TOOL_PATH is not None)
    a = handler_audit(PRIOR_PATH, HERE / (FAMILY + "_v0100.py"))
    chk("T2 ⓪(照版本算)v0102 零 bare except · 參數橋以外的例外處理數 = v0100 · 橋裡的全部有型別", a["ok"], a)
    fx = ("x = 1\ntry:\n    pass\nexcept ValueError:\n    pass\n" + GOV_BEGIN + " 橋 =====\ntry:\n    pass\n"
          "except Exception:\n    pass\n" + GOV_END + " =====\n")
    import tempfile
    with tempfile.TemporaryDirectory(prefix="mdl004_103_") as td:
        cur, base = Path(td) / "cur.py", Path(td) / "base.py"
        cur.write_text(fx, encoding="utf-8")
        base.write_text("try:\n    pass\nexcept ValueError:\n    pass\n", encoding="utf-8")
        g1 = handler_audit(cur, base)["ok"]
        cur.write_text(fx.replace("except ValueError", "except"), encoding="utf-8")
        g2 = handler_audit(cur, base)["ok"]
        cur.write_text(fx + "try:\n    pass\nexcept OSError:\n    pass\n", encoding="utf-8")
        g3 = handler_audit(cur, base)["ok"]
    chk("T3 判法:橋裡多 1 處 → 過;出現 bare → 不過;橋外多 1 處 → 不過", g1 and not g2 and not g3, (g1, g2, g3))
    good, other = prior_fails()
    chk("T4 v0102 自測只有舊 ⓪ 那一行不過(其餘九檢照過)", good, other[:3])
    print(f"[計] {TAG} 自測 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}", flush=True)
    return 0 if all(ok) else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args:
        return selftest()
    sys.argv = [sys.argv[0], *args]
    if "--offline-probe" in args:
        return PRIOR.main()                                    # 照 v0102:閘關著照樣點起來,不出網
    try:
        return PRIOR.main_governed()
    except KeyboardInterrupt:
        print("\n[中斷]")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
