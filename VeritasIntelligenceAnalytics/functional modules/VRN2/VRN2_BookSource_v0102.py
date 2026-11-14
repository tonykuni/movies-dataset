#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VRN2_BookSource v0102 — v0101 薄尾(v0101 / v0100 一字不改):主題與摘要裡的數字一律「千分位 + 小數兩位」。

操作員 2026-11-03:「數字小數點兩位要有千分位號」。
v0101 的算法句寫成「調整後目標價 200.31 ÷ 調整後收盤 169 = 上漲空間 18.5%」(去尾零 · 一位小數 · 沒有千分位)。本版:
  · 調整後目標價 / 調整後收盤 → 1,234.50 這種寫法(千分位 + 兩位小數)· 上漲空間 → 18.53%(兩位小數 · 超過千也加千分位)
  · 評價那一點原文的上漲空間數字照樣換成新算的(兩位小數)· 原文其他數字(目標價 208 元 · 營收 18.89 億元)不動
  · 只改 Combined「TOPIC & SUMMARY」這個組出來的欄 · 輸出冊的數值欄(TARGET_PRICE(ADJ) · ADJ_CLOSE …)不加千分位(那是資料 · 加了會壞掉數字)
其餘(四點去開頭符號 · 標題格式 · 評價點排第一 · 三種格式 · 冪等 · 收據)照 v0101。動詞同 v0101:apply [--v2] [--dry-run] · --selftest
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import re
import sys
import tempfile
from pathlib import Path

VERSION = "v0102"
DISPLAY_NAME = "VRN2_BookSource"
PRIOR_NAME = "VRN2_BookSource_v0101.py"
HERE = Path(__file__).resolve().parent


def _load_prior():
    path = HERE / PRIOR_NAME
    if not path.is_file():
        raise FileNotFoundError("前版 %s 不在 %s" % (PRIOR_NAME, HERE))
    spec = importlib.util.spec_from_file_location("vrn2_booksource_prior_v0101", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


V0101 = _load_prior()
V0100 = V0101.V0100
for _name in dir(V0101):
    if not _name.startswith("__") and _name not in globals():
        globals()[_name] = getattr(V0101, _name)
_v0101 = {k: getattr(V0101, k) for k in ("compose", "apply")}
TOPIC = V0101.TOPIC
POINTS = V0101.POINTS


def money(x) -> str:
    """1234.5 → 1,234.50(千分位 + 兩位小數);None → 空字串。"""
    return "{:,.2f}".format(x) if x is not None else ""


def compose(comb: dict, basic: dict, summ: dict) -> tuple:
    """同 v0101 compose,只差數字寫法:價格與上漲空間都是千分位 + 兩位小數。"""
    pts = [V0101.strip_lead(summ.get(k)) for k in POINTS]
    pts = [p.strip() for p in pts if p and p.strip()]
    k = next((i for i, p in enumerate(pts) if V0101._VAL.search(p)), None)
    if k:
        pts.insert(0, pts.pop(k))
    tp, adj = V0101._num(comb.get("TARGET_PRICE(ADJ)")), V0101._num(comb.get("ADJ_CLOSE"))
    redone = False
    if tp and adj and adj > 0:
        up = money((tp / adj - 1) * 100)
        basis = "調整後目標價 %s ÷ 調整後收盤 %s = 上漲空間 %s%%" % (money(tp), money(adj), up)
        if k is not None:
            p0 = V0101._UP_CN.sub(lambda m: m.group(1) + up + m.group(3), pts[0])
            p0 = V0101._UP_EN.sub(lambda m: (m.group(1) + up + m.group(3)) if m.group(1) is not None else (up + m.group(5)), p0)
            pts[0] = p0.rstrip() + "；" + basis
        else:
            rating = str(comb.get("RATING") or basic.get("RATING") or "").strip()
            pts = [("評價 %s：%s" % (rating, basis)) if rating else ("評價：" + basis)] + pts[:3]
        redone = True
    return " · ".join([V0101.title_line(comb, basic, summ)] + pts[:4]).strip(" ·"), redone


def apply(v2, dry: bool = False) -> dict:
    rec = _v0101["apply"](v2, dry)
    rec["module"] = "%s %s" % (DISPLAY_NAME, VERSION)
    if isinstance(rec.get("summary_cleanup"), dict):
        rec["summary_cleanup"]["number_format"] = "價格 1,234.50 · 上漲空間 18.53%(千分位 + 兩位小數 · 只在主題與摘要這段字 · 數值欄不動)"
    if not dry:
        try:
            (Path(v2) / V0100.RECEIPT).write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
        except (OSError, AttributeError):
            pass
    return rec


V0101.compose = compose                                     # v0101 fix_row 叫的 compose = 本版


# ── 自測 ──────────────────────────────────────────────────────────────────────────────────────────────
def selftest() -> int:
    bad = []

    def chk(label, cond):
        print(("[PASS] " if cond else "[FAIL] ") + label, flush=True)
        if not cond:
            bad.append(label)
    V0101.compose = _v0101["compose"]
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            rc = V0101.selftest()
    finally:
        V0101.compose = compose
    chk("⓪ v0101 自測照過(前版自己的接線 · 含 v0100)· %s" % (buf.getvalue().strip().splitlines() or ["—"])[-1][:60], rc == 0)
    chk("① 數字寫法:1234.5 → 1,234.50 · 169 → 169.00 · 0.5 → 0.50 · 1234567.891 → 1,234,567.89 · -3.456 → -3.46",
        [money(x) for x in (1234.5, 169, 0.5, 1234567.891, -3.456)] == ["1,234.50", "169.00", "0.50", "1,234,567.89", "-3.46"])
    comb = {"FILENAME": "a.pdf", "NAME": "示例公司", "YFINANCE_TICKER": "9999.TW", "RATING": "買進", "TARGET_PRICE(ADJ)": "1234.5", "ADJ_CLOSE": "1000", TOPIC: "x"}
    summ = {"TITLE": "- 標題甲", "POINT_1": "➢ 營收成長", "POINT_2": "• 目標價 1,300 元,潛在上漲空間 30%", "POINT_3": "毛利率回升", "POINT_4": ""}
    text, redone = compose(comb, {}, summ)
    parts = text.split(" · ")
    chk("② 主題與摘要:評價點第一 · 上漲空間 30% → 23.45% · 算法 調整後目標價 1,234.50 ÷ 調整後收盤 1,000.00 = 上漲空間 23.45% · 原文目標價 1,300 元不動 · 標題照 v0101",
        redone and parts[0] == "示例公司(9999.TW, 買進) - 標題甲" and parts[1] == "目標價 1,300 元,潛在上漲空間 23.45%；調整後目標價 1,234.50 ÷ 調整後收盤 1,000.00 = 上漲空間 23.45%"
        and parts[2:] == ["營收成長", "毛利率回升"])
    t2, _r2 = compose(dict(comb, RATING=""), {}, {"TITLE": "標題", "POINT_1": "營收", "POINT_2": "毛利", "POINT_3": "費用", "POINT_4": "庫存"})
    chk("③ 沒有評價句 → 第一點補一句(仍是四點)· 數字同寫法", t2.split(" · ")[1] == "評價：調整後目標價 1,234.50 ÷ 調整後收盤 1,000.00 = 上漲空間 23.45%"
        and len(t2.split(" · ")) == 5)
    t3, r3 = compose(dict(comb, ADJ_CLOSE=""), {}, summ)
    chk("④ 調整後收盤缺 → 數字不動(只排序 · 去符號)", not r3 and "潛在上漲空間 30%" in t3 and "調整後目標價" not in t3)
    t4, _r4 = compose({"NAME": "", "TICKER": "3231", "RATING": "Buy", "TARGET_PRICE(ADJ)": "160", "ADJ_CLOSE": "128"}, {"ENGLISH_NAME": "Wistron", "YFINANCE_TICKER": "3231.TW"},
                      {"TITLE": "Strong sales", "POINT_1": "Reiterate Buy with TP NT$165, 25% upside"})
    chk("⑤ 英文:「25% upside」→ 25.00% · 算法 160.00 ÷ 128.00", t4 == "Wistron(3231.TW, Buy) - Strong sales · Reiterate Buy with TP NT$165, 25.00% upside；調整後目標價 160.00 ÷ 調整後收盤 128.00 = 上漲空間 25.00%")
    with tempfile.TemporaryDirectory(prefix="vrn2-booksource102-") as td:
        v2 = Path(td) / "VIA_Reports" / "vrn2"
        out = v2 / "output"
        out.mkdir(parents=True)
        (out / "VRN2_Summary_latest.json").write_text(json.dumps([dict(summ, FILENAME="a.pdf", TICKER="9999")], ensure_ascii=False, indent=1), encoding="utf-8")
        (out / "VRN2_Combined_latest.json").write_text(json.dumps([dict(comb, TICKER="9999", BROKER="凱基", STATUS="s")], ensure_ascii=False, indent=1), encoding="utf-8")
        rec = apply(v2)
        cj = json.loads((out / "VRN2_Combined_latest.json").read_text(encoding="utf-8"))[0]
        rj = json.loads((v2 / V0100.RECEIPT).read_text(encoding="utf-8"))
        snap = (out / "VRN2_Combined_latest.json").read_bytes()
        rec2 = apply(v2)
        chk("⑥ 寫冊:Combined 主題與摘要新寫法 · 數值欄 TARGET_PRICE(ADJ) 1234.5 / ADJ_CLOSE 1000 原樣(不加千分位)· 收據 module v0102 · 再跑不變",
            "上漲空間 23.45%" in cj[TOPIC] and cj["TARGET_PRICE(ADJ)"] == "1234.5" and cj["ADJ_CLOSE"] == "1000" and rec["module"] == "VRN2_BookSource v0102"
            and rj["module"] == "VRN2_BookSource v0102" and "number_format" in rj["summary_cleanup"] and (out / "VRN2_Combined_latest.json").read_bytes() == snap
            and rec2["summary_cleanup"]["topic_rows"] == 0)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑦ 第 3 行 ACCEL-BRIDGE 標記 · 不連外 · v0101 的 fix_row 叫本版 compose",
        src.splitlines()[2].strip() == "# [VIA:ACCEL-BRIDGE:v0111]" and not re.search(r"^\s*(import|from)\s+(requests|urllib|socket|http)\b", src, re.M) and V0101.compose is compose)
    print("[%s] %s %s --selftest · 不過 %d" % ("PASS" if not bad else "FAIL", DISPLAY_NAME, VERSION, len(bad)), flush=True)
    return 0 if not bad else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    def opt(k, d=None):
        return argv[argv.index(k) + 1] if k in argv and argv.index(k) + 1 < len(argv) else d
    if "--selftest" in argv:
        return selftest()
    if not argv or argv[0] != "apply":
        print("用法:python %s apply [--v2 <VIA_Reports\\vrn2>] [--dry-run] · --selftest" % Path(__file__).name, flush=True)
        return 2
    v2 = Path(opt("--v2") or (Path(os.environ["VIA_ROOT"]) / "VIA_Reports" / "vrn2" if os.environ.get("VIA_ROOT") else HERE.parent.parent / "VIA_Reports" / "vrn2"))
    rec = apply(v2, dry="--dry-run" in argv)
    print("[計] 輸出冊 Source / Broker 欄 · 四點 / 主題與摘要 · %s · %s" % (rec["lamp"], rec["why"]), flush=True)
    print("[%s] %s %s · %s" % (rec["lamp"], DISPLAY_NAME, VERSION, rec["why"][:240]), flush=True)
    return 0 if rec["lamp"] in ("GREEN", "YELLOW", "GRAY") else 1


if __name__ == "__main__":
    sys.exit(main())
