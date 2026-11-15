#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_MDL019_DBStatusMatrix v0100 — 資料庫狀態矩陣(只讀 · VDF 自己的清點報告 → 一頁矩陣 + 建議)

操作員 2026-11-15:「Advice, database status with a very well organize matrix report to display if the display effect is good
please apply this matrix on the user interface HTml u/i」(VDF-REQ028)。
  來源   VDF 管理員自己寫的 VIA_Reports/vdf/DB_CHECK_latest.json(db check:冊 VIA_DB_Table_SSOT 每張表一列)
         + VERIFY_latest.json(db verify 獨立核對)。本支不開庫、不連網、不改任何報告。
  類別   照 db check 的狀態字:缺庫 · 缺表 · 空表 · 列數不足(紅)· 列數比上次少 · 過舊 · 待首寫(黃)· 正常(綠)· 冊上沒列 · 他系統表(資訊)。
  一頁   三行標頭 · KPI(總燈 · 庫找到 / 冊上 · 紅黃綠 · 最舊落後 · 獨立核對 · 他系統表 · 清點時間)
         · 建議(由重到輕:每條說什麼 + 怎麼做,只建議不代跑)
         · 矩陣一 庫 × 狀態(熱度格)· 矩陣二 寫入引擎 × 狀態(要重跑誰)· 逐表明細(依庫 · 列數 / 最少條 · 落後天上色)
         · 他系統的表(VRN-2 / VRN 未分辨:只讀監控 · 不代修 L123)。VDF 鎖定視覺規格(css sha256 驗過才套)。
  輸出   VIA_Reports/vdf/DB_STATUS_MATRIX_latest.html + .json。VDF 管理員 v0182 在 db check / db verify 後自動叫本支,資料庫頁即本頁。
動詞:render [--check JSON] [--verify JSON] [--out DIR] [--home DIR …] | --selftest。
  DuckDB 現查(唯讀):清點報告選的資料家 + 擷取家裡每個 .duckdb(read_only)與 parquet(read_parquet)—— 表 · 列 · 欄 · 日期範圍 · 日期數(增量快照)· 最新幾列;
         清點報告的列數逐表對現查(不一致 = 紅,排建議第一)。鎖住 / 壞檔照實記不擋。零網路 · 零安裝 · 不碰 TA-Lib · 同意閘不讀不寫 · 不寫環境。
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)。本支零外呼,只用來報閘況。"""
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

import hashlib
import html
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent                 # functional modules/VDF
VIA = HERE.parent.parent                               # VeritasIntelligenceAnalytics
TAG = "VDF_MDL019_DBStatusMatrix v" + Path(__file__).stem.rsplit("_v", 1)[-1]
OUT_REL = Path("VIA_Reports") / "vdf"
CHECK_NAME, VERIFY_NAME = "DB_CHECK_latest.json", "VERIFY_latest.json"
PAGE_NAME, DATA_NAME = "DB_STATUS_MATRIX_latest.html", "DB_STATUS_MATRIX_latest.json"
SPEC_GLOB = "VDF_UI_VisualSpec_SSOT_v*.json"
# 狀態類別(嚴重度由高到低;燈照 db check 自己判的)
CATS = [("缺庫", "RED"), ("缺表", "RED"), ("空表", "RED"), ("列數不足", "RED"), ("列數比上次少", "YELLOW"), ("過舊", "YELLOW"),
        ("待首寫", "YELLOW"), ("正常", "GREEN"), ("冊上沒列", "INFO"), ("他系統表", "INFO")]
CAT_ORDER = {c: i for i, (c, _l) in enumerate(CATS)}
CAT_LAMP = dict(CATS)
LAMP_HEX = {"RED": "#dc2626", "YELLOW": "#f59e0b", "GREEN": "#16a34a", "INFO": "#9ca3af", "GRAY": "#9ca3af"}
LAMP_RANK = {"RED": 3, "YELLOW": 2, "GREEN": 1, "INFO": 0, "GRAY": 0}


def category(state: str) -> str:
    """db check 的狀態字串 → 類別(他系統表 / 待首寫 先認;其餘取「 · 」前那段)。認不出 = 原字(不猜)。"""
    s = str(state or "").strip()
    if s.startswith("他系統表"):
        return "他系統表"
    if "待首寫" in s:
        return "待首寫"
    if s.startswith("空表") and "允許" in s:
        return "正常"
    base = s.split(" · ")[0].strip()
    return {"OK": "正常"}.get(base, base)


def other_label(state: str) -> str:
    m = re.match(r"他系統表\(([^)]*?)\s*寫\)", str(state or ""))
    return m.group(1).strip() if m else "他系統"


def writers(text) -> list:
    return [w for w in re.split(r"[\s,;/]+", str(text or "")) if w]


def load(root: Path = VIA, check: Path | None = None, verify: Path | None = None) -> dict:
    """讀 db check / db verify 自己寫的最新報告(只讀);沒有 = 照實回 None。"""
    d = Path(root) / OUT_REL
    cp, vp = Path(check or d / CHECK_NAME), Path(verify or d / VERIFY_NAME)
    chk = json.loads(cp.read_text(encoding="utf-8")) if cp.is_file() else None
    ver = json.loads(vp.read_text(encoding="utf-8")) if vp.is_file() else None
    return {"check": chk, "verify": ver, "check_path": str(cp), "verify_path": str(vp)}


def matrix(chk: dict) -> dict:
    rows = []
    for r in chk.get("rows") or []:
        c = category(r.get("狀態"))
        x = dict(r, 類別=c, 系統=(other_label(r.get("狀態")) if c == "他系統表" else "VDF"))
        rows.append(x)
    own = [r for r in rows if r["類別"] != "他系統表"]
    other = [r for r in rows if r["類別"] == "他系統表"]
    dbs = sorted({r["庫"] for r in rows})
    present = [c for c, _l in CATS if any(r["類別"] == c for r in own)] + sorted({r["類別"] for r in own} - set(CAT_ORDER))
    by_db = {}
    for db in dbs:
        rs = [r for r in own if r["庫"] == db]
        cnt = {c: sum(1 for r in rs if r["類別"] == c) for c in present}
        worst = max((r.get("燈") or "INFO" for r in rs), key=lambda lp: LAMP_RANK.get(lp, 0), default="INFO")
        missing = bool(rs) and all(str(r.get("狀態") or "").startswith("缺庫") for r in rs)   # 待首寫(「缺庫 · …」)也算整本不在
        by_db[db] = {"counts": cnt, "tables": len(rs), "lamp": worst, "missing": missing,
                     "other": sum(1 for r in other if r["庫"] == db)}
    eng = {}
    for r in own:
        if r["類別"] in ("正常", "冊上沒列"):
            continue
        for w in writers(r.get("寫入者")) or ["(冊上沒登寫入者)"]:
            e = eng.setdefault(w, {c: 0 for c in present})
            e[r["類別"]] = e.get(r["類別"], 0) + 1
    lag = [r for r in own if isinstance(r.get("落後天"), (int, float))]
    oldest = max(lag, key=lambda r: r["落後天"]) if lag else None
    lamps = {lp: sum(1 for r in own if (r.get("燈") or "") == lp) for lp in ("RED", "YELLOW", "GREEN", "INFO")}
    return {"rows": rows, "own": own, "other": other, "dbs": dbs, "cats": present, "by_db": by_db, "engines": eng,
            "lamps": lamps, "oldest": oldest,
            "db_found": sum(1 for db in dbs if by_db[db]["tables"] and not by_db[db]["missing"]), "db_total": len(dbs)}


def advice(m: dict, chk: dict, ver: dict | None, now: datetime | None = None) -> list:
    """照清點結果出建議(每條:燈 · 說什麼 · 怎麼做)。只建議,不代跑。"""
    out = []
    home = (chk.get("home_pick") or {}).get("picked") or chk.get("home") or "—"
    if m["db_total"] and m["db_found"] == 0:
        out.append(("RED", "資料家沒接上:冊上 %d 本庫在 %s 一本都找不到" % (m["db_total"], home),
                    "先 `VDF_SystemManager db where` 看候選;工作站用 ActivateVDF 的 `--db-home <資料家>`(或資料家冊 VDF_DataHome_SSOT)指到真正的庫夾"))
    else:
        miss = [db for db in m["dbs"] if m["by_db"][db]["missing"]]
        if miss:
            ws = sorted({w for r in m["own"] if r["庫"] in miss for w in writers(r.get("寫入者"))})
            out.append(("RED", "缺庫 %d 本:%s" % (len(miss), " · ".join(miss)), "跑寫入引擎建庫:%s" % (" · ".join(ws[:8]) or "(冊上沒登寫入者)")))
    for cat, what in (("缺表", "表不在庫裡"), ("空表", "表是空的"), ("列數不足", "列數低於冊上最少")):
        rs = [r for r in m["own"] if r["類別"] == cat]
        if rs:
            ws = sorted({w for r in rs for w in writers(r.get("寫入者"))})
            out.append(("RED", "%s %d 張(%s)" % (cat, len(rs), what), "重跑寫入者:%s;擷取類要先開雙閘(操作員的手)" % (" · ".join(ws[:8]) or "(冊上沒登寫入者)")))
    stale = sorted([r for r in m["own"] if r["類別"] == "過舊"], key=lambda r: -(r.get("落後天") or 0))
    if stale:
        top = " · ".join("%s.%s %s 天" % (r["庫"].replace(".duckdb", ""), r["表"], r.get("落後天")) for r in stale[:4])
        out.append(("YELLOW", "過舊 %d 張(最舊:%s)" % (len(stale), top), "增量擷取補到今天:重跑 %s" % " · ".join(sorted({w for r in stale for w in writers(r.get("寫入者"))})[:8])))
    drop = [r for r in m["own"] if r["類別"] == "列數比上次少"]
    if drop:
        out.append(("YELLOW", "列數比上次少 10%%+ 的表 %d 張" % len(drop), "先看寫入者這輪有沒有被閘擋或來源少給;確認後再跑,不要直接覆寫"))
    first = [r for r in m["own"] if r["類別"] == "待首寫"]
    if first:
        out.append(("YELLOW", "待首寫 %d 張(冊上允許 0 列,但庫 / 表還沒建)" % len(first),
                    "第一次跑寫入者:%s" % " · ".join(sorted({w for r in first for w in writers(r.get("寫入者"))})[:8])))
    extra = [r for r in m["own"] if r["類別"] == "冊上沒列"]
    if extra:
        out.append(("INFO", "庫裡有、冊上沒登的表 %d 張" % len(extra), "補登 DB 冊(VIA_DB_Table_SSOT 新版)或確認是暫存表"))
    if m["other"]:
        by = {}
        for r in m["other"]:
            by[r["系統"]] = by.get(r["系統"], 0) + 1
        out.append(("INFO", "他系統的表 %d 張(%s)" % (len(m["other"]), " · ".join("%s %d" % kv for kv in sorted(by.items()))),
                    "VDF 只攤開不代修(L123)—— 交給該系統自己的 manager"))
    if ver:
        mm = ver.get("mismatches")
        n_mm = len(mm) if isinstance(mm, list) else (mm or 0)
        lp = "GREEN" if str(ver.get("lamp")) == "PASS" and not n_mm else "RED"
        out.append((lp, "獨立核對(db verify):%s · %s 表 × 欄 %s · 差異 %s" % (ver.get("lamp"), ver.get("rows_compared"), ver.get("fields_compared"), n_mm),
                    "差異 = 0 才算清點可信;有差異先看 VERIFY_latest.html" if lp != "GREEN" else "清點與庫一致"))
        if ver.get("check_ts") and chk.get("ts") and str(ver["check_ts"])[:16] != str(chk["ts"])[:16]:
            out.append(("YELLOW", "核對的是另一輪清點(核對 %s · 清點 %s)" % (ver["check_ts"], chk["ts"]), "重跑 `db verify` 對齊最新清點"))
    else:
        out.append(("YELLOW", "還沒有獨立核對(db verify)報告", "跑 `VDF_SystemManager db verify`"))
    try:
        age_h = ((now or datetime.now()) - datetime.fromisoformat(str(chk.get("ts")))).total_seconds() / 3600.0
        if age_h > 24:
            out.append(("YELLOW", "清點是 %.0f 小時前(%s)" % (age_h, chk.get("ts")), "重跑 `VDF_SystemManager db check`"))
    except (TypeError, ValueError) as exc:
        out.append(("YELLOW", "清點時間讀不懂(%s)" % exc, "重跑 `VDF_SystemManager db check`"))
    lv = m.get("live")
    if lv and lv.get("diff"):
        out.append(("RED", "清點報告與 DuckDB 現查列數不一致 %d 張(例 %s)" % (len(lv["diff"]), "%s.%s 報告 %s / 現查 %s" % (
            lv["diff"][0]["庫"], lv["diff"][0]["表"], lv["diff"][0]["報告"], lv["diff"][0]["現查"])), "庫在這段時間被寫過 → 重跑 `VDF_SystemManager db check` 再看"))
    elif lv and lv.get("compared"):
        out.append(("GREEN", "清點報告與 DuckDB 現查一致(%d 張逐表比列數)" % lv["compared"], "清點可信"))
    mr = m.get("mirror")
    if mr and mr.get("diff"):
        x = mr["diff"][0]
        out.append(("RED", "擷取輸出兩份落地不一致 %d 張(例 %s.%s:duckdb %s / parquet %s)" % (len(mr["diff"]), x["庫"], x["表"], x["duckdb"], x["parquet"]),
                    "同一引擎寫的 .duckdb 與 .parquet 列數要相同 → 重跑該擷取引擎(VDF_SystemManager fetch run <id> --apply)"))
    elif mr and mr.get("compared"):
        out.append(("GREEN", "擷取輸出兩份落地一致(.duckdb ⇄ 同名 .parquet %d 張)" % mr["compared"], "照常"))
    dup = [(f["rel"], t["name"], t["dups"]) for f in (m.get("scan") or {}).get("files") or [] for t in f["tables"] if t.get("dups")]
    if dup:
        out.append(("YELLOW", "有整列重複的表 %d 張(例 %s.%s 重複 %d 列)" % (len(dup), dup[0][0], dup[0][1], dup[0][2]),
                    "增量寫入應以鍵覆寫;看該寫入引擎的去重鍵"))
    elif m.get("scan") and (m["scan"].get("files")):
        n_t = sum(1 for f in m["scan"]["files"] for t in f["tables"] if t.get("dups") == 0)
        out.append(("GREEN", "增量維護:%d 張表沒有整列重複" % n_t, "照常增量擷取"))
    if not out:
        out.append(("GREEN", "全部正常", "照常增量擷取"))
    out.sort(key=lambda a: -LAMP_RANK.get(a[0], 0))
    return [{"lamp": a, "what": b, "do": c} for a, b, c in out]


# ---------------------------------------------------------------- DuckDB 現查(唯讀)
DATE_CANDS = ("date", "trade_date", "portfolio_date", "as_of", "asof", "snapshot_date", "data_date", "report_date", "dt", "日期")
SCAN_GLOBS = ("*.duckdb", "*/*.duckdb", "*/*/*.duckdb", "*/*.parquet", "*/*/*.parquet")
SKIP_PARTS = ("_tmp", ".tmp", "VIA_spill", "__pycache__")
BACKUP_PARTS = ("backups",)  # 引擎覆寫前的備份(時間戳檔名):只數不列,不算資料
DUP_MAX_ROWS = 2_000_000  # 超過就不數重複列(大表在工作站上太慢;頁上寫「—」)


def default_homes(chk: dict | None, root: Path = VIA) -> list:
    """要現查的家:清點報告選的資料家 + 擷取家(VIA_VDF_FETCH_HOME · 倉內 VIA_Reports/vdf_fetch/dict);不在的不收。"""
    out = []
    if chk:
        h = (chk.get("home_pick") or {}).get("picked") or chk.get("home")
        if h:
            out.append(Path(h))
    if os.environ.get("VIA_VDF_FETCH_HOME"):
        out.append(Path(os.environ["VIA_VDF_FETCH_HOME"]))
    out.append(Path(root) / "VIA_Reports" / "vdf_fetch" / "dict")
    seen, uniq = set(), []
    for h in out:
        k = str(Path(h).resolve()) if Path(h).exists() else str(h)
        if Path(h).is_dir() and k not in seen:
            seen.add(k)
            uniq.append(Path(h))
    return uniq


def _cell_s(v) -> str:
    s = "" if v is None else str(v)
    return s if len(s) <= 40 else s[:39] + "…"


def _table_stats(con, rel: str, name: str, preview: int) -> dict:
    cols = [r[0] for r in con.execute("DESCRIBE SELECT * FROM %s" % rel).fetchall()]
    n = con.execute("SELECT COUNT(*) FROM %s" % rel).fetchone()[0]
    low = {c.lower(): c for c in cols}
    dcol = next((low[c] for c in DATE_CANDS if c in low), None)
    st = {"name": name, "rows": n, "cols": len(cols), "date_col": dcol, "dmin": None, "dmax": None, "ndates": None, "dups": None}
    if 0 < n <= DUP_MAX_ROWS:
        try:  # 增量維護:同一列不該寫兩次(整列相同 = 重複)
            st["dups"] = n - con.execute("SELECT COUNT(*) FROM (SELECT DISTINCT * FROM %s)" % rel).fetchone()[0]
        except Exception:  # noqa: BLE001 — 欄型別不能比(極少見):照實記不知道,不擋
            st["dups"] = None
    elif n == 0:
        st["dups"] = 0
    if dcol and n:
        q = '"%s"' % dcol.replace('"', '""')
        dmin, dmax, nd = con.execute("SELECT MIN(CAST(%s AS VARCHAR)), MAX(CAST(%s AS VARCHAR)), COUNT(DISTINCT %s) FROM %s WHERE CAST(%s AS VARCHAR) NOT LIKE '1900%%'"
                                     % (q, q, q, rel, q)).fetchone()
        st.update(dmin=str(dmin)[:10] if dmin else None, dmax=str(dmax)[:10] if dmax else None, ndates=nd)
        order = " ORDER BY %s DESC" % q
    else:
        order = ""
    show = cols[:8]
    sel = ", ".join('"%s"' % c.replace('"', '""') for c in show) or "*"
    st["preview_cols"] = show
    st["preview_rows"] = [[_cell_s(v) for v in r] for r in con.execute("SELECT %s FROM %s%s LIMIT %d" % (sel, rel, order, preview)).fetchall()]
    return st


def duck_scan(homes: list, preview: int = 3, max_files: int = 80, max_tables: int = 200) -> dict:
    """每個家裡的 .duckdb(唯讀開)與 parquet(DuckDB read_parquet)現查:表 · 列 · 欄 · 日期範圍 · 日期數 · 最新幾列。
    檔被別的行程鎖住 / 讀壞 → 照實記 error,不擋。"""
    try:
        import duckdb
    except ImportError:
        return {"error": "duckdb 未安裝(只查不裝)", "files": []}
    files, seen, nbak = [], set(), 0
    for home in homes:
        for pat in SCAN_GLOBS:
            for f in sorted(Path(home).glob(pat)):
                if any(x in f.parts for x in SKIP_PARTS) or str(f) in seen:
                    continue
                if any(x in f.relative_to(home).parts for x in BACKUP_PARTS):
                    seen.add(str(f))
                    nbak += 1
                    continue
                seen.add(str(f))
                files.append((Path(home), f))
    out = []
    for home, f in files[:max_files]:
        rec = {"file": f.name, "rel": str(f.relative_to(home)), "home": str(home), "kind": f.suffix.lstrip("."),
               "size": f.stat().st_size, "mtime": datetime.fromtimestamp(f.stat().st_mtime).isoformat(timespec="seconds"), "tables": [], "error": None}
        try:
            if f.suffix == ".duckdb":
                con = duckdb.connect(str(f), read_only=True)
                try:
                    tabs = con.execute("SELECT table_schema, table_name FROM information_schema.tables "
                                       "WHERE table_schema NOT IN ('information_schema', 'pg_catalog') ORDER BY 1, 2").fetchall()
                    for sch, tn in tabs[:max_tables]:
                        rel = '"%s"."%s"' % (sch.replace('"', '""'), tn.replace('"', '""'))
                        rec["tables"].append(_table_stats(con, rel, tn if sch == "main" else "%s.%s" % (sch, tn), preview))
                finally:
                    con.close()
            else:
                con = duckdb.connect()
                try:
                    rec["tables"].append(_table_stats(con, "read_parquet('%s')" % str(f).replace("'", "''"), f.stem, preview))
                finally:
                    con.close()
        except Exception as exc:  # noqa: BLE001 — 鎖住 / 壞檔 / 型別怪:照實記,不擋整頁
            rec["error"] = "%s: %s" % (type(exc).__name__, str(exc)[:160])
        out.append(rec)
    return {"error": None, "files": out, "truncated": len(files) > max_files, "homes": [str(h) for h in homes], "backup_files": nbak}


def mirror_check(scan: dict) -> dict:
    """擷取輸出的兩份落地要一致:同資料夾裡 .duckdb 的表 ⇄ 同名 .parquet(引擎一次寫兩份)列數相同。"""
    pq = {}
    for f in scan.get("files") or []:
        if f["kind"] == "parquet" and f["tables"]:
            pq[(f["home"], str(Path(f["rel"]).parent), Path(f["rel"]).stem)] = f["tables"][0]["rows"]
    same, diff = [], []
    for f in scan.get("files") or []:
        if f["kind"] != "duckdb":
            continue
        for t in f["tables"]:
            k = (f["home"], str(Path(f["rel"]).parent), t["name"])
            if k in pq:
                (same if pq[k] == t["rows"] else diff).append({"庫": f["rel"], "表": t["name"], "duckdb": t["rows"], "parquet": pq[k]})
    return {"compared": len(same) + len(diff), "same": len(same), "diff": diff}


def verify_live(rows: list, scan: dict, home: str | None = None) -> dict:
    """清點報告(db check)的列數 vs DuckDB 現查:同庫同表才比(只比清點那個家);報告沒列數(缺庫 / 缺表)不比。"""
    live = {}
    for f in scan.get("files") or []:
        if home and str(Path(f["home"])) != str(Path(home)):
            continue
        if f["kind"] == "duckdb":
            for t in f["tables"]:
                live[(f["file"], t["name"])] = t["rows"]
    same, diff, absent = [], [], []
    for r in rows:
        if r.get("列數") is None or r.get("類別") == "他系統表":
            continue
        k = (r.get("庫"), r.get("表"))
        if k not in live:
            absent.append(k)
        elif int(live[k]) == int(r["列數"]):
            same.append(k)
        else:
            diff.append({"庫": k[0], "表": k[1], "報告": r["列數"], "現查": live[k]})
    return {"compared": len(same) + len(diff), "same": len(same), "diff": diff, "not_found": absent}


# ---------------------------------------------------------------- U/I
def _spec_css() -> tuple:
    hits = sorted(HERE.glob(SPEC_GLOB))
    if not hits:
        return "", "規格冊不在 → 無樣式(照實)"
    s = json.loads(hits[-1].read_text(encoding="utf-8"))
    css = s.get("css") or ""
    if hashlib.sha256(css.encode("utf-8")).hexdigest() != s.get("css_sha256"):
        return "", "規格冊 css 對不上鎖 → 不套(照實黃)"
    return css, "%s · %s · sha256 驗過" % (hits[-1].name, s.get("style_id"))


EXTRA_CSS = (
    "body{background:#f8f7f2;max-width:1320px;margin:0 auto;padding:18px 16px}"
    ".mx-head{margin:0 0 14px}.mx-r1{font-size:10.5px;letter-spacing:.14em;color:#6b7468}.mx-r2{font-size:21px;font-weight:600;margin:2px 0}"
    ".mx-r3{font-size:11.5px;color:#55605a}.mx-sec{background:#fffefb;border:1px solid #dedfd5;border-radius:8px;padding:14px 16px;margin:0 0 14px}"
    ".mx-kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(136px,1fr));gap:10px;margin:0 0 14px}"
    ".mx-kpi{background:#fffefb;border:1px solid #dedfd5;border-radius:8px;padding:10px 12px;min-width:0}"
    ".mx-kpi .k{font-size:10.5px;color:#6b7468}.mx-kpi .v{font-size:19px;font-weight:600;margin-top:2px;word-break:break-word}"
    ".mx-lamp{display:inline-block;border-radius:5px;padding:0 6px;font-size:10.5px;color:#fff;white-space:nowrap}"
    ".mx-RED{background:#dc2626}.mx-YELLOW{background:#f59e0b}.mx-GREEN{background:#16a34a}.mx-INFO,.mx-GRAY{background:#9ca3af}"
    ".mx-scroll{overflow-x:auto;max-width:100%}table.mx{border-collapse:collapse;width:100%;font-size:11.5px}"
    "table.mx th,table.mx td{border-bottom:1px solid #e1e4dc;padding:6px 8px;text-align:left;vertical-align:top}"
    "table.mx th{background:#eeeee7;font-weight:600;font-size:10.5px;white-space:nowrap}"
    "td.mx-cell{text-align:center;font-variant-numeric:tabular-nums;min-width:44px}td.mx-num{text-align:right;font-variant-numeric:tabular-nums}"
    ".mx-bar{display:inline-block;height:8px;border-radius:4px;background:#eeeee7;width:80px;vertical-align:middle;overflow:hidden;margin-right:6px}"
    ".mx-bar span{display:block;height:100%}.mx-small{font-size:10.5px;color:#6b7468}.mx-adv li{margin:6px 0}"
    ".mx-adv code{background:#eeeee7;border-radius:4px;padding:0 4px}details.mx-db{border-top:1px solid #e1e4dc;padding:6px 0}"
    "details.mx-db summary{cursor:pointer;font-weight:600;padding:4px 0}.mx-h3{font-size:13px;font-weight:600;margin:16px 0 6px;word-break:break-all}")


def _e(x) -> str:
    return html.escape("" if x is None else str(x))


def _chip(lp) -> str:
    return '<span class="mx-lamp mx-%s">%s</span>' % (_e(lp), _e(lp))


def _cell(n: int, lamp: str, mx: int) -> str:
    if not n:
        return '<td class="mx-cell mx-small">·</td>'
    a = 0.14 + 0.66 * (n / max(mx, 1))
    hx = LAMP_HEX.get(lamp, "#9ca3af")
    rgb = tuple(int(hx[i:i + 2], 16) for i in (1, 3, 5))
    fg = "#fff" if a > 0.5 else "#26312f"
    return '<td class="mx-cell" style="background:rgba(%d,%d,%d,%.2f);color:%s;font-weight:600">%d</td>' % (rgb + (a, fg, n))


def _md_code(s: str) -> str:
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", _e(s))


def _sz(n: int) -> str:
    return ("%.1f MB" % (n / 1048576.0)) if n >= 1048576 else ("%d KB" % max(1, round(n / 1024.0)))


def _dups_cell(tables: list) -> str:
    dp = [t["dups"] for t in tables if t.get("dups") is not None]
    return "—" if not dp else ("0" if not sum(dp) else "%d %s" % (sum(dp), _chip("YELLOW")))


def _duck_section(m: dict) -> str:
    """DuckDB 現查段:每個家一塊 —— 先列 .duckdb 庫(表 · 列 · 日期 · 重複 · 歸屬),各庫最新幾列收合;parquet 鏡像收合成一個小表。"""
    sc = m.get("scan") or {}
    if not sc:
        return ""
    lv, mr = m.get("live") or {}, m.get("mirror") or {}
    vt = []
    if lv and lv.get("compared"):
        vt.append("清點報告 vs 現查:比對 %d 張 · 一致 %d · 不一致 %d" % (lv["compared"], lv.get("same", 0), len(lv.get("diff") or [])))
    elif lv:
        vt.append("清點報告 vs 現查:冊上的庫不在這些家裡(0 張可比)")
    if mr.get("compared"):
        vt.append(".duckdb ⇄ 同名 .parquet:%d 張 · 一致 %d · 不一致 %d" % (mr["compared"], mr["same"], len(mr["diff"])))
    alltabs = [t for f in sc.get("files") or [] for t in f["tables"]]
    if alltabs:
        vt.append("整列重複:%d 張表 · 重複 %d 列" % (sum(1 for t in alltabs if t.get("dups") is not None), sum(t.get("dups") or 0 for t in alltabs)))
    if sc.get("backup_files"):
        vt.append("引擎覆寫前備份 %d 檔(backups/,只數不列)" % sc["backup_files"])
    bad = bool(lv.get("diff") or mr.get("diff"))
    lamp = "RED" if bad else ("YELLOW" if any(t.get("dups") for t in alltabs) else ("GREEN" if alltabs else "GRAY"))
    out = ['<section class="mx-sec"><h2>DuckDB 現查(唯讀 · 本頁產生時直接查庫)</h2><p>%s %s</p>' % (_chip(lamp), _e(" · ".join(vt) or "沒有可比的"))]
    if sc.get("error"):
        out.append('<p class="mx-small">%s</p>' % _e(sc["error"]))
    for i, home in enumerate(sc.get("homes") or [], 1):
        fs = [f for f in sc.get("files") or [] if f["home"] == home]
        dbs, pqs = [f for f in fs if f["kind"] == "duckdb"], [f for f in fs if f["kind"] == "parquet"]
        out.append('<h3 class="mx-h3">家 %d · %s<span class="mx-small"> · %d 個 .duckdb · %d 個 parquet</span></h3>' % (i, _e(home), len(dbs), len(pqs)))
        rows = []
        for f in dbs:
            dmax = max([t["dmax"] for t in f["tables"] if t.get("dmax")] or ["—"])
            nd = max([t["ndates"] for t in f["tables"] if t.get("ndates")] or [0])
            rows.append("<tr><td><b>%s</b>%s</td><td class=\"mx-num\">%d</td><td class=\"mx-num\">%s</td><td>%s</td><td class=\"mx-num\">%s</td>"
                        "<td class=\"mx-num\">%s</td><td class=\"mx-num\">%s</td><td class=\"mx-small\">%s</td><td>%s</td></tr>" % (
                            _e(f["file"]), ('<br><span class="mx-small">%s</span>' % _e(str(Path(f["rel"]).parent))) if str(Path(f["rel"]).parent) != "." else "",
                            len(f["tables"]), _e(format(sum(t["rows"] for t in f["tables"]), ",")), _e(dmax), _e(nd or "—"), _dups_cell(f["tables"]),
                            _sz(f["size"]), _e(f["mtime"].replace("T", " ")[:16]),
                            (_chip("RED") + " " + _e(f["error"])) if f["error"] else ("DB 冊" if f["file"] in m["dbs"] else "擷取輸出")))
        if rows:
            out.append('<div class="mx-scroll"><table class="mx"><thead><tr><th>庫</th><th>表</th><th>總列數</th><th>最新日</th><th>日期數</th><th>重複列</th>'
                       '<th>大小</th><th>更新</th><th>歸屬</th></tr></thead><tbody>%s</tbody></table></div>' % "".join(rows))
        for f in dbs:
            if not f["tables"]:
                continue
            inner = []
            for t in f["tables"]:
                pv = "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % _e(c) for c in r) for r in t["preview_rows"])
                inner.append('<p><b>%s</b> · %s 列 · %d 欄%s%s</p><div class="mx-scroll"><table class="mx"><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>' % (
                    _e(t["name"]), _e(format(t["rows"], ",")), t["cols"],
                    (" · %s %s ~ %s · %s 個日期" % (_e(t["date_col"]), _e(t["dmin"]), _e(t["dmax"]), _e(t["ndates"]))) if t.get("date_col") else "",
                    (" · 重複 %d 列" % t["dups"]) if t.get("dups") else "", "".join("<th>%s</th>" % _e(c) for c in t["preview_cols"]), pv))
            out.append('<details class="mx-db"><summary>%s · %d 表 · 每表最新 3 列</summary>%s</details>' % (_e(f["rel"]), len(f["tables"]), "".join(inner)))
        if pqs:
            prow = "".join("<tr><td>%s</td><td class=\"mx-num\">%s</td><td>%s</td><td class=\"mx-num\">%s</td><td class=\"mx-small\">%s</td><td>%s</td></tr>" % (
                _e(f["rel"]), _e(format(sum(t["rows"] for t in f["tables"]), ",")), _e(max([t["dmax"] for t in f["tables"] if t.get("dmax")] or ["—"])),
                _dups_cell(f["tables"]), _e(f["mtime"].replace("T", " ")[:16]), (_chip("RED") + " " + _e(f["error"])) if f["error"] else "") for f in pqs)
            out.append('<details class="mx-db"><summary>parquet 檔 %d 個(DuckDB read_parquet 現查)</summary><div class="mx-scroll"><table class="mx"><thead><tr>'
                       '<th>檔</th><th>列</th><th>最新日</th><th>重複列</th><th>更新</th><th></th></tr></thead><tbody>%s</tbody></table></div></details>' % (len(pqs), prow))
        if not fs:
            out.append('<p class="mx-small">這個家裡沒有 .duckdb / parquet</p>')
    out.append("</section>")
    return "".join(out)


def page(data: dict, m: dict, adv: list) -> str:
    chk, ver = data["check"], data["verify"]
    css, css_note = _spec_css()
    cats = m["cats"]
    mx_db = max([v for db in m["dbs"] for v in m["by_db"][db]["counts"].values()] + [1])
    p = ['<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="via-page" content="DB_STATUS_MATRIX">'
         '<meta name="viewport" content="width=device-width,initial-scale=1">',
         "<title>VDF 資料庫狀態矩陣</title><style>%s</style><style>%s</style></head><body>" % (css, EXTRA_CSS),
         '<header class="mx-head"><div class="mx-r1">VERITAS INTELLIGENCE ANALYTICS</div><div class="mx-r2">Veritas DataForge</div>'
         '<div class="mx-r3">資料庫狀態矩陣 · 建議 · DuckDB 現查 · 庫 × 狀態 · 寫入引擎 × 狀態 · 逐表明細</div></header>']
    o = m["oldest"]
    kpis = [("總燈", _chip(chk.get("lamp"))), ("庫(找到 / 冊上)", "%d / %d" % (m["db_found"], m["db_total"])),
            ("VDF 表", str(len(m["own"]))), ("紅 · 黃 · 綠", "%d · %d · %d" % (m["lamps"]["RED"], m["lamps"]["YELLOW"], m["lamps"]["GREEN"])),
            ("最舊落後", ("%s 天" % o["落後天"]) if o else "—"), ("獨立核對", _chip("GREEN" if ver and ver.get("lamp") == "PASS" else ("RED" if ver else "GRAY")) + (" " + _e(ver.get("lamp")) if ver else " 沒有")),
            ("他系統表(只讀)", str(len(m["other"]))),
            ("DuckDB 現查", "%d 檔 · %d 表" % (len((m.get("scan") or {}).get("files") or []), sum(len(f["tables"]) for f in (m.get("scan") or {}).get("files") or []))),
            ("清點時間", _e(str(chk.get("ts") or "—").replace("T", " ")[:16]))]
    p.append('<div class="mx-kpis">%s</div>' % "".join('<div class="mx-kpi"><div class="k">%s</div><div class="v">%s</div></div>' % (_e(k), v) for k, v in kpis))
    p.append('<section class="mx-sec"><h2>建議(照清點結果 · 由重到輕)</h2><ol class="mx-adv">%s</ol></section>' % "".join(
        "<li>%s %s<br><span class=\"mx-small\">→ %s</span></li>" % (_chip(a["lamp"]), _e(a["what"]), _md_code(a["do"])) for a in adv))
    p.append(_duck_section(m))
    head = "".join("<th>%s %s</th>" % (_e(c), _chip(CAT_LAMP.get(c, "INFO"))) for c in cats)
    body = []
    for db in sorted(m["dbs"], key=lambda d: (-LAMP_RANK.get(m["by_db"][d]["lamp"], 0), d)):
        b = m["by_db"][db]
        body.append("<tr><td><b>%s</b>%s</td><td>%s</td><td class=\"mx-num\">%d</td>%s</tr>" % (
            _e(db), ' <span class="mx-small">(缺庫)</span>' if b["missing"] else "", _chip(b["lamp"]), b["tables"],
            "".join(_cell(b["counts"].get(c, 0), CAT_LAMP.get(c, "INFO"), mx_db) for c in cats)))
    p.append('<section class="mx-sec"><h2>矩陣一 · 庫 × 狀態</h2><p class="mx-small">格子 = 表數;顏色 = 該狀態的燈,越深越多</p>'
             '<div class="mx-scroll"><table class="mx"><thead><tr><th>庫</th><th>燈</th><th>表</th>%s</tr></thead><tbody>%s</tbody></table></div></section>' % (head, "".join(body)))
    if m["engines"]:
        cats2 = [c for c in cats if c not in ("正常", "冊上沒列")]
        mx_e = max([v for e in m["engines"].values() for v in e.values()] + [1])
        erows = sorted(m["engines"].items(), key=lambda kv: (-sum(kv[1].get(c, 0) * (10 ** (9 - CAT_ORDER.get(c, 9))) for c in cats2), kv[0]))
        p.append('<section class="mx-sec"><h2>矩陣二 · 寫入引擎 × 狀態(要重跑誰)</h2><div class="mx-scroll"><table class="mx"><thead><tr><th>寫入引擎</th>%s<th>合計</th></tr></thead><tbody>%s</tbody></table></div></section>' % (
            "".join("<th>%s</th>" % _e(c) for c in cats2),
            "".join("<tr><td><b>%s</b></td>%s<td class=\"mx-num\">%d</td></tr>" % (_e(w), "".join(_cell(e.get(c, 0), CAT_LAMP.get(c, "INFO"), mx_e) for c in cats2),
                                                                          sum(e.get(c, 0) for c in cats2)) for w, e in erows[:30])))
    det = []
    for db in sorted(m["dbs"], key=lambda d: (-LAMP_RANK.get(m["by_db"][d]["lamp"], 0), d)):
        rs = sorted([r for r in m["own"] if r["庫"] == db], key=lambda r: (CAT_ORDER.get(r["類別"], 99), r["表"]))
        if not rs:
            continue
        trs = []
        for r in rs:
            n, mn = r.get("列數"), r.get("最少") or 0
            pct = 100 if (n and not mn) else (min(100, int(100 * (n or 0) / mn)) if mn else 0)
            lag = r.get("落後天")
            trs.append("<tr><td>%s</td><td>%s</td><td>%s</td><td class=\"mx-num\"><span class=\"mx-bar\"><span style=\"width:%d%%;background:%s\"></span></span>%s / %s</td>"
                       "<td>%s</td><td class=\"mx-num\" style=\"color:%s\">%s</td><td class=\"mx-small\">%s</td></tr>" % (
                           _e(r["表"]), _chip(r.get("燈")), _e(r["類別"]), pct, LAMP_HEX.get(r.get("燈"), "#9ca3af"), _e(n if n is not None else "—"), _e(mn),
                           _e(r.get("最新日") or "—"), "#dc2626" if (lag or 0) > 30 else ("#f59e0b" if (lag or 0) > 10 else "#26312f"), _e(lag if lag is not None else "—"),
                           _e(r.get("寫入者") or "—")))
        b = m["by_db"][db]
        det.append('<details class="mx-db"%s><summary>%s %s · %d 表</summary><div class="mx-scroll"><table class="mx"><thead><tr><th>表</th><th>燈</th><th>狀態</th>'
                   '<th>列數 / 最少</th><th>最新日</th><th>落後天</th><th>寫入者</th></tr></thead><tbody>%s</tbody></table></div></details>' % (
                       " open" if b["lamp"] == "RED" and not b["missing"] else "", _chip(b["lamp"]), _e(db), len(rs), "".join(trs)))
    p.append('<section class="mx-sec"><h2>逐表明細(依庫 · 由重到輕)</h2>%s</section>' % "".join(det))
    if m["other"]:
        p.append('<section class="mx-sec"><h2>他系統的表(只讀監控 · VDF 不代修)</h2><div class="mx-scroll"><table class="mx"><thead><tr><th>系統</th><th>庫</th><th>表</th><th>原狀態</th></tr></thead><tbody>%s</tbody></table></div></section>' % "".join(
            "<tr><td>%s</td><td>%s</td><td>%s</td><td class=\"mx-small\">%s</td></tr>" % (_e(r["系統"]), _e(r["庫"]), _e(r["表"]), _e(r.get("狀態"))) for r in m["other"]))
    p.append('<p class="mx-small">來源:%s(%s · %s · 冊 %s)%s · %s · 樣式 %s</p></body></html>' % (
        _e(Path(data["check_path"]).name), _e(chk.get("tag")), _e(chk.get("ts")), _e(chk.get("book")),
        (" · %s(%s · %s)" % (_e(Path(data["verify_path"]).name), _e(ver.get("tag")), _e(ver.get("ts")))) if ver else "",
        _e(TAG), _e(css_note)))
    return "".join(p)


def render(root: Path = VIA, out_dir: Path | None = None, check: Path | None = None, verify: Path | None = None,
           homes: list | None = None, scan: bool = True) -> dict:
    data = load(root, check, verify)
    if not data["check"]:
        return {"lamp": "GRAY", "why": "沒有 %s(先跑 `VDF_SystemManager db check`)" % data["check_path"]}
    m = matrix(data["check"])
    if scan:
        m["scan"] = duck_scan(list(homes) if homes else default_homes(data["check"], root))
        ck_home = (data["check"] or {}).get("home") if data["check"] else None
        m["live"] = verify_live(m["own"], m["scan"], ck_home)
        m["mirror"] = mirror_check(m["scan"])
    adv = advice(m, data["check"], data["verify"])
    d = Path(out_dir or Path(root) / OUT_REL)
    d.mkdir(parents=True, exist_ok=True)
    hp, jp = d / PAGE_NAME, d / DATA_NAME
    hp.write_text(page(data, m, adv), encoding="utf-8")
    summ = {"engine": TAG, "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "check_ts": data["check"].get("ts"),
            "lamp": data["check"].get("lamp"), "db_found": m["db_found"], "db_total": m["db_total"], "tables": len(m["own"]),
            "lamps": m["lamps"], "by_db": m["by_db"], "engines": m["engines"], "advice": adv, "other": len(m["other"]),
            "duckdb_live": {"homes": (m.get("scan") or {}).get("homes"), "files": [{k: f[k] for k in ("rel", "kind", "error")} | {"tables": [
                {k: t[k] for k in ("name", "rows", "cols", "dmin", "dmax", "ndates", "dups")} for t in f["tables"]]} for f in (m.get("scan") or {}).get("files") or []],
                "verify": m.get("live"), "mirror": m.get("mirror"),
                "dups": sum(t.get("dups") or 0 for f in (m.get("scan") or {}).get("files") or [] for t in f["tables"])}}
    jp.write_text(json.dumps(summ, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return {"lamp": data["check"].get("lamp"), "page": str(hp), "data": str(jp), "advice": adv, "db_found": m["db_found"], "db_total": m["db_total"]}


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"]:
        return selftest()
    if args[:1] not in (["render"], []):
        print("[%s] 動詞:render [--check JSON] [--verify JSON] [--out DIR] [--home DIR …] | --selftest(只讀;VDF 自己的報告 + DuckDB 現查)" % TAG)
        return 2

    def opt(k):
        return Path(args[args.index(k) + 1]) if k in args and args.index(k) + 1 < len(args) else None
    homes = [Path(args[i + 1]) for i, a in enumerate(args) if a == "--home" and i + 1 < len(args)]
    r = render(VIA, opt("--out"), opt("--check"), opt("--verify"), homes or None)
    if r.get("lamp") == "GRAY":
        print("[%s] %s" % (TAG, r["why"]))
        return 2
    print("[%s] %s · 庫 %d / %d · 建議 %d 條 · %s" % (TAG, r["lamp"], r["db_found"], r["db_total"], len(r["advice"]), r["page"]))
    for a in r["advice"][:6]:
        print("  [%-6s] %s → %s" % (a["lamp"], a["what"][:90], a["do"][:90]))
    return 0


# ---------------------------------------------------------------- 自測(假清點 · 暫存夾 · 零網路)
def selftest() -> int:
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)[:300]) if note and not cond else ''}")

    print(f"=== {TAG} · 自測(資料庫狀態矩陣;假清點 · 暫存夾 · 零網路)===")
    chk("① 類別:OK → 正常 · 空表(冊上 0 列允許)→ 正常 · 待首寫 / 他系統表先認 · 其餘取「 · 」前段 · 他系統標籤取括號裡",
        category("OK") == "正常" and category("空表 · 冊上最少 0 列(允許)") == "正常" and category("缺庫 · 冊上最少 0 列 → 待首寫(寫入者 X)") == "待首寫"
        and category("他系統表(VRN-2 寫)· 缺庫 · VDF 只攤開不代修") == "他系統表" and category("過舊") == "過舊" and category("缺表") == "缺表"
        and other_label("他系統表(VRN-2 寫)· 缺庫") == "VRN-2" and other_label("他系統表(VRN 未分辨 寫)· x") == "VRN 未分辨")

    def row(db, t, st, lp, n=None, mn=1, d=None, lag=None, w="VDF_ENG001"):
        return {"庫": db, "表": t, "狀態": st, "燈": lp, "列數": n, "最少": mn, "上次列數": None, "最新日": d, "落後天": lag, "寫入者": w, "檔": ""}
    fx = {"verb": "db check", "tag": "VDF_SystemManager v0156", "ts": "2026-11-15T09:00:00", "book": "VIA_DB_Table_SSOT_v0102.json", "lamp": "RED",
          "home_pick": {"picked": "/x/home"},
          "rows": [row("a.duckdb", "p", "OK", "GREEN", 500, 1, "2026-11-14", 1), row("a.duckdb", "q", "過舊", "YELLOW", 90, 1, "2026-10-01", 45, "VDF_ENG055"),
                   row("a.duckdb", "r", "缺表", "RED", w="VDF_ENG055 VDF_ENG070"), row("a.duckdb", "s", "列數不足", "RED", 2, 10, "2026-11-14", 1, "VDF_ENG070"),
                   row("a.duckdb", "z", "冊上沒列", "INFO", mn=None, w=""), row("b.duckdb", "x", "缺庫", "RED", w="VDF_ENG051"),
                   row("b.duckdb", "y", "缺庫 · 冊上最少 0 列 → 待首寫(寫入者 VDF_ENG051 跑過才有)", "YELLOW", mn=0, w="VDF_ENG051"),
                   row("a.duckdb", "vrn_t", "他系統表(VRN-2 寫)· 缺表 · VDF 只攤開不代修", "INFO", w="VRN_ENG001")]}
    m = matrix(fx)
    chk("② 矩陣一 庫 × 狀態:a 庫 正常 1 · 過舊 1 · 缺表 1 · 列數不足 1 · 冊上沒列 1(燈 RED)· b 庫整本不在(缺庫 1 · 待首寫 1 → 找到 1 / 2)· 他系統表不進 VDF 計數",
        m["by_db"]["a.duckdb"]["counts"].get("過舊") == 1 and m["by_db"]["a.duckdb"]["counts"].get("缺表") == 1 and m["by_db"]["a.duckdb"]["lamp"] == "RED"
        and m["by_db"]["b.duckdb"]["missing"] is True and m["by_db"]["b.duckdb"]["counts"].get("缺庫") == 1 and len(m["own"]) == 7 and len(m["other"]) == 1
        and m["db_found"] == 1 and m["cats"][0] == "缺庫", m["by_db"])
    chk("③ 矩陣二 寫入引擎 × 狀態:ENG055 缺表 1 · 過舊 1 · ENG070 缺表 1 · 列數不足 1 · ENG051 缺庫 1 · 待首寫 1(正常 / 冊上沒列不算)",
        m["engines"]["VDF_ENG055"].get("缺表") == 1 and m["engines"]["VDF_ENG055"].get("過舊") == 1 and m["engines"]["VDF_ENG070"].get("列數不足") == 1
        and m["engines"]["VDF_ENG051"].get("待首寫") == 1 and "(冊上沒登寫入者)" not in m["engines"], m["engines"])
    adv = advice(m, fx, {"lamp": "PASS", "rows_compared": 7, "fields_compared": 35, "mismatches": [], "check_ts": "2026-11-15T09:00:00", "tag": "v0157", "ts": "x"},
                 now=datetime(2026, 11, 15, 12, 0))
    whats = " | ".join(a["what"] for a in adv)
    chk("④ 建議由重到輕:缺庫 → 缺表 / 列數不足(帶寫入者)→ 過舊(最舊 45 天)→ 待首寫 → 冊上沒列 → 他系統表 → 核對一致;紅在黃前",
        adv[0]["lamp"] == "RED" and "缺庫 1 本" in whats and "缺表 1 張" in whats and "45 天" in whats and "待首寫 1 張" in whats
        and "冊上沒登" in whats and "他系統的表 1 張(VRN-2 1)" in whats and any(a["lamp"] == "GREEN" and "核對" in a["what"] for a in adv)
        and [LAMP_RANK[a["lamp"]] for a in adv] == sorted([LAMP_RANK[a["lamp"]] for a in adv], reverse=True), whats)
    fx0 = dict(fx, rows=[row("a.duckdb", "p", "缺庫", "RED"), row("b.duckdb", "x", "缺庫", "RED")])
    adv0 = advice(matrix(fx0), fx0, None, now=datetime(2026, 11, 17, 12, 0))
    w0 = " | ".join(a["what"] for a in adv0)
    chk("⑤ 一本都找不到 → 第一條就是「資料家沒接上」+ db where / --db-home;沒有核對 → 提醒跑 db verify;清點超過 24 小時 → 提醒重跑",
        "資料家沒接上" in adv0[0]["what"] and "db where" in adv0[0]["do"] and "還沒有獨立核對" in w0 and "小時前" in w0, w0)
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        (d / "c.json").write_text(json.dumps(fx, ensure_ascii=False), encoding="utf-8")
        r = render(d, d / "out", d / "c.json", d / "nope.json")
        pg = Path(r["page"]).read_text(encoding="utf-8")
        css, css_note = _spec_css()
        chk("⑥ U/I:三行標頭 · KPI · 建議 · 矩陣一 / 二 · 逐表明細 · 他系統表只讀段 · 套 VDF 鎖定樣式(%s)· 不載外部腳本" % css_note,
            "VERITAS INTELLIGENCE ANALYTICS" in pg and "矩陣一 · 庫 × 狀態" in pg and "矩陣二 · 寫入引擎 × 狀態" in pg and "逐表明細" in pg
            and "他系統的表(只讀監控" in pg and 'content="DB_STATUS_MATRIX"' in pg[:300] and bool(css) and css in pg and "<script" not in pg.lower() and Path(r["data"]).is_file(), css_note)
        r0 = render(d, d / "out2", d / "none.json")
        try:
            import duckdb
            dbf = d / "home" / "a.duckdb"
            dbf.parent.mkdir()
            con = duckdb.connect(str(dbf))
            con.execute("CREATE TABLE p AS SELECT DATE '2026-11-01' + INTERVAL (i % 5) DAY AS date, i AS v FROM range(500) t(i)")
            con.execute("CREATE TABLE q AS SELECT 1 AS x")
            con.close()
            (d / "home" / "sub").mkdir()
            dk = duckdb.connect()
            dk.execute("COPY (SELECT 'x' AS a, 2 AS b) TO '%s' (FORMAT parquet)" % str(d / "home" / "sub" / "o.parquet").replace("'", "''"))
            dk.close()
            (d / "home" / "bad.duckdb").write_bytes(b"not a duckdb file")
            sc = duck_scan([d / "home"])
            fa = next(f for f in sc["files"] if f["file"] == "a.duckdb")
            tp = next(t for t in fa["tables"] if t["name"] == "p")
            fb = next(f for f in sc["files"] if f["file"] == "bad.duckdb")
            (d / "home" / "sub" / "backups").mkdir()
            (d / "home" / "sub" / "backups" / "20261115_000000_o.parquet").write_bytes((d / "home" / "sub" / "o.parquet").read_bytes())
            dk = duckdb.connect(str(d / "home" / "sub" / "m.duckdb"))
            dk.execute("CREATE TABLE o AS SELECT 'x' AS a, 2 AS b UNION ALL SELECT 'x', 2")
            dk.close()
            sc = duck_scan([d / "home"])
            fa = next(f for f in sc["files"] if f["file"] == "a.duckdb")
            tp = next(t for t in fa["tables"] if t["name"] == "p")
            fm = next(f for f in sc["files"] if f["file"] == "m.duckdb")
            mc = mirror_check(sc)
            chk("⑫ 增量維護:m.o 整列重複 1 · p 0 重複 · .duckdb(2 列)⇄ 同名 o.parquet(1 列)不一致照實抓 · backups/ 只數不列",
                fm["tables"][0]["dups"] == 1 and tp["dups"] == 0 and mc["compared"] == 1 and sc["backup_files"] == 1
                and not any("backups" in f["rel"] for f in sc["files"]) and mc["diff"][0]["duckdb"] == 2 and mc["diff"][0]["parquet"] == 1, (mc, fm["tables"][0]["dups"]))
            fo = next(f for f in sc["files"] if f["file"] == "o.parquet")
            chk("⑨ DuckDB 現查:唯讀開庫 · p 500 列 · 日期 2026-11-01 ~ 2026-11-05 · 5 個日期 · 最新列照日期排 · parquet 經 read_parquet · 壞檔照實記 error 不擋",
                tp["rows"] == 500 and tp["dmin"] == "2026-11-01" and tp["dmax"] == "2026-11-05" and tp["ndates"] == 5
                and str(tp["preview_rows"][0][0]).startswith("2026-11-05") and fo["tables"][0]["rows"] == 1 and fb["error"] and not fa["error"], (tp, fb.get("error")))
            lv = verify_live([{"庫": "a.duckdb", "表": "p", "列數": 500, "類別": "正常"}, {"庫": "a.duckdb", "表": "q", "列數": 7, "類別": "正常"},
                              {"庫": "a.duckdb", "表": "gone", "列數": 3, "類別": "正常"}, {"庫": "z.duckdb", "表": "x", "列數": None, "類別": "缺庫"}], sc)
            chk("⑩ 清點 vs 現查:p 一致 · q 報告 7 / 現查 1 不一致 · gone 找不到 · 缺庫不比", lv["same"] == 1 and len(lv["diff"]) == 1 and lv["diff"][0]["現查"] == 1
                and lv["not_found"] == [("a.duckdb", "gone")] and lv["compared"] == 2, lv)
            fx2 = dict(fx, rows=[row("a.duckdb", "p", "OK", "GREEN", 500, 1, "2026-11-05", 10), row("a.duckdb", "q", "OK", "GREEN", 7, 1, None, None)],
                       home_pick={"picked": str(d / "home")})
            (d / "c2.json").write_text(json.dumps(fx2, ensure_ascii=False), encoding="utf-8")
            r2 = render(d, d / "out3", d / "c2.json", d / "nope.json")
            pg2 = Path(r2["page"]).read_text(encoding="utf-8")
            chk("⑪ 頁面有 DuckDB 現查段(檔 · 表 · 總列數 · 日期數 · 歸屬 DB 冊)· 建議第一條紅 = 報告與現查不一致(q)",
                "DuckDB 現查(唯讀" in pg2 and "a.duckdb" in pg2 and "DB 冊" in pg2 and r2["advice"][0]["lamp"] == "RED" and "不一致" in r2["advice"][0]["what"],
                r2["advice"][:2])
        except ImportError:
            chk("⑨ DuckDB 現查:本機沒 duckdb → 照實跳過(不假綠)", duck_scan([d])["error"] == "duckdb 未安裝(只查不裝)")
    chk("⑦ 沒有清點報告 → GRAY 照實說先跑 db check(不假造)", r0.get("lamp") == "GRAY" and "db check" in r0.get("why", ""))
    text = Path(__file__).read_text(encoding="utf-8")
    body = text.split("def selftest", 1)[0]
    chk("⑧ VDF 獨立:只讀 VDF 自己的報告 · 不匯入他系統程式 · 兩座橋在 · 同意閘不讀不寫 · 不碰 TA-Lib · 不寫環境 · 不連網 · DuckDB 只在現查函式裡唯讀開",
        not re.search(r"^\s*(import|from)\s+(talib|CGC_|VRN_|VRN2_|VQG_|VAP_|VCGC)", text, re.M) and "read_only=True" in text and "[VIA:ACCEL-BRIDGE" in text and "[VIA:NET-BRIDGE" in text
        and not re.search(r"environ[\[.][^\n]{0,16}VIA_(NET|SCRAPE)_CON" + "SENT", body)
        and not re.search(r"os\.environ\[[^\]]*\]\s*=(?!=)|os\.environ\.(pop|setdefault|update)\(", body))
    print(f"[計] {TAG} 自測 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
