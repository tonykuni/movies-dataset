#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
v0110:操作員 2026-09-25 核准接手；ENG090 正式掛 L4_產出，讀 VDF 財報而不改擷取歸屬。
側線 2026-09-24 第十五段(續)(v0108→v0109;主線批號由併線的手指定 L25):**OFF_BOOK_PENDING +1 支 VRN_ENG090_FinStatementsTemplate**
  (交易所財報 VRN 模板頁:VDF_ENG082 交易所彙總財報 → 制式 U/I + SYNCHRONIZER 交接 + 上下自動燈號;LL334 由 089 讓號為 090)。
  它讀的是 VDF 的 `tw_financial_mops`,不是 VRN 研報六層鏈上的料,所以**不自己把它放上哪一層**——上不上架構冊、上哪一層
  (L4_產出?)是架構裁定(LL90),掛在待裁定清單(同批682 ENG088 的裁法;掉球 Z213)。沒掛的話守門 ⑧ 會把它當沒被交代的家族:
  v0107 / v0108 上實量是紅的(側線第十五段第一版漏跑這一站,併 main 時補量到)。其餘一字未動:六層、層名、節點、15 支歸位都不變;十七檢不變。
批735(v0107→v0108):**VRN 模板上架構冊**(操作員 2026-09-24「用制式模板html u/i套進去形成vrn模板都由synchonizer控制交接自適應式自動化」)。
  L4_產出 +1 節點 `functional modules/VRN/VRN_ENG089_TemplateView_v*.py`(VRN 模板:自測迴圈成果套進制式 U/I 三入口,模板零改動;
  synchronizer 模組只增不減、面板開關由 synchronizer 控制;上下游連結冊 NEW / CHANGED / GONE / SAME 對上一輪、新增項目必須上頁)。
  不上冊的話守門 ⑧「樹上每一個 VRN_ENG 家族都要被交代」會把它當沒被交代的家族(紅)。它的 --selftest 在六層鏈上跑:
  沒有 node / playwright 的機器上瀏覽器那一檢照實 SKIP。其餘一字未動:六層、層名、15 支歸位、待裁定清單都不變。
批728(v0106→v0107):**第二血統上架構冊**(操作員令「重整 VRN 實測修正到成功」;姊妹倉那一條線「在錯誤位置進行」的成果搬回母倉正位)。
  L3_驗證 +1 節點 `functional modules/VRN/engine/VRN_AutoTestLoop.py`(實檔自測迴圈 12 閘;姊妹倉 2026-09-23 在 106 份實檔上 FAIL 0 的那一套)。
  它的 `--selftest` 跑 VRN/tests 全部單元測試(首頁引擎 · 資料庫引擎 · 證據核心 · 名冊探針 · 迴圈)+ 合成語料小批,
  所以六層鏈(CGC_MDL172)敲這一個節點就等於把整條第二血統驗一遍——不必把沒有自測門的引擎一支支掛上來當 NODATA。
  其餘一字未動:六層、層名、15 支歸位、待裁定清單都不變;冊內容變了才重寫(v0106 冪等律照舊)。
批688(v0105→v0106):**建冊不再每跑一次就把追蹤檔弄髒**。
  工作站實錄:`via-vrnrun` 第一站 `via-vrnbook build` 之後,`git pull` 被擋——
      error: Your local changes to the following files would be overwritten by merge:
          supportive modules/registry/VIA_VRN_LogicArchitecture_SSOT_v0100.json
  根因是冊裡的 `built_at` 每次建都寫當下時間,內容一個指標都沒變,檔案卻永遠是髒的;
  而這本冊是「刻意入倉」的冊(再生物還原閘 MDL167 不還原它),於是每跑一次 VRN 就把下一次 pull 擋掉。
  v0106:建冊前先讀既有冊,**除 built_at 外內容相同就不重寫**,built_at 沿用上一次真正變動的時間;
  內容真的變了才寫(印「冊已變」與變在哪幾個頂層鍵)。do_build 可指定 book_path(自測進沙盒)。十七檢 +⑰。
批682(v0104→v0105):OFF_BOOK_PENDING +VRN_ENG088_SsotAdditiveBridge(側線稽核件原樣收進本線;上冊與否=操作員裁定);
  檢⑩ 的「OFF_BOOK_PENDING == []」改成不變量「歸位的 15 支不得同時掛待裁定」(LL332 會隨裁定改變的數字不可以當斷言)。其餘一字不動。
via_vrn_logic_book — VRN 邏輯架構索引正本 · 建冊器 + 守門員(批622;批641 v0101)

v0103→v0104(工作站實錄:一個「指標 35」沒辦法自己說出它是舊的)
  操作員在工作站打 `via-vrnbook`,印出來是:
      指標 35 · 在位且為尾版 35 · **過期 0** · [計] GREEN
  容器這邊同一支指令是 **50**,而且多一行 [已裁·留痕齊]。兩邊差 15,
  **而那盞燈在兩邊都是綠的** —— 因為守門只檢查「指標指得到尾版嗎」,
  它不檢查「這本冊本身是不是舊的」。舊冊上的 35 個指標,每一個都指得到,
  所以它誠實地回答了一個沒有人在問的問題。

  更糟的是冊自己記著 `version: v0101 · batch: 批641` —— **那是寫死的字面**,
  引擎都走到 v0103 了它還說自己是 v0101。冊不知道自己是誰建的。

  兩修:
  ① BOOK 的 version/batch/built_by 改成**從 __file__ 推導**,不再寫死。
     冊從此記得住「我是哪一支引擎建的」。
  ② 守門第一行就印身分:引擎尾版 · 冊由誰建 · 冊的 ts · 冊路徑。
     再加一盞 [冊版落後] 燈——引擎比冊新就明講,並給修法(`via-vrnbook build`)。
     **一個數字沒有年齡就會誤導**(LL304);這一次誤導的是「35 還是 50」。

v0102→v0103(批665 操作員授權「你決定 你覆核 你完成」:層名覆核)
  冊上自己掛著一條 PENDING_OPERATOR:「本冊的 L0-L5 是依既有引擎職責歸納的,
  **請操作員覆核層名與歸屬**」。批662 我又依那六層歸位了 15 支 ——
  一個暫定的框架用久了會變成事實上的正典,只是沒人裁過。操作員把覆核權交下來。

  **裁定:六層層名維持,層數維持。**
  改層名/改層數要把 50 個指標與 15 支歸位全部重做,而那換不到任何一個新的判斷力。
  我原本提出的兩個怪處,量過之後發現**錯的不是層名,是「一支引擎只能站一層」這個假設**:

  ① L2「結構與知識」裡混著加工站(ENG074 財報頁)與參考書(ENG063 詞庫)。
     不是層名錯,是節點少了一個欄位。補 role_kind:加工 / 參考 / 落庫。
  ② L5「儲存」底下三支全標「非正典」,正典儲存那一格看起來是空的。
     **它不是空的。** 量到:VRN_ENG073_ReportStructuredDB 自己建
     vrn_report_basic / vrn_report_analyst / vrn_report_metrics 三張表進
     vdf_tw_market.duckdb —— 那正是 L90 裁定的「正典 = vdf_tw_market.duckdb
     的 vrn_* 七張表」。承載者在,只是被歸在 L2(它同時做結構化與落庫,
     **它真的跨兩層**)。補 also_layers,L5 的空格當場被填上,憑據是可查的建表語句。

  兩個新欄位都是**只增不減**:既有的 layer/role/evidence 一個字不動,
  歸屬也沒有搬動任何一支。要推翻哪一支,看它的 also_layers_evidence 那一行就夠。

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
import json
import re
import sys
from datetime import datetime
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

# ═══ 批665:層名覆核的兩個正交欄位(只增不減;不搬任何一支的 layer)═══
# role_kind —— 同一層裡,「把料變成另一種料」和「被查的冊」是兩種東西。
#   L2 裡 ENG074 財報頁是加工站、ENG063 詞庫是參考書,壞掉的樣子完全不同:
#   加工站壞了會吐錯數字,參考書壞了是查不到。用同一盞燈看它們,兩邊都看不準。
ROLE_KIND = {
    "VRN_ENG063_Lexicon": ("參考", "詞庫:被查的冊,不產出新料"),
    "VRN_ENG064_KnowledgeStack": ("參考", "知識堆疊:被查的冊(批611 凍結對照表 2,784 筆)"),
    "VRN_ENG067_MindMapSSOT": ("參考", "三語關鍵字 SSOT x 分類:被查的冊"),
    "VRN_ENG066_NLPSupportHub": ("參考", "NLP 工具樞紐:被叫的工具面,不是管線站"),
    "VRN_ENG050_ContentStore": ("落庫", "對帳綠燈內容落庫(專用庫 via.duckdb,非正典)"),
    "VRN_ENG069_ConsensusDB": ("落庫", "共識庫(專用表,非正典)"),
    "VRN_ENG081_ParquetMainDB": ("落庫", "Parquet 派生車道(批615 正名:非正典)"),
}
_ROLE_DEFAULT = ("加工", "把料變成另一種料(預設)")

# also_layers —— 「一支引擎只能站一層」是**假設**不是事實。ENG073 同時做結構化與落庫。
#   憑據要可查:寫的是哪幾條建表語句、落進哪一本庫、對應哪一條律。
ALSO_LAYERS = {
    "VRN_ENG073_ReportStructuredDB": (
        ["L5_儲存"],
        "CREATE TABLE IF NOT EXISTS vrn_report_basic / vrn_report_analyst / vrn_report_metrics"
        " -> vdf_tw_market.duckdb;正是 L90 裁定的「正典 = vdf_tw_market.duckdb 的 vrn_* 七張表」。"
        "**L5 的正典儲存那一格不是空的,承載者被歸在 L2**(它真的跨兩層)"),
}

OFF_BOOK_PENDING = [           # 批662:15 支已歸位(見下);這裡只留**未來**樹上新冒出來、名冊上沒有的
    # 批682:側線 2026-09-21(claude/busy-bell-97sa4f)的 SSOT 增補審計橋原樣收進本線。它自己的規格項寫著
    #   「不在六層鏈上,是稽核件」——要不要上架構冊、上哪一層(L3 驗證?)是架構裁定,待操作員(LL90;LL305 提醒:掛著不等於交代完,
    #   下一批要有人讀)。掛在這裡的效果:守門/十六檢 ⑧ 不再把它當「沒被交代的家族」;冊上 off_book_pending 會帶它的抬頭與尾版。
    "VRN_ENG088_SsotAdditiveBridge",
    # 側線 2026-09-24 第十五段(續)(v0109):交易所財報 VRN 模板頁(讀 VDF_ENG082 的交易所彙總財報,不是研報六層鏈上的料)。
    #   上不上架構冊、上哪一層(L4_產出?)= 架構裁定,待操作員(LL90;掉球 Z213)。掛著的效果同上:守門 ⑧ 不再把它當沒被交代的家族。
]

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


_ME = Path(__file__).stem                      # via_vrn_logic_book_v0104
_ME_VER = "v" + _ME.rsplit("_v", 1)[-1]        # v0104

BOOK = {
 "schema": "VIA.VRN.LogicArchitecture.SSOT.v1",
 # 批666:版號/批次/建冊者不再寫死。寫死的版號會讓冊說自己是 v0101,
 #   而引擎早就 v0104——**冊不知道自己是誰建的**,於是一個「指標 35」
 #   沒辦法自己說出它是舊的。from_batch 留著原始出身,built_by 記當下。
 "version": _ME_VER,
 "built_by": _ME,
 "built_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
 "from_batch": "批641", "batch": "批666", "ts": "2026-09-20",
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
                        node(REG, "CGC_MDL141_ClosingGate_v*.py", "收尾閘(VRN 驗證收尾)"),
                        node(VRN / "engine", "VRN_AutoTestLoop*.py",
                             "實檔自測迴圈(第二血統總驗 12 閘;--selftest=VRN/tests 全部單元測試+合成小批;批728 自姊妹倉收回正位)")]},
  "L4_產出": {"why": "給人看的那一層",
              "nodes": [node(VRN, "VRN_ENG080_FourPointDigest_v*.py", "一題四點文摘"),
                        node(VRN, "VRN_ENG068_DailyBrief_v*.py", "每日簡報"),
                        node(VRN, "VRN_ENG079_ControlTowerDashboard_v*.py", "控制塔"),
                        node(VRN, "VRN_ENG089_TemplateView_v*.py",
                             "VRN 模板(自測成果套進制式 U/I;synchronizer 控制;上下游連結冊對上一輪 + 新增上頁檢查;批735)"),
                        node(VRN, "VRN_ENG090_FinStatementsTemplate_v*.py",
                             "交易所財報模板；上游 VDF_ENG082 唯讀；2026-09-25 操作員核准接手，歸 L4 產出(Z213)")]},
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
  {"item": "L0-L5 六層的層名(本冊第一次寫下來的那六個名字)",
   "state": "REVIEWED_B665",
   "why": "操作員批665 授權「你決定 你覆核 你完成」。**裁定:六層層名與層數維持。**"
          "改名/改層數要重做 50 個指標與 15 支歸位,換不到任何一個新的判斷力。"
          "原本提的兩個怪處,量過之後錯的不是層名,是『一支引擎只能站一層』這個假設:"
          "① L2 混著加工站與參考書 -> 補 role_kind(加工/參考/落庫),不動層;"
          "② L5 正典儲存看起來是空的 -> **不是空的**,ENG073 建 vrn_report_basic/"
          "analyst/metrics 進 vdf_tw_market.duckdb,正是 L90 的正典七表;它跨 L2+L5,"
          "補 also_layers。兩個欄位都只增不減,沒有搬動任何一支的歸屬。"
          "要推翻哪一支,看它的 role_kind_why / also_layers_evidence 那一行就夠",
   "ruled_by": "AI 代裁(批665 操作員授權)"},
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

# ── 批665:兩個正交欄位落到每一個節點(只增不減;不搬任何一支的 layer)──
#   role_kind 給**全部**節點(預設「加工」),不是只給名單上那幾支:
#   只標特例的話,沒標到的那些看起來像「還沒判」,而它們其實判完了(是加工)。
_b665 = {"role_kind": 0, "also_layers": 0, "layers_touched": set()}
for _lname, _lv in BOOK["layers"].items():
    for _n in _lv.get("nodes", []):
        _fam = str(_n.get("family") or "")
        _kind, _why = ROLE_KIND.get(_fam, _ROLE_DEFAULT)
        _n["role_kind"] = _kind
        _n["role_kind_why"] = _why
        _b665["role_kind"] += 1
        _al = ALSO_LAYERS.get(_fam)
        if _al:
            _n["also_layers"] = list(_al[0])
            _n["also_layers_evidence"] = _al[1]
            _b665["also_layers"] += 1
            _b665["layers_touched"].update(_al[0])
BOOK["layer_review_b665"] = {
    "ruled_by": "AI 代裁(批665 操作員授權「你決定 你覆核 你完成」)",
    "verdict": "六層層名維持,層數維持;不搬動任何一支的歸屬",
    "why": ("改層名/改層數要重做 50 個指標與 15 支歸位,換不到任何一個新的判斷力。"
            "原本提的兩個怪處,量過之後錯的不是層名,是『一支引擎只能站一層』這個假設"),
    "added_fields": ["role_kind", "role_kind_why", "also_layers", "also_layers_evidence"],
    "role_kind_tagged": _b665["role_kind"],
    "also_layers_tagged": _b665["also_layers"],
    "canonical_store_holder": sorted(ALSO_LAYERS),
    "note": ("L5『儲存』的正典那一格**不是空的**:ENG073 建 vrn_report_basic/analyst/metrics"
             " 進 vdf_tw_market.duckdb,正是 L90 的正典七表。它跨 L2+L5。"),
}

BOOK_PATH = REG / "VIA_VRN_LogicArchitecture_SSOT_v0100.json"


def _book_same(old: dict, new: dict) -> tuple:
    """批688:除 built_at 外是否相同;回 (同?, 變動的頂層鍵)。"""
    a = {k: v for k, v in (old or {}).items() if k != "built_at"}
    b = {k: v for k, v in (new or {}).items() if k != "built_at"}
    changed = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
    return (not changed), changed


def do_build(book_path=None) -> int:
    if missing:
        print("[FAIL] 指標解析不到,整本不寫(半本冊比沒有冊危險):", "; ".join(missing))
        return 1
    bp = book_path or BOOK_PATH
    n = sum(len(v["nodes"]) for v in BOOK["layers"].values())
    tail = (f"層 {len(BOOK['layers'])} · 引擎指標 {n} · 規則正本 {len(BOOK['rule_canons'])} · "
            f"今日裁定 {len(BOOK['rulings_today'])} · 待裁定 {len(BOOK['known_gaps'])}")
    old = None
    if bp.is_file():
        try:
            old = json.loads(bp.read_text(encoding="utf-8"))
        except Exception:
            old = None
    if old is not None:
        same, changed = _book_same(old, BOOK)
        if same:
            # 批688:內容沒變就不重寫——built_at 沿用上一次真正變動的時間,追蹤檔不弄髒,git pull 不被擋
            print(f"[build] {bp.name} 冊未變(built_at 沿用 {old.get('built_at')};不重寫)· {tail}")
            return 0
        print(f"[build] {bp.name} 冊已變:{', '.join(changed[:6])}{'…' if len(changed) > 6 else ''}")
    bp.write_text(json.dumps(BOOK, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[build] {bp.name} · {tail}")
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
    # 批665:「被動過」原本一律報紅,因為那個年代 AI 不該裁。操作員把覆核權交下來之後,
    #   冊上會有已裁的條目 —— 已裁**帶署名與憑據**是合法的;已裁**沒留痕**才是紅。
    #   分成兩堆講,不然一個「被動過 1」會把「裁得清清楚楚」和「偷偷改掉」講成同一件事。
    _g = book.get("known_gaps") or []
    ruled_ok = [g["item"] for g in _g if g.get("state") != "PENDING_OPERATOR"
                and str(g.get("ruled_by", "")).strip()
                and len(str(g.get("why", "")).strip()) > 30]
    ruled = [g["item"] for g in _g if g.get("state") != "PENDING_OPERATOR"
             and g["item"] not in ruled_ok]
    # 批666:第一行先講**身分**。工作站印「指標 35」、容器印「指標 50」,兩邊都是綠的——
    #   因為守門只問「指標指得到尾版嗎」,不問「這本冊本身是不是舊的」。
    #   舊冊上的 35 個指標每一個都指得到,所以它誠實地回答了一個沒人在問的問題。
    _bver = str(book.get("built_by") or book.get("version") or "(冊沒記建冊者)")
    _bat = str(book.get("built_at") or book.get("ts") or "?")
    print(f"=== VRN 邏輯架構索引冊 · 守門 ===")
    print(f"  引擎 {_ME}  ·  冊由 {_bver} 建於 {_bat}  ·  {BOOK_PATH.name}")
    print(f"  指標 {ok + len(gone) + len(stale)} · 在位且為尾版 {ok} · **過期 {len(stale)}** · 不在 {len(gone)}")
    # 冊版落後:引擎比冊新 = 這本冊是**上一代引擎**建的,上面的數字回答的是上一代的問題。
    #   這是**紅**不是提醒:綠燈配一本舊冊,就是一盞查不出問題的綠燈。
    stale_book = (_bver != _ME) and _bver.startswith("via_vrn_logic_book_v")
    if stale_book:
        # 兩個方向都要報:冊比引擎舊(沒重建)、冊比引擎新(樹落後沒拉)。
        #   只認一個方向的話,另一個方向會安靜地給出一盞綠燈。
        _dir = "冊比引擎舊(沒重建)" if _bver < _ME else "**冊比引擎新——你的樹落後了**"
        print(f"  [冊版不同步] {_dir}:引擎 {_ME} · 冊由 {_bver} 建"
              f"\n        —— 上面那些數字回答的是另一代的問題。"
              f"\n        修法:冊舊 → `via-vrnbook build`;樹舊 → `git pull` 再 `via-reload`。"
              f"\n        工作站實錄(批666):同一句 via-vrnbook 兩邊印「指標 35」與「指標 50」,"
              f"**兩邊都是綠的** —— 差的是冊不是樹,而守門當時看不出來")
    elif not str(book.get("built_by") or "").strip():
        print(f"  [冊沒記建冊者] 這本冊是舊格式(批666 之前),重建一次就會記住自己是誰建的:"
              f"`via-vrnbook build`")
    for x in stale:
        print(f"  [過期] {x}")
    for x in gone:
        print(f"  [不在] {x}")
    if lost:
        print(f"  [落地處不見] {len(lost)}:" + "; ".join(lost[:5]))
    if ruled_ok:
        print(f"  [已裁·留痕齊] {len(ruled_ok)}:" + "; ".join(x[:24] for x in ruled_ok[:3])
              + "  ← 署名與憑據都在,要推翻看 why 那一行")
    if ruled:
        print(f"  [待裁定被動過·沒留痕] {len(ruled)}:" + "; ".join(ruled[:3])
              + "  ← 裁了就要署名(ruled_by)並寫憑據(why);默默改掉才是紅")
    bad = len(stale) + len(gone) + len(lost) + len(ruled) + (1 if stale_book else 0)
    print(f"  [計] {'GREEN' if not bad else 'RED'}"
          + ("" if not bad else " · 修法:`via-vrnbook build` 重建索引冊(它是產物,不是手寫件)"))
    return 0 if not bad else 1


def _b665_checks(book: dict, chk) -> None:
    """批665 三檢:覆核裁定要落得到冊上,不是只寫在版史裡。"""
    lr = book.get("layer_review_b665") or {}
    nodes = [n for lv in book.get("layers", {}).values() for n in lv.get("nodes", [])]
    # ⑫ 裁定在冊上、六層沒被改名也沒被改數(裁的是「維持」,就要驗得出真的維持了)
    chk("⑫ 批665 層名覆核落冊:六層維持且裁定有署名",
        len(book.get("layers", {})) == 6 and "六層層名維持" in str(lr.get("verdict"))
        and "授權" in str(lr.get("ruled_by")),
        f"(層 {len(book.get('layers', {}))} · 裁定 {str(lr.get('verdict'))[:16]})")
    # ⑬ role_kind 給全部節點不是只給特例——只標特例,沒標到的看起來像還沒判
    untagged = [n.get("family") for n in nodes if not n.get("role_kind")]
    kinds = {n.get("role_kind") for n in nodes}
    chk("⑬ role_kind 逐節點都有(不是只標特例)",
        not untagged and kinds <= {"加工", "參考", "落庫"} and len(kinds) >= 2,
        f"(節點 {len(nodes)} · 未標 {len(untagged)} · 種類 {sorted(kinds)})")
    # ⑭ L5 正典那一格真的被填上了,而且憑據是可查的建表語句不是我的直覺
    holder = [n for n in nodes if "L5_儲存" in (n.get("also_layers") or [])]
    ev = " ".join(str(n.get("also_layers_evidence") or "") for n in holder)
    chk("⑭ L5 正典儲存有承載者,憑據是建表語句",
        len(holder) >= 1 and "vrn_report_basic" in ev and "vdf_tw_market.duckdb" in ev
        and "L90" in ev,
        f"(承載者 {[n.get('family') for n in holder]})")


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
    # 批665:這一檢原本寫死「一律 PENDING_OPERATOR」——那是**裁定權沒轉手**時代的規則。
    #   操作員把覆核權交下來之後,冊上就會有已裁的條目,舊檢會把它判成違規。
    #   但規矩的**精神**不是「AI 不准裁」,是「AI 不准**默默**裁」。所以改成:
    #     要嘛還掛著 PENDING_OPERATOR,要嘛已裁但**帶得出署名與憑據**。
    #   新檢比舊檢嚴:舊檢分不出「裁了沒署名」和「裁了有署名」,它把兩者一起擋掉;
    #   新檢真的去看有沒有留痕(LL90 的精神:裁定權轉手了,留痕的義務沒有轉手)。
    _gaps = BOOK["known_gaps"]
    _bad_gap = [g["item"][:20] for g in _gaps
                if g["state"] != "PENDING_OPERATOR"
                and not (str(g.get("ruled_by", "")).strip() and len(str(g.get("why", "")).strip()) > 30)]
    chk("⑤ 待裁定要嘛掛 PENDING_OPERATOR,要嘛已裁但署名+憑據齊(LL90:裁定權轉手,留痕義務沒有)",
        bool(_gaps) and not _bad_gap,
        f"(共 {len(_gaps)} 條 · 待裁 "
        f"{sum(1 for g in _gaps if g['state'] == 'PENDING_OPERATOR')} · 已裁 "
        f"{sum(1 for g in _gaps if g['state'] != 'PENDING_OPERATOR')} · 無痕 {_bad_gap})")
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
        and not (set(OFF_BOOK_PLACED) & set(OFF_BOOK_PENDING)) and sum(_by_layer.values()) == 15   # 批682:原本釘 OFF_BOOK_PENDING == [] 是把當下數字當斷言(LL332);
        #   docstring 自己說這張表「只留未來樹上新冒出來的」,所以要求它永遠空=要求未來永遠不准有新引擎。改成不變量:歸位的 15 支不得同時掛待裁定。
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
    _b665_checks(BOOK, chk)
    # ⑮ 冊記得住自己是誰建的(批666:寫死的版號讓冊說自己是 v0101,引擎早就 v0104)
    chk("⑮ 冊自述身分:built_by/built_at 由 __file__ 推導,不寫死",
        BOOK.get("built_by") == _ME and BOOK.get("version") == _ME_VER
        and len(str(BOOK.get("built_at") or "")) >= 10
        and BOOK.get("from_batch") == "批641",
        f"(built_by={BOOK.get('built_by')} · built_at={BOOK.get('built_at')})")
    # ⑯ 冊版落後要報紅不是提醒——綠燈配一本舊冊,是一盞查不出問題的綠燈
    with tempfile.TemporaryDirectory() as td:
        sb2 = Path(td) / "old.json"
        old_book = json.loads(json.dumps(BOOK))
        old_book["built_by"] = "via_vrn_logic_book_v0101"
        sb2.write_text(json.dumps(old_book, ensure_ascii=False), encoding="utf-8")
        import io
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc_old = do_check(sb2)
        out = buf.getvalue()
        chk("⑯ 冊版不同步判紅並給修法(兩個方向都要報)",
            rc_old != 0 and "冊版不同步" in out and "via-vrnbook build" in out
            and "git pull" in out,
            f"(rc={rc_old})")
    # ⑰ 批688:建冊冪等——內容沒變不重寫(built_at 沿用),內容變了才寫;追蹤檔不再每跑一次就髒
    with tempfile.TemporaryDirectory() as td:
        import io as _io688, contextlib as _cl688
        sb3 = Path(td) / "book.json"
        _b1 = _io688.StringIO()
        with _cl688.redirect_stdout(_b1):
            rc_b1 = do_build(sb3)
        bytes1 = sb3.read_bytes()
        _b2 = _io688.StringIO()
        with _cl688.redirect_stdout(_b2):
            rc_b2 = do_build(sb3)
        bytes2 = sb3.read_bytes()
        _old = json.loads(bytes2.decode("utf-8"))
        _old["known_gaps"] = list(_old.get("known_gaps") or []) + [{"fixture": "批688"}]
        sb3.write_text(json.dumps(_old, ensure_ascii=False, indent=1), encoding="utf-8")
        _b3 = _io688.StringIO()
        with _cl688.redirect_stdout(_b3):
            rc_b3 = do_build(sb3)
        _new = json.loads(sb3.read_text(encoding="utf-8"))
        chk("⑰ 建冊冪等:第二次 build 位元相同且印「冊未變」;內容變了(known_gaps 多一筆)才重寫並印「冊已變:known_gaps」",
            rc_b1 == 0 and rc_b2 == 0 and rc_b3 == 0 and bytes1 == bytes2
            and "冊未變" in _b2.getvalue() and "冊已變" in _b3.getvalue() and "known_gaps" in _b3.getvalue()
            and not any(isinstance(g, dict) and g.get("fixture") == "批688" for g in _new.get("known_gaps") or []),
            f"(第二次 {'同' if bytes1 == bytes2 else '異'} · 第三次 {'重寫' if '冊已變' in _b3.getvalue() else '沒寫'})")
    print(f"  [計] {len(ran)} 檢 OK {len(ran) - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== VRN 邏輯架構索引冊 · 十七檢自測(沙盒零網路)===")
        return selftest()
    if a and a[0] == "build":
        return do_build()
    return do_check()


if __name__ == "__main__":
    sys.exit(main())
