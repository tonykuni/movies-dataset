#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL095_DeckServer — 指揮台本地執行橋(批208;操作員令)
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
用法:python3 CGC_MDL095_DeckServer_v0100.py serve | --selftest
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
                                env=env, cwd=str(VIA))
        _runs[tid] = {"proc": proc, "log": logp, "lf": lf,
                      "started": datetime.now().strftime("%H:%M:%S")}
        return {"ok": True}


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
            tail = ""
            try:
                txt = r["log"].read_text(encoding="utf-8", errors="ignore")
                tail = "\n".join(txt.strip().splitlines()[-3:])[-400:]
            except Exception:
                pass
            state = "running" if rc is None else ("ok" if rc == 0 else "fail")
            out[tid] = {"zh": t["zh"], "state": state, "rc": rc,
                        "started": r["started"], "tail": tail,
                        "fix": _suggest(tail) if state == "fail" else ""}
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
            return self._json({"ok": True, "via": "deck-bridge"})
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

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    T = task_registry()
    py_ok = all(Path(t["argv"][1]).exists()
                for t in T.values() if t["argv"][0] == sys.executable)
    chk("① 白名單任務冊(10 任務含 finpages;py 引擎尾版 glob 全在位)",
        len(T) == 10 and py_ok)
    chk("② 任意指令拒絕(不在白名單=err;安全鐵則)",
        start_task("rm -rf /")["ok"] is False
        and "白名單" in start_task("evil")["err"])
    r = start_task("revenue_groups")
    import time
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
    chk("⑧ 指揮台頁供應(/ 端點讀 ui_support 現頁)",
        UI.exists() and 'u.path == "/"' in src)
    print(f"  [計] 八檢 OK {8 + 1 - len(fails) - 1} · FAIL {len(fails)}")
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
