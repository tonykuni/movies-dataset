#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL135_EnvGovernance v0118 — 薄尾:spaCy 模型件改指官方 wheel 網址(PyPI 上沒有,uv 解析必紅)

操作員 2026-10-04「完成後請 VCGC 檢查 VCGC 及 VRN VDF 所有工具環境無衝突安裝完畢」。ENV 劇本 E07(via-envgov run)量到:
  S02 家族 nlp → via_nlp 整包 36 件模擬 RED,唯一原因 = zh-core-web-sm==3.8.0 —— spaCy 模型不在 PyPI,
  只在 github.com/explosion/spacy-models 的 release 發 wheel(uv:「there is no version of zh-core-web-sm==3.8.0」)。
  本版只換 _pins_for_bundle 的輸出:{lang}_core_web_* · {lang}_core_news_* · {lang}_dep_news_trf · xx_ent_wiki_sm · xx_sent_ud_sm
  這類模型件,有 base 現版 → 換成同版本的官方 wheel 網址(裸網址:sh / ps1 段檔不必引號,uv pip compile / install 都吃);
  沒有版本 → 照舊(誠實紅,不猜版本)。其餘判準、段冊、模擬、apply 閘、移除候裁全照 v0117。
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
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL135_EnvGovernance"


def _vnum_v0118(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0118(p) < _vnum_v0118(__file__)), key=_vnum_v0118)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"
_PINS_V0117 = PRIOR._pins_for_bundle
SPACY_MODEL_RX = re.compile(r"^(?:[a-z]{2}|xx)[-_](?:core[-_](?:web|news)[-_](?:sm|md|lg|trf)|dep[-_]news[-_]trf|ent[-_]wiki[-_]sm|sent[-_]ud[-_]sm)$")
SPACY_WHEEL = "https://github.com/explosion/spacy-models/releases/download/{n}-{v}/{n}-{v}-py3-none-any.whl"


def __getattr__(name):
    return getattr(PRIOR, name)


def spacy_pin_v0118(pin: str) -> str:
    """name==ver 且 name 是 spaCy 模型 → 官方 wheel 裸網址;其他原樣。"""
    m = re.match(r"^([A-Za-z0-9_.-]+)==([0-9][0-9A-Za-z.+-]*)$", pin.strip())
    if not m or not SPACY_MODEL_RX.match(m.group(1).lower()):
        return pin
    n = re.sub(r"[-.]+", "_", m.group(1).lower())
    return SPACY_WHEEL.format(n=n, v=m.group(2))


def _pins_for_bundle(bundle, dists, baseline, skips):
    pins, dropped = _PINS_V0117(bundle, dists, baseline, skips)
    return [spacy_pin_v0118(p) for p in pins], dropped


def _install_v0118() -> None:
    PRIOR._pins_for_bundle = _pins_for_bundle         # build_plan / OCR 包都從模組層找它


_install_v0118()


def selftest() -> int:
    PRIOR._pins_for_bundle = _PINS_V0117
    try:
        rc0 = PRIOR.selftest()
    finally:
        _install_v0118()
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print(f"=== {TAG} · 薄尾自測(spaCy 模型件 → 官方 wheel 網址)===")
    chk("① v0117 自測過", rc0 == 0, f"rc {rc0}")
    u = spacy_pin_v0118("zh-core-web-sm==3.8.0")
    chk("② zh-core-web-sm==3.8.0 → 官方 wheel 裸網址(同版本;沒有空白 / 引號)",
        u == "https://github.com/explosion/spacy-models/releases/download/zh_core_web_sm-3.8.0/zh_core_web_sm-3.8.0-py3-none-any.whl" and " " not in u, u)
    keep = [spacy_pin_v0118(p) for p in ("spacy==3.8.16", "zh-core-web-sm", "numpy==2.4.6", "core-web-sm==1.0", "en_core_web_trf==3.8.0")]
    chk("③ 非模型件 · 沒版本的模型件 照原樣(不猜版本);en_core_web_trf 也換",
        keep[:4] == ["spacy==3.8.16", "zh-core-web-sm", "numpy==2.4.6", "core-web-sm==1.0"] and keep[4].endswith("/en_core_web_trf-3.8.0-py3-none-any.whl"), keep)
    b = {"members": ["spacy", "zh-core-web-sm"], "install": ["spacy", "zh-core-web-sm"]}
    pins, dropped = PRIOR._pins_for_bundle(b, {"spacy": {"ver": "3.8.16"}, "zh-core-web-sm": {"ver": "3.8.0"}}, {}, {})
    chk("④ 換裝:v0117 的 build_plan 走本版 _pins_for_bundle(模組層)", PRIOR._pins_for_bundle is _pins_for_bundle
        and pins == ["spacy==3.8.16", u] and dropped == [], pins)
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑤ 加速器橋 · 網路橋(def _via_net)在;不碰 TA-Lib;不寫同意閘", "[VIA:ACCEL-BRIDGE" in text and "def _via_net" in text
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M) and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", text))
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · v0117 {'PASS' if rc0 == 0 else 'FAIL'} · 合計 {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        return selftest()
    return PRIOR.main()


if __name__ == "__main__":
    raise SystemExit(main())
