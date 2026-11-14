#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VRN2_Workbench v0111 — v0110 薄尾(v0110 與它的前版一字不改):寬螢幕外觀鎖定不動 · 窄螢幕不溢出 · 控制項都有可讀名稱。

操作員 2026-11-04:「HTML U/I 的目前視覺鎖定 · 但其他優化功能可加入」+ 交付的 VIA HTML UI 跨裝置測試規格(4 種視窗 desktop 1920 / laptop 1440 /
tablet 768 / mobile 390 · 頁寬不超過視窗 · 按鍵與表單控制項都要有可讀名稱 · 會橫向溢出的表格要在可捲動的容器內 · 0 外連 · 0 主控台錯誤)。
v0110 在 4 種視窗實量:desktop / laptop 全過;tablet 頁面橫向溢出 201px(頁首右側那行路徑不斷行 · 左右兩欄在 768px 還並排)、mobile 溢出 11px
(去重矩陣表格 374px 放不進 340px 又沒有捲動容器);匯出格式下拉選單 + 檔案勾選框沒有可讀名稱。
v0111 只加兩段:
  ① CSS(id="wb111-tpl")全部包在 @media (max-width:999px) 裡 → 視窗 1000px 以上一個像素都不變(視覺鎖定 · 自測 + 瀏覽器截圖逐像素比對);
     999px 以下:左右兩欄改上下排、頁首那行路徑可斷行、各頁區塊內的寬表格在區塊裡橫向捲動(頁面本身不再橫向溢出)。不碰分頁列(main > div.bar)。
  ② 腳本(id="wb111-dom"):沒有可讀名稱的按鍵 / 選單 / 勾選框補 aria-label(看不見 · 只給讀屏與自動測試用):匯出格式選單 =「匯出格式 Export format」·
     勾選框 =「勾選 <該列報告名稱>」· 只有圖示的按鍵用它的 title / data-act。內容、資料、匯出一字不改。
動詞同前版:render · logo · --selftest。
"""
from __future__ import annotations

import hashlib
import importlib.util
import re
import sys
from pathlib import Path

VERSION = "v0111"
DISPLAY_NAME = "VRN2_Workbench"
PRIOR_NAME = "VRN2_Workbench_v0110.py"
HERE = Path(__file__).resolve().parent


def _load_prior():
    path = HERE / PRIOR_NAME
    if not path.is_file():
        raise FileNotFoundError("前版 %s 不在 %s" % (PRIOR_NAME, HERE))
    spec = importlib.util.spec_from_file_location("vrn2_workbench_prior_v0110", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


PRIOR = _load_prior()               # v0110
NARROW_PX = 999

_CSS = """<style id="wb111-tpl">/* VRN2_Workbench v0111 · 只在 999px 以下生效(寬螢幕外觀鎖定)· 不碰分頁列 .bar */
@media (max-width:999px){
.layout{display:block!important;height:auto!important}
.layout>aside{width:auto!important;max-width:none!important;height:auto!important;max-height:none!important}
.layout>main{height:auto!important;overflow:visible!important;min-width:0}
header.vh{height:auto!important;flex-wrap:wrap!important}
header.vh .meta{flex:1 1 100%!important;min-width:0!important;margin-left:0!important;text-align:left!important;white-space:normal!important;overflow-wrap:anywhere!important;word-break:break-all!important}
section.tabsec .box,section.tabsec .matrix,section.tabsec .w9-wrap,main>.box,main .w9-wrap,aside .w9-wrap{max-width:100%;overflow-x:auto!important}
section.tabsec table,main>.box table{max-width:none}
}
</style>"""
CSS_SHA256 = "809fee287419fc4b13d0b975a0e112462443c957914db3fc66825fcb73c79929"      # 建置時填(鎖定:CSS 一改就對不上 → 自測紅 → 要出新版)

_DOM = r"""<script id="wb111-dom">(function(){
  function named(el){
    if (el.getAttribute('aria-label') || el.getAttribute('aria-labelledby') || el.getAttribute('title')) return true;
    if (el.labels && el.labels.length) return true;
    var t = (el.tagName === 'SELECT' || el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') ? '' : (el.textContent || '');
    return t.replace(/\s+/g, '').length > 0;
  }
  function rowName(el){
    var tr = el.closest('tr'); if (!tr) return '';
    var cells = tr.querySelectorAll('td'); for (var i = 0; i < cells.length; i++) { if (cells[i].contains(el)) continue; var s = (cells[i].textContent || '').trim(); if (s) return s.slice(0, 80); }
    return '';
  }
  function label(root){
    (root || document).querySelectorAll('select,input,textarea,button,a.action,[role="button"]').forEach(function(el){
      if (el.type === 'hidden' || named(el)) return;
      var name = '';
      if (el.id === 'fmt') name = '匯出格式 Export format';
      else if (el.type === 'checkbox') { var r = rowName(el); name = r ? ('勾選 ' + r) : '勾選 Select'; }
      else if (el.type === 'date') name = '日期 Date';
      else if (el.tagName === 'SELECT') name = '選項 Option';
      else if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') name = el.getAttribute('placeholder') || '輸入 Input';
      else name = el.getAttribute('data-act') || el.getAttribute('data-w10') || '按鍵 Button';
      el.setAttribute('aria-label', name);
    });
  }
  label(document);
  if (window.MutationObserver) {
    var pending = false;
    new MutationObserver(function(){ if (pending) return; pending = true; setTimeout(function(){ pending = false; label(document); }, 50); })
      .observe(document.body, {childList: true, subtree: true});
  }
})();</script>"""

MARK = "<!-- VRN2_Workbench %s over v0110 · 窄螢幕不溢出 · 可讀名稱 · 寬螢幕外觀不變 %s -->"


def augment111(page: str) -> tuple:
    """(頁面, 說明)· 純函式可測 · 重入不重複 · 不動 main > div.bar · 寬螢幕外觀不動。"""
    if 'id="wb111-tpl"' in page:
        return page, "已是 v0111"
    notes = []
    if "</head>" in page:                                       # 第一個 </head> 才是頁首結尾(頁內腳本字串裡也可能有這幾個字)
        page = page.replace("</head>", _CSS + "\n</head>", 1)
    else:
        notes.append("沒有 </head>(CSS 接在頁尾)")
        page = page + _CSS
    if page.count("</title>") >= 1:
        page = page.replace("</title>", "</title>" + MARK % (VERSION, CSS_SHA256[:12]), 1)
    at = page.rfind("</body>")                                  # 最後一個 </body> 才是頁尾
    page = page[:at] + _DOM + page[at:] if at >= 0 else page + _DOM
    return page, " · ".join(notes) or "窄螢幕(999px 以下)上下排 · 寬表格區塊內捲動 · 頁首路徑可斷行 · 控制項補可讀名稱 · 寬螢幕不變"


def render(root: Path, out_path: Path | None = None, logo: str | None = None, assets_zip: Path | None = None) -> Path:
    out = PRIOR.render(Path(root), out_path, logo, assets_zip)
    page = Path(out).read_text(encoding="utf-8")
    try:
        page, note = augment111(page)
    except Exception as error:  # noqa: BLE001  後處理失敗不毀 v0110 頁
        print("    [U/I] [YELLOW] Workbench v0111 後處理沒做成(v0110 頁照出):%s: %s" % (type(error).__name__, str(error)[:160]), flush=True)
        return Path(out)
    if note.startswith("沒有"):
        print("    [U/I] [YELLOW] Workbench v0111 · %s" % note, flush=True)
    tmp = Path(out).with_suffix(".v0111.tmp")
    tmp.write_text(page, encoding="utf-8")
    tmp.replace(Path(out))
    return Path(out)


# ── 自測 ──────────────────────────────────────────────────────────────────────────────────────────────
def selftest() -> int:
    import contextlib
    import io
    fails = []

    def chk(label, cond):
        print("[%s] %s" % ("PASS" if cond else "FAIL", label))
        if not cond:
            fails.append(label)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc_prior = PRIOR.selftest()
    chk("① 前版 v0110 自測照過(%s)" % (buf.getvalue().strip().splitlines() or ["—"])[-1][:60], rc_prior == 0)
    src = Path(__file__).read_text(encoding="utf-8")
    css_sha = hashlib.sha256(_CSS.encode("utf-8")).hexdigest()
    body = _CSS.split(">", 1)[1].rsplit("</style>", 1)[0]
    body_nc = re.sub(r"/\*.*?\*/", "", body, flags=re.S).strip()
    one_media = body_nc.startswith("@media (max-width:%dpx){" % NARROW_PX) and body_nc.endswith("}") and body_nc.count("@media") == 1
    inner = body_nc[len("@media (max-width:%dpx){" % NARROW_PX):-1]
    sel = re.sub(r"\{[^}]*\}", "\n", inner)
    colors = re.findall(r"#[0-9a-fA-F]{3,6}\b", _CSS)
    chk("② 鎖定:CSS SHA-256 = 釘住的值 · 整段只在一個 @media (max-width:999px) 裡(1000px 以上外觀一像素不變)· 不加顏色 / 字級 · 第 3 行加速器標記",
        css_sha == CSS_SHA256 and one_media and not colors and "font-size" not in _CSS and "font:" not in _CSS and src.splitlines()[2].strip() == "# [VIA:ACCEL-BRIDGE:v0111]")
    chk("③ 分頁列(main > div.bar · 操作員鎖定)一個選擇器都不碰 · 窄螢幕規則只動版面(上下排 · 區塊內捲動 · 頁首路徑斷行)",
        ".bar" not in sel and not re.search(r"\.tabs(?!ec)", sel) and "overflow-x:auto" in inner and ".layout{display:block" in inner)
    page = ("<html lang=\"zh-Hant\"><head><title>x</title><style>.bar{}</style></head><body><header class=\"vh\"><h1>t</h1><div class=\"meta\">m</div></header>"
            "<div class=\"layout\" id=\"layout\"><aside></aside><main><div class=\"bar\"><select id=\"fmt\"><option>CSV</option></select></div>"
            "<section class=\"tabsec\"><div class=\"matrix\"><table><tr><td><input type=\"checkbox\"></td><td>a.pdf</td></tr></table></div></section></main></div></body></html>")
    got, note = augment111(page)
    tricky = page.replace("</section>", "</section><script>var a='<html><head></head><body></body></html>';</script>", 1)   # 頁內腳本(在 body 裡)字串含這幾個字
    got2, note2 = augment111(tricky)
    chk("④ 頁面:CSS 在第一個 </head> 前 · 腳本在最後一個 </body> 前(頁內腳本字串有這幾個字也不放錯)· 版號註記 · 原內容一字不少(只多三段)· 重入不重複",
        got.count('id="wb111-tpl"') == 1 and got.index('id="wb111-tpl"') < got.index("</head>") and got.count('id="wb111-dom"') == 1
        and got.index('id="wb111-dom"') < got.index("</body>") and (MARK % (VERSION, CSS_SHA256[:12])) in got
        and got.replace(_CSS + "\n", "", 1).replace(_DOM, "", 1).replace(MARK % (VERSION, CSS_SHA256[:12]), "", 1) == page
        and augment111(got)[0] == got and note.startswith("窄螢幕")
        and got2.index('id="wb111-tpl"') < got2.index("<body>") and got2.rindex("</body>") > got2.index('id="wb111-dom"') > got2.index("<script>var a=") and note2.startswith("窄螢幕"))
    chk("⑤ 腳本:只補 aria-label(看不見)· 匯出格式選單 / 勾選框(用該列報告名稱)/ 只有圖示的按鍵 · 不改文字 · 不改資料 · 不連外",
        "aria-label" in _DOM and "匯出格式 Export format" in _DOM and "'勾選 ' + r" in _DOM and ".textContent =" not in _DOM and "innerHTML" not in _DOM
        and "VRN2_DATA" not in _DOM and not re.search(r"fetch\(|XMLHttpRequest|https?://", _DOM))
    print("[%s] %s %s 自測 %s(5 項)" % ("GREEN" if not fails else "RED", DISPLAY_NAME, VERSION, "全過" if not fails else "不過:%s" % "; ".join(fails)))
    return 0 if not fails else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in argv:
        return selftest()
    if argv and argv[0] == "logo":
        return PRIOR.main(argv)
    import argparse
    import os
    ap = argparse.ArgumentParser(prog="VRN2_Workbench_v0111")
    ap.add_argument("verb", nargs="?", default="render")
    ap.add_argument("--root", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--logo", default=None)
    a = ap.parse_args(argv)
    if a.verb != "render":
        return PRIOR.main(argv)
    root = Path(a.root) if a.root else (os.environ.get("VIA_ROOT") and Path(os.environ["VIA_ROOT"])) or HERE.parent.parent
    path = render(root, a.out, a.logo)
    print("[GREEN] %s %s(前版 v0110)· %s" % (DISPLAY_NAME, VERSION, path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
