#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
via_vrn_logic_book — VRN 邏輯架構索引正本 · 建冊器 + 守門員(批622;批641 v0101)

v0100→v0101(批641 **冊上少了四支,而且沒有任何一道檢會說**)
  批640 我把 ENG085 接完、跑完、推完,然後跑 `via-vrnbook build` ——
  它印「引擎指標 25」,**零 diff**。ENG085 從頭到尾沒進過這本冊。
  一量:樹上 38 個 VRN_ENG 家族,冊上 19 個,**ENG084/085/086/087 四支全不在**
  (084/085 是批634/640 我自己造的,086/087 更早)。
  根因不是誰忘了,是 `BOOK["layers"]` 是**手寫名冊**:寫上去的會被守門,
  沒寫上去的連「不在」都不會被提起——**寫死的名冊會把新加的件從帳上抹掉**(LL213 同型)。
  v0101 兩件事:
    ① 四支就位(084→L0 輸入識別 · 085/086/087→L2 結構與知識)。
    ② 加檢⑧「樹上每一個 VRN_ENG 家族都要被交代」:不是要求全部上冊——
       有些本來就不該上(共識源、郵件、心智圖…)。要求的是**列出來**:
       在冊上,或在 `OFF_BOOK_PENDING` 裡帶著讀出來的抬頭掛 PENDING_OPERATOR。
       **哪一支該上架構冊是架構裁定,裁定權在操作員**(LL90);
       我能做的是不讓它安靜地不見(L92:哨兵抓到就要給得出下一步)。
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

def probe(folder: Path, family: str) -> Path | None:
    """只探、不記帳。**不得把待裁定清單的探路寫進 `missing`**。

    批641 自訂正:第一版拿 `tail()` 去讀 OFF_BOOK_PENDING 的抬頭,結果
    ENG017/018/023 這三支**沒有 `_vNNNN` 版號**(檔名就是 `…FetchingPDFTable.py`),
    `tail()` 便把它們記成「解析不到」,檢① 當場紅 —— **樹沒問題,是我的尺**(L93)。
    """
    hits = sorted(folder.glob(f"{family}_v*.py")) or sorted(folder.glob(f"{family}.py"))
    return hits[-1] if hits else None


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

#: 批641:**樹上有、架構冊上沒有**的 VRN_ENG 家族。
#: 這不是「漏了」的清單,是「還沒裁定該不該上架構冊」的清單——
#: 多數是共識源/郵件/心智圖/舊 MDL 轉正件,本來就未必屬於那六層。
#: 抬頭一律由 `head1()` 從樹上讀出來,**不是我寫的**(LL180);裁定權在操作員(LL90)。
OFF_BOOK_PENDING = []          # 批662:這 15 支已歸位(見下);這裡只留**未來**樹上新冒出來、名冊上沒有的

#: 批662(操作員令「把邏輯整理成功即可」)——**15 支活在樹上、卻說不出在鏈上哪個位置**,
#: 那就是「邏輯沒整理完」的具體長相。本批把它們歸位。
#:
#: **憑據不是我的直覺,是系統自己對每支的定義**:
#:   優先用**格子站名**(那是系統驗收它時用的一句話),站名沒有的用 docstring 第一句。
#:   11 支有格子站在跑(有自測、被驗收),4 支沒有——兩種都記下來,不含糊。
#: 每一筆都帶 `evidence`,操作員要推翻任何一支,看那一行就夠;改這張表就改得動(LL90 仍在)。
OFF_BOOK_PLACED = {
    # ── L1 擷取(六層的 why:非 OCR 優先,抓不到才退 OCR)──
    "VRN_ENG017_MDL004OCRFetchingPDFTable":
        ("L1_擷取", "OCR 退路:PDF 表格", "docstring 首句 `VRN_MDL004_OCR_FetchingPDFTable`(無格子站)"),
    "VRN_ENG018_MDL005OCRFetchingPDFText":
        ("L1_擷取", "OCR 退路:PDF 純文字", "docstring 首句 `VRN_MDL005_OCRFetchingPDFText`(無格子站)"),
    "VRN_ENG023_MDL011DailyFetcher":
        ("L1_擷取", "對外取料(法遵雙閘)", "docstring「統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT)」(無格子站)"),
    "VRN_ENG052_DocxEngine":
        ("L1_擷取", "DOCX 深度解析", "格子站名「docx 引擎(doc)」"),
    "VRN_ENG070_YahooConsensus":
        ("L1_擷取", "對外取共識資料", "格子站名「Yahoo 共識八檢(批194)」"),
    # ── L2 結構與知識(把抽出來的字變成有欄位的東西)──
    "VRN_ENG055_OfficeMerge":
        ("L2_結構與知識", "Office 併主表", "格子站名「office 併表橋(dry)」"),
    "VRN_ENG066_NLPSupportHub":
        ("L2_結構與知識", "NLP 工具樞紐", "格子站名「NLP 支援樞紐九檢(批157)」"),
    "VRN_ENG067_MindMapSSOT":
        ("L2_結構與知識", "三語關鍵字 SSOT×分類", "格子站名「三語 SSOT×MindMap 九檢(批158)」"),
    "VRN_ENG071_CnyesFusion":
        ("L2_結構與知識", "共識融合", "格子站名「鉅亨 FactSet 共識九檢(批199)」"),
    "VRN_ENG078_NLPOneBridge":
        ("L2_結構與知識", "NLP 正主橋", "格子站名「NLP OneEngine 橋自測(批283)」"),
    # ── L3 驗證(有值不等於對)──
    "VRN_ENG049_ContentReconcile":
        ("L3_驗證", "內容級對帳(唯讀)", "格子站名「reconcile 對帳」"),
    # ── L4 產出(給人看的那一層)──
    "VRN_ENG062_SummarizerV1":
        ("L4_產出", "摘要 v1", "docstring 首句 `VRN_ENG062_SummarizerV1`(無格子站)"),
    "VRN_ENG065_MailIntel":
        ("L4_產出", "郵件情報管線", "格子站名「郵件情報管線八檢(批143)」"),
    # ── L5 儲存(L90:正典=DuckDB;**底下兩支都是專用/派生庫,不動正典宣告**)──
    "VRN_ENG050_ContentStore":
        ("L5_儲存", "對帳綠燈內容落庫(**專用庫 via.duckdb,非正典**)", "格子站名「store 落庫(dry)」"),
    "VRN_ENG069_ConsensusDB":
        ("L5_儲存", "共識庫(**專用表,非正典**)", "格子站名「驗證共識庫八檢(批176)」"),
}


def _eng_families() -> set:
    """樹上活著的 VRN_ENG 家族(去版號)。退役/收容/產物夾不算。"""
    out = set()
    for p in (VIA / "functional modules" / "VRN").glob("VRN_ENG*.py"):
        s = str(p).replace("\\", "/")
        if any(k in s for k in ("__pycache__", "VIA_RetiredEngines", "references/intake", "SCOPE_COPY")):
            continue
        out.add(re.sub(r"_v\d{4}$", "", p.stem).split("_sha")[0])
    return out


def _book_families(book: dict) -> set:
    return {n.get("family", "") for v in book["layers"].values() for n in v["nodes"]}


def roster_gap(book: dict) -> list:
    """樹上有、冊上沒有、也不在 OFF_BOOK_PENDING 的家族=**沒有被交代的**。"""
    known = _book_families(book) | set(OFF_BOOK_PENDING)
    return sorted(f for f in _eng_families() if f.startswith("VRN_ENG") and f not in known)


BOOK = {
 "schema": "VIA.VRN.LogicArchitecture.SSOT.v1",
 "version": "v0101", "batch": "批641", "ts": "2026-09-20",
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
                            node(RULES, "SUP_MDL015_VISVRNBrokerAliasFullList_v*.py", "券商別名全表"),
                            node(VRN, "VRN_ENG084_FilenameTokenParse_v*.py", "檔名切分×三來源合流(批634 操作員規格)")]},
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
                              node(VRN, "VRN_ENG064_KnowledgeStack_v*.py", "知識堆疊(批611 零依賴簡→繁)"),
                              node(VRN, "VRN_ENG085_MarkdownRestore_v*.py", "本文還原(不刪除;類別/次類別/頁數;批636–640)"),
                              node(VRN, "VRN_ENG086_FirstPageLogicBridge_v*.py", "首頁邏輯橋"),
                              node(VRN, "VRN_ENG087_NLPTextSummaryBridge_v*.py", "NLP 文摘橋(072→MDL744→073 編排)")]},
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
 #: 批662:歸位的憑據逐支留著——操作員要推翻任何一支,看 evidence 那一行就夠。
 "placed_by_batch662": [{"family": f, "layer": lay, "role": role, "evidence": ev,
                         "placed_by": "批662",
                         "tail": (str(probe(VRN, f).relative_to(VIA)).replace("\\", "/")
                                  if probe(VRN, f) else ""),
                         "state": "PLACED" if probe(VRN, f) else "ABSENT"}
                        for f, (lay, role, ev) in sorted(OFF_BOOK_PLACED.items())],
 #: 批641:樹上有、架構冊上沒有的家族。**列出來 ≠ 該上架構冊**,裁定權在操作員(LL90)。
 "off_book_pending": [{"family": f, "state": "PENDING_OPERATOR",
                       "head": head1(probe(VRN, f) or Path("/nonexistent")),
                       "tail": (str(probe(VRN, f).relative_to(VIA)).replace("\\", "/") if probe(VRN, f) else ""),
                       "why": "樹上活著但未列入六層;是否上架構冊=架構裁定,待操作員"}
                      for f in OFF_BOOK_PENDING],
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

# ── 批662:把歸位的 15 支**真的放進那一層的 nodes**,不是另開一個 key 擺著看。
#   只另開 key 的話 `_book_families()` 照樣算不到它們,「待裁定 15」一個都不會少——
#   那就又是「宣告了沒接線」(批425 同族)。
for _f, (_lay, _role, _ev) in sorted(OFF_BOOK_PLACED.items()):
    _p = probe(VRN, _f)
    _node = ({"family": _f, "tail": str(_p.relative_to(VIA)).replace("\\", "/"),
              "head": head1(_p), "role": _role, "placed_by": "批662", "evidence": _ev}
             if _p else
             {"family": _f, "state": "ABSENT", "role": _role, "placed_by": "批662", "evidence": _ev,
              "why": "歸位表上有、樹上找不到尾版——誠實標空,不假裝它在"})
    BOOK["layers"][_lay]["nodes"].append(_node)

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

    ran = []

    def chk(name, cond, note=""):
        ran.append(name)
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
    _gap = roster_gap(BOOK)
    _tree, _onbook = _eng_families(), _book_families(BOOK)
    _vrn_tree = {f for f in _tree if f.startswith("VRN_ENG")}
    chk("⑧ 樹上每一個 VRN_ENG 家族都要被交代:在冊上,或在 OFF_BOOK_PENDING 裡掛 PENDING_OPERATOR"
        "(批641 實錄:ENG084/085/086/087 四支從頭到尾不在冊上,而**沒有任何一道檢會說**——"
        "手寫名冊只守得住寫上去的那些,沒寫上去的連「不在」都不會被提起 LL213 同型。"
        "本檢不要求全部上架構冊,只要求沒有一支安靜地不見)",
        not _gap and len(_vrn_tree) == len(_vrn_tree & (_onbook | set(OFF_BOOK_PENDING))),
        f"(樹 {len(_vrn_tree)} = 冊 {len(_vrn_tree & _onbook)} + 待裁定 {len(set(OFF_BOOK_PENDING) & _vrn_tree)}"
        f" · 沒被交代 {len(_gap)}{(': ' + ', '.join(_gap[:4])) if _gap else ''})")
    chk("⑨ 檢⑧ 咬得住:假裝有一支新引擎冒出來,它必須被點名",
        roster_gap({"layers": {"x": {"nodes": [{"family": f} for f in _onbook if f != "VRN_ENG085_MarkdownRestore"]}}})
        == ["VRN_ENG085_MarkdownRestore"] or "VRN_ENG085_MarkdownRestore" in roster_gap(
            {"layers": {"x": {"nodes": [{"family": f} for f in _onbook if f != "VRN_ENG085_MarkdownRestore"]}}}),
        "(拿掉 ENG085 → 被點名)")
    # ── 批662 ⑩⑪:15 支歸位(操作員令「把邏輯整理成功即可」)──
    _placed = BOOK["placed_by_batch662"]
    _by_layer = {}
    for x in _placed:
        _by_layer[x["layer"]] = _by_layer.get(x["layer"], 0) + 1
    _fams = _book_families(BOOK)
    chk("⑩ 批662 十五支歸位:每一支都真的進了那一層的 nodes(不是另開一個 key 擺著看——"
        "只擺著的話 _book_families 算不到,「待裁定 15」一個都不會少,那是宣告了沒接線)",
        len(_placed) == 15 and all(f in _fams for f in OFF_BOOK_PLACED)
        and OFF_BOOK_PENDING == [] and sum(_by_layer.values()) == 15
        and set(_by_layer) <= set(BOOK["layers"]),
        f"({' · '.join(f'{k} {v}' for k, v in sorted(_by_layer.items()))})")
    chk("⑪ 批662 憑據逐支留著,而且**不是我的直覺**:優先用格子站名(系統驗收它時的那一句),"
        "沒站的用 docstring 首句,兩種都寫明是哪一種;操作員要推翻任何一支,看 evidence 那一行就夠",
        all(x.get("evidence") for x in _placed)
        and sum(1 for x in _placed if "格子站名" in x["evidence"]) == 11
        and sum(1 for x in _placed if "docstring" in x["evidence"]) == 4
        and all(x.get("placed_by") == "批662" for x in _placed),
        f"(有站 {sum(1 for x in _placed if '格子站名' in x['evidence'])} 支 · "
        f"無站 {sum(1 for x in _placed if 'docstring' in x['evidence'])} 支)")
    print(f"  [計] {len(ran)} 檢 OK {len(ran) - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== VRN 邏輯架構索引冊 · 九檢自測(沙盒零網路)===")
        return selftest()
    if a and a[0] == "build":
        return do_build()
    return do_check()


if __name__ == "__main__":
    sys.exit(main())
