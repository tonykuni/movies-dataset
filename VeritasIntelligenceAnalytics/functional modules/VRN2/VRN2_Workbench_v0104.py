#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VRN2_Workbench v0104 — v0103 薄尾(v0103 / v0102 / v0101 / v0100 留著一字不改):介面名稱 VeritasReportNova · 印章 logo · 頁首依紅字大小調整。

操作員 2026-11-01:
  「呈現在 HTML U/I 上的子系統名稱還原為 VeritasReportNova · 成為 VRN 唯一系統」
  「印章 logo 為透明去背無框無特效 · 以紅字大小為依據跟 header 文字做 header 大小 logo 最佳化調節加入」(附印章圖:「理」+ 小印「窮理盡性」)

做法(只增不減 · 檔名 / 家族名 / 收據 / 輸出冊的值一個字都不改 · 只改畫面上的字):
  ① 名稱:畫面上的「VRN-2」→「VRN」(VeritasReportNova);頁首小字 VERITAS INTELLIGENCE ANALYTICS · VERITASREPORTNOVA · VRN WORKBENCH;分頁標題 VeritasReportNova · VRN Workbench。
     不改:檔名與指令(ActivateVRN-2_v####.py · VRN2_* · vrn2://)· 內嵌的輸出冊資料 window.VRN2_DATA(U/I 匯出的 CSV / JSON 必須跟輸出冊逐字相同)。
  ② 00 系統現況:VRN 是唯一的 VRN 系統 → 只讀互看只列 VDF · VCGC(VRN-1 那一列拿掉;左面板原有的 Gate 按鈕照舊不動)。
  ③ logo:本機沒有 VRN2_Logo.* 時用內建印章 VRN2_Logo_Seal_v0100.png(操作員 2026-11-01 附圖原樣 · 本來就是透明去背 · 只裁到印泥範圍 · 無框無特效無底色);
     有本機 logo 照舊用本機的(先後順序不變)。
  ④ 頁首依紅字大小:主印框(「理」那一方)上緣對齊頁首小字頂端、下緣對齊標語底端 → 主印框高 = 文字區塊高(瀏覽器載入 / 改變視窗大小時實量)·
     小印「窮理盡性」自然垂在右下;印章高 = 文字區塊高 ÷ 主印框佔比(內建印章 0.9068 · 本機 logo 視為 1)· 限 44 ~ 120px · 頁首高度跟著。
動詞同 v0103:render [--root] [--out] [--logo] · logo <來源> <輸出> · --selftest
[VIA:AST-CLASS] 類別 = 前端渲染器(VeritasReportNova 工作台 · 薄尾)· 入口 = ActivateVRN-2 收尾後 / RoundAll ⑤ 重渲染 / vrn2:// rerender / 本檔 CLI
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import sys
import tempfile
from pathlib import Path

VERSION = "v0104"
DISPLAY_NAME = "VRN2_Workbench"
PRIOR_NAME = "VRN2_Workbench_v0103.py"
HERE = Path(__file__).resolve().parent
SEAL = HERE / "VRN2_Logo_Seal_v0100.png"
SEAL_MAIN_FRAC = 0.9068          # 主印框高 ÷ 整張印章高(量自操作員附圖的 alpha:主印框 y 227–1015 · 全部 227–1096)
SYSTEM_NAME = "VeritasReportNova"
SHORT = "VRN"


def _load_prior():
    path = HERE / PRIOR_NAME
    if not path.is_file():
        raise FileNotFoundError("前版 %s 不在 %s" % (PRIOR_NAME, HERE))
    spec = importlib.util.spec_from_file_location("vrn2_workbench_prior_v0103", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


PRIOR = _load_prior()
for _name in dir(PRIOR):
    if not _name.startswith("__") and _name not in globals():
        globals()[_name] = getattr(PRIOR, _name)
V0101 = PRIOR.PRIOR.PRIOR          # v0103 → v0102 → v0101(render / find_logo 在這一層)

# ===== ③ logo:本機沒有 → 內建印章(先後順序不變)=====
_native_find_logo = V0101.find_logo


def find_logo(root, explicit):
    found = _native_find_logo(root, explicit)
    if found:
        return found
    return SEAL if SEAL.is_file() else None


V0101.find_logo = find_logo

# ===== ② 只讀互看只列 VDF · VCGC =====
_native_others = PRIOR.others


def others(root, data):
    return [o for o in _native_others(root, data) if o.get("sys") != "VRN-1"]


PRIOR.others = others

# ===== ① 名稱(只改畫面上的字)=====
_RE_NAME = re.compile(r"(?<![A-Za-z0-9_])VRN-2(?![0-9])")          # 不碰 ActivateVRN-2(前面是字母)· VRN2_ · vrn2://
_DATA_BLOCK = re.compile(r"<script>window\.VRN2_DATA = .*?</script>", re.S)


def rename_display(page: str) -> str:
    """畫面上的 VRN-2 → VRN;內嵌輸出冊資料(window.VRN2_DATA)原樣保留。"""
    parts, last = [], 0
    for m in _DATA_BLOCK.finditer(page):
        parts.append(_RE_NAME.sub(SHORT, page[last:m.start()]))
        parts.append(m.group(0))
        last = m.end()
    parts.append(_RE_NAME.sub(SHORT, page[last:]))
    return "".join(parts)


CSS_V0104 = r"""
/* v0104 操作員 2026-11-01:印章 logo(透明去背 · 無框無特效)· 主印框對齊頁首文字區塊 · 頁首高度跟著 */
header.vh{height:auto;min-height:var(--hd);align-items:center}
header.vh .logo.img{background:none!important;border:none!important;border-radius:0!important;box-shadow:none!important;padding:0!important;
  width:auto!important;height:var(--seal-main,56px)!important;overflow:visible;flex:none;align-self:center;position:relative;display:block!important}
header.vh .logo.img img{width:auto!important;height:var(--seal-full,62px)!important;max-width:none;object-fit:contain;display:block;filter:none!important;
  box-shadow:none!important;border:none!important;background:transparent!important;image-rendering:auto}
"""

JS_V0104 = r"""
<script>
(function(){
  var FRAC = %(frac)s, MIN = 44, MAX = 120;
  function fit(){
    var hd = document.querySelector('header.vh'), logo = hd && hd.querySelector('.logo.img'), txt = logo && logo.nextElementSibling;
    if (!logo || !txt) return;
    var r = txt.getBoundingClientRect(), main = Math.max(MIN, Math.min(MAX, Math.round(r.height)));
    hd.style.setProperty('--seal-main', main + 'px'); hd.style.setProperty('--seal-full', Math.round(main / FRAC) + 'px');
  }
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(fit);
  window.addEventListener('load', fit); var t; window.addEventListener('resize', function(){ clearTimeout(t); t = setTimeout(fit, 80); }); fit();
})();
</script>
"""

_A_TITLE = "<title>VRN-2 Workbench</title>"
_A_SMALL = "<small>VERITAS INTELLIGENCE ANALYTICS · VRN-2 WORKBENCH</small>"
_A_STYLE = "</style>"
_A_BODY = "</body>"
_A_SECT = "其他系統 · 只讀互看 · 四系統對等(VRN-1 · VRN-2 · VDF · VCGC)"
TAG = "<!-- VRN2_Workbench %s over v0103 -->" % VERSION


def render(root: Path, out_path: Path | None = None, logo: str | None = None, assets_zip: Path | None = None) -> Path:
    root = Path(root).resolve()
    out = PRIOR.render(root, out_path, logo, assets_zip)
    page = Path(out).read_text(encoding="utf-8")
    seal_used = 'class="logo img"' in page and (not logo) and _native_find_logo(root, None) is None and SEAL.is_file()
    frac = SEAL_MAIN_FRAC if seal_used else 1.0
    edits = ((_A_TITLE, "<title>%s · %s Workbench</title>%s" % (SYSTEM_NAME, SHORT, TAG)),
             (_A_SMALL, "<small>VERITAS INTELLIGENCE ANALYTICS · %s · %s WORKBENCH</small>" % (SYSTEM_NAME.upper(), SHORT)),
             (_A_SECT, "其他系統 · 只讀互看 · 三系統對等(%s · VDF · VCGC)" % SHORT),
             (_A_STYLE, CSS_V0104 + _A_STYLE),
             (_A_BODY, JS_V0104 % {"frac": frac} + _A_BODY))
    for anchor, new in edits:
        if page.count(anchor) != 1:
            raise RuntimeError("v0103 頁面錨點找不到(恰一次):%s(%d 次)" % (anchor[:50], page.count(anchor)))
        page = page.replace(anchor, new, 1)
    page = rename_display(page)
    tmp = Path(out).with_suffix(".tmp")
    tmp.write_text(page, encoding="utf-8")
    tmp.replace(Path(out))
    return Path(out)


def _region(page: str, start: str, end: str) -> str:
    i = page.index(start)
    return page[i:page.index(end, i)]


def selftest() -> int:
    bad = []

    def chk(label, cond):
        print("[%s] %s" % ("PASS" if cond else "FAIL", label))
        if not cond:
            bad.append(label)

    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        PRIOR.PRIOR._fixture_v0102(root)
        (root / "docs" / "handoff").mkdir(parents=True, exist_ok=True)
        json.dump({"lamp": "GREEN", "closeout_lamp": "YELLOW", "at": "2026-11-01T00:00:00Z", "summary": {"pending": 104}}, open(root / "docs" / "handoff" / "HANDOFF_latest.json", "w", encoding="utf-8"))
        ts = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")
        o = ts.sub("TS", Path(PRIOR.render(root, root / "wb.html")).read_text(encoding="utf-8"))
        n = ts.sub("TS", Path(render(root, root / "wb.html")).read_text(encoding="utf-8"))
        d_old = re.search(r"<script>window\.VRN2_DATA = .*?</script>", o, re.S).group(0)
        d_new = re.search(r"<script>window\.VRN2_DATA = .*?</script>", n, re.S).group(0)
        chk("① 輸出冊資料 window.VRN2_DATA 逐字不變(U/I 匯出 = 輸出冊)", d_old == d_new)
        vis = _DATA_BLOCK.sub("", n)
        chk("① 畫面上沒有「VRN-2」· 檔名 ActivateVRN-2 / VRN2_ / vrn2:// 照舊", "VRN-2" not in vis.replace("ActivateVRN-2", "") and "vrn2://" in n and "VRN2_" in n)
        chk("① 名稱:分頁標題 VeritasReportNova · VRN Workbench · 頁首小字 · h1 VeritasReportNova", "<title>VeritasReportNova · VRN Workbench</title>" in n
            and "VERITASREPORTNOVA · VRN WORKBENCH</small>" in n and "<h1>VeritasReportNova</h1>" in n)
        same = rename_display(_region(o, '<section class="tabsec" data-tab="overview">', "</main>")) == _region(n, '<section class="tabsec" data-tab="overview">', "</main>") \
            and rename_display(_region(o, "<aside>", "</aside>")) == _region(n, "<aside>", "</aside>")
        chk("② 原有功能不改:01 ~ 04 分頁與左面板 = v0103(只差畫面名稱)", same)
        mm = json.loads(re.search(r"window\.VRN2_SUMMARY = (\{.*?\}); window\.VRN2_SUMMARY\.rows", n, re.S).group(1))
        chk("② 00 只讀互看只列 VDF · VCGC(VRN 唯一)· 區標三系統對等", [x["sys"] for x in mm["others"]] == ["VCGC", "VDF"] and "三系統對等(VRN · VDF · VCGC)" in n)
        chk("③ 本機沒有 logo → 內建印章(data URI · 透明 PNG)· 無框無特效", SEAL.is_file() and '<div class="logo img"><img src="data:image/png;base64,' in n and "box-shadow:none!important" in CSS_V0104 and "filter:none!important" in CSS_V0104)
        (root / "VIA_Reports" / "vrn2" / "VRN2_Logo.png").write_bytes(SEAL.read_bytes())
        n2 = Path(render(root, root / "wb2.html")).read_text(encoding="utf-8")
        chk("③ 本機有 VRN2_Logo.png → 照舊用本機的(主印框佔比視為 1)", "var FRAC = 1.0," in n2 and "var FRAC = %s," % SEAL_MAIN_FRAC in n)
        chk("④ 頁首:主印框高 = 文字區塊高(實量 · 44 ~ 120px)· 印章高 = 主印框 ÷ 佔比", "--seal-main" in n and "Math.round(main / FRAC)" in n and "MIN = 44, MAX = 120" in n)
        chk("⑤ 標記 v0104 over v0103 · 00 頁仍是第一頁且開著", TAG in n and '<button class="active" data-act="tab" data-tab="summary">00 系統現況</button>' in n)
        try:
            from PIL import Image
            im = Image.open(SEAL).convert("RGBA")
            corner = [im.getpixel(p)[3] for p in ((0, 0), (im.width - 1, 0), (0, im.height - 1))]
            center = im.getpixel((int(im.width * 0.03), im.height // 2))   # 主印框左邊框
            seal_ok = max(corner) == 0 and center[3] > 200 and center[0] > 150 and center[1] < 120
        except Exception as error:  # noqa: BLE001
            seal_ok = SEAL.stat().st_size > 1000
            print("    (PIL 不在:只看檔案大小)", type(error).__name__)
        chk("③ 內建印章:角落透明 · 印泥紅 · 不加框", seal_ok)
    print("[%s] VRN2_Workbench %s --selftest · %d 項 · 不過 %d" % ("PASS" if not bad else "FAIL", VERSION, 10, len(bad)))
    return 0 if not bad else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in argv:
        return selftest()
    if argv and argv[0] == "logo":
        return PRIOR.main(argv)
    import argparse
    ap = argparse.ArgumentParser(prog="VRN2_Workbench_v0104")
    ap.add_argument("verb", nargs="?", default="render")
    ap.add_argument("--root", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--logo", default=None)
    a = ap.parse_args(argv)
    if a.verb != "render":
        return PRIOR.main(argv)
    root = Path(a.root) if a.root else (os.environ.get("VIA_ROOT") and Path(os.environ["VIA_ROOT"])) or HERE.parent.parent
    path = render(root, a.out, a.logo)
    print("[GREEN] %s %s · %s" % (DISPLAY_NAME, VERSION, path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
