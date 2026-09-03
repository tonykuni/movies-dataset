#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL095_DeckServer v0120 — 指揮台本地執行橋(批208;批304 Codex 安全模型;批333 收官整併;批334 +四任務;批335 +一鍵完工;批339 收件目的地冊)
====================================================================
操作員令:「指令不要複製貼上,按下去就自動在 PowerShell 進入執行;
執行狀況用矩陣報告顯示紅黃綠燈+問題解決方案」。
機制(瀏覽器沙盒正解=本機橋):
  127.0.0.1:8765 HTTP 橋(僅綁本機;白名單任務冊制——不接受任意
  指令=安全鐵則);同源指揮台頁→POST /run + CSRF→本橋 Popen
  執行(獨立行程;log 逐任務落盤)→頁面輪詢 /status→RYG 矩陣
  即時亮燈+log 尾+解方建議(SOLUTIONS 冊 pattern 對映)。
端點:GET /(MasterControl)/master/ping/status/唯讀分析；POST /run/
  intake/stock_fetch/vap_kline/vap_check/vap_flows。所有副作用端點均要求
  同源 Origin、Sec-Fetch-Site 與當次橋接器隨機權杖。
啟動:VIA.ps1 自動帶起(或 python 本檔 serve);Ctrl+C 停=任務
行程不受影響(獨立)。
v0101→v0102(9hh5to 會話「create real ui」令):+依賴治理任務八條
(deps_scan/deps_mirror/rebuild_scan/rebuild_full/lessons/ocr_probe/
ocr_plan/selftest_fast;net 任務沿用同意環境變數機制)+GET /govdeck
治理指揮頁(VIA_UI_GovDeck;按鈕真跑+RYG 即時燈+解方)。
v0102→v0103(9hh5to「不卡斷 20個加速器 動態進度」令):
①不卡斷=Popen stdin=DEVNULL(子引擎討 stdin 永不懸吊)+/status 尾窗
  定量讀(64KB 界讀,巨 log 不拖橋);②20加速器=ACCEL-BRIDGE 橋可視
  (/ping 曝 accel 在位/缺席;graceful 缺席零影響);③動態進度=
  /status 逐任務 elapsed/beat(log 心跳秒)/kb+PROG 規則冊 pct/done
  (無規則=誠實不假估,不定條)。
v0103→v0104(9hh5to「中央治理台 Mega-Prompt」令):+govcon 任務
(CGC_MDL106 六管線治理台;PROG 七段進度)+GET /govmatrix 矩陣報告
路由(GOVMATRIX 尾版=鐵律)。
v0104→v0105(9hh5to「手機代測 VAP 三分析」令):+VAP 分析端點四條
(/vap_revenue 月營收、/vap_groups 族群、/vap_etflist ETF 冊、
/vap_etf?ids= 個別/組合持股加總;VAP_ENG013 尾版 in-process 唯讀)
+GET /vapdeck 分析台頁(VIA_UI_VapDeck 尾版)。
v0105→v0106(9hh5to「共識取得+核對+K線量圖」令):+/vap_kline?code=
(K線三道:庫→TWSE 官方→降級;net 道自帶雙同意閘)+/vap_check?codes=
(共識庫內×鉅亨現值核對)。
v0106→v0107(9hh5to「量值切換+法人+資金流」令):+/vap_flows?code=
&days=(三大法人 T86 逐日+當沖統計;net 雙同意閘)。
v0107→v0108(9hh5to「三語轉碼」令):+uispec 任務(MDL107 UI 元件
三語轉碼管理器;PROG 五段進度)。
v0108→v0109(9hh5to「收官一次解決」令):+etf_fetch(ENG051 主動式
ETF 持股抓取;net 雙同意閘=補『操作簡單』唯一斷點)+chat2doc(MDL108
對話→文章/程式;PROG 四段)。
v0109→v0110(批264 操作員令「active etf analysis / taiwan stock
revenue analysis (with consensus data)」):+etf_analysis(ENG068 主動
ETF×共識加權 upside)+revenue_consensus(ENG069 月營收×共識四象限)
——28 任務,雙零網路(全讀在庫存證)。
v0110→v0111(批283):+nlp(VRN_ENG078 NLP OneEngine 收容橋;
零網路離線正道)——29 任務。
v0111→v0112(批297 稽核實錘):+unified_register(MDL113 統一編號
冊)+cmdcenter(MDL114 AIO 健康圖)=31 任務;①b 齊備清單補
etf_enrich(專屬存在檢)。
v0112→v0113(批301 操作員令「輸入參數最少化+WINDOW I/O 拖曳式+
下拉選單」;六維稽核雙實錘):
  ①POST /intake 真收落盤——拖曳收件從誠實 v1(只列名)升真收 v2:
    JSON {name,b64}(或 text/plain 簡單請求免 preflight)→basename
    淨檔名→50MB 上限→hash 定生死(同名同 hash=SKIP_IDENTICAL;
    同名異 hash=另存 _sha8 讓位不覆寫)→落 Downloads(工作站=
    via-intake 既有收容流直接接手)/無 Downloads=VIA_Reports/
    deck_intake(雲端誠實後備);回 {ok,saved,sha256,skip}
  ②+std_dashboard(VAP_ENG014 標準儀表板;零參數一鍵)=32 任務
    ——四系統自此各有深控一鍵任務(VAP 補位)
v0113→v0114(批304 總控台安全收旂):
  ①取消 wildcard CORS，不允許外部網站讀取本機狀態或紀錄。
  ②/run 由 GET 改為 JSON POST，與 /intake 一律要求同源 Origin、
    Sec-Fetch-Site 與每次啟動隨機 CSRF 權杖。
  ③/ 與 /master 由本橋注入當次權杖後供應 MasterControl；
    file:// 頁只作離線檢視，不能啟動工作或收件。
  ④封鎖 stock_fetch/vap_kline/vap_check/vap_flows 等有副作用 GET，
    避免 drive-by 網頁擅自促發網路或資料擷取。
v0114→v0115(批333 操作員令「用此檔案為 U/I 自動連結」=採納 Codex 線總控台頁+
安全模型;底=intake b305 Codex v0114 原件,整併雲端線 v0114 讀道):
  ①GET /api/<subject>→CGC_MDL119 SystemAPI 尾版(六主體聚合;唯讀)
  ②GET /system→VIA_UI_System 尾版(注入權杖+同源 shim=K線快查自動 POST)
  ③GET /probe→零資訊探針(CORP cross-origin;file:// 頁 no-cors 探在線→導同源)
  ④GET /VIA_UI_*.html→ui_support 同源靜態頁(唯讀;連結網在樞紐下自動同源=
    file:// 頁的相對連結於 /master 皆可達;路徑白名單正則+夾內守衛)
  任務冊 32 不變;副作用一律同源 CSRF POST(Codex 律);零 CORS
v0115→v0116(批334 操作員令「輸入介面導入/矩陣/功能鍵高自動化」):任務冊 32→36
  +system_ui(MDL120 系統總台再生)+group_class(ENG070 run)+group_backtest
  (ENG071 run)+story_rotation(ENG072 run)=系統總台功能鍵/自動鏈之白名單靶;
  全為本機零網路;安全模型不變。
v0116→v0117(批335 操作員令「完成一切未完工作自動化」):任務冊 36→37
  +complete_all(CGC_MDL121 run=完工鏈 16 步依序 subprocess;net=雙同意閘;PROG
  步數進度);閘(批212/P08/P09/P18)零自動解除。
v0117→v0118(批339 操作員令「繼續前後端整合」;MDL116 v0108 殼輸入面板對接):
  ①POST /intake 增可選欄 dest(收件目的地;固定冊二值零路徑注入):
    "downloads"(預設=既有行為零變)|"vrn_incoming"(→VIA/functional
    modules/VRN/input/incoming;殼 VRN 拖曳矩陣直落 VRN 收件夾;
    hash 去重/排他發布/50MB 上限/淨檔名 全沿用 _intake_save)
    未知 dest=400 誠實拒;缺 dest=既有 Downloads 落點
  ②/ping 回 v0118;自測 +㉑(dest 冊:合法二值放行·非法拒·根目錄真解析)
v0118→v0119(批342 六流程·Stream1 代碼層):_json/_serve 寫回吞 ConnectionAbortedError
  (WinError 10053=瀏覽器先斷線;原僅吞 BrokenPipe/ConnectionReset,10053 每次關分頁刷
  整段 traceback);零行為變更(僅日誌噪音);自測 +㉒
v0119→v0120(批347 全鏈除錯):⑳ 主體數改讀 MDL119 自報(≥6 且=其 subjects 冊長度),
  不再硬碼 6(MDL119 v0102 增 completion 後為 7;硬碼=陳舊斷言,非系統缺陷)
用法:python3 CGC_MDL095_DeckServer_v0120.py serve | --selftest
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_support = str(_sa_p / "supportive modules")
            if _sa_support not in _sa_sys.path:
                _sa_sys.path.insert(0, _sa_support)
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

# ===== [VIA:NET-BRIDGE:NOTE] 本引擎 urllib.parse 僅作 URL 剖析(零網路);
# 127.0.0.1 本機服務零外呼;任務之網路=各引擎自帶 SUP_MDL740 統包正主道。=====
import base64
import errno
import hashlib
import html
import hmac
import http.client
import json
import os
import re
import secrets
import subprocess
import sys
import tempfile
import threading
import time
import unicodedata
from contextlib import contextmanager
from datetime import date, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
UI = VIA / "supportive modules" / "ui_support" / "VIA_UI_CommandDeck_v0100.html"
MASTER_UI = VIA / "supportive modules" / "ui_support" / "VIA_UI_MasterControl_v0100.html"
UI_ROOT = MASTER_UI.parent
LOGDIR = VIA / "VIA_Reports" / "deck_runs"
PORT = 8765
TRUSTED_ORIGIN = f"http://127.0.0.1:{PORT}"
CSRF_TOKEN = secrets.token_urlsafe(32)
GLOBAL_CATEGORIES = frozenset({
    "idx", "etf", "us_jp", "fin_reports", "oil", "fx", "cmdty",
    "crypto", "us_macro", "fed", "us_fiscal_rates",
})
MUTATION_PATHS = frozenset({
    "/run", "/intake", "/stock_fetch", "/vap_kline", "/vap_check",
    "/vap_flows",
})
BLOCKED_MUTATION_GETS = MUTATION_PATHS

def _newest(dirp: Path, pat: str) -> Path | None:
    hits = sorted(dirp.glob(pat))
    return hits[-1] if hits else None


def _eng(sub: str, pat: str) -> str:
    p = _newest(VIA / sub, pat)
    return str(p) if p else ""


# 白名單任務冊(單一 SSOT;py 直呼=跨平台;boot=ps1/sh 依平台)
def task_registry() -> dict:
    is_nt = os.name == "nt"
    boot = (VIA / "supportive modules" / "registry" /
            ("via_boot_update.ps1" if is_nt else "via_boot_update.sh"))
    T = {
        "boot": {"zh": "全自動日更(boot 全鏈)",
                 "argv": (["powershell", "-NoProfile", "-ExecutionPolicy",
                           "Bypass", "-File", str(boot)] if is_nt
                          else ["bash", str(boot)]), "net": True},
        "backfill": {"zh": "歷史回補 2022~(續跑;2020/21 終止批212)",
                     "argv": [sys.executable,
                              _eng("functional modules/VDF/engine",
                                   "VDF_ENG064_HistoryBackfill_v*.py"), "run"],
                     "net": True, "range": True},
        "consensus": {"zh": "鉅亨 FactSet 共識",
                      "argv": [sys.executable,
                               _eng("functional modules/VRN",
                                    "VRN_ENG071_CnyesFusion_v*.py"), "run"],
                      "net": True, "codes": True},
        "revenue": {"zh": "月營收全市場(MOPS)",
                    "argv": [sys.executable,
                             _eng("functional modules/VDF/engine",
                                  "VDF_ENG063_MonthlyRevenue_v*.py"), "run"],
                    "net": True},
        "revenue_groups": {"zh": "族群月營收榜",
                           "argv": [sys.executable,
                                    _eng("functional modules/VDF/engine",
                                         "VDF_ENG063_MonthlyRevenue_v*.py"),
                                    "--groups"], "net": False},
        "global": {"zh": "全球宇宙擷取(11 類;批226)",
                   "argv": [sys.executable,
                            _eng("functional modules/VDF/engine",
                                 "VDF_ENG066_GlobalUniverse_v*.py"), "run"],
                   "net": True, "range": True, "cats": True},
        "firstpage": {"zh": "報告首頁文字擷取(批235)",
                      "argv": [sys.executable,
                               _eng("functional modules/VRN",
                                    "VRN_ENG072_FirstPageText_v*.py"), "run"],
                      "net": False},
        "structdb": {"zh": "報告結構化入庫(批237)",
                     "argv": [sys.executable,
                              _eng("functional modules/VRN",
                                   "VRN_ENG073_ReportStructuredDB_v*.py"), "run"],
                     "net": False},
        "finpages": {"zh": "財報頁表格擷取(批241)",
                     "argv": [sys.executable,
                              _eng("functional modules/VRN",
                                   "VRN_ENG074_FinancialPages_v*.py"), "run"],
                     "net": False},
        "etf_enrich": {"zh": "ETF 持股×共識增益(批243;ENG067)",
                       "argv": [sys.executable,
                                _eng("functional modules/VDF/engine",
                                     "VDF_ENG067_ConsensusEnrichment_v*.py"),
                                "run"], "net": False},
        "etf_analysis": {"zh": "主動 ETF×共識分析(批264;ENG068)",
                         "argv": [sys.executable,
                                  _eng("functional modules/VDF/engine",
                                       "VDF_ENG068_ETFConsensusAnalysis_v*.py"),
                                  "run"], "net": False},
        "unified_register": {"zh": "統一編號冊刷新(批287;MDL113)",
                             "argv": [sys.executable,
                                      _eng("supportive modules/registry",
                                           "CGC_MDL113_UnifiedRegistry_v*.py")],
                             "net": False},
        "cmdcenter": {"zh": "AIO 健康圖刷新(批288;MDL114)",
                      "argv": [sys.executable,
                               _eng("supportive modules/registry",
                                    "CGC_MDL114_CommandCenterBridge_v*.py"),
                               "run"], "net": False},
        "nlp": {"zh": "NLP OneEngine 橋(批283;ENG078)",
                "argv": [sys.executable,
                         _eng("functional modules/VRN",
                              "VRN_ENG078_NLPOneBridge_v*.py"), "run"],
                "net": False},
        "revenue_consensus": {"zh": "月營收×共識分析(批264;ENG069)",
                              "argv": [sys.executable,
                                       _eng("functional modules/VDF/engine",
                                            "VDF_ENG069_RevenueConsensus"
                                            "Analysis_v*.py"),
                                       "run"], "net": False},
        "mdconvert": {"zh": "文件→Markdown(批249)",
                      "argv": [sys.executable,
                               _eng("functional modules/VRN",
                                    "VRN_ENG075_DocToMarkdown_v*.py"), "run"],
                      "net": False},
        "regression": {"zh": "抽取鏈迴歸閘(批251)",
                       "argv": [sys.executable,
                                _eng("functional modules/VRN",
                                     "VRN_ENG076_RegressionGate_v*.py"),
                                "run"], "net": False},
        "vofie": {"zh": "VOFIE 全格式重構(批256)",
                  "argv": [sys.executable,
                           _eng("functional modules/VRN",
                                "VRN_ENG077_OmniFormatBridge_v*.py"),
                           "probe"], "net": False},
        "deps_scan": {"zh": "依賴全景掃描(via-deps)",
                      "argv": [sys.executable,
                               _eng("supportive modules/registry",
                                    "CGC_MDL046_DepSuper_v0*.py")], "net": False},
        "deps_mirror": {"zh": "三鏡像測速",
                        "argv": [sys.executable,
                                 _eng("supportive modules/registry",
                                      "CGC_MDL046_DepSuper_v0*.py"),
                                 "--mirror-test"], "net": True},
        "rebuild_scan": {"zh": "重建計畫快巡(--offline)",
                         "argv": [sys.executable,
                                  _eng("supportive modules/registry",
                                       "CGC_MDL050_EnvRebuild_v0*.py"),
                                  "--offline"], "net": False},
        "rebuild_full": {"zh": "重建七段(uv 實測+出執行檔)",
                         "argv": [sys.executable,
                                  _eng("supportive modules/registry",
                                       "CGC_MDL050_EnvRebuild_v0*.py")],
                         "net": True},
        "lessons": {"zh": "教訓帳本(矩陣+基線)",
                    "argv": [sys.executable,
                             _eng("supportive modules/registry",
                                  "CGC_MDL058_Lessons_v0*.py")], "net": False},
        "ocr_probe": {"zh": "OCR 車道探測",
                      "argv": [sys.executable,
                               _eng("supportive modules/registry",
                                    "via_ocr_super_v0*.py"), "--probe"],
                      "net": False},
        "ocr_plan": {"zh": "OCR 隔離安裝計畫",
                     "argv": [sys.executable,
                              _eng("supportive modules/registry",
                                   "via_ocr_super_v0*.py"), "--plan"],
                     "net": False},
        "selftest_fast": {"zh": "全矩陣自測(--fast)",
                          "argv": [sys.executable,
                                   _eng("supportive modules/registry",
                                        "CGC_MDL064_SelftestGrid_v0*.py"),
                                   "--fast"], "net": False},
        "etf_fetch": {"zh": "主動式ETF持股抓取(ENG051)",
                      "argv": [sys.executable,
                               _eng("functional modules/VDF/engine",
                                    "VDF_ENG051_ActiveTWETF_Holdings*.py")],
                      "net": True},
        "chat2doc": {"zh": "對話→文章/程式(NLP)",
                     "argv": [sys.executable,
                              _eng("supportive modules/registry",
                                   "CGC_MDL108_ChatToDoc_v0*.py")],
                     "net": False},
        "uispec": {"zh": "UI 元件三語轉碼",
                   "argv": [sys.executable,
                            _eng("supportive modules/registry",
                                 "CGC_MDL107_UISpecManager_v0*.py")],
                   "net": False},
        "govcon": {"zh": "中央治理台(六管線)",
                   "argv": [sys.executable,
                            _eng("supportive modules/registry",
                                 "CGC_MDL106_GovConsole_v0*.py")],
                   "net": False},
        "complete_all": {"zh": "一鍵完工鏈(16 步;批335;MDL121)",
                         "argv": [sys.executable,
                                  _eng("supportive modules/registry",
                                       "CGC_MDL121_CompletionAutomator_v*.py"),
                                  "run"],
                         "net": True},
        "system_ui": {"zh": "系統總台再生(六主體快照;批334;MDL120)",
                      "argv": [sys.executable,
                               _eng("supportive modules/registry",
                                    "CGC_MDL120_SystemUI_v*.py")],
                      "net": False},
        "group_class": {"zh": "族群分類×價格指數(批307;ENG070)",
                        "argv": [sys.executable,
                                 _eng("functional modules/VDF/engine",
                                      "VDF_ENG070_GroupClassificationIndex_v*.py"),
                                 "run"], "net": False},
        "group_backtest": {"zh": "族群回測(批308;ENG071)",
                           "argv": [sys.executable,
                                    _eng("functional modules/VDF/engine",
                                         "VDF_ENG071_GroupBacktest_v*.py"),
                                    "run"], "net": False},
        "story_rotation": {"zh": "故事族群輪動橋接 v0.5(批325;ENG072)",
                           "argv": [sys.executable,
                                    _eng("functional modules/VDF/engine",
                                         "VDF_ENG072_StoryRotationBridge_v*.py"),
                                    "run"], "net": False},
        "std_dashboard": {"zh": "VAP 標準儀表板(三頁 Plotly;批279)",
                          "argv": [sys.executable,
                                   _eng("functional modules/VAP/engine",
                                        "VAP_ENG014_StdDashboardTemplate_v0*.py"),
                                   "run"],
                          "net": False},
        "ui": {"zh": "重生全部 UI",
               "argv": [sys.executable,
                        _eng("supportive modules/registry",
                             "CGC_MDL096_SyncStatus_v*.py"), "--regen-all"],
               "net": False},
    }
    return T


# 解方冊(RYG 矩陣「狀況→解決方案」;pattern 對映=上次解法同步)
SOLUTIONS = [
    (r"VIA_NET_CONSENT|同意閘", "勾選同意閘後重按(fail-closed 設計)"),
    (r"Conflicting lock|lock", "資料庫使用中(回補/日更跑著)——等它完成再按,或先按停"),
    (r"404|Not Found", "端點候源(P16 型)——資料面已有官方/替代源,非阻斷"),
    (r"KeyboardInterrupt", "被手動中斷——已抓資料保留,重按即續跑"),
    (r"No such file", "檔案缺——先 git pull origin main 更新"),
    (r"ModuleNotFoundError: No module named '(\w+)'", "套件缺——pip install 該套件"),
    (r"Recv failure|Connection reset|Tunnel", "連線被斷(代理/防火牆)——重按重試;持續失敗=候源"),
]

_runs: dict = {}   # task -> {proc, run_id, accepted_params, log, started, ...}
_lock = threading.RLock()
_vap_mutation_lock = threading.Lock()
_intake_lock = threading.Lock()
_sync_execution: dict | None = None


def _suggest(tail: str) -> str:
    for pat, sol in SOLUTIONS:
        if re.search(pat, tail):
            return sol
    return ""


DATE_RX_Q = re.compile(r"^\d{4}-\d{2}-\d{2}$")
CODE_RX_Q = re.compile(r"^\d{4,6}$")
CATS_RX_Q = re.compile(r"^[a-z_]+(?:\s*,\s*[a-z_]+)*$")


def _request_error(message: str, field: str = "") -> dict:
    out = {"ok": False, "kind": "invalid_parameters", "err": message}
    if field:
        out["field"] = field
    return out


def _validated_task(tid, codes="", start="", end="", cats=""):
    """嚴格驗證並正規化任務參數；絕不靜默忽略畫面輸入。"""
    values = {"task": tid, "codes": codes, "start": start,
              "end": end, "cats": cats}
    for field, value in values.items():
        if not isinstance(value, str):
            return None, _request_error(f"{field} 必須是字串", field)
    if not tid or tid != tid.strip():
        return None, _request_error("工作項目不可空白或含首尾空格", "task")
    tasks = task_registry()
    if tid not in tasks:
        return None, {"ok": False, "kind": "unknown_task",
                      "field": "task",
                      "err": "任務不在白名單(安全鐵則:不接受任意指令)"}
    task = tasks[tid]
    accepted = {"task": tid, "codes": "", "start": "", "end": "",
                "cats": ""}
    argv_extra: list[str] = []

    raw_codes = codes.strip()
    if raw_codes:
        if not task.get("codes"):
            return None, _request_error("此工作不接受股票代號", "codes")
        code_items = [part for part in re.split(r"[\s,]+", raw_codes) if part]
        if not code_items or len(code_items) > 50 \
                or any(not CODE_RX_Q.fullmatch(item) for item in code_items):
            return None, _request_error(
                "股票代號須為 4-6 位數字，最多 50 個，以逗號或空白分隔", "codes")
        code_items = list(dict.fromkeys(code_items))
        accepted["codes"] = ",".join(code_items)
        argv_extra.extend(code_items)

    raw_start, raw_end = start.strip(), end.strip()
    if raw_start or raw_end:
        if not task.get("range"):
            return None, _request_error("此工作不接受日期範圍", "start")
        if not raw_start or not raw_end:
            return None, _request_error("開始日期與結束日期必須成對提供", "start")
        if not DATE_RX_Q.fullmatch(raw_start) or not DATE_RX_Q.fullmatch(raw_end):
            return None, _request_error("日期格式必須為 YYYY-MM-DD", "start")
        try:
            start_date, end_date = date.fromisoformat(raw_start), date.fromisoformat(raw_end)
        except ValueError:
            return None, _request_error("日期不是有效日曆日期", "start")
        if start_date > end_date:
            return None, _request_error("開始日期不可晚於結束日期", "start")
        accepted.update({"start": raw_start, "end": raw_end})
        argv_extra.extend(["--start", raw_start, "--end", raw_end])

    raw_cats = cats.strip()
    if raw_cats:
        if not task.get("cats"):
            return None, _request_error("此工作不接受資料分類", "cats")
        if len(raw_cats) > 160 or not CATS_RX_Q.fullmatch(raw_cats):
            return None, _request_error("資料分類格式不符", "cats")
        cat_items = [part.strip() for part in raw_cats.split(",")]
        cat_items = list(dict.fromkeys(cat_items))
        unknown = [item for item in cat_items if item not in GLOBAL_CATEGORIES]
        if unknown:
            return None, _request_error(
                "未知資料分類：" + ",".join(unknown), "cats")
        accepted["cats"] = ",".join(cat_items)
        argv_extra.extend(["--cats", accepted["cats"]])
    return (task, accepted, argv_extra), None


def _poll_run_locked(run: dict):
    """輪詢並關閉已完成的父行程 log handle；呼叫端必須持有 _lock。"""
    rc = run["proc"].poll()
    if rc is not None and not run.get("log_closed"):
        try:
            run["lf"].close()
        except Exception:
            pass
        run["log_closed"] = True
        run.setdefault("t1", time.time())
    return rc


def _active_run_locked():
    for task_id, run in _runs.items():
        if _poll_run_locked(run) is None:
            return task_id, run
    return None


def _active_execution_locked():
    if _sync_execution is not None:
        return _sync_execution["task"], _sync_execution
    return _active_run_locked()


def _active_execution():
    with _lock:
        active = _active_execution_locked()
        if not active:
            return None
        task_id, run = active
        return {"task": task_id, "run_id": run["run_id"]}


def _reserve_sync_execution(task: str, accepted_params: dict):
    """為 in-process 有副作用分析保留全域單通道。"""
    global _sync_execution
    with _lock:
        active = _active_execution_locked()
        if active:
            active_task, active_run = active
            return None, {"ok": False, "kind": "busy",
                          "run_id": active_run["run_id"],
                          "err": f"已有工作「{active_task}」執行中；"
                                 "全域單通道拒絕並行啟動"}
        lease = {"task": task, "run_id": secrets.token_urlsafe(18),
                 "accepted_params": accepted_params,
                 "started_at": datetime.now().astimezone().isoformat(
                     timespec="seconds")}
        _sync_execution = lease
        return lease, None


def _release_sync_execution(run_id: str):
    global _sync_execution
    with _lock:
        if _sync_execution and _sync_execution.get("run_id") == run_id:
            _sync_execution = None


def start_task(tid: str, codes: str = "", start: str = "", end: str = "",
               cats: str = "") -> dict:
    validated, error = _validated_task(tid, codes, start, end, cats)
    if error:
        return error
    task, accepted, argv_extra = validated
    with _lock:
        active = _active_execution_locked()
        if active:
            active_task, active_run = active
            return {"ok": False, "kind": "busy",
                    "run_id": active_run["run_id"],
                    "err": f"已有工作「{active_task}」執行中；"
                           "全域單通道拒絕並行啟動"}
        argv = list(task["argv"]) + argv_extra
        if not argv or not argv[0]:
            return {"ok": False, "kind": "engine_missing",
                    "err": "執行程式缺(先 git pull)"}
        if argv[0] == sys.executable and (len(argv) < 2 or not argv[1]
                                          or not Path(argv[1]).is_file()):
            return {"ok": False, "kind": "engine_missing",
                    "err": "引擎檔缺(先 git pull)"}
        env = dict(os.environ)
        if task.get("net"):
            env["VIA_NET_CONSENT"] = "YES"
            env["VIA_SCRAPE_CONSENT"] = "YES"
        LOGDIR.mkdir(parents=True, exist_ok=True)
        logp = LOGDIR / f"{tid}.log"
        lf = open(logp, "w", encoding="utf-8", errors="ignore")
        try:
            proc = subprocess.Popen(
                argv, stdout=lf, stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,  # 不卡斷:子引擎討 stdin 永不懸吊
                env=env, cwd=str(VIA))
        except Exception as exc:
            lf.close()
            return {"ok": False, "kind": "launch_failed",
                    "err": f"工作無法啟動({type(exc).__name__})"}
        run_id = secrets.token_urlsafe(18)
        now = datetime.now().astimezone()
        _runs[tid] = {
            "proc": proc, "run_id": run_id, "accepted_params": accepted,
            "log": logp, "lf": lf, "t0": time.time(),
            "started": now.strftime("%H:%M:%S"),
            "started_at": now.isoformat(timespec="seconds"),
        }
        return {"ok": True, "run_id": run_id,
                "accepted_params": accepted}


def _grid_total():
    """全矩陣站數(取 GRID 終判尾版;缺=None 誠實不假估)。"""
    try:
        ev = sorted((VIA / "VIA_Reports" / "selftest_runs").glob("GRID_*.json"))[-1]
        d = json.loads(ev.read_text(encoding="utf-8"))
        n = (d.get("total") or d.get("站數")
             or len(d.get("stations") or d.get("results") or []))
        return int(n) or None
    except Exception:
        return None


# 動態進度規則冊(9hh5to「動態進度」令):(計數樣式, 總數函式)。
# 無規則任務=不定條(誠實不假估)——elapsed/beat 仍全員供應。
PROG = {
    "complete_all": (r"^\[完工\] \d+/\d+ \S+ → (?:OK|FAIL|SKIP)", lambda: 16),
    "selftest_fast": (r"^\s*\[(?:OK|FAIL)\s*\]", _grid_total),
    "rebuild_full": (r"^── [①②③④⑤⑥⑦]", lambda: 7),
    "rebuild_scan": (r"^── [①②③④⑤⑥⑦]", lambda: 7),
    "lessons": (r"^── [①②③④⑤]", lambda: 5),
    "ocr_probe": (r"^\s*\[(?:備 |缺境|缺體|缺模)\]", lambda: 4),
    "govcon": (r"^── [①②③④⑤⑥⑦]", lambda: 7),
    "uispec": (r"^── [①②③④⑤]", lambda: 5),
    "chat2doc": (r"^── [①②③④]", lambda: 4),
}


_VAP = {"m": None}


def vap_mod():
    """VAP_ENG013 尾版 in-process 載入(唯讀分析;lazy 快取;缺=None 誠實)。"""
    if _VAP["m"] is None:
        try:
            import importlib.util as iu
            hits = sorted((VIA / "functional modules" / "VAP" / "engine"
                           ).glob("VAP_ENG013_MarketAnalytics_v0*.py"))
            sp = iu.spec_from_file_location("vap_eng013", hits[-1])
            m = iu.module_from_spec(sp)
            sys.modules["vap_eng013"] = m
            sp.loader.exec_module(m)
            _VAP["m"] = m
        except Exception:
            _VAP["m"] = False
    return _VAP["m"] or None


_SYSAPI = {"m": None}
_STATIC_UI_RX = re.compile(r"^/VIA_UI_[\w.-]+\.html$")


def sysapi_mod():
    """CGC_MDL119 SystemAPI 尾版 in-process 載入(批332;唯讀聚合;缺=None 誠實)。"""
    if _SYSAPI["m"] is None:
        try:
            import importlib.util as iu
            hits = sorted(HERE.glob("CGC_MDL119_SystemAPI_v0*.py"))
            sp = iu.spec_from_file_location("cgc_mdl119", hits[-1])
            m = iu.module_from_spec(sp)
            sys.modules["cgc_mdl119"] = m
            sp.loader.exec_module(m)
            _SYSAPI["m"] = m
        except Exception:
            _SYSAPI["m"] = False
    return _SYSAPI["m"] or None


def _static_ui_path(url_path: str) -> Path | None:
    """同源靜態頁白名單(批333):/VIA_UI_*.html→ui_support 夾內檔;越夾=None"""
    if not _STATIC_UI_RX.fullmatch(url_path):
        return None
    if url_path == "/VIA_UI_StdDashboard_v0100.html":   # Codex 精確 iframe 路由(frameable)優先
        return None
    target = (UI_ROOT / url_path[1:]).resolve()
    if target.parent != UI_ROOT.resolve() or not target.is_file():
        return None
    return target


def status_all() -> dict:
    T = task_registry()
    out = {}
    with _lock:
        for tid, t in T.items():
            r = _runs.get(tid)
            if r is None:
                out[tid] = {"zh": t["zh"], "state": "idle",
                            "run_id": None}
                continue
            rc = _poll_run_locked(r)
            tail, win, sz, mt = "", "", 0, None
            try:  # 不卡斷:尾窗定量讀(64KB 界),巨 log 不拖橋
                st_ = r["log"].stat()
                sz, mt = st_.st_size, st_.st_mtime
                with open(r["log"], "rb") as fh:
                    if sz > 65536:
                        fh.seek(sz - 65536)
                    win = fh.read().decode("utf-8", errors="ignore")
                tail = "\n".join(win.strip().splitlines()[-3:])[-400:]
            except Exception:
                pass
            state = "running" if rc is None else ("ok" if rc == 0 else "fail")
            ent = {"zh": t["zh"], "state": state, "rc": rc,
                   "run_id": r["run_id"],
                   "started": r["started"],
                   "tail": tail,
                   "elapsed": max(0, int((r.get("t1") or time.time())
                                         - r.get("t0", time.time()))),
                   "beat": max(0, int(time.time() - mt)) if mt else None,
                   "kb": sz // 1024,
                   "fix": _suggest(tail) if state == "fail" else ""}
            rule = PROG.get(tid)
            if rule and win:
                done = len(re.findall(rule[0], win, re.M))
                ent["done"] = done
                tot = rule[1]()
                if tot:  # 進度≠裁決:跑完(不論紅綠)=100;跑動中封頂 99
                    ent["pct"] = (min(100, done * 100 // tot) if rc is not None
                                  else min(99, done * 100 // tot))
            out[tid] = ent
    return out


def stock_data(code: str) -> dict:
    """個股全景聚合(批209:唯讀;庫鎖=busy 誠實;零發明=庫值直出)"""
    if not re.fullmatch(r"\d{4,6}[A-Z]?", code or ""):
        return {"err": "代號格式不符(4-6 位數字)"}
    import duckdb
    db = VIA / "functional modules" / "VDF" / "output_hub" / "mega" / "vdf_tw_market.duckdb"
    try:
        con = duckdb.connect(str(db), read_only=True)
    except Exception as e:
        if "lock" in str(e).lower():
            return {"busy": True, "note": "資料庫使用中(回補/日更)=稍後自動重試"}
        return {"err": str(e)[:120]}
    out = {"code": code}

    def q(sql, args=()):
        try:
            return con.execute(sql, list(args)).fetchall()
        except Exception:
            return []

    out["name"] = (q("SELECT name FROM tw_listings WHERE code=?", [code])
                   or [[code]])[0][0]
    out["px"] = [[str(d), c] for d, c in q(
        "SELECT date, close FROM prices_canonical WHERE ticker=? "
        "ORDER BY date DESC LIMIT 120", [f"{code}.TW"])][::-1]
    f = q("SELECT date, ret_1d, ret_20d, ret_60d, vol_20d_ann, ma20_ratio, "
          "ma60_ratio, hi252_dist, volu_z20 FROM features_daily "
          "WHERE ticker=? ORDER BY date DESC LIMIT 1", [f"{code}.TW"])
    out["factors"] = ([str(f[0][0])] + [f[0][i] for i in range(1, 9)]) if f else None
    out["consensus"] = [[s, str(d), th, tl, tm, na, e1, cl, up] for
                        d, s, th, tl, tm, na, e1, cl, up in q(
        "SELECT date, source, target_high, target_low, target_median, "
        "n_analysts, eps_fy1, close, upside_pct FROM consensus_daily "
        "WHERE code=? QUALIFY row_number() OVER (PARTITION BY source "
        "ORDER BY date DESC)=1", [code])]
    out["revenue"] = [[ym, rev, mom, yoy, hi] for ym, rev, mom, yoy, hi in q(
        "SELECT ym, revenue, mom_pct, yoy_pct, high_60m "
        "FROM monthly_revenue_analysis WHERE code=? ORDER BY ym DESC LIMIT 12",
        [code])]
    g = q("SELECT gid, above_ma20, n_ma20, win60, lose60 FROM ("
          "SELECT g.*, row_number() OVER (PARTITION BY gid ORDER BY date DESC) rn "
          "FROM group_features_daily g) WHERE rn=1 AND gid IN ("
          "SELECT GroupId FROM read_csv_auto(?) WHERE "
          "regexp_replace(Ticker, '\\.(TW|TWO)$', '')=?)",
          [str(sorted((VIA / "functional modules/GroupIndex/output_hub/rotation_runs"
                       ).glob("ROTATION_TW_*/csv/latest_classification.csv"))[-1]),
           code]) if list((VIA / "functional modules/GroupIndex/output_hub/rotation_runs"
                           ).glob("ROTATION_TW_*/csv/latest_classification.csv")) else []
    out["group"] = g[0] if g else None
    con.close()
    return out


INTAKE_CAP = 50 * 1024 * 1024  # 50MB 上限(批301)
# 批339:收件目的地固定冊(鍵→根;零路徑注入;殼側只能選鍵不能給路徑)
INTAKE_DESTS = frozenset({"downloads", "vrn_incoming"})


def _intake_root_for(dest: str, server_root=None) -> Path | None:
    """dest 鍵→真根;'' 或 'downloads'=既有行為(server.intake_root 或 Downloads)"""
    if dest == "vrn_incoming":
        return VIA / "functional modules" / "VRN" / "input" / "incoming"
    return Path(server_root) if server_root else None
_NAME_RX = re.compile(r"[^\w.\u4e00-\u9fff-]+")
_WINDOWS_RESERVED = {
    "CON", "PRN", "AUX", "NUL", "CLOCK$", "CONIN$", "CONOUT$",
    *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10)),
}


def _windows_device_key(name: str) -> str:
    """NFKC 亦涵蓋全形字與 ¹²³ 等 Windows 傳統裝置名變體。"""
    normalized = unicodedata.normalize("NFKC", name).replace("\\", "/")
    basename = normalized.rsplit("/", 1)[-1]
    return re.split(r"[.:]", basename, maxsplit=1)[0].strip(" .").upper()


def _safe_filename(name: str) -> str:
    if not isinstance(name, str):
        raise ValueError("檔名必須是字串")
    if _windows_device_key(name) in _WINDOWS_RESERVED:
        raise ValueError("Windows 保留裝置名不可收件")
    normalized = unicodedata.normalize("NFKC", name).replace("\\", "/")
    base = Path(normalized).name
    base = _NAME_RX.sub("_", base).strip(" .") or "unnamed"
    if _windows_device_key(base) in _WINDOWS_RESERVED:
        raise ValueError("Windows 保留裝置名不可收件")
    if base in (".", ".."):
        base = "unnamed"
    path = Path(base)
    suffix = path.suffix[:24]
    stem_limit = max(1, 180 - len(suffix))
    stem = path.stem[:stem_limit] or "unnamed"
    return stem + suffix


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _publish_error(exc: OSError) -> dict:
    number = getattr(exc, "errno", None)
    marker = errno.errorcode.get(number, f"OS-{number or 'UNKNOWN'}")
    return {"ok": False, "kind": "publish_failed",
            "err": f"原子收件發布失敗({marker})；未覆寫任何既有檔案"}


def _publish_bytes_exclusive(root: Path, target: Path, data: bytes):
    """完整寫同目錄暫存檔再 hard-link 發布；不支援時 fail-closed。"""
    descriptor = None
    temporary = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=".via-intake-", suffix=".tmp", dir=str(root))
        temporary = Path(temporary_name)
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = None  # fdopen 已接管
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, target)
        except FileExistsError:
            return False, None
        except OSError as exc:
            # 不以 copy/replace 降級：會暴露半成品或覆寫競態。
            return False, _publish_error(exc)
        return True, None
    except OSError as exc:
        return False, _publish_error(exc)
    finally:
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                pass
        try:
            if temporary is not None:
                temporary.unlink()
        except OSError:
            pass


def _intake_save(name: str, data: bytes, root: Path | None = None) -> dict:
    """hash 去重、進程鎖與排他原子發布；任何競態均不得覆寫既有檔。"""
    if not data:
        return {"ok": False, "err": "空檔(零位元組)=誠實拒收"}
    if len(data) > INTAKE_CAP:
        return {"ok": False, "err": f"逾 50MB 上限({len(data)//1048576}MB)"}
    try:
        base = _safe_filename(name)
    except ValueError as exc:
        return {"ok": False, "kind": "invalid_name", "err": str(exc)}
    if root is None:
        dl = Path.home() / "Downloads"
        root = dl if dl.is_dir() else (VIA / "VIA_Reports" / "deck_intake")
    try:
        root.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        return _publish_error(exc)
    sha = hashlib.sha256(data).hexdigest()
    original = Path(base)
    candidates = [base]
    for width in (8, 16, 32, 64):
        candidates.append(f"{original.stem}_{sha[:width]}{original.suffix}")
    candidates.extend(
        f"{original.stem}_{sha[:16]}_{index:02d}{original.suffix}"
        for index in range(1, 101))
    with _intake_lock:
        for candidate in candidates:
            target = root / candidate
            if target.exists():
                try:
                    if _file_sha256(target) == sha:
                        return {"ok": True, "saved": str(target),
                                "sha256": sha,
                                "skip": "SKIP_IDENTICAL(同名同 hash=冪等)"}
                except OSError:
                    pass
                continue
            published, publish_error = _publish_bytes_exclusive(root, target, data)
            if publish_error:
                return publish_error
            if published:
                return {"ok": True, "saved": str(target),
                        "sha256": sha, "skip": ""}
    return {"ok": False, "kind": "name_exhausted",
            "err": "同名候選已用盡；未覆寫任何既有檔案"}


_BRIDGE_SHIM = r"""
<script id="via-secure-bridge-shim">
(()=>{"use strict";
 const meta=document.querySelector('meta[name="via-csrf"]');
 const token=meta?meta.content:"";
 const nativeFetch=window.fetch.bind(window);
 const mutations=new Set(["/run","/intake","/stock_fetch","/vap_kline",
  "/vap_check","/vap_flows"]);
 window.fetch=function(input,init){
  const request=input instanceof Request?input:null;
  const url=new URL(request?request.url:String(input),location.href);
  let options=Object.assign({},init||{});
  let method=String(options.method||(request?request.method:"GET")).toUpperCase();
  if(url.origin===location.origin&&mutations.has(url.pathname)){
   if(method==="GET"){
    options.body=JSON.stringify(Object.fromEntries(url.searchParams.entries()));
    options.method="POST";method="POST";url.search="";
   }
   if(method==="POST"){
    const headers=new Headers(options.headers||(request?request.headers:undefined));
    headers.set("Content-Type","application/json");
    headers.set("X-VIA-CSRF",token);options.headers=headers;
   }
  }
  return nativeFetch(url.toString(),options);
 };
})();
</script>
"""


def _inject_ui_context(payload: bytes, token: str) -> bytes:
    """只改 HTTP 回應副本：填入權杖並兼容尚未升版的 GET UI。"""
    page = payload.decode("utf-8", errors="replace")
    safe_token = html.escape(token, quote=True)
    empty_meta = '<meta name="via-csrf" content="">'
    filled_meta = f'<meta name="via-csrf" content="{safe_token}">'
    if empty_meta in page:
        page = page.replace(empty_meta, filled_meta, 1)
    elif re.search(r'<meta\s+name=["\']via-csrf["\']', page, re.I):
        page = re.sub(
            r'<meta\s+name=["\']via-csrf["\'][^>]*>', filled_meta,
            page, count=1, flags=re.I)
    else:
        page = re.sub(r"<head([^>]*)>", r"<head\1>" + filled_meta,
                      page, count=1, flags=re.I)
    page = page.replace('const API_BASE="http://127.0.0.1:8765";',
                        "const API_BASE=location.origin;", 1)
    page = re.sub(r"</head>", _BRIDGE_SHIM + "</head>", page,
                  count=1, flags=re.I)
    return page.encode("utf-8")


def _result_http_code(result: dict, success: int = 200) -> int:
    if result.get("ok"):
        return success
    return {
        "busy": 409,
        "engine_missing": 503,
        "launch_failed": 500,
    }.get(str(result.get("kind", "")), 400)


def _public_run_result(result: dict) -> dict:
    """前端固定封套；內部錯誤分類不得洩漏成 schema 漂移。"""
    public = {"ok": bool(result.get("ok"))}
    for key in ("run_id", "accepted_params", "err"):
        if key in result:
            public[key] = result[key]
    return public


def _public_intake_result(result: dict) -> dict:
    allowed = ("ok", "saved", "sha256", "skip", "err", "dest")
    return {key: result[key] for key in allowed if key in result}


def _strict_body(body: dict, allowed: set[str], required: set[str] | None = None):
    unknown = sorted(set(body) - allowed)
    if unknown:
        return {"ok": False, "kind": "invalid_parameters",
                "err": "不接受欄位：" + ",".join(unknown)}
    missing = sorted((required or set()) - set(body))
    if missing:
        return {"ok": False, "kind": "invalid_parameters",
                "err": "缺少欄位：" + ",".join(missing)}
    return None


def _strict_code(value, field="code"):
    if not isinstance(value, str) or not CODE_RX_Q.fullmatch(value.strip()):
        return None, {"ok": False, "kind": "invalid_parameters",
                      "field": field, "err": "代號須為 4-6 位數字"}
    return value.strip(), None


def _strict_codes(value):
    if not isinstance(value, str):
        return None, {"ok": False, "kind": "invalid_parameters",
                      "field": "codes", "err": "代號清單必須是字串"}
    items = [part for part in re.split(r"[\s,]+", value.strip()) if part]
    if not items or len(items) > 50 or any(
            not CODE_RX_Q.fullmatch(item) for item in items):
        return None, {"ok": False, "kind": "invalid_parameters",
                      "field": "codes",
                      "err": "代號須為 4-6 位數字，最多 50 個"}
    return list(dict.fromkeys(items)), None


def _strict_int(value, field: str, minimum: int, maximum: int, default: int):
    if value in (None, ""):
        return default, None
    if isinstance(value, int) and not isinstance(value, bool):
        number = value
    elif isinstance(value, str) and re.fullmatch(r"\d{1,4}", value):
        number = int(value)
    else:
        number = None
    if number is None or not minimum <= number <= maximum:
        return None, {"ok": False, "kind": "invalid_parameters",
                      "field": field,
                      "err": f"{field} 必須介於 {minimum} 與 {maximum}"}
    return number, None


@contextmanager
def _temporary_net_consent():
    saved = {key: os.environ.get(key)
             for key in ("VIA_NET_CONSENT", "VIA_SCRAPE_CONSENT")}
    os.environ["VIA_NET_CONSENT"] = "YES"
    os.environ["VIA_SCRAPE_CONSENT"] = "YES"
    try:
        yield
    finally:
        for key, value in saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):  # 靜音存取日誌
        pass

    def _origin(self) -> str:
        return str(getattr(self.server, "trusted_origin", TRUSTED_ORIGIN))

    def _token(self) -> str:
        return str(getattr(self.server, "csrf_token", CSRF_TOKEN))

    def _host_is_trusted(self) -> bool:
        return self.headers.get("Host", "") == urlparse(self._origin()).netloc

    def _common_headers(self):
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Permissions-Policy",
                         "camera=(), microphone=(), geolocation=(), payment=(), usb=()")
        self.send_header("X-Permitted-Cross-Domain-Policies", "none")

    def _json(self, obj, code=200):
        b = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self._common_headers()
        self.end_headers()
        try:
            self.wfile.write(b)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass

    def _html(self, body: bytes, code=200, frameable=False):
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        frame_ancestors = "'self'" if frameable else "'none'"
        sandbox = "sandbox allow-scripts; " if frameable else ""
        self.send_header("Content-Security-Policy",
                         sandbox +
                         "default-src 'self'; script-src 'self' 'unsafe-inline'; "
                         "style-src 'self' 'unsafe-inline'; frame-src 'self'; "
                         "img-src 'self' data: blob:; font-src 'self' data:; "
                         "connect-src 'self'; base-uri 'none'; "
                         f"frame-ancestors {frame_ancestors}; form-action 'none'")
        self.send_header("X-Frame-Options", "SAMEORIGIN" if frameable else "DENY")
        self._common_headers()
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass

    def _serve_ui(self, path: Path, *, inject=False, frameable=False):
        try:
            body = path.read_bytes()
            if inject:
                body = _inject_ui_context(body, self._token())
        except Exception:
            name = html.escape(path.name)
            body = f"<h1>{name} 缺席；請先重生使用者介面</h1>".encode("utf-8")
            return self._html(body, 404, frameable=frameable)
        return self._html(body, frameable=frameable)

    def _trusted_mutation(self) -> bool:
        """副作用路徑必須由當次本機 MasterControl 同源發出。"""
        origin = self.headers.get("Origin", "")
        fetch_site = self.headers.get("Sec-Fetch-Site", "")
        token = self.headers.get("X-VIA-CSRF", "")
        return (self._host_is_trusted()
                and origin == self._origin()
                and fetch_site == "same-origin"
                and bool(token)
                and hmac.compare_digest(token, self._token()))

    def _read_json(self, cap: int) -> dict | None:
        media_type = self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
        if media_type != "application/json":
            self._json({"ok": False, "err": "只接受 application/json"}, 415)
            return None
        if self.headers.get("Transfer-Encoding"):
            self.close_connection = True
            self._json({"ok": False, "err": "不接受 Transfer-Encoding"}, 400)
            return None
        try:
            size = int(self.headers.get("Content-Length", "0") or "0")
        except ValueError:
            size = 0
        if size <= 0 or size > cap:
            self.close_connection = True
            self._json({"ok": False, "err": "長度缺或逾上限"}, 400)
            return None
        try:
            body = json.loads(self.rfile.read(size).decode("utf-8"))
            if not isinstance(body, dict):
                raise ValueError("body must be object")
            return body
        except Exception as exc:
            self._json({"ok": False,
                        "err": f"封套解析失敗({type(exc).__name__})"}, 400)
            return None

    def do_OPTIONS(self):
        # 同源 UI 不需要 CORS preflight；跨站預檢一律拒絕。
        self.close_connection = True
        if not self._host_is_trusted():
            return self._json({"ok": False, "err": "Host 不在本機安全冊"}, 421)
        return self._json({"ok": False, "err": "跨站請求已拒絕"}, 403)

    def do_POST(self):
        u = urlparse(self.path)
        if not self._host_is_trusted():
            self.close_connection = True
            return self._json({"ok": False, "err": "Host 不在本機安全冊"}, 421)
        if u.path not in MUTATION_PATHS:
            return self._json({"ok": False, "err": "POST 路徑不在安全冊"}, 404)
        if not self._trusted_mutation():
            self.close_connection = True
            return self._json({"ok": False,
                               "err": "非當次本機同源頁或權杖無效"}, 403)
        if u.query:
            return self._json({"ok": False, "err": "副作用端點只接受 JSON body"},
                              400)
        cap = INTAKE_CAP * 4 // 3 + 8192 if u.path == "/intake" else 16384
        body = self._read_json(cap)
        if body is None:
            return None
        if u.path == "/run":
            invalid = _strict_body(
                body, {"task", "codes", "start", "end", "cats"}, {"task"})
            if invalid:
                return self._json(_public_run_result(invalid), 400)
            result = start_task(body.get("task"), body.get("codes", ""),
                                body.get("start", ""), body.get("end", ""),
                                body.get("cats", ""))
            return self._json(_public_run_result(result),
                              _result_http_code(result, 202))
        if u.path == "/intake":
            invalid = _strict_body(body, {"name", "b64", "dest"}, {"name", "b64"})
            if invalid:
                return self._json(_public_intake_result(invalid), 400)
            dest = body.get("dest", "")
            if dest not in ("", *INTAKE_DESTS):
                return self._json(_public_intake_result(_request_error(
                    "dest 不在收件目的地冊(downloads|vrn_incoming)", "dest")), 400)
            name, encoded = body.get("name"), body.get("b64")
            if not isinstance(name, str) or not name.strip() or len(name) > 512:
                return self._json(_public_intake_result(_request_error(
                    "檔名必須是 1-512 字元字串", "name")), 400)
            if not isinstance(encoded, str):
                return self._json(_public_intake_result(
                    _request_error("b64 必須是字串", "b64")), 400)
            try:
                data = base64.b64decode(encoded, validate=True)
            except (ValueError, TypeError):
                return self._json(_public_intake_result(
                    _request_error("b64 不是有效 Base64", "b64")), 400)
            root = _intake_root_for(dest, getattr(self.server, "intake_root", None))
            result = _intake_save(name, data, root)
            if result.get("ok"):
                result["dest"] = dest or "downloads"
            if result.get("ok"):
                code = 200 if result.get("skip") else 201
            else:
                code = 500 if result.get("kind") == "publish_failed" else 400
            return self._json(_public_intake_result(result), code)
        if u.path == "/stock_fetch":
            invalid = _strict_body(body, {"code"}, {"code"})
            if invalid:
                return self._json(invalid, 400)
            code, invalid = _strict_code(body.get("code"))
            if invalid:
                return self._json(invalid, 400)
            result = start_task("consensus", codes=code)
            return self._json(_public_run_result(result),
                              _result_http_code(result, 202))

        if u.path == "/vap_kline":
            invalid = _strict_body(body, {"code", "months"}, {"code"})
            if invalid:
                return self._json(invalid, 400)
            code, invalid = _strict_code(body.get("code"))
            if invalid:
                return self._json(invalid, 400)
            months, invalid = _strict_int(body.get("months"), "months", 1, 60, 6)
            if invalid:
                return self._json(invalid, 400)
            accepted = {"code": code, "months": months}
            operation = lambda: module.kline(code, months)
        elif u.path == "/vap_check":
            invalid = _strict_body(body, {"codes"}, {"codes"})
            if invalid:
                return self._json(invalid, 400)
            codes, invalid = _strict_codes(body.get("codes"))
            if invalid:
                return self._json(invalid, 400)
            accepted = {"codes": codes}
            operation = lambda: module.consensus_check(codes)
        else:  # /vap_flows
            invalid = _strict_body(body, {"code", "days"}, {"code"})
            if invalid:
                return self._json(invalid, 400)
            code, invalid = _strict_code(body.get("code"))
            if invalid:
                return self._json(invalid, 400)
            days, invalid = _strict_int(body.get("days"), "days", 1, 120, 10)
            if invalid:
                return self._json(invalid, 400)
            accepted = {"code": code, "days": days}
            operation = lambda: module.flows(code, days)
        lease, busy = _reserve_sync_execution(u.path.lstrip("/"), accepted)
        if busy:
            return self._json(busy, 409)
        try:
            with _vap_mutation_lock, _temporary_net_consent():
                module = vap_mod()
                if not module:
                    return self._json(
                        {"ok": False, "err": "VAP_ENG013 缺(先 git pull)"}, 503)
                result = operation()
        except Exception as exc:
            return self._json({"ok": False, "kind": "operation_failed",
                               "err": f"分析執行失敗({type(exc).__name__})"}, 500)
        finally:
            _release_sync_execution(lease["run_id"])
        return self._json(result)

    def do_GET(self):
        u = urlparse(self.path)
        if not self._host_is_trusted():
            self.close_connection = True
            return self._json({"ok": False, "err": "Host 不在本機安全冊"}, 421)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        if u.path in BLOCKED_MUTATION_GETS:
            return self._json({"ok": False,
                               "err": "有副作用 GET 已封鎖；請改用同源 CSRF POST"},
                              405)
        if u.path == "/ping":
            return self._json({"ok": True, "via": "deck-bridge", "v": "v0120",
                               "accel": bool(VIA_ACCEL)})  # 加速器橋可視(graceful)
        if u.path == "/status":
            return self._json(status_all())
        if u.path == "/auto":          # 批210:自動駕駛派工記錄
            return self._json({"log": _auto_log})
        if u.path == "/stock_data":    # 批209:代號→全景聚合 JSON
            return self._json(stock_data(q.get("code", "")))
        if u.path == "/vap_revenue":
            m = vap_mod()
            return self._json(m.revenue_analysis() if m else {"err": "VAP_ENG013 缺(先 git pull)"})
        if u.path == "/vap_groups":
            m = vap_mod()
            return self._json(m.group_analysis() if m else {"err": "VAP_ENG013 缺(先 git pull)"})
        if u.path == "/vap_etflist":
            m = vap_mod()
            return self._json(m.etf_list(limit=60) if m else {"err": "VAP_ENG013 缺(先 git pull)"})
        if u.path == "/vap_etf":
            m = vap_mod()
            ids = [x for x in (q.get("ids", "").split(",")) if x]
            return self._json(m.etf_holdings(ids) if m else {"err": "VAP_ENG013 缺(先 git pull)"})
        if u.path == "/probe":           # 批333:file:// 頁探樞紐在線專用(零資訊;CORP cross-origin
            # =no-cors 探針可達;其餘端點維持 same-origin;實錄:CORP same-origin 使 no-cors 探針被
            # ERR_BLOCKED_BY_RESPONSE 擋下→導向永不觸發)
            b = b'{"ok":true}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(b)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Cross-Origin-Resource-Policy", "cross-origin")
            self.end_headers()
            try:
                self.wfile.write(b)
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                pass
            return
        if u.path.startswith("/api/"):   # 批332/333:標準系統 U/I 後端(六主體聚合;唯讀)
            m = sysapi_mod()
            name = u.path[len("/api/"):].strip("/") or "subjects"
            return self._json(m.api(name) if m
                              else {"state": "FAIL", "reason": "CGC_MDL119 缺(先 git pull)"})
        if u.path == "/system":          # 批332/333:系統總台(尾版;注入權杖+shim)
            sp_ = _newest(UI_ROOT, "VIA_UI_System_v0*.html")
            return self._serve_ui(sp_ or UI_ROOT / "VIA_UI_System_missing.html",
                                  inject=True)
        static = _static_ui_path(u.path)
        if static is not None:           # 批333:同源靜態頁(連結網自動同源;唯讀)
            return self._serve_ui(static, inject=True)
        if u.path == "/vapdeck":
            vp = _newest(UI_ROOT, "VIA_UI_VapDeck_v0*.html")
            return self._serve_ui(vp or UI_ROOT / "VIA_UI_VapDeck_missing.html",
                                  inject=True)
        if u.path == "/govmatrix":  # 中央治理台最新矩陣報告(尾版=鐵律)
            mp = _newest(VIA / "VIA_Reports" / "govconsole_runs",
                         "GOVMATRIX_*.html")
            fallback = VIA / "VIA_Reports" / "govconsole_runs" / "GOVMATRIX_missing.html"
            return self._serve_ui(mp or fallback)
        if u.path == "/govdeck":
            gp = _newest(UI_ROOT, "VIA_UI_GovDeck_v0*.html")
            return self._serve_ui(gp or UI_ROOT / "VIA_UI_GovDeck_missing.html",
                                  inject=True)
        if u.path in ("/", "/master"):
            return self._serve_ui(MASTER_UI, inject=True)
        if u.path == "/deck":
            return self._serve_ui(UI, inject=True)
        if u.path == "/VIA_UI_StdDashboard_v0100.html":
            return self._serve_ui(UI_ROOT / "VIA_UI_StdDashboard_v0100.html",
                                  frameable=True)
        return self._json({"err": "not found"}, 404)


_auto_log: list = []


def auto_pilot():
    """批210:自動駕駛——橋啟動即派工(該自動跑的自動跑)。
    規則冊(誠實留痕 _auto_log):
      ① 今日未日更(marker≠今日)→自動啟 boot 全鏈
      ② 歷史回補 checkpoint 未齊→自動續跑(冪等;已齊=秒退)
    防重三閘:boot marker/任務單例/回補 (段,檔) checkpoint。"""
    ts = datetime.now().strftime("%H:%M:%S")
    mark = (VIA / "functional modules" / "VDF" / "output_hub" / "mega" /
            ".last_boot_update")
    today = datetime.now().strftime("%Y-%m-%d")
    try:
        done_today = mark.exists() and mark.read_text(
            encoding="utf-8").strip() == today
    except Exception:
        done_today = False
    if not done_today:
        r = start_task("boot")
        _auto_log.append({"ts": ts, "task": "boot",
                          "why": "今日未日更(marker)",
                          "ok": r.get("ok", False), "note": r.get("err", "")})
    else:
        _auto_log.append({"ts": ts, "task": "boot",
                          "why": "今日已更=跳過(marker)", "ok": True,
                          "skipped": True})
    queued_note = False
    while True:
        r2 = start_task("backfill")
        if r2.get("kind") != "busy":
            break
        if not queued_note:
            _auto_log.append({"ts": datetime.now().strftime("%H:%M:%S"),
                              "task": "backfill",
                              "why": "全域單通道忙碌=誠實排隊等候",
                              "ok": True, "queued": True,
                              "run_id": r2.get("run_id")})
            queued_note = True
        time.sleep(2)
    _auto_log.append({"ts": datetime.now().strftime("%H:%M:%S"),
                      "task": "backfill",
                      "why": "歷史回補續跑(冪等;已齊=秒退)",
                      "ok": r2.get("ok", False), "note": r2.get("err", "")})


def serve() -> int:
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), H)
    srv.trusted_origin = TRUSTED_ORIGIN
    srv.csrf_token = CSRF_TOKEN
    threading.Thread(target=auto_pilot, daemon=True).start()
    print(f"[deck-bridge] http://127.0.0.1:{PORT}/master 啟動(僅本機;"
          f"同源 CSRF POST;白名單任務制;自動駕駛=日更+回補循序派工)"
          "·Ctrl+C 停橋不斷任務")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()
    return 0


def selftest() -> int:
    global LOGDIR, _sync_execution
    from concurrent.futures import ThreadPoolExecutor

    fails = []
    n_chk = [0]

    def chk(name, cond, note=""):
        n_chk[0] += 1
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    class FakeProc:
        def __init__(self):
            self.rc = None

        def poll(self):
            return self.rc

    class FakeVap:
        def kline(self, code, months):
            return {"lane": "mock", "code": code, "months": months}

        def consensus_check(self, codes):
            return {"lane": "mock", "codes": codes}

        def flows(self, code, days):
            return {"lane": "mock", "code": code, "days": days}

    old_logdir = LOGDIR
    old_popen = subprocess.Popen
    old_runs = dict(_runs)
    old_sync = _sync_execution
    old_vap = _VAP["m"]
    fake_processes = []

    def fake_popen(*args, **kwargs):
        proc = FakeProc()
        fake_processes.append(proc)
        stream = kwargs.get("stdout")
        if stream:
            stream.write("[MOCK] isolated selftest\n")
            stream.flush()
        return proc

    try:
        with tempfile.TemporaryDirectory() as td:
            sandbox_root = Path(td)
            LOGDIR = sandbox_root / "logs"
            subprocess.Popen = fake_popen
            with _lock:
                _runs.clear()
                _sync_execution = None
            _VAP["m"] = FakeVap()

            tasks = task_registry()
            chk("① 白名單任務冊固定 37 項(批334 +4;批335 +complete_all)且治理/VAP 任務齊備",
                len(tasks) == 37 and "system_ui" in tasks and "group_class" in tasks and "complete_all" in tasks
                and all(k in tasks for k in (
                    "deps_scan", "rebuild_full", "govcon", "uispec",
                    "etf_fetch", "etf_analysis", "revenue_consensus",
                    "unified_register", "cmdcenter", "std_dashboard")))

            valid_codes, err_codes = _validated_task(
                "consensus", "2330, 2454 2330")
            valid_global, err_global = _validated_task(
                "global", start="2024-01-01", end="2024-01-31",
                cats="idx,etf,idx")
            bad_cases = [
                _validated_task("evil")[1],
                _validated_task("consensus", "23A0")[1],
                _validated_task("revenue_groups", "2330")[1],
                _validated_task("backfill", start="2024-01-01")[1],
                _validated_task("backfill", start="2024-02-30",
                                end="2024-03-01")[1],
                _validated_task("backfill", start="2024-03-02",
                                end="2024-03-01")[1],
                _validated_task("global", cats="idx,unknown")[1],
                _validated_task(7)[1],
            ]
            chk("② task/codes/date/cats 嚴格驗證且不靜默忽略",
                err_codes is None and err_global is None
                and valid_codes[1]["codes"] == "2330,2454"
                and valid_global[1]["cats"] == "idx,etf"
                and all(item and not item.get("ok") for item in bad_cases))

            launched = start_task("revenue_groups")
            running = status_all()["revenue_groups"]
            accepted = {"task": "revenue_groups", "codes": "", "start": "",
                        "end": "", "cats": ""}
            chk("③ 隔離假行程回 run_id + 精確 accepted_params",
                launched.get("ok") is True
                and launched.get("accepted_params") == accepted
                and isinstance(launched.get("run_id"), str)
                and set(launched) == {"ok", "run_id", "accepted_params"})
            allowed_status = {"zh", "state", "run_id", "started", "elapsed",
                              "beat", "kb", "done", "pct", "rc", "fix", "tail"}
            chk("④ /status 僅回前端允許欄且 run_id 對應本次執行",
                running["state"] == "running"
                and running["run_id"] == launched["run_id"]
                and all(set(row) <= allowed_status
                        for row in status_all().values()))
            busy = start_task("std_dashboard")
            public_busy = _public_run_result(busy)
            chk("⑤ 全域單通道忙碌拒絕且公開封套無額外欄",
                busy.get("kind") == "busy"
                and busy.get("run_id") == launched["run_id"]
                and set(public_busy) <= {"ok", "run_id", "accepted_params", "err"})
            fake_processes[-1].rc = 0
            completed = status_all()["revenue_groups"]
            chk("⑥ 假行程完成後狀態與暫存 log 誠實收斂",
                completed["state"] == "ok" and completed["rc"] == 0
                and (LOGDIR / "revenue_groups.log").is_file())

            lease, lease_error = _reserve_sync_execution(
                "vap_kline", {"code": "2330", "months": 6})
            lease_busy = start_task("revenue_groups")
            _release_sync_execution(lease["run_id"])
            chk("⑦ in-process 分析亦共用全域 execution lock/409 語意",
                lease_error is None and lease_busy.get("kind") == "busy")

            payloads = [b"alpha"] * 4 + [b"beta"] * 4
            with ThreadPoolExecutor(max_workers=8) as pool:
                receipts = list(pool.map(
                    lambda data: _intake_save("same.txt", data, sandbox_root / "intake"),
                    payloads))
            intake_files = [p for p in (sandbox_root / "intake").iterdir()
                            if not p.name.startswith(".via-intake-")]
            traversal = _intake_save("../../evil.txt", b"safe",
                                     sandbox_root / "intake")
            chk("⑧ 收件並發原子唯一、hash 冪等且不覆寫",
                all(r.get("ok") for r in receipts)
                and len(intake_files) == 2
                and {p.read_bytes() for p in intake_files} == {b"alpha", b"beta"}
                and any(r.get("skip") for r in receipts))
            chk("⑧b 收件去路徑且只落指定暫存目錄",
                traversal.get("ok") is True
                and Path(traversal["saved"]).parent == sandbox_root / "intake"
                and Path(traversal["saved"]).name == "evil.txt")

            reserved_root = sandbox_root / "reserved"
            reserved_names = ("CON", "con.txt", "CoM¹.log", "lpt².csv",
                              "NUL.tar.gz", "ＣＯＮ.txt", "CLOCK$.txt",
                              "AUX .csv", "con:stream", ".CON", ".COM¹.txt",
                              "PRN.")
            reserved_receipts = [_intake_save(name, b"x", reserved_root)
                                 for name in reserved_names]
            reserved_untouched = not reserved_root.exists()
            allowed_device_like = _intake_save("COM10.txt", b"allowed",
                                               reserved_root)
            chk("⑧c Windows 保留裝置名含大小寫/延伸名/Unicode 上標皆拒收",
                reserved_untouched
                and all(not item.get("ok")
                        and item.get("kind") == "invalid_name"
                        for item in reserved_receipts)
                and allowed_device_like.get("ok") is True)

            real_link = os.link

            def links_unsupported(*_args, **_kwargs):
                raise OSError(errno.ENOTSUP, "selftest: hard-link unsupported")

            os.link = links_unsupported
            try:
                publish_failure = _intake_save(
                    "no-hardlink.txt", b"must-not-publish",
                    sandbox_root / "link-failure")
            finally:
                os.link = real_link
            failure_files = list((sandbox_root / "link-failure").iterdir())
            chk("⑧d hard-link 不支援時 fail-closed、結構化錯誤且零半成品",
                publish_failure.get("ok") is False
                and publish_failure.get("kind") == "publish_failed"
                and isinstance(publish_failure.get("err"), str)
                and failure_files == [])

            injected = _inject_ui_context(
                b'<html><head><meta name="via-csrf" content=""></head></html>',
                "unit-token")
            chk("⑨ 精確空 CSRF meta 契約只在 HTTP 回應副本注入",
                b'<meta name="via-csrf" content="unit-token">' in injected
                and b'<meta name="via-csrf" content="">' not in injected)

            server = ThreadingHTTPServer(("127.0.0.1", 0), H)
            thread = None
            try:
                port = server.server_address[1]
                origin = f"http://127.0.0.1:{port}"
                server.trusted_origin = origin
                server.csrf_token = "http-test-token"
                server.intake_root = sandbox_root / "http-intake"
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
            except Exception:
                if thread is not None and thread.is_alive():
                    server.shutdown()
                server.server_close()
                if thread is not None:
                    thread.join(timeout=5)
                raise

            def request(method, path, payload=None, headers=None):
                request_headers = dict(headers or {})
                body = None
                if payload is not None:
                    body = json.dumps(payload).encode("utf-8")
                    request_headers.setdefault("Content-Type", "application/json")
                conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
                try:
                    conn.request(method, path, body=body, headers=request_headers)
                    response = conn.getresponse()
                    raw = response.read()
                    return (response.status,
                            {k.lower(): v for k, v in response.getheaders()}, raw)
                finally:
                    conn.close()

            secure_headers = {"Origin": origin, "Sec-Fetch-Site": "same-origin",
                              "X-VIA-CSRF": "http-test-token"}
            try:
                master_code, master_headers, master_body = request("GET", "/master")
                blocked_codes = [request("GET", path)[0]
                                 for path in sorted(BLOCKED_MUTATION_GETS)]
                no_token = request("POST", "/run", {"task": "revenue_groups"})
                wrong_origin = request(
                    "POST", "/run", {"task": "revenue_groups"},
                    {"Origin": "http://evil.invalid",
                     "Sec-Fetch-Site": "same-origin",
                     "X-VIA-CSRF": "http-test-token"})
                preflight = request("OPTIONS", "/run")
                bad_schema = request(
                    "POST", "/run", {"task": "revenue_groups", "extra": 1},
                    secure_headers)
                run_code, _, run_body = request(
                    "POST", "/run", {"task": "revenue_groups"}, secure_headers)
                run_json = json.loads(run_body)
                status_code, _, status_body = request("GET", "/status")
                status_json = json.loads(status_body)
                busy_code, _, busy_body = request(
                    "POST", "/run", {"task": "std_dashboard"}, secure_headers)
                busy_json = json.loads(busy_body)
                fake_processes[-1].rc = 0
                request("GET", "/status")
                intake_code, _, intake_body = request(
                    "POST", "/intake",
                    {"name": "http.txt",
                     "b64": base64.b64encode(b"http-safe").decode("ascii")},
                    secure_headers)
                intake_json = json.loads(intake_body)
                intake_repeat = request(
                    "POST", "/intake",
                    {"name": "http.txt",
                     "b64": base64.b64encode(b"http-safe").decode("ascii")},
                    secure_headers)
                reserved_http = request(
                    "POST", "/intake",
                    {"name": "COM¹.txt",
                     "b64": base64.b64encode(b"reject").decode("ascii")},
                    secure_headers)
                os.link = links_unsupported
                try:
                    link_failure_http = request(
                        "POST", "/intake",
                        {"name": "http-link-fail.txt",
                         "b64": base64.b64encode(b"reject").decode("ascii")},
                        secure_headers)
                finally:
                    os.link = real_link
                link_failure_json = json.loads(link_failure_http[2])
                vap_code, _, vap_body = request(
                    "POST", "/vap_kline", {"code": "2330", "months": 6},
                    secure_headers)
                vap_json = json.loads(vap_body)
                plotly_code, plotly_headers, _ = request(
                    "GET", "/VIA_UI_StdDashboard_v0100.html")
                # 批333:/VIA_UI_*.html 同源靜態白名單=在夾檔 200;不存在/越夾=404
                arbitrary_code = request(
                    "GET", "/VIA_UI_NotInFolder_v9999.html")[0]
                traversal_code = request("GET", "/VIA_UI_..%2F..%2Fx.html")[0]

                chk("⑩ /master 同源供應、注入 token 且送安全 header",
                    master_code == 200
                    and b'<meta name="via-csrf" content="http-test-token">' in master_body
                    and "access-control-allow-origin" not in master_headers
                    and "content-security-policy" in master_headers
                    and master_headers.get("x-frame-options") == "DENY")
                chk("⑪ 六個副作用 GET 全數 405；跨站/無 token/預檢全拒",
                    blocked_codes == [405] * len(BLOCKED_MUTATION_GETS)
                    and no_token[0] == 403 and wrong_origin[0] == 403
                    and preflight[0] == 403 and bad_schema[0] == 400)
                chk("⑫ POST /run=202、固定 schema、run_id 串接 /status、忙碌=409",
                    run_code == 202 and run_json.get("ok") is True
                    and set(run_json) == {"ok", "run_id", "accepted_params"}
                    and run_json["accepted_params"] == accepted
                    and status_code == 200
                    and status_json["revenue_groups"]["run_id"] == run_json["run_id"]
                    and busy_code == 409
                    and set(busy_json) <= {"ok", "run_id", "accepted_params", "err"})
                chk("⑬ 安全 POST 收件與 VAP 分析真走 mock、零外網",
                    intake_code == 201 and intake_json.get("ok") is True
                    and intake_repeat[0] == 200
                    and vap_code == 200 and vap_json == {
                        "lane": "mock", "code": "2330", "months": 6})
                chk("⑬b HTTP 收件保留名=400；原子發布失敗=500 JSON 不斷線",
                    reserved_http[0] == 400
                    and json.loads(reserved_http[2]).get("ok") is False
                    and link_failure_http[0] == 500
                    and link_failure_json.get("ok") is False
                    and isinstance(link_failure_json.get("err"), str)
                    and not (server.intake_root / "http-link-fail.txt").exists())
                expected_plotly = (200 if (UI_ROOT /
                                   "VIA_UI_StdDashboard_v0100.html").is_file()
                                   else 404)
                chk("⑭ Plotly 精確檔名可讀+iframe 安全 header;靜態白名單外/越夾=404(批333)",
                    plotly_code == expected_plotly
                    and plotly_headers.get("x-frame-options") == "SAMEORIGIN"
                    and "content-security-policy" in plotly_headers
                    and arbitrary_code == 404 and traversal_code == 404)
            finally:
                if thread is not None and thread.is_alive():
                    server.shutdown()
                server.server_close()
                if thread is not None:
                    thread.join(timeout=5)

            src = Path(__file__).read_text(encoding="utf-8")
            chk("⑮ 無 wildcard CORS、僅 loopback、排隊誠實且 import 不重複加路徑",
                ("Access-Control-" + "Allow-Origin") not in src
                and '("127.0.0.1", PORT)' in src
                and 'r2.get("kind") != "busy"' in src
                and "_sa_support not in _sa_sys.path" in src)
    except Exception as exc:
        print(f"  [FAIL] 自測框架例外 {type(exc).__name__}: {exc}")
        fails.append("自測框架例外")
    finally:
        for run in _runs.values():
            try:
                run.get("lf").close()
            except Exception:
                pass
        with _lock:
            _runs.clear()
            _runs.update(old_runs)
            _sync_execution = old_sync
        LOGDIR = old_logdir
        subprocess.Popen = old_popen
        _VAP["m"] = old_vap

    chk("⑳ 批333 標準系統 U/I 讀道(/api/<subject>→MDL119 尾版;/system 注入;同源靜態頁白名單+越夾守衛)",
        '"/api/"' in src and '"/system"' in src and '"/probe"' in src
        and bool(sysapi_mod()) and sysapi_mod().api("subjects").get("state") == "OK"
        and len(sysapi_mod().api("subjects").get("subjects", [])) >= 6
        and all(isinstance(x, (str, dict)) for x in sysapi_mod().api("subjects").get("subjects", []))
        and _static_ui_path("/VIA_UI_Shell_CGC_v0100.html") is not None
        and _static_ui_path("/VIA_UI_../x.html") is None
        and _static_ui_path("/etc/passwd") is None
        and _static_ui_path("/VIA_UI_System_v0100.html") is not None)
    chk("㉑ 批339 收件目的地冊(dest 二值放行·非法 400·vrn_incoming 根=VRN/input/incoming·缺 dest=既有根)",
        INTAKE_DESTS == {"downloads", "vrn_incoming"}
        and _intake_root_for("vrn_incoming") == VIA / "functional modules" / "VRN" / "input" / "incoming"
        and _intake_root_for("", "/x/y") == Path("/x/y")
        and _intake_root_for("downloads", None) is None
        and _strict_body({"name": "a.pdf", "b64": "QQ==", "dest": "vrn_incoming"}, {"name", "b64", "dest"}, {"name", "b64"}) is None
        and _strict_body({"name": "a.pdf", "b64": "QQ==", "path": "../x"}, {"name", "b64", "dest"}, {"name", "b64"}) is not None
        and '"dest 不在收件目的地冊' in src
        and _public_intake_result({"ok": True, "dest": "vrn_incoming", "x": 1}) == {"ok": True, "dest": "vrn_incoming"})
    chk("㉒ 批342 寫回斷線三類全吞(BrokenPipe/ConnectionReset/ConnectionAborted=WinError 10053)",
        len(re.findall(r"^\s*except \(BrokenPipeError, ConnectionResetError, ConnectionAbortedError\):", src, re.M)) == 3
        and len(re.findall(r"^\s*except \(BrokenPipeError, ConnectionResetError\):", src, re.M)) == 0)
    print(f"  [計] 安全橋自測 {n_chk[0]} 項 · OK {n_chk[0] - len(fails)}"
          f" · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        print("=== 指揮台本地執行橋(CGC_MDL095 v0114)· 安全橋自測(零外網)===")
        return selftest()
    if "serve" in sys.argv[1:]:
        return serve()
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
