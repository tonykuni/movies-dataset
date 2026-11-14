#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN-2 v0260: page fragments (page_NNNN[_hash].pdf) are not stock reports — kept out of the stock scope (thin tail over v0259).

Desktop 2026-11-03 22:28: the full run stopped at the 7200-second cap of step ⑦. The source folder the operator picked held 305 files: 60 broker
reports and 200 single pages split out of other documents on 11-02 (page_0001.pdf · page_0001_03dd97f40f.pdf … page_0063.pdf, pages 1–63 of
several documents, scanned images, no text layer). vrn2scope (v0227 · v0231) keeps every PDF whose name is not an explicit non-stock name, so the
200 pages entered the stock scope (260), every one went through the OCR ladder (p1loop 6798 s) and acceptance never finished.

v0260 adds one more non-stock filename rule to the same regex vrn2scope and the stock identification read (v0231 globals · _SK_EXCL):
「page_」 + 3–5 digits + optional 「_」 + ≥6 hex + 「.pdf」 = a page split out of another file, not a whole report (the Workbench input matrix already
counts them as 頁面影像). They stay in the source folder untouched; vrn2scope just does not copy them into scope_in (and removes earlier copies
there, as it does for any file that left the scope). One extra line counts them. Extraction, books, acceptance and the U/I stay v0259 code.
"""
from __future__ import annotations

# ===== 1. Parameters =====
TAG = "v0260"
DISPLAY_NAME = "VRN-2 SystemManager"
PRIOR_NAME = "VRN_SystemManager_v0259.py"

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import re
import sys
import tempfile

# [VIA:ACCEL-BRIDGE:v0111] The original manager executes its accelerator bridge.
_spec = importlib.util.spec_from_file_location("vrn_manager_prior_for_v0260", Path(__file__).with_name(PRIOR_NAME))
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
for _name, _value in list(vars(PRIOR).items()):
    if not _name.startswith("__") and _name not in globals():
        globals()[_name] = _value


def __getattr__(name):
    return getattr(PRIOR, name)


# ===== 2. Page fragments out of the stock scope =====
PAGE_FRAGMENT = r"^page_\d{3,5}(?:_[0-9a-f]{6,})?\.pdf$"
_PAGE_RX = re.compile(PAGE_FRAGMENT, re.I)
_SCOPE_FN = PRIOR.vrn2scope                                 # v0231 code · its globals hold _SK_EXCL
_G = _SCOPE_FN.__globals__
_SK_EXCL_PRIOR = _G["_SK_EXCL"]
if PAGE_FRAGMENT not in _SK_EXCL_PRIOR.pattern:
    _G["_SK_EXCL"] = re.compile(_SK_EXCL_PRIOR.pattern + "|" + PAGE_FRAGMENT, _SK_EXCL_PRIOR.flags)
_SK_EXCL = _G["_SK_EXCL"]


def is_page_fragment(name: str) -> bool:
    return bool(_PAGE_RX.match(Path(str(name)).name))


def _source_dir():
    """The source folder vrn2scope just used (latest VRN2_SSOT_vNNNN.json · source_dir)."""
    ssd = Path(_SCOPE_FN.__globals__["HERE"]) / "SSOT"
    books = sorted(ssd.glob("VRN2_SSOT_v[0-9][0-9][0-9][0-9].json"), key=lambda p: int(re.search(r"_v(\d{4})", p.name).group(1)))
    try:
        return Path(json.loads(books[-1].read_text(encoding="utf-8")).get("source_dir") or "") if books else None
    except (OSError, ValueError):
        return None


def vrn2scope(args: list) -> tuple:
    """v0231 vrn2scope (page fragments now match the non-stock rule) + one line counting them."""
    rc, lines = _SCOPE_FN(args)
    src = _source_dir()
    n = 0
    if src and src.is_dir():
        n = sum(1 for p in src.rglob("*") if p.is_file() and is_page_fragment(p.name))
    lines = list(lines) + ["[計] v0260 頁面分割檔(page_NNNN[_雜湊].pdf · 從別的檔切出來的單頁 · 不是整份報告)%d 份不進個股範圍(原檔不動 · 輸入矩陣算「頁面影像」)" % n]
    return rc, lines


# ===== 3. Self-test =====
def selftest():
    bad = []

    def chk(name, cond):
        print("[%s] %s" % ("PASS" if cond else "FAIL", name), flush=True)
        if not cond:
            bad.append(name)

    names_page = ["page_0001.pdf", "page_0001_03dd97f40f.pdf", "PAGE_0063.PDF", "page_00012_abcdef12.pdf"]
    names_keep = ["MQ-1560 20260520.pdf", "GS-2330 page_0001.pdf", "page_1.pdf", "page_0001_xyz.pdf", "pages_0001.pdf", "華南投顧-6143-振曜-1141128.pdf", "926708.pdf"]
    chk("① 頁面分割檔認得:page_0001 · page_0001_03dd97f40f · 大寫 · 5 碼頁號",
        all(is_page_fragment(n) and _G["_SK_EXCL"].search(n) for n in names_page))
    chk("② 不誤判:報告檔名 · 名字中間有 page_ · 頁號不到 3 碼 · 字尾不是雜湊 · pages_ · 純數字檔名",
        not any(is_page_fragment(n) for n in names_keep) and not any(_G["_SK_EXCL"].search(n) for n in ("MQ-1560 20260520.pdf", "page_1.pdf", "page_0001_xyz.pdf", "926708.pdf")))
    chk("③ 舊規則照舊:晨會 / ETF / 產業 仍排除 · 只多一條 · v0231 的 vrn2scope 讀到的是新規則",
        all(_G["_SK_EXCL"].search(n) for n in ("0901晨會.pdf", "ETF週報.pdf", "產業報告.pdf")) and _G["_SK_EXCL"].pattern.startswith(_SK_EXCL_PRIOR.pattern)
        and _G["_SK_EXCL"].pattern.count(PAGE_FRAGMENT) == 1 and _SCOPE_FN.__globals__["_SK_EXCL"] is _G["_SK_EXCL"])
    saved = {k: _G.get(k) for k in ("HERE", "_resolve")}
    try:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            here = root / "mgr"
            (here / "SSOT").mkdir(parents=True)
            src = root / "src"
            (src / "pages").mkdir(parents=True)
            for n in ("MQ-1560 20260520.pdf", "華南投顧-6143-振曜-1141128.pdf", "0901晨會.pdf"):
                (src / n).write_bytes(b"%PDF-1.4 r")
            for n in ("page_0001.pdf", "page_0001_03dd97f40f.pdf", "page_0002_17fdb64600.pdf"):
                (src / "pages" / n).write_bytes(b"%PDF-1.4 p")
            rep = root / "VIA_Reports" / "vrn"                                     # _rep() = VIA_Reports\vrn → its parent \vrn2 is the VRN-2 folder
            rep.mkdir(parents=True)
            v2 = rep.parent / "vrn2"
            (v2 / "scope_in").mkdir(parents=True)
            (v2 / "scope_in" / "page_0001.pdf").write_bytes(b"%PDF-1.4 old")       # an earlier run copied a page in
            (here / "SSOT" / "VRN2_SSOT_v0100.json").write_text(json.dumps({"source_dir": str(src)}), encoding="utf-8")
            _G["HERE"] = here
            real_resolve = saved["_resolve"]

            def fake_resolve(name):
                if name == "_rep":
                    return lambda: str(rep)
                if name == "input_dir":
                    return lambda: str(src)
                return real_resolve(name)
            _G["_resolve"] = fake_resolve
            rc, lines = vrn2scope([])
            got = sorted(p.name for p in (v2 / "scope_in").iterdir())
            chk("④ 範圍夾只收 2 份報告(晨會照舊排除 · 3 份分割頁不進 · 先前複製進去的分割頁移走)· 多一行計數 3 份 · 原檔不動",
                rc == 0 and got == ["MQ-1560 20260520.pdf", "華南投顧-6143-振曜-1141128.pdf"] and "3 份不進個股範圍" in lines[-1]
                and any("個股範圍 2" in l and "排除非個股 4" in l for l in lines) and len(list((src / "pages").iterdir())) == 3)
    finally:
        _G.update(saved)
    chk("⑤ main 的 vrn2scope 走本版(多一行)· 其他動詞照 v0259(PRIOR.main)", main.__globals__["vrn2scope"] is vrn2scope and "vrn2scope" in main.__code__.co_consts)
    why = ""
    try:
        with contextlib.redirect_stdout(io.StringIO()) as said:
            prior_rc = PRIOR.selftest()
        why = "" if prior_rc == 0 else said.getvalue().strip().splitlines()[-1][:160]
    except AssertionError as error:
        prior_rc, why = 1, str(error)[:160]
    chk("⑥ v0259 自測(轉置表再驗 · 再跑 v0258 表格修補 · v0257 · 冪等閘)照樣全過%s" % (" · " + why if why else ""), prior_rc == 0)
    print("[%s] v0260: page fragments kept out of the stock scope (counted · source untouched) · %d checks · failed %d"
          % ("PASS" if not bad else "FAIL", 6, len(bad)), flush=True)
    return 0 if not bad else 1


def main(argv=None):
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments == ["--selftest"]:
        return selftest()
    if arguments[:1] == ["vrn2scope"]:
        code, lines = vrn2scope(arguments[1:])
        for line in lines:
            print(line, flush=True)
        return code
    return PRIOR.main(arguments)


if __name__ == "__main__":
    raise SystemExit(main())
