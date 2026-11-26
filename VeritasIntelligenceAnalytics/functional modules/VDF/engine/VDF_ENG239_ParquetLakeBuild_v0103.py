#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VDF_ENG239_ParquetLakeBuild v0103 — 薄尾(v0100–v0102 一字不動):入湖先讀資料家 · 起日照操作員裁定

操作員 2026-11-26:「準備建湖指令」。桌機 vdf3:蒸餾 / 核對黃在「湖目錄不在(VDF_catalog.duckdb)」。
讀碼:v0100 run() 的 find_dbs() 只掃倉內 functional modules\VDF\output_hub 與 VIA_Reports\vdf_fetch(跟 ENG242 v0101 以前同一個盲點);
資料家 …\via_database\vdf_database(VDF_DataHome_SSOT 第一個家)沒有明著讀 —— 只有倉內 output_hub 剛好是接點時才碰得到。
起日預設 2022-01-01,但操作員 2026-11-22 / 11-24 裁定資料家「2018 起」(DataPlane 冊 start = 2018-01-01)。
本版:
  ① 找庫:資料家 output_hub(VDF_MDL020_DataPlane 尾版 resolve_home)→ 前版兩個根;同一個實體檔(接點 / 捷徑)只收一次;
     略過 _quarantine · quarantine · _backup · selftest · _sha 指紋副本;印「入湖讀的庫」清單(家目錄寫 ~)。
  ② 沒給 --start → 用 DataPlane 冊的起日(book_start;操作員裁定),並印來源;給了 --start 照給的。
其餘(只增分片 · 遲到列 · 管家目錄 · 狀態)照 v0102 / v0100。只讀庫(不改庫)· 不出網(--skip-fetch 時零擷取)· 不用 TA-Lib · 不設同意閘。
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
STEM = "VDF_ENG239_ParquetLakeBuild"
VERSION = "v0103"
TAG = f"{STEM} {VERSION}"
SKIP_PARTS = ("_quarantine", "quarantine", "_backup", "selftest")
_SHA = re.compile(r"_sha[0-9a-f]{6,}$")


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(str(p)).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(f"{STEM}_prior_for_{VERSION}", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
P0 = PRIOR.P0                                       # v0100 本體(run 依模組全域名找 find_dbs / START_DEFAULT)
VDF = HERE.parent


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def tilde(p) -> str:
    s, h = str(p), str(Path.home())
    return "~" + s[len(h):] if h and s.startswith(h) else s


_DP = {}


def _dataplane():
    if "m" not in _DP:
        try:
            ts = sorted(VDF.glob("VDF_MDL020_DataPlane_v*.py"), key=_vnum)
            if ts:
                sp = importlib.util.spec_from_file_location(f"{STEM}_{VERSION}_dataplane", ts[-1])
                m = importlib.util.module_from_spec(sp)
                sys.modules[sp.name] = m
                sp.loader.exec_module(m)
                _DP["m"] = m
            else:
                _DP["m"] = None
        except Exception as e:  # noqa: BLE001 - 判不出家照實說,不擋
            _DP["m"], _DP["err"] = None, f"{type(e).__name__}: {str(e)[:120]}"
    return _DP["m"]


def data_home() -> tuple:
    dp = _dataplane()
    if dp is None or not callable(getattr(dp, "resolve_home", None)):
        return None, _DP.get("err", "DataPlane 尾版不在或沒有 resolve_home")
    try:
        return dp.resolve_home(None)
    except Exception as e:  # noqa: BLE001
        return None, f"resolve_home 失敗:{type(e).__name__}"


def book_start() -> tuple:
    dp = _dataplane()
    try:
        s = dp.book_start() if dp is not None and callable(getattr(dp, "book_start", None)) else None
    except Exception:  # noqa: BLE001
        s = None
    return (s, "DataPlane 冊 start(操作員 2026-11-22 / 11-24 裁定「2018 起」)") if s else (P0.START_DEFAULT, "ENG239 預設(DataPlane 冊讀不到)")


_ORIG_FIND = P0.find_dbs
LAST = {}


def _skip(p: Path) -> bool:
    low = [x.lower() for x in p.parts]
    return any(s in low for s in SKIP_PARTS) or bool(_SHA.search(p.stem)) or ".wal" in p.name


def find_dbs(extra=None) -> list:
    """資料家 output_hub 先(實體路徑去重)→ 前版兩個根 → extra。"""
    h, why = data_home()
    first = []
    if h is not None and (Path(h) / "output_hub").is_dir():
        first = [p for p in (Path(h) / "output_hub").glob("**/*.duckdb") if p.is_file() and not _skip(p)]
    rest = [p for p in _ORIG_FIND(extra) if not _skip(Path(p))]
    out, seen = [], set()
    for p in [*sorted(first), *rest]:
        k = os.path.normcase(str(Path(p).resolve()))
        if k not in seen:
            seen.add(k)
            out.append(Path(p))
    LAST.update(home=tilde(h) if h else None, home_why=why, from_home=len([p for p in out if p in first]), total=len(out))
    print(f"[入湖讀的庫] 資料家 {tilde(h) + '\\output_hub' if h else '沒判到(' + str(why) + ')'} · 從資料家 {LAST['from_home']} 個 · 共 {len(out)} 個(同實體只算一次)",
          flush=True)
    for p in out[:40]:
        print(f"   {tilde(p)}", flush=True)
    if len(out) > 40:
        print(f"   …另 {len(out) - 40} 個", flush=True)
    return out


def _install():
    P0.find_dbs = find_dbs
    s, why = book_start()
    P0.START_DEFAULT = s
    LAST["start"], LAST["start_why"] = s, why


_ORIG_START = P0.START_DEFAULT
_install()


def _uninstall():
    P0.find_dbs = _ORIG_FIND
    P0.START_DEFAULT = _ORIG_START


def main() -> int:
    a = sys.argv[1:]
    if a and a[0] == "--selftest":
        return selftest()
    if a and a[0] == "run" and "--start" not in a:
        print(f"[起日] {LAST['start']} · 來源:{LAST['start_why']}", flush=True)
    return PRIOR.main()


def selftest() -> int:
    ok, bad = [], []

    def chk(name, cond, note=""):
        (ok if cond else bad).append(name)
        print(f"  [{'OK' if cond else 'NG'}] {name}" + (f" · {str(note)[:300]}" if note and not cond else ""), flush=True)

    chk("加速器載入(VIA_ACCEL is not None)", VIA_ACCEL is not None)
    chk("網路工具載入(_via_net() is not None · 載入不出網)", _via_net() is not None, VIA_NET_TOOL_PATH)
    chk("已裝進 v0100 本體:run 找庫走本版 · 起日取 DataPlane 冊", P0.find_dbs is find_dbs and P0.START_DEFAULT == LAST["start"])
    keep_env = os.environ.get("VIA_VDF_DB_HOME")
    keep_globs = P0.DB_GLOBS
    try:
        duckdb = __import__("duckdb")
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            home = td / "via_database" / "vdf_database"
            for rel in ("output_hub/mega/vdf_tw_market.duckdb", "output_hub/_backup/old.duckdb", "output_hub/q/x_sha1a2b3c4d.duckdb"):
                (home / rel).parent.mkdir(parents=True, exist_ok=True)
                c = duckdb.connect(str(home / rel))
                c.execute("CREATE TABLE tw_daily_prices AS SELECT DATE '2026-11-20' AS date, '2330' AS ticker, 1.0 AS close")
                c.close()
            repo_hub = td / "repo_output_hub"
            try:
                os.symlink(home / "output_hub", repo_hub, target_is_directory=True)
                linked = True
            except OSError:
                linked = False
            stage = td / "vdf_fetch"
            stage.mkdir()
            c = duckdb.connect(str(stage / "stage_only.duckdb"))
            c.execute("CREATE TABLE t AS SELECT 1 AS a")
            c.close()
            os.environ["VIA_VDF_DB_HOME"] = str(home)       # 資料家指到暫存夾(不是同意閘;跑完還原)
            P0.DB_GLOBS = [(repo_hub, "**/*.duckdb"), (stage, "**/*.duckdb")]
            got = [Path(p).name for p in find_dbs()]
            chk("資料家 output_hub 先讀 · 暫存家照讀 · _backup / _sha 副本略過",
                got[:1] == ["vdf_tw_market.duckdb"] and "stage_only.duckdb" in got and "old.duckdb" not in got
                and not any("_sha" in g for g in got), got)
            chk("倉內 output_hub 是接點(指到同一實體)→ 同一個庫只收一次" + ("" if linked else "(這台建不了接點,略)"),
                (got.count("vdf_tw_market.duckdb") == 1) if linked else True, got)
            os.environ["VIA_VDF_DB_HOME"] = str(td / "not_here")
            _DP.clear()
            got2 = [Path(p).name for p in find_dbs()]
            chk("資料家不在 → 照前版兩個根讀,不丟例外", "stage_only.duckdb" in got2 and LAST["home"] is None, got2)
    finally:
        P0.DB_GLOBS = keep_globs
        if keep_env is None:
            os.environ.pop("VIA_VDF_DB_HOME", None)
        else:
            os.environ["VIA_VDF_DB_HOME"] = keep_env
        _DP.clear()
    s, why = book_start()
    chk("起日:DataPlane 冊讀得到 → 2018-01-01(操作員裁定);讀不到 → 退回 ENG239 預設並寫來源",
        (s == "2018-01-01" and "裁定" in why) or (s == _ORIG_START and "預設" in why), (s, why))
    _uninstall()
    try:
        rc = PRIOR.selftest()
    finally:
        _install()
    chk("前版 v0102 自測(本版換裝卸下)照過", rc == 0, rc)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("檔面:雙橋在 · 零 TA-Lib · 不設同意閘",
        "[VIA:ACCEL-BRIDGE:v0100]" in src and "[VIA:NET-BRIDGE:v0100]" in src
        and not re.search(r"^\s*(import|from)\s+(talib|requests)", src, re.M)
        and not re.search(r"^\s*os\.environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", src, re.M))
    print(f"{TAG} selftest {len(ok)}/{len(ok) + len(bad)}" + (" · 不過:" + " · ".join(bad) if bad else ""), flush=True)
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
