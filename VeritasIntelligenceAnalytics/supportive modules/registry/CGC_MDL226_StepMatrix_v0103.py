#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL226_StepMatrix v0103 — 薄尾:第 4–8 步從 HOLD 改成真量(唯讀;不套編號 · 不寫 PS · 不裝境 · 不改冊)

操作員(2026-10-03,貼回 via-vcgc test 136 站 · 紅 94):
  「修正以下問題  5 HOLD number after_policy 自動編碼編號,本口不套用 · 6 HOLD ps_template later · 7 HOLD env later ·
   8 HOLD subsystem 到這步才讀 … 加入加速模板或加速器」

先量(v0100–v0102):步 4–8 的燈一律 HOLD、ran=False,只是「排在後面」的宣告,從來沒量過;串測看到的是四個永遠不會變的 HOLD。
本尾版照 L04 只增:v0100 的 front() 照跑(步 1–3 一字不動),再把 4–8 填上真量到的燈。每步照原門禁「本口不做」的事仍然不做:

  4 policy      政策冊尾版在不在、讀不讀得到(只讀檔頭;整冊判定仍由 CGC_MDL207 PolicyRun / 流程閘,本口不印冊)
  5 number      自動編號:掃家族尾版,**撞號**(同家族同號不同名)照列、無號照列;只報不套用(applied=False)
  6 ps_template PS 模板 / 加速器章:倉根 Invoke-VIA-* 尾版 + Register 尾版 + supportive modules/*.ps1,
                查 CELERITAS-TEMPLATE-JOIN 與 [VIA:PS-ACCEL 兩個章;唯一 PS 入口(OperatorConsole 尾版)缺章 = RED;本口不寫任何 .ps1(written=False)
  7 env         沿用 VIA_Reports/env_manager/ENVMGR_latest.json 的總判 + 幾小時前(不重跑 416 秒的 check;不裝,installed=False);沒檔 = NODATA
  8 subsystem   照 v0100 的 subsystem_sync()(CGC_MDL219 RegexParamSync.check):drift 空 = GREEN,否則 YELLOW;冊不改(rewritten=False)
  3 accel_net   多報一個數:registry 家族尾版裡帶 [VIA:ACCEL-BRIDGE 的比例(加速器導入覆蓋),缺的列前 20 支;燈的判定照 v0100 不動

燈的意思:GREEN 過 · YELLOW 有發現(只列不修)· RED 擋 · NODATA 沒料 · HOLD 不再出現在 4–8。
main() 的 rc 照 v0100:前三步全綠 0,否則 2(4–8 的紅黃進卡,不改 rc;改 rc 等於改流程閘,那是 MDL207 的事)。
零網路 · 不安裝 · 不寫冊 · 不寫 .ps1 · 不套編號。
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
import sys
import time
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEM = "CGC_MDL226_StepMatrix"
VIA = HERE.parents[1]


def _vnum(path: Path) -> int:
    m = re.search(r"_v(\d+)$", path.stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location(STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    return getattr(PRIOR, name)


# 鏈:v0102 → v0101 → v0100。main() 用「自己模組的全域名」叫 front,所以要換的是鏈上**第一個自己定義 front 的那一支**(不是 __getattr__ 轉接來的);
# 本體 v0100 另留一個把手給 write_page / subsystem_sync / PAGE / ORDER。
_BASE = PRIOR
while hasattr(_BASE, "PRIOR"):
    _BASE = _BASE.PRIOR
_TOP = PRIOR
while "front" not in vars(_TOP) and hasattr(_TOP, "PRIOR"):
    _TOP = _TOP.PRIOR
_FRONT0 = _TOP.front

NUM_RX = re.compile(r"^(?P<fam>[A-Z]{2,5})_(?P<kind>MDL|ENG)(?P<no>\d{3})_(?P<name>\w+?)(?:_v\d{4})?\.py$")
SNAP_RX_V0103 = re.compile(r"(_sha[0-9a-f]{6,}|_v\d{4}R)+$")   # 同一支的快照 / 封存尾巴不算另一個名字
SKIP = {"references", "intake", "_output", "runs", "test", "tests", "fixtures", "sandbox", "__pycache__", "_to_delete", "archive", "backup"}


def _psvnum_v0103(path: Path) -> int:
    """PS 檔版號寫成 -vNNNN(OperatorConsole-v0111),Python 檔寫成 _vNNNN;兩種都認(_vnum 只認底線 → PS 檔全是 -1)。"""
    m = re.search(r"[-_]v(\d{4})$", path.stem)
    return int(m.group(1)) if m else -1


def _newest(folder: Path, pattern: str) -> Path | None:
    if not folder.is_dir():
        return None
    hits = sorted(folder.glob(pattern), key=_vnum)
    return hits[-1] if hits else None


def _head(path: Path, n: int = 12000) -> str:
    try:
        with path.open(encoding="utf-8", errors="replace") as fh:
            return fh.read(n)
    except Exception:
        return ""


def _tails_by_family(folders: list[Path]) -> dict[str, Path]:
    """同 stem 只取尾版(版號最大);沒版號的檔也算一支。"""
    tails: dict[str, Path] = {}
    for folder in folders:
        if not folder.is_dir():
            continue
        for p in folder.rglob("*.py"):
            if any(part in SKIP for part in p.relative_to(folder).parts[:-1]):
                continue
            stem = re.sub(r"_v\d{4}$", "", p.stem)
            if stem not in tails or _vnum(p) > _vnum(tails[stem]):
                tails[stem] = p
    return tails


def step_policy() -> dict:
    book = _newest(HERE, "VIA_Policy_Laws_SSOT_v*.json")
    ok = book is not None and _head(book, 200).lstrip().startswith("{")
    return {"lamp": "GREEN" if ok else "RED", "book": book.name if book else "", "printed": False,
            "judge": "CGC_MDL207_PolicyRun / 流程閘(本口只確認冊在、讀得到)", "missing": [] if ok else ["policy_book"]}


def step_number() -> dict:
    folders = [VIA / "functional modules" / "VDF", VIA / "functional modules" / "VRN", HERE,
               VIA / "supportive modules" / "70_VRN_Rules", VIA / "supportive modules" / "network"]
    tails = _tails_by_family(folders)
    by_no: dict[str, set] = defaultdict(set)
    unnumbered: list[str] = []
    for stem, p in tails.items():
        m = NUM_RX.match(p.name)
        if not m:
            unnumbered.append(str(p.relative_to(VIA)))
            continue
        by_no[m.group("fam") + "_" + m.group("kind") + m.group("no")].add(SNAP_RX_V0103.sub("", m.group("name")))
    collisions = {k: sorted(v) for k, v in by_no.items() if len(v) > 1}
    lamp = "YELLOW" if (collisions or unnumbered) else "GREEN"
    return {"lamp": lamp, "families": len(tails), "numbered": len(tails) - len(unnumbered),
            "collisions": collisions, "unnumbered": sorted(unnumbered)[:40], "unnumbered_total": len(unnumbered),
            "applied": False, "missing": sorted(collisions)}


def step_ps_template() -> dict:
    files: list[Path] = []
    fam: dict[str, Path] = {}
    for p in list(VIA.glob("Invoke-VIA-*.ps1")) + list(VIA.glob("Register-VIA-Commands-v*.ps1")):
        stem = re.sub(r"[-_]v\d{4}$", "", p.stem)
        if stem not in fam or _psvnum_v0103(p) > _psvnum_v0103(fam[stem]):
            fam[stem] = p
    files = sorted(fam.values()) + sorted((VIA / "supportive modules").glob("*.ps1"))
    no_join, no_accel = [], []
    for p in files:
        head = _head(p, 2_000_000)      # 讀整檔:入口檔頭說明很長,章在 6000 字元之後(v0111 第 122 行)
        if "CELERITAS-TEMPLATE-JOIN" not in head:
            no_join.append(p.name)
        if "[VIA:PS-ACCEL" not in head and "VIA_PS_Accel_Module" not in head:
            no_accel.append(p.name)
    entry = fam.get("Invoke-VIA-OperatorConsole")
    entry_ok = entry is not None and entry.name not in no_join and entry.name not in no_accel
    lamp = "RED" if not entry_ok else ("YELLOW" if (no_join or no_accel) else "GREEN")
    return {"lamp": lamp, "files": len(files), "entry": entry.name if entry else "", "entry_ok": entry_ok,
            "no_template_join": no_join[:40], "no_accel_bridge": no_accel[:40],
            "no_template_join_total": len(no_join), "no_accel_bridge_total": len(no_accel),
            "written": False, "missing": ([] if entry_ok else ["ps_entry_marks"])}


def step_env() -> dict:
    latest = VIA / "VIA_Reports" / "env_manager" / "ENVMGR_latest.json"
    if not latest.is_file():
        return {"lamp": "NODATA", "verdict": "", "age_h": None, "source": str(latest.relative_to(VIA)), "installed": False,
                "missing": ["ENVMGR_latest.json"], "rerun": "via-vcgc run --family core CGC_MDL240_EnvManager check"}
    try:
        verdict = str(json.loads(latest.read_text(encoding="utf-8")).get("verdict", "")).upper()
    except Exception:
        verdict = ""
    age_h = round((time.time() - latest.stat().st_mtime) / 3600.0, 1)
    lamp = {"GREEN": "GREEN", "AMBER": "YELLOW", "YELLOW": "YELLOW", "RED": "RED"}.get(verdict, "NODATA")
    if lamp == "GREEN" and age_h > 24:
        lamp = "YELLOW"
    return {"lamp": lamp, "verdict": verdict, "age_h": age_h, "source": str(latest.relative_to(VIA)), "installed": False,
            "missing": [] if lamp == "GREEN" else ["env_" + (verdict or "NODATA").lower()],
            "rerun": "via-vcgc run --family core CGC_MDL240_EnvManager check"}


def step_subsystem() -> dict:
    try:
        card = _BASE.subsystem_sync()
    except Exception as exc:  # 冊缺 / 鎖冊缺 → 誠實 NODATA,不冒充綠
        return {"lamp": "NODATA", "error": str(exc)[:200], "rewritten": False, "missing": ["subsystem_sync"]}
    drift = card.get("drift") or []
    missing = card.get("missing") or []
    lamp = "GREEN" if (not drift and not missing) else "YELLOW"
    return {"lamp": lamp, "drift": drift, "aligned": card.get("aligned"), "regex_book": card.get("regex_book"),
            "synonym_book": card.get("synonym_book"), "param_books": card.get("param_books"),
            "conflicts_stay": card.get("conflicts_stay"), "rewritten": False, "missing": list(missing)}


def accel_coverage() -> dict:
    tails = _tails_by_family([HERE, VIA / "functional modules" / "VDF", VIA / "functional modules" / "VRN"])
    lacking = sorted(str(p.relative_to(VIA)) for p in tails.values() if "VIA:ACCEL-BRIDGE" not in _head(p, 4000))
    return {"tails": len(tails), "with_bridge": len(tails) - len(lacking), "lacking": lacking[:20], "lacking_total": len(lacking)}


def front() -> dict:
    card = _FRONT0()                      # 步 1–3 一字不動(前版 front 全跑完才接手)
    later = {"policy": step_policy(), "number": step_number(), "ps_template": step_ps_template(),
             "env": step_env(), "subsystem": step_subsystem()}
    for row in card["rows"]:
        detail = later.get(row["id"])
        if detail is None:
            continue
        row["lamp"] = detail["lamp"]
        row["ran"] = True
        row["missing"] = list(detail.get("missing") or [])
    card["later"] = later
    card["accel_net"]["coverage"] = accel_coverage()
    card["door"] = Path(__file__).stem
    # opened_subsystem 照 v0100 的意思:前三步有沒有開子系統冊(v0161 / v0170 自測守這條)→ 仍是 False。
    # 第 8 步(子系統步)才讀冊比對,另記一欄照實說,不混進 opened_subsystem。
    card["subsystem_read"] = later["subsystem"]["lamp"] != "NODATA"
    card["subsystem_read_step"] = 8
    card["numbered"] = False
    card["ps_written"] = False
    card["env_updated"] = False
    card["book_edited"] = False
    card["later_pass"] = all(d["lamp"] == "GREEN" for d in later.values())
    card["later_missing"] = [k for k, d in later.items() if d["lamp"] != "GREEN"]
    if card.get("next") == "none" and not card["later_pass"]:
        card["next"] = "4–8 有發現(只列不修):" + ",".join(card["later_missing"]) + " → 看 later.*;編號 / PS 章 / 境 / 冊各自的正主修"
    return card


_TOP.front = front                    # 前版 main() / selftest() 用模組全域名 front → 走本版


def main() -> int:
    return PRIOR.main()


def selftest() -> int:
    """前版自測仍要過(它斷言 4–8 是 HOLD 的那一句在本版不再成立 → 用本版的規則重驗同一件事)。"""
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' · ' + note) if note else ''}")

    os.environ.pop("VIA_FROM_VCGC", None)
    denied = _TOP.main() == 2
    os.environ["VIA_FROM_VCGC"] = "YES"
    card = front()
    _BASE.write_page(card)
    rows = {r["id"]: r for r in card["rows"]}
    early = [r for r in card["rows"] if r["step"] <= 3]
    later = [r for r in card["rows"] if r["step"] >= 4]
    chk("① 不經 via-vcgc → DENY rc 2(同前版)", denied)
    chk("② 步 1–3 一字不動:順序同 ORDER · 前三步綠 · 不開子系統 · accel_net 不執行",
        [r["id"] for r in card["rows"]] == [n for _, n, _, _ in _BASE.ORDER] and all(r["lamp"] == "GREEN" for r in early)
        and all(r["may_open_subsystem"] is False for r in early) and card["accel_net"]["ran"] is False,
        ",".join(card["missing"]))
    chk("③ 步 4–8 不再 HOLD:每步有燈且 ran=True · 燈只在 GREEN/YELLOW/RED/NODATA",
        all(r["lamp"] in ("GREEN", "YELLOW", "RED", "NODATA") and r["ran"] is True for r in later))
    L = card["later"]
    chk("④ 本口不做的事仍不做:編號不套用 · PS 不寫 · 境不裝 · 冊不改",
        L["number"]["applied"] is False and L["ps_template"]["written"] is False and L["env"]["installed"] is False
        and L["subsystem"]["rewritten"] is False and card["numbered"] is False and card["ps_written"] is False
        and card["env_updated"] is False and card["book_edited"] is False)
    chk("⑤ 撞號規則:同家族同號不同名才算;無號只列不紅",
        isinstance(L["number"]["collisions"], dict) and L["number"]["lamp"] in ("GREEN", "YELLOW"),
        f"家族 {L['number']['families']} · 撞號 {len(L['number']['collisions'])} · 無號 {L['number']['unnumbered_total']}")
    chk("⑥ PS 章:唯一入口缺章才 RED;其餘缺章 YELLOW 只列",
        (L["ps_template"]["lamp"] == "RED") == (not L["ps_template"]["entry_ok"]),
        f"檔 {L['ps_template']['files']} · 缺模板章 {L['ps_template']['no_template_join_total']} · 缺加速章 {L['ps_template']['no_accel_bridge_total']} · 入口 {L['ps_template']['entry'] or '(無)'}")
    chk("⑦ 境:沿用 ENVMGR_latest.json,不重跑;沒檔 NODATA;超過 24h 的綠降黃",
        (L["env"]["lamp"] == "NODATA") == (L["env"]["age_h"] is None), f"{L['env']['verdict'] or 'NODATA'} · {L['env']['age_h']}h")
    chk("⑧ 子系統:drift 空且 missing 空才綠;冊不改", L["subsystem"]["lamp"] in ("GREEN", "YELLOW", "NODATA"),
        f"drift {len(L['subsystem'].get('drift') or [])}")
    chk("⑨ 加速器覆蓋:registry/VDF/VRN 尾版帶 [VIA:ACCEL-BRIDGE 的比例有量到",
        card["accel_net"]["coverage"]["tails"] >= 0 and "lacking_total" in card["accel_net"]["coverage"],
        f"{card['accel_net']['coverage']['with_bridge']}/{card['accel_net']['coverage']['tails']}")
    chk("⑫ 撞號不把同一支的快照 / 封存當成另一個名字(_sha… · _vNNNNR)",
        SNAP_RX_V0103.sub("", "OutputManager_shadd77e5eb") == "OutputManager" and SNAP_RX_V0103.sub("", "FinancialModel_v0100R") == "FinancialModel"
        and SNAP_RX_V0103.sub("", "TableRestorer_shae4a8560f6a41") == "TableRestorer")
    chk("⑪ PS 尾版認 -vNNNN:OperatorConsole 取版號最大那支(不是 glob 掃到的第一支)",
        _psvnum_v0103(Path("Invoke-VIA-OperatorConsole-v0111.ps1")) == 111 and _psvnum_v0103(Path("x_v0103.py")) == 103
        and (not L["ps_template"]["entry"] or _psvnum_v0103(Path(L["ps_template"]["entry"])) == max(
            [_psvnum_v0103(q) for q in VIA.glob("Invoke-VIA-OperatorConsole-*.ps1")] or [-1])), L["ps_template"]["entry"])
    chk("⑬ opened_subsystem 照 v0100 的意思(前三步不開子系統)仍是 False;第 8 步讀冊另記 subsystem_read(v0161 / v0170 自測守這條)",
        card["opened_subsystem"] is False and card.get("subsystem_read_step") == 8 and isinstance(card.get("subsystem_read"), bool))
    chk("⑩ 頁仍寫同一路徑(VIA_Step_Matrix_v0100.html),含 4–8 的燈", _BASE.PAGE.is_file() and "HOLD" not in _BASE.PAGE.read_text(encoding="utf-8"))
    ok = all(results)
    print(f"  {Path(__file__).stem} selftest +{sum(results)}/{len(results)} {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
