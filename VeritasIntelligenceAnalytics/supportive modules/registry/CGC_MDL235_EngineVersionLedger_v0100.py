#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL235_EngineVersionLedger v0100 — 無版號引擎的版本登錄冊(版號記在冊上,不改檔名)

操作員:「所有引擎都要有版本號註冊進行控管」「以此時此刻已成功鎖定的引擎全部上版本號 全部同步註冊更新」。
量過:活樹引擎命名(XXX_ENGnnn_ / XXX_MDLnnn_)的 .py 2299 支,其中 274 支檔名沒有 _vNNNN。
它們多半被**按模組名匯入**(套件內互叫);改檔名會斷匯入,也會打破雜湊鎖——所以不改名,改成**登錄**:
  每支一列:碼 · 路徑 · 版號(檔名帶舊式短版號 _vNNN 照用,否則 v0100 起)· sha256(CRLF/LF 正規化)·
  類別(A 去重副本 _sha / B 舊式短版號 / C 同碼已有版號尾版 / D 冊上 renamed_from 舊名 / E 無版號無後繼)· 後繼。
  **只增不減**:舊列永不刪改;檔的位元變了 → 追加一列新版號(v0100 → v0101 …,previous 指舊 sha);
  檔不見了 → 追加一列 state=ABSENT(不刪舊列)。
  check:每支現況 sha 要等於冊上最新一列;變了卻沒登錄 = RED(L04:換版要留版史)。
只收 VCGC 呼叫(VIA_FROM_VCGC=YES);build 預設乾跑,--apply 才寫冊。零網路、不改任何引擎檔。

用法(經 VCGC):
  python CGC_MDL235_EngineVersionLedger_v0100.py check
  python CGC_MDL235_EngineVersionLedger_v0100.py build [--apply]
  python CGC_MDL235_EngineVersionLedger_v0100.py --selftest
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

import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
ENGINE = Path(__file__).stem
LEDGER_GLOB = "VIA_EngineVersion_Ledger_v*.json"
LEDGER_NEW = HERE / "VIA_EngineVersion_Ledger_v0100.json"
SKIP = ("references/", "VIA_RetiredEngines", "new modules engines", "VIA_Reports/", "_superseded", "SCOPE_COPY",
        "VIA_Standalone_Package", "_backup", "/tests/", "_inbox", "quarantine")
ENG = re.compile(r"^([A-Z]{2,4}_(?:ENG|MDL)\d{3})_")
VERSIONED = re.compile(r"_v\d{4}\.py$")


def _vnum(path: Path) -> int:
    match = re.search(r"_v(\d+)$", path.stem)
    return int(match.group(1)) if match else -1


def ledger_path() -> Path:
    hits = [p for p in HERE.glob(LEDGER_GLOB) if re.search(r"_v\d+$", p.stem)]
    return max(hits, key=_vnum) if hits else LEDGER_NEW


def load_ledger() -> dict:
    p = ledger_path()
    if not p.is_file():
        return {"schema": "VIA.EngineVersionLedger.v1", "append_only": True, "rows": []}
    return json.loads(p.read_text(encoding="utf-8"))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def tracked(root: Path = VIA) -> list:
    out = subprocess.run(["git", "ls-files", "*.py"], cwd=root, capture_output=True, text=True).stdout.splitlines()
    return [f for f in out if not any(s in f for s in SKIP)]


def unversioned(files: list) -> list:
    return [f for f in files if ENG.match(Path(f).name) and not VERSIONED.search(f)]


def _renamed() -> dict:
    hits = [p for p in HERE.glob("VIA_Naming_Registry_v*.json") if re.search(r"_v\d+$", p.stem)]
    if not hits:
        return {}
    items = json.loads(max(hits, key=_vnum).read_text(encoding="utf-8")).get("items") or {}
    rows = items.values() if isinstance(items, dict) else items
    return {Path(r["renamed_from"]).stem: r.get("canonical") for r in rows if isinstance(r, dict) and r.get("renamed_from")}


def classify(rel: str, versioned_by_code: dict, renamed: dict) -> tuple:
    stem = Path(rel).stem
    code = ENG.match(Path(rel).name).group(1)
    if re.search(r"_sha[0-9a-f]{6,}$", stem):
        return "A", "去重副本 _sha(證據,非活引擎)", None
    m = re.search(r"_v(\d{1,3})$", stem)
    if m:
        return "B", "舊式短版號 _vNNN", None
    if code in versioned_by_code:
        return "C", "同碼已有版號尾版", versioned_by_code[code]
    if stem in renamed:
        return "D", "冊上 renamed_from 舊名", renamed[stem]
    return "E", "無版號、無後繼", None


def _first_version(rel: str) -> str:
    m = re.search(r"_v(\d{1,3})$", Path(rel).stem)
    return "v%04d" % int(m.group(1)) if m else "v0100"


def _bump(version: str) -> str:
    return "v%04d" % (int(version.lstrip("v")) + 1)


def plan(root: Path = VIA, book: dict | None = None) -> dict:
    book = book if book is not None else load_ledger()
    files = tracked(root)
    by_code = {}
    for f in files:
        m = ENG.match(Path(f).name)
        if m and VERSIONED.search(f):
            by_code.setdefault(m.group(1), Path(f).name)
    renamed = _renamed()
    latest = {}
    for row in book.get("rows") or []:
        latest[row["path"]] = row
    adds, same = [], 0
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    current = unversioned(files)
    for rel in current:
        sha = _sha(root / rel)
        last = latest.get(rel)
        cat, why, succ = classify(rel, by_code, renamed)
        if last and last.get("sha256") == sha and last.get("state") != "ABSENT":
            same += 1
            continue
        version = _bump(last["version"]) if last else _first_version(rel)
        adds.append({"code": ENG.match(Path(rel).name).group(1), "path": rel, "version": version, "sha256": sha,
                     "category": cat, "why": why, "successor": succ, "state": "PRESENT",
                     "previous": ({"version": last["version"], "sha256": last["sha256"]} if last else None), "at": now})
    gone = [p for p, r in latest.items() if r.get("state") != "ABSENT" and p not in set(current)]
    for rel in gone:
        adds.append({**latest[rel], "state": "ABSENT", "previous": {"version": latest[rel]["version"],
                                                                   "sha256": latest[rel]["sha256"]}, "at": now})
    cats = {}
    for r in adds:
        cats[r["category"]] = cats.get(r["category"], 0) + 1
    return {"unversioned": len(current), "unchanged": same, "adds": adds, "by_category": cats}


def check(root: Path = VIA) -> dict:
    p = plan(root)
    new = [r for r in p["adds"] if r["previous"] is None]
    changed = [r for r in p["adds"] if r["previous"] is not None and r["state"] == "PRESENT"]
    gone = [r for r in p["adds"] if r["state"] == "ABSENT"]
    state = "GREEN" if not p["adds"] else "RED"
    return {"via": "vcgc", "door": ENGINE, "ledger": ledger_path().name, "state": state,
            "unversioned": p["unversioned"], "registered_same": p["unchanged"],
            "not_registered": len(new), "changed_without_version": len(changed), "gone": len(gone),
            "examples": [f"{r['path']} → {r['version']}" for r in (changed + new + gone)[:8]],
            "next": "none" if state == "GREEN" else "via-vcgc 跑 build --apply 登錄(新版號追加,舊列不動)"}


def build(apply: bool = False) -> dict:
    book = load_ledger()
    p = plan(book=book)
    if apply and p["adds"]:
        book.setdefault("rows", []).extend(p["adds"])
        book["schema"], book["append_only"] = "VIA.EngineVersionLedger.v1", True
        book["rule"] = ("檔名沒有 _vNNNN 的引擎,版號記在本冊;位元一變就追加新版號,舊列永不刪改;"
                        "檔不見追加 ABSENT。check 看現況 sha 是否等於最新一列。")
        path = ledger_path()
        path.write_text(json.dumps(book, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="")
    return {"via": "vcgc", "door": ENGINE, "apply": apply, "ledger": ledger_path().name, "unversioned": p["unversioned"],
            "adds": len(p["adds"]), "by_category": p["by_category"], "unchanged": p["unchanged"]}


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False))
        return 2
    if args[:1] == ["build"]:
        print(json.dumps(build("--apply" in args), ensure_ascii=False, indent=1))
        return 0
    card = check()
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return 0 if card["state"] == "GREEN" else 2


def selftest() -> int:
    import tempfile
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' · ' + note) if note else ''}")

    keep = os.environ.pop("VIA_FROM_VCGC", None)
    chk("① 沒從 VCGC 進就拒", main(["build", "--apply"]) == 2)
    if keep is not None:
        os.environ["VIA_FROM_VCGC"] = keep
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        (root / "m").mkdir()
        (root / "m" / "ABC_ENG001_Thing.py").write_text("x = 1\n", encoding="utf-8")
        (root / "m" / "ABC_ENG002_Old_v012.py").write_text("y = 1\n", encoding="utf-8")
        (root / "m" / "ABC_ENG003_Done_v0101.py").write_text("z = 1\n", encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=root, check=True)
        p1 = plan(root, {"rows": []})
        chk("② 只登錄檔名沒版號的引擎;舊式短版號照用;帶 _vNNNN 的不進冊",
            sorted((r["path"], r["version"]) for r in p1["adds"]) == [("m/ABC_ENG001_Thing.py", "v0100"), ("m/ABC_ENG002_Old_v012.py", "v0012")],
            str([(r["path"], r["version"]) for r in p1["adds"]]))
        book = {"rows": list(p1["adds"])}
        chk("③ 冊與現況一致 → 零追加", not plan(root, book)["adds"])
        (root / "m" / "ABC_ENG001_Thing.py").write_text("x = 2\n", encoding="utf-8")
        p3 = plan(root, book)
        chk("④ 位元變了 → 追加新版號 v0101,previous 指舊 sha,舊列不動",
            len(p3["adds"]) == 1 and p3["adds"][0]["version"] == "v0101" and p3["adds"][0]["previous"]["version"] == "v0100"
            and book["rows"][0]["version"] == "v0100")
        (root / "m" / "ABC_ENG002_Old_v012.py").unlink()
        subprocess.run(["git", "add", "-A"], cwd=root, check=True)
        p4 = plan(root, book)
        chk("⑤ 檔不見 → 追加 ABSENT,不刪舊列", any(r["state"] == "ABSENT" and r["path"].endswith("_v012.py") for r in p4["adds"]))
    ok = all(results)
    print(f"  {ENGINE} selftest {sum(results)}/{len(results)} {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
