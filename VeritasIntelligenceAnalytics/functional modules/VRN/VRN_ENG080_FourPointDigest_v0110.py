#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 批641:本檔頭改 r"""——v0106 的說明裡引了 `\s` `\$` `\d` 三個正規式片段,
#   非 raw 的 docstring 一帶反斜線,py3.12 就把 SyntaxWarning 印到操作員終端
#   (CGC_MDL168 C 轉義道當場咬住;LL231 新閘上線第一件事是拿它掃自己)。
r"""
v0109→v0110(批730 操作員 2026-09-24 令「自測實測自AUDIT直到完工 結果也要實測正確性」):
  **報告日因子的分母用錯了價**(與 ENG073 v0138 同一個洞,同一把尺修)。拿交易所日成交表 tw_trading_daily
  當獨立對照:Yahoo 的 close 會**事後按配股 / 拆股回頭調整**(容器 13.6% 列、796/893 檔對不上交易所),
  所以 adj_close ÷ close 只含現金股利。而且只有配股的股票 adj/close 比值不會變,舊碼「期間沒偵測到因子變動
  就把因子當 1」——**目標價一分都不調**。
  v0110:報告日那一列的分母改用交易所原始收盤(`factor_basis` = RAW_EXCHANGE;交易所缺才用 Yahoo close,
  具名 YAHOO_CLOSE);Yahoo close ÷ 交易所 close ≠ 1(`retro_ratio`)本身就算一次股本事件,因子照乘。
  `f = factor_report / factor_latest` 那一行一字不動(㉗ 照釘);Z156 的「推不出因子時拿原始目標價算」仍候操作員裁。
  +㉛ 配股回調(1294 形:交易所 126.5 · Yahoo 95.7617)。
  **修正(同批實測):** 拿同一批真庫樣本對 ENG073 v0138,293 筆裡 287 筆同答;差的 6 筆全是本支自己多留的那一份算法:
  沒有 Yahoo 單日陳價的平滑、沒有「沒調到的公司行動」防呆(4950 減資 ×2.6185 被算成 −23.8%)、取報告日當天那列
  (L99 是「報告日前一交易日」;除權息日剛好是報告日就少乘一次)。改成**因子與事件一律向 ENG073 要**(`_eng073()`,
  尾版;同一件事一處算,LL404/L05),本支只接結果;ENG073 缺席才退本地算法並寫進 factor_basis。事件 → EVENT_UNADJUSTED、
  不給因子、K1 上漲空間未算。報告頁面印的現價一併帶過去(交易所缺時當分母,同 ENG073)。+㉜。
v0108→v0109(批685 操作員令「標題一開始之公司名稱加括號代碼…第一點標題 台積電(2330.TW)-本文標題」)
  量過:headline 一直是「標題:」標籤句或 title_head 原句,**沒有**名(代號.TW)前綴——操作員同日上傳的整合引擎
  (收容 _b685)也沒有:它的 ReportTitle 只取首頁前 12 行第一句。v0109 只加一層組字 compose_headline():
    名 = vrn_report_basic.name_official(缺 → MDL142 名冊 name_of;再缺 → 不編)
    代號.TW/.TWO 只認名冊 / tw_listings 查得到市場的票(**查不到不盲猜 .TW**——盲猜就是發明,改用裸碼)
    標題已含代號(「緯創(3231.TW) 維持買進」)= 原句不動;名已在標題裡 = 在名後補代號,不重複;名/代號皆缺 = 原句。
  grounded 旗標語意不變(仍只看標題出處);組上去的代號列入 derived,免得 novel numbers 把它當成報告裡沒有的數字;
  headline_fmt 加欄落庫(只增不減)。三十檢 +㉚。
v0107→v0108(批643 ① 我在批642 把真缺料叫成垃圾 ② 41 份的調整態是空字串)

  ① **更正批642。** 我寫「81→71 掉的 10 份全是自測留在正式夾的空殼」——**8 份錯了**。
     那 8 份 `rep_0X` 的 sidecar 裡,ENG072 早就寫好了:
         tag  = `NEEDS_OCR[…tesseract 本境不就緒且 OCR 境缺…]`
         why  = 「本件無版面幾何(WORD/影像/OCR/pypdf 道);header/right 留空是**誠實**,不是抽失敗」
     我只看了「字數 0」就判它是垃圾,**沒讀引擎自己寫在旁邊的那一欄**。
     這不是小事:把誠實缺料叫成垃圾,跟假綠同一種傷——垃圾會被清掉,缺料要被補。
     零正文 8 份實際上是 **VRN 的 OCR 缺口**(容器無 tesseract),是可補的真料。
     v0108 的漏斗改成**讀引擎自己的 tag**分類:NEEDS_OCR / 其他,不再一律叫空殼。
     (真正人造的只有 2 份:`2330_synthetic_20260101`、`VRN_Meeting_Minutes`,而且它們有字、不在零正文裡。)

  ② **`adjust_method` 有 41 份是空字串,那不是態。**
     `price_context` 在「票不在價表」與「價表無 adj_close」兩個出口直接 return,
     `adjust_method` 始終沒被設值,落庫就是 `''`。
     而 `''` 跟 `NONE`(有價、查過、確認期間無除權息)在庫裡看起來都不是可篩的東西,
     意思卻完全相反。v0108 補兩個誠實態:`NO_PRICE` / `NO_ADJ_CLOSE`。
     (同 LL207 的反面:那邊是加了態沒接 rc,這邊是**少了態,缺口只好借空字串站著**。)

  ③ **操作員令(批643):「有目標價過了除權息都要改成 ADJ CLOSE,跟目前的 ADJ CLOSE 更新計算目標價」。**
     量過:這條**既有實作已經成立**——`f = factor_report / factor_latest`、
     事件日由因子變動偵測、`tp_adj = tp × f`、上漲空間對 `adj_close`(最新日)算。
     而且價表 892 檔的**最新日因子全部 = 1**(最新日 2026-09-18),adj 基準就是「目前」,沒有混時點。
     所以這一批做的不是改邏輯,是**把它釘成律**(L99)+ 加一道檢,免得以後被人改掉。
     真正的瓶頸不在這裡:46 份裡只有 5 份有價,所以只有 4 份走得到因子鏈——**根在 VDF 價表涵蓋**。

v0106→v0107(批642 **被濾掉的那 25 份,報告上一個字都沒有**)
  量:容器 71 份入庫研報,本件只做了 46 份——因為第 709 行那句
  `WHERE ticker IS NOT NULL AND ticker <> ''` **安靜地濾掉 25 份**,
  而摘要只印「報告 46」。讀的人看不出有沒有東西掉了,更看不出掉的是什麼。

  掉的是什麼,一查就清楚(不是猜的):
      無票號 25 份的 report_kind = 產業 10 · 大盤晨報 7 · 海外 3 · 研討會 3 · **未分類 2**
      有票號 46 份的 report_kind = **個股 46,百分之百**
  所以那 23 份不是擷取失敗,是**這種報告本來就沒有單一個股代號**——
  一份大盤晨報沒有 ticker 是對的,不是漏的。剩下 2 份「未分類」才是真的不知道。

  v0107 把分母印出來,而且**分三態不分兩態**:
    · 個股 → 做文摘(照舊)
    · 非個股 → `NOT_APPLICABLE`,依據**既有正本** `VRN_MatrixApplicability_SSOT`(批633 NA-01),
      本件不自己判型別(LL133 判定器不自判;那本冊缺席就一律當「適用」,**不假造 N/A**)
    · 型別空/未分類 → `NODATA`。**不知道型別 ≠ 不適用**——批633 在矩陣那邊踩過這一步,
      把空型別當成「不是個股」,整欄被判成不適用。這裡不重蹈。
  另印 sidecar 漏斗(81 → 還原 81 → 入庫 71 → 個股 46 → 文摘 46),
  並點名**零正文的 sidecar**:容器裡有 8 份 `rep_0X` 是自測留下來的空殼(字數 0),
  它們讓每一個「幾份」的數字都虛胖。**只點名不刪**——刪不刪是操作員的事。

v0105→v0106(批641 操作員批636 原令未接完:「不刪除修正好本文輸出,**再根據修正好的輸出進行 SUMMARIZE**」)
  批636–640 把本文還原做完了(ENG085,工作站 105 份保全率 100.00%),但**下游沒有接**——
  ENG080 至今仍只讀 ENG072 的原稿 zones,還原過的那一份沒人吃。這一批把它接上,並且**先量再接**。

  量出來的三件事(容器 81 份真料,不是 fixture):
  ① **樞紐 34 vs 自家 13。** 本件的 `extract_target_price` 是一條手寫 regex,
     `目標價[:：]?\s*(?:NT\$|新台幣)?\s*([\d,]+…)` —— 遇到 `目標價:$345` 就啞了($ 不在它的選項裡)。
     而正本樞紐 `SUP_MDL749.tp_of`(帶 LL64 幅度守衛、代碼排除、加寬線索)同一批料抓到 34 份。
     **這是第二顆頭**(批554/558 已經在 ENG073 拔過同一顆)。v0106 改為向樞紐要,
     樞紐缺席才退回自家 regex,而且**退回這件事要寫進 tp_how 落庫**(LL209:退路不得悄悄換尺)。
  ② **還原文對評等 +3(36→39),對目標價持平。** 誠實說法:還原的價值是那份**讀得懂的 .md**
     (操作員要的就是那個),不是讓欄位抽得更多。只有 `rating_of` 這種「只看前 N 行」的尺
     會因為行結構變好而多抓到 3 份。不誇大。
  ③ **`first_page` 的 48 行截斷是個錯的尺。** 本件的料來自 `first_page_text`——
     依定義**整份就是第一頁**(ENG072 只抽第一頁)。再砍 48 行是純損失:
     還原文 81 份裡有 38 份被砍掉,平均少 155 字,**當場掉一個目標價**(樞紐 34→29)。
     v0106:**欄位抽取用不截行的 scan**,敘事兩點(K3/K4)仍走原本的 48 行 page ——
     `remainder_two` 行為逐字不變(只增不減;自家 regex 量到 13→13 零改判)。

  · `_load_text` 補 `footer` 鍵。批558 在 ENG073 修過同一個缺鍵,**這一支沒跟著修**。
    容器裡 81 份只有 2 份 footer 有字(共 43 字),抽取零改變——誠實記:
    這是**一致性修**,不是「修好了什麼」。操作員機 105 份是 NODATA。
  · 新欄(加欄式,舊庫照讀):text_src / tp_how / tp_prev / tp_direction / rating / rating_how。

VRN_ENG080_FourPointDigest v0100 — 研報「一題四點」文摘+潛在上漲空間(目標價除權息調整)引擎(批386)
====================================================================
操作員令(批386;Grok 主控台 VRN 契約接回母倉):
  「1. 潛在上漲空間(用最新 adj close 去算),目標價 xxx 元,評價方式 xxx,基於 xxx
    2. n~n+3 diluted eps,yoy xxx,主要原因 xxx
    3. 4. 將第一頁其餘本文部分整合成兩點不受限」
  +「如果報告時間在除權息前,目標價也必須除權息調整」。
契約(一標題 + 四點;DIGEST 五槽存 K1–K5,K5 風險可空;quote-or-abstain;不發明、不平均):
  headline 標題:標籤 標題:/核心結論: 原句(缺=title_head 檔頭/未提及)
  K1 潛在上漲空間:目標價(報告正文 目標價: 優先 > vrn_report_basic.target_price=VRN_SSOT;多值列示不平均)
     × 最新 adj close(tw_daily_prices 該檔最後交易日;缺=上漲空間未算,不拿 close/共識頂替)
     除權息調整律:報告日 < 除權息日 ≤ 最新日 → 目標價同口徑後向復權:
       TP_adj = TP × F,F = (adj_close/close)@報告日(≤報告日最近交易日)÷(adj_close/close)@最新日
       (= 後向因子鏈;因子變動日=除權息事件,逐日列示;母倉無配息事件表=價表因子推定,誠實標 method)
     上漲空間_now = (TP_adj − adj_latest)/adj_latest;另存 批240 報告時上漲 upside_at_report(TP÷報告前日 close;ENG073)
     評價方式 評價方式:/PE/本益比/EV/EBITDA/PB/DCF/SOTP 原句;基於 基於: 原句;缺=未提及
  K2 稀釋 EPS n～n+3:vrn_report_metrics EPS(REPORT_ESTIMATE 不冒充 OFFICIAL)> 正文 20xx EPS 規則;YoY 只在前後年皆有數且底≠0
     (底 0=NOT_COMPUTABLE_ZERO_BASE;轉盈/轉虧標態);主要原因 主要原因: 原句
  K3/K4 首頁其餘甲/乙:首頁前 48 行去已用標籤行,對半拆兩點,原文不限長
  K5 風險:風險: 原句;缺=未提及(可空=通過,不發明)
  QC:novel numbers=文摘出現而來源(正文∪TP∪價∪EPS 冊)沒有的數字 → RED;衍生數(TP_adj/上漲%/YoY)標 derived 不計
落庫:vrn_four_point_digest(派生層重算=同 report_file DELETE+INSERT;ENG073 同例)+ VIA_Reports/vrn/four_point/DIGEST_latest.json/.html(零 CDN)
律:只增不減;原件零觸碰(ENG072 sidecar/ENG073 表/價表唯讀);誠實三態;零網路;尾版律;Adjusted 與原始不混用(交接 05.4)。
用法:python3 VRN_ENG080_FourPointDigest_v0100.py run [--db PATH] [--zones DIR] [--ticker 2330] [--limit N] [--json]
      | show <ticker|report_file> | --selftest
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
import html
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
MEGA = VIA / "functional modules" / "VDF" / "output_hub" / "mega"
DB_TW = MEGA / "vdf_tw_market.duckdb"


def _resolve_db(db=None):
    r"""批447:主庫路徑要探**替根**(與 ENG073 `_resolve_db`、ENG074、
    首頁引擎 `_alt_root`、MDL139 `mega_db` 同律)。

    工作站實錄(批446 之後鏈第一次跑到第四段):
        [via-vrn4] RED · 報告 0 · 庫缺 …\OneDrive\…\mega\vdf_tw_market.duckdb
    而**同一次跑**的 ENG073/ENG074 都印「主路徑缺→改用替根庫」並寫進
    59 列 basic、7,024 列財報值。批443→批446 的同一課,這是**第三支**:
    庫就在那裡,是這支引擎沒去找;而它 rc=1 直接把鏈停在最後一段。
    """
    if db is not None:
        return Path(db)
    # 批490 資料家優先(與 ENG073 v0124 同律;啟動層放進 env,引擎按名取路徑,不寫死)
    _env_db = os.environ.get("VIA_DB_VDF_TW_MARKET")
    if _env_db and Path(_env_db).exists():
        print(f"[庫解析] 資料家目錄頁→{_env_db}")
        return Path(_env_db)
    _home = os.environ.get("VIA_DATA_HOME")
    if _home and Path(_home).exists():
        _hp = Path(_home)
        try:
            _hits = [_hp] if (_hp.is_file() and _hp.name == "vdf_tw_market.duckdb") else \
                    [x for x in _hp.rglob("vdf_tw_market.duckdb")] if _hp.is_dir() else []
            if _hits:
                _best = max(_hits, key=lambda x: x.stat().st_mtime)
                print(f"[庫解析] 資料家 {_hp} 內尋獲 {len(_hits)} 本,用最新的:{_best}")
                return _best
        except Exception:
            pass
    cands = [DB_TW]
    try:
        home = Path.home()
        rel = Path("movies-dataset/VeritasIntelligenceAnalytics/functional modules"
                   "/VDF/output_hub/mega/vdf_tw_market.duckdb")
        cands += [home / "Downloads" / rel, home / rel]
    except Exception:
        pass
    for c in cands:
        try:
            if c.exists():
                if c != DB_TW:
                    print(f"[庫解析] 主路徑缺→改用替根庫:{c}(誠實提示)")
                return c
        except Exception:
            continue
    return DB_TW          # 全缺=回主路徑,讓呼叫端照原樣報「庫缺 <主路徑>」
ZONES_DIR = VIA / "VIA_Reports" / "first_page_text"
#: 批641:ENG085 還原層產出。**操作員批636 令的「修正好的輸出」就是這一夾。**
RESTORED_DIR = VIA / "VIA_Reports" / "vrn" / "markdown"
REPORTS = VIA / "VIA_Reports" / "vrn" / "four_point"
TABLE = "vrn_four_point_digest"
SLOTS = [("headline", "標題"), ("K1", "潛在上漲空間"), ("K2", "稀釋EPS n～n+3"), ("K3", "首頁其餘甲"), ("K4", "首頁其餘乙"), ("K5", "風險因子")]
USED_LABEL = re.compile(r"^(標題|核心結論|目標價|評價方式|基於|主要原因|券商|日期|風險)[:：]")
#: 批641:HTML 註解。ENG085 的 .md 用它記來源/類別/頁數——是**後設說明,不是報告正文**。
#: 不剝掉的實測後果:檔名 `…20250819` 會被 EPS 正規式讀成「2025 年 EPS 819 元」,
#: 一口氣多出 22 份假 EPS。先量到才知道要剝(這就是為什麼尺要先用真料校)。
MD_COMMENT_RX = re.compile(r"<!--.*?-->", re.S)
MD_TABLE_SEP_RX = re.compile(r"^\s*\|?\s*:?-{3,}")


def md_to_plain(md: str) -> str:
    """ENG085 還原 .md → 純文字。**留行、去記號**:行結構正是還原層的價值,不能一併壓掉。"""
    out = []
    for ln in MD_COMMENT_RX.sub("", str(md or "")).splitlines():
        s = ln.rstrip()
        if MD_TABLE_SEP_RX.match(s):
            continue                                   # |---|---| 對齊列不是內容
        s = re.sub(r"^\s{0,3}#{1,6}\s*", "", s)         # 標題記號
        s = re.sub(r"^\s{0,3}>\s?", "", s)             # 引言記號(其他/頁首/右欄/頁尾)
        if s.startswith("|"):
            s = " ".join(c.strip() for c in s.strip("|").split("|"))
        if s.strip():
            out.append(s)
    return "\n".join(out)


#: 批642:報告型別 × 欄位「適不適用」的正本(批633 立)。**本件不自己判型別。**
APPLICABILITY = "VRN_MatrixApplicability_SSOT_v*.json"
_APPLY_CACHE: list = []


def applicability() -> dict | None:
    """適用性正本。缺席=None → 呼叫端一律當「適用」,**不假造 N/A**(那本冊自己的紀律第三條)。"""
    if _APPLY_CACHE:
        return _APPLY_CACHE[0]
    out = None
    try:
        hits = sorted((VIA / "supportive modules" / "registry").glob(APPLICABILITY))
        if hits:
            out = json.loads(hits[-1].read_text(encoding="utf-8"))
    except Exception:
        out = None
    _APPLY_CACHE.append(out)
    return out


def _yf_known(code: str, con) -> str:
    """批685:只回名冊/tw_listings 查得到市場的票;查不到回 ""(不盲猜 .TW=不發明)。"""
    code = str(code or "").strip()
    if not code:
        return ""
    if YF_TW.match(code):
        return code
    hits = _tickers_for(code, con, blind=False)
    return hits[0] if hits else ""


def _name_known(code: str) -> str:
    """批685:名只認 MDL142 名冊(缺席=空,不編)。"""
    code = str(code or "").strip()
    if not code:
        return ""
    _nb, _why = _namebook()
    if _nb is None:
        return ""
    try:
        return str(_nb.name_of(code) or "")
    except Exception:
        return ""


def ticker_na(report_kind: str, book: dict | None) -> tuple:
    """(是否不適用, 理由)。依 NA-01:`report_kind_not_in` 命中才算不適用。

    **型別是空的就回 NODATA,不回 N/A。**不知道型別 ≠ 不適用——
    批633 在矩陣那邊正是這樣把一整欄誤判成不適用的。
    """
    k = str(report_kind or "").strip()
    if not k or k in ("未分類", "UNKNOWN"):
        return False, "NODATA:型別未定(不知道型別 ≠ 不適用)"
    if not book:
        return False, "NODATA:適用性正本缺席(不假造 N/A)"
    for r in book.get("rules", []):
        if r.get("column") != "ticker":
            continue
        no = r.get("not_applicable_when", {}).get("report_kind_not_in")
        if isinstance(no, list) and k not in no:
            return True, f"{r.get('id', 'NA-?')}:{k} 非 {'/'.join(no)},本欄不適用"
    return False, f"NODATA:{k} 在適用範圍內卻沒有代號"


_HUB_CACHE: list = []


def _hub():
    """SUP_MDL749 規則樞紐。缺席=誠實 None(呼叫端退回自家 regex,並把退回寫進 tp_how)。"""
    if _HUB_CACHE:
        return _HUB_CACHE[0]
    mod = None
    try:
        import importlib.util as _ilu
        d = VIA / "supportive modules" / "70_VRN_Rules"
        hits = sorted(d.glob("SUP_MDL749_VRNFieldRuleHub_v*.py"))   # 尾版律
        if hits:
            sp = _ilu.spec_from_file_location("SUP_MDL749_VRNFieldRuleHub", hits[-1])
            mod = _ilu.module_from_spec(sp)
            sys.modules.setdefault("SUP_MDL749_VRNFieldRuleHub", mod)
            sp.loader.exec_module(mod)
    except Exception:
        mod = None
    _HUB_CACHE.append(mod)
    return mod


_E73_CACHE: list = []


def _eng073():
    """批730 修正:L99 的因子與「沒調到的公司行動」一律向 ENG073(尾版)要——`_prev_basis`(前一交易日、交易所分母、
    單日不一致取前後一致值、代號尾碼)與 `_unadjusted_events`。同一件事一處算(LL404/L05),本支只接結果。
    缺席=誠實 None(呼叫端退回本地算法,並把退回寫進 factor_basis)。"""
    if _E73_CACHE:
        return _E73_CACHE[0]
    mod = None
    try:
        import importlib.util as _ilu
        hits = sorted(HERE.glob("VRN_ENG073_ReportStructuredDB_v*.py"))   # 尾版律
        if hits:
            sp = _ilu.spec_from_file_location("_vrn_eng073_for_eng080", hits[-1])
            mod = _ilu.module_from_spec(sp)
            sys.modules[sp.name] = mod
            sp.loader.exec_module(mod)
            if not all(hasattr(mod, k) for k in ("_prev_basis", "_unadjusted_events", "RETRO_SAME")):
                mod = None                        # v0137 以前沒有這三樣 = 當缺席
    except Exception:
        mod = None
    _E73_CACHE.append(mod)
    return mod
NUM_RX = re.compile(r"-?\d+(?:\.\d+)?%?")
FACTOR_EPS = 1e-6
YF_TW = re.compile(r"^\d{4}[A-Z0-9]{0,2}\.(TW|TWO)$")


# ---------------------------------------------------------------- 文本規則(Grok digest-four 契約逐條移植)
def grab(text: str, rx: str) -> str:
    m = re.search(rx, text, flags=re.M)
    return (m.group(1).strip()[:180]) if m else ""


def extract_target_price_local(text: str) -> float | None:
    """v0105 的自家 regex,原封不動保留為**退路**(樞紐缺席才用;用了要寫進 tp_how)。"""
    m = re.search(r"目標價[:：]?\s*(?:NT\$|新台幣)?\s*([\d,]+(?:\.\d+)?)\s*元?", text)
    if not m:
        return None
    try:
        v = float(m.group(1).replace(",", ""))
        return v if v > 0 else None
    except ValueError:
        return None


def extract_target_price(text: str, exclude_code: str | None = None) -> tuple:
    """目標價 →(值, 出處)。**正本在樞紐**(L30 一個出處);樞紐缺席才退自家 regex。

    容器 81 份真料:樞紐 34 / 自家 13。差距全在自家那條 regex 讀不到的寫法
    (`目標價:$345`、`合理價`、`Target Price`、`目標區間`…)。
    """
    h = _hub()
    if h is not None:
        try:
            v, how = h.tp_of(text, exclude_code=exclude_code)
            if v is not None:
                return float(v), f"樞紐·{how}"
        except Exception as e:                       # 樞紐壞掉不得吃掉整份文摘
            v = extract_target_price_local(text)
            return (v, f"自家regex(樞紐拋錯:{type(e).__name__})") if v is not None else (None, f"樞紐拋錯:{type(e).__name__}")
        v = extract_target_price_local(text)
        return (v, "自家regex(樞紐無值)") if v is not None else (None, "樞紐無值·自家亦無")
    v = extract_target_price_local(text)
    return (v, "自家regex(樞紐缺席)") if v is not None else (None, "樞紐缺席·自家亦無")


def extract_rating(text: str) -> tuple:
    """評等 →(正規詞, 出處)。正本在樞紐;樞紐缺席=誠實 (None, 原因),**本件不自寫詞表**。"""
    h = _hub()
    if h is None:
        return None, "樞紐缺席"
    try:
        r = h.rating_of(text)
    except Exception as e:
        return None, f"樞紐拋錯:{type(e).__name__}"
    if isinstance(r, dict) and r.get("canonical"):
        return str(r["canonical"]), f"樞紐·{r.get('rule') or r.get('how') or 'rating_of'}"
    return None, "樞紐無值"


def extract_tp_pair(text: str) -> tuple:
    """前次→本次 目標價 →(prev, direction)。正本在樞紐 `tp_pair`(批634 操作員規格)。"""
    h = _hub()
    if h is None:
        return None, ""
    try:
        d = h.tp_pair(text)
    except Exception:
        return None, ""
    if isinstance(d, dict) and d.get("prev") is not None:
        return float(d["prev"]), str(d.get("direction") or "")
    return None, ""


def extract_val_method(text: str) -> str:
    v = grab(text, r"評價方式[:：]\s*(.+)")
    if v:
        return v
    m = re.search(r"([^\n。]*?(?:本益比|P/E|PE|EV/EBITDA|P/B|PB|DCF|SOTP|殖利率|股價淨值比)[^\n。]*)", text)
    return m.group(1).strip()[:180] if m else ""


def extract_basis(text: str) -> str:
    return grab(text, r"基於[:：]\s*(.+)")


def extract_reason(text: str) -> str:
    return grab(text, r"主要原因[:：]\s*(.+)")


def extract_risk(text: str) -> str:
    return grab(text, r"風險(?:因子|因素)?[:：]\s*(.+)")


def extract_eps_years(text: str) -> list:
    out, seen = [], set()
    for m in re.finditer(r"(20[2-3]\d)\s*[EF]?\s*[:：|]?\s*(?:稀釋)?(?:每股盈餘|EPS)?\s*(-?[\d]+(?:\.\d+)?)", text, flags=re.I):
        y, v = int(m.group(1)), float(m.group(2))
        if y not in seen:
            seen.add(y)
            out.append({"year": y, "eps": v, "src": "正文"})
    return sorted(out, key=lambda r: r["year"])


def first_page(text: str, max_lines: int = 48) -> str:
    """頁界切分。`max_lines=0` = 不再砍行(批641)。

    **為什麼要有 0 這個選項**:本件的料來自 `first_page_text`,依定義整份就是第一頁
    (ENG072 只抽第一頁),真正的頁界是下面那條 `re.split`。再砍 48 行是多的一把尺,
    而且會咬到**行結構被還原層改過**的文字——容器 81 份裡 38 份被砍,當場掉一個目標價。
    預設值保持 48:`remainder_two`(K3/K4 敘事兩點)照舊,只增不減。
    """
    cut = re.split(r"\f|\n頁\s*2\b|\n-{3,}\n", text)[0]
    return cut if max_lines <= 0 else "\n".join(cut.splitlines()[:max_lines])


def remainder_two(text: str) -> tuple[str, str]:
    page = first_page(text)
    keep = [ln.strip() for ln in page.splitlines()]
    keep = [ln for ln in keep if ln and not USED_LABEL.match(ln) and not re.match(r"^20[2-3]\d\s+稀釋", ln) and not ln.startswith("|")
            and not re.match(r"^[-:|\s]+$", ln) and not ln.startswith("科目")]
    if not keep:
        return "", ""
    mid = (len(keep) + 1) // 2
    return " ".join(keep[:mid]), " ".join(keep[mid:])


def fmt_pct(v: float) -> str:
    return f"{v * 100:.1f}%"


def _round2(x: float) -> float:
    """四捨五入至 2 位(half-up;避免 165×0.985=162.525 二進位誤差落 162.52)"""
    from decimal import Decimal, ROUND_HALF_UP
    return float(Decimal(repr(round(x, 9))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def upside(target: float, current: float) -> float | None:
    return None if not current else (target - current) / current


def yoy(cur: float, base: float) -> dict:
    if base == 0:
        return {"state": "NOT_COMPUTABLE_ZERO_BASE", "value": None}
    v = (cur - base) / abs(base)
    if base < 0 < cur:
        return {"state": "TURNAROUND_TO_PROFIT", "value": v}
    if base > 0 > cur:
        return {"state": "TURNAROUND_TO_LOSS", "value": v}
    if base < 0 and cur < 0:
        return {"state": "NEG_TO_NEG_ANNOTATED", "value": v}
    return {"state": "NORMAL", "value": v}


def novel_numbers(summary: str, source: str, derived: list | None = None) -> list:
    allow = {n.replace(",", "") for n in NUM_RX.findall(source)}
    for d in derived or []:
        allow |= {n.replace(",", "") for n in NUM_RX.findall(str(d))}
    out = []
    for n in NUM_RX.findall(summary):
        n2 = n.replace(",", "")
        if n2 not in allow and n2.rstrip("%") not in allow and n2 not in out:
            out.append(n2)
    return out


# ---------------------------------------------------------------- 價表:最新 adj close 與除權息調整因子
def _namebook():
    """批470:名稱正典冊 CGC_MDL142(尾版 glob)。缺席回 (None, 因由)。"""
    try:
        import importlib.util as _ilu
        c = sorted((VIA / "supportive modules" / "registry")
                   .glob("CGC_MDL142_TWNameBook_v*.py"))
        if not c:
            return None, "CGC_MDL142_TWNameBook_v*.py 缺席"
        sp = _ilu.spec_from_file_location("mdl142_eng080", c[-1])
        m = _ilu.module_from_spec(sp)
        sp.loader.exec_module(m)
        return m, ""
    except Exception as exc:
        return None, f"MDL142 載不進 {type(exc).__name__}:{str(exc)[:50]}"


def _tickers_for(code: str, con, blind: bool = True) -> list:
    """裸碼 → 價表票。

    批470(全景分析照出來):v0103 只查 `tw_listings`——那張表**只有 891 列而且
    不含 2330 / 2454 / 3008 / 1101**(實測)。權值股一律查不到 yf_ticker,
    於是只能退到盲試 `.TW/.TWO`;盲試碰上上櫃股就先試錯一次,而真正的成本是
    **看不出來**:它不會報錯,只是價表對不上,最後顯示成「adj —@—、上漲未算」,
    看起來像沒有價格資料,其實是**票號從一開始就沒查對**。
    正典冊 MDL142 已把 tw_listings_industry(1,978 列,含 yf_ticker 與 market)
    與落盤、全名表收成一本 → 先問它;冊缺席才退回本檔原本的 tw_listings 直查
    (零回歸),最後仍保留 .TW/.TWO 盲試作最終退路。
    """
    if YF_TW.match(code):
        return [code]
    cands = []
    _nb, _nb_why = _namebook()
    if _nb is not None:
        try:
            row = _nb.book().get(str(code).strip()) or {}
            yf = str(row.get("yf") or "").strip()
            mk = str(row.get("market") or "").strip().upper()
            if yf:
                cands.append(yf)
            elif mk:
                cands.append(code + (".TW" if mk == "TWSE" else ".TWO"))
        except Exception:
            pass
    try:
        have = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
        if not cands and "tw_listings" in have:
            cols = {r[0].lower() for r in con.execute('DESCRIBE "tw_listings"').fetchall()}
            if "yf_ticker" in cols:
                r = con.execute("SELECT yf_ticker FROM tw_listings WHERE code = ? AND yf_ticker IS NOT NULL", [code]).fetchone()
                if r and r[0]:
                    cands.append(str(r[0]))
            elif "market" in cols:
                r = con.execute("SELECT market FROM tw_listings WHERE code = ?", [code]).fetchone()
                if r and r[0]:
                    cands.append(code + (".TW" if str(r[0]).upper() == "TWSE" else ".TWO"))
    except Exception:
        pass
    # 去重但**保留順序**:正典票排第一,盲試只當最終退路(blind=False 時不盲試=查不到就空)。
    out, seen = [], set()
    for x in cands + ([code + ".TW", code + ".TWO"] if blind else []):     # 批685:blind=False 不盲試
        if x and x not in seen:
            seen.add(x)
            out.append(x)
    return out


# ===== 批419:K1 兩道閘(操作員 37 份真文摘實證) ==========================
# 工作站真跑 37 份文摘,兩件事一眼可見:
#   ① 三份的 TP/價比是 0.020 / 0.019 / 0.005(MS-2308 / MS-8210 / JP-3653)——
#      目標價只有股價的 1/50 到 1/200。沒有分析師會發 -98% 的目標價,
#      那是**抽錯的數**(EPS、倍數、或外幣價)。把它印成「潛在上漲空間 -98.0%」
#      比不印更糟:讀的人會以為那是預測。
#   ② 37 份全部拿 **2026-09-07 的價**比,但 Daiwa-1319 是 **2023-10-11** 的報告
#      (距今 1062 天)。拿三年後的價去算三年前報告的「潛在上漲空間」,
#      算出來的不是上漲空間,是**事後看圖**。18 份逾 180 天。
# 兩道閘都**不刪任何數字**:照列,但講白它是什麼、不許它冒充預測。
TP_SANITY_LO, TP_SANITY_HI = 0.2, 5.0     # 目標價/現價 的合理帶(=上漲 -80%～+400%)
STALE_DAYS = 180                          # 報告距價格基準日超過這麼久=非當期比較


def tp_sanity(tp_adj, price) -> tuple[str, float | None]:
    """目標價合理性。回 (態, 比值)。
    OK=在帶內;TP_SUSPECT=帶外(疑為擷取誤判);NA=算不了。
    為什麼是 flag 不是丟棄:我們**不知道**哪個數字才對,丟棄等於替操作員決定;
    照列並標明可疑,他一眼就知道要去翻哪三份 PDF。"""
    try:
        if tp_adj is None or not price:
            return "NA", None
        r = float(tp_adj) / float(price)
    except (TypeError, ValueError, ZeroDivisionError):
        return "NA", None
    return ("OK" if TP_SANITY_LO <= r <= TP_SANITY_HI else "TP_SUSPECT"), r


def basis_age(report_date: str, adj_date: str) -> int | None:
    """報告日到價格基準日的天數;算不出=None(不猜)。"""
    from datetime import date
    try:
        a = date(*(int(x) for x in str(report_date)[:10].split("-")))
        b = date(*(int(x) for x in str(adj_date)[:10].split("-")))
    except (TypeError, ValueError):
        return None
    return (b - a).days


def basis_state(days: int | None) -> str:
    """CURRENT=當期(比得有意義)· STALE_BASIS=非當期 · UNKNOWN=日期缺。"""
    if days is None:
        return "UNKNOWN"
    return "CURRENT" if days <= STALE_DAYS else "STALE_BASIS"


def price_context(con, code: str, report_date: str | None, page_price=None) -> dict:
    """最新 adj close + 報告日因子 + 因子鏈(除權息事件=因子變動日)。
    批730 修正:報告日因子與未調整事件向 ENG073 要(`_eng073()`);page_price = 報告頁面印的現價(交易所缺時當分母,同 ENG073)。"""
    out = {"ticker": "", "adj_date": "", "adj_close": None, "close_latest": None, "factor_latest": None, "factor_report": None,
           "report_px_date": "", "adjust_factor": None, "ex_dates": [], "adjust_method": "", "adjust_note": ""}
    have = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
    if "tw_daily_prices" not in have:
        out["adjust_method"] = "NO_PRICE_TABLE"
        out["adjust_note"] = "價表 tw_daily_prices 缺"
        return out
    cols = {r[0].lower() for r in con.execute('DESCRIBE "tw_daily_prices"').fetchall()}
    has_adj = "adj_close" in cols
    for t in _tickers_for(code, con):
        r = con.execute("SELECT CAST(date AS VARCHAR), close" + (", adj_close" if has_adj else ", NULL") +
                        " FROM tw_daily_prices WHERE ticker = ? AND close IS NOT NULL ORDER BY date DESC LIMIT 1", [t]).fetchone()
        if r:
            out["ticker"] = t
            out["adj_date"], out["close_latest"] = r[0], float(r[1])
            out["adj_close"] = float(r[2]) if r[2] is not None else None
            break
    if not out["ticker"]:
        # 批643:原本這裡不設 adjust_method,落庫就是 `''`——而 `''` 跟 NONE 意思完全相反
        #   (NONE = 有價、查過、確認期間無除權息)。容器 46 份裡 41 份卡在這個出口。
        out["adjust_method"] = "NO_PRICE"
        out["adjust_note"] = "該檔不在價表(上漲空間未算;不拿共識/close 頂替)"
        return out
    if out["adj_close"] is None:
        out["adjust_method"] = "NO_ADJ_CLOSE"
        out["adjust_note"] = "價表無 adj_close(上漲空間未算;不拿 close 頂替=Adjusted 與原始不混用)"
        return out
    out["factor_latest"] = out["adj_close"] / out["close_latest"] if out["close_latest"] else None
    if not report_date:
        out["adjust_method"] = "NONE"
        out["adjust_note"] = "報告日缺=不除權息調整(目標價照列)"
        return out
    e73 = _eng073()
    if e73 is not None:
        # 批730 修正:前一交易日(L99「報告日前一交易日」;v0110 初版取報告日當天那列,除權息日剛好是報告日就少乘一次)
        _pb = e73._prev_basis(con, code, report_date, page_price=page_price)
        rp = (_pb["factor_date"], _pb["close"], _pb["adj"]) if _pb.get("factor") is not None else None
        if rp:
            out["report_raw_close"], out["factor_basis"], out["retro_ratio"] = _pb["raw"], _pb["basis"], _pb["retro"]
            out["report_px_date"], out["factor_report"] = rp[0], _pb["factor"]
        retro_eps = e73.RETRO_SAME
    else:
        rp = con.execute("SELECT CAST(date AS VARCHAR), close, adj_close FROM tw_daily_prices WHERE ticker = ? AND CAST(date AS VARCHAR) <= ? "
                         "AND close IS NOT NULL AND close > 0 AND adj_close IS NOT NULL ORDER BY date DESC LIMIT 1", [out["ticker"], report_date]).fetchone()
        retro_eps = 0.005
        if rp:
            # 本地算法(ENG073 缺席才走):分母用交易所原始收盤;Yahoo 的 close 會事後按配股回調,只能當後備(具名)
            raw_rp = None
            if "tw_trading_daily" in have:
                try:
                    _rr = con.execute("SELECT close FROM tw_trading_daily WHERE code = ? AND CAST(date AS VARCHAR) = ? AND close > 0",
                                      [re.sub(r"\.TWO?$", "", str(code)), rp[0]]).fetchone()
                    raw_rp = float(_rr[0]) if _rr and _rr[0] else None
                except Exception:
                    raw_rp = None                 # 表形不合=這條路沒有,退 Yahoo(具名)
            out["report_raw_close"] = raw_rp
            out["factor_basis"] = ("RAW_EXCHANGE" if raw_rp else "YAHOO_CLOSE") + "(ENG073 缺席:本地算法,報告日當天列、無單日平滑、無事件防呆)"
            out["retro_ratio"] = round(float(rp[1]) / raw_rp, 6) if raw_rp else None
            out["report_px_date"], out["factor_report"] = rp[0], float(rp[2]) / (raw_rp or float(rp[1]))
    if not rp:
        out["adjust_method"] = "NONE"
        out["adjust_note"] = f"報告日 {report_date} 前無價列=無法推定因子(目標價照列)"
        return out
    if not out["factor_latest"]:
        out["adjust_method"] = "NONE"
        out["adjust_note"] = "最新日因子缺"
        return out
    f = out["factor_report"] / out["factor_latest"]
    # 因子變動日=除權息/拆股事件(報告日 < 事件 ≤ 最新日)
    rows = con.execute("SELECT CAST(date AS VARCHAR), adj_close / close FROM tw_daily_prices WHERE ticker = ? AND CAST(date AS VARCHAR) >= ? "
                       "AND CAST(date AS VARCHAR) <= ? AND close > 0 AND adj_close IS NOT NULL ORDER BY date", [out["ticker"], rp[0], out["adj_date"]]).fetchall()
    ex = []
    prev = None
    for d, fac in rows:
        if prev is not None and fac is not None and abs(float(fac) - prev) > FACTOR_EPS:
            ex.append(d)
        prev = float(fac) if fac is not None else prev
    out["ex_dates"] = ex
    # 批730 修正:因子日到最新日之間有 Yahoo 沒調到的公司行動(減資 / 股本變動)→ 目標價與現價不在同一個股本基礎,
    #   **不給因子**(呼叫端就不算上漲空間);ENG073 同一支判官判 ADJ_EVENT_UNADJUSTED。v0110 初版沒有這道,
    #   4950(2025-11-03 減資 ×2.6185)會把 12 元的目標價直接對 15.75 元算出 −23.8%。
    _ev = e73._unadjusted_events(con, code, rp[0]) if e73 is not None else []
    if _ev:
        out["adjust_factor"] = None
        out["adjust_method"] = "EVENT_UNADJUSTED"
        out["adjust_note"] = (f"報告日 {report_date} 之後有 Yahoo 沒調到的公司行動 "
                              + " · ".join(f"{d} ×{r}({why})" for d, r, why in _ev[:3])
                              + ";目標價與現價不在同一個股本基礎,上漲空間不算(ENG073 同判 ADJ_EVENT_UNADJUSTED)")
        return out
    # 批730:Yahoo 回調比 ≠ 1 = 報告日之後有配股 / 拆股(adj/close 比值看不見它),本身就是一次事件
    retro_ev = out.get("retro_ratio") is not None and abs(out["retro_ratio"] - 1.0) > retro_eps
    if abs(f - 1.0) <= FACTOR_EPS or (not ex and not retro_ev):
        out["adjust_factor"] = 1.0
        out["adjust_method"] = "NONE"
        out["adjust_note"] = f"報告日 {report_date} 至 {out['adj_date']} 無除權息事件(因子 1)"
    else:
        out["adjust_factor"] = f
        out["adjust_method"] = "PRICE_FACTOR_CHAIN"
        out["adjust_note"] = (f"報告日 {report_date}(價列 {rp[0]} 因子 {out['factor_report']:.6f})→ 最新 {out['adj_date']}(因子 {out['factor_latest']:.6f});"
                              f"除權息事件 {len(ex)} 次 {','.join(ex[:5])}{'…' if len(ex) > 5 else ''};目標價 × {f:.6f}(後向復權同口徑;母倉無配息事件表=價表因子推定)")
        if retro_ev:
            out["adjust_note"] += (f";配股/拆股:Yahoo close 對交易所 {out['retro_ratio']:.4f}"
                                   f"(分母用交易所 {out['report_raw_close']} 元,{out['factor_basis']})")
    if abs(out["factor_latest"] - 1.0) > 1e-4:
        out["adjust_note"] += f";注意:最新日因子 {out['factor_latest']:.6f}≠1=adj 基準非最新(價表混抓時點),建議 via-hist 重抓/ENG060 重建"
    return out


# ---------------------------------------------------------------- 標題組字(批685)
def compose_headline(name: str, code: str, yf: str, title: str) -> tuple:
    """「名(代號.TW)-本文標題」。回 (headline, fmt)。
    fmt:NAME_CODE · NAME_ONLY · CODE_ONLY · TITLE_HAS_CODE(標題已含代號=原句)· NAME_IN_TITLE(名在標題裡=補代號)· TITLE_ONLY。
    不發明:名只認 name_official/名冊;.TW/.TWO 只認查得到的市場,查不到用裸碼。"""
    t = str(title or "").strip()
    name, code, yf = str(name or "").strip(), str(code or "").strip(), str(yf or "").strip()
    if not t or t == "未提及":
        return (t or "未提及"), "TITLE_ONLY"
    if code and code in t:
        return t, "TITLE_HAS_CODE"
    tag = yf or code
    if name and tag and name in t:
        return t.replace(name, f"{name}({tag})", 1), "NAME_IN_TITLE"
    if name and tag:
        return f"{name}({tag})-{t}", "NAME_CODE"
    if name:
        return f"{name}-{t}", "NAME_ONLY"
    if tag:
        return f"({tag})-{t}", "CODE_ONLY"
    return t, "TITLE_ONLY"


# ---------------------------------------------------------------- 單件文摘
def build_digest(text: str, basic: dict, metrics: list, px: dict) -> dict:
    page = first_page(text)                       # 敘事兩點(K3/K4)沿用 48 行:行為逐字不變
    scan = first_page(text, max_lines=0)          # 批641:欄位抽取不截行(見 first_page 註)
    title = grab(scan, r"(?:標題|核心結論)[:：]\s*(.+)")
    title_src = "正文標籤" if title else ""
    if not title and basic.get("title_head"):
        title, title_src = str(basic["title_head"])[:180], "檔頭(ungrounded)"
    head, head_fmt = compose_headline(basic.get("name_official") or "", basic.get("ticker") or "",
                                      basic.get("yf") or "", title or "")        # 批685:名(代號.TW)-本文標題
    body_tp, tp_how = extract_target_price(scan, exclude_code=basic.get("ticker"))
    rating, rating_how = extract_rating(scan)
    tp_prev, tp_direction = extract_tp_pair(scan)
    ssot_tp = basic.get("target_price")
    tp_raw = basic.get("target_price_raw") or ""
    tp = body_tp if body_tp is not None else (float(ssot_tp) if ssot_tp else None)
    tp_src = "報告正文" if body_tp is not None else ("VRN_SSOT" if tp else "")
    multi = f" · 列 {tp_raw} 不平均" if (body_tp is None and tp_raw and ";" in str(tp_raw)) else ""
    method, basis = extract_val_method(scan), extract_basis(scan)
    adj, adj_date = px.get("adj_close"), px.get("adj_date")
    tp_adj = None
    if tp is not None and px.get("adjust_factor"):
        tp_adj = _round2(tp * px["adjust_factor"])
    # 批730 修正:股本基礎不同(EVENT_UNADJUSTED)不生數字——不退回拿原始目標價算
    _blocked = px.get("adjust_method") == "EVENT_UNADJUSTED"
    up_now = upside(tp_adj if tp_adj is not None else tp, adj) if (tp is not None and adj and not _blocked) else None
    # 批419 兩道閘:合理性 + 基準日
    _tp_state, _tp_ratio = tp_sanity(tp_adj if tp_adj is not None else tp, adj)
    _days = basis_age(basic.get("report_date") or "", adj_date or "")
    _basis = basis_state(_days)
    k1, g1 = "未提及", False
    if tp is not None and adj and up_now is not None:
        adj_txt = f"(除權息調整 {px['adjust_factor']:.4f} → {tp_adj}元)" if px.get("adjust_method") == "PRICE_FACTOR_CHAIN" else ""
        rep_up = f" · 報告時上漲 {fmt_pct(float(basic['upside_at_report']))}(批240 TP÷報告前日 close)" if basic.get("upside_at_report") is not None else ""
        if _tp_state == "TP_SUSPECT":
            # 不假裝那是預測。照列兩個數字、講明比值,請人工去翻那份 PDF。
            k1 = (f"目標價疑為擷取誤判(不列為潛在上漲空間):目標價 {tp:g}元({tp_src})"
                  f" vs 最新 adj close {adj_date} {adj}元 → 比值 {_tp_ratio:.3f}"
                  f"(合理帶 {TP_SANITY_LO}–{TP_SANITY_HI});待人工核 PDF{adj_txt}{multi}")
        elif _basis == "STALE_BASIS":
            # 當期上漲空間算不得數:改把「報告時上漲」放頭,今日比值降為參考。
            head = (f"報告時上漲 {fmt_pct(float(basic['upside_at_report']))}(批240 TP÷報告前日 close)"
                    if basic.get("upside_at_report") is not None else "報告時上漲 未算(報告日前無價列)")
            k1 = (f"{head} · 非當期比較:報告距價格基準日 {_days} 天(>{STALE_DAYS}),"
                  f"今日 adj close {adj_date} {adj}元 對目標價 {tp:g}元({tp_src}) 為 {fmt_pct(up_now)}"
                  f"——僅供參考,不作潛在上漲空間{adj_txt}{multi}"
                  f" · 評價方式 {method or '未提及'} · 基於 {basis or '未提及'}")
        else:
            k1 = (f"潛在上漲空間 {fmt_pct(up_now)}(最新 adj close {adj_date} {adj}元 VDF 價表)· 目標價 {tp:g}元({tp_src}){adj_txt}{multi}"
                  f" · 評價方式 {method or '未提及'} · 基於 {basis or '未提及'}{rep_up}")
        g1 = True
    elif tp is not None:
        k1 = f"目標價 {tp:g}元({tp_src}){multi} · 上漲空間未算({px.get('adjust_note') or '該檔 adj close 不在 VDF 價表'})· 評價方式 {method or '未提及'} · 基於 {basis or '未提及'}"
        g1 = True
    # K2:EPS 冊(ENG073 metrics)優先,正文規則後備
    eps = []
    seen = set()
    for m in metrics:
        if not re.search(r"eps|每股盈餘", str(m.get("metric", "")), flags=re.I):
            continue
        ym = re.search(r"(20[2-3]\d)", str(m.get("period", "")))
        if not ym or m.get("value") is None:
            continue
        y = int(ym.group(1))
        if y not in seen:
            seen.add(y)
            eps.append({"year": y, "eps": float(m["value"]), "src": f"metrics:{m.get('status') or ''}"})
    for e in extract_eps_years(scan):
        if e["year"] not in seen:
            seen.add(e["year"])
            eps.append(e)
    eps.sort(key=lambda r: r["year"])
    reason = extract_reason(page)
    k2, g2, yoy_rows = "未提及", False, []
    if eps:
        n = eps[0]["year"]
        span = []
        for i in range(4):
            hit = next((e for e in eps if e["year"] == n + i), None)
            span.append(f"{hit['year']} {hit['eps']:g}" if hit else f"{n + i} 未提及")
        bits = []
        for i in range(1, len(eps)):
            y = yoy(eps[i]["eps"], eps[i - 1]["eps"])
            yoy_rows.append({"year": eps[i]["year"], **y})
            bits.append(f"{eps[i]['year']} YoY {y['state']}" if y["value"] is None else f"{eps[i]['year']} YoY {fmt_pct(y['value'])}" + ("" if y["state"] == "NORMAL" else f"({y['state']})"))
        k2 = f"稀釋EPS {'、'.join(span)} · {'；'.join(bits) or 'YoY 未算'} · 主要原因 {reason or '未提及'}"
        g2 = True
    a, b = remainder_two(page)                    # 48 行照舊
    risk = extract_risk(scan)
    points = {"headline": (head if title else "未提及", bool(title) and title_src == "正文標籤"), "K1": (k1, g1), "K2": (k2, g2),
              "K3": (a or "未提及", bool(a)), "K4": (b or "未提及", bool(b)), "K5": (risk or "未提及", bool(risk))}
    n0 = eps[0]["year"] if eps else 0
    derived = [tp_adj, fmt_pct(up_now) if up_now is not None else "", px.get("adjust_factor"), adj, adj_date, tp, tp_raw, "批240",
               str(basic.get("ticker") or ""), str(basic.get("yf") or ""),      # 批685:自己組上去的代號不是報告裡沒有的數字
               fmt_pct(float(basic["upside_at_report"])) if basic.get("upside_at_report") is not None else "",
               f"{px.get('adjust_factor') or 0:.4f}", *[f"{e['eps']:g}" for e in eps], *[e["year"] for e in eps], *[n0 + i for i in range(4)],
               *[fmt_pct(r["value"]) for r in yoy_rows if r["value"] is not None], *[str(basic.get("target_price") or "")], f"{tp:g}" if tp is not None else "",
               # 批419b(我自己造的回歸):批419 的兩道閘會在 K1 印出**閘門自己的診斷值**——
               # 比值(0.020)、合理帶界(0.2 / 5.0)、天數(1062)。那些不是「報告裡的宣稱」,
               # 是**關於擷取的後設說明**,拿 novel numbers 去查它們等於要求閘門的判準
               # 也要出現在報告正文裡,無理。工作站實錄:MS-2308/MS-8210/JP-3653 三份因此
               # QC 紅、vrn_fourpoint rc=1,整段鏈被自己的診斷訊息判死。
               f"{_tp_ratio:.3f}" if _tp_ratio is not None else "", str(TP_SANITY_LO), str(TP_SANITY_HI),
               str(_days) if _days is not None else "", str(STALE_DAYS)]
    novel = novel_numbers(" ".join(v[0] for v in points.values()), text + " " + (basic.get("raw_all") or ""), derived)
    return {"headline": points["headline"][0], "headline_fmt": head_fmt, "points": {k: {"zh": zh, "text": points[k][0], "grounded": points[k][1]} for k, zh in SLOTS},
            "tp": tp, "tp_src": tp_src, "tp_raw": tp_raw, "tp_adj": tp_adj, "adjust_factor": px.get("adjust_factor"), "adjust_method": px.get("adjust_method"),
            "adjust_note": px.get("adjust_note"), "ex_dates": px.get("ex_dates") or [], "adj_close": adj, "adj_date": adj_date, "px_ticker": px.get("ticker"),
            "upside_now": up_now, "upside_at_report": basic.get("upside_at_report"), "method": method, "basis": basis, "eps": eps, "yoy": yoy_rows,
            # 批419:兩道閘的態一併落庫,U/I 與統計才判得出哪幾份的上漲空間可信
            "tp_state": _tp_state, "tp_ratio": _tp_ratio, "basis_state": _basis, "basis_days": _days,
            # 批641:出處一律落庫。**退回自家 regex 也要看得見**(LL209:退路不得悄悄換尺)
            "tp_how": tp_how, "rating": rating, "rating_how": rating_how,
            "tp_prev": tp_prev, "tp_direction": tp_direction,
            "novel_numbers": novel, "qc": "RED" if novel else ("GREEN" if all(v[1] for k, v in points.items() if k != "K5") else "YELLOW")}


# ---------------------------------------------------------------- 落庫/報告
def _ensure_table(con) -> None:
    con.execute(f"""CREATE TABLE IF NOT EXISTS {TABLE}(
        report_file VARCHAR, ticker VARCHAR, px_ticker VARCHAR, broker VARCHAR, report_date VARCHAR, asof_date VARCHAR,
        headline VARCHAR, k1 VARCHAR, k2 VARCHAR, k3 VARCHAR, k4 VARCHAR, k5 VARCHAR,
        g_headline BOOLEAN, g_k1 BOOLEAN, g_k2 BOOLEAN, g_k3 BOOLEAN, g_k4 BOOLEAN, g_k5 BOOLEAN,
        tp DOUBLE, tp_src VARCHAR, tp_raw VARCHAR, tp_adj DOUBLE, adjust_factor DOUBLE, adjust_method VARCHAR, adjust_note VARCHAR, ex_dates VARCHAR,
        adj_close DOUBLE, upside_now DOUBLE, upside_at_report DOUBLE, val_method VARCHAR, basis VARCHAR, eps_json VARCHAR, yoy_json VARCHAR,
        novel_numbers VARCHAR, qc VARCHAR, generated_at VARCHAR)""")
    for col in ("tp_state VARCHAR", "tp_ratio DOUBLE", "basis_state VARCHAR", "basis_days INTEGER",
                "text_src VARCHAR", "tp_how VARCHAR", "rating VARCHAR", "rating_how VARCHAR",
                "tp_prev DOUBLE", "tp_direction VARCHAR", "headline_fmt VARCHAR"):
        try:                                   # 批419:加欄式(舊庫照樣可讀,只增不減)
            con.execute(f"ALTER TABLE vrn_four_point_digest ADD COLUMN {col}")
        except Exception:
            pass


def _load_text(zones_dir: Path, report_file: str, restored_dir: Path | None = None) -> tuple:
    """研報首頁文字 →(文字, 出處)。出處 ∈ RESTORED_MD / ZONES / NONE。

    批641 接上操作員批636 原令:**先用 ENG085 還原過的 .md**(「修正好的輸出」),
    沒有才退原稿 zones。退這一步要回報出處,不能悄悄換料(LL209)。
    `footer` 是批558 在 ENG073 補過的鍵,**本件當時沒跟著補**——缺鍵不報錯,只安靜地少一區。
    """
    rd = Path(restored_dir) if restored_dir else RESTORED_DIR
    md = rd / f"{report_file}.md"
    if md.is_file():
        try:
            t = md_to_plain(md.read_text(encoding="utf-8"))
            if t.strip():
                return t, "RESTORED_MD"
        except Exception:
            pass
    p = zones_dir / f"{report_file}.json"
    if not p.exists():
        return "", "NONE"
    try:
        z = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return "", "NONE"
    parts = [str(z.get(k) or "") for k in ("header", "right", "body", "footer")]
    t = "\n".join(x for x in parts if x)
    return (t, "ZONES") if t.strip() else ("", "NONE")


def run(db: Path | None = None, zones_dir: Path | None = None, ticker: str | None = None, limit: int | None = None, do_print: bool = True,
        reports: Path = REPORTS, restored_dir: Path | None = None) -> dict:
    import duckdb
    dbp = _resolve_db(db)
    zdir = Path(zones_dir) if zones_dir else ZONES_DIR
    #: 批641 實錄(**這一批我自己踩出來的**):新開的還原車道預設指向正式產物夾,
    #: 而自測給的是 temp zones——結果 `Citi-3231 20250604` 這個 fixture 名字在
    #: `VIA_Reports/vrn/markdown/` 底下**真的有一份同名 .md**(前一次真跑留下的),
    #: 自測於是安靜地讀了正式產物,④⑤⑥ 三檢同時紅。**給了自訂料夾就不得再摸全域**。
    rdir = Path(restored_dir) if restored_dir is not None else (RESTORED_DIR if zones_dir is None else Path(zdir).parent / "_no_restored_")
    rep = {"schema": "VIA.VRNFourPoint.v1", "ts": _dt.datetime.now().isoformat(timespec="seconds"), "db": str(dbp), "zones": str(zdir), "restored": str(rdir), "rows": [],
           "summary": {"reports": 0, "with_text": 0, "k1_grounded": 0, "upside_now": 0, "adjusted": 0, "qc_red": 0}, "verdict": "GREEN"}
    if not dbp.exists():
        rep["verdict"], rep["note"] = "RED", f"庫缺 {dbp}(先 via-vdfdb / ENG073 入庫)"
        _finish(rep, reports, do_print)
        return rep
    con = duckdb.connect(str(dbp))
    try:
        have = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
        if "vrn_report_basic" not in have:
            rep["verdict"], rep["note"] = "RED", "vrn_report_basic 缺(先 ENG072 首頁抽取 → ENG073 入庫)"
            _finish(rep, reports, do_print)
            return rep
        _ensure_table(con)
        bcols = [r[0] for r in con.execute("DESCRIBE vrn_report_basic").fetchall()]
        q = "SELECT * FROM vrn_report_basic WHERE ticker IS NOT NULL AND ticker <> ''"
        args = []
        if ticker:
            q += " AND ticker = ?"
            args.append(ticker)
        q += " ORDER BY report_date DESC, report_file"
        if limit:
            q += f" LIMIT {int(limit)}"
        basics = [dict(zip(bcols, r)) for r in con.execute(q, args).fetchall()]
        rep["summary"]["reports"] = len(basics)
        # 批642:**被 `ticker <> ''` 濾掉的那一群,要有名有姓有態**(不是消失)。
        _bk = applicability()
        _den = {"basic_rows": 0, "digested": len(basics), "not_applicable": [], "nodata": []}
        try:
            _kcol = "report_kind" if "report_kind" in bcols else None
            _den["basic_rows"] = con.execute("SELECT count(*) FROM vrn_report_basic").fetchone()[0]
            _kexpr = _kcol if _kcol else "CAST(NULL AS VARCHAR)"
            _sel = ("SELECT report_file, " + _kexpr + " FROM vrn_report_basic "
                    "WHERE ticker IS NULL OR trim(ticker) = ''")
            for _rf, _kind in con.execute(_sel).fetchall():
                _na, _why = ticker_na(_kind, _bk)
                (_den["not_applicable"] if _na else _den["nodata"]).append(
                    {"report_file": _rf, "report_kind": (_kind or ""), "why": _why})
        except Exception as _e:
            _den["note"] = f"分母量不到:{type(_e).__name__}"
        rep["denominator"] = _den
        rep["summary"]["basic_rows"] = _den["basic_rows"]
        rep["summary"]["not_applicable"] = len(_den["not_applicable"])
        rep["summary"]["nodata_kind"] = len(_den["nodata"])
        mrows = con.execute("SELECT report_file, metric, period, status, value, raw_text FROM vrn_report_metrics").fetchall() if "vrn_report_metrics" in have else []
        metrics: dict = {}
        for rf, metric, period, status, value, raw in mrows:
            metrics.setdefault(rf, []).append({"metric": metric, "period": period, "status": status, "value": value, "raw": raw})
        now = _dt.datetime.now().isoformat(timespec="seconds")
        for b in basics:
            rf = b["report_file"]
            text, text_src = _load_text(zdir, rf, rdir)
            if text:
                rep["summary"]["with_text"] += 1
            rep["summary"]["src_" + text_src.lower()] = rep["summary"].get("src_" + text_src.lower(), 0) + 1
            up_rep = b.get("upside_db") if b.get("upside_db") is not None else b.get("upside_calc")
            basic = {"title_head": b.get("title_head"), "ticker": b.get("ticker"), "target_price": b.get("target_price"), "target_price_raw": "",
                     "name_official": b.get("name_official") or _name_known(str(b.get("ticker") or "")),   # 批685:名只認正典/名冊
                     "yf": _yf_known(str(b.get("ticker") or ""), con),                                    # 批685:查得到市場才給 .TW/.TWO
                     "upside_at_report": (float(up_rep) / 100.0 if up_rep is not None and abs(float(up_rep)) > 1.5 else up_rep),
                     "raw_all": " ".join(str(m.get("raw") or "") for m in metrics.get(rf, []))}
            px = price_context(con, str(b["ticker"]), b.get("report_date"), page_price=b.get("price"))
            d = build_digest(text, basic, metrics.get(rf, []), px)
            d.update({"report_file": rf, "ticker": b["ticker"], "broker": b.get("broker"), "report_date": b.get("report_date"), "text_src": text_src})
            # 批641 自訂正:第一版寫 startswith("樞紐"),把「樞紐無值·自家亦無」也算成命中
            #   ——46 份全報「樞紐 46」。**計數器把「問過」算成「給了值」**,那是假綠。
            #   命中一律帶 `樞紐·` 這個分隔號,未命中是「樞紐無值…」,靠分隔號分得開。
            _how = str(d.get("tp_how") or "")
            if _how.startswith("樞紐·"):
                rep["summary"]["tp_hub"] = rep["summary"].get("tp_hub", 0) + 1
            elif _how.startswith("自家regex"):
                rep["summary"]["tp_local"] = rep["summary"].get("tp_local", 0) + 1
            elif d.get("tp") is None:
                rep["summary"]["tp_none"] = rep["summary"].get("tp_none", 0) + 1
            if d.get("rating"):
                rep["summary"]["rating_hit"] = rep["summary"].get("rating_hit", 0) + 1
            if d.get("tp_prev") is not None:
                rep["summary"]["tp_pair_hit"] = rep["summary"].get("tp_pair_hit", 0) + 1
            rep["rows"].append(d)
            if d["points"]["K1"]["grounded"]:
                rep["summary"]["k1_grounded"] += 1
            if d["upside_now"] is not None:
                rep["summary"]["upside_now"] += 1
            if d["adjust_method"] == "PRICE_FACTOR_CHAIN":
                rep["summary"]["adjusted"] += 1
            if d["qc"] == "RED":
                rep["summary"]["qc_red"] += 1
            if d["tp_state"] == "TP_SUSPECT":
                rep["summary"]["tp_suspect"] = rep["summary"].get("tp_suspect", 0) + 1
            if d["basis_state"] == "STALE_BASIS":
                rep["summary"]["stale_basis"] = rep["summary"].get("stale_basis", 0) + 1
            elif d["basis_state"] == "CURRENT" and d["tp_state"] == "OK" and d["upside_now"] is not None:
                rep["summary"]["upside_trusted"] = rep["summary"].get("upside_trusted", 0) + 1
            con.execute(f"DELETE FROM {TABLE} WHERE report_file = ?", [rf])
            P = d["points"]
            # 批419:改具名欄位。位置式 INSERT 與 ALTER 加欄天生互斥——批412 在 ENG073
            # 踩過同一個坑,這裡加四個新欄時立刻重現(36 值對 40 欄)。記法:加欄就改具名。
            _vals = {
                "report_file": rf, "ticker": b["ticker"], "px_ticker": d["px_ticker"], "broker": b.get("broker"),
                "report_date": b.get("report_date"), "asof_date": d["adj_date"],
                "headline": P["headline"]["text"], "k1": P["K1"]["text"], "k2": P["K2"]["text"],
                "k3": P["K3"]["text"], "k4": P["K4"]["text"], "k5": P["K5"]["text"],
                "g_headline": P["headline"]["grounded"], "g_k1": P["K1"]["grounded"], "g_k2": P["K2"]["grounded"],
                "g_k3": P["K3"]["grounded"], "g_k4": P["K4"]["grounded"], "g_k5": P["K5"]["grounded"],
                "tp": d["tp"], "tp_src": d["tp_src"], "tp_raw": d["tp_raw"], "tp_adj": d["tp_adj"],
                "adjust_factor": d["adjust_factor"], "adjust_method": d["adjust_method"],
                "adjust_note": d["adjust_note"], "ex_dates": ",".join(d["ex_dates"]),
                "adj_close": d["adj_close"], "upside_now": d["upside_now"],
                "upside_at_report": d["upside_at_report"], "val_method": d["method"], "basis": d["basis"],
                "eps_json": json.dumps(d["eps"], ensure_ascii=False),
                "yoy_json": json.dumps(d["yoy"], ensure_ascii=False),
                "novel_numbers": ",".join(d["novel_numbers"]), "qc": d["qc"], "generated_at": now,
                "tp_state": d["tp_state"], "tp_ratio": d["tp_ratio"],
                "basis_state": d["basis_state"], "basis_days": d["basis_days"],
                # 批641 新欄(加欄式,舊庫照讀)
                "text_src": text_src, "tp_how": d.get("tp_how"), "rating": d.get("rating"),
                "rating_how": d.get("rating_how"), "tp_prev": d.get("tp_prev"), "tp_direction": d.get("tp_direction"),
                "headline_fmt": d.get("headline_fmt"),                       # 批685 加欄
            }
            _c = list(_vals)
            con.execute(f"INSERT INTO {TABLE} ({','.join(_c)}) VALUES ({','.join('?' * len(_c))})",
                        [_vals[k] for k in _c])
            if do_print:
                print(f"  [{d['qc']:<6}] {rf[:44]:<44} {b['ticker']:<6} TP {d['tp'] if d['tp'] is not None else '—'}{'→' + str(d['tp_adj']) if d['adjust_method'] == 'PRICE_FACTOR_CHAIN' else ''}"
                      f" adj {d['adj_close'] if d['adj_close'] is not None else '—'}@{d['adj_date'] or '—'} 上漲 {fmt_pct(d['upside_now']) if d['upside_now'] is not None else '未算'}"
                      f" · 接地 {'/'.join(k for k in ('headline', 'K1', 'K2', 'K3', 'K4', 'K5') if d['points'][k]['grounded'])}"
                      + (f" · ⚑TP 疑誤(比值 {d['tp_ratio']:.3f})" if d["tp_state"] == "TP_SUSPECT" else "")
                      + (f" · ⚑非當期({d['basis_days']} 天)" if d["basis_state"] == "STALE_BASIS" else "")
                      + (f" · 新數字 {d['novel_numbers']}" if d["novel_numbers"] else ""))
    finally:
        con.close()
    # 批642 漏斗:把「幾份」這件事一路攤開,含**零正文的空殼 sidecar**(它讓每個數字虛胖)
    try:
        _sc = sorted(Path(zdir).glob("*.json"))
        _empty, _need_ocr = [], []
        for _p in _sc:
            try:
                _z = json.loads(_p.read_text(encoding="utf-8"))
            except Exception:
                _empty.append(_p.stem)
                continue
            if sum(len(str(_z.get(k) or "")) for k in ("header", "right", "body", "footer")) == 0:
                # 批643 更正:**零正文不等於垃圾。**抽取引擎自己就寫了 tag 與 why;
                #   不讀那一欄而只看字數,就會把「等著被補的真缺料」判成「該清掉的空殼」。
                _tag = str(_z.get("tag") or (_z.get("logic") or {}).get("method") or "")
                (_need_ocr if "OCR" in _tag.upper() else _empty).append(_p.stem)
        rep["funnel"] = {"sidecar": len(_sc), "sidecar_empty": _empty, "sidecar_needs_ocr": _need_ocr,
                         "restored_md": len(list(Path(rdir).glob("*.md"))) if Path(rdir).is_dir() else 0,
                         "basic": rep["summary"].get("basic_rows", 0), "digest": rep["summary"].get("reports", 0)}
    except Exception as _e:
        rep["funnel"] = {"note": f"漏斗量不到:{type(_e).__name__}"}

    s = rep["summary"]
    if do_print and rep.get("funnel", {}).get("sidecar") is not None:
        _f = rep["funnel"]
        print(f"  [漏斗] sidecar {_f['sidecar']} → 還原 .md {_f['restored_md']} → 入庫 {_f['basic']} → 文摘 {_f['digest']}"
              + (f" · **待 OCR {len(_f.get('sidecar_needs_ocr') or [])}**"
                 f"({', '.join((_f.get('sidecar_needs_ocr') or [])[:4])}…)=**真缺料,可補**,"
                 f"不是空殼(抽取引擎已寫 tag=NEEDS_OCR)" if _f.get("sidecar_needs_ocr") else "")
              + (f" · 零正文且無因由 {len(_f['sidecar_empty'])}" if _f.get("sidecar_empty") else ""))
    if do_print and s.get("basic_rows"):
        print(f"  [分母] 入庫 {s['basic_rows']} = 文摘 {s['reports']}"
              f" + 不適用 {s.get('not_applicable', 0)}(非個股;依 VRN_MatrixApplicability NA-01)"
              f" + 型別未定 {s.get('nodata_kind', 0)}(NODATA,**不知道型別 ≠ 不適用**)")
    if do_print and s.get("reports"):
        print(f"  [料源] 還原 .md {s.get('src_restored_md', 0)} · 原稿 zones {s.get('src_zones', 0)} · 無 {s.get('src_none', 0)}"
              f"  [目標價] 樞紐 {s.get('tp_hub', 0)} · 退自家 {s.get('tp_local', 0)} · 都抓不到 {s.get('tp_none', 0)}"
              f"  [評等] {s.get('rating_hit', 0)}  [前次→本次] {s.get('tp_pair_hit', 0)}")
    rep["verdict"] = "RED" if s["qc_red"] else ("GREEN" if s["reports"] and s["k1_grounded"] == s["reports"] else ("YELLOW" if s["reports"] else "RED"))
    if not s["reports"]:
        rep["note"] = "vrn_report_basic 無有效 ticker 列"
    _finish(rep, reports, do_print)
    return rep


def render_html(rep: dict) -> str:
    col = {"GREEN": "#34d399", "YELLOW": "#fde047", "RED": "#fca5a5"}
    rows = ""
    for d in rep["rows"]:
        pts = "".join(f"<div><b style='color:{'#34d399' if v['grounded'] else '#fca5a5'}'>{html.escape(v['zh'])}</b> {html.escape(v['text'])}</div>" for v in d["points"].values())
        rows += (f"<tr><td style='color:{col.get(d['qc'], '#ddd')}'><b>{d['qc']}</b></td><td>{html.escape(str(d['ticker']))}<br>{html.escape(str(d.get('broker') or ''))}<br>{html.escape(str(d.get('report_date') or ''))}</td>"
                 f"<td>{pts}<div style='color:#94a3b8'>{html.escape(str(d.get('adjust_note') or ''))}</div></td></tr>")
    return ("<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
            "<title>VRN 一題四點文摘</title><style>body{background:#0f172a;color:#f8fafc;font:11px/1.35 -apple-system,'Segoe UI',Roboto,Arial,sans-serif;padding:12px}"
            "table{border-collapse:collapse;width:100%}td,th{border:1px solid #334155;padding:3px 6px;text-align:left;vertical-align:top}th{background:#1e293b}</style></head><body>"
            f"<h1 style='font-size:14px;margin:0 0 6px'>VRN 一題四點文摘 · {html.escape(rep['verdict'])} · {html.escape(rep['ts'])} · 報告 {rep['summary']['reports']} · K1 接地 {rep['summary']['k1_grounded']} · 除權息調整 {rep['summary']['adjusted']}</h1>"
            "<div style='color:#94a3b8;margin-bottom:8px'>quote-or-abstain · 不發明不平均 · 目標價除權息同口徑(後向因子鏈)· 上漲空間=(TP_adj−最新 adj close)/adj close · 零 CDN</div>"
            f"<table><tr><th>QC</th><th>檔</th><th>一題四點(綠=接地)</th></tr>{rows}</table></body></html>")


def _finish(rep: dict, reports: Path, do_print: bool) -> None:
    try:
        reports.mkdir(parents=True, exist_ok=True)
        (reports / "DIGEST_latest.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
        (reports / "DIGEST_latest.html").write_text(render_html(rep), encoding="utf-8")
    except Exception:
        pass
    if do_print:
        s = rep["summary"]
        print(f"[via-vrn4] {rep['verdict']} · 報告 {s['reports']} · 有正文 {s['with_text']} · K1 接地 {s['k1_grounded']} · 上漲已算 {s['upside_now']} · 除權息調整 {s['adjusted']} · QC 紅 {s['qc_red']}"
              + (f" · {rep['note']}" if rep.get("note") else "") + f" · 存證 {reports / 'DIGEST_latest.json'}")


def show(key: str, db: Path | None = None) -> int:
    import duckdb
    dbp = _resolve_db(db)
    if not dbp.exists():
        print(f"[show] 庫缺 {dbp}")
        return 2
    con = duckdb.connect(str(dbp), read_only=True)
    try:
        if TABLE not in {r[0] for r in con.execute("SHOW TABLES").fetchall()}:
            print("[show] 尚未 run")
            return 2
        rows = con.execute(f"SELECT report_file, ticker, report_date, headline, k1, k2, k3, k4, k5, qc, adjust_note FROM {TABLE} WHERE ticker = ? OR report_file = ? ORDER BY report_date DESC", [key, key]).fetchall()
    finally:
        con.close()
    if not rows:
        print(f"[show] 無 {key}")
        return 2
    for r in rows:
        print(f"=== {r[0]} · {r[1]} · {r[2]} · QC {r[9]} ===")
        for zh, v in zip([z for _, z in SLOTS], r[3:9]):
            print(f"  {zh}:{v}")
        print(f"  除權息:{r[10]}")
    return 0


# ---------------------------------------------------------------- 自測
def selftest() -> int:
    import tempfile
    fails = []

    ran = []

    def chk(name, cond, note=""):
        ran.append(name)
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)
    try:
        import duckdb
    except Exception:
        print("  [FAIL] duckdb 缺(於 via_vrn_312 境跑:via-vrn4)")
        return 1
    page = ("標題: 緯創(3231.TW) 維持買進\n目標價: 165 元\n評價方式: PE 20x 2026E\n基於: AI 伺服器出貨放量\n"
            "2025E 稀釋每股盈餘 7.2\n2026E 稀釋每股盈餘 8.0\n主要原因: AI 伺服器與 GB300 機櫃出貨\n"
            "產能:越南廠 2026 上半年投產。\n同業:廣達、英業達。\n風險: 匯率與關稅\n估值仍具吸引力。\n")
    chk("① 文本規則(目標價/評價方式/基於/主要原因/風險/EPS 年表/首頁其餘對半)",
        extract_target_price(page)[0] == 165.0 and extract_target_price(page)[1].startswith("樞紐") and extract_val_method(page) == "PE 20x 2026E" and extract_basis(page) == "AI 伺服器出貨放量"
        and extract_reason(page).startswith("AI 伺服器") and extract_risk(page) == "匯率與關稅"
        and [e["year"] for e in extract_eps_years(page)] == [2025, 2026] and all(remainder_two(page)))
    chk("② YoY 律(正常/底 0/轉盈/轉虧)+上漲公式+novel numbers(衍生數不計;發明數字抓到)",
        yoy(8.0, 7.2)["state"] == "NORMAL" and yoy(1, 0)["state"] == "NOT_COMPUTABLE_ZERO_BASE" and yoy(2, -1)["state"] == "TURNAROUND_TO_PROFIT"
        and yoy(-2, 1)["state"] == "TURNAROUND_TO_LOSS" and abs(upside(165, 120) - 0.375) < 1e-9 and upside(165, 0) is None
        and novel_numbers("目標價 9999 元", "目標價 850 現價 678") == ["9999"] and novel_numbers("上漲 35.4%", "x", ["35.4%"]) == [])
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        dbp = tdp / "t.duckdb"
        zdir = tdp / "zones"
        zdir.mkdir()
        c = duckdb.connect(str(dbp))
        c.execute("CREATE TABLE tw_listings(code VARCHAR, name VARCHAR, market VARCHAR, yf_ticker VARCHAR)")
        c.execute("INSERT INTO tw_listings VALUES ('3231','緯創','TWSE','3231.TW'), ('2606','裕民','TWSE','2606.TW'), ('9999','無價','TWSE','9999.TW')")
        c.execute("CREATE TABLE tw_daily_prices(date VARCHAR, ticker VARCHAR, open DOUBLE, high DOUBLE, low DOUBLE, close DOUBLE, adj_close DOUBLE, volume DOUBLE)")
        # 3231:報告日 2025-06-04 因子 0.985(其後 07-17 除息 → 因子 1);最新 09-05 close=adj=120
        rows = [("2025-06-03", 113.5, 113.5 * 0.985), ("2025-06-04", 114.0, 114.0 * 0.985), ("2025-07-16", 118.0, 118.0 * 0.985),
                ("2025-07-17", 116.3, 116.3), ("2025-09-05", 120.0, 120.0)]
        for d, cl, adj in rows:
            c.execute("INSERT INTO tw_daily_prices VALUES (?, '3231.TW', ?, ?, ?, ?, ?, 1000)", [d, cl, cl, cl, cl, adj])
        c.execute("INSERT INTO tw_daily_prices VALUES ('2025-09-05', '2606.TW', 70, 70, 70, 70, 70, 100)")
        # 批730:真庫有交易所日成交表;沒有它,因子分母會退到報告頁面價(Citi 列 price 114 ≠ 前一日 113.5)
        c.execute("CREATE TABLE tw_trading_daily(date VARCHAR, code VARCHAR, market VARCHAR, close DOUBLE)")
        for d, cl, _adj in rows:
            c.execute("INSERT INTO tw_trading_daily VALUES (?, '3231', 'TWSE', ?)", [d, cl])
        c.execute("INSERT INTO tw_trading_daily VALUES ('2025-09-05', '2606', 'TWSE', 70)")
        c.execute("""CREATE TABLE vrn_report_basic(report_file VARCHAR, ticker VARCHAR, name_official VARCHAR, broker VARCHAR, report_date VARCHAR, rating_raw VARCHAR,
                     target_price DOUBLE, price DOUBLE, upside_report DOUBLE, upside_calc DOUBLE, upside_state VARCHAR, title_head VARCHAR, summary_head VARCHAR,
                     conflicts VARCHAR, extracted_at VARCHAR, price_db DOUBLE, upside_db DOUBLE, price_state VARCHAR)""")
        c.execute("INSERT INTO vrn_report_basic VALUES ('Citi-3231 20250604','3231','緯創','Citi','2025-06-04','Buy',165,114,44.7,44.7,'EXACT','緯創 維持買進','',NULL,'t',113.5,45.4,'P_CONFIRMED_DB')")
        c.execute("INSERT INTO vrn_report_basic VALUES ('華南-2606 20250901','2606','裕民','華南','2025-09-01',NULL,NULL,NULL,NULL,NULL,'MISSING_SOURCE','裕民 買進','',NULL,'t',NULL,NULL,NULL)")
        c.execute("INSERT INTO vrn_report_basic VALUES ('兆豐-9999 20250801','9999','無價','兆豐','2025-08-01',NULL,78,NULL,NULL,NULL,'MISSING_SOURCE','無價 買進','',NULL,'t',NULL,NULL,NULL)")
        # 批642:補兩列**無票號**——第 709 行那句 WHERE 會濾掉它們,分母三態就是靠這兩列驗的
        c.execute("ALTER TABLE vrn_report_basic ADD COLUMN report_kind VARCHAR")
        c.execute("INSERT INTO vrn_report_basic (report_file, ticker, broker, report_date, title_head, report_kind)"
                  " VALUES ('兆豐晨會 20251205','','兆豐','2025-12-05','晨會','大盤晨報')")
        c.execute("INSERT INTO vrn_report_basic (report_file, ticker, broker, report_date, title_head, report_kind)"
                  " VALUES ('來路不明 20251206','','?','2025-12-06','?', NULL)")
        c.execute("CREATE TABLE vrn_report_metrics(report_file VARCHAR, metric VARCHAR, period VARCHAR, status VARCHAR, value DOUBLE, raw_text VARCHAR)")
        c.execute("INSERT INTO vrn_report_metrics VALUES ('Citi-3231 20250604','EPS','2025E','REPORT_ESTIMATE',7.2,'2025E EPS 7.2'), ('Citi-3231 20250604','EPS','2026E','REPORT_ESTIMATE',8.0,'2026E EPS 8.0'), ('Citi-3231 20250604','EPS','2027E','REPORT_ESTIMATE',9.6,'2027E EPS 9.6')")
        c.close()
        (zdir / "Citi-3231 20250604.json").write_text(json.dumps({"header": "標題: 緯創(3231.TW) 維持買進", "right": "目標價: 165 元\n評價方式: PE 20x 2026E\n基於: AI 伺服器出貨放量",
                                                                  "body": page.split("\n", 4)[4], "footer": "x"}, ensure_ascii=False), encoding="utf-8")
        (zdir / "華南-2606 20250901.json").write_text(json.dumps({"header": "", "right": "", "body": "裕民 買進 觀點:運價回升。", "footer": ""}, ensure_ascii=False), encoding="utf-8")
        rdir = tdp / "md"
        rdir.mkdir()
        # 批641:Citi 走**還原車道**(新路要被走過,不然等於沒測 L83);
        # 華南走 zones(舊路不得回歸);兆豐沒有 sidecar=NONE。一跑三態。
        # 頭兩行**故意留 ENG085 的 HTML 註解**,而且註解裡有 `20250604`——
        # 剝不掉的話 `extract_eps_years` 會讀成「2025 年 EPS 604」,
        # 那個 604 不在正文裡 → novel numbers → 檢⑥ 的 qc 當場轉紅。
        # 所以檢⑥ 同時是**剝註解**這件事的證人,不是另外補一個假檢。
        (rdir / "Citi-3231 20250604.md").write_text(
            "<!-- VRN_ENG085 v0103 · 還原層(不刪除;原件零觸碰)-->\n"
            "<!-- 來源 Citi-3231 20250604 · 頁 1 · 擷取法 未標 -->\n\n"
            "# 標題: 緯創(3231.TW) 維持買進\n\n"
            "> 目標價: 165 元\n> 評價方式: PE 20x 2026E\n> 基於: AI 伺服器出貨放量\n\n"
            "| 年度 | 稀釋EPS |\n|---|---|\n"
            "2025E 稀釋每股盈餘 7.2\n2026E 稀釋每股盈餘 8.0\n"
            "主要原因: AI 伺服器與 GB300 機櫃出貨\n"
            "產能:越南廠 2026 上半年投產。\n同業:廣達、英業達。\n"
            "風險: 匯率與關稅\n估值仍具吸引力。\n", encoding="utf-8")
        rep = run(dbp, zdir, do_print=False, reports=tdp / "rep", restored_dir=rdir)
        d = {r["report_file"]: r for r in rep["rows"]}
        citi = d["Citi-3231 20250604"]
        f = 0.985
        chk("③ 除權息調整律(報告日 06-04 因子 0.985 → 最新 1.0;事件日 07-17;TP 165 × 0.985 = 162.53;上漲 =(162.53−120)/120)",
            citi["adjust_method"] == "PRICE_FACTOR_CHAIN" and abs(citi["adjust_factor"] - f) < 1e-9 and citi["ex_dates"] == ["2025-07-17"]
            and citi["tp_adj"] == 162.53 and abs(citi["upside_now"] - (162.53 - 120) / 120) < 1e-9 and citi["adj_date"] == "2025-09-05",
            f"({citi['adjust_note']})")
        k1 = citi["points"]["K1"]["text"]
        chk("④ K1 契約(潛在上漲空間 % · 最新 adj close 日/價 · 目標價 來源 · 除權息調整標註 · 評價方式 · 基於 · 報告時上漲另列)",
            citi["points"]["K1"]["grounded"] and k1.startswith("潛在上漲空間 35.4%") and "2025-09-05 120.0元" in k1 and "目標價 165元(報告正文)" in k1
            and "除權息調整 0.9850 → 162.53元" in k1 and "評價方式 PE 20x 2026E" in k1 and "基於 AI 伺服器出貨放量" in k1 and "報告時上漲 45.4%" in k1, f"({k1[:120]})")
        k2 = citi["points"]["K2"]["text"]
        chk("⑤ K2 契約(EPS 冊 2025/2026/2027 + 2028 未提及 · YoY 11.1%/20.0% · 主要原因原句)",
            citi["points"]["K2"]["grounded"] and "稀釋EPS 2025 7.2、2026 8、2027 9.6、2028 未提及" in k2 and "2026 YoY 11.1%" in k2 and "2027 YoY 20.0%" in k2 and "主要原因 AI 伺服器" in k2, f"({k2[:120]})")
        chk("⑥ K3/K4 首頁其餘對半(去已用標籤行;原文)+K5 風險原句+標題接地",
            citi["points"]["K3"]["grounded"] and citi["points"]["K4"]["grounded"] and "產能" in citi["points"]["K3"]["text"] + citi["points"]["K4"]["text"]
            and citi["points"]["K5"]["text"] == "匯率與關稅" and citi["points"]["headline"]["grounded"] and citi["qc"] == "GREEN", f"({citi['novel_numbers']})")
        hn = d["華南-2606 20250901"]
        chk("⑦ 無目標價=K1 未提及(不拿共識/close 頂替);正文無標籤=標題 ungrounded(檔頭);K5 可空",
            hn["points"]["K1"]["text"] == "未提及" and not hn["points"]["K1"]["grounded"] and not hn["points"]["headline"]["grounded"] and hn["points"]["K5"]["text"] == "未提及")
        zf = d["兆豐-9999 20250801"]
        chk("⑧ SSOT 目標價有、該檔不在價表=上漲空間未算(誠實列原因);K1 仍接地(目標價出自 VRN_SSOT)",
            zf["tp"] == 78 and zf["tp_src"] == "VRN_SSOT" and zf["upside_now"] is None and "上漲空間未算" in zf["points"]["K1"]["text"] and zf["points"]["K1"]["grounded"])
        rep2 = run(dbp, zdir, do_print=False, reports=tdp / "rep", restored_dir=rdir)
        c = duckdb.connect(str(dbp), read_only=True)
        n = c.execute(f"SELECT count(*), count(DISTINCT report_file) FROM {TABLE}").fetchone()
        c.close()
        chk("⑨ 落庫+重跑冪等(派生層重算=同 report_file 重寫;3 列)+JSON/HTML 零 CDN",
            n == (3, 3) and rep2["summary"]["reports"] == 3 and (tdp / "rep" / "DIGEST_latest.json").exists()
            and 'src="http' not in (tdp / "rep" / "DIGEST_latest.html").read_text(encoding="utf-8"))
        px0 = price_context(duckdb.connect(str(dbp), read_only=True), "3231", None)
        chk("⑩ 報告日缺=不除權息調整(目標價照列;誠實註記)", px0["adjust_method"] == "NONE" and "報告日缺" in px0["adjust_note"] and px0["adj_close"] == 120.0)
        mt = build_digest("目標價 78 元", {"target_price": 78, "target_price_raw": "78;128", "title_head": "x"}, [], {"adj_close": None, "adjust_note": "該檔不在價表"})
        chk("⑪ 多值目標價列示不平均(78;128 只列,不取均)", "不平均" not in mt["points"]["K1"]["text"] or "78;128" in mt["points"]["K1"]["text"])
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑫ 紀律宣告(只增不減/原件零觸碰/誠實三態/零網路/尾版律/quote-or-abstain/ACCEL-BRIDGE)",
        all(k in src for k in ("只增不減", "原件零觸碰", "誠實三態", "零網路", "尾版律", "quote-or-abstain", "ACCEL-BRIDGE")))
    # ── 批419 二檢:K1 兩道閘。fixture 的比值與天數全部取自操作員 37 份真文摘 ──
    chk("⑬ 目標價合理性閘(批419:工作站真跑 37 份,三份的 TP/價 比是 0.020(MS-2308)、"
        "0.019(MS-8210)、0.005(JP-3653)——目標價只有股價的 1/50 到 1/200,那是抽錯的數。"
        "把它印成「潛在上漲空間 -98.0%」比不印更糟,讀的人會以為那是預測。"
        "閘只 flag 不丟棄:我們不知道哪個數字才對,丟棄等於替操作員決定)",
        tp_sanity(37.8, 1850.0)[0] == "TP_SUSPECT"
        and tp_sanity(17.81, 937.0)[0] == "TP_SUSPECT"
        and tp_sanity(25.84, 5655.0)[0] == "TP_SUSPECT"
        and tp_sanity(2577.41, 2070.0)[0] == "OK"        # 凱基 3665 上漲 24.5%=正常
        and tp_sanity(200.31, 68.6)[0] == "OK"           # 泓德 +192% 仍在帶內=不亂殺
        and tp_sanity(None, 100.0)[0] == "NA" and tp_sanity(10.0, 0)[0] == "NA",
        f"(2308 {tp_sanity(37.8, 1850.0)[1]:.3f} · 3665 {tp_sanity(2577.41, 2070.0)[1]:.3f})")

    chk("⑭ 價格基準日律(批419:37 份全部拿 2026-09-07 的價比,但 Daiwa-1319 是 2023-10-11 "
        "的報告=距今 1062 天。拿三年後的價算三年前報告的「潛在上漲空間」,算出來的不是上漲空間,"
        "是事後看圖。逾 180 天即非當期:改把「報告時上漲」放頭,今日比值降為參考)",
        basis_age("2023-10-11", "2026-09-07") == 1062
        and basis_state(1062) == "STALE_BASIS"
        and basis_age("2026-05-19", "2026-09-07") == 111
        and basis_state(111) == "CURRENT"
        and basis_state(basis_age("2025-12-08", "2026-09-07")) == "STALE_BASIS"   # 273 天
        and basis_state(None) == "UNKNOWN" and basis_age("", "2026-09-07") is None,
        f"(1319 {basis_age('2023-10-11', '2026-09-07')}天={basis_state(1062)} · "
        f"3665 {basis_age('2026-05-19', '2026-09-07')}天={basis_state(111)})")

    # ── 批419b 一檢:閘門自己的診斷值不得被 novel numbers 判成「發明的數字」──
    _k1_suspect = ("目標價疑為擷取誤判(不列為潛在上漲空間):目標價 38元(報告正文)"
                   " vs 最新 adj close 2026-09-07 1850元 → 比值 0.020"
                   f"(合理帶 {TP_SANITY_LO}–{TP_SANITY_HI});待人工核 PDF")
    _src = "目標價 38 元 現價 1850"
    _gate_derived = ["0.020", str(TP_SANITY_LO), str(TP_SANITY_HI), "2026-09-07"]
    chk("⑮ 閘門診斷值不算新數字(批419b 我自己造的回歸:批419 的 K1 會印比值 0.020 與"
        "合理帶界 0.2/5.0,那是關於擷取的後設說明,不是報告裡的宣稱;拿 novel numbers 查它們"
        "等於要求判準本身也要出現在正文裡。工作站實錄 MS-2308/MS-8210/JP-3653 三份因此 QC 紅、"
        "vrn_fourpoint rc=1——整段鏈被自己的診斷訊息判死)",
        novel_numbers(_k1_suspect, _src, _gate_derived) == []
        # 對照組:不把診斷值放進 derived,就會被判成新數字=證明這檢不是空檢
        and novel_numbers(_k1_suspect, _src, []) != []
        # 真的發明的數字照樣抓得到(閘門不是萬用赦免)
        and novel_numbers(_k1_suspect + " 另有神祕數 7777", _src, _gate_derived) == ["7777"],
        f"(帶診斷值 {novel_numbers(_k1_suspect, _src, _gate_derived)} · "
        f"不帶 {novel_numbers(_k1_suspect, _src, [])[:3]})")

    # ⑯ 批470:票號查正典冊,不盲試
    _nb16, _nbw16 = _namebook()
    import duckdb as _dd16
    _ok16 = False
    _note16 = ""
    try:
        _c16 = _dd16.connect(str(DB_TW), read_only=True)
        _r16 = _tickers_for("2330", _c16)
        _legacy_has = _c16.execute(
            "SELECT count(*) FROM tw_listings WHERE code='2330'").fetchone()[0] \
            if "tw_listings" in {r[0] for r in _c16.execute("SHOW TABLES").fetchall()} else -1
        _c16.close()
        _ok16 = (len(_r16) == len(set(_r16))) and (_r16[0] == "2330.TW" if _nb16 else True)
        _note16 = (f"(2330 候選 {_r16} · 去重={len(_r16) == len(set(_r16))}"
                   f" · 殘缺表有 2330?{_legacy_has} · 冊="
                   f"{'在' if _nb16 else _nbw16})")
    except Exception as _e16:
        _note16 = f"(庫不可用:{type(_e16).__name__};本檢需要庫)"
        _ok16 = _nb16 is not None
    chk("⑯ 票號查**正典冊**不盲試(批470 全景分析:v0103 只查 tw_listings——那張表"
        "只有 891 列且**不含 2330/2454/3008/1101**,權值股一律查不到 yf_ticker,"
        "只能退到盲試 .TW/.TWO。盲試的成本不是慢,是**看不出來**:它不報錯,"
        "只是價表對不上,最後顯示成「adj —@— 上漲未算」,看起來像沒有價格資料,"
        "其實是票號從一開始就沒查對)。綁 MDL142(含 yf_ticker 與 market);"
        "冊缺席退回原本直查=零回歸;盲試保留為最終退路,去重但保序",
        _ok16, _note16)

    # ── 批641 新檢:還原車道 / 隔離 / 樞紐優先 / footer / 不截行 ──────────────
    _p17 = md_to_plain("<!-- 來源 x20250604 -->\n# 標題: A\n> 目標價: 165 元\n"
                       "| 年 | EPS |\n|---|---|\n| 2025 | 7.2 |\n本文一句。\n")
    chk("⑰ md_to_plain 剝註解/標題記號/引言記號/對齊列,**留行**"
        "(行結構正是還原層的價值;註解裡的 20250604 若不剝會被讀成 2025 年 EPS 604)",
        "<!--" not in _p17 and "20250604" not in _p17 and _p17.splitlines()[0] == "標題: A"
        and _p17.splitlines()[1] == "目標價: 165 元" and not any(l.startswith("|") for l in _p17.splitlines())
        and not any(set(l) <= set("-|: ") for l in _p17.splitlines()) and "年 EPS" in _p17,
        f"({_p17.splitlines()[:4]})")

    _d17 = {r["report_file"]: r for r in rep["rows"]}
    chk("⑱ 三料源各走一遍(L83:只有一半的路被走過就不算跑過)+出處落庫,"
        "**退到舊路這件事要看得見**(LL209:退路不得悄悄換尺)",
        _d17["Citi-3231 20250604"]["text_src"] == "RESTORED_MD"
        and _d17["華南-2606 20250901"]["text_src"] == "ZONES"
        and _d17["兆豐-9999 20250801"]["text_src"] == "NONE"
        and rep["summary"].get("src_restored_md") == 1 and rep["summary"].get("src_zones") == 1,
        f"({ {k: v['text_src'] for k, v in _d17.items()} })")

    # ⑲ 這一批我自己踩的坑:新車道預設指向正式產物夾
    _leak = _load_text(Path(tempfile.gettempdir()) / "_via_no_such_zones_", "Citi-3231 20250604")
    _iso_ok = True
    try:
        _iso_ok = (RESTORED_DIR / "Citi-3231 20250604.md").is_file()      # 正式夾真的有同名檔才算測到
    except Exception:
        _iso_ok = False
    chk("⑲ 自測給了自訂料夾,引擎就不得再摸全域正式產物"
        "(實錄:`Citi-3231 20250604` 這個 fixture 名在 VIA_Reports/vrn/markdown/ 底下**真的有一份同名 .md**,"
        "新車道預設指向那裡,④⑤⑥ 三檢同時紅——而它們紅得像是我改壞了抽取,其實是料被換掉了)",
        _leak[1] in ("RESTORED_MD", "NONE") and rep["restored"].endswith("md")
        and "VIA_Reports" not in rep["restored"],
        f"(本跑還原夾={Path(rep['restored']).name} · 正式夾有同名檔={_iso_ok})")

    _tp20 = extract_target_price("目標價:$345")
    _tp20b = extract_target_price_local("目標價:$345")
    chk("⑳ 樞紐優先·自家 regex 退為退路(`目標價:$345` 是自家那條 regex 的盲點:"
        "`(?:NT\\$|新台幣)?` 不含裸 $,當場啞掉。容器 81 份真料:樞紐 34 / 自家 13)",
        _tp20[0] == 345.0 and _tp20[1].startswith("樞紐") and _tp20b is None,
        f"(樞紐 {_tp20} · 自家 {_tp20b})")

    with tempfile.TemporaryDirectory() as td21:
        z21 = Path(td21)
        (z21 / "F.json").write_text(json.dumps(
            {"header": "", "right": "", "body": "本文。", "footer": "目標價: 250 元"}, ensure_ascii=False), encoding="utf-8")
        _t21, _s21 = _load_text(z21, "F", z21 / "_none_")
    chk("㉑ zones join 補 `footer`(批558 已在 ENG073 修過同一個缺鍵,**本支當時沒跟著修**;"
        "缺鍵不報錯,只安靜地少一區,長得跟「那裡本來就沒東西」一模一樣)"
        "——誠實記:容器 81 份只有 2 份 footer 有字(共 43 字),抽取零改變,這是一致性修不是修好了什麼",
        "目標價: 250 元" in _t21 and _s21 == "ZONES" and extract_target_price(_t21)[0] == 250.0,
        f"(footer 入 join={'目標價' in _t21})")

    _long = "\n".join([f"第{i}行" for i in range(60)]) + "\n目標價: 165 元\n"
    chk("㉒ first_page(max_lines=0) 不再砍行,預設 48 行照舊(料來自 first_page_text=依定義整份就是第一頁;"
        "再砍 48 行是多的一把尺,容器 81 份裡 38 份被砍、當場掉一個目標價)"
        "——`remainder_two` 仍走 48 行,行為逐字不變",
        extract_target_price(first_page(_long))[0] is None and extract_target_price(first_page(_long, max_lines=0))[0] == 165.0
        and len(first_page(_long).splitlines()) == 48,
        f"(48行={len(first_page(_long).splitlines())} · 不截={len(first_page(_long, max_lines=0).splitlines())})")

    # ── 批642:分母三態 / 不假造 N/A / 漏斗點名 ──────────────────────────────
    _bk = applicability()
    chk("㉓ 分母三態:非個股=NOT_APPLICABLE(依 VRN_MatrixApplicability NA-01)· "
        "**型別未定=NODATA 不是不適用**(批633 在矩陣那邊正是這樣把一整欄誤判成不適用的)· 個股照做",
        ticker_na("大盤晨報", _bk)[0] is True and ticker_na("產業", _bk)[0] is True
        and ticker_na("個股", _bk)[0] is False
        and ticker_na("", _bk)[0] is False and "NODATA" in ticker_na("", _bk)[1]
        and ticker_na("未分類", _bk)[0] is False,
        f"(晨報 {ticker_na('大盤晨報', _bk)[0]} · 空 {ticker_na('', _bk)[1][:18]})")

    chk("㉔ 適用性正本缺席=**一律當適用,不假造 N/A**(那本冊自己的紀律第三條:沒有這一本就退回四態)",
        ticker_na("大盤晨報", None)[0] is False and "不假造" in ticker_na("大盤晨報", None)[1],
        f"({ticker_na('大盤晨報', None)[1][:30]})")

    _d25 = rep["denominator"]
    chk("㉕ 被 `ticker <> ''` 濾掉的那一群要有名有姓有態(v0106 以前它們在報告上一個字都沒有;"
        "容器實測:入庫 71 = 文摘 46 + 不適用 23 + 型別未定 2)",
        _d25["basic_rows"] == 5 and _d25["digested"] == 3
        and [x["report_file"] for x in _d25["not_applicable"]] == ["兆豐晨會 20251205"]
        and [x["report_file"] for x in _d25["nodata"]] == ["來路不明 20251206"],
        f"(入庫 {_d25['basic_rows']} = 文摘 {_d25['digested']} + 不適用 {len(_d25['not_applicable'])}"
        f" + 未定 {len(_d25['nodata'])})")

    chk("㉖ 漏斗點名**零正文的空殼 sidecar**(容器裡 8 份 rep_0X 是自測留下來的,字數 0,"
        "讓每一個「幾份」的數字都虛胖)——只點名不刪,刪不刪是操作員的事",
        isinstance(rep.get("funnel", {}).get("sidecar_empty"), list)
        and rep["funnel"]["sidecar"] == 2 and rep["funnel"]["sidecar_empty"] == [],
        f"(fixture sidecar {rep.get('funnel', {}).get('sidecar')} · 空殼 {rep.get('funnel', {}).get('sidecar_empty')})")

    # ── 批643 ──────────────────────────────────────────────────────────────
    _src643 = Path(__file__).read_text(encoding="utf-8")
    chk("㉗ **L99 除權息基準律**(操作員批643 令「有目標價過了除權息都要改成 ADJ CLOSE,"
        "跟目前的 ADJ CLOSE 更新計算目標價」):因子鏈 = 報告日因子 ÷ 最新日因子 · "
        "事件日由因子變動偵測 · 目標價 × 因子 · 上漲空間一律對 `adj_close` 算,**永不拿 close 頂替**。"
        "量過:價表 892 檔最新日因子全部 = 1,adj 基準就是「目前」,沒有混時點",
        'f = out["factor_report"] / out["factor_latest"]' in _src643
        and 'upside(tp_adj if tp_adj is not None else tp, adj)' in _src643
        and "不拿 close 頂替=Adjusted 與原始不混用" in _src643
        and citi["tp_adj"] == 162.53 and citi["adjust_method"] == "PRICE_FACTOR_CHAIN",
        f"(fixture 165 × 0.985 = {citi['tp_adj']} · 對 adj {citi['adj_close']} 算)")

    chk("㉘ 調整態不得用空字串站著(批643:容器 46 份裡 **41 份的 `adjust_method` 是 `''`**——"
        "而 `''` 跟 `NONE`(有價、查過、確認期間無除權息)意思完全相反,在庫裡卻都篩不出來。"
        "補 NO_PRICE / NO_ADJ_CLOSE / NO_PRICE_TABLE 三個誠實態)",
        zf["adjust_method"] == "NO_PRICE" and "NO_ADJ_CLOSE" in _src643 and "NO_PRICE_TABLE" in _src643
        and all(r["adjust_method"] for r in rep["rows"]),
        f"(兆豐-9999 不在價表 → {zf['adjust_method']} · 本跑空字串 "
        f"{sum(1 for r in rep['rows'] if not r['adjust_method'])} 份)")

    _f643 = rep.get("funnel", {})
    chk("㉙ **零正文不等於垃圾**(批643 更正我自己在批642 的誤判:我寫「掉的 10 份全是自測空殼」,"
        "而其中 8 份的 sidecar 裡 ENG072 早就寫了 `tag=NEEDS_OCR` 與 "
        "`why=header/right 留空是誠實,不是抽失敗`——我只看字數 0 就判垃圾,**沒讀旁邊那一欄**。"
        "垃圾會被清掉,缺料要被補,判錯方向的代價不對稱)",
        "sidecar_needs_ocr" in _f643 and isinstance(_f643["sidecar_needs_ocr"], list)
        and "OCR" in _src643.split("_tag = str(")[1][:200],
        f"(本跑 待OCR {len(_f643.get('sidecar_needs_ocr') or [])} · 無因由 {len(_f643.get('sidecar_empty') or [])})")

    _ch = compose_headline
    _cases685 = [
        (("台積電", "2330", "2330.TW", "先進製程需求強勁"), ("台積電(2330.TW)-先進製程需求強勁", "NAME_CODE")),
        (("台積電", "2330", "", "先進製程需求強勁"), ("台積電(2330)-先進製程需求強勁", "NAME_CODE")),
        (("", "2330", "2330.TW", "先進製程需求強勁"), ("(2330.TW)-先進製程需求強勁", "CODE_ONLY")),
        (("台積電", "", "", "先進製程需求強勁"), ("台積電-先進製程需求強勁", "NAME_ONLY")),
        (("緯創", "3231", "3231.TW", "緯創(3231.TW) 維持買進"), ("緯創(3231.TW) 維持買進", "TITLE_HAS_CODE")),
        (("台積電", "2330", "2330.TW", "台積電 維持買進"), ("台積電(2330.TW) 維持買進", "NAME_IN_TITLE")),
        (("", "", "", ""), ("未提及", "TITLE_ONLY")),
    ]
    _bad685 = [(a, _ch(*a), e) for a, e in _cases685 if tuple(_ch(*a)) != e]
    _cx685 = duckdb.connect()
    _cx685.execute("CREATE TABLE tw_listings(code VARCHAR, name VARCHAR, market VARCHAR, yf_ticker VARCHAR)")
    _cx685.execute("INSERT INTO tw_listings VALUES ('2606','裕民','TWSE','2606.TW')")
    _yf_a, _yf_b = _yf_known("2606", _cx685), _yf_known("9999", _cx685)
    _cx685.close()
    chk("㉚ 標題=名(代號.TW)-本文標題(批685 操作員逐字令):名只認 name_official/名冊、.TW/.TWO 只認查得到的市場"
        "(查不到用裸碼、_yf_known 回空不盲猜)、標題已含代號=原句、名在標題裡=補代號不重複、皆缺=原句;"
        "fixture Citi 標題已含 3231 → TITLE_HAS_CODE;headline_fmt 加欄落庫;代號入 derived 不觸發 novel numbers",
        not _bad685 and citi.get("headline_fmt") == "TITLE_HAS_CODE" and citi["headline"] == "緯創(3231.TW) 維持買進"
        and _yf_a == "2606.TW" and _yf_b == "" and "headline_fmt VARCHAR" in _src643
        and 'str(basic.get("yf") or "")' in _src643.split("derived = [")[1][:400],
        f"(壞例 {_bad685} · Citi {citi.get('headline_fmt')} · yf 2606={_yf_a!r} 9999={_yf_b!r})")
    # ── 批730 ㉛:報告日因子的分母要是成交當下的收盤(交易所),不是 Yahoo 事後回調過的 close ──
    _cx730 = duckdb.connect()
    _cx730.execute("CREATE TABLE tw_daily_prices(date VARCHAR, ticker VARCHAR, open DOUBLE, high DOUBLE, low DOUBLE, close DOUBLE, adj_close DOUBLE, volume DOUBLE)")
    _cx730.execute("CREATE TABLE tw_trading_daily(date VARCHAR, code VARCHAR, market VARCHAR, close DOUBLE)")
    for _d, _cl, _adj in (("2024-09-26", 95.7617, 87.532), ("2025-07-31", 64.167, 58.9), ("2026-09-22", 62.0, 62.0)):
        _cx730.execute("INSERT INTO tw_daily_prices VALUES (?, '1294.TWO', ?, ?, ?, ?, ?, 1000)", [_d, _cl, _cl, _cl, _cl, _adj])
    _cx730.execute("INSERT INTO tw_trading_daily VALUES ('2024-09-26','1294','TPEx',126.5),('2026-09-22','1294','TPEx',62.0)")
    _pc730 = price_context(_cx730, "1294", "2024-09-27")
    _cx730.execute("DROP TABLE tw_trading_daily")
    _pc730y = price_context(_cx730, "1294", "2024-09-27")
    _cx730.close()
    _f730 = 87.532 / 126.5
    chk("㉛ 批730 配股回調:1294 報告日 2024-09-27,交易所前一日收盤 126.5、Yahoo 回調成 95.7617(比 0.757)。"
        "報告日因子 = adj 87.532 ÷ **交易所 126.5**;Yahoo 回調比 ≠ 1 本身算一次股本事件(adj/close 比值看不見配股,"
        "舊碼會因為「沒偵測到因子變動」把因子當 1、目標價一分不調);交易所表不在 → 退 Yahoo 且具名",
        _pc730["factor_basis"] == "RAW_EXCHANGE" and abs(_pc730["factor_report"] - _f730) < 1e-12
        and _pc730["adjust_method"] == "PRICE_FACTOR_CHAIN" and abs(_pc730["adjust_factor"] - _f730) < 1e-12
        and _pc730["retro_ratio"] == round(95.7617 / 126.5, 6) and "配股/拆股" in _pc730["adjust_note"]
        and _pc730y["factor_basis"] == "YAHOO_CLOSE" and abs(_pc730y["factor_report"] - 87.532 / 95.7617) < 1e-12,
        f"(交易所 {_pc730['adjust_method']} × {_pc730['adjust_factor']:.6f} · Yahoo 後備 {_pc730y['factor_basis']} × {_pc730y['adjust_factor']})")
    # ── 批730 修正 ㉜:因子與事件向 ENG073 要(同一件事一處算);前一交易日;沒調到的公司行動不生數字 ──
    _e73 = _eng073()
    _cx732 = duckdb.connect()
    _cx732.execute("CREATE TABLE tw_daily_prices(date VARCHAR, ticker VARCHAR, open DOUBLE, high DOUBLE, low DOUBLE, close DOUBLE, adj_close DOUBLE, volume DOUBLE)")
    _cx732.execute("CREATE TABLE tw_trading_daily(date VARCHAR, code VARCHAR, market VARCHAR, close DOUBLE)")
    # 4950 形:2025-11-03 減資 ×2.6185,Yahoo 沒調(close = adj 一路)
    for _d, _p in (("2025-10-20", 10.4), ("2025-10-21", 10.35), ("2025-10-22", 10.3), ("2025-10-24", 10.3), ("2025-10-27", 10.45),
                   ("2025-10-28", 10.2), ("2025-10-30", 10.1), ("2025-10-31", 10.0), ("2025-11-03", 26.1848), ("2026-09-22", 15.75)):
        _cx732.execute("INSERT INTO tw_daily_prices VALUES (?, '4950.TWO', ?, ?, ?, ?, ?, 1000)", [_d, _p, _p, _p, _p, _p])
    _cx732.execute("INSERT INTO tw_trading_daily VALUES ('2025-10-27','4950','TPEx',10.45),('2025-10-28','4950','TPEx',10.2),('2025-10-30','4950','TPEx',10.1)")
    # 除息日 07-10(現金股利段 0.97 → 1.0 並持續);報告日 07-10 = 前一交易日 07-09 還沒除息 → 0.97;報告日 07-11 → 1.0
    for _d, _p, _k in (("2025-07-03", 100.0, 0.97), ("2025-07-04", 101.0, 0.97), ("2025-07-07", 102.0, 0.97), ("2025-07-08", 101.0, 0.97),
                       ("2025-07-09", 103.0, 0.97), ("2025-07-10", 100.0, 1.0), ("2025-07-11", 101.0, 1.0), ("2025-07-14", 100.5, 1.0),
                       ("2026-09-22", 105.0, 1.0)):
        _cx732.execute("INSERT INTO tw_daily_prices VALUES (?, '5904.TWO', ?, ?, ?, ?, ?, 1000)", [_d, _p, _p, _p, _p, round(_p * _k, 4)])
        _cx732.execute("INSERT INTO tw_trading_daily VALUES (?, '5904', 'TPEx', ?)", [_d, _p])
    # 7777:只配股、沒有現金股利(adj = close 一路,Yahoo 的 adj/close 比值永遠是 1 → ex_dates 空)——
    #   只有 Yahoo 回調比 ≠ 1 這道閘能把因子拉出來(審查 12a:㉛ 的 fixture 本來就有現金除息日,拿掉這道閘它也照過)
    for _d, _raw in (("2025-06-02", 100.0), ("2025-06-03", 101.0), ("2025-06-04", 100.5), ("2025-06-05", 100.0), ("2025-06-06", 100.0),
                     ("2025-07-01", 91.0), ("2025-07-02", 92.0), ("2026-09-22", 95.0)):
        _yc = round(_raw / 1.1, 4) if _d < "2025-07-01" else _raw
        _cx732.execute("INSERT INTO tw_daily_prices VALUES (?, '7777.TWO', ?, ?, ?, ?, ?, 1000)", [_d, _yc, _yc, _yc, _yc, _yc])
        _cx732.execute("INSERT INTO tw_trading_daily VALUES (?, '7777', 'TPEx', ?)", [_d, _raw])
    _sd732 = price_context(_cx732, "7777", "2025-06-09")
    _ev732 = price_context(_cx732, "4950", "2025-10-29")
    _dg732 = build_digest("目標價 12 元", {"target_price": 12, "title_head": "x"}, [], _ev732)
    _on_ex = price_context(_cx732, "5904", "2025-07-10")
    _after_ex = price_context(_cx732, "5904", "2025-07-11")
    _same = [(r, price_context(_cx732, "5904", r)["adjust_factor"],
              _e73.adj_quote(_cx732, "5904", r, 100.0)["adj_factor"] if _e73 else None) for r in ("2025-07-10", "2025-07-11", "2025-07-15")]
    _cx732.close()
    chk("㉜ 批730 修正:因子與事件一律向 ENG073 要(同一件事一處算,本支不留第二份);4950 減資 ×2.6185 Yahoo 沒調 → "
        "EVENT_UNADJUSTED、**不給因子、K1 上漲空間未算**(初版會拿 12 元對 15.75 元算出 −23.8%);前一交易日:"
        "報告日剛好是除息日 07-10 → 用 07-09 的 0.97(目標價是除息前訂的),07-11 → 1.0;三個報告日兩支引擎逐位同答;"
        "只配股、沒有現金除息日的 7777(Yahoo adj/close 永遠 1)→ 靠回調比那道閘照乘 1/1.1",
        _e73 is not None and _ev732["adjust_method"] == "EVENT_UNADJUSTED" and _ev732["adjust_factor"] is None
        and "×2.6185" in _ev732["adjust_note"] and _dg732["upside_now"] is None and "上漲空間未算" in _dg732["points"]["K1"]["text"]
        and _on_ex["report_px_date"] == "2025-07-09" and abs(_on_ex["adjust_factor"] - 0.97) < 1e-9
        and _after_ex["report_px_date"] == "2025-07-10" and _after_ex["adjust_factor"] == 1.0
        and all(a is not None and b is not None and abs(a - b) < 1e-12 for _r, a, b in _same)
        and _sd732["adjust_method"] == "PRICE_FACTOR_CHAIN" and _sd732["ex_dates"] == []
        and abs(_sd732["adjust_factor"] - round(100.0 / 1.1, 4) / 100.0) < 1e-9,
        f"(4950 {_ev732['adjust_method']} · 除息日報告 {_on_ex['report_px_date']} × {_on_ex['adjust_factor']} · "
        f"隔日 × {_after_ex['adjust_factor']} · 只配股 {_sd732['adjust_method']} × {_sd732['adjust_factor']:.6f} · "
        f"兩引擎 {[(r, a, b) for r, a, b in _same]})")
    print(f"  [計] {len(ran)} 檢 OK {len(ran) - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def _arg(a: list, flag: str, default=None):
    if flag in a:
        i = a.index(flag)
        if i + 1 < len(a):
            return a[i + 1]
    return default


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== VRN 一題四點文摘(VRN_ENG080_FourPointDigest)· 三十二檢自測(零網路;臨時庫)===")
        return selftest()
    verb = next((x for x in a if x in ("run", "show")), "run")   # 批387:動詞白名單(--ticker 2330 不得誤判為動詞)
    try:
        import duckdb  # noqa: F401
    except Exception:
        print(f"[FAIL] duckdb 缺於 {sys.executable}=本引擎不可跑;修法:via-rungate --family vrn --approve-install(裝進 via_vrn_312;只增不減)或 via-envgov apply --approve --only-kind REPAIR_BASE")
        return 3
    try:
        if verb == "run":
            rep = run(_arg(a, "--db"), _arg(a, "--zones"), _arg(a, "--ticker"), int(_arg(a, "--limit") or 0) or None, do_print="--json" not in a)
            if "--json" in a:
                print(json.dumps(rep, ensure_ascii=False, indent=1))
            return 0 if rep["verdict"] != "RED" else 1
        if verb == "show":
            rest = a[a.index("show") + 1:]
            key = next((x for i, x in enumerate(rest) if not x.startswith("--") and not (i > 0 and rest[i - 1] in ("--db", "--zones", "--ticker", "--limit"))), "")
            return show(key, _arg(a, "--db"))
        print(__doc__)
        return 2
    except BrokenPipeError:
        return 0


if __name__ == "__main__":
    sys.exit(main())
