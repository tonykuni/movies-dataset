#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_SystemManager v0156 — 薄尾:db check 的他系統表分開命名 VRN-1 / VRN-2 / VCGC(政策 L123 四系統對等獨立)· 互對照兩個以上相同即成功

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
  ⑦ 互對照(操作員 2026-10-19「互對照兩個以上相同即算對照成功  自測實測自改自完成」):v0122 的 universe xcheck 判法改
     「兩個以上來源相同即算對照成功」(容許差與來源照冊 VDF_InputUniverse_SSOT xcheck 節,不改冊)——
     加權收盤:當日有值的來源兩兩比(官方↔ENG055 用 official_vs_agg;有 yf 的對用 vs_yf);至少一對在容許內 → GREEN(第三個列 outlier,不擋);
       兩個以上來源但沒有任何一對相同 → RED;只一個來源 → YELLOW(沒得對照);一個都沒有 → NODATA。
     三表同日代號:有資料的表兩兩比代號集合;至少兩表完全相同 → GREEN;兩表以上有資料但都不同 → YELLOW(列缺漏樣本);
       庫裡不到兩張表 → YELLOW(沒得對照);表在但當日少於兩表有資料 → 最新日 YELLOW(日更未齊)、舊日 RED。
     universe xcheck 末行多印「[計] VDF 互對照 …」(ActivateVDF 的步驟摘要讀這行)。前版 v0122 自測跑前換回原判法。
  ⑧ 庫在哪(操作員 2026-10-19「查之前的對話紀錄,找到資料庫的位置位於文件之中」):文件記載資料家 = VIA_DataHome_SSOT home_win
     C:\\Users\\tonyk\\VIA System\\via_database(批490 操作員宣告;鏡根 via_database\\movies-dataset\\data\\…\\VDF\\output_hub;
     db move 的目的地例 via_database\\vdf_database)。v0151 的 db_home 只認 --home > VIA_VDF_DB_HOME > 倉內 output_hub,
     而 PS 啟動器預設把倉內 output_hub 當 --home 傳進來 → 工作站 db check 量的是倉內夾,不是資料家。本版:
     沒給 --home、或給的就是倉內預設 output_hub → 照冊上優先序比候選(VIA_VDF_DB_HOME > VIA_DATA_HOME > 冊 home_win / home_posix
     [各看 vdf_database · 鏡根 VDF output_hub · 家本身] > 倉內 output_hub),選「冊上的庫找到最多本」的那一個(同分取前面的);
     給了別的 --home 或設了 VIA_VDF_DB_HOME = 操作員指定,照用。結果多 home_pick(選誰 · 為什麼 · 每個候選找到幾本),
     終端印「[庫位置] …」;新動詞 db where [--home 夾] [--json] 只回選到的庫位置(ActivateVDF 先問它,check / refill 用同一個家)。
作法:換掉 v0151 模組的 db_check / _print_db(v0151 main 的 db 動詞查模組全域);v0155 的 min0_rows 照用;
      換掉 v0122 模組的 xcheck_index / xcheck_counts / xcheck / universe(查模組全域)。
只讀本倉 VRN 夾的檔名與 VRN-2 船單(他系統自報)與 VDF 自己的庫,不載入、不寫他系統的檔;不抓網、不碰 TA-Lib。
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
RULE = "兩個以上來源相同即算對照成功"


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


DATAHOME_GLOB = "VIA_DataHome_SSOT_v*.json"
MIRROR_REL = Path("movies-dataset") / "data" / "VeritasIntelligenceAnalytics" / "functional modules" / "VDF" / "output_hub"


def repo_hub() -> Path:
    return Path(os.path.realpath(HERE / "output_hub"))


def datahome_roots(reg: Path | None = None) -> list:
    """資料家根(照冊 precedence):env VIA_DATA_HOME > 冊 home_win(Windows)/ home_posix。只讀冊,不載入 VCGC 程式。"""
    out = []
    if os.environ.get("VIA_DATA_HOME"):
        out.append(("env VIA_DATA_HOME", Path(os.environ["VIA_DATA_HOME"])))
    hits = sorted((reg or DB_MOD.REG).glob(DATAHOME_GLOB), key=_vnum_v0156)
    if hits:
        try:
            j = json.loads(hits[-1].read_text(encoding="utf-8"))
        except (OSError, ValueError):
            j = {}
        key = "home_win" if os.name == "nt" else "home_posix"
        if j.get(key):
            out.append(("%s %s" % (hits[-1].name, key), Path(j[key])))
    return out


def home_candidates(reg: Path | None = None) -> list:
    """候選家(優先序):VIA_VDF_DB_HOME 已在 locate 先處理;資料家各根的 vdf_database · 鏡根 VDF output_hub · 根本身;最後倉內 output_hub(退路)。"""
    cands, seen = [], set()

    def add(why, p):
        rp = os.path.realpath(str(p))
        if rp not in seen and Path(rp).is_dir():
            seen.add(rp)
            cands.append((why, Path(rp)))
    for why, root in datahome_roots(reg):
        add(why + " → vdf_database", root / "vdf_database")
        add(why + " → 鏡根 VDF output_hub", root / MIRROR_REL)
        add(why, root)
    add("倉內 output_hub(退路)", repo_hub())
    return cands


def locate_db_home(explicit: str | None = None, reg: Path | None = None) -> dict:
    """選庫位置:給了別的 --home / 設了 VIA_VDF_DB_HOME = 照用;否則候選裡「冊上的庫找到最多本」的那個(同分取前面)。"""
    if explicit and os.path.realpath(explicit) != str(repo_hub()):
        return {"picked": str(Path(explicit)), "why": "--home 指定(照用)", "candidates": []}
    if os.environ.get("VIA_VDF_DB_HOME"):
        return {"picked": os.environ["VIA_VDF_DB_HOME"], "why": "env VIA_VDF_DB_HOME 指定(照用)", "candidates": []}
    _src, book = DB_MOD.table_book(reg)
    names = sorted({t["db"] for t in book})
    rows = []
    for why, p in home_candidates(reg):
        found = sum(1 for n in names if DB_MOD._find_db(p, n)[0] is not None)
        rows.append({"home": str(p), "why": why, "found": found, "total": len(names)})
    if not rows:
        return {"picked": str(repo_hub()), "why": "沒有候選在(照倉內 output_hub)", "candidates": []}
    best = max(rows, key=lambda r: (r["found"], -rows.index(r)))
    tail = "(倉內預設 --home 不算指定)" if explicit else ""
    return {"picked": best["home"], "why": "%s · 冊上 %d 本庫找到 %d 本%s" % (best["why"], best["total"], best["found"], tail), "candidates": rows}


def db_check(home: str | None = None, reg: Path | None = None, today=None, write: bool = True) -> dict:
    pick = locate_db_home(home, reg)
    o = _DB_CHECK_V0151(pick["picked"], reg, today, write=False)
    o["home_pick"] = pick
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
    hp = o.get("home_pick")
    if hp:
        print("  [庫位置] %s · %s" % (hp["picked"], hp["why"]))
        for c in hp.get("candidates") or []:
            print("    候選 %s · 找到 %d/%d · %s" % (c["home"], c["found"], c["total"], c["why"]))
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


def _owner_module(name: str):
    """沿前版鏈往下找真正定義 name 的那一版模組(xcheck_index / xcheck_counts / universe 在 v0122)。"""
    m = PRIOR
    for _ in range(64):
        if name in vars(m) and getattr(vars(m)[name], "__module__", None) == m.__name__:
            return m
        m = vars(m).get("PRIOR")
        if m is None:
            break
    return None


XM = _owner_module("xcheck_index")
_UNIVERSE_V0122 = XM.universe
_XCHECK_V0122 = XM.xcheck
_LAST = {}


def agree_pairs(vals: dict, tol: dict) -> tuple:
    """當日有值的來源兩兩比 → (相同的對, 全部比過的對 [(a, b, 相對差)])。官方↔ENG055 用 official_vs_agg;有 yf 用 vs_yf。"""
    have = [k for k in ("official", "agg", "yf") if vals.get(k)]
    pairs, ok = [], []
    for i, a in enumerate(have):
        for b in have[i + 1:]:
            base = vals["official"] if "official" in (a, b) else vals[a]
            d = abs(vals[a] - vals[b]) / base
            t = tol["official_vs_agg"] if {a, b} == {"official", "agg"} else tol["vs_yf"]
            pairs.append((a, b, d))
            if d <= t:
                ok.append((a, b))
    return ok, pairs


def xcheck_index(days: int = 20, dbs: dict | None = None) -> dict:
    dbs = dbs or {"idx": XM.DB_IDX, "tw": XM.DB_TW, "gl": XM.DB_GL}
    tol = XM.book()["xcheck"]["index"]["tolerance"]
    off = XM._series(dbs["idx"], "tw_index_daily", "date", "close", "index_code = 'TAIEX'")
    agg = XM._series(dbs["tw"], "tw_market_agg", "date", "taiex")
    yf = XM._series(dbs["gl"], "global_daily", "date", "close", "ticker = '^TWII'")
    dates = sorted(set(off) | set(agg) | set(yf), reverse=True)[:days]
    rows, run = [], XM._today()
    for d in sorted(dates):
        v = {"official": off.get(d), "agg": agg.get(d), "yf": yf.get(d)}
        n = sum(1 for x in v.values() if x)
        ok, pairs = agree_pairs(v, tol)
        same = sorted({k for p in ok for k in p})
        lamp = "NODATA" if n == 0 else ("YELLOW" if n == 1 else ("GREEN" if ok else "RED"))
        rows.append({"date": d, "official_close": v["official"], "agg_taiex": v["agg"], "yf_close": v["yf"], "n_sources": n,
                     "max_rel_diff": round(max((x for _a, _b, x in pairs), default=0.0), 6), "lamp": lamp, "run": run,
                     "agree": "+".join(same), "outlier": "+".join(k for k in ("official", "agg", "yf") if v[k] and k not in same) if ok else ""})
    lamps = [r["lamp"] for r in rows]
    verdict = "NODATA" if not rows else ("RED" if "RED" in lamps else ("GREEN" if all(x == "GREEN" for x in lamps) else "YELLOW"))
    return {"rows": rows, "verdict": verdict, "have": {"official": len(off), "agg": len(agg), "yf": len(yf)}, "rule": RULE}


def same_sets(s: dict) -> list:
    """有資料的表兩兩比代號集合 → 完全相同的對 [(a, b)]。"""
    names = [k for k, v in s.items() if v]
    return [(a, b) for i, a in enumerate(names) for b in names[i + 1:] if s[a] == s[b]]


def xcheck_counts(days: int = 20, db: Path | None = None) -> dict:
    db = db or XM.DB_TW
    rx = XM.book()["inputs"][0]["code_regex"]
    con = XM._con(db)
    if con is None:
        return {"rows": [], "verdict": "NODATA", "note": f"庫不在:{db}"}
    try:
        have = XM._tables(con)
        if "tw_daily_prices" not in have:
            return {"rows": [], "verdict": "NODATA", "note": "tw_daily_prices 不在"}
        dates = [r[0] for r in con.execute("SELECT DISTINCT substr(CAST(date AS VARCHAR), 1, 10) d FROM tw_daily_prices "
                                           f"ORDER BY d DESC LIMIT {int(days)}").fetchall()]
        if not dates:
            return {"rows": [], "verdict": "NODATA", "note": "價表空"}
        lo = min(dates)
        sets, missing = {}, []
        for name, t, code in XM.COUNT_SRC:
            if t not in have:
                missing.append(t)
                continue
            q = (f"SELECT DISTINCT substr(CAST(date AS VARCHAR), 1, 10) d, {code} c FROM \"{t}\" "
                 f"WHERE substr(CAST(date AS VARCHAR), 1, 10) >= ? AND regexp_full_match({code}, ?)")
            per = {}
            for d, c in con.execute(q, [lo, rx]).fetchall():
                per.setdefault(d, set()).add(c)
            sets[name] = per
    finally:
        con.close()
    rows, run, newest = [], XM._today(), max(dates)
    for d in sorted(dates):
        s = {n: sets[n].get(d, set()) for n in sets}
        ns = {n: len(v) for n, v in s.items()}
        filled = [n for n in s if s[n]]
        allv = [s[n] for n in filled]
        inter = set.intersection(*allv) if allv else set()
        union = set.union(*allv) if allv else set()
        pairs = same_sets(s)
        same = sorted({k for p in pairs for k in p})
        if pairs:
            lamp = "GREEN"
        elif len(filled) >= 2 or len(s) < 2:
            lamp = "YELLOW"                                     # 兩表以上有資料但不同 · 或冊上的表本庫不到兩張(沒得對照)
        else:
            lamp = "YELLOW" if d == newest else "RED"            # 少於兩表有資料:最新日 = 日更未齊(黃);舊日 = 紅
        rows.append({"date": d, "prices_n": ns.get("prices"), "chips_n": ns.get("chips"), "trading_n": ns.get("trading"),
                     "all3_n": len(inter), "only_sample": ",".join(sorted(union - inter)[:8]), "lamp": lamp, "run": run,
                     "agree": "+".join(same)})
    lamps = [r["lamp"] for r in rows]
    verdict = "RED" if "RED" in lamps else ("GREEN" if all(x == "GREEN" for x in lamps) else "YELLOW")
    return {"rows": rows, "verdict": verdict, "missing_tables": missing, "rule": RULE}


def xcheck(days: int = 20, write: bool = True, dbs: dict | None = None, out_db=None, reports=None) -> dict:
    kw = {k: v for k, v in (("out_db", out_db), ("reports", reports)) if v is not None}
    rep = _XCHECK_V0122(days, write, dbs, **kw)
    _LAST.clear()
    _LAST.update(rep)
    return rep


def summary_line(rep: dict) -> str:
    ix, ct = rep.get("index") or {}, rep.get("counts") or {}
    g = lambda rows: sum(1 for r in rows or [] if r.get("lamp") == "GREEN")     # noqa: E731
    return ("[計] VDF 互對照(%s)· 加權收盤 %s(%d/%d 日兩來源以上相同)· 三表同日代號 %s(%d/%d 日兩表以上相同)"
            % (RULE, ix.get("verdict"), g(ix.get("rows")), len(ix.get("rows") or []),
               ct.get("verdict"), g(ct.get("rows")), len(ct.get("rows") or [])))


def universe(args: list) -> int:
    _LAST.clear()
    rc = _UNIVERSE_V0122(args)
    if (args[:1] or [""])[0] == "xcheck" and _LAST:
        print("  " + summary_line(_LAST))
    return rc


_ORIG = (XM.xcheck_index, XM.xcheck_counts, XM.xcheck, XM.universe)   # v0122 原判法:前版自測照它驗
XM.xcheck_index = xcheck_index
XM.xcheck_counts = xcheck_counts
XM.xcheck = xcheck
XM.universe = universe


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args[:2]:
        return selftest()
    if args[:2] == ["db", "where"]:
        if os.environ.get("VIA_FROM_VCGC") != "YES":
            print("[VDF] 拒絕。只能經 VDF 啟動器 / via-vcgc(VIA_FROM_VCGC=YES)。")
            return 2
        h = args[args.index("--home") + 1] if "--home" in args and args.index("--home") + 1 < len(args) else None
        pick = locate_db_home(h)
        if "--json" in args:
            print(json.dumps(pick, ensure_ascii=False))
        for c in pick["candidates"]:
            print("  候選 %s · 找到 %d/%d · %s" % (c["home"], c["found"], c["total"], c["why"]))
        print("[計] VDF db where · %s · %s" % (pick["picked"], pick["why"]))
        return 0
    return PRIOR.main(args)


def _selftest_xcheck(chk) -> None:
    """互對照的六檢(⑧–⑬);沙盒庫 · 零網路。"""
    import contextlib
    import io
    import shutil
    import tempfile
    tol = {"official_vs_agg": 0.0005, "vs_yf": 0.005}
    cases = [({"official": 100.0, "agg": 100.01, "yf": 120.0}, [("official", "agg")]),
             ({"official": 100.0, "agg": 103.0, "yf": 100.2}, [("official", "yf")]),
             ({"official": None, "agg": 100.0, "yf": 100.3}, [("agg", "yf")]),
             ({"official": 100.0, "agg": 103.0, "yf": 110.0}, []),
             ({"official": 100.0, "agg": None, "yf": None}, []),
             ({"official": 100.0, "agg": 100.2, "yf": None}, [])]           # 差 0.2%:官方↔ENG055 容許 0.05% → 不相同
    got = [agree_pairs(v, tol)[0] for v, _e in cases]
    chk("⑧ 兩兩比:官方↔ENG055 用 0.0005、有 yf 的對用 0.005;相同的對照列(第三個不合不擋)", got == [e for _v, e in cases], got)
    s = {"prices": {"1101", "2330"}, "chips": {"1101"}, "trading": {"1101", "2330"}}
    chk("⑨ 代號集合:完全相同的兩表才算相同;空表不算", same_sets(s) == [("prices", "trading")]
        and same_sets({"prices": {"1"}, "chips": set(), "trading": {"1"}}) == [("prices", "trading")]
        and same_sets({"prices": {"1"}, "chips": {"2"}, "trading": set()}) == [], same_sets(s))
    try:
        import duckdb
    except ImportError:
        duckdb = None
    td = Path(tempfile.mkdtemp(prefix="vdfmgr157_"))
    try:
        if duckdb is None:
            chk("⑬ duckdb 不在本境 → 互對照只驗判法(不代裝;⑩–⑫ 要 duckdb 才跑)", True)
        else:
            idx, tw, gl = td / "idx.duckdb", td / "tw.duckdb", td / "gl.duckdb"
            c = duckdb.connect(str(idx))
            c.execute("create table tw_index_daily(date date, index_code varchar, close double)")
            c.execute("insert into tw_index_daily values ('2026-10-01','TAIEX',100),('2026-10-02','TAIEX',100),('2026-10-03','TAIEX',100),"
                      "('2026-10-05','TAIEX',100)")
            c.close()
            c = duckdb.connect(str(tw))
            c.execute("create table tw_market_agg(date date, taiex double)")
            c.execute("insert into tw_market_agg values ('2026-10-01',100.01),('2026-10-02',103),('2026-10-03',103),('2026-10-06',99)")
            c.execute("create table tw_daily_prices(date date, ticker varchar)")
            c.execute("create table tw_chip_inst(date date, code varchar)")
            c.execute("create table tw_trading_daily(date date, code varchar)")
            for d, pr, ch, trd in (("2026-10-01", ["1101.TW", "2330.TW"], ["1101"], ["1101", "2330"]),
                                   ("2026-10-02", ["1101.TW", "2330.TW"], ["1101"], ["1101"]),
                                   ("2026-10-03", ["1101.TW"], [], [])):
                for t, xs in (("tw_daily_prices", pr), ("tw_chip_inst", ch), ("tw_trading_daily", trd)):
                    for x in xs:
                        c.execute("insert into %s values (?, ?)" % t, [d, x])
            c.close()
            c = duckdb.connect(str(gl))
            c.execute("create table global_daily(date date, ticker varchar, close double)")
            c.execute("insert into global_daily values ('2026-10-01','^TWII',130),('2026-10-02','^TWII',100.2),('2026-10-03','^TWII',110)")
            c.close()
            ix = xcheck_index(20, {"idx": idx, "tw": tw, "gl": gl})
            lam = {str(r["date"])[:10]: (r["lamp"], r["agree"], r["outlier"]) for r in ix["rows"]}
            chk("⑩ 加權收盤真庫:官方+ENG055 相同、yf 偏 → GREEN(yf 列 outlier);官方+yf 相同 → GREEN;三個都不同 → RED;"
                "只一個來源 → YELLOW;總判 RED",
                lam.get("2026-10-01") == ("GREEN", "agg+official", "yf") and lam.get("2026-10-02") == ("GREEN", "official+yf", "agg")
                and lam.get("2026-10-03")[0] == "RED" and lam.get("2026-10-05")[0] == "YELLOW" and lam.get("2026-10-06")[0] == "YELLOW"
                and ix["verdict"] == "RED", lam)
            solo = td / "solo.duckdb"
            c = duckdb.connect(str(solo))
            c.execute("create table tw_daily_prices(date date, ticker varchar)")
            c.execute("insert into tw_daily_prices values ('2026-10-01','1101.TW'),('2026-10-02','1101.TW')")
            c.close()
            cs = xcheck_counts(20, solo)
            ct = xcheck_counts(20, tw)
            lc = {str(r["date"])[:10]: (r["lamp"], r["agree"]) for r in ct["rows"]}
            chk("⑪ 三表同日代號真庫:價量=成交值 → GREEN(籌碼少照列);籌碼=成交值 → GREEN(價量多照列);最新日只一表有 → YELLOW;庫裡只一張表 → 舊日也 YELLOW(沒得對照)",
                lc == {"2026-10-01": ("GREEN", "prices+trading"), "2026-10-02": ("GREEN", "chips+trading"),
                       "2026-10-03": ("YELLOW", "")}
                and [r["lamp"] for r in cs["rows"]] == ["YELLOW", "YELLOW"] and cs["verdict"] == "YELLOW", (lc, cs.get("rows")))
            buf = io.StringIO()
            prev = {k: getattr(XM, k) for k in ("DB_IDX", "DB_TW", "DB_GL")}
            XM.DB_IDX, XM.DB_TW, XM.DB_GL = idx, tw, gl
            try:
                with contextlib.redirect_stdout(buf):
                    rc = XM.universe(["xcheck", "--dry"])
            finally:
                for k, v in prev.items():
                    setattr(XM, k, v)
            out = buf.getvalue()
            chk("⑫ universe xcheck 動詞走本版:末行「[計] VDF 互對照」帶規則 · 兩判;紅 → rc 1;--dry 不寫",
                re.search(r"\[計\] VDF 互對照\(" + RULE + r"\)· 加權收盤 RED\(2/5 日.*三表同日代號 YELLOW\(2/3 日", out) is not None and rc == 1,
                (rc, out[-400:]))
    finally:
        shutil.rmtree(td, ignore_errors=True)


def _selftest_where(chk) -> None:
    """庫在哪的三檢(⑭–⑯);沙盒冊與沙盒家 · 不碰真資料家。"""
    import contextlib
    import io
    import shutil
    import tempfile
    td = Path(tempfile.mkdtemp(prefix="vdfwhere156_"))
    keep = {k: os.environ.get(k) for k in ("VIA_DATA_HOME", "VIA_VDF_DB_HOME", "VIA_FROM_VCGC")}
    try:
        for k in ("VIA_DATA_HOME", "VIA_VDF_DB_HOME"):
            os.environ.pop(k, None)
        reg = td / "reg"
        reg.mkdir()
        (reg / "VIA_DB_Table_SSOT_v0100.json").write_text(json.dumps({"tables": [
            {"db": "w_a_test.duckdb", "table": "t1"}, {"db": "w_b_test.duckdb", "table": "t2"}]}), encoding="utf-8")
        book_home = td / "bookhome"
        mirror = book_home / MIRROR_REL / "mega"
        mirror.mkdir(parents=True)
        (mirror / "w_a_test.duckdb").write_bytes(b"x")
        (book_home / "w_b_test.duckdb").write_bytes(b"x")               # 家本身也有一本:鏡根只找到 1 本 · 家本身 rglob 找到 2 本
        key = "home_win" if os.name == "nt" else "home_posix"
        (reg / "VIA_DataHome_SSOT_v0100.json").write_text(json.dumps({key: str(book_home)}), encoding="utf-8")
        envh = td / "envhome"
        (envh / "vdf_database").mkdir(parents=True)
        for n in ("w_a_test.duckdb", "w_b_test.duckdb"):
            (envh / "vdf_database" / n).write_bytes(b"x")
        p0 = locate_db_home(None, reg)
        p1 = locate_db_home(str(repo_hub()), reg)
        chk("⑭ 沒給 --home(或給的是倉內預設 output_hub)→ 照冊上的資料家比候選:找到最多本的贏(家本身 2/2 > 鏡根 1/2 > 倉內 0/2;倉內夾不在就不列)",
            Path(p0["picked"]) == Path(os.path.realpath(book_home)) and p1["picked"] == p0["picked"]
            and [c["found"] for c in p0["candidates"] if not c["why"].startswith("倉內")] == [1, 2]
            and all(c["found"] == 0 for c in p0["candidates"] if c["why"].startswith("倉內"))   # 倉內 output_hub 不在(CI 稀疏檢出)= 不列,在 = 0 本
            and "倉內預設" in p1["why"], (p0, p1))
        os.environ["VIA_DATA_HOME"] = str(envh)
        p2 = locate_db_home(None, reg)
        os.environ["VIA_VDF_DB_HOME"] = str(td / "op")
        p3 = locate_db_home(None, reg)
        p4 = locate_db_home(str(td / "given"), reg)
        chk("⑮ 優先序:env VIA_DATA_HOME 的 vdf_database(2/2)排在冊 home 前、同分取前面;VIA_VDF_DB_HOME / 給了別的 --home = 操作員指定,照用",
            Path(p2["picked"]) == Path(os.path.realpath(envh / "vdf_database")) and p2["candidates"][0]["why"].startswith("env VIA_DATA_HOME")
            and p3["picked"] == str(td / "op") and p4["picked"] == str(td / "given") and not p4["candidates"], (p2, p3, p4))
        os.environ.pop("VIA_VDF_DB_HOME", None)
        oc = db_check(None, reg, write=False)
        os.environ["VIA_FROM_VCGC"] = "YES"
        buf = io.StringIO()
        keep_reg = DB_MOD.REG
        DB_MOD.REG = reg
        try:
            with contextlib.redirect_stdout(buf):
                rc = main(["db", "where", "--json"])
        finally:
            DB_MOD.REG = keep_reg
        out = buf.getvalue()
        chk("⑯ db check 量的就是選到的家(home · home_pick 同一個);db where 動詞:回 JSON 與「[計] VDF db where · <家> · 為什麼」;rc 0",
            Path(oc["home"]) == Path(p2["picked"]) and oc.get("home_pick", {}).get("picked") == p2["picked"] and rc == 0 and json.loads(out.splitlines()[0])["picked"] == p2["picked"] and "[計] VDF db where · " + p2["picked"] in out, out[-300:])
    finally:
        for k, v in keep.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(td, ignore_errors=True)


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

    print("=== %s %s · 薄尾自測(他系統表分開命名 VRN-1 / VRN-2 / VCGC · 互對照 %s;沙盒 · 零網路)===" % (_STEM, TAG, RULE))
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
        _selftest_xcheck(chk)
        _selftest_where(chk)
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
    if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1":
        return 0
    keep = (XM.xcheck_index, XM.xcheck_counts, XM.xcheck, XM.universe)
    XM.xcheck_index, XM.xcheck_counts, XM.xcheck, XM.universe = _ORIG   # 前版自測照前版判法驗
    try:
        prc = PRIOR.selftest()
    finally:
        XM.xcheck_index, XM.xcheck_counts, XM.xcheck, XM.universe = keep
    return 0 if prc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
