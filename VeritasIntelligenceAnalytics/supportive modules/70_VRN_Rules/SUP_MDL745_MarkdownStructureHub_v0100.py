#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""SUP_MDL745 · MarkdownStructureHub v0100 —— Markdown 結構重組收容件統轄橋

操作員 2026-09-12 上傳 `MarkdownEditingEngine_v1.2.0_FINAL.zip` 並令「這個檔案支援看看」。

**先查再造**(批435/批437 那一課,第四次):
  · 這一包與前三包不同——它**真的有庫裡沒有的東西**。
  · `engine/semantic_reconstruction.py` 969 行、**純 stdlib**(csv/hashlib/json/re/pathlib),
    不需要 Node/Rust/Go 也跑得起來;那三種語言是 MarkdownEditingEngine 的 lint 車道,
    結構重組這一段是純 Python。
  · 它做的正好是批436 文件結構層在做的事,而且做得比我細:
      def_classify_blocks      frontmatter/code/table/heading/list/quote/HTML/paragraph 先分類再切
      def_period_is_boundary   句點是不是**真的**句界(版本號 v1.2.0、小數 41.43、縮寫 Inc. 都不是)
      def_split_sentences      中英句尾 + 收尾引號/括號狀態機
      def_analyze_tables       表頭/分隔列/逐列欄數/matrix SHA-256 驗證
      def_build_information_units  narrative/definition/action/metric/key_value/table_record

它的門規 `split-first-merge-never`——「可證明的結構邊界可以切開;**不自動**把句子、
標題或表格資料格接在一起」——與批436 操作員令「接斷句直到句號」看似衝突,其實不是:
我接的是**同一句被 PDF 換行切斷**的碎片,不是把兩句接成一句;而且標題本來就不參與接句。
真正要借的是它的**句界判定**:批436 的 `buf[-1] in "。.!?"` 會把
「報告日期:2025.12.」當成句尾——那是日期不是句號。

紀律:
  · 收容件原地不動(不改它一個位元;MANIFEST.sha256 隨包保留)
  · 零網路、零彈窗
  · 掛不上就誠實回 ABSENT/FAILED 並講出因由——不靜默退後備(批419e)
  · 尾版律:同名多版取語意版號最大者
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
INTAKE = VIA / "functional modules" / "VRN" / "references" / "intake"

MODULE_ID = "SUP_MDL745"
HUB_NAME = "MarkdownStructureHub"
HUB_VERSION = "v0100"
PKG_GLOB = "MarkdownEditingEngine_v*"
PKG_MARKER = Path("engine") / "semantic_reconstruction.py"

_CACHE: dict = {}


def _ver(d: Path) -> tuple:
    """語意版號。字母序陷阱:'v1.10.0' < 'v1.9.0' 為字串真、語意假。"""
    vs = [(int(m.group(1)), int(m.group(2)), int(m.group(3) or 0))
          for m in re.finditer(r"v(\d+)\.(\d+)(?:\.(\d+))?", d.name + "|" + d.parent.name)]
    return max(vs) if vs else (0, 0, 0)


def roots() -> list[Path]:
    if not INTAKE.is_dir():
        return []
    return [d for d in sorted(INTAKE.glob(PKG_GLOB))
            if d.is_dir() and (d / PKG_MARKER).is_file()]


def newest() -> Path | None:
    c = roots()
    return max(c, key=_ver) if c else None


def mount() -> dict:
    """掛載尾版收容件。只載 semantic_reconstruction(純 stdlib);
    markdown_engine 需要外部 lint 工具鏈,**本橋不碰**——碰了就是把
    「結構重組」與「lint 修檔」綁在一起,而我們只要前者。"""
    if "mount" in _CACHE:
        return _CACHE["mount"]
    d = newest()
    if d is None:
        st = {"state": "ABSENT", "dir": "", "dir_name": "", "version": "",
              "why": f"intake 下找不到 {PKG_GLOB}/{PKG_MARKER}({INTAKE})"}
        _CACHE["mount"] = st
        return st
    try:
        import importlib.util
        f = d / PKG_MARKER
        spec = importlib.util.spec_from_file_location("via_md_semrec", f)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
        need = ("def_classify_blocks", "def_split_sentences", "def_period_is_boundary",
                "def_analyze_tables", "def_build_information_units")
        miss = [n for n in need if not hasattr(mod, n)]
        if miss:
            st = {"state": "FAILED", "dir": str(d), "dir_name": d.name,
                  "version": ".".join(str(x) for x in _ver(d)),
                  "why": f"收容件在位但缺函式 {miss}(版本不合?)"}
        else:
            _CACHE["mod"] = mod
            st = {"state": "VERIFIED", "dir": str(d), "dir_name": d.name,
                  "version": ".".join(str(x) for x in _ver(d)), "why": ""}
    except Exception as exc:
        st = {"state": "FAILED", "dir": str(d), "dir_name": d.name,
              "version": ".".join(str(x) for x in _ver(d)),
              "why": f"載入失敗 {type(exc).__name__}:{str(exc)[:90]}"}
    _CACHE["mount"] = st
    return st


def _mod():
    mount()
    return _CACHE.get("mod")


# ---------- 服務面(VRN 文件結構層直接消費的四道) ----------

def period_is_boundary(text: str, index: int) -> bool | None:
    """這個位置的句點是不是**真的**句界?回 None=收容件缺席(不假裝判得出)。

    批436 的 `buf[-1] in "。.!?"` 會把「報告日期:2025.12.」當句尾——
    那是日期不是句號。這一道就是拿來擋這件事的。
    """
    m = _mod()
    if m is None:
        return None
    try:
        return bool(m.def_period_is_boundary(text, index))
    except Exception as exc:
        _CACHE["why_boundary"] = f"{type(exc).__name__}:{str(exc)[:60]}"
        return None


def sentences(text: str) -> list[dict]:
    """句級切分(收容件正主)。缺席=空清單並留因由,不自己切一套。"""
    m = _mod()
    if m is None:
        return []
    try:
        return list(m.def_split_sentences(text or ""))
    except Exception as exc:
        _CACHE["why_sentences"] = f"{type(exc).__name__}:{str(exc)[:60]}"
        return []


def blocks(text: str) -> list[dict]:
    """區塊分類:frontmatter/code/table/heading/list/quote/HTML/paragraph。
    **先分類再切句**——在程式碼、網址、版本號裡切句是批436 沒防到的。"""
    m = _mod()
    if m is None:
        return []
    try:
        out = m.def_classify_blocks((text or "").splitlines())
        return list(out[0]) if isinstance(out, tuple) else list(out)
    except Exception as exc:
        _CACHE["why_blocks"] = f"{type(exc).__name__}:{str(exc)[:60]}"
        return []


def tables(text: str) -> list[dict]:
    """表格 shape 驗證(表頭/分隔列/逐列欄數/matrix SHA-256)。"""
    m = _mod()
    if m is None:
        return []
    try:
        bl = m.def_classify_blocks((text or "").splitlines())
        bl = bl[0] if isinstance(bl, tuple) else bl
        out = m.def_analyze_tables(bl)
        return list(out[0]) if isinstance(out, tuple) else list(out)
    except Exception as exc:
        _CACHE["why_tables"] = f"{type(exc).__name__}:{str(exc)[:60]}"
        return []


def why() -> dict:
    """上一次各道為何回空(空字串=沒問題)。捕捉到就要顯示(批419e)。"""
    return {k: v for k, v in _CACHE.items() if k.startswith("why_")}


def status() -> dict:
    st = mount()
    return {"module": MODULE_ID, "hub": HUB_NAME, "version": HUB_VERSION,
            "mount": st, "candidates": [d.name for d in roots()], "why": why()}


def _print_status() -> int:
    st = mount()
    print(f"=== {MODULE_ID} {HUB_NAME} {HUB_VERSION} · Markdown 結構重組統轄橋 ===")
    print(f"  掛載態  {st['state']}  夾={st['dir_name'] or '-'}  版={st['version'] or '-'}")
    if st["why"]:
        print(f"  因由    {st['why']}")
    print(f"  候選    {len(roots())} 套:{', '.join(d.name for d in roots()) or '-'}")
    if st["state"] == "VERIFIED":
        demo = "報告日期:2025.12.04 研究員:黃煜倫。目標價 145 元。"
        print(f"  句界示範 「{demo}」→ {len(sentences(demo))} 句")
    return 0


def selftest() -> int:
    fails, done = [], []

    def chk(name, cond, note=""):
        done.append(name)
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    st = mount()
    chk("① 收容件掛得上且版本說得出(尾版律;字母序陷阱已避開)",
        st["state"] in ("VERIFIED", "ABSENT"),
        f"(態={st['state']} 夾={st['dir_name'] or '-'} 版={st['version'] or '-'}"
        + (f" 因由={st['why']}" if st["why"] else "") + ")")

    if st["state"] != "VERIFIED":
        chk("② 收容缺席時每一道都誠實回空並講得出為何(不假裝有)",
            sentences("x") == [] and blocks("x") == [] and tables("x") == []
            and period_is_boundary("x.", 1) is None,
            f"(因由={st['why']})")
        print(f"  [計] 六檢({len(done)} 檢) OK {len(done) - len(fails)} · FAIL {len(fails)}")
        return 1 if fails else 0

    # ② 句界:日期的句點不是句尾
    t2 = "報告日期:2025.12.04 研究員:黃煜倫。"
    i_date = t2.index("2025.") + 4          # 「2025**.**12」那一點
    i_end = t2.index("。")
    b_date, b_end = period_is_boundary(t2, i_date), period_is_boundary(t2, i_end)
    chk("② 句點不等於句界——日期/小數/版本號裡的點不是句尾(批436 的 "
        "`buf[-1] in \"。.!?\"` 會把「報告日期:2025.12.」當句尾,那是日期)",
        b_date is False and b_end is True,
        f"(「2025.12」的點→句界={b_date} · 「。」→句界={b_end})")

    # ③ 區塊先分類再切句
    md3 = "# 標題\n\n本文第一句。本文第二句。\n\n| a | b |\n| --- | --- |\n| 1 | 2 |\n"
    bl3 = blocks(md3)
    kinds3 = {str(b.get("kind") or b.get("type") or "") for b in bl3}
    chk("③ 先分類區塊再切句(frontmatter/code/table/heading/list/quote/HTML/paragraph)"
        "——在程式碼、網址、版本號裡切句是批436 沒防到的",
        len(bl3) >= 3 and any("head" in k for k in kinds3) and any("table" in k for k in kinds3),
        f"(區塊 {len(bl3)} 塊;型別={sorted(kinds3)})")

    # ④ 表格 shape
    tb4 = tables(md3)
    chk("④ 表格 shape 驗證(表頭/分隔列/逐列欄數;逐格照抄不補值)",
        len(tb4) >= 1, f"(表 {len(tb4)} 張)")

    # ⑤ 句級切分真的切得開
    s5 = sentences("本季營收成長 12%。毛利率下滑。")
    chk("⑤ 句級切分(中英句尾 + 收尾引號/括號狀態機)",
        len(s5) == 2, f"(切出 {len(s5)} 句)")

    # ⑥ 紀律宣告在檔
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑥ 紀律宣告(收容件原地不動/零網路/尾版律/誠實降級留因由 在檔)",
        all(k in src for k in ("收容件原地不動", "零網路", "尾版律", "誠實")),
        "")
    print(f"  [計] 六檢({len(done)} 檢) OK {len(done) - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print(f"=== {MODULE_ID} {HUB_NAME} · 六檢自測(零網路)===")
        return selftest()
    if "--json" in args:
        print(json.dumps(status(), ensure_ascii=False, indent=1))
        return 0
    return _print_status()


if __name__ == "__main__":
    sys.exit(main())
