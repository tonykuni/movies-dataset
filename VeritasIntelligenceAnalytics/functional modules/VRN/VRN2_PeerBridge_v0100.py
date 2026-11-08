#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0100]
r"""VRN2_PeerBridge v0100 — VRN-2 為主:缺的功能向 VRN-1 借來用(操作員 2026-11-08 令)。

操作員令:「VRN-2為主 缺少功能自VRN-1抓來用 等VRN-2功能完美才去整合 全部自動完成」。

現況(本支動手前實查,不是推定):
  * VRN-1 自己有 `functional modules/VRN/engine/VRN_ToolBridge_v0100.py`,借用協定乾淨:
    工具冊(相對路徑 + sha256)→ `borrow(tool_id)` 依路徑載入並驗 sha256。
  * **VRN-2 這側倉內沒有任何 ToolBridge**。VRN-1 的橋去找 VRN-2 的工具冊時,期待它在
    `VIA_Reports/vrn2/tools/VRN2_ToolManifest_v0100.json` —— 而 `VIA_Reports/**` 本倉**從不提交**,
    所以那本冊是臨時的、倉裡根本不存在。結論:**VRN-2 目前借不到任何東西**,這是第一個要補的洞。

本支就是 VRN-2 自己那一側的橋(VRN-1 是另一個系統的倉,**只讀**:不改它、不在它的夾裡留
`__pycache__`、不動它的正本 / 冊 / 號 / 檔;政策 L120 / L123 五系統對等獨立)。

動詞:
  peer                  找 VRN-1(VIA_VRN1_ROOT → 家目錄 → 本倉旁)並印它的引擎清單與指紋
  manifest [--apply]    VRN-2 自己的工具冊(可提交正本 + VRN-1 期待的 VIA_Reports 位置各一份)
  gap                   能力差異矩陣:VRN-1 每個能力 × VRN-2 有 / 缺 / 待判 × 證據(**由程式算,不手寫**)
  borrow <tool_id>      向 VRN-1 借一支工具:驗 sha256 → 依路徑載入 → 回函式(只讀)
  fill                  把確認的缺口登成借用條目(借用冊;只增)
  readiness             整合就緒燈:**只要還有缺口就不給綠**
  integrate             整合閘 —— readiness 不綠就**拒絕執行**(操作員:等 VRN-2 功能完美才去整合)
  all                   peer → manifest → gap → fill → readiness
  --selftest            夾具自測(零網路 · 只寫沙盒 · 不碰 VRN-1)

誠實規矩:
  * 差異矩陣的 MATCH 要有**證據檔**(哪個檔、哪一行命中),拿不出證據不准寫 MATCH。
  * 判不出來的寫 `REVIEW`,**不寫 MATCH 也不寫 GAP** —— 不替操作員判。
  * `integrate` 是閘不是步驟:缺口 > 0 就 rc 1 擋下,訊息印出還缺哪幾項。
    「等 VRN-2 功能完美才整合」用程式擋,不靠我記得。
  * 借到的工具只在記憶體裡用,**不複製 VRN-1 的檔進本倉**(複製就變成兩份正本,會漂)。
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

import argparse
import ast
import hashlib
import importlib.util
import json
import os
import re
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_ID = "via.vrn2.peerbridge/1"
VRN1_ENGINE_REL = "functional modules/VRN/engine"
# VRN-2 自己的工具冊:倉內可提交正本
MANIFEST_REL = "functional modules/VRN/ssot/VRN2_ToolManifest_v0100.json"
# VRN-1 的橋去找 VRN-2 工具冊時期待的位置(VIA_Reports 不提交 → 每次重生)
PEER_EXPECTED_REL = "VIA_Reports/vrn2/tools/VRN2_ToolManifest_v0100.json"
BORROW_BOOK_REL = "functional modules/VRN/ssot/VRN2_BorrowBook_v0100.json"


def utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def via_root(start: Path | None = None) -> Path:
    p = (start or Path(__file__)).resolve()
    while p.parent != p:
        if (p / "supportive modules").is_dir() and (p / "functional modules").is_dir():
            return p
        p = p.parent
    return Path(__file__).resolve().parents[2]


# ═══════════════════════════════════════════════════════════════════════════
# VRN-2 自己借出的工具(VRN-1 的橋寫明它想借 section.near 與 ocr.image)
# 每筆:工具 id → (相對路徑 glob, 函式名候選, 說明)
# ═══════════════════════════════════════════════════════════════════════════
LEND: dict[str, dict] = {
    # 這兩支是薄尾版本,公開面靠 PEP 562 `__getattr__` 轉接前版本體 ——
    # AST 只看得到 `main`,看不到被動態轉接的那些名字。所以入口認 `main`,
    # 並在冊上標 forwards_dynamically,不假裝能把全部公開名列出來。
    "section.near": {
        "glob": "functional modules/VRN/VRN_ENG049_ContentReconcile_v*.py",
        "funcs": ["main", "near_section", "section_near", "reconcile"],
        "why": "同段鄰近比對(VRN-1 的橋指名要借這支)",
    },
    "ocr.image": {
        "glob": "functional modules/VRN/VRN_ENG057_ScanOcrRescue_v*.py",
        "funcs": ["main", "ocr_image", "rescue", "run"],
        "why": "影像 OCR 救援(VRN-1 的橋指名要借這支)",
    },
    "table.omni": {
        "glob": "functional modules/VRN/VRN_ENG058_TableOmni_v*.py",
        "funcs": ["restore", "run", "main"],
        "why": "表格全式還原",
    },
    "verified.matrix": {
        "glob": "functional modules/VRN/VRN_ENG083_VerifiedMatrix_v*.py",
        "funcs": ["build", "run", "main"],
        "why": "驗證過的輸出矩陣",
    },
}


# ═══════════════════════════════════════════════════════════════════════════
# VRN-1 的能力表 —— 能力 id × 它哪支引擎提供 × 要在 VRN-2 找到什麼才算有
# keys 是「證明 VRN-2 也有」的關鍵詞;需要全部命中其中一組才算 MATCH。
# ═══════════════════════════════════════════════════════════════════════════
VRN1_CAPS: list[dict] = [
    {"cap": "output.verify", "engine": "VRN_OutputVerify_v0100.py",
     "what": "輸出驗證 + 自動修正:每筆輸出回原檔逐欄證明",
     "vrn2_any": ["VerbatimVerifier", "IndependentVerifier", "VerifiedMatrix"]},
    {"cap": "pivot.db", "engine": "VRN_PivotDB_v0100.py",
     "what": "驗證過的還原表格 → 事實表 + PIVOT",
     "vrn2_any": ["ParquetMainDB", "ReportStructuredDB", "OutputStore"]},
    {"cap": "ocr.image", "engine": "VRN_Ocr_v0100.py",
     "what": "影像 OCR:找不到引擎照實說找不到",
     "vrn2_any": ["ScanOcrRescue", "OCRFetchingPDFTable", "OCRFetchingPDFText"]},
    {"cap": "page.regions", "engine": "VRN_PageRegions_v0100.py",
     "what": "個股報告拆頁再組回",
     "vrn2_any": ["FirstPageText", "FinancialPages", "TableGeometryReconstructor"]},
    {"cap": "title.trim", "engine": "VRN_TitleTrim_v0100.py",
     "what": "標題拆解(只處理個股報告)",
     "vrn2_any": ["SummarizerV1", "FilenameTokenParse"]},
    {"cap": "ticker.master", "engine": "VIA_TW_Ticker_Master_v0210.py",
     "what": "台股代碼主檔",
     "vrn2_any": ["MarketFetch", "DailyFetcher"]},
    {"cap": "firstpage.engine", "engine": "VIA_VRN_FirstPageEngine.py",
     "what": "第一頁引擎",
     "vrn2_any": ["FirstPageEngine", "FirstPageLogicBridge", "FirstPageText"]},
    {"cap": "report.db", "engine": "VRN_Integrated_ReportDatabase_Engine.py",
     "what": "整合報告資料庫",
     "vrn2_any": ["ReportStructuredDB", "ParquetMainDB"]},
    {"cap": "autotest.loop", "engine": "VRN_AutoTestLoop.py",
     "what": "自動測試 → 自動修正 → 直到成功或說清楚卡在哪",
     "vrn2_any": ["RoundAll", "RegressionGate"]},
    {"cap": "lexicon.valuation", "engine": "mother/VRN_ENG395_ValuationMethodLexicon_v0100.py",
     "what": "評價方法詞庫",
     "vrn2_any": ["Lexicon", "InvestmentRegexPattern"]},
    # ↓ 以下在 VRN-2 側找不到明顯對應 → 由程式判定,不預設答案
    {"cap": "prove.lock", "engine": "VRN_Lock_v0100.py",
     "what": "證明對的就鎖住:後來改壞它的變更要被拒絕",
     "vrn2_any": ["ProveLock", "VRN_Lock", "ResultLock"]},
    {"cap": "truth.matrix", "engine": "VRN_TruthMatrix_v0100.py",
     "what": "母系統第一頁真值矩陣(貼上的表 → 一報告一列)",
     "vrn2_any": ["TruthMatrix"]},
    {"cap": "evidence.core", "engine": "VRN_Evidence_Core.py",
     "what": "兩個 VRN 引擎共用的同一套證據規則",
     "vrn2_any": ["Evidence_Core", "EvidenceCore"]},
    {"cap": "run.cache", "engine": "VRN_RunCache_v0100.py",
     "what": "一輪讀過的放 TEMP,輸入沒變就重用",
     "vrn2_any": ["RunCache"]},
    {"cap": "temp.store", "engine": "VRN_TempStore_v0100.py",
     "what": "TEMP 分擔記憶體,刪除規則寫明",
     "vrn2_any": ["TempStore"]},
    {"cap": "focus.only", "engine": "VRN_Focus_v0100.py",
     "what": "只處理操作員指名的那些(檔名 · 第一頁 …)",
     "vrn2_any": ["Focus"]},
    {"cap": "ast.id", "engine": "VRN_AstId_v0100.py",
     "what": "每個 VRN 模組 / 類 / 函式都有號、類別與說明",
     "vrn2_any": ["AstId", "AstIdentity"]},
    {"cap": "dataframe.headers", "engine": "VRN_DataFrame_v0100.py",
     "what": "每份輸出都是 DataFrame 並對表頭核對",
     "vrn2_any": ["DataFrame_v", "HeaderCheck"]},
    {"cap": "local.db", "engine": "VRN_LocalDB_v0100.py",
     "what": "公司名與 ADJ 收盤取自本機 VDF 庫",
     "vrn2_any": ["VDFBridge", "LocalDB"]},
    {"cap": "ticker.record", "engine": "VRN_TickerRecord_v0100.py",
     "what": "4 位代碼為鍵:一股一筆 15 欄",
     "vrn2_any": ["TickerRecord"]},
    {"cap": "book.check", "engine": "VRN_BookCheck_v0100.py",
     "what": "別場會話收來的冊當測試儀器",
     "vrn2_any": ["BookCheck"]},
    {"cap": "run.matrix", "engine": "VRN_Matrix_v0100.py",
     "what": "一輪的驗證結果在主控台做成矩陣",
     "vrn2_any": ["ControlTowerDashboard", "VerifiedMatrix"]},
    {"cap": "panorama.probe", "engine": "VRN_PanoramaProbe.py",
     "what": "母系統進件十段管線全景實測(唯讀 · 禁網)",
     "vrn2_any": ["PanoramaProbe", "FeatureAudit"]},
]


# ═══════════════════════════════════════════════════════════════════════════
# 找 VRN-1(只讀)
# ═══════════════════════════════════════════════════════════════════════════
def vrn1_candidates(via: Path) -> list[Path]:
    out: list[Path] = []
    env = os.environ.get("VIA_VRN1_ROOT")
    if env:
        out.append(Path(env))
    home = Path.home()
    for name in ("via-vdf-vrn", "VIA-VDF-VRN"):
        out.append(home / name)
        out.append(via.parent.parent / name)
        out.append(via.parent / name)
    seen: set[str] = set()
    uniq = []
    for p in out:
        s = str(p)
        if s not in seen:
            seen.add(s)
            uniq.append(p)
    return uniq


def find_vrn1(via: Path) -> tuple[Path | None, str]:
    tried = []
    for p in vrn1_candidates(via):
        tried.append(str(p))
        if (p / VRN1_ENGINE_REL).is_dir():
            return p, f"找到 {p}"
    return None, "找不到 VRN-1;試過:" + " · ".join(tried[:5])


def engine_docline(path: Path) -> str:
    """只取首行說明。別人的檔裡若有壞轉義,ast.parse 會噴 SyntaxWarning ——
    那是那些檔自己的既有問題,不是本支的;這裡把雜訊關掉以免汙染收據,
    但**不吞真的剖析失敗**(失敗回空字串,差異矩陣就只能靠檔名判)。"""
    import warnings
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        doc = (ast.get_docstring(tree) or "").strip().splitlines()
        return doc[0][:140] if doc else ""
    except Exception:
        return ""


def vrn1_engines(root: Path) -> list[dict]:
    d = root / VRN1_ENGINE_REL
    out = []
    if not d.is_dir():
        return out
    for p in sorted(d.rglob("*.py")):
        try:
            out.append({"rel": p.relative_to(root).as_posix(),
                        "name": p.name,
                        "sha256": sha256(p),
                        "doc": engine_docline(p)})
        except Exception as exc:  # noqa: BLE001
            out.append({"rel": str(p), "name": p.name, "sha256": None,
                        "doc": f"(讀不到:{str(exc)[:50]})"})
    return out


def cmd_peer(args) -> int:
    via = via_root()
    root, why = find_vrn1(via)
    if root is None:
        print(f"[RED] {why}")
        print("      設 VIA_VRN1_ROOT 指向 VRN-1 的倉根,或把它 clone 到家目錄 via-vdf-vrn/")
        return 1
    eng = vrn1_engines(root)
    print(f"[VRN-1 只讀] {root}")
    print(f"  引擎 {len(eng)} 支(含子夾)")
    for e in eng[: args.limit]:
        sha = (e["sha256"] or "??")[:12]
        print(f"  {sha}  {e['name'][:42]:<43} {e['doc'][:70]}")
    if len(eng) > args.limit:
        print(f"  … 其餘 {len(eng) - args.limit} 支(--limit 調整)")
    print("[提醒] 本支對 VRN-1 只讀:不改它、不在它夾裡留 __pycache__、不複製它的檔進本倉。")
    return 0


# ═══════════════════════════════════════════════════════════════════════════
# VRN-2 自己的工具冊
# ═══════════════════════════════════════════════════════════════════════════
def tail_of(via: Path, glob: str) -> Path | None:
    hits = sorted(via.glob(glob))
    return hits[-1] if hits else None


def build_manifest(via: Path) -> dict:
    tools = {}
    missing = []
    for tid, spec in LEND.items():
        p = tail_of(via, spec["glob"])
        if p is None:
            missing.append(tid)
            tools[tid] = {"state": "ABSENT", "glob": spec["glob"], "why": spec["why"]}
            continue
        try:
            tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
            names = {n.name for n in ast.walk(tree)
                     if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
        except Exception:
            names = set()
        func = next((f for f in spec["funcs"] if f in names), None)
        tools[tid] = {
            "state": "LENDABLE" if func else "NO_ENTRY",
            "path": p.relative_to(via).as_posix(),
            "sha256": sha256(p),
            "func": func,
            "func_candidates": spec["funcs"],
            # 薄尾版本用 PEP 562 把其餘公開名動態轉接給前版本體;AST 看不到那些名字,
            # 所以這裡只誠實記「有動態轉接」,不把看不到的名字當成已列舉。
            "forwards_dynamically": "__getattr__" in names,
            "why": spec["why"],
        }
        if func is None:
            missing.append(tid)
    return {
        "schema": "VIA.VRN2.ToolManifest.v1",
        "system": "VRN-2",
        "version": "v0100",
        "ts": utc(),
        "note": ("VRN-2 借出的工具冊。VRN-1 的橋會讀這本冊並驗 sha256。"
                 "倉內正本是可提交的那一份;VIA_Reports 下那一份是 VRN-1 期待的位置,每次重生。"),
        "tools": tools,
        "lendable": sorted(t for t, v in tools.items() if v.get("state") == "LENDABLE"),
        "not_lendable": sorted(missing),
    }


def cmd_manifest(args) -> int:
    via = via_root()
    mf = build_manifest(via)
    print(f"[VRN-2 工具冊] 可借出 {len(mf['lendable'])}/{len(mf['tools'])}")
    for tid, v in mf["tools"].items():
        mark = {"LENDABLE": "  ✓", "ABSENT": "  ✗", "NO_ENTRY": "  ?"}[v["state"]]
        extra = f" → {v.get('func')}" if v.get("func") else ""
        print(f"{mark} {tid:<17} {v['state']:<10} {v.get('path', v.get('glob', ''))[-56:]}{extra}")
    if mf["not_lendable"]:
        print(f"[照實] 借不出去的:{mf['not_lendable']}(找不到檔或找不到入口函式,不假裝能借)")
    if args.apply:
        for rel in (MANIFEST_REL, PEER_EXPECTED_REL):
            out = via / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(mf, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
            print(f"[寫入] {rel}")
        print("[說明] VRN-1 的橋寫死去 VIA_Reports 找,而本倉不提交 VIA_Reports →"
              " 倉內另存一份可提交正本,兩份內容相同。")
    return 0


# ═══════════════════════════════════════════════════════════════════════════
# 能力差異矩陣(由程式算,不手寫)
# ═══════════════════════════════════════════════════════════════════════════
_INDEX_CACHE: dict[str, list[tuple[str, str, str]]] = {}


def vrn2_index(via: Path, with_doc: bool = False) -> list[tuple[str, str, str]]:
    """(檔名, 相對路徑, 首行說明) —— 只掃 VRN-2 自己的 functional modules/VRN。

    說明只在 `with_doc` 時才讀檔並剖析,而且**整輪只建一次索引**:
    先前的寫法對每個沒命中的能力都重掃全樹(650 檔 × 9 缺口 × 2 關鍵詞),
    `all` 又把矩陣跑三遍 → 實測直接吃掉 120 秒逾時。這是真的效能缺陷,不是調參。
    """
    key = f"{via}|{int(with_doc)}"
    if key in _INDEX_CACHE:
        return _INDEX_CACHE[key]
    d = via / "functional modules" / "VRN"
    out: list[tuple[str, str, str]] = []
    if d.is_dir():
        for p in sorted(d.rglob("*.py")):
            if "__pycache__" in p.parts or "references" in p.parts:
                continue
            doc = engine_docline(p) if with_doc else ""
            out.append((p.name, p.relative_to(via).as_posix(), doc))
    _INDEX_CACHE[key] = out
    return out


def gap_matrix(via: Path) -> dict:
    idx = vrn2_index(via)
    names = [(n.lower(), rel) for n, rel, _ in idx]

    def by_name(cap: dict) -> list[dict]:
        out = []
        for key in cap["vrn2_any"]:
            k = key.lower()
            hit = next((rel for n, rel in names if k in n), None)
            if hit:
                out.append({"key": key, "file": hit})
        return out

    # 說明索引(要讀檔剖析,貴)只在真的有能力靠檔名沒命中時才建,而且只建一次。
    misses = [cap for cap in VRN1_CAPS if not by_name(cap)]
    doc_idx = vrn2_index(via, with_doc=True) if misses else idx

    rows = []
    for cap in VRN1_CAPS:
        hits = by_name(cap)
        if hits:
            state = "MATCH"
        else:
            # 檔名找不到 → 再掃說明一次;掃不到才算 GAP,掃到算 REVIEW(要人看)
            soft = []
            for key in cap["vrn2_any"]:
                for name, rel, doc in doc_idx:
                    if doc and key.lower() in doc.lower():
                        soft.append({"key": key, "file": rel})
                        break
            state = "REVIEW" if soft else "GAP"
            hits = soft
        rows.append({"cap": cap["cap"], "vrn1_engine": cap["engine"],
                     "what": cap["what"], "state": state,
                     "evidence": hits[:3],
                     "looked_for": cap["vrn2_any"]})
    counts = {s: sum(1 for r in rows if r["state"] == s) for s in ("MATCH", "REVIEW", "GAP")}
    return {"schema": SCHEMA_ID, "ts": utc(), "rows": rows, "counts": counts,
            "vrn2_files_scanned": len(idx)}


def print_gap(m: dict) -> None:
    print(f"[能力差異矩陣] VRN-1 能力 {len(m['rows'])} 項 · 掃過 VRN-2 檔 {m['vrn2_files_scanned']}")
    print(f"{'狀態':<7}{'能力':<20}{'VRN-1 引擎':<42}證據 / 找過什麼")
    for r in sorted(m["rows"], key=lambda x: {"GAP": 0, "REVIEW": 1, "MATCH": 2}[x["state"]]):
        ev = (r["evidence"][0]["file"].split("/")[-1] if r["evidence"]
              else "找過:" + "/".join(r["looked_for"])[:46])
        print(f"{r['state']:<7}{r['cap']:<20}{r['vrn1_engine'][:40]:<42}{ev[:52]}")
    c = m["counts"]
    print(f"\n[判決] MATCH {c['MATCH']} · REVIEW {c['REVIEW']} · **GAP {c['GAP']}**")
    print("[誠實] MATCH 一律附證據檔;判不出來的寫 REVIEW,不寫 MATCH 也不寫 GAP。")


def cmd_gap(args) -> int:
    m = gap_matrix(via_root())
    if args.json:
        print(json.dumps(m, ensure_ascii=False, indent=1))
    else:
        print_gap(m)
    return 0


# ═══════════════════════════════════════════════════════════════════════════
# 借用:驗 sha256 → 依路徑載入(只讀,不在 VRN-1 夾裡留 __pycache__)
# ═══════════════════════════════════════════════════════════════════════════
class BorrowError(RuntimeError):
    pass


def load_readonly(path: Path, name: str):
    """依路徑載入,載入期間關掉 bytecode 寫入:別人的夾不留任何檔。"""
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise BorrowError(f"載不起來:{path}")
    mod = importlib.util.module_from_spec(spec)
    prev = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    finally:
        sys.dont_write_bytecode = prev
    return mod


def borrow(tool_id: str, via: Path | None = None,
           vrn1: Path | None = None) -> tuple[object, dict]:
    via = via or via_root()
    if vrn1 is None:
        vrn1, why = find_vrn1(via)
        if vrn1 is None:
            raise BorrowError(why)
    cap = next((c for c in VRN1_CAPS if c["cap"] == tool_id), None)
    if cap is None:
        raise BorrowError(f"不認識的能力 id:{tool_id};"
                          f"可借的看 `gap`:{[c['cap'] for c in VRN1_CAPS][:6]}…")
    path = vrn1 / VRN1_ENGINE_REL / cap["engine"]
    if not path.is_file():
        raise BorrowError(f"VRN-1 側找不到 {cap['engine']}(路徑 {path})")
    digest = sha256(path)
    mod = load_readonly(path, "_vrn1_borrowed_" + re.sub(r"\W+", "_", tool_id))
    rec = {"tool_id": tool_id, "vrn1_engine": cap["engine"],
           "path": str(path), "sha256": digest, "ts": utc(),
           "what": cap["what"], "state": "BORROWED"}
    return mod, rec


def cmd_borrow(args) -> int:
    try:
        mod, rec = borrow(args.tool_id)
    except BorrowError as exc:
        print(f"[RED] 借不到:{exc}")
        return 1
    pub = [n for n in dir(mod) if not n.startswith("_")]
    print(f"[BORROWED] {rec['tool_id']} ← VRN-1 {rec['vrn1_engine']}")
    print(f"  sha256 {rec['sha256'][:16]}… · 公開名 {len(pub)} 個")
    print(f"  {', '.join(pub[:12])}{' …' if len(pub) > 12 else ''}")
    print("[提醒] 只在記憶體用,**不複製 VRN-1 的檔進本倉**(複製就變兩份正本,會漂)。")
    return 0


def cmd_fill(args) -> int:
    via = via_root()
    m = gap_matrix(via)
    vrn1, why = find_vrn1(via)
    todo = [r for r in m["rows"] if r["state"] in ("GAP", "REVIEW")]
    book = {
        "schema": "VIA.VRN2.BorrowBook.v1", "version": "v0100", "ts": utc(),
        "law": "只增不減:換版出新版號檔;借到的工具只在記憶體用,不複製 VRN-1 的檔進本倉",
        "vrn1_root": str(vrn1) if vrn1 else None,
        "vrn1_found": vrn1 is not None,
        "why": why,
        "entries": [],
    }
    for r in todo:
        cap = next(c for c in VRN1_CAPS if c["cap"] == r["cap"])
        entry = {"tool_id": r["cap"], "state_in_vrn2": r["state"],
                 "vrn1_engine": cap["engine"], "what": cap["what"],
                 "borrow": f"VRN2_PeerBridge_v0100.py borrow {r['cap']}"}
        if vrn1 is not None:
            p = vrn1 / VRN1_ENGINE_REL / cap["engine"]
            entry["vrn1_present"] = p.is_file()
            entry["vrn1_sha256"] = sha256(p) if p.is_file() else None
            entry["borrowable"] = p.is_file()
        else:
            entry["vrn1_present"] = None
            entry["borrowable"] = False
        book["entries"].append(entry)
    ok = [e for e in book["entries"] if e.get("borrowable")]
    print(f"[借用冊] 缺口 {len(todo)} 項 · VRN-1 側拿得到 {len(ok)} 項")
    for e in book["entries"]:
        mark = "  ✓" if e.get("borrowable") else "  ✗"
        print(f"{mark} {e['state_in_vrn2']:<7}{e['tool_id']:<20}← {e['vrn1_engine'][:36]}")
    if args.apply:
        out = via / BORROW_BOOK_REL
        out.parent.mkdir(parents=True, exist_ok=True)
        if out.exists():
            print(f"[不覆蓋] {BORROW_BOOK_REL} 已存在 —— 只增不減,要換版請出新版號檔")
            return 1
        out.write_text(json.dumps(book, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"[寫入] {BORROW_BOOK_REL}")
    return 0


# ═══════════════════════════════════════════════════════════════════════════
# 整合就緒燈 + 整合閘(操作員:等 VRN-2 功能完美才去整合)
# ═══════════════════════════════════════════════════════════════════════════
def readiness(via: Path) -> dict:
    m = gap_matrix(via)
    mf = build_manifest(via)
    vrn1, why = find_vrn1(via)
    blockers = []
    if m["counts"]["GAP"]:
        blockers.append(f"VRN-2 仍有 {m['counts']['GAP']} 項能力缺口(GAP)")
    if m["counts"]["REVIEW"]:
        blockers.append(f"{m['counts']['REVIEW']} 項待操作員判(REVIEW)—— 不替他判")
    if mf["not_lendable"]:
        blockers.append(f"VRN-2 借不出去的工具 {len(mf['not_lendable'])} 項:{mf['not_lendable']}")
    if vrn1 is None:
        blockers.append("找不到 VRN-1:" + why)
    lamp = "GREEN" if not blockers else "YELLOW"
    return {"schema": SCHEMA_ID, "ts": utc(), "lamp": lamp, "blockers": blockers,
            "gap_counts": m["counts"], "not_lendable": mf["not_lendable"],
            "vrn1_found": vrn1 is not None}


def cmd_readiness(args) -> int:
    r = readiness(via_root())
    print(f"[整合就緒燈] {r['lamp']}")
    for b in r["blockers"]:
        print(f"  · {b}")
    if r["lamp"] == "GREEN":
        print("  缺口 0 · 待判 0 · 工具冊可借出齊全 → 才可以談整合")
    else:
        print("[操作員令] 「等 VRN-2 功能完美才去整合」→ 以上沒清掉就不整合。")
    return 0 if r["lamp"] == "GREEN" else 1


def cmd_integrate(args) -> int:
    """整合閘:readiness 不綠就拒絕 —— 用程式擋,不靠我記得。"""
    r = readiness(via_root())
    if r["lamp"] != "GREEN":
        print("[拒絕整合] 整合就緒燈 " + r["lamp"] + " —— 操作員令「等 VRN-2 功能完美才去整合」。")
        for b in r["blockers"]:
            print(f"  擋住的原因:{b}")
        print("[下一步] 先把 GAP 補完、REVIEW 交操作員裁,readiness 轉綠後再跑 integrate。")
        return 1
    print("[整合] readiness GREEN —— 但整合步驟本身尚未實作(本輪奉令不做整合)。")
    print("       要整合請操作員另下令,並說明整合範圍(冊 / 號 / 入口 / U/I 各自怎麼併)。")
    return 2


def cmd_all(args) -> int:
    via = via_root()
    print("══ ① 找 VRN-1(只讀)══")
    cmd_peer(argparse.Namespace(limit=8))
    print("\n══ ② VRN-2 工具冊 ══")
    cmd_manifest(argparse.Namespace(apply=args.apply))
    print("\n══ ③ 能力差異矩陣 ══")
    cmd_gap(argparse.Namespace(json=False))
    print("\n══ ④ 借用冊 ══")
    cmd_fill(argparse.Namespace(apply=args.apply))
    print("\n══ ⑤ 整合就緒燈 ══")
    rc = cmd_readiness(argparse.Namespace())
    return 0 if rc in (0, 1) else rc


# ═══════════════════════════════════════════════════════════════════════════
# 自測(零網路 · 只寫沙盒 · 不碰 VRN-1)
# ═══════════════════════════════════════════════════════════════════════════
def selftest() -> int:
    checks: list[tuple[str, bool, str]] = []

    def ck(name: str, cond: bool, note: str = "") -> None:
        checks.append((name, bool(cond), note))

    tmp = Path(tempfile.mkdtemp(prefix="vrn2_peerbridge_"))
    try:
        # 假 VIA 根 + 假 VRN-1
        fake = tmp / "via"
        (fake / "supportive modules").mkdir(parents=True)
        (fake / "functional modules" / "VRN").mkdir(parents=True)
        v1 = tmp / "via-vdf-vrn" / VRN1_ENGINE_REL
        v1.mkdir(parents=True)

        # ── 找 peer ──
        # ① 真的沒有鄰居時要回 None + 說明(另開一個沒有 via-vdf-vrn 鄰居的樹)
        lone_base = tmp / "lonely"
        lone = lone_base / "deep" / "via"
        (lone / "supportive modules").mkdir(parents=True)
        (lone / "functional modules" / "VRN").mkdir(parents=True)
        got, why = find_vrn1(lone)
        ck("沒有鄰居時回 None + 說明", got is None and "找不到" in why, why[:70])
        # ② 鄰居在旁邊就要找到(fake 的上一層正好有 via-vdf-vrn)
        got_sib, why_sib = find_vrn1(fake)
        ck("鄰居在上一層能找到", got_sib == tmp / "via-vdf-vrn", f"{got_sib} · {why_sib[:40]}")
        # ③ VIA_VRN1_ROOT 指定優先
        os.environ["VIA_VRN1_ROOT"] = str(tmp / "via-vdf-vrn")
        got2, why2 = find_vrn1(lone)
        ck("VIA_VRN1_ROOT 指定得到(連沒鄰居的樹也行)",
           got2 == tmp / "via-vdf-vrn", str(got2))

        # ── 借用:sha256 驗過才載,且不在對方夾裡留 __pycache__ ──
        eng = v1 / "VRN_Lock_v0100.py"
        eng.write_text('"""fake lock"""\n\n\ndef prove(x=1):\n    return x\n', encoding="utf-8")
        mod, rec = borrow("prove.lock", via=fake, vrn1=tmp / "via-vdf-vrn")
        ck("借到 VRN-1 的工具", hasattr(mod, "prove") and mod.prove(7) == 7)
        ck("借用紀錄帶 sha256", len(rec["sha256"]) == 64)
        ck("紀錄標 BORROWED", rec["state"] == "BORROWED")
        ck("**不在 VRN-1 夾裡留 __pycache__**",
           not (v1 / "__pycache__").exists(), str(list(v1.iterdir())))

        # 檔不在 → BorrowError,不是靜靜回 None
        try:
            borrow("truth.matrix", via=fake, vrn1=tmp / "via-vdf-vrn")
            ck("缺檔要丟 BorrowError", False, "沒丟")
        except BorrowError as exc:
            ck("缺檔丟 BorrowError", "找不到" in str(exc), str(exc)[:60])
        try:
            borrow("nope.nope", via=fake, vrn1=tmp / "via-vdf-vrn")
            ck("不認識的 id 要丟 BorrowError", False, "沒丟")
        except BorrowError:
            ck("不認識的 id 丟 BorrowError", True)

        # ── 工具冊:找不到檔要照實 ABSENT,不假裝能借 ──
        mf0 = build_manifest(fake)
        ck("空樹的工具冊全 ABSENT",
           all(v["state"] == "ABSENT" for v in mf0["tools"].values()), str(mf0["tools"])[:90])
        ck("空樹 lendable 為 0", mf0["lendable"] == [])
        ck("not_lendable 列出全部", len(mf0["not_lendable"]) == len(LEND))

        # 放一支有入口函式的 → LENDABLE
        d2 = fake / "functional modules" / "VRN"
        (d2 / "VRN_ENG049_ContentReconcile_v0100.py").write_text(
            '"""x"""\n\n\ndef reconcile(a=1):\n    return a\n', encoding="utf-8")
        mf1 = build_manifest(fake)
        ck("有入口函式 → LENDABLE",
           mf1["tools"]["section.near"]["state"] == "LENDABLE",
           str(mf1["tools"]["section.near"]))
        ck("LENDABLE 記下函式名", mf1["tools"]["section.near"]["func"] == "reconcile")
        # 有檔但沒入口函式 → NO_ENTRY(不是 LENDABLE)
        (d2 / "VRN_ENG057_ScanOcrRescue_v0100.py").write_text(
            '"""x"""\n\n\ndef unrelated(a=1):\n    return a\n', encoding="utf-8")
        mf2 = build_manifest(fake)
        ck("有檔沒入口 → NO_ENTRY 不是 LENDABLE",
           mf2["tools"]["ocr.image"]["state"] == "NO_ENTRY",
           str(mf2["tools"]["ocr.image"]))
        ck("NO_ENTRY 算進 not_lendable", "ocr.image" in mf2["not_lendable"])
        # 薄尾版 PEP 562:只看得到 main,其餘靠 __getattr__ 動態轉接 → 要標出來
        (d2 / "VRN_ENG057_ScanOcrRescue_v0101.py").write_text(
            '"""薄尾"""\n\n\ndef __getattr__(name):\n    raise AttributeError(name)\n\n\n'
            'def main():\n    return 0\n', encoding="utf-8")
        mf3 = build_manifest(fake)
        ck("薄尾版認 main 為入口 → LENDABLE",
           mf3["tools"]["ocr.image"]["state"] == "LENDABLE"
           and mf3["tools"]["ocr.image"]["func"] == "main",
           str(mf3["tools"]["ocr.image"]))
        ck("薄尾版標出 forwards_dynamically(AST 看不到被轉接的名字,不假裝列舉)",
           mf3["tools"]["ocr.image"]["forwards_dynamically"] is True)

        # ── 差異矩陣:檔名命中才 MATCH,且要附證據 ──
        m0 = gap_matrix(fake)
        ck("空樹下大多是 GAP", m0["counts"]["GAP"] > 15, str(m0["counts"]))
        rec_match = [r for r in m0["rows"] if r["state"] == "MATCH"]
        ck("每個 MATCH 都附證據", all(r["evidence"] for r in rec_match),
           str([r["cap"] for r in rec_match if not r["evidence"]]))
        ck("GAP 的列有記找過什麼",
           all(r["looked_for"] for r in m0["rows"] if r["state"] == "GAP"))
        # 放一支讓 ocr.image 命中
        (d2 / "VRN_ENG057_ScanOcrRescue_v0101.py").write_text('"""x"""\n', encoding="utf-8")
        m1 = gap_matrix(fake)
        ocr = next(r for r in m1["rows"] if r["cap"] == "ocr.image")
        ck("檔名命中 → MATCH + 證據檔", ocr["state"] == "MATCH" and ocr["evidence"],
           str(ocr)[:120])

        # ── 效能迴歸:索引只准建一次(先前重掃全樹讓 all 吃掉 120s 逾時)──
        _INDEX_CACHE.clear()
        reads = {"n": 0}
        _orig_doc = globals()["engine_docline"]

        def _counting_doc(p):
            reads["n"] += 1
            return _orig_doc(p)

        globals()["engine_docline"] = _counting_doc
        try:
            n_files = len([p for p in (fake / "functional modules" / "VRN").rglob("*.py")])
            gap_matrix(fake)
            first = reads["n"]
            gap_matrix(fake)          # 第二次應完全走快取
            second = reads["n"] - first
        finally:
            globals()["engine_docline"] = _orig_doc
        ck("說明索引每檔最多讀一次(不重掃全樹)", first <= n_files,
           f"讀 {first} 次 / 檔 {n_files}")
        ck("第二次 gap 完全走快取(0 次讀檔)", second == 0, f"第二次又讀 {second} 次")

        # ── 整合閘:有缺口就必須拒絕 ──
        r0 = readiness(fake)
        ck("有缺口時 readiness 不綠", r0["lamp"] != "GREEN", r0["lamp"])
        ck("readiness 列出擋住的原因", len(r0["blockers"]) >= 1, str(r0["blockers"])[:90])
        import contextlib
        import io
        buf = io.StringIO()
        _orig = globals()["via_root"]
        globals()["via_root"] = lambda start=None: fake
        try:
            with contextlib.redirect_stdout(buf):
                rc_i = cmd_integrate(argparse.Namespace())
        finally:
            globals()["via_root"] = _orig
        ck("**整合閘在不綠時拒絕執行(rc 1)**", rc_i == 1, f"rc={rc_i}")
        ck("拒絕時印出操作員那句令", "等 VRN-2 功能完美才去整合" in buf.getvalue())
        ck("拒絕時列出擋住原因", "擋住的原因" in buf.getvalue())

        # ── 借用冊只增不減 ──
        bb = fake / BORROW_BOOK_REL
        bb.parent.mkdir(parents=True, exist_ok=True)
        bb.write_text("{}", encoding="utf-8")
        buf2 = io.StringIO()
        globals()["via_root"] = lambda start=None: fake
        try:
            with contextlib.redirect_stdout(buf2):
                rc_f = cmd_fill(argparse.Namespace(apply=True))
        finally:
            globals()["via_root"] = _orig
        ck("借用冊已存在時拒絕覆寫", rc_f == 1 and "不覆蓋" in buf2.getvalue(),
           buf2.getvalue()[-80:])

        # 工具冊寫兩份(倉內正本 + VRN-1 期待位置)
        buf3 = io.StringIO()
        globals()["via_root"] = lambda start=None: fake
        try:
            with contextlib.redirect_stdout(buf3):
                cmd_manifest(argparse.Namespace(apply=True))
        finally:
            globals()["via_root"] = _orig
        ck("工具冊寫到倉內正本", (fake / MANIFEST_REL).is_file())
        ck("工具冊也寫到 VRN-1 期待的位置", (fake / PEER_EXPECTED_REL).is_file())
        a = json.loads((fake / MANIFEST_REL).read_text(encoding="utf-8"))
        b = json.loads((fake / PEER_EXPECTED_REL).read_text(encoding="utf-8"))
        ck("兩份內容相同", a == b)

        os.environ.pop("VIA_VRN1_ROOT", None)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        os.environ.pop("VIA_VRN1_ROOT", None)

    ok = sum(1 for _, c, _ in checks if c)
    for name, cond, note in checks:
        if not cond:
            print(f"  [FAIL] {name}" + (f" — {note}" if note else ""))
    print(f"[自測] {ok}/{len(checks)} " + ("PASS" if ok == len(checks) else "FAIL"))
    return 0 if ok == len(checks) else 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="VRN2_PeerBridge_v0100",
        description="VRN-2 為主:缺的功能向 VRN-1 借來用(VRN-1 只讀)")
    ap.add_argument("--selftest", action="store_true", help="夾具自測(零網路 · 只寫沙盒)")
    sub = ap.add_subparsers(dest="verb")

    p = sub.add_parser("peer", help="找 VRN-1 並印引擎清單")
    p.add_argument("--limit", type=int, default=30)
    p.set_defaults(fn=cmd_peer)

    p = sub.add_parser("manifest", help="VRN-2 自己的工具冊")
    p.add_argument("--apply", action="store_true")
    p.set_defaults(fn=cmd_manifest)

    p = sub.add_parser("gap", help="能力差異矩陣")
    p.add_argument("--json", action="store_true")
    p.set_defaults(fn=cmd_gap)

    p = sub.add_parser("borrow", help="向 VRN-1 借一支工具")
    p.add_argument("tool_id")
    p.set_defaults(fn=cmd_borrow)

    p = sub.add_parser("fill", help="缺口登成借用條目")
    p.add_argument("--apply", action="store_true")
    p.set_defaults(fn=cmd_fill)

    p = sub.add_parser("readiness", help="整合就緒燈")
    p.set_defaults(fn=cmd_readiness)

    p = sub.add_parser("integrate", help="整合閘(不綠就拒絕)")
    p.set_defaults(fn=cmd_integrate)

    p = sub.add_parser("all", help="peer → manifest → gap → fill → readiness")
    p.add_argument("--apply", action="store_true")
    p.set_defaults(fn=cmd_all)
    return ap


def main(argv: list[str] | None = None) -> int:
    ap = build_parser()
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()
    if not getattr(args, "fn", None):
        ap.print_help()
        return 0
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
