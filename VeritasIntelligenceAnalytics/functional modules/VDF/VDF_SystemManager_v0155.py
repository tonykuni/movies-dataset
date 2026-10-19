#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_SystemManager v0155 — 薄尾:db check 分得出「VDF 自己的表」與「他系統寫的表」(L120 三系統獨立)

操作員令(2026-10-19):「這裡專注 修正獨立系統VDF 自動跳出HTML U/I清點資料庫沒問題就是收尾」。
  工作站 ActivateVDF 真跑:db_check RED。容器同一支 db check 實看(VDF\output_hub):RED 34 列裡有 14 列是 VRN 寫進
  vdf_tw_market.duckdb 的表(vrn_report_* · vrn_four_point_digest · via_policy_* …,寫入者 VRN_ENG074 / VRN_ENG082,
  或冊上沒登寫入者但表名 vrn_ 開頭)。VDF 的 refill 補不了、也不該補(L120:互不影響,只攤開不代修),卻把 VDF 的燈染紅,
  資料庫清點永遠過不了。
本版:
  ① 冊上寫入者全是他系統(VRN_ / CGC_ 開頭,沒有 VDF_)· 或沒登寫入者但表名 vrn_ 開頭 → 該列燈改 INFO,狀態前加「他系統表(VRN 寫)」,
     原狀態(缺表 / 空表 …)照留;列照樣列在頁上與 CSV(只攤開不代修),不計入 VDF 的總燈。
  ② VDF 自己的表判法一字不改(缺庫 / 缺表 / 空表 / 列數不足 = RED;列數比上次少 / 過舊 = YELLOW)。
  ③ 冊上 min_rows = 0(冊自己說「可為空」,例 tw_financial_mops · fwd_valuation_daily · 官方財報落地前 0 列不是壞):
     v0151 用 `min_rows or 1` 把 0 當 1 → 空表照紅、缺表也紅,跟冊的判準(「min_rows 才是判準」)相反。本版:
     最少 0 · 表在但空 = GREEN「空表 · 冊上最少 0 列(允許)」;最少 0 · 缺表 / 缺庫 = YELLOW「… · 冊上最少 0 列 → 待首寫」。
     最少 ≥ 1 的照 v0151(缺 / 空 = RED)。
  ④ 總燈只看 VDF 自己的表;結果多一欄 other_system(他系統表幾列 · 其中原本會紅幾列)與 min0(最少 0 列改判幾列),終端摘要行也印。
作法:換掉 v0151 模組的 db_check / _print_db(v0151 main 的 db 動詞呼叫時查模組全域)。其餘照 v0154。
只收 VIA_FROM_VCGC=YES(舊名;= 經任一系統自己的 manager / 啟動器啟動,L120 ⑥ 甲)。不抓網、不碰 TA-Lib、不寫他系統的檔。
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
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: F401
except ImportError:
    VIA_ACCEL = None
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

# ===== [VIA:LIB-BRIDGE:v0100] 三庫正典橋(批597;缺席大聲拋,不 graceful) =====
import sys as _lb_sys
from pathlib import Path as _lb_Path
_lb_p = _lb_Path(__file__).resolve()
while _lb_p.parent != _lb_p:
    if (_lb_p / "supportive modules").is_dir():
        _lb_sys.path.insert(0, str(_lb_p / "supportive modules"))
        break
    _lb_p = _lb_p.parent
import VIA_LibCanon as _LIB          # 正典缺席=大聲拋,不假裝有(LL151)
# ===== [VIA:LIB-BRIDGE:END] =====


import json
import os
import re
import sys
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA_ROOT = HERE.parents[1]
_STEM = "VDF_SystemManager"
TAG = "v0155"
SELF_ID = "VDF"
OTHER_PREFIX = ("VRN_", "CGC_")                    # 他系統寫入者的家族前綴(VDF 自己 = VDF_)


def _vnum_v0155(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0155(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0155(p) < _vnum_v0155(__file__)), key=_vnum_v0155)
PRIOR = _load_v0155(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


def _owner_module(name: str):
    """沿前版鏈往下找真正定義 name 的那一版模組(db_check / _print_db 在 v0151)。"""
    m = PRIOR
    for _ in range(64):
        if name in vars(m):
            return m
        m = vars(m).get("PRIOR")
        if m is None:
            break
    return None


DB_MOD = _owner_module("db_check")
_DB_CHECK_V0151 = DB_MOD.db_check
_PRINT_DB_V0151 = DB_MOD._print_db


def other_system(row: dict) -> str | None:
    """這列是他系統寫的表 → 回系統名(VRN / CGC);VDF 自己的 · 認不出 = None。"""
    ws = [w for w in str(row.get("寫入者") or "").split() if w]
    if ws:
        if any(w.startswith("VDF_") for w in ws):
            return None
        hit = [w for w in ws if w.startswith(OTHER_PREFIX)]
        return hit[0].split("_", 1)[0] if len(hit) == len(ws) else None
    return "VRN" if str(row.get("表") or "").startswith("vrn_") else None


def split_rows(rows: list) -> dict:
    """他系統表的列改 INFO(原狀態照留在字串裡);回 {改了幾列, 其中原本紅幾列 · 黃幾列}。"""
    n = red = yel = 0
    for r in rows:
        sysname = other_system(r)
        if not sysname or r.get("燈") == "INFO":
            continue
        n += 1
        red += r["燈"] == "RED"
        yel += r["燈"] == "YELLOW"
        r["狀態"] = "他系統表(%s 寫)· %s · VDF 只攤開不代修" % (sysname, r["狀態"])
        r["燈"] = "INFO"
    return {"n": n, "was_red": red, "was_yellow": yel}


def min0_rows(rows: list) -> dict:
    """冊上最少 0 列的表:空 = GREEN(允許);缺表 / 缺庫 = YELLOW(待首寫)。回改判幾列。"""
    ok = wait = 0
    for r in rows:
        if r.get("燈") != "RED" or r.get("最少") is None or int(r["最少"]) != 0:
            continue
        if r.get("狀態") == "空表":
            r["狀態"], r["燈"] = "空表 · 冊上最少 0 列(允許)", "GREEN"
            ok += 1
        elif r.get("狀態") in ("缺表", "缺庫"):
            r["狀態"], r["燈"] = r["狀態"] + " · 冊上最少 0 列 → 待首寫(寫入者 %s 跑過才有)" % (r.get("寫入者") or "冊上沒登"), "YELLOW"
            wait += 1
    return {"empty_ok": ok, "await_first_write": wait}


def db_check(home: str | None = None, reg: Path | None = None, today=None, write: bool = True) -> dict:
    o = _DB_CHECK_V0151(home, reg, today, write=False)
    if not o.get("rows"):
        if write and o.get("lamp") != "NODATA":
            o["files"] = DB_MOD._write_db(o)
        return o
    other = split_rows(o["rows"])
    o["min0"] = min0_rows(o["rows"])
    cnt = {k: sum(1 for r in o["rows"] if r["燈"] == k) for k in ("RED", "YELLOW", "GREEN", "INFO")}
    o["summary"] = cnt
    o["other_system"] = other
    o["tag"] = "%s %s" % (_STEM, TAG)
    o["lamp"] = "RED" if cnt["RED"] else ("YELLOW" if cnt["YELLOW"] else "GREEN")
    if write:
        o["files"] = DB_MOD._write_db(o)
    return o


def _print_db(o: dict) -> None:
    _PRINT_DB_V0151(o)
    ot = o.get("other_system")
    if ot and ot.get("n"):
        print("  [他系統表] %d 列(原判 紅 %d · 黃 %d)是 VRN / VCGC 寫的表 → 頁上與 CSV 照列(INFO),不計 VDF 的燈(L120 只攤開不代修)"
              % (ot["n"], ot["was_red"], ot["was_yellow"]))
    m0 = o.get("min0")
    if m0 and (m0["empty_ok"] or m0["await_first_write"]):
        print("  [最少 0 列] 冊上允許空的表:空表 %d 列改綠 · 缺表 / 缺庫 %d 列改黃(待首寫)" % (m0["empty_ok"], m0["await_first_write"]))


DB_MOD.db_check = db_check
DB_MOD._print_db = _print_db


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args[:2]:
        return selftest()
    return PRIOR.main(args)


def selftest() -> int:
    import datetime
    import shutil
    import tempfile
    p = f = 0

    def chk(name, cond, note=""):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s%s" % (name, (" · " + str(note)[:300]) if note else ""))

    print("=== %s %s · 薄尾自測(db check 分 VDF 自己的表 / 他系統表;沙盒 · 零網路)===" % (_STEM, TAG))
    td = Path(tempfile.mkdtemp(prefix="vdfmgr155_"))
    keep = os.environ.get("VIA_VDF_HEALTH_OUT")
    try:
        import duckdb
    except ImportError:
        duckdb = None
    try:
        os.environ["VIA_VDF_HEALTH_OUT"] = str(td / "out")
        rows = [{"表": "tw_daily_prices", "寫入者": "VDF_ENG073 VDF_ENG078"}, {"表": "vrn_report_arith_check", "寫入者": "VRN_ENG074"},
                {"表": "vrn_report_basic", "寫入者": ""}, {"表": "via_policy_sync", "寫入者": "VRN_ENG082"},
                {"表": "tw_universe", "寫入者": ""}, {"表": "mixed", "寫入者": "VRN_ENG074 VDF_ENG056"}, {"表": "odd", "寫入者": "XYZ_ENG001"}]
        chk("① 判他系統:寫入者全是 VRN_ / CGC_ → 他系統;有任何 VDF_ 寫入者 → VDF 的;沒登寫入者看表名 vrn_;認不出 = VDF 的(不放水)",
            [other_system(r) for r in rows] == [None, "VRN", "VRN", "VRN", None, None, None], [other_system(r) for r in rows])
        if duckdb is None:
            chk("⑦ duckdb 不在本境 → 只驗判法(不代裝;②–⑤ 要 duckdb 才跑)", True)
        else:
            home = td / "home" / "mega"
            home.mkdir(parents=True)
            reg = td / "reg"
            reg.mkdir()
            con = duckdb.connect(str(home / "vdf_tw_market.duckdb"))
            con.execute("create table tw_daily_prices(date date, v int)")
            con.execute("insert into tw_daily_prices values (current_date, 1)")
            con.close()
            book = [{"db": "vdf_tw_market.duckdb", "table": "tw_daily_prices", "writers": ["VDF_ENG073"], "min_rows": 1},
                    {"db": "vdf_tw_market.duckdb", "table": "vrn_report_arith_check", "writers": ["VRN_ENG074"], "min_rows": 1},
                    {"db": "vdf_tw_market.duckdb", "table": "vrn_report_basic", "writers": [], "min_rows": 1}]
            (reg / "VIA_DB_Table_SSOT_v0100.json").write_text(json.dumps({"tables": book}), encoding="utf-8")
            today = datetime.date.today()
            o = db_check(str(td / "home"), reg, today)
            st = {r["表"]: (r["燈"], r["狀態"]) for r in o["rows"]}
            page = Path(o["files"]["html"]).read_text(encoding="utf-8")
            chk("② 他系統兩張缺表 → INFO(狀態寫「他系統表(VRN 寫)· 缺表」,頁上照列);VDF 自己那張有資料 → GREEN;總燈 GREEN",
                o["lamp"] == "GREEN" and st["tw_daily_prices"][0] == "GREEN"
                and st["vrn_report_arith_check"] == ("INFO", "他系統表(VRN 寫)· 缺表 · VDF 只攤開不代修")
                and st["vrn_report_basic"][0] == "INFO" and o["other_system"] == {"n": 2, "was_red": 2, "was_yellow": 0}
                and "vrn_report_arith_check" in page and o["summary"]["INFO"] == 2, (o["lamp"], st, o.get("other_system")))
            book.append({"db": "vdf_tw_market.duckdb", "table": "tw_chip_inst", "writers": ["VDF_ENG056"], "min_rows": 1})
            book.append({"db": "vdf_hub.duckdb", "table": "digest_vdf_rows", "writers": ["VDF_ENG045"], "min_rows": 1})
            book.append({"db": "vdf_tw_market.duckdb", "table": "tw_financial_mops", "writers": ["VDF_ENG082"], "min_rows": 0})
            book.append({"db": "vdf_tw_market.duckdb", "table": "tw_empty_ok", "writers": ["VDF_ENG082"], "min_rows": 0})
            book.append({"db": "vdf_tw_market.duckdb", "table": "tw_empty_bad", "writers": ["VDF_ENG082"], "min_rows": 1})
            con = duckdb.connect(str(home / "vdf_tw_market.duckdb"))
            con.execute("create table tw_empty_ok(date date)")
            con.execute("create table tw_empty_bad(date date)")
            con.close()
            (reg / "VIA_DB_Table_SSOT_v0100.json").write_text(json.dumps({"tables": book}), encoding="utf-8")
            o2 = db_check(str(td / "home"), reg, today)
            st2 = {r["表"]: (r["燈"], r["狀態"]) for r in o2["rows"]}
            chk("③ VDF 自己的表判法不改:缺表 / 缺庫照紅,總燈 RED(不放水)",
                o2["lamp"] == "RED" and st2["tw_chip_inst"] == ("RED", "缺表") and st2["digest_vdf_rows"] == ("RED", "缺庫")
                and st2["tw_empty_bad"] == ("RED", "空表") and o2["summary"]["RED"] == 3, (o2["lamp"], st2))
            chk("④ 冊上最少 0 列:表在但空 → GREEN(允許);缺表 → YELLOW 待首寫(列寫入者);最少 1 列的空表照紅",
                st2["tw_empty_ok"] == ("GREEN", "空表 · 冊上最少 0 列(允許)")
                and st2["tw_financial_mops"] == ("YELLOW", "缺表 · 冊上最少 0 列 → 待首寫(寫入者 VDF_ENG082 跑過才有)")
                and o2["min0"] == {"empty_ok": 1, "await_first_write": 1}, (st2, o2.get("min0")))
            prev = os.environ.get("VIA_FROM_VCGC")
            os.environ["VIA_FROM_VCGC"] = "YES"
            import contextlib
            import io
            buf = io.StringIO()
            try:
                with contextlib.redirect_stdout(buf):
                    rc = DB_MOD.main(["db", "check", "--home", str(td / "home")])
            finally:
                if prev is None:
                    os.environ.pop("VIA_FROM_VCGC", None)
                else:
                    os.environ["VIA_FROM_VCGC"] = prev
            chk("⑤ 管理員 db check 動詞走本版(v0151 main 查模組全域):終端印「他系統表」「最少 0 列」兩行;紅 → 結束碼 1",
                "[他系統表]" in buf.getvalue() and "[最少 0 列]" in buf.getvalue() and rc == 1, buf.getvalue()[-300:])
        src = Path(__file__).read_text(encoding="utf-8")
        imports = re.findall(r"^\s*(?:import|from)\s+([A-Za-z_][\w.]*)", src, re.M)
        chk("⑥ 加速器橋 · 網路橋在;不匯入他系統程式;不碰 TA-Lib;同意閘不寫",
            "VIA:ACCEL-BRIDGE" in src and "def _via_net" in src
            and not [x for x in imports if x.startswith(("CGC_", "VRN_", "VCGC"))]
            and not re.search(r"^\s*(import|from)\s+" + "talib", src, re.M)
            and not re.search(r"\[[\"']VIA_(NET|SCRAPE)_" + r"CONSENT[\"']\]\s*=(?!=)", src))
    finally:
        if keep is None:
            os.environ.pop("VIA_VDF_HEALTH_OUT", None)
        else:
            os.environ["VIA_VDF_HEALTH_OUT"] = keep
        shutil.rmtree(td, ignore_errors=True)
    print("  [計] %s %s 本版 %d/%d · %s" % (_STEM, TAG, p, p + f, "PASS" if not f else "FAIL"))
    if f:
        return 1
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    return 0 if prc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
