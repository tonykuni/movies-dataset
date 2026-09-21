#!/usr/bin/env python3
# v0112→v0113(批685 操作員令:「年度財務報表頁將所有的資料截取下來後也將財報 TWSE/TPEX/MOPS 擷取年度資料去核對;
#   如果是歷史數據至少會有一起對起來就確認之資料是相同的;歷史數據跟報告數據都有的話以歷史數據為主;
#   其他截取下來的數據可以用加減法跟除法來驗證」):
#   量過:三方對照(批403)比的是 檔名×首頁×表格,**從來沒有對過官方**;VDF_ENG082 早就落了 tw_financial(yfinance 年度/季度),
#   兩邊各自成立、中間沒有線。加減除驗算則散在 vrn_finaudit(讀 Digest_Matrix,不讀正典表)與退役 MDL008——都不對著 vrn_report_financial。
#   操作員同日上傳的 VRN_Integrated_ReportDatabase_Engine(收容 _b685)也沒有這兩件:它的財報列只有 PERIOD_UNCLEAR 一種驗證態。
#   v0113 兩件,規則**只從冊上取**(VRN_FieldRules_SSOT rules.financial.verify,經 SUP_MDL749 rules();冊缺=ABSENT 誠實略,本檔零影子規則、零容差數字):
#   ① official_check():已報年度值 × 官方 tw_financial 同檔同年 → AGREE/ROUNDING/UNIT_SCALE/DIVERGE/ONLY_REPORT/NO_OFFICIAL_*;
#      **歷史數據為主**:官方有值 value_final 取官方,報告值留在 report_value 作證據不改不刪(正典表 vrn_report_financial 零觸碰);
#      每份另落一列 __alignment__:至少一項對得起來=CONFIRMED(操作員:「至少會有一起對起來」)。落 vrn_report_official_check(派生層重算)。
#   ② arith_check():同份同期間的正典值套冊上恆等式(毛利=營收−成本 · 毛利率=毛利÷營收 · 資產=負債+權益 …)→ PASS/FAIL/UNIT_SCALE/INSUFFICIENT/DIV_ZERO;
#      缺運算元就**點名缺哪個正典**(營業成本/營業費用/資產/負債/權益 目前不在 VRN_Financial_Synonyms_SSOT=候 register,登錄後零改碼即生效)。落 vrn_report_arith_check。
#   run 同輪跑兩者(--no-cross 一起關);--verify / --arith / --official 可單獨重算;status 印分佈;三十一檢 +㉖–㉛。
# 批631:本檔 v0111 的 docstring 裡有 `\d` / `\*` 這種**在字串裡不是合法跳脫**的序列,
#   而那個 docstring 不是 raw string。py3.11 只給 DeprecationWarning(預設不印),
#   **py3.12 給 SyntaxWarning 並印到終端**——工作站的矩陣輸出被它插進來,
#   連帶把 docstring 那一行也印出來,表格當場被切斷。
#   修法:那個 docstring 改成 r"""…"""(一個字元),語意零變。
# v0109→v0110(批563 操作員「同意」接收容冊的 MOPS 判定規則):
#   收容冊 VRN_AnnualExtract_SSOT 的 note 有四條判定規則(認「合計」· 應收/存貨取「淨額」·
#   權益與 ROE/BVPS 以「歸屬於母公司業主之權益」為準 · 稀釋 EPS 為主)。
#   量出來的缺口在**這一支的下游**:`parse_data_row` 把「淨額/合計/總額/總計」當雜訊字尾剝掉
#   去對正典名(對映本身沒錯),但 `rows.append` **沒有去重也沒有優先序**——
#   同一頁同時有「權益總計」與「歸屬於母公司業主之權益總計」時,兩列都進去,
#   誰先誰後就決定了 ROE 的分母。**那是一個不報錯、只安靜算錯的位置**:
#   拿含非控制權益的「權益總額」當分母,ROE 會偏低而且看起來完全正常。
#   本版**只標名次不刪列**(只增不減):每列多兩欄 `mops_rank` / `mops_why`,
#   由呼叫端取 max;輸的那列照樣留著,誰贏誰輸看得見。
#   排名實作向樞紐要(Zero-Hydra),樞紐或冊缺席=名次 0、行為與 v0109 一位元不差。
# -*- coding: utf-8 -*-
"""
v0108→v0109(批521 工作站實錄 via-ryg vrn RED ⑯:Windows 上 Path('/tmp/_b_.duckdb') 印成反斜線,字串比對永遠不等=判錯的紅燈;改 as_posix 比對;程式行為零改)
VRN_ENG074_FinancialPages — 財報頁表格擷取器(批241 波2;操作員選項2)
====================================================================
規格書 b236「Financial Data 76 欄」首波:報告後頁財務表→
VeritasSynonymEngine 科目對齊→時間軸 zip→vrn_report_financial。
機制(操作員 Gemini 對談之表格重建三步):
  ①財務頁判準:頁文含 ≥2 個核心科目(營業收入/毛利/營業利益/
    稅後/EPS)且有期間表頭列(≥2 個 20xx/兩碼Q/民國 tokens)
  ②表頭定位:期間 tokens 列=時間軸;E/F/(F)=ESTIMATE 狀態拆離
  ③數據列拆解:首數字切分點前=科目名(Gemini 防呆①)→
    VRN_Financial_Synonyms_SSOT.normalize_metric() 對齊 canonical;
    未命中=UNKNOWN 誠實列示候 register(不硬套);
    數值支援 千位逗號/負數 (1,250)/−/-;與時間軸 zip 對齊
落庫:vrn_report_financial(report_file,page,canonical,raw_label,
  period,status,value,raw_text)——派生層重算(同檔重寫);
  REPORT_STATED/ESTIMATE 隔離,永不冒充官方值(雙 SSOT)。

v0101→v0102(批403 操作員問「所有 VRN 檔案有拆解 FILENAME/首頁/財報頁
表格、讀取相互對照的引擎模組?」——盤點查出唯一缺口並補):
  盤點結論:①檔名拆解=ENG073 extract_one(四碼 ticker 逐驗 tw_listings
  名冊/BROKER_DICT 券商/三格式日期)在位 ②首頁=ENG072 v0105 分區+
  pdfplumber 法B 雙法逐區對照(AGREE/PARTIAL/DIVERGE)在位 ③財報頁表格
  =本引擎在位 ④檔名↔首頁對照=ENG073 交互驗證(ticker/官方名/升幅
  EXACT·ROUNDING_ONLY·FORMULA_MISMATCH·PARSE_SUSPECT)在位——但
  **財報頁表格從不與首頁/檔名對照**:v0101 只寫 vrn_report_financial,
  全樹亦只有本引擎讀它,ENG080 四點取的是 ENG073 的 vrn_report_metrics。
  故本版補第三邊,三角閉合(不另造引擎=Zero-Hydra,對照住在表格擁有者):
  crosscheck() 讀 vrn_report_basic(檔名邊)+vrn_report_metrics(首頁邊)
  ×vrn_report_financial(表格邊)→ vrn_report_crosscheck:
    · eps@期間:首頁 rx 值 vs 表格值 → AGREE(≤1%)/ROUNDING(≤5%)/
      UNIT_SCALE(比值近 1e±2/3/6=單位差,非錯)/DIVERGE/ONLY_FIRSTPAGE/
      ONLY_TABLE/MISSING_BOTH(誠實七態,不判死不覆寫)
    · ticker_on_fin_page:檔名 ticker 是否現身於該報告財報頁原文
    · report_date_vs_periods:報告日年 vs 表格最大 REPORT_STATED 年
      (表格已報年份晚於報告日=DATE_AHEAD 誠實可疑)
  派生層重算(同 report_file DELETE+INSERT);ENG073 兩表缺=誠實略過
  不 crash(先跑 ENG073);run 內建跑一次,亦可 --crosscheck 單獨重算。
v0106→v0107(批504 操作員上傳 VIA_VRNLogic_AllInOne_v0201 + financial_data_standardization):
  SSOT normalize_metric 未命中(UNKNOWN)的科目名,問 SUP_MDL748 財務邏輯橋要**第二意見**(AllInOne FINANCIAL_SYNONYMS +
  FDS 28 欄對照)。二見只寫在 raw_text 註記「[二見 total_assets@allinone]」與跑完的「候 register」清單,**canonical 不改**
  (單一真相仍是 VRN_Financial_Synonyms_SSOT;要不要登錄=操作員定;只增不減)。橋缺席=零回歸(照 v0106)。
用法:python3 VRN_ENG074_FinancialPages_v0107.py run [--dir 報告夾]
      [--no-cross] | --crosscheck | --verify | --arith | --official | --status | --selftest
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


def _resolve_db(db: Path | None) -> Path | None:
    r"""批244:庫路徑誠實解析(工作站雙 clone 債——mega 庫可能在
    Downloads\movies-dataset 替根)。顯式 db=信任直用(selftest 建新
    庫);預設=主路徑→替根探測;全缺=None 誠實停 rc2 不 traceback。

    批447:docstring 前面補 r —— 工作站每跑一次就印
    `SyntaxWarning: invalid escape sequence '\m'`。Windows 路徑寫進
    非 raw 字串是本樹第三次踩(Grid docstring 的 `\U` 是 SyntaxError,
    這個只是 warning,但一樣是把反斜線當逃逸字元在讀)。"""
    if db is not None:
        return Path(db)
    cands = [DB_TW]
    try:
        home = Path.home()
        rel = Path("movies-dataset/VeritasIntelligenceAnalytics/functional modules/VDF/output_hub/mega/vdf_tw_market.duckdb")
        cands += [home / "Downloads" / rel, home / rel]
    except Exception:
        pass
    for c in cands:
        if c and Path(c).exists():
            if Path(c) != DB_TW:
                print(f"[庫解析] 主路徑缺→改用替根庫:{c}(誠實提示)")
            return Path(c)
    print(f"[庫缺] {DB_TW} 不在且替根未尋獲=誠實停(rc2)。"
          "先跑 VDF_ENG065_DbImport 三包匯入,或確認 clone 根。")
    return None


import importlib.util
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
REPORTS = HERE / "input_reports"
#: 輸入規格正典(批442:與首頁全能引擎/ENG072 v0108/MDL139/MDL141 同一本冊)
SPEC_REL = Path("supportive modules") / "registry" / "VIA_InputConsole_Spec_v0100.json"


def _report_dirs(given: Path | None = None, *, no_incoming: bool = False) -> tuple[list[Path], str]:
    """報告夾律:--dir > 冊 user.vrn_dir > 冊 dir_default;**incoming 一律併入**。"""
    import json as _json
    dirs: list[Path] = []
    blk, user, why = {}, "", "冊不在 → 只用內建預設"
    sp = VIA / SPEC_REL
    if sp.exists():
        try:
            d = _json.loads(sp.read_text(encoding="utf-8-sig"))
            blk = d["families"]["vrn"]["input"]
            user = str((d.get("user") or {}).get("vrn_dir") or "").strip()
            why = f"冊 {sp.name}"
        except Exception as exc:
            why = f"冊讀取失敗 {type(exc).__name__} → 內建預設"
    if given is not None:
        dirs.append(given)
    elif user:
        q = Path(user)
        dirs.append(q if q.is_absolute() else VIA / q)
    else:
        dirs.append(VIA / blk.get("dir_default", "functional modules/VRN/input_reports"))
    inc = VIA / blk.get("incoming", "functional modules/VRN/input/incoming")
    if not no_incoming and inc not in dirs:
        dirs.append(inc)
    return dirs, why
DB_TW = VIA / "functional modules" / "VDF" / "output_hub" / "mega" / "vdf_tw_market.duckdb"

CORE_ITEMS = ("營業收入", "營業毛利", "毛利", "營業利益", "稅後", "淨利",
              "EPS", "每股盈餘", "Revenue", "Gross", "Operating")
PERIOD_RX = re.compile(r"(20\d{2}(?:\s*[EF(]|年)?|(?<!\d)\d{2}Q[1-4]"
                       r"|1[01]\d年?)[EF)]?", re.I)
PERIOD_TOKEN_RX = re.compile(          # 批615:+季在前 1Q25 / 半年 1H25 / FY25 / TTM
    r"^(20\d{2}|\d{2}Q[1-4]|[1-4]Q\d{2,4}|\d{2,4}H[12]|[12]H\d{2,4}"
    r"|FY\s*\d{2,4}|TTM|LTM|1[01]\d)(?:年)?\(?([EFA])?\)?$", re.I)
NUM_RX = re.compile(r"^\(?-?[\d,]+(?:\.\d+)?\)?%?$|^--?$|^—$")
FIRST_DIGIT_RX = re.compile(r"^(.*?[^\d(,\-])\s+(\(?-?\d[\d,]*"
                            r"(?:\.\d+)?.*)$")


def _syn():
    p = HERE / "VRN_Financial_Synonyms_SSOT.py"
    spec = importlib.util.spec_from_file_location("finsyn74", p)
    m = importlib.util.module_from_spec(spec)
    sys.modules["finsyn74"] = m
    spec.loader.exec_module(m)
    return m


_HUB748 = {"tried": False, "mod": None, "why": ""}


def _hub748():
    """批504:SUP_MDL748 財務邏輯橋尾版(第二意見);缺席=None(零回歸)。"""
    if _HUB748["tried"]:
        return _HUB748["mod"]
    _HUB748["tried"] = True
    try:
        hits = sorted((VIA / "supportive modules" / "70_VRN_Rules").glob("SUP_MDL748_FinancialLogicHub_v*.py"))
        if not hits:
            _HUB748["why"] = "SUP_MDL748 缺席"
            return None
        spec = importlib.util.spec_from_file_location("sup_mdl748_for_074", hits[-1])
        m = importlib.util.module_from_spec(spec)
        sys.modules["sup_mdl748_for_074"] = m
        spec.loader.exec_module(m)
        _HUB748["mod"] = m if hasattr(m, "second_opinion") else None
        _HUB748["why"] = "" if _HUB748["mod"] else f"{hits[-1].name} 無 second_opinion"
    except Exception as exc:
        _HUB748["why"] = f"橋載入失敗 {type(exc).__name__}:{str(exc)[:50]}"
    return _HUB748["mod"]


def _val(tok: str) -> float | None:
    tok = tok.strip().rstrip("%")
    if tok in ("--", "-", "—", ""):
        return None
    neg = tok.startswith("(") and tok.endswith(")")
    tok = tok.strip("()").replace(",", "")
    try:
        v = float(tok)
        return -v if neg else v
    except Exception:
        return None


# ═══ 批615:期間拆解 + 單位/幣別 ═════════════════════════════════════════════
# 操作員裁定(批615):**VRN 正典儲存層 = DuckDB**。本段補的是正典表的欄位,
# 不是換儲存層。
#
# 實害實錄:庫裡躺著 `revenue 營業收入淨額 2023 = 5839.0`——**沒有單位**。
# 百萬元還是千元?下游無從得知。既有的 UNIT_SCALE 只能在**事後**拿兩個值的比值
# 猜「大概差了 1000 倍」,那是推論不是資料。單位要在抽取當下就記下來。
#
# 還有一個抽取漏:`PERIOD_TOKEN_RX` 吃得下 `24Q1`(年在前),吃不下 `1Q25`
# (季在前)——那是外資報告最常見的寫法,整欄會被當成非表頭丟掉。
#
# 紀律:**解不出來就留空並說出原文**,不猜(零發明)。unit 尤其不准由數值大小反推。
_Q_RX = __import__("re").compile(r"^(?:([1-4])Q(\d{2}|\d{4})|(\d{2}|\d{4})Q([1-4]))$", __import__("re").I)
_H_RX = __import__("re").compile(r"^(?:([12])H(\d{2}|\d{4})|(\d{2}|\d{4})H([12]))$", __import__("re").I)
_FY_RX = __import__("re").compile(r"^FY\s*(\d{2}|\d{4})$", __import__("re").I)
_TTM_RX = __import__("re").compile(r"^(TTM|LTM)$", __import__("re").I)


def _yr4(y: str) -> int:
    r"""兩碼年補世紀;民國 3 碼(1[01]\d)轉西元。"""
    n = int(y)
    if len(y) == 4:
        return n + 1911 if 100 <= n <= 199 else n
    if len(y) == 3:
        return n + 1911
    return 2000 + n if n < 70 else 1900 + n


def period_parts(tok: str) -> dict:
    """期間 token → 結構。解不出的欄位留 None 並在 why 說出原文(不猜)。"""
    t = (tok or "").strip().strip("()").rstrip("年")
    est = ""
    m_ef = __import__("re").match(r"^(.*?)\(?([EFA])\)?$", t, __import__("re").I)
    if m_ef and m_ef.group(2):
        t, est = m_ef.group(1), m_ef.group(2).upper()
    for rx, kind in ((_Q_RX, "FQ"), (_H_RX, "FH")):
        m = rx.match(t)
        if m:
            a, ya, yb, b = m.groups()
            idx, yr = (a, ya) if a else (b, yb)
            return {"period_type": kind, "fiscal_year": _yr4(yr),
                    "fiscal_quarter": int(idx) if kind == "FQ" else None,
                    "half": int(idx) if kind == "FH" else None,
                    "estimate": est, "why": f"{kind}:{tok}"}
    m = _FY_RX.match(t)
    if m:
        return {"period_type": "FY", "fiscal_year": _yr4(m.group(1)),
                "fiscal_quarter": None, "half": None, "estimate": est, "why": f"FY:{tok}"}
    if _TTM_RX.match(t):
        return {"period_type": "TTM", "fiscal_year": None, "fiscal_quarter": None,
                "half": None, "estimate": est, "why": f"TTM:{tok}"}
    if __import__("re").fullmatch(r"20\d{2}|1[01]\d", t):
        return {"period_type": "FY", "fiscal_year": _yr4(t), "fiscal_quarter": None,
                "half": None, "estimate": est, "why": f"YEAR:{tok}"}
    return {"period_type": None, "fiscal_year": None, "fiscal_quarter": None,
            "half": None, "estimate": est, "why": f"UNPARSED:{tok}"}


# ── 單位宣告(頁面文字)。只認**寫出來的**,不由數值大小反推 ──────────────────
_UNIT_DECL = (
    (r"新台幣\s*百萬元|NT\$?\s*(?:mn?|million)\b|單位[::]\s*百萬", "TWD", 1e6, "百萬元"),
    (r"新台幣\s*十億元|NT\$?\s*bn\b|單位[::]\s*十億",             "TWD", 1e9, "十億元"),
    (r"新台幣\s*億元|單位[::]\s*億",                                 "TWD", 1e8, "億元"),
    (r"新台幣\s*千元|NT\$?\s*(?:k|thousand)\b|單位[::]\s*千",     "TWD", 1e3, "千元"),
    (r"新台幣\s*元|單位[::]\s*(?:新台幣)?元",                        "TWD", 1.0, "元"),
    (r"US\$?\s*(?:mn?|million)\b|美元\s*百萬",                     "USD", 1e6, "百萬美元"),
    (r"US\$?\s*(?:k|thousand)\b|美元\s*千",                        "USD", 1e3, "千美元"),
    (r"人民幣\s*百萬|RMB\s*(?:mn?|million)\b|CNY\s*(?:mn?)\b",    "CNY", 1e6, "百萬人民幣"),
)


def scan_unit_decl(text: str) -> dict:
    """整頁文字裡找單位宣告。找不到 = 三欄全 None + why 說明(誠實,不猜)。"""
    import re as _re
    for rx, cur, scale, label in _UNIT_DECL:
        m = _re.search(rx, text or "", _re.I)
        if m:
            return {"unit": label, "currency": cur, "scale": scale,
                    "why": f"PAGE_DECL:{m.group(0)[:24]}"}
    return {"unit": None, "currency": None, "scale": None,
            "why": "NO_DECL(頁面沒有寫單位;不由數值大小反推)"}


# 語意單位:比率與倍數不吃頁面的金額單位(毛利率永遠是 %,PER 永遠是倍)
_PCT = ("margin", "yoy", "qoq", "growth", "roe", "roa", "roic", "yield", "率")
_MULT = ("per", "pbr", "psr", "ev_ebitda", "倍")


def unit_for_row(canonical: str, raw_label: str, page_unit: dict) -> dict:
    key = f"{canonical or ''} {raw_label or ''}".lower()
    if any(k in key for k in _PCT):
        return {"unit": "%", "currency": None, "scale": 1.0, "why": "SEMANTIC:比率"}
    if any(k in key for k in _MULT):
        return {"unit": "x", "currency": None, "scale": 1.0, "why": "SEMANTIC:倍數"}
    if "eps" in key or "每股" in key:
        cur = page_unit.get("currency") or "TWD"
        return {"unit": f"{cur}/股", "currency": cur, "scale": 1.0, "why": "SEMANTIC:每股"}
    return dict(page_unit)


FIN_COLS_B615 = ("period_type", "fiscal_year", "fiscal_quarter", "period_src",
                 "unit", "currency", "scale", "unit_src")
FIN_COLS_B615_SQL = ("VARCHAR", "INTEGER", "INTEGER", "VARCHAR",
                     "VARCHAR", "VARCHAR", "DOUBLE", "VARCHAR")


def migrate_financial_cols(con) -> list:
    """只增不減的欄位遷移:既有列保持原值,新欄先留 NULL(誠實=還沒重抽)。"""
    added = []
    for c, t in zip(FIN_COLS_B615, FIN_COLS_B615_SQL):
        try:
            con.execute(f'ALTER TABLE vrn_report_financial ADD COLUMN IF NOT EXISTS "{c}" {t}')
            added.append(c)
        except Exception:
            pass
    return added


def parse_header(line: str) -> list[tuple[str, str]] | None:
    """期間表頭列→[(period, status)];<2 tokens=非表頭"""
    out = []
    for tok in line.split():
        m = PERIOD_TOKEN_RX.match(tok)
        if not m:
            continue
        p = m.group(1)
        if re.match(r"^1[01]\d$", p):
            p = str(int(p) + 1911)                 # 民國年
        st = "ESTIMATE" if (m.group(2) or "").upper() in ("E", "F") \
            else "REPORT_STATED"
        out.append((p, st))
    return out if len(out) >= 2 else None


_MOPS = {"mod": None, "tried": False}


def _mops(raw_label: str, canonical: str = "") -> tuple:
    """批563:向樞紐要 MOPS 列優先序(名次, 為什麼)。
    樞紐或收容冊缺席 = (0, "") = 與 v0109 行為完全相同(誠實退路,不自己編一套)。"""
    if not _MOPS["tried"]:
        _MOPS["tried"] = True
        try:
            hits = sorted((VIA / "supportive modules" / "70_VRN_Rules").glob(
                "SUP_MDL749_VRNFieldRuleHub_v*.py"))
            if hits:
                import importlib.util as _il
                sp = _il.spec_from_file_location("_vrn_hub_e74", hits[-1])
                m = _il.module_from_spec(sp)
                sp.loader.exec_module(m)
                _MOPS["mod"] = m
        except Exception:
            _MOPS["mod"] = None
    m = _MOPS["mod"]
    if m is None or not hasattr(m, "mops_rank"):
        return 0, ""
    try:
        return m.mops_rank(raw_label, canonical)
    except Exception:
        return 0, ""


# ══════════════ 批685:官方年度核對(歷史數據為主)+ 加減除驗算 ══════════════
#: 規則只從冊上取(VRN_FieldRules_SSOT rules.financial.verify);引擎不帶數字、不帶影子規則(L05/L30)。
OFFICIAL_COLS = ("report_file", "ticker", "canonical", "period", "report_value",
                 "report_scale", "official_value", "official_col", "official_period",
                 "ratio", "state", "winner", "value_final", "note", "checked_at")
ARITH_COLS = ("report_file", "ticker", "period", "rule_id", "zh", "target",
              "expected", "actual", "diff", "state", "note", "checked_at")


def _hub749():
    """批685:規則樞紐尾版(與 _mops 同一個載入器,不再抄一份);缺席=None。"""
    if not _MOPS["tried"]:
        _mops("", "")
    return _MOPS["mod"]


def verify_rules() -> dict:
    """財報驗證規則(官方欄位對照 + 恆等式)——只從冊上取:SUP_MDL749.rules() → rules.financial.verify。
    樞紐/冊/段缺 = ABSENT 誠實(冊缺就是不驗,不是自己編一套)。"""
    m = _hub749()
    if m is None or not hasattr(m, "rules"):
        return {"state": "ABSENT", "why": "SUP_MDL749 樞紐缺席"}
    try:
        book = m.rules()
    except Exception as exc:
        return {"state": "RED", "why": f"rules() 讀不動 {type(exc).__name__}"}
    v = ((book.get("rules") or {}).get("financial") or {}).get("verify")
    if not isinstance(v, dict) or not v.get("identities"):
        return {"state": "ABSENT", "why": "冊無 rules.financial.verify(批685 段)"}
    out = dict(v)
    out["state"] = "OK"
    return out


def _ticker_of(con, stem: str) -> tuple[str, str]:
    """(ticker, report_date) 自 vrn_report_basic;表缺=('','')。"""
    if not _has_table(con, "vrn_report_basic"):
        return "", ""
    b = con.execute("SELECT ticker, report_date FROM vrn_report_basic WHERE report_file=?",
                    [stem]).fetchone()
    return (str(b[0] or ""), str(b[1] or "")) if b else ("", "")


def _stated_annual(con, stem: str) -> tuple[dict, dict]:
    """已報(REPORT_STATED)年度列 → {(canonical, year): (value, scale)};另回 {ESTIMATE, NOT_ANNUAL} 各幾列。
    年度 = period_type 為 FY/空 且 fiscal_year 在;舊列(批615 前 fiscal_year NULL)退到 period 前四碼。"""
    out, tally = {}, {"NOT_ANNUAL": 0, "ESTIMATE": 0}
    for cn, per, st, val, sc, fy, pt in con.execute(
            "SELECT canonical, period, status, value, scale, fiscal_year, period_type "
            "FROM vrn_report_financial WHERE report_file=? AND value IS NOT NULL "
            "AND canonical IS NOT NULL AND canonical <> ''", [stem]).fetchall():
        if st != "REPORT_STATED":
            tally["ESTIMATE"] += 1
            continue
        if pt and pt not in ("FY", "YEAR"):
            tally["NOT_ANNUAL"] += 1
            continue
        p = str(per or "")
        year = fy if fy else (int(p[:4]) if (len(p) == 4 and p.isdigit()) else None)
        if year is None:
            tally["NOT_ANNUAL"] += 1
            continue
        out.setdefault((cn, int(year)), (float(val), (float(sc) if sc else None)))
    return out, tally


def _official_rows(con, table: str, ticker: str, forms: list, annual: str, want: list) -> dict:
    """{year: {"__period__": 期末日, column: value}} 自官方表(只取年度列);無=空 dict。"""
    if not ticker:
        return {}
    tks = [f.replace("{code}", ticker) for f in forms] or [ticker]
    sel = "".join(f', "{c}"' for c in want)
    ph = ",".join("?" * len(tks))
    try:
        rows = con.execute(f'SELECT "Period"{sel} FROM {table} WHERE "Ticker" IN ({ph}) '
                           f'AND "Period_Type" = ?', tks + [annual]).fetchall()
    except Exception:
        return {}
    out = {}
    for r in rows:
        per = str(r[0] or "")
        if not per[:4].isdigit():
            continue
        out.setdefault(int(per[:4]), {"__period__": per, **{c: r[i + 1] for i, c in enumerate(want)}})
    return out


def official_check(con, stems: list[str] | None = None, do_print: bool = True) -> dict:
    """官方年度核對(批685):已報年度值 × tw_financial 同檔同年 → 誠實態;**歷史數據為主**(官方有值 value_final 取官方)。
    正典表 vrn_report_financial 零觸碰;結果落 vrn_report_official_check(派生層重算=同 report_file DELETE+INSERT)。"""
    from datetime import datetime
    rules = verify_rules()
    if rules.get("state") != "OK":
        if do_print:
            print(f"  [官方核對] 規則冊缺={rules.get('why')}=誠實略(不驗不是驗過)")
        return {"skipped": "NO_RULES", "why": rules.get("why")}
    if not _has_table(con, "vrn_report_financial"):
        if do_print:
            print("  [官方核對] vrn_report_financial 未建=誠實略(先 run)")
        return {"skipped": "NO_FINANCIAL"}
    off = rules.get("official") or {}
    table = str(off.get("table") or "tw_financial")
    if not _has_table(con, table):
        if do_print:
            print(f"  [官方核對] 官方表 {table} 不在=誠實略;補料=VDF_ENG082_FinStatements run --only <代碼>"
                  "(同意閘 VIA_NET_CONSENT 你自設,我不代設)")
        return {"skipped": "NO_OFFICIAL_TABLE", "table": table}
    cols = dict(off.get("columns") or {})
    have = {r[0] for r in con.execute(f"DESCRIBE {table}").fetchall()}
    want = sorted({c for c in cols.values() if c in have})
    forms = list(off.get("ticker_forms") or ["{code}.TW", "{code}.TWO"])
    annual = str(off.get("period_type_annual") or "annual")
    con.execute("""CREATE TABLE IF NOT EXISTS vrn_report_official_check(
        report_file VARCHAR, ticker VARCHAR, canonical VARCHAR, period VARCHAR,
        report_value DOUBLE, report_scale DOUBLE, official_value DOUBLE, official_col VARCHAR,
        official_period VARCHAR, ratio DOUBLE, state VARCHAR, winner VARCHAR,
        value_final DOUBLE, note VARCHAR, checked_at VARCHAR)""")
    if stems is None:
        stems = [r[0] for r in con.execute(
            "SELECT DISTINCT report_file FROM vrn_report_financial").fetchall()]
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    tally: dict[str, int] = {}
    n_rows = 0
    for stem in stems:
        ticker, _rd = _ticker_of(con, stem)
        stated, sk = _stated_annual(con, stem)
        orows = _official_rows(con, table, ticker, forms, annual, want) if ticker else {}
        rows, hits = [], 0
        for (cn, year), (val, sc) in sorted(stated.items()):
            col = cols.get(cn)
            rv = val * sc if sc else val
            ov, oper = None, ""
            if not ticker:
                st, note = "NO_TICKER", "報告無在冊四碼"
            elif not col:
                st, note = "NO_OFFICIAL_COLUMN", f"正典 {cn} 無官方對照欄(冊 columns 未列)"
            elif col not in have:
                st, note = "NO_OFFICIAL_COLUMN", f"官方表無欄 {col}"
            elif not orows:
                st, note = "NO_OFFICIAL_TICKER", f"{table} 無 {ticker}(先 VDF_ENG082 run --only {ticker})"
            elif year not in orows:
                st, note = "NO_OFFICIAL_PERIOD", f"{table} 有 {ticker} 但無 {year} 年度"
            else:
                _ov = orows[year].get(col)
                ov = float(_ov) if _ov is not None else None
                oper = str(orows[year].get("__period__") or "")
                st0, _r0 = compare_values(rv, ov)
                st = {"ONLY_FIRSTPAGE": "ONLY_REPORT", "ONLY_TABLE": "ONLY_OFFICIAL"}.get(st0, st0)
                note = (("單位未宣告(scale NULL)=不反推;" if sc is None else "")
                        + f"報告 {rv:g} vs 官方 {'—' if ov is None else format(ov, 'g')}")
            ratio = (ov / rv) if (ov is not None and rv) else None
            if st in ("AGREE", "ROUNDING", "UNIT_SCALE"):
                hits += 1
            winner = "OFFICIAL" if ov is not None else "REPORT"
            vfinal = ov if ov is not None else rv
            note += " · 歷史數據為主:value_final=官方" if winner == "OFFICIAL" else " · 官方無值:value_final=報告"
            rows.append((stem, ticker, cn, str(year), rv, sc, ov, col or "", oper, ratio,
                         st, winner, vfinal, note, ts))
        # 每份一列 __alignment__:至少一項對得起來=CONFIRMED(操作員:「至少會有一起對起來」)
        if not ticker:
            al, aln = "NO_TICKER", "報告無在冊四碼"
        elif not stated:
            al, aln = "NO_STATED", f"報告無已報年度值(預估 {sk['ESTIMATE']} 列 · 非年度 {sk['NOT_ANNUAL']} 列)"
        elif not orows:
            al, aln = "NO_OFFICIAL_TICKER", f"{table} 無 {ticker}"
        elif hits:
            al, aln = "CONFIRMED", f"{hits}/{len(stated)} 項對得起來(AGREE/ROUNDING/UNIT_SCALE)"
        else:
            al, aln = "UNCONFIRMED", f"0/{len(stated)} 項對得起來(人工核 PDF)"
        rows.append((stem, ticker, "__alignment__", "", None, None, None, "", "", None,
                     al, "", None, aln, ts))
        con.execute("DELETE FROM vrn_report_official_check WHERE report_file=?", [stem])
        for r in rows:
            con.execute("INSERT INTO vrn_report_official_check VALUES ("
                        + ",".join("?" * len(OFFICIAL_COLS)) + ")", list(r))
            tally[r[10]] = tally.get(r[10], 0) + 1
        n_rows += len(rows)
    if do_print:
        head = " · ".join(f"{k} {v}" for k, v in sorted(tally.items(), key=lambda x: -x[1]))
        print(f"  [官方核對] {len(stems)} 件 × {table} 年度 → {n_rows} 列 · {head}")
    return {"reports": len(stems), "rows": n_rows, "tally": tally}


def _identity_eval(rule: dict, vals: dict) -> tuple:
    """回 (state, expected, actual, diff, note)。誠實五態:PASS/FAIL/UNIT_SCALE/INSUFFICIENT/DIV_ZERO。容差只從冊上取。"""
    ka, kb, kt, op = rule.get("a"), rule.get("b"), rule.get("target"), rule.get("op")
    a, b, t = vals.get(ka), vals.get(kb), vals.get(kt)
    missing = [k for k, v in ((ka, a), (kb, b), (kt, t)) if v is None]
    if missing:
        return ("INSUFFICIENT", None, t, None,
                "缺 " + "/".join(str(k) for k in missing) + "(不在本份正典列;候 register 或報告未載)")
    if op == "sub":
        exp = a - b
    elif op == "add":
        exp = a + b
    elif op in ("div", "div_pct"):
        if b == 0:
            return "DIV_ZERO", None, t, None, f"{kb}=0"
        exp = a / b * (100.0 if op == "div_pct" else 1.0)
    else:
        return "INSUFFICIENT", None, t, None, f"未知運算 {op}(冊)"
    if op == "div_pct":
        tol = rule.get("tol_abs_pp")
        if tol is None:
            return "INSUFFICIENT", round(exp, 4), t, None, "冊未給 tol_abs_pp"
        tol = float(tol)
        diff = abs(t - exp)
        if diff <= tol:
            st = "PASS"
        elif abs(t * 100.0 - exp) <= tol:
            st, diff = "UNIT_SCALE", abs(t * 100.0 - exp)
        else:
            st = "FAIL"
        return st, round(exp, 4), t, round(diff, 4), f"|{t:g}−{exp:.2f}|={diff:.2f}pp · 容差 {tol:g}pp(冊)"
    tol = rule.get("tol_rel")
    if tol is None:
        return "INSUFFICIENT", round(exp, 4), t, None, "冊未給 tol_rel"
    tol = float(tol)
    base = abs(exp) if exp else abs(t)
    if not base:
        return ("PASS" if t == exp else "FAIL"), exp, t, 0.0, ("兩邊皆 0" if t == exp else "期望 0 實際非 0")
    diff = abs(t - exp) / base
    st = "PASS" if diff <= tol else "FAIL"
    return st, round(exp, 4), t, round(diff, 6), f"相對差 {diff * 100:.2f}% · 容差 {tol * 100:g}%(冊)"


def arith_check(con, stems: list[str] | None = None, do_print: bool = True) -> dict:
    """加減除驗算(批685):同份同期間的正典值套冊上恆等式;缺運算元=INSUFFICIENT 並點名(L92 哨兵要給得出下一步)。
    落 vrn_report_arith_check(派生層重算);正典表零觸碰。三值全缺的期間不落列(不是驗算對象,不是缺)。"""
    from datetime import datetime
    rules = verify_rules()
    if rules.get("state") != "OK":
        if do_print:
            print(f"  [驗算] 規則冊缺={rules.get('why')}=誠實略")
        return {"skipped": "NO_RULES", "why": rules.get("why")}
    if not _has_table(con, "vrn_report_financial"):
        if do_print:
            print("  [驗算] vrn_report_financial 未建=誠實略(先 run)")
        return {"skipped": "NO_FINANCIAL"}
    ids = list(rules.get("identities") or [])
    con.execute("""CREATE TABLE IF NOT EXISTS vrn_report_arith_check(
        report_file VARCHAR, ticker VARCHAR, period VARCHAR, rule_id VARCHAR, zh VARCHAR,
        target VARCHAR, expected DOUBLE, actual DOUBLE, diff DOUBLE, state VARCHAR,
        note VARCHAR, checked_at VARCHAR)""")
    if stems is None:
        stems = [r[0] for r in con.execute(
            "SELECT DISTINCT report_file FROM vrn_report_financial").fetchall()]
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    tally: dict[str, int] = {}
    missing_tally: dict[str, int] = {}
    n_rows = 0
    for stem in stems:
        ticker, _rd = _ticker_of(con, stem)
        byper: dict[str, dict] = {}
        for cn, per, val in con.execute(
                "SELECT canonical, period, value FROM vrn_report_financial WHERE report_file=? "
                "AND value IS NOT NULL AND canonical IS NOT NULL AND canonical <> ''",
                [stem]).fetchall():
            byper.setdefault(str(per), {}).setdefault(cn, float(val))
        rows = []
        for per in sorted(byper):
            vals = byper[per]
            for rule in ids:
                keys = (rule.get("a"), rule.get("b"), rule.get("target"))
                if not any(vals.get(k) is not None for k in keys):
                    continue                              # 三值全缺=不是驗算對象
                st, exp, act, diff, note = _identity_eval(rule, vals)
                if st == "INSUFFICIENT":
                    for k in keys:
                        if vals.get(k) is None:
                            missing_tally[str(k)] = missing_tally.get(str(k), 0) + 1
                rows.append((stem, ticker, per, rule.get("id"), rule.get("zh"), rule.get("target"),
                             exp, act, diff, st, note, ts))
        con.execute("DELETE FROM vrn_report_arith_check WHERE report_file=?", [stem])
        for r in rows:
            con.execute("INSERT INTO vrn_report_arith_check VALUES ("
                        + ",".join("?" * len(ARITH_COLS)) + ")", list(r))
            tally[r[9]] = tally.get(r[9], 0) + 1
        n_rows += len(rows)
    if do_print:
        head = " · ".join(f"{k} {v}" for k, v in sorted(tally.items(), key=lambda x: -x[1]))
        print(f"  [驗算] {len(stems)} 件 × {len(ids)} 條恆等式 → {n_rows} 列 · {head or '無可驗列'}")
        if missing_tally:
            top = sorted(missing_tally.items(), key=lambda kv: -kv[1])[:8]
            print("  [驗算] 缺運算元點名(候 register 進 VRN_Financial_Synonyms_SSOT=你定):"
                  + ", ".join(f"{k} ×{v}" for k, v in top))
    return {"reports": len(stems), "rows": n_rows, "tally": tally, "missing": missing_tally}


def parse_data_row(line: str, header: list, syn, hub=None) -> dict | None:
    """數據列:首數字切分→科目 normalize_metric→zip 時間軸"""
    m = FIRST_DIGIT_RX.match(line.strip())
    if not m:
        return None
    label = m.group(1).strip(" :‧·")
    toks = m.group(2).split()
    vals = [_val(t) for t in toks if NUM_RX.match(t)]
    if not label or len(vals) < 2:
        return None
    def _canon(lbl: str) -> str:
        r = syn.normalize_metric(lbl)
        if r and r != lbl:                     # SSOT 未命中=回原字串
            return r
        for suf in ("淨額", "合計", "總額", "總計"):
            if lbl.endswith(suf):
                r = syn.normalize_metric(lbl[:-len(suf)])
                if r and r != lbl[:-len(suf)]:
                    return r
        return ""
    canon = _canon(label)
    alt = ""
    if not canon and hub is not None:
        # 批504:UNKNOWN 才問第二意見;只建議(raw_text 註記 + 候 register),canonical 不改
        try:
            alts = hub.second_opinion(label).get("alts") or []
            alt = "/".join(f"{a['canonical']}@{a['src']}" for a in alts)
        except Exception:
            alt = ""
    cells = []
    for (per, st), v in zip(header, vals):
        if v is not None:
            cells.append({"period": per, "status": st, "value": v})
    return {"raw_label": label, "canonical": canon, "cells": cells, "alt": alt} \
        if cells else None


def is_financial_page(text: str) -> bool:
    hits = sum(1 for k in CORE_ITEMS if k in text)
    return hits >= 2 and len(PERIOD_RX.findall(text)) >= 2


def _intake_bridge():
    """批466:受理三類的判準綁**ENG072 尾版**(它是收件的正主),不另抄一份。
       橋缺席=退回本檔原本的 PDF-only 行為並講出因由(零回歸)。"""
    try:
        import importlib.util as _ilu
        c = sorted(Path(__file__).resolve().parent.glob("VRN_ENG072_FirstPageText_v*.py"))
        if not c:
            return None, "VRN_ENG072_FirstPageText_v*.py 缺席"
        sp = _ilu.spec_from_file_location("eng072_for_074", c[-1])
        m = _ilu.module_from_spec(sp)
        sp.loader.exec_module(m)
        if not hasattr(m, "kind_of"):
            return None, f"{c[-1].name} 無 kind_of(舊版;PDF-only 退路)"
        return m, ""
    except Exception as exc:
        return None, f"ENG072 橋載入失敗 {type(exc).__name__}:{str(exc)[:50]}"


def extract_docx_fin(p: Path) -> tuple[list[dict], str]:
    """WORD 財報表格(批466)。**零相依**:.docx 本來就是 zip,`<w:tbl>` 就是表。
       Zero-Hydra:**不另造解析器**——把每個 `<w:tr>` 的儲存格併成一行文字,
       交回本檔既有的 parse_header / parse_data_row / _syn(與 PDF 道同一套規則,
       所以同一份報告換成 Word 出的值會一致)。
       WORD 無頁界概念 → page 記 0,並在 raw_text 標「WORD 表N」,不假裝有頁碼。"""
    import zipfile
    import xml.etree.ElementTree as ET
    W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    try:
        with zipfile.ZipFile(p) as z:
            if "word/document.xml" not in z.namelist():
                return [], "zip 內無 word/document.xml"
            root = ET.fromstring(z.read("word/document.xml"))
    except zipfile.BadZipFile:
        return [], "不是 zip(可能是舊版 .doc 二進位)"
    except Exception as exc:
        return [], f"{type(exc).__name__}:{str(exc)[:50]}"

    def cell_text(tc):
        return " ".join(t.text for t in tc.iter(f"{W}t") if t.text).strip()

    syn = _syn()
    hub = _hub748()
    rows, ntbl = [], 0
    for tbl in root.iter(f"{W}tbl"):
        ntbl += 1
        lines = []
        for tr in tbl.iter(f"{W}tr"):
            cells = [cell_text(tc) for tc in tr.iter(f"{W}tc")]
            line = "  ".join(c for c in cells if c)
            if line:
                lines.append(line)
        if not lines or not is_financial_page("\n".join(lines)):
            continue
        header = None
        for line in lines:
            h = parse_header(line)
            if h:
                header = h
                continue
            if not header:
                continue
            d = parse_data_row(line, header, syn, hub)
            if not d:
                continue
            _mr, _mw = _mops(d["raw_label"], d["canonical"])
            for c in d["cells"]:
                rows.append({
                    "report_file": p.stem, "page": 0,
                    "canonical": d["canonical"],
                    "raw_label": d["raw_label"][:60],
                    "mops_rank": _mr, "mops_why": _mw,
                    "period": c["period"], "status": c["status"],
                    "value": c["value"],
                    **_b615_cols(c["period"], d["canonical"], d["raw_label"],
                                 {"unit": None, "currency": None, "scale": None,
                                  "why": "WORD 道無頁面單位宣告來源"}),
                    "raw_text": f"[WORD 表{ntbl}] " + str(c.get("raw_text", line))[:60] + (f" [二見 {d['alt']}]" if d.get("alt") else ""),
                })
    return rows, ("" if rows else f"{ntbl} 個表,無一通過財報頁判準")


def _b615_cols(period: str, canonical: str, raw_label: str, page_unit: dict) -> dict:
    """批615:把期間拆解與單位解析組成 8 個新欄。解不出就留 None 並在 *_src 說原文。"""
    pp = period_parts(period)
    uu = unit_for_row(canonical, raw_label, page_unit)
    return {"period_type": pp["period_type"], "fiscal_year": pp["fiscal_year"],
            "fiscal_quarter": pp["fiscal_quarter"], "period_src": pp["why"],
            "unit": uu["unit"], "currency": uu["currency"],
            "scale": uu["scale"], "unit_src": uu["why"]}


def extract_pdf_fin(p: Path) -> list[dict]:
    """頁 2..N 財務頁表格;回 rows(每列=科目×期間×值)"""
    try:
        import fitz
    except Exception:
        return []
    syn = _syn()
    hub = _hub748()
    rows = []
    try:
        with fitz.open(str(p)) as doc:
            for pno in range(1, doc.page_count):
                text = doc[pno].get_text("text", sort=True)
                if not is_financial_page(text):
                    continue
                pu = scan_unit_decl(text)      # 批615:單位宣告每頁掃一次
                header = None
                for line in text.splitlines():
                    h = parse_header(line)
                    if h:
                        header = h
                        continue
                    if header:
                        d = parse_data_row(line, header, syn, hub)
                        if d:
                            for c in d["cells"]:
                                rows.append({
                                    "report_file": p.stem, "page": pno + 1,
                                    "canonical": d["canonical"],
                                    "raw_label": d["raw_label"][:60],
                                    "period": c["period"],
                                    "status": c["status"],
                                    "value": c["value"],
                                    "raw_text": line.strip()[:120] + (f" [二見 {d['alt']}]" if d.get("alt") else ""),
                                    **_b615_cols(c["period"], d["canonical"],
                                                 d["raw_label"], pu)})
    except Exception:
        return rows
    return rows


# ===== 批403:三方對照(檔名 × 首頁 × 財報頁表格)=====================
CROSS_COLS = ("report_file", "ticker", "dimension", "period",
              "first_page_value", "table_value", "ratio", "state", "note",
              "checked_at")
# 單位差常見倍率(千元/百萬元/元 之間;比值落此附近=UNIT_SCALE 非 DIVERGE)
UNIT_FACTORS = (1e3, 1e2, 1e6, 1e-2, 1e-3, 1e-6)


def compare_values(a: float | None, b: float | None) -> tuple[str, float | None]:
    """a=首頁邊值 b=表格邊值;回 (state, ratio=b/a)。誠實七態,不判死。"""
    if a is None and b is None:
        return "MISSING_BOTH", None
    if a is None:
        return "ONLY_TABLE", None
    if b is None:
        return "ONLY_FIRSTPAGE", None
    if a == 0 or b == 0:
        return ("AGREE", 1.0) if a == b else ("DIVERGE", None)
    ratio = b / a
    diff = abs(b - a) / abs(a)
    if diff <= 0.01:
        return "AGREE", ratio
    if diff <= 0.05:
        return "ROUNDING", ratio
    for f in UNIT_FACTORS:
        if abs(ratio / f - 1.0) <= 0.02:
            return "UNIT_SCALE", ratio
    return "DIVERGE", ratio


def _has_table(con, name: str) -> bool:
    try:
        con.execute(f"SELECT 1 FROM {name} LIMIT 1")
        return True
    except Exception:
        return False


def crosscheck(con, stems: list[str] | None = None,
               do_print: bool = True) -> dict:
    """三方對照落 vrn_report_crosscheck;ENG073 兩表缺=誠實略過(不 crash)"""
    from datetime import datetime
    if not _has_table(con, "vrn_report_financial"):
        if do_print:
            print("  [對照] vrn_report_financial 未建=誠實略(先 run)")
        return {"skipped": "NO_FINANCIAL"}
    if not (_has_table(con, "vrn_report_basic")
            and _has_table(con, "vrn_report_metrics")):
        if do_print:
            print("  [對照] ENG073 兩表(basic/metrics)缺=誠實略過,"
                  "不假綠;先跑 VRN_ENG073_ReportStructuredDB run")
        return {"skipped": "NO_ENG073"}
    con.execute(f"""CREATE TABLE IF NOT EXISTS vrn_report_crosscheck(
        report_file VARCHAR, ticker VARCHAR, dimension VARCHAR,
        period VARCHAR, first_page_value DOUBLE, table_value DOUBLE,
        ratio DOUBLE, state VARCHAR, note VARCHAR, checked_at VARCHAR)""")
    if stems is None:
        stems = [r[0] for r in con.execute(
            "SELECT DISTINCT report_file FROM vrn_report_financial").fetchall()]
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    tally: dict[str, int] = {}
    rows_all = []
    for stem in stems:
        b = con.execute(
            "SELECT ticker, report_date FROM vrn_report_basic "
            "WHERE report_file=?", [stem]).fetchone()
        ticker, rdate = (b[0] or "", b[1] or "") if b else ("", "")
        fp = {}                                   # 首頁邊:(metric, period)→值
        for mt, per, val in con.execute(
                "SELECT metric, period, value FROM vrn_report_metrics "
                "WHERE report_file=? AND value IS NOT NULL", [stem]).fetchall():
            fp.setdefault((mt, per), val)
        tb = {}                                   # 表格邊:(canonical, period)→值
        for cn, per, val in con.execute(
                "SELECT canonical, period, value FROM vrn_report_financial "
                "WHERE report_file=? AND value IS NOT NULL", [stem]).fetchall():
            if cn:
                tb.setdefault((cn, per), val)
        rows = []
        # ① eps(兩邊共有之正典鍵;eps_diluted 併看,表格優先精確鍵)
        keys = {k for k in fp if k[0] == "eps"} | \
               {k for k in tb if k[0] in ("eps", "eps_diluted")}
        for _m, per in sorted({(("eps"), k[1]) for k in keys}):
            a = fp.get(("eps", per))
            b2 = tb.get(("eps", per))
            if b2 is None:
                b2 = tb.get(("eps_diluted", per))
            st, ratio = compare_values(a, b2)
            rows.append((stem, ticker, "eps", per, a, b2, ratio, st,
                         "首頁 rx × 財報頁表格", ts))
        # ② 表格獨有之正典科目(首頁無對照=誠實列 ONLY_TABLE 供人工核)
        for (cn, per), val in sorted(tb.items()):
            if cn in ("eps", "eps_diluted"):
                continue
            rows.append((stem, ticker, cn, per, None, val, None,
                         "ONLY_TABLE", "表格獨有科目(首頁無同名值)", ts))
        # ③ 檔名 ticker ↔ 財報頁原文(第三邊:檔名 × 表格)
        if ticker:
            hit = con.execute(
                "SELECT count(*) FROM vrn_report_financial WHERE "
                "report_file=? AND raw_text LIKE ?",
                [stem, f"%{ticker}%"]).fetchone()[0]
            rows.append((stem, ticker, "ticker_on_fin_page", "", None, None,
                         None,
                         "TICKER_ON_FIN_PAGE" if hit else "TICKER_NOT_ON_FIN_PAGE",
                         f"財報頁原文命中 {hit} 列(未命中非錯=多數表格不重印代號)",
                         ts))
        else:
            rows.append((stem, "", "ticker_on_fin_page", "", None, None, None,
                         "NO_TICKER", "檔名無在冊四碼(研討會/晨報誠實非個股)",
                         ts))
        # ④ 報告日 ↔ 表格已報期間(表格已報年晚於報告日=誠實可疑)
        stated = con.execute(
            "SELECT max(CAST(substr(period,1,4) AS INTEGER)) FROM "
            "vrn_report_financial WHERE report_file=? AND status='REPORT_STATED'"
            " AND substr(period,1,4) SIMILAR TO '[0-9]{4}'", [stem]).fetchone()
        smax = stated[0] if stated else None
        ryear = int(rdate[:4]) if rdate[:4].isdigit() else None
        if ryear is None:
            st4, note4 = "NO_DATE", "檔名無可解析日期"
        elif smax is None:
            st4, note4 = "NO_TABLE_STATED", "表格無已報期間(全為預估或無表)"
        elif smax > ryear:
            st4, note4 = "DATE_AHEAD", f"表格已報 {smax} > 報告日 {ryear}=誠實可疑"
        else:
            st4, note4 = "DATE_CONSISTENT", f"表格已報 {smax} ≤ 報告日 {ryear}"
        rows.append((stem, ticker, "report_date_vs_periods", rdate,
                     float(ryear) if ryear else None,
                     float(smax) if smax else None, None, st4, note4, ts))
        con.execute("DELETE FROM vrn_report_crosscheck WHERE report_file=?",
                    [stem])                        # 派生層重算
        for r in rows:
            con.execute("INSERT INTO vrn_report_crosscheck VALUES "
                        "(?,?,?,?,?,?,?,?,?,?)", list(r))
            tally[r[7]] = tally.get(r[7], 0) + 1
        rows_all += rows
    if do_print:
        head = " · ".join(f"{k} {v}" for k, v in sorted(
            tally.items(), key=lambda x: -x[1]))
        print(f"  [對照] {len(stems)} 件 × 三邊 → {len(rows_all)} 列 · {head}")
    return {"reports": len(stems), "rows": len(rows_all), "tally": tally}


def run(src: Path | None = None, db: Path | None = None,
        cross: bool = True, *, no_incoming: bool = False) -> int:
    import duckdb
    # 批442:報告夾綁**輸入規格正典**(與首頁全能引擎、ENG072 v0108、MDL141 同一本冊)。
    # v0103 把 input_reports 寫死成唯一預設,而操作員的 64 份報告住在 input/incoming
    # ——ENG072 v0107 犯過一模一樣的病(批438),同一個錯不該在第二支引擎再犯一次。
    dirs, spec_why = _report_dirs(src, no_incoming=no_incoming)
    # 批466:收件三類(WORD/PDF/IMAGE)。v0105 寫死 `d.glob("*.pdf")`——
    # ①站 ENG072 收得下的 docx 與影像,到這一站**連被看見都沒有**
    # (實測:corpus 三件,這裡只報「1 件 PDF」)。判準綁 ENG072 尾版。
    _e72, _e72_why = _intake_bridge()
    def _kind(q: Path) -> str:
        if _e72 is not None:
            return _e72.kind_of(q)
        return "pdf" if q.suffix.lower() == ".pdf" else ""
    pdfs, diag = [], []
    for d in dirs:
        got = sorted(x for x in d.iterdir() if x.is_file() and _kind(x)) if d.is_dir() else []
        _np = sum(1 for x in got if _kind(x) == "pdf")
        diag.append((d, "夾不存在" if not d.is_dir()
                     else ("夾是空的" if not any(d.iterdir())
                           else f"{len(got)} 件(PDF {_np}/WORD "
                                f"{sum(1 for x in got if _kind(x) == 'word')}/影像 "
                                f"{sum(1 for x in got if _kind(x) == 'image')})")))
        pdfs.extend(got)
    pdfs = sorted({f.resolve(): f for f in pdfs}.values())
    if not pdfs:
        print(f"[財報頁] 無報告件(誠實;先跑缺件搜集)· 夾律={spec_why}"
              + (f" · 收件判準退路({_e72_why})" if _e72_why else ""))
        for d, st in diag:
            print(f"   · {d} → {st}")
        return 2
    src = dirs[0]
    print(f"[財報頁] 夾律={spec_why};取件 {len(pdfs)} 份 · "
          + " · ".join(f"{d.name}={st}" for d, st in diag))
    dbp = _resolve_db(Path(db) if db else None)
    if dbp is None:
        return 2
    con = duckdb.connect(str(dbp))
    con.execute("""CREATE TABLE IF NOT EXISTS vrn_report_financial(
        report_file VARCHAR, page INTEGER, canonical VARCHAR,
        raw_label VARCHAR, period VARCHAR, status VARCHAR,
        value DOUBLE, raw_text VARCHAR,
        period_type VARCHAR, fiscal_year INTEGER, fiscal_quarter INTEGER,
        period_src VARCHAR, unit VARCHAR, currency VARCHAR,
        scale DOUBLE, unit_src VARCHAR)""")
    migrate_financial_cols(con)          # 批615:舊庫就地補欄(只增不減;舊列留 NULL=還沒重抽)
    tot = unk = 0
    _bykind = {"pdf": 0, "word": 0, "image": 0, "other": 0}
    _notes = []
    _alt_tally: dict = {}                            # 批504:候 register(二見)
    for p in pdfs:
        k = _kind(p) or "other"
        _bykind[k] = _bykind.get(k, 0) + 1
        if k == "word":
            rows, _why = extract_docx_fin(p)
            if _why:
                _notes.append((p.stem, f"WORD:{_why}"))
        elif k == "image":
            # 影像沒有文字層,本檔的表格還原全靠文字行 → 誠實回零,
            # 並**講出下一步**。不假抽、也不再默默略過(v0105 是後者)。
            rows = []
            _notes.append((p.stem, "影像無文字層=本站零值(誠實);"
                                   "要從影像出表需影像表格 OCR 道,尚未在位"))
        else:
            rows = extract_pdf_fin(p)
        con.execute("DELETE FROM vrn_report_financial WHERE report_file=?",
                    [p.stem])                       # 派生層重算
        for r in rows:
            # 批615:改**具名欄位** INSERT。原本是 `VALUES (?,?,?,?,?,?,?,?)` 配
            # `list(r.values())`——靠 dict 順序的位置參數,而 WORD 道的列多了
            # mops_rank/mops_why 兩鍵(10 值塞 8 位)。那是還沒爆的炸彈,一併拆掉。
            _cols = ("report_file", "page", "canonical", "raw_label", "period",
                     "status", "value", "raw_text") + FIN_COLS_B615
            con.execute(
                "INSERT INTO vrn_report_financial (" + ",".join(f'"{c}"' for c in _cols)
                + ") VALUES (" + ",".join("?" * len(_cols)) + ")",
                [r.get(c) for c in _cols])
        u = sum(1 for r in rows if not r["canonical"])
        for r in rows:
            if not r["canonical"]:
                _m2 = re.search(r"\[二見 ([^\]]+)\]", r["raw_text"])
                if _m2:
                    _alt_tally[_m2.group(1)] = _alt_tally.get(_m2.group(1), 0) + 1
        tot += len(rows)
        unk += u
        if rows:
            print(f"  [{p.stem[:44]}] +{len(rows)} 值"
                  f"(UNKNOWN 科目 {u}=候 register)")
    n = con.execute("SELECT count(*) FROM vrn_report_financial").fetchone()[0]
    if cross:                                       # 批403:三方對照同輪落庫
        crosscheck(con, [p.stem for p in pdfs])
    if cross:                                       # 批685:官方年度核對 + 加減除驗算(同輪;缺冊/缺表=誠實略)
        arith_check(con, [p.stem for p in pdfs])
        official_check(con, [p.stem for p in pdfs])
    con.close()
    for _st, _wy in _notes:
        print(f"  [註] {_st[:44]} · {_wy}")
    print(f"[財報頁計] {len(pdfs)} 件(PDF {_bykind['pdf']}/WORD {_bykind['word']}"
          f"/影像 {_bykind['image']})· 本輪 +{tot} 值(未對齊 {unk} 誠實)"
          f" · 庫 {n:,} 列")
    if _hub748() is None:
        print(f"  [二見] 橋缺({_HUB748['why']})=UNKNOWN 科目無第二意見(照舊)")
    else:
        _top = sorted(_alt_tally.items(), key=lambda kv: -kv[1])[:8]
        print(f"  [二見] UNKNOWN {unk} 值中有第二意見 {sum(_alt_tally.values())} 值 · 候 register(登錄進 VRN_Financial_Synonyms_SSOT=你定):"
              + (", ".join(f"{k} ×{v}" for k, v in _top) if _top else "無"))
    return 0


def status() -> int:
    import duckdb
    con = duckdb.connect(str(DB_TW), read_only=True)
    try:
        for c, n in con.execute(
                "SELECT canonical, count(*) FROM vrn_report_financial "
                "GROUP BY canonical ORDER BY 2 DESC LIMIT 15").fetchall():
            print(f"  [{c or 'UNKNOWN'}] {n}")
    except Exception:
        print("  未建(先 run)")
    try:                                            # 批403:三方對照分佈
        rs = con.execute(
            "SELECT dimension, state, count(*) FROM vrn_report_crosscheck "
            "GROUP BY 1,2 ORDER BY 3 DESC LIMIT 12").fetchall()
        print("  --- 三方對照(檔名×首頁×財報頁表格)---")
        for d, st, n in rs:
            print(f"  [{d}] {st} {n}")
        if not rs:
            print("  (無列;先 run 或 --crosscheck)")
    except Exception:
        print("  三方對照表未建(先 run 或 --crosscheck)")
    for _tb, _zh in (("vrn_report_official_check", "官方年度核對(歷史數據為主)"),
                     ("vrn_report_arith_check", "加減除驗算")):        # 批685
        try:
            rs = con.execute(f"SELECT state, count(*) FROM {_tb} GROUP BY 1 ORDER BY 2 DESC").fetchall()
            print(f"  --- {_zh} ---")
            for st, n in rs:
                print(f"  [{st}] {n}")
            if not rs:
                print("  (無列;先 run 或 --verify)")
        except Exception:
            print(f"  {_zh}表未建(先 run 或 --verify)")
    con.close()
    return 0


def selftest() -> int:
    import tempfile
    import duckdb
    fails = []
    _n = [0]                      # 批563:檢數用數的,不用寫死的(寫死的會跟實際脫鉤)

    def chk(name, cond, note=""):
        _n[0] += 1
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    src_txt = Path(__file__).read_text(encoding="utf-8")
    syn = _syn()
    chk("① SynonymEngine SSOT 掛載(normalize_metric 正主)",
        syn.normalize_metric("營業收入") == "revenue"
        and callable(syn.normalize_metric))
    h = parse_header("6873泓德能源 2023 24Q1 24Q2 2024 25Q1(F) 2025(F)")
    chk("② 期間表頭定位(混合年/季/E·F 狀態拆離)",
        h is not None and ("2023", "REPORT_STATED") in h
        and ("2025", "ESTIMATE") in h and ("24Q1", "REPORT_STATED") in h)
    d = parse_data_row("營業收入淨額 5,839 884 1,272 10,125 1,467 12,108",
                       h, syn)
    chk("③ 壓平數據列拆解+科目對齊(Gemini 首數字切分)",
        d is not None and d["canonical"] == "revenue"
        and d["cells"][0]["value"] == 5839.0
        and d["cells"][0]["period"] == "2023")
    d2 = parse_data_row("神秘特殊科目 100 200 300", h[:3], syn)
    chk("④ 未命中=UNKNOWN 誠實(不硬套;候 register)",
        d2 is not None and d2["canonical"] == "")
    d3 = parse_data_row("營業利益 (1,250) -70.2 300", h[:3], syn)
    chk("⑤ 負數雙格式((1,250)=-1250;-70.2)",
        d3 is not None and d3["cells"][0]["value"] == -1250.0
        and d3["cells"][1]["value"] == -70.2)
    chk("⑥ 財務頁判準(核心科目≥2+期間≥2;非財頁拒)",
        is_financial_page("營業收入 100 毛利 50 2023 2024")
        and not is_financial_page("本公司免責聲明如下"))
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        import fitz
        doc = fitz.open()
        doc.new_page().insert_text((40, 60), "COVER PAGE")
        pg = doc.new_page()
        pg.insert_text((40, 60), "6873 2023 2024 2025(F)",
                       fontname="china-t")
        pg.insert_text((40, 80), "營業收入淨額 5,839 10,125 12,108",
                       fontname="china-t")
        pg.insert_text((40, 100), "營業毛利 1,450 2,528 3,100",
                       fontname="china-t")
        doc.save(str(tdp / "fx_fin.pdf"))
        doc.close()
        dbp = tdp / "t.duckdb"
        rc1 = run(tdp, dbp, no_incoming=True)
        rc2 = run(tdp, dbp, no_incoming=True)
        con = duckdb.connect(str(dbp))
        n = con.execute("SELECT count(*) FROM vrn_report_financial").fetchone()[0]
        rev = con.execute("SELECT value FROM vrn_report_financial WHERE "
                          "canonical='revenue' AND period='2025' "
                          "AND status='ESTIMATE'").fetchone()
        con.close()
        chk("⑦ PDF 端到端(頁2 表→庫;2025F=12108 ESTIMATE)",
            rc1 == 0 and rev is not None and rev[0] == 12108.0)
        chk("⑧ 重跑冪等(派生層重算;列數不倍增)", rc2 == 0 and n == 6)
    chk("⑨ 雙 SSOT 隔離宣告(REPORT_STATED/ESTIMATE;永不冒充官方)",
        "永不冒充官方" in src_txt and "REPORT_STATED" in src_txt)
    chk("⑩ 零網路+加速橋", "ACCEL-BRIDGE" in src_txt
        and all(("import " + k) not in src_txt for k in ("requests", "httpx")))
    # --- 批403 三方對照四檢 -------------------------------------------
    chk("⑪ 對照狀態律(AGREE≤1%/ROUNDING≤5%/UNIT_SCALE 千百萬倍/DIVERGE/單邊/雙缺)",
        compare_values(10.0, 10.05)[0] == "AGREE"
        and compare_values(10.0, 10.4)[0] == "ROUNDING"
        and compare_values(10.0, 10000.0)[0] == "UNIT_SCALE"
        and compare_values(10.0, 25.0)[0] == "DIVERGE"
        and compare_values(10.0, None)[0] == "ONLY_FIRSTPAGE"
        and compare_values(None, 10.0)[0] == "ONLY_TABLE"
        and compare_values(None, None)[0] == "MISSING_BOTH")
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        import fitz
        doc = fitz.open()
        doc.new_page().insert_text((40, 60), "COVER PAGE")
        pg = doc.new_page()
        pg.insert_text((40, 60), "6873 2023 2024 2025(F)", fontname="china-t")
        pg.insert_text((40, 80), "營業收入淨額 5,839 10,125 12,108",
                       fontname="china-t")
        pg.insert_text((40, 100), "每股盈餘 1.20 2.40 3.10", fontname="china-t")
        doc.save(str(tdp / "6873_2024-05-06_元大.pdf"))
        doc.close()
        dbp = tdp / "x.duckdb"
        c0 = duckdb.connect(str(dbp))
        c0.execute("CREATE TABLE vrn_report_basic(report_file VARCHAR,"
                   " ticker VARCHAR, report_date VARCHAR)")
        c0.execute("INSERT INTO vrn_report_basic VALUES "
                   "('6873_2024-05-06_元大','6873','2024-05-06')")
        c0.execute("CREATE TABLE vrn_report_metrics(report_file VARCHAR,"
                   " metric VARCHAR, period VARCHAR, status VARCHAR,"
                   " value DOUBLE, raw_text VARCHAR)")
        c0.execute("INSERT INTO vrn_report_metrics VALUES "
                   "('6873_2024-05-06_元大','eps','2024','STATED',2.40,''),"
                   "('6873_2024-05-06_元大','eps','2025','ESTIMATE',9.90,'')")
        c0.close()
        rc = run(tdp, dbp, no_incoming=True)
        con = duckdb.connect(str(dbp))
        got = dict(con.execute(
            "SELECT period, state FROM vrn_report_crosscheck "
            "WHERE dimension='eps'").fetchall())
        onlyt = con.execute(
            "SELECT count(*) FROM vrn_report_crosscheck WHERE "
            "dimension='revenue' AND state='ONLY_TABLE'").fetchone()[0]
        tk = con.execute(
            "SELECT state FROM vrn_report_crosscheck WHERE "
            "dimension='ticker_on_fin_page'").fetchone()
        dt = con.execute(
            "SELECT state, note FROM vrn_report_crosscheck WHERE "
            "dimension='report_date_vs_periods'").fetchone()
        n1 = con.execute("SELECT count(*) FROM vrn_report_crosscheck").fetchone()[0]
        run(tdp, dbp, no_incoming=True)                               # 冪等重跑
        n2 = con.execute("SELECT count(*) FROM vrn_report_crosscheck").fetchone()[0]
        con.close()
        chk("⑫ 三方對照端到端(首頁 eps 2024=2.40 對表格 2.40=AGREE;"
            "2025 首頁 9.90 對表格 3.10=DIVERGE)",
            rc == 0 and got.get("2024") == "AGREE"
            and got.get("2025") == "DIVERGE", f"{got}")
        chk("⑬ 表格獨有科目 ONLY_TABLE + 檔名↔財報頁 ticker + 報告日 vs 期間",
            onlyt >= 1 and tk is not None
            and tk[0].startswith("TICKER_")
            and dt is not None and dt[0] == "DATE_CONSISTENT", f"{tk} {dt}")
        chk("⑭ 對照冪等(派生層重算不倍增)", n1 == n2 and n1 > 0)
    with tempfile.TemporaryDirectory() as td2:
        dbp2 = Path(td2) / "y.duckdb"
        c1 = duckdb.connect(str(dbp2))
        c1.execute("CREATE TABLE vrn_report_financial(report_file VARCHAR,"
                   " page INTEGER, canonical VARCHAR, raw_label VARCHAR,"
                   " period VARCHAR, status VARCHAR, value DOUBLE,"
                   " raw_text VARCHAR)")
        r0 = crosscheck(c1, do_print=False)
        c1.close()
        chk("⑮ ENG073 兩表缺=誠實略過不 crash(指路先跑 ENG073)",
            r0.get("skipped") == "NO_ENG073")
    # ⑯ 批425:run 動詞的 --db 必須真的傳進 run()(v0102 寫死 None)。
    # 攔真實呼叫來證明,不掃原始碼字串。
    _seen = {}
    _real_run, _real_argv = globals()["run"], sys.argv
    try:
        globals()["run"] = lambda src=None, db=None, cross=True: (_seen.update(
            {"src": src, "db": db, "cross": cross}) or 0)
        sys.argv = ["x", "run", "--dir", "/tmp/_d_", "--db", "/tmp/_b_.duckdb"]
        _rc = main()
    finally:
        globals()["run"], sys.argv = _real_run, _real_argv
    chk("⑯ run 動詞的 --db 真的接到 run()(批425:v0102 是 run(d, None, ...),"
        "db 那格寫死 None,`run --db X` 永遠寫進預設庫;--db 只有 --crosscheck 分支"
        "解析得到=更難察覺。實跑證據:ENG074 印「對照 28 列」而收尾讀 X 是「已對照 0/5」)",
        _rc == 0 and Path(str(_seen.get("db"))).as_posix() == "/tmp/_b_.duckdb"      # 批521:Windows 反斜線同義
        and Path(str(_seen.get("src"))).as_posix() == "/tmp/_d_" and _seen.get("cross") is True,
        f"(src={_seen.get('src')} db={_seen.get('db')} cross={_seen.get('cross')})")

    # ── 批466 兩檢:三類收件 + WORD 表格零相依讀法(帶活對照組)──
    import tempfile as _tf, zipfile as _zp
    with _tf.TemporaryDirectory() as _td74:
        _d74 = Path(_td74)
        _W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
        _p = lambda t: f'<w:p><w:r><w:t xml:space="preserve">{t}</w:t></w:r></w:p>'   # noqa: E731
        _tc = lambda t: f'<w:tc>{_p(t)}</w:tc>'                                       # noqa: E731
        _tr = lambda cs: "<w:tr>" + "".join(_tc(c) for c in cs) + "</w:tr>"           # noqa: E731
        _tbl = ("<w:tbl>" + _tr(["項目", "2024", "2025F", "2026F"])
                + _tr(["營業收入", "2,894,308", "3,512,000", "4,180,000"])
                + _tr(["毛利率", "56.1%", "58.2%", "59.0%"])
                + _tr(["每股盈餘", "45.25", "52.80", "59.80"]) + "</w:tbl>")
        _body = _p("2454 財務預測") + _p("損益表(單位:新台幣百萬元)") + _tbl
        _doc = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                f'<w:document xmlns:w="{_W}"><w:body>{_body}<w:sectPr/></w:body></w:document>')
        _ct = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://'
               'schemas.openxmlformats.org/package/2006/content-types"><Default Extension='
               '"rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
               '<Default Extension="xml" ContentType="application/xml"/><Override PartName='
               '"/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument'
               '.wordprocessingml.document.main+xml"/></Types>')
        _rl = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns='
               '"http://schemas.openxmlformats.org/package/2006/relationships"><Relationship '
               'Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
               'relationships/officeDocument" Target="word/document.xml"/></Relationships>')
        _dx = _d74 / "fx74_fin.docx"
        with _zp.ZipFile(_dx, "w", _zp.ZIP_DEFLATED) as _z:
            _z.writestr("[Content_Types].xml", _ct)
            _z.writestr("_rels/.rels", _rl)
            _z.writestr("word/document.xml", _doc)
        (_d74 / "fx74_scan.png").write_bytes(b"\x89PNG\r\n\x1a\n")   # 只要副檔名被認得

        _v105_gate = sorted(_d74.glob("*.pdf"))          # 對照組:v0105 的閘
        _e72m, _e72w = _intake_bridge()
        _k = (lambda q: _e72m.kind_of(q)) if _e72m else (lambda q: "pdf" if q.suffix.lower() == ".pdf" else "")
        _v106_gate = sorted(x for x in _d74.iterdir() if x.is_file() and _k(x))
        chk("⑰ 收件三類(批466 實測:①站 ENG072 收得下的 docx 與影像,到本站**連被看見都沒有**"
            "——v0105 的閘是 `d.glob(\"*.pdf\")`,同一個夾直接回「無 PDF」rc=2。判準綁 ENG072 "
            "尾版的 kind_of,不另抄一份;橋缺席退回 PDF-only=零回歸)",
            len(_v105_gate) == 0 and len(_v106_gate) == 2 and _e72m is not None,
            f"(v0105 閘={len(_v105_gate)} 件 · v0106 閘={len(_v106_gate)} 件"
            f"{(' · 橋退路=' + _e72w) if _e72w else ''})")

        _rw, _why74 = extract_docx_fin(_dx)
        _cn = {r["canonical"] for r in _rw}
        _eps = {r["period"]: (r["value"], r["status"]) for r in _rw if r["canonical"] == "eps"}
        chk("⑱ WORD 財報表零相依讀法(.docx 本來就是 zip,`<w:tbl>` 就是表)。"
            "**Zero-Hydra:不另造解析器**——每個 <w:tr> 併成一行交回本檔既有的 "
            "parse_header/parse_data_row/_syn,所以同一份報告換成 Word 出的值與 PDF 道一致。"
            "WORD 無頁界 → page 記 0 並在 raw_text 標「WORD 表N」,不假裝有頁碼",
            len(_rw) == 9 and _cn == {"eps", "gross_margin", "revenue"}
            and _eps.get("2024") == (45.25, "REPORT_STATED")
            and _eps.get("2026") == (59.8, "ESTIMATE")
            and all(r["page"] == 0 for r in _rw)
            and all("[WORD 表" in r["raw_text"] for r in _rw),
            f"({len(_rw)} 值 · 科目 {sorted(_cn)} · EPS2024={_eps.get('2024')} "
            f"· EPS2026={_eps.get('2026')} · page 全 0="
            f"{all(r['page'] == 0 for r in _rw)})")

    # ⑲ 批504:UNKNOWN 科目的第二意見——只註記不改 canonical;橋缺席=SKIP 誠實
    _hb = _hub748()
    if _hb is not None:
        _d19 = parse_data_row("資產總計 100 200 300", h[:3], syn, _hb)
        chk("⑲ 第二意見(批504):SSOT 未命中「資產總計」→ canonical 仍空(不硬套),alt 帶 total_assets@allinone(候 register)",
            _d19 is not None and _d19["canonical"] == "" and "total_assets@allinone" in _d19.get("alt", ""), f"(alt={_d19.get('alt') if _d19 else None})")
    else:
        chk("⑲ 第二意見(橋缺席=SKIP 誠實)", True, f"({_HUB748['why']})")
    # ⑳ 批563:MOPS 名次真的有蓋到列上(不是只有樞紐會算,是**本器產出的每一列都帶著它**)
    _hd = [("2025", "ACTUAL"), ("2024", "ACTUAL")]
    _d1 = parse_data_row("歸屬於母公司業主之權益總計 3,050,000 2,800,000", _hd, _syn())
    _d2 = parse_data_row("權益總計 3,200,000 2,950,000", _hd, _syn())
    _r1 = _mops(_d1["raw_label"], _d1["canonical"]) if _d1 else (None, None)
    _r2 = _mops(_d2["raw_label"], _d2["canonical"]) if _d2 else (None, None)
    chk("⑳ MOPS 列優先序接線(批563 操作員「同意」):本器的 rows 每列多帶 `mops_rank`/`mops_why`,"
        "由呼叫端取 max;**輸的那列不刪**(只增不減)。名次向樞紐要,樞紐或收容冊缺席=名次 0="
        "與 v0109 行為一位元不差(誠實退路,不自己編一套)",
        _d1 and _d2 and _r1[0] == 40 and _r2[0] == 20 and _r1[0] > _r2[0],
        f"(歸屬母公司 {_r1[0]}『{_r1[1]}』 vs 權益總計 {_r2[0]}『{_r2[1]}』)")

    # ═══ 批615 五檢:期間拆解 + 單位 ═══════════════════════════════════
    chk("㉑ 期間拆解:年 / 季(兩種寫法)/ 半年 / FY / 民國,估計旗標分得開",
        period_parts("2025")["fiscal_year"] == 2025
        and period_parts("2025E")["estimate"] == "E"
        # 兩種寫法要解出同一個**結構**;`why` 記的是原文,本來就該不同,不進比對
        and (lambda k: [{x: period_parts(t)[x] for x in k} for t in ("1Q25", "25Q1")])(
            ("period_type", "fiscal_year", "fiscal_quarter"))[0]
            == (lambda k: [{x: period_parts(t)[x] for x in k} for t in ("1Q25", "25Q1")])(
            ("period_type", "fiscal_year", "fiscal_quarter"))[1]
        and period_parts("1Q25")["fiscal_quarter"] == 1
        and period_parts("1Q25")["period_type"] == "FQ"
        and period_parts("1H25")["period_type"] == "FH"
        and period_parts("FY26")["fiscal_year"] == 2026
        and period_parts("114")["fiscal_year"] == 2025,
        f'(1Q25={period_parts("1Q25")} · 114={period_parts("114")["fiscal_year"]})')

    chk("㉒ **解不出來就留空並說出原文**,不猜(零發明)",
        period_parts("上半年")["period_type"] is None
        and period_parts("上半年")["why"].startswith("UNPARSED:")
        and scan_unit_decl("這頁沒寫單位")["unit"] is None
        and "NO_DECL" in scan_unit_decl("這頁沒寫單位")["why"])

    chk("㉓ 單位只認**寫出來的**宣告(頁面文字),不由數值大小反推",
        scan_unit_decl("單位:新台幣百萬元")["scale"] == 1e6
        and scan_unit_decl("單位:新台幣百萬元")["currency"] == "TWD"
        and scan_unit_decl("NT$ mn")["scale"] == 1e6
        and scan_unit_decl("US$mn")["currency"] == "USD"
        and scan_unit_decl("單位:千元")["scale"] == 1e3,
        f'(百萬={scan_unit_decl("單位:新台幣百萬元")} )')

    chk("㉔ 語意單位不吃金額宣告:比率永遠 % · 倍數永遠 x · 每股跟幣別",
        unit_for_row("gross_margin", "毛利率", scan_unit_decl("單位:新台幣百萬元"))["unit"] == "%"
        and unit_for_row("per", "本益比(倍)", scan_unit_decl("單位:千元"))["unit"] == "x"
        and unit_for_row("eps", "每股盈餘", scan_unit_decl("單位:新台幣百萬元"))["unit"] == "TWD/股"
        and unit_for_row("revenue", "營業收入淨額",
                         scan_unit_decl("單位:新台幣百萬元"))["scale"] == 1e6)

    chk("㉕ 遷移只增不減:舊庫補欄不動舊值,新欄留 NULL(誠實=還沒重抽)",
        (lambda: (lambda con: (
            con.execute("CREATE TABLE vrn_report_financial(report_file VARCHAR,"
                        " page INTEGER, canonical VARCHAR, raw_label VARCHAR,"
                        " period VARCHAR, status VARCHAR, value DOUBLE, raw_text VARCHAR)"),
            con.execute("INSERT INTO vrn_report_financial VALUES"
                        " ('f',1,'revenue','營收','2023','REPORT_STATED',5839.0,'x')"),
            migrate_financial_cols(con),
            con.execute("SELECT value, unit, fiscal_year FROM vrn_report_financial").fetchone()
        )[-1])(__import__("duckdb").connect(":memory:")))() == (5839.0, None, None))

    # ═══ 批685 六檢:官方年度核對(歷史數據為主)+ 加減除驗算 ═══════════════
    _vr = verify_rules()
    chk("㉖ 驗證規則只從冊上取(SUP_MDL749 rules() → rules.financial.verify:恆等式 ≥5 · 官方對照欄 ≥5 · 優先序 OFFICIAL_WINS);本檔零影子規則、零容差數字",
        _vr.get("state") == "OK" and len(_vr.get("identities") or []) >= 5
        and len((_vr.get("official") or {}).get("columns") or {}) >= 5
        and (_vr.get("official") or {}).get("precedence") == "OFFICIAL_WINS"
        and ('tol_rel"' + ': 0.') not in src_txt and ("IDENTITIES" + " = [") not in src_txt,   # 針拼接:檢自己的敘述不得自撞(批446 那一課)
        f"(恆等式 {len(_vr.get('identities') or [])} · 對照欄 {len((_vr.get('official') or {}).get('columns') or {})})")
    with tempfile.TemporaryDirectory() as td3:
        c3 = duckdb.connect(str(Path(td3) / "z.duckdb"))
        c3.execute("CREATE TABLE vrn_report_basic(report_file VARCHAR, ticker VARCHAR, report_date VARCHAR)")
        c3.execute("INSERT INTO vrn_report_basic VALUES ('2330_2025-03-01_凱基','2330','2025-03-01'),"
                   "('9999_2025-03-01_無官方','9999','2025-03-01')")
        c3.execute("CREATE TABLE vrn_report_financial(report_file VARCHAR, page INTEGER, canonical VARCHAR,"
                   " raw_label VARCHAR, period VARCHAR, status VARCHAR, value DOUBLE, raw_text VARCHAR,"
                   " period_type VARCHAR, fiscal_year INTEGER, fiscal_quarter INTEGER, period_src VARCHAR,"
                   " unit VARCHAR, currency VARCHAR, scale DOUBLE, unit_src VARCHAR)")
        _A, _B = "2330_2025-03-01_凱基", "9999_2025-03-01_無官方"
        _rows685 = [
            (_A, 2, "revenue", "營業收入", "2024", "REPORT_STATED", 2894308.0, "", "FY", 2024, None, "", "百萬元", "TWD", 1e6, ""),
            (_A, 2, "gross_profit", "營業毛利", "2024", "REPORT_STATED", 1624354.0, "", "FY", 2024, None, "", "百萬元", "TWD", 1e6, ""),
            (_A, 2, "gross_margin", "毛利率", "2024", "REPORT_STATED", 56.1, "", "FY", 2024, None, "", "%", "TWD", 1.0, ""),
            (_A, 2, "eps", "每股盈餘", "2024", "REPORT_STATED", 45.25, "", "FY", 2024, None, "", "TWD/股", "TWD", 1.0, ""),
            (_A, 2, "net_income", "稅後淨利", "2024", "REPORT_STATED", 1173268.0, "", "FY", 2024, None, "", "", "TWD", None, ""),
            (_A, 2, "op_profit", "營業利益", "2024", "REPORT_STATED", 1322050.0, "", "FY", 2024, None, "", "百萬元", "TWD", 1e6, ""),
            (_A, 2, "revenue", "營業收入", "2025", "ESTIMATE", 3500000.0, "", "FY", 2025, None, "", "百萬元", "TWD", 1e6, ""),
            (_A, 2, "revenue", "營業收入", "1Q25", "REPORT_STATED", 839254.0, "", "FQ", 2025, 1, "", "百萬元", "TWD", 1e6, ""),
            (_B, 2, "revenue", "營業收入", "2024", "REPORT_STATED", 1000.0, "", "FY", 2024, None, "", "百萬元", "TWD", 1e6, ""),
            (_B, 2, "gross_profit", "營業毛利", "2024", "REPORT_STATED", 400.0, "", "FY", 2024, None, "", "百萬元", "TWD", 1e6, ""),
            (_B, 2, "gross_margin", "毛利率", "2024", "REPORT_STATED", 45.0, "", "FY", 2024, None, "", "%", "TWD", 1.0, ""),
        ]
        c3.executemany("INSERT INTO vrn_report_financial VALUES (" + ",".join("?" * 16) + ")", _rows685)
        _nfin0 = c3.execute("SELECT count(*), sum(value) FROM vrn_report_financial").fetchone()
        _ar = arith_check(c3, do_print=False)
        _st = {(r[0], r[2], r[3]): (r[9], r[10]) for r in c3.execute("SELECT * FROM vrn_report_arith_check").fetchall()}
        chk("㉗ 加減除驗算:2330 毛利率 1624354÷2894308=56.12 對 56.1 → PASS · 9999 400÷1000=40 對 45 → FAIL · 毛利=營收−成本 缺 cogs → INSUFFICIENT 點名 · 營益率缺 op_margin → INSUFFICIENT 點名(缺=候 register,不是錯)",
            _st.get((_A, "2024", "GM_DIV"), ("",))[0] == "PASS"
            and _st.get((_B, "2024", "GM_DIV"), ("",))[0] == "FAIL"
            and _st.get((_A, "2024", "GP_SUB"), ("",))[0] == "INSUFFICIENT" and "cogs" in _st.get((_A, "2024", "GP_SUB"), ("", ""))[1]
            and _st.get((_A, "2024", "OPM_DIV"), ("",))[0] == "INSUFFICIENT" and "op_margin" in _st.get((_A, "2024", "OPM_DIV"), ("", ""))[1]
            and _ar.get("missing", {}).get("cogs", 0) >= 1,
            f"({_st.get((_A, '2024', 'GM_DIV'))} · {_st.get((_B, '2024', 'GM_DIV'))} · 缺 {dict(sorted(_ar.get('missing', {}).items()))})")
        _o0 = official_check(c3, do_print=False)
        c3.execute('CREATE TABLE tw_financial("Date" VARCHAR, "Ticker" VARCHAR, "Period" VARCHAR, "Period_Type" VARCHAR,'
                   ' "Revenue" DOUBLE, "Gross_Profit" DOUBLE, "Operating_Income" DOUBLE, "Net_Income" DOUBLE, "EPS" DOUBLE,'
                   ' "Total_Assets" DOUBLE, "Total_Liabilities" DOUBLE, "Equity" DOUBLE, "Operating_CF" DOUBLE,'
                   ' "Investing_CF" DOUBLE, "Financing_CF" DOUBLE, "Free_CF" DOUBLE, "ROE" DOUBLE, "ROA" DOUBLE,'
                   ' "Gross_Margin" DOUBLE, "Operating_Margin" DOUBLE, "Net_Margin" DOUBLE, "Debt_To_Equity" DOUBLE,'
                   ' "Source" VARCHAR, fetched_at VARCHAR)')
        c3.execute("INSERT INTO tw_financial VALUES ('2025-09-21','2330.TW','2024-12-31','annual',2894307699000,1624354000000,"
                   "1322050000000,1173268000000,45.25,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,56.12,45.67,40.54,NULL,'yfinance','')")
        c3.execute("INSERT INTO tw_financial VALUES ('2025-09-21','2330.TW','2024-03-31','quarterly',839254000000,NULL,"
                   "NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'yfinance','')")
        _o1 = official_check(c3, do_print=False)
        _oc = {(r[0], r[2], r[3]): (r[10], r[11], r[12]) for r in c3.execute("SELECT * FROM vrn_report_official_check").fetchall()}
        _n1 = c3.execute("SELECT count(*) FROM vrn_report_official_check").fetchone()[0]
        _na = c3.execute("SELECT count(*) FROM vrn_report_arith_check").fetchone()[0]
        chk("㉘ 官方年度核對端到端:營收 2,894,308 百萬 × 1e6 對官方 2,894,307,699,000 → AGREE · EPS 45.25 → AGREE · 毛利率 56.1 對 56.12 → AGREE · 稅後淨利單位未宣告(scale NULL)→ UNIT_SCALE 不判 DIVERGE · 1Q25 季列/2025 預估列不入年度核對 · 9999 → NO_OFFICIAL_TICKER 指路 VDF_ENG082",
            _oc.get((_A, "revenue", "2024"), ("",))[0] == "AGREE"
            and _oc.get((_A, "eps", "2024"), ("",))[0] == "AGREE"
            and _oc.get((_A, "gross_margin", "2024"), ("",))[0] == "AGREE"
            and _oc.get((_A, "net_income", "2024"), ("",))[0] == "UNIT_SCALE"
            and (_A, "revenue", "1Q25") not in _oc and (_A, "revenue", "2025") not in _oc
            and _oc.get((_B, "revenue", "2024"), ("",))[0] == "NO_OFFICIAL_TICKER",
            "(" + " · ".join(f"{k[1]}={v[0]}" for k, v in sorted(_oc.items()) if k[0] == _A) + ")")
        chk("㉙ **歷史數據為主**:官方有值 winner=OFFICIAL 且 value_final=官方原值(2,894,307,699,000)· 報告值留在 report_value 不改 · 每份一列 __alignment__:2330 CONFIRMED(至少一項對得起來)· 9999 NO_OFFICIAL_TICKER",
            _oc.get((_A, "revenue", "2024"), ("", "", None))[1] == "OFFICIAL"
            and _oc.get((_A, "revenue", "2024"), ("", "", None))[2] == 2894307699000.0
            and _oc.get((_A, "__alignment__", ""), ("",))[0] == "CONFIRMED"
            and _oc.get((_B, "__alignment__", ""), ("",))[0] == "NO_OFFICIAL_TICKER"
            and c3.execute("SELECT report_value FROM vrn_report_official_check WHERE report_file=? AND canonical='revenue'",
                           [_A]).fetchone()[0] == 2894308.0 * 1e6,
            f"({_oc.get((_A, 'revenue', '2024'))} · {_oc.get((_A, '__alignment__', ''))})")
        _keep_vr = globals()["verify_rules"]
        try:
            globals()["verify_rules"] = lambda: {"state": "ABSENT", "why": "fixture"}
            _oa = official_check(c3, do_print=False)
            _aa = arith_check(c3, do_print=False)
        finally:
            globals()["verify_rules"] = _keep_vr
        chk("㉚ 誠實略不假綠:官方表不在 → NO_OFFICIAL_TABLE(指路補料;同意閘不代設)· 冊缺 → 兩者 NO_RULES(不驗不是驗過;引擎不自己編一套)",
            _o0.get("skipped") == "NO_OFFICIAL_TABLE" and _oa.get("skipped") == "NO_RULES" and _aa.get("skipped") == "NO_RULES",
            f"({_o0.get('skipped')} · {_oa.get('skipped')} · {_aa.get('skipped')})")
        arith_check(c3, do_print=False)
        official_check(c3, do_print=False)
        _n2 = c3.execute("SELECT count(*) FROM vrn_report_official_check").fetchone()[0]
        _na2 = c3.execute("SELECT count(*) FROM vrn_report_arith_check").fetchone()[0]
        _nfin1 = c3.execute("SELECT count(*), sum(value) FROM vrn_report_financial").fetchone()
        c3.close()
        chk("㉛ 冪等(派生層重算不倍增)+ 正典表 vrn_report_financial 零觸碰(列數與值總和不變)+ run 同輪接線(--no-cross 一起關)+ --verify/--arith/--official 動詞在",
            _n1 == _n2 and _na == _na2 and _n1 > 0 and _nfin0 == _nfin1
            and "arith_check(con, [p.stem for p in pdfs])" in src_txt and "official_check(con, [p.stem for p in pdfs])" in src_txt
            and '"--verify"' in src_txt and '"--arith"' in src_txt and '"--official"' in src_txt,
            f"(官方 {_n1}={_n2} · 驗算 {_na}={_na2} · 正典 {_nfin0}={_nfin1})")
    print(f"  [計] 三十一檢({_n[0]} 檢) OK {_n[0] - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


# ===== [VIA:COMMONUTILS-BRIDGE:v0100] VRN 共用小工具正典橋(批594;正典 SUP_MDL753)=====
# 本處原本的行為:旗標取值 · 回 Path
# 批594 量過:VRN 尾版 170 支 · 定義 68 處 · **18 個行為群**(全部在模組層)。
# 差異是真的:`_cel_submit` 兩群差在「有沒有第二層退路」;`_si` 有一群用 **bare `except:`**
# (連 SystemExit 都吞——**那是潛在缺陷不是風格**,正典給選項等價遷移,不代改 LL90);
# `_jwrite` 三群差在 mkdir / default / 吞不吞例外,而且**底下直接接批592 的 SUP_MDL752**,
# 不另造一支 JSON 寫法。綁定不是 def(寫 def 家族數不會掉,LL143);
# 可變預設值由正典 `_fresh()` 保證每次新的一份(L76)。
import importlib.util as _cu_ilu
from pathlib import Path as _cu_Path
_CU_MOD = None
_cu_p = _cu_Path(__file__).resolve()
while _cu_p.parent != _cu_p:
    _cu_hits = sorted((_cu_p / "supportive modules").glob("SUP_MDL753_VIACommonUtils_v*.py"))
    if _cu_hits:
        _cu_spec = _cu_ilu.spec_from_file_location("VIA_COMMONUTILS", _cu_hits[-1])
        _CU_MOD = _cu_ilu.module_from_spec(_cu_spec)
        _cu_spec.loader.exec_module(_CU_MOD)
        break
    _cu_p = _cu_p.parent
if _CU_MOD is None:
    raise RuntimeError("[FAIL] 共用小工具正典缺席:supportive modules/SUP_MDL753_VIACommonUtils_v*.py")
_argval = _CU_MOD.bind_argval(as_path=True)
# ===== [VIA:COMMONUTILS-BRIDGE:END] =====


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 財報頁表格擷取器(VRN_ENG074 v0113)· 三十一檢自測(零網路;臨時庫)===")
        return selftest()
    if "--status" in args:
        return status()
    if any(f in args for f in ("--verify", "--arith", "--official")):   # 批685:單獨重算(缺冊/缺表 rc2 誠實)
        import duckdb
        dbp = _resolve_db(Path(args[args.index("--db") + 1])
                          if "--db" in args else None)
        if dbp is None:
            return 2
        con = duckdb.connect(str(dbp))
        outs = []
        if "--verify" in args or "--arith" in args:
            outs.append(arith_check(con))
        if "--verify" in args or "--official" in args:
            outs.append(official_check(con))
        con.close()
        return 2 if any(o.get("skipped") for o in outs) else 0
    if "--crosscheck" in args:                      # 批403:單獨重算三方對照
        import duckdb
        dbp = _resolve_db(Path(args[args.index("--db") + 1])
                          if "--db" in args else None)
        if dbp is None:
            return 2
        con = duckdb.connect(str(dbp))
        r = crosscheck(con)
        con.close()
        return 2 if r.get("skipped") else 0
    if args and args[0] == "run":
        # 批425(沙盒實跑整條鏈時發現):v0102 這裡是 run(d, None, ...) ——
        # db 那一格**寫死 None**,所以 `run --db X` 永遠寫進預設庫。
        # (--db 在 --crosscheck 分支有解析,唯獨 run 這條沒有=更難察覺。)
        # 實跑證據:ENG074 印「對照 5 件 → 28 列」,收尾閘讀 X 卻是「已對照 0/5」,
        # 因為 28 列根本不在 X 裡。與批423 $StageTimeoutSec、ENG073 --dir/--db、
        # MDL141 --db 同一家族:參數在、線沒接。
        d = _argval(args, "--dir")
        return run(d, _argval(args, "--db"), "--no-cross" not in args)
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
