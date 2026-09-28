#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL230_ToolCoverageProbe v0101 — 兩支工具的註冊 · 本名版號 · 覆蓋率 · 舊副本 全景探針(只讀)

v0101 adds Ⓕ: the tool each place actually names carries the version.

操作員 2026-09-28:「網路工具名稱不對 請查有版本號 VeritasAegisNexus.py 名稱有版本才對」。
v0100 的 Ⓐ 只問登錄冊與載入器,全綠;可是每個 VIA 行程真正掛上的是啟動層
(bootstrap/sitecustomize ④)決定的——它掛的是無版號的 network/VeritasAegisNexus.py
(本體,沒有 v0116 反封鎖梯)與 accelerator/VeritasCeleritas.py(23 行 CLI 座位)。冊綠、現場錯。

Ⓕ 一列一件工具,五個地方各自說它叫什麼,全部要是**同一個版號檔名**才綠:
  冊(VIA_EngineVersion_Register 的 engine 列)· 載入器解析(CGC_MDL225 尾版 resolved)·
  啟動層實掛(起一個子行程讀 VIA_TOOLS_MOUNT)· 加速器名冊尾版 network_mount/fetch_mount ·
  鎖(VIA_ToolVersion_Lock)。任一處是無版號名或不同版 → RED,並指名是哪一處。
其餘各格照 v0100(L05 每格問正主;L10 只印不刪)。只讀 · 零網路 · 不安裝。

用法:
  python CGC_MDL230_ToolCoverageProbe_v0101.py probe [--zip <VeritasCeleritas-v*.zip>] [--plain] [--width N] [--json]
  python CGC_MDL230_ToolCoverageProbe_v0101.py --selftest
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

import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEM = "CGC_MDL230_ToolCoverageProbe"
VERSIONED = re.compile(r"_v\d{4}\.py$")
TOOLS = (("accelerator", "VeritasCeleritas", "fetch_mount"), ("network", "VeritasAegisNexus", "network_mount"))


def _vnum(path: Path) -> int:
    match = re.search(r"_v(\d+)$", path.stem)
    return int(match.group(1)) if match else -1


def _prior() -> Path:
    mine = _vnum(Path(__file__))
    older = [p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < mine]
    if not older:
        raise ImportError(f"{STEM}: no version below v{mine:04d}")
    return max(older, key=_vnum)


PRIOR = _prior()
_spec = importlib.util.spec_from_file_location(f"{STEM}_prior_for_v{_vnum(Path(__file__)):04d}", PRIOR)
_PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _PRIOR
_spec.loader.exec_module(_PRIOR)

VIA = _PRIOR.VIA
SUPP = _PRIOR.SUPP
ENGINE_TAG = f"{STEM} v{_vnum(Path(__file__)):04d}"
_PRIOR.ENGINE_TAG = ENGINE_TAG
_PROBE = _PRIOR.probe
_SELFTEST = _PRIOR.selftest


def _json(path: Path | None) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path and path.is_file() else {}
    except Exception as exc:
        return {"_error": f"{path.name}: {type(exc).__name__}"}


def _newest(folder: Path, pattern: str) -> Path | None:
    hits = [p for p in folder.glob(pattern) if re.search(r"_v\d+$", p.stem)]
    return max(hits, key=_vnum) if hits else None


def boot_mounts(timeout: int = 180) -> dict:
    """Start one child with the VIA bootstrap on PYTHONPATH and read what it mounted. No tool body is loaded."""
    env = dict(os.environ)
    env.pop("VIA_BOOT", None)
    env.pop("VIA_TOOLS_MOUNT", None)
    boot = str(SUPP / "bootstrap")
    env["PYTHONPATH"] = boot + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    try:
        cp = subprocess.run([sys.executable, "-c", "import os;print(os.environ.get('VIA_TOOLS_MOUNT',''))"],
                            capture_output=True, text=True, env=env, timeout=timeout, cwd=str(VIA))
    except Exception as exc:
        return {"_error": f"{type(exc).__name__}: {str(exc)[:80]}"}
    out = {}
    for part in (cp.stdout.strip().splitlines() or [""])[-1].split(";"):
        if "=" in part:
            name, how = part.split("=", 1)
            out[name] = Path(how.split(":", 1)[1]).name if how.startswith("lazy:") else how
    return out


def judge(tool: str, names: dict) -> tuple:
    """One lamp for one tool. names = {place: file name}. GREEN only if every place names one versioned file."""
    wrong = [f"{k}={v or 'ABSENT'}" for k, v in names.items() if not v or not VERSIONED.search(str(v))]
    distinct = sorted({str(v) for v in names.values() if v})
    if wrong:
        return "RED", "無版號或缺:" + " · ".join(wrong)
    if len(distinct) != 1:
        return "RED", "各處版號不一:" + " · ".join(f"{k}={v}" for k, v in names.items())
    return "GREEN", f"{len(names)} 處同名 {distinct[0]}"


def names_by_place(res: dict | None = None) -> dict:
    book = _json(HERE / "VIA_EngineVersion_Register_v0100.json")
    lock = _json(HERE / "VIA_ToolVersion_Lock_v0100.json")
    roster_path = _newest(HERE, "VIA_Accelerator_Roster_SSOT_v*.json")
    control = (_json(roster_path).get("control_plane") or {})
    mounts = boot_mounts()
    res = res if res is not None else (_PRIOR.versions().get("resolved") or {})
    out = {}
    for fam, name, field in TOOLS:
        reg = next((r["file"] for r in book.get("rows") or [] if r.get("family") == fam and r.get("role") == "engine"), "")
        out[fam] = {
            "冊 engine": reg,
            "載入器解析": res.get(fam, ""),
            "啟動層實掛": mounts.get(name, mounts.get("_error", "")),
            f"名冊 {roster_path.name if roster_path else '?'}": Path(str(control.get(field, ""))).name,
            "鎖": Path(str((lock.get(fam) or {}).get("path", ""))).name,
        }
    return out


def unity(res: dict | None = None) -> dict:
    places = names_by_place(res)
    rows = []
    for fam, names in places.items():
        lamp, why = judge(fam, names)
        rows.append([lamp, fam] + [names[k] or "ABSENT" for k in names] + [why])
    cols = ["燈", "工具"] + list(next(iter(places.values())).keys()) + ["判"]
    state = "RED" if any(r[0] == "RED" for r in rows) else "GREEN"
    return {"state": state, "rows": rows, "cols": cols}


def probe(zip_path: Path | None = None, root: Path = VIA) -> dict:
    rep = _PROBE(zip_path, root)
    u = unity(rep.get("resolved") or {})
    rep["kpi"].insert(1, ["Ⓕ 工具本名(版號)", u["state"],
                          " · ".join(f"{r[1]} {r[2]}" for r in u["rows"]) + " · 冊/解析/啟動層/名冊/鎖 五處同名"])
    rep["sections"].insert(1, ("Ⓕ 工具本名:五處都要是同一個版號檔名(啟動層實掛 = 每個 VIA 行程 import 到的那一份)",
                               u["cols"], u["rows"], 0))
    for r in u["rows"]:
        if r[0] != "GREEN":
            rep["todo"].insert(0, ["RED", "本名", r[1], r[-1], "把寫無版號名的那一處改成版號尾版(L04 新版號;冊只增)"])
    rep["unity"] = u
    rep["engine"] = ENGINE_TAG
    rep["verdict"] = _PRIOR._worst([k[1] for k in rep["kpi"] if k[1] not in ("HOLD", "INFO")])
    return rep


_PRIOR.probe = probe

for _name, _value in vars(_PRIOR).items():
    if not _name.startswith("__") and _name not in globals():
        globals()[_name] = _value


def __getattr__(name: str):
    """Every public name of the prior version stays reachable here."""
    return getattr(_PRIOR, name)


def selftest() -> int:
    _PRIOR.probe = _PROBE              # v0100 的九檢量 v0100 的形狀(五張矩陣、KPI 四列)
    try:
        rc = _SELFTEST()
    finally:
        _PRIOR.probe = probe
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' · ' + note) if note else ''}")

    good = {"a": "VeritasAegisNexus_v0116.py", "b": "VeritasAegisNexus_v0116.py"}
    chk("⑩ 判準:五處同一版號檔名才綠", judge("network", good)[0] == "GREEN")
    chk("⑪ 負控:任一處是無版號名 → RED 並指名那一處",
        judge("network", dict(good, c="VeritasAegisNexus.py"))[0] == "RED"
        and "c=VeritasAegisNexus.py" in judge("network", dict(good, c="VeritasAegisNexus.py"))[1])
    chk("⑫ 負控:兩處版號不一 → RED", judge("network", dict(good, c="VeritasAegisNexus_v0115.py"))[0] == "RED")
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        rep = probe()
        w = _PRIOR.write(rep, Path(td), use_plain=True, echo=False)
        j = json.loads(Path(w["json"]).read_text(encoding="utf-8"))
    chk("⑭ v0101 形狀:六張矩陣 + KPI 五列(Ⓕ 在 Ⓐ 之後)",
        len(j["sections"]) == 6 and len(j["kpi"]) == 5 and j["kpi"][1][0].startswith("Ⓕ"),
        f"總判 {rep['verdict']}")
    u = rep["unity"]
    chk("⑬ 真樹:加速器與網路工具五處同名且有版號", u["state"] == "GREEN",
        " | ".join(f"{r[1]} {r[-1]}" for r in u["rows"]))
    ok = rc == 0 and all(results)
    print(f"  {ENGINE_TAG} selftest +{sum(results)}/{len(results)} {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


_PRIOR.selftest = selftest


def main(argv=None) -> int:
    return _PRIOR.main(argv)


if __name__ == "__main__":
    sys.exit(main())
