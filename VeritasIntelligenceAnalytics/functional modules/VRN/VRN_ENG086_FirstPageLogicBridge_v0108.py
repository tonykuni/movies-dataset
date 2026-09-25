#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
v0107→v0108(批546 **更正**:收容件根本沒被改過,是 CRLF;批544/545 的診斷我錯了兩次)

  操作員照批545 印的診斷列了夾內檔案,結果只有一個檔:

      VIA_VRN_FirstPageEngine_2.py      30727 B   7BEDF1D6

  沒有多餘檔。那我批545 說的「夾裡多一個排在後面的入侵者」也不成立。
  把倉庫那份(LF · 30,115B · d4cdaedf)逐位元轉成 CRLF 再算一次:

      30,727 B · md5 7bedf1d680a5e65e223ed0f914350cb4      ← 位元數與 md5 都完全吻合

  **收容件一個位元都沒被改。**是 git 在 Windows 上依 core.autocrlf 把 LF 轉成 CRLF,
  612 正是這個檔的**行數**,每行多一個 \r。我從批544 起一路斷言「正本被就地改過」、
  還指名是 ACCEL-BRIDGE 注入——那是**我造的判錯紅燈**,而且我讓它上了台帳、教訓與交接檔。

  更難看的是:倉庫的 .gitattributes 裡早就寫著同一個教訓——
      # VTR subsystem: manifest hashes raw bytes - checkout must be byte-exact (no CRLF conversion)
  VTR 與 v0160A 因為「冊比對原始位元」都鎖過位元,我做收容件位元錨時沒去看,也沒鎖。

  v0108 修兩層:
    ① 比對改成**行尾無關**:raw 不符但 LF 正規化後相符 → 判「行尾(CRLF)」照樣過,並講明原因;
       真的內容不同才是 RED。位元錨的本意是抓「內容被換掉」,不是抓平台換行。
    ② 位元鎖寫進 .gitattributes(`references/intake/** -text`),讓它以後不再發生。
v0106→v0107(批545:救法沒救到——因為紅燈點名的是**資料夾**,不是那個檔)

  操作員照 v0106 印的救法跑了 `git checkout -- "…/VIA_VRN_FirstPageEngine_2.py"`,沒有報錯,
  再跑一次 via-ryg,md5 還是 7bedf1d6。原因是我選檔的方式本身有洞:

      ENGINE_GLOB = "VIA_VRN_FirstPageEngine*.py"
      intake_engine_file() = sorted(home.glob(ENGINE_GLOB))[-1]     ← **排最後的那個**

  收容件夾裡只要多一個排在 `_2.py` 後面的同名系列檔(`_3.py`、`_v0101.py`…),
  它就自動變成「正典」——而那種檔是**未追蹤**的,git checkout 動不到它,所以救法救不回來。
  30,727B 那一份很可能就是這樣進來的(操作員今天上傳過四次同名檔)。

  這是 LL93 的同一種錯,只是這次是我犯在選檔上:我量的是「排序最後的那個」,
  而該量的是「**冊上點名的那一個**」。位元錨本來就寫著 name=VIA_VRN_FirstPageEngine_2.py,
  卻沒有拿它去取檔——錨只用來比對,沒用來**定位**。

  v0107 三件:
    ① 錨檔一律**按名字取**(home / INTAKE_ANCHOR["name"]),不再吃 glob 排序;
    ② 收容件夾裡**每一個** `VIA_VRN_FirstPageEngine*.py` 都列出來(檔名 · 位元 · md5),
       多出來的那一個當場現形,不必再猜;
    ③ 救法分兩種講清楚:錨檔被改過 → git checkout;**夾裡多了不在冊上的檔** → 那是入侵者,
       git checkout 救不了(它未追蹤),要你自己挪走。本支一樣不代改、不代刪任何檔。
v0105→v0106(批544:⑱ 在工作站上**咬到真東西了**,那就要告訴人怎麼救)

  批541 加 ⑱ 的時候,本境三方一致、永遠是綠的;那時候它看起來像一檢沒用的東西。
  批543 操作員在工作站跑 via-ryg,⑱ 第一次真跑就亮紅:

      收容件 md5 7bedf1d6 ≠ 錨 d4cdaedf · 檔案 30,727B(錨是 30,115B)· 冊 =錨 · 模組 11/11

  讀法:**冊沒被動,檔被動了**,而且多了 612 位元組。倉庫裡那份是乾淨的(d4cdaedf),
  所以是工作站那一份被就地改過——最可能是某次全樹補橋把 [VIA:ACCEL-BRIDGE](約 629B)
  注進了收容件。那正是 LL72 記過的同一種事故,只是這次落在 VRN 的收容件上。
  (也解釋了為什麼同一份 30,115B 的原檔被上傳了四次——那是在試圖把它救回來。)

  v0106 只改一件事:**紅燈要能自救**。①/⑱ 失敗時直接把還原指令印出來,
  不要只丟兩串 md5 讓人自己猜。本支不代改任何檔——還原是操作員的手(不代設)。
v0104→v0105(批541 操作員令「加這個檢查導入」——同一份收容件已經第四次被上傳)

  操作員今天又把 `VIA_VRN_FirstPageEngine.py` 丟了兩份進來(30,115 bytes,兩份 md5 完全一樣,
  而且跟 9/9、9/15 上傳的那兩份也一樣:d4cdaedf…)。量過:它**早就在收容件裡**,
  位元一個不差,自測 ① 每次都綠。那為什麼還要加一檢?

  因為 ① 那一檢其實比它看起來弱:它拿**檔案的 md5** 去對**同一個資料夾裡的冊**。
  檔案跟冊一起被換掉,兩邊還是一致——綠燈照亮,騙的是自己(跟 LL74 先建後斷言同一種形狀)。
  而且它只驗位元,不驗「導入」這件事本身:檔案在、位元對,但 import 就炸、或宣告的模組被改名,
  ① 一樣是綠的。**「有這個檔」跟「這個檔導得進來、東西都在」是兩件事。**

  v0105 補的 ⑱ 三段都要過才算導入成立:
    ① 位元錨 —— 期望 md5/sha256/bytes **寫死在程式碼裡**(INTAKE_ANCHOR),檔案、冊、錨三方一致。
       冊被改寫也騙不過,因為錨不在那個資料夾裡。
    ② 真的 import 得起來 —— 不是「檔案存在」,是 exec_module 真的跑完。
    ③ 冊上宣告的 11 個模組一個不少 —— SSOT loader(load_ssot_blocks)+ 10 個類別,
       少一個就是導入殘缺,不是「差不多有」。

v0103→v0104(批541 去衝突:同一家不得有兩個正典名)
  合併三張券商表(收容件字典 × SSOT 正本 × 橋側補冊)後還剩兩個**活衝突**——同一個別名對到兩個正典名,
  下游一 join 就散:
    · `clst` → CLSA / CLST。操作員裁定 **CLSA = CLST 是同一家**(里昂),冊上原本分成兩筆;
      已把 CLST 併入 CLSA(SSOT 20→19 家;CLST 原文保留在 merged_b541 鍵下,只增不減)。
    · `jp / jpm / jpmorgan / j.p. morgan` → J.P.MORGAN(SSOT)/ JPMORGAN(補冊)。
      舊讓位規則有個洞:只 pop「不在 SSOT **且不在補冊**」的鍵,而 JPMORGAN 兩邊都有,於是永遠 pop 不掉。
  v0104:① 讓位規則改成「只要別名被 SSOT 收編,非 SSOT 的鍵一律讓位」,不看它在不在補冊
  ② 新增 `broker_conflicts()` 與自測 ⑯',斷言合併後**零撞名**——鎖上了,同一家兩個正典名就再也回不來。
v0102→v0103(批540 整合去重時自己打出來的潛伏假評等)
  `safe_rating` 的「獨立短行」分支寫著**「≤8 字剛好是別名」**,實作卻是用 `canon_of()` 做**包含**比對。
  差別在:「外資持有比重上升」剛好 8 字、裡面有「持有」→ 被判成 HOLD。那是外資持股比重,不是評等。
  64 份真研報裡目前沒咬到(三個走這條路的都是 `買進`/`Buy` 自成一行的真評等),所以這是**潛伏**的假綠,
  不是已發生的錯——但規則說「剛好是」就該是「剛好是」,說到做到。
  v0103:該分支改成**整行等於別名**(去尾標點後全等);線索詞分支維持包含比對(那裡包含才對)。
  這一改只會拿掉假命中,不會少掉真命中——64 份實測評等維持 36。
VRN_ENG086_FirstPageLogicBridge v0102 — 第一頁邏輯補缺正主橋(批537:券商證據分級 + 目標價/日期誠實四態)

v0101→v0102(批537,全是實測打出來的):
  ① **電郵網域不是文內證據**:Daiwa 三份被判成 CATHAY,唯一的「cathay」出現在分析師信箱 `…@daiwacm-cathay.com.tw`(大和國泰合資體的網域)。
     券商判定改**證據分級**:文內(去電郵/網址後)> 檔名 > 電郵網域(弱)。每列帶 `broker_how`,假綠自此看得見。
  ② **目標價誠實四態**:命中 / 報告自述 n.a.(Daiwa「Target price: n.a.」)/ 修復文字裡根本沒有目標價欄(GS、MQ 的側欄沒被修復出來)/ 有線索卻抓不到(=真 RED)。
     舊版把後三種混成一個「30/64」,像是抓漏 34 份——那是**判錯的紅燈**,和假綠一樣傷。
  ③ **檔名日期誠實三態**:命中 / 檔名本來就沒有日期(研討會講義、`6933_AMAX-KY_個股介紹報告.pdf`)/ 有六碼以上數字卻解不出(=真 RED)。

VRN_ENG086_FirstPageLogicBridge v0101 — 第一頁邏輯補缺正主橋(批536:+corpus 真報告語料實測)

v0100→v0101:+`corpus` 動詞——直接吃收容件 AttachmentFixedOutput(操作員 C:\測試樣本報告 那 64 份研報的**修復文字**,
  01_repair/documents/NNN_<原檔名>.pdf.txt;收容件零觸碰唯讀)→ 逐檔跑檔名階梯 + 券商/評等/目標價/互核 →
  VIA_Reports/first_page_logic/CORPUS_latest.json + .md(append-only)。這是**內容級**實測:原 PDF 不在本境,
  但文字是同一批檔的修復輸出,誠實標明來源。

VRN_ENG086_FirstPageLogicBridge v0100 — 第一頁邏輯補缺正主橋(批522 操作員上傳 VIA_VRN_FirstPageEngine v0101 ALL-IN-ONE;「附件看能否修第一頁邏輯缺失部分」)

收容件:functional modules/VRN/references/intake/VIA_VRN_FirstPageEngine_v0101_b522/VIA_VRN_FirstPageEngine_2.py(零觸碰;md5 冊 _INTAKE_MANIFEST_b522.json)
本橋(正主;Zero-Hydra 一功能一主):
  ① 以 importlib 載入收容件,拿它的 TickerFilename(檔名→代碼階梯:FILE_SUFFIX→FILE_BARE→SECTOR→TITLE_SUFFIX→TITLE_SYNONYM→BODY_SUFFIX→年段回收→BODY_BARE)、
     FieldValidation(email/電話/目標價)、CrossValidation(檔名×首頁四欄互核、資訊區/本文區在不在)、FinancialValidation(加減/乘除/YoY 容差帶);
  ② 名冊不再靠收容件的 SSOT 區塊(VIA 正典 SSOT 無 _RAW_REGEX/_RAW_SYNONYMS)→ 自 VDF 庫 tw_listings(code/name;唯讀;庫解析律 LL27/LL30)灌 official_set + 名→碼;
  ③ 橋側防呆(收容件已知毛病,不改它):券商別名短拉丁字(gs/ms/mq)須大寫獨立詞、一般拉丁詞要詞界、泛用英文字(capital/president)要跟 securities/invest;
     評等要線索詞(評等/建議/Rating)或獨立短行,buy 不撞 buyback、hold 不撞 holdings、add 不單獨算;目標價先認「目標價/TP/Target Price」線索,再退收容件 NT$ 正則;
     台灣本土券商補冊(兆豐/國泰/永豐/玉山/元富/華南/日盛/康和/宏遠/台新/第一金/合庫/新光/國票/亞東/大昌/福邦/德信;外資 匯豐/法巴/瑞信/巴克萊/Jefferies/海通/中金/瑞穗/日興);
     民國 7 碼日期(1140822)補認;
  ④ enrich:讀 ENG072 的 sidecar(VIA_Reports/first_page_text/<stem>.json;header/right/body/footer)→ 每件寫 VIA_Reports/first_page_logic/<stem>.logic86.json
     (append-only;ENG072 正本與其 sidecar 零觸碰;律 L46)+ LOGIC86_latest.json 摘要(代碼法分布/檔名×首頁一致率/券商/評等/目標價命中率);
  ⑤ bench:拿 functional modules/VRN/StockReportBasicInfo.json(76 份真檔名,57 份有 Ticker/Broker/ReportDate 正解)量檔名階梯命中率,漏的逐件印(小數量實測);
  ⑥ gap:收容件八模組對 VRN 現況的補缺表(已接線/未接線誠實:版面字級階層與隱藏格線表格重建要 chars 幾何,本批不接)。
誠實四態:收容件缺=ABSENT;sidecar 零件=NODATA;名冊庫缺=名冊 ABSENT 仍可跑(命中率打折並標明)。零網路。
用法:python3 VRN_ENG086_FirstPageLogicBridge_v0104.py [status|gap|bench [--limit N]|corpus [--limit N]|enrich [--in DIR] [--out DIR] [--limit N]] | --selftest
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


import datetime as _dt
import hashlib
import importlib.util
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
INTAKE_ROOT = HERE / "references" / "intake"
INTAKE_GLOB = "VIA_VRN_FirstPageEngine_v*_b*"
ENGINE_GLOB = "VIA_VRN_FirstPageEngine*.py"
FP_OUT = VIA / "VIA_Reports" / "first_page_text"       # ENG072 sidecar(只讀)
OUT = VIA / "VIA_Reports" / "first_page_logic"         # 本橋產物(append-only)
BASICINFO = HERE / "StockReportBasicInfo.json"
OLD_DB = VIA / "functional modules" / "VDF" / "output_hub" / "mega" / "vdf_tw_market.duckdb"

EXTRA_BROKER = {
    "MEGA": ["兆豐", "mega securities", "mega sec"], "CATHAY": ["國泰證期", "國泰證券", "國泰投顧", "cathay securities", "cathay sec"],
    "SINOPAC": ["永豐", "sinopac"], "ESUN": ["玉山", "e.sun", "esun"], "MASTERLINK": ["元富", "masterlink"],
    "HUANAN": ["華南永昌", "華南", "hua nan"], "JIHSUN": ["日盛", "jih sun", "jihsun"], "CONCORD": ["康和", "concord securities"],
    "HONGYUAN": ["宏遠", "hong yuan"], "TAISHIN": ["台新", "taishin"], "FIRSTSEC": ["第一金", "first securities"],
    "TCB": ["合庫", "合作金庫"], "SKS": ["新光", "shin kong"], "IBF": ["國票", "ibf securities"], "ORIENTAL": ["亞東", "oriental securities"],
    "DACHANG": ["大昌", "ta chang"], "FUBANG": ["福邦"], "TACHING": ["德信"],
    "HSBC": ["匯豐", "hsbc"], "BNP": ["法巴", "bnp paribas", "bnp"], "CREDITSUISSE": ["瑞信", "credit suisse"], "BARCLAYS": ["巴克萊", "barclays"],
    "JEFFERIES": ["jefferies"], "HAITONG": ["海通", "haitong"], "CICC": ["中金", "cicc"], "MIZUHO": ["瑞穗", "mizuho"], "NIKKO": ["日興", "smbc nikko", "nikko"],
    "BERNSTEIN": ["bernstein"], "JPMORGAN": ["jp", "小摩"], "MORGANSTANLEY": ["大摩"], "CLSA": ["clst", "clsa", "里昂"], "GF": ["gf securities", "廣發"], "KGI": ["凱基投顧", "凱基證券"], "CAPITAL": ["群益投顧", "群益證券"], "PRESIDENT": ["統一投顧", "統一證券"], "CTBC": ["中信投顧", "中信證券"],
}
GENERIC_LATIN = {"capital", "president", "first", "oriental", "concord", "mega", "add"}     # 泛用英文字:要跟 securities/invest 才算券商
_RATING_CUE = re.compile(  # 批536:線索詞與評等之間容得下「調降至/調升至/維持/由X至」
    r"(投資評等|評等|評級|建議|Rating|Recommendation|Rec\.)[^\n]{0,8}?[:：]?\s*"
    r"(強力買進|買進|加碼|逢低|中立|持有|區間|賣出|減碼|Strong Buy|Buy|Outperform|Overweight|Accumulate|Add|Neutral|Hold|Market Perform|Equal-?weight|Sell|Underperform|Underweight|Reduce)", re.I)
_TP_CUES = (re.compile(r"目標價[^\d]{0,14}?(\d[\d,]*\.?\d*)"),
            re.compile(r"(?<![A-Za-z])(?:(?i:target\s*price|price\s*target)|TP|PT)(?![A-Za-z])\s*[:：]?\s*(?:\(?NT\$?\)?|NTD|TWD)?\s*\$?\s*(\d[\d,]*\.?\d*)"))


# ---------------------------------------------------------------- 收容件
def intake_home() -> Path | None:
    hits = sorted(p for p in INTAKE_ROOT.glob(INTAKE_GLOB) if p.is_dir())
    return hits[-1] if hits else None


def _eol_pair(b: bytes) -> tuple:
    """批546:回 (原始 md5, LF 正規化後 md5)。位元錨要抓的是「內容被換掉」,
    不是「git 在 Windows 上把 LF 換成 CRLF」——後者是平台行為,不是汙染。"""
    lf = b.replace(b"\r\n", b"\n")
    return hashlib.md5(b).hexdigest(), hashlib.md5(lf).hexdigest()


def eol_verdict(b: bytes, want_md5: str, want_bytes: int | None = None) -> tuple:
    """回 (ok, 說法)。三態:位元一致 / 只差行尾(照樣算對) / 內容真的不同(RED)。"""
    raw, lf = _eol_pair(b)
    if raw == want_md5:
        return True, f"md5 {raw[:8]}=錨 · {len(b)}B"
    if lf == want_md5 or (want_bytes and len(b.replace(b"\r\n", b"\n")) == want_bytes and lf == want_md5):
        return True, (f"md5 {raw[:8]}≠錨,但**只差行尾**(CRLF;LF 正規化後 {lf[:8]}=錨)"
                      f" · {len(b)}B vs 錨 {want_bytes}B —— 內容一位元沒變,是 core.autocrlf 幹的")
    return False, f"md5 {raw[:8]}≠錨 {want_md5[:8]}(LF 正規化後 {lf[:8]} 也不符=內容真的不同)· {len(b)}B"


def intake_files(home: Path | None = None) -> list:
    """批545:收容件夾裡**每一個**同系列檔都列出來(檔名 · 位元 · md5)。
    多一個不在冊上的檔就會當場現形——不必再從一句 md5 去猜是哪個檔被算到。"""
    home = home or intake_home()
    if home is None:
        return []
    out = []
    for f in sorted(home.glob(ENGINE_GLOB)):
        try:
            b = f.read_bytes()
            out.append({"name": f.name, "bytes": len(b), "md5": hashlib.md5(b).hexdigest()})
        except Exception as exc:
            out.append({"name": f.name, "bytes": None, "md5": f"讀不了 {type(exc).__name__}"})
    return out


def intake_engine_file(home: Path | None = None) -> Path | None:
    """批545:**按冊上點名的檔名取**,不再吃 glob 排序。
    舊寫法 `sorted(glob)[-1]` 有洞:夾裡多一個排在後面的同系列檔(`_3.py`/`_v0101.py`…),
    它就自動變成「正典」,而那種檔多半未追蹤,git checkout 還救不回來。
    錨檔不在時才退回 glob 尾版(維持舊行為,但會在 ① 誠實講出來)。"""
    home = home or intake_home()
    if home is None:
        return None
    named = home / INTAKE_ANCHOR["name"]
    if named.is_file():
        return named
    fs = sorted(home.glob(ENGINE_GLOB))
    return fs[-1] if fs else None


def intake_md5_ok(home: Path | None = None) -> tuple[bool, str]:
    home = home or intake_home()
    if home is None:
        return False, "收容件缺"
    mans = sorted(home.glob("_INTAKE_MANIFEST_*.json"))
    f = intake_engine_file(home)
    if not mans or f is None:
        return False, "冊或引擎檔缺"
    try:
        m = json.loads(mans[-1].read_text(encoding="utf-8"))
        e = next((x for x in m.get("files", []) if x.get("name") == f.name), None)
        if not e:
            return False, f"冊上沒有 {f.name}"
        return eol_verdict(f.read_bytes(), e.get("md5") or "", e.get("bytes"))   # 批546 行尾無關
    except Exception as exc:
        return False, f"冊讀不了 {type(exc).__name__}"


# 批541 位元錨:期望值寫死在**程式碼裡**,不是只寫在收容件資料夾的冊裡。
# 冊跟檔案一起被換掉時,兩邊仍然自洽——那種綠燈只是自己對自己點頭(LL74)。錨放在外面才擋得住。
INTAKE_ANCHOR = {
    "name": "VIA_VRN_FirstPageEngine_2.py",
    "bytes": 30115,
    "md5": "d4cdaedf949d78d062a12c0a779b2fb0",
    "sha256": "05029fc07d6679b5ca5d55e351610a7c812eaef755cc59900dc716060699b906",
    # 冊上 `modules` 宣告的 11 項,對到模組裡真正的物件名(SSOT loader 是函式不是類別)
    "symbols": ("load_ssot_blocks", "TickerFilename", "Layout", "TableGeometry", "NLPRepair",
                "FinancialValidation", "PriceAdjustment", "BrokerRatingDict", "FieldValidation",
                "CrossValidation", "FirstPageEngine"),
    "batch": "批522 導入;批541 加錨",
}


INTAKE_REL = "functional modules/VRN/references/intake/VIA_VRN_FirstPageEngine_v0101_b522/VIA_VRN_FirstPageEngine_2.py"


def intake_restore_hint(r: dict) -> str:
    """批544:收容件對不上錨時,直接給還原指令——紅燈要能自救,不是丟兩串 md5 給人猜。
    倉庫裡那份就是錨本身,所以 git checkout 一行就回得來;**本支不代改任何檔**(不代設)。"""
    if "\u2260" not in str(r.get("anchor", "")):
        return ""
    files = intake_files()
    extra = [x for x in files if x["name"] != INTAKE_ANCHOR["name"]]
    lines = ["\n     \u6536\u5bb9\u4ef6\u593e\u88e1\u7684\u540c\u7cfb\u5217\u6a94(\u5168\u5217;\u518a\u4e0a\u53ea\u8a8d "
             + INTAKE_ANCHOR["name"] + "):"]
    for x in files:
        mark = "\u2190 \u518a\u4e0a\u9019\u4e00\u500b" if x["name"] == INTAKE_ANCHOR["name"] else "\u2190 \u4e0d\u5728\u518a\u4e0a"
        lines.append(f"       {x['name']:<40} {x['bytes']}B  {str(x['md5'])[:8]}  {mark}")
    if extra:
        lines.append("     \u21b3 \u6551\u6cd5\u4e00(\u4f60\u7684\u624b):\u4e0a\u9762\u6a19\u300c\u4e0d\u5728\u518a\u4e0a\u300d\u7684\u6a94\u662f\u5f8c\u4f86\u653e\u9032\u53bb\u7684,"
                     "git checkout \u6551\u4e0d\u4e86(\u5b83\u672a\u8ffd\u8e64)\u3002\u8acb\u81ea\u884c\u632a\u8d70\u6216\u522a\u9664\u3002")
    return "\n".join(lines) + ("\n     \u21b3 \u6551\u6cd5(\u4f60\u7684\u624b,\u4e00\u884c):git checkout -- \"" + INTAKE_REL + "\"\n"
            "       \u5009\u5eab\u88e1\u90a3\u4efd\u5c31\u662f\u9328(30,115B / d4cdaedf);\u5de5\u4f5c\u7ad9\u9019\u4efd\u88ab\u5c31\u5730\u6539\u904e\u3002\n"
            "       \u6539\u5b8c\u518d\u8dd1\u4e00\u6b21\u672c\u81ea\u6e2c;\u4ecd\u4e0d\u7b26\u5c31\u628a git status \u90a3\u4e00\u884c\u8cbc\u51fa\u4f86\u3002")


def intake_import_ok(home: Path | None = None) -> tuple[bool, dict]:
    """收容件**導入**驗證(不是「檔案在不在」,是「導得進來、東西都在」)。三段全過才算成立。

    ① 位元錨:檔案 md5/sha256/bytes == 程式碼裡的錨,且錨 == 冊裡的值(三方一致)。
    ② 真 import:exec_module 真的跑完(不是 importlib.util.find_spec 那種「看得到就算」)。
    ③ 模組齊全:冊上宣告的 11 項一個不少。
    回 (ok, 明細);任何一段掛掉都誠實說是哪一段,不含混成一句「收容件有問題」。
    """
    A = INTAKE_ANCHOR
    r = {"anchor": None, "manifest": None, "import": None, "symbols": None, "missing": []}
    home = home or intake_home()
    f = intake_engine_file(home) if home is not None else None
    if f is None:
        r["anchor"] = "ABSENT:收容件缺"
        return False, r
    b = f.read_bytes()
    md5 = hashlib.md5(b).hexdigest()
    sha = hashlib.sha256(b).hexdigest()
    ok_anchor, why_anchor = eol_verdict(b, A["md5"], A["bytes"])      # 批546 行尾無關
    ok_anchor = ok_anchor and f.name == A["name"]
    r["anchor"] = why_anchor if f.name == A["name"] else f"檔名不符:{f.name} ≠ 冊上的 {A['name']}"
    # 冊也要跟錨一致——冊被改寫的那一刻,這裡就會亮
    ok_man = False
    mans = sorted(home.glob("_INTAKE_MANIFEST_*.json"))
    if mans:
        try:
            m = json.loads(mans[-1].read_text(encoding="utf-8"))
            e = next((x for x in m.get("files", []) if x.get("name") == A["name"]), None)
            ok_man = bool(e) and e.get("md5") == A["md5"] and e.get("sha256") == A["sha256"] and e.get("bytes") == A["bytes"]
            r["manifest"] = f"{mans[-1].name} {'=' if ok_man else '≠'}錨"
        except Exception as exc:
            r["manifest"] = f"冊讀不了 {type(exc).__name__}"
    else:
        r["manifest"] = "冊缺"
    mod, why = load_intake()
    ok_imp = mod is not None
    r["import"] = why if ok_imp else f"載不動:{why}"
    if ok_imp:
        r["missing"] = [k for k in A["symbols"] if not hasattr(mod, k)]
        r["symbols"] = f"{len(A['symbols']) - len(r['missing'])}/{len(A['symbols'])}"
    ok_sym = ok_imp and not r["missing"]
    return (ok_anchor and ok_man and ok_sym), r


_E = {"mod": None, "why": ""}


def load_intake():
    """收容件模組(importlib;零觸碰);缺=None+因由。"""
    if _E["mod"] is not None or _E["why"]:
        return _E["mod"], _E["why"]
    f = intake_engine_file()
    if f is None:
        _E["why"] = f"收容件缺:{INTAKE_ROOT / INTAKE_GLOB}"
        return None, _E["why"]
    try:
        spec = importlib.util.spec_from_file_location("via_vrn_firstpage_intake", f)
        m = importlib.util.module_from_spec(spec)
        sys.modules["via_vrn_firstpage_intake"] = m
        spec.loader.exec_module(m)
        for need in ("TickerFilename", "BrokerRatingDict", "FieldValidation", "CrossValidation", "FinancialValidation", "FirstPageEngine"):
            if not hasattr(m, need):
                _E["why"] = f"收容件無 {need}"
                return None, _E["why"]
        _E["mod"] = m
        return m, ""
    except Exception as exc:
        _E["why"] = f"收容件載入失敗 {type(exc).__name__}:{str(exc)[:60]}"
        return None, _E["why"]


# ---------------------------------------------------------------- 名冊(VDF tw_listings 唯讀)
def resolve_vdf_db() -> tuple[Path | None, str]:
    p = os.environ.get("VIA_DB_VDF_TW_MARKET")
    if p and Path(p).is_file():
        return Path(p), "VIA_DB_VDF_TW_MARKET"
    home = os.environ.get("VIA_DATA_HOME")
    if home and Path(home).is_dir():
        hits = sorted(Path(home).rglob("vdf_tw_market.duckdb"))
        if hits:
            return hits[0], "VIA_DATA_HOME rglob"
    if OLD_DB.is_file():
        return OLD_DB, "舊主路徑 output_hub/mega"
    return None, "庫缺(先 via-vdffetch / via-datahome)"


_R = {"tried": False, "codes": set(), "names": {}, "how": ""}


def roster() -> dict:
    """official_set(四碼)+ 名→碼;庫缺/表缺=空集誠實(命中率打折並標明)。"""
    if _R["tried"]:
        return _R
    _R["tried"] = True
    db, how = resolve_vdf_db()
    _R["how"] = how
    if db is None:
        return _R
    try:
        import duckdb
        con = duckdb.connect(str(db), read_only=True)
        try:
            rows = con.execute("SELECT code, name FROM tw_listings WHERE code IS NOT NULL").fetchall()
        finally:
            con.close()
        for code, name in rows:
            c = str(code).strip()
            if len(c) == 4 and c.isdigit():
                _R["codes"].add(c)
                n = str(name or "").strip()
                if len(n) >= 2:
                    _R["names"][n] = c
        _R["how"] = f"{how} · tw_listings {len(_R['codes'])} 檔"
    except Exception as exc:
        _R["how"] = f"{how} · tw_listings 讀不了 {type(exc).__name__}"
    return _R


# ---------------------------------------------------------------- 橋側防呆

# ── 批536:三件正主工具(操作員令「用同義字抓 SSOT/檔名拆解 · NLP 工具 · LAYOUT 工具」)
BROKER_SSOT = VIA / "functional modules" / "VRN" / "registry" / "VRN_BROKER_LIST_v01.json"
_SSOT = {"tried": False, "table": {}, "how": ""}


def ssot_brokers() -> tuple[dict, str]:
    """券商同義字**正本**=VRN_BROKER_LIST(SUP_MDL015 管的那本;20 家含完整別名)。
    canonical 用 canonical_en(英文代號),同時收中文 canonical 當別名。缺=空表誠實。"""
    if _SSOT["tried"]:
        return _SSOT["table"], _SSOT["how"]
    _SSOT["tried"] = True
    if not BROKER_SSOT.is_file():
        _SSOT["how"] = f"SSOT 缺:{BROKER_SSOT.name}"
        return {}, _SSOT["how"]
    try:
        d = json.loads(BROKER_SSOT.read_text(encoding="utf-8"))
        rows = d.get("brokers") or d.get("items") or (d if isinstance(d, list) else [])
        if not rows:
            rows = [v for k, v in d.items() if isinstance(v, dict) and v.get("aliases")]
        tbl = {}
        for b in rows:
            key = str(b.get("canonical_en") or b.get("canonical") or "").upper().replace(" ", "")
            if not key:
                continue
            al = [str(x) for x in (b.get("aliases") or []) if str(x).strip()]
            for extra in (b.get("canonical"), b.get("canonical_en")):
                if extra and str(extra) not in al:
                    al.append(str(extra))
            tbl[key] = al
        _SSOT.update(table=tbl, how=f"{BROKER_SSOT.name} · {len(tbl)} 家 · {sum(len(v) for v in tbl.values())} 別名")
    except Exception as exc:                                  # noqa: BLE001
        _SSOT["how"] = f"SSOT 讀不了 {type(exc).__name__}"
    return _SSOT["table"], _SSOT["how"]


_LAYOUT = {"tried": False, "idx": {}, "how": ""}


def layout_index() -> tuple[dict, str]:
    """LAYOUT 工具:收容件 02_layout/logical_layout.json(唯讀)→ {原檔名: {header, body}}。
    有版面就用版面,沒有才退回「前 N 行當資訊區」(不編造分區)。"""
    if _LAYOUT["tried"]:
        return _LAYOUT["idx"], _LAYOUT["how"]
    _LAYOUT["tried"] = True
    home = corpus_home()
    if home is None:
        _LAYOUT["how"] = "語料收容件缺"
        return {}, _LAYOUT["how"]
    lay = home.parent.parent / "02_layout" / "logical_layout.json"
    if not lay.is_file():
        _LAYOUT["how"] = "logical_layout.json 缺(退回行數啟發)"
        return {}, _LAYOUT["how"]
    try:
        d = json.loads(lay.read_text(encoding="utf-8"))
        idx: dict = {}
        for e in d.get("elements", []):
            fn = str(e.get("filename") or "")
            if not fn:
                continue
            sub = str(e.get("subtype") or "").upper()
            txt = str(e.get("text") or "")
            slot = "header" if sub in ("TITLE", "HEADER", "HEAD", "SUBTITLE") else "body"
            idx.setdefault(fn, {"header": [], "body": []})[slot].append(txt)
        _LAYOUT.update(idx={k: {"header": "\n".join(v["header"]), "body": "\n".join(v["body"])} for k, v in idx.items()},
                       how=f"logical_layout.json · {len(idx)} 檔 · {d.get('element_count')} 元素")
    except Exception as exc:                                  # noqa: BLE001
        _LAYOUT["how"] = f"layout 讀不了 {type(exc).__name__}"
    return _LAYOUT["idx"], _LAYOUT["how"]


_NLPH = {"tried": False, "mod": None, "how": ""}


def nlp_hub():
    """NLP 工具:VRN_ENG066 樞紐(normalize 正主);缺=None 誠實(不自己寫轉換表)。"""
    if _NLPH["tried"]:
        return _NLPH["mod"], _NLPH["how"]
    _NLPH["tried"] = True
    try:
        c = sorted(HERE.glob("VRN_ENG066_NLPSupportHub_v*.py"))
        if not c:
            _NLPH["how"] = "ENG066 缺席"
            return None, _NLPH["how"]
        spec = importlib.util.spec_from_file_location("eng066_for_086", c[-1])
        m = importlib.util.module_from_spec(spec)
        sys.modules["eng066_for_086"] = m
        spec.loader.exec_module(m)
        if not hasattr(m, "normalize"):
            _NLPH["how"] = f"{c[-1].name} 無 normalize"
            return None, _NLPH["how"]
        try:
            probe = m.normalize("报告营收")
            ok = "報告" in probe and "營收" in probe
        except Exception:
            ok = False
        _NLPH.update(mod=m, how=f"{c[-1].name} · 簡繁轉換{'可' if ok else '不可(本境無 opencc;直通)'}")
    except Exception as exc:                                  # noqa: BLE001
        _NLPH["how"] = f"ENG066 載入失敗 {type(exc).__name__}"
    return _NLPH["mod"], _NLPH["how"]


def nlp_normalize(text: str) -> str:
    """過 ENG066 樞紐做簡→繁與全形正規化。**逐行**做:樞紐的 normalize 會把換行吃掉
    (ENG064 normalizer 的 preserve_newlines=False),行結構一沒,逐行判準(標題行/獨立短行評等)就全失效——
    批536 實測:整段丟進去,評等由 33/38 掉到 29/38。缺樞紐=原樣回傳(誠實)。"""
    m, _ = nlp_hub()
    if m is None or not text:
        return text
    out = []
    for ln in text.splitlines():
        if not ln.strip():
            out.append(ln)
            continue
        try:
            out.append(m.normalize(ln) or ln)
        except Exception:
            out.append(ln)
    return "\n".join(out)

def _has_cjk(s: str) -> bool:
    return bool(re.search(r"[一-鿿]", s or ""))


def broker_tables(E=None) -> dict:
    """收容件 BROKER 字典 + VIA 補冊(canon → 別名集)。"""
    E = E or load_intake()[0]
    base = dict(getattr(E, "BrokerRatingDict").BROKER) if E is not None else {}
    out = {k: list(v) for k, v in base.items()}
    ssot, _ = ssot_brokers()                                  # 批536:SSOT 券商冊=正本(一功能一主 L30)
    ssot_alias = {a.lower() for v in ssot.values() for a in v}
    for k, v in ssot.items():
        out.setdefault(k, [])
        out[k] = list(dict.fromkeys(out[k] + list(v)))
    for k, v in EXTRA_BROKER.items():                         # 我的補冊只補 SSOT 沒有的;別名撞上就讓位(避免同一家兩個正典名)
        if k not in ssot and any(a.lower() in ssot_alias for a in v):
            continue
        out.setdefault(k, [])
        out[k] = list(dict.fromkeys(out[k] + list(v)))
    for k in list(out):                                       # 批541:別名被 SSOT 收編 → 非 SSOT 的鍵一律讓位
        # 舊規則多一句 `and k not in EXTRA_BROKER`,於是「兩邊都有」的鍵(JPMORGAN)永遠 pop 不掉=同一家兩個正典名
        if k not in ssot and any(a.lower() in ssot_alias for a in out[k]):
            out.pop(k, None)
    return out


def broker_conflicts(E=None) -> dict:
    """批541 去衝突量尺:合併後同一個別名對到多個正典名 = 衝突(下游一 join 就散)。
    回 {n, rows};自測斷言它必須是 0——鎖上了,同一家兩個正典名就回不來。"""
    import collections as _c
    own = _c.defaultdict(set)
    for k, al in broker_tables(E).items():
        for a2 in al:
            a2 = str(a2).strip().lower()
            if a2:
                own[a2].add(k)
    rows = [{"alias": a2, "canons": sorted(v)} for a2, v in sorted(own.items()) if len(v) > 1]
    return {"n": len(rows), "rows": rows}


_CONTACT_RX = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+|(?:https?://|www\.)\S+", re.I)


def strip_contacts(text: str) -> str:
    """批537:分析師信箱與網址**不是**文內券商證據。
    實測:Daiwa-3653/6278/PCB 的唯一「cathay」出自 `…@daiwacm-cathay.com.tw`(大和國泰合資體網域),
    而 `cathay`(6 字)比 `daiwa`(5 字)長,最長別名優先就把三份日系報告判成國泰=假綠。"""
    return _CONTACT_RX.sub(" ", text or "")


def subject_names(text: str, filename: str, ticker: str | None) -> set:
    """批537:**不靠庫**把「本報告標的公司名」讀出來——庫在本境是空殼(tw_listings 只有 892 檔,2891 不在內;LL49),
    靠庫的否決在工作站有效、在本境失效=會留下假綠。兩條與代碼相鄰的鐵證:
      ① 文內 `台灣中信金(2891.TW/2891 TT)` → 括號前那串就是公司名;
      ② 檔名 `凱基投顧_2891 中信金_施志鴻_…` → 代碼後那串就是公司名。"""
    out = set()
    if not ticker:
        return out
    tk = re.escape(str(ticker))
    for m in re.finditer(r"([\u4e00-\u9fffA-Za-z][\u4e00-\u9fffA-Za-z0-9\-\.&]{1,15})\s*[(（]\s*" + tk + r"\b", text or ""):
        out.add(m.group(1))
    for m in re.finditer(tk + r"\s*[_\-  ]\s*([\u4e00-\u9fff][\u4e00-\u9fffA-Za-z\-]{1,11})", filename or ""):
        out.add(m.group(1))
    return {x for x in out if x}


def safe_broker_ev(text: str, E=None, allow_contacts: bool = False, veto: set | None = None) -> tuple:
    """券商正典 + **證據分級**。回 (canon|None, how);how ∈ 文內 / 電郵網域(弱) / 無。
    veto=本報告標的公司名:別名若是標的公司名的一部分就不算券商證據(批537)。"""
    canon = _safe_broker_raw(text if allow_contacts else strip_contacts(text), E, veto)
    if canon:
        return canon, ("電郵網域(弱)" if allow_contacts else "文內")
    return None, "無"


def safe_broker(text: str, E=None) -> str | None:
    """相容殼:只要正典名(去電郵/網址後判;要含電郵證據請用 safe_broker_ev(..., allow_contacts=True))。"""
    return safe_broker_ev(text, E)[0]


def _safe_broker_raw(text: str, E=None, veto: set | None = None) -> str | None:
    """券商正典:CJK 別名子字串;拉丁別名詞界;≤3 字拉丁(gs/ms/mq/ubs)須大寫獨立詞;泛用英文字要跟 securities/invest。最長別名優先。
    批537 標的否決:金控名常與券商同源(中信金 2891 / 台新金 2887 / 元大金 2885),標的公司名內的別名不是券商證據
    ——實測 `凱基投顧_2891 中信金_…` 被判成 CTBC(內文只有「中信金」,「凱基投顧」在檔名)=假綠。
    代價很小:券商寫自家母公司的報告會退到檔名那層,而那層本來就是對的。"""
    if not text:
        return None
    low = text.lower()
    vetol = {v.lower() for v in (veto or set()) if v}
    best = None
    for canon, aliases in broker_tables(E).items():
        for a in aliases:
            al = a.lower().strip()
            if not al or any(al in v for v in vetol):      # 批537:別名是標的公司名的一部分 → 不算券商證據
                continue
            hit = False
            if _has_cjk(al):
                hit = al in text
            elif len(al) <= 3:
                hit = re.search(r"(?<![A-Za-z])" + re.escape(a.upper()) + r"(?![A-Za-z])", text) is not None
            elif al in GENERIC_LATIN:
                hit = re.search(r"(?<![a-z])" + re.escape(al) + r"(?![a-z])\s+(securities|sec\b|investment|invest)", low) is not None
            else:
                hit = re.search(r"(?<![a-z])" + re.escape(al) + r"(?![a-z])", low) is not None
            if hit and (best is None or len(al) > best[1]):
                best = (canon, len(al))
    return best[0] if best else None


def safe_rating(text: str, E=None) -> dict:
    """評等正典:線索詞(評等/建議/Rating)後的詞優先;否則獨立短行(≤8 字)剛好是別名;拉丁詞界(buy≠buyback、hold≠holdings);add 不單獨算。"""
    E = E or load_intake()[0]
    RAT = dict(getattr(E, "BrokerRatingDict").RATING) if E is not None else {}
    if not text:
        return {"raw": None, "canonical": None, "in_dict": False, "how": "空文"}

    def canon_of(word: str) -> str | None:
        w = word.lower().strip()
        for k, al in RAT.items():
            for a in al:
                a = a.lower()
                if _has_cjk(a):
                    if a in w:
                        return k
                elif re.fullmatch(re.escape(a), w) or re.search(r"(?<![a-z])" + re.escape(a) + r"(?![a-z])", w):
                    return k
        return None
    m = _RATING_CUE.search(text)
    if m:
        c = canon_of(m.group(2))
        return {"raw": m.group(0)[:40], "canonical": c, "in_dict": c is not None, "how": "線索詞"}
    def canon_exact(word: str) -> str | None:
        """批540:整行**等於**別名才算(去尾標點);包含不算——「外資持有比重上升」含「持有」但不是評等。"""
        w = (word or "").strip().strip(":：。.、,,;;").strip()
        if not w:
            return None
        for k, al in RAT.items():
            for a2 in al:
                if w == a2 or w.lower() == a2.lower():
                    return k
        return None

    for ln in text.splitlines():
        s = ln.strip()
        if 0 < len(s) <= 8:
            c = canon_exact(s)
            if c is not None and s.lower() not in ("add",):
                return {"raw": s, "canonical": c, "in_dict": True, "how": "獨立短行(整行等於別名)"}
    for k, al in RAT.items():
        for a in al:
            if not _has_cjk(a) and len(a) >= 5 and a.lower() not in ("accumulate",):
                if re.search(r"(?<![a-z])" + re.escape(a.lower()) + r"(?![a-z])", text.lower()):
                    return {"raw": a, "canonical": k, "in_dict": True, "how": "拉丁詞界"}
    return {"raw": None, "canonical": None, "in_dict": False, "how": "無線索"}


_UPSIDE_RX = re.compile(r"(潛在)?上漲空間|上檔空間|upside", re.I)


def _is_upside_context(text: str, pos: int, span: int = 26) -> bool:
    """備用倉 via-vdf-vrn 對同一批 64 份報告的教訓:目標價與「潛在上漲空間」是兩個欄位;
    幅度(23%)不是價格。命中點前後有上漲空間字樣、或數字帶 %,一律不當目標價。"""
    seg = text[max(0, pos - span): pos + span]
    return bool(_UPSIDE_RX.search(seg)) or "%" in seg[span:span + 4] or "％" in seg[span:span + 4]


def _plausible_tp(raw: str) -> bool:
    """數字字串至少兩位數或帶小數(「1」「5」這種單碼多半是頁碼/序號)。"""
    digits = re.sub(r"[^\d]", "", raw or "")
    return len(digits) >= 2 or "." in (raw or "")


def safe_target_price(text: str, E=None, exclude_code: str | None = None, exclude_codes: set | None = None) -> tuple[float | None, str]:
    """目標價:線索詞(目標價/Target Price/TP/PT 詞界)優先,退收容件 NT$ 弱正則;候選過濾:至少兩位數或帶小數、不得是代碼(解析到的代碼或名冊內且出現在文中的四碼)。"""
    ex = set(exclude_codes or set())
    if exclude_code:
        ex.add(str(exclude_code))

    def _ok(raw: str):
        if not _plausible_tp(raw):
            return None
        try:
            v = float(raw.replace(",", ""))
        except ValueError:
            return None
        if v == float(int(v)) and str(int(v)) in ex:
            return None
        return v
    for i, rx in enumerate(_TP_CUES):
        for m in rx.finditer(text or ""):
            if _is_upside_context(text or "", m.end(1)):      # 幅度不是價格
                continue
            v = _ok(m.group(1))
            if v is not None:
                return v, ("目標價線索" if i == 0 else "TP 線索")
    E = E or load_intake()[0]
    # 批536:文中沒有「目標價/Target Price/TP/PT」線索就**不給值**——弱正則會把任何 NT$ 數字當目標價
    # (實測:MS-Thermal 這類產業報告被抓出 17382 = 誤抓,下游會吃到假資料)。
    if E is not None and re.search(r"目標價|Target\s*Price|Price\s*Target|(?<![A-Za-z])TP(?![A-Za-z])|(?<![A-Za-z])PT(?![A-Za-z])", text or "", re.I):
        try:
            for m in E.FieldValidation._TP.finditer(text or ""):
                v = _ok(m.group(1))
                if v is not None:
                    return v, "收容件 NT$ 正則(弱)"
        except Exception:
            pass
    return None, "無"


def roc7_to_iso(tok: str) -> str | None:
    t = str(tok or "")
    if len(t) == 7 and t.isdigit() and t[0] == "1":
        y, mo, d = 1911 + int(t[:3]), int(t[3:5]), int(t[5:])
        if 1 <= mo <= 12 and 1 <= d <= 31:
            return f"{y:04d}-{mo:02d}-{d:02d}"
    return None



# ── 批536:文件類型(決定「該不該有單一代碼」;沒有不是漏抓,是這份報告本來就沒有)
_DOCTYPE_RULES = (
    ("晨會早報", ("晨會", "早報", "晨間", "盤勢", "日報", "週報", "周報")),
    ("市場分析", ("美股分析", "日股分析", "港股分析", "陸股", "asia hardware", "insights")),
    ("期貨", ("期貨", "futures")),
    ("策略展望", ("展望", "大趨勢", "策略", "outlook", "thoughts on")),
    ("產業報告", ("產業", "族群", "類股", "sector", "memory", "automation", "thermal", "abf", "pcb", "ccl", "tpu", "hardware")),
)
_RATING_FN = (
    (re.compile(r"[,(（]\s*NR[_\s]*未評等"), None),
    (re.compile(r"[,(（]\s*N\s*[,，]\s*中立"), "HOLD"),
    (re.compile(r"初次評等\s*買進|評等\s*買進|買進"), "BUY"),
    (re.compile(r"評等\s*中立|維持中立"), "HOLD"),
    (re.compile(r"評等\s*賣出|減碼"), "SELL"),
)


_TP_CUE_ANY = re.compile(r"目標價|Target\s*Price|Price\s*Target|(?<![A-Za-z])TP(?![A-Za-z])|(?<![A-Za-z])PT(?![A-Za-z])", re.I)
_TP_NA_RX = re.compile(r"(?:目標價|Target\s*Price|Price\s*Target)\s*[:：]?\s*(?:n\.\s?a\.?|(?<![A-Za-z])na(?![A-Za-z])|not\s+applicable|不適用|未提供|未評等)", re.I)


def tp_state(text: str, value) -> str:
    """批537 目標價誠實四態:HIT / NA_DECLARED(報告自己寫 n.a.)/ ABSENT_IN_TEXT(這份文字裡根本沒有目標價欄)/ MISS(有線索卻抓不到=真 RED)。"""
    if value is not None:
        return "HIT"
    t = text or ""
    if _TP_NA_RX.search(t):
        return "NA_DECLARED"
    if not _TP_CUE_ANY.search(t):
        return "ABSENT_IN_TEXT"
    return "MISS"


def rating_state(canonical, has_token: bool, is_stock: bool) -> str:
    """批537 評等誠實四態:HIT / NOT_STOCK(產業、晨會、市場分析本來就沒有單一評等)/ NA_NO_TOKEN(文中無評等字樣)/ MISS(有字樣、是個股、卻抓不到=真 RED)。"""
    if canonical:
        return "HIT"
    if not is_stock:
        return "NOT_STOCK"
    return "MISS" if has_token else "NA_NO_TOKEN"


def date_state(filename: str, date) -> str:
    """批537 檔名日期誠實三態:HIT / ABSENT(檔名本來就沒有六碼以上數字)/ MISS(有卻解不出=真 RED)。"""
    if date:
        return "HIT"
    return "MISS" if re.search(r"\d{6,8}", filename or "") else "ABSENT"


def doc_type(filename: str) -> str:
    low = (filename or "").lower()
    for name, keys in _DOCTYPE_RULES:
        if any(k in low or k in (filename or "") for k in keys):
            return name
    return "個股報告"


def expects_ticker(filename: str) -> bool:
    return doc_type(filename) == "個股報告"


def rating_from_filename(filename: str) -> str | None:
    for rx, canon in _RATING_FN:
        if rx.search(filename or ""):
            return canon
    return None


LOCAL_RATING_SCALE = (      # 批537:本土/在地券商自己的評等用語(收容件 RATING 冊沒有;實測凱基三份報告全寫「增加持股」)
    ("增加持股", "BUY"), ("增持", "BUY"), ("優於大盤", "BUY"), ("強於大盤", "BUY"), ("表現優於大盤", "BUY"),
    ("減少持股", "SELL"), ("減持", "SELL"), ("劣於大盤", "SELL"), ("弱於大盤", "SELL"), ("表現劣於大盤", "SELL"),
    ("持有評等", "HOLD"), ("同步大盤", "HOLD"), ("與大盤同步", "HOLD"), ("區間操作", "HOLD"),
)
_LOCAL_RATING_RX = re.compile("|".join(re.escape(w) for w, _ in LOCAL_RATING_SCALE))
_LOCAL_RATING_MAP = dict(LOCAL_RATING_SCALE)


def rating_local_scale(text: str, lines: int = 40) -> dict | None:
    """本土券商評等尺度:只看前 N 行(第一頁的評等欄/重申句),避免內文「外資持有」「增持庫藏股」誤判。"""
    head = "\n".join((text or "").splitlines()[:lines])
    best = None
    for m in _LOCAL_RATING_RX.finditer(head):
        w = m.group(0)
        if best is None or len(w) > len(best):
            best = w                                   # 最長者優先:「表現優於大盤」勝過「優於大盤」
    if not best:
        return None
    return {"raw": best, "canonical": _LOCAL_RATING_MAP[best], "in_dict": False, "how": "本土評等尺度(前段)"}


_TITLE_RATING = re.compile(r"[;,，、:：\-–—(（]\s*(""強力買進|買進|加碼|逢低|中立|持有|區間|賣出|減碼|Strong Buy|Buy|Outperform|Overweight|Accumulate|Add|Neutral|Hold|Market Perform|Equal-?weight|Sell|Underperform|Underweight|Reduce"r")\b", re.I)


def rating_from_title(text: str, E=None) -> dict | None:
    """外資標題常把評等掛句尾:`Hon Hai (2317.TW): …; Buy (on CL)`。以標點為界,只看前兩行。"""
    E = E or load_intake()[0]
    RAT = dict(getattr(E, "BrokerRatingDict").RATING) if E is not None else {}
    head = "\n".join((text or "").splitlines()[:2])
    m = _TITLE_RATING.search(head)
    if not m:
        return None
    w = m.group(1).lower()
    for k, al in RAT.items():
        if any(w == a.lower() for a in al):
            return {"raw": m.group(0).strip(), "canonical": k, "in_dict": True, "how": "標題行(標點為界)"}
    return None


def rating_has_any_token(text: str, E=None) -> bool:
    """文中到底有沒有評等字樣——沒有=誠實 N/A,不是漏抓。"""
    E = E or load_intake()[0]
    RAT = dict(getattr(E, "BrokerRatingDict").RATING) if E is not None else {}
    low = (text or "").lower()
    for al in RAT.values():
        for a in al:
            if _has_cjk(a):
                if a in (text or ""):
                    return True
            elif re.search(r"(?<![a-z])" + re.escape(a.lower()) + r"(?![a-z])", low):
                return True
    return bool(re.search(r"投資評等|評等|評級", text or ""))

_RATING_QUOTED = re.compile(r"(維持|調整為|調升為|調降為|給予|給與)?\s*[「『\u201c\"]\s*(""強力買進|買進|加碼|逢低|中立|持有|區間|賣出|減碼"r")\s*[」』”\"]\s*(評等|評級)?")
_NOT_RATED = re.compile(r"未評等|NR[_\s]*未評等|Not\s*Rated|\bNR\b")


def rating_quoted(text: str, E=None) -> dict | None:
    """本土寫法:`我們維持「持有」評等。`——評等詞在引號裡,線索詞在後。"""
    E = E or load_intake()[0]
    RAT = dict(getattr(E, "BrokerRatingDict").RATING) if E is not None else {}
    m = _RATING_QUOTED.search(text or "")
    if not m:
        return None
    w = m.group(2)
    for k, al in RAT.items():
        if any(w == a for a in al):
            return {"raw": m.group(0).strip()[:24], "canonical": k, "in_dict": True, "how": "引號內評等"}
    return None


def rating_not_rated(text: str, filename: str = "") -> dict | None:
    """`未評等 / NR / Not Rated`=券商明說不給評等(誠實記 NR,不是漏抓)。"""
    if _NOT_RATED.search((filename or "") + "\n" + (text or "")[:4000]):
        return {"raw": "未評等", "canonical": "NR", "in_dict": True, "how": "明示未評等"}
    return None

def rating_standalone(text: str, E=None, lines: int = 40) -> dict | None:
    """前 N 行裡「獨立一行就是評等」的外資寫法(Buy / Outperform / Neutral / Overweight)。"""
    E = E or load_intake()[0]
    RAT = dict(getattr(E, "BrokerRatingDict").RATING) if E is not None else {}
    for ln in (text or "").splitlines()[:lines]:
        t = ln.strip().strip(":：").strip()
        if not t or len(t) > 22:
            continue
        for k, al in RAT.items():
            for a in al:
                if t.lower() == a.lower():
                    return {"raw": t, "canonical": k, "in_dict": True, "how": "前段獨立行"}
    return None

def make_tf(E, codes: set | None = None, names: dict | None = None):
    tf = E.TickerFilename(None, codes or None)
    if names:
        tf.alias2tk = dict(names)
        tf.tk2name = {c: n for n, c in names.items()}
    return tf


def filename_fields(E, tf, filename: str) -> dict:
    p = tf.parse_filename(filename)
    ticker = p["tickers"][0] if p["tickers"] else None
    date = p["dates"][0] if p["dates"] else None
    if date is None:
        for tok, kind in tf.tokenize(filename):
            if kind == "DIGIT" and roc7_to_iso(tok):
                date = roc7_to_iso(tok)
                break
    broker = safe_broker(re.sub(r"\.(pdf|docx?|pptx?)$", "", filename, flags=re.I), E)
    return {"ticker": ticker, "broker": broker, "date": date, "parse": p}


# ---------------------------------------------------------------- 逐件邏輯
def analyze_one(E, tf, filename: str, header: str, right: str, body: str, footer: str) -> dict:
    fnf = filename_fields(E, tf, filename)
    title = (header or "").strip() or (body or "").strip().splitlines()[0][:120] if (header or body) else ""
    full = "\n".join(x for x in (header, right, body, footer) if x)
    zone = "\n".join(x for x in (header, right) if x) + "\n" + (body or "")[:400]
    res = tf.resolve(filename, title, body or "")
    emails = tf.parse_email(full)
    fv = E.FieldValidation()
    veto = {n for n in ((getattr(tf, "tk2name", {}) or {}).get(res.get("ticker")), ) if n}   # 批537:標的公司名(庫)
    veto |= subject_names(full, filename, res.get("ticker"))                          # 批537:標的公司名(文內/檔名相鄰;不靠庫)
    page_broker, broker_how = safe_broker_ev(zone, E, veto=veto)                      # 批537 證據分級:文內(去電郵/網址)
    if not page_broker:
        page_broker, broker_how = safe_broker_ev(full, E, veto=veto)
    if not page_broker and fnf["broker"]:
        page_broker, broker_how = fnf["broker"], "檔名"                                # 批536:頁面沒認出就用檔名(券商自己命名的)
    if not page_broker:
        page_broker, broker_how = safe_broker_ev(full, E, allow_contacts=True, veto=veto)   # 批537 最弱一層:分析師電郵網域
    head_for_rating = "\n".join(x for x in (header, right) if x) + "\n" + (body or "")     # 批537:本土尺度只看前段
    rating = safe_rating(zone, E)
    if not rating.get("canonical"):                                                   # 批536:檔名評等 → 前段獨立行(外資寫法)
        _c = rating_from_filename(filename)
        if _c:
            rating = {"raw": filename[:40], "canonical": _c, "in_dict": True, "how": "檔名評等"}
        else:
            _alt = rating_from_title(full, E) or rating_standalone(full, E)
            if _alt and _alt.get("canonical"):
                rating = _alt
            else:
                _s2 = safe_rating(full, E)                    # 批536:線索詞掃全文(兆豐「投資評等調降至中立」在內文)
                if _s2.get("canonical"):
                    rating = _s2
                else:
                    _q = (rating_quoted(full, E) or rating_local_scale(head_for_rating)
                          or rating_not_rated(full, filename))                       # 批536:引號內評等 · 批537:本土尺度 · 明示未評等
                    if _q:
                        rating = _q
    rating["text_has_token"] = rating_has_any_token(full, E)   # 文中沒有評等字樣=誠實 N/A(不是漏抓)
    codes_in_text = {c for c in re.findall(r"(?<!\d)([1-9]\d{3})(?!\d)", full) if c in roster()["codes"]} | ({res.get("ticker")} if res.get("ticker") else set())
    digest = bool(re.search(r"晨會|早報|週報|周報|日報|摘要|盤勢|大趨勢|策略|展望", filename)) and res.get("method") in ("BODY_BARE", "BODY_SUFFIX", "NONE", "SECTOR_FILE", "SECTOR_TITLE")
    if digest:                                                      # 多公司摘要/晨會:目標價與評等不屬單一公司,不取(誠實)
        tp, tp_how = None, "多公司摘要不取"
        rating = {"raw": None, "canonical": None, "in_dict": False, "how": "多公司摘要不取"}
    else:
        tp, tp_how = safe_target_price(zone, E, exclude_codes=codes_in_text)
        if tp is None:
            tp, tp_how = safe_target_price(full, E, exclude_codes=codes_in_text)
    xv = E.CrossValidation()
    page = {"ticker": res.get("ticker") or None, "broker": page_broker, "date": fnf["date"]}
    out = {
        "schema": "VIA.FirstPageLogic86.v1", "filename": filename,
        "filename_fields": {k: fnf[k] for k in ("ticker", "broker", "date")},
        "ticker": res, "broker": page_broker, "broker_how": broker_how, "rating": rating,
        "target_price": {"value": tp, "how": tp_how, "validation": (fv.validate_target_price(tp) if tp is not None else {"target_price": None, "verdict": "N/A"})},
        "doc_type": doc_type(filename), "expects_ticker": expects_ticker(filename),
        "emails": emails, "tel": fv.extract_tel(full)[:3],
        "xv_filename_vs_page": xv.filename_vs_page(fnf, page),
        "xv_zone_presence": xv.zone_presence([x for x in (tp, rating.get("canonical"), page_broker) if x], [s for s in re.split(r"(?<=[。.!?！？])\s*", body or "") if s.strip()][:50]),
        "governance": "append-only;ENG072 正本與 sidecar 零觸碰;收容件零觸碰(橋側防呆)",
    }
    if emails:
        e0 = emails[0]["analyst_id"] + "@" + emails[0]["broker_domain"]
        out["email_validation"] = fv.validate_email(e0, page_broker)
    return out


def _read_sidecar(p: Path) -> dict:
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"_err": f"{type(exc).__name__}"}
    if not isinstance(d, dict):
        return {"_err": "非物件"}
    body = d.get("body") or ""
    if not body and (p.with_suffix(".txt")).exists():
        try:
            body = p.with_suffix(".txt").read_text(encoding="utf-8", errors="replace")
        except Exception:
            body = ""
    src = d.get("source") or {}
    fn = None
    if isinstance(src, dict):
        fn = src.get("file") or src.get("name") or src.get("path")
    elif isinstance(src, str):
        fn = src
    fn = Path(fn).name if fn and re.search(r"\.(pdf|docx?|pptx?|png|jpe?g|tiff?)$", str(fn), re.I) else None     # source 多半是方法描述字串,不是檔名
    fn = fn or (p.stem + ".pdf")
    return {"filename": fn, "header": d.get("header") or "", "right": d.get("right") or "", "body": body, "footer": d.get("footer") or ""}


def enrich(args: list, do_print: bool = True) -> dict:
    E, why = load_intake()
    rep = {"schema": "VIA.FirstPageLogic86.summary.v1", "verb": "enrich", "ts": _dt.datetime.now().isoformat(timespec="seconds"), "state": "ABSENT", "why": why, "n": 0}
    if E is None:
        _emit(rep, do_print)
        return rep
    src = Path(_arg(args, "--in", str(FP_OUT)))
    out_dir = Path(_arg(args, "--out", str(OUT)))
    limit = int(_arg(args, "--limit", "0") or 0)
    files = sorted(p for p in src.glob("*.json") if not p.name.endswith(".logic86.json") and not p.name.startswith("LOGIC86"))
    if limit > 0:
        files = files[:limit]
    if not files:
        rep.update(state="NODATA", why=f"sidecar 零件:{src}(先 via-firstpage)")
        _emit(rep, do_print)
        return rep
    R = roster()
    tf = make_tf(E, R["codes"], R["names"])
    out_dir.mkdir(parents=True, exist_ok=True)
    methods, agree, n_broker, n_rating, n_tp, n_err, items = {}, 0, 0, 0, 0, 0, []
    for p in files:
        sc = _read_sidecar(p)
        if sc.get("_err"):
            n_err += 1
            items.append({"stem": p.stem, "state": "FAIL", "why": sc["_err"]})
            continue
        try:
            r = analyze_one(E, tf, sc["filename"], sc["header"], sc["right"], sc["body"], sc["footer"])
        except Exception as exc:
            n_err += 1
            items.append({"stem": p.stem, "state": "FAIL", "why": f"{type(exc).__name__}:{str(exc)[:60]}"})
            continue
        r["source_sidecar"] = str(p)
        r["ts"] = rep["ts"]
        (out_dir / (p.stem + ".logic86.json")).write_text(json.dumps(r, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        m = r["ticker"]["method"]
        methods[m] = methods.get(m, 0) + 1
        if r["xv_filename_vs_page"]["verdict"] == "PASS" and r["xv_filename_vs_page"]["fields"]["ticker"]["match"] is not None:
            agree += 1
        n_broker += 1 if r["broker"] else 0
        n_rating += 1 if r["rating"].get("canonical") else 0
        n_tp += 1 if r["target_price"]["value"] is not None else 0
        items.append({"stem": p.stem, "state": "OK", "ticker": r["ticker"]["ticker"], "method": m, "broker": r["broker"], "rating": r["rating"].get("canonical"), "tp": r["target_price"]["value"]})
    n = len(files) - n_err
    rep.update(state="OK" if n > 0 else "FAIL", n=n, errors=n_err, roster=R["how"], out_dir=str(out_dir),
               methods=methods, ticker_agree_filename_page=agree, broker_hit=n_broker, rating_hit=n_rating, tp_hit=n_tp, items=items,
               why=f"{n} 件 · 代碼法 {methods} · 檔名×首頁代碼一致 {agree}/{n} · 券商 {n_broker}/{n} · 評等 {n_rating}/{n} · 目標價 {n_tp}/{n}")
    (out_dir / "LOGIC86_latest.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    _emit(rep, do_print)
    return rep


def bench(args: list, do_print: bool = True) -> dict:
    """小數量實測:StockReportBasicInfo.json 的真檔名 vs 記錄的 Ticker/Broker/ReportDate。"""
    E, why = load_intake()
    rep = {"verb": "bench", "state": "ABSENT", "why": why, "n": 0}
    if E is None:
        _emit(rep, do_print)
        return rep
    if not BASICINFO.exists():
        rep.update(state="NODATA", why=f"{BASICINFO.name} 缺")
        _emit(rep, do_print)
        return rep
    recs = [r for r in json.loads(BASICINFO.read_text(encoding="utf-8")) if r.get("SourceFile")]
    limit = int(_arg(args, "--limit", "0") or 0)
    if limit > 0:
        recs = recs[:limit]
    R = roster()
    tf = make_tf(E, R["codes"], R["names"])
    t_hit = t_tot = b_hit = b_tot = d_hit = d_tot = 0
    misses = []
    for r in recs:
        fn = r["SourceFile"]
        res = tf.resolve(fn)
        ff = filename_fields(E, tf, fn)
        want_t = str(r.get("Ticker") or "").strip()
        if want_t:
            t_tot += 1
            if res.get("ticker") == want_t:
                t_hit += 1
            else:
                misses.append(f"代碼 {fn[:48]} → {res.get('ticker') or '-'}({res.get('method')}) ≠ {want_t}")
        want_b = str(r.get("Broker") or "").strip()
        if want_b:
            b_tot += 1
            wb = safe_broker(want_b, E)
            if ff["broker"] and wb and ff["broker"] == wb:
                b_hit += 1
            else:
                misses.append(f"券商 {fn[:48]} → {ff['broker'] or '-'} ≠ {want_b}({wb or '冊無'})")
        want_d = str(r.get("ReportDate") or "").strip()
        if want_d:
            d_tot += 1
            if ff["date"] == want_d:
                d_hit += 1
            else:
                misses.append(f"日期 {fn[:48]} → {ff['date'] or '-'} ≠ {want_d}")
    rep.update(state="OK", n=len(recs), roster=R["how"], ticker=f"{t_hit}/{t_tot}", broker=f"{b_hit}/{b_tot}", date=f"{d_hit}/{d_tot}", misses=misses,
               why=f"{len(recs)} 份真檔名 · 代碼 {t_hit}/{t_tot} · 券商 {b_hit}/{b_tot} · 日期 {d_hit}/{d_tot} · 名冊 {R['how']}")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "BENCH_latest.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    _emit(rep, do_print)
    if do_print:
        for m in misses[:40]:
            print("  [漏] " + m)
    return rep


GAP_TABLE = [
    ("TickerFilename 檔名→代碼階梯(FILE_SUFFIX/FILE_BARE/SECTOR/TITLE_SUFFIX/TITLE_SYNONYM/BODY_SUFFIX/年段回收/BODY_BARE)+ 三碼互核", "已接線(enrich/bench)"),
    ("BrokerRatingDict 券商/評等正典(+VIA 本土券商補冊;橋側詞界防呆)", "已接線"),
    ("FieldValidation email/電話/目標價 + 目標價合理性(TP=PER×EPS、上漲空間 ≤200%)", "已接線(PER/EPS 有料時才驗)"),
    ("CrossValidation 檔名×首頁四欄互核、資訊區/本文區在不在、歷史值對交易所來源", "已接線(檔名×首頁、區在不在);歷史值對來源=候(要 ENG074 表格)"),
    ("NLPRepair 句修復(可掛 via_nlp)", "未接線(ENG072 自有句級修復 ⑭;不疊床)"),
    ("Layout 字級階層(MAIN_TITLE/HEADLINE/H2/BODY/FOOTER)+ 公司名=最大且粗體", "未接線(要 chars 幾何;ENG072 sidecar 無 chars)=候"),
    ("TableGeometry 隱藏格線表格重建 + 期別表頭正典(12/24A→2024-12)", "未接線(要 chars 幾何)=候;期別正典可供 ENG074"),
    ("FinancialValidation 加減/乘除/YoY 容差帶(PASS/PASS-SOFT/WARN/FAIL)", "庫可用;接 ENG074/ENG080 = 候"),
    ("PriceAdjustment 還原價一致性/上漲空間", "庫可用;ENG080 已有除權息因子鏈(不疊床)"),
]


def gap(do_print: bool = True) -> dict:
    E, why = load_intake()
    rep = {"verb": "gap", "state": "OK" if E is not None else "ABSENT", "why": why or f"{len(GAP_TABLE)} 模組補缺表", "rows": GAP_TABLE}
    if do_print:
        print(f"=== [via-fplogic gap] 收容件八模組 vs VRN 現況 · {rep['state']} · {rep['why'][:100]} ===")
        for a, b in GAP_TABLE:
            print(f"  [{'接' if b.startswith('已') else '候'}] {a} → {b}")
    return rep


def status(do_print: bool = True) -> dict:
    home = intake_home()
    ok, md = intake_md5_ok(home)
    R = roster()
    n_sc = len(list(FP_OUT.glob("*.json"))) if FP_OUT.exists() else 0
    last = None
    if (OUT / "LOGIC86_latest.json").exists():
        try:
            last = json.loads((OUT / "LOGIC86_latest.json").read_text(encoding="utf-8"))
        except Exception:
            last = None
    rep = {"verb": "status", "state": "OK" if home is not None and ok else "ABSENT", "intake": str(home) if home else None, "md5": md, "roster": R["how"],
           "sidecars": n_sc, "last": {k: last.get(k) for k in ("ts", "state", "n", "why")} if last else None,
           "why": f"收容件 {'在' if home else '缺'} {md} · 名冊 {R['how']} · ENG072 sidecar {n_sc} 件 · 最近 enrich {(last or {}).get('ts') or '尚未'}"}
    _emit(rep, do_print)
    return rep



# ---------------------------------------------------------------- 真報告語料(批536)
CORPUS_GLOB = "AttachmentFixedOutput_v*_b*"
CORPUS_SUB = "01_repair/documents"


def corpus_home() -> Path | None:
    """收容件 AttachmentFixedOutput 尾版的 documents 夾(唯讀;零觸碰)。"""
    hits = sorted(p for p in INTAKE_ROOT.glob(CORPUS_GLOB) if p.is_dir())
    for h in reversed(hits):
        for inner in sorted(h.glob("AttachmentFixedOutput_v*")):
            d = inner / CORPUS_SUB
            if d.is_dir():
                return d
        d = h / CORPUS_SUB
        if d.is_dir():
            return d
    return None


def _orig_name(stem: str) -> str:
    """`003_20251204兆豐個股報告-志強-KY(6768).pdf` → 原檔名(去掉序號前綴)。"""
    m = re.match(r"^\d{2,4}_(.+)$", stem)
    return m.group(1) if m else stem


TP_ZH = {"HIT": "命中", "NA_DECLARED": "報告自述 n.a.", "ABSENT_IN_TEXT": "文字無此欄", "NOT_STOCK": "非個股(不需)", "MISS": "有線索抓不到(RED)"}
DATE_ZH = {"HIT": "命中", "ABSENT": "檔名無日期", "MISS": "有數字解不出(RED)"}
RATING_ZH = {"HIT": "命中", "NA_NO_TOKEN": "文中無評等字樣", "NOT_STOCK": "非個股(不需)", "MISS": "有字樣抓不到(RED)"}


def _fmt_states(d: dict, zh: dict | None = None) -> str:
    """把分格計數印成誠實一行:`命中 30 · 報告自述 n.a. 2 · 文字無此欄 16 · 有線索抓不到(RED) 0`。"""
    order = list((zh or {}).keys()) or sorted(d)
    keys = [k for k in order if k in d] + [k for k in sorted(d) if k not in order]
    return " · ".join(f"{(zh or {}).get(k, k)} {d[k]}" for k in keys) or "無"


def corpus(args: list, do_print: bool = True) -> dict:
    E, why = load_intake()
    rep = {"schema": "VIA.FirstPageLogic86.corpus.v1", "verb": "corpus", "ts": _dt.datetime.now().isoformat(timespec="seconds"),
           "state": "ABSENT", "why": why, "n": 0}
    if E is None:
        _emit(rep, do_print)
        return rep
    home = corpus_home()
    if home is None:
        rep.update(state="NODATA", why=f"語料收容件缺:{INTAKE_ROOT / CORPUS_GLOB}/{CORPUS_SUB}")
        _emit(rep, do_print)
        return rep
    limit = int(_arg(args, "--limit", "0") or 0)
    files = sorted(home.glob("*.txt"))
    if limit:
        files = files[:limit]
    R = roster()
    tf = make_tf(E, R["codes"], R["names"])
    rows, methods, types = [], {}, {}
    n_b = n_r = n_tp = n_date = n_r_na = 0
    tp_states, date_states, broker_hows, rating_states = {}, {}, {}, {}   # 批537 誠實四態/三態/證據分級的分格計數
    for f in files:
        name = _orig_name(f.stem)                      # `003_x.pdf.txt` → `x.pdf`
        try:
            body = f.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            rows.append({"file": name, "state": "FAIL", "why": f"{type(exc).__name__}"})
            continue
        lay, _lay_how = layout_index()                 # 批536 LAYOUT 工具:有版面用版面
        li = lay.get(name) or {}
        head = "\n".join(x for x in (li.get("header") or "", "\n".join(body.splitlines()[:12])) if x)   # 版面標題 + 前段(相加;沒有版面就只有前段)
        body = nlp_normalize(body)                     # 批536 NLP 工具:過 ENG066 樞紐(缺=直通,誠實)
        head = nlp_normalize(head)
        try:
            r = analyze_one(E, tf, name, head, "", body, "")
        except Exception as exc:
            rows.append({"file": name, "state": "FAIL", "why": f"{type(exc).__name__}: {str(exc)[:70]}"})
            continue
        m = r["ticker"]["method"]
        methods[m] = methods.get(m, 0) + 1
        types[r.get("doc_type")] = types.get(r.get("doc_type"), 0) + 1
        n_b += 1 if r["broker"] else 0
        n_r += 1 if r["rating"].get("canonical") else 0
        if not r["rating"].get("canonical") and not r["rating"].get("text_has_token"):
            n_r_na += 1
        n_tp += 1 if r["target_price"]["value"] is not None else 0
        n_date += 1 if r["filename_fields"].get("date") else 0
        ts = tp_state(head + "\n" + body, r["target_price"]["value"])
        if ts != "HIT" and not r["ticker"]["ticker"]:
            ts = "NOT_STOCK"          # 批537:沒有單一代碼的產業/晨會報告本來就不該有目標價(真抓到就還它 HIT)
        ds = date_state(name, r["filename_fields"].get("date"))
        bh = r.get("broker_how") or "無"
        rs = rating_state(r["rating"].get("canonical"), bool(r["rating"].get("text_has_token")), bool(r.get("expects_ticker")))
        rating_states[rs] = rating_states.get(rs, 0) + 1
        tp_states[ts] = tp_states.get(ts, 0) + 1
        date_states[ds] = date_states.get(ds, 0) + 1
        broker_hows[bh] = broker_hows.get(bh, 0) + 1
        rows.append({"file": name, "state": "OK", "chars": len(body),
                     "ticker": r["ticker"]["ticker"], "method": m, "broker": r["broker"],
                     "rating": r["rating"].get("canonical"), "rating_how": r["rating"].get("how"),
                     "rating_token_in_text": r["rating"].get("text_has_token"), "rating_state": rs, "tp": r["target_price"]["value"],
                     "broker_how": bh, "tp_state": ts, "date": r["filename_fields"].get("date"), "date_state": ds,
                     "doc_type": r.get("doc_type"), "expects_ticker": r.get("expects_ticker"),
                     "xv": r["xv_filename_vs_page"]["verdict"]})
    n = sum(1 for r in rows if r["state"] == "OK")
    OUT.mkdir(parents=True, exist_ok=True)
    want = [r for r in rows if r.get("expects_ticker")]
    got = [r for r in want if r.get("ticker")]
    nowant = [r for r in rows if r["state"] == "OK" and not r.get("expects_ticker")]
    rep.update(state="OK" if n else "FAIL", n=n, errors=len(rows) - n, source=str(home), roster=R["how"],
               tools={"券商同義字 SSOT": ssot_brokers()[1], "LAYOUT": layout_index()[1], "NLP 樞紐": nlp_hub()[1]},
               methods=methods, doc_types=types, ticker_expected=len(want), ticker_hit=len(got),
               ticker_not_expected=len(nowant), broker_hit=n_b,
               rating_hit=n_r, rating_na_no_token=n_r_na, tp_hit=n_tp, date_hit=n_date, rows=rows,
               broker_evidence=broker_hows, tp_states=tp_states, date_states=date_states, rating_states=rating_states,
               red=tp_states.get("MISS", 0) + date_states.get("MISS", 0) + rating_states.get("MISS", 0),
               why=(f"{n} 份真研報(修復文字;原 PDF 不在本境)· 個股報告代碼 {len(got)}/{len(want)}"
                    f"(另 {len(nowant)} 份產業/晨會/市場/策略類本來就無單一代碼)"
                    f" · 券商 {n_b}/{n}(證據 {_fmt_states(broker_hows)})"
                    f" · 評等 {_fmt_states(rating_states, RATING_ZH)}"
                    f" · 目標價 {_fmt_states(tp_states, TP_ZH)} · 檔名日期 {_fmt_states(date_states, DATE_ZH)}"))
    (OUT / "CORPUS_latest.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    md = ["# VRN 第一頁邏輯 · 真報告語料實測(批536)", "",
          f"來源:`{home}`(收容件唯讀;操作員 C:\\測試樣本報告 那批的修復文字)", "",
          f"**{rep['why']}**", "", "| 檔 | 代碼 | 法 | 券商 | 證據 | 評等 | 等態 | 目標價 | 價態 | 檔名日期 | 期態 | 互核 |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        md.append(f"| {r['file'][:46]} | {r.get('ticker') or '-'} | {r.get('method') or r.get('why', '')[:20]} | "
                  f"{r.get('broker') or '-'} | {r.get('broker_how') or '-'} | {r.get('rating') or '-'} | "
                  f"{RATING_ZH.get(r.get('rating_state'), r.get('rating_state') or '-')} | "
                  f"{r.get('tp') if r.get('tp') is not None else '-'} | {TP_ZH.get(r.get('tp_state'), r.get('tp_state') or '-')} | "
                  f"{r.get('date') or '-'} | {DATE_ZH.get(r.get('date_state'), r.get('date_state') or '-')} | {r.get('xv') or '-'} |")
    (OUT / "CORPUS_latest.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    if do_print:
        print(f"=== [via-fplogic corpus] 真報告語料 · {rep['state']} · {rep['why']} ===")
        print(f"  [來源] {home}")
        for k, v in (rep.get("tools") or {}).items():
            print(f"  [工具] {k:<14} {v}")
        for r in rows[:14]:
            print(f"  [{r['state']:<4}] {r['file'][:44]:<44} {r.get('ticker') or '-':<5} {r.get('method') or '':<16} "
                  f"{r.get('broker') or '-':<12} {r.get('rating') or '-':<5} {r.get('tp') if r.get('tp') is not None else '-'}")
        print(f"  [四態] 評等   {_fmt_states(rating_states, RATING_ZH)}")
        print(f"  [四態] 目標價 {_fmt_states(tp_states, TP_ZH)}")
        print(f"  [三態] 檔名日期 {_fmt_states(date_states, DATE_ZH)}")
        print(f"  [證據] 券商 {_fmt_states(broker_hows)}")
        print(f"  [紅燈] 真 RED(有線索卻抓不到)= {rep['red']}")
        print(f"  [產物] {OUT}/CORPUS_latest.json · CORPUS_latest.md")
    return rep

def _arg(args: list, key: str, default=None):
    if key in args and args.index(key) + 1 < len(args):
        return args[args.index(key) + 1]
    return default


def _emit(rep: dict, do_print: bool) -> None:
    if not do_print:
        return
    print(f"=== [via-fplogic {rep.get('verb')}] 第一頁邏輯補缺正主橋 · {rep['state']} · {str(rep.get('why', ''))[:170]} ===")
    for it in (rep.get("items") or [])[:12]:
        print(f"  [{it.get('state'):<4}] {it.get('stem', '')[:44]:<44} 代碼 {it.get('ticker') or '-'}({it.get('method') or it.get('why', '')[:30]}) 券商 {it.get('broker') or '-'} 評等 {it.get('rating') or '-'} 目標價 {it.get('tp') if it.get('tp') is not None else '-'}")
    if rep.get("out_dir"):
        print(f"  [產物] {rep['out_dir']}/<stem>.logic86.json + LOGIC86_latest.json(append-only)")


# ---------------------------------------------------------------- 自測
def selftest() -> int:
    import tempfile
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    home = intake_home()
    ok, md = intake_md5_ok(home)
    _, _ir1 = intake_import_ok(home)
    chk("① 收容件在位(尾版 glob)且 md5 對冊(零觸碰)", home is not None and ok,
        f"({home.name if home else '缺'} {md})" + (intake_restore_hint(_ir1) if not ok else ""))
    E, why = load_intake()
    chk("② importlib 載入收容件:TickerFilename/BrokerRatingDict/FieldValidation/CrossValidation/FinancialValidation/FirstPageEngine 齊", E is not None, why)
    if E is None:
        print(f"  [計] 二十檢 OK {20 - len(fails) - 18} · FAIL {len(fails) + 18}(收容件缺,後十八檢略)")
        return 1
    tf = make_tf(E, {"3706", "2330", "6873"}, {"台積電": "2330", "神達": "3706", "泓德能源": "6873"})
    fn1 = "【國泰證期研究部】神達(3706 TT)-初次評等買進(+30.4_)-大顯神威，營運騰達-20250822.pdf"
    ff1 = filename_fields(E, tf, fn1)
    r1 = tf.resolve(fn1)
    chk("③ 真檔名:代碼 3706(FILE_SUFFIX 「3706 TT」)· 日期 2025-08-22 · 券商 CATHAY(VIA 補冊「國泰證期」)", r1["ticker"] == "3706" and r1["method"] == "FILE_SUFFIX" and ff1["date"] == "2025-08-22" and ff1["broker"] == "CATHAY", f"({r1['method']} {ff1['date']} {ff1['broker']})")
    r2 = tf.resolve("20250819兆豐個股報告-泓德能源(6873).pdf")
    r3 = tf.resolve("2025 台積電 研究報告.pdf", title="台積電(2330 TT)", body="")
    r4 = tf.resolve("半導體產業展望 2025.pdf")
    r5 = tf.resolve("2025 台積電.pdf", title="台積電 法說會重點", body="")
    ff5 = filename_fields(E, tf, "凱基投顧-1140822-台積電.pdf")
    chk("④ 階梯:FILE_BARE 6873 · 年段 2025 不當代碼→TITLE_SUFFIX 2330 · 產業檔=SECTOR · 名→碼 TITLE_SYNONYM 2330 · 民國 7 碼 1140822→2025-08-22 · 兆豐=SSOT 正典 MEGABANK",
        r2["ticker"] == "6873" and r2["method"] == "FILE_BARE" and r3["ticker"] == "2330" and r3["method"] == "TITLE_SUFFIX" and r4["is_sector"] and r5["ticker"] == "2330" and r5["method"] == "TITLE_SYNONYM"
        and ff5["date"] == "2025-08-22" and ff5["broker"] == "KGI" and filename_fields(E, tf, "20250819兆豐個股報告-泓德能源(6873).pdf")["broker"] in ("MEGABANK", "MEGA"),
        f"({r2['method']} {r3['method']} {r4['method']} {r5['method']} {ff5['date']})")
    naive = E.BrokerRatingDict()
    chk("⑤ 券商防呆(收容件 broker_normalize 子字串撞詞;橋側詞界):earnings guidance→None(收容件會說 GOLDMAN)· 凱基投顧→KGI · Goldman Sachs→SSOT 正典 GOLDMANSACHS · 獨立 MS→MORGANSTANLEY · terms→None · capital expenditure→None",
        naive.broker_normalize("earnings guidance") in ("GOLDMAN", "GOLDMANSACHS") and safe_broker("earnings guidance", E) is None and safe_broker("凱基投顧 研究部", E) == "KGI"
        and safe_broker("Goldman Sachs Equity Research", E) in ("GOLDMANSACHS", "GOLDMAN") and safe_broker("MS Research 2330", E) == "MORGANSTANLEY" and safe_broker("terms of use", E) is None
        and safe_broker("capital expenditure rose", E) is None and safe_broker("Capital Securities Corp", E) == "CAPITAL")
    chk("⑥' 批540 獨立短行要**整行等於**別名:「外資持有比重上升」(8 字含「持有」)不得判成 HOLD;「持有」自成一行才算",
        safe_rating("\n".join(["x"] * 3) + "\n外資持有比重上升", E)["canonical"] is None
        and safe_rating("台積電\n持有\n目標價 900", E)["canonical"] == "HOLD"
        and safe_rating("台積電\nBuy\n目標價 900", E)["canonical"] == "BUY",
        f"(誤判句={safe_rating(chr(10).join(['x'] * 3) + chr(10) + '外資持有比重上升', E)['canonical']})")
    chk("⑥ 評等防呆:buyback 計畫→None(收容件會說 BUY)· 評等:買進→BUY · Rating: Overweight→BUY · holdings 30%→None · 維持中立(線索)→HOLD · 獨立短行「賣出」→SELL",
        naive.rating_normalize("buyback 計畫") == "BUY" and safe_rating("庫藏股 buyback 計畫", E)["canonical"] is None and safe_rating("投資評等:買進 目標價 1,250", E)["canonical"] == "BUY"
        and safe_rating("Rating: Overweight", E)["canonical"] == "BUY" and safe_rating("holdings 30% of assets", E)["canonical"] is None
        and safe_rating("建議:中立", E)["canonical"] == "HOLD" and safe_rating("台積電\n賣出\n目標價 900", E)["canonical"] == "SELL")
    tp1, how1 = safe_target_price("目標價:NT$1,250 元(前 1,100)", E)
    tp2, how2 = safe_target_price("Target Price NT$ 1,300 ; current 1,000", E)
    tp3, _ = safe_target_price("營收 NT$ 12,345 百萬", E)
    tp4, _ = safe_target_price("目標價 4441 公司訪談", E, exclude_code="4441")
    tp5, _ = safe_target_price("TP 1 頁", E)
    tp6, _ = safe_target_price("HTTP 200 ok", E)
    fv = E.FieldValidation()
    v = fv.validate_target_price(1250.0, per=20, eps=62.5, current=1000.0, fin=E.FinancialValidation())
    chk("⑦ 目標價:線索詞優先(目標價/Target Price/TP/PT 詞界)1250/1300;無線索退收容件弱正則(營收 NT$ 會誤中=標「弱」)· 目標價旁四碼=代碼不算 · 單碼不算 · HTTP 不算 · 合理性 TP=PER×EPS PASS · 上漲 25% sane",
        tp1 == 1250.0 and how1 == "目標價線索" and tp2 == 1300.0 and v["verdict"] == "PASS" and any(c["name"] == "upside_sane" and c["ok"] for c in v["checks"])
        and tp4 is None and tp5 is None and tp6 is None, f"({tp1} {tp2} 弱={tp3} 代碼旁={tp4} 單碼={tp5} HTTP={tp6})")
    xv = E.CrossValidation()
    a = xv.filename_vs_page({"ticker": "2330", "broker": "KGI", "date": "2025-08-22"}, {"ticker": "2330", "broker": "KGI", "date": "2025-08-22"})
    b = xv.filename_vs_page({"ticker": "2330", "broker": "KGI", "date": None}, {"ticker": "2317", "broker": None, "date": None})
    z = xv.zone_presence([1250, "BUY"], ["句一", "句二"])
    chk("⑧ 互核:三欄同=PASS · 代碼異=FAIL(缺欄=None 不判)· 區在不在 PASS", a["verdict"] == "PASS" and b["verdict"] == "FAIL" and b["fields"]["broker"]["match"] is None and z["verdict"] == "PASS")
    with tempfile.TemporaryDirectory() as td:
        T = Path(td)
        sc = T / "in"
        sc.mkdir()
        raw = json.dumps({"header": "凱基投顧 研究部 台積電(2330 TT) 投資評等:買進 目標價:NT$1,250", "right": "analyst@kgi.com.tw 02-2181-8888", "body": "台積電第二季營收年增 30%。毛利率 58%。", "footer": "免責聲明", "tables": []}, ensure_ascii=False)
        (sc / "凱基投顧-20250822-台積電(2330).json").write_text(raw, encoding="utf-8")
        (sc / "壞件.json").write_text("{not json", encoding="utf-8")
        rep = enrich(["--in", str(sc), "--out", str(T / "out")], do_print=False)
        j = json.loads((T / "out" / "凱基投顧-20250822-台積電(2330).logic86.json").read_text(encoding="utf-8"))
        same = (sc / "凱基投顧-20250822-台積電(2330).json").read_text(encoding="utf-8") == raw
    chk("⑨ enrich:ENG072 sidecar → .logic86.json(代碼 2330 FILE_BARE · 券商 KGI · 評等 BUY · 目標價 1250 · email 驗 KGI 網域 · 檔名×首頁 PASS)· 壞件計 errors 不炸 · 來源 sidecar 位元零變(append-only)",
        rep["state"] == "OK" and rep["n"] == 1 and rep["errors"] == 1 and j["ticker"]["ticker"] == "2330" and j["broker"] == "KGI" and j["rating"]["canonical"] == "BUY"
        and j["target_price"]["value"] == 1250.0 and j.get("email_validation", {}).get("domain_broker") == "KGI" and j["xv_filename_vs_page"]["verdict"] == "PASS" and same,
        f"({rep['why'][:80]})")
    mail = "Jentech Precision (3653 TT)\nhelen.chien@daiwacm-cathay.com.tw\nSource: FactSet, Daiwa forecasts"
    b_strip, how_strip = safe_broker_ev(mail, E)
    b_mail, how_mail = safe_broker_ev("neil.teng@daiwacm-cathay.com.tw", E, allow_contacts=True)
    b_none, _ = safe_broker_ev("neil.teng@daiwacm-cathay.com.tw", E)
    chk("⑪ 批537 券商證據分級:分析師信箱網域不是文內證據(daiwacm-cathay → 去電郵後 DAIWA 系,不再判成 CATHAY)· 只剩電郵時標「弱」· 去電郵後無證據=None",
        b_strip is not None and b_strip != "CATHAY" and how_strip == "文內" and b_mail is not None and how_mail == "電郵網域(弱)" and b_none is None,
        f"({b_strip}/{how_strip} 弱={b_mail}/{how_mail} 去電郵={b_none})")
    chk("⑫ 批537 目標價誠實四態:抓到=HIT · 報告自述「Target price: n.a.」=NA_DECLARED(不是漏抓)· 通篇無目標價字樣=ABSENT_IN_TEXT · 有線索卻無數字=MISS(真 RED)",
        tp_state("目標價:1250", 1250.0) == "HIT" and tp_state("Target price: n.a.\nShare price 2,470", None) == "NA_DECLARED"
        and tp_state("September revenue of NT$14,503mn", None) == "ABSENT_IN_TEXT" and tp_state("目標價 待定", None) == "MISS",
        f"({tp_state('Target price: n.a.', None)} {tp_state('營收 NT$1,000', None)} {tp_state('目標價 待定', None)})")
    chk("⑬ 批537 檔名日期誠實三態:20251204=HIT · `6933_AMAX-KY_個股介紹報告.pdf` 無六碼數字=ABSENT(不是漏解)· 有八碼卻解不出=MISS(真 RED)",
        date_state("Daiwa-3653 20251002.pdf", "2025-10-02") == "HIT" and date_state("6933_AMAX-KY_個股介紹報告.pdf", None) == "ABSENT"
        and date_state("第三場 AI潮流下展望2026半導體產業趨勢 - 陳子昂.pdf", None) == "ABSENT" and date_state("報告99999999.pdf", None) == "MISS")
    tf2 = make_tf(E, {"2891", "3665"}, None)          # 批537:**空名冊**(本境庫是空殼)——否決要靠文內/檔名相鄰,不靠庫
    kgi = analyze_one(E, tf2, "凱基投顧_2891 中信金_施志鴻_20260519.pdf",
                      "動態更新金融 ‧ 台灣中信金(2891.TW/2891 TT)", "",
                      "增加持股‧維持收盤價 May 19 (NT$)\n55.40\n12 個月目標價 (NT$)\n63.00", "")
    chk("⑭ 批537 標的否決(空名冊也要成立)+ 本土評等尺度:`凱基投顧_2891 中信金_…` 內文只有「中信金」(標的公司名)→ 不判 CTBC,退檔名層得 KGI · 凱基寫「增加持股」= BUY",
        kgi["broker"] == "KGI" and kgi["broker_how"] == "檔名" and kgi["rating"]["canonical"] == "BUY" and kgi["target_price"]["value"] == 63.0
        and subject_names("台灣中信金(2891.TW/2891 TT)", "凱基投顧_2891 中信金_施志鴻_20260519.pdf", "2891") >= {"中信金"},
        f"({kgi['broker']}/{kgi['broker_how']} {kgi['rating']['canonical']} {kgi['target_price']['value']})")
    chk("⑮ 批537 評等誠實四態:抓到=HIT · 產業/市場報告沒有單一評等=NOT_STOCK · 個股但文中無評等字樣=NA_NO_TOKEN · 個股有字樣卻抓不到=MISS(真 RED)· 「外資持有」在內文不當評等",
        rating_state("BUY", True, True) == "HIT" and rating_state(None, True, False) == "NOT_STOCK"
        and rating_state(None, False, True) == "NA_NO_TOKEN" and rating_state(None, True, True) == "MISS"
        and rating_local_scale("\n".join(["x"] * 60) + "\n外資持有比重上升") is None
        and rating_local_scale("重申貿聯「增加持股」評等")["canonical"] == "BUY")
    cf = broker_conflicts(E)
    tbl_k = set(broker_tables(E))
    chk("⑯' 批541 去衝突:合併三張券商表後**零撞名**(同一別名不得對到多個正典名)· CLSA=CLST 同一家(操作員裁定,CLST 已併入)"
        "· 讓位規則不看鍵在不在補冊(舊規則的洞讓 JPMORGAN 永遠 pop 不掉)",
        cf["n"] == 0 and "CLSA" in tbl_k and "CLST" not in tbl_k and "JPMORGAN" not in tbl_k,
        f"(撞名 {cf['n']}{':' + str(cf['rows'][:3]) if cf['rows'] else ''} · 家數 {len(tbl_k)})")
    src = Path(__file__).read_text(encoding="utf-8").split("def selftest")[0]
    chk("⑩ 律:零網路 · 收容件零觸碰(每一處 write_text 的目標都在產物夾 OUT/out_dir,絕不寫收容件)· 產物夾與 ENG072 分開(first_page_logic)· 名冊只讀(read_only=True)· 檔名 .logic86.json",
        all(("import " + k) not in src for k in ("requests", "httpx", "urllib")) and "read_only=True" in src and 'VIA / "VIA_Reports" / "first_page_logic"' in src
        and ".logic86.json" in src and "INTAKE_ROOT" in src
        and all(re.search(r"\(OUT\s*/|out_dir\s*/|\(T\s*/", ln) for ln in src.splitlines() if ".write_text(" in ln)
        and not re.search(r"(INTAKE_ROOT|home|corpus_home\(\))[^\n]*\.write_text", src))
    iok, ir = intake_import_ok()
    chk("⑱ 批541 收容件**導入**驗證(操作員令「加這個檢查導入」):位元錨寫死在碼裡(檔案=錨=冊 三方一致,"
        "冊被改寫也騙不過)· 真的 exec_module 導得進來(不是「看得到就算」)· 冊上宣告的 11 個模組一個不少",
        iok, f"(錨 {ir['anchor']} · 冊 {ir['manifest']} · 導入 {ir['import']} · 模組 {ir['symbols']}"
             f"{' 缺 ' + '、'.join(ir['missing']) if ir['missing'] else ''})"
             + (intake_restore_hint(ir) if not iok else ""))
    # ⑱ 負控:把「檔案與冊一起被換掉」這件事真的做一次(做在產物夾的沙盒裡,收容件零觸碰)。
    # 只驗位元、只對同資料夾的冊,這一關會綠;有錨才擋得住——所以這裡斷言它**必須**是紅的。
    tamper = None
    try:
        import shutil as _sh
        sb = OUT / "_selftest_intake_tamper"
        if sb.exists():
            _sh.rmtree(sb)
        sb.mkdir(parents=True, exist_ok=True)
        src = intake_engine_file(intake_home())
        body = src.read_bytes() + b"\n# tampered\n"
        (sb / INTAKE_ANCHOR["name"]).write_bytes(body)
        (sb / "_INTAKE_MANIFEST_fake.json").write_text(json.dumps(
            {"schema": "VIA.IntakeManifest.v1", "files": [
                {"name": INTAKE_ANCHOR["name"], "bytes": len(body),
                 "md5": hashlib.md5(body).hexdigest(),
                 "sha256": hashlib.sha256(body).hexdigest()}]},
            ensure_ascii=False), encoding="utf-8")
        old_md5_ok, _ = intake_md5_ok(sb)          # 舊那一檢:檔案對冊 → 自洽 → 綠(這就是它的弱點)
        tamper_ok, _tr = intake_import_ok(sb)      # 新那一檢:對的是碼裡的錨 → 紅
        tamper = (old_md5_ok, tamper_ok)
        _sh.rmtree(sb, ignore_errors=True)
    except Exception as exc:
        tamper = ("ERR", f"{type(exc).__name__}")
    chk("⑱' ⑱ 的負控:把收容件與冊**一起**換掉(沙盒內;收容件零觸碰)——舊的 md5 對冊檢會照樣給綠(自洽),"
        "⑱ 必須亮紅。擋不住這一手的檢查,綠燈只是自己對自己點頭",
        tamper == (True, False), f"(舊檢 {tamper[0]} · ⑱ {tamper[1]})")
    # ⑲ 批545:按名字取錨檔把引擎救回正軌了,但夾裡那個多出來的檔**還在**——
    # 如果就這樣讓 ①⑱ 轉綠,等於把汙染掃到地毯下(正本零觸碰只剩一句口號)。
    # 所以分開講:引擎吃對了(①⑱ 綠)· 夾子不乾淨(⑲ 紅),兩件事各自有各自的燈。
    _files = intake_files()
    _man = sorted((intake_home() or Path(".")).glob("_INTAKE_MANIFEST_*.json"))
    _reg = set()
    if _man:
        try:
            _reg = {x.get("name") for x in (json.loads(_man[-1].read_text(encoding="utf-8")).get("files") or [])}
        except Exception:
            _reg = set()
    _extra = [x["name"] for x in _files if x["name"] not in _reg]
    chk("⑲ 批545 收容件夾只能有冊上點名的檔:多一個排在後面的同系列檔,舊的 `sorted(glob)[-1]` 就會把它當正典"
        "(而它多半未追蹤,git checkout 還救不回來)。錨檔改**按名字取**之後引擎吃對了,但夾子髒不髒要另外講",
        not _extra,
        f"(夾內 {len(_files)} 個 · 冊上 {len(_reg)} 個"
        + (f" · **多出來** {'、'.join(_extra)} ← 未追蹤的話請自行挪走" if _extra else " · 零多餘") + ")")
    print(f"  [計] 二十檢 OK {20 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 第一頁邏輯補缺正主橋(VRN_ENG086 v0107)· 二十檢自測(零網路;收容件 FirstPageEngine v0101 _b522)===")
        return selftest()
    verb = args[0] if args and not args[0].startswith("--") else "status"
    if verb == "status":
        return 0 if status()["state"] == "OK" else 1
    if verb == "gap":
        return 0 if gap()["state"] == "OK" else 1
    if verb == "bench":
        return 0 if bench(args[1:])["state"] == "OK" else 1
    if verb == "enrich":
        return 0 if enrich(args[1:])["state"] == "OK" else 1
    if verb == "corpus":
        return 0 if corpus(args[1:])["state"] == "OK" else 1
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
