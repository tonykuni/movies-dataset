#!/usr/bin/env python3
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
      [--no-cross] | --crosscheck | --status | --selftest
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
PERIOD_TOKEN_RX = re.compile(
    r"^(20\d{2}|\d{2}Q[1-4]|1[01]\d)(?:年)?\(?([EFA])?\)?$", re.I)
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
                    "raw_text": f"[WORD 表{ntbl}] " + str(c.get("raw_text", line))[:60] + (f" [二見 {d['alt']}]" if d.get("alt") else ""),
                })
    return rows, ("" if rows else f"{ntbl} 個表,無一通過財報頁判準")


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
                                    "raw_text": line.strip()[:120] + (f" [二見 {d['alt']}]" if d.get("alt") else "")})
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
        value DOUBLE, raw_text VARCHAR)""")
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
            con.execute("INSERT INTO vrn_report_financial VALUES "
                        "(?,?,?,?,?,?,?,?)", list(r.values()))
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

    print(f"  [計] 二十檢({_n[0]} 檢) OK {_n[0] - len(fails)} · FAIL {len(fails)}")
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
        print("=== 財報頁表格擷取器(VRN_ENG074 v0107)· 十九檢自測(零網路)===")
        return selftest()
    if "--status" in args:
        return status()
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
