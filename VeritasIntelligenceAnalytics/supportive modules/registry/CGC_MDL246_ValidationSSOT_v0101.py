#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL246_ValidationSSOT v0101 — 薄尾:交叉代碼准多段(X-REQ-BACK · X-REQ-OPEN · X-PEER · X-PEER-TEXT)

實錄(2026-10-12,VCGC 全功能串測 V-val 紅 rc 1):
  [RED] V-XREF 工作流冊引用了本冊沒登記的交叉代碼 X-REQ-BACK(VCGC:VCGC-WKF013, VCGC-WKF014, VCGC-WKF015)
  [RED] V-SDD  SDD 驗證器實作了本冊沒登記的交叉代碼:X-PEER(驗證器多了新檢,本冊沒跟上)
v0100 的兩條正則只認單段代碼(XCODE_RX ^X-[A-Z]+$ · SDD_XCODE_RX 只抓第一段):多段代碼登進冊會被判 V-CODE 格式不對,
不登又是 V-XREF / V-SDD 紅;SDD 驗證器 v0104(X-REQ-BACK)· v0100(X-REQ-OPEN)· v0106(X-PEER · X-PEER-TEXT,L120)早就在發這些代碼。
本版只換兩條正則(段與段以 - 相連,每段大寫,首段仍是 X):冊 VIA_Validation_SSOT_v0101.json 同批登記這四個代碼(正主 · 記號 · L120)。
check / show / main 全照 v0100(本體讀模組全域正則,換裝即生效;v0100 一字不動)。只收 VCGC 呼叫;零網路;不碰 TA-Lib。
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

import contextlib
import copy
import importlib.util
import io
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = Path(__file__).stem
_STEM = "CGC_MDL246_ValidationSSOT"


def _vnum_v0101(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0101(p) < _vnum_v0101(__file__)), key=_vnum_v0101)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + ENGINE, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)

XCODE_RX_V0101 = re.compile(r"^X-[A-Z]+(?:-[A-Z]+)*$")            # X-REQ-BACK · X-PEER-TEXT;X-req · X- · X-REQ- 都不是
SDD_XCODE_RX_V0101 = re.compile(r"\"(X-[A-Z]+(?:-[A-Z]+)*)\"")    # 驗證器原始碼裡 "X-…" 整個代碼,不只第一段
PRIOR.XCODE_RX = XCODE_RX_V0101                                  # 本體 check() 讀模組全域 → 換裝即生效
PRIOR.SDD_XCODE_RX = SDD_XCODE_RX_V0101
XCODE_RX, SDD_XCODE_RX = XCODE_RX_V0101, SDD_XCODE_RX_V0101


def __getattr__(name: str):
    """薄尾轉接:本版沒蓋的公開名稱照前版(TAILAPI)。"""
    return getattr(PRIOR, name)


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args:
        return selftest()
    return PRIOR.main(args)


def selftest() -> int:
    print(f"=== {ENGINE} · 薄尾自測(交叉代碼准多段)===")
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)[:220]) if note and not cond else ''}")

    good = ("X-COL", "X-REQ-BACK", "X-PEER-TEXT", "X-A-B-C")
    bad = ("X-req-back", "X-", "X-REQ-", "X-REQ--BACK", "X-REQ BACK", "Y-REQ", "x-REQ", "X-REQ-back")
    chk("① 代碼正則:多段大寫准(X-REQ-BACK · X-PEER-TEXT)· 小寫 / 空段 / 尾 - / 非 X 不准",
        all(XCODE_RX.match(c) for c in good) and not any(XCODE_RX.match(c) for c in bad))
    found = sorted(set(SDD_XCODE_RX.findall('_row(r, "RED", "X-REQ-BACK", "x"); "X-PEER" "X-NEWCHK" "X-PEER-TEXT" "x-no" "X-bad-Case"')))
    chk("② 驗證器代碼正則:整個多段代碼都抓到(不只第一段)· 單段照舊 · 小寫不抓", found == ["X-NEWCHK", "X-PEER", "X-PEER-TEXT", "X-REQ-BACK"], found)
    chk("③ 本體換裝:v0100 的 XCODE_RX / SDD_XCODE_RX 指向本版正則", PRIOR.XCODE_RX is XCODE_RX_V0101 and PRIOR.SDD_XCODE_RX is SDD_XCODE_RX_V0101)
    bp = PRIOR.newest(PRIOR.BOOK_GLOB)
    book = PRIOR._json(bp) or {}
    codes = {str(x.get("code")) for x in book.get("cross_checks") or []}
    books, pol = PRIOR.workflow_books(), PRIOR.policy_ids()
    sdd_text = PRIOR.chain_text(PRIOR.newest("CGC_MDL245_SDDValidator_v*.py"))
    rep = PRIOR.check(book=book, books=books, sdd_text=sdd_text, pol_ids=pol)
    notg = [f"{r['rule']}:{r['msg'][:70]}" for r in rep["rows"] if r["lamp"] != "GREEN" and r["rule"] in ("V-CODE", "V-XREF", "V-SDD", "V-OWNER", "V-IMPL", "V-POLICY")]
    chk(f"④ 真冊 {bp.name if bp else '-'}:四個多段代碼登記了 · 正主 / 記號 / L120 都對得到 · V-CODE / V-XREF / V-SDD 無紅黃 · 整冊 {rep['state']}",
        bp is not None and _vnum_v0101(bp) >= 101 and {"X-REQ-BACK", "X-REQ-OPEN", "X-PEER", "X-PEER-TEXT"} <= codes and not notg and rep["state"] == "GREEN",
        notg or rep.get("why"))
    b2 = copy.deepcopy(book)
    b2["cross_checks"] = [x for x in b2["cross_checks"] if x.get("code") != "X-PEER"]
    for s in ("VCGC", "VDF", "VRN"):
        b2["systems"][s]["cross_check"] = [c for c in b2["systems"][s]["cross_check"] if c != "X-PEER"]
    r2 = PRIOR.check(book=b2, books=books, sdd_text=sdd_text, pol_ids=pol)
    chk("⑤ 負控:冊少登 X-PEER → V-SDD 紅(驗證器多了新檢,本冊沒跟上)照抓",
        r2["state"] == "RED" and any(r["rule"] == "V-SDD" and r["lamp"] == "RED" and "X-PEER" in r["msg"] for r in r2["rows"]))
    b3 = copy.deepcopy(book)
    b3["cross_checks"].append(dict(b3["cross_checks"][0], code="X-REQ-back"))
    r3 = PRIOR.check(book=b3, books=books, sdd_text=sdd_text, pol_ids=pol)
    chk("⑥ 負控:冊登了小寫段 X-REQ-back → V-CODE 紅(格式仍管)",
        any(r["rule"] == "V-CODE" and r["lamp"] == "RED" and "X-REQ-back" in r["msg"] for r in r3["rows"]))
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        prc = PRIOR.selftest()
    print("  ── 前版 v0100 自測(摘末行)── " + (buf.getvalue().strip().splitlines() or ["(無輸出)"])[-1])
    chk("⑦ 前版鏈 v0100 自測 rc 0(本版正則換裝後,它的真冊 ② 也綠)", prc == 0)
    src = Path(__file__).read_text(encoding="utf-8")
    import ast
    chk("⑧ 檔頭:加速器橋在(__future__ 之後);不碰 TA-Lib;不直派子行程;不載外部函式庫",
        "[VIA:ACCEL-BRIDGE:" in src and src.index("from __future__") < src.index("[VIA:ACCEL-BRIDGE:")
        and "import " + "talib" not in src
        and not any(isinstance(n, (ast.Import, ast.ImportFrom)) and any((x.name or "").split(".")[0] == "sub" + "process" for x in n.names) for n in ast.walk(ast.parse(src))))
    print(f"[計] {ENGINE} 薄尾 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
