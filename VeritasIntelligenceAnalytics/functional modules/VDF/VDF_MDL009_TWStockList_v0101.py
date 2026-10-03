#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_MDL009_TWStockList v0101 — 薄尾:年區代碼(2021–2030)經中英文名稱局部識別核對,真股票不刪

操作員 2026-10-03:「要經過中英文名稱進行局部識別核對 不可刪」「中英文名局部識別權不在本文反覆出現」
「將這幾家有股票的代碼中英文名稱寫入程式識別 沒幾家」。
  問題   v0100 照 MDL001 鎖定 regex (?!202[1-9])(?!2030) 全碼過濾,把交易所行情裡的真股票當年份樣碼丟掉
         (中央冊 VIA_Central_Synonym_Regex YEAR_SUSPECT 的 defect_note 已記:字形判不了,只能拿冊對帳)。
  做法   只有「形狀是四碼股票、卻落在鎖定 regex 擋區」的代碼走名稱核對(局部;其餘代碼照 v0100,不逐列比名)。
         核對冊 = 下面 YEAR_ZONE_ROSTER_V0101 這幾家(官方 t187ap03_L 2026-08-05 快照,sha256 b836d04f79b0aceb):
         代碼 + 中文簡稱 + 英文簡稱。行情名 / 基本資料簡稱對上中文,或基本資料英文簡稱對上英文 = 股票,保留。
         名稱對不上、或冊外新代碼 → 照樣保留(不可刪),標 id_check 並亮黃請人核。
  不改   鎖定 regex 本身(MDL001 / 中央冊 LOCKED)原樣;v0100 檔原樣;共用核心 *_v0100(MDL010 用)全數沿用。
  欄位   開頭五欄不變;其後多 name_en(基本資料英文簡稱)· id_check(年區代碼的核對結果,其他列空白)。
         DuckDB 舊表缺新欄 → 先 ALTER TABLE ADD COLUMN 再增量(不重建、不丟舊列)。
動詞:run [--date YYYY-MM-DD] [--min N] | status | --selftest。不碰 TA-Lib。
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


# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import json
import os
import re
import sys
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_MDL009_TWStockList"


def _vnum_v0101(p) -> int:
    m = re.search(r"_v(\d+)$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0101(p) < _vnum_v0101(__file__)), key=_vnum_v0101)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
for _n, _v in vars(PRIOR).items():                     # 共用核心 *_v0100(MDL010 以本家族尾版為 CORE)全數沿用
    if not _n.startswith("__") and _n not in globals():
        globals()[_n] = _v

TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"


def fetch_json_v0100(url: str):
    """同名接手 v0100:網路入口跟著「本模組」的 _via_net 走。MDL010 寫 CORE._via_net、MDL008 fixture 換的是尾版命名空間;
    v0100 的函式看的是它自己的全域,不接手的話換網會落空(實測 MDL010 自測因此找不到輸出)。"""
    keep = PRIOR._via_net
    PRIOR._via_net = globals()["_via_net"]
    try:
        return PRIOR.fetch_json_v0100(url)
    finally:
        PRIOR._via_net = keep
STOCK_SHAPE_RX = re.compile(r"^[1-9]\d{3}$")           # 中央冊 YEAR_BY_ROSTER 的字形:只判形狀,年 / 碼交給下面的冊
ROSTER_SRC_V0101 = "t187ap03_L 2026-08-05 快照(supportive modules/VIA_Central_Governance/tw_source_snapshots · sha256 b836d04f79b0aceb)"
# 鎖定 regex 擋區裡的真股票(官方上市公司基本資料逐筆抄錄):代碼 → (中文簡稱, 公司名稱, 英文簡稱)
YEAR_ZONE_ROSTER_V0101 = {
    "2022": ("聚亨", "聚亨企業股份有限公司", "TYCOONS"),
    "2023": ("燁輝", "燁輝企業股份有限公司", "YP"),
    "2024": ("志聯", "志聯工業股份有限公司", "CHIH LIEN"),
    "2025": ("千興", "千興不銹鋼(股)公司", "CSSSC"),
    "2027": ("大成鋼", "大成不銹鋼工業股份有限公司", "TC"),
    "2028": ("威致", "威致鋼鐵工業股份有限公司", "WEI CHIH"),
    "2029": ("盛餘", "盛餘股份有限公司", "SYSCO"),
    "2030": ("彰源", "彰源企業股份有限公司", "FROCH"),
}
ID_YELLOW_V0101 = ("MISMATCH", "NOT_IN_ROSTER")


def _norm_en_v0101(s: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", str(s or "").upper())


def zh_hit_v0101(names, short: str, full: str) -> bool:
    """中文局部識別:任一來源名與冊上簡稱互相包含,或來源名落在公司全名裡。"""
    for n in (str(x or "").strip() for x in names):
        if n and (short in n or n in short or n in full):
            return True
    return False


def en_hit_v0101(en: str, roster_en: str) -> bool:
    """英文局部識別:去空白標點後大寫比對,互相包含即算(TC / TA CHEN 這類縮寫寬容)。"""
    a, b = _norm_en_v0101(en), _norm_en_v0101(roster_en)
    return bool(a and b and (a == b or (len(min(a, b, key=len)) >= 2 and (a in b or b in a))))


def identify_v0101(code: str, names, en: str) -> str:
    """擋區代碼的核對結果:ZH+EN / ZH / EN = 股票;MISMATCH = 在冊但名稱對不上;NOT_IN_ROSTER = 冊外。三者都保留。"""
    hit = YEAR_ZONE_ROSTER_V0101.get(code)
    if hit is None:
        return "NOT_IN_ROSTER"
    zh, en_ok = zh_hit_v0101(names, hit[0], hit[1]), en_hit_v0101(en, hit[2])
    return "ZH+EN" if zh and en_ok else ("ZH" if zh else ("EN" if en_ok else "MISMATCH"))


def collect_v0101(day: str) -> tuple:
    """同 v0100 collect 的來源與併表;差別只在擋區:四碼股票形狀的代碼不丟,走名稱核對後保留。"""
    got, states = {}, {}
    for k, url in SRC.items():
        states[k], got[k] = fetch_json_v0100(url)
    basic = {}
    for r in got.get("twse_basic") or []:
        basic[("TWSE", str(r.get("公司代號") or "").strip())] = (str(r.get("公司簡稱") or "").strip(), str(r.get("產業別") or "").strip(),
                                                              str(r.get("英文簡稱") or "").strip())
    for r in got.get("tpex_basic") or []:
        code = str(r.get("公司代號") or r.get("SecuritiesCompanyCode") or "").strip()
        basic[("TPEX", code)] = (str(r.get("公司簡稱") or r.get("CompanyAbbreviation") or "").strip(), str(r.get("產業別") or "").strip(),
                                 str(r.get("英文簡稱") or "").strip())
    raw = [("TWSE", str(r.get("Code") or r.get("證券代號") or "").strip(), str(r.get("Name") or r.get("證券名稱") or "").strip())
           for r in got.get("twse_quote") or []]
    raw += [("TPEX", str(r.get("SecuritiesCompanyCode") or r.get("CompanyCode") or "").strip(),
             str(r.get("CompanyName") or "").strip()) for r in got.get("tpex_quote") or []]
    rows, rejected, zone = [], [], []
    for market, code, name in raw:
        short, ind, en = basic.get((market, code), ("", "", ""))
        check = ""
        if not SSOT_STOCK_RX.match(code):
            if not STOCK_SHAPE_RX.match(code):          # ETF / 權證 / A 碼:不是股票形狀,照 v0100 列在被擋
                rejected.append({"ticker": code, "name": name, "market": market})
                continue
            check = identify_v0101(code, (name, short), en)
            zone.append({"ticker": code, "name": short or name, "name_en": en, "market": market, "id_check": check})
        rows.append(keyed_row_v0100(day, code, short or name, market, industry=ind, name_en=en, id_check=check))
    return rows, rejected, states, zone


def verify_v0101(rows: list, rejected: list, states: dict, prev: list, day: str, mins: dict, zone: list) -> dict:
    """v0100 七項照算;V2 改成「鎖定律或年區名稱核對」,另加 V8 年區中英文名稱局部識別。"""
    v = PRIOR.verify(rows, rejected, states, prev, day, mins)
    kept = {z["ticker"] for z in zone}
    bad = [r["ticker"] for r in rows if not SSOT_STOCK_RX.match(r["ticker"]) and r["ticker"] not in kept]
    for c in v["checks"]:
        if c["id"] == "V2":
            c.update(name="SSOT 代碼律(MDL001 鎖定 regex;擋區走中英文名稱核對)", lamp="RED" if bad else "GREEN",
                     note=f"違律 {len(bad)} · 擋區經名稱核對保留 {len(kept)} · 被擋 {len(rejected)}(ETF / 權證 / A 碼等,照列)")
    review = [f"{z['ticker']} {z['name']}:{z['id_check']}" for z in zone if z["id_check"] in ID_YELLOW_V0101]
    ok = [f"{z['ticker']} {z['name']}({z['id_check']})" for z in zone if z["id_check"] not in ID_YELLOW_V0101]
    v["checks"].append({"id": "V8", "name": "年區代碼中英文名稱局部識別(不可刪)", "lamp": "YELLOW" if review else "GREEN",
                        "note": f"核對過 {len(ok)} {ok[:8]}" + (f" · 待人核(仍保留){review[:8]}" if review else "") + f" · 冊 {ROSTER_SRC_V0101}"})
    v["lamp"] = lamp_v0100(v["checks"])
    return v


def evolve_schema_v0101(out_root: Path, table: str, cols: list) -> list:
    """DuckDB 舊表缺新欄就補欄(VARCHAR;舊列為 NULL),讓增量照走;回補了哪些欄。"""
    db = Path(out_root) / "vdf_master_lists.duckdb"
    if not db.is_file():
        return []
    try:
        import duckdb
    except ImportError:
        return []
    con = duckdb.connect(str(db))
    try:
        have = {r[0] for r in con.execute("SELECT column_name FROM information_schema.columns WHERE table_name = ?", [table]).fetchall()}
        add = [c for c in cols if have and c not in have]
        for c in add:
            con.execute(f'ALTER TABLE {table} ADD COLUMN "{c}" VARCHAR')
        return add
    finally:
        con.close()


def run_v0101(day: str | None = None, out_root: Path | None = None, mins: dict | None = None) -> dict:
    day = day or date.today().isoformat()
    out_root = Path(out_root or Path.cwd())
    rows, rejected, states, zone = collect_v0101(day)
    prev = load_previous_v0100(out_root, OUT_DIR, STEM)
    v = verify_v0101(rows, rejected, states, prev, day, mins if mins is not None else MIN_DEFAULT, zone)
    final = v["diff"]["rows"]
    rep = {"engine": TAG, "date": day, "count": len(rows), "lamp": v["lamp"], "checks": v["checks"],
           "diff": {k: v["diff"][k] for k in ("baseline", "counts", "new", "delisted_today", "mass_delist", "mass_delist_limit")},
           "rejected": rejected[:200], "year_zone": zone, "sources": states, "key_columns": list(KEY_COLS),
           "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    accept = v["lamp"] != "RED" and bool(rows)
    if accept and final:
        rep["schema_added"] = evolve_schema_v0101(out_root, TABLE, list(final[0].keys()) + ["status", "first_seen"])
    rep["write"] = write_outputs_v0100(final, rep, out_root, OUT_DIR, STEM, TABLE, day, accept=accept)
    return rep


run = run_v0101


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"]:
        return selftest()
    PRIOR.run, PRIOR.TAG = run_v0101, TAG              # v0100 的動詞解析照用,跑的是本版
    return PRIOR.main(args)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    keep_run, keep_tag = PRIOR.run, PRIOR.TAG
    try:
        rc0 = PRIOR.selftest()
    finally:
        PRIOR.run, PRIOR.TAG = keep_run, keep_tag
    print(f"=== {TAG} · 薄尾自測(年區代碼中英文名稱局部識別 · 不可刪 · 假網路工具 · 零外呼)===")
    chk("① v0100 自測過(生成 · 開頭五欄 · 日差 · DuckDB 增量 · 下市守門 · 雙閘 · 入口)", rc0 == 0, f"rc {rc0}")
    snap = PRIOR_PATH.parents[2] / "supportive modules" / "VIA_Central_Governance" / "tw_source_snapshots" / "t187ap03_L_20260805.json"
    if snap.is_file():
        off = {r["公司代號"]: (r["公司簡稱"], r["公司名稱"], r["英文簡稱"]) for r in json.loads(snap.read_text(encoding="utf-8"))
               if STOCK_SHAPE_RX.match(r["公司代號"]) and not SSOT_STOCK_RX.match(r["公司代號"])}
        chk("② 寫入程式的幾家 = 官方快照擋區裡的全部上市股票(代碼 · 中文簡稱 · 公司名稱 · 英文簡稱逐字一致)",
            off == YEAR_ZONE_ROSTER_V0101, sorted(off))
    else:
        chk("② 官方快照不在(冊照程式內 8 家;不假裝比過)", len(YEAR_ZONE_ROSTER_V0101) == 8, "快照缺席")
    twse = [{"Code": c, "Name": n} for c, n in (("2330", "台積電"), ("2027", "大成鋼"), ("2030", "彰源"), ("2023", "燁輝"),
                                                 ("2024", "CHIH LIEN"), ("2029", "別家公司"), ("2026", "新掛牌"), ("0050", "元大台灣50"), ("00981A", "主動群益"))]
    tpex = [{"SecuritiesCompanyCode": "6488", "CompanyName": "環球晶"}]
    basic = [{"公司代號": "2330", "公司簡稱": "台積電", "產業別": "24", "英文簡稱": "TSMC"},
             {"公司代號": "2027", "公司簡稱": "大成鋼", "產業別": "10", "英文簡稱": "TC"},
             {"公司代號": "2030", "公司簡稱": "", "產業別": "10", "英文簡稱": "FROCH"},
             {"公司代號": "2024", "公司簡稱": "", "產業別": "10", "英文簡稱": "CHIH LIEN"},
             {"公司代號": "2029", "公司簡稱": "", "產業別": "10", "英文簡稱": ""}]

    class _Net:
        def __init__(self, data):
            self.data = data

        def http_json(self, url, timeout=30):
            for k, u in SRC.items():
                if u == url:
                    return {"state": "OK", "data": self.data.get(k, [])}
            return {"state": "FAIL", "note": "no route"}
    g = globals()
    real = g["_via_net"]
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        try:
            g["_via_net"] = lambda: _Net({"twse_quote": twse, "tpex_quote": tpex, "twse_basic": basic, "tpex_basic": []})
            r = run_v0101("2026-10-01", root, mins={"TWSE": 1, "TPEX": 1})
            got = {z["ticker"]: z["id_check"] for z in r["year_zone"]}
            import pandas as pd
            tick = set(pd.read_parquet(root / OUT_DIR / f"{STEM}_latest.parquet")["ticker"])          # 首跑是基準,看寫出的清單
            chk("③ 擋區不刪:2027 大成鋼(中 + 英)· 2030 彰源(中 + 英)· 2023 燁輝(中)· 2024 志聯(只有英文 CHIH LIEN)全數保留",
                got.get("2027") == "ZH+EN" and got.get("2030") == "ZH+EN" and got.get("2023") == "ZH" and got.get("2024") == "EN"
                and {"2027", "2030", "2023", "2024"} <= tick, got)
            chk("④ 名稱對不上(2029 寫成別家公司)· 冊外新代碼(2026)→ 照樣保留,V8 黃請人核(黃不是綠)",
                got.get("2029") == "MISMATCH" and got.get("2026") == "NOT_IN_ROSTER" and {"2029", "2026"} <= tick
                and next(c for c in r["checks"] if c["id"] == "V8")["lamp"] == "YELLOW" and r["lamp"] == "YELLOW", r["lamp"])
            chk("⑤ 非股票形狀照擋(0050 · 00981A)· 擋區以外不逐列比名(2330 id_check 空白)",
                {x["ticker"] for x in r["rejected"]} == {"0050", "00981A"} and next(c for c in r["checks"] if c["id"] == "V2")["lamp"] == "GREEN")
            df = pd.read_parquet(root / OUT_DIR / f"{STEM}_latest.parquet")
            chk("⑥ 開頭五欄不變;其後 name_en · id_check;2330 id_check 空白",
                list(df.columns[:5]) == list(KEY_COLS) and {"name_en", "id_check"} <= set(df.columns)
                and set(df.loc[df.ticker == "2330", "id_check"]) == {""} and set(df.loc[df.ticker == "2027", "name_en"]) == {"TC"}, list(df.columns))
            import duckdb
            old = root / "old"
            old.mkdir()
            con = duckdb.connect(str(old / "vdf_master_lists.duckdb"))
            con.execute(f"CREATE TABLE {TABLE} (date VARCHAR, ticker VARCHAR, yf_ticker VARCHAR, bloomberg_ticker VARCHAR, name VARCHAR, "
                        "market VARCHAR, industry VARCHAR, status VARCHAR, first_seen VARCHAR)")
            con.execute(f"INSERT INTO {TABLE} VALUES ('2026-09-30','2330','2330.TW','2330 TT','台積電','TWSE','24','ACTIVE','2026-09-30')")
            con.close()
            r2 = run_v0101("2026-10-01", old, mins={"TWSE": 1, "TPEX": 1})
            con = duckdb.connect(str(old / "vdf_master_lists.duckdb"))
            n = con.execute(f"SELECT COUNT(*), COUNT(DISTINCT date), COUNT(id_check) FROM {TABLE}").fetchone()
            con.close()
            chk("⑦ v0100 舊表(沒有 name_en / id_check)→ 補欄後增量,舊列保留", set(r2.get("schema_added") or []) == {"name_en", "id_check"}
                and n[0] == 1 + r2["count"] and n[1] == 2, (r2.get("schema_added"), n))
        finally:
            g["_via_net"] = real
    import contextlib
    import io
    saved = {k: os.environ.pop(k, None) for k in ("VIA_FROM_VDFSM", "VIA_FROM_VCGC")}
    try:
        with contextlib.redirect_stdout(io.StringIO()) as buf:
            rc_x = main(["run"])
    finally:
        PRIOR.run, PRIOR.TAG = keep_run, keep_tag
        for k, v in saved.items():
            if v is not None:
                os.environ[k] = v
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑧ 沒有總控入口 → rc2;共用核心 *_v0100 照出(MDL010 用);加速器橋 · 網路橋在;不碰 TA-Lib;不寫同意閘",
        rc_x == 2 and "VDF System Manager" in buf.getvalue() and all(callable(globals().get(n)) for n in
        ("entry_ok_v0100", "fetch_json_v0100", "keyed_row_v0100", "diff_v0100", "write_outputs_v0100", "load_previous_v0100", "lamp_v0100", "print_report_v0100"))
        and "[VIA:ACCEL-BRIDGE" in text and "[VIA:NET-BRIDGE" in text
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M) and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", text))
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · v0100 {'PASS' if rc0 == 0 else 'FAIL'} · 合計 {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
