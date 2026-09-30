#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL247_SSOTPanorama v0100 — SSOT 全景:正則 · 同義字 · 自動編號 · 命名 · 註冊 · 上下連結 × VCGC → VDF → VRN → SUP

操作員令(側線 2026-09-29 i):「VCGC TO VDF TO VRN 全部檢測 · SSOT REGEX 同義字 自動編號 命名 註冊功能強化 ·
SSOT 全景式檢視 · 自動自適應式上下單向檢測到底 · 只增不減只要不發生衝突」。

一張矩陣:六族(列)× 四層(欄,由上而下 VCGC 中央 → VDF → VRN → SUP 共用件)。
  上下單向:先量中央、再量下層;上層某族紅,下層同族的格標「上游紅」(照量、不冒充綠,也不提前停 = 檢測到底)。
  自適應:每個探針記輸入指紋(git 索引 blob + 未提交檔的大小 / 時間 + 正主尾版);指紋沒變就沿用上次結果(標「沿用」),
          變了才重跑正主;--full 全部重跑。
  不另立第二把尺:每格都呼叫既有正主 ——
    正則 / 同義字:VCGC ssot_link(第四扇門:CGC_MDL169 · CGC_MDL176 · SUP_MDL749 · VRN_ENG088 · CGC_MDL185)
    自動編號:CGC_MDL237 audit(只增稽核 + 冊內一致;v0108 起)· CGC_MDL242 C3(尾版有號)
    命名:CGC_MDL242 C3(版號異形 · 沒版號檔 · 具名排除)+ 同號異名普查(全樹沒有既有正主,本引擎只報不改)
    註冊:CGC_MDL242 C3(已註冊)· VCGC registry_sync 乾跑(新 / 變 / 過期 / 撞號)· VDF / VRN 管理器上行七處
    上下連結:SDD 檢查(X-COL · X-CODE · X-COMP · X-ENGINE · X-REQ · X-REQ-BACK · X-LOCK;CGC_MDL245 v0104 起)
唯讀:只寫 VIA_Reports/ssot_panorama/(JSON · HTML · 快取),不改任何冊、不連網、不裝東西、不碰 TA-Lib。
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

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import hashlib
import html as _html
import importlib.util
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
ENGINE = Path(__file__).stem
OUT = VIA / "VIA_Reports" / "ssot_panorama"
LAYERS = (("VCGC", "中央"), ("VDF", "資料"), ("VRN", "研報"), ("SUP", "共用件"))
FAMILIES = (("REGEX", "正則"), ("SYN", "同義字"), ("NUM", "自動編號"), ("NAME", "命名"), ("REG", "註冊"), ("LINK", "上下連結"))
RANK = {"RED": 0, "YELLOW": 1, "GATED": 2, "NODATA": 2, "ABSENT": 2, "GREEN": 3, "N/A": 4}
LAYER_OF_DIR = (("supportive modules/registry/", "VCGC"), ("functional modules/VDF/", "VDF"), ("functional modules/VRN/", "VRN"),
                ("supportive modules/", "SUP"))
NOT_LIVE = ("references/", "VIA_Reports/", "VIA_RetiredEngines", "_output/", "RUN_2026", "SCOPE_COPY", "new modules engines",
            "_quarantine", "BACKUP/", "/tests/", "__pycache__")
NUM_RX = re.compile(r"^((?:[A-Z][A-Za-z]*_)?(?:CGC|SUP|VDF|VRN|VAP|VIA|VIS|VME|VMT)_(?:MDL|ENG)\d+)_([A-Za-z0-9]+)_v\d+$")
WKF_CODE_RX = re.compile(r"\b(VCGC|VDF|VRN|VAP)-WKF\d{3}\b")
DOOR_REGEX = ("matrix.", "booksync.ticker")
DOOR_DOWN = ("hub.drift", "bridge.", "union.gate")          # 下游(VRN 讀冊端)跟不上中央的格


def _vnum(path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


def lamp(state) -> str:
    """Owners speak slightly different dialects; the panorama speaks five words."""
    s = str(state or "").upper()
    if s in ("RED", "BROKEN", "FAIL", "CRASH"):
        return "RED"
    if s in ("YELLOW", "AMBER", "STALE", "FINDING", "PARTIAL"):
        return "YELLOW"
    if s in ("GATED", "NODATA", "ABSENT", "N/A"):
        return s
    return "GREEN" if s in ("GREEN", "OK", "PASS") else "NODATA"


def worst(states) -> str:
    states = [lamp(s) for s in states if s]
    return min(states, key=lambda s: RANK[s]) if states else "N/A"


def cell(family, layer, state, detail="", owner="", nxt="", n=None) -> dict:
    return {"family": family, "layer": layer, "state": lamp(state), "detail": str(detail)[:400], "owner": owner, "next": nxt, "n": n}


def layer_of(rel: str) -> str | None:
    for prefix, layer in LAYER_OF_DIR:
        if rel.startswith(prefix):
            return layer
    return None


# ---------------------------------------------------------------- owners (loaded lazily, newest tail by glob)
def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _tail(folder: Path, stem: str) -> Path | None:
    hits = [p for p in folder.glob(stem + "_v*.py") if _vnum(p) >= 0]
    return max(hits, key=_vnum) if hits else None


_OWNERS: dict = {}


def owner(stem: str, folder: Path = HERE):
    if stem not in _OWNERS:
        p = _tail(folder, stem)
        _OWNERS[stem] = _load(p, f"{stem}_for_{ENGINE}") if p else None
    return _OWNERS[stem]


# ---------------------------------------------------------------- adaptive fingerprints
def _git(*args) -> str:
    return subprocess.run(["git", *args], cwd=VIA, capture_output=True, text=True).stdout


def fingerprint(specs: tuple, owners: tuple = ()) -> str:
    """git index blobs of the pathspecs + size/mtime of their uncommitted files + the owner tails' names and sizes."""
    h = hashlib.sha256()
    h.update(_git("ls-files", "-s", "--", *specs).encode("utf-8"))
    dirty = set(_git("diff", "--name-only", "--relative", "--", *specs).split("\n")) | set(
        _git("ls-files", "--others", "--exclude-standard", "--", *specs).split("\n"))
    for rel in sorted(x for x in dirty if x):
        p = VIA / rel
        h.update(f"{rel}|{p.stat().st_size if p.exists() else -1}|{p.stat().st_mtime_ns if p.exists() else -1}".encode("utf-8"))
    for stem in owners:
        p = _tail(HERE, stem)
        h.update(f"{stem}|{p.name if p else '-'}|{p.stat().st_size if p else -1}".encode("utf-8"))
    return h.hexdigest()[:16]


# ---------------------------------------------------------------- probes: each returns a list of cells
def probe_door(ctx) -> list:
    """正則 / 同義字:VCGC 第四扇門的逐格結果。中央冊的格歸 VCGC;下游讀冊端跟不上的格(hub.drift · bridge.* · union.gate)歸 VRN。"""
    vcgc = ctx.get("vcgc")
    if vcgc is None:
        return [cell("REGEX", "VCGC", "ABSENT", "VCGC 尾版載不到(ssot_link 是第四扇門的正主)", "CGC_MDL149"),
                cell("SYN", "VCGC", "ABSENT", "VCGC 尾版載不到", "CGC_MDL149")]
    d = vcgc.ssot_link(light=True)
    groups = {}
    for r in d.get("rows") or []:
        rid = str(r.get("id") or "")
        fam = "REGEX" if rid.startswith(DOOR_REGEX) else "SYN"
        lay = "VRN" if rid.startswith(DOOR_DOWN) else "VCGC"
        groups.setdefault((fam, lay), []).append(r)
    out = []
    for (fam, lay), rows in sorted(groups.items()):
        bad = [r for r in rows if lamp(r.get("state")) != "GREEN"]
        detail = " ; ".join(f"{r['id']} {lamp(r.get('state'))}:{str(r.get('detail') or r.get('why') or '')[:90]}" for r in (bad or rows)[:4])
        nxt = next((str(r.get("next")) for r in bad if r.get("next")), "via-vcgc ssot plan(零寫規劃)")
        out.append(cell(fam, lay, worst(r.get("state") for r in rows), f"{len(rows)} 格 · 非綠 {len(bad)} · {detail}",
                        " · ".join(sorted({Path(str(r.get('src') or r.get('owner') or '')).stem for r in rows if r.get('src') or r.get('owner')}))[:120],
                        nxt if bad else "", len(rows)))
    return out


def probe_c3(ctx) -> list:
    """自動編號 / 命名 / 註冊(各層):CGC_MDL242 涵蓋稽核 C3 的逐層明細。"""
    pv = ctx.get("pathverify") or owner("CGC_MDL242_PathVerify")
    if pv is None:
        return [cell(f, lay, "ABSENT", "CGC_MDL242 不在", "CGC_MDL242") for f in ("NUM", "NAME", "REG") for lay, _ in LAYERS]
    _, detail = pv.engine_rows()
    return c3_cells(detail)


def c3_cells(detail: dict) -> list:
    out = []
    for lay, _ in LAYERS:
        d = detail.get(lay)
        if d is None:
            out += [cell(f, lay, "ABSENT", "C3 沒有這一層", "CGC_MDL242") for f in ("NUM", "NAME", "REG")]
            continue
        t = d.get("tails", 0)
        no_num, no_ntime = d.get("no_number") or [], d.get("no_number_time") or []
        no_reg, no_rtime = d.get("no_register") or [], d.get("no_register_time") or []
        rules = d.get("outside_register_rules") or {}
        odd = sum(v for k, v in rules.items() if "版號異形" in k)
        named = sum(v for k, v in rules.items() if "具名排除" in k)
        copies = sum(v for k, v in rules.items() if "同名副本" in k)
        out.append(cell("NUM", lay, "YELLOW" if (no_num or no_ntime) else "GREEN",
                        f"尾版 {t} · 有號 {t - len(no_num)} · 缺號 {len(no_num)}{(':' + '、'.join(no_num[:3])) if no_num else ''}"
                        f" · 缺編號時間 {len(no_ntime)}", "CGC_MDL242 C3 × 編號冊", "via-vcgc run CGC_MDL237_NumberingSystem --apply" if no_num else "", t))
        out.append(cell("NAME", lay, "YELLOW" if odd else "GREEN",
                        f"版號異形 {odd}(非四碼,尾版律不管;Z279)· 沒版號 .py {d.get('unversioned', 0)}(Z281 待逐支判定;不計燈)· 具名排除 {named}",
                        "CGC_MDL242 C3", "各自出四碼版號新檔再遷呼叫(L04;操作員排序)" if odd else "", t))
        out.append(cell("REG", lay, "YELLOW" if (no_reg or no_rtime) else "GREEN",
                        f"尾版 {t} · 已註冊 {t - odd - named - copies - len(no_reg)}(另:版號異形 {odd} · 具名排除 {named} · 同名副本 {copies})"
                        f" · 待註冊 {len(no_reg)}{(':' + '、'.join(no_reg[:3])) if no_reg else ''} · 缺註冊時間 {len(no_rtime)}",
                        "CGC_MDL242 C3 × 元件註冊冊", "via-vcgc registry-sync --apply" if no_reg else "", t))
    return out


def naming_census(files: list) -> dict:
    """同號異名:同一個 <前綴>_<MDL|ENG><號> 掛了兩個以上的名字(活檔尾版族)。全樹沒有既有正主量這件事 → 本引擎只報不改。"""
    groups = {}
    for rel in files:
        folder = rel.rpartition("/")[0] + "/"
        if any(t in folder for t in NOT_LIVE):
            continue
        m = NUM_RX.match(Path(rel).stem)
        lay = layer_of(rel)
        if m and lay:
            groups.setdefault(m.group(1), {}).setdefault(m.group(2), lay)
    out = {lay: [] for lay, _ in LAYERS}
    for num, names in sorted(groups.items()):
        if len(names) > 1:
            out[sorted(names.values(), key=lambda x: [k for k, _ in LAYERS].index(x))[0]].append(f"{num}:{'/'.join(sorted(names))}")
    return out


def probe_naming(ctx) -> list:
    files = ctx.get("files") if ctx.get("files") is not None else _git("ls-files", "*.py").splitlines()
    col = naming_census(files)
    return [cell("NAME", lay, "YELLOW" if col[lay] else "GREEN",
                 f"同號異名 {len(col[lay])} 組" + (":" + " ; ".join(col[lay][:4]) if col[lay] else ""),
                 "本引擎普查(無既有正主)", "是同家族伴隨模組就記進命名冊;真撞號由操作員裁定改號(不自動改名)" if col[lay] else "",
                 len(col[lay])) for lay, _ in LAYERS]


def probe_numbering(ctx) -> list:
    num = ctx.get("numbering") or owner("CGC_MDL237_NumberingSystem")
    if num is None or not hasattr(num, "audit"):
        return [cell("NUM", "VCGC", "ABSENT", "CGC_MDL237 v0108 以上才有 audit", "CGC_MDL237")]
    rep = num.audit()
    return [cell("NUM", "VCGC", rep["lamp"],
                 f"只增稽核 基準 {str(rep['baseline'])[:12]} · 列 {rep['before']} → {rep['after']}(+{rep['added']})· 遺失 {len(rep['missing'])}"
                 f" · 改身分 {len(rep['changed_identity'])} · 重號 {rep['duplicate_codes']} · 冊內不一致 {len(rep['integrity'])}"
                 + ("(" + " ; ".join(f"{i.get('rule')} {i.get('n', '')}" for i in rep["integrity"][:3]) + ")" if rep["integrity"] else ""),
                 "CGC_MDL237 audit", "紅列多為待裁定(法條缺號 Z263 · 同義字一詞兩主 Z264);遺失 / 改身分 > 0 才是真紅" if rep["integrity"] else "",
                 rep["after"])]


def probe_registry(ctx) -> list:
    vcgc = ctx.get("vcgc")
    if vcgc is None:
        return [cell("REG", "VCGC", "ABSENT", "VCGC 尾版載不到", "CGC_MDL149")]
    r = vcgc.registry_sync(apply=False)
    pending = r.get("new", 0) + r.get("changed", 0) + r.get("stale", 0)
    clash = len(r.get("collisions") or [])
    return [cell("REG", "VCGC", "YELLOW" if (pending or clash) else "GREEN",
                 f"元件冊乾跑 新 {r.get('new', 0)} · 變 {r.get('changed', 0)} · 過期 {r.get('stale', 0)} · 撞號 {clash}(零寫)",
                 "CGC_MDL149 registry_sync(apply=False)", "via-vcgc registry-sync --apply(批准)" if pending or clash else "", pending)]


def probe_managers(ctx) -> list:
    out = []
    for lay, folder, stem in (("VDF", VIA / "functional modules" / "VDF", "VDF_SystemManager"),
                              ("VRN", VIA / "functional modules" / "VRN", "VRN_SystemManager")):
        mgr = (ctx.get("managers") or {}).get(lay)
        if mgr is None:
            mgr = owner(stem, folder)
        if mgr is None:
            out.append(cell("REG", lay, "ABSENT", f"{stem} 不在", stem))
            continue
        up = (mgr.collect() or {}).get("upstream") or {}
        seven = up.get("seven") or {}
        miss = [k for k, v in seven.items() if not v]
        out.append(cell("REG", lay, "GREEN" if seven and not miss else ("YELLOW" if seven else "NODATA"),
                        f"上行七處 {up.get('done', 0)}/{len(seven) or 7}" + (f" · 缺 {miss}" if miss else "") + f" · 總管理器 {up.get('via_manager', '?')}",
                        stem + " upstream", "補缺的那一處(spec / grid / register / deck / manager / inventory / handover)" if miss else "", up.get("done")))
    return out


def probe_sdd(ctx) -> list:
    sdd = ctx.get("sdd") or owner("CGC_MDL245_SDDValidator")
    if sdd is None:
        return [cell("LINK", lay, "ABSENT", "CGC_MDL245 不在", "CGC_MDL245") for lay, _ in LAYERS]
    base = sdd
    while "PRIOR" in vars(base):
        base = vars(base)["PRIOR"]
    rep = base.check(write=False)
    state = base.load_books()
    state["req"] = base._json(base.newest("VIA_Requirements_SSOT_v*.json"))
    back = sdd.back_links(state) if hasattr(sdd, "back_links") else []
    return sdd_cells(rep, state, back)


def sdd_cells(rep: dict, state: dict, back: list) -> list:
    rows = rep.get("rows") or []
    glob_rules = ("X-COL", "X-CODE", "X-COMP", "X-ENGINE", "X-REQ", "X-OWNER", "X-ITEM", "X-OLD", "X-CONFLICT")
    central = worst(r.get("lamp") for r in rows if r.get("rule") in glob_rules)
    lock_rows = [r for r in rows if r.get("rule") == "X-LOCK" and lamp(r.get("lamp")) != "GREEN"]
    reqs = (state.get("req") or {}).get("requirements") or []
    out = []
    for lay, _ in LAYERS:
        wk = [w for _, w in state.get("wkfs") or [] if str(w.get("code", "")).startswith(lay + "-")]
        steps = sum(len(w.get("steps") or []) for w in wk)
        rq = [r for r in reqs if str(r.get("code", "")).startswith(lay + "-")]
        gaps = [b for b in back if b.split("→")[-1].startswith(lay + "-")]
        relock = sorted({m.group(0) for r in lock_rows for m in WKF_CODE_RX.finditer(str(r.get("msg"))) if m.group(0).startswith(lay + "-")})
        if not wk and not rq:
            out.append(cell("LINK", lay, "N/A", "本層沒有工作流與需求(共用件掛在各子系統的步上)", "CGC_MDL245"))
            continue
        st = worst([central if lay == "VCGC" else "GREEN", "YELLOW" if gaps else "GREEN", "YELLOW" if relock else "GREEN"])
        out.append(cell("LINK", lay, st,
                        f"工作流 {len(wk)} · 步 {steps} · 需求 {len(rq)} · 單向 {len(gaps)}{(':' + '、'.join(gaps[:3])) if gaps else ''}"
                        f" · 待重驗鎖 {len(relock)}{(':' + '、'.join(relock[:3])) if relock else ''}"
                        + (f" · 中央結構檢 {central}" if lay == "VCGC" else ""),
                        "CGC_MDL245 check(X-*)", ("工作流冊出新版補回指;" if gaps else "") + ("via-vcgc sdd selftests / real → lock --apply" if relock else ""),
                        len(wk)))
    return out


PROBES = (
    ("door", ("supportive modules/registry/*.json", "supportive modules/70_VRN_Rules/*.json", "functional modules/VRN/*.json"),
     ("CGC_MDL149_VeritasCentralGovernanceConsole", "CGC_MDL169_VIAStateMatrix", "CGC_MDL176_SynonymUnion", "CGC_MDL185_SsotBookSync"), probe_door),
    ("c3", ("*.py", "supportive modules/registry/VIA_Component_Inventory_SSOT_v0100.json", "supportive modules/registry/VIA_NumberBooks"),
     ("CGC_MDL242_PathVerify",), probe_c3),
    ("naming", ("*.py",), (), probe_naming),
    ("numbering", ("supportive modules/registry/VIA_NumberBooks", "supportive modules/registry/VIA_Numbering_SSOT_v*.json"),
     ("CGC_MDL237_NumberingSystem",), probe_numbering),
    ("registry", ("*.py", "*.ps1", "supportive modules/registry/VIA_Component_Inventory_SSOT_v0100.json",
                  "supportive modules/registry/VIA_EngineVersion_Register_v*.json"), ("CGC_MDL149_VeritasCentralGovernanceConsole",), probe_registry),
    ("managers", ("VIA_SYSTEM_MANAGER_v*.py", "Register-VIA-Commands-v*.ps1", "supportive modules/registry/*.json", "docs"),
     ("CGC_MDL149_VeritasCentralGovernanceConsole",), probe_managers),
    ("sdd", ("supportive modules/registry/VIA_Workflow_*.json", "supportive modules/registry/VIA_Requirements_SSOT_v*.json",
             "supportive modules/registry/VIA_LampLock_v*.json", "*.py"), ("CGC_MDL245_SDDValidator",), probe_sdd),
)


FAMILY_OF_PROBE = {"door": "REGEX", "c3": "NUM", "naming": "NAME", "numbering": "NUM", "registry": "REG", "managers": "REG", "sdd": "LINK"}


# ---------------------------------------------------------------- the cascade
def cascade(cells: list) -> dict:
    """Top-down, one way: a RED upstream cell marks the same family further down as behind an upstream red (measured anyway)."""
    order = [k for k, _ in LAYERS]
    grid = {}
    for c in cells:
        key = (c["family"], c["layer"])
        grid[key] = c if key not in grid else dict(grid[key], state=worst([grid[key]["state"], c["state"]]),
                                                   detail=grid[key]["detail"] + " ‖ " + c["detail"], owner=grid[key]["owner"] + " + " + c["owner"],
                                                   next=grid[key]["next"] or c["next"])
    for fam, _ in FAMILIES:
        red_at = None
        for lay in order:
            c = grid.get((fam, lay))
            if c is None:
                grid[(fam, lay)] = cell(fam, lay, "N/A", "本層沒有此族的冊或正主(不冒充綠)")
                continue
            if red_at:
                c["upstream_red"] = red_at
            if c["state"] == "RED" and not red_at:
                red_at = lay
    fam_verdict = {fam: worst(grid[(fam, lay)]["state"] for lay in order) for fam, _ in FAMILIES}
    return {"grid": grid, "families": fam_verdict, "verdict": worst(fam_verdict.values())}


def _load_cache(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def run(full: bool = False, write: bool = True, ctx: dict | None = None, probes=None, out_dir: Path | None = None) -> dict:
    ctx = dict(ctx or {})
    out_dir = out_dir or OUT
    cache_path = out_dir / "cache.json"
    cache = {} if full else _load_cache(cache_path)
    cells, meta, t0 = [], [], time.time()
    for pid, specs, owners, fn in (probes or PROBES):
        t1 = time.time()
        fp = fingerprint(specs, owners) if not ctx.get("fp") else ctx["fp"](pid)
        hit = cache.get(pid)
        if hit and hit.get("fp") == fp and hit.get("engine") == ENGINE:
            got, reused = hit["cells"], True
        else:
            try:
                got = fn(ctx)
            except Exception as exc:            # owner blew up: say so, in the family it feeds (never a silent green)
                got = [cell(FAMILY_OF_PROBE.get(pid, "LINK"), "VCGC", "RED", f"正主呼叫失敗 {type(exc).__name__}: {str(exc)[:160]}", pid)]
            reused = False
            cache[pid] = {"fp": fp, "engine": ENGINE, "cells": got, "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        for c in got:
            c = dict(c, probe=pid, reused=reused)
            cells.append(c)
        meta.append({"probe": pid, "fp": fp, "reused": reused, "secs": round(time.time() - t1, 2)})
    res = cascade(cells)
    rep = {"schema": "VIA.SSOTPanorama.v1", "engine": ENGINE, "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "verdict": res["verdict"],
           "families": res["families"], "layers": [k for k, _ in LAYERS], "cells": [dict(v, key=f"{k[0]}@{k[1]}") for k, v in res["grid"].items()],
           "probes": meta, "reused": sum(1 for m in meta if m["reused"]), "secs": round(time.time() - t0, 1),
           "rule": "上下單向:中央 → VDF → VRN → SUP;上層紅 → 下層同族標上游紅(照量)。沿用 = 輸入指紋沒變。只讀。"}
    if write:
        out_dir.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
        (out_dir / "SSOT_PANORAMA_latest.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
        kit = ctx.get("kit", "auto")
        kit = owner("CGC_MDL241_TemplateAdapter") if kit == "auto" else kit
        if kit is not None:
            (out_dir / "SSOT_PANORAMA_latest.html").write_text(page(rep, kit), encoding="utf-8")
    return rep


# ---------------------------------------------------------------- output
SIGN = {"GREEN": "綠", "YELLOW": "黃", "RED": "紅", "GATED": "閘", "NODATA": "無料", "ABSENT": "缺", "N/A": "—"}


def show(rep: dict) -> None:
    grid = {c["key"]: c for c in rep["cells"]}
    lays = rep["layers"]
    print(f"[SSOT 全景] {rep['verdict']} · 上下單向 {' → '.join(lays)} · 探針 {len(rep['probes'])}(沿用 {rep['reused']})· {rep['secs']}s")
    print("  " + "族".ljust(8) + "".join(x.ljust(8) for x in lays) + "族總判")
    for fam, zh in FAMILIES:
        row = "".join((SIGN[grid[f'{fam}@{x}']['state']] + ("↑" if grid[f'{fam}@{x}'].get("upstream_red") else "")).ljust(8) for x in lays)
        print(f"  {zh:<6}{row}{rep['families'][fam]}")
    for c in sorted(rep["cells"], key=lambda c: (RANK[c["state"]], [f for f, _ in FAMILIES].index(c["family"]), lays.index(c["layer"]))):
        if c["state"] in ("GREEN", "N/A"):
            continue
        zh = dict(FAMILIES)[c["family"]]
        print(f"  [{c['state']}] {zh}@{c['layer']} · {c['detail'][:230]}" + (f"  → {c['next']}" if c.get("next") else "")
              + (f"(上游 {c['upstream_red']} 紅)" if c.get("upstream_red") else "") + ("(沿用)" if c.get("reused") else ""))
    print("  下一步:via-vcgc ssot panorama --full(全部重量)· 頁:VIA_Reports/ssot_panorama/SSOT_PANORAMA_latest.html")


def page(rep: dict, kit) -> str:
    e = _html.escape
    grid = {c["key"]: c for c in rep["cells"]}
    lays = rep["layers"]
    head = "<tr><th>族</th>" + "".join(f"<th>{e(x)} {e(dict(LAYERS)[x])}</th>" for x in lays) + "<th>族總判</th></tr>"
    body_rows = ""
    for fam, zh in FAMILIES:
        tds = ""
        for x in lays:
            c = grid[f"{fam}@{x}"]
            tds += f"<td title='{e(c['detail'])}'>{kit.lamp(c['state'], SIGN[c['state']] + (' ↑上游紅' if c.get('upstream_red') else ''))}</td>"
        body_rows += f"<tr><td>{e(zh)}</td>{tds}<td>{kit.lamp(rep['families'][fam], rep['families'][fam])}</td></tr>"
    det = "".join(f"<tr><td>{kit.lamp(c['state'], c['state'])}</td><td>{e(dict(FAMILIES)[c['family']])}@{e(c['layer'])}</td><td>{e(c['detail'])}</td>"
                  f"<td>{e(c['owner'])}</td><td>{e(c.get('next') or '')}</td><td>{'沿用' if c.get('reused') else '重量'}</td></tr>"
                  for c in sorted(rep["cells"], key=lambda c: (RANK[c["state"]], c["family"], lays.index(c["layer"]))))
    side = (f"<div class='via-card'>{kit.lamp(rep['verdict'], '總判 ' + rep['verdict'])}</div><div class='via-note'>{e(rep['ts'])}</div>"
            f"<div class='via-note'>探針 {len(rep['probes'])} · 沿用 {rep['reused']} · {rep['secs']}s</div>")
    body = (f"<h3>① 六族 × 四層(由上而下 {' → '.join(lays)})</h3><table class='via'>{head}{body_rows}</table>"
            f"<h3>② 逐格明細(不綠的排前面;每格都標正主與下一步)</h3><table class='via'><tr><th>燈</th><th>族@層</th><th>量到的</th>"
            f"<th>正主</th><th>下一步</th><th>來源</th></tr>{det}</table>"
            f"<div class='via-note'>{e(rep['rule'])}</div>")
    return kit.page("SSOT 全景 · 上下單向檢測", body, side, module={"id": "vcgc-ssot-panorama", "name": "SSOT 全景"})


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args:
        return selftest()
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc(via-vcgc ssot panorama)"}, ensure_ascii=False))
        return 2
    ctx = {"vcgc": owner("CGC_MDL149_VeritasCentralGovernanceConsole")}
    rep = run(full="--full" in args, write="--no-write" not in args, ctx=ctx)
    if "--json" in args:
        print(json.dumps(rep, ensure_ascii=False, indent=1))
    else:
        show(rep)
    return {"GREEN": 0, "YELLOW": 2, "GATED": 2, "NODATA": 2, "ABSENT": 2, "N/A": 2, "RED": 1}[rep["verdict"]]


# ---------------------------------------------------------------- selftest
def selftest() -> int:
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    chk("① 燈語統一:AMBER→黃 · BROKEN→紅 · 未知→無料;最壞者勝", (lamp("AMBER"), lamp("BROKEN"), lamp("weird"), worst(["GREEN", "YELLOW", "RED"]))
        == ("YELLOW", "RED", "NODATA", "RED"))
    res = cascade([cell("NUM", "VCGC", "RED", "x"), cell("NUM", "VDF", "GREEN"), cell("NUM", "VRN", "YELLOW"), cell("REG", "VCGC", "GREEN")])
    g = res["grid"]
    chk("② 上下單向:中央紅 → 下層同族標上游紅(照量,不改它的燈);別族不受牽連",
        g[("NUM", "VDF")].get("upstream_red") == "VCGC" and g[("NUM", "VDF")]["state"] == "GREEN" and g[("NUM", "VRN")].get("upstream_red") == "VCGC"
        and not g[("REG", "VDF")].get("upstream_red") and res["families"]["NUM"] == "RED")
    chk("③ 到底:沒有正主的格補成 —(N/A),每族每層都有格,不提前停", len(g) == len(FAMILIES) * len(LAYERS) and g[("SYN", "SUP")]["state"] == "N/A")
    calls = {"n": 0}

    def fake(ctx):
        calls["n"] += 1
        return [cell("REG", "VCGC", "GREEN", "fake")]
    fps = {"v": "a"}
    with tempfile.TemporaryDirectory() as tmp:
        probes = (("fake", (), (), fake),)
        ctx = {"fp": lambda pid: fps["v"], "kit": None}
        r1 = run(ctx=ctx, probes=probes, out_dir=Path(tmp))
        r2 = run(ctx=ctx, probes=probes, out_dir=Path(tmp))
        fps["v"] = "b"
        r3 = run(ctx=ctx, probes=probes, out_dir=Path(tmp))
        r4 = run(full=True, ctx=ctx, probes=probes, out_dir=Path(tmp))
        r5 = run(write=False, ctx=ctx, probes=probes, out_dir=Path(tmp) / "none")
        none_written = not (Path(tmp) / "none").exists()
        cached = (Path(tmp) / "cache.json").is_file() and (Path(tmp) / "SSOT_PANORAMA_latest.json").is_file()
    chk("④ 自適應:指紋沒變沿用、變了重跑、--full 全重跑;寫時落快取與 JSON,--no-write 一個檔都不寫",
        calls["n"] == 4 and (r1["reused"], r2["reused"], r3["reused"], r4["reused"]) == (0, 1, 0, 0) and none_written and cached,
        f"呼叫 {calls['n']} 次 · 沿用 {[r['reused'] for r in (r1, r2, r3, r4, r5)]} · 不寫 {none_written} · 有快取 {cached}")
    det = {"VCGC": {"tails": 10, "no_number": [], "no_register": [], "outside_register_rules": {"版號異形(非四碼;尾版律不管)": 2}, "unversioned": 5},
           "VDF": {"tails": 3, "no_number": ["a_v0100.py"], "no_register": ["a_v0100.py"], "outside_register_rules": {}, "unversioned": 0}}
    cs = {(c["family"], c["layer"]): c for c in c3_cells(det)}
    chk("⑤ C3 對應:缺號 → 編號黃 · 待註冊 → 註冊黃 · 版號異形 → 命名黃;乾淨 → 綠;沒這層 → 缺",
        cs[("NUM", "VDF")]["state"] == "YELLOW" and cs[("REG", "VDF")]["state"] == "YELLOW" and cs[("NAME", "VCGC")]["state"] == "YELLOW"
        and cs[("NUM", "VCGC")]["state"] == "GREEN" and cs[("NUM", "VRN")]["state"] == "ABSENT")
    col = naming_census(["supportive modules/registry/CGC_MDL900_Alpha_v0100.py", "supportive modules/registry/CGC_MDL900_Beta_v0101.py",
                         "functional modules/VDF/VDF_ENG900_One_v0100.py", "functional modules/VDF/VDF_ENG900_One_v0101.py",
                         "supportive modules/registry/references/CGC_MDL901_A_v0100.py", "supportive modules/registry/references/CGC_MDL901_B_v0100.py"])
    chk("⑥ 同號異名普查:同號兩名抓到 · 同名多版不算 · 不活的夾不算", col["VCGC"] == ["CGC_MDL900:Alpha/Beta"] and col["VDF"] == [], col)
    rows = [{"lamp": "GREEN", "rule": "X-COMP", "msg": ""}, {"lamp": "YELLOW", "rule": "X-LOCK", "msg": "['VCGC-WKF003:a→b']"}]
    st = {"wkfs": [("b", {"code": "VCGC-WKF003", "steps": [{"code": "VCGC-WKF003-STP001"}]}), ("b", {"code": "VRN-WKF002", "steps": []})],
          "req": {"requirements": [{"code": "VRN-REQ006"}, {"code": "VCGC-REQ001"}]}}
    sc = {c["layer"]: c for c in sdd_cells({"rows": rows}, st, ["VRN-REQ006→VRN-WKF002"])}
    chk("⑦ 上下連結:待重驗鎖歸到它的層 · 單向歸到被指的工作流那層 · 沒有工作流的層 = —",
        sc["VCGC"]["state"] == "YELLOW" and "待重驗鎖 1" in sc["VCGC"]["detail"] and sc["VRN"]["state"] == "YELLOW" and "單向 1" in sc["VRN"]["detail"]
        and sc["SUP"]["state"] == "N/A" and sc["VDF"]["state"] == "N/A")
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑧ 檔頭 · 加速器橋 · 網路橋在;不碰 TA-Lib;沒有寫冊的呼叫(只寫 VIA_Reports)",
        "VIA:ACCEL-BRIDGE" in text and "VIA:NET-BRIDGE" in text and not re.search(r"^\s*(import|from)\s+talib", text, re.M)
        and not re.search(r"sync\(apply\s*=\s*True", text))
    real = naming_census(_git("ls-files", "*.py").splitlines())
    chk("⑨ 實樹:同號異名普查跑得動(只報不改)", isinstance(real, dict) and set(real) == {k for k, _ in LAYERS},
        {k: len(v) for k, v in real.items()})
    print(f"[SSOT 全景] 自測 fail={len(ok) - sum(ok)}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
