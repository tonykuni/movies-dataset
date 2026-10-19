#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_SystemManager v0156 — 薄尾:db check 的他系統表分開命名 VRN-1 / VRN-2 / VCGC(政策 L123 四系統對等獨立)

操作員令(2026-10-19):「VRN-1 VRN-2 VDF VCGC都是獨立系統  互不干涉」「1. 分開命名  2. CHANGE TO 4 SYSTEMS.」;
  問答:VRN-1 = 另一團隊的倉(C:\\Users\\tonyk\\VIA-VDF-VRN,不在本倉)。
  v0155 把他系統寫的表一律標「他系統表(VRN 寫)」或「(CGC 寫)」——VRN 沒分 VRN-1 / VRN-2,VCGC 寫成 CGC。
本版(VDF 自己的表判法一字不改;只改他系統表的名字與計數):
  ① 寫入者 CGC_ 開頭 → VCGC。
  ② 寫入者 VRN2_ 開頭,或 VRN_ 代碼在本倉 functional modules/VRN/(VRN-2 的底座,L123 ①)或 VRN-2 自報船單
     docs/handoff/ai/vrn2_ship/VRN2_Bundle_latest.json(files · depends_on_tracked)找得到 → VRN-2。
  ③ 寫入者 VRN_ 開頭、本倉與 VRN-2 船單都找不到 → VRN-1(另一團隊的倉;代碼列進 other_system.vrn1_codes 供核對)。
  ④ 冊上沒登寫入者、表名 vrn_ 開頭 → 「VRN 未分辨」(分不出 VRN-1 / VRN-2 就明寫,不猜;L123 ②)。
  ⑤ 一張表多個他系統寫入者 → 名字以「 + 」相連(例 VRN-2 + VCGC);有任何 VDF_ 寫入者 → 仍是 VDF 的表(同 v0155)。
  ⑥ 結果 other_system 多 by_system(每個系統幾列)與 vrn1_codes;終端摘要行逐系統印。
作法:換掉 v0151 模組的 db_check / _print_db(v0151 main 的 db 動詞查模組全域);v0155 的 min0_rows 照用。
只讀本倉 VRN 夾的檔名與 VRN-2 船單(他系統自報),不載入、不寫他系統的檔;不抓網、不碰 TA-Lib。
只收 VIA_FROM_VCGC=YES(舊名;= 經任一系統自己的 manager / 啟動器啟動,L120 ⑥ · L123 ③)。
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
TAG = "v0156"
SELF_ID = "VDF"
VRN_DIR = VIA_ROOT / "functional modules" / "VRN"
VRN2_BUNDLE = VIA_ROOT / "docs" / "handoff" / "ai" / "vrn2_ship" / "VRN2_Bundle_latest.json"
UNSURE = "VRN 未分辨"


def _vnum_v0156(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0156(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0156(p) < _vnum_v0156(__file__)), key=_vnum_v0156)
PRIOR = _load_v0156(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


DB_MOD = PRIOR.DB_MOD                              # v0151 模組(db_check / _print_db / _write_db 在那)
_DB_CHECK_V0151 = PRIOR._DB_CHECK_V0151
_PRINT_DB_V0151 = PRIOR._PRINT_DB_V0151
min0_rows = PRIOR.min0_rows


def _keys(name: str) -> set:
    """檔名 → 可比對的鍵:去版號的整個幹名(VRN_SystemManager)+ 代碼(VRN_ENG074)。"""
    stem = re.sub(r"_v\d{4}$", "", Path(name).stem)
    out = {stem}
    m = re.match(r"(VRN2?_[A-Za-z]+\d+)", stem)
    if m:
        out.add(m.group(1))
    return out


def vrn2_keys(vrn_dir: Path | None = None, bundle: Path | None = None) -> set:
    """VRN-2 認得的寫入者鍵:本倉 VRN 夾的檔名(VRN-2 的底座)∪ VRN-2 自報船單上的路徑(只讀檔名與清單,不載入)。"""
    keys = set()
    d = VRN_DIR if vrn_dir is None else Path(vrn_dir)
    if d.is_dir():
        for p in d.iterdir():
            if p.name.startswith(("VRN_", "VRN2_")) and p.suffix in (".py", ".ps1"):
                keys |= _keys(p.name)
    b = VRN2_BUNDLE if bundle is None else Path(bundle)
    try:
        j = json.loads(b.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        j = {}
    for k in ("files", "depends_on_tracked"):
        for it in j.get(k) or []:
            path = it.get("path") if isinstance(it, dict) else it
            if path:
                keys |= _keys(str(path).replace("\\", "/").rsplit("/", 1)[-1])
    return keys


def writer_system(w: str, v2: set) -> str | None:
    """一個寫入者 → VCGC / VRN-2 / VRN-1;VDF 自己的或認不出 = None。"""
    if w.startswith("CGC_"):
        return "VCGC"
    if w.startswith("VRN2_"):
        return "VRN-2"
    if w.startswith("VRN_"):
        return "VRN-2" if _keys(w) & v2 else "VRN-1"
    return None


def other_system(row: dict, v2: set | None = None) -> str | None:
    """這列是他系統寫的表 → 系統名(VRN-1 / VRN-2 / VCGC / 「A + B」/ VRN 未分辨);VDF 自己的 · 認不出 = None。"""
    v2 = vrn2_keys() if v2 is None else v2
    ws = [w for w in str(row.get("寫入者") or "").split() if w]
    if ws:
        if any(w.startswith("VDF_") for w in ws):
            return None
        names = [writer_system(w, v2) for w in ws]
        if None in names:
            return None
        return " + ".join(sorted(set(names), key=["VRN-1", "VRN-2", "VCGC"].index))
    return UNSURE if str(row.get("表") or "").startswith("vrn_") else None


def split_rows(rows: list, v2: set | None = None) -> dict:
    """他系統表的列改 INFO,狀態寫「他系統表(<系統> 寫)」(原狀態照留);回幾列 · 原本紅黃幾列 · 每系統幾列 · VRN-1 代碼。"""
    v2 = vrn2_keys() if v2 is None else v2
    n = red = yel = 0
    by, v1 = {}, set()
    for r in rows:
        name = other_system(r, v2)
        if not name or r.get("燈") == "INFO":
            continue
        n += 1
        red += r["燈"] == "RED"
        yel += r["燈"] == "YELLOW"
        by[name] = by.get(name, 0) + 1
        v1 |= {w for w in str(r.get("寫入者") or "").split() if writer_system(w, v2) == "VRN-1"}
        why = "· 冊上沒登寫入者,表名 vrn_ 開頭 " if name == UNSURE else ""
        r["狀態"] = "他系統表(%s 寫)%s· %s · VDF 只攤開不代修" % (name, why, r["狀態"])
        r["燈"] = "INFO"
    return {"n": n, "was_red": red, "was_yellow": yel, "by_system": by, "vrn1_codes": sorted(v1)}


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
        by = " · ".join("%s %d" % kv for kv in sorted((ot.get("by_system") or {}).items()))
        print("  [他系統表] %d 列(原判 紅 %d · 黃 %d)· %s → 頁上與 CSV 照列(INFO),不計 VDF 的燈(L123 四系統互不干涉 · 只攤開不代修)"
              % (ot["n"], ot["was_red"], ot["was_yellow"], by))
        if ot.get("vrn1_codes"):
            print("  [他系統表] VRN-1 寫入者(本倉與 VRN-2 船單都沒有 → 另一團隊的倉):%s" % " ".join(ot["vrn1_codes"]))
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

    print("=== %s %s · 薄尾自測(他系統表分開命名 VRN-1 / VRN-2 / VCGC;沙盒 · 零網路)===" % (_STEM, TAG))
    td = Path(tempfile.mkdtemp(prefix="vdfmgr156_"))
    keep = os.environ.get("VIA_VDF_HEALTH_OUT")
    try:
        import duckdb
    except ImportError:
        duckdb = None
    try:
        os.environ["VIA_VDF_HEALTH_OUT"] = str(td / "out")
        vd = td / "VRN"
        vd.mkdir()
        for n in ("VRN_ENG074_FinancialPages_v0102.py", "VRN_SystemManager_v0153.py", "VRN_NoCode.txt"):
            (vd / n).write_text("#\n", encoding="utf-8")
        bd = td / "VRN2_Bundle_latest.json"
        bd.write_text(json.dumps({"files": [{"path": "functional modules/VRN/VRN2_UIAction_v0102.py"}],
                                  "depends_on_tracked": [{"path": "functional modules\\VRN\\VRN_ENG082_PolicySync_v0111.py"}]}), encoding="utf-8")
        v2 = vrn2_keys(vd, bd)
        chk("① VRN-2 鍵:本倉 VRN 夾檔名(代碼 + 去版號幹名)∪ 船單 files / depends_on_tracked(含反斜線路徑);非 .py/.ps1 不算",
            {"VRN_ENG074", "VRN_SystemManager", "VRN2_UIAction", "VRN_ENG082"} <= v2 and "VRN_NoCode" not in v2, sorted(v2))
        rows = [{"表": "tw_daily_prices", "寫入者": "VDF_ENG073 VDF_ENG078"}, {"表": "vrn_report_arith_check", "寫入者": "VRN_ENG074"},
                {"表": "via_policy_sync", "寫入者": "VRN_ENG082"}, {"表": "x2", "寫入者": "VRN2_UIAction"},
                {"表": "x1", "寫入者": "VRN_ENG999"}, {"表": "c", "寫入者": "CGC_MDL149"},
                {"表": "mix2", "寫入者": "CGC_MDL149 VRN_ENG074 VRN_ENG999"}, {"表": "vrn_report_basic", "寫入者": ""},
                {"表": "tw_universe", "寫入者": ""}, {"表": "mixed", "寫入者": "VRN_ENG074 VDF_ENG056"}, {"表": "odd", "寫入者": "XYZ_ENG001 VRN_ENG074"}]
        got = [other_system(r, v2) for r in rows]
        chk("② 分開命名:本倉 / 船單有 → VRN-2;都沒有 → VRN-1;CGC_ → VCGC;多系統以 + 相連;沒登寫入者的 vrn_ 表 → VRN 未分辨(不猜);"
            "有 VDF_ 或認不出的寫入者 → VDF 的(不放水)",
            got == [None, "VRN-2", "VRN-2", "VRN-2", "VRN-1", "VCGC", "VRN-1 + VRN-2 + VCGC", UNSURE, None, None, None], got)
        rr = [dict(r, 燈="RED", 狀態="缺表") for r in rows]
        sp = split_rows(rr, v2)
        st = {r["表"]: (r["燈"], r["狀態"]) for r in rr}
        chk("③ split_rows:他系統列改 INFO、狀態寫系統名(原狀態照留);by_system 逐系統計數;VRN-1 代碼列出;VDF 的列不動",
            sp == {"n": 7, "was_red": 7, "was_yellow": 0, "vrn1_codes": ["VRN_ENG999"],
                   "by_system": {"VRN-2": 3, "VRN-1": 1, "VCGC": 1, "VRN-1 + VRN-2 + VCGC": 1, UNSURE: 1}}
            and st["x1"] == ("INFO", "他系統表(VRN-1 寫)· 缺表 · VDF 只攤開不代修")
            and st["vrn_report_basic"] == ("INFO", "他系統表(VRN 未分辨 寫)· 冊上沒登寫入者,表名 vrn_ 開頭 · 缺表 · VDF 只攤開不代修")
            and st["tw_daily_prices"] == ("RED", "缺表") and st["odd"] == ("RED", "缺表"), (sp, st))
        real = vrn2_keys()
        chk("④ 本倉實讀:VRN 夾有檔 → VRN-2 鍵非空(VRN_ENG074 · VRN_ENG082 在本倉 → 冊上這兩個寫入者判 VRN-2)",
            not VRN_DIR.is_dir() or {"VRN_ENG074", "VRN_ENG082"} <= real, len(real))
        if duckdb is None:
            chk("⑤ duckdb 不在本境 → 只驗判法(不代裝;⑥ 要 duckdb 才跑)", True)
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
                    {"db": "vdf_tw_market.duckdb", "table": "via_policy_x", "writers": ["VRN_ENG9999"], "min_rows": 1},
                    {"db": "vdf_tw_market.duckdb", "table": "vrn_report_basic", "writers": [], "min_rows": 1}]
            (reg / "VIA_DB_Table_SSOT_v0100.json").write_text(json.dumps({"tables": book}), encoding="utf-8")
            prev = os.environ.get("VIA_FROM_VCGC")
            os.environ["VIA_FROM_VCGC"] = "YES"
            import contextlib
            import io
            buf = io.StringIO()
            try:
                o = db_check(str(td / "home"), reg, datetime.date.today())
                page = Path(o["files"]["html"]).read_text(encoding="utf-8")      # 先讀:下面 db 動詞用真冊,會蓋同一頁
                with contextlib.redirect_stdout(buf):
                    rc = DB_MOD.main(["db", "check", "--home", str(td / "home")])
            finally:
                if prev is None:
                    os.environ.pop("VIA_FROM_VCGC", None)
                else:
                    os.environ["VIA_FROM_VCGC"] = prev
            st = {r["表"]: (r["燈"], r["狀態"]) for r in o["rows"]}
            out = buf.getvalue()
            chk("⑥ db check 真跑:他系統三張 INFO 分標 VRN-2 / VRN-1 / VRN 未分辨;VDF 那張 GREEN;總燈 GREEN;頁上照列;"
                "管理員 db 動詞走本版(本倉真冊),終端逐系統印",
                o["lamp"] == "GREEN" and st["tw_daily_prices"][0] == "GREEN"
                and st["vrn_report_arith_check"][1].startswith("他系統表(VRN-2 寫)")
                and st["via_policy_x"][1].startswith("他系統表(VRN-1 寫)") and st["vrn_report_basic"][1].startswith("他系統表(VRN 未分辨 寫)")
                and o["other_system"]["by_system"] == {"VRN-2": 1, "VRN-1": 1, UNSURE: 1} and o["tag"] == "%s %s" % (_STEM, TAG)
                and "VRN-1 寫" in page and rc in (0, 1, 2) and re.search(r"\[他系統表\] \d+ 列.*VRN-2 \d+", out)
                and "VRN 未分辨" in out and "L123" in out,
                (o["lamp"], st, o.get("other_system"), rc, out[-400:]))
        src = Path(__file__).read_text(encoding="utf-8")
        imports = re.findall(r"^\s*(?:import|from)\s+([A-Za-z_][\w.]*)", src, re.M)
        chk("⑦ 加速器橋 · 網路橋在;不匯入他系統程式(只讀檔名與船單);不碰 TA-Lib;同意閘不寫",
            "VIA:ACCEL-BRIDGE" in src and "def _via_net" in src
            and not [x for x in imports if x.startswith(("CGC_", "VRN_", "VRN2_", "VCGC"))]
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
