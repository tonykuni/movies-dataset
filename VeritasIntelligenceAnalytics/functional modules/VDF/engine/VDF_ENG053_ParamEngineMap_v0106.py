#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VDF_ENG053_ParamEngineMap v0106 — 薄尾(v0100–v0105 一字不動):VDF 參數唯一正本 + 衍生冊 + 引擎合併計畫

操作員 2026-11-25:「用 VCGC 省 Token 建 VCGC 與 VDF:統一參數控制 · 合併引擎 · 照 CLAUDE.md · 桌機實測」。逐題定案:
  正本 = VDF_ParamControl_SSOT 尾版(唯一可手改的參數冊);Unified · DataPlane · FinPeriod 裡被登記的參數路徑與 Param_Engine_Map
  改由正本產生(衍生冊,不再手改)。VCGC 只讀匯總(下一批)。引擎合併:先出計畫,不刪。這批只做 VDF。
動詞(其餘照前版 run · --selftest):
  unify [--apply]       正本 ↔ 各冊尾版對齊:每列 SAME(同)· REPOINT(冊換版、值同)· DRIFT(值不同)· MISSING(尾版沒這路徑)
                        + NEW(Unified 尾版有、正本沒登的葉)。--apply 出正本新版號:冊名指到尾版 · DRIFT 採尾版值並記 history
                        (首次接管:操作員的裁定都已落在尾版冊,例 PC-001)· NEW 補登 VDF-PAR-### · MISSING 只標不刪 · counts 重算。
  derive [--apply]      以正本值為準:各冊尾版在被登記路徑上的值 ≠ 正本 → 出該冊新版號(只改那些路徑,其餘一字不動,
                        帶 derived_from);Param_Engine_Map 用前版 build_map() 重算,出新版號(不覆寫前版檔)。
  consolidate           VDF 引擎合併計畫(不改任何引擎檔):家族版本數 · 尾版頂層函式正規化 AST 雜湊撞同 = 重複實作 ·
                        被誰引用(其他 VDF 尾版的名稱 / 字串)· 參數集重疊(Param_Engine_Map)→ KEEP · MERGE_CANDIDATE → 本體 ·
                        DORMANT_CANDIDATE(沒人引用)· 每列附證據。實體合併 / 刪除不在本批(待裁定 2)。
輸出:VIA_Reports/vdf_params/<UTC>/ 的 DataFrame(polars,退 pandas)parquet zstd + SUMMARY.json;運作帳 RUN_LEDGER.jsonl 只增。
寫冊規則:新版號 = max(本機 ∪ origin/main)+1 · 暫存檔原子換名 · 前版一字不動 · 只增不減;寫前寫後跑 VCGC ssot panorama
(主控台不在 = 黃退路,VDF 照寫:系統獨立)。號碼 VDF-PAR-### 由 VDF 自發(VDF-REQ038 裁定)。
用法:python VDF_ENG053_ParamEngineMap_v0106.py unify|derive [--apply] | consolidate | run | --selftest
rc:0 綠 · 2 黃(有差異未寫 / 有 MISSING)· 1 紅
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0111] SuperAccel 加速器橋(從 TEMP 跑時改由工作目錄 / VIA_REPO 找倉;graceful) =====
try:
    import os as _sa_os
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_hit = None
    _sa_roots = [_sa_Path(__file__).resolve(), _sa_Path.cwd().resolve()]
    if _sa_os.environ.get("VIA_REPO"):
        _sa_roots.append(_sa_Path(_sa_os.environ["VIA_REPO"]).resolve())
    for _sa_r in _sa_roots:
        for _sa_q in (_sa_r, *_sa_r.parents):
            for _sa_c in (_sa_q / "supportive modules", _sa_q / "VeritasIntelligenceAnalytics" / "supportive modules"):
                if (_sa_c / "VIA_SuperAccel_Module.py").exists():
                    _sa_hit = _sa_c
                    break
            if _sa_hit:
                break
        if _sa_hit:
            break
    if _sa_hit and str(_sa_hit) not in _sa_sys.path:
        _sa_sys.path.insert(0, str(_sa_hit))
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響(自測會把它記成黃)
# ===== [VIA:ACCEL-BRIDGE:END] =====
# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(操作員 2026-11-25「網路工具也要強制加入」;從 TEMP 跑時改由工作目錄 / VIA_REPO 找倉;graceful) =====
VIA_NET_TOOL_PATH = None
try:
    import os as _nb_os
    from pathlib import Path as _nb_Path
    _nb_roots = [_nb_Path(__file__).resolve(), _nb_Path.cwd().resolve()]
    if _nb_os.environ.get("VIA_REPO"):
        _nb_roots.append(_nb_Path(_nb_os.environ["VIA_REPO"]).resolve())
    for _nb_r in _nb_roots:
        for _nb_q in (_nb_r, *_nb_r.parents):
            for _nb_dir in (_nb_q / "supportive modules" / "network", _nb_q / "VeritasIntelligenceAnalytics" / "supportive modules" / "network"):
                _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py")) if _nb_dir.is_dir() else []
                if _nb_hits:
                    VIA_NET_TOOL_PATH = str(_nb_hits[-1])
                    break
            if VIA_NET_TOOL_PATH:
                break
        if VIA_NET_TOOL_PATH:
            break
except Exception:  # noqa: BLE001
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT:載入不出網,真的連線才看閘);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:  # noqa: BLE001
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import ast
import copy
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

STEM = "VDF_ENG053_ParamEngineMap"
VERSION = "v0106"
TAG = f"{STEM} {VERSION}"
HERE = Path(__file__).resolve().parent
_T0 = time.time()
MASTER = "VDF_ParamControl_SSOT"
UNIFIED = "VDF_Unified_Params"
REGISTRY = "VDF_Param_Registry"
EMAP = "VDF_Param_Engine_Map"
CLASS_OF = {"time": "時間範圍", "fetch": "輸入參數", "markets": "輸入參數", "output": "輸出參數", "honesty": "規則"}
SKIP_TOP = {"schema", "note", "version", "prior", "ts", "derived_from"}
_MISSING = object()
INVENTORY_BOOKS = {EMAP, REGISTRY}                                        # consolidate 的引用面排除這兩本(它們本身就是全引擎清冊)


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(str(p)).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(STEM + "_prior_for_" + VERSION, PRIOR_PATH)
P = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = P
_spec.loader.exec_module(P)
UNIFIED_ALIAS = P.UNIFIED_ALIAS                                            # VDF_SSOTSync 從尾版收割別名表:照前版原值轉接
VDF = HERE.parent


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(P, name)


def say(msg: str) -> None:
    print(f"[{time.time() - _T0:6.1f}s] {msg}", flush=True)


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def family(name: str) -> str:
    return re.sub(r"_v\d{4}$", "", Path(name).stem)


def tail_of(vdf: Path, fam: str):
    c = [p for p in vdf.rglob(fam + "_v*.json") if _vnum(p) >= 0 and "_sha" not in p.name.lower()]
    return max(c, key=_vnum) if c else None


def get_path(obj, path: str):
    cur = obj
    for k in path.split("."):
        if isinstance(cur, dict) and k in cur:
            cur = cur[k]
        else:
            return _MISSING
    return cur


def set_path(obj, path: str, value) -> None:
    ks = path.split(".")
    cur = obj
    for k in ks[:-1]:
        cur = cur.setdefault(k, {})
    cur[ks[-1]] = value


def load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


# ---------------------------------------------------------------- 寫冊(新版號 · 原子 · 只增)
def published_max(p: Path, fam: str) -> int:
    try:
        repo = p.resolve()
        while repo.parent != repo and not (repo / ".git").exists():
            repo = repo.parent
        rel = p.parent.resolve().relative_to(repo).as_posix()
        r = subprocess.run(["git", "-C", str(repo), "ls-tree", "--name-only", "origin/main", rel + "/"],
                           capture_output=True, text=True, timeout=30)
        return max([_vnum(x) for x in r.stdout.splitlines() if Path(x).name.startswith(fam + "_v")] or [-1])
    except Exception:  # noqa: BLE001 - 沒有 git / origin:只看本機
        return -1


def write_next(tail: Path, obj: dict, why: str, extra: dict | None = None) -> Path:
    fam = family(tail.name)
    nv = max(max((_vnum(p) for p in tail.parent.glob(fam + "_v*.json")), default=-1), published_max(tail, fam)) + 1
    vs = f"v{nv:04d}"
    dest = tail.with_name(f"{fam}_{vs}.json")
    if dest.exists():
        raise FileExistsError(dest.name)
    new = dict(obj)
    if "version" in new:
        new["version"] = vs
    new["prior"] = tail.name
    new["ts"] = now_utc()
    new[f"why_{vs}"] = why
    new.update(extra or {})
    tmp = dest.with_name(dest.name + f".{os.getpid()}.sdd_tmp")
    tmp.write_text(json.dumps(new, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    json.loads(tmp.read_text(encoding="utf-8"))
    os.replace(tmp, dest)
    return dest


def ssot_panorama(vdf: Path) -> str:
    for q in (vdf, *vdf.parents):
        v = sorted((q / "supportive modules" / "registry").glob("CGC_MDL149_VeritasCentralGovernanceConsole_v*.py"), key=_vnum)
        if v:
            try:
                r = subprocess.run([sys.executable, str(v[-1]), "ssot", "panorama"], cwd=str(q.parent), capture_output=True, text=True,
                                   timeout=900, env=dict(os.environ, VIA_FROM_VCGC="YES", PYTHONUTF8="1"), encoding="utf-8", errors="replace")
                return f"rc {r.returncode}"
            except Exception as e:  # noqa: BLE001
                return f"YELLOW({type(e).__name__})"
    return "YELLOW(VCGC 主控台不在:跳過 · 退路)"


# ---------------------------------------------------------------- unify
def _contains(big, small) -> bool:
    if isinstance(big, dict) and isinstance(small, dict):
        return all(k in big and big[k] == v for k, v in small.items())
    if isinstance(big, list) and isinstance(small, list):
        enc = lambda x: json.dumps(x, sort_keys=True, ensure_ascii=False, default=str)  # noqa: E731
        return {enc(x) for x in small} <= {enc(x) for x in big}
    return False


def direction(vdf: Path, e: dict, val) -> str:
    """值不同時判誰較新(不盲採任一邊;只增不減):
    超集 → 多的那邊較新;否則看正本登記時指的那版冊:那版的值 = 正本 → 後來改的是冊(BOOK_AHEAD);
    那版的值 = 現在冊值 → 後來改的是正本(MASTER_AHEAD);其餘 CONFLICT(兩邊都改過,要裁定)。"""
    mv = e.get("value")
    if _contains(mv, val) and mv != val:
        return "MASTER_AHEAD"
    if _contains(val, mv) and mv != val:
        return "BOOK_AHEAD"
    old = next((p for p in vdf.rglob(e["book"])), None)
    tail = tail_of(vdf, family(e["book"]))
    if old is not None and tail is not None and old.name != tail.name:     # 有版本史才能判方向;同一版就只能裁定
        ov = get_path(load(old), e["path"])
        if ov is not _MISSING and ov == mv:
            return "BOOK_AHEAD"
        if ov is not _MISSING and ov == val:
            return "MASTER_AHEAD"
    return "CONFLICT"


def unify(vdf: Path, apply: bool = False) -> dict:
    mt = tail_of(vdf, MASTER)
    if mt is None:
        return {"lamp": "RED", "note": f"正本 {MASTER} 不在"}
    m = load(mt)
    rows, cache = [], {}
    for e in m.get("params", []):
        fam = family(e["book"])
        t = cache.setdefault(fam, tail_of(vdf, fam))
        val = get_path(load(t), e["path"]) if t else _MISSING
        if t is None or val is _MISSING:
            st = "MISSING"
        elif val != e.get("value"):
            st = direction(vdf, e, val)
        elif t.name != e["book"]:
            st = "REPOINT"
        else:
            st = "SAME"
        rows.append({"id": e["id"], "name": e["name"], "class": e.get("class"), "book_old": e["book"], "book_tail": t.name if t else None,
                     "path": e["path"], "value_old": e.get("value"), "value_tail": None if val is _MISSING else val, "state": st})
    ut = cache.get(UNIFIED) or tail_of(vdf, UNIFIED)
    have = {(family(e["book"]), e["path"]) for e in m.get("params", [])}
    if ut:
        u = load(ut)
        for top, v in u.items():
            if top in SKIP_TOP or not isinstance(v, dict) or top.startswith("why_"):
                continue
            for k, val in v.items():
                if (UNIFIED, f"{top}.{k}") not in have:
                    rows.append({"id": None, "name": f"統一參數 · {top}.{k}", "class": CLASS_OF.get(top, "輸入參數"), "book_old": None,
                                 "book_tail": ut.name, "path": f"{top}.{k}", "value_old": None, "value_tail": val, "state": "NEW"})
    res = {"master": mt.name, "rows": rows, "counts": {s: sum(1 for r in rows if r["state"] == s)
                                                       for s in ("SAME", "REPOINT", "BOOK_AHEAD", "MASTER_AHEAD", "CONFLICT", "MISSING", "NEW")}}
    todo = sum(res["counts"][k] for k in ("REPOINT", "BOOK_AHEAD", "MASTER_AHEAD", "CONFLICT", "NEW"))
    if apply and todo:
        new = copy.deepcopy(m)
        by = {r["id"]: r for r in rows if r["id"]}
        at = now_utc()
        for e in new["params"]:
            r = by[e["id"]]
            if r["state"] in ("REPOINT", "BOOK_AHEAD", "MASTER_AHEAD"):
                if r["state"] == "BOOK_AHEAD":
                    e.setdefault("history", []).append({"at": at, "from": e.get("value"), "to": r["value_tail"], "book_from": e["book"],
                                                        "book_to": r["book_tail"], "reason": "正本接管:冊較新(版本史判定),採冊值"})
                    e["value"] = r["value_tail"]
                    e["updated_at"] = at
                elif r["state"] == "MASTER_AHEAD":
                    e["derive_pending"] = at                              # 正本較新:值不動,derive 寫回冊
                e["book"] = r["book_tail"]
            elif r["state"] == "CONFLICT":
                k = len(new.setdefault("conflicts", [])) + 1
                e["conflict_open"] = f"PC-{k:03d}"                       # derive 看到這個標記就不寫回(衝突由操作員裁)
                new["conflicts"].append({"id": f"PC-{k:03d}", "what": f"{e['id']} {e['name']}:正本與 {r['book_tail']} {e['path']} 兩邊都改過",
                                         "status": "OPEN(待操作員裁定;兩邊都沒動)", "master_value": e.get("value"), "book_value": r["value_tail"],
                                         "opened_at": at, "by": TAG})
            elif r["state"] == "MISSING":
                e["missing_in_tail"] = at
        nums = [int(x["id"].rsplit("-", 1)[1]) for x in new["params"] if re.fullmatch(r"VDF-PAR-\d+", str(x.get("id")))]
        n = max(nums or [0])
        for r in rows:
            if r["state"] == "NEW":
                n += 1
                r["id"] = f"VDF-PAR-{n:03d}"
                new["params"].append({"name": r["name"], "book": r["book_tail"], "path": r["path"], "value": r["value_tail"], "class": r["class"],
                                      "mutable": True, "why": f"{TAG} unify 補登:{r['book_tail']} {r['path']}", "id": r["id"],
                                      "version": "v0100", "registered_at": at})
        c = new.setdefault("counts", {})
        c["io_params_total"] = len(new["params"])
        c["mutable"] = sum(1 for x in new["params"] if x.get("mutable"))
        c["immutable"] = c["io_params_total"] - c["mutable"]
        c["by_class"] = {k: sum(1 for x in new["params"] if x.get("class") == k) for k in sorted({x.get("class") for x in new["params"]})}
        rt = tail_of(vdf, REGISTRY)
        if rt:
            c["code_params_harvested"] = len(load(rt).get("params", []))
            c["code_params_book"] = rt.name
        if len(new["params"]) < len(m["params"]):
            res.update(lamp="RED", note="新版列數比前版少 → 不寫")
            return res
        res["written"] = write_next(mt, new, f"{TAG} unify:正本接管 · REPOINT {res['counts']['REPOINT']} · "
                                    f"BOOK_AHEAD {res['counts']['BOOK_AHEAD']} · MASTER_AHEAD {res['counts']['MASTER_AHEAD']}(derive 寫回)· CONFLICT {res['counts']['CONFLICT']}(開 PC 待裁)· "
            f"NEW {res['counts']['NEW']} · MISSING {res['counts']['MISSING']}(只標不刪)",
                                    {"master": True, "derived_books": sorted({family(x["book"]) for x in new["params"]}) + [EMAP]}).name
    open_ = res["counts"]["MISSING"] + res["counts"]["CONFLICT"]
    res["lamp"] = "GREEN" if (not todo or res.get("written")) and not open_ else "YELLOW"
    return res


# ---------------------------------------------------------------- derive
def derive(vdf: Path, apply: bool = False, map_builder=None) -> dict:
    mt = tail_of(vdf, MASTER)
    if mt is None:
        return {"lamp": "RED", "note": f"正本 {MASTER} 不在"}
    m = load(mt)
    rows, writes = [], []
    moved: dict = {}
    by_fam: dict = {}
    for e in m.get("params", []):
        if e.get("missing_in_tail"):
            continue
        if e.get("conflict_open"):
            rows.append({"book": e["book"], "path": e["path"], "id": e["id"], "state": f"CONFLICT_SKIP {e['conflict_open']}"})
            continue
        by_fam.setdefault(family(e["book"]), []).append(e)
    for fam, es in sorted(by_fam.items()):
        t = tail_of(vdf, fam)
        if t is None:
            rows.append({"book": fam, "path": "*", "state": "BOOK_MISSING", "id": None})
            continue
        b = load(t)
        new = copy.deepcopy(b)
        changed = 0
        for e in es:
            cur = get_path(b, e["path"])
            st = "SAME" if cur == e["value"] else ("ADD" if cur is _MISSING else "SET")
            rows.append({"book": t.name, "path": e["path"], "id": e["id"], "state": st,
                         "value_book": None if cur is _MISSING else cur, "value_master": e["value"]})
            if st != "SAME":
                set_path(new, e["path"], e["value"])
                changed += 1
        if apply and changed:
            dest = write_next(t, new, f"{TAG} derive:正本 {mt.name} 的 {changed} 條參數寫回(其餘一字不動)", {"derived_from": mt.name})
            writes.append(dest.name)
            moved[fam] = dest.name
        elif t.name != es[0]["book"]:
            moved.setdefault(fam, t.name)
    if map_builder is not None:
        try:
            et = tail_of(vdf, EMAP)
            fresh = map_builder()
            old = load(et) if et else {}
            strip = lambda d: {k: v for k, v in d.items() if k not in ("ts", "prior", "derived_from", "version") and not k.startswith("why_")}  # noqa: E731
            same = et is not None and json.dumps(strip(old), sort_keys=True, ensure_ascii=False, default=str) == json.dumps(strip(fresh), sort_keys=True, ensure_ascii=False, default=str)
            rows.append({"book": et.name if et else EMAP, "path": "(整冊重算)", "id": None, "state": "SAME" if same else "REBUILD"})
            if apply and not same:
                base = et or (vdf / f"{EMAP}_v0000.json")
                writes.append(write_next(base, fresh, f"{TAG} derive:由正本 {mt.name} 與各冊尾版重算(前版不覆寫)", {"derived_from": mt.name}).name)
        except Exception as e:  # noqa: BLE001 - 重算失敗照實列,不擋其他衍生冊
            rows.append({"book": EMAP, "path": "(整冊重算)", "id": None, "state": f"ERROR {type(e).__name__}: {str(e)[:120]}"})
    if apply and writes and moved:                                         # 冊出了新版 → 同一輪正本指到新冊名、清掉「待寫回」(下次 unify 不再報 REPOINT)
        nm = copy.deepcopy(m)
        for e in nm["params"]:
            fam = family(e["book"])
            if fam in moved:
                e["book"] = moved[fam]
                e.pop("derive_pending", None)
        writes.append(write_next(mt, nm, f"{TAG} derive:衍生冊已寫回,正本冊名指到新版({', '.join(sorted(moved.values()))})").name)
    diff = [r for r in rows if r["state"] not in ("SAME",)]
    err = [r for r in rows if str(r["state"]).startswith(("ERROR", "BOOK_MISSING"))]
    lamp = "RED" if err else ("GREEN" if not diff or (apply and writes) else "YELLOW")
    return {"master": mt.name, "rows": rows, "written": writes, "lamp": lamp,
            "counts": {s: sum(1 for r in rows if str(r["state"]).startswith(s)) for s in ("SAME", "SET", "ADD", "REBUILD", "CONFLICT_SKIP", "ERROR", "BOOK_MISSING")}}


# ---------------------------------------------------------------- consolidate(只出計畫)
def _norm_hash(fn: ast.AST) -> str:
    body = list(fn.body)
    if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant) and isinstance(body[0].value.value, str):
        body = body[1:]
    return hashlib.sha256("".join(ast.dump(s, annotate_fields=False, include_attributes=False) for s in body).encode()).hexdigest()[:16]


def families(vdf: Path) -> dict:
    out: dict = {}
    for base in (vdf, vdf / "engine"):
        for p in base.glob("VDF_*.py"):
            if "_sha" in p.name.lower():
                continue
            fam = family(p.name) if _vnum(p) >= 0 else p.stem
            out.setdefault(fam, []).append(p)
    return {f: sorted(ps, key=_vnum) for f, ps in out.items()}


def consolidate(vdf: Path, emap: dict | None = None) -> dict:
    fams = families(vdf)
    tails = {f: ps[-1] for f, ps in fams.items()}
    fn_hash: dict = {}
    srcs, rows = {}, []
    for f, t in tails.items():
        try:
            src = t.read_text(encoding="utf-8-sig", errors="replace")
            tree = ast.parse(src)
        except SyntaxError:
            rows.append({"family": f, "tail": t.name, "versions": len(fams[f]), "action": "REVIEW", "evidence": "SyntaxError"})
            continue
        srcs[f] = src
        for n in tree.body:
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and len(n.body) >= 5 and n.name not in ("main", "selftest", "__getattr__"):
                fn_hash.setdefault(_norm_hash(n), set()).add((f, n.name))
    dup_of: dict = {}
    for h, owners in fn_hash.items():
        fs = {o[0] for o in owners}
        if len(fs) >= 2:
            for o in owners:
                dup_of.setdefault(o[0], set()).update(x for x in fs if x != o[0])
    unreadable: list = []
    texts = dict(srcs)                                                    # 引用面:VDF 尾版 .py + VDF 各 JSON 冊尾版(管理器 / 冊常用短碼叫引擎)
    jf: dict = {}
    for j in vdf.rglob("*.json"):
        if "_sha" in j.name.lower() or j.stat().st_size > 5_000_000:
            continue
        k = family(j.name) if _vnum(j) >= 0 else j.stem
        if k in INVENTORY_BOOKS:                                          # 掃全部引擎產生的清冊:列出每一支 ≠ 有人用它(自證循環)
            continue
        if k not in jf or _vnum(j) > _vnum(jf[k]):
            jf[k] = j
    for k, j in jf.items():
        try:
            texts["json:" + k] = j.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            unreadable.append(f"{j.name}: {type(e).__name__}")              # 照實記(OneDrive I/O 等),摘要帶出

    def tokens(f: str) -> set:
        m = re.match(r"(VDF_(?:ENG|MDL)\d+)", f)
        return {f} | ({m.group(1), m.group(1)[4:]} if m else set())

    rx = re.compile(r"(?<![A-Za-z0-9])(VDF_[A-Za-z0-9_]+|ENG\d+|MDL\d+)")
    seen = {}                                                             # 每份文字只掃一次:抽出記號集合(含 VDF_ENGnnn 前綴與短碼)
    for g, txt in texts.items():
        st = set()
        for t in rx.findall(txt):
            st.add(re.sub(r"_v\d{4}$", "", t))
            m = re.match(r"(VDF_(?:ENG|MDL)\d+)", t)
            if m:
                st.update((m.group(1), m.group(1)[4:]))
        seen[g] = st
    refs = {f: sorted(g for g, st in seen.items() if g != f and tokens(f) & st) for f in tails}
    params = {}
    for eng, v in ((emap or {}).get("by_engine") or {}).items():
        names = (v.get("consts") or []) if isinstance(v, dict) else []
        params[family(Path(eng).name)] = {c.get("name") if isinstance(c, dict) else str(c) for c in names} | set((v or {}).get("cli") or [])
    done = {r["family"] for r in rows}
    for f, t in sorted(tails.items()):
        if f in done:
            continue
        dups = sorted(dup_of.get(f, ()))
        ov = sorted(g for g in params if g != f and params.get(f) and len(params[f]) >= 3
                    and len(params[f] & params[g]) / max(1, len(params[f] | params[g])) >= 0.8)
        body = None
        if dups:
            cand = [f] + dups
            body = max(cand, key=lambda x: (len(refs.get(x, [])), len(fams.get(x, [])), x))
        if dups and body != f:
            act = f"MERGE_CANDIDATE → {body}"
        elif not refs[f] and "SystemManager" not in f and not f.startswith(("VDF_MDL013", "VDF_MDL022")):
            act = "DORMANT_CANDIDATE"
        else:
            act = "KEEP"
        rows.append({"family": f, "tail": t.name, "versions": len(fams[f]), "dup_with": dups, "referenced_by": len(refs[f]),
                     "ref_sample": refs[f][:5], "param_overlap": ov, "action": act,
                     "evidence": f"重複函式 {len(dups)} 家 · 被引用 {len(refs[f])} · 參數重疊 {len(ov)}"})
    cnt = {}
    for r in rows:
        k = r["action"].split(" ")[0]
        cnt[k] = cnt.get(k, 0) + 1
    return {"rows": rows, "counts": cnt, "families": len(tails), "unreadable": unreadable,
            "lamp": "YELLOW" if cnt.get("MERGE_CANDIDATE") or cnt.get("DORMANT_CANDIDATE") or unreadable else "GREEN"}


# ---------------------------------------------------------------- DataFrame · 收據 · 運作帳
def frame(rows: list):
    cols = sorted({k for r in rows for k in r}) or ["state"]
    norm = [{c: (json.dumps(r.get(c), ensure_ascii=False, default=str) if not isinstance(r.get(c), (str, type(None))) else r.get(c)) for c in cols} for r in rows]
    try:
        import polars as pl
        return pl.DataFrame(norm, schema={c: pl.Utf8 for c in cols}) if norm else pl.DataFrame(schema={c: pl.Utf8 for c in cols})
    except ImportError:
        try:
            import pandas as pd
            return pd.DataFrame(norm, columns=cols).astype("string")
        except ImportError:
            return None


def save(verb: str, res: dict, out_root: Path) -> Path:
    od = out_root / datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
    od.mkdir(parents=True, exist_ok=True)
    df = frame(res.get("rows", []))
    fmt = "none"
    if df is not None:
        try:
            if hasattr(df, "write_parquet"):
                df.write_parquet(od / f"{verb}.parquet", compression="zstd")
            else:
                df.to_parquet(od / f"{verb}.parquet", compression="zstd", index=False)
            fmt = "parquet"
        except Exception:  # noqa: BLE001 - 沒有 parquet 寫手 → jsonl 退路
            (od / f"{verb}.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False, default=str) + "\n" for r in res.get("rows", [])), encoding="utf-8")
            fmt = "jsonl(退路)"
    summ = {k: v for k, v in res.items() if k != "rows"}
    summ.update(engine=TAG, verb=verb, utc=now_utc(), format=fmt, accel=VIA_ACCEL is not None, net=VIA_NET_TOOL_PATH is not None,
                three={"should": len(res.get("rows", [])), "done": len(res.get("rows", [])), "skipped": []})
    (od / "SUMMARY.json").write_text(json.dumps(summ, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    with (out_root / "RUN_LEDGER.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps({"utc": summ["utc"], "verb": verb, "secs": round(time.time() - _T0, 2), "lamp": res.get("lamp"),
                            "counts": res.get("counts"), "written": res.get("written")}, ensure_ascii=False, default=str) + "\n")
    return od


def fresh_map() -> dict:
    """Engine_Map 一律在新行程重算:同一行程裡 derive 剛寫出的冊新版,前版 build_map 看不到(它在載入時就定了尾版)。"""
    r = subprocess.run([sys.executable, str(Path(__file__).resolve()), "_map-json"], capture_output=True, text=True, encoding="utf-8",
                       env=dict(os.environ, PYTHONUTF8="1"), timeout=600)
    if r.returncode != 0:
        raise RuntimeError(f"_map-json rc {r.returncode}: {r.stderr[-200:]}")
    return json.loads(r.stdout[r.stdout.index("{"):])


def main() -> int:
    a = sys.argv[1:]
    if a[:1] == ["--selftest"]:
        return selftest()
    verb = a[0] if a else ""
    if verb == "_map-json":                                               # 子行程用:新行程重新解析各冊尾版後重算(前版在載入時就定了尾版)
        sys.stdout.write(json.dumps(P.build_map(), ensure_ascii=False, default=str))
        return 0
    if verb not in ("unify", "derive", "consolidate"):
        return P.main()
    apply = "--apply" in a
    out_root = VDF.parent.parent / "VIA_Reports" / "vdf_params"
    say(f"{TAG} {verb}{' --apply' if apply else ''} · VDF {VDF} · 加速器 {'載入' if VIA_ACCEL is not None else '沒載到(黃)'} · 網路工具 {'在' if VIA_NET_TOOL_PATH else '不在'}")
    if apply:
        say("寫前 ssot panorama:" + ssot_panorama(VDF))
    if verb == "unify":
        res = unify(VDF, apply)
    elif verb == "derive":
        res = derive(VDF, apply, map_builder=fresh_map)
    else:
        et = tail_of(VDF, EMAP)
        res = consolidate(VDF, load(et) if et else None)
    if apply and res.get("written"):
        say("寫後 ssot panorama:" + ssot_panorama(VDF))
    od = save(verb, res, out_root)
    say(f"{verb} · {res['lamp']} · " + " · ".join(f"{k} {v}" for k, v in (res.get("counts") or {}).items())
        + (f" · 寫 {res['written']}" if res.get("written") else "") + (f" · {res['note']}" if res.get("note") else ""))
    for r in [r for r in res.get("rows", []) if r.get("state") not in ("SAME", None) or str(r.get("action", "")).startswith(("MERGE", "DORMANT"))][:25]:
        say("  " + " · ".join(str(r.get(k)) for k in ("state", "action", "id", "family", "name", "book_tail", "book", "path", "evidence") if r.get(k) is not None)[:200])
    say(f"DataFrame → {od}")
    return {"GREEN": 0, "YELLOW": 2}.get(res["lamp"], 1)


# ---------------------------------------------------------------- 自測(全在暫存夾造資料)
def selftest() -> int:
    ok, bad = [], []

    def chk(name, cond, note=""):
        (ok if cond else bad).append(name)
        print(("  [OK] " if cond else "  [NG] ") + name + (f" · {note}" if note else ""), flush=True)

    chk("加速器載入(VIA_ACCEL is not None)", VIA_ACCEL is not None)
    chk("網路工具載入(_via_net() is not None · 載入不出網)", _via_net() is not None, str(VIA_NET_TOOL_PATH))
    chk("前版經 glob 載入(v0105)· 別名表照轉接", PRIOR_PATH.name == STEM + "_v0105.py" and UNIFIED_ALIAS == P.UNIFIED_ALIAS)
    with tempfile.TemporaryDirectory() as td:
        vdf = Path(td) / "VDF"
        (vdf / "engine").mkdir(parents=True)
        w = lambda n, o: (vdf / n).write_text(json.dumps(o, ensure_ascii=False), encoding="utf-8")  # noqa: E731
        w("VDF_Unified_Params_v0100.json", {"time": {"start_date": "2022-01-01"}})
        w("VDF_Unified_Params_v0102.json", {"schema": "x", "time": {"start_date": "2018-01-01", "use_current_as_end": True},
                                            "fetch": {"batch_size": 5}, "markets": {"TW": ["^TWII"]}})
        w("VDF_DataPlane_SSOT_v0104.json", {"params": {"protocol": {"a": "tw"}}, "other": [1, 2, 3], "unit": {"仟元": 0.001}, "lanes": 3})
        w("VDF_Param_Registry_v0102.json", {"params": [{"name": "X"}] * 3})
        w("VDF_ParamControl_SSOT_v0103.json", {"version": "v0103", "params": [
            {"id": "VDF-PAR-001", "name": "協定", "book": "VDF_DataPlane_SSOT_v0102.json", "path": "params.protocol", "value": {"a": "tw"}, "class": "輸出參數", "mutable": False},
            {"id": "VDF-PAR-023", "name": "起始日", "book": "VDF_Unified_Params_v0100.json", "path": "time.start_date", "value": "2022-01-01", "class": "時間範圍", "mutable": True},
            {"id": "VDF-PAR-025", "name": "batch", "book": "VDF_Unified_Params_v0100.json", "path": "fetch.batch_size", "value": 5, "class": "輸入參數", "mutable": True},
            {"id": "VDF-PAR-026", "name": "單位", "book": "VDF_DataPlane_SSOT_v0104.json", "path": "unit", "value": {"仟元": 0.001, "(空白)": 1e-06}, "class": "規則", "mutable": False},
            {"id": "VDF-PAR-027", "name": "兩邊都改", "book": "VDF_DataPlane_SSOT_v0104.json", "path": "lanes", "value": 4, "class": "輸入參數", "mutable": True},
            {"id": "VDF-PAR-030", "name": "已拿掉", "book": "VDF_Unified_Params_v0100.json", "path": "output.gone", "value": 1, "class": "輸出參數", "mutable": True}],
            "counts": {"io_params_total": 4}})
        u = unify(vdf)
        st = {r["id"] or r["path"]: r["state"] for r in u["rows"]}
        chk("unify 判態(REPOINT · BOOK_AHEAD · MASTER_AHEAD · CONFLICT · MISSING · NEW)", st.get("VDF-PAR-001") == "REPOINT" and st.get("VDF-PAR-023") == "BOOK_AHEAD"
            and st.get("VDF-PAR-026") == "MASTER_AHEAD" and st.get("VDF-PAR-027") == "CONFLICT"
            and st.get("VDF-PAR-030") == "MISSING" and st.get("time.use_current_as_end") == "NEW" and st.get("markets.TW") == "NEW", str(st))
        chk("unify 只查不寫", not (vdf / "VDF_ParamControl_SSOT_v0104.json").exists())
        u2 = unify(vdf, apply=True)
        nb = load(vdf / "VDF_ParamControl_SSOT_v0104.json") if (vdf / "VDF_ParamControl_SSOT_v0104.json").exists() else {}
        ids = [x["id"] for x in nb.get("params", [])]
        p23 = next((x for x in nb.get("params", []) if x["id"] == "VDF-PAR-023"), {})
        chk("unify --apply:出 v0104 · 前版不動 · 只增", ids[:6] == ["VDF-PAR-001", "VDF-PAR-023", "VDF-PAR-025", "VDF-PAR-026", "VDF-PAR-027", "VDF-PAR-030"] and len(ids) == 8
            and load(vdf / "VDF_ParamControl_SSOT_v0103.json")["version"] == "v0103", str(ids))
        chk("DRIFT 採尾版值 + history;冊名指到尾版", p23.get("value") == "2018-01-01" and p23.get("history", [{}])[0].get("from") == "2022-01-01"
            and p23.get("book") == "VDF_Unified_Params_v0102.json")
        chk("NEW 補登 VDF-PAR-031 起 · MISSING 只標", ids[6:] == ["VDF-PAR-031", "VDF-PAR-032"]
            and any(x.get("missing_in_tail") for x in nb["params"] if x["id"] == "VDF-PAR-030"))
        p26 = next((x for x in nb.get("params", []) if x["id"] == "VDF-PAR-026"), {})
        chk("MASTER_AHEAD 正本值不動(不丟鍵)· CONFLICT 兩邊不動並開 PC", p26.get("value") == {"仟元": 0.001, "(空白)": 1e-06}
            and next(x for x in nb["params"] if x["id"] == "VDF-PAR-027")["value"] == 4 and nb.get("conflicts", [{}])[-1].get("status", "").startswith("OPEN"))
        chk("counts 重算(總數 · 程式常數冊指到尾版)", nb.get("counts", {}).get("io_params_total") == 8 and nb["counts"].get("code_params_book") == "VDF_Param_Registry_v0102.json"
            and nb.get("master") is True and nb.get("why_v0104"))
        u3 = unify(vdf)
        chk("再 unify = 只剩 MASTER_AHEAD(待 derive)· CONFLICT(待裁)· MISSING", u3["counts"]["BOOK_AHEAD"] == 0 and u3["counts"]["NEW"] == 0
            and u3["counts"]["REPOINT"] == 0, str(u3["counts"]))
        d = derive(vdf, map_builder=lambda: {"by_engine": {"e.py": {}}, "gaps": {}})
        chk("derive 查:MASTER_AHEAD 要寫回 · CONFLICT 跳過不寫 · Engine_Map 要重算", d["counts"]["SET"] == 1 and d["counts"]["CONFLICT_SKIP"] == 1
            and d["counts"]["REBUILD"] == 1, str(d["counts"]))
        pc = load(vdf / "VDF_ParamControl_SSOT_v0104.json")
        for x in pc["params"]:
            if x["id"] == "VDF-PAR-025":
                x["value"] = 9
        (vdf / "VDF_ParamControl_SSOT_v0104.json").write_text(json.dumps(pc, ensure_ascii=False), encoding="utf-8")
        d2 = derive(vdf, apply=True, map_builder=lambda: {"by_engine": {"e.py": {}}, "gaps": {}})
        ub = load(vdf / "VDF_Unified_Params_v0103.json") if (vdf / "VDF_Unified_Params_v0103.json").exists() else {}
        chk("derive --apply:正本改值 → 衍生冊新版(只改那條 · derived_from)", ub.get("fetch", {}).get("batch_size") == 9
            and ub.get("time", {}).get("start_date") == "2018-01-01" and ub.get("derived_from") == "VDF_ParamControl_SSOT_v0104.json"
            and load(vdf / "VDF_Unified_Params_v0102.json")["fetch"]["batch_size"] == 5, str(d2.get("written")))
        u4 = unify(vdf)
        chk("derive 後正本指到新冊 · 再 unify 只剩 CONFLICT / MISSING", u4["counts"]["REPOINT"] == 0 and u4["counts"]["MASTER_AHEAD"] == 0
            and u4["counts"]["CONFLICT"] == 1 and u4["counts"]["MISSING"] == 1, str(u4["counts"]))
        chk("Engine_Map 出新版號(不覆寫)", (vdf / "VDF_Param_Engine_Map_v0001.json").exists() or any("Engine_Map" in x for x in d2["written"]), str(d2["written"]))
        chk("沒有殘留暫存檔", not list(vdf.rglob("*.sdd_tmp")))
        body = "def run(x):\n    a = x + 1\n    b = a * 2\n    c = b - 3\n    d = c / 4\n    return d\n"
        (vdf / "engine" / "VDF_ENG900_A_v0100.py").write_text(body + "import json\n", encoding="utf-8")
        (vdf / "engine" / "VDF_ENG900_A_v0101.py").write_text(body, encoding="utf-8")
        (vdf / "engine" / "VDF_ENG901_B_v0100.py").write_text("'''同功能另一支'''\n" + body.replace("def run(x):", "def go(x):\n    '''doc'''"), encoding="utf-8")
        (vdf / "engine" / "VDF_ENG902_C_v0100.py").write_text("X = 'VDF_ENG900_A'\n", encoding="utf-8")
        (vdf / "engine" / "VDF_ENG903_D_v0100.py").write_text("def f():\n    return 1\n", encoding="utf-8")
        (vdf / "VDF_Param_Engine_Map_v0005.json").write_text(json.dumps({"by_engine": {"VDF_ENG903_D_v0100.py": {}}}), encoding="utf-8")
        c = consolidate(vdf)
        act = {r["family"]: r["action"] for r in c["rows"]}
        chk("consolidate:同 AST 異名 → 合併候選指向被引用的本體", act.get("VDF_ENG901_B") == "MERGE_CANDIDATE → VDF_ENG900_A" and act.get("VDF_ENG900_A") == "KEEP", str(act))
        chk("consolidate:全引擎清冊(Engine_Map)列到不算引用 · 沒人引用 → 休眠候選 · 不改任何檔", act.get("VDF_ENG903_D") == "DORMANT_CANDIDATE" and (vdf / "engine" / "VDF_ENG903_D_v0100.py").exists())
        df = frame(c["rows"])
        chk("輸出 DataFrame", df is not None and len(df) == len(c["rows"]))
    print(f"{TAG} selftest {len(ok)}/{len(ok) + len(bad)}" + (" · 不過:" + " · ".join(bad) if bad else ""), flush=True)
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
