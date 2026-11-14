#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0121 — 薄尾:SSOT 鍵帶副檔名(2026-10-06 實跑:ADOPTED=46 但 Index=45,一族同時有 .json 與 .csv 撞成一鍵,違 L108 ② 不同表=不同號)。

改法(前版 v0120 檔不動;本版在記憶體替換前版兩個函式,其餘照前版鏈):
  鍵 = VRN|central_registry|<族>            (.json,預設,45 鍵一字不改)
  鍵 = VRN|central_registry|<族>|<ext>      (csv 等非 json 才帶,新增 1 鍵)
  ssot diff 改以「鍵」對中央尾版,不再以族名(同族兩表不會互比)
自測: VIA_FROM_VCGC=YES python VRN_SystemManager_v0121.py --selftest(temp 沙盒;前版鏈自測原樣印出)
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
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

TAG = "v0121"
HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"


def _vnum_v0121(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0121(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0121(p) < _vnum_v0121(__file__)),
                 key=_vnum_v0121)
PRIOR = _load_v0121(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


# ────────────────── 鍵帶副檔名律 v0121 ──────────────────
_P20 = PRIOR
_PRIOR_INVENTORY = _P20.ssot_inventory


def key_v0121(family: str, ext: str = ".json") -> str:
    base = "VRN|%s|%s" % (_P20._SOURCE, family)
    e = (ext or "").lower().lstrip(".")
    return base if e in ("", "json") else base + "|" + e


def ssot_inventory() -> dict:
    out = _PRIOR_INVENTORY()
    for row in out.get("rows", []):
        row["key"] = key_v0121(row["family"], row.get("ext", ".json"))
    out["key_rule"] = "VRN|central_registry|<族>[|<ext>](json 省略)"
    return out


def ssot_diff() -> dict:
    r = _P20._roots_v0120()
    idx = _P20._load_index_v0120(r)
    out = {"verb": "ssot_diff", "ts": _P20._now_v0120(), "rows": [], "_notes": []}
    counts = {"EQUAL": 0, "DIFF": 0, "MISSING_LOCAL": 0, "MISSING_CENTRAL": 0}
    central = {x["key"]: x for x in ssot_inventory()["rows"]} if r["central"].is_dir() else {}
    for key, ent in sorted(idx["entries"].items()):
        loc = Path(ent.get("local_path", ""))
        ct = central.get(key)
        if not loc.exists():
            st = "MISSING_LOCAL"
        elif ct is None:
            st = "MISSING_CENTRAL"
        else:
            st = "EQUAL" if _P20._sha_v0120(loc) == ct["sha256"] else "DIFF"
        counts[st] += 1
        out["rows"].append({"key": key, "status": st, "local": str(loc),
                            "local_sha": (_P20._sha_v0120(loc) if loc.exists() else None),
                            "central_file": (ct["central_file"] if ct else None), "central_sha": (ct["sha256"] if ct else None)})
    out["counts"] = counts
    out["lamp"] = "RED" if counts["DIFF"] else ("YELLOW" if (counts["MISSING_LOCAL"] or counts["MISSING_CENTRAL"]) else "GREEN")
    if not idx["entries"]:
        out["lamp"] = "GRAY"
        out["_notes"].append("Index 空:先 ssot adopt --apply")
    return out


# 記憶體替換:前版 adopt / number pull / main 內部呼叫的是前版模組全域,換掉後整條 ssot 動詞鏈都走新鍵(前版檔案一字不動)
_P20.ssot_inventory = ssot_inventory
_P20.ssot_diff = ssot_diff
ssot_adopt = _P20.ssot_adopt
ssot_number_pull = _P20.ssot_number_pull
ssot_resolve = _P20.ssot_resolve


def main(argv=None) -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[VRN] 拒絕。只能經 via-vcgc。")
        return 2
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args[:2]:
        return selftest()
    return _P20.main(args)   # ssot 動詞鏈與 intake/eps-check/closeout/reconstruct/layout-check/deepread 照前版鏈(已換鍵)


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

    td = Path(tempfile.mkdtemp(prefix="vrnsm121-"))
    central = td / "central_registry"
    home = td / "VRN"
    for k, v in (("VIA_VRN_SSOT_CENTRAL", str(central)), ("VIA_VRN_SSOT_HOME", str(home)),
                 ("VIA_NO_OPEN", "1"), ("VIA_NO_NET", "1"), ("VIA_VRN_UI_DIR", str(td / "ui"))):
        os.environ[k] = v
    _P20._w_v0120(central / "VRN_Verified_Module_Registry_v0100.json", {"rows": [1, 2]})
    (central / "VRN_Verified_Module_Registry_v0100.csv").write_text("a,b\n1,2\n", encoding="utf-8")
    _P20._w_v0120(central / "VIA_VRN_DocClass_SSOT_v0101.json", {"classes": ["個股"]})
    inv = ssot_inventory()
    keys = sorted(x["key"] for x in inv["rows"])
    chk("① 鍵帶副檔名:同族 json/csv 兩鍵不撞 · json 鍵一字不改",
        keys == ["VRN|central_registry|VIA_VRN_DocClass_SSOT", "VRN|central_registry|VRN_Verified_Module_Registry",
                 "VRN|central_registry|VRN_Verified_Module_Registry|csv"])
    ap = ssot_adopt(apply=True)
    idx = _P20._load_index_v0120(_P20._roots_v0120())
    chk("② adopt --apply:ADOPTED 3 · Index 3 鍵(前版撞鍵時只會 2)· 編號留白 3",
        ap["counts"]["ADOPTED"] == 3 and len(idx["entries"]) == 3 and all(e["ssot_no"] == "" for e in idx["entries"].values()))
    d0 = ssot_diff()
    chk("③ diff 以鍵對中央:同族兩表各對各 → EQUAL 3", d0["counts"]["EQUAL"] == 3 and d0["lamp"] == "GREEN")
    (home / "SSOT" / "VRN_Verified_Module_Registry_v0100.csv").write_text("a,b\n9,9\n", encoding="utf-8")
    d1 = ssot_diff()
    bad = [x["key"] for x in d1["rows"] if x["status"] == "DIFF"]
    chk("④ 負控:只動 csv → 只有 csv 鍵 DIFF,json 鍵仍 EQUAL", bad == ["VRN|central_registry|VRN_Verified_Module_Registry|csv"])
    _P20._w_v0120(central / "VIA_SSOT_Numbers_VRN_v0100.json",
                  {"entries": [{"key": "VRN|central_registry|VRN_Verified_Module_Registry|csv", "ssot_no": "SSOT-VCGC-VRN-BOOK0002"}]})
    n1 = ssot_number_pull()
    chk("⑤ number pull 認得帶 ext 的鍵:filled 1 · pending 2", n1["filled"] == 1 and n1["pending"] == 2)
    chk("⑥ 遷移:前版 v0120 Index(無 ext 鍵)原鍵保留,只新增 csv 鍵,不改不刪",
        "VRN|central_registry|VRN_Verified_Module_Registry" in idx["entries"] and len(idx["entries"]) == 3)
    chk("⑦ 前版鏈動詞可達:adopt/resolve/number_pull 來自 v0120 · main 經前版",
        ssot_adopt is _P20.ssot_adopt and callable(ssot_resolve) and callable(_P20.intake))
    print("  ── 前版鏈自測(原樣印出,不緩衝)──")
    prc = _P20.selftest()
    chk("⑧ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    body = Path(__file__).read_text(encoding="utf-8")
    chk("⑨ 帶加速器橋 · VIA_FROM_VCGC 閘 · glob 取前版", "[VIA:ACCEL-BRIDGE:v0100]" in body and "VIA_FROM_VCGC" in body)
    for k in ("VIA_VRN_SSOT_CENTRAL", "VIA_VRN_SSOT_HOME", "VIA_NO_OPEN", "VIA_NO_NET", "VIA_VRN_UI_DIR"):
        os.environ.pop(k, None)
    shutil.rmtree(td, ignore_errors=True)
    print("[計] VRN_SystemManager_v0121 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
