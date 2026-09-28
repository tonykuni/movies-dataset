#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL230_ToolCoverageProbe v0100 — 兩支工具的註冊 · 覆蓋率 · 舊副本 全景探針(只讀)

操作員 2026-09-28:「重申加速器與網路工具都有新版本號請將它們註冊 · 加速器導入所有 py 檔 ps 檔 · 網路工具導入 vdf 檔案全部 ·
用全景式分析 ast 探針檢查他們功能覆蓋率要達 100% · 上面少了網路工具版本號你查一下 · 舊的請刪除」。

本支**不自己立尺**(L05),每一格都問正主:
  Ⓐ 工具註冊   → CGC_MDL225_VersionPanorama 尾版 check()(v0101 起載入器照尾版、冊要有尾版、鎖 sha、PS7 配對)
  Ⓑ 上游包比對 → 上傳的 zip(--zip)或樹內 intake 收件夾:同不同一份、有沒有 TA-Lib(L50:有就不採用)
  Ⓒ 覆蓋率     → CGC_MDL183 CeleritasPolicyGate 尾版 scan()(PY 加速器橋 · PS 模板章)
                 + VDF_SystemManager 尾版 read_bridge()(VDF 尾版 加速器橋 / 網路橋)+ CGC_MDL190 TALibLock scan()
  Ⓓ 舊副本     → 樹上無版號的 VeritasCeleritas*.py / VeritasAegisNexus*.py(intake 收件不算):
                 同一份群 · 角色 · 誰還在用(按名匯入 · 檔名引用 · 路徑引用 · 凍結 no_delete · VDF 工具副本位)。
                 **一個引用都沒有才標「可刪」並印出 git rm 指令;本支永不刪(L10 刪除是操作員的手)。**
輸出:VIA_Reports/toolprobe/TOOLPROBE_latest.json(+ .txt;rich 在就印 rich 表)。零網路 · 零寫庫 · 不安裝。

用法:
  python CGC_MDL230_ToolCoverageProbe_v0100.py probe [--zip <VeritasCeleritas-v*.zip>] [--plain] [--width N] [--json]
  python CGC_MDL230_ToolCoverageProbe_v0100.py --selftest
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
import io
import json
import os
import re
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
SUPP = VIA / "supportive modules"
OUT = VIA / "VIA_Reports" / "toolprobe"
ENGINE_TAG = "CGC_MDL230_ToolCoverageProbe v" + Path(__file__).stem.rsplit("_v", 1)[-1]
CONTAINERS = ("supportive modules", "new modules engines")
NOT_LIVE = ("references", "VIA_Reports", ".git", "__pycache__", "node_modules", "_superseded", "SCOPE_COPY")
CODE_EXT = (".py", ".ps1", ".psm1", ".cmd", ".bat")
COPY_NAME = re.compile(r"^(VeritasCeleritas|VeritasAegisNexus)(__[A-Za-z0-9]+)?\.py$")
IMPORT_RE = re.compile(r"^\s*(?:import|from)\s+(VeritasAegisNexus|VeritasCeleritas)\b"
                       r"|import_module\(\s*['\"](VeritasAegisNexus|VeritasCeleritas)['\"]", re.M)
UPSTREAM_FILES = ("engine/VeritasCeleritas.py", "ps7/VeritasCeleritas.PS7.ps1", "ps7/VeritasCeleritas.PS7.Template.ps1")
SEV = {"RED": 0, "ABSENT": 1, "NODATA": 2, "AMBER": 3, "HOLD": 4, "INFO": 5, "GREEN": 6}


def _vnum(p: Path) -> int:
    m = re.search(r"[_-]v(\d+)$", p.stem)
    return int(m.group(1)) if m else -1


def _tail(folder: Path, stem: str) -> Path | None:
    hits = [p for p in folder.glob(stem + "_v*.py") if _vnum(p) >= 0]
    return max(hits, key=_vnum) if hits else None


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _ruler(folder: Path, stem: str):
    p = _tail(folder, stem)
    if p is None:
        return None, f"{stem} 尾版不在"
    try:
        return _load(p, "mdl230_" + p.stem), p.name
    except Exception as e:  # 尺壞 = 照實 NODATA,不自己補一把尺
        return None, f"{p.name} 載不動:{type(e).__name__}: {e}"


def _ruler_with(folder: Path, stem: str, attr: str):
    """尾版沒轉接該函式就往回找到**具體實作**那一版(同一把尺,不另立;照實標出是哪一版)。"""
    hits = sorted([p for p in folder.glob(stem + "_v*.py") if _vnum(p) >= 0], key=_vnum, reverse=True)
    if not hits:
        return None, f"{stem} 尾版不在"
    for p in hits:
        if re.search(r"^def " + re.escape(attr) + r"\(", p.read_text(encoding="utf-8", errors="ignore"), re.M):
            try:
                mod = _load(p, "mdl230_" + p.stem)
            except Exception as e:
                return None, f"{p.name} 載不動:{type(e).__name__}: {e}"
            note = p.name if p == hits[0] else f"{p.name}(尾版 {hits[0].name} 沒轉接 {attr},往回到具體實作)"
            return mod, note
    return None, f"{stem} 各版都沒有 {attr}"


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _worst(states) -> str:
    states = [s for s in states if s]
    return min(states, key=lambda s: SEV.get(s, 5)) if states else "NODATA"


def _rel(p: Path, root: Path = VIA) -> str:
    return str(p.relative_to(root)).replace("\\", "/")


# ---------------------------------------------------------------- Ⓐ 工具註冊(問 CGC_MDL225 尾版)
def versions() -> dict:
    mod, name = _ruler(HERE, "CGC_MDL225_VersionPanorama")
    if mod is None:
        return {"state": "NODATA", "ruler": name, "rows": [], "resolved": {}}
    card = mod.check()
    rows = [[r["lamp"], r["family"], r["role"], r["file"], r["code"]] for r in card["rows"]]
    return {"state": "GREEN" if card.get("lock_success") else "RED", "ruler": name, "rows": rows,
            "resolved": card.get("resolved") or {}, "missing": card.get("missing") or []}


# ---------------------------------------------------------------- Ⓑ 上游包比對
def _upstream_texts(zip_path: Path | None) -> tuple:
    """回 (來源說明, {相對名: bytes})。給 zip 就讀 zip;沒給就讀樹內 intake 最後一個收件夾。"""
    got = {}
    if zip_path:
        with zipfile.ZipFile(zip_path) as z:
            for n in z.namelist():
                for want in UPSTREAM_FILES:
                    if n.replace("\\", "/").endswith("/" + want) or n == want:
                        got[want] = z.read(n)
        return f"zip {Path(zip_path).name}", got
    cands = sorted((SUPP / "references" / "intake").glob("VIA_Celeritas_v*"))
    if not cands:
        return "intake 收件夾不在", got
    for want in UPSTREAM_FILES:
        hit = next(iter(sorted(cands[-1].glob("*/" + want))), None)
        if hit:
            got[want] = hit.read_bytes()
    sub = next((d.name for d in sorted(cands[-1].iterdir()) if d.is_dir()), "")
    return f"intake {cands[-1].name}/{sub}", got


def upstream(zip_path: Path | None = None) -> dict:
    src, got = _upstream_texts(zip_path)
    intake = {}
    for d in sorted((SUPP / "references" / "intake").glob("VIA_Celeritas_v*")):
        for want in UPSTREAM_FILES:
            for p in d.glob("*/" + want):
                intake.setdefault(_sha(p.read_bytes()), d.name)
    eng_tail = None
    mod, _ = _ruler(HERE, "CGC_MDL225_VersionPanorama")
    if mod is not None and hasattr(mod, "engine_tail"):
        eng_tail = mod.engine_tail()
    tree = {"engine/VeritasCeleritas.py": eng_tail,
            "ps7/VeritasCeleritas.PS7.ps1": SUPP / "ps7" / "VeritasCeleritas.PS7.ps1",
            "ps7/VeritasCeleritas.PS7.Template.ps1": SUPP / "ps7" / "VeritasCeleritas.PS7.Template.ps1"}
    rows, talib_hits, same_all = [], 0, bool(got)
    for want in UPSTREAM_FILES:
        b = got.get(want)
        if b is None:
            rows.append(["ABSENT", want, "—", "—", "—", "上游包沒有這支"])
            same_all = False
            continue
        s = _sha(b)
        text = b.decode("utf-8", errors="ignore")
        tl = len(re.findall(r"talib", text, re.I))
        talib_hits += tl if want.endswith(".py") else 0
        seen = intake.get(s)
        same_all = same_all and bool(seen)
        tp = tree.get(want)
        tree_same = bool(tp and tp.is_file() and _sha(tp.read_bytes()) == s)
        ver = (re.findall(r"__version__\s*=\s*['\"]([^'\"]+)['\"]", text) or ["—"])[-1] if want.endswith(".py") else "—"
        rows.append(["INFO" if seen else "AMBER", want, s[:12], f"已收件 {seen}" if seen else "新的(未收件)",
                     ("同樹內 " + tp.name) if tree_same else ("≠ 樹內 " + (tp.name if tp else "—")),
                     f"talib 字樣 {tl} · 版 {ver}"])
    pkg = re.search(r"v\d+\.\d+\.\d+", src)
    verdict = ("不採用:上游引擎含 TA-Lib(L50 第一條);樹內合規衍生 " + (eng_tail.name if eng_tail else "—") + " 已註冊"
               if talib_hits else "上游引擎零 TA-Lib:要換版仍走 L04 新版號檔 + 登錄冊(操作員裁定)")
    return {"state": "GREEN" if (talib_hits and eng_tail) or (not talib_hits and same_all) else "AMBER",
            "source": src, "package": pkg.group(0) if pkg else "—", "same_as_intake": same_all,
            "talib_hits": talib_hits, "verdict": verdict,
            "note": ("已收件同位元,不重收" if same_all else "有新檔:照 L04 收進 intake 新批號(不覆寫正本)"), "rows": rows}


# ---------------------------------------------------------------- Ⓒ 覆蓋率(問 CGC_MDL183 · VDF_SystemManager · CGC_MDL190)
def _ps_family(p: Path) -> tuple:
    m = re.match(r"^(.*?)[-_]v(\d+)$", p.stem)
    return (str(p.parent), m.group(1) if m else p.stem), (int(m.group(2)) if m else -1)


def _param_first(text: str) -> bool:
    for ln in text.splitlines():
        s = ln.strip()
        if not s or s.startswith("#"):
            continue
        return bool(re.match(r"(?i)^(param\s*\(|\[CmdletBinding)", s))
    return False


def ps_debt_split(debt: list, root: Path = VIA) -> dict:
    fam = {}
    for rp in debt:
        p = root / rp
        key, n = _ps_family(p)
        fam.setdefault(key, []).append((n, rp))
    tails = {max(v)[1] for v in fam.values()}
    top_param, unreadable = 0, []
    for rp in tails:
        p = root / rp
        try:
            top_param += _param_first(p.read_text(encoding="utf-8-sig", errors="ignore"))
        except OSError as e:
            unreadable.append(f"{rp}: {type(e).__name__}")   # 讀不動照實列(L16 缺件 ≠ 壞掉)
    return {"tails": len(tails), "history": len(debt) - len(tails), "tails_param_first": top_param, "unreadable": unreadable}


def coverage() -> dict:
    rows, notes = [], {}
    gate, gname = _ruler(HERE, "CGC_MDL183_CeleritasPolicyGate")
    g = None
    if gate is not None:
        try:
            g = gate.scan()
        except Exception as e:
            gname += f" · scan 失敗 {type(e).__name__}: {e}"
    if g and g.get("state") != "NODATA":
        py, ps = g["py"], g["ps"]
        elig = py["n"] - py["exempt"] - py["readonly"]
        rows.append(["GREEN" if not py["missing"] else "RED", "PY 加速器橋(L103① · L102)", gname, py["n"], py["bridged"],
                     f"凍結豁免 {py['exempt']} · 正典唯讀 {py['readonly']}", len(py["missing"]),
                     f"{py['bridged'] * 100 / max(elig, 1):.1f}%"])
        non_debt = ps["n"] - ps["debt"] - ps["self"]
        rows.append(["GREEN" if not ps["new_missing"] else "RED", "PS 模板章 · 基線外(新產出)", gname, non_debt, ps["joined"],
                     f"自指豁免 {ps['self']}", len(ps["new_missing"]), f"{ps['joined'] * 100 / max(non_debt, 1):.1f}%"])
        base = gate.baseline() if hasattr(gate, "baseline") else {}
        split = ps_debt_split(list((base.get("ps1_debt") or {}).get("files") or []))
        rows.append(["AMBER" if ps["debt"] else "GREEN", "PS 模板章 · 既有債(L70 操作員的手)", gname, ps["debt"], 0,
                     f"尾版 {split['tails']}(param 在頂 {split['tails_param_first']})· 版史 {split['history']}", ps["debt"], "0.0%"])
        rows.append(["AMBER" if ps["debt"] else "GREEN", "PS 模板章 · 全樹", gname, ps["n"], ps["joined"], "—", ps["debt"],
                     f"{ps['joined'] * 100 / max(ps['n'], 1):.1f}%"])
        notes["ps_split"] = split
        notes["py_missing"] = py["missing"][:20]
        notes["ps_new_missing"] = ps["new_missing"][:20]
    else:
        rows.append(["NODATA", "PY/PS(Celeritas 閘)", gname, "—", "—", (g or {}).get("why", "—"), "—", "—"])
    vdf_dir = VIA / "functional modules" / "VDF"
    vm, vname = _ruler_with(vdf_dir, "VDF_SystemManager", "read_bridge")
    br = tl = None
    if vm is not None:
        try:
            br, tl = vm.read_bridge(), vm.read_tool()
        except Exception as e:
            vname += f" · 讀失敗 {type(e).__name__}: {e}"
    if br:
        live = br["tails"] - br["excluded"]
        rows.append(["GREEN" if not br["accel"]["missing"] else "RED", "VDF 尾版 · 加速器橋", vname, br["tails"], br["accel"]["has"],
                     f"排除 {br['excluded']}", len(br["accel"]["missing"]), f"{br['accel']['has'] * 100 / max(live, 1):.1f}%"])
        rows.append(["GREEN" if not br["net"]["missing_any"] else ("RED" if br["net"]["callers_missing"] else "AMBER"),
                     "VDF 尾版 · 網路橋(L103② · L09)", vname, br["tails"], br["net"]["has"],
                     f"真擷取 {br['net']['callers']}(缺 {len(br['net']['callers_missing'])})", len(br["net"]["missing_any"]),
                     f"{br['net']['has'] * 100 / max(live, 1):.1f}%"])
    else:
        rows.append(["NODATA", "VDF 尾版橋", vname, "—", "—", "—", "—", "—"])
    ta, tname = _ruler(HERE, "CGC_MDL190_TALibLock")
    t = None
    if ta is not None:
        try:
            t = ta.scan()
        except Exception as e:
            tname += f" · scan 失敗 {type(e).__name__}"
    if t:
        rows.append([t.get("state", "NODATA"), "TA-Lib 匯入(L50 第一條)", tname, "全樹活檔", "—", "—", t.get("imports", 0),
                     "零匯入" if not t.get("imports") else "有匯入"])
    else:
        rows.append(["NODATA", "TA-Lib 匯入(L50)", tname, "—", "—", "—", "—", "—"])
    state = _worst([r[0] for r in rows])
    return {"state": state, "rows": rows, "notes": notes, "tool": tl}


# ---------------------------------------------------------------- Ⓓ 舊副本(誰還在用;沒人用才可刪 · 本支永不刪)
def _live(rp: str) -> bool:
    return not any(seg in NOT_LIVE for seg in rp.split("/"))


def find_copies(root: Path = VIA) -> list:
    out = []
    for c in CONTAINERS:
        base = root / c
        if not base.is_dir():
            continue
        for p in base.rglob("Veritas*.py"):
            rp = _rel(p, root)
            if COPY_NAME.match(p.name) and "/references/" not in "/" + rp and "__pycache__" not in rp:
                out.append(p)
    return sorted(out)


def _pkg_root(rp: str) -> str:
    parts = rp.split("/")
    if len(parts) <= 2:          # 直接在容器根:由加速器橋把容器插進 sys.path,按名匯入全樹共用
        return ""
    return "/".join(parts[:2])


def corpus_refs(copies: list, root: Path = VIA) -> dict:
    """一次走完活檔(程式類),回每支副本的引用清單。只看文字,不執行任何檔。"""
    info = {}
    for p in copies:
        rp = _rel(p, root)
        parent = rp.rsplit("/", 1)[0]
        pkg = _pkg_root(rp)
        inner = parent.split("/", 1)[1] if "/" in parent else ""
        needles = [n for n in {inner, inner.replace("/", "\\")} if inner and inner not in ("network", "accelerator")]
        info[rp] = {"mod": p.stem.split("__")[0], "name": p.name, "parent": parent, "pkg": pkg, "needles": needles,
                    "by_name": [], "by_file": [], "by_path": []}
    importers, unreadable = [], []
    for c in CONTAINERS + ("functional modules",):
        base = root / c
        if not base.is_dir():
            continue
        for f in base.rglob("*"):
            if f.suffix.lower() not in CODE_EXT or not f.is_file():
                continue
            rf = _rel(f, root)
            if not _live(rf):
                continue
            try:
                if f.stat().st_size > 4_000_000:
                    continue
                data = f.read_bytes()
            except OSError as e:
                unreadable.append(f"{rf}: {type(e).__name__}")   # 讀不動的不假裝沒引用:照實列進 _unreadable
                continue
            if b"Veritas" not in data and not any(n.encode() in data for i in info.values() for n in i["needles"]):
                continue
            text = data.decode("utf-8", errors="ignore")
            mods = {m.group(1) or m.group(2) for m in IMPORT_RE.finditer(text)}
            if mods:
                importers.append((rf, mods))
            for rp, i in info.items():
                if rf == rp:
                    continue
                if i["needles"] and any(n in text for n in i["needles"]):
                    i["by_path"].append(rf)
                same = rf.rsplit("/", 1)[0] == i["parent"] or (i["pkg"] and rf.startswith(i["pkg"] + "/"))
                if same and (f'"{i["name"]}"' in text or f"'{i['name']}'" in text):
                    i["by_file"].append(rf)           # 同夾 / 同套件以檔名載入(with_name · 必備清單 · 啟動器)
    for rp, i in info.items():
        for rf, mods in importers:
            if i["mod"] not in mods or rf == rp:  # 自己匯入自己不算有人在用
                continue
            if i["pkg"] == "" and not any(rf.startswith(x["pkg"] + "/") for x in info.values() if x["pkg"] and x["mod"] == i["mod"]):
                i["by_name"].append(rf)           # 容器根副本:沒有自家副本的按名匯入都落到它
            elif i["pkg"] and rf.startswith(i["pkg"] + "/"):
                i["by_name"].append(rf)           # 套件內按名匯入
    for i in info.values():
        i["unreadable"] = unreadable
    return info


def legacy(root: Path = VIA, tool: dict | None = None) -> dict:
    copies = find_copies(root)
    refs = corpus_refs(copies, root)
    shas = {rp: _sha((root / rp).read_bytes()) for rp in refs}
    groups = {}
    for rp, s in shas.items():
        groups.setdefault(s, []).append(rp)
    gid = {s: chr(ord("A") + k) for k, s in enumerate(sorted(groups, key=lambda s: (-len(groups[s]), s)))}
    tool_dirs = set()
    for t in ((tool or {}).get("tools") or {}).values():
        for c in t.get("copies") or []:
            tool_dirs.add(c["path"])
    net_tail = _tail(root / "supportive modules" / "network", "VeritasAegisNexus")
    net_body = ""
    if net_tail:
        m = re.search(r"with_name\(\s*['\"](VeritasAegisNexus\.py)['\"]", net_tail.read_text(encoding="utf-8", errors="ignore"))
        net_body = _rel(net_tail.with_name(m.group(1)), root) if m else ""
    rows, cmds, keep = [], [], 0
    for rp in sorted(refs):
        i = refs[rp]
        why = []
        if rp == "supportive modules/accelerator/VeritasCeleritas.py":
            why.append("正典位(轉 VeritasCeleritas 尾版;不可動律)")
        if rp == net_body:
            why.append(f"{net_tail.name} 的本體(with_name 載入)")
        lock = root / (rp + ".freeze.lock.json")
        if lock.is_file():
            try:
                if (json.loads(lock.read_text(encoding="utf-8")).get("policy") or {}).get("no_delete"):
                    why.append("凍結鎖 no_delete")
            except Exception:
                why.append("凍結鎖在(讀不動,當作不可刪)")
        if rp in tool_dirs:
            why.append("VDF 工具副本位(read_tool 量同一份)")
        if i["by_name"]:
            why.append(f"按名匯入 {len(i['by_name'])} 支" + ("(加速器橋把容器插進 sys.path)" if not i["pkg"] else "(套件內)"))
        if i["by_file"]:
            why.append(f"同夾/同套件檔名引用 {len(i['by_file'])} 支")
        if i["by_path"]:
            why.append(f"路徑引用 {len(i['by_path'])} 支")
        if i.get("unreadable") and not why:
            why.append(f"有 {len(i['unreadable'])} 支活檔讀不動,引用數不完整 → 不判可刪")
        deletable = not why
        state = "AMBER" if deletable else "HOLD"
        if deletable:
            cmds.append(f'git rm -- "{rp}"')
        else:
            keep += 1
        rows.append([state, rp, shas[rp][:12], gid[shas[rp]], "可刪(沒有任何引用)" if deletable else "保留", " · ".join(why) or "—",
                     (i["by_name"] + i["by_file"] + i["by_path"])[:1][0] if (i["by_name"] or i["by_file"] or i["by_path"]) else "—"])
    return {"state": "AMBER" if cmds else "HOLD", "copies": len(rows), "keep": keep, "deletable": len(cmds),
            "retire_cmds": cmds, "rows": rows,
            "rule": "一個引用都沒有才可刪;刪除是操作員的手(L10),本支只印 git rm,永不刪。有引用的先遷呼叫者到版號尾版再刪。",
            "detail": {rp: {k: v[:30] for k, v in i.items() if k in ("by_name", "by_file", "by_path")} for rp, i in refs.items()}}


# ---------------------------------------------------------------- 彙總 · 矩陣 · 輸出
def probe(zip_path: Path | None = None, root: Path = VIA) -> dict:
    v = versions()
    u = upstream(zip_path)
    c = coverage()
    lg = legacy(root, c.get("tool"))
    res = v.get("resolved") or {}
    kpi = [
        ["Ⓐ 工具註冊", v["state"], f"加速器 {res.get('accelerator', '—')} ← {res.get('accelerator_loader', '—')} · "
                                   f"網路 {res.get('network', '—')} ← {res.get('network_loader', '—')} · 尺 {v.get('ruler')}"],
        ["Ⓑ 上游包", u["state"], f"{u['source']} {u['package']} · {u['verdict']} · {u['note']}"],
        ["Ⓒ 覆蓋率", c["state"], " · ".join(f"{r[1]} {r[7]}" for r in c["rows"])],
        ["Ⓓ 舊副本", lg["state"], f"{lg['copies']} 支 · 保留 {lg['keep']} · 可刪 {lg['deletable']}(只印指令,L10)"],
    ]
    todo = []
    for r in v.get("rows") or []:
        if r[0] != "GREEN":
            todo.append([r[0], "註冊", f"{r[1]} {r[2]} {r[3]}", "版號登錄冊 / 鎖 / PS7 配對不符", "照 L04 登錄尾版(冊只增不改)"])
    if u["state"] != "GREEN":
        todo.append([u["state"], "上游包", u["source"], u["verdict"], u["note"]])
    for r in c["rows"]:
        if r[0] == "RED":
            todo.append(["RED", "覆蓋", r[1], f"缺 {r[6]}", "via-bridge-sweep --subsystems --apply(乾跑先看)"])
        elif r[0] == "AMBER" and "既有債" in r[1]:
            todo.append(["AMBER", "覆蓋", r[1], f"{r[3]} 支舊 .ps1 沒模板章;{r[5]}",
                         "L70:操作員批准後才接;param 在頂者模板章要插在 param() 之後,先在工作站用 PS 剖析器乾跑"])
        elif r[0] not in ("GREEN", "AMBER"):
            todo.append([r[0], "覆蓋", r[1], str(r[5]), "單跑該尺 --selftest 看根因"])
    for r in lg["rows"]:
        if r[4] != "保留":
            todo.append(["AMBER", "舊副本", r[1], "沒有任何引用", f'操作員的手:git rm -- "{r[1]}"'])
    if lg["keep"]:
        todo.append(["HOLD", "舊副本", f"{lg['keep']} 支保留", "仍有活檔在用(見 Ⓓ 理由欄)", "先把呼叫者遷到版號尾版(L04 新版號),引用歸零才可刪"])
    todo.sort(key=lambda r: SEV.get(str(r[0]), 5))
    verdict = _worst([k[1] for k in kpi if k[1] not in ("HOLD", "INFO")])
    sections = [
        ("Ⓐ 工具註冊(CGC_MDL225 尾版:冊 · 載入器尾版 · 鎖 sha · PS7 配對)", ["燈", "家族", "角色", "檔", "碼/版"], v.get("rows") or [], 0),
        (f"Ⓑ 上游包比對({u['source']} {u['package']})· {u['verdict']}", ["燈", "檔", "sha12", "收件", "與樹內", "說明"], u["rows"], 0),
        ("Ⓒ 功能覆蓋率(正主各自量;本支不另判)", ["燈", "面", "尺", "分母", "已接", "不計", "缺", "覆蓋"], c["rows"], 0),
        (f"Ⓓ 舊副本 {lg['copies']} 支(保留 {lg['keep']} · 可刪 {lg['deletable']};只印不刪 L10)",
         ["燈", "檔", "sha12", "同份群", "處置", "理由", "例:引用者"], lg["rows"], 0),
        (f"Ⓔ 工具待辦({len(todo)} 列)", ["燈", "來源", "項目", "說明", "下一步"], todo, 0),
    ]
    cell = lambda x: "—" if x is None or x == "" else (f"{x:,}" if isinstance(x, int) else str(x).replace("\n", " "))
    sections = [(t, cols, [[cell(x) for x in r] for r in rows], s) for t, cols, rows, s in sections]
    return {"engine": ENGINE_TAG, "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "ts_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"), "verdict": verdict,
            "kpi": kpi, "todo": todo, "sections": sections, "resolved": res,
            "upstream": {k: u[k] for k in ("source", "package", "same_as_intake", "talib_hits", "verdict", "note")},
            "coverage_notes": c.get("notes"), "retire_cmds": lg["retire_cmds"], "legacy_detail": lg["detail"],
            "rules": ["L05 不立第二把尺:每格問正主", "L10 刪除是操作員的手:只印 git rm", "L50 TA-Lib 第一條:上游含就不採用",
                      "L70 動 .ps1 要操作員批准", "L04 換版 = 新版號檔 + 登錄冊只增"]}


def _plain(rep: dict, width: int) -> str:
    mod, _ = _ruler(HERE, "CGC_MDL229_SweepReport")
    title = f"VIA 工具註冊與覆蓋全景 · {rep['verdict']} · {rep['ts']}"
    if mod is not None and hasattr(mod, "plain"):
        return mod.plain(rep["sections"], width, title)
    return title + "\n" + "\n".join(f"━━ {t} ━━\n" + "\n".join("  " + " │ ".join(r) for r in rows) for t, _c, rows, _s in rep["sections"])


def write(rep: dict, out: Path = OUT, width: int = 160, use_plain: bool = False, echo: bool = True) -> dict:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    txt = _plain(rep, width)
    engine = "plain"
    if not use_plain:
        try:
            from rich import box
            from rich.console import Console
            from rich.table import Table
            from rich.text import Text
            style = {"GREEN": "green", "AMBER": "yellow", "HOLD": "cyan", "INFO": "dim", "NODATA": "dark_orange", "RED": "bold red", "ABSENT": "red"}
            con = Console(width=max(100, int(width)), force_terminal=echo, legacy_windows=False,
                          file=(sys.stdout if echo else io.StringIO()), soft_wrap=False)
            con.rule(f"[bold]VIA 工具註冊與覆蓋全景 · {rep['verdict']} · {rep['ts']}")
            for t, cols, rows, st in rep["sections"]:
                tb = Table(title=t, title_justify="left", title_style="bold cyan", box=box.SIMPLE_HEAVY, header_style="bold", pad_edge=False)
                for c in cols:
                    tb.add_column(c, overflow="fold")
                for r in rows or [["(無)"] + [""] * (len(cols) - 1)]:
                    cells = list(r) + [""] * (len(cols) - len(r))
                    if st is not None and style.get(cells[st]):
                        cells[st] = Text(cells[st], style=style[cells[st]])
                    tb.add_row(*cells)
                con.print(tb)
            engine = "rich"
        except ImportError:
            engine = "plain"
    if engine == "plain" and echo:
        print(txt)
    (out / "TOOLPROBE_latest.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "TOOLPROBE_latest.txt").write_text(txt, encoding="utf-8")
    return {"engine": engine, "json": str(out / "TOOLPROBE_latest.json"), "txt": str(out / "TOOLPROBE_latest.txt")}


# ---------------------------------------------------------------- 自測(真樹只讀;寫只落暫存夾)
def selftest() -> int:
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' · ' + note) if note else ''}")

    watch = [HERE / "VIA_EngineVersion_Register_v0100.json", HERE / "VIA_ToolVersion_Lock_v0100.json",
             SUPP / "network" / "VeritasAegisNexus.py", SUPP / "VeritasAegisNexus.py"]
    before = {p: _sha(p.read_bytes()) for p in watch if p.is_file()}
    v = versions()
    chk("① 工具註冊問 CGC_MDL225 尾版且全綠(網路載入器尾版有版號)", v["state"] == "GREEN" and v["resolved"].get("network_loader"),
        f"{v.get('ruler')} · {v['resolved'].get('network')} ← {v['resolved'].get('network_loader')}")
    u = upstream()
    chk("② 上游包(intake)含 TA-Lib → 不採用,樹內合規衍生已註冊", u["talib_hits"] > 0 and u["verdict"].startswith("不採用"), u["verdict"])
    with tempfile.TemporaryDirectory() as td:
        zp = Path(td) / "VeritasCeleritas-v1.14.0_test.zip"
        src = sorted((SUPP / "references" / "intake").glob("VIA_Celeritas_v*"))
        with zipfile.ZipFile(zp, "w") as z:
            for want in UPSTREAM_FILES:
                for p in src[-1].glob("*/" + want) if src else []:
                    z.write(p, "VeritasCeleritas-v1.14.0/" + want)
        uz = upstream(zp)
        chk("③ 給 zip:認得同位元已收件、版號從包名讀", uz["same_as_intake"] and uz["package"] == "v1.14.0", f"{uz['source']} · {uz['note']}")
    c = coverage()
    names = {r[1]: r for r in c["rows"]}
    py = next((r for k, r in names.items() if k.startswith("PY")), None)
    net = next((r for k, r in names.items() if "網路橋" in k), None)
    debt = next((r for k, r in names.items() if "既有債" in k), None)
    chk("④ 覆蓋率問正主:PY 缺 0 · VDF 網路橋有列 · PS 既有債照實 AMBER(L70)",
        py and py[6] == 0 and net and debt and (debt[0] == "AMBER") == (debt[3] > 0),
        " · ".join(f"{r[1]} {r[7]}" for r in c["rows"]))
    lg = legacy(VIA, c.get("tool"))
    by = {r[1]: r for r in lg["rows"]}
    body = by.get("supportive modules/network/VeritasAegisNexus.py")
    root_copy = by.get("supportive modules/VeritasAegisNexus.py")
    chk("⑤ 舊副本:網路本體與容器根副本都判保留(有引用)", body and body[4] == "保留" and "本體" in body[5] and root_copy and root_copy[4] == "保留",
        f"{(body or ['', '', '', '', '', '—'])[5]} | {(root_copy or ['', '', '', '', '', '—'])[5]}")
    with tempfile.TemporaryDirectory() as td:
        r = Path(td)
        (r / "new modules engines" / "OldPkg" / "lib").mkdir(parents=True)
        (r / "new modules engines" / "UsedPkg").mkdir(parents=True)
        orphan = r / "new modules engines" / "OldPkg" / "lib" / "VeritasAegisNexus.py"
        orphan.write_text("X = 1\n", encoding="utf-8")
        used = r / "new modules engines" / "UsedPkg" / "VeritasCeleritas.py"
        used.write_text("Y = 1\n", encoding="utf-8")
        (r / "new modules engines" / "UsedPkg" / "run.py").write_text("import VeritasCeleritas\n", encoding="utf-8")
        (r / "new modules engines" / "RefPkg" / "lib").mkdir(parents=True)
        (r / "new modules engines" / "RefPkg" / "lib" / "VeritasCeleritas.py").write_text("from VeritasCeleritas import x\n", encoding="utf-8")
        (r / "new modules engines" / "RefPkg" / "run.ps1").write_text("$need = @('VeritasCeleritas.py')\n", encoding="utf-8")
        s = legacy(r)
        rows = {x[1]: x for x in s["rows"]}
        chk("⑥ 沙盒:沒人引用 → 可刪且只印 git rm;按名匯入 / 同套件檔名引用 → 保留;自己匯入自己不算;檔案一支都沒刪",
            rows["new modules engines/OldPkg/lib/VeritasAegisNexus.py"][4].startswith("可刪")
            and rows["new modules engines/UsedPkg/VeritasCeleritas.py"][4] == "保留"
            and rows["new modules engines/RefPkg/lib/VeritasCeleritas.py"][4] == "保留"
            and s["retire_cmds"] == ['git rm -- "new modules engines/OldPkg/lib/VeritasAegisNexus.py"'] and orphan.is_file() and used.is_file(),
            f"{s['retire_cmds']}")
    with tempfile.TemporaryDirectory() as td:
        rep = probe()
        w = write(rep, Path(td), use_plain=True, echo=False)
        j = json.loads(Path(w["json"]).read_text(encoding="utf-8"))
        chk("⑦ 五張矩陣 + KPI 四列 + JSON 落指定夾", len(j["sections"]) == 5 and len(j["kpi"]) == 4 and Path(w["txt"]).is_file(),
            f"總判 {rep['verdict']} · 待辦 {len(rep['todo'])}")
    after = {p: _sha(p.read_bytes()) for p in watch if p.is_file()}
    chk("⑧ 零寫入:登錄冊 · 鎖 · 兩支網路副本位元不變", before == after)
    keep = os.environ.pop("VIA_FROM_VCGC", None)
    denied = main(["probe"]) == 2
    if keep is not None:
        os.environ["VIA_FROM_VCGC"] = keep
    chk("⑨ 沒從 VCGC 進(VIA_FROM_VCGC)就拒跑", denied)
    ok = all(results)
    print(f"  {ENGINE_TAG} selftest {sum(results)}/{len(results)} {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a:
        return selftest()
    if not a or a[0] != "probe":
        print(__doc__)
        return 0
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc(PSGATE-1:先從 VCGC 跑過流程)"}, ensure_ascii=False))
        return 2
    zp = Path(a[a.index("--zip") + 1]) if "--zip" in a and a.index("--zip") + 1 < len(a) else None
    if zp and not zp.is_file():
        print(f"[ToolProbe] zip 不在:{zp}(照樹內 intake 比對)")
        zp = None
    width = int(a[a.index("--width") + 1]) if "--width" in a and a.index("--width") + 1 < len(a) else 160
    rep = probe(zp)
    w = write(rep, width=width, use_plain="--plain" in a, echo="--json" not in a)
    if "--json" in a:
        print(json.dumps({k: rep[k] for k in ("verdict", "kpi", "resolved", "upstream", "retire_cmds")}, ensure_ascii=False, indent=1))
    print(f"[ToolProbe] {w['engine']} · 總判 {rep['verdict']} · 待辦 {len(rep['todo'])} · 可刪 {len(rep['retire_cmds'])} · JSON {w['json']}")
    return 0 if rep["verdict"] != "RED" else 1


if __name__ == "__main__":
    sys.exit(main())
