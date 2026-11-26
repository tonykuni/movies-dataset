#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""CGC_MDL158_VIAPanoramaAuditRepair v0123 — 薄尾(v0122 以前一字不動):hydra 依桌機實跑修五處

桌機實錄(2026-11-26 VIA_HostBoot v0102 hydra → via_01_vdf · 收據 intake/fastrun-20261126_123649):應掃 1837 · 223 秒 · 確認 3019。
讀戰報(只讀結構):via_01_vdf 幾乎全是副本與凍結件 —— VeritasIntelligenceAnalytics\… 倉副本 958 筆 · system_v0104\ 757 · intake 747 ·
frozen 553;可自動修 156 筆裡 155 筆落在副本 / 凍結 / 收容。三支 COMPILE 也都是副本(倉內正本 compile 過或已不在)。
本版五修(其餘照 v0122):
  ① 區位(zone):每檔分 正本 · 倉副本(目標不在 git 倉裡卻含 VeritasIntelligenceAnalytics\ 子樹)· 副本(runtime_sources)·
     凍結(frozen)· 收容(intake)。分組與 --apply 只對「正本」;其餘照列發現、標區位、一律不寫(CLAUDE.md:凍結來源不改 ·
     一個主工作倉,副本只標記不同步改)。戰報多「各區位發現數」。
  ② --apply 重掃只掃「改過的檔 + 它的下游」(v0122 每修一檔就重掃整夾:1837 檔 × 223 秒 ≈ 數小時);補丁若改到匯入清單 = 還原。
  ③ 同名模組多處(VeritasAegisNexus.py 六份):匯入只連到「最近的那一份」(同夾優先 → 共同路徑最長),不再全連 → 假循環。
  ④ from . import x:找本夾 x.py / x\__init__.py,不再報「匯入 . 找不到」。
  ⑤ ruff 叫不起來(桌機 FileNotFoundError)→ 再試 python -m ruff;都不行照實黃。
只讀程式碼結構;不執行被掃的檔;不出網;不用 TA-Lib;不設同意閘。舊主控台字串門:"read" "slice" "digest" --if-etag def pack_payload。
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

import ast
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import warnings
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL158_VIAPanoramaAuditRepair"
_HYDRA_VER2 = "v0123"
TAG = f"{_STEM} {_HYDRA_VER2}"


def _vnum(path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


_PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location("panorama_prior_for_" + Path(__file__).stem, _PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
VERBS = dict(PRIOR.VERBS)          # 動詞表照前版:"read" "slice" "digest" "pack" "tools" "verbs" … hydra(v0122)
VERBS["hydra"] = (PRIOR.VERBS["hydra"][0], PRIOR.VERBS["hydra"][1],
                  PRIOR.VERBS["hydra"][2] + ";v0123:分區位(正本 / 倉副本 / 副本 / 凍結 / 收容,只修正本)· 只重掃改過的檔與下游")


def __getattr__(name: str):
    return getattr(PRIOR, name)


def pack_payload(root, limit: int = 200) -> dict:
    """整夾索引:原樣轉交前版鏈(明寫在本檔,讓只認字串的舊門也看得到)。"""
    return PRIOR.pack_payload(root, limit)


# ---------------------------------------------------------------- ③④ 匯入解析:最近的一份 · from . import x
_ORIG_RESOLVE = PRIOR._resolve_local


def _nearest(cands: set, f: Path) -> set:
    if len(cands) <= 1:
        return set(cands)
    same = {c for c in cands if c.parent == f.parent}
    if same:
        return {sorted(same, key=str)[0]}

    def common(c):
        n = 0
        for a, b in zip(c.parts, f.parts):
            if a != b:
                break
            n += 1
        return n
    best = max(common(c) for c in cands)
    return {sorted((c for c in cands if common(c) == best), key=str)[0]}


def _resolve_local(name: str, f: Path, idx: dict) -> set:
    return _nearest(_ORIG_RESOLVE(name, f, idx), f)


def _imports(tree, f: Path) -> list:
    out = PRIOR._imports_v0122(tree, f)
    for n in ast.walk(tree):                                   # from . import x / from .. import y:子模組也是候選
        if isinstance(n, ast.ImportFrom) and n.level and not n.module:
            for a in n.names:
                out.append((("." * n.level) + a.name, n.lineno, n, True))
    return out


def pass1(rel, src, tree, err, imports, guard, idx, f):
    found = PRIOR._pass1_v0122(rel, src, tree, err, imports, guard, idx, f)
    keep = []
    for x in found:
        if x["cls"] == "UNRESOLVED" and tree is not None:
            m = re.match(r"匯入 (\.+) 找不到$", x["detail"])
            if m:
                lvl = len(m.group(1))
                names = [a.name for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.level == lvl and not n.module
                         and n.lineno == x["line"] for a in n.names]
                if names and all(_ORIG_RESOLVE(m.group(1) + nm, f, idx) for nm in names):
                    continue                                    # from . import x:x 在本夾 → 不是缺
        keep.append(x)
    return keep


# ---------------------------------------------------------------- ⑤ ruff:再試 python -m ruff
def ruff_undef(files: list, roots: list) -> tuple:
    res, state = PRIOR._ruff_undef_v0122(files, roots)
    if not state.startswith("黃") or not files:
        return res, state
    if importlib.util.find_spec("ruff") is None:
        return res, state + " · python -m ruff 也沒有(可經 VCGC 安裝閘補 ruff)"
    out = {}
    for i in range(0, len(files), 400):
        chunk = [str(f) for f in files[i:i + 400]]
        try:
            cp = subprocess.run([sys.executable, "-m", "ruff", "check", "--isolated", "--no-cache", "--select", "F821", "--output-format", "json", *chunk],
                                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
            rows = json.loads(cp.stdout or "[]")
        except (OSError, ValueError, subprocess.TimeoutExpired) as e:
            return {}, f"黃 · python -m ruff 也跑不起來({type(e).__name__});UNDEF 略過"
        for r in rows:
            m = re.search(r"`([^`]+)`", r.get("message", ""))
            out.setdefault(PRIOR._rel(Path(r["filename"]).resolve(), roots), []).append((r["location"]["row"], m.group(1) if m else "?"))
    return out, "python -m ruff F821"


# 裝進 v0122 模組全域(panorama / apply 內部呼叫的名字走本版)
PRIOR._imports_v0122, PRIOR._pass1_v0122, PRIOR._ruff_undef_v0122 = PRIOR._imports, PRIOR.pass1, PRIOR.ruff_undef
PRIOR._resolve_local, PRIOR._imports, PRIOR.pass1, PRIOR.ruff_undef = _resolve_local, _imports, pass1, ruff_undef


# ---------------------------------------------------------------- ① 區位
ZONES = ("正本", "倉副本", "副本", "凍結", "收容")


def _in_git(p: Path) -> bool:
    for q in [p, *p.parents]:
        if (q / ".git").exists():
            return True
    return False


def zone_of(rel: str, root_in_git: bool) -> str:
    parts = rel.split("/")[:-1]
    low = [x.lower() for x in parts]
    if any("intake" in x for x in low):
        return "收容"
    if "frozen" in low:
        return "凍結"
    if "runtime_sources" in low:
        return "副本"
    if not root_in_git and "VeritasIntelligenceAnalytics" in parts:
        return "倉副本"
    return "正本"


def panorama(targets: list, workers: int = 0) -> dict:
    pan = PRIOR._panorama_v0122(targets, workers)
    in_git = any(_in_git(Path(r)) for r in pan["roots"])
    zf = {rel: zone_of(rel, in_git) for rel in pan["_files"]}
    by_zone = {z: 0 for z in ZONES}
    for x in pan["findings"]:
        x["zone"] = zf.get(x["file"], "正本")
        by_zone[x["zone"]] += 1
        if x["zone"] != "正本":
            x["mode"] = f"不寫({x['zone']})"
            if x["fix"] == "auto":
                x["fix"] = "skip"
    pan["groups"] = {"A": [r for r in pan["groups"]["A"] if zf.get(r) == "正本"],
                     "B": [r for r in pan["groups"]["B"] if zf.get(r) == "正本"],
                     "不寫": sorted({x["file"] for x in pan["findings"] if x["zone"] != "正本"})}
    pan["zones"] = by_zone
    pan["zone_files"] = {z: sum(1 for v in zf.values() if v == z) for z in ZONES}
    pan["cycles"] = [c for c in pan["cycles"] if all(zf.get(x) == "正本" for x in c)] + \
                    [c for c in pan["cycles"] if not all(zf.get(x) == "正本" for x in c)]
    return pan


PRIOR._panorama_v0122 = PRIOR.panorama
PRIOR.panorama = panorama


# ---------------------------------------------------------------- ② --apply:只重掃改過的檔與下游
def rescan(pan: dict, rels: list) -> list:
    """只重掃指定的檔(同一份模組索引;UNDEF 只對這幾檔叫 ruff)。"""
    roots = [Path(r) for r in pan["roots"]]
    files = [Path(pan["_files"][r]) for r in rels if r in pan["_files"]]
    allf = [Path(p) for p in pan["_files"].values()]
    idx = PRIOR.module_index(allf, roots)
    undef, _st = ruff_undef(files, roots)
    defs_cache = {}

    def defs_of(p: Path) -> dict:
        if p not in defs_cache:
            try:
                t = ast.parse(PRIOR._read(p)[0])
                defs_cache[p] = {n.name: n for n in t.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
            except (SyntaxError, OSError, ValueError):
                defs_cache[p] = {}
        return defs_cache[p]

    out = []
    for f in files:
        rel = PRIOR._rel(f, roots)
        src, bom = PRIOR._read(f)
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                tree, err = ast.parse(src), None
        except SyntaxError as e:
            tree, err = None, e
        imps = _imports(tree, f) if tree is not None else []
        out += pass1(rel, src, tree, err, imps, PRIOR._in_import_guard(tree) if tree is not None else set(), idx, f)
        if tree is not None:
            bound = PRIOR._bound_names(tree)
            out += [PRIOR._finding(rel, "UNDEF", ln, f"未定義名 {nm}", "雙判(ruff F821 + 本模組沒有綁定)") for ln, nm in undef.get(rel, []) if nm not in bound]
            mine = defs_of(f)
            imported = {}
            for n in ast.walk(tree):
                if isinstance(n, ast.ImportFrom):
                    tgt = _resolve_local(("." * n.level) + (n.module or ""), f, idx)
                    if len(tgt) == 1:
                        d = defs_of(next(iter(tgt)))
                        for a in n.names:
                            if a.name in d:
                                imported[a.asname or a.name] = d[a.name]
            single = {k: v for k, v in mine.items() if sum(1 for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == k) == 1}
            out += PRIOR.pass2(rel, tree, single, imported) + PRIOR.pass3(rel, src, tree)
        if bom:
            out.append(PRIOR._finding(rel, "BOM", 1, "檔頭帶 UTF-8 BOM(原始碼本身)", "雙判(位元組 EF BB BF + decode)", fix="manual"))
    return out


def _import_sig(src: str) -> list:
    try:
        t = ast.parse(src)
    except SyntaxError:
        return ["<syntax>"]
    return sorted(ast.dump(n) for n in ast.walk(t) if isinstance(n, (ast.Import, ast.ImportFrom)))


def apply(pan: dict, targets: list, workers: int = 0) -> dict:
    files = pan["_files"]
    by = {}
    for x in pan["findings"]:
        if x["fix"] == "auto" and x.get("zone", "正本") == "正本":
            by.setdefault(x["file"], []).append(x)
    backup = Path(tempfile.mkdtemp(prefix="VIA_hydra_bak_"))
    keys = PRIOR._keys

    def one(rel: str, dependents: list) -> dict:
        p = Path(files[rel])
        why = PRIOR._exempt(p)
        if why:
            return {"file": rel, "state": "SKIP", "why": why, "fixed": []}
        orig = p.read_bytes()
        bak = backup / hashlib.sha256(str(p).encode()).hexdigest()[:16]
        bak.write_bytes(orig)
        src, bom = PRIOR._read(p)
        new = PRIOR.patch_source(src, by[rel])
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                ast.parse(new)
                compile(new, rel, "exec")
        except SyntaxError as e:
            return {"file": rel, "state": "ROLLBACK", "why": f"補丁後語法不過(行 {e.lineno}),沒寫檔", "fixed": []}
        if _import_sig(new) != _import_sig(src):
            return {"file": rel, "state": "ROLLBACK", "why": "補丁改到匯入清單(不准),沒寫檔", "fixed": []}
        tmp = p.with_name(p.name + ".hydra_tmp")
        tmp.write_bytes((("﻿" if bom else "") + new).encode("utf-8"))
        os.replace(tmp, p)
        scope = [rel, *[d for d in dependents if d in files]]
        before = {k for k in keys(pan["findings"]) if k[0] in set(scope)}
        after = keys(rescan(pan, scope))
        new_keys = after - before
        if new_keys:
            tmp2 = p.with_name(p.name + ".hydra_rb")
            tmp2.write_bytes(bak.read_bytes())
            os.replace(tmp2, p)
            return {"file": rel, "state": "ROLLBACK", "why": f"重掃多出 {len(new_keys)} 筆新發現:{sorted(new_keys)[:2]}", "fixed": []}
        done = [x["id"] for x in by[rel] if (x["file"], x["cls"], x["line"], x["detail"]) not in after]
        return {"file": rel, "state": "PASS", "fixed": done, "rescanned": len(scope)}

    a_files = [r for r in pan["groups"]["A"] if r in by]
    b_files = [r for r in pan["groups"]["B"] if r in by]
    res = []
    with ThreadPoolExecutor(max_workers=max(1, min(len(a_files) or 1, workers or PRIOR.accel_workers(8)[0]))) as ex:
        res += list(ex.map(lambda r: dict(one(r, []), mode="並行批次"), a_files))
    for i, r in enumerate(b_files, 1):
        res.append(dict(one(r, pan["_redges"].get(r, [])), mode=f"序列第 {i} 步"))
    return {"results": res, "backup": str(backup)}


PRIOR._apply_v0122 = PRIOR.apply
PRIOR.apply = apply


def report(before, fix, after) -> dict:
    rep = PRIOR._report_v0122(before, fix, after)
    rep["zones"] = before.get("zones", {})
    rep["zone_files"] = before.get("zone_files", {})
    rep["auto_fixable"] = sum(1 for x in before["findings"] if x["fix"] == "auto")
    rep["groups"]["不寫"] = len(before["groups"].get("不寫", []))
    return rep


PRIOR._report_v0122 = PRIOR.report
PRIOR.report = report


def hydra(argv: list) -> int:
    _LAST.clear()
    return PRIOR.hydra(argv)


def _print_zones_hook():
    import builtins
    keep = builtins.print

    def pr(*a, **k):
        s = " ".join(str(x) for x in a)
        keep(*a, **k)
        if s.startswith("  ② 依賴圖") and _LAST.get("zones"):
            z = _LAST["zones"]
            keep(f"  ①b 區位(只修正本):檔 {_LAST['zone_files']} · 發現 {z} → 副本 / 凍結 / 收容 照列不寫")
    return pr


_LAST = {}
_P_PAN = PRIOR.panorama


def _pan_rec(targets, workers=0):
    p = _P_PAN(targets, workers)
    if not _LAST:                                    # 橫幅印「修前」的區位數(修後那一輪不覆蓋)
        _LAST.update(zones=p["zones"], zone_files=p["zone_files"])
    return p


PRIOR.panorama = _pan_rec
PRIOR.print = _print_zones_hook()
_TAG_V0122 = PRIOR.TAG
PRIOR.TAG = TAG                  # 戰報 / 橫幅照實寫跑的是哪一版


# ---------------------------------------------------------------- 入口
def print_verbs() -> int:
    e = '$E'
    print(f"[{TAG} 動詞表] {len(VERBS)} 個 · {e} = 鎖冊 token 那一支")
    for k, (use, when, what) in VERBS.items():
        print(f"  {k:<10} python3 \"{e}\" {use}")
        print(f"             何時:{when} · 做什麼:{what}")
    return 0


def main() -> int:
    argv = sys.argv[1:]
    if argv == ["--selftest"]:
        return selftest()
    if argv[:1] == ["verbs"]:
        return print_verbs()
    if argv[:1] == ["hydra"]:
        return hydra(argv[1:])
    return PRIOR.main()


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f" · {str(note)[:300]}" if note and not cond else ""), flush=True)

    chk("① 加速器真的載到(VIA_ACCEL is not None)", VIA_ACCEL is not None)
    with tempfile.TemporaryDirectory() as td:
        d = Path(td) / "via_01_vdf"
        files = {
            "live/a.py": "import helper\n\n\ndef r(p):\n    return open(p).read()\n",
            "live/helper.py": "X = 1\n",
            "live/pkg/m.py": "from . import sib\n",
            "live/pkg/sib.py": "Y = 2\n",
            "VeritasIntelligenceAnalytics/supportive modules/Nexus.py": "import Nexus\n",
            "system_v0104/runtime_sources/x/Nexus.py": "import Nexus\nopen('a').read()\n",
            "system_v0104/frozen/y/Nexus.py": "import Nexus\nopen('b').read()\n",
            "system_v0104/frozen/references/intake/z.py": "open('c').read()\n",
        }
        for k, v in files.items():
            (d / k).parent.mkdir(parents=True, exist_ok=True)
            (d / k).write_text(v, encoding="utf-8")
        pan = panorama([str(d)], 2)
        z = {x["file"]: x["zone"] for x in pan["findings"]}
        chk("② 區位:倉副本 · 副本(runtime_sources)· 凍結 · 收容 · 正本 各歸各位",
            z.get("system_v0104/runtime_sources/x/Nexus.py") == "副本" and z.get("system_v0104/frozen/y/Nexus.py") == "凍結"
            and z.get("system_v0104/frozen/references/intake/z.py") == "收容" and z.get("live/a.py") == "正本", z)
        chk("③ 同名模組多份:只連最近那份 → 不再出假循環(三份 Nexus 各自只連到自己)",
            not any(len(c) > 1 for c in pan["cycles"]), pan["cycles"])
        chk("④ from . import sib:本夾有 sib.py → 不報 UNRESOLVED",
            not any(x["cls"] == "UNRESOLVED" and x["file"] == "live/pkg/m.py" for x in pan["findings"]), [x for x in pan["findings"] if x["cls"] == "UNRESOLVED"])
        chk("⑤ 分組與自動修只含正本;副本 / 凍結 / 收容的 ENCODING 標 skip、列「不寫」",
            set(pan["groups"]["A"] + pan["groups"]["B"]) <= {"live/a.py", "live/helper.py", "live/pkg/m.py", "live/pkg/sib.py"}
            and all(x["fix"] != "auto" for x in pan["findings"] if x["zone"] != "正本")
            and "system_v0104/frozen/y/Nexus.py" in pan["groups"]["不寫"], pan["groups"])
        h0 = {k: hashlib.sha256((d / k).read_bytes()).hexdigest() for k in files}
        import time as _t
        t0 = _t.time()
        calls = {"n": 0}
        keep = PRIOR._panorama_v0122

        def counting(*a, **k):
            calls["n"] += 1
            return keep(*a, **k)
        PRIOR._panorama_v0122 = counting
        try:
            fx = apply(pan, [str(d)], 2)
        finally:
            PRIOR._panorama_v0122 = keep
        h1 = {k: hashlib.sha256((d / k).read_bytes()).hexdigest() for k in files}
        changed = sorted(k for k in files if h0[k] != h1[k])
        chk("⑥ --apply 只改正本(live/a.py 插 encoding);副本 / 凍結 / 收容位元不變",
            changed == ["live/a.py"] and 'open(p, encoding="utf-8-sig")' in (d / "live/a.py").read_text(encoding="utf-8"), [changed, fx["results"]])
        chk("⑦ 修補只重掃改過的檔與下游:不再整夾重跑全景(呼叫 0 次)", calls["n"] == 0 and all(r.get("rescanned", 1) >= 1 for r in fx["results"]),
            [calls, _t.time() - t0])
        (d / "live/b.py").write_text("import helper\nopen('q').read()\n", encoding="utf-8")
        pan2 = panorama([str(d)], 2)
        keep_p = PRIOR.patch_source
        PRIOR.patch_source = lambda src, fixes: "import os\n" + src
        try:
            fx2 = apply(pan2, [str(d)], 2)
        finally:
            PRIOR.patch_source = keep_p
        r2 = [r for r in fx2["results"] if r["file"] == "live/b.py"]
        chk("⑧ 補丁改到匯入清單 → ROLLBACK 不寫", r2 and r2[0]["state"] == "ROLLBACK" and (d / "live/b.py").read_text(encoding="utf-8").startswith("import helper"), r2)
        out = Path(td) / "rep.json"
        rc = PRIOR.hydra([str(d), "--out", str(out), "--max", "2"])
        rep = json.loads(out.read_bytes().decode("utf-8"))["report"]
        chk("⑨ 戰報多 zones / zone_files · 可自動修只算正本", set(rep.get("zones", {})) == set(ZONES) and rep["auto_fixable"] >= 1 and rc in (0, 1, 2), rep.get("zones"))
    chk("⑩ VERBS 前版全在(含 hydra)", set(PRIOR.VERBS) <= set(VERBS))
    import contextlib
    import io
    buf = io.StringIO()
    keep_install = (PRIOR._resolve_local, PRIOR._imports, PRIOR.pass1, PRIOR.ruff_undef, PRIOR.panorama, PRIOR.apply, PRIOR.report, PRIOR.print)
    PRIOR._resolve_local, PRIOR._imports, PRIOR.pass1, PRIOR.ruff_undef = _ORIG_RESOLVE, PRIOR._imports_v0122, PRIOR._pass1_v0122, PRIOR._ruff_undef_v0122
    PRIOR.panorama, PRIOR.report = PRIOR._panorama_v0122, PRIOR._report_v0122
    PRIOR.TAG = _TAG_V0122
    try:
        del PRIOR.print
    except AttributeError:
        pass
    PRIOR.apply = PRIOR._apply_v0122
    try:
        with contextlib.redirect_stdout(buf):
            rc_p = PRIOR.selftest()
    finally:
        (PRIOR._resolve_local, PRIOR._imports, PRIOR.pass1, PRIOR.ruff_undef, PRIOR.panorama, PRIOR.apply, PRIOR.report, PRIOR.print) = keep_install
        PRIOR.TAG = TAG
    tail = [ln for ln in buf.getvalue().splitlines() if ln.strip()][-1:] or [""]
    chk("⑪ 前版 v0122 自測(本版換裝卸下)照過", rc_p == 0, tail[0][:200])
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑫ 檔面:第 3 行加速器標記 · glob 取前版 · 零 TA-Lib · 不設同意閘 · 字串門字樣在",
        src.splitlines()[2].startswith("# [VIA:ACCEL-BRIDGE") and "HERE.glob(_STEM" in src
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M)
        and not re.search(r"^\s*os\.environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", src, re.M)
        and all(w in src for w in ('"read"', '"slice"', '"digest"', "--if-etag", "def pack_payload")))
    print(f"[計] {TAG} 本版 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 2



if __name__ == "__main__":
    raise SystemExit(main())
