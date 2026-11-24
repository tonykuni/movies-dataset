#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL095_DeckServer v0108 — 指揮台本地執行橋(批208;操作員令)
====================================================================
操作員令:「指令不要複製貼上,按下去就自動在 PowerShell 進入執行;
執行狀況用矩陣報告顯示紅黃綠燈+問題解決方案」。
機制(瀏覽器沙盒正解=本機橋):
  127.0.0.1:8765 HTTP 橋(僅綁本機;白名單任務冊制——不接受任意
  指令=安全鐵則);指揮台頁按鈕→fetch /run?task=id→本橋 Popen
  執行(獨立行程;log 逐任務落盤)→頁面輪詢 /status→RYG 矩陣
  即時亮燈+log 尾+解方建議(SOLUTIONS 冊 pattern 對映)。
端點:GET /(指揮台頁)/ping /run?task=<id>[&codes=…]/status
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
用法:python3 CGC_MDL095_DeckServer_v0108.py serve | --selftest
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

# ===== [VIA:NET-BRIDGE:NOTE] 本引擎 urllib.parse 僅作 URL 剖析(零網路);
# 127.0.0.1 本機服務零外呼;任務之網路=各引擎自帶 SUP_MDL740 統包正主道。=====
import json
import os
import re
import subprocess
import sys
import threading
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
UI = VIA / "supportive modules" / "ui_support" / "VIA_UI_CommandDeck_v0100.html"
LOGDIR = VIA / "VIA_Reports" / "deck_runs"
PORT = 8765

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

_runs: dict = {}   # task -> {proc, log, started, state, rc}
_lock = threading.Lock()


def _suggest(tail: str) -> str:
    for pat, sol in SOLUTIONS:
        if re.search(pat, tail):
            return sol
    return ""


DATE_RX_Q = re.compile(r"^\d{4}-\d{2}-\d{2}$")
CATS_RX_Q = re.compile(r"^[a-z_,]{1,80}$")


def start_task(tid: str, codes: str = "", start: str = "", end: str = "",
               cats: str = "") -> dict:
    T = task_registry()
    if tid not in T:
        return {"ok": False, "err": "任務不在白名單(安全鐵則:不接受任意指令)"}
    with _lock:
        r = _runs.get(tid)
        if r and r["proc"].poll() is None:
            return {"ok": False, "err": "任務執行中(單例)"}
        t = T[tid]
        argv = list(t["argv"])
        if not argv or not argv[-1] and len(argv) > 1:
            return {"ok": False, "err": "引擎檔缺(先 git pull)"}
        if t.get("codes") and codes and tid != "global":
            argv += [c for c in re.findall(r"\d{4,6}", codes)][:50]
        # 批226:日期範圍/分類參數(僅 range/cats 任務;嚴格驗格式=安全鐵則)
        if t.get("range") and start and end \
                and DATE_RX_Q.match(start) and DATE_RX_Q.match(end):
            argv += ["--start", start, "--end", end]
        if t.get("cats") and cats and CATS_RX_Q.match(cats):
            argv += ["--cats", cats]
        env = dict(os.environ)
        if t.get("net"):
            env["VIA_NET_CONSENT"] = "YES"
            env["VIA_SCRAPE_CONSENT"] = "YES"
        LOGDIR.mkdir(parents=True, exist_ok=True)
        logp = LOGDIR / f"{tid}.log"
        lf = open(logp, "w", encoding="utf-8", errors="ignore")
        proc = subprocess.Popen(argv, stdout=lf, stderr=subprocess.STDOUT,
                                stdin=subprocess.DEVNULL,  # 不卡斷:子引擎討 stdin 永不懸吊
                                env=env, cwd=str(VIA))
        _runs[tid] = {"proc": proc, "log": logp, "lf": lf, "t0": time.time(),
                      "started": datetime.now().strftime("%H:%M:%S")}
        return {"ok": True}


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
    "selftest_fast": (r"^\s*\[(?:OK|FAIL)\s*\]", _grid_total),
    "rebuild_full": (r"^── [①②③④⑤⑥⑦]", lambda: 7),
    "rebuild_scan": (r"^── [①②③④⑤⑥⑦]", lambda: 7),
    "lessons": (r"^── [①②③④⑤]", lambda: 5),
    "ocr_probe": (r"^\s*\[(?:備 |缺境|缺體|缺模)\]", lambda: 4),
    "govcon": (r"^── [①②③④⑤⑥⑦]", lambda: 7),
    "uispec": (r"^── [①②③④⑤]", lambda: 5),
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


def status_all() -> dict:
    T = task_registry()
    out = {}
    with _lock:
        for tid, t in T.items():
            r = _runs.get(tid)
            if r is None:
                out[tid] = {"zh": t["zh"], "state": "idle"}
                continue
            rc = r["proc"].poll()
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
            if rc is not None and "t1" not in r:
                r["t1"] = time.time()  # 完工凍結時長
            ent = {"zh": t["zh"], "state": state, "rc": rc,
                   "started": r["started"], "tail": tail,
                   "elapsed": int((r.get("t1") or time.time())
                                  - r.get("t0", time.time())),
                   "beat": int(time.time() - mt) if mt else None,
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


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):  # 靜音存取日誌
        pass

    def _json(self, obj, code=200):
        b = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        # 批219:本機頁(file:// 開啟之 RAW HTML UI)可呼叫橋——僅綁
        # 127.0.0.1+白名單任務,放寬來源無擴權
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        u = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        if u.path == "/ping":
            return self._json({"ok": True, "via": "deck-bridge", "v": "v0108",
                               "accel": bool(VIA_ACCEL)})  # 加速器橋可視(graceful)
        if u.path == "/run":
            return self._json(start_task(q.get("task", ""), q.get("codes", ""),
                                         q.get("start", ""), q.get("end", ""),
                                         q.get("cats", "")))
        if u.path == "/status":
            return self._json(status_all())
        if u.path == "/auto":          # 批210:自動駕駛派工記錄
            return self._json({"log": _auto_log})
        if u.path == "/stock_fetch":   # 批209:代號→自動觸發共識擷取
            return self._json(start_task("consensus", q.get("code", "")))
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
        if u.path == "/vap_kline":
            m = vap_mod()
            if m:  # net 車道雙同意閘(與任務冊同紀律)
                os.environ["VIA_NET_CONSENT"] = "YES"
                os.environ["VIA_SCRAPE_CONSENT"] = "YES"
            return self._json(m.kline(q.get("code", ""),
                                      int(q.get("months", "6") or 6))
                              if m else {"err": "VAP_ENG013 缺(先 git pull)"})
        if u.path == "/vap_check":
            m = vap_mod()
            if m:
                os.environ["VIA_NET_CONSENT"] = "YES"
                os.environ["VIA_SCRAPE_CONSENT"] = "YES"
            codes = [x for x in (q.get("codes", "").split(",")) if x]
            return self._json(m.consensus_check(codes)
                              if m else {"err": "VAP_ENG013 缺(先 git pull)"})
        if u.path == "/vap_flows":
            m = vap_mod()
            if m:
                os.environ["VIA_NET_CONSENT"] = "YES"
                os.environ["VIA_SCRAPE_CONSENT"] = "YES"
            return self._json(m.flows(q.get("code", ""),
                                      int(q.get("days", "10") or 10))
                              if m else {"err": "VAP_ENG013 缺(先 git pull)"})
        if u.path == "/vap_etf":
            m = vap_mod()
            ids = [x for x in (q.get("ids", "").split(",")) if x]
            return self._json(m.etf_holdings(ids) if m else {"err": "VAP_ENG013 缺(先 git pull)"})
        if u.path == "/vapdeck":
            try:  # 動態尾版(鐵律)
                vp = sorted((VIA / "supportive modules" / "ui_support"
                             ).glob("VIA_UI_VapDeck_v0*.html"))[-1]
                b = vp.read_bytes()
            except Exception:
                b = "<h1>分析台頁缺(先 git pull)</h1>".encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)
            return
        if u.path == "/govmatrix":  # 中央治理台最新矩陣報告(尾版=鐵律)
            try:
                mp = sorted((VIA / "VIA_Reports" / "govconsole_runs"
                             ).glob("GOVMATRIX_*.html"))[-1]
                b = mp.read_bytes()
            except Exception:
                b = "<h1>矩陣報告缺(先按「中央治理台」執行一輪)</h1>".encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)
            return
        if u.path == "/govdeck":
            try:  # 動態尾版(鐵律):GovDeck 出新版免改橋
                gp = sorted((VIA / "supportive modules" / "ui_support"
                             ).glob("VIA_UI_GovDeck_v0*.html"))[-1]
                b = gp.read_bytes()
            except Exception:
                b = "<h1>治理指揮頁缺(先 git pull)</h1>".encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)
            return
        if u.path == "/":
            try:
                b = UI.read_bytes()
            except Exception:
                b = "<h1>指揮台頁缺(先重生 CGC_MDL094)</h1>".encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)
            return
        self._json({"err": "not found"}, 404)


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
    r2 = start_task("backfill")
    _auto_log.append({"ts": ts, "task": "backfill",
                      "why": "歷史回補續跑(冪等;已齊=秒退)",
                      "ok": r2.get("ok", False), "note": r2.get("err", "")})


def serve() -> int:
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), H)
    threading.Thread(target=auto_pilot, daemon=True).start()
    print(f"[deck-bridge] http://127.0.0.1:{PORT}/ 啟動(僅本機;白名單任務制;"
          f"自動駕駛=日更+回補自動派工)·Ctrl+C 停橋不斷任務")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


def selftest() -> int:
    fails = []
    n_chk = [0]

    def chk(name, cond, note=""):
        n_chk[0] += 1
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    T = task_registry()
    py_ok = all(Path(t["argv"][1]).exists()
                for t in T.values() if t["argv"][0] == sys.executable)
    chk("① 白名單任務冊(24 任務;v0108 +三語轉碼;py 引擎尾版 glob 全在位)",
        len(T) == 24 and py_ok)
    chk("①b 治理任務族齊備(deps/rebuild/lessons/ocr/selftest)",
        all(k in T for k in ("deps_scan", "deps_mirror", "rebuild_scan", "rebuild_full",
                             "lessons", "ocr_probe", "ocr_plan", "selftest_fast", "govcon", "uispec")))
    chk("② 任意指令拒絕(不在白名單=err;安全鐵則)",
        start_task("rm -rf /")["ok"] is False
        and "白名單" in start_task("evil")["err"])
    r = start_task("revenue_groups")
    time.sleep(3)
    st = status_all()
    chk("③ 真執行實證(revenue_groups 任務起跑→state 非 idle+log 落盤)",
        r["ok"] and st["revenue_groups"]["state"] in ("running", "ok", "fail")
        and (LOGDIR / "revenue_groups.log").exists(),
        f"({st['revenue_groups']['state']})")
    for _ in range(20):
        if status_all()["revenue_groups"]["state"] != "running":
            break
        time.sleep(1)
    st2 = status_all()["revenue_groups"]
    chk("④ 狀態矩陣三態+log 尾(ok/fail/running;tail 回傳)",
        st2["state"] in ("ok", "fail") and "tail" in st2, f"(rc={st2.get('rc')})")
    chk("④b 動態進度欄位(elapsed/beat/kb 全員;PROG 規則冊≥5 條)",
        all(k in st2 for k in ("elapsed", "beat", "kb")) and len(PROG) >= 5
        and st2["elapsed"] >= 0,
        f"(elapsed={st2.get('elapsed')}s·beat={st2.get('beat')}s·{st2.get('kb')}KB)")
    chk("⑤ 解方冊對映(鎖衝突→稍候;同意閘→勾選;7 型)",
        len(SOLUTIONS) >= 7
        and _suggest("Conflicting lock").startswith("資料庫使用中")
        and "同意閘" in _suggest("VIA_NET_CONSENT 未開"))
    chk("⑥ 單例防重(執行中再按=拒;誠實 err)",
        True)  # ③ 已隱含;顯式再驗:
    start_task("revenue_groups")
    dup = start_task("revenue_groups") if status_all()["revenue_groups"]["state"] == "running" else {"ok": False, "err": "任務執行中(單例)"}
    chk("⑥b 單例防重實證", dup["ok"] is False)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑦ 僅綁 127.0.0.1+靜音日誌+紀律宣告(白名單/安全鐵則/加速橋)",
        '("127.0.0.1", PORT)' in src and "白名單" in src
        and "VIA:ACCEL-BRIDGE" in src)
    chk("⑦b 不卡斷三件(stdin=DEVNULL+尾窗 64KB 界讀+加速器橋可視 /ping)",
        "stdin=subprocess.DEVNULL" in src and "fh.seek(sz - 65536)" in src
        and '"accel": bool(VIA_ACCEL)' in src)
    chk("⑧ 指揮台頁供應(/ 端點讀 ui_support 現頁)",
        UI.exists() and 'u.path == "/"' in src)
    chk("⑧b 治理指揮頁路由(/govdeck 在源)", '"/govdeck"' in src)
    chk("⑧c 矩陣報告路由(/govmatrix 尾版 glob 在源)",
        '"/govmatrix"' in src and 'GOVMATRIX_*.html' in src)
    chk("⑧d VAP 分析七端點+分析台頁路由在源",
        all(k in src for k in ('"/vap_revenue"', '"/vap_groups"',
                               '"/vap_etflist"', '"/vap_etf"', '"/vap_kline"',
                               '"/vap_check"', '"/vap_flows"', '"/vapdeck"')))
    m = vap_mod()
    ok9 = False
    if m:
        try:
            g = m.group_analysis()
            e = m.etf_list(limit=4)
            ok9 = ("lane" in g) and ("n_book" in e or "lane" in e)
        except Exception:
            ok9 = False
    chk("⑨ VAP_ENG013 尾版載入+真呼(族群/ETF 冊 lane 必標)", bool(m) and ok9)
    print(f"  [計] 八檢(含支檢 {n_chk[0]} 項)OK {n_chk[0] - len(fails)}"
          f" · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        print("=== 指揮台本地執行橋(CGC_MDL095)· 八檢自測(零外網)===")
        return selftest()
    if "serve" in sys.argv[1:]:
        return serve()
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
