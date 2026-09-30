#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL237_NumberingSystem v0108 — 薄尾:活檔判定只看目錄 · 只增稽核 audit · --apply 寫完自核(遺失 / 改身分 / 重號 → 整批還原)

實測(側線 2026-09-29 i,PR #375 頭 d1034c48a):NOT_LIVE 的 `_quarantine` 拿整條路徑做子字串比對,活檔
supportive modules/network/vdf_akshare_dedup_invalid_quarantine_gate_v02783.py 因為檔名含 invalid_quarantine 被當成隔離夾,
編號冊一直沒號(Z280 當時記成「只認四碼」,實測不是)。全樹 5,727 支活碼檔只有這一支是被檔名誤排。
  ① live_files():NOT_LIVE 只比對目錄那一段,檔名不算;活檔只會變多、不會變少(只增)。
  ② audit [--base <ref>] [--json]:唯讀。現行編號冊對基準(預設 git merge-base HEAD origin/main,取不到就 HEAD)逐碼比:
     before · after · added · missing(基準有、現在沒有)· changed_identity(同一碼換了鍵)· duplicate_codes,
     欄位同 PR #375 的 NUMBERING_APPEND_AUDIT;另查冊內一致:分類碼連續 · 列上 cat_code = SSOT 分類表 ·
     SSOT books 的 n / sha 對得上檔 · 冊上宣告碼 ≠ 發出號的紅列。
  ③ --apply:寫之前留住每本冊的原位元組;寫完立刻用 ② 對寫前比,遺失 / 改身分 / 重號任一 > 0 → 全部還原、rc 2。
其餘整支照 v0107(乾跑、--full 語意、各類收集與發號都不動)。
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
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL237_NumberingSystem"
ENGINE = Path(__file__).stem


def _vnum(path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + ENGINE, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR.BASE
BOOK_RX = re.compile(r"^VIA_NumberBook_(?P<kind>[A-Z]+)(?:_(?P<sub>[A-Z0-9]+))?_v\d+\.jsonl$")
_V0107_LIVE = BASE.live_files


def __getattr__(name: str):
    return getattr(PRIOR, name)


# ---------------------------------------------------------------- ① live files: folder part only
def live_path(rel: str, tokens=None) -> bool:
    """A tracked path is live unless a NOT_LIVE token sits in its folder part (the file name never excludes it)."""
    folder = rel.rpartition("/")[0] + "/"
    return not any(t in folder for t in (BASE.NOT_LIVE if tokens is None else tokens))


def live_files(*patterns) -> list:
    out = subprocess.run(["git", "ls-files", *patterns], cwd=BASE.VIA, capture_output=True, text=True).stdout.splitlines()
    return [f for f in out if live_path(f)]


BASE.live_files = live_files


# ---------------------------------------------------------------- ② audit
def _identity(kind: str, row: dict):
    """What a code stands for: the content key (full rows) or the qualified name (compact CLS / FNC rows)."""
    return row.get("q") if kind in BASE.COMPACT else row.get("key")


def inventory(books: dict, ssot: dict | None) -> dict:
    """books: {file name: text}; ssot: the SSOT document. → {"codes": {code: (kind, identity)}, "dups": [...], "rows": n}"""
    codes, dups, n = {}, [], 0
    for name, text in sorted(books.items()):
        m = BOOK_RX.match(name)
        if not m:
            continue
        kind = m.group("kind")
        for line in text.splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            n += 1
            code = row.get("code")
            if code in codes:
                dups.append(code)
            codes[code] = (kind, _identity(kind, row))
    for kind in BASE.IN_SSOT:
        for row in ((ssot or {}).get("rows") or {}).get(kind) or []:
            n += 1
            code = row.get("code")
            if code in codes:
                dups.append(code)
            codes[code] = (kind, row.get("key"))
    return {"codes": codes, "dups": dups, "rows": n}


def compare(before: dict, after: dict) -> dict:
    """Append-only verdict between two inventories (same fields as PR #375 NUMBERING_APPEND_AUDIT)."""
    b, a = before["codes"], after["codes"]
    missing = sorted(c for c in b if c not in a)
    changed = sorted(c for c in b if c in a and a[c] != b[c])
    added = [c for c in a if c not in b]
    return {"before": before["rows"], "after": after["rows"], "added": len(added), "missing": missing,
            "changed_identity": changed, "duplicate_codes": len(after["dups"]), "duplicate_sample": sorted(set(after["dups"]))[:10]}


def integrity(books: dict, ssot: dict) -> list:
    """Consistency inside the current books: contiguous category codes · row cat_code = SSOT category · books meta n/sha · RED rows."""
    issues = []
    cats = ssot.get("categories") or {}
    for kind, table in sorted(cats.items()):
        nums = sorted(int(c.split("-C")[-1]) for c in table.values() if re.fullmatch(re.escape(kind) + r"-C\d+", str(c)))
        if nums != list(range(1, len(table) + 1)):
            issues.append({"rule": "分類碼不連續", "kind": kind, "n": len(table)})
    red = 0

    def row_check(kind, row):
        nonlocal red
        if row.get("cat") is not None and row.get("cat_code") is not None and (cats.get(kind) or {}).get(row["cat"]) != row["cat_code"]:
            issues.append({"rule": "列上分類碼 ≠ SSOT 分類表", "kind": kind, "code": row.get("code")})
        if row.get("lamp") == "RED":
            red += 1

    for name, text in books.items():
        m = BOOK_RX.match(name)
        if not m or m.group("kind") in BASE.COMPACT:
            continue
        for line in text.splitlines():
            if line.strip():
                row_check(m.group("kind"), json.loads(line))
    for kind in BASE.IN_SSOT:
        for row in (ssot.get("rows") or {}).get(kind) or []:
            row_check(kind, row)
    by_name = {Path(str(meta.get("file", ""))).name: meta for meta in _metas(ssot)}
    for name, text in books.items():
        meta = by_name.get(name)
        if meta is None:
            issues.append({"rule": "冊檔沒登在 SSOT books", "file": name})
            continue
        n = sum(1 for line in text.splitlines() if line.strip())
        if meta.get("n") != n or meta.get("sha") != hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]:
            issues.append({"rule": "SSOT books 的 n / sha 對不上檔", "file": name, "meta_n": meta.get("n"), "n": n})
    if red:
        issues.append({"rule": "紅列(冊上宣告碼 ≠ 發出號等;不改任何一邊)", "n": red})
    return issues


def _metas(ssot: dict) -> list:
    out = []
    for meta in (ssot.get("books") or {}).values():
        if meta.get("files"):
            out.extend(meta["files"].values())
        elif meta.get("file"):
            out.append(meta)
    return out


def _git(*args) -> tuple:
    r = subprocess.run(["git", *args], cwd=BASE.VIA, capture_output=True, text=True)
    return r.returncode, r.stdout


def base_ref() -> str:
    rc, out = _git("merge-base", "HEAD", "origin/main")
    return out.strip() if rc == 0 and out.strip() else "HEAD"


def _ssot_path() -> Path | None:
    return BASE._newest(HERE, "VIA_Numbering_SSOT_v*.json")


def current_state() -> tuple:
    books = {p.name: p.read_text(encoding="utf-8") for p in sorted(BASE.BOOK_DIR.glob("VIA_NumberBook_*.jsonl"))}
    sp = _ssot_path()
    return books, (json.loads(sp.read_text(encoding="utf-8")) if sp else {})


def state_at(ref: str) -> tuple:
    """Books and SSOT as committed at a git ref (paths relative to the VIA folder)."""
    rel_dir = BASE.BOOK_DIR.relative_to(BASE.VIA).as_posix()
    rc, listing = _git("ls-tree", "--name-only", ref, "--", rel_dir + "/")     # paths relative to the VIA folder (cwd), not the repo root
    books = {}
    for name in (Path(x).name for x in (listing.splitlines() if rc == 0 else [])):
        if BOOK_RX.match(name):
            rc2, text = _git("show", f"{ref}:./{rel_dir}/{name}")
            if rc2 == 0:
                books[name] = text
    sp = _ssot_path()
    ssot = {}
    if sp:
        rc3, text = _git("show", f"{ref}:./{sp.relative_to(BASE.VIA).as_posix()}")
        ssot = json.loads(text) if rc3 == 0 and text.strip() else {}
    return books, ssot


def audit(ref: str | None = None, before=None, after=None) -> dict:
    ref = ref or base_ref()
    b_books, b_ssot = before if before is not None else state_at(ref)
    a_books, a_ssot = after if after is not None else current_state()
    cmp = compare(inventory(b_books, b_ssot), inventory(a_books, a_ssot))
    issues = integrity(a_books, a_ssot)
    bad = bool(cmp["missing"] or cmp["changed_identity"] or cmp["duplicate_codes"])
    lamp = "RED" if bad else ("YELLOW" if issues else "GREEN")
    return {"engine": ENGINE, "baseline": ref, **cmp, "integrity": issues, "lamp": lamp}


def _print_audit(rep: dict, out=sys.stdout) -> None:
    print(f"[編號只增稽核] {rep['lamp']} · 基準 {str(rep['baseline'])[:12]} · 列 {rep['before']} → {rep['after']}(+{rep['added']})"
          f" · 遺失 {len(rep['missing'])} · 改身分 {len(rep['changed_identity'])} · 重號 {rep['duplicate_codes']}"
          f" · 冊內不一致 {len(rep['integrity'])}", file=out)
    for c in rep["missing"][:5]:
        print(f"  [遺失] {c}", file=out)
    for c in rep["changed_identity"][:5]:
        print(f"  [改身分] {c}", file=out)
    for i in rep["integrity"][:8]:
        print("  [冊內] " + " · ".join(f"{k} {v}" for k, v in i.items()), file=out)


# ---------------------------------------------------------------- ③ transactional --apply
def snapshot() -> dict:
    files = sorted(BASE.BOOK_DIR.glob("VIA_NumberBook_*.jsonl"))
    sp = _ssot_path() or BASE.SSOT_NEW
    return {"dir": BASE.BOOK_DIR, "ssot": sp, "bytes": {p: p.read_bytes() for p in files + ([sp] if sp.is_file() else [])}}


def restore(snap: dict) -> int:
    """Put every book back byte for byte; remove book files this run created. Returns the number of files touched."""
    n = 0
    for p, data in snap["bytes"].items():
        if not p.is_file() or p.read_bytes() != data:
            p.write_bytes(data)
            n += 1
    for p in snap["dir"].glob("VIA_NumberBook_*.jsonl"):
        if p not in snap["bytes"]:
            p.unlink()
            n += 1
    if snap["ssot"] not in snap["bytes"] and snap["ssot"].is_file():
        snap["ssot"].unlink()
        n += 1
    return n


def _texts(snap: dict) -> tuple:
    books = {p.name: data.decode("utf-8") for p, data in snap["bytes"].items() if p.parent == snap["dir"]}
    data = snap["bytes"].get(snap["ssot"])
    return books, (json.loads(data.decode("utf-8")) if data else {})


def guarded_apply(argv: list, runner=None) -> int:
    snap = snapshot()
    rc = (runner or PRIOR.main)(argv)
    rep = audit("寫前(本輪)", before=_texts(snap), after=current_state())
    _print_audit(rep, out=sys.stderr)
    if rep["lamp"] == "RED":
        n = restore(snap)
        print(f"[編號只增稽核] 寫入違反只增 → 已整批還原 {n} 檔,rc 2", file=sys.stderr)
        return 2
    return rc


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args:
        return selftest()
    if args[:1] == ["audit"] or "--apply" in args:
        if os.environ.get("VIA_FROM_VCGC") != "YES":
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
    if "--apply" in args:
        return guarded_apply(argv if argv is not None else sys.argv[1:])
    return PRIOR.main(argv)


# ---------------------------------------------------------------- selftest
def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    toks = ("references/", "VIA_Reports/", "_quarantine", "RUN_2026")
    cases = {"supportive modules/network/x_invalid_quarantine_gate_v02783.py": True, "a/_quarantine/x_v0100.py": False,
             "VIA_Reports/y_v0100.py": False, "a/RUN_20260617_1/z.py": False, "ok/RUN_2026_note_v0100.py": True}
    chk("① 活檔只看目錄:檔名含隔離字樣不算隔離,目錄才算", all(live_path(p, toks) is v for p, v in cases.items()),
        {p.split('/')[-1]: live_path(p, toks) for p in cases})
    chk("② 本版裝進本體(收集器呼叫的就是本版)", BASE.live_files is live_files)
    target = "supportive modules/network/vdf_akshare_dedup_invalid_quarantine_gate_v02783.py"
    tracked = target in _V0107_LIVE("*.py") or target in subprocess.run(["git", "ls-files", target], cwd=BASE.VIA,
                                                                          capture_output=True, text=True).stdout
    now = live_files("*.py")
    chk("③ 實樹:被檔名誤排的活檔現在收得到,其餘判定一支不少", (not tracked or target in now) and set(_V0107_LIVE("*.py")) <= set(now),
        f"舊 {len(_V0107_LIVE('*.py'))} → 新 {len(now)}")
    b = {"VIA_NumberBook_MDL_v0100.jsonl": '{"code":"VIA-A-MDL001","key":"a@v1"}\n{"code":"VIA-A-MDL002","key":"b@v1"}\n',
         "VIA_NumberBook_FNC_A_v0100.jsonl": '{"code":"VIA-A-MDL001-FNC001","q":"main"}\n'}
    a_ok = dict(b, **{"VIA_NumberBook_MDL_v0100.jsonl": b["VIA_NumberBook_MDL_v0100.jsonl"] + '{"code":"VIA-A-MDL003","key":"c@v1"}\n'})
    s0 = {"rows": {"SSOT": [{"code": "VIA-A-SSOT001", "key": "s@v1"}]}}
    r_ok = compare(inventory(b, s0), inventory(a_ok, s0))
    chk("④ 只增:新增 1 · 遺失 0 · 改身分 0 · 重號 0", (r_ok["added"], r_ok["missing"], r_ok["changed_identity"], r_ok["duplicate_codes"]) == (1, [], [], 0), r_ok)
    a_bad = {"VIA_NumberBook_MDL_v0100.jsonl": '{"code":"VIA-A-MDL001","key":"a@v2"}\n{"code":"VIA-A-MDL001","key":"a@v2"}\n',
             "VIA_NumberBook_FNC_A_v0100.jsonl": '{"code":"VIA-A-MDL001-FNC001","q":"other"}\n'}
    r_bad = compare(inventory(b, s0), inventory(a_bad, {}))
    chk("⑤ 反控:遺失(MDL002 · SSOT001)· 改身分(MDL001 · FNC001)· 重號 都抓得到",
        r_bad["missing"] == ["VIA-A-MDL002", "VIA-A-SSOT001"] and r_bad["changed_identity"] == ["VIA-A-MDL001", "VIA-A-MDL001-FNC001"]
        and r_bad["duplicate_codes"] == 1, r_bad)
    books = {"VIA_NumberBook_MDL_v0100.jsonl": '{"code":"VIA-A-MDL001","cat":"x","cat_code":"MDL-C001","key":"a"}\n'}
    sha = hashlib.sha256(books["VIA_NumberBook_MDL_v0100.jsonl"].encode()).hexdigest()[:16]
    good = {"categories": {"MDL": {"x": "MDL-C001"}}, "books": {"MDL": {"file": "r/VIA_NumberBook_MDL_v0100.jsonl", "n": 1, "sha": sha}}, "rows": {}}
    chk("⑥ 冊內一致:乾淨冊 0 項", integrity(books, good) == [], integrity(books, good))
    bad = {"categories": {"MDL": {"x": "MDL-C002"}}, "books": {"MDL": {"file": "r/VIA_NumberBook_MDL_v0100.jsonl", "n": 2, "sha": sha}}, "rows": {}}
    rules = sorted({i["rule"] for i in integrity(books, bad)})
    chk("⑦ 反控:分類碼不連續 · 列上分類碼不符 · n/sha 不符 都抓得到",
        rules == ["SSOT books 的 n / sha 對不上檔", "分類碼不連續", "列上分類碼 ≠ SSOT 分類表"], rules)
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        (d / "VIA_NumberBook_MDL_v0100.jsonl").write_bytes(b'{"code":"VIA-A-MDL001","key":"a"}\n')
        (d / "VIA_Numbering_SSOT_v0100.json").write_bytes(b'{"rows":{}}\n')
        saved = (BASE.BOOK_DIR, BASE._newest)
        BASE.BOOK_DIR = d
        BASE._newest = lambda folder, pat: (d / "VIA_Numbering_SSOT_v0100.json") if "Numbering_SSOT" in pat else saved[1](folder, pat)
        try:
            def bad_writer(_argv):
                (d / "VIA_NumberBook_MDL_v0100.jsonl").write_text('{"code":"VIA-A-MDL009","key":"z"}\n', encoding="utf-8")
                (d / "VIA_NumberBook_ENV_v0100.jsonl").write_text('{"code":"VIA-A-ENV001","key":"e"}\n', encoding="utf-8")
                return 0

            def good_writer(_argv):
                p = d / "VIA_NumberBook_MDL_v0100.jsonl"
                p.write_text(p.read_text(encoding="utf-8") + '{"code":"VIA-A-MDL002","key":"b"}\n', encoding="utf-8")
                return 0
            import io
            import contextlib
            with contextlib.redirect_stderr(io.StringIO()):
                rc_bad = guarded_apply(["--apply"], runner=bad_writer)
            restored = (d / "VIA_NumberBook_MDL_v0100.jsonl").read_bytes() == b'{"code":"VIA-A-MDL001","key":"a"}\n' and not (d / "VIA_NumberBook_ENV_v0100.jsonl").exists()
            with contextlib.redirect_stderr(io.StringIO()):
                rc_good = guarded_apply(["--apply"], runner=good_writer)
            kept = "VIA-A-MDL002" in (d / "VIA_NumberBook_MDL_v0100.jsonl").read_text(encoding="utf-8")
        finally:
            BASE.BOOK_DIR, BASE._newest = saved
    chk("⑧ --apply 寫後自核:丟號的寫入整批還原(rc 2、多出的冊刪掉),只增的寫入留下", rc_bad == 2 and restored and rc_good == 0 and kept,
        f"壞 rc {rc_bad} 還原 {restored} · 好 rc {rc_good} 留下 {kept}")
    hb, hs = state_at("HEAD")
    chk("⑩ 基準取得:HEAD 的冊與 SSOT 讀得到(路徑相對 VIA 夾,不是倉根)", len(hb) > 0 and bool(hs.get("rows")),
        f"冊 {len(hb)} 本 · SSOT 列類 {len(hs.get('rows') or {})}")
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑨ 檔頭 · 加速器橋 · 網路橋在;不碰 TA-Lib", "VIA:ACCEL-BRIDGE" in text and "VIA:NET-BRIDGE" in text
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M))
    print(f"[編號 v0108] 本版 {sum(ok)}/{len(ok)}")
    if not all(ok):
        return 1
    return PRIOR.selftest()


if __name__ == "__main__":
    raise SystemExit(main())
