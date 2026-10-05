#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0122 — 薄尾:Index 孤鍵退役(2026-10-06 第二段實跑:Index=47 但中央 46 · diff MISSING_CENTRAL=1)。

成因:v0121 鍵改帶副檔名後,csv-only 族(VRN_FileRegistry_Stage)的舊鍵「…|VRN_FileRegistry_Stage」與新鍵「…|VRN_FileRegistry_Stage|csv」
指向同一本機冊 → 一表兩鍵;舊鍵已被 VCGC 發了號(發了不收回)。
律(只增不減):舊鍵不刪,標 status=RETIRED · retired_at · superseded_by=<新鍵>;號留在舊鍵上不再用;diff / number pull / VCGC 偵測一律跳過 RETIRED。
  ssot adopt [--apply]   照前版鏈收養後,再做孤鍵退役(--apply 才寫 Index;dry-run 只列)
  ssot diff              RETIRED 不計入 MISSING_CENTRAL,另計 retired
  ssot number pull       RETIRED 跳過,另計 retired
自測: VIA_FROM_VCGC=YES python VRN_SystemManager_v0122.py --selftest(temp 沙盒;前版鏈自測原樣印出)
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

import importlib.util
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

TAG = "v0122"
HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"


def _vnum_v0122(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0122(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0122(p) < _vnum_v0122(__file__)),
                 key=_vnum_v0122)
PRIOR = _load_v0122(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


# ────────────────── 孤鍵退役律 v0122 ──────────────────
_P21 = PRIOR
_P20 = _P21._P20
_ADOPT_21 = _P20.ssot_adopt          # v0120 本體(已在 v0121 換鍵)
_DIFF_21 = _P20.ssot_diff            # v0121 版
_PULL_21 = _P20.ssot_number_pull     # v0120 版


def _retire_pass_v0122(apply: bool) -> dict:
    r = _P20._roots_v0120()
    idx = _P20._load_index_v0120(r)
    live = {x["key"] for x in _P21.ssot_inventory()["rows"]} if r["central"].is_dir() else set()
    by_local: dict = {}
    for k, e in idx["entries"].items():
        if e.get("status") != "RETIRED" and k in live:
            by_local.setdefault(str(Path(e.get("local_path", "")).resolve()), k)
    rows = []
    for k, e in idx["entries"].items():
        if e.get("status") == "RETIRED" or k in live:
            continue
        twin = by_local.get(str(Path(e.get("local_path", "")).resolve()))
        if twin and twin != k:
            rows.append({"key": k, "superseded_by": twin, "ssot_no": e.get("ssot_no", ""), "status": "RETIRED" if apply else "PLAN_RETIRE"})
            if apply:
                e["status"] = "RETIRED"
                e["retired_at"] = _P20._now_v0120()
                e["superseded_by"] = twin
                e["retire_note"] = "一表兩鍵(鍵改帶副檔名後的舊鍵);號留此鍵不再用"
        else:
            rows.append({"key": k, "superseded_by": None, "ssot_no": e.get("ssot_no", ""), "status": "ORPHAN_NO_TWIN"})
    if apply and any(x["status"] == "RETIRED" for x in rows):
        _P20._save_index_v0120(r, idx)
        for x in rows:
            if x["status"] == "RETIRED":
                _P20._ledger_v0120(r, {"ts": _P20._now_v0120(), "key": x["key"], "status": "RETIRED", "superseded_by": x["superseded_by"]})
    return {"rows": rows, "retired": sum(1 for x in rows if x["status"] == "RETIRED"),
            "plan": sum(1 for x in rows if x["status"] == "PLAN_RETIRE"), "orphan": sum(1 for x in rows if x["status"] == "ORPHAN_NO_TWIN")}


def ssot_adopt(apply: bool = False) -> dict:
    out = _ADOPT_21(apply=apply)
    rp = _retire_pass_v0122(apply)
    out["retire"] = rp
    if rp["orphan"]:
        out["_notes"].append("孤鍵無雙生 %d(本機冊不在中央也不是改鍵殘留)→ 交操作員+AI 裁,未退役" % rp["orphan"])
        out["lamp"] = "YELLOW" if out.get("lamp") == "GREEN" else out.get("lamp")
    if rp["plan"]:
        out["_notes"].append("dry-run:孤鍵 %d 待退役(--apply 才標 RETIRED)" % rp["plan"])
    return out


def ssot_diff() -> dict:
    out = _DIFF_21()
    r = _P20._roots_v0120()
    idx = _P20._load_index_v0120(r)
    keep, retired = [], 0
    for row in out["rows"]:
        if idx["entries"].get(row["key"], {}).get("status") == "RETIRED":
            retired += 1
            out["counts"][row["status"]] -= 1
            row["status"] = "RETIRED"
        keep.append(row)
    out["rows"] = keep
    out["counts"]["RETIRED"] = retired
    c = out["counts"]
    out["lamp"] = "RED" if c["DIFF"] else ("YELLOW" if (c["MISSING_LOCAL"] or c["MISSING_CENTRAL"]) else ("GREEN" if idx["entries"] else "GRAY"))
    return out


def ssot_number_pull() -> dict:
    r = _P20._roots_v0120()
    idx = _P20._load_index_v0120(r)
    out = _PULL_21()
    retired = 0
    for row in out["rows"]:
        if idx["entries"].get(row["key"], {}).get("status") == "RETIRED":
            retired += 1
            if row["status"] == "ALREADY":
                out["already"] -= 1
            elif row["status"] == "PENDING":
                out["pending"] -= 1
            row["status"] = "RETIRED"
    out["retired"] = retired
    out["lamp"] = "GREEN" if (idx["entries"] and out["pending"] == 0) else "GRAY"
    return out


# 記憶體替換(前版檔案一字不動):前版 main 的 ssot 動詞鏈改走本版三函式
_P20.ssot_adopt = ssot_adopt
_P20.ssot_diff = ssot_diff
_P20.ssot_number_pull = ssot_number_pull
_P21.ssot_adopt = ssot_adopt
_P21.ssot_diff = ssot_diff
_P21.ssot_number_pull = ssot_number_pull


def _print_tally_v0122(out: dict) -> None:
    if out.get("verb") == "ssot_adopt" and out.get("retire"):
        rp = out["retire"]
        print("  [退役] 孤鍵 RETIRED=%d PLAN=%d 無雙生=%d" % (rp["retired"], rp["plan"], rp["orphan"]))
        for x in rp["rows"]:
            print("    %s %s → %s · 號 %s" % (x["status"], x["key"], x["superseded_by"], x["ssot_no"] or "留白"))
    elif out.get("verb") == "ssot_diff":
        print("  [退役] RETIRED 不計 %d" % out["counts"].get("RETIRED", 0))
    elif out.get("verb") == "ssot_number_pull":
        print("  [退役] RETIRED 跳過 %d" % out.get("retired", 0))


_TALLY_20 = _P20._print_tally_v0120


def _tally_v0122(out: dict) -> None:
    _TALLY_20(out)
    _print_tally_v0122(out)


_P20._print_tally_v0120 = _tally_v0122


def main(argv=None) -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[VRN] 拒絕。只能經 via-vcgc。")
        return 2
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args[:2]:
        return selftest()
    return _P21.main(args)


def selftest() -> int:
    p = f = 0

    def chk(name, cond):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s" % name)

    td = Path(tempfile.mkdtemp(prefix="vrnsm122-"))
    central = td / "central_registry"
    home = td / "VRN"
    for k, v in (("VIA_VRN_SSOT_CENTRAL", str(central)), ("VIA_VRN_SSOT_HOME", str(home)),
                 ("VIA_NO_OPEN", "1"), ("VIA_NO_NET", "1"), ("VIA_VRN_UI_DIR", str(td / "ui"))):
        os.environ[k] = v
    (central / "VRN_FileRegistry_Stage_v029VRN1C.csv").parent.mkdir(parents=True, exist_ok=True)
    (central / "VRN_FileRegistry_Stage_v029VRN1C.csv").write_text("a,b\n1,2\n", encoding="utf-8")
    _P20._w_v0120(central / "VIA_VRN_DocClass_SSOT_v0101.json", {"classes": ["個股"]})
    r = _P20._roots_v0120()
    # 模擬 v0120 時代的 Index:csv 族用無 ext 舊鍵,且已被發號
    old_key = "VRN|central_registry|VRN_FileRegistry_Stage"
    _ADOPT_21(apply=True)
    idx = _P20._load_index_v0120(r)
    new_key = old_key + "|csv"
    idx["entries"][old_key] = dict(idx["entries"][new_key], key=old_key, ssot_no="SSOT-VCGC-VRN-BOOK0001")
    _P20._save_index_v0120(r, idx)
    chk("① 夾具:一表兩鍵(舊鍵已有號)· Index 3", len(_P20._load_index_v0120(r)["entries"]) == 3)
    d0 = _DIFF_21()
    chk("② 前版 diff 會把舊鍵當 MISSING_CENTRAL=1(第二段實跑現象重現)", d0["counts"]["MISSING_CENTRAL"] == 1)
    dry = ssot_adopt(apply=False)
    i1 = _P20._load_index_v0120(r)
    chk("③ adopt dry-run:PLAN_RETIRE 1 · Index 未改", dry["retire"]["plan"] == 1 and i1["entries"][old_key].get("status") != "RETIRED")
    ap = ssot_adopt(apply=True)
    i2 = _P20._load_index_v0120(r)
    e = i2["entries"][old_key]
    chk("④ adopt --apply:舊鍵 RETIRED · superseded_by=新鍵 · 號留在舊鍵 · 不刪(Index 仍 3)",
        ap["retire"]["retired"] == 1 and e["status"] == "RETIRED" and e["superseded_by"] == new_key
        and e["ssot_no"] == "SSOT-VCGC-VRN-BOOK0001" and len(i2["entries"]) == 3)
    d1 = ssot_diff()
    chk("⑤ diff:RETIRED 不計 → MISSING_CENTRAL 0 · RETIRED 1 · 綠", d1["counts"]["MISSING_CENTRAL"] == 0 and d1["counts"]["RETIRED"] == 1 and d1["lamp"] == "GREEN")
    n1 = ssot_number_pull()
    chk("⑥ number pull:RETIRED 跳過 1 · pending 2(新鍵與 DocClass)", n1["retired"] == 1 and n1["pending"] == 2 and n1["already"] == 0)
    ap2 = ssot_adopt(apply=True)
    chk("⑦ 冪等:再 adopt 退役 0 · 無雙生 0", ap2["retire"]["retired"] == 0 and ap2["retire"]["orphan"] == 0)
    i3 = _P20._load_index_v0120(r)
    i3["entries"]["VRN|central_registry|VRN_Gone"] = {"key": "VRN|central_registry|VRN_Gone", "local_path": str(home / "SSOT" / "nope.json"), "ssot_no": ""}
    _P20._save_index_v0120(r, i3)
    ap3 = ssot_adopt(apply=True)
    chk("⑧ 負控:孤鍵無雙生 → 不退役 · 黃 · 記注交裁", ap3["retire"]["orphan"] == 1
        and _P20._load_index_v0120(r)["entries"]["VRN|central_registry|VRN_Gone"].get("status") != "RETIRED" and ap3["lamp"] == "YELLOW")
    chk("⑨ 前版鏈動詞可達 · main 經 v0121", callable(_P21.ssot_resolve) and callable(_P20.intake))
    print("  ── 前版鏈自測(原樣印出,不緩衝)──")
    prc = _P21.selftest()
    chk("⑩ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    body = Path(__file__).read_text(encoding="utf-8")
    chk("⑪ 帶加速器橋 · VIA_FROM_VCGC 閘 · glob 取前版", "[VIA:ACCEL-BRIDGE:v0100]" in body and "VIA_FROM_VCGC" in body)
    for k in ("VIA_VRN_SSOT_CENTRAL", "VIA_VRN_SSOT_HOME", "VIA_NO_OPEN", "VIA_NO_NET", "VIA_VRN_UI_DIR"):
        os.environ.pop(k, None)
    shutil.rmtree(td, ignore_errors=True)
    print("[計] VRN_SystemManager_v0122 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
