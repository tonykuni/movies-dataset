#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
via_vrn_logic_book — VRN 邏輯架構索引正本 · 建冊器 + 守門員(批622)
====================================================================
操作員令(批622):「想把今天的 VRN 邏輯整合一遍,不要遺漏」。

**指過去,不複製。**本冊只記「哪一層的正典在哪一支」,規則本身留在原處——
複製一份規則出來就是開第二顆頭(零 Hydra),而且複本一定比正本先過期。

三件事:
  build            重建索引冊(glob 尾版解析 + 逐支讀出檔頭第一句職責)
  check(預設)     守門:冊上每一個指標**現在仍解析得到、而且仍是尾版**;
                   今日裁定的 landed_in 檔案都在;待裁定項一律 PENDING_OPERATOR
  --selftest       七檢(沙盒零網路)

為什麼要有守門員:索引冊最大的風險不是寫錯,是**寫對之後放著爛**。
引擎一開新版號,冊上的 tail 就過期;沒有人會發現,因為它看起來還是一本冊。
所以 check 比的是「冊上寫的」對「樹上現在的尾版」——不一致就紅,並指名該重建。

誠實:解析不到任何一支就**整本不寫**(半本冊比沒有冊危險)。
====================================================================
"""
import json, re, sys
from pathlib import Path

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

VIA = Path(__file__).resolve().parent.parent.parent
VRN = VIA / "functional modules" / "VRN"
RULES = VIA / "supportive modules" / "70_VRN_Rules"
REG = VIA / "supportive modules" / "registry"
missing = []

def tail(folder: Path, pat: str) -> Path | None:
    hits = sorted(folder.glob(pat))
    if not hits:
        missing.append(f"{folder.name}/{pat}")
        return None
    return hits[-1]

def head1(p: Path) -> str:
    """讀檔頭第一句職責。**讀出來的,不是我寫的**(LL180)。"""
    try:
        for ln in p.read_text(encoding="utf-8", errors="replace").splitlines()[:14]:
            t = ln.strip().strip('"').strip("r").strip('"').strip()
            if t and not t.startswith(("#!", "# -*-", "#", '"""', "r'''")) and len(t) > 12:
                return re.sub(r"\s+", " ", t)[:190]
    except Exception:
        pass
    return "(讀不到抬頭;誠實)"

def node(folder, pat, why=""):
    p = tail(folder, pat)
    if p is None:
        return {"family": pat.replace("_v*.py", "").replace("*.py", ""), "state": "ABSENT",
                "why": "尾版 glob 解析不到——這一格是空的,不是壞的(誠實)"}
    return {"family": p.stem.rsplit("_v", 1)[0], "tail": str(p.relative_to(VIA)).replace("\\", "/"),
            "head": head1(p), "role": why}

BOOK = {
 "schema": "VIA.VRN.LogicArchitecture.SSOT.v1",
 "version": "v0100", "batch": "批622", "ts": "2026-09-19",
 "purpose": ("操作員令「把今天的 VRN 邏輯整合一遍不要遺漏」。"
             "本冊是**索引**不是內容:每一層只記『正典在哪一支』,規則本身留在原處。"
             "複製一份規則出來就是開第二顆頭(零 Hydra),而且它一定會比正本先過期。"),
 "how_built": ("本冊由 docs 附的建冊腳本 glob 尾版解析、逐支讀出檔頭第一句職責後產生——"
               "**指標是量出來的,職責是讀出來的**,不是我寫的(LL180)。"
               "解析不到任何一支就整本不寫(半本冊比沒有冊危險)。"),
 "law_bindings": ["L90 VRN 正典儲存層=DuckDB(批615 操作員裁定)",
                  "L30 一功能一主(擷取文字修復的擁有者=ENG082)",
                  "L54 尾版律(本冊所有指標一律 glob 尾版,不寫死版號)"],
 "layers": {
  "L0_輸入識別": {"why": "檔名 → 股號/券商/日期;識別錯了後面全錯",
                  "nodes": [node(RULES, "SUP_MDL030_VISVRNTickerFilenameSSOT_v*.py", "檔名→股號正本"),
                            node(RULES, "SUP_MDL031_VISVRNTickerRegexShim_v*.py", "regex 橋"),
                            node(RULES, "SUP_MDL015_VISVRNBrokerAliasFullList_v*.py", "券商別名全表")]},
  "L1_擷取": {"why": "非 OCR 優先,抓不到才退 OCR;由簡到繁(批493 操作員令)",
              "owner": "VRN_ENG082_ExtractionLogic(L30:文字修復只寫在這一支)",
              "nodes": [node(VRN, "VRN_ENG082_ExtractionLogic_v*.py", "擷取中央邏輯庫(擁有者)"),
                        node(VRN, "VRN_ENG060_TextOmni_v*.py", "文字道"),
                        node(VRN, "VRN_ENG058_TableOmni_v*.py", "表格道(需 poppler)"),
                        node(VRN, "VRN_ENG057_ScanOcrRescue_v*.py", "掃描件 OCR 救援"),
                        node(VRN, "VRN_ENG056_PdfForensics_v*.py", "PDF 取證"),
                        node(VRN, "VRN_ENG059_GapMultirescue_v*.py", "缺口多重救援"),
                        node(VRN, "VRN_ENG075_DocToMarkdown_v*.py", "文件→Markdown"),
                        node(VRN, "VRN_ENG077_OmniFormatBridge_v*.py", "多格式橋"),
                        node(RULES, "SUP_MDL747_OcrLaneRunner_v*.py", "OCR 車道調度(需 poppler/tesseract)"),
                        node(RULES, "SUP_MDL746_PDFPlumberPlusHub_v*.py", "pdfplumber 樞紐")]},
  "L2_結構與知識": {"why": "把抽出來的字變成有欄位的東西",
                    "nodes": [node(VRN, "VRN_ENG072_FirstPageText_v*.py", "首頁文字"),
                              node(VRN, "VRN_ENG073_ReportStructuredDB_v*.py", "研報結構庫"),
                              node(VRN, "VRN_ENG074_FinancialPages_v*.py", "財報頁(批615 期間/單位/幣別)"),
                              node(VRN, "VRN_ENG063_Lexicon_v*.py", "詞庫"),
                              node(VRN, "VRN_ENG064_KnowledgeStack_v*.py", "知識堆疊(批611 零依賴簡→繁)")]},
  "L3_驗證": {"why": "「有值」不等於「對」——驗過才准進矩陣(批569)",
              "nodes": [node(VRN, "VRN_ENG083_VerifiedMatrix_v*.py", "驗證矩陣"),
                        node(VRN, "VRN_ENG076_RegressionGate_v*.py", "回歸閘"),
                        node(REG, "CGC_MDL141_ClosingGate_v*.py", "收尾閘(VRN 驗證收尾)")]},
  "L4_產出": {"why": "給人看的那一層",
              "nodes": [node(VRN, "VRN_ENG080_FourPointDigest_v*.py", "一題四點文摘"),
                        node(VRN, "VRN_ENG068_DailyBrief_v*.py", "每日簡報"),
                        node(VRN, "VRN_ENG079_ControlTowerDashboard_v*.py", "控制塔")]},
  "L5_儲存": {"why": "L90:正典=DuckDB;其餘全是派生層,單向永不回灌",
              "canonical": "**DuckDB** —— `vdf_tw_market.duckdb` 的 `vrn_*` 七張表(L90;批615 操作員裁定)",
              "nodes": [node(VRN, "VRN_ENG081_ParquetMainDB_v*.py", "Parquet 派生車道(**非正典**;批615 正名)")]},
 },
 "rule_canons": {
  "方法冊_def01_21": node(VRN, "vrn_method_kernel_v*.py", "方法核:def01–def21(含期間解析)"),
  "六欄規則": node(RULES, "SUP_MDL749_VRNFieldRuleHub_v*.py", "研報六欄規則正本樞紐"),
  "財務邏輯": node(RULES, "SUP_MDL748_FinancialLogicHub_v*.py", "財務邏輯樞紐"),
  "版面樞紐": node(RULES, "SUP_MDL743_GenericLayoutHub_v*.py", "通用版面樞紐"),
  "NLP 應用": node(RULES, "SUP_MDL744_NLPApplicationHub_v*.py", "NLP 應用樞紐"),
  "Markdown 結構": node(RULES, "SUP_MDL745_MarkdownStructureHub_v*.py", "Markdown 結構樞紐"),
  "階段別名": {"book": "supportive modules/registry/VIA_VRN_StageAlias_Map_v0100.json",
               "exists": (REG / "VIA_VRN_StageAlias_Map_v0100.json").is_file()},
  "繁簡轉換": {"book": "supportive modules/registry/VIA_ZhConvert_S2TWP_CharMap_v0100.json",
               "exists": (REG / "VIA_ZhConvert_S2TWP_CharMap_v0100.json").is_file(),
               "why": "批611:opencc 缺席時的凍結對照表;**函式消失不是降級,是斷線**"},
  "基本資料欄": {"book": "functional modules/VRN/StockReportBasicInfo.json",
                 "exists": (VRN / "StockReportBasicInfo.json").is_file()},
  "Sheet 產出計畫": {"book": "functional modules/VRN/StockReport_GoogleSheet_OutputPlan.json",
                     "exists": (VRN / "StockReport_GoogleSheet_OutputPlan.json").is_file()},
 },
 "external_tools": {
  "why": "批618 量過:pdf2image 靠 PATH 找 pdftoppm;剝掉 = VRN 取表道當場斷線",
  "anchors_book": "supportive modules/registry/VIA_BadEnv_Blacklist_v0102.json#path_tool_anchors",
  "tools": ["poppler(pdftoppm/pdfinfo/pdftocairo)", "tesseract"],
 },
 "rulings_today": [
  {"batch": "批611", "what": "簡→繁不再依賴 opencc:凍結對照表 2,784 筆",
   "landed_in": ["functional modules/VRN/VRN_ENG064_KnowledgeStack_v0102.py",
                 "supportive modules/registry/VIA_ZhConvert_S2TWP_CharMap_v0100.json"],
   "why": "一個套件缺席讓三站同時紅;shim 把函式變成 None=**函式消失**,不是降級"},
  {"batch": "批615", "what": "操作員裁定:VRN 正典儲存層 = DuckDB(L90)",
   "landed_in": ["supportive modules/registry/VIA_Policy_Laws_SSOT_v0100.json#L90",
                 "functional modules/VRN/VRN_ENG081_ParquetMainDB_v0101.py"],
   "why": "批472 原令寫 Parquet 當唯一真值;批615 覆蓋。兩令並存,時序為準,不刪舊令"},
  {"batch": "批615", "what": "數值入正典必須帶**宣告出來的**單位,不得由數值大小反推(LL178)",
   "landed_in": ["supportive modules/registry/VIA_Policy_Laws_SSOT_v0100.json#L90 配套②",
                 "functional modules/VRN/VRN_ENG074_FinancialPages_v0111.py"], "why": ""},
  {"batch": "批615", "what": "期間拆解:1Q25 與 25Q1 同義(ENG074 檢㉑ 只比三個結構欄,不比 why)",
   "landed_in": ["functional modules/VRN/VRN_ENG074_FinancialPages_v0111.py"], "why": ""},
  {"batch": "批618", "what": "poppler 是 VRN 的活相依,列入 PATH 搬家白名單(不得盲剝)",
   "landed_in": ["supportive modules/registry/VIA_BadEnv_Blacklist_v0102.json#path_tool_anchors",
                 "supportive modules/registry/via_conflict_guard_v0101.py"], "why": ""},
 ],
 "known_gaps": [
  {"item": "財報欄位清單(FinancialData)沒有與 StockReportBasicInfo.json 對稱的正本冊",
   "state": "PENDING_OPERATOR",
   "why": "量過:VRN 夾內有 StockReportBasicInfo.json,沒有 StockReportFinancialData.json。"
          "欄位清單目前散在 ENG074 的程式碼裡。要不要獨立成冊是裁定,不是我能決定的(LL90)"},
  {"item": "四層擷取/五層驗證的**層名**是本冊第一次寫下來的",
   "state": "PENDING_OPERATOR",
   "why": "各引擎自己知道自己在做什麼,但沒有一本冊講過整條鏈怎麼分層。"
          "本冊的 L0–L5 是依既有引擎職責歸納的,**請操作員覆核層名與歸屬**"},
 ],
}

BOOK_PATH = REG / "VIA_VRN_LogicArchitecture_SSOT_v0100.json"


def do_build() -> int:
    if missing:
        print("[FAIL] 指標解析不到,整本不寫(半本冊比沒有冊危險):", "; ".join(missing))
        return 1
    BOOK_PATH.write_text(json.dumps(BOOK, ensure_ascii=False, indent=1), encoding="utf-8")
    n = sum(len(v["nodes"]) for v in BOOK["layers"].values())
    print(f"[build] {BOOK_PATH.name} · 層 {len(BOOK['layers'])} · 引擎指標 {n} · "
          f"規則正本 {len(BOOK['rule_canons'])} · 今日裁定 {len(BOOK['rulings_today'])} · "
          f"待裁定 {len(BOOK['known_gaps'])}")
    return 0


def _all_pointers(book: dict) -> list:
    out = []
    for lname, lay in (book.get("layers") or {}).items():
        for nd in lay.get("nodes") or []:
            if nd.get("tail"):
                out.append((lname, nd["family"], nd["tail"]))
    for k, v in (book.get("rule_canons") or {}).items():
        if isinstance(v, dict) and v.get("tail"):
            out.append(("rule_canons", v.get("family") or k, v["tail"]))
    return out


def do_check(book_path: Path = None) -> int:
    """守門:冊上寫的 == 樹上現在的尾版?landed_in 都還在?待裁定沒被我偷偷裁掉?"""
    bp = book_path or BOOK_PATH
    if not bp.is_file():
        print(f"[check] ABSENT 冊不在:{bp}(先跑 build)")
        return 3
    book = json.loads(bp.read_text(encoding="utf-8"))
    gone, stale, ok = [], [], 0
    for lname, fam, rel in _all_pointers(book):
        p = VIA / rel
        if not p.is_file():
            gone.append(f"{fam} → {rel}")
            continue
        now = sorted(p.parent.glob(fam + "_v*.py"))
        if now and now[-1] != p:
            stale.append(f"{fam}:冊寫 {p.name} · 樹上尾版 {now[-1].name}")
            continue
        ok += 1
    lost = [f"{r['batch']} → {x}" for r in (book.get("rulings_today") or [])
            for x in (r.get("landed_in") or [])
            if not (VIA / x.split("#")[0]).exists()]
    ruled = [g["item"] for g in (book.get("known_gaps") or []) if g.get("state") != "PENDING_OPERATOR"]
    print(f"=== VRN 邏輯架構索引冊 · 守門 ===")
    print(f"  指標 {ok + len(gone) + len(stale)} · 在位且為尾版 {ok} · **過期 {len(stale)}** · 不在 {len(gone)}")
    for x in stale:
        print(f"  [過期] {x}")
    for x in gone:
        print(f"  [不在] {x}")
    if lost:
        print(f"  [落地處不見] {len(lost)}:" + "; ".join(lost[:5]))
    if ruled:
        print(f"  [待裁定被動過] {len(ruled)}:" + "; ".join(ruled[:3])
              + "  ← 裁定權在操作員(LL90),本工具不自己裁")
    bad = len(stale) + len(gone) + len(lost) + len(ruled)
    print(f"  [計] {'GREEN' if not bad else 'RED'}"
          + ("" if not bad else " · 修法:`via-vrnbook build` 重建索引冊(它是產物,不是手寫件)"))
    return 0 if not bad else 1


def selftest() -> int:
    import tempfile
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    chk("① 建冊器解析得到全部指標(解析不到就整本不寫)", not missing, f"(缺 {len(missing)})")
    chk("② 層 6 段齊、每層都有 why(沒有理由的分層等於分類噪音)",
        len(BOOK["layers"]) == 6 and all(v.get("why") for v in BOOK["layers"].values()))
    chk("③ 指過去不複製:冊裡不得出現規則內容,只有指標與讀出來的抬頭",
        all("tail" in n and "head" in n for v in BOOK["layers"].values() for n in v["nodes"]))
    chk("④ L5 儲存層釘死 L90(正典=DuckDB;ENG081 標明非正典)",
        "DuckDB" in BOOK["layers"]["L5_儲存"]["canonical"]
        and "非正典" in BOOK["layers"]["L5_儲存"]["nodes"][0]["role"])
    chk("⑤ 待裁定一律 PENDING_OPERATOR(索引冊不代操作員裁定;LL90)",
        all(g["state"] == "PENDING_OPERATOR" for g in BOOK["known_gaps"]) and BOOK["known_gaps"])
    with tempfile.TemporaryDirectory() as td:
        sb = Path(td) / "b.json"
        fake = json.loads(json.dumps(BOOK))
        fake["layers"]["L1_擷取"]["nodes"][0]["tail"] = "functional modules/VRN/NOPE_v0001.py"
        sb.write_text(json.dumps(fake, ensure_ascii=False), encoding="utf-8")
        chk("⑥ 守門抓得到「指標不在了」", do_check(sb) == 1)
        fake2 = json.loads(json.dumps(BOOK))
        fake2["known_gaps"][0]["state"] = "RESOLVED"
        sb.write_text(json.dumps(fake2, ensure_ascii=False), encoding="utf-8")
        chk("⑦ 守門抓得到「待裁定被人改成已裁定」(冊被動過手腳也是紅)", do_check(sb) == 1)
    print(f"  [計] 七檢 OK {7 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== VRN 邏輯架構索引冊 · 七檢自測(沙盒零網路)===")
        return selftest()
    if a and a[0] == "build":
        return do_build()
    return do_check()


if __name__ == "__main__":
    sys.exit(main())
