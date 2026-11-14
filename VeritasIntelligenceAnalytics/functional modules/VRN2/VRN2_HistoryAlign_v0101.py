#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VRN2_HistoryAlign v0101 — v0100 薄尾(v0100 留著一字不改):刪除區只收「真的被歷史數據否定」的列。

VRN2_RoundAll 端到端只修回合實測(合成市場資料只故意改 4 格):v0100 把 100 列送進刪除區 —— 其中 50 多列比值 ≈ 0 / 0.01 / 9 / 84,229,
是同一科目字在別的單位(bn ↔ mn)、成長率 / 占比表、或別的口徑,不是「被歷史否定」。v0101 每一列各自判:
  ① 檔案倍率下比值 0.97 ~ 1.03 → 對上 → 歷史覆蓋(同 v0100)。
  ② 檔案倍率對不上,但別的倍率(×1000 · ÷1000 · …)對得上 → 這列是另一個單位 → 歷史覆蓋 · SCALE 記這列自己的倍率 · 不進刪除區。
  ③ 都對不上,但同一數量級(比值 0.5 ~ 2)→ 被歷史否定 → 刪除區(同 v0100 的理由格式)· 對齊冊放歷史值。
  ④ 比值在 0.5 ~ 2 之外 → 口徑 / 單位不明 → 不覆蓋、不刪,報告值照原冊(VALUE_SOURCE = REPORT(口徑不明 · 不覆蓋))· RECON_RATIO 照記。
  ⑤ SECTION / TABLE 標示成長 / 占比 / %(YoY · growth · 成長 · 增減 · 率 · margin · % of)的列一律當比率列(不是金額)。
  ⑥ 檢驗用的「每 (科目, 年度) 一個值」優先取歷史覆蓋的值,再取對上的報告值,最後才是第一個出現的。
動詞同 v0100:align --root <VIA 根> [--fin] [--market] [--out] · --selftest
"""
from __future__ import annotations

import importlib.util
import json
import re
import sys
import tempfile
from pathlib import Path

VERSION = "v0101"
DISPLAY_NAME = "VRN2_HistoryAlign"
TAG = "歷史對齊 v0101"
PRIOR_NAME = "VRN2_HistoryAlign_v0100.py"
HERE = Path(__file__).resolve().parent
SAME_MAGNITUDE = (0.5, 2.0)
_RATIO_SECTION = re.compile(r"%|yoy|qoq|growth|成長|增減|年增|季增|率|margin|% of|percent|pct|ratio|佔|占", re.I)


def _prior():
    for path in (HERE / PRIOR_NAME, HERE.parent / "v146" / "new" / PRIOR_NAME):
        if path.is_file():
            spec = importlib.util.spec_from_file_location("vrn2_historyalign_prior_v0100", path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            return module
    raise FileNotFoundError("前版 %s 不在 %s" % (PRIOR_NAME, HERE))


PRIOR = _prior()
for _name in dir(PRIOR):
    if not _name.startswith("__") and _name not in globals():
        globals()[_name] = getattr(PRIOR, _name)
PRIOR.TAG = TAG


def _ratio_context(row: dict) -> bool:
    return bool(_RATIO_SECTION.search("%s %s" % (row.get("SECTION") or "", row.get("TABLE") or "")))


def align_file(rows: list, hist: dict, has_hist: bool) -> dict:
    """一份報告:對單位 → 逐列判(對上 / 別單位對上 / 被否定 / 口徑不明)→ 刪除區只收被否定的 → 檢驗。"""
    P = PRIOR
    parsed = []
    for row in rows:
        std = "" if _ratio_context(row) else P.std_of(row.get("ITEM"))
        y, kind = P.period_of(row.get("PERIOD"))
        parsed.append((row, std, y, kind, P.num(row.get("VALUE")), P.ratio_of(row.get("ITEM"))))
    money_pairs = [(v, hist.get((std, y))) for row, std, y, kind, v, _ in parsed if std in P.MONEY and y and kind != "E" and v is not None and hist.get((std, y))]
    eps_pairs = [(v, hist.get((std, y))) for row, std, y, kind, v, _ in parsed if std in P.PER_SHARE and y and kind != "E" and v is not None and hist.get((std, y))]
    scale, n_money = P.pick_scale(money_pairs)
    n_eps = sum(1 for r, h in eps_pairs if h and P.TOL_LO <= r / h <= P.TOL_HI)
    matched = n_money + n_eps
    receipt = {"rows": len(rows), "has_history": has_hist, "history_cells": len(hist), "matched_periods": matched, "matched_money": n_money, "matched_per_share": n_eps,
               "scale": scale, "scale_label": P.SCALE_LABEL.get(scale, "—") if scale else ("未定(只有每股對上)" if matched else "—"), "overrides": 0, "overrides_other_unit": 0, "deleted": 0, "unclear": 0,
               "checks": [], "checks_pass": "—"}
    aligned, deleted = [], []
    if not has_hist:
        receipt.update(lamp="GRAY", why="沒有歷史資料(⑥e 市場擷取沒有這份的年度財報)· 不覆蓋 · 報告值照原冊")
    elif matched == 0:
        receipt.update(lamp="YELLOW", why="沒有一期對上(金額 %d 對 · 每股 %d 對 · 歷史格 %d)· 不覆蓋 · 報告值照原冊" % (len(money_pairs), len(eps_pairs), len(hist)))
    else:
        receipt.update(lamp="GREEN", why="對上 %d 期(金額 %d · 每股 %d)· 倍率 %s" % (matched, n_money, n_eps, receipt["scale_label"]))
    overriding = receipt["lamp"] == "GREEN"
    final, rank = {}, {}
    for row, std, y, kind, v, ratio_key in parsed:
        is_money, is_ps = std in P.MONEY, std in P.PER_SHARE
        s = scale if (is_money and scale) else 1.0
        h = hist.get((std, y)) if (std and y) else None
        extra = {"STD": std, "YEAR": y, "KIND": kind, "SCALE": s if is_money else 1.0, "VALUE_REPORT": row.get("VALUE"), "RECON_RATIO": None, "RECON_DIFF": None}
        unit = "百萬台幣" if (is_money and scale) else ("元/股" if is_ps else ("%" if (ratio_key or _ratio_context(row) or re.search(r"%|率|margin", P._norm(row.get("ITEM")))) else "原單位"))
        quality = 0
        if overriding and h is not None and v is not None and h and (is_money and scale or is_ps):
            ratio = (v * s) / h
            alt = None
            if not (P.TOL_LO <= ratio <= P.TOL_HI) and is_money:
                alt = next((t for t in P.SCALES if t != s and P.TOL_LO <= (v * t) / h <= P.TOL_HI), None)
            if P.TOL_LO <= ratio <= P.TOL_HI or alt is not None:
                use = alt if alt is not None else s
                r2 = (v * use) / h
                extra.update(VALUE_FINAL=round(h, 6), UNIT_FINAL=unit, SCALE=use if is_money else 1.0, RECON_RATIO=round(r2, 6), RECON_DIFF=round(v * use - h, 6),
                             VALUE_SOURCE="HISTORY(MOPS / TWSE)" if alt is None else "HISTORY(MOPS / TWSE · 這列單位 %s 對上)" % P.SCALE_LABEL.get(alt, "×%s" % alt))
                receipt["overrides"] += 1
                receipt["overrides_other_unit"] += int(alt is not None)
                quality = 3
            elif SAME_MAGNITUDE[0] <= ratio <= SAME_MAGNITUDE[1]:
                extra.update(VALUE_FINAL=round(h, 6), UNIT_FINAL=unit, VALUE_SOURCE="HISTORY(覆蓋 · 報告值進刪除區)", RECON_RATIO=round(ratio, 6), RECON_DIFF=round(v * s - h, 6))
                deleted.append(P._out_row(row, {"STD": std, "YEAR": y, "HISTORY_VALUE": round(h, 6), "UNIT_HISTORY": unit, "SCALE": s, "RECON_RATIO": round(ratio, 6),
                                                "DELETED_REASON": "與歷史數據差 > 3%%(報告 %s × %s = %s · 歷史 %s · 比值 %.4f · 同數量級)→ 歷史覆蓋" % (row.get("VALUE"), s, round(v * s, 4), round(h, 4), ratio)}))
                receipt["overrides"] += 1
                receipt["deleted"] += 1
                quality = 3
            else:
                extra.update(VALUE_FINAL=round(v * s, 6) if is_money else v, UNIT_FINAL=unit, VALUE_SOURCE="REPORT(口徑不明 · 不覆蓋)", RECON_RATIO=round(ratio, 6))
                receipt["unclear"] += 1
        else:
            if v is not None and (is_money and scale):
                extra.update(VALUE_FINAL=round(v * s, 6), UNIT_FINAL=unit, VALUE_SOURCE=P._source(kind, y, v, has_hist, overriding))
                quality = 1
            else:
                extra.update(VALUE_FINAL=v if v is not None else row.get("VALUE"), UNIT_FINAL=unit, VALUE_SOURCE=P._source(kind, y, v, has_hist, overriding))
                quality = 1 if v is not None else 0
        out = P._out_row(row, extra)
        aligned.append(out)
        if y and v is not None and quality:
            key = (std or ("ratio:" + ratio_key if ratio_key else ""), y)
            if key[0] and (key not in final or quality > rank[key]):
                final[key] = out["VALUE_FINAL"] if isinstance(out["VALUE_FINAL"], (int, float)) else v
                rank[key] = quality
    receipt["checks"] = P.checks(final)
    n_ok = sum(1 for c in receipt["checks"] if c["verdict"] == "PASS")
    receipt["checks_pass"] = "%d/%d" % (n_ok, len(receipt["checks"])) if receipt["checks"] else "—"
    if receipt["lamp"] == "GREEN":
        receipt["why"] += " · 覆蓋 %d(別單位 %d)· 刪除區 %d · 口徑不明不動 %d" % (receipt["overrides"], receipt["overrides_other_unit"], receipt["deleted"], receipt["unclear"])
    return {"aligned": aligned, "deleted": deleted, "receipt": receipt}


PRIOR.align_file = align_file          # v0100 的 align() 走它自己 globals 的 align_file → 本版
align = PRIOR.align


def selftest() -> int:
    bad = []

    def chk(label, cond):
        PRIOR.say(("[PASS] " if cond else "[FAIL] ") + label)
        if not cond:
            bad.append(label)

    with tempfile.TemporaryDirectory(prefix="vrn2-hist101-") as td:
        root = Path(td)
        PRIOR._fixture(root)
        v2 = root / "VIA_Reports" / "vrn2"
        fin = json.loads((v2 / "output" / "VRN2_FinancialData_latest.json").read_text(encoding="utf-8"))
        A = "A-2330 20260101.pdf"

        def add(item, period, value, section="", table="P5·F·01·TB"):
            fin.append({"REPORT_DATE": "2026-01-01", "FILENAME": A, "TICKER": "2330", "BROKER": "A", "PAGE": 6, "TABLE": table, "ITEM": item, "PERIOD": period, "VALUE": value, "VERIFY": "VERIFIED", "ROW": 9, "SECTION": section})
        add("Revenue (NT$ mn)", "2024A", "2,000,123", table="P6·F·02·TB")        # 另一張表用百萬:別單位對上 → 覆蓋 · 不刪
        add("Revenue", "2025A", "12.5", section="YoY growth (%)")               # 成長率段落 → 比率列 · 不碰
        add("Revenue", "2024A", "20.0", table="P7·F·03·TB")                     # 比值 0.01 → 口徑不明 · 不刪
        (v2 / "output" / "VRN2_FinancialData_latest.json").write_text(json.dumps(fin, ensure_ascii=False), encoding="utf-8")
        r = align(root)
        fa = r["files"][A]
        al = json.loads((v2 / "output" / "VRN2_FinancialAligned_latest.json").read_text(encoding="utf-8"))
        de = json.loads((v2 / "output" / "VRN2_Deleted_latest.json").read_text(encoding="utf-8"))
        a_rows = [x for x in al if x["FILENAME"] == A]
        mn = next(x for x in a_rows if x["ITEM"] == "Revenue (NT$ mn)")
        growth = next(x for x in a_rows if x["ITEM"] == "Revenue" and x.get("PERIOD") == "2025A" and x.get("VALUE_REPORT") == "12.5")
        odd = next(x for x in a_rows if x["ITEM"] == "Revenue" and x.get("VALUE_REPORT") == "20.0")
        chk("① v0100 的行為保留:A 對上 · 倍率 ×1000 · 2025A 淨利(比值 0.85 · 同數量級)進刪除區 1 列 · B 一期沒對上黃 · C 沒歷史灰", fa["lamp"] == "GREEN" and fa["scale"] == 1000.0 and len(de) == 1 and de[0]["STD"] == "net_income" and "同數量級" in de[0]["DELETED_REASON"]
            and r["files"]["B-2454 20260102.pdf"]["lamp"] == "YELLOW" and r["files"]["C-6669 20260103.pdf"]["lamp"] == "GRAY")
        chk("② 另一張表用百萬(檔案倍率 ×1000 對不上 · ×1 對上)→ 歷史覆蓋 · SCALE 1 · 不進刪除區", mn["VALUE_SOURCE"].startswith("HISTORY(MOPS / TWSE · 這列單位") and mn["SCALE"] == 1.0 and abs(mn["RECON_RATIO"] - 1.0) < 1e-3 and fa["overrides_other_unit"] == 1)
        chk("③ 成長率段落的 Revenue 12.5 → 比率列(STD 空)· 不覆蓋不刪", growth["STD"] == "" and not growth["VALUE_SOURCE"].startswith("HISTORY"))
        chk("④ 比值 0.01 的 Revenue 20.0 → 口徑不明 · 不覆蓋 · 不刪 · RECON_RATIO 照記", odd["VALUE_SOURCE"] == "REPORT(口徑不明 · 不覆蓋)" and odd["RECON_RATIO"] < 0.5 and fa["unclear"] == 1 and not any(d.get("VALUE") == "20.0" for d in de))
        cks = fa["checks"]
        chk("⑤ 檢驗取值優先歷史:2024 毛利 = 營收 − 成本 仍 PASS(營收取歷史值不是口徑不明的 20.0)", next(c for c in cks if c["year"] == 2024 and "毛利 = 營收" in c["check"])["verdict"] == "PASS")
        chk("⑥ 收據 why 帶覆蓋 / 別單位 / 刪除區 / 口徑不明 計數 · 原冊沒動", "別單位 1" in fa["why"] and "口徑不明不動 1" in fa["why"] and len(json.loads((v2 / "output" / "VRN2_FinancialData_latest.json").read_text(encoding="utf-8"))) == len(fin))
    PRIOR.say("[%s] %s %s --selftest · 6 項 · 不過 %d" % ("PASS" if not bad else "FAIL", DISPLAY_NAME, VERSION, len(bad)))
    return 0 if not bad else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in argv:
        return selftest()
    return PRIOR.main(argv)


if __name__ == "__main__":
    sys.exit(main())
