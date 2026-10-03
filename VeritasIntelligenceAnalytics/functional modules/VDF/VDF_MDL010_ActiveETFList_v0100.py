#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_MDL010_ActiveETFList v0100 — 擷取第一步 ②:主動式台股 ETF 清單(自動生成 · 驗證過 · 所有資料庫的開頭)

操作員 2026-10-03:「自動更新全台股清單及主動式 ETF 清單 可驗證 輸出兩組代號 …」「產生兩個自動生成清單驗證過引擎為第一步」。
  來源   TWSE OpenAPI t187ap47_L(ETF 冊)· 只走鎖版網路工具 http_json(雙閘在工具裡;AI 永不代設)。
  規則   沿用舊模組 VDF_ENG077 的兩條律(原件照載入,不另抄;載不到才用同文的後備):
           代碼律 ^\\d{5}A$(主動式 = 五碼 + A)· 揭露律 國內成分 = 須每日揭露持股 / 國外成分 = 不須 / 類型未知 = None(誠實)。
  開頭欄 date · ticker · yf_ticker(.TW)· bloomberg_ticker("00981A TT")· name,其後 market · fund_type · domestic · status · first_seen。
  驗證   V1 冊有料 · V2 代碼律 · V3 不重號 · V4 yf / bbg 後綴 · V5 日差 NEW / DELISTED · V6 大量下市守門 · V7 揭露類型可判(未知 = 黃)。
  輸出   <輸出根>/0-2-ActiveETFList/:active_etf_list_latest.parquet / .csv · active_etf_list_<日>.parquet · verify_report.json;
         DuckDB <輸出根>/vdf_master_lists.duckdb 表 tw_active_etf_list(增量:date + ticker 反連接;temp 當溢寫記憶體)。
  共用核心 = VDF_MDL009_TWStockList(寫檔 · 日差 · DuckDB 增量 · 入口),一條規則一份。
入口:VDF System Manager 總控標記 VIA_FROM_VDFSM=YES 或 VCGC。動詞:run [--date YYYY-MM-DD] | status | --selftest。不碰 TA-Lib。
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
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
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
TAG = "VDF_MDL010_ActiveETFList v" + Path(__file__).stem.rsplit("_v", 1)[-1]
ETF_BOOK_URL = "https://openapi.twse.com.tw/v1/opendata/t187ap47_L"
OUT_DIR, STEM, TABLE = "0-2-ActiveETFList", "active_etf_list", "tw_active_etf_list"
A_CODE_FALLBACK = re.compile(r"^\d{5}A$")


def _load_v0100(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


CORE = _load_v0100(sorted(HERE.glob("VDF_MDL009_TWStockList_v*.py"))[-1], "vdf_mdl009_core_for_mdl010")
KEY_COLS = CORE.KEY_COLS


def _eng077_rules_v0100():
    """舊模組 ENG077 的代碼律 / 揭露律原件;載不到 = 同文後備(誠實標記來源)。"""
    tails = sorted((HERE / "engine").glob("VDF_ENG077_ActiveETFUniverse_v*.py"))
    for t in [tails[0]] if tails else []:                         # v0100 = 兩條律的原件(後續薄尾沒改它們)
        try:
            m = _load_v0100(t, "vdf_eng077_rules_for_mdl010")
            return m.is_active_code, m.is_domestic, t.name
        except Exception:
            break

    def is_active_code(code):
        return bool(A_CODE_FALLBACK.match(str(code or "").strip()))

    def is_domestic(fund_type, name=""):
        t = str(fund_type or "")
        return True if "國內成分" in t else (False if "國外成分" in t else None)
    return is_active_code, is_domestic, "後備(同文)"


IS_ACTIVE, IS_DOMESTIC, RULE_SRC = _eng077_rules_v0100()


def collect(day: str) -> tuple:
    CORE._via_net = _via_net                                      # 網路入口照本支(總控 / fixture 換的是本支的)
    st, data = CORE.fetch_json_v0100(ETF_BOOK_URL)
    rows, rejected = [], []
    for it in data or []:
        code = str(it.get("基金代號") or "").strip()
        name = str(it.get("基金簡稱") or it.get("基金名稱") or "").strip()
        if not IS_ACTIVE(code):
            rejected.append({"ticker": code, "name": name})
            continue
        ft = str(it.get("基金類型") or "").strip()
        rows.append(CORE.keyed_row_v0100(day, code, name, "TWSE", fund_type=ft, domestic=IS_DOMESTIC(ft, name)))
    return rows, rejected, {"etf_book": st}


def verify(rows: list, rejected: list, states: dict, prev: list, day: str) -> dict:
    checks = []
    gated = states.get("etf_book") == "GATED"
    checks.append({"id": "V1", "name": "ETF 冊有料", "lamp": "GREEN" if rows else "RED",
                   "note": f"主動式 {len(rows)} · 非 A 碼 {len(rejected)} · 來源 {states}" + (" · 雙閘沒開(不是壞掉)" if gated else "")})
    bad = [r["ticker"] for r in rows if not IS_ACTIVE(r["ticker"])]
    checks.append({"id": "V2", "name": f"代碼律 ^\\d{{5}}A$(ENG077 {RULE_SRC})", "lamp": "RED" if bad else "GREEN", "note": f"違律 {bad[:5]}"})
    seen, dup = set(), []
    for r in rows:
        (dup.append(r["ticker"]) if r["ticker"] in seen else seen.add(r["ticker"]))
    checks.append({"id": "V3", "name": "不重號", "lamp": "RED" if dup else "GREEN", "note": f"重號 {dup[:5]}"})
    suf = [r["ticker"] for r in rows if r["yf_ticker"] != r["ticker"] + ".TW" or r["bloomberg_ticker"] != r["ticker"] + " TT"]
    checks.append({"id": "V4", "name": "yf / bloomberg 後綴", "lamp": "RED" if suf else "GREEN", "note": f"不合 {suf[:5]}"})
    df = CORE.diff_v0100(rows, prev, day)
    checks.append({"id": "V5", "name": "日差(對前一份)", "lamp": "GREEN", "note": ("首跑基準 · " if df["baseline"] else "") + json.dumps(df["counts"])})
    checks.append({"id": "V6", "name": "大量下市守門", "lamp": "RED" if df["mass_delist"] else "GREEN",
                   "note": f"今日消失 {len(df['delisted_today'])} / 上限 {df['mass_delist_limit']}"})
    unknown = [r["ticker"] for r in rows if r["domestic"] is None]
    checks.append({"id": "V7", "name": "揭露類型可判(國內 / 國外成分)", "lamp": "YELLOW" if unknown else "GREEN",
                   "note": f"國內 {sum(r['domestic'] is True for r in rows)} · 國外 {sum(r['domestic'] is False for r in rows)} · 未知 {unknown[:5]}"})
    return {"checks": checks, "diff": df, "lamp": CORE.lamp_v0100(checks)}


def run(day: str | None = None, out_root: Path | None = None) -> dict:
    day = day or date.today().isoformat()
    out_root = Path(out_root or Path.cwd())
    rows, rejected, states = collect(day)
    prev = CORE.load_previous_v0100(out_root, OUT_DIR, STEM)
    v = verify(rows, rejected, states, prev, day)
    rep = {"engine": TAG, "date": day, "count": len(rows), "lamp": v["lamp"], "checks": v["checks"], "rules": RULE_SRC,
           "diff": {k: v["diff"][k] for k in ("baseline", "counts", "new", "delisted_today", "mass_delist", "mass_delist_limit")},
           "rejected_non_active": len(rejected), "sources": states, "key_columns": list(KEY_COLS),
           "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    rep["write"] = CORE.write_outputs_v0100(v["diff"]["rows"], rep, out_root, OUT_DIR, STEM, TABLE, day,
                                            accept=v["lamp"] != "RED" and bool(rows))
    return rep


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"]:
        return selftest()
    if not CORE.entry_ok_v0100():
        print("[VDF_MDL010] 拒絕。由 VDF System Manager 總控:python \"functional modules/VDF/VDF_SystemManager_v0128.py\" fetch run MDL010 --apply")
        return 2
    verb = args[0] if args else "run"
    if verb not in ("run", "status"):
        print(f"[拒跑] {TAG}:未知動詞 '{verb}'(已知:run · status · --selftest)")
        return 2
    if verb == "status":
        p = Path.cwd() / OUT_DIR / "verify_report.json"
        print(p.read_text(encoding="utf-8") if p.is_file() else f"[{TAG}] 還沒有報告(先 run)")
        return 0 if p.is_file() else 2
    rep = run(args[args.index("--date") + 1] if "--date" in args else None)
    CORE.print_report_v0100(TAG, rep)
    if rep["sources"].get("etf_book") == "GATED":
        return 4
    return {"GREEN": 0, "YELLOW": 0, "RED": 1}[rep["lamp"]] if rep["count"] else 2


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print(f"=== {TAG} · 自測(假網路工具 · 暫存輸出根 · 零外呼)===")
    chk("① 規則 = 舊模組 ENG077 原件(代碼律 · 揭露律)", RULE_SRC.startswith("VDF_ENG077") and IS_ACTIVE("00981A") and not IS_ACTIVE("0050")
        and IS_DOMESTIC("國內成分證券主動式交易所交易基金(股票)") is True and IS_DOMESTIC("國外成分證券主動式") is False and IS_DOMESTIC("") is None, RULE_SRC)
    book = [{"基金代號": c, "基金簡稱": n, "基金類型": t, "出表日期": "1151001"} for c, n, t in (
        ("00981A", "主動群益台灣強棒", "國內成分證券主動式交易所交易基金(股票)"), ("00980A", "主動野村臺灣優選", "國內成分證券主動式交易所交易基金(股票)"),
        ("00402A", "主動安聯美國科技", "國外成分證券主動式交易所交易基金(股票)"), ("0050", "元大台灣50", "國內成分證券指數股票型基金"),
        ("00679B", "元大美債20年", "國外成分債券指數股票型基金"))]

    class _Net:
        def __init__(self, data, deny=False):
            self.data, self.deny = data, deny

        def http_json(self, url, timeout=30):
            if self.deny:
                return {"state": "DENY"}
            return {"state": "OK", "data": self.data} if url == ETF_BOOK_URL else {"state": "FAIL", "note": "no route"}
    g = globals()
    real = g["_via_net"]
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        try:
            g["_via_net"] = lambda: _Net(book)
            r1 = run("2026-10-01", root)
            import pandas as pd
            df = pd.read_parquet(root / OUT_DIR / f"{STEM}_latest.parquet")
            chk("② 生成:只留 A 碼 3 檔 · 被動 / 債券 ETF 擋 · 國內 2 國外 1", r1["count"] == 3 and r1["lamp"] == "GREEN" and r1["rejected_non_active"] == 2
                and sorted(df.ticker) == ["00402A", "00980A", "00981A"], r1["lamp"])
            chk("③ 開頭五欄 · 00981A.TW / '00981A TT'", list(df.columns[:5]) == list(KEY_COLS)
                and set(df.loc[df.ticker == "00981A", "yf_ticker"]) == {"00981A.TW"} and set(df.loc[df.ticker == "00981A", "bloomberg_ticker"]) == {"00981A TT"})
            g["_via_net"] = lambda: _Net(book[1:] + [{"基金代號": "00988A", "基金簡稱": "新主動", "基金類型": ""}])
            r2 = run("2026-10-02", root)
            chk("④ 日差:00981A 消失 · 00988A 新增;類型未知 → 黃(不猜)", r2["diff"]["new"] == ["00988A"] and r2["diff"]["delisted_today"] == ["00981A"]
                and r2["lamp"] == "YELLOW", r2["lamp"])
            import duckdb
            con = duckdb.connect(str(root / "vdf_master_lists.duckdb"))
            n = con.execute(f"SELECT COUNT(DISTINCT date) FROM {TABLE}").fetchone()[0]
            con.close()
            r2b = run("2026-10-02", root)
            chk("⑤ DuckDB 增量:兩天兩份 · 同日重跑零新列", n == 2 and r2b["write"]["duckdb_added"] == 0)
            g["_via_net"] = lambda: _Net([], deny=True)
            os.environ["VIA_FROM_VDFSM"] = "YES"
            cwd = os.getcwd()
            os.chdir(root)
            try:
                import contextlib
                import io
                with contextlib.redirect_stdout(io.StringIO()):
                    rc_g = main(["run"])
            finally:
                os.chdir(cwd)
                os.environ.pop("VIA_FROM_VDFSM", None)
            chk("⑥ 雙閘沒開 → rc4(不是壞掉)", rc_g == 4)
        finally:
            g["_via_net"] = real
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑦ 加速器橋 · 網路橋在;不碰 TA-Lib;不寫同意閘;共用核心 = MDL009", "[VIA:ACCEL-BRIDGE" in text and "[VIA:NET-BRIDGE" in text
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M) and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", text)
        and Path(CORE.__file__).name.startswith("VDF_MDL009_TWStockList_v"))
    print(f"  [計] {TAG} {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
