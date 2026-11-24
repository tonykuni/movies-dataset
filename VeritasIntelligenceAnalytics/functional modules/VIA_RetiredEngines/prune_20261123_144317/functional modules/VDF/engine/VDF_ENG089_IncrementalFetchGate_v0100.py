#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
VDF_ENG089_IncrementalFetchGate v0100 — 增量擷取閘(批569)

操作員令(批569):「VDF 自2023年後到最新的資料庫增量擷取,**不要重複 BATCH FETCHING**」。
同一句話操作員在批383 就說過一次:「抓過的資料不必再抓」。說第二次=**還在重抓**。

【這一批只做第一步:把真相攤開,零改線(L61)】
  不改任何現役擷取引擎的行為。本閘只回答三個問題,答完操作員才決定誰改:
    ① 庫裡**已經有什麼**(每張表的日期涵蓋)
    ② 從 2023-01-01 到最新,**真正缺的是哪幾段**(只列缺口,不列已有)
    ③ 哪幾支擷取引擎**抓之前沒看庫**(那就是重抓的來源)

【誠實四態】
  0=GREEN(算得出缺口,或本來就沒缺口)· 1=RED(壞了)
  · 2=NODATA(庫在但空/沒有日期欄,算不出水位——不是紅燈)
  · 3=ABSENT(目錄或庫不在;附上要先跑哪一句)

【紀律】
  · **零網路**:本閘一個位元組都不抓,只讀庫與目錄。
  · **零寫入**:不建表、不寫庫、不改任何擷取引擎。沒有 --apply。
  · **不代設同意閘**:要真的去抓是操作員的手。
  · **零九頭龍**:庫的清點**複用 CGC_MDL123 資料家 catalog**,本閘不自己再寫一份掃庫。

用法:
  via-vdfinc scan                     每張表的水位(列/日期欄/最早/最新)
  via-vdfinc plan  [--since 2023-01-01] [--until YYYY-MM-DD]
                                      只列缺口:頭段缺、尾段缺;有庫可讀時 --deep 逐日反連結
  via-vdfinc plan --deep              逐日反連結(真正的「不要重抓」清單;要庫讀得到)
  via-vdfinc audit                    哪幾支尾版擷取引擎抓之前沒看庫
  via-vdfinc --selftest
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
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
import argparse
import ast
import json
import os
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent.parent
VERSION = Path(__file__).stem.rsplit("_v", 1)[-1]
REPORTS = VIA / "VIA_Reports" / "vdf" / "incremental"
CATALOG = VIA / "VIA_Reports" / "datahome" / "DATAHOME_CATALOG_latest.json"
DEFAULT_SINCE = "2023-01-01"        # 操作員令:自 2023 年後
ENGINE_DIR = VIA / "functional modules" / "VDF" / "engine"

# 抓網的正典口(L:網路只認 AegisNexus,740 留作橋)
NET_MARKS = ("SUP_MDL740", "AegisNexus", "NetUnified", "net_unified")
# 「抓之前有看庫」的證據:水位查詢 / 反連結 / checkpoint
WATERMARK_MARKS = (
    r"max\s*\(\s*[\"'`]?\w*date", r"MAX\s*\(", r"watermark", r"高水位", r"last_date",
    r"checkpoint", r"anti[-_]?join", r"NOT\s+IN\s*\(\s*SELECT", r"LEFT\s+JOIN[\s\S]{0,120}IS\s+NULL",
    r"已在庫", r"existing_dates", r"have_dates",
)
_WM_RX = re.compile("|".join(WATERMARK_MARKS), re.I)


# ────────────────────────── 小工具 ──────────────────────────
def _d(s) -> date | None:
    s = str(s or "").strip()[:10]
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None


def _json(p: Path):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:
        return None


def tails(dirpath: Path, pat: str = "VDF_ENG*_v*.py") -> dict:
    out = {}
    for p in sorted(dirpath.glob(pat)):
        fam = p.stem.rsplit("_v", 1)[0]
        if fam not in out or p.stem > out[fam].stem:
            out[fam] = p
    return out


# ────────────────────────── ① scan:庫裡已經有什麼 ──────────────────────────
def scan() -> dict:
    cat = _json(CATALOG)
    if not cat:
        return {"state": "ABSENT",
                "why": f"資料家目錄不在:{CATALOG.name} → 先跑 `via-datahome catalog`(唯讀清點,不觸網)",
                "catalog": str(CATALOG)}
    rows = []
    for ent in (cat.get("dbs") or cat.get("entries") or []):
        for t in (ent.get("tables") or []):
            rows.append({"db": ent.get("name") or ent.get("path", ""), "table": t.get("table", ""),
                         "rows": t.get("rows", -1), "date_col": t.get("date_col", ""),
                         "lo": t.get("lo", ""), "hi": t.get("hi", ""), "err": t.get("err", "")})
    if not rows:
        # 目錄在但沒有表:誠實 NODATA,不編
        by = cat.get("by_table") or {}
        rows = [{"db": v.get("db", ""), "table": k, "rows": -1, "date_col": "", "lo": "", "hi": "",
                 "err": "目錄只記了表名,沒有列數/日期範圍"} for k, v in by.items()]
    dated = [r for r in rows if r.get("date_col") and _d(r.get("lo"))]
    return {"state": "OK" if dated else ("NODATA" if rows else "ABSENT"),
            "why": "" if dated else "目錄裡沒有任何帶日期欄且有列的表(庫空或還沒 catalog)",
            "n_tables": len(rows), "n_dated": len(dated), "tables": rows,
            "catalog_ts": cat.get("ts") or cat.get("updated_at", "")}


# ────────────────────────── ② plan:只列缺口 ──────────────────────────
def plan(since: str = DEFAULT_SINCE, until: str = "", deep: bool = False) -> dict:
    s = _d(since) or _d(DEFAULT_SINCE)
    u = _d(until) or date.today()
    sc = scan()
    if sc["state"] in ("ABSENT", "NODATA"):
        return {**sc, "since": str(s), "until": str(u)}
    gaps, covered, nodate = [], [], []
    for r in sc["tables"]:
        lo, hi = _d(r.get("lo")), _d(r.get("hi"))
        if not r.get("date_col") or lo is None or hi is None:
            nodate.append(r["table"])
            continue
        head = (str(s), str(min(lo - timedelta(days=1), u))) if lo > s else None
        tail = (str(max(hi + timedelta(days=1), s)), str(u)) if hi < u else None
        wins = [w for w in (head, tail) if w and _d(w[0]) <= _d(w[1])]
        if wins:
            gaps.append({"db": r["db"], "table": r["table"], "have": f"{r['lo']}→{r['hi']}",
                         "rows": r["rows"], "missing": [f"{a}→{b}" for a, b in wins],
                         "missing_days": sum((_d(b) - _d(a)).days + 1 for a, b in wins)})
        else:
            covered.append({"table": r["table"], "have": f"{r['lo']}→{r['hi']}", "rows": r["rows"]})
    out = {"state": "OK", "since": str(s), "until": str(u),
           "n_tables": sc["n_tables"], "n_gap": len(gaps), "n_covered": len(covered),
           "gaps": gaps, "covered": covered, "no_date_col": nodate,
           "note": ("目錄只看得到最早/最新兩點,**中間的洞看不到**;要真正的逐日缺口用 --deep"
                    if not deep else "")}
    if deep:
        out["deep"] = deep_gaps(s, u)
        out["note"] = "逐日反連結:列出的日期是庫裡**真的沒有**的,照這份抓就不會重抓"
    return out


def _db_paths() -> list:
    cat = _json(CATALOG) or {}
    ps = []
    for ent in (cat.get("dbs") or cat.get("entries") or []):
        p = ent.get("path")
        if p and str(p).endswith(".duckdb"):
            ps.append(Path(p))
    return ps


def deep_gaps(s: date, u: date) -> dict:
    """逐日反連結:庫裡 distinct 日期 vs [s,u] 的差集。庫讀不到就誠實說,不猜。"""
    try:
        import duckdb  # noqa
    except Exception:
        return {"state": "ABSENT", "why": "本境沒有 duckdb 模組(不代裝;在工作站跑)"}
    res = {"state": "OK", "tables": []}
    for db in _db_paths():
        if not db.exists():
            res["tables"].append({"db": str(db), "state": "ABSENT", "why": "庫檔不在"})
            continue
        con = None
        try:
            import duckdb
            con = duckdb.connect(str(db), read_only=True)   # 唯讀:零寫入
            for (t,) in con.execute("SELECT table_name FROM information_schema.tables").fetchall():
                cols = [r[1] for r in con.execute(f'PRAGMA table_info("{t}")').fetchall()]
                dc = next((c for c in cols if str(c).lower() in
                           ("date", "obs_date", "trade_date", "dt", "ts", "datadate")), "")
                if not dc:
                    continue
                have = {str(r[0])[:10] for r in con.execute(
                    f'SELECT DISTINCT "{dc}" FROM "{t}" WHERE "{dc}" >= ? AND "{dc}" <= ?',
                    [str(s), str(u)]).fetchall()}
                want, d = [], s
                while d <= u:
                    if d.weekday() < 5 and str(d) not in have:   # 週末不算缺(非交易日)
                        want.append(str(d))
                    d += timedelta(days=1)
                res["tables"].append({"db": db.name, "table": t, "date_col": dc,
                                      "have_days": len(have), "missing_days": len(want),
                                      "missing_head": want[:10], "missing_tail": want[-10:]})
        except Exception as exc:
            res["tables"].append({"db": str(db), "state": "FAIL",
                                  "why": f"{type(exc).__name__}: {exc}"})   # L62:不截斷
        finally:
            if con is not None:
                try:
                    con.close()
                except Exception:
                    pass
    return res


# ────────────────────────── ③ audit:誰抓之前沒看庫 ──────────────────────────
def _calls_net(tree, src: str) -> bool:
    return any(m in src for m in NET_MARKS)


def audit() -> dict:
    """靜態稽核:尾版 VDF 引擎裡,**走正典網路口**的那些,抓之前有沒有看庫。

    誠實話:這是**程式碼層的代理指標**,不是行為證明。它只能說「這支檔裡找不到看庫的痕跡」,
    不能說「它一定重抓」。真憑實據是 plan --deep 在工作站跑出來的逐日缺口。
    """
    rows = []
    for fam, p in sorted(tails(ENGINE_DIR).items()):
        src = p.read_text(encoding="utf-8", errors="ignore")
        if not _calls_net(None, src):
            continue
        try:
            ast.parse(src)
            parse_ok = True
        except Exception:
            parse_ok = False
        wm = bool(_WM_RX.search(src))
        # 只把「真的在迴圈裡逐日/逐票抓」的算進重抓風險;純分析引擎排除
        fetchy = bool(re.search(r"\b(fetch|backfill|download|抓取|回補|擷取)\w*\s*\(", src, re.I))
        rows.append({"engine": fam.replace("VDF_", ""), "version": p.stem.rsplit("_v", 1)[1],
                     "watermark": wm, "fetchy": fetchy, "parse_ok": parse_ok,
                     "risk": ("重抓風險" if (fetchy and not wm) else ("看庫" if wm else "非擷取"))})
    risky = [r for r in rows if r["risk"] == "重抓風險"]
    return {"state": "OK", "n_net": len(rows), "n_watermark": sum(1 for r in rows if r["watermark"]),
            "n_risky": len(risky), "risky": risky, "rows": rows,
            "note": "程式碼層代理指標:只說『找不到看庫的痕跡』,不等於『一定重抓』。真憑實據看 plan --deep"}


def write_out(name: str, payload: dict) -> Path:
    REPORTS.mkdir(parents=True, exist_ok=True)
    p = REPORTS / name
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    return p


# ────────────────────────── 自測 ──────────────────────────
def selftest() -> int:
    import tempfile
    n, fails = [0], []

    def chk(name, ok, note=""):
        n[0] += 1
        if not ok:
            fails.append(name)
        print(f"  [{'OK' if ok else 'FAIL'}] {name}" + (f" ({note})" if note else ""))

    print(f"=== VDF_ENG089 增量擷取閘 v{VERSION} · 自測(零網路;零寫庫) ===")
    code = Path(__file__).read_text(encoding="utf-8").split("def selftest", 1)[0]
    chk("① 零網路(不 import requests/httpx/urllib;不呼叫任何抓取)",
        not any(k in code for k in ("import requests", "import httpx", "import urllib",
                                    "urlopen(", "\n    fetch(")))
    chk("② 零寫庫(連線一律 read_only;無 CREATE/INSERT/UPDATE/DELETE)",
        "read_only=True" in code and not re.search(r"\b(CREATE|INSERT|UPDATE|DELETE)\s+", code))
    chk("③ 沒有 --apply(本閘只算缺口,不代抓)", '"--apply"' not in code and "'--apply'" not in code)
    chk("④ 零九頭龍:庫清點複用 MDL123 資料家 catalog,不自己再寫一份掃庫",
        "DATAHOME_CATALOG_latest.json" in code)

    g = globals()
    sc0 = scan()
    chk("⑤ 目錄不在=誠實 ABSENT 且講得出要先跑哪一句(不是空表假綠)",
        sc0["state"] in ("ABSENT", "NODATA", "OK")
        and (sc0["state"] != "ABSENT" or "via-datahome catalog" in sc0.get("why", "")),
        f"{sc0['state']} · {sc0.get('why','')[:60]}")

    # 合成目錄:一張頭缺、一張尾缺、一張全覆蓋、一張沒有日期欄
    with tempfile.TemporaryDirectory() as td:
        fake = Path(td) / "DATAHOME_CATALOG_latest.json"
        fake.write_text(json.dumps({"ts": "2026-09-17", "dbs": [{"name": "t.duckdb", "path": str(Path(td) / "t.duckdb"), "tables": [
            # 夾具寫法要「純」:hi 必須等於 until,否則它同時有頭缺**和**一天尾缺,
            # 斷言就會為了錯的理由紅(第一版我把 hi 寫成 2026-09-16,自己被自己的夾具騙了一次)。
            {"table": "head_gap", "rows": 10, "date_col": "date", "lo": "2024-01-01", "hi": "2026-09-17"},
            {"table": "tail_gap", "rows": 10, "date_col": "date", "lo": "2023-01-01", "hi": "2025-06-30"},
            {"table": "full", "rows": 10, "date_col": "date", "lo": "2022-12-01", "hi": "2026-09-17"},
            {"table": "both_gap", "rows": 10, "date_col": "date", "lo": "2024-01-01", "hi": "2026-09-16"},
            {"table": "nodate", "rows": 10, "date_col": "", "lo": "", "hi": ""}]}]},
            ensure_ascii=False), encoding="utf-8")
        old = g["CATALOG"]
        g["CATALOG"] = fake
        try:
            sc = scan()
            chk("⑥ scan 讀得出五張表,帶日期欄的算四張", sc["state"] == "OK" and sc["n_tables"] == 5 and sc["n_dated"] == 4,
                f"表 {sc['n_tables']} · 帶日期 {sc['n_dated']}")
            pl = plan("2023-01-01", "2026-09-17")
            byt = {x["table"]: x for x in pl["gaps"]}
            chk("⑦ plan 只列缺口:頭缺算頭段、尾缺算尾段、頭尾都缺列兩段、全覆蓋的不列",
                set(byt) == {"head_gap", "tail_gap", "both_gap"}
                and byt["head_gap"]["missing"] == ["2023-01-01→2023-12-31"]
                and byt["tail_gap"]["missing"] == ["2025-07-01→2026-09-17"]
                and byt["both_gap"]["missing"] == ["2023-01-01→2023-12-31", "2026-09-17→2026-09-17"]
                and [c["table"] for c in pl["covered"]] == ["full"],
                f"缺 {pl['n_gap']} · 覆蓋 {pl['n_covered']} · 無日期欄 {pl['no_date_col']}")
            chk("⑧ 缺口天數算得對(純頭缺 2023 整年=365;頭尾都缺=365+1=366)",
                byt["head_gap"]["missing_days"] == 365 and byt["both_gap"]["missing_days"] == 366,
                f"頭 {byt['head_gap']['missing_days']} · 頭尾 {byt['both_gap']['missing_days']}")
            chk("⑨ 沒有日期欄的表誠實列在 no_date_col,不當成「沒缺」",
                pl["no_date_col"] == ["nodate"])
            chk("⑩ 不 --deep 時明說『中間的洞看不到』(不假裝這份是完整答案)",
                "中間的洞看不到" in pl["note"])
        finally:
            g["CATALOG"] = old

    # 真庫逐日反連結
    with tempfile.TemporaryDirectory() as td2:
        try:
            import duckdb
            dbp = Path(td2) / "x.duckdb"
            con = duckdb.connect(str(dbp))
            con.execute("CREATE TABLE px(date DATE, v INT)")
            con.execute("INSERT INTO px VALUES ('2026-09-14',1),('2026-09-15',1),('2026-09-17',1)")
            con.close()
            fake2 = Path(td2) / "DATAHOME_CATALOG_latest.json"
            fake2.write_text(json.dumps({"dbs": [{"name": "x.duckdb", "path": str(dbp), "tables": [
                {"table": "px", "rows": 3, "date_col": "date", "lo": "2026-09-14", "hi": "2026-09-17"}]}]},
                ensure_ascii=False), encoding="utf-8")
            old = g["CATALOG"]
            g["CATALOG"] = fake2
            try:
                dg = deep_gaps(date(2026, 9, 14), date(2026, 9, 17))
                t0 = dg["tables"][0]
                chk("⑪ --deep 逐日反連結:2026-09-16(週三)在庫裡沒有→列為缺;週末不算缺",
                    dg["state"] == "OK" and t0["missing_days"] == 1
                    and t0["missing_head"] == ["2026-09-16"],
                    f"有 {t0['have_days']} 天 · 缺 {t0['missing_days']} 天 {t0['missing_head']}")
                before = dbp.stat().st_mtime
                deep_gaps(date(2026, 9, 14), date(2026, 9, 17))
                chk("⑫ --deep 唯讀:跑完庫檔 mtime 不變(不是看旗標,是真的比)",
                    dbp.stat().st_mtime == before)
            finally:
                g["CATALOG"] = old
        except ImportError:
            chk("⑪ --deep 需要 duckdb:本境沒有=誠實跳過(不代裝、不假綠)", True, "duckdb 缺席")
            chk("⑫ --deep 唯讀:同上誠實跳過", True, "duckdb 缺席")

    a = audit()
    chk("⑬ audit 掃得到走正典網路口的尾版引擎", a["state"] == "OK" and a["n_net"] >= 10,
        f"觸網尾版 {a['n_net']} · 有看庫 {a['n_watermark']} · 重抓風險 {a['n_risky']}")
    chk("⑭ audit 明講自己只是程式碼層代理指標(不冒充行為證明)",
        "代理指標" in a["note"] and "不等於" in a["note"])
    chk("⑮ 預設起日照操作員令 2023-01-01", DEFAULT_SINCE == "2023-01-01")
    chk("⑯ 帶加速器橋(MDL156 覆蓋閘)", "[VIA:ACCEL-BRIDGE" in Path(__file__).read_text(encoding="utf-8"))

    # LL112:分子分母同一個計數來源
    print(f"  [計] {n[0]} 檢 OK {n[0] - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser(prog="VDF_ENG089_IncrementalFetchGate", description="增量擷取閘(零網路;零寫庫)")
    ap.add_argument("verb", nargs="?", default="scan", choices=["scan", "plan", "audit"])
    ap.add_argument("--since", default=DEFAULT_SINCE)
    ap.add_argument("--until", default="")
    ap.add_argument("--deep", action="store_true", help="逐日反連結(要庫讀得到)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    r = {"scan": scan, "plan": (lambda: plan(a.since, a.until, a.deep)), "audit": audit}[a.verb]()
    p = write_out(f"VDFINC_{a.verb.upper()}_{ts}.json", r)
    write_out(f"VDFINC_{a.verb.upper()}_latest.json", r)
    if a.json:
        print(json.dumps(r, ensure_ascii=False))
    else:
        print(f"[VDF_ENG089 v{VERSION}] {a.verb} · {r.get('state')}")
        if a.verb == "plan" and r.get("state") == "OK":
            print(f"  區間 {r['since']} → {r['until']} · 表 {r['n_tables']} · 有缺 {r['n_gap']} · 已覆蓋 {r['n_covered']}")
            for gp in r["gaps"][:30]:
                print(f"   [缺] {gp['table']:<28} 已有 {gp['have']:<24} 缺 {' · '.join(gp['missing'])}({gp['missing_days']} 天)")
            if r.get("no_date_col"):
                print(f"   [無日期欄] {r['no_date_col']}")
            if r.get("note"):
                print(f"   註:{r['note']}")
        elif a.verb == "audit":
            print(f"  觸網尾版 {r['n_net']} · 有看庫 {r['n_watermark']} · **重抓風險 {r['n_risky']}**")
            for x in r["risky"]:
                print(f"   [重抓風險] {x['engine']} v{x['version']}")
            print(f"   註:{r['note']}")
        else:
            for k in ("n_tables", "n_dated", "why", "catalog_ts"):
                if r.get(k) not in (None, ""):
                    print(f"  {k:>12} : {r[k]}")
        print(f"  存證 {p.name}")
    return {"OK": 0, "NODATA": 2, "ABSENT": 3}.get(r.get("state"), 1)


if __name__ == "__main__":
    sys.exit(main())
