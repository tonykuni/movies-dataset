#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL237_NumberingSystem v0109 — 薄尾:只登本批(--apply --scope)· audit 加註冊完整性(IMMUT · DUPREG · XCODE · FPSTALE · UNCOMMITTED · TIMEFMT)

操作員 2026-09-30:「SSOT / 自動編號 / 含版本及時間自動註冊 / WORKFLOW SSOT / REGEX / 同義字管理等將邏輯管理編號架構及可能的風險
從新整理優化一遍」;2026-09-29:「既有範圍內註冊 不要擴張範圍」。架構與風險冊正本:VIA_Registry_Architecture_SSOT_v*.json。
  ① --apply --scope [檔 …]:範圍預設 = 對基準(merge-base HEAD origin/main)有變的檔;有未提交變更的來源不發號(先提交再編號,R04)。
     收集只留來源在範圍內的項(函式 / 類別跟著模組;工具列看檔名;函式庫看範圍內檔案的 import),再照本體發號 ——
     號碼與分類碼只對本批連續(R03)。寫回:範圍外的舊列一字不動;記錄來源在範圍內的舊列換成引擎新值(例:就地改的活冊換指紋);
     新列全收。寫後照 v0108 只增自核,違反即整批還原、rc 2。scope 動詞只乾跑列出範圍。
  ② audit 加註冊完整性(讀架構冊 mutability / time):
     IMMUT   已發布的版號冊(snapshot)在本分支被就地改 = RED(R01;需求冊 v0104 事件)
     DUPREG  引擎版本冊同(家族 · 角色 · 檔)多號,或一家多列 engine 席位 = RED(R06)
     XCODE   元件冊與引擎版本冊共用 VIA-TOOL 空間同號兩主 = RED(R07)
     FPSTALE SSOT 冊內容指紋與檔不符 = YELLOW(R05;CRLF 工作複本照容忍)
     UNCOMMITTED 列上更新時間是 uncommitted = YELLOW(R04)
     TIMEFMT 本批新列的 numbered_at 不在時間規範 = YELLOW(R08)
其餘照 v0108(全量 --apply 仍是操作員下令才跑;只增自核照舊)。只收 VCGC 呼叫(audit / --apply)。零網路。
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

import ast
import hashlib
import importlib.util
import json
import os
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL237_NumberingSystem"
ENGINE = Path(__file__).stem
ARCH_GLOB = "VIA_Registry_Architecture_SSOT_v*.json"
REGISTER = "VIA_EngineVersion_Register_v0100.json"
INVENTORY = "VIA_Component_Inventory_SSOT_v0100.json"


def _vnum(path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + ENGINE, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR.BASE
PARENT_RX = re.compile(r"^(VIA-[A-Z0-9]+-(?:MDL|ENG)\d+)-")
VERSIONED_JSON = re.compile(r"^(?P<fam>.+)_v(?P<v>\d{4})\.json$")
DEFAULT_TIME = (r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\+00:00|Z)$", r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} \+0000$")


def __getattr__(name: str):
    return getattr(PRIOR, name)


_git, base_ref, current_state, state_at = PRIOR._git, PRIOR.base_ref, PRIOR.current_state, PRIOR.state_at
snapshot, restore, _texts, compare, inventory, integrity = (PRIOR.snapshot, PRIOR.restore, PRIOR._texts, PRIOR.compare,
                                                           PRIOR.inventory, PRIOR.integrity)


def arch(folder: Path | None = None) -> dict:
    """The registry architecture book (mutability classes · time rules); {} when absent (checks then use built-in defaults)."""
    hits = sorted((folder or HERE).glob(ARCH_GLOB), key=_vnum)
    try:
        return json.loads(hits[-1].read_text(encoding="utf-8")) if hits else {}
    except (OSError, ValueError):
        return {}


# ---------------------------------------------------------------- ① scope
def _lines(out: str) -> set:
    return {x.strip() for x in out.splitlines() if x.strip()}


def scope_files(ref: str | None = None) -> set:
    """VIA-relative paths that differ from the base (committed on this branch, staged or not)."""
    rc, out = _git("diff", "--name-only", "--relative", ref or base_ref())
    return _lines(out) if rc == 0 else set()


def dirty_files() -> set:
    """VIA-relative paths with uncommitted changes, plus untracked files: numbered only after they are committed."""
    _rc, changed = _git("diff", "--name-only", "--relative", "HEAD")
    _rc2, untracked = _git("ls-files", "--others", "--exclude-standard")
    return _lines(changed) | _lines(untracked)


def imports_of(files, root: Path | None = None) -> set:
    """Top-level module names imported by these .py files (what their LIB rows are keyed by)."""
    names = set()
    for rel in files:
        if not str(rel).endswith(".py"):
            continue
        try:
            tree = ast.parse(((root or BASE.VIA) / rel).read_text(encoding="utf-8", errors="ignore"))
        except (OSError, SyntaxError, ValueError):
            continue
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                names.update(a.name.split(".")[0] for a in n.names)
            elif isinstance(n, ast.ImportFrom) and n.module and not n.level:
                names.add(n.module.split(".")[0])
    return names


class Scope:
    """What this batch may register: its own files, minus anything not yet committed."""

    def __init__(self, files, dirty=(), imports=()):
        self.dirty = {str(x) for x in dirty}
        self.files = {str(x) for x in files} - self.dirty
        self.names = {Path(f).name for f in self.files}
        self.imports = set(imports)

    def item_in(self, it: dict) -> bool:
        src = str(it.get("source") or "")
        if src in self.dirty:
            return False
        if src in self.files:
            return True
        if it.get("kind") == "LIB":
            return str(it.get("key") or "") in self.imports
        return str(it.get("name") or "") in self.names

    def row_refresh(self, row: dict, parents: set) -> bool:
        """An existing row takes the engine's new values only when the file it was recorded from is in scope."""
        if "source" in row:
            src = str(row.get("source") or "")
            return src in self.files and src not in self.dirty
        m = PARENT_RX.match(str(row.get("code") or ""))
        return bool(m) and m.group(1) in parents


def _parse(text: str) -> list:
    return [(json.loads(x)["code"], x) for x in text.splitlines() if x.strip()]


def merge_scoped(before: tuple, after: tuple, scope: Scope) -> tuple:
    """(books, ssot) before the write + the engine's full output → the scoped result and a per-book report.

    Old rows stay byte for byte unless the file they were recorded from is in scope; every new code is kept (the scoped
    collector only let in-scope items through, so the engine issued new codes for nothing else)."""
    b_books, b_ssot = before
    a_books, a_ssot = after
    parents = set()                                     # module / engine rows whose functions and classes may change
    for name in set(b_books) | set(a_books):
        m = PRIOR.BOOK_RX.match(name)
        if not (m and m.group("kind") in ("MDL", "ENG")):
            continue
        old = {c: line for c, line in _parse(b_books.get(name, ""))}
        for c, line in old.items():
            if scope.row_refresh(json.loads(line), set()):
                parents.add(c)
        parents.update(c for c, _l in _parse(a_books.get(name, "")) if c not in old)
    books, report = {}, {}
    for name in sorted(n for n in set(b_books) | set(a_books) if PRIOR.BOOK_RX.match(n)):
        old = dict(_parse(b_books.get(name, "")))
        new = dict(_parse(a_books.get(name, "")))
        out, added, refreshed = dict(old), 0, 0
        for code, line in new.items():
            if code not in old:
                out[code] = line
                added += 1
            elif line != old[code] and scope.row_refresh(json.loads(old[code]), parents):
                out[code] = line
                refreshed += 1
        books[name] = "".join(out[c] + "\n" for c in sorted(out))
        if added or refreshed:
            report[name] = {"added": added, "refreshed": refreshed}
    ssot = json.loads(json.dumps(b_ssot or a_ssot, ensure_ascii=False))
    for kind, rows in (a_ssot.get("rows") or {}).items():
        old = {r["code"]: r for r in ((b_ssot.get("rows") or {}).get(kind) or [])}
        out, added, refreshed = dict(old), 0, 0
        for r in rows:
            c = r["code"]
            if c not in old:
                out[c] = r
                added += 1
            elif r != old[c] and scope.row_refresh(old[c], parents):
                out[c] = r
                refreshed += 1
        ssot.setdefault("rows", {})[kind] = [out[c] for c in sorted(out)]
        if added or refreshed:
            report["rows." + kind] = {"added": added, "refreshed": refreshed}
    cats = {k: dict(v) for k, v in (b_ssot.get("categories") or {}).items()}
    for kind, table in (a_ssot.get("categories") or {}).items():
        for cat, code in table.items():
            if cat not in cats.setdefault(kind, {}):
                cats[kind][cat] = code
    ssot["categories"] = cats
    for kind, meta in (a_ssot.get("books") or {}).items():      # a book file the engine opened this run (new subsystem)
        have = ssot.setdefault("books", {}).setdefault(kind, json.loads(json.dumps(meta, ensure_ascii=False)))
        for sub, fm in (meta.get("files") or {}).items():
            have.setdefault("files", {}).setdefault(sub, dict(fm))
    _remeta(ssot, books)
    return books, ssot, report


def _remeta(ssot: dict, books: dict) -> None:
    """Book metadata (n / sha per file, totals per kind, rows.X counts) recomputed from the merged texts."""
    sha = lambda t: hashlib.sha256(t.encode("utf-8")).hexdigest()[:16]     # noqa: E731
    for kind, meta in (ssot.get("books") or {}).items():
        if meta.get("in"):
            meta["n"] = len(((ssot.get("rows") or {}).get(kind)) or [])
        elif meta.get("files"):
            for sub, fm in meta["files"].items():
                name = Path(fm["file"]).name
                if name in books:
                    fm.update(n=sum(1 for x in books[name].splitlines() if x.strip()), sha=sha(books[name]))
            meta["n"] = sum(fm.get("n") or 0 for fm in meta["files"].values())
        elif meta.get("file"):
            name = Path(meta["file"]).name
            if name in books:
                meta.update(n=sum(1 for x in books[name].splitlines() if x.strip()), sha=sha(books[name]))


def _write_state(books: dict, ssot: dict, snap: dict) -> None:
    for name, text in books.items():
        p = snap["dir"] / name
        if not p.is_file() or p.read_text(encoding="utf-8") != text:
            p.write_text(text, encoding="utf-8", newline="")
    snap["ssot"].write_text(json.dumps(ssot, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="")


def scoped_apply(files=None, ref: str | None = None, build=None, out=sys.stdout) -> int:
    """--apply --scope: register only this batch (see ①). Returns 0 / 2 (write violated append-only → restored)."""
    ref = ref or base_ref()
    raw = set(files) if files is not None else scope_files(ref)
    dirty = dirty_files() if files is None else set()
    keep = raw - dirty
    scope = Scope(raw, dirty, imports_of(f for f in keep if f.endswith(".py")))
    snap = snapshot()
    before = _texts(snap)
    inner = BASE.collect

    def collect():
        items, notes = inner()
        return [it for it in items if scope.item_in(it)], notes

    BASE.collect = collect
    try:
        (build or BASE.build)(True)
    finally:
        BASE.collect = inner
    books, ssot, report = merge_scoped(before, current_state(), scope)
    _write_state(books, ssot, snap)
    rep = PRIOR.audit("寫前(本輪)", before=before, after=current_state())
    held = sorted(f for f in dirty & raw)
    print(f"[編號 · 只登本批] 範圍 {len(raw)} 檔 · 未提交不發號 {len(held)} · 寫入 "
          + (" · ".join(f"{k} +{v['added']}/~{v['refreshed']}" for k, v in sorted(report.items())) or "無"), file=out)
    for f in held[:8]:
        print(f"  [先提交再編號] {f}", file=out)
    PRIOR._print_audit(rep, out=out)
    if rep["lamp"] == "RED":
        n = restore(snap)
        print(f"[編號 · 只登本批] 寫入違反只增 → 已整批還原 {n} 檔,rc 2", file=out)
        return 2
    return 0


# ---------------------------------------------------------------- ② registry integrity
def _match_any(value: str, patterns) -> bool:
    return any(re.match(p, value) for p in patterns)


def immut_violations(changed, base_versions: dict, arch_doc: dict) -> list:
    """changed: VIA-relative *_vNNNN.json paths that exist on the base and differ now; base_versions: dir|family → count."""
    mut = (arch_doc.get("mutability") or {})
    snap_fams = set(mut.get("snapshot_families") or [])
    living = set(mut.get("living_books") or [])
    out = []
    for rel in sorted(changed):
        m = VERSIONED_JSON.match(Path(rel).name)
        if not m or Path(rel).name in living:
            continue
        fam = m.group("fam")
        if fam in snap_fams or base_versions.get(f"{Path(rel).parent.as_posix()}|{fam}", 0) >= 2:
            out.append(rel)
    return out


def dupreg(register: dict) -> list:
    rows = register.get("rows") or []
    seen, out = {}, []
    for r in rows:
        k = (r.get("family"), r.get("role"), r.get("file"))
        seen.setdefault(k, []).append(r.get("code"))
    out += [f"{k[0]}·{k[1]}·{k[2]}:{'/'.join(v)}" for k, v in seen.items() if len(v) > 1]
    seats = {}
    for r in rows:
        if r.get("role") == "engine":
            seats.setdefault(r.get("family"), []).append(r.get("code"))
    out += [f"{fam} 席位 {len(v)} 列:{'/'.join(v)}" for fam, v in seats.items() if len(v) > 1]
    return out


def xcode(inventory_doc: dict, register: dict) -> list:
    inv = {}
    for r in inventory_doc.get("records") or []:
        inv.setdefault(r.get("code"), r.get("identity"))
    return [f"{r.get('code')}:{r.get('file')} ↔ {inv[r.get('code')]}" for r in register.get("rows") or []
            if r.get("where") == "this register" and r.get("code") in inv]


def fpstale(ssot: dict, root: Path) -> list:
    out = []
    for r in ((ssot.get("rows") or {}).get("SSOT")) or []:
        want, src = r.get("content_sha"), r.get("source")
        if not want or not src:
            continue
        p = root / src
        if not p.is_file():
            continue
        raw = p.read_bytes()
        got = {hashlib.sha256(raw).hexdigest()[:len(want)], hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()[:len(want)]}
        if want not in got:
            out.append(f"{r.get('code')} {Path(src).name}")
    return out


def uncommitted_rows(books: dict, ssot: dict) -> list:
    out = []
    for name, text in books.items():
        for code, line in _parse(text):
            if '"uncommitted"' in line and json.loads(line).get("updated_at") == "uncommitted":
                out.append(code)
    for rows in (ssot.get("rows") or {}).values():
        out += [r["code"] for r in rows if r.get("updated_at") == "uncommitted"]
    return out


def timefmt(new_rows: list, patterns=DEFAULT_TIME) -> list:
    return [r.get("code") for r in new_rows if isinstance(r.get("numbered_at"), str) and not _match_any(r["numbered_at"], patterns)]


def _base_versions(ref: str, dirs) -> dict:
    counts = {}
    for d in sorted(set(dirs)):
        rc, out = _git("ls-tree", "--name-only", ref, "--", (d + "/") if d else ".")
        for name in (Path(x).name for x in (out.splitlines() if rc == 0 else [])):
            m = VERSIONED_JSON.match(name)
            if m:
                k = f"{d}|{m.group('fam')}"
                counts[k] = counts.get(k, 0) + 1
    return counts


def registry_checks(ref: str | None = None, after=None, root: Path | None = None) -> list:
    ref = ref or base_ref()
    root = root or BASE.VIA
    arch_doc = arch()
    rc, out = _git("diff", "--name-only", "--relative", ref, "--", "*.json")
    changed = [f for f in _lines(out) if VERSIONED_JSON.match(Path(f).name)] if rc == 0 else []
    on_base = [f for f in changed if _git("cat-file", "-e", f"{ref}:./{f}")[0] == 0]
    immut = immut_violations(on_base, _base_versions(ref, (Path(f).parent.as_posix() for f in on_base)), arch_doc)
    reg = BASE._json(HERE / REGISTER) or {}
    inv = BASE._json(HERE / INVENTORY) or {}
    a_books, a_ssot = after if after is not None else current_state()
    b_books, b_ssot = state_at(ref)
    base_codes = set(inventory(b_books, b_ssot)["codes"])
    new_rows = []
    for name, text in a_books.items():
        for code, line in _parse(text):
            if code not in base_codes:
                new_rows.append(json.loads(line))
    for rows in (a_ssot.get("rows") or {}).values():
        new_rows += [r for r in rows if r.get("code") not in base_codes]
    pats = tuple(((arch_doc.get("time") or {}).get("accepted_regex")) or DEFAULT_TIME)
    found = [
        ("IMMUT", "RED", immut, "已發布版號冊就地改(要出新版號檔)"),
        ("DUPREG", "RED", dupreg(reg), "引擎版本冊同檔多號 / 一家多列席位"),
        ("XCODE", "RED", xcode(inv, reg), "元件冊 × 引擎版本冊同號兩主"),
        ("FPSTALE", "YELLOW", fpstale(a_ssot, root), "SSOT 冊指紋過期(就地改後要重編)"),
        ("UNCOMMITTED", "YELLOW", uncommitted_rows(a_books, a_ssot), "未提交就發號(先提交再編號)"),
        ("TIMEFMT", "YELLOW", timefmt(new_rows, pats), "本批新列時間不在規範"),
    ]
    return [{"rule": r, "lamp": lamp if hits else "GREEN", "n": len(hits), "what": what, "hits": hits[:8]}
            for r, lamp, hits, what in found]


def audit(ref: str | None = None, before=None, after=None) -> dict:
    rep = PRIOR.audit(ref, before=before, after=after)
    if before is None:                                  # a write guard (before given) judges only its own write
        rep["registry"] = registry_checks(rep["baseline"], after=after)
        lamps = [rep["lamp"]] + [c["lamp"] for c in rep["registry"]]
        rep["lamp"] = "RED" if "RED" in lamps else "YELLOW" if "YELLOW" in lamps else "GREEN"
    return rep


def _print_audit(rep: dict, out=sys.stdout) -> None:
    PRIOR._print_audit(rep, out=out)
    for c in rep.get("registry") or []:
        tail = (" · " + " ; ".join(str(h) for h in c["hits"][:4])) if c["n"] else ""
        print(f"  [註冊完整性] {c['lamp']:6s} {c['rule']:11s} {c['n']:>4} · {c['what']}{tail}", file=out)


# ---------------------------------------------------------------- main
def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args:
        return selftest()
    gated = args[:1] in (["audit"], ["scope"]) or "--apply" in args
    if gated and os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False))
        return 2
    if args[:1] == ["audit"]:
        ref = args[args.index("--base") + 1] if "--base" in args and args.index("--base") + 1 < len(args) else None
        rep = audit(ref)
        if "--json" in args:
            print(json.dumps(rep, ensure_ascii=False, indent=1))
        else:
            _print_audit(rep)
        return {"GREEN": 0, "YELLOW": 2, "RED": 1}[rep["lamp"]]
    if args[:1] == ["scope"]:
        raw, dirty = scope_files(), dirty_files()
        print(json.dumps({"via": "vcgc", "verb": "scope", "baseline": base_ref(), "files": sorted(raw - dirty),
                          "held_uncommitted": sorted(raw & dirty)}, ensure_ascii=False, indent=1))
        return 0
    if "--apply" in args and "--scope" in args:
        i = args.index("--scope")
        listed = [a for a in args[i + 1:] if not a.startswith("--")]
        return scoped_apply(listed or None)
    return PRIOR.main(argv)


# ---------------------------------------------------------------- selftest
def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    sc = Scope({"a/new_v0101.py", "r/Book_SSOT_v0100.json", "a/dirty_v0100.py"}, {"a/dirty_v0100.py"}, {"rich"})
    items = [{"kind": "MDL", "source": "a/new_v0101.py", "name": "new_v0101"},
             {"kind": "FNC", "source": "a/new_v0101.py", "name": "main"},
             {"kind": "MDL", "source": "a/dirty_v0100.py", "name": "dirty_v0100"},
             {"kind": "MDL", "source": "a/old_v0100.py", "name": "old_v0100"},
             {"kind": "LIB", "source": "pip", "key": "rich", "name": "rich"},
             {"kind": "LIB", "source": "pip", "key": "numpy", "name": "numpy"},
             {"kind": "TOOL", "source": "VIA-TOOL-0001 · x", "name": "new_v0101.py"}]
    got = [sc.item_in(it) for it in items]
    chk("① 範圍收集:本批檔 · 其函式 · 本批 import 的庫 · 檔名對得上的工具收;未提交與範圍外不收",
        got == [True, True, False, False, True, False, True], got)
    mdl_b = '{"code":"VIA-A-MDL001","source":"a/old_v0100.py","updated_at":"t0"}\n'
    mdl_a = ('{"code":"VIA-A-MDL001","source":"a/old_v0100.py","updated_at":"t0","lamp":"AMBER","gone_since":"x"}\n'
             '{"code":"VIA-A-MDL002","source":"a/new_v0101.py","updated_at":"t1"}\n')
    fnc_b = '{"code":"VIA-A-MDL001-FNC001","q":"f"}\n'
    fnc_a = '{"code":"VIA-A-MDL001-FNC001","q":"f","lamp":"AMBER"}\n{"code":"VIA-A-MDL002-FNC001","q":"main"}\n'
    b_ssot = {"categories": {"MDL": {"a": "MDL-C001"}},
              "books": {"MDL": {"file": "x/VIA_NumberBook_MDL_v0100.jsonl", "n": 1, "sha": "-"},
                        "FNC": {"n": 1, "files": {"A": {"file": "x/VIA_NumberBook_FNC_A_v0100.jsonl", "n": 1, "sha": "-"}}},
                        "SSOT": {"in": "rows.SSOT", "n": 1}},
              "rows": {"SSOT": [{"code": "VIA-A-SSOT001", "source": "r/Book_SSOT_v0100.json", "content_sha": "old"}]}}
    a_ssot = json.loads(json.dumps(b_ssot))
    a_ssot["categories"]["MDL"]["b"] = "MDL-C002"
    a_ssot["rows"]["SSOT"] = [{"code": "VIA-A-SSOT001", "source": "r/Book_SSOT_v0100.json", "content_sha": "new"},
                              {"code": "VIA-A-SSOT002", "source": "r/Other_SSOT_v0100.json", "content_sha": "n2"}]
    before = ({"VIA_NumberBook_MDL_v0100.jsonl": mdl_b, "VIA_NumberBook_FNC_A_v0100.jsonl": fnc_b}, b_ssot)
    after = ({"VIA_NumberBook_MDL_v0100.jsonl": mdl_a, "VIA_NumberBook_FNC_A_v0100.jsonl": fnc_a}, a_ssot)
    books, ssot, rep = merge_scoped(before, after, sc)
    mdl = books["VIA_NumberBook_MDL_v0100.jsonl"].splitlines()
    fnc = books["VIA_NumberBook_FNC_A_v0100.jsonl"].splitlines()
    chk("② 合併:範圍外舊列一字不動(下市標記不寫)· 新列收 · 子函式跟著模組",
        mdl[0] == mdl_b.strip() and len(mdl) == 2 and fnc[0] == fnc_b.strip() and len(fnc) == 2, {"mdl": len(mdl), "fnc": len(fnc)})
    s_rows = {r["code"]: r for r in ssot["rows"]["SSOT"]}
    chk("③ 範圍內就地改的冊換指紋 · 分類碼只增 · 冊檔 n 重算",
        s_rows["VIA-A-SSOT001"]["content_sha"] == "new" and "VIA-A-SSOT002" in s_rows
        and ssot["categories"]["MDL"] == {"a": "MDL-C001", "b": "MDL-C002"}
        and ssot["books"]["MDL"]["n"] == 2 and ssot["books"]["FNC"]["n"] == 2 and ssot["books"]["SSOT"]["n"] == 2, rep)
    cmp = compare(inventory(*before), inventory(books, ssot))
    chk("④ 合併結果只增:遺失 0 · 改身分 0 · 重號 0", not cmp["missing"] and not cmp["changed_identity"] and not cmp["duplicate_codes"], cmp)
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        (d / "VIA_NumberBook_MDL_v0100.jsonl").write_text(mdl_b, encoding="utf-8")
        (d / "VIA_NumberBook_FNC_A_v0100.jsonl").write_text(fnc_b, encoding="utf-8")
        (d / "VIA_Numbering_SSOT_v0100.json").write_text(json.dumps(b_ssot), encoding="utf-8")
        saved = (BASE.BOOK_DIR, BASE._newest)
        BASE.BOOK_DIR = d
        BASE._newest = lambda folder, pat: (d / "VIA_Numbering_SSOT_v0100.json") if "Numbering_SSOT" in pat else saved[1](folder, pat)
        seen = {}

        def fake_build(_apply):
            seen["items"] = [it["source"] for it in BASE.collect()[0]]
            (d / "VIA_NumberBook_MDL_v0100.jsonl").write_text(mdl_a, encoding="utf-8")
            (d / "VIA_NumberBook_FNC_A_v0100.jsonl").write_text(fnc_a, encoding="utf-8")
            (d / "VIA_Numbering_SSOT_v0100.json").write_text(json.dumps(a_ssot), encoding="utf-8")

        own = '{"code":"VIA-A-MDL002","source":"a/new_v0101.py","key":"k1"}\n'

        def bad_build(_apply):                           # an in-scope row whose identity changes → append-only violated
            (d / "VIA_NumberBook_MDL_v0100.jsonl").write_text(
                mdl_b + '{"code":"VIA-A-MDL002","source":"a/new_v0101.py","key":"k2"}\n', encoding="utf-8")

        inner = BASE.collect
        BASE.collect = lambda: ([{"kind": "MDL", "source": "a/new_v0101.py", "name": "n"},
                                 {"kind": "MDL", "source": "a/old_v0100.py", "name": "o"}], {})
        try:
            import io
            import contextlib
            with contextlib.redirect_stdout(io.StringIO()):
                rc_good = scoped_apply({"a/new_v0101.py", "r/Book_SSOT_v0100.json"}, ref="HEAD", build=fake_build)
            good_mdl = (d / "VIA_NumberBook_MDL_v0100.jsonl").read_text(encoding="utf-8")
            (d / "VIA_NumberBook_MDL_v0100.jsonl").write_text(mdl_b + own, encoding="utf-8")
            (d / "VIA_Numbering_SSOT_v0100.json").write_text(json.dumps(b_ssot), encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                rc_bad = scoped_apply({"a/new_v0101.py"}, ref="HEAD", build=bad_build)
            restored = (d / "VIA_NumberBook_MDL_v0100.jsonl").read_text(encoding="utf-8") == mdl_b + own
        finally:
            BASE.collect = inner
            BASE.BOOK_DIR, BASE._newest = saved
    chk("⑤ --apply --scope 端到端:收集器只看得到本批 · 範圍外列不動 · 丟號的寫入整批還原 rc 2",
        rc_good == 0 and seen.get("items") == ["a/new_v0101.py"] and good_mdl.splitlines()[0] == mdl_b.strip()
        and "VIA-A-MDL002" in good_mdl and rc_bad == 2 and restored, f"好 {rc_good} · 收 {seen.get('items')} · 壞 {rc_bad} 還原 {restored}")
    arch_doc = {"mutability": {"snapshot_families": ["Req_SSOT"], "living_books": ["Live_SSOT_v0100.json"]}}
    viol = immut_violations(["r/Req_SSOT_v0104.json", "r/Live_SSOT_v0100.json", "r/Multi_v0101.json", "r/Single_v0100.json"],
                            {"r|Multi": 2, "r|Single": 1}, arch_doc)
    chk("⑥ IMMUT:版號冊(列名或基準上 ≥2 版)就地改抓到;活冊與單版冊不算", viol == ["r/Multi_v0101.json", "r/Req_SSOT_v0104.json"], viol)
    reg_bad = {"rows": [{"family": "t", "role": "engine", "file": "x_v2.py", "code": "C1"},
                        {"family": "t", "role": "engine", "file": "x_v2.py", "code": "C2"},
                        {"family": "n", "role": "engine", "file": "y_v2.py", "code": "C3"},
                        {"family": "n", "role": "candidate", "file": "y_v2.py", "code": "C4"}]}
    reg_ok = {"rows": [{"family": "t", "role": "engine", "file": "x_v2.py", "code": "C1"},
                       {"family": "t", "role": "candidate", "file": "x_v2.py", "code": "C2"}]}
    d_bad, d_ok = dupreg(reg_bad), dupreg(reg_ok)
    chk("⑦ DUPREG:同(家族·角色·檔)兩號 · 一家兩列席位抓到;席位 + 候選列(network v1652 先例)不算", len(d_bad) == 2 and d_ok == [], d_bad)
    xc = xcode({"records": [{"code": "VIA-TOOL-0001", "identity": "tool|a"}]},
               {"rows": [{"code": "VIA-TOOL-0001", "file": "b.py", "where": "this register"},
                         {"code": "VIA-TOOL-0002", "file": "c.py", "where": "this register"}]})
    chk("⑧ XCODE:共用 VIA-TOOL 空間同號兩主抓到", len(xc) == 1 and xc[0].startswith("VIA-TOOL-0001"), xc)
    with tempfile.TemporaryDirectory() as tmp:
        r = Path(tmp)
        (r / "a.json").write_bytes(b'{"a":1}\r\n')
        good = hashlib.sha256(b'{"a":1}\n').hexdigest()[:12]
        s = {"rows": {"SSOT": [{"code": "S1", "source": "a.json", "content_sha": good},
                               {"code": "S2", "source": "a.json", "content_sha": "000000000000"}]}}
        fp = fpstale(s, r)
    chk("⑨ FPSTALE:指紋過期抓到;CRLF 工作複本照容忍", fp == ["S2 a.json"], fp)
    u = uncommitted_rows({"VIA_NumberBook_SSOT_v0100.jsonl": '{"code":"X1","updated_at":"uncommitted"}\n{"code":"X2","updated_at":"t"}\n'},
                         {"rows": {"SSOT": [{"code": "X3", "updated_at": "uncommitted"}]}})
    tf = timefmt([{"code": "N1", "numbered_at": "2026-09-30T01:02:03+00:00"}, {"code": "N2", "numbered_at": "2026-09-30 01:02:03 +0000"},
                  {"code": "N3", "numbered_at": "2026-09-30T01:02:03"}, {"code": "N4", "numbered_at": "20260930_010203"}])
    chk("⑩ UNCOMMITTED · TIMEFMT:未提交列與不帶時區的新時間抓到", u == ["X1", "X3"] and tf == ["N3", "N4"], {"u": u, "tf": tf})
    live = registry_checks()
    lamps = {c["rule"]: (c["lamp"], c["n"]) for c in live}
    chk("⑪ 實樹唯讀:六項註冊完整性都量得出(引擎版本冊 · 元件冊 · 編號冊 · 架構冊都讀得到)",
        set(lamps) == {"IMMUT", "DUPREG", "XCODE", "FPSTALE", "UNCOMMITTED", "TIMEFMT"} and bool(arch().get("mutability")), lamps)
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑫ 檔頭 · 加速器橋 · 網路橋在;不碰 TA-Lib", "VIA:ACCEL-BRIDGE" in text and "VIA:NET-BRIDGE" in text
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M))
    print(f"[編號 v0109] 本版 {sum(ok)}/{len(ok)}")
    if not all(ok):
        return 1
    return PRIOR.selftest()


if __name__ == "__main__":
    raise SystemExit(main())
