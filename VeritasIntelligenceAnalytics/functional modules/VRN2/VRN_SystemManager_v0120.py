#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0120 — 薄尾:SSOT 下放第一段(操作員令 2026-10-06「VCGC 全部資料先下放到 VRN SYSTEM MANAGER」· L111 ① 正本在基層)。

權責(操作員裁定 2026-10-06):VRN 有生成權 · VCGC 有偵測權與編號權 · 裁決與協調歸操作員 + AI。
本版只做「盤點 + 收養 + 解析 + 比對 + 讀號」,不碰中央 registry 任何一冊(只讀),VRN 自己的冊只增不減、永不覆寫。
  ssot inventory            掃中央 registry 列出全部 VRN 冊(VIA_VRN_* / VRN_* / VRNTextScope / CardBook_VRN / Workflow_VRN)+ 共用冊(只列不搬);每族取尾版 · sha256
  ssot adopt [--apply]      把尾版複製進 functional modules/VRN/SSOT/(VIA_VRN_* → VRN_*);預設 dry-run;已在且 hash 同=SKIP,hash 異=CONFLICT 不覆寫;
                            寫 registry/VRN_SSOT_Index_v0100.json(鍵 VRN|central_registry|<族> · 本機路徑 · 中央路徑 · sha256 · ssot_no 留白)+ 收養帳 jsonl
  ssot resolve <冊名>       統一讀冊入口:先 VRN/SSOT/ 尾版,查無才回退中央並誠實記 note
  ssot diff                 Index 逐冊:本機 hash vs 中央尾版 hash → EQUAL / DIFF(RED)/ MISSING
  ssot number pull          依鍵從中央編號冊(VIA_SSOT_Numbers_VRN_v*.json,VCGC 第二段才會建)讀回 ssot_no 填 Index;冊未建=誠實 PENDING
沙盒鍵(LL114 每個來源都要關得進沙盒):VIA_VRN_SSOT_CENTRAL(中央 registry 夾)· VIA_VRN_SSOT_HOME(VRN 夾)。
自測: VIA_FROM_VCGC=YES python VRN_SystemManager_v0120.py --selftest(全在 temp 沙盒;前版鏈自測原樣印出,不緩衝)
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
import hashlib
import importlib.util
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

TAG = "v0120"
HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"


def _vnum_v0120(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0120(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0120(p) < _vnum_v0120(__file__)),
                 key=_vnum_v0120)
PRIOR = _load_v0120(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


# ────────────────── SSOT 下放律 v0120 ──────────────────
_OWN_GLOBS = ("VIA_VRN_*.json", "VRN_*.json", "VRN_*.csv",
              "VIA_Policy_VRNTextScope_*.json", "VIA_Essentia_CardBook_VRN_*.json", "VIA_Workflow_VRN_SSOT_*.json")
_SHARED_FAMILIES = ("VIA_Central_Synonym_Regex", "VIA_SSOT_SynonymUnion",
                    "VIA_FinalParameters_CanonicalRegistry", "VDF_VRN_SourceFallback_AllDataRegistry")
_LEGACY_RE = re.compile(r"^VRN_MDL\d{3}_")
_INDEX_STEM = "VRN_SSOT_Index"
_LEDGER_NAME = "VRN_SSOT_Adopt_Ledger.jsonl"
_NUMBER_GLOB = "VIA_SSOT_Numbers_VRN_v*.json"
_SOURCE = "central_registry"


def _now_v0120() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


def _roots_v0120() -> dict:
    central = Path(os.environ.get("VIA_VRN_SSOT_CENTRAL") or (HERE.parents[1] / "supportive modules" / "registry"))
    home = Path(os.environ.get("VIA_VRN_SSOT_HOME") or HERE)
    return {"central": central, "ssot": home / "SSOT", "registry": home / "registry"}


def _sha_v0120(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _family_v0120(name: str) -> tuple:
    """檔名 → (族名, 版號字串)。VIA_VRN_X_v0102.json → (VIA_VRN_X, v0102);sha 尾綴剝掉;無版號=v0000。"""
    stem = Path(name).stem
    stem = re.sub(r"_sha[0-9a-f]{8,}$", "", stem)
    m = re.search(r"_(v\d{4})$", stem)
    if m:
        return stem[: m.start()], m.group(1)
    m = re.search(r"_(v\d{2,3}[A-Za-z0-9]*)$", stem)      # VRN_FileRegistry_Stage_v029VRN1C 這類舊式版號
    if m:
        return stem[: m.start()], m.group(1)
    return stem, "v0000"


def _vsort_v0120(ver: str):
    m = re.match(r"v(\d{4})$", ver)
    return (int(m.group(1)) if m else -1, ver)


def _target_v0120(family: str) -> str:
    if family.startswith("VIA_VRN_"):
        return "VRN_" + family[len("VIA_VRN_"):]
    if family.startswith("VIA_"):
        return "VRN_" + family[len("VIA_"):]          # VIA_Policy_VRNTextScope → VRN_Policy_VRNTextScope
    return family


def _key_v0120(family: str) -> str:
    return "VRN|%s|%s" % (_SOURCE, family)


def ssot_inventory() -> dict:
    r = _roots_v0120()
    central = r["central"]
    out = {"verb": "ssot_inventory", "ts": _now_v0120(), "central": str(central), "rows": [], "shared": [], "_notes": []}
    if not central.is_dir():
        out["_notes"].append("中央 registry 不在:%s" % central)
        out["lamp"] = "RED"
        return out
    fams: dict = {}
    seen: set = set()
    for g in _OWN_GLOBS:
        for p in sorted(central.glob(g)):
            if not p.is_file() or p.name in seen:
                continue
            seen.add(p.name)
            fam, ver = _family_v0120(p.name)
            if fam in _SHARED_FAMILIES:
                continue
            fams.setdefault((fam, p.suffix.lower()), []).append((ver, p))
    for (fam, ext), lst in sorted(fams.items()):
        lst.sort(key=lambda t: _vsort_v0120(t[0]))
        ver, p = lst[-1]
        kind = "legacy" if _LEGACY_RE.match(fam) else "own"
        out["rows"].append({
            "key": _key_v0120(fam), "family": fam, "kind": kind, "ext": ext,
            "central_file": p.name, "version": ver, "versions_seen": len(lst),
            "sha256": _sha_v0120(p), "bytes": p.stat().st_size, "target": _target_v0120(fam),
        })
    for fam in _SHARED_FAMILIES:
        hits = sorted(central.glob(fam + "_v*.json"), key=lambda q: _vsort_v0120(_family_v0120(q.name)[1]))
        if hits:
            out["shared"].append({"family": fam, "central_file": hits[-1].name, "sha256": _sha_v0120(hits[-1]),
                                  "action": "LIST_ONLY(切片下放=v0121)"})
    out["own"] = sum(1 for x in out["rows"] if x["kind"] == "own")
    out["legacy"] = sum(1 for x in out["rows"] if x["kind"] == "legacy")
    out["lamp"] = "GREEN" if out["rows"] else "YELLOW"
    if not out["rows"]:
        out["_notes"].append("中央 registry 零 VRN 冊(路徑對嗎?)")
    return out


def _index_path_v0120(r: dict) -> Path:
    hits = sorted(r["registry"].glob(_INDEX_STEM + "_v*.json"), key=lambda q: _vsort_v0120(_family_v0120(q.name)[1]))
    return hits[-1] if hits else r["registry"] / (_INDEX_STEM + "_v0100.json")


def _load_index_v0120(r: dict) -> dict:
    fp = _index_path_v0120(r)
    if fp.exists():
        try:
            d = json.loads(fp.read_text(encoding="utf-8"))
            if isinstance(d, dict) and isinstance(d.get("entries"), dict):
                return d
        except (OSError, ValueError):
            pass
    return {"schema": "VRN_SSOT_Index", "version": "v0100", "key_contract": "VRN|<source>|<table>",
            "rule": "編號格留白;VCGC 偵測無誤後發號;VRN 以鍵讀回;只增不減;不同來源=不同號(L108 ②)",
            "created_at": _now_v0120(), "entries": {}}


def _save_index_v0120(r: dict, idx: dict) -> Path:
    fp = _index_path_v0120(r)
    fp.parent.mkdir(parents=True, exist_ok=True)
    idx["updated_at"] = _now_v0120()
    fp.write_text(json.dumps(idx, ensure_ascii=False, indent=1), encoding="utf-8")
    return fp


def _ledger_v0120(r: dict, row: dict) -> None:
    try:
        r["registry"].mkdir(parents=True, exist_ok=True)
        with open(r["registry"] / _LEDGER_NAME, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    except OSError:
        pass


def ssot_adopt(apply: bool = False) -> dict:
    r = _roots_v0120()
    inv = ssot_inventory()
    out = {"verb": "ssot_adopt", "ts": _now_v0120(), "apply": apply, "ssot_dir": str(r["ssot"]),
           "rows": [], "_notes": list(inv["_notes"]), "shared_skipped": len(inv["shared"])}
    if inv["lamp"] == "RED":
        out["lamp"] = "RED"
        return out
    idx = _load_index_v0120(r)
    counts = {"ADOPTED": 0, "PLAN": 0, "SKIP": 0, "CONFLICT": 0}
    for row in inv["rows"]:
        src = r["central"] / row["central_file"]
        dest = r["ssot"] / ("%s_%s%s" % (row["target"], row["version"], row["ext"]))
        status = "PLAN"
        if dest.exists():
            status = "SKIP" if _sha_v0120(dest) == row["sha256"] else "CONFLICT"
        elif apply:
            r["ssot"].mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            status = "ADOPTED" if _sha_v0120(dest) == row["sha256"] else "CONFLICT"
        counts[status] += 1
        rec = {"key": row["key"], "family": row["family"], "kind": row["kind"], "status": status,
               "local_path": str(dest), "central_path": str(src), "central_version": row["version"],
               "sha256": row["sha256"], "bytes": row["bytes"]}
        out["rows"].append(rec)
        if status in ("ADOPTED", "SKIP"):
            ent = idx["entries"].get(row["key"])
            if ent is None:
                idx["entries"][row["key"]] = {
                    "key": row["key"], "subsystem": "VRN", "source": _SOURCE, "table": row["family"],
                    "kind": row["kind"], "local_path": str(dest), "central_path": str(src),
                    "central_version": row["version"], "sha256": row["sha256"],
                    "ssot_no": "", "adopted_at": _now_v0120(), "history": []}
            elif ent.get("sha256") != row["sha256"]:
                ent.setdefault("history", []).append({"sha256": ent.get("sha256"), "local_path": ent.get("local_path"),
                                                      "central_version": ent.get("central_version"), "until": _now_v0120()})
                ent.update({"local_path": str(dest), "central_path": str(src),
                            "central_version": row["version"], "sha256": row["sha256"]})
        if apply:
            _ledger_v0120(r, {"ts": out["ts"], "key": row["key"], "status": status, "sha256": row["sha256"],
                              "local": str(dest), "central": str(src)})
    if apply or any(x["status"] == "SKIP" for x in out["rows"]):
        if apply:
            out["index"] = str(_save_index_v0120(r, idx))
    out["counts"] = counts
    out["index_entries"] = len(idx["entries"])
    out["blank_numbers"] = sum(1 for e in idx["entries"].values() if not e.get("ssot_no"))
    out["lamp"] = "RED" if counts["CONFLICT"] else ("YELLOW" if (not apply and counts["PLAN"]) else "GREEN")
    if counts["CONFLICT"]:
        out["_notes"].append("CONFLICT=本機同名冊 hash 與中央不同;不覆寫,交操作員+AI 裁(ssot diff 看細節)")
    return out


def ssot_diff() -> dict:
    r = _roots_v0120()
    idx = _load_index_v0120(r)
    out = {"verb": "ssot_diff", "ts": _now_v0120(), "rows": [], "_notes": []}
    counts = {"EQUAL": 0, "DIFF": 0, "MISSING_LOCAL": 0, "MISSING_CENTRAL": 0}
    central_tail = {x["family"]: x for x in ssot_inventory()["rows"]} if r["central"].is_dir() else {}
    for key, ent in sorted(idx["entries"].items()):
        loc = Path(ent.get("local_path", ""))
        ct = central_tail.get(ent.get("table"))
        if not loc.exists():
            st = "MISSING_LOCAL"
        elif ct is None:
            st = "MISSING_CENTRAL"
        else:
            st = "EQUAL" if _sha_v0120(loc) == ct["sha256"] else "DIFF"
        counts[st] += 1
        out["rows"].append({"key": key, "status": st, "local": str(loc), "local_sha": (_sha_v0120(loc) if loc.exists() else None),
                            "central_file": (ct["central_file"] if ct else None), "central_sha": (ct["sha256"] if ct else None)})
    out["counts"] = counts
    out["lamp"] = "RED" if counts["DIFF"] else ("YELLOW" if (counts["MISSING_LOCAL"] or counts["MISSING_CENTRAL"]) else "GREEN")
    if not idx["entries"]:
        out["lamp"] = "GRAY"
        out["_notes"].append("Index 空:先 ssot adopt --apply")
    return out


def ssot_resolve(book: str) -> dict:
    """book = 族名(VRN_DocClass_SSOT / VIA_VRN_DocClass_SSOT 皆可)。先本機 SSOT/ 尾版,查無回退中央。"""
    r = _roots_v0120()
    cands = {book, _target_v0120(book)}
    if book.startswith("VRN_"):
        cands.add("VIA_" + book)
    out = {"verb": "ssot_resolve", "book": book, "path": None, "where": None, "_notes": []}
    for stem in sorted(cands):
        hits = sorted(list(r["ssot"].glob(stem + "_v*.json")) + list(r["ssot"].glob(stem + "_v*.csv")),
                      key=lambda q: _vsort_v0120(_family_v0120(q.name)[1]))
        if hits:
            out.update(path=str(hits[-1]), where="local", lamp="GREEN")
            return out
    for stem in sorted(cands):
        hits = sorted(list(r["central"].glob(stem + "_v*.json")) + list(r["central"].glob(stem + "_v*.csv")),
                      key=lambda q: _vsort_v0120(_family_v0120(q.name)[1]))
        if hits:
            out.update(path=str(hits[-1]), where="central", lamp="YELLOW")
            out["_notes"].append("本機 SSOT/ 無此冊,回退中央(尚未下放或屬共用/政策冊)")
            return out
    out.update(lamp="RED")
    out["_notes"].append("本機與中央都查無:%s" % book)
    return out


def ssot_number_pull() -> dict:
    r = _roots_v0120()
    idx = _load_index_v0120(r)
    out = {"verb": "ssot_number_pull", "ts": _now_v0120(), "filled": 0, "already": 0, "pending": 0, "rows": [], "_notes": []}
    books = sorted(r["central"].glob(_NUMBER_GLOB), key=lambda q: _vsort_v0120(_family_v0120(q.name)[1])) if r["central"].is_dir() else []
    table: dict = {}
    if books:
        try:
            d = json.loads(books[-1].read_text(encoding="utf-8"))
            ents = d.get("entries") if isinstance(d, dict) else d
            if isinstance(ents, dict):
                table = {k: (v.get("ssot_no") if isinstance(v, dict) else v) for k, v in ents.items()}
            elif isinstance(ents, list):
                table = {e.get("key"): e.get("ssot_no") for e in ents if isinstance(e, dict) and e.get("key")}
            out["number_book"] = books[-1].name
        except (OSError, ValueError) as exc:
            out["_notes"].append("編號冊讀取失敗 %s:%s" % (books[-1].name, type(exc).__name__))
    else:
        out["_notes"].append("中央編號冊未建(%s)— VCGC 第二段才發號;全部 PENDING 屬正常" % _NUMBER_GLOB)
    changed = False
    for key, ent in sorted(idx["entries"].items()):
        if ent.get("ssot_no"):
            out["already"] += 1
            st = "ALREADY"
        elif table.get(key):
            ent["ssot_no"] = str(table[key])
            ent["numbered_at"] = _now_v0120()
            out["filled"] += 1
            changed = True
            st = "FILLED"
        else:
            out["pending"] += 1
            st = "PENDING"
        out["rows"].append({"key": key, "status": st, "ssot_no": ent.get("ssot_no", "")})
    if changed:
        out["index"] = str(_save_index_v0120(r, idx))
    out["lamp"] = "GREEN" if (idx["entries"] and out["pending"] == 0) else ("GRAY" if idx["entries"] else "GRAY")
    return out


def _emit_v0120(verb: str, out: dict) -> None:
    fn = getattr(PRIOR, "emit_matrix_html", None)
    if callable(fn):
        try:
            fn(verb, out)
        except Exception as exc:  # noqa: BLE001 — U/I 失敗不擋主流程,誠實印
            print("  [U/I] emit_matrix_html %s(主流程照走)" % type(exc).__name__)
    dump = getattr(PRIOR, "_dump_result_v0119", None)
    if callable(dump):
        dump(verb, out)


def _print_tally_v0120(out: dict) -> None:
    v = out.get("verb")
    if v == "ssot_inventory":
        print("[計] ssot inventory own=%d legacy=%d shared=%d(只列)· %s" % (out.get("own", 0), out.get("legacy", 0), len(out.get("shared", [])), out["lamp"]))
    elif v == "ssot_adopt":
        c = out.get("counts", {})
        print("[計] ssot adopt%s ADOPTED=%d PLAN=%d SKIP=%d CONFLICT=%d · Index=%d 冊 · 編號留白=%d · %s"
              % (" --apply" if out["apply"] else "(dry-run)", c.get("ADOPTED", 0), c.get("PLAN", 0), c.get("SKIP", 0), c.get("CONFLICT", 0),
                 out.get("index_entries", 0), out.get("blank_numbers", 0), out["lamp"]))
        for x in out["rows"]:
            if x["status"] == "CONFLICT":
                print("  [RED] CONFLICT %s · 本機 %s" % (x["key"], x["local_path"]))
    elif v == "ssot_diff":
        c = out.get("counts", {})
        print("[計] ssot diff EQUAL=%d DIFF=%d MISSING_LOCAL=%d MISSING_CENTRAL=%d · %s"
              % (c.get("EQUAL", 0), c.get("DIFF", 0), c.get("MISSING_LOCAL", 0), c.get("MISSING_CENTRAL", 0), out["lamp"]))
        for x in out["rows"]:
            if x["status"] == "DIFF":
                print("  [RED] DIFF %s" % x["key"])
    elif v == "ssot_resolve":
        print("[計] ssot resolve %s → %s · %s · %s" % (out["book"], out.get("where"), out.get("path"), out["lamp"]))
    elif v == "ssot_number_pull":
        print("[計] ssot number pull filled=%d already=%d pending=%d · %s" % (out["filled"], out["already"], out["pending"], out["lamp"]))
    for n in out.get("_notes", []):
        print("  [注] %s" % n)


def main(argv=None) -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[VRN] 拒絕。只能經 via-vcgc。")
        return 2
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args[:2]:
        return selftest()
    as_json = "--json" in args
    a = [x for x in args if x != "--json"]
    if a[:1] == ["ssot"]:
        sub = a[1] if len(a) > 1 else ""
        if sub == "inventory":
            out = ssot_inventory()
        elif sub == "adopt":
            out = ssot_adopt(apply=("--apply" in a))
        elif sub == "diff":
            out = ssot_diff()
        elif sub == "resolve":
            if len(a) < 3:
                print("[拒跑] ssot resolve <冊名>")
                return 2
            out = ssot_resolve(a[2])
        elif sub == "number" and a[2:3] == ["pull"]:
            out = ssot_number_pull()
        else:
            print("[拒跑] ssot inventory | adopt [--apply] | resolve <冊名> | diff | number pull")
            return 2
        _emit_v0120(out["verb"], out)
        if as_json:
            print(json.dumps(out, ensure_ascii=False))
        _print_tally_v0120(out)
        return 1 if out.get("lamp") == "RED" else 0
    return PRIOR.main(args)   # intake/eps-check/reconcile/closeout/reconstruct/layout-check/deepread 照前版鏈


def _w_v0120(p: Path, obj) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")


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

    td = Path(tempfile.mkdtemp(prefix="vrnsm120-"))
    central = td / "central_registry"
    home = td / "VRN"
    os.environ["VIA_VRN_SSOT_CENTRAL"] = str(central)
    os.environ["VIA_VRN_SSOT_HOME"] = str(home)
    os.environ["VIA_NO_OPEN"] = "1"
    os.environ["VIA_NO_NET"] = "1"
    os.environ["VIA_VRN_UI_DIR"] = str(td / "ui")
    _w_v0120(central / "VIA_VRN_DocClass_SSOT_v0100.json", {"v": 100})
    _w_v0120(central / "VIA_VRN_DocClass_SSOT_v0101.json", {"v": 101, "classes": ["個股", "產業"]})
    _w_v0120(central / "VRN_S05_FieldRegistry_v0102.json", {"fields": ["ReportDate", "TargetPrice"]})
    _w_v0120(central / "VIA_Policy_VRNTextScope_v0100.json", {"scope": "text"})
    _w_v0120(central / "VRN_MDL105_VRN_DoNotRedo_DoneRegistry__SUPPORT_RULE__v0_0.json", {"legacy": True})
    _w_v0120(central / "VIA_Central_Synonym_Regex_v0107.json", {"regex": {}, "synonyms": {}})
    _w_v0120(central / "VIA_Policy_Laws_SSOT_v0106.json", {"laws": []})
    r = _roots_v0120()
    chk("① 沙盒生效:中央/本機根都在 temp(LL114 每個來源都關進沙盒)",
        str(r["central"]).startswith(str(td)) and str(r["ssot"]).startswith(str(td)) and str(r["registry"]).startswith(str(td)))
    inv = ssot_inventory()
    fam = {x["family"]: x for x in inv["rows"]}
    chk("② inventory:每族只取尾版(DocClass→v0101,見 2 版)· own 3 · legacy 1 · shared 1 只列",
        fam.get("VIA_VRN_DocClass_SSOT", {}).get("version") == "v0101" and fam["VIA_VRN_DocClass_SSOT"]["versions_seen"] == 2
        and inv["own"] == 3 and inv["legacy"] == 1 and len(inv["shared"]) == 1 and inv["lamp"] == "GREEN")
    chk("③ 改名律:VIA_VRN_X→VRN_X · VIA_Policy_VRNTextScope→VRN_Policy_VRNTextScope · VRN_* 原名",
        fam["VIA_VRN_DocClass_SSOT"]["target"] == "VRN_DocClass_SSOT"
        and fam["VIA_Policy_VRNTextScope"]["target"] == "VRN_Policy_VRNTextScope"
        and fam["VRN_S05_FieldRegistry"]["target"] == "VRN_S05_FieldRegistry")
    chk("④ 鍵契約 VRN|central_registry|<族>", all(re.match(r"^VRN\|central_registry\|[A-Za-z0-9_]+$", x["key"]) for x in inv["rows"]))
    dry = ssot_adopt(apply=False)
    chk("⑤ adopt dry-run:PLAN 4 · 本機 SSOT/ 未建 · Index 未寫 · 黃燈",
        dry["counts"]["PLAN"] == 4 and not r["ssot"].exists() and not _index_path_v0120(r).exists() and dry["lamp"] == "YELLOW")
    ap = ssot_adopt(apply=True)
    dest = r["ssot"] / "VRN_DocClass_SSOT_v0101.json"
    idx = _load_index_v0120(r)
    chk("⑥ adopt --apply:ADOPTED 4 · 檔在且 hash 同 · Index 4 鍵 · 編號格全留白 · 共用冊沒搬",
        ap["counts"]["ADOPTED"] == 4 and dest.exists() and _sha_v0120(dest) == fam["VIA_VRN_DocClass_SSOT"]["sha256"]
        and len(idx["entries"]) == 4 and all(e["ssot_no"] == "" for e in idx["entries"].values())
        and not list(r["ssot"].glob("*Synonym*")) and ap["lamp"] == "GREEN")
    ap2 = ssot_adopt(apply=True)
    chk("⑦ 冪等:第二次 apply 全 SKIP · Index 仍 4 鍵 · 帳本 8 列", ap2["counts"]["SKIP"] == 4 and ap2["counts"]["ADOPTED"] == 0
        and len(_load_index_v0120(r)["entries"]) == 4
        and len((r["registry"] / _LEDGER_NAME).read_text(encoding="utf-8").splitlines()) == 8)
    d0 = ssot_diff()
    chk("⑧ diff 全 EQUAL 綠", d0["counts"]["EQUAL"] == 4 and d0["lamp"] == "GREEN")
    dest.write_text('{"tampered": true}', encoding="utf-8")
    d1 = ssot_diff()
    chk("⑨ 負控:本機被動手腳 → diff DIFF=1 紅", d1["counts"]["DIFF"] == 1 and d1["lamp"] == "RED")
    ap3 = ssot_adopt(apply=True)
    chk("⑩ 永不覆寫:hash 異=CONFLICT 紅 · 本機內容原封不動", ap3["counts"]["CONFLICT"] == 1
        and dest.read_text(encoding="utf-8") == '{"tampered": true}' and ap3["lamp"] == "RED")
    dest.write_text((central / "VIA_VRN_DocClass_SSOT_v0101.json").read_text(encoding="utf-8"), encoding="utf-8")
    rs = ssot_resolve("VRN_DocClass_SSOT")
    rs2 = ssot_resolve("VIA_VRN_DocClass_SSOT")
    rs3 = ssot_resolve("VIA_Policy_Laws_SSOT")
    rs4 = ssot_resolve("VRN_NoSuchBook")
    chk("⑪ resolve:本機優先(新舊名都認)· 政策冊回退中央黃 · 查無紅",
        rs["where"] == "local" and rs2["where"] == "local" and rs["path"].endswith("VRN_DocClass_SSOT_v0101.json")
        and rs3["where"] == "central" and rs3["lamp"] == "YELLOW" and rs4["lamp"] == "RED")
    n0 = ssot_number_pull()
    chk("⑫ number pull:編號冊未建 → 全 PENDING 灰 · 誠實記注", n0["pending"] == 4 and n0["filled"] == 0 and n0["lamp"] == "GRAY" and n0["_notes"])
    _w_v0120(central / "VIA_SSOT_Numbers_VRN_v0100.json",
             {"entries": [{"key": "VRN|central_registry|VIA_VRN_DocClass_SSOT", "ssot_no": "SSOT_2026_000123"}]})
    n1 = ssot_number_pull()
    n2 = ssot_number_pull()
    e = _load_index_v0120(r)["entries"]["VRN|central_registry|VIA_VRN_DocClass_SSOT"]
    chk("⑬ 發號後依鍵讀回:filled 1 · pending 3 · Index 填 SSOT_2026_000123 · 再拉=already 1 不重填",
        n1["filled"] == 1 and n1["pending"] == 3 and e["ssot_no"] == "SSOT_2026_000123"
        and n2["filled"] == 0 and n2["already"] == 1)
    chk("⑭ 只讀中央:自測全程中央 registry 檔數不變(7 冊 + 1 編號冊)", len(list(central.glob("*.json"))) == 8)
    print("  ── 前版鏈自測(原樣印出,不緩衝;資訊卡 2026-10-05 v0117 教訓)──")
    prc = PRIOR.selftest()
    chk("⑮ 前版鏈 %s 自測 rc 0 · intake/eps-check/closeout 可達" % PRIOR_PATH.stem,
        prc == 0 and callable(PRIOR.intake) and callable(__getattr__("closeout")))
    body = Path(__file__).read_text(encoding="utf-8")
    chk("⑯ 帶加速器橋 · VIA_FROM_VCGC 閘 · glob 取前版", "[VIA:ACCEL-BRIDGE:v0100]" in body and "VIA_FROM_VCGC" in body)
    for k in ("VIA_VRN_SSOT_CENTRAL", "VIA_VRN_SSOT_HOME", "VIA_NO_OPEN", "VIA_NO_NET", "VIA_VRN_UI_DIR"):
        os.environ.pop(k, None)
    shutil.rmtree(td, ignore_errors=True)
    print("[計] VRN_SystemManager_v0120 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
