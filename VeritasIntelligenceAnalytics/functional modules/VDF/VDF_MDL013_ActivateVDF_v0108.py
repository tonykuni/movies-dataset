#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VDF_MDL013_ActivateVDF v0108 — 薄尾:總覽頁「資料庫清點」的他系統表分開命名 VRN-1 / VRN-2 / VCGC(政策 L123 四系統)

操作員令(2026-10-19):「VRN-1 VRN-2 VDF VCGC都是獨立系統  互不干涉」「1. 分開命名  2. CHANGE TO 4 SYSTEMS.」。
v0106 的總覽卡寫死「VRN / VCGC 寫的表」,沒分 VRN-1 / VRN-2。本版:
  ① 讀 db check 每列狀態的「他系統表(<系統> 寫)」(VDF_SystemManager v0156 寫的名字)逐系統計數 → 清點摘要多 other_by;
     舊結果(v0155 寫的「VRN 寫」)照原字計,不猜成 VRN-1 / VRN-2。
  ② 總覽卡「他系統表」一格改逐系統列(例:VRN-2 6 · VRN 未分辨 6),註明 L123 四系統互不干涉、只攤開不代修。
  ③ 終端多一行「[他系統表] VRN-2 n · …」。本輪 JSON / 頁頭標 v0108。
其餘全照 v0107(記憶體 / TEMP 鉤 · 起跑實測)。VDF 自己的模組:不匯入他系統程式;同意閘不讀不寫;不碰 TA-Lib;不裝套件、不寫環境。
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
    """統包唯一網路工具惰性載入;本檔的連網全經 MDL008 子行程改道。"""
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

import html
import importlib.util
import re
import sys
import warnings
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_MDL013_ActivateVDF"
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"
OTHER_RE = re.compile(r"^他系統表[((](.+?) 寫[))]")


def _vnum_v0108(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0108(p) < _vnum_v0108(__file__)), key=_vnum_v0108)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
with warnings.catch_warnings():                    # 同 v0102:前版鏈只擋載入那一刻的編譯警告
    warnings.simplefilter("ignore", SyntaxWarning)
    warnings.simplefilter("ignore", DeprecationWarning)
    _spec.loader.exec_module(PRIOR)
V0100 = PRIOR.V0100


def __getattr__(name):
    return getattr(PRIOR, name)


def _owner(name: str):
    """沿前版鏈找真正定義 name 的那一版模組(db_inventory / db_section 在 v0106)。"""
    m = PRIOR
    for _ in range(16):
        if name in vars(m) and getattr(vars(m)[name], "__module__", None) == m.__name__:
            return m
        m = vars(m).get("PRIOR")
        if m is None:
            break
    return None


DBM = _owner("db_section")
_DB_INVENTORY_V0106 = DBM.db_inventory
_DB_SECTION_V0106 = DBM.db_section
OLD_NOTE = "VRN / VCGC 寫的表:只攤開不代修,不計 VDF 的燈(L120)"


def other_by(rows) -> dict:
    """他系統表逐系統計數(名字照 db check 寫的;認不出名字的記「他系統(未標)」)。"""
    out = {}
    for r in rows or []:
        m = OTHER_RE.match(str(r.get("狀態") or ""))
        k = m.group(1).strip() if m else "他系統(未標)"
        out[k] = out.get(k, 0) + 1
    return out


def db_inventory(ui_dir: Path | None = None, pre=DBM._UNSET) -> dict:
    db = _DB_INVENTORY_V0106(ui_dir, pre)
    if "other_rows" in db:
        db["other_by"] = other_by(db["other_rows"])
    return db


def db_section(db: dict | None) -> str:
    s = _DB_SECTION_V0106(db)
    if not s or not db or OLD_NOTE not in s:
        return s
    by = db.get("other_by")
    if by is None:
        by = other_by(db.get("other_rows"))
    names = " · ".join("%s %d" % (html.escape(k), v) for k, v in sorted(by.items())) or "0"
    return s.replace(OLD_NOTE, "%s<br>只攤開不代修,不計 VDF 的燈(L123 四系統 VRN-1 · VRN-2 · VDF · VCGC 互不干涉)" % names, 1)


DBM.db_inventory = db_inventory
DBM.db_section = db_section
_ACTIVATE_V0107 = PRIOR.activate


def activate(opt, manager: Path | None = None, py: str | None = None, temp: Path | None = None) -> dict:
    """同 v0107 activate;本輪 JSON / 頁頭標 v0108,跑完逐系統印他系統表。"""
    keep = PRIOR.TAG
    prev = DBM._WRITE_REPORT_V0100

    def _stamp_then_write(c, u=None):
        c["schema"], c["tag"] = "VDF_ActivateVDF_v0108", TAG
        return prev(c, u) if u is not None else prev(c)
    PRIOR.TAG = TAG
    DBM._WRITE_REPORT_V0100 = _stamp_then_write
    try:
        card = _ACTIVATE_V0107(opt, manager, py, temp)
    finally:
        PRIOR.TAG = keep
        DBM._WRITE_REPORT_V0100 = prev
    by = (card.get("db") or {}).get("other_by")
    if by:
        print("  [他系統表] " + " · ".join("%s %d" % kv for kv in sorted(by.items()))
              + " → 只攤開不代修,不計 VDF 的燈(L123 四系統互不干涉)", flush=True)
    return card


for _n in dir(PRIOR):
    if not _n.startswith("__") and _n not in globals():
        globals()[_n] = getattr(PRIOR, _n)


def selftest() -> int:
    import json
    import os
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

    print(f"=== {TAG} · 薄尾自測(總覽卡他系統表分開命名;沙盒 · 零網路)===")
    rows = [{"狀態": "他系統表(VRN-2 寫)· 缺表 · VDF 只攤開不代修"}, {"狀態": "他系統表(VRN-2 寫)· 空表"},
            {"狀態": "他系統表(VRN-1 寫)· 缺表"}, {"狀態": "他系統表(VCGC 寫)· 缺表"},
            {"狀態": "他系統表(VRN-1 + VRN-2 寫)· 缺表"}, {"狀態": "他系統表(VRN 未分辨 寫)· 冊上沒登寫入者,表名 vrn_ 開頭 · 缺表"},
            {"狀態": "他系統表(VRN 寫)· 缺表"}, {"狀態": "他系統表?"}]
    by = other_by(rows)
    chk("① 逐系統計數:照 db check 寫的名字(VRN-2 / VRN-1 / VCGC / 多系統 / VRN 未分辨);舊結果「VRN」照原字,不猜",
        by == {"VRN-2": 2, "VRN-1": 1, "VCGC": 1, "VRN-1 + VRN-2": 1, "VRN 未分辨": 1, "VRN": 1, "他系統(未標)": 1}, by)
    td = Path(tempfile.mkdtemp(prefix="vdfact108_"))
    try:
        ui = td / "ui"
        d = DBM.db_report_dir(ui)
        d.mkdir(parents=True, exist_ok=True)
        j = d / "DB_CHECK_latest.json"
        j.write_text(json.dumps({"lamp": "GREEN", "tag": "VDF_SystemManager v0156", "rows": [
            {"庫": "a.duckdb", "表": "tw_x", "狀態": "OK", "燈": "GREEN", "列數": 3},
            {"庫": "a.duckdb", "表": "vrn_report_basic", "狀態": "他系統表(VRN 未分辨 寫)· 缺表", "燈": "INFO", "寫入者": ""},
            {"庫": "a.duckdb", "表": "via_policy_x<b>", "狀態": "他系統表(VRN-2 寫)· 缺表", "燈": "INFO", "寫入者": "VRN_ENG082"},
            {"庫": "a.duckdb", "表": "c", "狀態": "他系統表(VCGC<i> 寫)· 缺表", "燈": "INFO", "寫入者": "CGC_X"}]}, ensure_ascii=False),
            encoding="utf-8")
        db = db_inventory(ui, pre=None)
        sec = db_section(db)
        chk("② 清點摘要多 other_by;總覽卡逐系統列(名字跳脫)、寫 L123 四系統,不再是「VRN / VCGC 寫的表」",
            db.get("other_by") == {"VRN 未分辨": 1, "VRN-2": 1, "VCGC<i>": 1} and OLD_NOTE not in sec
            and "VCGC&lt;i&gt; 1 · VRN 未分辨 1 · VRN-2 1" in sec and "L123 四系統" in sec and "<i>" not in sec, (db.get("other_by"), sec[-600:]))
        old = dict(db)
        old.pop("other_by")
        chk("③ 舊摘要沒有 other_by(前版寫的)→ 卡上照 other_rows 現算;NOT_RUN 卡不動",
            "VRN-2 1" in db_section(old) and db_section({"lamp": "NOT_RUN", "why": "x"}) == _DB_SECTION_V0106({"lamp": "NOT_RUN", "why": "x"}))
        chk("④ v0106 總覽頁走本版(render_html 查模組全域 db_section / write_report 查 db_inventory)",
            DBM.db_section is db_section and DBM.db_inventory is db_inventory)
    finally:
        shutil.rmtree(td, ignore_errors=True)
    src = Path(__file__).read_text(encoding="utf-8")
    imports = re.findall(r"^\s*(?:import|from)\s+([A-Za-z_][\w.]*)", src, re.M)
    chk("⑤ 加速器橋 · 網路橋在;不匯入他系統程式;不碰 TA-Lib;同意閘不寫",
        "VIA:ACCEL-BRIDGE" in src and "def _via_net" in src
        and not [x for x in imports if x.startswith(("CGC_", "VRN_", "VRN2_", "VCGC"))]
        and not re.search(r"^\s*(import|from)\s+" + "talib", src, re.M)
        and not re.search(r"\[[\"']VIA_(NET|SCRAPE)_" + r"CONSENT[\"']\]\s*=(?!=)", src))
    print(f"  [計] {TAG} 本版 {p}/{p + f} · {'PASS' if not f else 'FAIL'}")
    if f:
        return 1
    if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1":
        return 0
    rc1 = PRIOR.selftest()
    return rc1 if rc1 in (0, 1, 2, 3) else 1        # 前版紅照實回(同 v0107)


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["--selftest"]:
        return selftest()
    opt = V0100.parse(argv)
    if opt.verb != "run":
        return V0100.main(argv)
    card = activate(opt)
    return {"GREEN": 0, "YELLOW": 2, "INTERRUPTED": 130}.get(card["lamp"], 1)


if __name__ == "__main__":
    raise SystemExit(main())
