#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vrn_fin_extract_v0102 — 財報頁年度分析擷取器(TOOL-082)薄尾:每股盈餘「基本 / 稀釋」沒寫清楚時的取值律
====================================================================
操作員 2026-11-15:「SSOT REGEX 同義字 不衝突前提下只增不減 · DILUTED EPS / BASIC EPS 若沒寫清楚財報頁有兩個值取小的
但財報頁只有一個取他但須標註兩種區分不明確不專業」;「系統全部獨立 獨立修正 … 各有各的 MAIN SYSTEM MANAGER」(VRN-2 自己改)。
本版(v0101 一字不動;只換 load_ssot / extract_annual / to_fin_dict 三個名字,其餘照 v0101):
  冊:knowledge/VRN_AnnualExtract_SSOT_v0101.json(只增 eps_unlabeled 一項 + eps_rule;79 項一字不動)。
  ① 頁上有標明 基本 / 稀釋 → 照 v0101(fin.eps = 基本;稀釋另存),並記 eps_kind = BASIC。
  ② 沒寫清楚(列名只有「每股盈餘」等、不含 基本 / 稀釋 / Basic / Diluted)→ 每一期收集所有這種列的值:
       兩個值 → 取小的,eps_kind = UNLABELED_MIN_OF_TWO;
       一個值 → 取它,但標註「基本 / 稀釋區分不明確(財報頁不專業)」,eps_kind = UNLABELED_SINGLE;
       三個以上 → 取最小並列出全部候選,eps_kind = UNLABELED_MIN_OF_N(交人看)。
  ③ 有標明的優先;同一頁標明與沒標明並存 → 用標明的,沒標明的照列在 eps_unlabeled_candidates(不丟)。
用法同 v0101:python vrn_fin_extract_v0102.py --file <財報頁.txt> [--fin-out <fin.json>] [--year YYYY] [--no-open] | --selftest
VRN 不直接對外:只帶加速器橋,不帶網路橋。不碰 TA-Lib。
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
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIOR_NAME = "vrn_fin_extract_v0101.py"
SSOT_V0101 = HERE / "knowledge" / "VRN_AnnualExtract_SSOT_v0101.json"
UNCLEAR_NOTE = "基本 / 稀釋區分不明確(財報頁不專業)"


def _load_prior():
    spec = importlib.util.spec_from_file_location("vrn_fin_extract_v0101_for_v0102", HERE / PRIOR_NAME)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


P = _load_prior()
_EXTRACT_V0101 = P.extract_annual
_TO_FIN_V0101 = P.to_fin_dict


def __getattr__(name):
    """尾版律 TAILAPI:前版公開名稱經本檔轉接。"""
    return getattr(P, name)


def load_ssot() -> dict:
    return json.loads(SSOT_V0101.read_text(encoding="utf-8-sig"))


def _unlabeled_rows(text: str, ssot: dict, years: list) -> list:
    """每一條沒寫基本 / 稀釋的每股盈餘列 → {label, values:{期: 值}}(依 v0101 同一套數字 / 年欄解析)。"""
    item = next((i for i in ssot.get("items") or [] if i.get("key") == "eps_unlabeled"), None)
    if not item:
        return []
    pats = sorted(item.get("zh", []) + item.get("en", []), key=len, reverse=True)
    excl = item.get("exclude") or []
    out = []
    for ln in text.replace("（", "(").replace("）", ")").splitlines():
        if any(x in ln for x in excl):
            continue
        hit = next((p for p in pats if (p in ln) or (re.match(r"^[A-Za-z]", p) and re.search(r"\b" + re.escape(p).replace(r"\ ", r"\s*") + r"\b", ln, re.I))), None)
        if hit is None:
            continue
        nums = [n for n in (P.parse_number(t) for t in P.NUM_RX.findall(ln.split(hit)[-1])) if n is not None]
        if not nums:
            continue
        vals = {}
        for i, v in enumerate(nums[:max(len(years), 1) if years else len(nums)]):
            vals[years[i] if i < len(years) else "Y%d" % (i + 1)] = v
        out.append({"label": hit, "line": ln.strip()[:120], "values": vals})
    return out


def eps_pick(result: dict, unlabeled: list) -> dict:
    """每一期的 EPS 取值與身分(照冊上 eps_rule)。"""
    rows = result.get("rows") or {}
    basic, diluted = rows.get("basic_eps"), rows.get("diluted_eps")
    per = {}
    for y in result.get("years") or []:
        if basic and y in basic["values"]:
            per[y] = {"value": basic["values"][y], "kind": "BASIC", "note": "頁上標明基本每股盈餘",
                      "diluted": (diluted or {}).get("values", {}).get(y)}
            continue
        if diluted and y in diluted["values"]:
            per[y] = {"value": diluted["values"][y], "kind": "DILUTED", "note": "頁上只標明稀釋每股盈餘"}
            continue
        cands = [r["values"][y] for r in unlabeled if y in r["values"]]
        if len(cands) == 1:
            per[y] = {"value": cands[0], "kind": "UNLABELED_SINGLE", "note": UNCLEAR_NOTE, "candidates": cands}
        elif len(cands) == 2:
            per[y] = {"value": min(cands), "kind": "UNLABELED_MIN_OF_TWO", "note": "沒寫基本 / 稀釋、同期兩個值 → 取小的;" + UNCLEAR_NOTE,
                      "candidates": cands}
        elif len(cands) > 2:
            per[y] = {"value": min(cands), "kind": "UNLABELED_MIN_OF_N", "note": "同期 %d 個沒標明的值 → 取最小,交人看;%s" % (len(cands), UNCLEAR_NOTE),
                      "candidates": cands}
    return per


def extract_annual(text: str, ssot: dict) -> dict:
    """v0101 原樣擷取(eps_unlabeled 那一項不走 v0101 的單列比對,改由本版依律處理)+ 每期 EPS 取值與身分。"""
    base_ssot = dict(ssot, items=[i for i in ssot.get("items") or [] if i.get("key") != "eps_unlabeled"])
    res = _EXTRACT_V0101(text, base_ssot)
    unl = _unlabeled_rows(text, ssot, res.get("years") or [])
    res["eps"] = eps_pick(res, unl)
    labeled = bool((res.get("rows") or {}).get("basic_eps") or (res.get("rows") or {}).get("diluted_eps"))
    if unl and labeled:
        res["eps_unlabeled_candidates"] = unl                  # 標明與沒標明並存:用標明的,沒標明的照列不丟
    res["misses"] = [m for m in res.get("misses") or [] if m != "eps_unlabeled"]
    return res


def to_fin_dict(result: dict, year: str | None = None) -> dict:
    fin = _TO_FIN_V0101(result, year)
    col = year or (result["years"][0] if result.get("years") else "Y1")
    e = (result.get("eps") or {}).get(col)
    if e:
        fin.setdefault("eps", e["value"])                      # 有標明基本的照 v0101 已填;沒有才用本版取值
        fin["eps_kind"] = e["kind"]
        if e["kind"].startswith("UNLABELED"):
            fin["eps_note"] = e["note"]
    return fin


P.SSOT_PATH = SSOT_V0101
P.load_ssot = load_ssot
P.extract_annual = extract_annual
P.to_fin_dict = to_fin_dict


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)[:240]) if note and not cond else ""), flush=True)

    ssot = load_ssot()
    old = json.loads((HERE / "knowledge" / "VRN_AnnualExtract_SSOT_v0100.json").read_text(encoding="utf-8-sig"))
    ok_keys = [i["key"] for i in old["items"]]
    new_keys = [i["key"] for i in ssot["items"]]
    chk("① 冊 v0101 只增不減:舊 %d 項全在且內容一字不動 · 只多 eps_unlabeled · 有 eps_rule" % len(ok_keys),
        new_keys[:len(ok_keys)] == ok_keys and new_keys[len(ok_keys):] == ["eps_unlabeled"] and ssot["items"][:len(ok_keys)] == old["items"] and "eps_rule" in ssot)
    head = "項目                     2024       2023\n"
    t_lab = head + "基本每股盈餘             12.00      10.50\n稀釋每股盈餘             11.90      10.40\n"
    r = extract_annual(t_lab, ssot)
    f = to_fin_dict(r, "2024")
    chk("② 標明基本 / 稀釋 → 取基本(照 v0101)· 稀釋另存 · 身分 BASIC", f.get("eps") == 12.0 and f.get("eps_kind") == "BASIC" and r["eps"]["2024"]["diluted"] == 11.9, (f, r["eps"]))
    t_two = head + "每股盈餘                 12.00      10.50\n每股盈餘(虧損)           11.90      10.40\n"
    r = extract_annual(t_two, ssot)
    f = to_fin_dict(r, "2024")
    chk("③ 沒寫清楚 · 同期兩個值 → 取小的 11.90 · 身分 UNLABELED_MIN_OF_TWO · 標註區分不明確",
        f.get("eps") == 11.9 and f.get("eps_kind") == "UNLABELED_MIN_OF_TWO" and "區分不明確" in f.get("eps_note", "")
        and r["eps"]["2023"]["value"] == 10.4, (f, r["eps"]))
    t_one = head + "每股盈餘                 12.00      10.50\n"
    r = extract_annual(t_one, ssot)
    f = to_fin_dict(r, "2024")
    chk("④ 沒寫清楚 · 只有一個值 → 取它 12.00 · 身分 UNLABELED_SINGLE · 必須標註「基本 / 稀釋區分不明確(財報頁不專業)」",
        f.get("eps") == 12.0 and f.get("eps_kind") == "UNLABELED_SINGLE" and f.get("eps_note") == UNCLEAR_NOTE, (f, r["eps"]))
    t_en = "Item 2024 2023\nEarnings per Share 5.12 4.10\nEPS 5.05 4.02\n"
    r = extract_annual(t_en, ssot)
    chk("⑤ 英文頁沒寫 Basic / Diluted 兩個值 → 取小的 5.05", r["eps"].get("2024", {}).get("value") == 5.05 and r["eps"]["2024"]["kind"] == "UNLABELED_MIN_OF_TWO", r["eps"])
    t_mix = head + "基本每股盈餘             12.00      10.50\n每股盈餘                 11.80      10.30\n"
    r = extract_annual(t_mix, ssot)
    chk("⑥ 標明與沒標明並存 → 用標明的 12.00 · 沒標明的照列在候選不丟", r["eps"]["2024"]["value"] == 12.0 and r["eps"]["2024"]["kind"] == "BASIC"
        and r.get("eps_unlabeled_candidates") and r["eps_unlabeled_candidates"][0]["values"]["2024"] == 11.8, r.get("eps_unlabeled_candidates"))
    chk("⑦ 「基本每股盈餘」不會被當成沒標明(排除字)· 沒有 EPS 的頁不出 eps · misses 不列 eps_unlabeled",
        not _unlabeled_rows(t_lab, ssot, ["2024", "2023"]) and extract_annual(head + "營業收入 100 90\n", ssot)["eps"] == {}
        and "eps_unlabeled" not in extract_annual(t_lab, ssot)["misses"])
    cp = subprocess.run([sys.executable, str(HERE / PRIOR_NAME), "--selftest"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
    fails = [x for x in (cp.stdout or "").splitlines() if "[FAIL]" in x]
    summ = [x for x in (cp.stdout or "").splitlines() if "[計]" in x]
    chk("⑧ 前版 v0101 自測照過(用它自己的 v0100 冊;%s)" % (summ[-1].strip() if summ else "沒有計數行"),
        cp.returncode == 0 and not fails and summ and "FAIL 0" in summ[-1], (cp.stdout or cp.stderr)[-300:])
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑨ 薄尾:v0101 不改檔 · 前版公開名稱經 __getattr__ 轉接 · 只帶加速器橋 · 不碰 TA-Lib",
        (HERE / PRIOR_NAME).is_file() and callable(__getattr__("parse_number")) and "[VIA:ACCEL-BRIDGE:v0100]" in text
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M))
    n = sum(ok)
    print("[計] vrn_fin_extract v0102 自測 %d/%d · %s" % (n, len(ok), "PASS" if n == len(ok) else "FAIL"), flush=True)
    return 0 if n == len(ok) else 1


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 財報頁年度分析擷取器 v0102 · EPS 基本 / 稀釋取值律自測(合成 fixture 零網路)===")
        return selftest()
    return P.main()


if __name__ == "__main__":
    sys.exit(main())
