#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VDF_ENG242_ThreePeriodDistill v0102 — 薄尾(v0100 / v0101 一字不動):先讀資料家的真庫 · 收據點名讀了哪個庫

操作員 2026-11-26 問:「他們有去讀取資料庫嗎」(資料家 …\VeritasIntelligenceAnalytics\via_database\vdf_database)。
讀碼確認:沒有。v0100 的 inventory / names 只拿 MDL012 的 default_home()(倉內 VIA_Reports\vdf_fetch\dict,擷取暫存家)
當唯一的根去找 .duckdb;VDF 自己的資料家冊 VDF_DataHome_SSOT 尾版(第一個家 = 上面那個 vdf_database)從沒被看。
桌機收據 inventory ok 5 / 缺或錯 14、names 七張表 CatalogException,都是在暫存家裡找到不完整的副本。
本版:找庫的根依序 =
  ① 資料家:VDF_MDL020_DataPlane 尾版 resolve_home()(--home 不適用 · env VIA_VDF_DB_HOME > VDF_DataHome_SSOT 冊上第一個存在的 db_home;
     同系統現成的判法,不另做)
  ② 倉內 functional modules\VDF\output_hub(工作站接點指到資料家的 output_hub;ENG239 入湖也讀這裡)
  ③ MDL012 擷取暫存家(v0100 原本唯一的根)
  第一個有命中的根勝(MDL012 find_db 原判法:output_hub 夾內優先 · 大檔優先)。
  每個庫第一次命中印一行「讀庫 <檔> ← <路徑>(哪個根)」;inventory / names 的結果多 search_roots 與 db_paths 兩欄(家目錄寫成 ~)。
唯讀開庫(read_only=True,照前版);不寫庫、不搬檔、不出網;資料內容不離開本機(收據只有路徑 · 列數 · 欄名)。
其餘動詞全部轉給 v0101 → v0100。
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)。本支零外呼。"""
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
import os
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
VDF = HERE.parent
STEM = "VDF_ENG242_ThreePeriodDistill"
VERSION = "v0102"
TAG = f"{STEM} {VERSION}"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location(f"{PRIOR_PATH.stem}_for_{VERSION}", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = getattr(PRIOR, "PRIOR", PRIOR)            # v0100 本體(main / inventory / names / m012 都在這裡)


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def tilde(p) -> str:
    s, h = str(p), str(Path.home())
    return "~" + s[len(h):] if h and s.startswith(h) else s


_DP = {}


def data_home() -> tuple:
    """資料家:VDF_MDL020_DataPlane 尾版 resolve_home()(env VIA_VDF_DB_HOME > VDF_DataHome_SSOT 冊上第一個存在的 db_home)。
    DataPlane 載不起來 → (None, 原因);不丟例外。"""
    try:
        if "mod" not in _DP:
            t = BASE.newest(VDF, "VDF_MDL020_DataPlane_v*.py")
            _DP["mod"] = BASE.load_mod(t, f"{STEM}_{VERSION}_dataplane") if t else None
        dp = _DP["mod"]
        if dp is None or not callable(getattr(dp, "resolve_home", None)):
            return None, "DataPlane 尾版不在或沒有 resolve_home"
        return dp.resolve_home(None)
    except Exception as e:  # noqa: BLE001 - 判不出家照實說,不擋
        return None, f"DataPlane 載入失敗:{type(e).__name__}: {str(e)[:120]}"


def search_roots(mod) -> list:
    """找庫的根(依序)→ [(Path, 為什麼)]。"""
    out = []
    h, why = data_home()
    if h is not None:
        out.append((Path(h), f"資料家 · {why}"))
    hub = VDF / "output_hub"
    if hub.is_dir():
        out.append((hub, "倉內 output_hub(工作站接點 → 資料家)"))
    if hasattr(mod, "default_home"):
        out.append((Path(mod.default_home()), "MDL012 擷取暫存家(v0100 原本唯一的根)"))
    seen, uniq = set(), []
    for p, w in out:
        k = os.path.normcase(str(p.resolve())) if p.exists() else os.path.normcase(str(p))
        if k not in seen:
            seen.add(k)
            uniq.append((p, w))
    return uniq


HITS = {}
ROOTS_SHOWN = []


def _wrap_find_db(mod):
    if getattr(mod, "_v0102_wrapped", False):
        return mod
    orig = mod.find_db

    def find_db(name, roots):
        sr = search_roots(mod)
        if not ROOTS_SHOWN:
            ROOTS_SHOWN.extend((tilde(p), w, p.is_dir()) for p, w in sr)
            if not any(w.startswith("資料家") for _, w in sr):
                _h, dwhy = data_home()
                BASE.say(f"  [黃] 資料家沒判到:{dwhy} → 只能在倉內 / 暫存家找(設 VIA_VDF_DB_HOME 或補 VDF_DataHome_SSOT 冊)")
            for i, (p, w, ok) in enumerate(ROOTS_SHOWN, 1):
                BASE.say(f"  找庫的根 {i}:{p}({w}){'' if ok else ' · 這台不在'}")
        extra = [Path(r) for r in (roots or [])]
        allr = [p for p, _ in sr] + [r for r in extra if all(os.path.normcase(str(r)) != os.path.normcase(str(p)) for p, _ in sr)]
        hit = orig(name, allr)
        if hit is not None and name not in HITS:
            hp = os.path.normcase(str(Path(hit).resolve()))
            why = next((w for p, w in sr if p.exists() and hp.startswith(os.path.normcase(str(p.resolve())))), "前版給的根")
            HITS[name] = {"path": tilde(hit), "root": why}
            BASE.say(f"  讀庫 {name} ← {tilde(hit)}({why})")
        elif hit is None and name not in HITS:
            HITS[name] = {"path": None, "root": "所有根都沒有"}
            BASE.say(f"  讀庫 {name} ← 找不到(所有根都沒有)")
        return hit

    mod.find_db = find_db
    mod._v0102_wrapped = True
    return mod


_ORIG = {"m012": BASE.m012, "inventory": BASE.inventory, "names": BASE.names}


def m012(*a, **k):
    return _wrap_find_db(_ORIG["m012"](*a, **k))


def inventory(mod, rows_or_book, roots=None, lake=None):
    if hasattr(mod, "find_db"):
        _wrap_find_db(mod)
    res = _ORIG["inventory"](mod, rows_or_book, roots, lake)
    res["search_roots"] = [{"root": p, "why": w, "exists": ok} for p, w, ok in ROOTS_SHOWN]
    res["db_paths"] = dict(HITS)
    return res


def names(cols_by_src, nb):
    res = _ORIG["names"](cols_by_src, nb)
    res["search_roots"] = [{"root": p, "why": w, "exists": ok} for p, w, ok in ROOTS_SHOWN]
    res["db_paths"] = dict(HITS)
    missing = sorted(k for k, v in HITS.items() if v.get("path") is None)
    empty = sorted(k for k, v in (cols_by_src or {}).items() if not v)
    if missing or empty or not cols_by_src:          # 要求的目標缺一不綠:沒讀到庫 / 表讀不到欄 = 黃,逐項點名
        res["lamp"] = "YELLOW"
        res["note"] = ("沒找到的庫:" + " · ".join(missing) if missing else "") + (
            ("；" if missing and empty else "") + "讀不到欄的表:" + " · ".join(empty) if empty else "") or "一張表都沒讀到"
    return res


def _install():
    BASE.m012, BASE.inventory, BASE.names = m012, inventory, names
    BASE.TAG = TAG


def _uninstall():
    BASE.m012, BASE.inventory, BASE.names = _ORIG["m012"], _ORIG["inventory"], _ORIG["names"]
    BASE.TAG = getattr(PRIOR, "TAG", BASE.TAG)


_install()


def main() -> int:
    if sys.argv[1:2] in (["--selftest"], ["selftest"]):
        return selftest()
    return BASE.main()


def selftest() -> int:
    ok, bad = [], []

    def chk(name, cond, note=""):
        (ok if cond else bad).append(name)
        print(f"  [{'OK' if cond else 'NG'}] {name}" + (f" · {str(note)[:300]}" if note and not cond else ""), flush=True)

    chk("加速器載入(VIA_ACCEL is not None)", VIA_ACCEL is not None)
    chk("網路工具載入(_via_net() is not None · 載入不出網)", _via_net() is not None, VIA_NET_TOOL_PATH)
    chk("前版 = 同家族比自己小的最大版 · 已裝進 v0100 本體(m012 · inventory · names · 橫幅)",
        _vnum(PRIOR_PATH) < _vnum(Path(__file__)) and BASE.m012 is m012 and BASE.inventory is inventory and BASE.names is names and BASE.TAG == TAG)
    keep_env = os.environ.get("VIA_VDF_DB_HOME")
    try:
        duckdb = BASE._duck()
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            home, stage = td / "via_database" / "vdf_database", td / "vdf_fetch" / "dict"
            (home / "output_hub").mkdir(parents=True)
            stage.mkdir(parents=True)
            for p, n in ((home / "output_hub" / "vdf_tw_market.duckdb", 5), (stage / "vdf_tw_market.duckdb", 2)):
                c = duckdb.connect(str(p))
                c.execute("CREATE TABLE tw_daily_prices AS SELECT DATE '2026-11-20' + CAST(i AS INTEGER) AS date, '2330' AS code, 100.0 + i AS close FROM range(%d) t(i)" % n)
                c.close()
            c = duckdb.connect(str(stage / "only_stage.duckdb"))
            c.execute("CREATE TABLE t AS SELECT 1 AS a")
            c.close()
            os.environ["VIA_VDF_DB_HOME"] = str(home)          # 資料家指到暫存夾(不是同意閘;跑完還原)
            h, why = data_home()
            chk("資料家照 DataPlane resolve_home:env VIA_VDF_DB_HOME 指的夾", h is not None and Path(h) == home, (h, why))

            class FakeMod:
                @staticmethod
                def default_home():
                    return stage

                @staticmethod
                def load_book():
                    return {"groups": [{"id": "tw_daily", "sources": [
                        {"type": "duckdb", "db": "vdf_tw_market.duckdb", "table": "tw_daily_prices", "date_col": "date", "key_col": "code"},
                        {"type": "duckdb", "db": "only_stage.duckdb", "table": "t"},
                        {"type": "duckdb", "db": "nowhere.duckdb", "table": "x"}]}]}

            mm = _ORIG["m012"]()
            FakeMod.find_db = staticmethod(mm.find_db)
            HITS.clear()
            ROOTS_SHOWN.clear()
            res = inventory(FakeMod, None)
            by = {r["db"]: r for r in res["rows"]}
            dp = res["db_paths"]
            chk("同名庫兩處都有 → 讀資料家的那份(5 列),不是暫存家的副本(2 列)",
                by["vdf_tw_market.duckdb"]["state"] == "OK" and str(home) in str(Path(dp["vdf_tw_market.duckdb"]["path"].replace("~", str(Path.home()), 1)))
                and "資料家" in dp["vdf_tw_market.duckdb"]["root"] and by["vdf_tw_market.duckdb"].get("rows") == 5, (by.get("vdf_tw_market.duckdb"), dp))
            chk("資料家沒有的庫 → 退到暫存家照讀(前版行為保留)",
                by["only_stage.duckdb"]["state"] == "OK" and "暫存家" in dp["only_stage.duckdb"]["root"], dp.get("only_stage.duckdb"))
            chk("哪裡都沒有 → DB_MISSING 照實 · 收據寫「所有根都沒有」",
                by["nowhere.duckdb"]["state"] == "DB_MISSING" and dp["nowhere.duckdb"]["path"] is None, by.get("nowhere.duckdb"))
            chk("收據多 search_roots(依序:資料家 → 倉內 output_hub → 暫存家)與 db_paths",
                res["search_roots"] and "資料家" in res["search_roots"][0]["why"] and "暫存家" in res["search_roots"][-1]["why"], res["search_roots"])
            nres = names({"vdf_tw_market.duckdb:tw_daily_prices": ["date", "code", "close"], "x.duckdb:t": []}, BASE.name_book())
            chk("names:有表讀不到欄 / 有庫沒找到 → 黃並點名(不再 0 欄也綠)",
                nres["lamp"] == "YELLOW" and "x.duckdb:t" in nres.get("note", "") and "nowhere.duckdb" in nres.get("note", ""), nres.get("note"))
            os.environ["VIA_VDF_DB_HOME"] = str(td / "not_here")
            h2, why2 = data_home()
            chk("資料家不在 → (None, 原因),不丟例外;根只剩倉內 / 暫存家", h2 is None and "不在" in why2
                and all("資料家 ·" not in w for _, w in search_roots(FakeMod)), (h2, why2))
    finally:
        if keep_env is None:
            os.environ.pop("VIA_VDF_DB_HOME", None)
        else:
            os.environ["VIA_VDF_DB_HOME"] = keep_env
        HITS.clear()
        ROOTS_SHOWN.clear()
    _uninstall()                                   # 前版鏈自測照前版原行為(不碰這台的真資料家)
    try:
        print(f"[前版] {PRIOR_PATH.name} 自測(本版換裝卸下)", flush=True)
        rc = PRIOR.selftest()
    finally:
        _install()
    chk("前版 v0101 鏈自測照過(rc 0;它自己再擦同意閘跑 v0100)· 跑完本版又換上", rc == 0 and BASE.m012 is m012, rc)
    chk("自測後 VIA_VDF_DB_HOME 原樣還原", os.environ.get("VIA_VDF_DB_HOME") == keep_env)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("檔面:雙橋在 · 唯讀開庫(本檔不寫真庫)· 零 TA-Lib · 不設同意閘",
        "[VIA:ACCEL-BRIDGE:v0100]" in src and "[VIA:NET-BRIDGE:v0100]" in src
        and not re.search(r"^\s*(import|from)\s+(talib|requests)", src, re.M)
        and not re.search(r"^\s*os\.environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", src, re.M))
    print(f"{TAG} selftest {len(ok)}/{len(ok) + len(bad)}" + (" · 不過:" + " · ".join(bad) if bad else ""), flush=True)
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
