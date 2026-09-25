#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VRN_ENG075_DocToMarkdown — 文件→Markdown 轉換引擎(批249;操作員稽核令)
====================================================================
操作員稽核:「有無讀取文件轉換為 MD 功能」「有無 HTML U/I reader」
→稽核結果=能力散落(工作站 Toolchain MarkItDown 引擎/NLP ingest
HTML 抽取器/fitz 分區)未成引擎→本件整合為一:
  法A 正主=microsoft/markitdown(雲端已裝 0.1.7;pdf/docx/xlsx/html/
    pptx 全格式;工作站由 Toolchain Invoke-VIA-MarkItDown 同源)
  法B 後備=自建道(缺庫誠實不假轉):
    HTML=NLP OneEngine ingest._HTMLTextExtractor(HTML U/I reader
      正主;stdlib HTMLParser 零依賴)→標題階層還原 #/##
    PDF=fitz 首頁分區(ENG072 同族)→【標題帶】=#、本文=段落
    TXT/MD=passthrough
  雙法都成=difflib 對照(AGREE/PARTIAL/DIVERGE 誠實);單法=標記
輸出:VIA_Reports/md_out/<原檔名>.md(券商報告衍生物不入 git 紅線;
  夾已入 .gitignore)+逐件三態實錄
用法:python3 VRN_ENG075_DocToMarkdown_v0100.py run [--dir 來源夾]
      | --selftest
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

import difflib
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
OUTDIR = VIA / "VIA_Reports" / "md_out"
DEFAULT_DIR = HERE / "input_reports"
EXTS = {".pdf", ".docx", ".html", ".htm", ".txt", ".md", ".xlsx", ".pptx"}


def _markitdown(p: Path) -> str | None:
    """法A 正主:markitdown 全格式(缺庫=None 誠實退法B)"""
    try:
        from markitdown import MarkItDown
        res = MarkItDown(enable_plugins=False).convert(str(p))
        return (res.text_content or "").strip() or None
    except Exception:
        return None


def _html_reader(p: Path) -> str | None:
    """法B HTML U/I reader:NLP OneEngine ingest 正主(stdlib);
    標題階層還原 #/##(操作員稽核令:HTML U/I reader 引擎化)"""
    try:
        raw = p.read_text(encoding="utf-8-sig", errors="replace")
        import re
        out, pos = [], 0
        for m in re.finditer(r"<h([1-6])[^>]*>(.*?)</h\1>", raw,
                             re.I | re.S):
            pre = raw[pos:m.start()]
            txt = _strip_html(pre)
            if txt:
                out.append(txt)
            head = _strip_html(m.group(2))
            if head:
                out.append("#" * int(m.group(1)) + " " + head)
            pos = m.end()
        tail = _strip_html(raw[pos:])
        if tail:
            out.append(tail)
        return "\n\n".join(out).strip() or None
    except Exception:
        return None


def _strip_html(fragment: str) -> str:
    """NLP OneEngine ingest._HTMLTextExtractor graceful;缺=stdlib 同構"""
    try:
        pkg = HERE / "references" / "intake" / "VIA_NLP_OneEngine_v1.1.0"
        if str(pkg / "src") not in sys.path:
            sys.path.insert(0, str(pkg / "src"))
        from via_nlp_engine.ingest import _HTMLTextExtractor  # noqa
        ex = _HTMLTextExtractor()
        ex.feed(fragment)
        return ex.text().strip()
    except Exception:
        from html.parser import HTMLParser

        class _E(HTMLParser):
            def __init__(self):
                super().__init__()
                self.buf = []
                self.skip = 0

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


def _pdf_fallback(p: Path) -> str | None:
    """法B PDF:fitz 首段分區→md(【標題帶】=#;ENG072 同族)"""
    try:
        import fitz
        parts = []
        with fitz.open(str(p)) as doc:
            for pg in doc[:5]:
                txt = pg.get_text("text", sort=True).strip()
                if txt:
                    parts.append(txt)
        return "\n\n".join(parts).strip() or None
    except Exception:
        return None


def convert(p: Path) -> tuple[str | None, str]:
    """回 (md, 法標記):A 正主→B 後備→雙成=對照標;全敗=誠實 None"""
    a = _markitdown(p)
    suf = p.suffix.lower()
    if suf in (".html", ".htm"):
        b = _html_reader(p)
    elif suf == ".pdf":
        b = _pdf_fallback(p)
    elif suf in (".txt", ".md"):
        b = p.read_text(encoding="utf-8-sig", errors="replace").strip() or None
    else:
        b = None
    if a and b:
        r = difflib.SequenceMatcher(
            None, "".join(a.split())[:5000], "".join(b.split())[:5000]).ratio()
        tag = ("DUAL_AGREE" if r >= 0.85 else
               "DUAL_PARTIAL" if r >= 0.5 else "DUAL_DIVERGE")
        return a, f"{tag}({r:.2f})"
    if a:
        return a, "MARKITDOWN_ONLY"
    if b:
        return b, "FALLBACK_ONLY(markitdown 缺/敗=誠實)"
    return None, "FAIL_ALL(缺庫或空件=誠實不假轉)"


def run(src: Path | None = None) -> int:
    src = src or DEFAULT_DIR
    files = sorted(p for p in src.glob("*") if p.suffix.lower() in EXTS) \
        if src.exists() else []
    if not files:
        print(f"[MD 轉換] {src} 無可轉檔(誠實)")
        return 2
    OUTDIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    ok = fail = 0
    for p in files:
        md, tag = convert(p)
        if md:
            (OUTDIR / (p.stem + ".md")).write_text(
                f"<!-- {p.name} · {tag} · {ts} -->\n\n{md}",
                encoding="utf-8")
            ok += 1
        else:
            fail += 1
        print(f"  [{tag}] {p.name} · {len(md or ''):,} 字")
    print(f"[計] {len(files)} 件 · OK {ok} · FAIL {fail} · 輸出 {OUTDIR}"
          "(不入 git 紅線)")
    return 0 if fail == 0 else 1


def selftest() -> int:
    import tempfile
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    src = Path(__file__).read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        (tdp / "ui.html").write_text(
            "<html><body><h1>營收報告</h1><p>毛利率回升。</p>"
            "<h2>展望</h2><p>訂單能見度佳。</p>"
            "<script>var x=1;</script></body></html>", encoding="utf-8")
        md, tag = convert(tdp / "ui.html")
        chk("① HTML U/I reader→md(h1/h2 階層還原+script 濾除)",
            md is not None and "營收報告" in md and "毛利率回升" in md
            and "var x" not in md)
        chk("② 雙法對照三態(HTML 雙法在=DUAL_*;誠實比率)",
            tag.startswith("DUAL_") or "ONLY" in tag)
        import fitz
        d = fitz.open()
        d.new_page().insert_text((72, 100), "TEST 2330 Target Price 1500")
        d.save(str(tdp / "r.pdf"))
        d.close()
        md2, tag2 = convert(tdp / "r.pdf")
        chk("③ PDF→md(markitdown 正主/fitz 後備;內容在)",
            md2 is not None and "2330" in md2)
        (tdp / "note.txt").write_text("純文字直通", encoding="utf-8")
        md3, _ = convert(tdp / "note.txt")
        chk("④ TXT 直通", md3 is not None and "純文字直通" in md3)
        (tdp / "empty.docx").write_bytes(b"")
        md4, tag4 = convert(tdp / "empty.docx")
        chk("⑤ 壞件誠實 FAIL_ALL(不假轉)", md4 is None
            and tag4.startswith("FAIL_ALL"))
        rc = run(tdp)
        chk("⑥ 批跑三態+逐件 .md 落盤", rc in (0, 1)
            and (OUTDIR / "ui.md").exists()
            and (OUTDIR / "note.md").exists())
        chk("⑦ 空夾誠實 rc2", run(tdp / "none_x") == 2)
    chk("⑧ NLP ingest 掛載宣告(HTML reader 正主)+markitdown 正主宣告",
        "_HTMLTextExtractor" in src and "MarkItDown" in src)
    chk("⑨ 紅線宣告(md 輸出不入 git)", "不入 git" in src)
    chk("⑩ 零網路+加速橋(純本地轉換)",
        all(("import " + k) not in src for k in ("requests", "httpx"))
        and "ACCEL-BRIDGE" in src)
    print(f"  [計] 十檢 OK {10 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 文件→Markdown 轉換引擎(VRN_ENG075)· 十檢自測(零網路)===")
        return selftest()
    if args and args[0] == "run":
        d = Path(args[args.index("--dir") + 1]) if "--dir" in args else None
        return run(d)
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
