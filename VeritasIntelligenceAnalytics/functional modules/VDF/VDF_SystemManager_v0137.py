#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_SystemManager v0137 — 薄尾:採納母系統裁定(操作員令 2026-10-06:沒號的分區列管;參數邏輯在不違規下整合;過時退役;不可九頭龍不可傷引擎)。
  table register [--apply]   照前版鏈登記後,讀 VCGC 的 registry/VIA_KeyRulings_v0100.json:
                             ① 本系統表有鍵裁定且表頭冊 keys 空 → 採組合鍵(DF06)或合成鍵 _rid(登記時標 key_ruling,原冊不改)
                             ② 本系統表有退役裁定 → 表頭冊該表標 RETIRED + replaced_by(號留;冊本身由 dormant 流程處理,不毀)
  其餘動詞照前版鏈。沙盒鍵:VIA_VDF_HOME · VIA_VDF_RULINGS(指定裁定書,測試用)。
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

import datetime
import importlib.util
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_SystemManager"
TAG = "v0137"


def _vnum_v0137(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0137(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0137(p) < _vnum_v0137(__file__)), key=_vnum_v0137)
PRIOR = _load_v0137(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


def _rulings_v0137():
    p = os.environ.get("VIA_VDF_RULINGS")
    home = Path(os.environ.get("VIA_VDF_HOME") or HERE)
    fp = Path(p) if p else (home.parents[1] / "supportive modules" / "registry" / "VIA_KeyRulings_v0100.json")
    try:
        return json.loads(fp.read_text(encoding="utf-8-sig")) if fp.exists() else {}
    except ValueError:
        return {}


def _adopt_rulings_v0137(apply: bool) -> dict:
    home = Path(os.environ.get("VIA_VDF_HOME") or HERE)
    reg = home / "registry"
    hits = sorted(reg.glob("VDF_TableHeader_v*.json"), key=lambda q: int(re.search(r"_v(\d{4})", q.name).group(1))) if reg.is_dir() else []
    out = {"keys": 0, "retired": 0, "skipped": 0}
    if not hits:
        return out
    book = json.loads(hits[-1].read_text(encoding="utf-8-sig"))
    rul = _rulings_v0137()
    now = datetime.datetime.now().isoformat(timespec="seconds")
    changed = False
    for tid, r in (rul.get("tables") or {}).items():
        e = book.get("tables", {}).get(tid)
        if not e or r.get("sub") != "VDF":
            continue
        if list(e.get("keys") or []) == list(r["keys"]):
            out["skipped"] += 1
            continue
        if e.get("keys"):
            e["prev_keys"] = e.get("keys")          # 裁定優先於自動剖析鍵(自動鍵 TEST 失敗才會有裁定);舊鍵留 history
        e["keys"] = list(r["keys"])
        for c in e.get("columns", []):
            c["pk"] = c["name"] in r["keys"]
        if r.get("kind") == "synthetic" and not any(c["name"] == "_rid" for c in e.get("columns", [])):
            e["columns"].append({"name": "_rid", "dtype": "str", "required": True, "pk": True, "synthetic": "sha8(整列)"})
        e["key_ruling"] = r.get("kind")
        e["key_ruled_at"] = now
        out["keys"] += 1
        changed = True
    for tid, r in (rul.get("retire") or {}).items():
        e = book.get("tables", {}).get(tid)
        if not e or r.get("sub") != "VDF" or e.get("status") == "RETIRED":
            continue
        e.update(status="RETIRED", retired_at=now, replaced_by=r.get("replaced_by"), retire_reason=r.get("why"))
        out["retired"] += 1
        changed = True
    if apply and changed:
        hits[-1].write_text(json.dumps(book, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


_TABLE_REGISTER_PRIOR = None


def table_register(apply: bool = False) -> dict:
    res = PRIOR.table_register(apply=apply)
    ad = _adopt_rulings_v0137(apply)
    res["rulings"] = ad
    return res


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)

    if "--selftest" in args[:2]:
        return selftest()
    if args[:2] == ["table", "register"]:
        PRIOR.main(args)                                   # 前版鏈登記 + 它自己的 [計] 印出
        ad = _adopt_rulings_v0137(apply_flag(args))     # 再採納母系統裁定
        print("[計] rulings 採納%s · 鍵 %d · 退役 %d · 已有鍵略過 %d" % (" --apply" if apply_flag(args) else "(dry-run)", ad["keys"], ad["retired"], ad["skipped"]))
        return 0
    return PRIOR.main(args)


def apply_flag(args) -> bool:
    return "--apply" in args


def selftest() -> int:
    import shutil
    import tempfile
    p = f = 0

    def chk(name, cond):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s" % name)

    td = Path(tempfile.mkdtemp(prefix="vdfrul-"))
    home = td / "functional modules" / "VDF"
    (home / "registry").mkdir(parents=True)
    saved = {k: os.environ.get(k) for k in ("VIA_VDF_HOME", "VIA_VDF_RULINGS")}
    os.environ["VIA_VDF_HOME"] = str(home)
    os.environ["VIA_VDF_RULINGS"] = str(td / "rul.json")
    (home / "registry" / "VDF_TableHeader_v0100.json").write_text(json.dumps({"tables": {"t_nokey": {"tid": "t_nokey", "keys": [], "columns": [{"name": "a", "dtype": "int", "required": True, "pk": False}], "status": "ACTIVE", "table_no": ""},
        "t_old": {"tid": "t_old", "keys": ["k"], "columns": [], "status": "ACTIVE", "table_no": "SSOT-VCGC-VDF-TBL0009"}, "t_haskey": {"tid": "t_haskey", "keys": ["id"], "columns": [], "status": "ACTIVE", "table_no": ""}}}), encoding="utf-8")
    (td / "rul.json").write_text(json.dumps({"tables": {"t_nokey": {"sub": "VDF", "keys": ["_rid"], "kind": "synthetic"}, "t_haskey": {"sub": "VDF", "keys": ["zz"], "kind": "composite"}, "t_other": {"sub": "XX", "keys": ["q"], "kind": "composite"}},
        "retire": {"t_old": {"sub": "VDF", "replaced_by": "t_new", "why": "過時"}}}), encoding="utf-8")
    d0 = _adopt_rulings_v0137(apply=False)
    bk0 = json.loads((home / "registry" / "VDF_TableHeader_v0100.json").read_text(encoding="utf-8"))
    chk("① dry-run:算到 鍵 2(含覆蓋自動鍵)退役 1,冊未改", d0["keys"] == 2 and d0["retired"] == 1 and bk0["tables"]["t_nokey"]["keys"] == [])
    d1 = _adopt_rulings_v0137(apply=True)
    bk = json.loads((home / "registry" / "VDF_TableHeader_v0100.json").read_text(encoding="utf-8"))
    chk("② --apply:t_nokey 採合成鍵 _rid(加欄標 synthetic)· t_old RETIRED 帶 replaced_by 號留 · 別系統裁定不碰 · 裁定覆蓋自動鍵留 prev_keys", bk["tables"]["t_nokey"]["keys"] == ["_rid"] and any(c["name"] == "_rid" and c.get("synthetic") for c in bk["tables"]["t_nokey"]["columns"])
        and bk["tables"]["t_old"]["status"] == "RETIRED" and bk["tables"]["t_old"]["replaced_by"] == "t_new" and bk["tables"]["t_old"]["table_no"] == "SSOT-VCGC-VDF-TBL0009" and bk["tables"]["t_haskey"]["keys"] == ["zz"] and bk["tables"]["t_haskey"]["prev_keys"] == ["id"])
    d2 = _adopt_rulings_v0137(apply=True)
    chk("③ 冪等:再採納 鍵 0 退役 0", d2["keys"] == 0 and d2["retired"] == 0)
    print("  ── 前版鏈自測(原樣印出)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("④ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    body = Path(__file__).read_text(encoding="utf-8")
    chk("⑤ 帶加速器橋 · glob 取前版", "[VIA:ACCEL-BRIDGE:v0100]" in body)
    for k, v in saved.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    shutil.rmtree(td, ignore_errors=True)
    print("[計] VDF_SystemManager_v0137 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
