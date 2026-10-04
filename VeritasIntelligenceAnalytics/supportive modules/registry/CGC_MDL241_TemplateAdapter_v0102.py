#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""CGC_MDL241_TemplateAdapter v0102 — 薄尾:燈色修正(操作員 2026-10-03:矩陣「標黃燈卻是灰燈」→ 亮色燈;紅燈慢閃)

根因(AST):v0100 `lamp()` 的對映表沒有 YELLOW 這個鍵 → 落到 UNTESTED(灰 #64748b);GATED / ABSENT 同樣落灰。全景(MDL247)、全檢(MDL248)
都經 kit.lamp() 畫燈,所以六族矩陣的黃全變灰。
本尾版:① lamp():YELLOW / STALE / PARTIAL / AMBER / FINDING → SKIP(黃);GATED / ABSENT / DORMANT / HOLD → UNTESTED(灰);NODATA → 青(新類)
        ② css():在前版 CSS 後**追加** VIA_UI_FormatLock 尾版的 lamp_css(亮色填色 · 紅燈 via-blink 1.8s · reduced-motion 關閃)
前版 plan / apply / spec / sync / watch 一字不動;換的是擁有者層的兩個名字,MDL247 / 248 不必改。
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
import html as _html, importlib.util, json, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL241_TemplateAdapter"
ENGINE = _STEM + "_v0102"


def _vnum(p: Path) -> int:
    m = re.search(r"_v(\d+)$", p.stem)
    return int(m.group(1)) if m else -1


_PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location("mdl241_prior_for_" + Path(__file__).stem, _PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    return getattr(PRIOR, name)


_OWNER = PRIOR
while hasattr(_OWNER, "PRIOR") and "lamp" not in vars(_OWNER):
    _OWNER = _OWNER.PRIOR
_ORIG_LAMP, _ORIG_CSS = _OWNER.lamp, _OWNER.css

LAMP_MAP = {"GREEN": "OK", "OK": "OK", "PASS": "OK",
            "YELLOW": "SKIP", "AMBER": "SKIP", "STALE": "SKIP", "PARTIAL": "SKIP", "FINDING": "SKIP", "REVIEW": "SKIP", "WARN": "SKIP",
            "RED": "FAIL", "FAIL": "FAIL", "ERROR": "FAIL",
            "NODATA": "NODATA", "N/A": "UNTESTED", "GATED": "UNTESTED", "ABSENT": "UNTESTED", "DORMANT": "UNTESTED", "HOLD": "UNTESTED", "SKIP": "UNTESTED", "UNTESTED": "UNTESTED"}
FALLBACK_CSS = ("@keyframes via-blink{0%,100%{opacity:1}50%{opacity:.25}}.via-lamp,.lamp{display:inline-block;width:12px;height:12px;border-radius:50%;vertical-align:middle;margin-right:4px;border:1px solid rgba(0,0,0,.15)}"
                ".via-lamp.OK,.lamp.GREEN{background:#16a34a}.via-lamp.SKIP,.lamp.YELLOW{background:#f59e0b}.via-lamp.FAIL,.lamp.RED{background:#dc2626;animation:via-blink 1.8s ease-in-out infinite}"
                ".via-lamp.UNTESTED,.lamp.GRAY{background:#9ca3af}.via-lamp.NODATA,.lamp.NODATA{background:#0891b2}@media (prefers-reduced-motion: reduce){.via-lamp.FAIL,.lamp.RED{animation:none}}")


def _lamp_css() -> str:
    """FormatLock 尾版的 lamp_css;冊不在或沒這欄 → 內建同內容(誠實 fallback,不假綠)。"""
    try:
        books = sorted(HERE.glob("VIA_UI_FormatLock_v*.json"), key=_vnum)
        if books:
            d = json.loads(books[-1].read_text(encoding="utf-8"))
            if d.get("lamp_css"):
                return d["lamp_css"]
    except Exception:
        pass
    return FALLBACK_CSS


def lamp(state: str, text: str = "") -> str:
    k = LAMP_MAP.get(str(state).upper(), "UNTESTED")
    return f"<span class='via-lamp {k}'></span>{_html.escape(str(text or state))}"


def css(sp: dict | None = None) -> str:
    return _ORIG_CSS(sp) + _lamp_css()


_OWNER.lamp = lamp
_OWNER.css = css


def selftest() -> int:
    ok = []
    def chk(name, cond, note=""):
        ok.append(bool(cond)); print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + note) if note else ''}")
    chk("① 根因重現:前版 YELLOW → UNTESTED(灰)", "UNTESTED" in _ORIG_LAMP("YELLOW"))
    chk("② 本版 YELLOW / STALE / PARTIAL → SKIP(黃)", all("via-lamp SKIP" in lamp(s) for s in ("YELLOW", "STALE", "PARTIAL")))
    chk("③ GATED / ABSENT / DORMANT → 灰 · NODATA → 青 · RED → FAIL", "UNTESTED" in lamp("GATED") and "UNTESTED" in lamp("ABSENT") and "NODATA" in lamp("NODATA") and "FAIL" in lamp("RED"))
    c = css()
    chk("④ CSS 追加:紅燈慢閃 keyframes · 黃 #f59e0b · reduced-motion 關閃 · 前版 CSS 仍在", "via-blink" in c and "#f59e0b" in c and "prefers-reduced-motion" in c and ".via-lamp." in c and c.startswith(_ORIG_CSS()[:40]))
    chk("⑤ 擁有者層已換(MDL247 / 248 經 kit.lamp 自動走本版)", _OWNER.lamp is lamp and _OWNER.css is css)
    chk("⑥ 文字 HTML 轉義不變", "&lt;" in lamp("GREEN", "<x>"))
    chk("⑦ 加速器橋在", "VIA:ACCEL-BRIDGE" in Path(__file__).read_text(encoding="utf-8"))
    print(f"  [計] {ENGINE} 薄尾 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        return selftest()
    return PRIOR.main()


if __name__ == "__main__":
    raise SystemExit(main())
