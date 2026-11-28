#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""CGC_MDL149_VeritasCentralGovernanceConsole v0204 — 薄尾(v0203 一字不動):元件掃描認得「任何名字的家族常數 + glob 取前版」的薄尾

實錄(2026-11-28,VDF_ENG232 v0109 · VDF_MDL013 v0123 登記時):registry-sync 要把 ENG232 v0100–v0107 · ENG068 v0106 共 68 個
  還在用的元件標 RETIRED。根因:v0172 的 forwarded_defs 沿前版鏈往下讀,每一層都要先過 is_thin;v0176 的 is_thin 只認
  `STEM = "<家族>"` / `_STEM = "<家族>"` 或字面前版檔名。ENG232 v0108 · ENG068 v0107 用 `FAMILY = "<家族>"` +
  `HERE.glob(FAMILY + "_v*.py")` 一樣是在載自家前版,卻被當成實體 → 鏈在那一層斷掉,它底下各版的類別 / 函式全被當成消失
  (教訓 LL-20261128-17 原本要尾版改名 STEM 來遷就;前版已發布不能改,所以改掃描)。全樹量到 56 個家族的鏈停在這種寫法上。
本版(判法以外一字不動):
  ① is_thin 多認一種:`<名字> = "<家族>"`(行首賦值)而且同一支檔有 `glob(<名字> + "_v*…")`、有 exec_module。
     v0176 原本認的三種照認;別的家族 / 沒有載入器 / 名字沒拿去 glob 的照舊不認。
  ② 掛在「同一行程那一疊」:包 v0203 的 ensure_home_first(它載入舊疊、掛好同名兩份的判法之後),再把鏈上每一層的 is_thin 換成本版;
     活元件快取換名(舊名的結果是照舊判法算的)。舊動詞(registry-sync · sdd · handoff …)照 v0203 在本行程跑。
  ③ synchronizer 的步驟執行檔改成本檔(否則步驟裡的舊動詞走 v0203、帶不到新判法)。其餘動詞照 v0203 轉交。
  自測(裁定甲):本版 + 直接前版 v0203(它的自測不往下串鏈)。不寫任何檔;不出網;不碰 TA-Lib;不 import 他系統。
用法照舊:VIA_FROM_VCGC=YES python CGC_MDL149_VeritasCentralGovernanceConsole_v0204.py <動詞…> · --selftest
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

import contextlib
import importlib.util
import io
import os
import re
import sys
import tempfile
from pathlib import Path

VERSION = "v0204"
STEM = "CGC_MDL149_VeritasCentralGovernanceConsole"
TAG = STEM + " " + VERSION
HERE = Path(__file__).resolve().parent
CACHE_NAME = "live_components_home_thin"            # 新判法下的活元件快取名(v0203 的 live_components_home 是舊判法算的)


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(str(p)).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)              # v0203
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
_ENSURE_V0203 = PRIOR.ensure_home_first


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接(v0203 的 __getattr__ 會先掛好鉤子)
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def is_thin_v0204(stem: str, source: str) -> bool:
    """這支檔是不是載入自家前版的薄尾。v0176 的三種 + 「<名字> = '<家族>'」且 glob(<名字> + '_v*')。"""
    if "exec_module" not in source:
        return False
    if re.search(re.escape(stem) + r"(?:_v\d{3,4}\.py|_v\*|['\"]\s*\+)", source):
        return True
    if re.search(r"(?m)^\s*_?STEM\s*=\s*['\"]" + re.escape(stem) + r"['\"]", source):
        return True
    for m in re.finditer(r"(?m)^\s*([A-Za-z_]\w*)\s*=\s*['\"]" + re.escape(stem) + r"['\"]", source):
        if re.search(r"glob\(\s*" + re.escape(m.group(1)) + r"\s*\+\s*['\"]_v\*", source):
            return True
    return False


is_thin = is_thin_v0204          # 舊疊載入時 v0176 的模組層迴圈會把鏈上每一支(含本檔)的 is_thin 蓋掉;本版一律用 is_thin_v0204 裝回


def _chain_modules() -> list:
    me = sys.modules.get(__name__)
    return [m for m in list(sys.modules.values()) if STEM in str(getattr(m, "__file__", "") or "") and m is not me]


def install_thin() -> int:
    """鏈上每一層的 is_thin 換成本版;v0188 的沿用版 forwarded_defs 在建立時把 is_thin 綁進閉包,所以用它自己的工廠在原位重建一次。"""
    globals()["is_thin"] = is_thin_v0204
    mods = _chain_modules()
    n = 0
    for m in mods:
        if "is_thin" in vars(m) and m.__dict__["is_thin"] is not is_thin_v0204:
            m.__dict__["is_thin"] = is_thin_v0204
            n += 1
    maker = next((vars(m)["make_forwarded_defs_v0188"] for m in mods if callable(vars(m).get("make_forwarded_defs_v0188"))), None)
    for m in mods:
        f = vars(m).get("forwarded_defs")
        if maker is None or not callable(f) or not callable(vars(m).get("extend")) or getattr(f, "__v0204_thin__", False):
            continue
        if getattr(f, "__v0188_cached__", False):
            m.__dict__["forwarded_defs"] = getattr(f, "__wrapped__", f)   # 先放回 v0172 原函式,工廠的 __wrapped__ 才指得對
            neu = maker(m)
            neu.__v0204_thin__ = True
            m.__dict__["forwarded_defs"] = neu
            n += 1
    return n


def ensure_home_first() -> dict:
    """v0203 那一套(載入舊疊 · 同名兩份判法 · 快取換名)照跑,再把鏈上每一層的 is_thin 換成本版。可重複呼叫。"""
    st = _ENSURE_V0203()
    st["thin_hooked"] = install_thin()
    return st


PRIOR.ensure_home_first = ensure_home_first
PRIOR.CACHE_NAME = CACHE_NAME


def synchronizer(args: list) -> int:
    """照 v0203,但步驟執行檔是本檔(步驟裡的舊動詞才會帶新判法)。找不到同步台就原樣轉交。"""
    try:
        P = PRIOR._prior_module()
        owner = P.sync_owner()
        cfg = dict(P.sync_config(owner), prior=Path(__file__).resolve()) if owner is not None else None
    except AttributeError:
        owner = cfg = None
    if owner is None or cfg is None:
        return PRIOR.forward(["synchronizer", *args])
    os.environ.setdefault(PRIOR.OWN_FLAG, "YES")
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    return owner.sy_command(cfg, args)


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] in ("--selftest", "selftest") and "--legacy" not in args:
        return selftest()
    if args[:1] == ["synchronizer"]:
        return synchronizer(args[1:])
    if PRIOR.is_legacy(args):
        return PRIOR.legacy_main(args)
    rc = PRIOR.forward(args)
    if not args or args[0] == "help":
        PRIOR.help_extra()
        print("  [%s] 元件掃描:任何名字的家族常數 + glob 取前版的薄尾也沿前版鏈讀。" % VERSION)
    return rc


def _owner():
    return next((m for m in _chain_modules() if callable(vars(m).get("forwarded_defs")) and callable(vars(m).get("extend"))), None)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:300]) if note and not cond else ""), flush=True)

    print("[計] %s 自測開始(本版 + 直接前版 v0203 · 暫存樹 · 不寫真樹 · 零網路)" % TAG, flush=True)
    L = "\nloader.exec_module(mod)\n"
    cases = {"STEM": ('STEM = "Demo"' + L, True), "_STEM": ('_STEM = "Demo"' + L, True),
             "FAMILY+glob": ('FAMILY = "Demo"\np = HERE.glob(FAMILY + "_v*.py")' + L, True),
             "任何名字+glob": ('_FAM = "Demo"\nx = sorted(HERE.glob(_FAM + \'_v*.py\'))' + L, True),
             "字面前版檔名": ('p = HERE / "Demo_v0101.py"' + L, True),
             "別的家族": ('FAMILY = "Other"\np = HERE.glob(FAMILY + "_v*.py")' + L, False),
             "沒有載入器": ('FAMILY = "Demo"\np = HERE.glob(FAMILY + "_v*.py")\n', False),
             "名字沒拿去 glob": ('FAMILY = "Demo"\np = HERE.glob("Other_v*.py")' + L, False),
             "非行首的名字": ('x = {"k": FAMILY}; y = 1; FAMILY = "Demo"' + L, False)}
    got = {k: is_thin_v0204("Demo", s) for k, (s, _w) in cases.items()}
    chk("① 判法:v0176 的三種照認 · 多認「名字 = 家族 + glob(名字 + _v*)」· 別的家族 / 沒載入器 / 名字沒 glob / 非行首照舊不認",
        all(got[k] == w for k, (_s, w) in cases.items()), {k: v for k, v in got.items() if v != cases[k][1]})
    st = ensure_home_first()
    owner = _owner()
    holders = [m for m in _chain_modules() if "is_thin" in vars(m)]
    chk("② 掛在同一行程那一疊:鏈上每一層的 is_thin 都是本版 · 掃描本體在 · 快取換名", owner is not None and holders
        and all(m.__dict__["is_thin"] is is_thin_v0204 for m in holders) and is_thin is is_thin_v0204 and st.get("bodies", 0) >= 1 and PRIOR.CACHE_NAME == CACHE_NAME,
        (st, len(holders), owner is not None))
    if owner is not None:
        from unittest.mock import patch
        with tempfile.TemporaryDirectory(prefix="vcgc204_") as td:
            root = Path(td)
            (root / "Demo_v0100.py").write_text("class Reader:\n    def read(self): pass\ndef base_fn(): pass\n", encoding="utf-8")
            (root / "Demo_v0101.py").write_text('FAMILY = "Demo"\np = HERE.glob(FAMILY + "_v*.py")\nloader.exec_module(mod)\ndef mid(): pass\n',
                                                encoding="utf-8")
            tail = root / "Demo_v0102.py"
            tail.write_text('STEM = "Demo"\nloader.exec_module(mod)\n', encoding="utf-8")
            with patch.dict(owner.forwarded_defs.__globals__, {"VIA": root}):
                found = set(owner.forwarded_defs([("Demo", tail)]))
        chk("③ 三層合成鏈(中間那層用 FAMILY + glob):最底層的類別 · 方法 · 函式都沿到", {"class|Demo:Reader", "function|Demo:Reader.read",
            "function|Demo:base_fn", "function|Demo:mid"} <= found, sorted(found))
        eng = PRIOR.VIA / "functional modules" / "VDF" / "engine"
        real = {}
        for fam in ("VDF_ENG232_TWIndexOfficial", "VDF_ENG068_ETFConsensusAnalysis"):
            tails = sorted(eng.glob(fam + "_v*.py"), key=_vnum)
            rows = owner.forwarded_defs([(fam, tails[-1])]) if tails else {}
            real[fam] = sorted({Path(str(r.get("source", ""))).name for r in rows.values()})
        want = {"VDF_ENG232_TWIndexOfficial": ("_v0107.py", "_v0100.py"),       # v0108 用 FAMILY:它底下的 v0107 一路到 v0100
                "VDF_ENG068_ETFConsensusAnalysis": ("_v0106.py",)}                # v0107 用 FAMILY:它底下的本體 v0106
        chk("④ 真樹:ENG232(v0108 用 FAMILY)讀到 v0107 … v0100 · ENG068(v0107 用 FAMILY)讀到 v0106 —— 不再停在 FAMILY 那一層",
            all(all(any(n.endswith(w) for n in real[k]) for w in ws) for k, ws in want.items()), {k: v[:4] for k, v in real.items()})
    else:
        chk("③ 掃描本體在本行程(forwarded_defs)", False, "owner None")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc3 = PRIOR.selftest()
    print(buf.getvalue(), end="", flush=True)
    chk("⑤ 直接前版 v0203 自測照過(它的自測不往下串鏈)", rc3 == 0, rc3)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑥ 加速器 · 網路工具橋在且載到 · 零 TA-Lib · 不設同意閘 · 不含本機路徑", VIA_ACCEL is not None and VIA_NET_TOOL_PATH is not None
        and src.splitlines()[2].startswith("# [VIA:ACCEL-BRIDGE") and not re.search(r"^\s*(import|from)\s+talib", src, re.M)
        and not re.search(r"^\s*os\.environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", src, re.M) and "C:\\Users\\" + "tonyk" not in src)
    good = all(ok)
    print("[計] %s 自測 %d/%d · %s" % (TAG, sum(ok), len(ok), "PASS" if good else "FAIL"), flush=True)
    return 0 if good else 1


if __name__ == "__main__":
    raise SystemExit(main())
