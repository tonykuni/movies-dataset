#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VCGC_CommandHub_v0104.py — 薄尾(v0103 以前一字不動):程式碼點名的舊版 → 先遷移引用 → 再退役

操作員 2026-11-23:「那 103 支程式碼點名的也遷移引用後退役」。
v0103 把「有程式碼點名」(CODE_REF)一律留著。本版用語法樹把點名分成兩種:
  CODE_DEAD  點名已不會執行 —— 點名的檔本身也是死版 / 只在 docstring 或註解 / 點名所在的頂層函式已被同家族較新的活版蓋掉
             → 照 v0103 流程(先標退役 → 證明 → 搬),證明時另把「點名它的活檔」也逐支載入
  CODE_LIVE  點名仍會執行 → 先遷移引用:
             · 點名者是家族尾版 → 出新版號(整檔複本,把舊檔名換成目標家族現役尾版的檔名)
             · 點名者沒有版號(測試 / 啟動腳本)→ 原地改(git 有歷史)
             · 點名者是鏈中段(被尾版載入、函式沒被蓋)或 .ps1 → 不自動改,列清單(PS 既有檔不改;中段要另出尾版覆寫)
             改寫一律先在 TEMP:ast.parse + compile 過 → 點名者 --selftest 改前改後同 rc(沒有自測的只做載入)→ 才落檔
             遷移後舊點名者變成死版(新版是整檔、不連前版)→ 下一輪 prune 一起退
新動詞:migrate [--apply] [--system S](預設乾跑)· prune 預設類別加 CODE_DEAD。其餘照 v0103。| --selftest
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
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import ast
import collections
import contextlib
import importlib.util
import io
import json
import re
import shutil
import subprocess
import sys
import tempfile
import tokenize
from datetime import datetime, timezone
from pathlib import Path

VERSION = "v0104"
FAMILY = "VCGC_CommandHub"
HERE = Path(__file__).resolve().parent


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(FAMILY + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
P2 = PRIOR.PRIOR                      # v0102(prune_scan / cmd_prune 在這)


def __getattr__(name):
    return getattr(PRIOR, name)


CODE_ROOT = PRIOR.CODE_ROOT
_TAIL_RX = re.compile(r"(.+)_v(\d{4})\.py$")


# ------------------------------------------------------------------------------
# 點名是否仍會執行(語法樹)
# ------------------------------------------------------------------------------
class FamilyIndex:
    def __init__(self, via: Path):
        self.via = via
        self.link = P2._load_token_link(via)
        files = subprocess.run(["git", "-C", str(via), "ls-files", "*.py"], capture_output=True, text=True).stdout.splitlines()
        self.fam: dict[tuple, dict[int, Path]] = collections.defaultdict(dict)
        for f in files:
            if P2._FROZEN.search(f):
                continue
            m = _TAIL_RX.match(Path(f).name)
            if m:
                self.fam[(str(Path(f).parent), m.group(1))][int(m.group(2))] = via / f
        self._live: dict = {}

    def status(self, rel: str):
        """回 (TAIL | MIDDLE | DEAD | UNVER | GONE, 家族鍵, 版號)。"""
        m = _TAIL_RX.match(Path(rel).name)
        if not m:
            return ("UNVER", None, None) if (self.via / rel).is_file() else ("GONE", None, None)
        key = (str(Path(rel).parent), m.group(1))
        vs = self.fam.get(key)
        v = int(m.group(2))
        if not vs or v not in vs:
            return "GONE", key, v
        if key not in self._live:
            self._live[key] = PRIOR.live_versions(m.group(1), vs, self.link)
        if v == max(vs):
            return "TAIL", key, v
        return ("MIDDLE" if v in self._live[key] else "DEAD"), key, v

    def newer_defs(self, key, v) -> set:
        out = set()
        for w in self._live.get(key, set()):
            if w > v:
                out |= top_names(self.fam[key][w])
        return out


def top_names(p: Path) -> set:
    try:
        t = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return set()
    out = {n.name for n in t.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
    out |= {x.id for n in t.body if isinstance(n, ast.Assign) for x in n.targets if isinstance(x, ast.Name)}
    return out


def code_owners(src: str, name: str) -> list:
    """name 出現在哪些頂層定義的「程式字串」裡(docstring / 註解不算);模組層字串回 None。"""
    tree = ast.parse(src)
    doc = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.body \
                and isinstance(n.body[0], ast.Expr) and isinstance(getattr(n.body[0], "value", None), ast.Constant):
            doc.add(id(n.body[0].value))
    out = []
    for top in tree.body:
        owner = top.name if isinstance(top, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) else (
            top.targets[0].id if isinstance(top, ast.Assign) and isinstance(top.targets[0], ast.Name) else None)
        for n in ast.walk(top):
            if isinstance(n, ast.Constant) and isinstance(n.value, str) and name in n.value and id(n) not in doc:
                out.append(owner)
    return out


def effective_refs(idx: FamilyIndex, name: str, referrers: list[str]) -> list[tuple[str, str]]:
    """回仍會執行的 (身分, 點名檔)。身分 = TAIL / MIDDLE / UNVER / PS。"""
    eff = []
    for f in referrers:
        if P2._FROZEN.search(f):
            continue
        if f.endswith((".ps1", ".psm1")):
            eff.append(("PS", f))
            continue
        if not f.endswith(".py"):
            continue
        st, key, v = idx.status(f)
        if st in ("DEAD", "GONE"):
            continue
        try:
            owners = code_owners((idx.via / f).read_text(encoding="utf-8", errors="replace"), name)
        except SyntaxError:
            owners = [None]
        if not owners:
            continue
        if st == "MIDDLE":
            newer = idx.newer_defs(key, v)
            if all(o is not None and o in newer for o in owners):
                continue
        eff.append((st, f))
    return eff


_V0102_SCAN = P2.prune_scan


def prune_scan(via: Path, systems: list[str] | None = None) -> dict:
    """v0102 掃描 + CODE_REF 細分 CODE_DEAD / CODE_LIVE(帶 effective 清單)。"""
    rep = _V0102_SCAN(via, systems)
    if "error" in rep:
        return rep
    code = [x for x in rep["dead"] if x["kind"] == "CODE_REF"]
    if code:
        idx = FamilyIndex(via)
        refs = P2.name_refs(via, {Path(x["path"]).name for x in code})
        by = collections.Counter(rep["by_kind"])
        for x in code:
            eff = effective_refs(idx, Path(x["path"]).name, sorted(refs.get(Path(x["path"]).name, set())))
            x["kind"] = "CODE_LIVE" if eff else "CODE_DEAD"
            x["effective"] = [{"as": a, "file": f} for a, f in eff]
            x["referrers"] = sorted(f for f in refs.get(Path(x["path"]).name, set()) if f.endswith(".py") and not P2._FROZEN.search(f))
            by["CODE_REF"] -= 1
            by[x["kind"]] += 1
        rep["by_kind"] = {k: v for k, v in by.items() if v}
    return rep


P2.prune_scan = prune_scan

# 證明時把「點名候選的活檔」也逐支載入(v0103 證完後,同一批在新 worktree 再比點名者前後)
_V0103_PROVE = PRIOR.prune_prove


def prune_prove(via: Path, cands: list[dict], log=print, lanes: int = 4, rounds: int = 3) -> dict:
    res = _V0103_PROVE(via, cands, log=log, lanes=lanes, rounds=rounds)
    proven = res.get("proven") or []
    refs = sorted({f for x in proven for f in x.get("referrers", []) if (via / f).is_file()} - {x["path"] for x in proven})
    if not proven or not refs:
        return res
    top = Path(subprocess.run(["git", "-C", str(via), "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip())
    sub = via.resolve().relative_to(top.resolve())
    tmp = Path(tempfile.mkdtemp(prefix="via_prune_refs_"))
    wt = tmp / "wt"
    subprocess.run(["git", "-C", str(top), "worktree", "add", "-q", "--detach", str(wt), "HEAD"], check=True, capture_output=True)
    try:
        wvia = wt / sub
        before = {f: PRIOR._probe(wvia, f, False) for f in refs}
        rel = [str(sub / x["path"]) for x in proven]
        for i in range(0, len(rel), 200):
            subprocess.run(["git", "-C", str(wt), "rm", "-q", "--", *rel[i:i + 200]], check=True, capture_output=True)
        PRIOR.retire_mark(wvia, [x["path"] for x in proven], apply=True)
        after = {f: PRIOR._probe(wvia, f, False) for f in refs}
    finally:
        subprocess.run(["git", "-C", str(top), "worktree", "remove", "--force", str(wt)], capture_output=True)
        shutil.rmtree(tmp, ignore_errors=True)
    broken = [f for f in refs if before[f][0] == 0 and after[f][0] != 0]
    drop = {x["path"] for x in proven if set(x.get("referrers", [])) & set(broken)}
    log(f"[prove] 點名候選的活檔 {len(refs)} 支前後載入:變壞 {len(broken)}" + (f" → 剔除它們點名的 {len(drop)} 支" if drop else ""))
    for f in broken[:10]:
        log(f"  [FAIL] {f} · 前 rc {before[f][0]} · 後 rc {after[f][0]}")
    res["proven"] = [x for x in proven if x["path"] not in drop]
    res["referrer_probe"] = {"checked": len(refs), "broken": broken}
    return res


PRIOR.prune_prove = prune_prove
P2.prune_prove = prune_prove


# ------------------------------------------------------------------------------
# 新檔登記(只登本批):編號冊走 MDL237 --apply --scope;中央元件冊走引擎 TEMP 同步、只帶本批新列
# ------------------------------------------------------------------------------
def register_new(via: Path, paths: list[str], log=print) -> dict:
    out: dict = {}
    V = PRIOR.find_tail("CGC_MDL149_VeritasCentralGovernanceConsole", [via])
    if V:
        r = PRIOR.PRIOR._job([sys.executable, str(V), "run", "CGC_MDL237_NumberingSystem", "--apply", "--scope", *paths], via, 1800)
        line = next((l for l in r["out"].splitlines() if "只登本批" in l), "")
        aud = next((l for l in r["out"].splitlines() if "編號只增稽核" in l), "")
        out["numbering"] = {"rc": r["rc"], "line": line.strip(), "audit": aud.strip()}
        log(f"[register] 編號冊:{line.strip() or r['rc']} | {aud.strip()}")
    synced_path, eng = PRIOR.engine_component_sync(via)
    if synced_path is None:
        out["component"] = {"error": eng.get("error")}
        return out
    try:
        book = via / PRIOR.COMPONENT_BOOK
        want = set(paths)
        with PRIOR.file_lock(book):
            real = json.loads(book.read_text(encoding="utf-8"))
            synced = json.loads(synced_path.read_text(encoding="utf-8"))
            have = {r.get("key") for r in real.get("records", [])}
            used = {r.get("code") for r in real.get("records", [])}
            add = [r for r in synced.get("records", []) if r.get("key") not in have and r.get("source") in want and r.get("code") not in used]
            if add:
                real["records"] = sorted(real.get("records", []) + add, key=lambda r: r.get("code", ""))
                cnt = dict(real.get("counters") or {})
                for k, v in (synced.get("counters") or {}).items():
                    cnt[k] = max(int(cnt.get(k, 0)), int(v))
                real["counters"] = cnt
                real["updated_at"] = datetime.now().isoformat(timespec="seconds")
                PRIOR.atomic_write_bytes(book, (json.dumps(real, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))
        out["component"] = {"added": len(add)}
        log(f"[register] 中央元件冊:本批新列 {len(add)}(引擎算出的其他新列 {eng.get('new')} 不帶)")
    finally:
        shutil.rmtree(synced_path.parent, ignore_errors=True)
    return out


# ------------------------------------------------------------------------------
# migrate:CODE_LIVE 的點名改指目標家族現役尾版
# ------------------------------------------------------------------------------
def _tail_of(via: Path, rel: str) -> Path | None:
    m = _TAIL_RX.match(Path(rel).name)
    if not m:
        return None
    vs = sorted((via / Path(rel).parent).glob(m.group(1) + "_v*.py"), key=_vnum)
    return vs[-1] if vs else None


def _next_version_path(p: Path) -> Path:
    m = _TAIL_RX.match(p.name)
    vs = sorted(p.parent.glob(m.group(1) + "_v*.py"), key=_vnum)
    return p.parent / f"{m.group(1)}_v{_vnum(vs[-1]) + 1:04d}.py"


def _has_selftest(src: str) -> bool:
    return "--selftest" in src


def _run_check(root: Path, rel: str, selftest: bool) -> tuple[int, str]:
    return PRIOR._probe(root, rel, selftest)


def plan_migrations(via: Path, rep: dict) -> dict:
    jobs: dict[str, dict] = {}
    held = []
    for x in rep["dead"]:
        if x["kind"] != "CODE_LIVE":
            continue
        tail = _tail_of(via, x["path"])
        old, new = Path(x["path"]).name, (tail.name if tail else None)
        if not new or new == old:
            held.append({"target": x["path"], "why": "目標家族找不到現役尾版"})
            continue
        for e in x["effective"]:
            if e["as"] in ("PS", "MIDDLE"):
                held.append({"target": x["path"], "referrer": e["file"], "why": {"PS": "PS 既有檔不改(另出 PS 新版或改走 Python 入口)",
                                                                                 "MIDDLE": "點名在鏈中段未被覆寫的函式,要另出尾版覆寫"}[e["as"]]})
                continue
            j = jobs.setdefault(e["file"], {"referrer": e["file"], "as": e["as"], "swaps": {}})
            j["swaps"][old] = new
    blocked_targets = {h["target"] for h in held}
    return {"jobs": list(jobs.values()), "held": held, "blocked_targets": sorted(blocked_targets)}


def migrate_one(via: Path, job: dict, apply: bool, log=print) -> dict:
    src_p = via / job["referrer"]
    text = src_p.read_text(encoding="utf-8")
    new_text = text
    for old, new in job["swaps"].items():
        new_text = re.sub(r"(?<![A-Za-z0-9_\-])" + re.escape(old), new, new_text)
    if new_text == text:
        return {"referrer": job["referrer"], "ok": False, "why": "沒有可換的字串"}
    if job["as"] == "TAIL":
        dst = _next_version_path(src_p)
    else:
        dst = src_p
    # TEMP 驗:ast + compile
    try:
        ast.parse(new_text)
        compile(new_text, str(dst), "exec")
    except SyntaxError as e:
        return {"referrer": job["referrer"], "ok": False, "why": f"語法 / 編譯不過:{e}"}
    rel_dst = str(dst.relative_to(via))
    st = _has_selftest(text)
    before = _run_check(via, job["referrer"], st)
    tmp = Path(tempfile.mkdtemp(prefix="via_migrate_"))
    try:
        top = Path(subprocess.run(["git", "-C", str(via), "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip())
        sub = via.resolve().relative_to(top.resolve())
        wt = tmp / "wt"
        subprocess.run(["git", "-C", str(top), "worktree", "add", "-q", "--detach", str(wt), "HEAD"], check=True, capture_output=True)
        try:
            wvia = wt / sub
            (wvia / rel_dst).parent.mkdir(parents=True, exist_ok=True)
            (wvia / rel_dst).write_text(new_text, encoding="utf-8")
            after = _run_check(wvia, rel_dst, st)
        finally:
            subprocess.run(["git", "-C", str(top), "worktree", "remove", "--force", str(wt)], capture_output=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    ok = (after[0] == before[0]) or (before[0] != 0 and after[0] == 0)
    res = {"referrer": job["referrer"], "to": rel_dst, "swaps": job["swaps"], "selftest": st, "rc_before": before[0],
           "rc_after": after[0], "ok": ok, "why": "" if ok else after[1][-200:]}
    if ok and apply:
        if job["as"] == "TAIL":
            doc = (f"# [VIA:MIGRATE {VERSION}] 由 {src_p.name} 整檔複本;只把點名的舊版檔名換成目標家族現役尾版:"
                   + " · ".join(f"{o} → {n}" for o, n in job["swaps"].items()) + "(舊版退役用)\n")
            lines = new_text.splitlines(keepends=True)
            ins = 0
            while ins < len(lines) and (lines[ins].startswith("#!") or "coding" in lines[ins][:30]):
                ins += 1
            new_text = "".join(lines[:ins]) + doc + "".join(lines[ins:])
            ast.parse(new_text)
            compile(new_text, str(dst), "exec")
        dst.write_text(new_text, encoding="utf-8")
    log(f"  [{'OK' if ok else 'FAIL'}] {job['referrer']} → {rel_dst} · 換 {len(job['swaps'])} · "
        f"{'自測' if st else '載入'} rc {before[0]} → {after[0]}")
    return res


def cmd_migrate(systems: list[str] | None, apply: bool) -> int:
    via = CODE_ROOT
    rep = prune_scan(via, systems)
    plan = plan_migrations(via, rep)
    print(f"[migrate] 仍會執行的點名:可遷 {len(plan['jobs'])} 支點名檔 · 暫不能遷 {len(plan['held'])} 處"
          f"(目標 {len(plan['blocked_targets'])} 支留著)· {'寫入' if apply else '乾跑'}")
    results = [migrate_one(via, j, apply) for j in plan["jobs"]]
    out = PRIOR.PRUNE_DIR / "MIGRATE_latest.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "apply": apply,
                               "results": results, "held": plan["held"]}, ensure_ascii=False, indent=1), encoding="utf-8")
    okn = sum(r.get("ok") for r in results)
    print(f"[migrate] 過 {okn} · 不過 {len(results) - okn} · 報告 {out}")
    for h in plan["held"][:40]:
        print(f"  [留] {Path(h['target']).name} ← {Path(h.get('referrer', '-')).name}:{h['why']}")
    print("NEXT: " + ("via-migrate --apply" if not apply else "提交 → via-prune --prove --apply(舊點名者與目標一起退)"))
    return 0 if okn == len(results) else 1


PRIOR.CMD["via-prune"]["help"] += " CODE_DEAD(點名已不會執行)也一起證、一起退;CODE_LIVE 先跑 via-migrate。"
P2.COMMANDS.append({"name": "via-migrate", "group": "維護", "title": "遷移仍會執行的舊版點名(退役前)", "target": ["prune", "migrate"],
                    "plugin": "本中樞(ast + compile + 自測前後比)",
                    "help": "找出仍會執行的舊版檔名點名:點名者是尾版就出新版號(整檔複本 + 換成目標現役尾版)、沒有版號就原地改;"
                            "先在 TEMP 驗 ast/compile 與自測前後同 rc 才寫。PS 既有檔與鏈中段只列清單不改。預設乾跑,--apply 才寫。",
                    "examples": ["via-migrate", "via-migrate --apply"], "replaces": []})
P2.CMD["via-migrate"] = P2.COMMANDS[-1]

_V0103_MAIN = PRIOR._main_with_kinds


def _main_v0104(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] == ["register"]:
        r = register_new(CODE_ROOT, [x for x in a[1:] if not x.startswith("--")])
        return 0 if "error" not in r.get("component", {}) else 1
    if a[:2] == ["prune", "migrate"]:
        a = a[1:]
    if a[:1] == ["migrate"]:
        sysx = [a[a.index("--system") + 1].upper()] if "--system" in a else None
        return cmd_migrate(sysx, "--apply" in a)
    if a[:1] == ["prune"] and "--kinds" not in a:
        a += ["--kinds", "UNREF,DOC_REF,SNAP_REF,REG_REF,CODE_DEAD"]
    if a[:1] == ["x"] and a[1:2] == ["via-migrate"]:
        return _main_v0104(["migrate"] + a[2:])
    return _V0103_MAIN(a)


P2.main = _main_v0104
PRIOR.main = _main_v0104


def main(argv: list[str] | None = None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    return _main_v0104(a)


def selftest() -> int:
    ok = bad = 0

    def chk(name, cond, note=""):
        nonlocal ok, bad
        ok += bool(cond)
        bad += not cond
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}", flush=True)

    src = ('"""doc 提到 X_v0100.py"""\n# 註解 X_v0100.py\nA = "X_v0100.py"\n'
           'def f():\n    """X_v0100.py"""\n    return "X_v0100.py"\nclass C:\n    pass\n')
    owners = code_owners(src, "X_v0100.py")
    chk("① 點名分辨:docstring / 註解不算,模組常數與函式字串才算", owners == ["A", "f"], f"({owners})")
    with tempfile.TemporaryDirectory(prefix="vcgc_mig_st_") as td:
        T = Path(td)
        subprocess.run(["git", "init", "-q", str(T)], check=True)
        d = T / "fam"
        d.mkdir()
        g = ("from pathlib import Path\nimport re\ndef _vnum(p):\n    return int(re.search(r'_v(\\d{4})$',Path(p).stem).group(1))\n"
             "PRIOR_PATH=max((p for p in Path(__file__).parent.glob('R_v*.py') if _vnum(p)<_vnum(__file__)),key=_vnum)\n")
        (d / "R_v0100.py").write_text('def run():\n    return "X_v0100.py"\ndef keep():\n    return "X_v0100.py"\n', encoding="utf-8")
        (d / "R_v0101.py").write_text(g + 'def run():\n    return "X_v0101.py"\n', encoding="utf-8")
        (d / "X_v0100.py").write_text("x=1\n", encoding="utf-8")
        (d / "X_v0101.py").write_text("x=2\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(T), "add", "-A"], check=True)
        idx = FamilyIndex.__new__(FamilyIndex)
        idx.via, idx._live = T, {}
        idx.link = lambda t, s, n: "glob 取前版" if ".glob(" in t else "本體"
        idx.fam = collections.defaultdict(dict)
        for p in d.glob("*.py"):
            m = _TAIL_RX.match(p.name)
            idx.fam[("fam", m.group(1))][int(m.group(2))] = p
        chk("② 身分:尾版 / 鏈中段", idx.status("fam/R_v0101.py")[0] == "TAIL" and idx.status("fam/R_v0100.py")[0] == "MIDDLE")
        eff = effective_refs(idx, "X_v0100.py", ["fam/R_v0100.py"])
        chk("③ 鏈中段:run 被新版蓋掉不算,keep 沒被蓋 → 仍會執行", eff == [("MIDDLE", "fam/R_v0100.py")], f"({eff})")
        (d / "R_v0100.py").write_text('def run():\n    return "X_v0100.py"\n', encoding="utf-8")
        idx._live = {}
        chk("④ 鏈中段:唯一點名所在函式被蓋 → 不會執行(CODE_DEAD)", effective_refs(idx, "X_v0100.py", ["fam/R_v0100.py"]) == [])
        chk("⑤ PS 點名一律算仍會執行(不改既有 PS)", effective_refs(idx, "X_v0100.py", ["a/Run-X.ps1"]) == [("PS", "a/Run-X.ps1")])
        chk("⑥ 下一個版號", _next_version_path(d / "R_v0101.py").name == "R_v0102.py")
        sw = re.sub(r"(?<![A-Za-z0-9_\-])" + re.escape("X_v0100.py"), "X_v0101.py", 'a="X_v0100.py";b="YX_v0100.py"')
        chk("⑦ 換名只換完整檔名(前面接字母數字的不換)", sw == 'a="X_v0101.py";b="YX_v0100.py"', f"({sw})")
    chk("⑧ via-migrate 進指令冊", "via-migrate" in P2.CMD and P2.LEGACY.get("via-migrate") is None)
    chk("⑨ 加速器橋執行時生效", VIA_ACCEL is not None)
    with contextlib.redirect_stdout(io.StringIO()) as buf:
        rc = PRIOR.selftest()
    t = [l for l in buf.getvalue().splitlines() if "[計]" in l]
    chk("⑩ 前版 v0103 自測", rc == 0, f"({t[-1].strip() if t else rc})")
    print(f"  [計] {FAMILY} {VERSION} 自測 OK {ok} · FAIL {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
