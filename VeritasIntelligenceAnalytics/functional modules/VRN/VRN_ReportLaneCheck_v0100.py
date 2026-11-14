#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_ReportLaneCheck v0100 — VRN-2 兩條車道(個股報告 · 非個股報告)能不能處理:只讀檢查 + 樣本分類 → 矩陣(誠實四態)。

操作員 2026-11-09:「檢查 VRN 可以處理個股報告及非個股報告」。
  check     ① 個股車道:啟動器尾版(docs/handoff/ai/vrn2_release_v*/ 或運行副本 functional modules/VRN2/)· 管理器尾版 · 分類器(VRN_SystemManager v0231 的
               _SK_EXCL 排除字 + 檔名代號律)在不在;最近一次 VRN2_Activate / Scope / Completion 收據(本機有才讀)。
            ② 非個股車道:非個股摘要器 v0310 引擎 · REUSE_MANIFEST · internal/NON_STOCK_CORE_v*.py(缺 = BLOCKED · 等上傳)· 啟動器有沒有接線(字串掃描)·
               交接冊 work item REQ195 狀態。
            ③ 樣本分類(預設倉內 fixtures REAL_TEST_INPUT;--pdf-dir 可換):照 v0231 同一套檔名律分 個股 / 非個股 + 原因;有 pymupdf 才讀首頁標題補代號(沒有 = 檔名車道 · 照實)。
            燈:個股車道三件齊 = GREEN;非個股車道缺核心 = BLOCKED(整體 YELLOW · 不寫成綠);啟動器 / 管理器缺 = RED。
  selftest  tempfile 假樹 · 分類律 · BLOCKED / READY 判定 · 不碰 environ · 不跑任何啟動器。
輸出:<out>/VRN2_LaneCheck_latest.json / .md(預設 <VIA>/VIA_Reports/vrn2)。
邊界:只讀;不 import 管理器(用正則抽 _SK_EXCL 字面 · 不執行);不連網;不改 VRN-2 任何檔;VCGC 的燈不寫成 VRN-2 的成功(四系統對等 · 只讀互看)。
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_root = _sa_Path(__file__).resolve()
    for _ in range(6):
        _sa_root = _sa_root.parent
        if (_sa_root / "VeritasIntelligenceAnalytics").is_dir() or _sa_root.name == "VeritasIntelligenceAnalytics":
            break
    _sa_dir = (_sa_root / "VeritasIntelligenceAnalytics" if (_sa_root / "VeritasIntelligenceAnalytics").is_dir() else _sa_root) / "supportive modules" / "accelerator"
    if _sa_dir.is_dir() and str(_sa_dir) not in _sa_sys.path:
        _sa_sys.path.insert(0, str(_sa_dir))
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import argparse
import json
import os
import re
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

VERSION = "v0100"
ENGINE = "VRN_ReportLaneCheck " + VERSION
HERE = Path(__file__).resolve().parent                  # functional modules/VRN
VIA = HERE.parent.parent
CLASSIFIER_SRC = "VRN_SystemManager_v0231.py"           # 分類律正本(抽字面 · 不執行)
FIXTURE_REL = "functional modules/VRN/intake/VRN_v0108_Annual/VRN_v0108_Complete_Handover/pack/engine/fixtures/REAL_TEST_INPUT"
NONSTOCK_REL = "functional modules/VRN/nonstock_v0310"
_FALLBACK_EXCL = r"(?i)晨會|早報|盤後|盤勢|ETF|籌碼|總經|論壇|第.場|專題|產業|Databook|summit|Insights|hardware|Thermal|Memory|Automation|PCB|ABF|CPO|AI Power|TPU|Components|觀察家|[周週]報|解盤|股市分析|股分析|鋼鐵"


def load_excl(vrn_dir: Path) -> tuple:
    p = vrn_dir / CLASSIFIER_SRC
    if p.is_file():
        m = re.search(r'^_SK_EXCL\s*=\s*re\.compile\(r"(.+?)"\)\s*$', p.read_text(encoding="utf-8"), re.M)
        if m:
            return re.compile(m.group(1)), CLASSIFIER_SRC
    return re.compile(_FALLBACK_EXCL), "fallback(v0231 同字)"


def ticker_from_name(nm: str) -> str:
    """同 v0231 _sk_ticker 的檔名段:四位數 · 不是年份(20xx)除非後面跟 TT / ) / ,。"""
    for t in re.findall(r"(?<!\d)(\d{4})(?!\d|年)", nm):
        if not re.match(r"20[1-3]\d$", t) or re.search(t + r"\s?(?:TT|\)|,)", nm):
            return t
    return ""


def first_page_title(pdf: Path) -> str:
    try:
        import fitz  # noqa: PLC0415  (pymupdf · 有才用)
    except ImportError:
        return ""
    try:
        with fitz.open(str(pdf)) as doc:
            return (doc[0].get_text() or "")[:400] if len(doc) else ""
    except Exception:  # noqa: BLE001
        return ""


def classify(name: str, excl, title: str = "") -> dict:
    tk = ticker_from_name(name)
    if not tk and title:
        m = re.search(r"\(?(?<!\d)(\d{4})(?:\s?TT|\.TWO?|\s?TW|\))", title) or re.search(r"\(([A-Z]{1,5})\s?US\)", title)
        tk = m.group(1) if m else ""
    hit = excl.search(name)
    if not tk:
        return {"file": name, "lane": "non_stock", "ticker": "", "why": "沒有個股代號(檔名%s)" % ("與首頁" if title else "")}
    if hit:
        return {"file": name, "lane": "non_stock", "ticker": tk, "why": "排除字「%s」(產業 / 晨報 / 盤後 / ETF / 論壇等)" % hit.group(0)}
    return {"file": name, "lane": "stock", "ticker": tk, "why": "代號 %s · 無排除字" % tk}


def _latest(globs: list, root: Path):
    hits = []
    for g in globs:
        hits.extend(p for p in root.glob(g) if p.is_file())
    return sorted(hits)[-1] if hits else None


def launcher_tail(via: Path) -> dict:
    out = {"runtime_copy": None, "release_zip": None, "version": None}
    rt = _latest(["functional modules/VRN2/ActivateVRN-2_v*.py"], via)
    if rt:
        out["runtime_copy"] = rt.name
    zips = sorted((p for p in via.glob("docs/handoff/ai/vrn2_release_v*/*.zip") if p.is_file()), key=lambda p: (p.parent.name, p.name.startswith("VRN2_Closeout"), p.name), reverse=True)
    for zp in zips:                                              # 由新到舊 · 找第一個裝著啟動器的 zip(測試工具 zip 不算)
        try:
            with zipfile.ZipFile(zp) as z:
                names = [n for n in z.namelist() if re.search(r"ActivateVRN-2_v\d{4}\.py$", n)]
        except (OSError, zipfile.BadZipFile):
            continue
        if names:
            out["release_zip"] = str(zp.relative_to(via)).replace("\\", "/")
            out["in_zip"] = sorted(names)[-1]
            break
    v = out["runtime_copy"] or out.get("in_zip") or ""
    m = re.search(r"v(\d{4})", v)
    out["version"] = "v" + m.group(1) if m else None
    return out


def read_json(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def nonstock_lane(via: Path) -> dict:
    nd = via / NONSTOCK_REL
    eng = sorted((nd / "engine").glob("VIA_NON_STOCK_SUMMARIZER_ENGINE_v*.py")) if (nd / "engine").is_dir() else []
    core = sorted((nd / "internal").glob("NON_STOCK_CORE_v*.py")) if (nd / "internal").is_dir() else []
    man = sorted(nd.glob("REUSE_MANIFEST_v*.json"))
    seats = sorted((nd / "reuse" / "vrn2").glob("*.py")) if (nd / "reuse" / "vrn2").is_dir() else []
    wired = False
    for pat in ("functional modules/VRN2/ActivateVRN-2_v*.py", "functional modules/VRN2/VRN2_RoundAll_v*.py"):
        lt = _latest([pat], via)
        if lt and re.search(r"nonstock|NON_STOCK|SUMMARIZER_ENGINE_v03", lt.read_text(encoding="utf-8", errors="ignore")):
            wired = True
    req = None
    cont = _latest(["supportive modules/registry/VIA_Handoff_Continuity_SSOT_v*.json"], via)
    if cont:
        d = read_json(cont) or {}
        for w in (d.get("work_items") or []):
            if isinstance(w, dict) and "REQ195" in json.dumps(w, ensure_ascii=False):
                req = {k: w.get(k) for k in ("id", "status", "state", "note", "why") if k in w}
                break
    state = "READY" if (eng and core and man) else ("BLOCKED" if eng else "ABSENT")
    return {"state": state, "engine": eng[-1].name if eng else None, "core": core[-1].name if core else None, "manifest": man[-1].name if man else None, "seats": [p.name for p in seats],
            "wired_into_launcher": wired, "req195": req,
            "why": {"READY": "引擎 · 核心 · manifest 齊;接線 %s" % ("有" if wired else "無(等接)"), "BLOCKED": "internal/NON_STOCK_CORE_v*.py 缺(等操作員上傳 NON_STOCK_CORE_v0400.zip)· 引擎 REUSE_HARD_GATE 會停;啟動器今天把非個股 PDF 排除在 ⑥b(不送 · 不報錯)",
                    "ABSENT": "非個股摘要器不在倉內"}[state]}


def run(args) -> int:
    via = Path(args.via).resolve() if args.via else VIA
    vrn_dir = via / "functional modules" / "VRN"
    out_root = Path(args.out) if args.out else via / "VIA_Reports" / "vrn2"
    out_root.mkdir(parents=True, exist_ok=True)
    at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    excl, excl_src = load_excl(vrn_dir)
    mgr = _latest(["functional modules/VRN/VRN_SystemManager_v*.py"], via)
    la = launcher_tail(via)
    stock = {"launcher": la, "manager_tail": mgr.name if mgr else None, "classifier": {"source": excl_src, "pattern_len": len(excl.pattern)},
             "receipts": {k: (read_json(via / "VIA_Reports" / "vrn2" / f) or {"state": "ABSENT"}) for k, f in (("activate", "VRN2_Activate_latest.json"), ("scope", "VRN2_Scope_latest.json"), ("completion", "VRN2_Completion_latest.json"))}}
    for k, v in stock["receipts"].items():
        if isinstance(v, dict) and v.get("state") != "ABSENT":
            stock["receipts"][k] = {kk: v.get(kk) for kk in ("version", "lamp", "verdict", "at", "ts", "red", "yellow") if kk in v} | ({"stock": len(v.get("stock") or []), "non_stock": len(v.get("non_stock") or [])} if k == "scope" else {})
    stock["state"] = "READY" if (la["version"] and mgr and excl_src != "fallback(v0231 同字)") else ("DEGRADED" if (la["version"] and mgr) else "RED")
    ns = nonstock_lane(via)
    pdf_dir = Path(args.pdf_dir) if args.pdf_dir else via / FIXTURE_REL
    samples = []
    if pdf_dir.is_dir():
        for p in sorted(pdf_dir.glob("*.pdf")):
            samples.append(classify(p.name, excl, first_page_title(p) if args.read_pdf else ""))
    cnt = {"stock": sum(1 for s in samples if s["lane"] == "stock"), "non_stock": sum(1 for s in samples if s["lane"] == "non_stock")}
    lamp = "RED" if stock["state"] == "RED" else ("YELLOW" if (ns["state"] != "READY" or stock["state"] == "DEGRADED" or not samples) else "GREEN")
    rec = {"engine": ENGINE, "at": at, "lamp": lamp, "stock_lane": stock, "non_stock_lane": ns, "samples": {"dir": str(pdf_dir), "exists": pdf_dir.is_dir(), "title_lane": bool(args.read_pdf), "counts": cnt, "rows": samples},
           "meaning": {"GREEN": "兩條車道都能處理", "YELLOW": "個股車道 %s · 非個股車道 %s(%s)" % (stock["state"], ns["state"], ns["why"]), "RED": "個股車道啟動器 / 管理器缺"}[lamp],
           "note": "本檢查只讀 VRN-2 自報的收據與檔;VCGC closeout_lamp 另算(四系統對等 · 只讀互看)"}
    (out_root / "VRN2_LaneCheck_latest.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    L = ["# VRN-2 車道檢查 · %s · %s · **%s**" % (ENGINE, at, lamp), "", rec["meaning"], "", "| 車道 | 狀態 | 要件 | 說明 |", "|---|---|---|---|",
         "| 個股報告 | %s | 啟動器 %s · 管理器 %s · 分類器 %s | 收據 activate=%s scope=個股 %s / 非個股 %s |" % (stock["state"], la["version"] or "缺", stock["manager_tail"] or "缺", excl_src,
                                                                                            (stock["receipts"]["activate"] or {}).get("lamp", "ABSENT"), (stock["receipts"]["scope"] or {}).get("stock", "—"), (stock["receipts"]["scope"] or {}).get("non_stock", "—")),
         "| 非個股報告 | %s | 引擎 %s · 核心 %s · manifest %s · 席位 %d · 接線 %s | %s |" % (ns["state"], ns["engine"] or "缺", ns["core"] or "**缺**", ns["manifest"] or "缺", len(ns["seats"]), "有" if ns["wired_into_launcher"] else "無", ns["why"]),
         "", "## 樣本分類(%s · %s)" % (pdf_dir, "檔名 + 首頁" if args.read_pdf else "檔名車道"), "", "| 檔 | 車道 | 代號 | 原因 |", "|---|---|---|---|"]
    L += ["| %s | %s | %s | %s |" % (s["file"].replace("|", "/"), s["lane"], s["ticker"] or "—", s["why"]) for s in samples] or ["| (夾不在或沒有 PDF) | | | |"]
    L += ["", "個股 %d · 非個股 %d。%s" % (cnt["stock"], cnt["non_stock"], rec["note"])]
    (out_root / "VRN2_LaneCheck_latest.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("[%s] %s · 個股車道 %s(啟動器 %s)· 非個股車道 %s · 樣本 個股 %d / 非個股 %d → %s" % (lamp, ENGINE, stock["state"], la["version"], ns["state"], cnt["stock"], cnt["non_stock"], out_root / "VRN2_LaneCheck_latest.json"), flush=True)
    return 0 if lamp != "RED" else 2


def selftest() -> int:
    checks = []

    def chk(name, cond, note=""):
        checks.append((name, bool(cond), note))
        print("  [%s] %s%s" % ("PASS" if cond else "FAIL", name, (" · " + note) if note else ""), flush=True)
    env_before = dict(os.environ)
    excl, src = load_excl(HERE)
    chk("① 分類律字面抽自 %s(不執行管理器)" % CLASSIFIER_SRC, src == CLASSIFIER_SRC and "晨會" in excl.pattern)
    rows = [classify(n, excl) for n in ("MQ-1560_20260520.pdf", "Daiwa-6278_20260521.pdf", "20251208_台新台股盤勢分析.pdf", "20260916兆豐台灣產業專題-航太產業.pdf", "【中信｜債券ETF周報】_CTBC260915.pdf", "3014TT-20231005.pdf", "20251205兆豐晨會報告(二)-公司訪談摘要.pdf")]
    lanes = [r["lane"] for r in rows]
    chk("② 檔名律:MQ-1560 / Daiwa-6278 / 3014TT → 個股;盤勢 / 產業專題 / ETF 周報 / 晨會 → 非個股(含原因)", lanes == ["stock", "stock", "non_stock", "non_stock", "non_stock", "stock", "non_stock"] and all(r["why"] for r in rows))
    chk("③ 年份不當代號:20251208 不是 1208 代號;3014TT 取 3014", ticker_from_name("20251208_台新台股盤勢分析.pdf") == "" and ticker_from_name("3014TT-20231005.pdf") == "3014")
    chk("④ 首頁標題補代號:(2330 TT) → 2330;(NVDA US) → NVDA", classify("report.pdf", excl, "台積電 (2330 TT) 目標價")["ticker"] == "2330" and classify("r.pdf", excl, "NVIDIA (NVDA US)")["ticker"] == "NVDA")
    with tempfile.TemporaryDirectory(prefix="lanecheck_") as td:
        via = Path(td)
        nd = via / NONSTOCK_REL
        (nd / "engine").mkdir(parents=True)
        (nd / "engine" / "VIA_NON_STOCK_SUMMARIZER_ENGINE_v0310.py").write_text("# e\n", encoding="utf-8")
        (nd / "REUSE_MANIFEST_v0310.json").write_text("{}", encoding="utf-8")
        ns = nonstock_lane(via)
        chk("⑤ 非個股車道:核心缺 → BLOCKED · 說明寫等上傳 · 接線 無", ns["state"] == "BLOCKED" and "NON_STOCK_CORE" in ns["why"] and ns["wired_into_launcher"] is False)
        (nd / "internal").mkdir()
        (nd / "internal" / "NON_STOCK_CORE_v0400.py").write_text("# c\n", encoding="utf-8")
        chk("⑥ 核心到了 → READY", nonstock_lane(via)["state"] == "READY")
        (via / "functional modules" / "VRN").mkdir(parents=True, exist_ok=True)
        (via / "functional modules" / "VRN" / "VRN_SystemManager_v0262.py").write_text("# m\n", encoding="utf-8")
        rel = via / "docs/handoff/ai/vrn2_release_v0178"
        rel.mkdir(parents=True)
        with zipfile.ZipFile(rel / "VRN2_Closeout_v0178.zip", "w") as z:
            z.writestr("ActivateVRN-2_v0178.py", "# l\n")
            z.writestr("ActivateVRN-2_v0136.py", "# base\n")
        la = launcher_tail(via)
        chk("⑦ 啟動器尾版從發布 zip 找到 v0178(非 v0136 底座)", la["version"] == "v0178" and la["in_zip"] == "ActivateVRN-2_v0178.py")
        pdfs = via / "pdfs"
        pdfs.mkdir()
        for n in ("MQ-1560_20260520.pdf", "20251208_台新台股盤勢分析.pdf"):
            (pdfs / n).write_bytes(b"%PDF-1.4\n")
        out = via / "out"
        ns_args = argparse.Namespace(via=str(via), out=str(out), pdf_dir=str(pdfs), read_pdf=False)
        rc = run(ns_args)
        rec = json.loads((out / "VRN2_LaneCheck_latest.json").read_text(encoding="utf-8"))
        chk("⑧ run:假樹沒有 v0231 → 分類器 fallback → 個股車道 DEGRADED · 非個股 READY · 樣本 1/1 · 燈 YELLOW · md 在", rc == 0 and rec["stock_lane"]["state"] == "DEGRADED" and rec["non_stock_lane"]["state"] == "READY" and rec["samples"]["counts"] == {"stock": 1, "non_stock": 1} and rec["lamp"] == "YELLOW" and (out / "VRN2_LaneCheck_latest.md").is_file())
        (nd / "internal" / "NON_STOCK_CORE_v0400.py").unlink()
        rc = run(ns_args)
        rec = json.loads((out / "VRN2_LaneCheck_latest.json").read_text(encoding="utf-8"))
        chk("⑨ 核心拿掉 → 非個股 BLOCKED · 整體 YELLOW(不寫成綠)", rec["non_stock_lane"]["state"] == "BLOCKED" and rec["lamp"] == "YELLOW")
    src_text = Path(__file__).read_text(encoding="utf-8")
    chk("⑩ 邊界:不 import 管理器 / 不起子行程 / 不連網 · 不寫 environ", re.search(r"^\s*(import|from)\s+(subprocess|urllib|requests|VRN_SystemManager)", src_text, re.M) is None and not re.findall(r"os\.environ\[[^\]]+\]\s*=", src_text) and dict(os.environ) == env_before)
    n = sum(1 for _, ok, _ in checks if ok)
    print("[%s] %s selftest · %d/%d" % ("PASS" if n == len(checks) else "FAIL", ENGINE, n, len(checks)), flush=True)
    return 0 if n == len(checks) else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in argv or argv[:1] == ["selftest"]:                      # VCGC 站表 / 交接案用 --selftest 旗標
        return selftest()
    ap = argparse.ArgumentParser(prog="VRN_ReportLaneCheck_v0100.py", description=__doc__.split("\n")[0])
    ap.add_argument("verb", choices=["check", "selftest"])
    ap.add_argument("--via", default=None)
    ap.add_argument("--out", default=None, help="輸出夾(預設 <VIA>/VIA_Reports/vrn2)")
    ap.add_argument("--pdf-dir", dest="pdf_dir", default=None, help="樣本 PDF 夾(預設倉內 fixtures REAL_TEST_INPUT)")
    ap.add_argument("--read-pdf", dest="read_pdf", action="store_true", help="有 pymupdf 時讀首頁標題補代號")
    args = ap.parse_args(argv)
    if args.verb == "selftest":
        return selftest()
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
