#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VDF SystemManager v0193 — 薄尾(v0192 以前一字不動):自測裡「APScheduler 缺」照標籤算黃,不算紅

PR #749 CI(VDF · manager and daily data contracts (Windows),run 45761663444):v0192 自測 7/8 → rc 1。
那台 Windows 跑者只裝 duckdb / pandas,沒有 APScheduler;v0192 的那一檢寫著「APScheduler 可用(缺 = 黃)」,卻把缺當成不過。
CLAUDE.md:缺依賴而跳過 = 黃(不是綠、也不是程式錯)。本版:
  · 這台沒有 APScheduler → 前版自測照跑,只有那一檢的「不過」改印成 [黃] 並寫補法(via-install --yes apscheduler),
    其餘檢查全過才回 0;任何其他一檢不過照舊回 1。
  · 這台有 APScheduler → 前版自測必須全過(cron 觸發 · 不疊跑 · 合併錯過 · 執行緒池那一檢照驗)。
  · 正式動詞(schedule start)沒有 APScheduler 照舊報錯,不假裝能跑。
其餘動詞全部轉給 v0192。不用 TA-Lib · 不設同意閘 · 本檔零外呼。
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)。本支零外呼。"""
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
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEM = "VDF_SystemManager"
VERSION = "v0193"
TAG = f"VDF SystemManager {VERSION}"
APS_LINE = "APScheduler 可用(缺 = 黃)"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(str(p)).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(f"{STEM}_prior_for_{VERSION}", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def has_apscheduler() -> bool:
    return importlib.util.find_spec("apscheduler") is not None


def judge(prior_out: str, prior_rc: int, aps: bool) -> tuple:
    """→ (rc, 說明)。沒有 APScheduler 時,只有那一檢不過 = 黃(rc 0);其他不過 = 紅(rc 1)。"""
    bad = [ln.strip() for ln in prior_out.splitlines() if ln.strip().startswith("[NG]")]
    others = [ln for ln in bad if APS_LINE not in ln]
    if prior_rc == 0:
        return 0, "前版自測全過"
    if not aps and not others and bad:
        return 0, "[黃] 這台沒有 APScheduler:排程 start 不可用(補法 via-install --yes apscheduler);其餘檢查全過"
    return 1, "前版自測不過:" + " · ".join(others or bad)[:300]


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    return PRIOR.main(a)


def selftest() -> int:
    ok, bad = [], []

    def chk(name, cond, note=""):
        (ok if cond else bad).append(name)
        print(f"  [{'OK' if cond else 'NG'}] {name}" + (f" · {str(note)[:300]}" if note and not cond else ""), flush=True)

    chk("加速器載入(VIA_ACCEL is not None)", VIA_ACCEL is not None)
    chk("網路工具載入(_via_net() is not None · 載入不出網)", _via_net() is not None, VIA_NET_TOOL_PATH)
    chk("前版 = 同家族比自己小的最大版 · 動詞轉給前版", _vnum(PRIOR_PATH) < _vnum(Path(__file__)) and callable(PRIOR.main))
    ng_aps = f"  [NG] {APS_LINE} · via-install --yes apscheduler\nVDF SystemManager v0192 selftest 7/8 · 不過:{APS_LINE}\n"
    ng_other = "  [NG] 排程工作取自 VDF 正本(可編輯可管理)\n  [NG] " + APS_LINE + "\n"
    chk("判法:沒 APScheduler 且只有那一檢不過 → 黃 rc 0;另有別檢不過 → rc 1;有 APScheduler 時那一檢不過 → rc 1",
        judge(ng_aps, 1, False)[0] == 0 and "[黃]" in judge(ng_aps, 1, False)[1]
        and judge(ng_other, 1, False)[0] == 1 and judge(ng_aps, 1, True)[0] == 1 and judge("", 0, True)[0] == 0)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc_p = PRIOR.selftest()
    out = buf.getvalue()
    print(out.rstrip("\n"), flush=True)
    aps = has_apscheduler()
    rc_j, why = judge(out, rc_p, aps)
    print(f"  {why}", flush=True)
    chk(f"前版 v0192 自測(這台 APScheduler {'有' if aps else '沒有'})", rc_j == 0, why)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("檔面:雙橋在 · 零 TA-Lib · 不設同意閘",
        "[VIA:ACCEL-BRIDGE:v0100]" in src and "[VIA:NET-BRIDGE:v0100]" in src
        and not re.search(r"^\s*(import|from)\s+(talib|requests)", src, re.M)
        and not re.search(r"^\s*os\.environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", src, re.M))
    print(f"{TAG} selftest {len(ok)}/{len(ok) + len(bad)}" + (" · 不過:" + " · ".join(bad) if bad else ""), flush=True)
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
