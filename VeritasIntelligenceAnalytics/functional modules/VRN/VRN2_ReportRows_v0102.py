#!/usr/bin/env python3
r"""VRN2_ReportRows v0102 — 薄尾(v0100 · v0101 一字不動):HTML U/I 顯示名「VRN」;檔名 · 資料照舊是 VRN-2。

操作員令(2026-11-14):「VRN only exist in html ui」。
本支的報告頁(VRN2_ReportRows_latest.html)標題 / 頁首 / 來源說明看得到「VRN-2」(實跑:<title>VRN-2 報告一行一單位</title>)。
本版只換 v0100 模組上的 render_html 一個名字:畫好的頁面經 vrn_ui_label —— 看得到的文字 VRN-2 → VRN;
標籤屬性 · <script> · <style> · VRN-2_ 識別字 · VRN-1 不動。JSON / CSV / Parquet 的來源欄(VRN-2 主線)、檔名、路徑照舊。
其餘(轉接層 · 主線冊 · 非個股 v0310 · 原句驗證)全照 v0101。零網路 · 不碰 TA-Lib · 不讀寫同意閘。
用法同前:python VRN2_ReportRows_v0102.py run --pdf-dir <夾> --out <夾> · 自測 --selftest(本版 + 前版 v0101)。
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
    """統包唯一網路工具惰性載入;本檔的連網全經 MDL008 子行程改道。"""
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

_STEM = "VRN2_ReportRows"
import contextlib
import importlib.util
import os
import pathlib
import re
import sys
import tempfile
import warnings
from pathlib import Path

HERE = Path(__file__).resolve().parent
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"


def _vnum_tail(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_tail(p) < _vnum_tail(__file__)), key=_vnum_tail)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
with warnings.catch_warnings():
    warnings.simplefilter("ignore", SyntaxWarning)
    warnings.simplefilter("ignore", DeprecationWarning)
    _spec.loader.exec_module(PRIOR)


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def _own_src_ok() -> bool:
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    return ("[VIA:ACCEL-BRIDGE" in src and "[VIA:NET-BRIDGE" in src and "_CONSENT" not in body
            and not re.search(r"^\s*(import|from)\s+(CGC_|VRN_|VCGC|ta" + r"lib\b)", src, re.M))


class _Checks:
    def __init__(self):
        self.ok = []

    def __call__(self, name, cond, note=""):
        self.ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)[:300]) if (note and not cond) else ""), flush=True)

    def done(self) -> int:
        good = all(self.ok)
        print("[計] %s 薄尾 %d/%d · %s" % (TAG, sum(self.ok), len(self.ok), "PASS" if good else "FAIL"), flush=True)
        return 0 if good else 1


# ────────────────── HTML U/I 顯示名(操作員 2026-11-14:「VRN only exist in html ui」)──────────────────
# 只換「看得到的文字」:<title> / 標題 / 內文裡的 VRN-2 → VRN。標籤屬性(href / src / class / data-*)· <script> · <style> 不動;
# 後面接英數或底線的(VRN-2_xxx 這種識別字 / 檔名)不動;VRN-1 不動。檔名 · 路徑 · JSON / CSV 資料照舊是 VRN-2。
_UI_SPLIT = re.compile(r"(<script\b.*?</script\s*>|<style\b.*?</style\s*>|<!--.*?-->|<[^>]*>)", re.S | re.I)
_UI_NAME = re.compile(r"VRN-2(?![\w-])")


def vrn_ui_label(html: str) -> str:
    parts = _UI_SPLIT.split(html)
    for i in range(0, len(parts), 2):                     # 偶數段 = 標籤之間的文字
        parts[i] = _UI_NAME.sub("VRN", parts[i])
    return "".join(parts)


def ui_label_selftest(chk) -> None:
    src = ("<html><head><title>VRN-2 引擎矩陣</title><style>.x{content:'VRN-2'}</style></head><body>"
           "<h1 class='VRN-2'>VRN-2 引擎矩陣 · VRN-2 SystemManager v0274</h1><a href='VRN-2_x.html' data-k=\"VRN-2\">VRN-2 報告</a>"
           "<p>VRN-2_EngineMatrix_latest.json · VRN-1 借用 · VRN-2-alpha</p><script>var s='VRN-2';</script><!-- VRN-2 --></body></html>")
    out = vrn_ui_label(src)
    chk("U1 顯示名:<title> / <h1> / 連結文字的 VRN-2 → VRN",
        "<title>VRN 引擎矩陣</title>" in out and ">VRN 引擎矩陣 · VRN SystemManager v0274</h1>" in out and ">VRN 報告</a>" in out, out[:300])
    chk("U2 不動:標籤屬性 · <style> · <script> · 註解 · VRN-2_ 識別字 · VRN-1 · VRN-2-alpha",
        "class='VRN-2'" in out and "href='VRN-2_x.html'" in out and 'data-k="VRN-2"' in out and "content:'VRN-2'" in out
        and "var s='VRN-2'" in out and "<!-- VRN-2 -->" in out and "VRN-2_EngineMatrix_latest.json" in out and "VRN-1 借用" in out
        and "VRN-2-alpha" in out, out)
    chk("U3 冪等:再套一次不變 · 沒有 VRN-2 的頁原樣", vrn_ui_label(out) == out and vrn_ui_label("<p>VDF</p>") == "<p>VDF</p>")


P0 = PRIOR.P                                                    # v0101 釘的 v0100 本體(render_html / write_outputs 在這)
_RENDER_ORIG = P0.render_html


def render_html(rows: list, s: dict) -> str:
    return vrn_ui_label(_RENDER_ORIG(rows, s))


def install() -> None:
    P0.render_html = render_html


def uninstall() -> None:
    P0.render_html = _RENDER_ORIG


install()


def selftest() -> int:
    chk = _Checks()
    print("=== %s · 薄尾自測(HTML U/I 顯示名 VRN;零網路)===" % TAG, flush=True)
    ui_label_selftest(chk)
    rows = [{"file": "a.pdf", "row_no": 1, "row_key": "2330 台積電", "kind": "stock", "ticker": "2330", "rating": "買進",
             "target_price": "1000", "close_price": "900", "summary": ["營收年增"], "data_rows": [], "key_numbers": [], "tickers": [],
             "pages": [1], "status": "VERIFIED", "verified_sentences": 1, "summary_sentences": 1, "kind_zh": "個股",
             "broker": "X", "date": "2026-11-14", "lane_why": "VRN-2 主線 · 來源:VRN-2 主線"}]
    summ = {"lamp": "GREEN", "at": "2026-11-14T00:00:00", "reports": 1, "rows": 1, "by_kind": {"stock": 1}, "sentences": {"verified": 1, "total": 1}}
    with tempfile.TemporaryDirectory() as td:
        out = Path(td)
        P0.write_outputs(rows, summ, out)                       # v0100 寫頁 → 走本版 render_html
        page = (out / "VRN2_ReportRows_latest.html").read_text(encoding="utf-8")
        data = (out / "VRN2_ReportRows_latest.json").read_text(encoding="utf-8")
    vis = re.sub(r"<style\b.*?</style>", "", page, flags=re.S)
    chk("R1 報告頁(v0100 write_outputs 實寫):標題「VRN 報告一行一單位」· 頁首「VRN 報告擷取」· 來源說明 VRN 主線 · 看得到的字沒有 VRN-2",
        "<title>VRN 報告一行一單位</title>" in page and "<h1>VRN 報告擷取" in page and "VRN 主線" in page and "VRN-2" not in re.sub(r"<[^>]*>", " ", vis), page[:300])
    chk("R2 資料照舊:JSON 來源欄仍是「VRN-2 主線」(只改 HTML 顯示)", "VRN-2 主線" in data, data[:200])
    chk("R3 換裝在位:v0100 模組的 render_html 是本版", P0.render_html is render_html)
    chk("R4 兩座橋在 · 不匯入他系統程式 · 不碰 TA-Lib · 同意閘不讀不寫", _own_src_ok())
    uninstall()
    try:
        rc = PRIOR.selftest()
    finally:
        install()
    chk("R5 前版 v0101 自測 rc 0(本版換裝卸下)· 跑完又換上", rc == 0 and P0.render_html is render_html, rc)
    return chk.done()


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a or a[:1] == ["selftest"]:
        return selftest()
    install()
    return PRIOR.main(a)


if __name__ == "__main__":
    sys.exit(main())
