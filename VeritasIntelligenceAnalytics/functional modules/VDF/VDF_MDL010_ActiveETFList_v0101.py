#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_MDL010_ActiveETFList v0101 — 薄尾(v0100 一字不改):主動式台股 ETF 抓不到每日持股 = 不符合(V8)

操作員 2026-11-15 令:「主動式台股ETF若無法抓取每日持股資訊就代表不符合」(VDF-REQ026)。
本版只加一條判定,清單本身(列 · 欄 · DuckDB 表 tw_active_etf_list)照 v0100,不加欄、不刪列:
  證據  ENG051(主動 ETF 每日持股引擎)自己的擷取紀錄 fetch_status —— 每檔每輪一列(PASS / FAIL · 持股檔數 · 持股日 · 錯誤)。
        先讀它匯出的 <ETF 根>/active_tw_etf_holdings/parquet/fetch_status_latest.parquet,沒有才唯讀開 ActiveTWETF.duckdb。
        ETF 根照 ENG051 同一順序:VIA_ACTIVE_TW_ETF_ROOT → VIA_ROOT/functional modules/VDF/output_hub/active_tw_etf → 本夾 output_hub/active_tw_etf。
  窗    只看「最新一輪」ENG051(紀錄裡最晚的擷取日)—— 每跑一輪自動往前滾,不寫死天數。
  判定  最新一輪 PASS 且持股 > 0                         → 符合(daily_holdings OK)
        最新一輪 FAIL 或持股 0                           → 不符合:無法抓取每日持股(附 ENG051 的錯誤)
        最新一輪沒有它 · 國外成分(不須每日揭露)         → 不符合:不揭露每日持股 → 抓不到
        最新一輪沒有它 · 國內 / 類型未知                 → 未判(不猜;黃)
  V8    不符合不是錯(燈不因它紅);有未判 = YELLOW;全判完 = GREEN。明細(符合 / 不符合 + 原因 / 未判)寫進 verify_report.json 的 V8。
  輸出  <輸出根>/0-2-ActiveETFList/active_etf_qualified_latest.csv · active_etf_qualified_<日>.csv(清單每檔一列 + 判定欄);
        清單驗證紅(沒寫清單)就不寫。
  qualify  不連網:讀既有清單 + 目前的 ENG051 紀錄重判(ENG051 當天抓完再跑,判定跟上當天)。
入口同 v0100(VDF System Manager 總控 VIA_FROM_VDFSM=YES 或 VCGC)。動詞:run [--date] | status | qualify | --selftest。不碰 TA-Lib;同意閘不讀不寫。
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

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
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
    """統包唯一網路工具惰性載入(法遵雙閘在工具裡);缺席回 None(誠實)。本版的清單擷取照 v0100 走它。"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====
import csv
import importlib.util
import json
import os
import re
import sys
from contextlib import contextmanager
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_MDL010_ActiveETFList"
TAG = _STEM + " v" + Path(__file__).stem.rsplit("_v", 1)[-1]


def _vnum_v0101(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0101(p) < _vnum_v0101(__file__)), key=_vnum_v0101)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
for _n, _v in vars(PRIOR).items():                     # 前版公開名稱全數轉接(TAILAPI)
    if not _n.startswith("__") and _n not in globals():
        globals()[_n] = _v


def __getattr__(name):
    """前版公開名稱(collect · ETF_BOOK_URL …)一律轉接到 v0100。"""
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


CORE, OUT_DIR, STEM = PRIOR.CORE, PRIOR.OUT_DIR, PRIOR.STEM
_VERIFY_V0100, _RUN_V0100, _MAIN_V0100, _TAG_V0100 = PRIOR.verify, PRIOR.run, PRIOR.main, PRIOR.TAG

QUAL_STEM = "active_etf_qualified"
EVIDENCE_PARQUET = Path("active_tw_etf_holdings") / "parquet" / "fetch_status_latest.parquet"
EVIDENCE_DB = Path("active_tw_etf_holdings") / "ActiveTWETF.duckdb"
QUAL_COLS = ("date", "ticker", "name", "domestic", "daily_holdings", "holdings_date", "holding_count", "evidence_run", "qualified", "reason")
_EVIDENCE_ROOT_OVERRIDE: list = []                     # 自測用(不寫環境)


def evidence_roots() -> list:
    """ETF 根候選(照 ENG051 _default_root 的順序)。擷取系統子行程會把「… / "output_hub"」歸位到 --home(那一個也收),
    倉內真正的 output_hub 用 joinpath 寫(不被歸位)—— 兩處都看,誰的 ENG051 紀錄最新用誰。"""
    if _EVIDENCE_ROOT_OVERRIDE:                         # 自測:只看沙盒(工作站上真的 ENG051 紀錄不混進來)
        return list(_EVIDENCE_ROOT_OVERRIDE)
    out = []
    if os.environ.get("VIA_ACTIVE_TW_ETF_ROOT"):
        out.append(Path(os.environ["VIA_ACTIVE_TW_ETF_ROOT"]))
    if os.environ.get("VIA_ROOT"):
        out.append(Path(os.environ["VIA_ROOT"]).joinpath("functional modules", "VDF", "output_hub", "active_tw_etf"))
    out.append(HERE.joinpath("output_hub", "active_tw_etf"))
    out.append(HERE / "output_hub" / "active_tw_etf")   # 擷取系統子行程裡 = <--home>/output_hub/active_tw_etf
    out.append(Path.home().joinpath("Downloads", "VeritasIntelligenceAnalytics", "data"))   # ENG051 最後退路(沒 VIA_ROOT 時)
    seen, uniq = set(), []
    for p in out:
        k = str(Path(p))
        if k not in seen:
            seen.add(k)
            uniq.append(Path(p))
    return uniq


def _iso(v) -> str:
    s = "" if v is None else str(v)
    return "" if s in ("NaT", "nan", "None") else s[:19].replace("T", " ")


def _norm_rows(records: list) -> dict:
    by = {}
    for r in records:
        t = str(r.get("etf_ticker") or "").strip().upper()
        if not t:
            continue
        cur = {"status": str(r.get("status") or "").strip().upper(), "holding_count": r.get("holding_count"),
               "portfolio_date": _iso(r.get("portfolio_date"))[:10], "run_at": _iso(r.get("run_at")), "errors": str(r.get("errors") or "")[:160]}
        if t not in by or cur["run_at"] > by[t]["run_at"]:
            by[t] = cur
    return by


def _evidence_at(root: Path):
    """一個 ETF 根 → (rows, source) / None(沒有紀錄);讀壞丟例外(由呼叫端照實記)。"""
    pq, db = root / EVIDENCE_PARQUET, root / EVIDENCE_DB
    if pq.is_file():
        import pandas as pd
        return _norm_rows(pd.read_parquet(pq).to_dict("records")), pq
    if db.is_file():
        import duckdb
        con = duckdb.connect(str(db), read_only=True)
        try:
            cur = con.execute("SELECT run_at, etf_ticker, status, holding_count, portfolio_date, errors FROM fetch_status")
            names = [d[0] for d in cur.description]
            return _norm_rows([dict(zip(names, x)) for x in cur.fetchall()]), db
        finally:
            con.close()
    return None


def load_evidence(roots: list | None = None) -> dict:
    """ENG051 最新擷取紀錄 → {source, latest_run, rows{ticker: …}, error}。多個根都有 → 取最新一輪的那個。
    讀不到 = rows 空 + 照實寫原因(不擋清單)。"""
    tried, errs, best = [], [], None
    for root in (evidence_roots() if roots is None else [Path(r) for r in roots]):
        try:
            got = _evidence_at(root)
        except Exception as exc:  # noqa: BLE001 — 一處讀壞不擋別處:照實記
            errs.append("%s: %s: %s" % (root, type(exc).__name__, str(exc)[:120]))
            continue
        if got is None:
            tried.append(str(root))
            continue
        rows, src = got
        latest = max((r["run_at"] for r in rows.values()), default="")
        if best is None or latest > best["latest_run"]:
            best = {"source": str(src), "latest_run": latest, "rows": rows, "error": None}
    if best is not None:
        if errs:
            best["error"] = "另有讀不了的紀錄:" + " · ".join(errs)[:200]
        return best
    why = ("讀不了 ENG051 紀錄:" + " · ".join(errs)[:200]) if errs else "沒有 ENG051 擷取紀錄(試過 %s)" % " · ".join(tried[:4])
    return {"source": None, "latest_run": "", "rows": {}, "error": why}


def qualify(rows: list, ev: dict) -> list:
    """清單每檔 → 判定列(qualified True / False / None + 原因)。"""
    last_day = (ev.get("latest_run") or "")[:10]
    out = []
    for r in rows:
        t = str(r.get("ticker") or "").strip().upper()
        dom = r.get("domestic")
        if dom is None or str(dom).strip() in ("", "None", "nan", "NaN"):
            dom = None                                 # 類型未知(含 parquet 讀回的空值)= None,不當成國外
        elif not isinstance(dom, bool):
            dom = str(dom).strip().lower() == "true"
        e = ev["rows"].get(t)
        q = {"date": r.get("date") or "", "ticker": t, "name": r.get("name") or "", "domestic": dom, "daily_holdings": None,
             "holdings_date": (e or {}).get("portfolio_date", ""), "holding_count": (e or {}).get("holding_count"),
             "evidence_run": (e or {}).get("run_at", ""), "qualified": None, "reason": ""}
        try:
            n_hold = int(float(q["holding_count"])) if q["holding_count"] not in (None, "") else 0
        except (TypeError, ValueError):
            n_hold = 0
        in_last = bool(e) and last_day and e["run_at"][:10] == last_day
        if in_last and e["status"] == "PASS" and n_hold > 0:
            q.update(daily_holdings="OK", qualified=True, reason="最新一輪抓到每日持股 %d 檔(持股日 %s)" % (n_hold, q["holdings_date"] or "—"))
        elif in_last:
            q.update(daily_holdings="FAIL", qualified=False,
                     reason="無法抓取每日持股(ENG051 %s · %s · 持股 %d%s)" % (e["run_at"][:16], e["status"] or "—", n_hold,
                                                                     (" · " + e["errors"][:80]) if e["errors"] else ""))
        elif dom is False:
            q.update(daily_holdings="NO_DAILY_DISCLOSURE", qualified=False, reason="國外成分:不須每日揭露持股 → 抓不到每日持股")
        elif e:
            q.update(reason="未判:最新一輪 ENG051(%s)沒有它的紀錄(上次 %s · %s)" % (last_day, e["run_at"][:10], e["status"] or "—"))
        else:
            q.update(reason="未判:" + (ev.get("error") or "沒有 ENG051 擷取紀錄"))
        out.append(q)
    return out


def check_v8(q: list, ev: dict) -> dict:
    yes = [x["ticker"] for x in q if x["qualified"] is True]
    no = [{"ticker": x["ticker"], "reason": x["reason"]} for x in q if x["qualified"] is False]
    und = [{"ticker": x["ticker"], "reason": x["reason"]} for x in q if x["qualified"] is None]
    return {"id": "V8", "name": "每日持股抓得到(抓不到 = 不符合;VDF-REQ026)", "lamp": "YELLOW" if und else "GREEN",
            "note": "符合 %d · 不符合 %d · 未判 %d · 證據 %s(最新一輪 %s)%s" % (
                len(yes), len(no), len(und), Path(ev["source"]).name if ev.get("source") else "—", ev.get("latest_run") or "—",
                (" · " + ev["error"]) if ev.get("error") else ""),
            "qualified": yes, "not_qualified": no, "undetermined": und, "evidence": ev.get("source")}


_LAST: dict = {}


def verify(rows, rejected, states, prev, day) -> dict:
    """v0100 七檢 + V8(每日持股抓得到)。"""
    v = _VERIFY_V0100(rows, rejected, states, prev, day)
    ev = load_evidence()
    q = qualify(rows, ev)
    v["checks"].append(check_v8(q, ev))
    v["lamp"] = CORE.lamp_v0100(v["checks"])
    _LAST.update(q=q, ev=ev)
    return v


def write_qualified(out_root: Path, day: str, q: list) -> dict:
    d = Path(out_root) / OUT_DIR
    d.mkdir(parents=True, exist_ok=True)
    for name in (f"{QUAL_STEM}_latest.csv", f"{QUAL_STEM}_{day}.csv"):
        with open(d / name, "w", encoding="utf-8-sig", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(QUAL_COLS))
            w.writeheader()
            for x in q:
                w.writerow({k: ("" if x.get(k) is None else x.get(k)) for k in QUAL_COLS})
    return {"file": f"{QUAL_STEM}_latest.csv", "rows": len(q), "qualified": sum(x["qualified"] is True for x in q),
            "not_qualified": sum(x["qualified"] is False for x in q), "undetermined": sum(x["qualified"] is None for x in q)}


_VIA_NET_V0100 = PRIOR._via_net


def _forward_via_net_v0101():
    """v0100 的 collect 叫的網路入口 → 轉到本檔此刻的 _via_net(擷取系統 fixture / 總控換的是本檔模組全域的那個)。"""
    return globals()["_via_net"]()


@contextmanager
def _installed():
    """一次 run 期間:v0100 的 run 叫的 verify = 本版(多 V8)· 網路入口轉到本檔 · 報告記本版。結束還原(v0100 自測看它自己的狀態)。"""
    PRIOR.verify, PRIOR.TAG, PRIOR._via_net = verify, TAG, _forward_via_net_v0101
    try:
        yield
    finally:
        PRIOR.verify, PRIOR.TAG, PRIOR._via_net = _VERIFY_V0100, _TAG_V0100, _VIA_NET_V0100


def run(day: str | None = None, out_root: Path | None = None) -> dict:
    day = day or date.today().isoformat()
    out_root = Path(out_root or Path.cwd())
    _LAST.clear()
    with _installed():
        rep = _RUN_V0100(day, out_root)
    if (rep.get("write") or {}).get("written") and _LAST.get("q") is not None:
        rep["qualify"] = write_qualified(out_root, day, _LAST["q"])
    else:
        rep["qualify"] = {"file": None, "why": "清單沒寫(驗證紅或沒資料)→ 判定不另寫檔(V8 明細仍在 verify_report.json)"}
    return rep


def qualify_only(out_root: Path | None = None) -> dict:
    """不連網重判:既有清單 + 目前 ENG051 紀錄 → 判定檔(清單不動)。"""
    out_root = Path(out_root or Path.cwd())
    rows = CORE.load_previous_v0100(out_root, OUT_DIR, STEM)
    if not rows:
        return {"rows": 0, "why": "還沒有清單(先 run)"}
    ev = load_evidence()
    q = qualify(rows, ev)
    day = str(rows[0].get("date") or date.today().isoformat())[:10]
    res = write_qualified(out_root, day, q)
    res["v8"] = check_v8(q, ev)
    return res


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"]:
        return selftest()
    if args[:1] == ["qualify"]:
        if not CORE.entry_ok_v0100():
            print("[VDF_MDL010] 拒絕。由 VDF System Manager 總控(VIA_FROM_VDFSM=YES)")
            return 2
        res = qualify_only()
        if not res.get("rows"):
            print("[%s] qualify · %s" % (TAG, res.get("why")))
            return 2
        v8 = res["v8"]
        print("[%s] qualify · %s · %s" % (TAG, v8["lamp"], v8["note"]))
        for x in v8["not_qualified"]:
            print("  [不符合] %s · %s" % (x["ticker"], x["reason"]))
        for x in v8["undetermined"]:
            print("  [未判] %s · %s" % (x["ticker"], x["reason"]))
        return 0
    keep = PRIOR.run
    PRIOR.run = run                                    # v0100 main 的 run / status / 回傳碼規則照用,run 換成本版
    try:
        return _MAIN_V0100(args)
    finally:
        PRIOR.run = keep


# ---------------------------------------------------------------- 自測(假網路工具 · 假 ENG051 紀錄 · 暫存輸出根 · 零外呼)
def selftest() -> int:
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)[:300]) if note and not cond else ''}")

    print(f"=== {TAG} · 自測(抓不到每日持股 = 不符合;假網路 · 假 ENG051 紀錄 · 零外呼)===")
    import pandas as pd
    ev_rows = [
        {"run_at": "2026-11-14 18:00:01", "etf_ticker": "00981A", "status": "PASS", "source_type": "TWSE", "holding_count": 52, "portfolio_date": "2026-11-14", "errors": ""},
        {"run_at": "2026-11-14 18:00:03", "etf_ticker": "00980A", "status": "FAIL", "source_type": "TWSE", "holding_count": 0, "portfolio_date": None, "errors": "HTTP 404"},
        {"run_at": "2026-11-14 18:00:05", "etf_ticker": "00984A", "status": "PASS", "source_type": "TWSE", "holding_count": 0, "portfolio_date": "2026-11-14", "errors": ""},
        {"run_at": "2026-11-10 18:00:00", "etf_ticker": "00985A", "status": "PASS", "source_type": "TWSE", "holding_count": 40, "portfolio_date": "2026-11-10", "errors": ""},
        {"run_at": "2026-11-13 18:00:00", "etf_ticker": "00981A", "status": "FAIL", "source_type": "TWSE", "holding_count": 0, "portfolio_date": None, "errors": "old"},
    ]
    lst = [{"date": "2026-11-15", "ticker": t, "name": n, "domestic": d} for t, n, d in (
        ("00981A", "主動統一台股增長", True), ("00980A", "主動野村臺灣優選", True), ("00402A", "主動安聯美國科技", False),
        ("00984A", "主動甲", True), ("00985A", "主動乙", True), ("00988A", "主動丙", None))]
    ev = {"source": "x.parquet", "latest_run": "2026-11-14 18:00:05", "rows": _norm_rows(ev_rows), "error": None}
    q = {x["ticker"]: x for x in qualify(lst, ev)}
    chk("① 判定:最新一輪 PASS 且有持股 = 符合 · FAIL / 持股 0 = 不符合(附錯誤)· 國外成分 = 不符合 · 最新一輪沒抓 / 沒紀錄 = 未判(不猜)· 同檔取最新一列",
        q["00981A"]["qualified"] is True and q["00981A"]["daily_holdings"] == "OK"
        and q["00980A"]["qualified"] is False and "無法抓取每日持股" in q["00980A"]["reason"] and "HTTP 404" in q["00980A"]["reason"]
        and q["00984A"]["qualified"] is False and q["00402A"]["qualified"] is False and q["00402A"]["daily_holdings"] == "NO_DAILY_DISCLOSURE"
        and q["00985A"]["qualified"] is None and "最新一輪" in q["00985A"]["reason"] and q["00988A"]["qualified"] is None, q)
    v8 = check_v8(list(q.values()), ev)
    v8b = check_v8([x for x in q.values() if x["qualified"] is not None], ev)
    chk("② V8 燈:有未判 = YELLOW · 全判完 = GREEN(不符合不是錯,燈不因它紅)· 明細三組",
        v8["lamp"] == "YELLOW" and v8b["lamp"] == "GREEN" and len(v8["qualified"]) == 1 and len(v8["not_qualified"]) == 3
        and len(v8["undetermined"]) == 2, v8["note"])
    book = [{"基金代號": c, "基金簡稱": n, "基金類型": t, "出表日期": "1151114"} for c, n, t in (
        ("00981A", "主動統一台股增長", "國內成分證券主動式交易所交易基金(股票)"), ("00980A", "主動野村臺灣優選", "國內成分證券主動式交易所交易基金(股票)"),
        ("00402A", "主動安聯美國科技", "國外成分證券主動式交易所交易基金(股票)"), ("0050", "元大台灣50", "國內成分證券指數股票型基金"))]

    class _Net:
        def http_json(self, url, timeout=30):
            return {"state": "OK", "data": book} if url == PRIOR.ETF_BOOK_URL else {"state": "FAIL", "note": "no route"}
    keep_net = globals()["_via_net"]
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        etf_root = root / "etf_root"
        (etf_root / EVIDENCE_PARQUET).parent.mkdir(parents=True)
        pd.DataFrame(ev_rows).to_parquet(etf_root / EVIDENCE_PARQUET, index=False)
        _EVIDENCE_ROOT_OVERRIDE[:] = [etf_root]
        try:
            globals()["_via_net"] = lambda: _Net()       # 跟擷取系統 fixture 一樣換本檔模組全域的入口
            rep = run("2026-11-15", root / "out")
            d = root / "out" / OUT_DIR
            vr = json.loads((d / "verify_report.json").read_text(encoding="utf-8"))
            v8r = next((c for c in vr["checks"] if c["id"] == "V8"), {})
            lst_df = pd.read_parquet(d / f"{STEM}_latest.parquet")
            qdf = pd.read_csv(d / f"{QUAL_STEM}_latest.csv", encoding="utf-8-sig", dtype=str).fillna("")
            chk("③ 一輪:清單 3 檔照 v0100(欄不變 · 不加判定欄)· verify_report 多 V8(明細在)· 判定檔 3 列:00981A 符合 · 00980A / 00402A 不符合 · 報告記本版",
                rep["count"] == 3 and rep["engine"] == TAG and v8r.get("qualified") == ["00981A"]
                and sorted(x["ticker"] for x in v8r.get("not_qualified", [])) == ["00402A", "00980A"]
                and "qualified" not in lst_df.columns and list(lst_df.columns[:5]) == list(CORE.KEY_COLS)
                and dict(zip(qdf.ticker, qdf.qualified)) == {"00981A": "True", "00980A": "False", "00402A": "False"}
                and rep["qualify"]["not_qualified"] == 2, (rep.get("qualify"), v8r.get("note")))
            import duckdb
            con = duckdb.connect(str(root / "out" / "vdf_master_lists.duckdb"), read_only=True)
            cols = [r[0] for r in con.execute("DESCRIBE tw_active_etf_list").fetchall()]
            con.close()
            chk("④ DuckDB 清單表欄位照 v0100(判定不進表 · 前一輪的庫照樣能增量)", "qualified" not in cols and "ticker" in cols, cols)
            ev_rows[1].update(status="PASS", holding_count=48, portfolio_date="2026-11-14", run_at="2026-11-14 19:00:00")
            pd.DataFrame(ev_rows).to_parquet(etf_root / EVIDENCE_PARQUET, index=False)
            before = (d / f"{STEM}_latest.parquet").read_bytes()
            res = qualify_only(root / "out")
            qdf2 = pd.read_csv(d / f"{QUAL_STEM}_latest.csv", encoding="utf-8-sig", dtype=str).fillna("")
            chk("⑤ qualify(不連網):ENG051 當天補抓到 00980A → 改判符合;清單檔一個位元都沒動",
                dict(zip(qdf2.ticker, qdf2.qualified)).get("00980A") == "True" and res["qualified"] == 2
                and (d / f"{STEM}_latest.parquet").read_bytes() == before, res)
            (etf_root / EVIDENCE_PARQUET).unlink()
            con = duckdb.connect(str(etf_root / EVIDENCE_DB))
            con.execute("CREATE TABLE fetch_status (run_at TIMESTAMP, etf_ticker VARCHAR, status VARCHAR, source_type VARCHAR,"
                        " holding_count BIGINT, portfolio_date DATE, errors VARCHAR)")
            con.execute("INSERT INTO fetch_status VALUES ('2026-11-14 18:00:01','00981A','PASS','TWSE',52,'2026-11-14','')")
            con.close()
            ev_db = load_evidence()
            chk("⑥ 沒匯出檔 → 唯讀開 ENG051 庫的 fetch_status", ev_db["source"].endswith("ActiveTWETF.duckdb") and ev_db["rows"].get("00981A", {}).get("status") == "PASS",
                ev_db)
            other = root / "etf_other"
            (other / EVIDENCE_PARQUET).parent.mkdir(parents=True)
            pd.DataFrame([dict(ev_rows[0], run_at="2026-11-15 18:00:00", status="FAIL", holding_count=0, errors="newer")]).to_parquet(
                other / EVIDENCE_PARQUET, index=False)
            ev_two = load_evidence([etf_root, other, root / "nowhere"])
            chk("⑥b 兩個根都有紀錄(倉內 output_hub · 擷取家歸位)→ 用最新一輪那一個", ev_two["source"].startswith(str(other))
                and ev_two["latest_run"].startswith("2026-11-15"), ev_two.get("source"))
            ev_none = load_evidence([root / "nowhere"])
            qn = {x["ticker"]: x for x in qualify(lst[:3], ev_none)}
            chk("⑦ 沒有 ENG051 紀錄 → 國內 = 未判(黃 · 原因寫明)· 國外成分照樣不符合 · 不當機",
                qn["00981A"]["qualified"] is None and "沒有 ENG051" in qn["00981A"]["reason"] and qn["00402A"]["qualified"] is False
                and check_v8(list(qn.values()), ev_none)["lamp"] == "YELLOW", qn)
        finally:
            globals()["_via_net"] = keep_net
            _EVIDENCE_ROOT_OVERRIDE[:] = []
    chk("⑧ 換裝只在一輪裡:平時 v0100 的 verify / TAG / 網路入口是它自己的(前版自測照舊)",
        PRIOR.verify is _VERIFY_V0100 and PRIOR.TAG == _TAG_V0100 and PRIOR._via_net is _VIA_NET_V0100)
    text = Path(__file__).read_text(encoding="utf-8")
    body = text.split("def selftest", 1)[0]
    chk("⑨ 加速器橋 · 網路橋在;不碰 TA-Lib;同意閘不讀不寫;不匯入他系統程式;不寫環境",
        "[VIA:ACCEL-BRIDGE" in text and "[VIA:NET-BRIDGE" in text and not re.search(r"^\s*(import|from)\s+(talib|CGC_|VRN_|VCGC)", text, re.M)
        and "_CON" + "SENT" not in body and not re.search(r"os\.environ\[[^\]]*\]\s*=(?!=)|os\.environ\.(pop|setdefault|update)\(", body))
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}")
    if not all(ok):
        return 1
    if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1":
        return 0
    rc = PRIOR.selftest()
    print(f"  [計] {TAG} 前版鏈 rc {rc} · {'PASS' if rc == 0 else 'FAIL'}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
