#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL236_NumberedCatalog v0100 — VCGC · VDF · VRN 編號總冊 · 測試狀態 · 流程邏輯路徑(紅黃綠 · 鎖定時間)

操作員 2026-09-28:「每一個 vcgc vdf vrn 所用的工具 參數 ssot regex 參數 指數都有編號 全部整理列入 u/i tab 最後一頁
紅黃綠三燈顯示狀況 偵測工具 unit integration system test 狀態顯示 流程邏輯 workflow 圖像化也放最後 tabs 全都編號
邏輯路徑編號備份 附上版本號及鎖定日期(還要加上時間)只增不減只要不衝突」。

本支只彙整、不另立尺(L05):每一列的狀態都問正主——
  TOOL   工具登錄冊 VIA_EngineVersion_Register(+ 鎖冊 sha:CGC_MDL233)
  SSOT   registry 下每一本 *SSOT* 冊(同族取尾版):讀得動 = 綠
  REGEX  SSOT 冊裡鍵名帶 regex/pattern 的字串 + 工具本體 / VRN 規則模組的 re.compile 字面(CGC_MDL233 param_tables):
         編得過 = 綠;編不過 = 紅;同一鍵名在兩處不同值 = 黃(衝突,只增不減要求不衝突)
  PARAM  工具本體與 VRN 規則模組的字面參數表(CGC_MDL233 param_tables):一張表一號
  INDEX  DB 表冊 VIA_DB_Table_SSOT 尾版的每一張表(指數 · 指標 · 名冊資料)
  TEST   unit = 自測格子 GRID 最新一份 · integration = VDF / VRN 鏈最新一份 · system = 一鍵 RUNALL 步驟 ·
         偵測工具 = 各探針最新報告(CGC_MDL233 / MDL235 當場量)
  PATH   流程邏輯路徑:流程冊 VIA_Workflow_SSOT 每一條 · VRN 邏輯冊每一層 · VDF 鏈站序
編號:VIA_Numbering_Ledger_v*(尾版)—— 同一個鍵永遠同一號,新鍵取下一號,**舊號永不改、永不刪**。
鎖定時間:該筆來源檔在 git 上最後一次提交的時間(日期 + 時間 + 時區);鎖燈冊另附 measured_at(工作站時間)。
路徑備份:VIA_LogicPath_Backup_v*(尾版)—— 路徑內容一變就追加一列新版號(v0100 → v0101 …),舊列不動。
只收 VCGC 呼叫;build 預設乾跑,--apply 才寫編號冊與路徑備份。零網路。
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
import importlib.util
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
REPO = VIA.parent
REPORTS = VIA / "VIA_Reports"
ENGINE = Path(__file__).stem
PREFIX = {"TOOL": "TL", "SSOT": "SS", "REGEX": "RX", "PARAM": "PM", "INDEX": "IX", "TEST": "TS", "PATH": "LP"}
LEDGER_NEW = HERE / "VIA_Numbering_Ledger_v0100.json"
BACKUP_NEW = HERE / "VIA_LogicPath_Backup_v0100.json"
LAMP = {"GREEN": "綠", "AMBER": "黃", "RED": "紅"}


def _vnum(path: Path) -> int:
    match = re.search(r"_v(\d+)$", path.stem)
    return int(match.group(1)) if match else -1


def _newest(folder: Path, pattern: str) -> Path | None:
    hits = [p for p in folder.glob(pattern) if re.search(r"_v\d+$", p.stem)]
    return max(hits, key=_vnum) if hits else None


def _json(path: Path | None):
    if not path or not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


_GIT_TIME: dict = {}


def locked_at(path: Path) -> str:
    """Last commit time of this file (date + time + zone). Not committed yet = 'uncommitted'."""
    key = str(path)
    if key not in _GIT_TIME:
        out = subprocess.run(["git", "log", "-1", "--format=%ci", "--", str(path)], cwd=REPO,
                             capture_output=True, text=True).stdout.strip()
        _GIT_TIME[key] = out or "uncommitted"
    return _GIT_TIME[key]


def _version_of(name: str) -> str:
    m = re.search(r"_v(\d{4})(?:\.\w+)?$", name)
    return "v" + m.group(1) if m else "—"


def _activator():
    p = _newest(HERE, "CGC_MDL233_ToolActivate_v*.py")
    return _load(p, "tool_activate_for_mdl236") if p else None


# ---------------------------------------------------------------- numbering (append-only)
def load_ledger() -> dict:
    return _json(_newest(HERE, "VIA_Numbering_Ledger_v*.json")) or {"schema": "VIA.NumberingLedger.v1", "append_only": True,
                                                                     "next": {}, "codes": {}}


def number(ledger: dict, kind: str, key: str) -> str:
    codes, nxt = ledger.setdefault("codes", {}), ledger.setdefault("next", {})
    full = f"{kind}|{key}"
    if full not in codes:
        n = int(nxt.get(kind, 1))
        codes[full] = f"{PREFIX[kind]}-{n:04d}"
        nxt[kind] = n + 1
    return codes[full]


# ---------------------------------------------------------------- catalog
def _row(ledger, kind, key, name, version, source, locked, lamp, note=""):
    return {"code": number(ledger, kind, key), "kind": kind, "name": name, "version": version, "source": source,
            "locked_at": locked, "lamp": lamp, "note": note}


def tools(ledger: dict) -> list:
    reg_p = HERE / "VIA_EngineVersion_Register_v0100.json"
    reg = _json(reg_p) or {}
    act = _activator()
    lock = (_json(act.lock_path()) if act else None) or {}
    rows = []
    for r in reg.get("rows") or []:
        path = VIA / r.get("path", "")
        lamp, note = "GREEN", r.get("role", "")
        if not path.is_file():
            lamp, note = "RED", "檔不在"
        elif _version_of(path.name) == "—":
            lamp, note = "AMBER", "沒有四位版號"
        ent = lock.get(r.get("family")) or {}
        if r.get("role") == "engine" and ent:
            pinned = act.pinned(r["family"]) if act else None
            if not pinned or pinned.name != path.name:
                lamp, note = "RED", f"冊 engine ≠ 鎖冊({pinned.name if pinned else '缺'})"
        src = act.lock_path() if (act and ent and r.get("role") == "engine") else reg_p
        rows.append(_row(ledger, "TOOL", f"{r.get('family')}|{r.get('role')}|{r.get('code')}", path.name, _version_of(path.name),
                         f"{r.get('code')} · {r.get('family')}", locked_at(src), lamp, note))
    return rows


def ssot_books() -> list:
    fam = {}
    for p in HERE.glob("*SSOT*.json"):
        key = re.sub(r"_v\d+$", "", p.stem)
        if key not in fam or _vnum(p) > _vnum(fam[key]):
            fam[key] = p
    return sorted(fam.values(), key=lambda p: p.name)


def ssot(ledger: dict) -> list:
    rows = []
    for p in ssot_books():
        data = _json(p)
        lamp, note = ("GREEN", f"{len(data) if hasattr(data, '__len__') else 1} 鍵") if data is not None else ("RED", "讀不動")
        rows.append(_row(ledger, "SSOT", re.sub(r"_v\d+$", "", p.stem), p.name, _version_of(p.name), "registry",
                         locked_at(p), lamp, note))
    return rows


def _walk_regex(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            sub = f"{path}.{k}" if path else str(k)
            if isinstance(v, str) and re.search(r"(?i)regex|pattern|\brx\b", str(k)):
                yield sub, v
            else:
                yield from _walk_regex(v, sub)
    elif isinstance(obj, list):
        for i, v in enumerate(obj[:500]):
            yield from _walk_regex(v, f"{path}[{i}]")


def _rule_modules() -> list:
    """Tool bodies (lock book) + VRN rule / SSOT module tails that carry literal tables."""
    out = []
    act = _activator()
    if act:
        for fam in ("accelerator", "network"):
            p = act.pinned(fam)
            if p:
                out.append(act._body_of(p))
    rules = VIA / "supportive modules" / "70_VRN_Rules"
    fam = {}
    for p in rules.glob("SUP_MDL0*_v*.py"):
        if re.search(r"(?i)ssot|regex|alias|ticker|lexicon", p.stem):
            k = re.sub(r"_v\d+$", "", p.stem)
            if k not in fam or _vnum(p) > _vnum(fam[k]):
                fam[k] = p
    return out + sorted(fam.values(), key=lambda p: p.name)


def regex_and_params(ledger: dict) -> tuple:
    act = _activator()
    rx_rows, pm_rows, seen = [], [], {}
    for p in ssot_books():
        book = re.sub(r"_v\d+$", "", p.stem)
        for key, pat in _walk_regex(_json(p) or {}):
            seen.setdefault(key.split(".")[-1], set()).add(pat)
            try:
                re.compile(pat)
                lamp, note = "GREEN", ""
            except re.error as exc:
                lamp, note = "RED", f"編不過:{exc}"
            rx_rows.append(_row(ledger, "REGEX", f"{book}|{key}", key, _version_of(p.name), p.name,
                                locked_at(p), lamp, (note or pat)[:90]))
    for mod in _rule_modules():
        try:
            tables = act.param_tables(mod) if act else {}
        except SyntaxError:
            tables = {}
        base = re.sub(r"_v\d+$", "", mod.stem)
        for key, val in tables.items():
            if key.endswith("#regex"):
                seen.setdefault(key[:-6].split(".")[-1], set()).add(str(val))
                try:
                    re.compile(val)
                    lamp, note = "GREEN", str(val)[:90]
                except re.error as exc:
                    lamp, note = "RED", f"編不過:{exc}"
                rx_rows.append(_row(ledger, "REGEX", f"{base}|{key}", key[:-6], _version_of(mod.name), mod.name,
                                    locked_at(mod), lamp, note))
            else:
                size = len(val) if hasattr(val, "__len__") and not isinstance(val, str) else 1
                pm_rows.append(_row(ledger, "PARAM", f"{base}|{key}", key, _version_of(mod.name), mod.name,
                                    locked_at(mod), "GREEN", f"{type(val).__name__} · {size} 項"))
    for r in rx_rows:                                   # same key name, two different patterns = conflict (AMBER)
        if r["lamp"] == "GREEN" and len(seen.get(r["name"].split(".")[-1], ())) > 1:
            r["lamp"], r["note"] = "AMBER", "同名 regex 兩處不同值(衝突待裁定):" + r["note"]
    return rx_rows, pm_rows


def indices(ledger: dict) -> list:
    p = _newest(HERE, "VIA_DB_Table_SSOT_v*.json")
    book = _json(p) or {}
    dbm = _json(REPORTS / "dbmanager" / "DBM_REPORT_latest.json") or {}
    seen = {str(t.get("table")): t for t in (dbm.get("tables") or []) if isinstance(t, dict)}
    rows = []
    for t in book.get("tables") or []:
        name = str(t.get("table"))
        live = seen.get(name)
        if live is None:
            lamp, note = "AMBER", "本機沒有 DB 面板量測(工作站跑一鍵後才有)"
        else:
            st = str(live.get("state") or live.get("lamp") or "").upper()
            lamp = "GREEN" if st in ("GREEN", "OK") else "RED" if st in ("RED", "HIGH") else "AMBER"
            note = st
        rows.append(_row(ledger, "INDEX", f"{t.get('db', '')}|{name}", name, _version_of(p.name) if p else "—",
                         f"{t.get('db', '')}", locked_at(p) if p else "—", lamp, (note + " · " + str(t.get("note") or ""))[:120]))
    return rows


# ---------------------------------------------------------------- tests
def _state_lamp(state) -> str:
    s = str(state or "").upper()
    if s in ("OK", "GREEN", "PASS", "DONE"):
        return "GREEN"
    if s.startswith(("FAIL", "RED", "CRASH", "RC=", "TIMEOUT", "ERROR")):
        return "RED"
    return "AMBER"


def tests(ledger: dict) -> list:
    rows = []
    grid_p = max(REPORTS.glob("selftest_runs/GRID_*.json"), default=None)
    grid = _json(grid_p) or {}
    for st in grid.get("rows") or grid.get("stations") or grid.get("results") or []:
        rows.append(_row(ledger, "TEST", f"unit|{st.get('name')}", str(st.get("name")), "unit", grid_p.name if grid_p else "",
                         str(grid.get("ts") or ""), _state_lamp(st.get("state")), str(st.get("note") or "")[:120]))
    if not rows:
        rows.append(_row(ledger, "TEST", "unit|grid", "自測格子", "unit", "VIA_Reports/selftest_runs", "—", "AMBER", "還沒有 GRID 報告"))
    for name, glob_pat, key in (("VDF 鏈", "vdf_chain/VDFCHAIN_*.json", "id"), ("VRN 鏈", "vrn_chain/VRNCHAIN_*.json", "name")):
        p = max(REPORTS.glob(glob_pat), default=None)
        rep = _json(p) or {}
        items = next((v for v in rep.values() if isinstance(v, list) and v and isinstance(v[0], dict) and key in v[0]), [])
        for it in items:
            rows.append(_row(ledger, "TEST", f"integration|{name}|{it.get(key)}", f"{name} · {it.get(key)}", "integration",
                             p.name if p else "", str(rep.get("generated") or rep.get("ts") or ""),
                             _state_lamp(it.get("state") or it.get("lamp")), str(it.get("why") or it.get("note") or "")[:120]))
        if not items:
            rows.append(_row(ledger, "TEST", f"integration|{name}", name, "integration", glob_pat, "—", "AMBER", "還沒有鏈報告"))
    run = _json(REPORTS / "runall" / "RUNALL_STEPS_latest.json") or {}
    for st in run.get("steps") or []:
        rows.append(_row(ledger, "TEST", f"system|{st.get('id') or st.get('title')}", str(st.get("title")), "system",
                         "RUNALL_STEPS_latest.json", str(run.get("ts") or ""), _state_lamp(st.get("state")),
                         " / ".join(st.get("tail") or [])[:120]))
    if not run:
        rows.append(_row(ledger, "TEST", "system|runall", "一鍵 RUNALL", "system", "VIA_Reports/runall", "—", "AMBER", "還沒有一鍵紀錄"))
    act = _activator()
    probes = []
    if act:
        st = act.status()
        probes.append(("CGC_MDL233 工具鎖冊", "GREEN" if st["next"] == "none" else "RED",
                       " · ".join(f"{t['family']}={t['pinned']}" for t in st["tools"]), act.lock_path()))
    led = _newest(HERE, "CGC_MDL235_EngineVersionLedger_v*.py")
    if led:
        ck = _load(led, "ledger_for_mdl236").check()
        probes.append(("CGC_MDL235 引擎版本登錄", ck["state"], f"登錄 {ck['registered_same']} · 未登 {ck['not_registered']} · 變了未登 {ck['changed_without_version']}",
                       _load(led, "ledger_for_mdl236b").ledger_path()))
    for label, rel, field in (("CGC_MDL230 工具覆蓋探針", "toolprobe/TOOLPROBE_latest.json", "verdict"),
                              ("CGC_MDL234 舊名殘留探針", "toolprobe/RENAME_RESIDUE_latest.json", "ps"),
                              ("CGC_MDL156 加速器控管", "accelerator/VIA_ACCELERATOR_CONTROL_latest.json", "verdict")):
        rep = _json(REPORTS / rel)
        if rep is None:
            probes.append((label, "AMBER", "本機還沒跑(報告不在)", REPORTS / rel))
            continue
        val = rep.get(field)
        lamp = ("GREEN" if not (val or {}).get("LIVE") else "RED") if isinstance(val, dict) else _state_lamp(val)
        probes.append((label, lamp, json.dumps(val, ensure_ascii=False)[:120], REPORTS / rel))
    for label, lamp, note, src in probes:
        rows.append(_row(ledger, "TEST", f"detect|{label}", label, "偵測工具", Path(src).name,
                         locked_at(src) if str(src).startswith(str(VIA / "supportive modules")) else "當場量/報告", lamp, note))
    return rows


# ---------------------------------------------------------------- logic paths (+ append-only backup)
def logic_paths(ledger: dict) -> list:
    paths = []
    wf_p = HERE / "VIA_Workflow_SSOT_v0100.json"
    for w in (_json(wf_p) or {}).get("workflows") or []:
        paths.append({"key": f"workflow|{w.get('id')}", "name": f"{w.get('id')} · {w.get('zh', '')}", "nodes": list(w.get("nodes") or []),
                      "source": wf_p.name, "src": wf_p})
    vl_p = HERE / "VIA_VRN_LogicArchitecture_SSOT_v0100.json"
    vl = _json(vl_p) or {}
    for layer, body in (vl.get("layers") or {}).items():
        paths.append({"key": f"vrn_layer|{layer}", "name": f"VRN {layer}", "nodes": [n.get("family") for n in body.get("nodes") or []],
                      "source": f"{vl_p.name} {vl.get('version', '')}", "src": vl_p})
    lock_p = _newest(HERE, "VIA_LampLock_v*.json")
    lock = _json(lock_p) or {}
    for chain, nodes in (lock.get("nodes") or {}).items():
        paths.append({"key": f"locked_chain|{chain}", "name": f"{chain.upper()} 鏈(鎖燈冊)", "nodes": list(nodes),
                      "source": f"{lock_p.name} · measured_at {lock.get('measured_at', '')}", "src": lock_p})
    for p in paths:
        p["code"] = number(ledger, "PATH", p["key"])
        p["sha"] = hashlib.sha256(json.dumps(p["nodes"], ensure_ascii=False).encode()).hexdigest()[:16]
        p["locked_at"] = locked_at(p["src"])
    return paths


def backup_plan(paths: list) -> list:
    book = _json(_newest(HERE, "VIA_LogicPath_Backup_v*.json")) or {"rows": []}
    last = {}
    for r in book.get("rows") or []:
        last[r["code"]] = r
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S +0000")
    adds = []
    for p in paths:
        prev = last.get(p["code"])
        if prev and prev["sha"] == p["sha"]:
            continue
        version = "v%04d" % (int(prev["version"][1:]) + 1) if prev else "v0100"
        adds.append({"code": p["code"], "key": p["key"], "name": p["name"], "nodes": p["nodes"], "sha": p["sha"],
                     "version": version, "source": p["source"], "source_locked_at": p["locked_at"], "backed_up_at": now,
                     "previous": {"version": prev["version"], "sha": prev["sha"]} if prev else None})
    return adds


def path_versions(paths: list) -> dict:
    book = _json(_newest(HERE, "VIA_LogicPath_Backup_v*.json")) or {"rows": []}
    out = {}
    for r in book.get("rows") or []:
        out[r["code"]] = r
    return out


def catalog() -> dict:
    ledger = load_ledger()
    rx, pm = regex_and_params(ledger)
    paths = logic_paths(ledger)
    return {"ledger": ledger, "tool": tools(ledger), "ssot": ssot(ledger), "regex": rx, "param": pm,
            "index": indices(ledger), "test": tests(ledger), "paths": paths, "backup_adds": backup_plan(paths),
            "versions": path_versions(paths)}


def build(apply: bool = False) -> dict:
    cat = catalog()
    new_codes = len(cat["ledger"].get("codes", {})) - len((load_ledger().get("codes") or {}))
    if apply:
        led = cat["ledger"]
        led["rule"] = "同一鍵永遠同一號;新鍵取下一號;舊號永不改、永不刪(只增不減)"
        path = _newest(HERE, "VIA_Numbering_Ledger_v*.json") or LEDGER_NEW
        path.write_text(json.dumps(led, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="")
        if cat["backup_adds"]:
            bp = _newest(HERE, "VIA_LogicPath_Backup_v*.json") or BACKUP_NEW
            book = _json(bp) or {"schema": "VIA.LogicPathBackup.v1", "append_only": True, "rows": []}
            book["rule"] = "路徑內容(節點序)一變就追加一列新版號;舊列永不刪改;時間含時區"
            book["rows"].extend(cat["backup_adds"])
            bp.write_text(json.dumps(book, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="")
    counts = {k: len(cat[k]) for k in ("tool", "ssot", "regex", "param", "index", "test", "paths")}
    lamps = {}
    for k in ("tool", "ssot", "regex", "param", "index", "test"):
        for r in cat[k]:
            lamps[r["lamp"]] = lamps.get(r["lamp"], 0) + 1
    return {"via": "vcgc", "door": ENGINE, "apply": apply, "counts": counts, "lamps": lamps, "new_codes": max(0, new_codes),
            "backup_adds": len(cat["backup_adds"])}


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False))
        return 2
    print(json.dumps(build("--apply" in args), ensure_ascii=False, indent=1))
    return 0


def selftest() -> int:
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' · ' + note) if note else ''}")

    keep = os.environ.pop("VIA_FROM_VCGC", None)
    chk("① 沒從 VCGC 進就拒", main(["--apply"]) == 2)
    if keep is not None:
        os.environ["VIA_FROM_VCGC"] = keep
    led = {"codes": {"TOOL|a": "TL-0001"}, "next": {"TOOL": 2}}
    a, b, c = number(led, "TOOL", "a"), number(led, "TOOL", "b"), number(led, "TOOL", "b")
    chk("② 編號只增:舊鍵同號、新鍵取下一號、重問同號", a == "TL-0001" and b == "TL-0002" and c == "TL-0002")
    chk("③ 鎖定時間是日期 + 時間 + 時區", bool(re.match(r"\d{4}-\d\d-\d\d \d\d:\d\d:\d\d [+-]\d{4}$",
                                               locked_at(HERE / "VIA_EngineVersion_Register_v0100.json"))))
    cat = catalog()
    chk("④ 七類都有列(工具 · SSOT · regex · 參數 · 指數 · 測試 · 路徑)",
        all(cat[k] for k in ("tool", "ssot", "regex", "param", "index", "test", "paths")),
        " · ".join(f"{k} {len(cat[k])}" for k in ("tool", "ssot", "regex", "param", "index", "test", "paths")))
    chk("⑤ 燈只有紅黃綠三種", {r["lamp"] for k in ("tool", "ssot", "regex", "param", "index", "test") for r in cat[k]} <= set(LAMP))
    codes = [r["code"] for k in ("tool", "ssot", "regex", "param", "index", "test") for r in cat[k]] + [p["code"] for p in cat["paths"]]
    chk("⑥ 每一列都有編號,而且不重號", len(codes) == len(set(codes)) and all(codes), f"{len(codes)} 號")
    ok = all(results)
    print(f"  {ENGINE} selftest {sum(results)}/{len(results)} {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
