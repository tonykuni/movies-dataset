#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VRN_ENG080_FourPointDigest v0111 — 薄尾:QC「新數字」把組字連字號誤認成負號(前版 v0110 本體照讀)

v0110→v0111(R35 操作員工作站實錄 2026-10-01 `via-closeout vrn --run`:vrn_fourpoint rc=1 · QC 紅 8):
  紅的 8 份全是同一個形:「新數字 ['-2026']」(CTBC 260915–260918 五份 · 光焱 / 國光生)、['-2025'](CTBC 251208 兩份)、
  ['-2023'](6933 AMAX-KY)。來源不是報告,是本引擎自己——v0109 的 compose_headline() 組「名(代號.TW)-本文標題」,
  本文標題以年份開頭時(「2026 年…」)就組出「…(1303.TW)-2026…」;NUM_RX = `-?\d+…` 把組字的「-」當負號,
  抽成 "-2026",來源只有 "2026" → 判「文摘出現、來源沒有的數字」= RED。是我們自己造的假紅,不是摘要捏造數字。
  修法(只動 QC 的取數,不動摘要):數字前的「-」緊貼在 ASCII 字母 / 數字 / 小數點 / 右括號之後 = 連接號,不是負號;
  這種 token 取無號值比對。空白、行首、中文字後的「-」照舊算負號(「上漲 -9.5%」「上漲-9.5%」仍是 -9.5%,
  來源沒有 -9.5% 照樣紅)。來源與 derived 取數用同一把尺(「2025-2026」兩邊都取 2025 · 2026)。
  其餘(K1–K5、目標價調整、入庫、頁)一字不動,照 v0110。
VIA_FROM_VCGC:經 VCGC 跑(via-console run --item vrn_fourpoint / via-closeout vrn --run 取尾版);零網路;不用 TA-Lib;正本唯讀。
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

import importlib.util
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_ENG080_FourPointDigest"


def _vnum(p: Path) -> int:
    m = re.search(r"_v(\d+)$", Path(p).stem)
    return int(m.group(1)) if m else -1


_PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum,
                  default=HERE / "VRN_ENG080_FourPointDigest_v0110.py")   # the prior this tail was cut from
_spec = importlib.util.spec_from_file_location("fourpoint_prior_for_" + Path(__file__).stem, _PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    return getattr(PRIOR, name)


ENGINE = Path(__file__).stem
# 「-」前一字是這些 = 連接號(組字 / 區間 / 代碼),不是負號
_JOINER_BEFORE = re.compile(r"[A-Za-z0-9.)\]）】]")


def numbers(text: str) -> list:
    """同 NUM_RX 取數;緊貼在 ASCII 字母 / 數字 / 小數點 / 右括號後的「-」視為連接號,取無號值。逗號去掉。"""
    s = str(text or "")
    out = []
    for m in PRIOR.NUM_RX.finditer(s):
        tok = m.group(0).replace(",", "")
        if tok.startswith("-") and m.start() > 0 and _JOINER_BEFORE.match(s[m.start() - 1]):
            tok = tok[1:]
        out.append(tok)
    return out


def novel_numbers(summary: str, source: str, derived: list | None = None) -> list:
    allow = set(numbers(source))
    for d in derived or []:
        allow |= set(numbers(str(d)))
    out = []
    for n2 in numbers(summary):
        if n2 not in allow and n2.rstrip("%") not in allow and n2 not in out:
            out.append(n2)
    return out


PRIOR.novel_numbers = novel_numbers          # build_digest 在前版命名空間裡叫它 → 換這一格即可


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note and not cond else ''}")

    head, fmt = PRIOR.compose_headline("南亞", "1303", "1303.TW", "2026 年營運展望")
    chk("實錄重現:年份開頭的標題組出「(1303.TW)-2026」", fmt == "NAME_CODE" and ")-2026" in head, head)
    src = "南亞 1303 2026 年營運展望 目標價 310 現價 236"
    chk("前版取數把它判成新數字 -2026(假紅的根)", "-2026" in PRIOR.NUM_RX.findall(head))
    chk("本版:組字連接號不算負號 → 不判新數字", novel_numbers(head, src) == [], novel_numbers(head, src))
    chk("區間「2025-2026」兩邊都取正值(來源與摘要同一把尺)", numbers("2025-2026F") == ["2025", "2026"])
    chk("真負號照舊:空白後的 -9.5% 來源沒有 → 仍判新數字", novel_numbers("上漲空間 -9.5%", "目標價 70 現價 77") == ["-9.5%"])
    chk("真負號照舊:中文字後的 -9.5% 仍是負號", numbers("上漲-9.5%") == ["-9.5%"])
    chk("derived 放行照舊", novel_numbers("上漲 -9.5%", "x", ["-9.5%"]) == [])
    chk("捏造的數字照抓:目標價 9999", novel_numbers("目標價 9999 元", "目標價 850 現價 678") == ["9999"])
    chk("前版 build_digest 走本版的 novel_numbers", PRIOR.novel_numbers is novel_numbers)
    body = Path(__file__).read_text(encoding="utf-8")
    chk("帶加速器橋 · VIA_FROM_VCGC 標記 · 不匯入 TA-Lib", "[VIA:ACCEL-BRIDGE" in body and "VIA_FROM_VCGC" in body
        and not re.search(r"^\s*(import|from)\s+" + "ta" + r"lib\b", body, re.M))
    print("--- 前版 v0110 全套自測(在本版取數下重跑)---")
    prc = PRIOR.selftest()
    chk("前版自測在本版取數下仍全過", prc == 0)
    print(f"[VRN_ENG080 v0111 連接號≠負號] 自測 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        return selftest()
    return PRIOR.main()


if __name__ == "__main__":
    sys.exit(main())
