#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vrn_report_digest_v0111 — 個股報告摘要批跑器(TOOL-070)
批121:三券商真件六債修(中信 3665/2330·大和 1815·華夏 1305 memo 實測定讞)
  ㉓ PDF 抽取道優先序 — pymupdf(fitz)閱讀序正確為首選,pypdf 後備
     (pypdf 版面重排=值先於標籤+數字內插空白「2, 275」,3665 TP 誤抽
     2.0 根因);抽出即數字接合正規化(「2, 775」→「2,775」)。
  ㉔ TP 前次排除 — 參數冊 target_price 加 (?<!前次) 負向回顧;TW02
     TP 層同閘(前次目標價 2,720 不得壓正目標價 2,775)。
  ㉕ 券商檔名 token 識別 — 檔名逐段取字首英文 token 對映
     broker_prefix_map(Daiwa1815→Daiwa→大和;CTBC260824→CTBC→中信證)。
  ㉖ 報告日檔名後備 — 內文無日期時檔名 6 碼 YYMMDD(CTBC240612→
     2024-06-12);8 碼既有 hay 道不變。
  ㉗ 分析師 EMAIL 窗優先 — 鄰近窗兩段掃:先 EMAIL 再職稱標籤
     (許哲豪在 jeff.syu@ 旁);stopwords 冊補 個股/大盤/走勢 類雜訊
     (「個股與大盤走勢(%)」圖表標題誤擷案)。
  ㉘ TW02 評等抗噪 — 純 ASCII 評等字命中須 ±30 字內有評等語境
     (rating/評等/維持/調升…);「reduce the supply chain」「反傾銷
     稅(ADD)」類內文動詞不再誤咬,無評等=誠實留空。
批74:nan 誠實閘(yfinance 取價失敗回 nan 時,列值一律轉 None 顯示
「—」,不印 nan 假值;工作站 20260820_011756 批證據定讞)
批73:U/I 接母子統一套件(雙主題/auto-fit/微互動;via_theme 全站共享)
====================================================================
操作員令(批41,2026-08-18):「現在又修復文字功能及摘要功能
請寫每個個股報告摘葉(=摘要)」。
v0100→v0101(批42,2026-08-19):
  ① --collect 歸庫搬移 — 原報告搬入正典新報告夾(預設
     functional modules/VRN/input/reports;gitignore 圈內不入版控)。
     零刪除鐵律:搬移+manifest 存證+--undo 可逆;整合去重:同名
     全同 hash=讓位零動作(原地不動記 DUP)、同名異內容=_sha8
     鏡像收容 byte-exact。
  ② --vdf 串跑 — 摘要矩陣列餵 VDF 輸出樞紐(動態解析最新版)
     六格式輸出+讀回驗證,驗證矩陣一併顯示。
  ③ RICH 矩陣 — 每次跑完的驗證結果以 rich 自動調寬高矩陣顯示
     (欄寬隨內容與終端寬自適應、列高 fold 自動換行;rich 缺席
     graceful 降級純文字,誠實零假裝)。
v0101→v0102(批55/58,2026-08-19):
  ④ TW02 抽取道 — 操作員令「評等RATING 目標價都可以在首頁上左右
     資訊區跟修正後的內文找到 目標價TARGET PRICE也是可在同樣位置
     找到」:動態解析最新 VRN_TW02_ReportParser_v*(嚴禁寫死版號),
     首頁區(first_page_chars)先抽評等/目標價/券商/代碼,未中再
     全文(修正後內文)fallback;RATING_SYNONYMS 中英同義+
     TARGET_PRICE_PATTERN(目標價/合理價/TP/PT/Fair Value+NT$ 千分
     位)。新舊整合鐵則(批58):簡單的先用(v1 中央參數 regex 為
     底)、TW02 為升級層、TW02 缺席 graceful 降級 v1 零假綠;逐欄
     記抽取源(TW02:首頁/TW02:內文/v1)誠實可稽。
v0102→v0103(批59,2026-08-19):
  ⑤ 只截個股報告 — 操作員令「VRN只截取個股報告」:無有效代碼件
     =SKIP:非個股報告(誠實,不強掛 ticker;品質債②修)。
  ⑥ 固定十一欄 — REPORT DATE/FILENAME/BROKER/ANALYST/TICKER/
     YFINANCE TICKER/NAME(官方冊 TWSE·TPEX 名稱優先)/ADJ CLOSE/
     RATING/TARGET PRICE/UPSIDE%(算)。市場判定:內文明示
     .TWO/.TW > 官方個股註冊冊(TOOL-075 產物,動態最新)> TWSE
     預設;market 餵 Summarizer(品質債③修,櫃買 .TWO 不再誤掛
     .TW)。分析師=錨定式(分析師:/Analyst: 標籤;TW02 寬鬆式
     任 2-4 中文字=噪音不用),抽不到誠實留空。
v0103→v0104(批62,2026-08-19;工作站 64 份真跑證據定讞):
  ⑦ 報告類型閘 — 晨會/盤勢/早報/日港美股/期貨/產業/趨勢/展望等
     檔名關鍵詞(中央參數 non_stock_keywords)=SKIP:非個股報告(類型);
     官方冊閘:冊≥registry_gate_min_size(1000,工作站全冊生效、
     容器種子冊不誤觸)且代碼不在冊=SKIP:非個股報告(不在官方冊)
     (雜訊代碼 2730/3110 類穿閘債,官方 SSOT 定生死)。
  ⑧ TP 黃旗 — |上漲%|>tp_suspect_abs_upside(80)=tp_suspect 誠實
     標記(值不改不刪,矩陣 ⚠ 顯示;6533 TP=3.0 誤抽類即時可見)。
v0104→v0105(批64,2026-08-19):
  ⑨ 券商局部識別 — 操作員令「券商名稱 簡稱 中英文縮寫可在
     FILENAME 及內文採取局部識別」:檔名首段縮寫對映
     broker_prefix_map(MS/GS/JP/Citi/CLST/Daiwa/UBS/MQ/GF/KGI/
     CTBC,中央參數冊)+既有 Summarizer 中文簡稱 hay 掃+TW02
     BROKER_PATTERNS/EMAIL 域名,四道疊加。
  ⑩ 市場啟發式後備 — 操作員核定台股代碼統一解析(上櫃區段
     3/4/5/6/8 開頭;VRN_OperatorRegex_TWTicker_v0100 收容件):
     官方冊缺席且內文無明示時的第四後備層(工作站全冊仍為主)。
v0105→v0106(批65,2026-08-19):
  ⑪ 分析師三道 — 令「分析師的姓名通常出現在 EMAIL 電話 職稱附近
     EMAIL @前面通常是分析師的英文名字」:①錨定標籤(分析師:/
     Analyst:)②職稱/EMAIL 鄰近窗中文名(stopwords 濾)③EMAIL
     @ 前英文名(去數字,. 轉空格)。
  ⑫ 名用中文簡稱 — 官方冊中文簡稱>檔名中文 token(name_stopwords
     濾)>Summarizer 報告文名。
  ⑬ BROKER 英文縮寫顯示 — broker_abbr_display 對映(MS/GS/KGI/
     Yuanta…,中央參數冊);JSON 雙留全名+縮寫。
  ⑭ 末欄=標題+摘要 — 矩陣/U/I 末欄併列 headline+五點第一點。
  ⑮ 40 型分類閘 — 批65 收容分類器(webscraping 包)加層:scope
     非 COMPANY/UNKNOWN 且信心≥0.6=SKIP;UNCLASSIFIED 誠實不擋。
v0106→v0107(批67,2026-08-19;工作站 64 份 v0106 真跑證據定讞):
  ⑯ 市場優先序反轉 — 官方冊>內文明示>啟發式>預設(6147 頎邦案:
     報告文誤標 .TW 壓過官方冊致 404;官方資料=實績 SSOT 定生死)。
  ⑰ 官方名簡稱化 — TPEX 官方冊存全稱(德微科技股份有限公司):
     去「股份有限公司/有限公司」尾,仍逾四字且檔名中文 token 在
     =用檔名簡稱(鈺緯/德微/振曜/頎邦;令「名用中文簡稱」)。
  ⑱ 分析師抗噪 — 錨定式必須帶冒號(Analyst Certification/
     Analysts employed 誤擷案);擷值過 stopwords 閘(評等/買進/
     持有/比重…);._ 正規化為空格。
原則:
  ① 引擎不重造 — 摘要核心=VRN_ENG062 Summarizer(一標題五點+
     ADJ CLOSE 指標);本批跑器動態解析最新版匯入,零改寫正本。
  ② 黃旗補治 — Summarizer 五點缺句時落預設填充語;本器逐點比對
     填充語清單,命中即加「〔自動生成〕」標註(台帳黃旗結案,
     正本零觸碰=version-forward 外包裝)。
  ③ 參數中央化 — 全參數讀 knowledge/VRN_Digest_Params_v0100.json
     (該冊已入 TOOL-069 中央參數樞紐衝突圈);引擎零寫死。
  ④ 誠實三態 — 逐報告 OK/FAIL/SKIP;pdf 無抽取器=SKIP 誠實;
     ticker 年區 2021-2030 依 LOCKED regex 排除。
  ⑤ 存證 — VIA_Reports/digest_runs/DIGEST_<ts>/:逐報告 .md+
     Digest_Matrix.json;理印 U/I VIA_UI_ReportDigest.html。
用法:
  via-digest --dir <報告夾>       → 批跑(txt/md/docx;pdf 視環境)
  via-digest                      → 掃預設候選夾(冊列)
  via-digest --limit N            → 只跑前 N 件
  via-digest --collect --from <舊夾> [--from <舊夾2>] [--to <新夾>]
                                  → 原報告歸庫搬移(manifest+undo)
  via-digest --undo <manifest>    → 反轉一次歸庫搬移
  via-digest --vdf                → 摘要矩陣串跑 VDF 六格式+驗證
  via-digest --selftest           → 十檢(合成 fixture 零網路)
  via-digest --no-open            → 不開 U/I
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

import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import time
import zipfile
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent          # functional modules/VRN
VIA = HERE.parent.parent
PARAMS_PATH = HERE / "knowledge" / "VRN_Digest_Params_v0100.json"
MOTTO = "VERITAS INTELLIGENCE ANALYTICS · OBSERVA · INTELLEGE · PRAEVIDE"


def load_params() -> dict:
    return json.loads(PARAMS_PATH.read_text(encoding="utf-8-sig"))


def load_summarizer():
    """動態解析最新 Summarizer(鐵律:嚴禁寫死版號)"""
    hits = sorted(HERE.glob("VRN_ENG062_Summarizer*.py")) or sorted(HERE.glob("VRN_Summarizer_v*.py"))
    if not hits:
        return None, "Summarizer 引擎缺(誠實)"
    eng = hits[-1]
    spec = importlib.util.spec_from_file_location("vrn_summarizer_dyn", eng)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as exc:
        return None, f"Summarizer 匯入敗:{str(exc)[:80]}"
    return mod, eng.name


ANALYST_RX = re.compile(
    r"(?:分析師|研究員|Analyst)\s*[::]\s*"
    r"([\u4e00-\u9fff]{2,4}(?:[、,,\s][\u4e00-\u9fff]{2,4})*|[A-Z][A-Za-z._ ]{2,40})")


def _analyst_clean(val: str, prm: dict) -> str | None:
    """分析師擷值抗噪:stopwords 閘+._ 正規化(批67)"""
    val = re.sub(r"[._]+", " ", (val or "").strip()).strip()
    stop = set(prm.get("analyst_stopwords", []))
    if not val or val in stop or any(w in val for w in stop):
        return None
    if re.match(r"^[A-Za-z]", val) and val.lower().split()[0] in (
            "certification", "disclosure", "disclosures", "employed", "rating", "report"):
        return None
    return val


def load_equity_registry() -> dict:
    """官方個股註冊冊(TWSE/TPEX;TOOL-075 產物,動態最新)→{code:(名,市場)};缺=誠實空"""
    cfg = VIA / "supportive modules/VIA_FlowSystem/FlowSystem_v2/config"
    hits = sorted(cfg.glob("TW_Equity_Registry_v*.json"))
    if not hits:
        return {}
    try:
        d = json.loads(hits[-1].read_text(encoding="utf-8-sig"))
        return {e["ticker"]: (e.get("name", ""), e.get("market", "TWSE"))
                for e in d.get("equities", []) if e.get("ticker")}
    except Exception:
        return {}


def resolve_equity(ticker: str, text: str, reg: dict,
                   prm: dict | None = None) -> tuple[str, str, str]:
    """市場判定四道(批67 序):官方冊 SSOT > 內文明示 .TWO/.TW > 上櫃
    啟發式(操作員核定 OTC_PREFIXES)> TWSE 預設;回 (market, yf, 官方名)"""
    name, market = reg.get(ticker, ("", ""))
    if not market:  # 批67:官方冊 SSOT 優先,內文明示降第二(6147 誤標案)
        m = re.search(rf"\b{re.escape(ticker)}\.(TWO|TW)\b", text)
        if m:
            market = "TPEX" if m.group(1) == "TWO" else "TWSE"
    if not market:
        otc = tuple(prm.get("otc_prefixes", [])) if prm else ()
        if otc and len(ticker) == 4 and ticker.startswith(otc):
            market = "TPEX"  # 啟發式後備(官方冊在位時不會走到)
        else:
            market = "TWSE"
    yf = f"{ticker}.TWO" if market == "TPEX" else f"{ticker}.TW"
    return market, yf, name


def load_classifier40():
    """批65 收容 40 型報告分類器(webscraping 包;缺=誠實 None)"""
    import warnings
    p = HERE / "webscraping_dualengine_v20260819" / "VIA_Investment_Report_Classifier.py"
    if not p.exists():
        return None
    spec = importlib.util.spec_from_file_location("vrn_cls40_dyn", p)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["vrn_cls40_dyn"] = mod
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            spec.loader.exec_module(mod)
    except Exception:
        sys.modules.pop("vrn_cls40_dyn", None)
        return None
    return mod


def classify_non_stock(stem: str, ticker: str, reg: dict, prm: dict,
                       cls40=None, head_text: str = "") -> str | None:
    """批62 報告類型閘:檔名關鍵詞+官方冊閘+40 型分類器加層(批65);
    回 SKIP 因由或 None(=個股)"""
    for kw in prm.get("non_stock_keywords", []):
        if kw in stem:
            return f"類型:{kw}"
    if ticker and len(reg) >= int(prm.get("registry_gate_min_size", 1000)) \
            and ticker not in reg:
        return "不在官方冊"
    if cls40 is not None:
        try:
            r = cls40.def_classify_investment_report(stem, head_text)
            if (r.report_scope not in ("COMPANY", "COMPANY_OR_TOPIC", "UNKNOWN")
                    and r.confidence >= 0.6):
                return f"類型:{r.report_type_code}"
        except Exception:
            pass  # 分類器異常=不擋(其餘閘仍在,誠實 fail-open 單層)
    return None


def shorten_official_name(off_name: str, stem: str, prm: dict) -> tuple[str, str]:
    """批67 令「名用中文簡稱」:去公司尾綴;仍逾四字且檔名中文 token 在=檔名簡稱"""
    short = re.sub(r"(股份有限公司|有限公司)$", "", off_name).strip()
    nstop = prm.get("name_stopwords", [])
    toks = [t for t in re.findall(r"[\u4e00-\u9fff]{2,4}", stem)
            if not any(w in t for w in nstop)]
    # 檔名 token 為官方名前綴(德微科技→德微)或官方名仍逾四字=用檔名簡稱
    if toks and toks[0] != short and (short.startswith(toks[0]) or len(short) > 4):
        return toks[0], "官方冊+檔名簡稱"
    return short, "官方冊"


def _nn(v):
    """nan 誠實閘:nan/None → None(顯示 —);其餘原值(批74)"""
    import math
    if v is None:
        return None
    try:
        if isinstance(v, float) and math.isnan(v):
            return None
    except Exception:
        pass
    return v


def tp_flag(upside, prm: dict) -> bool:
    """TP 黃旗:上漲%絕對值逾閾=疑誤抽(值不改,誠實標記)"""
    thr = float(prm.get("tp_suspect_abs_upside", 80.0))
    return upside is not None and abs(upside) > thr


def load_tw02():
    """動態解析最新 TW02 ReportParser(批55;嚴禁寫死版號;缺席=誠實降級)"""
    import warnings
    hits = sorted(HERE.glob("VRN_TW02_ReportParser_v*.py"))
    if not hits:
        return None, "TW02 缺(降級 v1 抽取)"
    eng = hits[-1]
    name = "vrn_tw02_dyn"
    spec = importlib.util.spec_from_file_location(name, eng)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod  # 先掛名再 exec(dataclass 解析需要)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            spec.loader.exec_module(mod)
    except Exception as exc:
        sys.modules.pop(name, None)
        return None, f"TW02 匯入敗:{str(exc)[:60]}"
    return mod, eng.name


def _sweep(msg: str, i: int, n: int) -> None:
    """常備令Ⅱ:動態進度條(單行覆寫,不卡斷)"""
    w = 24
    k = int(w * i / max(n, 1))
    sys.stdout.write(f"\r  [{'█' * k}{'░' * (w - k)}] {i}/{n} {msg[:44]:<44}")
    sys.stdout.flush()
    if i >= n:
        sys.stdout.write("\n")


# ── RICH 自動調寬高矩陣(批42:每次跑出來驗證後的結果都用矩陣顯示)──
def rich_matrix(title: str, columns: list[str], rows: list[list[str]],
                state_col: int | None = None) -> bool:
    """rich Table:欄寬隨內容+終端寬自適應、overflow=fold 列高自動換行;
    state_col 指定狀態欄→OK 綠/SKIP·AUTO 黃/FAIL 紅。rich 缺=誠實降級純文字。"""
    try:
        from rich import box
        from rich.console import Console
        from rich.table import Table
        t = Table(title=title, box=box.SIMPLE_HEAVY, title_style="bold",
                  header_style="bold cyan", show_lines=False, pad_edge=False)
        for c in columns:
            t.add_column(c, overflow="fold", no_wrap=False)
        for r in rows:
            cells = [str(x) if x is not None else "—" for x in r]
            if state_col is not None and state_col < len(cells):
                s = cells[state_col]
                color = ("green" if s.startswith(("OK", "MOVED", "COMPAT", "PASS"))
                         else "red" if s.startswith("FAIL")
                         else "yellow")
                cells[state_col] = f"[{color}]{s}[/{color}]"
            t.add_row(*cells)
        Console().print(t)
        return True
    except Exception:
        print(f"  ── {title}(rich 缺席,純文字降級)──")
        print("  " + " | ".join(columns))
        for r in rows:
            print("  " + " | ".join(str(x) if x is not None else "—" for x in r))
        return False


# ── 歸庫搬移(批42:原報告搬新報告夾;零刪除=manifest+undo)──
def sha256_of(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def collect_reports(sources: list[Path], dest: Path, prm: dict,
                    manifest_dir: Path) -> int:
    exts = set(prm["extensions"])
    dest.mkdir(parents=True, exist_ok=True)
    files = []
    for src in sources:
        if not src.exists():
            print(f"  [SKIP] 來源夾缺:{src}(誠實)")
            continue
        files += [p for p in sorted(src.rglob("*"))
                  if p.is_file() and p.suffix.lower() in exts and "_sha" not in p.stem
                  and dest not in p.parents]
    if not files:
        print("  [SKIP] 來源夾零報告件(誠實)")
        return 0
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    entries = []
    n_mv = n_dup = n_mirror = 0
    for i, p in enumerate(files, 1):
        _sweep(p.name, i, len(files))
        sha = sha256_of(p)
        tgt = dest / p.name
        if tgt.exists():
            if sha256_of(tgt) == sha:      # 全同=讓位零動作(原地不動)
                entries.append({"src": str(p), "dst": "", "sha256": sha, "action": "DUP_SKIP"})
                n_dup += 1
                continue
            tgt = dest / f"{p.stem}_sha{sha[:8]}{p.suffix}"  # 異內容=_sha 鏡像收容
            if tgt.exists() and sha256_of(tgt) == sha:
                entries.append({"src": str(p), "dst": "", "sha256": sha, "action": "DUP_SKIP"})
                n_dup += 1
                continue
            n_mirror += 1
        shutil.move(str(p), str(tgt))
        entries.append({"src": str(p), "dst": str(tgt), "sha256": sha, "action": "MOVED"})
        n_mv += 1
    manifest_dir.mkdir(parents=True, exist_ok=True)
    mf = manifest_dir / f"COLLECT_{ts}_manifest.json"
    mf.write_text(json.dumps({"schema": "VIA.DigestCollect.v1", "ts": ts,
                              "dest": str(dest), "sources": [str(s) for s in sources],
                              "moved": n_mv, "dup_skip": n_dup, "sha_mirror": n_mirror,
                              "entries": entries}, ensure_ascii=False, indent=1),
                  encoding="utf-8")
    rich_matrix("歸庫搬移結果(零刪除:manifest+undo 可逆)",
                ["件", "動作", "落點"],
                [[Path(e["src"]).name, e["action"],
                  Path(e["dst"]).name if e["dst"] else "(原地讓位)"] for e in entries],
                state_col=1)
    print(f"  [計] 搬 {n_mv}(內 _sha 鏡像 {n_mirror})· 全同讓位 {n_dup} · manifest {mf.name}")
    print(f"  [undo] via-digest --undo \"{mf}\"")
    return 0


def undo_collect(manifest: Path) -> int:
    if not manifest.exists():
        print(f"  [FAIL] manifest 不存在:{manifest}")
        return 1
    d = json.loads(manifest.read_text(encoding="utf-8"))
    n_back = n_skip = 0
    for e in reversed(d["entries"]):
        if e["action"] != "MOVED" or not e["dst"]:
            continue
        src, dst = Path(e["src"]), Path(e["dst"])
        if not dst.exists() or src.exists():
            n_skip += 1
            continue
        src.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(dst), str(src))
        n_back += 1
    print(f"  [計] undo 還原 {n_back} · 略過 {n_skip}(落點缺/原位已有,誠實)")
    return 0


# ── VDF 串跑(批42:VDF 可以試跑;摘要矩陣列→六格式輸出+驗證)──
def build_vdf_rows(matrix: dict) -> list[dict]:
    rows = []
    for r in matrix["rows"]:
        if r["state"] != "OK":
            continue
        rows.append({"ReportCode": r.get("report_code", ""), "Ticker": r.get("ticker", ""),
                     "Name": r.get("name", "") or "", "Broker": r.get("broker", "") or "",
                     "Rating": r.get("rating", "") or "",
                     "TargetPrice": r.get("target_price"), "AdjClose": r.get("adj_close"),
                     "UpsidePct": r.get("upside_pct"), "AutoFilled": r.get("auto_filled", 0),
                     "File": r["file"], "Headline": r.get("headline", "")})
    return rows


def run_vdf_chain(matrix: dict, run_dir: Path) -> int:
    rows = build_vdf_rows(matrix)
    if not rows:
        print("  [SKIP] VDF 串跑:零 OK 列可餵(誠實)")
        return 0
    vdf_dir = VIA / "functional modules/VDF"
    hubs = sorted(vdf_dir.glob("VDF_ENG045_OutputHub_v0*.py"))  # 動態解析最新版(鐵律)
    if not hubs:
        print("  [SKIP] VDF 輸出樞紐缺(誠實)")
        return 0
    rows_json = run_dir / "digest_vdf_rows.json"
    rows_json.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    r = subprocess.run([sys.executable, str(hubs[-1]), str(rows_json)],
                       capture_output=True, text=True, timeout=600, cwd=str(vdf_dir))
    evs = sorted((VIA / "VIA_Reports" / "vdfout_runs").glob("VDFOUT_*.json"))
    if r.returncode == 0 and evs:
        m = json.loads(evs[-1].read_text(encoding="utf-8"))["matrix"]
        rich_matrix(f"VDF 六格式輸出+讀回驗證矩陣({len(rows)} 摘要列)",
                    ["表", "格式", "狀態", "列數", "位元組", "檔"],
                    [[x["table"], x["format"], x["status"], x["rows"], x["bytes"], x["file"]]
                     for x in m], state_col=2)
        ok = sum(1 for x in m if str(x["status"]).startswith(("OK", "COMPAT")))
        print(f"  [計] VDF 格式出 {ok}/{len(m)} 綠 · 存證 {evs[-1].name}")
        return 0
    print(f"  [FAIL] VDF 串跑 rc={r.returncode}:{(r.stderr or r.stdout).strip()[-120:]}")
    return 1


# ── 文字抽取(修復後文字功能之最小自足道;docx 零外依)──────
def extract_text(p: Path) -> tuple[str, str]:
    """回 (text, state);state ∈ OK / SKIP:<因>"""
    ext = p.suffix.lower()
    if ext in (".txt", ".md"):
        for enc in ("utf-8-sig", "cp950", "big5", "latin-1"):
            try:
                return p.read_text(encoding=enc), "OK"
            except (UnicodeDecodeError, LookupError):
                continue
        return "", "SKIP:編碼不明"
    if ext == ".docx":
        try:
            with zipfile.ZipFile(p) as z:
                xml = z.read("word/document.xml").decode("utf-8", "ignore")
            xml = re.sub(r"</w:p>", "\n", xml)
            text = re.sub(r"<[^>]+>", "", xml)
            return re.sub(r"\n{3,}", "\n\n", text).strip(), "OK"
        except Exception as exc:
            return "", f"SKIP:docx 讀取敗 {str(exc)[:40]}"
    if ext == ".pdf":
        # 批121 ㉓:pymupdf 閱讀序正確為首選(pypdf 版面重排=值先於標籤
        # +數字內插空白,3665 TP 誤抽根因);pypdf 後備;皆缺=誠實 SKIP
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(str(p))
            return _pdf_norm("\n".join(pg.get_text() for pg in doc)), "OK"
        except ImportError:
            pass
        except Exception as exc:
            return "", f"SKIP:pdf 讀取敗 {str(exc)[:40]}"
        try:
            import pypdf
            reader = pypdf.PdfReader(str(p))
            return _pdf_norm("\n".join((pg.extract_text() or "")
                                       for pg in reader.pages)), "OK"
        except ImportError:
            return "", "SKIP:pdf 抽取器缺(pymupdf/pypdf)"
        except Exception as exc:
            return "", f"SKIP:pdf 讀取敗 {str(exc)[:40]}"
    return "", f"SKIP:副檔名不支援 {ext}"


def _pdf_norm(text: str) -> str:
    """批121 ㉓:PDF 文字數字接合正規化——「2, 775」/「2 ,775」類千分位
    內插空白接回「2,775」(抽取器版面切字誤差;僅接合逗號千分位,零改值)"""
    return re.sub(r"([0-9])\s*,\s*([0-9]{3})(?![0-9])", r"\1,\2", text)


# ── 批120 多代碼綜合文件閘 ──────────────────────────────────
def multi_doc_gate(text: str, meta: dict, prm: dict) -> str:
    """個股報告須「單碼主導」或「關鍵欄支撐」;族群彙整/多股綜合文=SKIP。
    真報告不誤殺:目標價/分析師/報告日期任一在=支撐即放行;
    多碼但主碼壓倒性(≥2× 次高且=錨定碼)亦放行(報告內比較同業屬常態)。"""
    locked = re.compile(prm["tw_ticker_locked"])
    year = re.compile(prm["year_suspect"])
    counts: dict = {}
    for c in re.findall(r"(?<![0-9.])([0-9]{4})(?![0-9.])", text[:20000]):
        if locked.match(c) and not year.match(c):
            counts[c] = counts.get(c, 0) + 1
    support = any(meta.get(k) for k in ("target_price", "analyst", "report_date"))
    if len(counts) >= 5 and not support:
        top = sorted(counts.values(), reverse=True)
        second = top[1] if len(top) > 1 else 0
        anchored = meta.get("ticker", "")
        dominant = (counts.get(anchored, 0) == top[0] and top[0] >= max(2 * second, 3))
        if not dominant:
            return (f"多代碼綜合文件:{len(counts)} 碼·關鍵欄零支撐·主碼不主導")
    return ""


# ── 批121 ㉘:TW02 評等/TP 抗噪閘 ────────────────────────────
def _tw02_rating_find(tw02, seg: str):
    """純 ASCII 評等字(reduce/add/buy…)須前置 20 字內有評等標籤才收
    (Rating: Overweight ✓);「reduce the supply chain」「反傾銷稅(ADD)」
    內文動詞、「Rating Percentage of total Buy* 72.63%」評等分布表、
    「comprised of Daiwa's Buy…ratings」disclosure 法遵文皆拒(誠實留空)"""
    for m in tw02.RATING_PATTERN.finditer(seg):
        raw = m.group(1)
        if raw.isascii():
            pre = seg[max(0, m.start() - 20):m.start()]
            if not re.search(r"(?i)rating|rated|評等|評級|投資建議|推薦|維持|調升|調降", pre):
                continue
        return m
    return None


def _tw02_tp_find(tw02, seg: str):
    """TP 命中若緊接「前次」之後=前次目標價,跳過取下一命中(批121 ㉔)"""
    for m in tw02.TARGET_PRICE_PATTERN.finditer(seg):
        if seg[max(0, m.start() - 2):m.start()] == "前次":
            continue
        return m
    return None


# ── 元資料收割(檔名+內文;LOCKED regex 年區排除)────────────
def harvest_meta(p: Path, text: str, prm: dict, broker_dict: dict,
                 tw02=None) -> dict:
    pats = prm["meta_patterns"]
    locked = re.compile(prm["tw_ticker_locked"])
    year = re.compile(prm["year_suspect"])  # LOCKED 第一支放行四碼,年區須疊拒絕閘(字庫 v0101 同法)
    hay = p.stem + "\n" + text[:3000]
    meta = {}
    for cand in re.findall(pats["ticker_candidate"], hay):
        if locked.match(cand) and not year.match(cand):
            meta["ticker"] = cand
            break
    m = re.search(pats["target_price"], text)
    if m:
        meta["target_price"] = float(m.group(1).replace(",", ""))
    m = re.search(pats["rating"], text)
    if m:
        meta["rating"] = m.group(1)
    m = re.search(pats["eps_current"], text)
    if m:
        meta["eps_current"] = float(m.group(1))
    m = re.search(pats["report_date"], hay)
    if m:
        d = re.sub(r"[-/\.]", "", m.group(1))
        meta["report_date"] = f"{d[:4]}-{d[4:6]}-{d[6:8]}"
    if not meta.get("report_date"):  # 批121 ㉖:檔名 6 碼 YYMMDD 後備(CTBC240612)
        m = re.search(r"(?<![0-9])(2[0-9])([01][0-9])([0-3][0-9])(?![0-9])", p.stem)
        if m:
            meta["report_date"] = f"20{m.group(1)}-{m.group(2)}-{m.group(3)}"
            meta.setdefault("src", {})["report_date"] = "檔名YYMMDD"
    m = ANALYST_RX.search(text[:prm["first_page_chars"]]) or ANALYST_RX.search(text)
    if m:
        v = _analyst_clean(m.group(1), prm)
        if v:
            meta["analyst"] = v
    if not meta.get("analyst"):  # 批65 ②+批121 ㉗:鄰近窗中文名(EMAIL 窗優先於職稱標籤窗)
        stop = set(prm.get("analyst_stopwords", []))
        for rx in (r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+", r"研究員|Analyst|分析師"):
            for am in re.finditer(rx, text[:6000]):
                win = text[max(0, am.start() - 40):am.end() + 40]
                cands = [x for x in re.findall(r"[\u4e00-\u9fff]{2,4}", win)
                         if x not in stop and not any(w in x for w in stop)]
                if cands:
                    meta["analyst"] = cands[0]
                    meta.setdefault("src", {})["analyst"] = "鄰近窗"
                    break
            if meta.get("analyst"):
                break
    if not meta.get("analyst"):  # 批65 ③:EMAIL @ 前=英文名
        em = re.search(r"([A-Za-z][A-Za-z0-9._-]{2,30})@[A-Za-z0-9.-]+", text[:6000])
        if em:
            eng = re.sub(r"\d+", "", em.group(1)).replace(".", " ").replace("_", " ").strip()
            if len(eng) >= 3:
                meta["analyst"] = eng.title()
                meta.setdefault("src", {})["analyst"] = "EMAIL英名"
    for broker in broker_dict:
        if broker and broker in hay:
            meta["broker"] = broker
            break
    if not meta.get("broker"):  # 批64+批121 ㉕:檔名逐段取字首英文 token 對映(Daiwa1815→Daiwa)
        pmap = prm.get("broker_prefix_map", {})
        for tok in re.split(r"[-_\s]+", p.stem):
            am = re.match(r"[A-Za-z]+", tok)
            alpha = am.group(0) if am else ""
            hit = next((full for abbr, full in pmap.items()
                        if alpha.lower() == abbr.lower()), None)
            if hit:
                meta["broker"] = hit
                meta.setdefault("src", {})["broker"] = "檔名縮寫"
                break
    # ── TW02 升級層(批55 令:評等/目標價=首頁上左右資訊區→修正後內文)──
    meta.setdefault("src", {})
    if tw02 is not None:
        fp = text[:prm["first_page_chars"]]
        try:
            page = tw02.PageParser.parse_first_page(fp)
        except Exception:
            page = {}
        if not meta.get("ticker") and page:
            tk = page.get("tickers", {})
            cand = ([c.split(".")[0] for c in tk.get("tw_yfinance", [])]
                    or [c.replace(" TT", "") for c in tk.get("tw_bloomberg", [])]
                    or tk.get("tw_pure", []))
            if cand:
                meta["ticker"] = cand[0]
                meta["src"]["ticker"] = "TW02:首頁"
        m = _tw02_rating_find(tw02, fp)
        where = "TW02:首頁"
        if not m:
            m = _tw02_rating_find(tw02, text)
            where = "TW02:內文"
        if m:
            raw = m.group(1)
            meta["rating"] = raw  # Summarizer 用原字(誠實原貌)
            low = raw.lower()
            meta["rating_class"] = next(
                (c for c, syns in tw02.RATING_SYNONYMS.items()
                 if raw in syns or low in [x.lower() for x in syns]), None)
            meta["src"]["rating"] = where
        m = _tw02_tp_find(tw02, fp)
        where = "TW02:首頁"
        if not m:
            m = _tw02_tp_find(tw02, text)
            where = "TW02:內文"
        if m:
            try:
                meta["target_price"] = float(m.group(1).replace(",", ""))
                meta["src"]["target_price"] = where
            except ValueError:
                pass
        if not meta.get("broker") and page.get("broker"):
            meta["broker"] = page["broker"]
            meta["src"]["broker"] = "TW02:首頁"
    return meta


def tag_fillers(summary, prm: dict) -> tuple[int, dict]:
    """五點逐比填充語;命中加〔自動生成〕標註(正本 dataclass 就地
    改欄位值=本器輸出物,Summarizer 引擎零觸碰)"""
    tag = prm["filler_tag"]
    fillers = set(prm["filler_phrases"])
    p1_rx = re.compile(prm["point1_fallback_regex"])
    fields = ["point_1_conclusion", "point_2_growth", "point_3_valuation",
              "point_4_peers", "point_5_risk"]
    n = 0
    flags = {}
    for f in fields:
        v = getattr(summary, f, "") or ""
        auto = v in fillers or (f == "point_1_conclusion" and bool(p1_rx.match(v)))
        flags[f] = "AUTO" if auto else "TEXT"
        if auto and tag not in v:
            setattr(summary, f, f"{v}{tag}")
            n += 1
    return n, flags


# ── 批跑 ─────────────────────────────────────────────────────
def run_batch(report_dir: Path, limit: int | None, no_open: bool,
              out_root: Path | None = None) -> tuple[int, dict | None, Path | None]:
    prm = load_params()
    mod, eng_name = load_summarizer()
    if mod is None:
        print(f"  [FAIL] {eng_name}")
        return 1, None, None
    tw02, tw02_name = load_tw02()
    cls40 = load_classifier40()
    reg = load_equity_registry()
    print(f"  [引擎] {eng_name} · 參數冊 {PARAMS_PATH.name}(中央化)"
          f" · 抽取道 {tw02_name if tw02 else 'v1(' + tw02_name + ')'}"
          f" · 官方個股冊 {len(reg)} 檔")
    exts = set(prm["extensions"])
    files = sorted(p for p in report_dir.rglob("*")
                   if p.is_file() and p.suffix.lower() in exts and "_sha" not in p.stem)
    if limit:
        files = files[:limit]
    if not files:
        print(f"  [SKIP] {report_dir} 內零報告件(誠實;支援 {'/'.join(sorted(exts))})")
        return 0, None, None
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = (out_root or (VIA / prm["output_root"])) / f"DIGEST_{ts}"
    run_dir.mkdir(parents=True, exist_ok=True)
    broker_dict = getattr(mod, "BROKER_ABBR_DICT", {})
    rows = []
    n_ok = n_fail = n_skip = 0
    for i, p in enumerate(files, 1):
        _sweep(p.name, i, len(files))
        text, state = extract_text(p)
        if state != "OK" or not text.strip():
            n_skip += 1
            rows.append({"file": p.name, "state": state if state != "OK" else "SKIP:空文",
                         "ticker": "", "headline": ""})
            continue
        try:
            meta = harvest_meta(p, text, prm, broker_dict, tw02)
            reason = classify_non_stock(p.stem, meta.get("ticker", ""), reg, prm,
                                        cls40, text[:400])
            if reason:  # 批62 報告類型閘/官方冊閘
                n_skip += 1
                rows.append({"file": p.name, "state": f"SKIP:非個股報告({reason})",
                             "ticker": meta.get("ticker", ""), "headline": ""})
                continue
            if not meta.get("ticker"):  # 批59 令:VRN 只截取個股報告
                n_skip += 1
                rows.append({"file": p.name, "state": "SKIP:非個股報告(無有效代碼)",
                             "ticker": "", "headline": ""})
                continue
            md_reason = multi_doc_gate(text, meta, prm)  # 批120 閘
            if md_reason:
                n_skip += 1
                rows.append({"file": p.name, "state": f"SKIP:非個股報告({md_reason})",
                             "ticker": meta.get("ticker", ""), "headline": ""})
                continue
            market, yf_tk, off_name = resolve_equity(meta["ticker"], text, reg, prm)
            fp = text[:prm["first_page_chars"]]
            rest = text[prm["first_page_chars"]:]
            summary = mod.summarize_report(
                ticker=meta.get("ticker", ""), first_page_text=fp, remaining_text=rest,
                broker=meta.get("broker", ""), report_date=meta.get("report_date", ""),
                filename=p.name, target_price=meta.get("target_price"),
                rating=meta.get("rating", ""), eps_current=meta.get("eps_current"),
                market=market)
            name_src = "報告文"
            if off_name:  # 官方冊中文簡稱=SSOT 優先(批65/67 令:名用中文簡稱)
                summary.name, name_src = shorten_official_name(off_name, p.stem, prm)
            elif not re.search(r"[\u4e00-\u9fff]", summary.name or ""):
                nstop = prm.get("name_stopwords", [])
                toks = [t for t in re.findall(r"[\u4e00-\u9fff]{2,6}", p.stem)
                        if not any(w in t for w in nstop)]
                if toks:
                    summary.name = toks[0]
                    name_src = "檔名"
            n_auto, flags = tag_fillers(summary, prm)
            stem = (summary.report_code or p.stem).replace("/", "_")
            md_path = run_dir / f"{stem}_digest.md"
            md_path.write_text(summary.to_markdown() + "\n", encoding="utf-8")
            n_ok += 1
            rows.append({"file": p.name, "state": "OK", "ticker": summary.ticker,
                         "report_date": getattr(summary, "report_date", "") or meta.get("report_date", ""),
                         "analyst": meta.get("analyst", ""),
                         "yf_ticker": getattr(summary, "yfinance_ticker", "") or yf_tk,
                         "market": market,
                         "name_src": name_src,
                         "name": summary.name, "broker": summary.broker,
                         "broker_abbr": prm.get("broker_abbr_display", {}).get(
                             summary.broker or meta.get("broker", ""),
                             summary.broker or meta.get("broker", "")),
                         "eps_current": meta.get("eps_current"),
                         "tp_suspect": tp_flag(_nn(summary.upside_pct), prm),
                         "rating": summary.rating, "target_price": _nn(summary.target_price),
                         "adj_close": _nn(summary.adj_close), "upside_pct": _nn(summary.upside_pct),
                         "report_code": summary.report_code, "headline": summary.headline,
                         "point_1": getattr(summary, "point_1_conclusion", "") or "",
                         "auto_filled": n_auto, "point_flags": flags,
                         "extract_src": meta.get("src", {}),
                         "rating_class": meta.get("rating_class"),
                         "src_disp": "·".join(sorted({v for v in meta.get("src", {}).values()})) or "v1",
                         "md": md_path.name})
        except Exception as exc:
            n_fail += 1
            rows.append({"file": p.name, "state": f"FAIL:{str(exc)[:60]}",
                         "ticker": "", "headline": ""})
    matrix = {"schema": "VIA.ReportDigest.v2", "ts": ts, "dir": str(report_dir),
              "engine": eng_name, "extractor": tw02_name if tw02 else "v1",
              "total": len(files),
              "ok": n_ok, "fail": n_fail, "skip": n_skip, "rows": rows}
    (run_dir / "Digest_Matrix.json").write_text(
        json.dumps(matrix, ensure_ascii=False, indent=1), encoding="utf-8")
    ui = render_ui(matrix, run_dir, prm)
    rich_matrix(f"個股報告摘要矩陣 · {ts}(批59 十一欄;五點黃=填充語{prm['filler_tag']})",
                ["態", "報告日", "檔名", "券商", "分析師", "代碼", "YF代碼",
                 "名稱", "ADJ CLOSE", "評等", "目標價", "上漲%", "標題+摘要"],
                [[r["state"], r.get("report_date", ""), r["file"],
                  r.get("broker_abbr", "") or r.get("broker", "") or "",
                  r.get("analyst", ""), r.get("ticker", ""), r.get("yf_ticker", ""),
                  r.get("name", "") or "", r.get("adj_close"), r.get("rating", "") or "",
                  r.get("target_price"),
                  (f"{r.get('upside_pct')}⚠" if r.get("tp_suspect") else r.get("upside_pct")),
                  ((r.get("headline", "") or "")[:36] + "|"
                   + (r.get("point_1", "") or "")[:36]) if r.get("headline") else ""]
                 for r in rows], state_col=0)
    print(f"  [計] 報告 {len(files)} · OK {n_ok} · FAIL {n_fail} · SKIP {n_skip}(誠實三態)")
    print(f"  [存] {run_dir.relative_to(VIA) if run_dir.is_relative_to(VIA) else run_dir}"
          f" · U/I {ui.name}")
    if not no_open:
        try:
            import webbrowser
            webbrowser.open(ui.as_uri())
        except Exception:
            pass
    return (1 if n_fail else 0), matrix, run_dir


# ── 理印紙墨 U/I ──────────────────────────────────────────────


def _load_ui_kit():
    """批73:母子統一 U/I 套件(動態最新;缺=graceful 用內建 CSS)"""
    import importlib.util
    import warnings
    hits = sorted((VIA / "supportive modules" / "registry").glob("via_ui_kit_v0*.py"))
    if not hits:
        return None
    spec = importlib.util.spec_from_file_location("via_ui_kit_dyn", hits[-1])
    mod = importlib.util.module_from_spec(spec)
    sys.modules["via_ui_kit_dyn"] = mod
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            spec.loader.exec_module(mod)
    except Exception:
        sys.modules.pop("via_ui_kit_dyn", None)
        return None
    return mod

CSS = """
body{background:#f2f1ec;color:#1b1a17;font-family:'Cormorant Garamond','Noto Serif CJK TC','Microsoft JhengHei',serif;margin:0;padding:24px}
.card{background:#fbfaf7;border:1px solid #dbd9d3;border-radius:6px;padding:18px 22px;margin:14px auto;max-width:1280px}
h1{font-size:20px;margin:0 0 2px}
.motto{color:#9e2b25;letter-spacing:.14em;font-size:11px;margin-bottom:14px}
table{border-collapse:collapse;width:100%;font-size:12.5px}
th{color:#3c6660;text-align:left;border-bottom:1.5px solid #3c6660;padding:4px 8px}
td{border-bottom:1px solid #dbd9d3;padding:4px 8px;vertical-align:top}
.ok{color:#3d7a52;font-weight:bold}.warn{color:#8a6420;font-weight:bold}.bad{color:#9e2b25;font-weight:bold}
.mono{font-family:Consolas,monospace;font-size:11.5px}.dim{color:#6b6a64}
"""


def render_ui(matrix: dict, run_dir: Path, prm: dict) -> Path:
    _kit = _load_ui_kit()
    _css = _kit.kit_css() if _kit else CSS
    _js = ('<script>' + _kit.kit_js() + '</script>') if _kit else ''
    rows = []
    for r in matrix["rows"]:
        st = r["state"]
        cls = "ok" if st == "OK" else ("bad" if st.startswith("FAIL") else "warn")
        flags = r.get("point_flags", {})
        dots = "".join(
            f"<span class='{'warn' if flags.get(f) == 'AUTO' else 'ok'}'>●</span>"
            for f in ["point_1_conclusion", "point_2_growth", "point_3_valuation",
                      "point_4_peers", "point_5_risk"]) if flags else "—"
        rows.append(
            f"<tr><td class='{cls}'>{st}</td><td class='mono'>{r.get('report_date', '')}</td>"
            f"<td class='mono dim'>{r['file']}</td><td>{r.get('broker_abbr', '') or r.get('broker', '') or ''}</td>"
            f"<td>{r.get('analyst', '') or ''}</td><td class='mono'>{r.get('ticker', '')}</td>"
            f"<td class='mono'>{r.get('yf_ticker', '')}</td><td>{r.get('name', '') or ''}</td>"
            f"<td class='mono'>{r.get('adj_close', '') or ''}</td><td>{r.get('rating', '') or ''}</td>"
            f"<td>{r.get('target_price', '') or ''}</td>"
            f"<td>{('<span class=warn>' + str(r.get('upside_pct')) + ' ⚠疑誤抽</span>') if r.get('tp_suspect') else (r.get('upside_pct', '') or '')}</td>"
            f"<td class='mono dim'>{r.get('src_disp', '') or ''}</td>"
            f"<td>{dots}</td><td class='dim'>{(r.get('headline', '') or '')[:48]}"
            f"<br><span class='mono'>{(r.get('point_1', '') or '')[:60]}</span></td></tr>")
    html = f"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">
<title>VRN 個股報告摘要矩陣</title><style>{_css}</style></head><body>
<div class="card"><h1>個股報告摘要矩陣 · Report Digest</h1>
<div class="motto">{MOTTO}</div>
<div class="dim">批次 {matrix['ts']} · 來源 {matrix['dir']} · 引擎 {matrix['engine']}
 · 報告 {matrix['total']}(OK {matrix['ok']} / FAIL {matrix['fail']} / SKIP {matrix['skip']})
 · 五點燈:綠=原文抽句 / 黃=填充語{prm['filler_tag']}標註</div>
<table><tr><th>態</th><th>報告日</th><th>檔名</th><th>券商</th><th>分析師</th><th>代碼</th>
<th>YF代碼</th><th>名稱</th><th>ADJ CLOSE</th><th>評等</th><th>目標價</th><th>上漲%</th>
<th>抽取源</th><th>五點</th><th>標題+摘要</th></tr>{''.join(rows)}</table></div>
{_js}</body></html>"""
    out = run_dir / prm["ui_name"]
    out.write_text(html, encoding="utf-8")
    return out


# ── 七檢自測(合成 fixture 零網路)───────────────────────────
FIXTURE_FULL = """數位測試工業 投資報告
評等:買進 (維持)
目標價:250 元
分析師:王小明
2026-01-15
AI 應用需求強勁,先進封裝訂單能見度達兩季。
預估 EPS 12.5 元,年增 18%。
成長動能:高速運算產品線放量,市佔持續提升。
財務預估:毛利率站穩 42%,ROE 20% 以上。
同業比較:相較同業 A 公司與 B 公司,產品組合較優。
風險因子:留意庫存去化不如預期與匯率波動。
"""

FIXTURE_SPARSE = """測試精機
簡評:產業復甦初期。
"""

# 批55 令 fixture:首頁上左右資訊區(英式評等+NT$ 千分位目標價)
FIXTURE_TW02_HEAD = """統一測試科技 (2377.TW) 投資報告
Rating: Overweight    Target Price: NT$1,200
分析師觀點:伺服器散熱需求強勁,訂單能見度高。
"""

# 批55 令 fixture:首頁無評等目標價,修正後內文才有(合理價變體)
FIXTURE_TW02_BODY = """測試應材 6180
本季表現平穩,首頁資訊區無評等揭示。
""" + "填充行。\n" * 600 + """
經修正後之內文評價:我們認為合理價 850 元具吸引力,評等調整為 買進。
"""


def selftest() -> int:
    import shutil
    import tempfile
    t0 = time.time()
    fails = []

    def chk(name, cond, note=""):
        state = "OK" if cond else "FAIL"
        if not cond:
            fails.append(name)
        print(f"  [{state}] {name} {note}")

    prm = load_params()
    # ① 參數冊中央化在位:必備鍵齊
    need = {"first_page_chars", "filler_phrases", "filler_tag", "meta_patterns",
            "tw_ticker_locked", "output_root"}
    chk("參數冊必備鍵", need <= set(prm.keys()), f"({PARAMS_PATH.name})")

    # ② Summarizer 動態解析可匯入
    mod, eng_name = load_summarizer()
    chk("Summarizer 動態匯入", mod is not None, f"({eng_name})")
    if mod is None:
        print("  [計] 七檢中止(引擎缺)")
        return 1

    # ③ ticker 年區閘=LOCKED 收+YEAR_SUSPECT 拒疊閘:2330 收、2025 拒
    locked = re.compile(prm["tw_ticker_locked"])
    year = re.compile(prm["year_suspect"])
    gate = lambda s: bool(locked.match(s)) and not year.match(s)
    chk("ticker 年區閘", gate("2330") and not gate("2025"))

    with tempfile.TemporaryDirectory() as td:
        sand = Path(td)
        rpt = sand / "reports"
        rpt.mkdir()
        (rpt / "2330_數位測試工業_20260115.txt").write_text(FIXTURE_FULL, encoding="utf-8")
        (rpt / "1560_測試精機.txt").write_text(FIXTURE_SPARSE, encoding="utf-8")
        # 合成 docx(zip+document.xml;零外依)
        dx = rpt / "3661_合成docx報告.docx"
        with zipfile.ZipFile(dx, "w") as z:
            z.writestr("word/document.xml",
                       "<w:document><w:p><w:t>合成docx 目標價:300 元 評等:持有</w:t></w:p>"
                       "<w:p><w:t>風險因子:留意需求波動。</w:t></w:p></w:document>")
        (rpt / "空文報告.txt").write_text("", encoding="utf-8")  # SKIP 態觸發件(空文;兩端環境穩定)
        (rpt / "晨會報告_台股.txt").write_text(
            "晨會報告\n台積電 2330 大盤觀察與昨日回顧。\n", encoding="utf-8")  # 批62 類型閘觸發件
        (rpt / "產業週報_半導體.txt").write_text(
            "半導體產業週報\n本週產業動態:先進製程需求穩健。\n2026 年展望正向。\n",
            encoding="utf-8")  # 批59 個股閘觸發件(無有效代碼=非個股)

        # ④ docx 抽取道通
        text, state = extract_text(dx)
        chk("docx 抽取(零外依)", state == "OK" and "目標價" in text)

        # ⑤ 元資料收割:ticker/目標價/評等/日期
        meta = harvest_meta(rpt / "2330_數位測試工業_20260115.txt", FIXTURE_FULL, prm,
                            getattr(mod, "BROKER_ABBR_DICT", {}))
        chk("元資料收割", meta.get("ticker") == "2330" and meta.get("target_price") == 250.0
            and meta.get("rating") == "買進" and meta.get("report_date") == "2026-01-15")

        # ⑥ 批跑三態+黃旗標註:sparse 件五點必有 AUTO 標
        rc, mx_out, _rd = run_batch(rpt, limit=None, no_open=True, out_root=sand / "out")
        runs = sorted((sand / "out").glob("DIGEST_*"))
        ok6 = bool(runs) and rc == 0
        if ok6:
            mx = json.loads((runs[-1] / "Digest_Matrix.json").read_text(encoding="utf-8"))
            sparse = next((r for r in mx["rows"] if r["file"].startswith("1560")), {})
            ind = next((r for r in mx["rows"] if r["file"].startswith("產業週報")), {})
            morn = next((r for r in mx["rows"] if r["file"].startswith("晨會報告")), {})
            ok6 = (mx["ok"] >= 3 and mx["fail"] == 0 and mx["skip"] == 3
                   and sparse.get("auto_filled", 0) >= 3
                   and ind.get("state", "").startswith("SKIP:非個股報告")
                   and morn.get("state", "").startswith("SKIP:非個股報告(類型"))
        chk("批跑三態+填充語標註", ok6)

        # ⑦ 產物齊:逐報告 md 含標註、U/I 含銘言
        ok7 = False
        if runs:
            mds = list(runs[-1].glob("*_digest.md"))
            ui = runs[-1] / prm["ui_name"]
            ok7 = (len(mds) >= 3 and ui.exists()
                   and MOTTO in ui.read_text(encoding="utf-8")
                   and any(prm["filler_tag"] in m.read_text(encoding="utf-8") for m in mds))
        chk("md+U/I 產物齊", ok7)

        # ⑧ 歸庫搬移:MOVED+全同讓位 DUP_SKIP+異內容 _sha 鏡像+manifest
        old1, old2 = sand / "old1", sand / "old2"
        newlib = sand / "newlib"
        old1.mkdir(); old2.mkdir()
        (old1 / "甲報告.txt").write_text(FIXTURE_FULL, encoding="utf-8")
        (old2 / "甲報告.txt").write_text(FIXTURE_FULL, encoding="utf-8")      # 全同=讓位
        (old2 / "乙報告.txt").write_text(FIXTURE_SPARSE, encoding="utf-8")
        (newlib / "").parent.mkdir(exist_ok=True)
        (newlib).mkdir(exist_ok=True)
        (newlib / "乙報告.txt").write_text("既存異內容", encoding="utf-8")     # 異內容=_sha 鏡像
        collect_reports([old1, old2], newlib, prm, sand / "mf")
        mfs = sorted((sand / "mf").glob("COLLECT_*_manifest.json"))
        ok8 = False
        if mfs:
            md_ = json.loads(mfs[-1].read_text(encoding="utf-8"))
            ok8 = (md_["moved"] == 2 and md_["dup_skip"] == 1 and md_["sha_mirror"] == 1
                   and (newlib / "甲報告.txt").exists()
                   and (old2 / "甲報告.txt").exists()          # 讓位=原地不動
                   and len(list(newlib.glob("乙報告_sha*.txt"))) == 1)
        chk("歸庫搬移(MOVED/讓位/_sha鏡像/manifest)", ok8)

        # ⑨ undo 可逆:MOVED 件全數回原位
        rc9 = undo_collect(mfs[-1]) if mfs else 1
        chk("undo 還原可逆", rc9 == 0 and (old1 / "甲報告.txt").exists()
            and (old2 / "乙報告.txt").exists()
            and not list(newlib.glob("乙報告_sha*.txt")))

        # ⑩ VDF 列建構+RICH 渲染道通(rich 缺=graceful 降級亦過)
        vrows = build_vdf_rows(mx_out) if mx_out else []
        ok10 = (len(vrows) == 3 and all("Ticker" in r for r in vrows)
                and json.dumps(vrows, ensure_ascii=False))
        rich_matrix("渲染道通測試", ["a", "b"], [["x", "OK"]], state_col=1)
        chk("VDF 列建構+RICH 渲染", bool(ok10))
        # ⑪ TW02 抽取道:首頁區英式評等+NT$ 千分位目標價(批55 令)
        tw02, tw02_name = load_tw02()
        ok11 = tw02 is not None
        if ok11:
            m11 = harvest_meta(rpt / "2330_數位測試工業_20260115.txt",
                               FIXTURE_TW02_HEAD, prm, {}, tw02)
            ok11 = (m11.get("rating") == "Overweight"
                    and m11.get("rating_class") == "BUY"
                    and m11.get("target_price") == 1200.0
                    and m11.get("src", {}).get("rating") == "TW02:首頁"
                    and m11.get("src", {}).get("target_price") == "TW02:首頁")
        chk("TW02 首頁區抽取(Overweight→BUY+NT$1,200)", ok11, f"({tw02_name})")

        # ⑫ TW02 內文 fallback(合理價變體)+TW02 缺席降級 v1 不假綠
        ok12 = tw02 is not None
        if ok12:
            m12 = harvest_meta(rpt / "1560_測試精機.txt",
                               FIXTURE_TW02_BODY, prm, {}, tw02)
            m_no = harvest_meta(rpt / "2330_數位測試工業_20260115.txt",
                                FIXTURE_FULL, prm, {}, None)  # 降級道
            ok12 = (m12.get("target_price") == 850.0
                    and m12.get("src", {}).get("target_price") == "TW02:內文"
                    and m12.get("rating") == "買進"
                    and m_no.get("target_price") == 250.0
                    and m_no.get("rating") == "買進"
                    and m_no.get("src") == {})
        chk("TW02 內文fallback(合理價850)+缺席降級v1", ok12)

        # ⑬ 市場判定三道:官方冊 TPEX>內文明示 .TWO>TWSE 預設(批59)
        regfx = {"6180": ("測試應材官方", "TPEX"), "2330": ("台積電", "TWSE")}
        r1 = resolve_equity("6180", "無明示", regfx)
        r2 = resolve_equity("2330", "看好 2330.TWO 動能", {})
        r3 = resolve_equity("1560", "無資訊", {})
        chk("市場判定(官方冊/明示/預設)+官方名",
            r1 == ("TPEX", "6180.TWO", "測試應材官方")
            and r2[0] == "TPEX" and r2[1] == "2330.TWO"
            and r3 == ("TWSE", "1560.TW", ""))

        # ⑭ 十一欄在列:分析師錨定+YF 代碼+官方名覆寫(seed 冊 2330=台積電)
        row2330 = next((r for r in mx["rows"] if r["file"].startswith("2330")), {}) if ok6 else {}
        chk("十一欄在列(分析師/YF/官方名)",
            row2330.get("analyst") == "王小明"
            and row2330.get("yf_ticker") == "2330.TW"
            and row2330.get("name") == "台積電"
            and row2330.get("name_src") == "官方冊"
            and "report_date" in row2330 and "market" in row2330)
        # ⑮ 類型閘+官方冊閘(批62;工作站真跑債定讞)
        regfx1k = {str(1101 + i): ("x", "TWSE") for i in range(1100)}
        regfx1k["2330"] = ("台積電", "TWSE")
        chk("類型閘+官方冊閘",
            classify_non_stock("凱基期貨晨間解盤20251205", "6919", {}, prm) is not None
            and classify_non_stock("GS-AI PCB CCL 20251204", "2730", regfx1k, prm) == "不在官方冊"
            and classify_non_stock("華南投顧-2606-裕民-1141202", "2606", {"2606": ("裕民", "TWSE")}, prm) is None
            and classify_non_stock("JP-2330 20250718", "2330", regfx1k, prm) is None)
        # ⑯ TP 黃旗:6533 類 -98.79 標記、常態 19.3 不標(值不改)
        chk("TP 黃旗(|上漲%|>80 誠實標)",
            tp_flag(-98.79, prm) and tp_flag(115.78, prm)
            and not tp_flag(19.3, prm) and not tp_flag(None, prm))
        # ⑰ 券商檔名縮寫局部識別(批64:MS-/GS-/Citi- 類)
        m17 = harvest_meta(rpt / "MS-2308 20251128.txt", "內文無券商線索之測試文",
                           prm, {}, None)
        m17b = harvest_meta(rpt / "Daiwa-1319 20231011.txt", "測試文", prm, {}, None)
        chk("券商檔名縮寫識別(MS/Daiwa)",
            m17.get("broker") == "Morgan Stanley"
            and m17.get("src", {}).get("broker") == "檔名縮寫"
            and m17b.get("broker") == "Daiwa 大和")
        # ⑱ 市場啟發式後備(操作員核定 OTC 區段;官方冊在位優先不變)
        r18a = resolve_equity("4153", "無明示", {}, prm)          # 4 開頭→TPEX 啟發式
        r18b = resolve_equity("2330", "無明示", {}, prm)          # 2 開頭→TWSE
        r18c = resolve_equity("6180", "無明示", {"6180": ("官方", "TPEX")}, prm)  # 冊優先
        r18d = resolve_equity("3231", "看好 3231.TW 動能", {}, prm)  # 明示壓過啟發式
        r18e = resolve_equity("6147", "報告文誤標 6147.TW", {"6147": ("頎邦", "TPEX")}, prm)
        nm, nsrc = shorten_official_name("德微科技股份有限公司", "華南投顧-3675-德微-Memo", prm)
        nm2, _ = shorten_official_name("台積電", "JP-2330", prm)
        chk("市場序(冊壓明示)+官方名簡稱化",
            r18a[1] == "4153.TWO" and r18b[1] == "2330.TW"
            and r18c[0] == "TPEX" and r18d[1] == "3231.TW"
            and r18e[1] == "6147.TWO"                       # 批67:冊 SSOT 壓誤標
            and nm == "德微" and nsrc == "官方冊+檔名簡稱" and nm2 == "台積電")
        # ⑲ 分析師三道+40 型分類閘(批65)
        m19a = harvest_meta(rpt / "t1.txt",
                            "本報告由 研究員 王大明 撰寫 wang.daming@kgi.com",
                            prm, {}, None)
        m19b = harvest_meta(rpt / "t2.txt",
                            "as prepared by jane.doe@ms.com for institutional clients",
                            prm, {}, None)
        cls40 = load_classifier40()
        g19 = classify_non_stock("MARKET WRAP 20251205", "2330", {}, prm, cls40, "")
        g19b = classify_non_stock("MS-2308 Update", "2308", {}, prm, cls40, "")
        m19c = harvest_meta(rpt / "t3.txt",
                            "Analyst Certification\nAnalysts employed by non-US affiliates",
                            prm, {}, None)
        chk("分析師三道(鄰近窗/EMAIL英名)+40型閘+抗噪",
            not m19c.get("analyst")
            and m19a.get("analyst") == "王大明"
            and m19a.get("src", {}).get("analyst") == "鄰近窗"
            and m19b.get("analyst") == "Jane Doe"
            and m19b.get("src", {}).get("analyst") == "EMAIL英名"
            and (cls40 is None or (g19 == "類型:MARKET_WRAP" and g19b is None)))
        # ⑳ BROKER 縮寫顯示+末欄標題+摘要(批65 令)
        abbr = prm.get("broker_abbr_display", {})
        row2330b = next((r for r in mx["rows"] if r["file"].startswith("2330")), {}) if ok6 else {}
        chk("BROKER縮寫+標題摘要欄",
            abbr.get("Morgan Stanley") == "MS" and abbr.get("元大") == "Yuanta"
            and "broker_abbr" in row2330b and bool(row2330b.get("point_1")))
        # ㉑ nan 誠實閘(批74:yfinance 失敗回 nan 不得上頁)
        chk("nan 誠實閘", _nn(float("nan")) is None and _nn(None) is None
            and _nn(1.25) == 1.25 and _nn("x") == "x"
            and not tp_flag(float("nan"), prm))
    n = 21 - len(fails)
    # 二十二檢(批120):多代碼綜合文件閘
    _prm22 = {"tw_ticker_locked": r"^(?:[1-9]\d{3})$|^(?!202[1-9]|2030)\d{4}$",
              "year_suspect": r"^20(2[1-9]|30)$"}
    _multi = " ".join(f"{1000+i*7} 公司{i}" for i in range(20))
    _r1 = multi_doc_gate(_multi, {"ticker": "1007"}, _prm22)
    _r2 = multi_doc_gate(_multi, {"ticker": "1007", "target_price": 100.0}, _prm22)
    _r3 = multi_doc_gate("2330 台積電 " * 10 + " 2454 2317", {"ticker": "2330"}, _prm22)
    chk("多代碼綜合閘(殺綜合/放支撐/放主導)",
        bool(_r1) and _r2 == "" and _r3 == "")
    # ── 批121 ㉓-㉖:三券商真件六債修 ──
    import tempfile as _tf
    with _tf.TemporaryDirectory() as _td:
        _sand = Path(_td)
        # ㉓ PDF 抽取道優先序(fitz)+數字接合正規化
        try:
            import fitz as _fz
            _pdf = _sand / "t23.pdf"
            _doc = _fz.open()
            _pg = _doc.new_page()
            _pg.insert_text((72, 72), "Target box", fontname="helv")
            _doc.save(str(_pdf))
            _t23, _s23 = extract_text(_pdf)
            ok23 = _s23 == "OK" and "Target box" in _t23
            note23 = "(fitz)"
        except ImportError:
            ok23, note23 = True, "(pdf 抽取器缺,道未測=誠實)"
        chk("㉓ PDF fitz 優先道", ok23 and _pdf_norm("2, 775 元") == "2,775 元"
            and _pdf_norm("112.00") == "112.00" and _pdf_norm("1 , 079") == "1,079", note23)
        # ㉔ TP 前次排除(參數冊 (?<!前次) 閘)
        m24 = harvest_meta(_sand / "t24.txt",
                           "前次目標價:2,720 元\n目標價:2,775 元", prm, {}, None)
        chk("㉔ TP 前次目標價排除(2,775 非 2,720)", m24.get("target_price") == 2775.0)
        # ㉕ broker 檔名 token(Daiwa1815→大和/CTBC260824→中信證)+檔名 YYMMDD 日期後備
        m25a = harvest_meta(_sand / "Daiwa1815_20260821.txt", "no broker in text", prm, {}, None)
        m25b = harvest_meta(_sand / "貿聯_3665B_CTBC260824.txt", "內文無券商", prm, {}, None)
        m25c = harvest_meta(_sand / "台積電_2330B_CTBC240612.txt", "內文無日期", prm, {}, None)
        chk("㉕ broker token+檔名YYMMDD後備",
            m25a.get("broker") == "Daiwa 大和"
            and m25a.get("report_date") == "2026-08-21"
            and m25b.get("broker") == "中國信託證券"
            and m25c.get("report_date") == "2024-06-12"
            and m25c.get("src", {}).get("report_date") == "檔名YYMMDD")
        # ㉖ TW02 評等抗噪(內文動詞/分布表拒;Rating: 標籤收)+分析師 EMAIL 窗優先
        tw26, _ = load_tw02()
        ok26 = tw26 is not None
        if ok26:
            r26a = harvest_meta(_sand / "a.txt",
                                "qualification to reduce the supply chain risks", prm, {}, tw26)
            r26b = harvest_meta(_sand / "b.txt",
                                "反傾銷稅(ADD)和反補貼稅(CVD)的實施", prm, {}, tw26)
            r26c = harvest_meta(_sand / "c.txt", "Rating: Overweight", prm, {}, tw26)
            r26d = harvest_meta(_sand / "d.txt",
                                "Rating  Percentage of total  Buy*  72.63%  Hold**", prm, {}, tw26)
            m26 = harvest_meta(_sand / "e.txt",
                               "個股與大盤走勢(%)\n許哲豪\njeff.syu@ctbcsis.com", prm, {}, None)
            ok26 = (not r26a.get("rating") and not r26b.get("rating")
                    and r26c.get("rating") == "Overweight" and not r26d.get("rating")
                    and m26.get("analyst") == "許哲豪"
                    and m26.get("src", {}).get("analyst") == "鄰近窗")
        chk("㉖ TW02評等抗噪+分析師EMAIL窗優先", ok26)
    print(f"  [計] 二十六檢 OK {26 - len(fails)} · FAIL {len(fails)} · {round(time.time() - t0, 1)}s")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 個股報告摘要批跑器 v0111 · 二十六檢自測(合成 fixture 零網路)===")
        return selftest()
    if "--undo" in args:
        i = args.index("--undo")
        if i + 1 >= len(args):
            print("[用法] via-digest --undo <manifest路徑>")
            return 2
        print("=== 歸庫搬移 undo(零刪除鐵律)===")
        return undo_collect(Path(args[i + 1]))
    if "--collect" in args:
        prm = load_params()
        sources = [Path(args[i + 1]) for i, a in enumerate(args)
                   if a == "--from" and i + 1 < len(args)]
        if not sources:
            print("[用法] via-digest --collect --from <舊報告夾> [--from <舊夾2>] [--to <新夾>]")
            return 2
        dest = (Path(args[args.index("--to") + 1]) if "--to" in args
                else VIA / "functional modules/VRN/input/reports")
        print(f"=== 原報告歸庫搬移 → {dest}(manifest+undo;全同讓位/_sha 鏡像)===")
        return collect_reports(sources, dest, prm, VIA / prm["output_root"])
    limit = None
    if "--limit" in args:
        i = args.index("--limit")
        limit = int(args[i + 1]) if i + 1 < len(args) else None
    no_open = "--no-open" in args
    prm = load_params()
    if "--dir" in args:
        i = args.index("--dir")
        report_dir = Path(args[i + 1]) if i + 1 < len(args) else None
        if not report_dir or not report_dir.exists():
            print(f"  [FAIL] 報告夾不存在:{report_dir}")
            return 1
    else:
        report_dir = next((VIA / d for d in prm["default_scan_dirs"]
                           if (VIA / d).exists()), None)
        if report_dir is None:
            print("  [SKIP] 未指定 --dir 且預設候選夾皆缺(誠實):")
            for d in prm["default_scan_dirs"]:
                print(f"         · {d}")
            return 0
        print(f"  [夾] 未指定 --dir,用預設候選:{report_dir.relative_to(VIA)}")
    print(f"=== 個股報告摘要批跑器 v0111 · 批121 三券商真件六債修(TOOL-070)===")
    rc, matrix, run_dir = run_batch(report_dir, limit, no_open)
    if "--vdf" in args and matrix and run_dir:
        rc = max(rc, run_vdf_chain(matrix, run_dir))
    return rc


if __name__ == "__main__":
    sys.exit(main())
