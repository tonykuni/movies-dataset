#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
VDF_ENG082_FinStatements v0104 — 三大報表擷取引擎(側線 2026-09-24 第十四段 · PR #116 審查修正)
v0103→v0104(側線 2026-09-24 第十四段;主線批號由併線的手指定 L25;PR #116 以 v0103 併進 main 之後,Codex 審四條逐條實量屬實):
  ① 空列表、或有值卻一項都解不出的回應(欄名或年季變了),v0103 記 OK、0 項 → 計畫判齊,要等下一季才重抓。v0104 分三種:
     佔位列(除了出表日期全空;實量 TPEX 8 個空業別端點都是這樣)=空業別 OK;空列表=EMPTY;有值卻一項都解不出=UNPARSED。
     後兩種不算抓成功、不記完成、下次照抓;解析例外也照報 ERROR、不記完成。同類的另一種:平常有資料的業別偶爾只回佔位列
     (上次 0 項、前一次有項目)→ 計畫再抓一次確認;連兩次 0 項才算真的空了(業別真的清空也不會一直重抓)。
  ② 一個端點成功、其餘逾時,v0103 整個市場標 OK、rc0。v0104 抓完用同一套判準(mops_plan)重算還缺什麼:全齊才 rc0;
     還缺(被擋 · 失敗 · 舊一季 · 少了)= PARTIAL / NODATA rc2(VDF_ENG057 · ENG078 同慣例),並印 [仍缺]。
  ③ 那一批只少了幾項(不是全刪),v0103 認不出。台帳多記「寫入後表裡實存項數」n_stored,計畫拿現有項數比,少了就重抓
     (比實存不比解析項數:同一批重複的列、別的端點先寫過的同鍵,都不會被當成少了)。
  ④ 期限當天抓的 v0103 算齊,可是期限當天還能申報。v0104:「該齊的那一季」要等期限整天過完;期限當天或之前抓的都照抓。
  另外:改壞測試量到正典 upsert_rows 照 v0110 語意不替來源去重,一批裡同鍵兩列會兩列都進表(實量);交易所回應若有重複列,
  長表就有重複鍵。v0104 寫入前同一批同鍵只留第一筆,報「同一批重複 N 項只留第一筆」(真資料量過 0 重複)。
  升級相容:v0103 建的台帳沒有 n_stored 欄,計畫照讀(當 NULL),寫台帳時正典 upsert_rows 照型別補欄。
  自測 ⑭⑮⑳ 的 rc 改成誠實的 rc2,⑬ 加驗佔位列 / 認不出的列數,⑯ 加驗 --force 重抓已齊的市場 rc0;
  +㉒ 釘住四條(另加同批重複只留一筆、表裡零重複鍵 · 別的端點先寫過的同鍵不當成少了 · 解析例外記 ERROR)。二十二檢。

VDF_ENG082_FinStatements v0103 — 三大報表擷取引擎(側線 2026-09-24 第十三段:交易所 MOPS 彙總財報車道)
v0102→v0103(側線 2026-09-24 第十三段;主線批號由併線的手指定 L25;掉球 Z165 · Z4;操作員令「所有數據都以交易所為主」
  「擷取資料前要先檢查資料庫缺啥,確定擷取範圍去擷取 … 整合資料庫去重補不足 確保完整性」):
  財報原本只有 yfinance 一條車道,MOPS 只探路不解析(Z165:燈綠的是新鮮度不是覆蓋)。v0103 加**交易所車道** `run --mops`
  (照現有短令 via-finstat 就能跑,不必動 .ps1):
  · 來源=交易所公開 OpenAPI 的 MOPS 彙總財報,**整市場一次一個業別**:上櫃 TPEX mopsfin_t187ap06_O_*(綜合損益表)/
    t187ap07_O_*(資產負債表),上市 TWSE t187ap06_L_* / t187ap07_L_*;業別六種(一般 ci · 金融 basi · 證券期貨 bd · 金控 fh ·
    保險 ins · 異業 mim)。一個市場 12 個請求就是全市場;它只給**最新一季**,歷史靠每季跑一次累積(只增不減)。
  · 實量(容器 2026-09-24,只量測、不經引擎):TPEX 12 個端點都回 JSON——一般業損益 885 家 / 資產負債 885 家(115 年第 2 季),
    證券期貨業 7 家,其餘業別回一列空的佔位列;兩類端點的欄名不一樣(代號 SecuritiesCompanyCode / 公司代號、日期 Date / 出表日期、
    年季 Year+Season / 年度+季別),還有一欄欄名是空白字元。TWSE 從容器回 800B 安全頁(跟 T86 同),工作站再驗(Z201)。
  · **損益表是年初至今累計,不是單季**:883 家拿 Q2 營業收入 ÷ 同家 1–8 月累計月營收,中位數 0.736(≈6/8;單季會是 ≈0.375)。
    所以另存一張長表 `tw_financial_mops`(一家 × 一季 × 一科目一列,科目名照交易所原文、單位另列:仟元 / 元 / 股;
    basis=YTD 或 POINT),**不**混進 yfinance 那張 tw_financial——那張的消費者(VRN_ENG074 等)讀的是單季/年度,混進去會把累計數當單季。
  · 先查庫再抓(操作員令①):**逐端點**(市場 × 報表 × 業別)看擷取台帳 tw_financial_mops_log 與資料表——這個端點在「今天該齊
    的那一季」(法定期限已過的最近一季;季界與期限全走正典 period_lag,季底月日讀期別規則冊,本支不另寫季底表或期別換算 LL442)
    的期限之後抓成功過、拿到的不是更舊的季、有項目的那一批資料表裡
    還在,三條都成立才不抓;一個端點傳輸敗,下次只補它。空業別(只有佔位列)抓成功過就算齊。`--force` 照抓。
    `--dry` 只印計畫(不碰網路、不寫庫,閘沒開也能看)。每個端點每一趟的結果(態 · 幾列幾項 · 期別)記進擷取台帳(正典
    upsert_rows,鍵 source+fetched_at,只增);中斷那一趟不記(下次照抓)。
  · 抓法走正典:網路只經 NetUnified http_text(閘先行,永不代設)· 批次走 SUP_MDL753 batch_fetch(每個端點抓完就落庫,中斷不失)·
    寫入走正典 upsert_rows(鍵 code+period+statement+item,只增不覆寫,schema= 照宣告欄型)· 民國年、出表日期一律走正典 roc_to_iso
    (不自寫民國換算)· 數字走正典 num。同鍵異值(交易所更正過的數字)照留舊值、只報項數。
  · 覆蓋率另立(Z165):status 多印一段「交易所財報覆蓋」:每市場最新一季有損益 / 資產負債的家數對冊上家數,**不混進新鮮度燈**;
    另列各端點最近一次抓的結果(例 TWSE BLOCKED 12)。
  · 市場參數照收 tpex / twse(逗號或 PowerShell 拆開都吃);打錯字 → [用法] rc2(不謊報已齊);只指定被擋的市場 → rc2 NODATA。
  yfinance 車道(run 不帶 --mops)一字不動。自測 +⑬–㉑ 共二十一檢。

VDF_ENG082_FinStatements v0102 — 三大報表擷取引擎(批689B PR #63 Codex 兩條 P2 都是真的)
v0101→v0102:
  ① 「逾時的注入執行緒沒被停掉」:v0101 的看門狗 join 完就走,daemon 執行緒還在 Yahoo 那邊重試,多檔連跑會把連線/記憶體
     一直疊上去。v0102 兩條車道**都開子行程**(`_lane_pull(ticker, inject)`):注入車道在子行程裡自己建 AegisNexus session 注入
     yfinance,逾時 = kill,不留殭屍;原生車道同一支子行程不注入。主行程從此不碰 yfinance 單例。
  ② 「沒有 duckdb 的境 --selftest 會炸」:⑪ 的 `import duckdb` 沒包 ImportError,③–⑥ 那條「無 duckdb=SKIP 誠實」的路它沒走;
     v0102 ⑪ 同一條路(缺 duckdb=SKIP)。十二檢不變。

VDF_ENG082_FinStatements v0101 — 三大報表擷取引擎(批688 工作站第一次真跑:三個洞一次補)
v0100→v0101(批688 操作員實錄 `via-py vdf … run --only 2330,2454`):
  ① `目標 1 檔`:PowerShell 把 `2330,2454` 當陣列拆成兩個參數,`--only` 只吃到第一個。v0101 的 --only 把後面連續的非旗標 token 全收,再各自以逗號拆。
  ② `yfinance Ticker(2330.TW) failed: Yahoo API requires curl_cffi session not requests.Session` 兩次 → 零列:
     收容件把例外吞成 WARNING 回空列,v0100 只在 TypeError 才退原生,於是永遠退不到。v0101:注入 session 那一趟零列就**再跑一趟原生**
     (yfinance 自帶 curl_cffi;docstring 從 v0100 起就寫「拒收=退原生,tag 講明」,現在真的做到),兩趟都空才記零列。
  ③ 零列之後 `SELECT COUNT(*) FROM tw_financial` 直接 Traceback(表根本沒建過):改成表不在=0,零列誠實 rc2 並講「一列都沒抓到,表未建」。
  ④ 容器實測(faulthandler 75s 堆疊):注入 AegisNexus session 那一趟不是拒收而是**在 urllib3 Retry 退避睡眠裡爬**
     (Cookie/crumb fetch failed (RetryError) 一再重試),一檔幾分鐘才回空列。AegisNexus 車道仍然先走(L09),但加**看門狗**:
     INJECT_TIMEOUT_S=40 秒沒回就放掉那條執行緒(daemon)改走原生;tag 講明是「逾時→原生」還是「零列→原生」。
  ⑤ 原生那一趟**必須另開子行程**:yfinance 的 YfData 是單例,注入過一次 session 之後,同一行程裡「不帶 session」的 Ticker
     仍拿同一個注入 session 在爬(容器實測:看門狗之後的原生趟一樣不回)。子行程=乾淨的 yfinance,逾時可 kill(不留殭屍執行緒)。
  十二檢 +⑨⑩⑪⑫。

VDF_ENG082_FinStatements v0100 — 三大報表擷取引擎(批505;填主控台冊 vdf/fin_statements「缺席」空位)
====================================================================
操作員上傳 vdf_fetchers_financials.py(收容 VDF/references/intake/vdf_fetchers_financials_b504;正本零觸碰)。
它直呼 requests/yfinance,批494 律:網路只認 VeritasAegisNexus。本引擎**只掛不搬**:
  · 同意閘:SUP_MDL740 NetUnified gate_state()(法遵雙閘 VIA_NET_CONSENT + VIA_SCRAPE_CONSENT;fail-closed;永不代設)
  · MOPS 車道:走 NetUnified http_text(AegisNexus 車道)只**探路**(可達/長度入台帳);解析=候(收容件自己也寫「TODO/brittle」)
  · yfinance 車道:收容件 _fin_from_yfinance(canonical schema tw_financial 23 欄),Ticker 以 AegisNexus ResilientHTTPClient session
    注入(yfinance 若拒絕該 session 型別=退原生,tag 講明);yfinance 缺席=[缺件] 誠實停 rc2(裝=你的手)
  · 落地:DuckDB 表 tw_financial(派生層:同 Ticker DELETE+INSERT,冪等)+ parquet(duckdb COPY,零 pyarrow 相依)於 output_hub/mega/fin/
  · 庫找法:--db > env VIA_DB_VDF_TW_MARKET > VIA_DATA_HOME 內最新 vdf_tw_market.duckdb > output_hub/mega
用法:python3 VDF_ENG082_FinStatements_v0100.py run [--only 2330,2317] [--limit 5] [--years 5] [--db PATH] [--dry]
      | run --mops [--market tpex,twse] [--force] [--db PATH] [--dry]    (v0103 交易所車道;短令 via-finstat run --mops)
      | status [--db PATH] | --selftest
律:只增不減;誠實三態(GATED/ABSENT/NODATA/GREEN);零 CDN;閘不代設;自測零網路零污染(暫存庫)。
"""
from __future__ import annotations

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(VDF 全導入令;惰性載入=import 時零網路、零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT;網路只認 AegisNexus);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

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
# ===== [VIA:LIB-BRIDGE:v0100] 三庫正典橋(批597;缺席大聲拋,不 graceful) =====
import sys as _lb_sys
from functools import partial as _lb_partial
from pathlib import Path as _lb_Path
_lb_p = _lb_Path(__file__).resolve()
while _lb_p.parent != _lb_p:
    if (_lb_p / "supportive modules").is_dir():
        _lb_sys.path.insert(0, str(_lb_p / "supportive modules"))
        break
    _lb_p = _lb_p.parent
import VIA_LibCanon as _LIB          # 正典缺席=大聲拋,不假裝有(LL151)
# ===== [VIA:LIB-BRIDGE:END] =====

import importlib.util
import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
VDF = HERE.parent
VIA = VDF.parent.parent
OUT = VDF / "output_hub" / "mega"
INTAKE = VDF / "references" / "intake"
TABLE = "tw_financial"
VERSION = "0104"
INJECT_TIMEOUT_S = 40          # 批688:注入 session 那一趟的看門狗(秒);逾時=放掉改走原生,不是壞
NATIVE_TIMEOUT_S = 90          # 批688:原生那一趟(子行程)的逾時(秒)
MOPS_PROBE = "https://mops.twse.com.tw/mops/web/t164sb04"
# v0103 交易所車道:MOPS 彙總財報(交易所公開 OpenAPI;整市場,只給最新一季)
MOPS_TABLE = "tw_financial_mops"
MOPS_OA = {"TPEX": "https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap{st}_O_{ind}",
           "TWSE": "https://openapi.twse.com.tw/v1/opendata/t187ap{st}_L_{ind}"}
MOPS_IND = ("ci", "basi", "bd", "fh", "ins", "mim")       # 一般 · 金融 · 證券期貨 · 金控 · 保險 · 異業
MOPS_ST = {"06": "IS", "07": "BS"}                        # 綜合損益表(年初至今累計)· 資產負債表(季底時點)
MOPS_KEYS = ["code", "period", "statement", "item"]
MOPS_SCHEMA = ("date VARCHAR, code VARCHAR, name VARCHAR, market VARCHAR, industry VARCHAR, statement VARCHAR, basis VARCHAR, "
               "item VARCHAR, value DOUBLE, unit VARCHAR, period VARCHAR, report_date VARCHAR, source VARCHAR, fetched_at VARCHAR")
MOPS_META = {"year": ("Year", "年度"), "quarter": ("Season", "季別"), "code": ("SecuritiesCompanyCode", "公司代號"),
             "name": ("CompanyName", "公司名稱"), "report": ("Date", "出表日期")}
MOPS_SLEEP_S = 0.5                                        # 每個請求之間(交易所節流紀律)
MOPS_LOG = "tw_financial_mops_log"                        # 擷取台帳:每個端點每一趟的結果(空業別沒有資料列,只能靠它知道「抓成功過」)
MOPS_LOG_KEYS = ["source", "fetched_at"]
MOPS_LOG_SCHEMA = ("market VARCHAR, statement VARCHAR, industry VARCHAR, source VARCHAR, state VARCHAR, n_records BIGINT, "
                   "n_items BIGINT, n_stored BIGINT, period VARCHAR, period_end VARCHAR, note VARCHAR, fetched_at VARCHAR")


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def fetcher():
    """收容件尾版(vdf_fetchers_financials_b*/vdf_fetchers_financials.py);缺=None(誠實)。"""
    hits = sorted(INTAKE.glob("vdf_fetchers_financials_b*/vdf_fetchers_financials.py"))
    if not hits:
        return None
    try:
        return _load("vdf_fetchers_financials_intake", hits[-1])
    except Exception:
        return None


def net():
    """NetUnified(via_net_unified_v*.py → SUP_MDL740 正典);缺=None。"""
    hits = sorted((VIA / "supportive modules" / "network").glob("via_net_unified_v*.py"))
    if not hits:
        return None
    try:
        return _load("via_net_for_eng082", hits[-1])
    except Exception:
        return None


def gate_open() -> tuple:
    n = net()
    if n is None or not hasattr(n, "gate_state"):
        env = os.environ
        return (env.get("VIA_NET_CONSENT") == "YES" and bool(env.get("VIA_SCRAPE_CONSENT"))), "NetUnified 缺;退 env 直讀"
    g = n.gate_state()
    return bool(g.get("open")), f"gate1 {g.get('gate1_raw')} · gate2 {'set' if g.get('gate2_scrape_token_set') else '(未設)'}"


def aegis_session():
    """AegisNexus ResilientHTTPClient 的 requests session(給 yfinance 注入);缺=None + why。"""
    p = VIA / "supportive modules" / "network" / "VeritasAegisNexus.py"
    if not p.is_file():
        return None, "VeritasAegisNexus.py 缺"
    try:
        m = _load("via_aegis_for_eng082", p)
        cli = m.ResilientHTTPClient()
        s = cli._get_session()
        return s, f"AegisNexus session {type(s).__name__}"
    except Exception as exc:
        return None, f"AegisNexus session 取不到 {type(exc).__name__}:{str(exc)[:50]}"


def columns() -> list:
    f = fetcher()
    if f is None:
        return ["Date", "Ticker", "Period", "Period_Type", "Revenue", "Gross_Profit", "Operating_Income", "Net_Income", "EPS", "Total_Assets",
                "Total_Liabilities", "Equity", "Operating_CF", "Investing_CF", "Financing_CF", "Free_CF", "ROE", "ROA", "Gross_Margin",
                "Operating_Margin", "Net_Margin", "Debt_To_Equity", "Source"]
    return list(f._new_row("", "", "", "").keys())


def norm_ticker(t: str) -> str:
    """2330 → 2330.TW;2330.TWO/AAPL 照原;四碼台股預設上市(.TW),回空=.TWO 再試由 run 決定。"""
    t = str(t or "").strip().upper()
    if not t:
        return ""
    if t.isdigit() and len(t) == 4:
        return t + ".TW"
    return t


def _resolve_db(explicit: str | None):
    if explicit:
        return Path(explicit)
    e = os.environ.get("VIA_DB_VDF_TW_MARKET")
    if e and Path(e).is_file():
        return Path(e)
    home = os.environ.get("VIA_DATA_HOME")
    if home and Path(home).is_dir():
        c = sorted((q for q in Path(home).rglob("vdf_tw_market.duckdb") if "/_self_test" not in str(q).replace("\\", "/")), key=lambda q: q.stat().st_mtime)
        if c:
            return c[-1]
    p = OUT / "vdf_tw_market.duckdb"
    return p if p.is_file() else None


def listings(con, limit: int) -> list:
    try:
        rows = con.execute("SELECT code FROM tw_listings WHERE code IS NOT NULL ORDER BY code LIMIT ?", [int(limit)]).fetchall()
        return [str(r[0]) for r in rows]
    except Exception:
        return []


_LANE_CODE = (
    "import sys, json, logging, importlib.util as u; logging.disable(logging.WARNING)\n"
    "fp, ticker, inject, aegis = sys.argv[1], sys.argv[2], sys.argv[3] == '1', sys.argv[4]\n"
    "tag = 'native'\n"
    "if inject:\n"
    "    try:\n"
    "        import functools, yfinance as yf\n"
    "        sp = u.spec_from_file_location('via_aegis_lane', aegis); m = u.module_from_spec(sp); sys.modules['via_aegis_lane'] = m; sp.loader.exec_module(m)\n"
    "        s = m.ResilientHTTPClient()._get_session()\n"
    "        yf.Ticker = functools.partial(yf.Ticker, session=s); tag = 'aegis:' + type(s).__name__\n"
    "    except Exception as e:\n"
    "        print(json.dumps({'rows': [], 'tag': 'aegis-inject-failed:' + type(e).__name__})); sys.exit(0)\n"
    "sp = u.spec_from_file_location('fetch_lane', fp); m = u.module_from_spec(sp); sys.modules['fetch_lane'] = m; sp.loader.exec_module(m)\n"
    "try:\n"
    "    rows = list(m._fin_from_yfinance(ticker))\n"
    "except Exception as e:\n"
    "    print(json.dumps({'rows': [], 'tag': tag + ':' + type(e).__name__ + ':' + str(e)[:60]})); sys.exit(0)\n"
    "print(json.dumps({'rows': rows, 'tag': tag}, default=str))\n"
)


def _lane_pull(ticker: str, inject: bool, timeout_s: float) -> tuple:
    """批689B:一條車道=一個**子行程**(可 kill,不留殭屍;yfinance 單例不進主行程)。
    inject=True 在子行程裡自建 AegisNexus session 注入 yfinance;False=原生。回 (rows, tag);逾時=([], 'timeout')。"""
    import json as _json
    import subprocess as _sp
    f = fetcher()
    fp = getattr(f, "__file__", "") or ""
    if not fp:
        return [], "no-fetcher"
    aegis = str(VIA / "supportive modules" / "network" / "VeritasAegisNexus.py")
    try:
        r = _sp.run([sys.executable, "-c", _LANE_CODE, fp, ticker, "1" if inject else "0", aegis],
                    capture_output=True, text=True, timeout=timeout_s, stdin=_sp.DEVNULL,
                    env=dict(os.environ, PYTHONUTF8="1"))
    except _sp.TimeoutExpired:
        return [], "timeout"                                     # subprocess.run 逾時=子行程已被 kill
    except Exception as exc:
        return [], f"spawn-failed:{type(exc).__name__}"
    if r.returncode != 0:
        return [], f"rc{r.returncode}"
    line = (r.stdout or "").strip().splitlines()
    try:
        d = _json.loads(line[-1]) if line else {}
        return list(d.get("rows") or []), str(d.get("tag") or "")
    except Exception:
        return [], "bad-json"


def _native_pull(ticker: str) -> list:
    """相容殼(v0101 名字):原生車道。"""
    return _lane_pull(ticker, False, NATIVE_TIMEOUT_S)[0]


def _pull(ticker: str, years: int) -> tuple:
    """yfinance 車道:先 AegisNexus 注入(子行程,看門狗 INJECT_TIMEOUT_S,逾時 kill),零列/逾時/拒收 → 原生(子行程)。
    回 (rows, tag);tag 講明走了哪一趟。零快取、零假抽。"""
    f = fetcher()
    if f is None:
        return [], "ABSENT(收容件 vdf_fetchers_financials 缺)"
    try:
        import yfinance  # noqa: F401  只驗缺件;主行程不建 Ticker
    except Exception as exc:
        return [], f"缺件 No module named 'yfinance'({type(exc).__name__};via-envtools 排裝,裝=你的手)"
    rows, t1 = _lane_pull(ticker, True, INJECT_TIMEOUT_S)
    if rows:
        tag = f"AegisNexus session({t1})"
    else:
        why = (f"逾時 {INJECT_TIMEOUT_S}s(urllib3 Retry 退避)" if t1 == "timeout"
               else (f"拒收/失敗 {t1}" if (":" in t1 or "failed" in t1) else "零列"))
        rows, t2 = _lane_pull(ticker, False, NATIVE_TIMEOUT_S)
        tag = f"AegisNexus session {why}→原生(子行程,yfinance 自帶 curl_cffi)" + (" 有料" if rows else f" 仍零列({t2})")
    cutoff = f"{datetime.now().year - int(years)}-01-01"
    rows = [r for r in rows if str(r.get("Period", "")) >= cutoff]
    return rows, tag


def write_rows(con, rows: list, cols: list) -> int:
    con.execute("CREATE TABLE IF NOT EXISTS " + TABLE + " (" + ", ".join(f'"{c}" ' + ("VARCHAR" if c in ("Date", "Ticker", "Period", "Period_Type", "Source") else "DOUBLE") for c in cols)
                + ", fetched_at VARCHAR)")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tickers = sorted({r.get("Ticker") for r in rows if r.get("Ticker")})
    for t in tickers:
        con.execute(f"DELETE FROM {TABLE} WHERE Ticker = ?", [t])          # 派生層重算:同 Ticker 重寫
    ph = ",".join("?" for _ in cols) + ",?"
    for r in rows:
        con.execute(f"INSERT INTO {TABLE} VALUES ({ph})", [r.get(c) for c in cols] + [now])
    return len(rows)


def mops_probe(code: str) -> dict:
    """MOPS 探路(AegisNexus 車道;只記可達/長度;解析=候)。閘未開=DENIED 誠實。"""
    n = net()
    if n is None or not hasattr(n, "http_text"):
        return {"state": "ABSENT", "why": "NetUnified 缺"}
    try:
        r = n.http_text(MOPS_PROBE, timeout=20)
        return {"state": r.get("state", "?"), "len": len(str(r.get("data") or "")), "via": r.get("via", ""), "why": str(r.get("why") or r.get("reason") or "")[:80]}
    except Exception as exc:
        return {"state": "FAIL", "why": f"{type(exc).__name__}:{str(exc)[:60]}"}


def mops_unit(item: str) -> str:
    """科目 → 單位(交易所彙總財報:金額仟元;每股類與標「（元）」的是元;標「（單位：股）」的是股)。"""
    s = str(item)
    if "單位：股" in s or "單位:股" in s:
        return "股"
    if "（元）" in s or "(元)" in s or "每股" in s:
        return "元"
    return "仟元"


def _mops_qends() -> list:
    """季別 1–4 → 季底月日('03/31' …):讀期別規則冊 quarterly_statements 的期限表鍵(就是四個季底月日);
    本支不另寫季底表或期別換算(LL442)。冊上不是四個季底 → 大聲拋(不靜默把每一列都跳掉)。"""
    due = ((_LIB.UTILS.load_period_rules().get("cadences") or {}).get("quarterly_statements") or {}).get("due") or {}
    ends = sorted(due)
    if len(ends) != 4:
        raise ValueError(f"期別規則冊 quarterly_statements 的期限表應有四個季底月日,實得 {ends}")
    return [x.replace("-", "/") for x in ends]


def _mops_placeholder(rec) -> bool:
    """交易所空業別的佔位列:除了出表日期,每一欄都是空的(實量 TPEX 四個空業別 × 兩表,8 個端點都是這樣)。"""
    return isinstance(rec, dict) and all(v is None or not str(v).strip() for k, v in rec.items() if k not in MOPS_META["report"])


def mops_rows(data, market: str, statement: str, industry: str, source: str, fetched_at: str, stats: dict | None = None) -> list:
    """交易所 OpenAPI 一個端點的回應(list of dict)→ 長表列(一家 × 一季 × 一科目一列)。
    欄名兩套都認(Year/年度 · Season/季別 · SecuritiesCompanyCode/公司代號 · CompanyName/公司名稱 · Date/出表日期);
    沒有年季或代號的佔位列、欄名是空白的欄、空值都跳過。民國年季 → 季底日與出表日期一律走正典 roc_to_iso(不自寫換算),
    季底月日讀期別規則冊。v0104:stats 給了就回填 skipped =「不是佔位列、卻一項都沒解出來」的列數(欄名或年季變了的訊號)。"""
    meta_keys = {a for al in MOPS_META.values() for a in al}
    qends = _mops_qends()
    out, skipped = [], 0
    for rec in data or []:
        if _mops_placeholder(rec):
            continue                                             # 空業別的佔位列:正常,不算認不出
        if not isinstance(rec, dict):
            skipped += 1
            continue
        m = {k: next((str(rec[a]).strip() for a in al if a in rec and rec[a] is not None), "") for k, al in MOPS_META.items()}
        q = int(m["quarter"]) if m["quarter"].isdigit() else 0     # 佔位列季別是空的
        if not 1 <= q <= 4 or not m["code"] or not m["year"]:
            skipped += 1
            continue
        pe = _LIB.UTILS.roc_to_iso(f"{m['year']}/{qends[q - 1]}")
        if not pe:
            skipped += 1
            continue
        rep = _LIB.UTILS.roc_to_iso(m["report"]) if m["report"] else None
        n0 = len(out)
        for k, v in rec.items():
            item = str(k).strip()
            if not item or k in meta_keys:
                continue
            val = _LIB.UTILS.num(v)
            if val is None:
                continue
            out.append({"date": pe, "code": m["code"], "name": m["name"], "market": market, "industry": industry,
                        "statement": statement, "basis": "YTD" if statement == "IS" else "POINT", "item": item, "value": val,
                        "unit": mops_unit(item), "period": f"{pe[:4]}Q{q}", "report_date": rep, "source": source, "fetched_at": fetched_at})
        if len(out) == n0:
            skipped += 1                                         # 年季代號都在、卻一個數字都沒有
    if stats is not None:
        stats["skipped"] = skipped
    return out


def mops_fetch(url: str) -> tuple:
    """一個端點 → (態, 資料或因由)。態:OK(list)· DENY(閘)· BLOCKED(交易所安全頁)· FAIL · ABSENT(NetUnified 缺)。"""
    n = net()
    if n is None or not hasattr(n, "http_text"):
        return "ABSENT", "NetUnified 缺"
    r = n.http_text(url, timeout=60)
    st = str(r.get("state") or "")
    if st == "DENY":
        return "DENY", str(r.get("note") or "閘未開")
    if st != "OK":
        return "FAIL", str(r.get("note") or r.get("why") or st)[:120]
    body = r.get("data")
    txt = body.decode("utf-8", "replace") if isinstance(body, (bytes, bytearray)) else str(body or "")
    head = txt.lstrip()[:2000]
    if head.startswith("<") and ("SECURITY" in head.upper() or "安全性" in head):
        return "BLOCKED", "交易所回安全頁(這台機器或頻率被擋;換工作站再試)"
    try:
        data = json.loads(txt)
    except ValueError:
        return "FAIL", "回應不是 JSON"
    if not isinstance(data, list):
        return "FAIL", "回應不是列表"
    return "OK", data


def mops_target(today=None) -> tuple:
    """今天該齊的是哪一季 = 法定期限已過的最近一季 → (季底日, 期限)。季界與期限全走正典 period_lag
    (它回「值所在那一季的季底 iso」與「下一季的期限 due」,規則在期別規則冊 quarterly_statements);本支不另寫季底表或
    期別換算(LL442),只做「季底 +1 天 = 下一季第一天」。規則沒認到 → (None, None)。"""
    today = today or datetime.now().date()
    d, best = today - timedelta(days=400), (None, None)
    for _ in range(8):
        cur = _LIB.UTILS.period_lag(MOPS_TABLE, d.isoformat(), today=today)
        if cur.get("state") != "PERIOD_DUE" or not cur.get("iso") or not cur.get("due"):
            return None, None
        if str(cur["due"]) >= today.isoformat():                                         # v0104:期限當天還能申報,過了那天才算
            break
        d = datetime.strptime(cur["iso"], "%Y-%m-%d").date() + timedelta(days=1)          # 下一季第一天
        best = (_LIB.UTILS.period_lag(MOPS_TABLE, d.isoformat(), today=today).get("iso"), str(cur["due"]))
    return best


def _mops_url(m: str, st: str, ind: str) -> str:
    return MOPS_OA[m].format(st=st, ind=ind)


def _mops_source(m: str, st: str, ind: str) -> str:
    return _mops_url(m, st, ind).rsplit("/", 1)[-1]


def mops_plan(dbp, markets: list, force: bool, today=None) -> dict:
    """先查庫(操作員令①):**逐端點**(市場 × 報表 × 業別)看擷取台帳與資料表 → 要抓哪幾個。交易所 OpenAPI 只給最新一季;
    三條都成立才不抓:① 這個端點在「今天該齊的那一季」的法定期限之後抓成功過 ② 那一趟拿到的不是更舊的季
    ③ 那一趟有項目的話,資料表裡那一批的項數不少於寫入後實存的項數(v0104:少了幾項也重抓)。空業別(只有佔位列)抓成功過就算齊。
    v0104:期限當天抓的不算(當天還能申報);上次 0 項(只有佔位列)、前一次卻有項目 → 再抓一次確認(連兩次 0 項才算真的空了)。
    一個端點傳輸敗 → 下次只補它,不因為同市場別的端點到位就整個市場判齊。回 {市場: ([(報表, 業別) 要抓的…], 因由)}。"""
    eps = [(st, ind) for st in MOPS_ST for ind in MOPS_IND]
    if force:
        return {m: (list(eps), "--force 照抓") for m in markets}
    qe, due = mops_target(today)
    if qe is None:
        return {m: (list(eps), f"期別規則沒認到 {MOPS_TABLE}(冊上 quarterly_statements),照抓") for m in markets}
    last, have, prev_n = {}, {}, {}
    if dbp is not None and Path(dbp).exists():
        import duckdb
        try:
            con = duckdb.connect(str(dbp), read_only=True)
        except Exception as exc:
            return {m: (list(eps), f"庫開不了({type(exc).__name__}),照抓") for m in markets}
        try:
            tabs = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
            if MOPS_LOG in tabs:
                lcols = {r[0] for r in con.execute(f"DESCRIBE {MOPS_LOG}").fetchall()}
                ns_sql = "n_stored" if "n_stored" in lcols else "NULL AS n_stored"          # v0103 建的台帳沒有這一欄(寫台帳時正典會加)
                for src, f, p, pe, n, ns, rn in con.execute(
                        f"SELECT source, fetched_at, period, period_end, n_items, n_stored, rn FROM (SELECT source, fetched_at, period, period_end, "
                        f"n_items, {ns_sql}, row_number() OVER (PARTITION BY source ORDER BY fetched_at DESC) rn FROM {MOPS_LOG} WHERE state = 'OK') "
                        f"WHERE rn <= 2").fetchall():
                    if rn == 1:
                        last[src] = (str(f or ""), p, pe, int(n or 0), int(ns or 0))
                    else:
                        prev_n[src] = int(n or 0)
            if MOPS_TABLE in tabs:
                have = {(a, b): c for a, b, c in con.execute(f"SELECT source, period, count(*) FROM {MOPS_TABLE} GROUP BY 1, 2").fetchall()}
        finally:
            con.close()
    out = {}
    for m in markets:
        todo, why = [], {}
        for st, ind in eps:
            src = _mops_source(m, st, ind)
            f, p, pe, n, ns = last.get(src, ("", None, None, 0, 0))
            if not f:
                r = "沒抓成功過"
            elif f[:10] <= due:
                r = f"上次成功 {f[:10]} 不晚於期限 {due}(期限當天還能申報)"
            elif pe is not None and pe < qe:
                r = f"上次拿到 {p} 舊於 {qe} 那一季"
            elif not n and prev_n.get(src, 0):
                r = f"上次 0 項、前一次有 {prev_n[src]} 項(交易所空回?再抓一次確認)"
            elif ns and have.get((src, p), 0) < ns:
                r = f"資料表裡那一批少了(存 {ns} 項,現 {have.get((src, p), 0)} 項)"
            else:
                continue
            todo.append((st, ind))
            why[r] = why.get(r, 0) + 1
        head = f"該齊 {qe} 那一季(法定期限 {due})"
        out[m] = (todo, f"{head} · 要抓 {len(todo)}/{len(eps)}:" + " · ".join(f"{k} {v}" for k, v in why.items()) if todo
                  else f"已齊:{head},{len(eps)} 個端點都在期限之後抓成功過")
    return out


def mops_revised(dbp, rows: list) -> int:
    """同鍵異值(交易所更正過的數字):本批與庫裡同鍵、值不同的項數。照留舊值(只增不減),只報數。"""
    if not rows or dbp is None or not Path(dbp).exists():
        return 0
    import duckdb
    import pandas as pd
    con = duckdb.connect(str(dbp), read_only=True)
    try:
        if MOPS_TABLE not in {r[0] for r in con.execute("SHOW TABLES").fetchall()}:
            return 0
        con.register("_mr", pd.DataFrame([{k: r[k] for k in MOPS_KEYS + ["value"]} for r in rows]))
        return con.execute(f"SELECT count(*) FROM _mr b JOIN {MOPS_TABLE} t USING (code, period, statement, item) "
                           "WHERE t.value IS DISTINCT FROM b.value").fetchone()[0]
    finally:
        con.close()


def run_mops(db: str | None, dry: bool, markets: list | None = None, force: bool = False, today=None, now=None) -> int:
    """v0103 交易所車道:先查庫定範圍(逐端點)→ 只抓缺的端點(batch_fetch,每個端點抓完就落庫)→ 長表 tw_financial_mops;
    每個端點這一趟的結果記進擷取台帳 tw_financial_mops_log(中斷那一趟不記,下次照抓)。"""
    bad = [m for m in (markets or []) if m not in MOPS_OA]
    if bad:                                                      # 打錯市場名不能變成「都已齊,零請求」
        print(f"[用法] --market 只收 tpex / twse(收到 {','.join(bad)});沒有抓 rc2")
        return 2
    markets = list(dict.fromkeys(markets or ["TPEX", "TWSE"]))  # 同一市場寫兩次只抓一次
    ok, gwhy = gate_open()
    print(f"[三大報表·交易所車道] VDF_ENG082 v{VERSION} · 閘 {gwhy} · 市場 {','.join(markets)}")
    dbp = _resolve_db(db)
    if dbp is None:
        print("[庫缺] vdf_tw_market.duckdb 不在(env VIA_DB_VDF_TW_MARKET / VIA_DATA_HOME / output_hub/mega 皆無)=誠實停 rc2")
        return 2
    try:
        _mops_qends()
    except Exception as exc:                                     # 冊壞了:抓下來也對不到季底,不抓
        print(f"[FAIL] 期別規則冊讀不到季底 {type(exc).__name__}:{str(exc)[:120]} rc1")
        return 1
    plan = mops_plan(dbp, markets, force, today=today)
    for m in markets:
        print(f"  [計畫] {m}:{'抓' if plan[m][0] else '不抓'} · {plan[m][1]}")
    todo = [(m, st, ind) for m in markets for st, ind in plan[m][0]]
    if dry:
        print(f"  [DRY] 只列不抓(不碰網路、不寫庫):要抓 {len(todo)} 個端點")
        return 0
    if not todo:
        print(f"[交易所財報計] 都已齊,零請求(--force 可照抓)· 表 {MOPS_TABLE}")
        return 0
    if not ok:
        print("[FAIL-CLOSED] 同意閘未開(VIA_NET_CONSENT/VIA_SCRAPE_CONSENT)=拒跑;閘由你自己設,我不代設")
        return 2
    stamp = (now or datetime.now()).strftime("%Y-%m-%d %H:%M:%S")
    states, acc = {}, {"added": 0, "revised": 0, "periods": set()}

    def fetch_one(it):
        m, st, ind = it
        url = _mops_url(m, st, ind)
        sk = {}
        try:
            state, data = mops_fetch(url)
            time.sleep(MOPS_SLEEP_S)
            if state != "OK":
                states[it] = (state, data, None, 0, None, None)
                return None                                      # 傳輸敗/被擋=不記 done(下次重試)
            rows = mops_rows(data, m, MOPS_ST[st], ind, url.rsplit("/", 1)[-1], stamp, stats=sk)
        except Exception as exc:                                 # v0104:解析例外也照報、不記完成(下次重試)
            states[it] = ("ERROR", f"{type(exc).__name__}:{str(exc)[:100]}", None, 0, None, None)
            return None
        if not rows and not data:                                # v0104:空列表 ≠ 空業別(空業別回一列佔位列)
            states[it] = ("EMPTY", "回應是空列表(連佔位列都沒有)", 0, 0, None, None)
            return None
        if not rows and sk.get("skipped"):                       # v0104:有值卻一項都解不出(欄名或年季變了?)
            states[it] = ("UNPARSED", f"{len(data)} 列一項都解不出(欄名或年季變了?)", len(data), 0, None, None)
            return None
        seen, uniq = set(), []
        for r in rows:                                           # v0104:同一批同鍵只留第一筆(正典 upsert_rows 照 v0110 語意不替來源去重)
            k = tuple(r[c] for c in MOPS_KEYS)
            if k not in seen:
                seen.add(k)
                uniq.append(r)
        dup, rows = len(rows) - len(uniq), uniq
        pers, ends = {r["period"] for r in rows}, {r["date"] for r in rows}
        states[it] = ("OK", f"{len(data)} 列 → {len(rows)} 項" + (f"(略過 {sk['skipped']} 列認不出)" if sk.get("skipped") else "")
                      + (f"(同一批重複 {dup} 項只留第一筆)" if dup else ""),
                      len(data), len(rows), max(pers) if pers else None, max(ends) if ends else None)
        acc["periods"] |= pers
        return rows

    def persist(tb, rows):
        acc["revised"] += mops_revised(dbp, rows)
        acc["added"] += _LIB.UTILS.upsert_rows(dbp, tb, rows, MOPS_KEYS, schema=MOPS_SCHEMA, counts=True)[0]

    try:
        res = _LIB.UTILS.batch_fetch(todo, fetch_one, persist, done=set(), workers=1, accel=VIA_ACCEL, flush_n=1,
                                     key_of=lambda it: "|".join(it), target_of=lambda it: MOPS_TABLE,
                                     say=lambda s: print(s, flush=True))
    except Exception as exc:
        print(f"[FAIL] 寫庫失敗 {type(exc).__name__}:{str(exc)[:120]}(庫被別的程序占住?等它跑完再跑;只增不減,重跑冪等)")
        return 1
    for m in markets:
        if not plan[m][0]:
            continue
        mine = {it: v for it, v in states.items() if it[0] == m}
        by = {}
        for it, v in mine.items():
            by[v[0]] = by.get(v[0], 0) + 1
        bad = [f"{MOPS_ST[it[1]]}_{it[2]} {v[0]}:{str(v[1])[:40]}" for it, v in sorted(mine.items()) if v[0] != "OK"]
        print(f"  [{m}] 端點 {len(mine)}:" + " · ".join(f"{k} {v}" for k, v in sorted(by.items())) + (f" · 沒拿到 {'; '.join(bad[:3])}" if bad else ""))
    if res["rc"]:
        print(f"[交易所財報計] 中斷 rc={res['rc']}:+{acc['added']:,} 項已落庫;這一趟不記台帳,下次照抓(只增不減,重跑冪等)")
        return res["rc"]
    stored = {}                                                  # v0104:寫入後表裡實存項數(計畫拿它比,少了幾項也認)
    if any(v[0] == "OK" for v in states.values()):
        import duckdb
        con = duckdb.connect(str(dbp), read_only=True)
        try:
            if MOPS_TABLE in {r[0] for r in con.execute("SHOW TABLES").fetchall()}:
                stored = {(a, b): c for a, b, c in con.execute(f"SELECT source, period, count(*) FROM {MOPS_TABLE} GROUP BY 1, 2").fetchall()}
        finally:
            con.close()
    log = [{"market": m, "statement": MOPS_ST[st], "industry": ind, "source": _mops_source(m, st, ind),
            "state": v[0] if v[0] != "OK" or "|".join((m, st, ind)) in res["done"] else "UNSAVED",
            "n_records": v[2], "n_items": v[3], "n_stored": stored.get((_mops_source(m, st, ind), v[4]), 0) if v[0] == "OK" and v[4] else 0,
            "period": v[4], "period_end": v[5], "note": str(v[1])[:200], "fetched_at": stamp}
           for (m, st, ind), v in states.items()]
    try:
        _LIB.UTILS.upsert_rows(dbp, MOPS_LOG, log, MOPS_LOG_KEYS, schema=MOPS_LOG_SCHEMA)
    except Exception as exc:
        print(f"[FAIL] 擷取台帳寫入失敗 {type(exc).__name__}:{str(exc)[:120]}(資料已落庫;下次會重抓這些端點,只增不減)")
        return 1
    after = mops_plan(dbp, markets, False, today=today)          # v0104:抓完用同一套判準看還缺什麼,全齊才算成功
    outcome = {}
    for m in markets:
        left, mine = after[m][0], [v[0] for it, v in states.items() if it[0] == m]
        if not plan[m][0]:
            outcome[m] = "已齊"
        elif not left:
            outcome[m] = "OK"
        elif mine and len(set(mine)) == 1 and mine[0] != "OK":
            outcome[m] = mine[0]
        else:
            outcome[m] = f"PARTIAL 缺 {len(left)}/{len(MOPS_ST) * len(MOPS_IND)}"
        if left:
            print(f"  [仍缺] {m}:{after[m][1]}")
    done_all = all(v in ("OK", "已齊") for v in outcome.values())
    part = not done_all and any(v in ("OK", "已齊") or v.startswith("PARTIAL") for v in outcome.values())
    print(f"[交易所財報計] {'PARTIAL · ' if part else ''}+{acc['added']:,} 項 · 同鍵異值 {acc['revised']}(照留舊值)· "
          f"期別 {','.join(sorted(acc['periods'])) or '—'} · 市場 " + " · ".join(f"{k} {v}" for k, v in outcome.items())
          + f" · 表 {MOPS_TABLE} · rc={0 if done_all else 2}")
    return 0 if done_all else 2                                  # 全齊才 0;還缺(被擋 · 失敗 · 舊一季 · 少了)= PARTIAL/NODATA rc2


def mops_coverage(con) -> list:
    """覆蓋率另立(Z165;不混新鮮度燈):每市場最新一季有損益 / 資產負債的家數 vs 冊上家數;另列各端點最近一次抓的結果(擷取台帳)。"""
    tabs = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
    eps = []
    if MOPS_LOG in tabs:
        by = {}
        for m, st, n in con.execute(f"SELECT market, state, count(*) FROM (SELECT market, state, row_number() OVER (PARTITION BY source "
                                    f"ORDER BY fetched_at DESC) rn FROM {MOPS_LOG}) WHERE rn = 1 GROUP BY 1, 2 ORDER BY 1, 2").fetchall():
            by.setdefault(m, []).append(f"{st} {n}")
        eps = [f"  交易所財報端點(各端點最近一次):{m} " + " · ".join(v) for m, v in by.items()]
    if MOPS_TABLE not in tabs:
        return [f"  交易所財報覆蓋:{MOPS_TABLE} 未建(先 run --mops;閘要你開)"] + eps
    listed = {}
    out = []
    if "tw_listings" in tabs and "market" in {r[0] for r in con.execute("DESCRIBE tw_listings").fetchall()}:
        listed = dict(con.execute("SELECT market, count(DISTINCT code) FROM tw_listings GROUP BY 1").fetchall())
    for m, p, n_is, n_bs, n in con.execute(
            f"SELECT market, period, count(DISTINCT code) FILTER (WHERE statement = 'IS'), count(DISTINCT code) FILTER (WHERE statement = 'BS'), "
            f"count(*) FROM {MOPS_TABLE} t WHERE period = (SELECT max(period) FROM {MOPS_TABLE} x WHERE x.market = t.market) "
            f"GROUP BY 1, 2 ORDER BY 1").fetchall():
        out.append(f"  交易所財報覆蓋(跟新鮮度燈分開):{m} {p} 損益 {n_is} 家 · 資產負債 {n_bs} 家 · 冊上 {listed.get(m, '?')} 家 · {n:,} 項"
                   "(ETF/受益憑證不申報財報,冊上若含它們就不會是 100%)")
    return out + eps


def run(only: list | None, limit: int, years: int, db: str | None, dry: bool) -> int:
    ok, gwhy = gate_open()
    print(f"[三大報表] VDF_ENG082 v{VERSION} · 收容件 {'在' if fetcher() else '缺'} · 閘 {gwhy}")
    dbp = _resolve_db(db)
    if dbp is None:
        print("[庫缺] vdf_tw_market.duckdb 不在(env VIA_DB_VDF_TW_MARKET / VIA_DATA_HOME / output_hub/mega 皆無)=誠實停 rc2")
        return 2
    import duckdb
    con = duckdb.connect(str(dbp))
    try:
        codes = [c for c in (only or []) if c] or listings(con, limit)
        tickers = [norm_ticker(c) for c in codes if norm_ticker(c)]
        print(f"  庫 {dbp} · 目標 {len(tickers)} 檔:{','.join(tickers[:8])}{'…' if len(tickers) > 8 else ''} · 年數 {years}")
        if not tickers:
            print("  [缺料] 無目標(tw_listings 無列且未給 --only)=誠實停 rc2")
            return 2
        if dry:
            print("  [DRY] 只列不抓(不碰網路、不寫庫)")
            return 0
        if not ok:
            print("[FAIL-CLOSED] 同意閘未開(VIA_NET_CONSENT/VIA_SCRAPE_CONSENT)=拒跑;閘由你自己設,我不代設")
            return 2
        cols = columns()
        tot, tags, empty = 0, {}, []
        for i, t in enumerate(tickers, 1):
            rows, tag = _pull(t, years)
            if not rows and t.endswith(".TW"):
                rows2, tag2 = _pull(t[:-3] + ".TWO", years)      # 上櫃再試
                if rows2:
                    rows, tag = rows2, tag2 + "(上櫃 .TWO)"
            if tag.startswith("缺件") or tag.startswith("ABSENT"):
                print(f"  [{tag}]")
                return 2
            tags[tag] = tags.get(tag, 0) + 1
            if rows:
                tot += write_rows(con, rows, cols)
                print(f"  [{i}/{len(tickers)}] {t} +{len(rows)} 列")
            else:
                empty.append(t)
                print(f"  [{i}/{len(tickers)}] {t} 零列({tag[:60]})")
            time.sleep(0.3)
        try:
            n = con.execute(f"SELECT COUNT(*) FROM {TABLE}").fetchone()[0]
        except Exception:
            n = 0                                                # 批688:一列都沒抓到=表根本沒建,不是炸
        if not tot and not n:
            print(f"[三大報表計] {len(tickers)} 檔 · 一列都沒抓到,表 {TABLE} 未建(零列 {len(empty)} · 車道 {tags})=誠實 rc2;"
                  "零列的因由看上面每檔括號(拒收 session→已退原生;仍零列=Yahoo 無此檔或網路被擋)")
            return 2
        pq = OUT / "fin"
        pq.mkdir(parents=True, exist_ok=True)
        pqf = pq / f"{TABLE}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.parquet"
        try:
            con.execute(f"COPY (SELECT * FROM {TABLE}) TO '{pqf.as_posix()}' (FORMAT PARQUET)")
        except Exception as exc:
            pqf = f"parquet 未寫 {type(exc).__name__}"
        mp = mops_probe(tickers[0].split(".")[0])
        print(f"  [MOPS 探路] {mp.get('state')} · {mp.get('why') or ('len ' + str(mp.get('len')))} · 解析=候(VERIFY_PENDING)")
        print(f"[三大報表計] {len(tickers)} 檔 · +{tot} 列 · 零列 {len(empty)} · 表 {TABLE} 共 {n:,} 列 · parquet {pqf} · 車道 {tags}")
        return 0 if tot else 2
    finally:
        con.close()


def status(db: str | None) -> int:
    dbp = _resolve_db(db)
    print(f"[三大報表] VDF_ENG082 v{VERSION} · 收容件 {'在' if fetcher() else '缺'} · 閘 {gate_open()[1]} · 庫 {dbp or '缺'}")
    if dbp is None:
        return 2
    import duckdb
    try:
        con = duckdb.connect(str(dbp), read_only=True)
    except Exception as exc:
        print(f"  庫忙/壞:{str(exc)[:80]}")
        return 2
    try:
        n = con.execute(f"SELECT COUNT(*) FROM {TABLE}").fetchone()[0]
        by = con.execute(f"SELECT Ticker, COUNT(*), MAX(Period) FROM {TABLE} GROUP BY 1 ORDER BY 1 LIMIT 12").fetchall()
        print(f"  {TABLE} {n:,} 列 · " + " · ".join(f"{t} {c}({p})" for t, c, p in by))
    except Exception:
        print(f"  {TABLE} 未建(先 run;閘要你開)")
    try:
        for line in mops_coverage(con):                          # v0103:交易所財報覆蓋另立一段
            print(line)
    finally:
        con.close()
    return 0


def selftest() -> int:
    import contextlib
    import io
    import tempfile
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)
    f = fetcher()
    cols = columns()
    chk("① 收容件掛載(vdf_fetchers_financials_b*;canonical 23 欄 Date…Source)", f is not None and len(cols) == 23 and cols[0] == "Date" and cols[-1] == "Source", f"({len(cols)} 欄)")
    chk("② 代號正規:2330→2330.TW · 2330.TWO 照原 · AAPL 照原 · 空=空", norm_ticker("2330") == "2330.TW" and norm_ticker("2330.two") == "2330.TWO" and norm_ticker("aapl") == "AAPL" and norm_ticker("") == "")
    sv = {k: os.environ.get(k) for k in ("VIA_NET_CONSENT", "VIA_SCRAPE_CONSENT", "VIA_DB_VDF_TW_MARKET", "VIA_DATA_HOME")}
    with tempfile.TemporaryDirectory() as td:
        try:
            import duckdb
            dbp = Path(td) / "t.duckdb"
            con = duckdb.connect(str(dbp)); con.execute("CREATE TABLE tw_listings(code VARCHAR, name VARCHAR)"); con.execute("INSERT INTO tw_listings VALUES ('2330','台積電'),('2317','鴻海')"); con.close()
            os.environ.pop("VIA_NET_CONSENT", None); os.environ.pop("VIA_SCRAPE_CONSENT", None)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = run(None, 5, 5, str(dbp), False)
            chk("③ 同意閘 fail-closed:閘未開 → 印 [FAIL-CLOSED] 同意閘未開 · rc2(匯流排判 GATED,不是壞)", rc == 2 and "[FAIL-CLOSED] 同意閘未開" in buf.getvalue())
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc_d = run(["2330"], 5, 5, str(dbp), True)
            chk("④ --dry 只列不抓不寫(閘未開也能列目標)", rc_d == 0 and "[DRY]" in buf.getvalue() and "2330.TW" in buf.getvalue())
            # ⑤ 端到端(假車道):monkeypatch _pull → 合成列;寫表 + 冪等 + parquet(duckdb COPY)
            g = globals()
            real_pull, real_probe = g["_pull"], g["mops_probe"]
            g["_pull"] = lambda t, y: ([dict(f._new_row(t, "2024-12-31", "annual", "selftest"), Revenue=100.0, Gross_Profit=40.0, Net_Income=10.0, Equity=50.0),
                                        dict(f._new_row(t, "2023-12-31", "annual", "selftest"), Revenue=90.0)], "fake-lane")
            g["mops_probe"] = lambda c: {"state": "SKIP", "why": "selftest 零網路"}
            os.environ["VIA_NET_CONSENT"] = "YES"; os.environ["VIA_SCRAPE_CONSENT"] = "x"
            _out = g["OUT"]; g["OUT"] = Path(td) / "mega"
            try:
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    rc1 = run(["2330", "2317"], 5, 5, str(dbp), False)
                    rc2 = run(["2330", "2317"], 5, 5, str(dbp), False)
                con = duckdb.connect(str(dbp), read_only=True)
                n = con.execute(f"SELECT COUNT(*) FROM {TABLE}").fetchone()[0]
                tk = con.execute(f"SELECT COUNT(DISTINCT Ticker) FROM {TABLE}").fetchone()[0]
                ncol = len(con.execute(f"SELECT * FROM {TABLE} LIMIT 0").description)
                con.close()
                pqs = list((Path(td) / "mega" / "fin").glob("tw_financial_*.parquet"))
                chk("⑤ 端到端(假車道):2 檔 × 2 期 → 4 列、23+1 欄、重跑冪等(同 Ticker DELETE+INSERT 不倍增)、parquet 由 duckdb COPY 落 mega/fin(零 pyarrow)",
                    rc1 == 0 and rc2 == 0 and n == 4 and tk == 2 and ncol == 24 and len(pqs) >= 1, f"(列 {n} · 檔 {tk} · 欄 {ncol} · parquet {len(pqs)})")
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    rc_s = status(str(dbp))
                chk("⑥ status 讀得出表(列數/逐檔最新期)", rc_s == 0 and "tw_financial 4 列" in buf.getvalue() and "2330.TW 2(2024-12-31)" in buf.getvalue(), f"({buf.getvalue().splitlines()[-1][:80]})")
            finally:
                g["_pull"], g["mops_probe"], g["OUT"] = real_pull, real_probe, _out
        except ImportError:
            chk("③④⑤⑥ 端到端(本環境無 duckdb=SKIP 誠實)", True)
        finally:
            for k, v in sv.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑦ 零直呼網路(無 import requests/httpx/yfinance 於模組頂層;yfinance 只在車道內惰性 import;MOPS 走 NetUnified http_text)",
        all(("\nimport " + k) not in src for k in ("requests", "httpx", "yfinance")) and "http_text(" in src and "gate_state()" in src)
    ok, why = gate_open()
    chk("⑧ 閘態讀自 NetUnified gate_state(永不代設;本容器應為關)", isinstance(ok, bool) and bool(why), f"({ok} · {why[:50]})")
    # ⑨ 批688:--only 吃得下 PowerShell 拆開的陣列與逗號兩種寫法
    chk("⑨ --only 兩種寫法皆全收(`--only 2330,2454` 與 PowerShell 拆成 `--only 2330 2454`;遇下一個旗標停)",
        _only_list(["run", "--only", "2330,2454", "--limit", "5"]) == ["2330", "2454"]
        and _only_list(["run", "--only", "2330", "2454", "--years", "5"]) == ["2330", "2454"]
        and _only_list(["run"]) == [],
        f"({_only_list(['run', '--only', '2330', '2454', '--years', '5'])})")
    # ⑩⑪⑫ 批688/689:兩條車道都是子行程——自測用假車道(_lane_pull 換掉)驗主行程的判斷:零列/逾時/拒收 → 原生;都空 → rc2 不炸
    import types as _ty688
    _g688 = globals()
    _real_lane, _real_fetcher = _g688["_lane_pull"], _g688["fetcher"]
    _row = lambda t: {"Date": "", "Ticker": t, "Period": "2024-12-31", "Period_Type": "annual", "Revenue": 1.0, "Source": "yfinance"}
    try:
        _g688["fetcher"] = lambda: _ty688.SimpleNamespace(__file__="fake", _new_row=lambda t, p, pt, s: {"Date": "", "Ticker": t, "Period": p, "Period_Type": pt, "Source": s})
        _g688["_lane_pull"] = lambda t, inject, to: (([], "aegis:Session") if inject else ([_row(t)], "native"))
        rows10, tag10 = _pull("2330.TW", 5)
        chk("⑩ 注入 session 那一趟零列 → 再跑一趟原生(子行程,乾淨 yfinance)→ 有料;tag 講明退了原生",
            len(rows10) == 1 and "原生" in tag10 and "有料" in tag10, f"({len(rows10)} 列 · {tag10[:70]})")
        _g688["_lane_pull"] = lambda t, inject, to: (([], "timeout") if inject else ([_row(t)], "native"))
        rows12, tag12 = _pull("2330.TW", 5)
        chk("⑫ 注入那一趟逾時(子行程被 kill,不留殭屍)→ 原生;tag 講明「逾時→原生 有料」",
            len(rows12) == 1 and "逾時" in tag12 and "有料" in tag12, f"({len(rows12)} 列 · {tag12[:70]})")
        _g688["_lane_pull"] = lambda t, inject, to: ([], "timeout" if inject else "native")
        try:
            import duckdb as _dk11
        except ImportError:
            _dk11 = None
        if _dk11 is None:
            chk("⑪ 兩趟都零列 → 表未建=0 列、誠實 rc2 不 Traceback(本環境無 duckdb=SKIP 誠實)", True)
        else:
            import tempfile as _tf688, io as _io11, contextlib as _cl11
            with _tf688.TemporaryDirectory() as td11:
                dbp11 = Path(td11) / "e.duckdb"
                _c = _dk11.connect(str(dbp11)); _c.execute("CREATE TABLE tw_listings(code VARCHAR, name VARCHAR)"); _c.close()
                _keep = {k: os.environ.get(k) for k in ("VIA_NET_CONSENT", "VIA_SCRAPE_CONSENT")}
                os.environ["VIA_NET_CONSENT"] = "YES"; os.environ["VIA_SCRAPE_CONSENT"] = "x"
                _real_probe = _g688["mops_probe"]; _g688["mops_probe"] = lambda c: {"state": "SKIP", "why": "selftest"}
                try:
                    _b11 = _io11.StringIO()
                    with _cl11.redirect_stdout(_b11):
                        rc11 = run(["2330"], 5, 5, str(dbp11), False)
                finally:
                    _g688["mops_probe"] = _real_probe
                    for k, v in _keep.items():
                        if v is None:
                            os.environ.pop(k, None)
                        else:
                            os.environ[k] = v
                chk("⑪ 兩趟都零列 → 表未建=0 列、誠實 rc2 並講因由,不 Traceback(工作站實錄:CatalogException tw_financial does not exist)",
                    rc11 == 2 and "一列都沒抓到" in _b11.getvalue() and "Traceback" not in _b11.getvalue(), f"(rc={rc11})")
    finally:
        _g688["_lane_pull"], _g688["fetcher"] = _real_lane, _real_fetcher
    # ⑬–㉑ v0103 交易所車道(零網路:假 NetUnified 回合成 JSON;暫存庫;固定 today/now,不隨日期漂)
    _ok13 = True
    try:
        import duckdb as _dk13
        import pandas  # noqa: F401
    except ImportError:
        _ok13 = False
    _ci = [{"Date": "1150924", "Year": "115", "Season": "2", "SecuritiesCompanyCode": "1240", "CompanyName": "茂生農經",
            "營業收入": "1440672.00", "營業毛利（毛損）": "219087.00", "未實現銷貨（損）益": "", "基本每股盈餘（元）": "2.85"},
           {"Date": "1150924", "Year": "115", "Season": "2", "SecuritiesCompanyCode": "1259", "CompanyName": "安心",
            "營業收入": "-1,234.50", "營業毛利（毛損）": "--", "基本每股盈餘（元）": "-0.12"},
           {"Date": "1150924", "Year": "115", "Season": "2", "SecuritiesCompanyCode": "", "CompanyName": "", "營業收入": "9.00"}]
    _bd = [{"Date": "1150924", "年度": "115", "季別": "2", "公司代號": "5864", "CompanyName": "致和證", "收益": "5225386.00"}]
    _bs = [{"出表日期": "1150924", "年度": "115", "季別": "2", "公司代號": "1240", "公司名稱": "茂生農經", "資產總計": "2315123.00",
            " ": "7.00", "待註銷股本股數（單位：股）": "100.00", "每股參考淨值": "33.91"}]
    _ph = [{"Date": "1150924", "Year": "", "Season": "", "SecuritiesCompanyCode": "", "CompanyName": "", "利息淨收益": ""}]
    _bq = [{"Date": "1150924", "Year": "115", "Season": "5", "SecuritiesCompanyCode": "9999", "CompanyName": "壞季", "利息淨收益": "1.00"},
           {"Date": "1150924", "Year": "115", "Season": "2", "SecuritiesCompanyCode": "1333", "CompanyName": "沒數字", "利息淨收益": ""}]
    _skci, _sk13 = {}, {}
    _r13 = mops_rows(_ci, "TPEX", "IS", "ci", "mopsfin_t187ap06_O_ci", "2026-09-24 10:00:00", stats=_skci) \
        + mops_rows(_bd, "TPEX", "IS", "bd", "mopsfin_t187ap06_O_bd", "2026-09-24 10:00:00") \
        + mops_rows(_bs, "TPEX", "BS", "ci", "mopsfin_t187ap07_O_ci", "2026-09-24 10:00:00") \
        + mops_rows(_ph + _bq, "TPEX", "IS", "basi", "mopsfin_t187ap06_O_basi", "2026-09-24 10:00:00", stats=_sk13)
    _by13 = {(r["code"], r["item"]): r for r in _r13}
    _src13 = Path(__file__).read_text(encoding="utf-8").split("def selftest", 1)[0]
    chk("⑬ v0103 交易所彙總財報解析:兩套欄名都認(Year/年度 · Season/季別 · SecuritiesCompanyCode/公司代號 · Date/出表日期);"
        "季底日 2026-06-30 · 期別 2026Q2 · 出表日 2026-09-24 走正典 roc_to_iso;損益 basis=YTD、資產負債 POINT;單位 仟元/元/股;"
        "負數與千分位照認、空值與「--」跳過;佔位列、季別不在 1–4 的列、有年季但代號空的列、欄名空白的欄(有值也一樣)都跳過;本支沒有自寫民國換算;"
        "v0104 佔位列(只有出表日期)不算認不出,其餘解不出的列照數(空 / 認不出判定用)",
        len(_r13) == 9 and _by13[("1240", "營業收入")]["date"] == "2026-06-30" and _by13[("1240", "營業收入")]["period"] == "2026Q2"
        and _by13[("1240", "營業收入")]["report_date"] == "2026-09-24" and _by13[("1240", "營業收入")]["basis"] == "YTD"
        and _by13[("1240", "資產總計")]["basis"] == "POINT" and _by13[("1240", "基本每股盈餘（元）")]["unit"] == "元"
        and _by13[("1240", "每股參考淨值")]["unit"] == "元" and _by13[("1240", "待註銷股本股數（單位：股）")]["unit"] == "股"
        and _by13[("1240", "營業收入")]["unit"] == "仟元" and _by13[("1259", "營業收入")]["value"] == -1234.5
        and ("1259", "營業毛利（毛損）") not in _by13 and ("5864", "收益") in _by13 and _by13[("5864", "收益")]["name"] == "致和證"
        and not any(r["code"] == "" for r in _r13) and ("1911" not in _src13)
        and _skci.get("skipped") == 1 and _sk13.get("skipped") == 2 and _mops_placeholder(_ph[0]) and not _mops_placeholder(_bq[0]),
        f"({len(_r13)} 項 · {sorted({r['period'] for r in _r13})})")
    if not _ok13:
        chk("⑭–㉒ v0103/v0104 交易所車道端到端(本環境無 duckdb/pandas=SKIP 誠實)", True)
    else:
        import types as _ty13
        import datetime as _dt13
        _calls = []
        _page = "<html><body>因為安全性考量，您所執行的頁面無法呈現。FOR SECURITY REASONS, THIS PAGE CAN NOT BE ACCESSED.</body></html>"
        _payload = {"06_O_ci": _ci, "06_O_bd": _bd, "07_O_ci": _bs, "06_O_basi": _ph}

        def _fake_text(url, timeout=30):
            _calls.append(url)
            if "openapi.twse.com.tw" in url:
                return {"state": "OK", "data": _page, "via": "fake"}
            key = url.rsplit("t187ap", 1)[-1]
            return {"state": "OK", "data": json.dumps(_payload.get(key, _ph), ensure_ascii=False), "via": "fake"}
        _fake = _ty13.SimpleNamespace(http_text=_fake_text, gate_state=lambda: {"open": True, "gate1_raw": "YES", "gate2_scrape_token_set": True})
        _g13 = globals()
        _real_net, _real_sleep = _g13["net"], _g13["MOPS_SLEEP_S"]
        _keep13 = {k: os.environ.get(k) for k in ("VIA_NET_CONSENT", "VIA_SCRAPE_CONSENT")}
        _today, _now = _dt13.date(2026, 9, 24), _dt13.datetime(2026, 9, 24, 10, 0, 0)
        try:
            _g13["net"], _g13["MOPS_SLEEP_S"] = (lambda: _fake), 0
            with tempfile.TemporaryDirectory() as td13:
                db13 = Path(td13) / "m.duckdb"
                _c = _dk13.connect(str(db13))
                _c.execute("CREATE TABLE tw_listings(code VARCHAR, name VARCHAR, market VARCHAR)")
                _c.execute("INSERT INTO tw_listings VALUES ('1240','茂生農經','TPEX'),('1259','安心','TPEX'),('5864','致和證','TPEX'),('3718','x','TPEX')")
                _c.close()
                _b = io.StringIO()
                with contextlib.redirect_stdout(_b):
                    rc14 = run_mops(str(db13), False, ["TPEX", "TWSE"], today=_today, now=_now)
                out14, n_calls14 = _b.getvalue(), len(_calls)
                _c = _dk13.connect(str(db13), read_only=True)
                n14 = _c.execute(f"SELECT count(*), count(DISTINCT code), count(DISTINCT market) FROM {MOPS_TABLE}").fetchone()
                ty14 = dict(_c.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{MOPS_TABLE}'").fetchall())
                lg14 = dict(_c.execute(f"SELECT state, count(*) FROM {MOPS_LOG} GROUP BY 1").fetchall())
                lp14 = {(a, b): (c, d) for a, b, c, d in _c.execute(f"SELECT industry, statement, period, n_items FROM {MOPS_LOG} WHERE market = 'TPEX'").fetchall()}
                _c.close()
                chk("⑭ v0103 交易所車道端到端(假 NetUnified):TPEX 12 個端點都回 JSON → 長表 9 項(3 家;佔位列不進);TWSE 12 個回安全頁 → "
                    "BLOCKED 照報、不記完成;每個端點一個請求(24);欄型照宣告(value DOUBLE);v0104 上市還缺 → rc2 標 PARTIAL(不當成功);"
                    "擷取台帳 24 筆(OK 12 · BLOCKED 12;空業別記 OK、期別空)",
                    rc14 == 2 and "PARTIAL" in out14 and n_calls14 == 24 and n14 == (9, 3, 1) and ty14.get("value") == "DOUBLE" and ty14.get("date") == "VARCHAR"
                    and "[TPEX] 端點 12:OK 12" in out14 and "[TWSE] 端點 12:BLOCKED 12" in out14 and "+9 項" in out14
                    and lg14 == {"OK": 12, "BLOCKED": 12} and lp14.get(("ci", "IS")) == ("2026Q2", 5) and lp14.get(("basi", "IS")) == (None, 0),
                    f"(rc {rc14} · 請求 {n_calls14} · 表 {n14} · {out14.strip().splitlines()[-1][:90]})")
                # ⑮ 先查庫:TPEX 已在法定期限(08-14)之後抓齊 → 零請求;TWSE 庫裡沒有 → 照抓;--force 照抓;--dry 零請求
                _calls.clear()
                _b = io.StringIO()
                with contextlib.redirect_stdout(_b):
                    rc15 = run_mops(str(db13), False, ["TPEX"], today=_today, now=_now)
                    rc15d = run_mops(str(db13), True, ["TPEX", "TWSE"], today=_today, now=_now)
                c15 = len(_calls)
                _b2 = io.StringIO()
                with contextlib.redirect_stdout(_b2):
                    rc15p = run_mops(str(db13), False, ["TPEX", "TWSE"], today=_today, now=_now)   # TPEX 已齊 + TWSE 被擋
                c15p = len(_calls) - c15
                p_stale = mops_plan(db13, ["TPEX"], False, today=_dt13.date(2026, 11, 20))        # Q3 已過 11/14 → 要抓
                p_force = mops_plan(db13, ["TPEX"], True, today=_today)
                p_oct = mops_plan(db13, ["TPEX"], False, today=_dt13.date(2026, 10, 1))           # Q3 期限(11/14)還沒到 → 仍判齊
                chk("⑮ v0103 先查庫再抓:TPEX 2026Q2 已在法定期限 08-14 之後抓過 → 不抓、零請求;--dry 只印計畫(TWSE 庫裡沒有 → 抓 12 個)、零請求;"
                    "10/01(下一季期限未到)仍判齊;下一季(11/14)到期之後 → 要抓;--force 照抓;TPEX 已齊 + TWSE 被擋 → v0104 rc2 標 PARTIAL(只請求 TWSE 12 個;上市還缺不當成功);"
                    "--market 兩種寫法(逗號 / PowerShell 拆成兩個 token)都吃",
                    rc15 == 0 and c15 == 0 and "都已齊,零請求" in _b.getvalue() and rc15d == 0 and "要抓 12 個端點" in _b.getvalue()
                    and len(p_stale["TPEX"][0]) == 12 and "不晚於期限 2026-11-14" in p_stale["TPEX"][1] and len(p_force["TPEX"][0]) == 12
                    and p_oct["TPEX"][0] == []
                    and rc15p == 2 and c15p == 12 and "PARTIAL" in _b2.getvalue() and "TPEX 已齊 · TWSE BLOCKED" in _b2.getvalue()
                    and _only_list(["run", "--mops", "--market", "tpex,twse", "--force"], "--market") == ["tpex", "twse"]
                    and _only_list(["run", "--mops", "--market", "tpex", "twse", "--dry"], "--market") == ["tpex", "twse"],
                    f"(請求 {c15} · 計畫 { {k: (len(v[0]), v[1][:48]) for k, v in mops_plan(db13, ['TPEX', 'TWSE'], False, today=_today).items()} })")
                # ⑯ 期限之前抓的 → 要重抓;同鍵異值照留舊值只報數;重跑冪等
                _early = _dt13.datetime(2026, 8, 1, 9, 0, 0)
                db16 = Path(td13) / "early.duckdb"
                _dk13.connect(str(db16)).close()
                _b = io.StringIO()
                with contextlib.redirect_stdout(_b):
                    run_mops(str(db16), False, ["TPEX"], today=_dt13.date(2026, 8, 1), now=_early)
                p_early = mops_plan(db16, ["TPEX"], False, today=_today)
                _ci[0]["營業收入"] = "1440999.00"                     # 交易所更正過的數字
                _b = io.StringIO()
                with contextlib.redirect_stdout(_b):
                    rc16 = run_mops(str(db16), False, ["TPEX"], today=_today, now=_now)
                p16b = mops_plan(db16, ["TPEX"], False, today=_today)                          # 期限後重抓過 → 判齊(台帳取最近一次成功)
                with contextlib.redirect_stdout(io.StringIO()):                              # v0104:--force 重抓已齊的市場 → 抓完用非 force 判準重算 → rc0
                    rc16f = run_mops(str(db16), False, ["TPEX"], force=True, today=_today, now=_dt13.datetime(2026, 9, 24, 10, 30, 0))
                _c = _dk13.connect(str(db16), read_only=True)
                v16 = _c.execute(f"SELECT value FROM {MOPS_TABLE} WHERE code = '1240' AND item = '營業收入'").fetchone()[0]
                n16 = _c.execute(f"SELECT count(*) FROM {MOPS_TABLE}").fetchone()[0]
                _c.close()
                chk("⑯ v0103 在法定期限之前抓的那一季 → 下次照抓(可能還沒申報齊);交易所更正過的數字=同鍵異值 1 項照報、照留舊值;重跑冪等(+0 項);期限後重抓過 → 判齊;v0104 --force 重抓已齊的市場 rc0",
                    len(p_early["TPEX"][0]) == 12 and "不晚於期限 2026-08-14" in p_early["TPEX"][1] and rc16 == 0 and "同鍵異值 1" in _b.getvalue()
                    and "+0 項" in _b.getvalue() and v16 == 1440672.0 and n16 == 9 and p16b["TPEX"][0] == [] and rc16f == 0, f"(值 {v16} · 項 {n16} · {p16b['TPEX'][1][:40]} · force rc {rc16f})")
                # ⑰ 閘未開 → FAIL-CLOSED 零請求;status 印覆蓋(跟新鮮度燈分開)
                _g13["net"] = _real_net
                os.environ.pop("VIA_NET_CONSENT", None)
                os.environ.pop("VIA_SCRAPE_CONSENT", None)
                _calls.clear()
                _c = _dk13.connect(str(db13))                            # 舊一季也在庫裡 → 覆蓋只報最新一季
                _c.execute(f"INSERT INTO {MOPS_TABLE} (date, code, market, statement, item, value, period) "
                           "VALUES ('2026-03-31', '1240', 'TPEX', 'IS', '營業收入', 1.0, '2026Q1')")
                _c.close()
                _b = io.StringIO()
                with contextlib.redirect_stdout(_b):
                    rc17 = run_mops(str(db13), False, ["TWSE"], today=_today, now=_now)
                    rs17 = status(str(db13))
                chk("⑰ v0103 同意閘未開 → [FAIL-CLOSED] rc2、零請求(閘永不代設);status 另印交易所財報覆蓋:TPEX 2026Q2 損益 3 家 · 資產負債 1 家 · 冊上 4 家"
                    "(庫裡還有舊一季 2026Q1 也只報最新一季);各端點最近一次:TPEX OK 12 · TWSE BLOCKED 12",
                    rc17 == 2 and "[FAIL-CLOSED]" in _b.getvalue() and not _calls and rs17 == 0
                    and "TPEX 2026Q2 損益 3 家 · 資產負債 1 家 · 冊上 4 家" in _b.getvalue() and "2026Q1" not in _b.getvalue()
                    and "交易所財報端點(各端點最近一次):TPEX OK 12" in _b.getvalue() and "交易所財報端點(各端點最近一次):TWSE BLOCKED 12" in _b.getvalue(),
                    f"(rc {rc17} · {[l for l in _b.getvalue().splitlines() if '覆蓋' in l][:2]})")
                # ⑱ 市場參數:打錯市場名 → [用法] rc2 零請求;同一市場寫兩次只抓一次;只指定被擋的市場 → rc2 NODATA、不標 PARTIAL
                _g13["net"] = (lambda: _fake)
                _calls.clear()
                _b = io.StringIO()
                with contextlib.redirect_stdout(_b):
                    rc18u = run_mops(str(db13), False, ["TPX"], today=_today, now=_now)
                    rc18d = run_mops(str(db13), True, ["TWSE", "TWSE"], today=_today, now=_now)
                c18u, out18u = len(_calls), _b.getvalue()
                _b = io.StringIO()
                with contextlib.redirect_stdout(_b):
                    rc18t = run_mops(str(db13), False, ["TWSE"], today=_today, now=_now)
                chk("⑱ v0103 市場參數:打錯市場名 → [用法] rc2、零請求(不謊報「都已齊」);同一市場寫兩次只算一次(計畫 12 個端點);"
                    "只指定被擋的市場 → rc2 NODATA、不標 PARTIAL",
                    rc18u == 2 and "[用法]" in out18u and c18u == 0 and "都已齊" not in out18u and rc18d == 0 and "要抓 12 個端點" in out18u
                    and rc18t == 2 and len(_calls) == 12 and "PARTIAL" not in _b.getvalue() and "TWSE BLOCKED" in _b.getvalue(),
                    f"(rc {rc18u}/{rc18d}/{rc18t} · 請求 {c18u}/{len(_calls)})")
                # ⑲ 端點回應態對照(mops_fetch):不是 JSON / 不是列表 → FAIL · DENY · 傳輸敗 · 安全頁 · 列表 · NetUnified 缺
                _resp19 = {"u_txt": {"state": "OK", "data": "abc"}, "u_obj": {"state": "OK", "data": '{"message": "err"}'},
                           "u_deny": {"state": "DENY", "note": "閘未開"}, "u_fail": {"state": "FAIL", "note": "timeout"},
                           "u_page": {"state": "OK", "data": _page.encode("utf-8")}, "u_ok": {"state": "OK", "data": b'[{"a": 1}]'}}
                _g13["net"] = lambda: _ty13.SimpleNamespace(http_text=lambda url, timeout=30: _resp19[url])
                st19 = {k: mops_fetch(k)[0] for k in _resp19}
                _g13["net"] = lambda: None
                st19["absent"] = mops_fetch("u_ok")[0]
                chk("⑲ v0103 端點回應態:不是 JSON / 不是列表 → FAIL(不當成空的 OK)· 閘 DENY → DENY · 傳輸敗 → FAIL · 安全頁(bytes 也認)→ BLOCKED · "
                    "列表(bytes)→ OK · NetUnified 缺 → ABSENT",
                    st19 == {"u_txt": "FAIL", "u_obj": "FAIL", "u_deny": "DENY", "u_fail": "FAIL", "u_page": "BLOCKED", "u_ok": "OK", "absent": "ABSENT"},
                    f"({st19})")
                # ⑳ 逐端點補抓(擷取台帳):一個端點傳輸敗 → 下次只補它;拿到舊一季 → 照抓;資料表那一批被刪 → 照抓;空業別抓成功過=齊
                db20 = Path(td13) / "ep.duckdb"
                _dk13.connect(str(db20)).close()
                _flaky = []
                _payload["07_O_bd"] = [{"出表日期": "1150924", "年度": "115", "季別": "1", "公司代號": "5864", "公司名稱": "致和證", "資產總計": "1.00"}]

                def _fake20(url, timeout=30):
                    if url.endswith("t187ap06_O_fh") and not _flaky:
                        _flaky.append(url)
                        _calls.append(url)
                        return {"state": "FAIL", "note": "timeout", "via": "fake"}
                    return _fake_text(url, timeout)
                _g13["net"] = lambda: _ty13.SimpleNamespace(http_text=_fake20, gate_state=_fake.gate_state)
                _calls.clear()
                _b = io.StringIO()
                with contextlib.redirect_stdout(_b):
                    rc20a = run_mops(str(db20), False, ["TPEX"], today=_today, now=_dt13.datetime(2026, 9, 24, 11, 0, 0))
                c20a, out20a = len(_calls), _b.getvalue()
                _c = _dk13.connect(str(db20))
                _c.execute(f"DELETE FROM {MOPS_TABLE} WHERE source = 'mopsfin_t187ap06_O_ci'")
                _c.close()
                p20 = mops_plan(db20, ["TPEX"], False, today=_today)
                _b = io.StringIO()
                with contextlib.redirect_stdout(_b):
                    rc20b = run_mops(str(db20), False, ["TPEX"], today=_today, now=_dt13.datetime(2026, 9, 24, 12, 0, 0))
                c20b = len(_calls) - c20a
                p20c = mops_plan(db20, ["TPEX"], False, today=_today)
                _c = _dk13.connect(str(db20), read_only=True)
                n20ci = _c.execute(f"SELECT count(*) FROM {MOPS_TABLE} WHERE source = 'mopsfin_t187ap06_O_ci'").fetchone()[0]
                _c.close()
                _payload.pop("07_O_bd", None)
                chk("⑳ v0103 逐端點補抓(擷取台帳):一個端點傳輸敗 → 下次只補它(不因同市場別的端點到位就整個市場判齊);拿到舊一季(2026Q1)→ 照抓;"
                    "資料表那一批被刪 → 照抓;空業別抓成功過=齊、不重抓(第二趟只 3 個請求);v0104 還缺(舊一季)就 rc2",
                    rc20a == 2 and c20a == 12 and "FAIL 1" in out20a and len(p20["TPEX"][0]) == 3 and "沒抓成功過 1" in p20["TPEX"][1]
                    and "上次拿到 2026Q1 舊於 2026-06-30 那一季 1" in p20["TPEX"][1] and "資料表裡那一批少了(存 5 項,現 0 項) 1" in p20["TPEX"][1]
                    and rc20b == 2 and c20b == 3 and p20c["TPEX"][0] == [("07", "bd")] and n20ci == 5,
                    f"(請求 {c20a}/{c20b} · 計畫 {p20['TPEX'][0]} → {p20c['TPEX'][0]} · ci {n20ci})")
                # ㉑ 中斷(Ctrl+C)那一趟:已抓的照落庫、台帳不記(下次照抓);台帳寫不進去 → rc1(資料已落庫,不裝綠)
                db21 = Path(td13) / "intr.duckdb"
                _dk13.connect(str(db21)).close()

                def _fake21(url, timeout=30):
                    if url.endswith("t187ap06_O_bd"):
                        raise KeyboardInterrupt
                    return _fake_text(url, timeout)
                _g13["net"] = lambda: _ty13.SimpleNamespace(http_text=_fake21, gate_state=_fake.gate_state)
                _b = io.StringIO()
                with contextlib.redirect_stdout(_b):
                    rc21a = run_mops(str(db21), False, ["TPEX"], today=_today, now=_dt13.datetime(2026, 9, 24, 13, 0, 0))
                _c = _dk13.connect(str(db21), read_only=True)
                t21 = {r[0] for r in _c.execute("SHOW TABLES").fetchall()}
                n21 = _c.execute(f"SELECT count(*) FROM {MOPS_TABLE}").fetchone()[0] if MOPS_TABLE in t21 else -1
                _c.close()
                db21b = Path(td13) / "logview.duckdb"
                _c = _dk13.connect(str(db21b))
                _c.execute(f"CREATE VIEW {MOPS_LOG} AS SELECT * FROM (VALUES (NULL::VARCHAR, NULL::VARCHAR, NULL::VARCHAR, NULL::VARCHAR, "
                           "NULL::VARCHAR, NULL::BIGINT, NULL::BIGINT, NULL::BIGINT, NULL::VARCHAR, NULL::VARCHAR, NULL::VARCHAR, NULL::VARCHAR)) "
                           "v(market, statement, industry, source, state, n_records, n_items, n_stored, period, period_end, note, fetched_at) WHERE false")
                _c.close()
                _g13["net"] = lambda: _fake
                _b2 = io.StringIO()
                with contextlib.redirect_stdout(_b2):
                    rc21b = run_mops(str(db21b), False, ["TPEX"], today=_today, now=_dt13.datetime(2026, 9, 24, 14, 0, 0))
                _c = _dk13.connect(str(db21b), read_only=True)
                n21b = _c.execute(f"SELECT count(*) FROM {MOPS_TABLE}").fetchone()[0]
                _c.close()
                _real_rules = _LIB.UTILS.load_period_rules
                _broken = dict(_real_rules(), cadences={})                                  # 期別規則冊少了季表規則
                _calls.clear()
                _b3 = io.StringIO()
                try:
                    _LIB.UTILS.load_period_rules = lambda path=None: _broken
                    with contextlib.redirect_stdout(_b3):
                        rc21c = run_mops(str(db21b), False, ["TPEX"], today=_today, now=_dt13.datetime(2026, 9, 24, 15, 0, 0))
                finally:
                    _LIB.UTILS.load_period_rules = _real_rules
                chk("㉑ v0103 中斷(Ctrl+C)那一趟:已抓的照落庫(一般業損益 5 項)、台帳不記(下次照抓)、rc130;台帳寫不進去 → [FAIL] rc1"
                    "(資料照落庫 9 項,不裝綠);期別規則冊少了季表規則 → rc1 零請求(抓下來也對不到季底)",
                    rc21a == 130 and MOPS_LOG not in t21 and n21 == 5 and rc21b == 1 and "擷取台帳寫入失敗" in _b2.getvalue() and n21b == 9
                    and rc21c == 1 and not _calls and "期別規則冊讀不到季底" in _b3.getvalue(),
                    f"(rc {rc21a}/{rc21b}/{rc21c} · 表 {sorted(t21)} · 項 {n21}/{n21b} · 冊壞請求 {len(_calls)})")
                # ㉒ v0104 Codex 審四條(PR #116):空 / 認不出不算抓成功 · 一個端點成功≠市場到位 · 那一批少了幾項也認 · 期限當天抓的隔天照抓
                db22a = Path(td13) / "one_ok.duckdb"                                          # (a) 只有一般業損益成功,其餘逾時 / 例外
                _dk13.connect(str(db22a)).close()

                def _fake22a(url, timeout=30):
                    if url.endswith("t187ap06_O_ci"):
                        return _fake_text(url, timeout)
                    if url.endswith("t187ap07_O_fh"):
                        raise RuntimeError("parser boom")
                    return {"state": "FAIL", "note": "timeout", "via": "fake"}
                _g13["net"] = lambda: _ty13.SimpleNamespace(http_text=_fake22a, gate_state=_fake.gate_state)
                _b = io.StringIO()
                with contextlib.redirect_stdout(_b):
                    rc22a = run_mops(str(db22a), False, ["TPEX"], today=_today, now=_dt13.datetime(2026, 9, 24, 16, 0, 0))
                out22a = _b.getvalue()
                _g13["net"] = lambda: _fake                                                    # (b) 空列表 / 欄名變了
                db22b = Path(td13) / "empty.duckdb"
                _dk13.connect(str(db22b)).close()
                _payload["07_O_ins"] = []
                _payload["07_O_mim"] = [{"Date": "1150924", "CoYear": "115", "CoSeason": "2", "CoCode": "1240", "資產總計": "5.00"}]
                _payload["06_O_bd"] = _bd + _bd                                                # (e) 同一批重複的列:只留一筆
                _payload["07_O_fh"] = _bs                                                      # (e) 別的端點先寫過的同鍵:實存 0 項,不當成少了
                _b = io.StringIO()
                with contextlib.redirect_stdout(_b):
                    rc22b = run_mops(str(db22b), False, ["TPEX"], today=_today, now=_dt13.datetime(2026, 9, 24, 16, 0, 0))
                out22b = _b.getvalue()
                p22b = mops_plan(db22b, ["TPEX"], False, today=_today)
                _c = _dk13.connect(str(db22b), read_only=True)
                dup22 = _c.execute(f"SELECT count(*) FROM (SELECT code, period, statement, item FROM {MOPS_TABLE} GROUP BY ALL HAVING count(*) > 1)").fetchone()[0]
                note22 = _c.execute(f"SELECT note, n_items, n_stored FROM {MOPS_LOG} WHERE source = 'mopsfin_t187ap06_O_bd'").fetchone()
                fh22 = _c.execute(f"SELECT n_items, n_stored FROM {MOPS_LOG} WHERE source = 'mopsfin_t187ap07_O_fh'").fetchone()
                _c.close()
                _payload.pop("07_O_fh", None)
                _payload.pop("07_O_ins", None)
                _payload.pop("07_O_mim", None)
                _payload["06_O_bd"] = _bd
                _c = _dk13.connect(str(db22b))                                                 # (c) 那一批少了 2 項(不是全刪)
                _c.execute(f"DELETE FROM {MOPS_TABLE} WHERE source = 'mopsfin_t187ap06_O_ci' AND code = '1259'")
                _c.close()
                p22c = mops_plan(db22b, ["TPEX"], False, today=_today)
                db22d = Path(td13) / "dueday.duckdb"                                           # (d) 期限當天(8/14)抓的
                _dk13.connect(str(db22d)).close()
                with contextlib.redirect_stdout(io.StringIO()):
                    run_mops(str(db22d), False, ["TPEX"], today=_dt13.date(2026, 8, 14), now=_dt13.datetime(2026, 8, 14, 9, 0, 0))
                p22d0 = mops_plan(db22d, ["TPEX"], False, today=_dt13.date(2026, 8, 14))
                p22d1 = mops_plan(db22d, ["TPEX"], False, today=_dt13.date(2026, 8, 15))
                db22f = Path(td13) / "blank.duckdb"                                            # (f) 平常有資料的端點只回佔位列
                _dk13.connect(str(db22f)).close()
                with contextlib.redirect_stdout(io.StringIO()):
                    run_mops(str(db22f), False, ["TPEX"], today=_today, now=_dt13.datetime(2026, 9, 24, 16, 0, 0))
                    _payload["06_O_ci"] = _ph
                    run_mops(str(db22f), False, ["TPEX"], force=True, today=_today, now=_dt13.datetime(2026, 9, 24, 17, 0, 0))
                p22f1 = mops_plan(db22f, ["TPEX"], False, today=_today)
                with contextlib.redirect_stdout(io.StringIO()):
                    rc22f = run_mops(str(db22f), False, ["TPEX"], today=_today, now=_dt13.datetime(2026, 9, 24, 18, 0, 0))
                p22f2 = mops_plan(db22f, ["TPEX"], False, today=_today)
                _payload["06_O_ci"] = _ci
                db22g = Path(td13) / "oldlog.duckdb"                                           # (g) v0103 建的台帳(沒有 n_stored 欄)
                _c = _dk13.connect(str(db22g))
                _c.execute(f"CREATE TABLE {MOPS_LOG} (market VARCHAR, statement VARCHAR, industry VARCHAR, source VARCHAR, state VARCHAR, "
                           "n_records BIGINT, n_items BIGINT, period VARCHAR, period_end VARCHAR, note VARCHAR, fetched_at VARCHAR)")
                _c.close()
                p22g = mops_plan(db22g, ["TPEX"], False, today=_today)
                with contextlib.redirect_stdout(io.StringIO()):
                    rc22g = run_mops(str(db22g), False, ["TPEX"], today=_today, now=_dt13.datetime(2026, 9, 24, 19, 0, 0))
                _c = _dk13.connect(str(db22g), read_only=True)
                cols22g = {r[0] for r in _c.execute(f"DESCRIBE {MOPS_LOG}").fetchall()}
                _c.close()
                p22g2 = mops_plan(db22g, ["TPEX"], False, today=_today)
                chk("㉒ v0104 Codex 審四條:① 空列表 → EMPTY、欄名變了 → UNPARSED、解析例外 → ERROR,都不算抓成功、下次照抓(佔位列照舊算空業別);"
                    "② 一般業損益成功、其餘逾時 → PARTIAL 缺 11/12、rc2(不再當成功);③ 那一批少了 2 項(不是全刪)→ 只補那個端點;"
                    "同一批重複的列只留一筆、表裡零重複鍵;別的端點先寫過的同鍵(實存 0 項)不當成少了;④ 期限當天抓的:當天判齊(該齊的還是上一季)、隔天照抓;"
                    "平常有資料的端點只回佔位列 → 再抓一次確認,連兩次 0 項才算空(rc0);v0103 建的舊台帳(沒有 n_stored 欄)照讀照寫、正典補欄",
                    rc22a == 2 and "PARTIAL 缺 11/12" in out22a and "[仍缺] TPEX" in out22a and "ERROR 1" in out22a
                    and rc22b == 2 and "EMPTY 1" in out22b and "UNPARSED 1" in out22b and "同一批重複 1 項只留第一筆" in str(note22[0]) and note22[1:] == (1, 1) and dup22 == 0 and fh22 == (3, 0)
                    and sorted(p22b["TPEX"][0]) == [("07", "ins"), ("07", "mim")] and "沒抓成功過 2" in p22b["TPEX"][1]
                    and p22c["TPEX"][0] == [("06", "ci"), ("07", "ins"), ("07", "mim")] and "資料表裡那一批少了(存 5 項,現 3 項) 1" in p22c["TPEX"][1]
                    and p22d0["TPEX"][0] == [] and len(p22d1["TPEX"][0]) == 12 and "不晚於期限 2026-08-14" in p22d1["TPEX"][1]
                    and p22f1["TPEX"][0] == [("06", "ci")] and "上次 0 項、前一次有 5 項" in p22f1["TPEX"][1] and rc22f == 0 and p22f2["TPEX"][0] == []
                    and len(p22g["TPEX"][0]) == 12 and rc22g == 0 and "n_stored" in cols22g and p22g2["TPEX"][0] == [],
                    f"(rc {rc22a}/{rc22b} · 計畫 {p22b['TPEX'][0]} → {p22c['TPEX'][0]} · 期限日 {len(p22d0['TPEX'][0])}/{len(p22d1['TPEX'][0])})")
        finally:
            _g13["net"], _g13["MOPS_SLEEP_S"] = _real_net, _real_sleep
            _ci[0]["營業收入"] = "1440672.00"
            for k, v in _keep13.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
    print(f"  [計] 二十二檢 OK {22 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def _only_list(args: list, flag: str = "--only") -> list:
    """批688:`--only 2330,2454` 在 PowerShell 會被拆成 `--only 2330 2454`(逗號=陣列);
    把 --only 後面連續的非旗標 token 全收,再各自以逗號拆。v0103:旗標可換(`--market tpex,twse` 同理;預設 --only)。"""
    if flag not in args:
        return []
    out = []
    for tok in args[args.index(flag) + 1:]:
        if str(tok).startswith("--"):
            break
        out += [x.strip() for x in str(tok).split(",") if x.strip()]
    return out


def _argval(args, flag, default=None):
    if flag in args:
        i = args.index(flag) + 1
        if i < len(args) and not args[i].startswith("--"):
            return args[i]
    return default


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print(f"=== 三大報表擷取引擎(VDF_ENG082 v{VERSION})· 二十二檢自測(零網路;暫存庫)===")
        return selftest()
    db = _argval(a, "--db")
    if a and (a[0] == "mops" or (a[0] == "run" and "--mops" in a)):   # v0103 交易所車道(短令 via-finstat run --mops)
        mk = [x.upper() for x in _only_list(a, "--market")]         # PowerShell 把 tpex,twse 拆成兩個 token 也吃
        return run_mops(db, "--dry" in a, mk or None, force="--force" in a)
    if a and a[0] == "run":
        only = _only_list(a)                                     # 批688:PowerShell 陣列拆參也吃得下
        return run(only or None, int(_argval(a, "--limit", 5)), int(_argval(a, "--years", 5)), db, "--dry" in a)
    if a and a[0] == "status":
        return status(db)
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
