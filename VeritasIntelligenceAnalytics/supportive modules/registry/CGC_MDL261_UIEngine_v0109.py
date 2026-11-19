#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL261_UIEngine v0109 — 薄尾:自測只驗本版自己管的(讀冊規則 · 轉接介面),不再重跑整條前版鏈

操作員 2026-11-19 22:10 裁定「甲」:尾版自測只驗本版與直接前版,舊版的交接案記成被尾版的案接手(VCGC-REQ236:seq-02)。
為什麼:v0100 ~ v0103 的自測釘著當時的世界(內建範本的版面 · VDF_MDL012 的尾版號 · 色票),在現在的樹上各有 1 ~ 6 項不過;
  每一版的自測又都重跑前版鏈,一路傳到 v0108(4/5)→ 七個交接案紅、串測一個紅站。功能沒有壞(執行面 v0108 的 ② ~ ⑤ 都過)。
本版只改自測這一件(v0100 … v0108 一字不動;build · 五頁 · 匯入 · design_book · design_css · main 的其餘動詞全部照前版):
  ① ② 用暫存夾裡的夾具冊驗 design_book / design_css 的規則(取尾版 · systems.VCGC 純量覆蓋 · 燈四色鎖定 · design.css 只收純 CSS)——不寫死任何一代的色值。
  ③ 真樹只看本引擎自己要的東西:模板冊找得到、token 不空、燈四色是鎖定值。
  ④ 直接前版(v0108)的公開名稱從本版都拿得到(TAILAPI);main 把自測以外的參數原樣交給前版。
  ⑤ 橋在 · 不碰 TA-Lib · 自測以外不寫檔。
前版鏈的自測沒有刪,要看仍可各自 --selftest;它們的結果不再算進本版。本檔只讀冊、不寫冊、不改他系統的檔(L120 / L123)。
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

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 全導入令;graceful 零行為變更) =====
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
    """統包唯一網路工具惰性載入;本檔零網路,橋只為全樹一致。"""
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
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL261_UIEngine"
SELF_ID = "VCGC"
BOOK_STEM_V0109 = "VIA_UI_Template_SSOT"
CSS_BAD_RX_V0109 = re.compile(r"<|@import|url\s*\(|https?:", re.I)
API_V0109 = ("design_book", "design_css", "typekit_book", "typekit_block", "main", "BASE", "TK_ROOT")   # 直接前版一定要拿得到的名稱


def _vnum_v0109(p) -> int:
    m = re.search(r"_v(\d+)$", Path(p).stem)
    return int(m.group(1)) if m else -1


def _prior_path_v0109() -> Path:
    """前版 = 同家族比本檔小的最大版號(不釘名,避免 PINVER)。"""
    me = _vnum_v0109(__file__)
    hits = [p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0109(p) < me]
    return max(hits, key=_vnum_v0109)


PRIOR_PATH = _prior_path_v0109()
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0109", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR.BASE
TK_ROOT = PRIOR.TK_ROOT


def __getattr__(name: str):
    """薄尾轉接:本版沒蓋的公開名稱照前版(TAILAPI)。"""
    return getattr(PRIOR, name)


TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv == ["--selftest"]:
        return selftest()
    return PRIOR.main(argv)


def _fixture_book_v0109(root: Path, ver: int, tokens: dict, vcgc: dict, css: str) -> None:
    reg = root / "supportive modules" / "registry"
    reg.mkdir(parents=True, exist_ok=True)
    (reg / ("%s_v%04d.json" % (BOOK_STEM_V0109, ver))).write_text(
        json.dumps({"tokens": tokens, "systems": {SELF_ID: vcgc}, "design": {"css": css}}, ensure_ascii=False), encoding="utf-8")


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print(f"=== {TAG} · 薄尾自測(只驗本版自己管的;前版鏈的自測不在這裡重跑)===")
    me = sys.modules[__name__]
    lamps = dict(me.LOCK_LAMPS_V0107)
    with tempfile.TemporaryDirectory(prefix="cgc261_v0109_") as td:
        a, b = Path(td) / "a", Path(td) / "b"
        _fixture_book_v0109(a, 100, {"bg": "old", "sys": "old"}, {}, "")
        _fixture_book_v0109(a, 101, {"bg": "shared-bg", "sys": "shared-sys", "lamp-red": "not-locked", "nested": {"x": 1}},
                            {"sys": "vcgc-sys", "note": "不該進 token", "theme_zh": "夾具", "list": [1]}, ".fx{margin:0}")
        d = me.design_book(a)
        t = d.get("tokens") or {}
        chk("① 夾具冊:取尾版 · systems.VCGC 純量蓋過共用 token · 巢狀 / 清單 / note 不進 token · 燈四色不管冊怎麼寫都是鎖定值",
            d.get("book") == BOOK_STEM_V0109 + "_v0101.json" and t.get("bg") == "shared-bg" and t.get("sys") == "vcgc-sys"
            and "nested" not in t and "note" not in t and "list" not in t and all(t.get(k) == v for k, v in lamps.items()) and d.get("theme") == "夾具",
            {k: t.get(k) for k in ("bg", "sys", "lamp-red")})
        css = me.design_css(d)
        _fixture_book_v0109(b, 100, {"bg": "x"}, {"sys": "y"}, ".fx{background:url(http://example.invalid/a.png)}")
        bad = me.design_book(b)
        none = me.design_book(Path(td) / "empty")
        chk("② design.css:純 CSS 照收並接在 :root{token} 後面;含 url( / http 的整段不收並寫原因;沒有冊照實說、不丟例外",
            ".fx{margin:0}" in css and "--bg:shared-bg" in css.replace(" ", "") and not CSS_BAD_RX_V0109.search(css)
            and bad.get("css") == "" and "不收" in str(bad.get("why")) and none.get("book") is None and "找不到" in str(none.get("why")))
    real = me.design_book()
    rt = real.get("tokens") or {}
    chk("③ 真樹:模板冊找得到(%s)· token 不空 · 燈四色是鎖定值(不比任何一代的色值)" % real.get("book"),
        str(real.get("book") or "").startswith(BOOK_STEM_V0109 + "_v") and len(rt) > len(lamps) and all(rt.get(k) == v for k, v in lamps.items()), len(rt))
    seen = []
    keep = PRIOR.main
    PRIOR.main = lambda argv=None: (seen.append(list(argv or [])), 0)[1]
    try:
        rc = main(["__v0109_probe__", "x"])
    finally:
        PRIOR.main = keep
    miss = [n for n in API_V0109 if not hasattr(me, n)] + [n for n in dir(PRIOR) if not n.startswith("_") and not hasattr(me, n)]
    chk("④ 直接前版 %s 的公開名稱從本版都拿得到(缺 %d)· main 把自測以外的參數原樣交給前版 · 跑完還原" % (PRIOR_PATH.stem, len(miss)),
        not miss and rc == 0 and seen == [["__v0109_probe__", "x"]] and PRIOR.main is keep, miss[:5])
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑤ 加速器橋 · 網路工具橋在;不碰 TA-Lib;自測以外不寫檔;本檔沒有任何色碼",
        "[VIA:ACCEL-BRIDGE" in text and "[VIA:NET-BRIDGE" in text and not re.search(r"^\s*(import|from)\s+talib", text, re.M)
        and ".write_text(" not in text.split("def _fixture_book_v0109", 1)[0] and not re.search(r"#[0-9a-fA-F]{6}\b", text))
    good = all(ok)
    print("  ── 前版鏈(v0100 … %s)的自測沒有在這裡跑;要看請各自 --selftest(交接冊 VCGC-REQ236:seq-02)" % PRIOR_PATH.stem.rsplit("_", 1)[-1])
    print(f"[{'PASS' if good else 'FAIL'}] {TAG} selftest · {sum(ok)}/{len(ok)}")
    return 0 if good else 1


if __name__ == "__main__":
    raise SystemExit(main())
