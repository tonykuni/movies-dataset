#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SUP_MDL866 v0110 — 薄尾(v0109 以前一字不動):NLP · layout · markdown 整合成一支入口(只增不減)

操作員 2026-11-25:「同意 NLP layout markdown 在倉內整合成一支」「只要功能工具不衝突 · 不會沒人維護 · 只增不減 ·
  合併指令 · 最佳化 · 導入加速器 100% · 用 VCGC 工具完成」。
VCGC 量測(工具矩陣 CGC_MDL272 + 語法樹掃現役檔):
  · NLP 11 族、layout 十餘族、markdown 1 族;真正會執行、繞過入口直接掛收容件的:VRN_ENG072(nlp_hub / gle_hub 的退路)·
    VRN_ENG073(_nfkc 退路)· VRN_ENG075(_strip_html 寫死 v1.1.0)· VRN_ENG078(自己挑 OneEngine 尾版)· CGC_MDL108(寫死 v1.1.0)
本版做的事(都是「加」,前版的動詞與行為一字不動):
  ① 一支入口:nlp_hub() → SUP_MDL744 尾版 · layout_hub() / gle_hub() → SUP_MDL743 尾版 · markdown_hub() → SUP_MDL745 尾版;
     回傳的就是那三支模組本身(呼叫端原本用的方法一個不少 → 行為零變更),同一行程只載一次。
  ② 共用功能:text_processor() · normalize(s) · html_text(fragment) · gle() · md_sentences / md_blocks / md_tables(text)·
     hub_status();每一道缺席都誠實回 None / 空並留原因,退路照舊(stdlib)。
  ③ 動詞(合併指令,經 VCGC 中樞 via-nlp 叫):hub-status · normalize <文字> · html <檔> · md-blocks <檔> · gle-status;
     前版動詞(reconstruct · unified · scan · semantic · intake …)原樣轉交。
呼叫端改走本入口由各自的新版號做(VRN_ENG072 v0140 · VRN_ENG073 v0141 · VRN_ENG075 v0102 ·
  CGC_MDL108 v0101),入口不在就退回各自原路(只增不減)。VRN_ENG078 掛的是它自己收容夾的另一組 OneEngine(v1.6.1),
  改道會換版本 = 功能衝突 → 不改道,照前版(操作員「功能工具不衝突」)。收容件原地不動(凍結來源不改)。零網路。
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

import importlib.util
import json
import re
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "SUP_MDL866_VIAUnifiedNLPOrchestrator"
VERSION = "v0110"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):
    return getattr(PRIOR, name)


BACKENDS = {"nlp": "SUP_MDL744_NLPApplicationHub", "layout": "SUP_MDL743_GenericLayoutHub", "markdown": "SUP_MDL745_MarkdownStructureHub"}
_CACHE: dict = {}
_WHY: dict = {}


def _load_backend(key: str):
    """同一行程只載一次;以後端家族尾版的模組名註冊在 sys.modules(呼叫端用 glob 載同一支時也拿到同一個物件)。"""
    if key in _CACHE:
        return _CACHE[key]
    hits = sorted(HERE.glob(BACKENDS[key] + "_v*.py"), key=_vnum)
    mod = None
    if not hits:
        _WHY[key] = f"ABSENT:{BACKENDS[key]}_v*.py 不在 {HERE.name}"
    else:
        name = hits[-1].stem
        mod = sys.modules.get(name)
        if mod is None:
            try:
                sp = importlib.util.spec_from_file_location(name, hits[-1])
                mod = importlib.util.module_from_spec(sp)
                sys.modules[name] = mod
                sp.loader.exec_module(mod)
                _WHY[key] = ""
            except Exception as e:  # noqa: BLE001
                sys.modules.pop(name, None)
                mod = None
                _WHY[key] = f"{type(e).__name__}: {e}"[:200]
    _CACHE[key] = mod
    return mod


def nlp_hub():
    return _load_backend("nlp")


def layout_hub():
    return _load_backend("layout")


gle_hub = layout_hub


def markdown_hub():
    return _load_backend("markdown")


def nlp_package_dir():
    """744 掛的 OneEngine 收容夾(語意版號最大者);缺 = None。"""
    h = nlp_hub()
    try:
        d = h.newest() if h is not None else None
        return Path(d) if d else None
    except Exception as e:  # noqa: BLE001
        _WHY["nlp_package_dir"] = f"{type(e).__name__}: {e}"[:200]
        return None


def text_processor():
    h = nlp_hub()
    try:
        return h.text_processor() if h is not None else None
    except Exception as e:  # noqa: BLE001
        _WHY["text_processor"] = f"{type(e).__name__}: {e}"[:200]
        return None


def normalize(s: str) -> str:
    """NFKC 正規化:① 收容件 TextProcessor ② 744.nfkc ③ stdlib NFKC。"""
    tp = text_processor()
    if tp is not None:
        try:
            return tp.normalize(s)
        except Exception:  # noqa: BLE001
            pass
    h = nlp_hub()
    if h is not None and hasattr(h, "nfkc"):
        try:
            return h.nfkc(s)
        except Exception:  # noqa: BLE001
            pass
    return unicodedata.normalize("NFKC", s)


def _ingest_mod():
    if "ingest" in _CACHE:
        return _CACHE["ingest"]
    mod = None
    h = nlp_hub()
    try:
        d = Path(h.newest()) if h is not None and h.newest() else None
        src = d / "src" if d is not None and (d / "src" / "via_nlp_engine" / "ingest.py").is_file() else None
        if src is not None:
            if str(src) not in sys.path:
                sys.path.insert(0, str(src))
            from via_nlp_engine import ingest as mod  # noqa: PLC0415
    except Exception as e:  # noqa: BLE001
        _WHY["ingest"] = f"{type(e).__name__}: {e}"[:200]
        mod = None
    _CACHE["ingest"] = mod
    return mod


def html_text(fragment: str) -> str:
    """HTML → 純文字:① 收容件尾版 ingest._HTMLTextExtractor ② stdlib 同構(跳 script / style)。"""
    ing = _ingest_mod()
    if ing is not None and hasattr(ing, "_HTMLTextExtractor"):
        try:
            ex = ing._HTMLTextExtractor()
            ex.feed(fragment)
            return ex.text().strip()
        except Exception:  # noqa: BLE001
            pass
    from html.parser import HTMLParser

    class _E(HTMLParser):
        def __init__(self):
            super().__init__()
            self.buf, self.skip = [], 0

        def handle_starttag(self, tag, attrs):
            if tag in ("script", "style"):
                self.skip += 1

        def handle_endtag(self, tag):
            if tag in ("script", "style") and self.skip:
                self.skip -= 1

        def handle_data(self, d):
            if not self.skip and d.strip():
                self.buf.append(d.strip())
    e = _E()
    e.feed(fragment)
    return " ".join(e.buf).strip()


def gle():
    h = layout_hub()
    try:
        return h.gle() if h is not None and hasattr(h, "gle") else None
    except Exception as e:  # noqa: BLE001
        _WHY["gle"] = f"{type(e).__name__}: {e}"[:200]
        return None


def _md(fn: str, text: str) -> list:
    h = markdown_hub()
    try:
        return getattr(h, fn)(text) if h is not None and hasattr(h, fn) else []
    except Exception as e:  # noqa: BLE001
        _WHY["md_" + fn] = f"{type(e).__name__}: {e}"[:200]
        return []


def md_sentences(text: str) -> list:
    return _md("sentences", text)


def md_blocks(text: str) -> list:
    return _md("blocks", text)


def md_tables(text: str) -> list:
    return _md("tables", text)


def hub_status() -> dict:
    out = {"entry": f"{_STEM} {VERSION}", "accel": VIA_ACCEL is not None, "backends": {}}
    for k in BACKENDS:
        m = _load_backend(k)
        out["backends"][k] = {"module": getattr(m, "__name__", None), "file": Path(getattr(m, "__file__", "") or "").name or None,
                              "why": _WHY.get(k, "")}
    h = nlp_hub()
    try:
        out["nlp_package"] = Path(h.newest()).name if h is not None and h.newest() else None
    except Exception:  # noqa: BLE001
        out["nlp_package"] = None
    md = markdown_hub()
    try:
        out["markdown_package"] = (md.status().get("mount") or {}).get("dir_name") if md is not None else None
    except Exception:  # noqa: BLE001
        out["markdown_package"] = None
    g = gle()
    out["layout_engine"] = getattr(g, "__name__", None)
    out["text_processor"] = type(text_processor()).__name__ if text_processor() is not None else None
    out["why"] = {k: v for k, v in _WHY.items() if v}
    return out


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    if a[:1] == ["hub-status"]:
        print(json.dumps(hub_status(), ensure_ascii=False, indent=1))
        return 0
    if a[:1] == ["normalize"]:
        print(normalize(" ".join(a[1:])))
        return 0
    if a[:1] == ["html"] and len(a) > 1:
        print(html_text(Path(a[1]).read_text(encoding="utf-8", errors="replace")))
        return 0
    if a[:1] == ["md-blocks"] and len(a) > 1:
        print(json.dumps(md_blocks(Path(a[1]).read_text(encoding="utf-8", errors="replace")), ensure_ascii=False, indent=1))
        return 0
    if a[:1] == ["gle-status"]:
        g = gle()
        print(json.dumps({"layout_engine": getattr(g, "__name__", None), "dir": getattr(g, "_VIA_ENGINE_DIR", None),
                          "why": _WHY.get("layout") or _WHY.get("gle", "")}, ensure_ascii=False))
        return 0 if g is not None else 3
    return PRIOR.main(a)


def selftest() -> int:
    ok = bad = 0

    def chk(name, cond, note=""):
        nonlocal ok, bad
        ok += bool(cond)
        bad += not cond
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}", flush=True)

    st = hub_status()
    b = st["backends"]
    chk("① 一支入口掛三個後端(744 · 743 · 745 尾版)", all(b[k]["file"] for k in BACKENDS), json.dumps({k: v["file"] for k, v in b.items()}, ensure_ascii=False))
    chk("② 回傳的是後端模組本身(呼叫端原本的方法都在)", nlp_hub() is _CACHE["nlp"] and hasattr(nlp_hub(), "text_processor")
        and hasattr(layout_hub(), "gle") and hasattr(markdown_hub(), "blocks"))
    chk("③ 同一行程只載一次", nlp_hub() is nlp_hub() and layout_hub() is gle_hub())
    chk("④ normalize:全形 → 半形(收容件或 stdlib 皆同)", normalize("ＡＢＣ１２３") == "ABC123")
    chk("⑤ html_text:去標籤、跳 script", html_text("<p>台積電<b>2330</b></p><script>x=1</script>").replace(" ", "") == "台積電2330")
    blocks = md_blocks("# 標題\n\n| a | b |\n|---|---|\n| 1 | 2 |\n")
    chk("⑥ markdown 區塊(745 後端)", isinstance(blocks, list) and len(blocks) >= 1, f"({len(blocks)} 塊)")
    chk("⑦ 前版動詞仍在(只增不減)", all(hasattr(PRIOR, n) for n in ("reconstruct", "unified", "scan_folder", "semantic", "intake_status")))
    chk("⑧ 加速器橋執行時生效", VIA_ACCEL is not None)
    print(f"  [計] {_STEM} {VERSION} 自測 OK {ok} · FAIL {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
