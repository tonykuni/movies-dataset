#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VDF SystemManager v0196 — 薄尾(v0195 以前一字不動):PR #774 Codex 兩筆 P1

  ① 沒量到的輸出拿到綠燈:契約綠 + 實測灰時,worst() 把灰與綠同級 → 回綠;所有輸出都有表頭、又沒有資料家時,
     outputs 與 vv ② 的 outputs 格沒讀任何資料庫就亮綠(AGENTS.md §6:主機資料庫沒驗 = 未完成)。
     → 本版:實測灰(沒資料家)一律把那一列至少壓成黃(「未量」);總燈跟著黃,不會因為沒量而變綠。
  ② 資料家底下的庫在 output_hub/mega 這種子夾時,v0195 只看 home/<庫名> → 全部誤報「未擷取」。
     → 本版:庫一律照 MDL020 的 find_dbs(home)(往下三層 · mega 優先 · 略過備份 / 自測 / 暫存)找正典庫;
       冊上不在 find_dbs 協定裡的庫與 parquet 檔,照同樣的層數與略過規則找。
其餘照 v0195 / v0194(三流程 vv · 契約 · 表頭草稿)。零網路 · 不碰 TA-Lib · 不設同意閘 · 不 import VCGC。
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
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(VDF 全導入令;惰性載入=import 時零網路、零行為變更) =====
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
except Exception:  # noqa: BLE001
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT;網路只認 AegisNexus);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:  # noqa: BLE001
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import json
import re
import sys
import tempfile
from pathlib import Path

VERSION = "v0196"
STEM = "VDF_SystemManager"
TAG = f"VDF_SystemManager {VERSION}"
HERE = Path(__file__).resolve().parent
UNMEASURED = "未量(沒有資料家;主機實測後才算)"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(f"{STEM}_prior_for_{VERSION}", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)                 # v0195(outputs · vv)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


_DP: dict = {}


def _dp_p(root: Path | None = None):
    """MDL020 的 v0100 本體(find_dbs · SKIP_DIRS);找不到就 None(照同規則自己找)。"""
    if "P" not in _DP:
        try:
            _DP["P"] = PRIOR.dataplane(root or PRIOR._p("sm_via_root")()).P
        except Exception:  # noqa: BLE001
            _DP["P"] = None
    return _DP["P"]


SKIP_FALLBACK = ("_bak", "backup", "backups", "_selftest", "selftest", "tmp", "_tmp")


def locate(home: Path, name: str, P=None) -> Path | None:
    """冊上的庫 / parquet 檔在資料家底下的實際位置:MDL020 find_dbs 優先;其餘照同層數 · 同略過規則。"""
    if P is not None:
        try:
            hit = P.find_dbs(home).get(name)
            if hit is not None:
                return hit
        except Exception:  # noqa: BLE001
            pass
    skip = set(getattr(P, "SKIP_DIRS", ()) or SKIP_FALLBACK)
    cands = []
    for pat in (name, "*/" + name, "*/*/" + name, "*/*/*/" + name):
        for p in home.glob(pat):
            parts = p.relative_to(home).parts[:-1]
            if not any(x in skip for x in parts) and "temp" not in [s.lower() for s in parts]:
                cands.append(p)
    return sorted(set(cands), key=lambda p: ("mega" not in p.parts, -p.stat().st_size))[0] if cands else None


_ORIG_MEASURE = PRIOR.measure


def measure(o: dict, home: Path) -> dict:
    """照 locate() 找到實際位置,再交給 v0195 的唯讀量測(DESCRIBE + 列數;判法不變)。"""
    name = o.get("db") or o.get("file")
    hit = locate(home, str(name or ""), _dp_p()) if name else None
    if hit is None:
        return _ORIG_MEASURE(o, home)                         # 找不到 → v0195 照實回「未擷取」
    o2 = dict(o)
    if o.get("db"):
        o2["db"] = hit.name
    else:
        o2["file"] = hit.name
    return _ORIG_MEASURE(o2, hit.parent)


_ORIG_CHECK = PRIOR.output_check


def output_check(root: Path, outputs=None, tables=None, home=None, book_name: str = "", out_dir=None) -> dict:
    r = _ORIG_CHECK(root, outputs, tables, home, book_name, out_dir)
    for row in r["rows"]:
        if row.get("measure") == "GRAY" and row.get("contract") != "GRAY":
            row["lamp"] = PRIOR.worst([row["lamp"], "YELLOW"])
            row.setdefault("problems", []).append(UNMEASURED)
    r["lamp"] = PRIOR.worst(x["lamp"] for x in r["rows"]) if r["rows"] else "GRAY"
    if r["rows"] and all(x.get("measure") == "GRAY" for x in r["rows"]) and r["lamp"] == "GREEN":
        r["lamp"] = "YELLOW"                                   # 保險:整批沒量就不得綠
    r["unmeasured"] = sum(1 for x in r["rows"] if x.get("measure") == "GRAY")
    return r


PRIOR.measure = measure
PRIOR.output_check = output_check


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:240]) if note and not cond else ""), flush=True)

    print(f"[計] {TAG} 自測開始(本版 4 項 + 前版 {PRIOR_PATH.name} 自測 · 暫存資料家 · 零網路)", flush=True)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("T1 加速器真的載到 · 第 3 行標記 · 網路橋在", VIA_ACCEL is not None and src.splitlines()[2] == "# [VIA:ACCEL-BRIDGE:v0111]"
        and VIA_NET_TOOL_PATH is not None)
    import duckdb
    spec = {"t_ok": {"subsystem": "VDF", "source": {"kind": "duckdb", "path": "x/vdf_tw_market.duckdb", "table": "t_ok"},
                     "columns": [{"name": "date", "dtype": "date", "key": True}, {"name": "v", "dtype": "float", "required": True}], "min_rows": 1}}
    outs = [{"id": "O1", "db": "vdf_tw_market.duckdb", "table": "t_ok"}]
    with tempfile.TemporaryDirectory(prefix="vdf_out196_") as td:
        r0 = output_check(Path(td), outs, spec, "沒有資料家(容器)", "fx_book", Path(td))
        chk("T2 (Codex P1 ①)全部有表頭、沒有資料家 → 不得綠(黃 · 未量)", r0["lamp"] == "YELLOW" and r0["rows"][0]["lamp"] == "YELLOW"
            and UNMEASURED in r0["rows"][0]["problems"] and r0["unmeasured"] == 1, r0)
        home = Path(td) / "home"
        nested = home / "output_hub" / "mega"
        nested.mkdir(parents=True)
        (home / "_bak").mkdir()
        c = duckdb.connect(str(nested / "vdf_tw_market.duckdb"))
        c.execute("CREATE TABLE t_ok(date DATE, v DOUBLE)")
        c.execute("INSERT INTO t_ok VALUES ('2026-01-02', 1.0)")
        c.close()
        c = duckdb.connect(str(home / "_bak" / "vdf_tw_market.duckdb"))      # 備份夾裡的同名庫不得被選中
        c.execute("CREATE TABLE other(a INT)")
        c.close()
        r1 = output_check(Path(td), outs, spec, home, "fx_book", Path(td))
        chk("T3 (Codex P1 ②)庫在 output_hub/mega 子夾 → 找得到並實測綠(備份夾的同名庫不選)",
            r1["rows"][0]["measure"] == "GREEN" and r1["rows"][0]["lamp"] == "GREEN" and r1["rows"][0].get("rows") == 1, r1["rows"])
        chk("T4 locate:MDL020 find_dbs 優先;協定外的檔照同層數 · 略過規則找", locate(home, "vdf_tw_market.duckdb", None) == nested / "vdf_tw_market.duckdb"
            and locate(home, "nope.parquet", None) is None)
    rc = PRIOR.selftest() if callable(getattr(PRIOR, "selftest", None)) else 1
    chk("T5 前版 v0195 自測照過(含整條前版鏈)", rc == 0, rc)
    print(f"[計] {TAG} 自測 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}", flush=True)
    return 0 if all(ok) else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    return PRIOR.main(a)


if __name__ == "__main__":
    raise SystemExit(main())
