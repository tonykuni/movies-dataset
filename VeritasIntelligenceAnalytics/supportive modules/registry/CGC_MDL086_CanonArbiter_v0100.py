#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL086_CanonArbiter — 真雙位置正典裁定器(批133 收官;via-canon)
====================================================================
承 CGC_MDL085 仲裁:VERSION_ARBITRATION 138 件(36 獨立組)收官。
操作員令「Finish the projects」+批133 建議規則核備:
  規則 R1(位置正典):同名跨目錄組=LOCATION_CANON——
    functional modules/ 系統目錄優先;同系統內 engine/ 等組織子目錄
    優先於根;全在 supportive 者取組織子目錄(非 supportive 根);
    平手取 mtime 最新。非正典位置=鏡像讓位「登錄」(零刪除零搬移,
    僅記帳;工作面 glob 一律解析正典位置)。
  規則 R2(ID 錯標):異名共用 module_id 組=ID_REALIGNMENT——
    檔名前綴與 module_id 相符者=正當持有人;其餘=錯標頭候修版
    (version-forward 修正標頭,原件零觸碰,候操作員核准)。
產物:VIA_Canon_Registry_v0100.json(本目錄;append-only 正典冊)
     +VIA_Reports/govtriage_runs/CANON_<ts>.json 存證。
紅線:唯讀裁定零檔案操作;只增不減;裁定狀態=PROPOSED_AUTO(依核備
規則自動裁定),操作員可逐組否決(冊為 append-only,否決=追加覆寫項)。
用法:via-canon run | --selftest
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

import json
import re
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
OUT_ROOT = VIA / "VIA_Reports" / "govtriage_runs"
CANON_BOOK = HERE / "VIA_Canon_Registry_v0100.json"

_SHA_RX = re.compile(r"(_sha[0-9a-f]{4,})+(?=\.[A-Za-z0-9]+$|$)")
_ID_RX = re.compile(r"^([A-Z]{2,5}_(?:ENG|MDL)\d{3})")


def _base(name: str) -> str:
    return _SHA_RX.sub("", name)


def rank_location(rel: str, mtime: float) -> tuple:
    """R1 位置排序鍵:非退役>functional 系統目錄>組織子目錄>根;平手 mtime 新者
    退役鏡頭:_superseded/_quarantine 夾與 _sha 鏡像名=最低權(不得為正典,
    除非全組皆退役)"""
    p = Path(rel)
    low = rel.lower()
    live = 0 if ("_superseded" in low or "quarantine" in low
                 or "_sha" in p.name.lower()) else 1
    in_func = 1 if str(p).startswith("functional modules") else 0
    depth = len(p.parts)
    at_sup_root = 1 if (str(p.parent) == "supportive modules") else 0
    return (live, in_func, 1 - at_sup_root, depth, mtime)


def decide_location(members: list[str]) -> dict:
    """同名跨目錄組=位置正典裁定(零刪除;非正典=讓位登錄)"""
    scored = []
    for m in members:
        p = VIA / m
        mt = p.stat().st_mtime if p.exists() else 0.0
        scored.append((rank_location(m, mt), m))
    scored.sort(reverse=True)
    canon = scored[0][1]
    return {"kind": "LOCATION_CANON", "canonical": canon,
            "yields": [m for _, m in scored[1:]],
            "rationale": "R1:functional 系統目錄優先>組織子目錄>根;平手 mtime 新者;"
                         "非正典=讓位登錄(零刪除零搬移)"}


def decide_id(module_id: str, members: list[str]) -> dict:
    """R2 ID 錯標裁定:檔名前綴相符者=正當持有人"""
    holders = [m for m in members
               if _base(Path(m).name).upper().startswith(module_id.upper())]
    if len(holders) == 1:
        return {"kind": "ID_REALIGNMENT", "module_id": module_id,
                "canonical": holders[0],
                "mislabeled": [m for m in members if m != holders[0]],
                "rationale": "R2:檔名前綴與 module_id 相符=正當持有人;"
                             "餘=錯標頭候修版(version-forward;候核准)"}
    return {"kind": "ID_REALIGNMENT_REVIEW", "module_id": module_id,
            "members": members, "canonical": None,
            "rationale": "R2 無法自動判(0 或多重相符)=候操作員裁決"}


def _load_va_groups():
    """讀最新 ARBIT 存證,萃 VERSION_ARBITRATION 獨立組(同名/異名分流)"""
    hits = sorted(OUT_ROOT.glob("ARBIT_*.json"))
    if not hits:
        return None, None, "無 ARBIT 存證(先跑 via-arbit run)"
    d = json.loads(hits[-1].read_text(encoding="utf-8"))
    loc_groups, id_rows = {}, []
    for x in d["dispositions"]:
        if x["verdict"] != "VERSION_ARBITRATION":
            continue
        mem = sorted(set(x["active"]))
        bases = {_base(Path(m).name) for m in mem}
        if len(bases) == 1:
            loc_groups[tuple(mem)] = True
        else:
            id_rows.append(mem)
    return loc_groups, id_rows, hits[-1].name


def _module_id_map():
    """從最新 CentralGov run 議題表補 module_id(SSOT 組憑證)"""
    import pandas as pd
    runs = sorted((VIA / "VIA_Reports" / "centralgov_runs").glob("RUN_*"))
    if not runs:
        return {}
    issues = sorted(runs[-1].glob("round_*/issues.csv.gz"))[-1]
    df = pd.read_csv(issues, low_memory=False)
    out = {}
    for _, r in df[df["category"] == "SSOT_AUTHORITY_COLLISION"].iterrows():
        m = re.search(r"module_id=([A-Za-z0-9_]+):", str(r["detail"]))
        if m:
            out[str(r["relative_path"])] = m.group(1)
    return out


def run() -> int:
    loc_groups, id_rows, src = _load_va_groups()
    if loc_groups is None:
        print(f"[FAIL] {src}")
        return 1
    idmap = _module_id_map()
    print(f"=== 真雙位置正典裁定(批133 收官)· 源 {src} ===")
    entries, seen = [], set()
    for mem in loc_groups:
        key = "|".join(mem)
        if key in seen:
            continue
        seen.add(key)
        entries.append({"group": list(mem), **decide_location(list(mem))})
    for mem in id_rows:
        mid = next((idmap[m] for m in mem if m in idmap), None)
        key = (mid or "?") + "|" + "|".join(mem)
        if key in seen:
            continue
        seen.add(key)
        if mid:
            entries.append({"group": mem, **decide_id(mid, mem)})
        else:
            entries.append({"group": mem, "kind": "ID_REALIGNMENT_REVIEW",
                            "module_id": None, "canonical": None,
                            "rationale": "module_id 憑證缺=候操作員裁決"})
    counts = {}
    for e in entries:
        counts[e["kind"]] = counts.get(e["kind"], 0) + 1
    for k, v in sorted(counts.items()):
        print(f"  [{k}] {v} 組")
    for e in entries:
        if e["kind"] == "LOCATION_CANON":
            print(f"    ★ {e['canonical']}  (讓位登錄 {len(e['yields'])})")
    book = {"schema": "VIA.CanonRegistry.v1", "policy":
            "append-only;PROPOSED_AUTO=依批133 核備規則 R1/R2 自動裁定;"
            "零刪除零搬移;操作員否決=追加覆寫項;工作面 glob 解析正典位置",
            "entries": []}
    if CANON_BOOK.exists():
        book = json.loads(CANON_BOOK.read_text(encoding="utf-8-sig"))
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    for e in entries:
        book["entries"].append({**e, "status": "PROPOSED_AUTO", "ts": stamp})
    CANON_BOOK.write_text(json.dumps(book, ensure_ascii=False, indent=1),
                          encoding="utf-8")
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    out = OUT_ROOT / f"CANON_{stamp}.json"
    out.write_text(json.dumps({"source": src, "counts": counts,
                               "entries": entries}, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print(f"  [冊] {CANON_BOOK.name} 共 {len(book['entries'])} 項")
    print(f"  [存] {out.relative_to(VIA)}")
    return 0


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    r1 = rank_location("functional modules/VDF/engine/a.py", 1.0)
    r2 = rank_location("functional modules/VDF/a.py", 9.0)
    r3 = rank_location("supportive modules/registry/a.py", 9.0)
    r4 = rank_location("supportive modules/a.py", 9.0)
    r5 = rank_location("functional modules/VRN/_superseded/20260804/a.py", 99.0)
    chk("① R1 排序(退役最低;functional>supportive;engine 深層>根)",
        r1 > r2 > r3 > r4 > r5)

    import tempfile
    with tempfile.TemporaryDirectory(dir=str(VIA)) as td:
        rel = Path(td).relative_to(VIA)
        (VIA / rel / "m.py").write_text("A=1\n")
        d = decide_location([f"{rel}/m.py", "functional modules/VDF/engine/VDF_MDL007_SSOTResolver.py"])
        chk("② 位置正典裁定=functional 優先+讓位登錄",
            d["canonical"].startswith("functional modules")
            and len(d["yields"]) == 1)

    d2 = decide_id("VDF_ENG051", ["functional modules/VDF/engine/VDF_ENG050_OrderFetch_v0101.py",
                                  "functional modules/VDF/engine/VDF_ENG051_ActiveTWETF_Holdings.py"])
    chk("③ R2 ID 正當持有人=檔名前綴相符者",
        d2["kind"] == "ID_REALIGNMENT"
        and d2["canonical"].endswith("VDF_ENG051_ActiveTWETF_Holdings.py")
        and len(d2["mislabeled"]) == 1)

    d3 = decide_id("VRN_ENG099", ["a/x.py", "a/y.py"])
    chk("④ R2 無相符=候操作員(不硬判)", d3["kind"] == "ID_REALIGNMENT_REVIEW")

    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def run()", 1)[1].split("def selftest", 1)[0]
    chk("⑤ 零檔案操作(run 段僅寫冊+存證;無刪除/搬移)",
        ("shu" + "til") not in body and ("re" + "name(") not in body
        and (".un" + "link") not in body)
    chk("⑥ 冊 append-only 政策宣告", "append-only" in src and "PROPOSED_AUTO" in src)
    print(f"  [計] 六檢 OK {6 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 正典裁定器(CGC_MDL086)· 六檢自測(合成件)===")
        return selftest()
    if "run" in args or not args:
        return run()
    print(__doc__.split("用法:")[1])
    return 0


if __name__ == "__main__":
    sys.exit(main())
