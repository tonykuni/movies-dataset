#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL276_QuarantineRecover v0100 — 隔離區找回:丟失的檔先到隔離區(VIA_RetiredEngines)找,再到 git 歷史找,單檔還原

操作員 2026-10-14:「丟失的文件可到隔離區尋找」。盤點(唯讀):隔離區 = functional modules/VIA_RetiredEngines/ 與 VIA_RetiredEngines/
(退役以搬代刪;RETIRE_MANIFEST*.json 記 from → to + sha256;batch581 記 retired → canonical;570 · 573 兩批沒有清單)。
工具鏈清單點名的 VIA_Recover(「定位並自隔離區還原」)樹上不存在 —— 本支補上,只做那件事:
  index            建隔離區索引:清單的每一筆 + 沒清單批次的檔(去掉批次前綴推回原路徑)→ VIA_Reports/quarantine/QUARANTINE_INDEX_latest.json
  lost             掃登記冊引用但樹上不在的檔(元件冊 ACTIVE 的 source · 交接冊 managed_modules / watch · 需求冊尾版 homes),逐筆標
                   IN_QUARANTINE(隔離區有,附 sha)· IN_GIT(git 歷史刪除過,附提交)· NOT_FOUND
  find <字串>      檔名 / 路徑片段在隔離區與 git 歷史裡找
  restore <原路徑> [--apply]   從隔離區**複製**回原路徑(隔離區留證據,只增)、核 sha256;隔離區沒有就從 git 該檔刪除前的提交取回。
                   目的地已有檔 = 拒絕(不覆蓋);預設乾跑;寫入只增帳 registry/VIA_Quarantine_Restore_Ledger_v0100.jsonl
只收 VCGC 呼叫;零網路;不刪、不搬隔離區裡的任何檔。
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
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
ENGINE = Path(__file__).stem
ZONES = ("functional modules/VIA_RetiredEngines", "VIA_RetiredEngines")
LEDGER = "supportive modules/registry/VIA_Quarantine_Restore_Ledger_v0100.jsonl"
REPORT = "VIA_Reports/quarantine"
BATCH_RX = re.compile(r"^batch\d+[^/]*$")
VNUM = re.compile(r"_v(\d+)$")


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _json(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


# ---------------------------------------------------------------- index
def build_index(via: Path = VIA) -> list:
    """Every quarantined file: original path · quarantine path · sha256 (from the manifest when it has one) · batch · source."""
    via = Path(via)
    rows, seen = [], set()
    for zone in ZONES:
        zdir = via / zone
        if not zdir.is_dir():
            continue
        for batch in sorted(p for p in zdir.iterdir() if p.is_dir()):
            for man in sorted(batch.glob("*manifest*.json")) + sorted(batch.glob("RETIRE_MANIFEST*.json")):
                d = _json(man)
                if not isinstance(d, dict):
                    continue
                for m in d.get("moves") or []:
                    if isinstance(m, dict) and m.get("from") and m.get("to") and m["to"] not in seen:
                        seen.add(m["to"])
                        rows.append({"orig": m["from"], "qpath": m["to"], "sha256": m.get("sha256", ""), "batch": batch.name, "source": "manifest"})
                for it in d.get("items") or []:
                    if isinstance(it, dict) and it.get("retired"):
                        q = str((batch / Path(it["retired"]).name).relative_to(via))
                        if q not in seen:
                            seen.add(q)
                            rows.append({"orig": it["retired"], "qpath": q, "sha256": it.get("sha256", ""), "batch": batch.name,
                                         "source": "manifest", "canonical": it.get("canonical", "")})
            for f in batch.rglob("*"):
                if not f.is_file() or "manifest" in f.name.lower() or f.name.startswith("undo_retire"):
                    continue
                q = str(f.relative_to(via))
                if q in seen:
                    continue
                seen.add(q)
                rel = f.relative_to(batch)
                rows.append({"orig": str(rel), "qpath": q, "sha256": "", "batch": batch.name, "source": "inferred"})
    return rows


# ---------------------------------------------------------------- git
def _git(args: list, cwd: Path) -> str:
    try:
        r = subprocess.run(["git"] + args, cwd=str(cwd), capture_output=True, text=True, timeout=120)
        return r.stdout if r.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def git_deleted(via: Path, needle: str) -> list:
    """(commit, repo path) pairs where a path containing `needle` was deleted; newest first."""
    out = _git(["log", "--all", "--diff-filter=D", "--name-only", "--format=@@%H", "--", "."], via)
    hits, commit = [], ""
    for ln in out.splitlines():
        if ln.startswith("@@"):
            commit = ln[2:]
        elif ln and needle in ln:
            hits.append({"commit": commit, "path": ln})
    return hits


def _repo_root(via: Path) -> Path:
    top = _git(["rev-parse", "--show-toplevel"], via).strip()
    return Path(top) if top else via.parent


# ---------------------------------------------------------------- lost
def registered_refs(via: Path) -> list:
    """(where, path relative to VIA) for every concrete file the books say should exist."""
    reg = via / "supportive modules" / "registry"
    refs = []
    inv = _json(reg / "VIA_Component_Inventory_SSOT_v0100.json") or {}
    for r in inv.get("records") or []:
        s = str(r.get("source") or "")
        if r.get("state") == "ACTIVE" and "/" in s and Path(s).suffix:
            refs.append(("component_inventory", s))
    ho = _json(reg / "VIA_Handoff_Continuity_SSOT_v0100.json") or {}
    for key in ("managed_modules", "watch"):
        for s in ho.get(key) or []:
            if isinstance(s, str) and "*" not in s:
                refs.append(("handoff." + key, s))
    reqs = sorted(reg.glob("VIA_Requirements_SSOT_v*.json"), key=lambda p: int(VNUM.search(p.stem).group(1)) if VNUM.search(p.stem) else -1)
    rq = _json(reqs[-1]) if reqs else {}
    for r in (rq or {}).get("requirements") or []:
        for h in r.get("homes") or []:
            if isinstance(h, str) and "*" not in h and Path(h).suffix in (".py", ".ps1", ".json", ".md", ".jsonl"):
                p = h if "/" in h else "supportive modules/registry/" + h
                refs.append(("requirements." + str(r.get("code")), p))
    out, seen = [], set()
    for w, p in refs:
        if p not in seen:
            seen.add(p)
            out.append((w, p))
    return out


def lost(via: Path = VIA, index: list | None = None, with_git: bool = True) -> list:
    via = Path(via)
    index = build_index(via) if index is None else index
    by_orig = {}
    for r in index:
        by_orig.setdefault(r["orig"], r)
        by_orig.setdefault(Path(r["orig"]).name, r)
    rows = []
    names = None
    for where, p in registered_refs(via):
        if (via / p).exists():
            continue
        if where.startswith("requirements.") and p.startswith("supportive modules/registry/") and p.count("/") == 2:
            if names is None:  # 需求冊 homes 常只寫檔名:倉內任一處有同名檔就算在(不誤報)
                root = via.parent if (via.parent / ".git").exists() else via
                names = {f.name for f in root.rglob("*") if f.is_file() and ".git" not in f.parts}
            if Path(p).name in names:
                continue
        q = by_orig.get(p) or by_orig.get(Path(p).name)
        row = {"path": p, "where": where}
        if q:
            row.update(state="IN_QUARANTINE", qpath=q["qpath"], sha256=q["sha256"], batch=q["batch"])
        else:
            g = git_deleted(via, Path(p).name)[:1] if with_git else []
            row.update(state="IN_GIT", commit=g[0]["commit"], gitpath=g[0]["path"]) if g else row.update(state="NOT_FOUND")
        rows.append(row)
    return rows


# ---------------------------------------------------------------- restore
def restore(via: Path, orig: str, apply: bool = False, index: list | None = None) -> dict:
    via = Path(via)
    dest = via / orig
    if dest.exists():
        return {"state": "REFUSED", "why": "目的地已有檔(不覆蓋)", "path": orig}
    index = build_index(via) if index is None else index
    q = next((r for r in index if r["orig"] == orig), None) or next((r for r in index if Path(r["orig"]).name == Path(orig).name), None)
    if q:
        src = via / q["qpath"]
        got = sha256(src)
        if q["sha256"] and got != q["sha256"]:
            return {"state": "REFUSED", "why": "隔離區檔的 sha256 與清單不符", "path": orig, "qpath": q["qpath"]}
        res = {"state": "PLAN" if not apply else "RESTORED", "path": orig, "from": q["qpath"], "sha256": got, "kind": "quarantine"}
        if apply:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            if sha256(dest) != got:
                return {"state": "FAILED", "why": "複製後 sha256 不符", "path": orig}
            _ledger(via, res)
        return res
    g = git_deleted(via, Path(orig).name)
    if not g:
        return {"state": "NOT_FOUND", "path": orig}
    root = _repo_root(via)
    blob = subprocess.run(["git", "show", f"{g[0]['commit']}^:{g[0]['path']}"], cwd=str(root), capture_output=True, timeout=120)
    if blob.returncode != 0:
        return {"state": "NOT_FOUND", "path": orig, "why": "git 取不回"}
    res = {"state": "PLAN" if not apply else "RESTORED", "path": orig, "from": f"git {g[0]['commit'][:12]}^:{g[0]['path']}",
           "sha256": hashlib.sha256(blob.stdout).hexdigest(), "kind": "git"}
    if apply:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(blob.stdout)
        _ledger(via, res)
    return res


def _ledger(via: Path, row: dict) -> None:
    p = via / LEDGER
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(dict(row, ts=now_utc(), engine=ENGINE), ensure_ascii=False) + "\n")


def _write(via: Path, name: str, obj) -> str:
    d = via / REPORT
    d.mkdir(parents=True, exist_ok=True)
    (d / name).write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return str((d / name).relative_to(via))


# ---------------------------------------------------------------- CLI
def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a:
        return selftest()
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False))
        return 2
    verb = a[0] if a else "lost"
    if verb == "index":
        idx = build_index(VIA)
        rep = _write(VIA, "QUARANTINE_INDEX_latest.json", {"at": now_utc(), "engine": ENGINE, "files": len(idx), "rows": idx})
        print(f"[隔離區] 索引 {len(idx)} 檔 · 有清單 {sum(r['source'] == 'manifest' for r in idx)} · 推回原路徑 {sum(r['source'] == 'inferred' for r in idx)} · {rep}")
        return 0
    if verb == "lost":
        rows = lost(VIA)
        c = {s: sum(r["state"] == s for r in rows) for s in ("IN_QUARANTINE", "IN_GIT", "NOT_FOUND")}
        rep = _write(VIA, "LOST_latest.json", {"at": now_utc(), "engine": ENGINE, "counts": c, "rows": rows})
        lamp = "GREEN" if not rows else ("RED" if c["NOT_FOUND"] else "YELLOW")
        print(f"[隔離區找回] {lamp} · 登記冊引用但樹上不在 {len(rows)} · 隔離區有 {c['IN_QUARANTINE']} · git 有 {c['IN_GIT']} · 找不到 {c['NOT_FOUND']} · {rep}")
        for r in rows[:20]:
            print(f"  {r['state']:<13} {r['path']}  ← {r.get('qpath') or r.get('gitpath') or '-'}")
        return 0 if lamp == "GREEN" else (1 if lamp == "RED" else 2)
    if verb == "find" and len(a) > 1:
        needle = a[1]
        q = [r for r in build_index(VIA) if needle in r["orig"] or needle in r["qpath"]]
        g = git_deleted(VIA, needle)
        for r in q[:30]:
            print(f"  隔離區  {r['orig']}  →  {r['qpath']}")
        for r in g[:30]:
            print(f"  git     {r['path']}  @ {r['commit'][:12]}")
        print(f"[隔離區找] 「{needle}」隔離區 {len(q)} · git {len(g)}")
        return 0 if (q or g) else 2
    if verb == "restore" and len(a) > 1:
        r = restore(VIA, a[1], apply="--apply" in a)
        print(json.dumps(r, ensure_ascii=False))
        return 0 if r["state"] in ("PLAN", "RESTORED") else (2 if r["state"] == "NOT_FOUND" else 1)
    print("用法:index | lost | find <字串> | restore <原路徑> [--apply] | --selftest")
    return 2


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    with tempfile.TemporaryDirectory() as tmp:
        via = Path(tmp)
        reg = via / "supportive modules" / "registry"
        reg.mkdir(parents=True)
        b1 = via / "functional modules" / "VIA_RetiredEngines" / "batch900_wave1"
        (b1 / "supportive modules" / "registry").mkdir(parents=True)
        q1 = b1 / "supportive modules" / "registry" / "CGC_MDL900_Gone_v0100.py"
        q1.write_text("print('gone')\n", encoding="utf-8")
        man = {"moves": [{"from": "supportive modules/registry/CGC_MDL900_Gone_v0100.py",
                          "to": str(q1.relative_to(via)), "sha256": sha256(q1)}]}
        (b1 / "RETIRE_MANIFEST.json").write_text(json.dumps(man), encoding="utf-8")
        b2 = via / "functional modules" / "VIA_RetiredEngines" / "batch901_nomanifest" / "supportive modules" / "registry"
        b2.mkdir(parents=True)
        (b2 / "CGC_MDL901_Orphan_v0100.py").write_text("x = 1\n", encoding="utf-8")
        (reg / "CGC_MDL902_Here_v0100.py").write_text("y = 2\n", encoding="utf-8")
        inv = {"records": [
            {"source": "supportive modules/registry/CGC_MDL900_Gone_v0100.py", "state": "ACTIVE"},
            {"source": "supportive modules/registry/CGC_MDL901_Orphan_v0100.py", "state": "ACTIVE"},
            {"source": "supportive modules/registry/CGC_MDL902_Here_v0100.py", "state": "ACTIVE"},
            {"source": "supportive modules/registry/CGC_MDL903_Nowhere_v0100.py", "state": "ACTIVE"},
            {"source": "supportive modules/registry/CGC_MDL904_Retired_v0100.py", "state": "RETIRED"},
            {"source": "EnvBaseline:pwsh", "state": "ACTIVE"}]}
        (reg / "VIA_Component_Inventory_SSOT_v0100.json").write_text(json.dumps(inv), encoding="utf-8")
        idx = build_index(via)
        chk("① 索引:清單那筆帶 sha256 與原路徑 · 沒清單的批次去掉批次前綴推回原路徑",
            any(r["source"] == "manifest" and r["orig"].endswith("CGC_MDL900_Gone_v0100.py") and r["sha256"] for r in idx)
            and any(r["source"] == "inferred" and r["orig"] == "supportive modules/registry/CGC_MDL901_Orphan_v0100.py" for r in idx), len(idx))
        rows = lost(via, idx, with_git=False)
        st = {Path(r["path"]).name: r["state"] for r in rows}
        (via / "elsewhere").mkdir()
        (via / "elsewhere" / "VIA_Home_SSOT_v0100.json").write_text("{}", encoding="utf-8")
        (reg / "VIA_Requirements_SSOT_v0100.json").write_text(json.dumps({"requirements": [
            {"code": "R1", "homes": ["VIA_Home_SSOT_v0100.json", "VIA_Absent_SSOT_v0100.json"]}]}), encoding="utf-8")
        rows = lost(via, idx, with_git=False)
        st = {Path(r["path"]).name: r["state"] for r in rows}
        chk("②b 需求冊 homes 只寫檔名:倉內別處有同名檔 = 在(不誤報)· 哪裡都沒有 = NOT_FOUND",
            "VIA_Home_SSOT_v0100.json" not in st and st.get("VIA_Absent_SSOT_v0100.json") == "NOT_FOUND", st)
        st.pop("VIA_Absent_SSOT_v0100.json", None)
        chk("② 丟失掃描:只看 ACTIVE 的具體檔(RETIRED · 假 id 不算)· 在樹上的不報 · 隔離區有 / 找不到分開",
            st == {"CGC_MDL900_Gone_v0100.py": "IN_QUARANTINE", "CGC_MDL901_Orphan_v0100.py": "IN_QUARANTINE",
                   "CGC_MDL903_Nowhere_v0100.py": "NOT_FOUND"}, st)
        plan = restore(via, "supportive modules/registry/CGC_MDL900_Gone_v0100.py", apply=False, index=idx)
        chk("③ 還原預設乾跑:不寫檔", plan["state"] == "PLAN" and not (reg / "CGC_MDL900_Gone_v0100.py").exists())
        done = restore(via, "supportive modules/registry/CGC_MDL900_Gone_v0100.py", apply=True, index=idx)
        led = (via / LEDGER).read_text(encoding="utf-8").splitlines()
        chk("④ --apply:複製回原路徑(隔離區那份還在)· sha256 相符 · 只增帳記一行",
            done["state"] == "RESTORED" and (reg / "CGC_MDL900_Gone_v0100.py").read_text() == "print('gone')\n" and q1.exists()
            and len(led) == 1 and json.loads(led[0])["kind"] == "quarantine")
        again = restore(via, "supportive modules/registry/CGC_MDL900_Gone_v0100.py", apply=True, index=idx)
        q1.write_text("tampered\n", encoding="utf-8")
        (reg / "CGC_MDL900_Gone_v0100.py").unlink()
        bad = restore(via, "supportive modules/registry/CGC_MDL900_Gone_v0100.py", apply=True, index=idx)
        chk("⑤ 目的地已有檔 = 拒絕(不覆蓋)· 隔離區檔被改過(sha 不符)= 拒絕", again["state"] == "REFUSED" and bad["state"] == "REFUSED"
            and "sha256" in bad["why"], (again["state"], bad["state"]))
    real = build_index(VIA)
    src = Path(__file__).read_text(encoding="utf-8")
    os.environ.pop("VIA_FROM_VCGC", None)
    denied = main(["lost"]) == 2
    os.environ["VIA_FROM_VCGC"] = "YES"
    chk("⑥ 實樹隔離區索引得動 · 只收 VCGC · 加速器橋在 · 不碰 TA-Lib", len(real) > 0 and denied and "VIA:ACCEL-BRIDGE" in src
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M), f"實樹 {len(real)} 檔")
    print(f"  {ENGINE} selftest {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
