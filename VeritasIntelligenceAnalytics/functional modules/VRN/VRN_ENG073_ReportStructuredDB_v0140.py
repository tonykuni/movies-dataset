#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VRN_ENG073_ReportStructuredDB v0140 — 薄尾:vrn_report_metrics 同期多候選值收斂(掉球 Z298;操作員 2026-10-14「繼續修 Z298」)

實錄(容器 functional modules/VRN/db/vrn_reports.duckdb):77 列 · 同 report_file+metric+period 相異 73 組,多出的 4 組全是 EPS ——
  ① 年份被當成 EPS:「2027 年EPS 預估維持不變。 2025」→ 2025.0、「…我們新增2028」→ 2028.0(EPS_RX 的數字欄吃到下一句的年份);
  ② 同值重複:「2026 年EPS 預估10」與「2026 年 EPS 預估10」→ 兩列 10.0;
  ③ 真的兩個值:「2024 EPS 11.00」vs「2024 年EPS 9.53」、「2027年EPS 分別為12.95」vs「2027 年EPS 及18」。
本版規則(只動 eps,其他指標不碰;VRN 自己的引擎 L120):
  只動 metric=eps(目標價 · 殖利率等原樣通過):
  ① 丟:metric=eps 且數字原文是 19xx/20xx/21xx 四位整數(不帶小數)—— 那是年份,不是 EPS;
  ② 併:同 report_file+metric+period+value 只留第一筆(原文出現次序);
  ③ 標:同 report_file+metric+period 仍有兩個以上不同值 → 每列 status 改成「CONFLICT:<原狀態>」,值都留(不替操作員挑值);
     下游 ENG080 每年取第一筆、來源欄會帶出 metrics:CONFLICT:…,看得出來不是乾淨值。
  自測結束碼:0 全綠 · 3 本版全過、前版鏈的紅逐檢都歸得到缺件(㉑㉒㉓ ← pydantic)且收斂沒新增 ·
           2 本版全過、收斂沒新增,但前版有缺件以外的既有紅(例 ㉝ 寫死 NLP 樞紐 v1.8.0,樹上已 v1.9.0)· 1 其餘。
  入庫路徑:run 內的 extract_one 包一層 resolve_metrics(換的是本體模組的全域,run 照本體原樣跑);
  既有資料:`metrics-resolve [--db 庫] [--apply]` 依 report_file 先刪再插(與 run 同一寫法);不帶 --apply 一律乾跑;
           `metrics-resolve --selftest` 只跑本版收斂五檢(完整 --selftest 另接前版鏈,前版自身的紅照實傳出);
           預設找 run 的庫(_resolve_db)與 functional modules/VRN/db/vrn_reports.duckdb,有表的才處理。
其餘整支照前版(__getattr__ 轉接;UPS_PRICE_RX / UPS_TOTAL_RX 逐字帶著 —— VRN_ENG086 以尾版檔 AST 讀這兩條)。
VRN 不直接對外:只帶加速器橋,不帶網路橋。
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

import importlib.util
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_ENG073_ReportStructuredDB"
VRN_DB = HERE / "db" / "vrn_reports.duckdb"


def _vnum(path: Path) -> int:
    m = re.search(r"_v(\d+)$", path.stem)
    return int(m.group(1)) if m else -1


_PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location("eng073_prior_for_" + Path(__file__).stem, _PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    return getattr(PRIOR, name)


# The upside labels' canon is this family's tail (VRN_ENG086 reads UPS_PRICE_RX / UPS_TOTAL_RX off the newest ENG073 file by
# AST, not by import). A thin tail must still carry them, word for word as v0138 (selftest asserts they are identical).
UPS_PRICE_RX = re.compile(
    r"(?:Expected\s*)?share\s*price\s*return|股價報酬(?:率)?|價格報酬(?:率)?", re.I)
UPS_TOTAL_RX = re.compile(
    r"(?:Expected\s*)?total\s*return|總報酬(?:率)?|整體報酬(?:率)?", re.I)

_YEAR_TOKEN = re.compile(r"^(?:19|20|21)\d{2}$")
_LAST_NUM = re.compile(r"(-?[\d,]+(?:\.\d+)?)\s*$")


def _body():
    """往前版鏈找真正定義 extract_one 的那一支(run 用的是它的全域)。"""
    m = PRIOR
    while "extract_one" not in vars(m):
        m = vars(m)["PRIOR"]
    return m


BODY = _body()
_EXTRACT_ONE = BODY.extract_one


def year_like(m: dict) -> bool:
    """eps 的數字原文是 19xx/20xx/21xx 四位整數 = 年份被當成 EPS。"""
    if str(m.get("metric", "")).lower() != "eps" or m.get("value") is None:
        return False
    tok = _LAST_NUM.search(str(m.get("raw_text") or ""))
    raw = tok.group(1).replace(",", "") if tok else ""
    if raw:
        return bool(_YEAR_TOKEN.match(raw))
    v = float(m["value"])
    return v.is_integer() and 1900 <= v <= 2199


def resolve_metrics(mets: list) -> tuple:
    """只動 eps:① 丟年份 EPS ② 同鍵同值併 ③ 同鍵多值標 CONFLICT:<原狀態>;其他指標原樣通過。回 (新列, 計數)。次序照原文。"""
    stats = {"year_like": 0, "same_value": 0, "conflict_keys": 0, "conflict_rows": 0}
    kept, seen = [], set()
    for m in mets:
        if str(m.get("metric", "")).lower() != "eps":
            kept.append(m)                      # eps 以外原樣通過(目標價 · 殖利率等不併不標)
            continue
        if year_like(m):
            stats["year_like"] += 1
            continue
        sig = (m.get("report_file"), m.get("metric"), m.get("period"), m.get("value"))
        if sig in seen:
            stats["same_value"] += 1
            continue
        seen.add(sig)
        kept.append(dict(m))
    groups: dict = {}
    for m in kept:
        if str(m.get("metric", "")).lower() == "eps":
            groups.setdefault((m.get("report_file"), m.get("metric"), m.get("period")), []).append(m)
    for rows in groups.values():
        if len(rows) > 1:
            stats["conflict_keys"] += 1
            stats["conflict_rows"] += len(rows)
            for m in rows:
                st = str(m.get("status") or "")
                if not st.startswith("CONFLICT:"):
                    m["status"] = "CONFLICT:" + st
    return kept, stats


def extract_one(stem: str, zones: dict, names: dict) -> tuple:
    basic, mets = _EXTRACT_ONE(stem, zones, names)
    return basic, resolve_metrics(mets)[0]


BODY.extract_one = extract_one   # run() 讀本體模組的全域 → 入庫路徑走收斂


_COLS = ("report_file", "metric", "period", "status", "value", "raw_text")


def metrics_resolve(db: Path | None = None, apply: bool = False) -> dict:
    """既有 vrn_report_metrics 照同一套規則收斂;--apply 依 report_file 先刪再插(與 run 同一寫法)。"""
    import duckdb
    cands = [Path(db)] if db else [c for c in (BODY._resolve_db(None), VRN_DB) if c]
    out = {"apply": apply, "dbs": []}
    for p in dict.fromkeys(cands):
        rec = {"db": str(p)}
        out["dbs"].append(rec)
        if not Path(p).is_file():
            rec["state"] = "NODB"
            continue
        con = duckdb.connect(str(p), read_only=not apply)
        try:
            if "vrn_report_metrics" not in {r[0] for r in con.execute("SHOW TABLES").fetchall()}:
                rec["state"] = "NOTABLE"
                continue
            rows = [dict(zip(_COLS, r)) for r in con.execute(
                f"SELECT {', '.join(_COLS)} FROM vrn_report_metrics ORDER BY rowid").fetchall()]
            by: dict = {}
            for r in rows:
                by.setdefault(r["report_file"], []).append(r)
            tot = {"year_like": 0, "same_value": 0, "conflict_keys": 0, "conflict_rows": 0}
            changed = {}
            for rf, rs in by.items():
                new, st = resolve_metrics(rs)
                for k in tot:
                    tot[k] += st[k]
                if new != rs:
                    changed[rf] = new
            rec.update(rows_before=len(rows), reports=len(by), reports_changed=len(changed), **tot)
            if apply and changed:
                con.execute("BEGIN TRANSACTION")
                try:
                    for rf, new in changed.items():
                        con.execute("DELETE FROM vrn_report_metrics WHERE report_file = ?", [rf])
                        for m in new:
                            con.execute(f"INSERT INTO vrn_report_metrics ({', '.join(_COLS)}) VALUES (?,?,?,?,?,?)",
                                        [m[c] for c in _COLS])
                    con.execute("COMMIT")
                except Exception:
                    con.execute("ROLLBACK")
                    raise
            rec["rows_after"] = con.execute("SELECT COUNT(*) FROM vrn_report_metrics").fetchone()[0]
            rec["state"] = ("APPLIED" if apply else "DRY") if changed else "CLEAN"
        finally:
            con.close()
    return out


def selftest(chain: bool = True) -> int:
    """chain=False(metrics-resolve --selftest)只跑本版 ①–⑤;完整自測再接前版鏈 ⑥。"""
    import tempfile
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}" + (f" — {note}" if note else ""))

    same = all(getattr(PRIOR, n).pattern == globals()[n].pattern and getattr(PRIOR, n).flags == globals()[n].flags
               for n in ("UPS_PRICE_RX", "UPS_TOTAL_RX"))
    chk("① 尾版帶的上漲空間標籤正規式與前版逐字相同(VRN_ENG086 以尾版為正本讀)", same)
    rf = "R"
    sample = [
        {"report_file": rf, "metric": "eps", "period": "2027", "status": "ESTIMATE", "value": 2025.0, "raw_text": "2027 年EPS 預估維持不變。 2025"},
        {"report_file": rf, "metric": "eps", "period": "2027", "status": "ESTIMATE", "value": 2028.0, "raw_text": "2027 年 EPS 預估維持不變。我們新增2028"},
        {"report_file": rf, "metric": "eps", "period": "2026", "status": "ESTIMATE", "value": 10.0, "raw_text": "2026 年EPS 預估10"},
        {"report_file": rf, "metric": "eps", "period": "2026", "status": "ESTIMATE", "value": 10.0, "raw_text": "2026 年 EPS 預估10"},
        {"report_file": rf, "metric": "eps", "period": "2024", "status": "STATED", "value": 11.0, "raw_text": "2024 EPS 11.00"},
        {"report_file": rf, "metric": "eps", "period": "2024", "status": "STATED", "value": 9.53, "raw_text": "2024 年EPS 9.53"},
        {"report_file": rf, "metric": "eps", "period": "2025", "status": "ESTIMATE", "value": 2000.5, "raw_text": "2025E EPS 2,000.5"},
        {"report_file": rf, "metric": "target_price", "period": "2025", "status": "ESTIMATE", "value": 2025.0, "raw_text": "目標價 2025"},
        {"report_file": rf, "metric": "target_price", "period": "2025", "status": "ESTIMATE", "value": 2025.0, "raw_text": "目標價 2025"},
        {"report_file": rf, "metric": "target_price", "period": "2025", "status": "ESTIMATE", "value": 2100.0, "raw_text": "目標價 2100"},
    ]
    new, st = resolve_metrics(sample)
    got = [(m["period"], m["value"], m["status"]) for m in new]
    chk("② 年份 EPS 丟 2 · 同值併 1 · 多值標 CONFLICT 1 組(值都留)· 帶小數的大 EPS 不誤殺 · eps 以外(目標價重複 / 多值)原樣不動",
        st == {"year_like": 2, "same_value": 1, "conflict_keys": 1, "conflict_rows": 2}
        and got == [("2026", 10.0, "ESTIMATE"), ("2024", 11.0, "CONFLICT:STATED"), ("2024", 9.53, "CONFLICT:STATED"),
                    ("2025", 2000.5, "ESTIMATE"), ("2025", 2025.0, "ESTIMATE"), ("2025", 2025.0, "ESTIMATE"),
                    ("2025", 2100.0, "ESTIMATE")], f"{st} · {got}")
    again, st2 = resolve_metrics(new)
    chk("③ 冪等:收斂過的再收一次不變(CONFLICT 不疊)", again == new and st2["year_like"] == 0 and st2["same_value"] == 0, str(st2))
    chk("④ run 的入庫路徑換成本版 extract_one(本體模組的全域)", BODY.extract_one is extract_one, f"本體 {Path(BODY.__file__).name}")
    import duckdb
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "r.duckdb"
        con = duckdb.connect(str(p))
        con.execute("CREATE TABLE vrn_report_metrics(report_file VARCHAR, metric VARCHAR, period VARCHAR, status VARCHAR, value DOUBLE, raw_text VARCHAR)")
        rows = sample + [{"report_file": "OK", "metric": "eps", "period": "2026", "status": "ESTIMATE", "value": 5.0, "raw_text": "2026E EPS 5"}]
        con.executemany("INSERT INTO vrn_report_metrics VALUES (?,?,?,?,?,?)", [[r[c] for c in _COLS] for r in rows])
        con.close()
        dry = metrics_resolve(p)["dbs"][0]
        ap = metrics_resolve(p, apply=True)["dbs"][0]
        con = duckdb.connect(str(p), read_only=True)
        ok_rows = con.execute("SELECT COUNT(*) FROM vrn_report_metrics WHERE report_file = 'OK'").fetchone()[0]
        con.close()
        re_ap = metrics_resolve(p, apply=True)["dbs"][0]
        chk("⑤ metrics-resolve 乾跑不寫 · --apply 只改有變的報告(11 → 8)· 沒變的報告不動 · 再跑 CLEAN",
            dry["state"] == "DRY" and dry["rows_after"] == 11 and ap["state"] == "APPLIED" and ap["rows_after"] == 8
            and ap["reports_changed"] == 1 and ok_rows == 1 and re_ap["state"] == "CLEAN",
            f"{dry['state']} {dry['rows_after']} → {ap['state']} {ap['rows_after']} → {re_ap['state']}")
    if not chain:
        ok = all(results)
        print(f"  [v0140] 收斂自測 {sum(results)}/{len(results)} · {'PASS' if ok else 'FAIL'}(不含前版鏈;完整自測用 --selftest)")
        return 0 if ok else 1
    import contextlib
    import io

    def _prior_fails(patched: bool) -> tuple:
        BODY.extract_one = extract_one if patched else _EXTRACT_ONE
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                rc = PRIOR.selftest()
        finally:
            BODY.extract_one = extract_one
        lines = buf.getvalue().splitlines()
        return rc, {ln.split("(")[0].strip() for ln in lines if ln.lstrip().startswith("[FAIL]")}, \
            next((ln.strip() for ln in lines if "[計]" in ln), "")

    rc0, base, _ = _prior_fails(False)
    rc1, now, tally = _prior_fails(True)
    for ln in sorted(now):
        print(f"    前版鏈 {ln}")
    chk("⑥ 前版自測鏈:本版收斂不新增任何紅(與不掛收斂時的 FAIL 集合相同;前版自身的紅照實列出)",
        now == base, f"{_PRIOR_PATH.name} rc={rc1} · {tally} · 新增紅 {sorted(now - base) or 0}")
    ok = all(results)
    # 前版的紅能不能歸到缺件:只認逐檢對得上的(㉑㉒㉓ 金融機構 SSOT 三檢要 pydantic,批412);其餘一律不算環境
    need = {"㉑": "pydantic", "㉒": "pydantic", "㉓": "pydantic"}
    tags = {next((c for c in ln if c in need), "") for ln in now}
    env_only = bool(now) and "" not in tags and all(importlib.util.find_spec(need[t]) is None for t in tags)
    print(f"  [v0140] 自測 {sum(results)}/{len(results)} · {'PASS' if ok else 'FAIL'}"
          + ("" if rc1 == 0 else f" · 前版鏈 rc={rc1}(既有紅照實傳出,不因本版綠而洗綠)")
          + ("" if rc1 == 0 else (" · 全部可歸缺件 pydantic(裝件是操作員的手)" if env_only else " · 前版有缺件以外的既有紅 → YELLOW")))
    if ok and rc1 == 0:
        return 0
    if ok and now == base:
        return 3 if env_only else 2   # 3 = 前版紅全屬缺件 · 2 = 前版有其他既有紅、本版沒新增(YELLOW,不冒充環境)
    return 1


def main() -> int:
    args = sys.argv[1:]
    if args[:1] == ["metrics-resolve"] and "--selftest" in args:
        return selftest(chain=False)
    if args[:1] == ["metrics-resolve"]:
        db = Path(args[args.index("--db") + 1]) if "--db" in args and args.index("--db") + 1 < len(args) else None
        r = metrics_resolve(db, apply="--apply" in args)
        for d in r["dbs"]:
            print(f"  [Z298 收斂] {d['state']} · {d['db']}" + (
                f" · 列 {d['rows_before']} → {d['rows_after']} · 報告 {d['reports_changed']}/{d['reports']} 有變 · "
                f"年份EPS 丟 {d['year_like']} · 同值併 {d['same_value']} · 多值 CONFLICT {d['conflict_keys']} 組"
                if "rows_before" in d else ""))
        states = {d["state"] for d in r["dbs"]}
        return 0 if states & {"APPLIED", "CLEAN"} and "DRY" not in states else (2 if "DRY" in states else 1)
    if "--selftest" in args:
        return selftest()
    return PRIOR.main()


if __name__ == "__main__":
    sys.exit(main())
