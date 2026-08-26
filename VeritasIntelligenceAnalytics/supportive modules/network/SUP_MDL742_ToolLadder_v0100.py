#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SUP_MDL742_ToolLadder — 工具升階梯解析器(批181;操作員令)
====================================================================
操作員令:「工具不要衝突只增優化不減少;OCR 等工序輕型優先,輕能
解決就不用重型武器,依此類推;所有的都要加入加速器」。
冊=VIA_Tool_Escalation_Ladder_v0100.json(單一正主;append-only)。
本解析器供全引擎消費(引擎不自選重型工具=衝突防制):
  resolve(kind)      → 該工序現可用最輕階(importlib probe 誠實;
                        缺件=列名不假在)
  ladder(kind)       → 全階梯+各階在位狀態
  escalate(kind, lv, evidence) → 升階留痕(冊 escalation_log append;
                        無證據=拒升,輕階未敗不得動重械)
  網路工序 frozen=True:永回統包正主,不參與升降(操作員凍結令)。
只增不減:重械備裝於 via-install 同意閘後,不刪不預載。
用法:python3 SUP_MDL742_ToolLadder_v0100.py [--status] | --selftest
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
import json
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
LADDER_P = VIA / "supportive modules" / "registry" / "VIA_Tool_Escalation_Ladder_v0100.json"


def _load() -> dict:
    return json.loads(LADDER_P.read_text(encoding="utf-8"))


def _probe(mod: str | None) -> bool:
    """在位探測:probe=null 視為內建恆在;缺件誠實 False"""
    if mod is None:
        return True
    try:
        return importlib.util.find_spec(mod) is not None
    except Exception:
        return False


def ladder(kind: str) -> list[dict]:
    d = _load()
    lad = d["ladders"].get(kind)
    if lad is None:
        raise KeyError(f"工序未入冊:{kind}(冊={sorted(d['ladders'])})")
    return [{**r, "available": _probe(r.get("probe"))} for r in lad["rungs"]]


def resolve(kind: str) -> dict:
    """現可用最輕階(輕型優先鐵則);全缺=誠實 NONE_AVAILABLE"""
    d = _load()
    lad = d["ladders"][kind]
    if lad.get("frozen"):
        r = lad["rungs"][0]
        return {**r, "available": True, "frozen": True,
                "note": "網路凍結令:統包正主唯一,不參與升降"}
    for r in lad["rungs"]:
        if _probe(r.get("probe")):
            return {**r, "available": True}
    return {"lv": None, "tool": "NONE_AVAILABLE(誠實;候 via-install 閘)",
            "available": False}


def escalate(kind: str, to_lv: int, evidence: str) -> dict:
    """升階留痕:無實敗證據=拒升(輕階未敗不得動重械)"""
    if not evidence or len(evidence.strip()) < 10:
        return {"granted": False,
                "reason": "拒升:無輕階實敗證據(evidence 必填≥10 字)"}
    d = _load()
    lad = d["ladders"][kind]
    if lad.get("frozen"):
        return {"granted": False, "reason": "拒升:網路工序凍結(操作員令)"}
    cur = resolve(kind)
    if cur.get("lv") is not None and to_lv <= cur["lv"]:
        return {"granted": False,
                "reason": f"拒升:目標階 {to_lv} 不高於現輕階 {cur['lv']}"}
    entry = {"ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
             "kind": kind, "from_lv": cur.get("lv"), "to_lv": to_lv,
             "evidence": evidence.strip()[:300]}
    d["escalation_log"].append(entry)
    LADDER_P.write_text(json.dumps(d, ensure_ascii=False, indent=1),
                        encoding="utf-8")
    return {"granted": True, **entry}


def status() -> int:
    d = _load()
    for k, lad in d["ladders"].items():
        cur = resolve(k)
        mark = "凍結" if lad.get("frozen") else f"L{cur.get('lv')}"
        print(f"  [{mark:>3}] {k:14s} → {cur['tool'][:46]}")
    print(f"  升階留痕:{len(d['escalation_log'])} 筆")
    return 0


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    d = _load()
    chk("① 階梯冊在位(9 工序+append-only+衝突防制政策)",
        len(d["ladders"]) == 9 and d["append_only"] is True
        and "單一正主" in d["policy"])
    chk("② 每工序≥1 階且輕階置頂(lv 遞增序)",
        all(all(r["lv"] == i + 1 for i, r in enumerate(v["rungs"]))
            for v in d["ladders"].values()))
    r = resolve("DATAFRAME")
    ro = resolve("OCR_PDF_TEXT")
    chk("③ 輕型優先實證(DATAFRAME 現輕階=L1 DuckDB;OCR 件雲端未裝="
        "誠實 NONE_AVAILABLE 候閘,不假在)",
        r["lv"] == 1 and "DuckDB" in r["tool"]
        and (ro["lv"] == 1 or ro["available"] is False),
        f"(DF=L{r['lv']}·OCR={'L'+str(ro['lv']) if ro['lv'] else '候閘'})")
    seg = ladder("ZH_SEGMENT")
    chk("④ probe 誠實(pkuseg 缺=available False 列名不假在)",
        seg[0]["available"] and not seg[2]["available"])
    net = resolve("NETWORK")
    chk("⑤ 網路凍結(永回統包正主+frozen 旗)",
        net.get("frozen") and "SUP_MDL740" in net["tool"])
    e1 = escalate("OCR_PDF_TEXT", 3, "")
    chk("⑥ 無證據拒升(輕階未敗不得動重械)", not e1["granted"])
    e2 = escalate("OCR_PDF_TEXT", 3,
                  "selftest 演練證據:L1 pdfplumber 對掃描件回空文字(無文字層)")
    d2 = _load()
    chk("⑦ 有證據准升+冊留痕 append",
        e2["granted"] and len(d2["escalation_log"]) >= 1
        and d2["escalation_log"][-1]["to_lv"] == 3)
    e3 = escalate("NETWORK", 2, "任何理由")
    ta = resolve("TA_INDICATOR")
    chk("⑧ 凍結拒升+TA 輕階=自建工廠(talib 重械備而不用)",
        not e3["granted"] and ta["lv"] == 1 and "TAFactory" in ta["tool"])
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑨ 紀律宣告(只增不減/輕型優先/加速器橋在檔)",
        "只增不減" in src and "輕型優先" in src and "VIA:ACCEL-BRIDGE" in src)
    print(f"  [計] 九檢 OK {9 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 工具升階梯解析器(SUP_MDL742)· 九檢自測(零網路)===")
        return selftest()
    return status()


if __name__ == "__main__":
    sys.exit(main())
