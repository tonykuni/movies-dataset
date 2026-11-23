#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VCGC_CommandHub_v0103.py — 薄尾(v0102 以前一字不動):舊版退役 = 先在編號冊標退役 → 再證明 → 才搬走

操作員 2026-11-23:「同意 先在編號冊標退役再證明後搬走」。
v0102 實測:VDF / VRN / VCGC 舊版有 1,346 支仍登在活冊上,拿掉後 MDL276 lost 與元件冊 stale 上升 → 閘擋下。
容器 worktree 實驗(VDF 150 支):拿掉後 lost 1→14、stale 0→56;跑 VCGC registry-sync --apply 標 RETIRED 後 lost 回 1、stale 0,
但 registry-sync 沒有範圍參數,會順帶登 120 支無關新檔;MDL237 --scope 對已不在的檔不寫 gone_since(只有全量 apply 才寫)。
所以本版加「只標本批」的退役標記,算法照兩個引擎本身、範圍只限本批檔:
  ① 中央元件冊(VIA_Component_Inventory_SSOT):叫 VCGC 主控台自己的 registry_sync,寫到 TEMP 複本(引擎支援 path 參數);
     只把「來源 = 本批檔」的記錄照引擎結果併回(ACTIVE → RETIRED + retired_at;或來源換到活檔),其餘新列 / 變更一律不帶。
  ② 編號冊(VIA_NumberBooks/*.jsonl):來源 = 本批檔的列補 gone_since(MDL237 的時間格式)與 lamp AMBER;號不改不刪,
     其他行位元組不動(只重寫被標的那幾行)。
  ③ 寫冊:作業系統檔案鎖 + 唯一暫存檔名 + 原子換檔。
退役流程(via-prune --prove --apply):
  證明(git worktree,TEMP):量基準 → git rm 候選 → ①② 標退役 → 再量(家族尾版載入 · 五入口自測 · MDL276 lost ·
       registry stale · MDL237 遺失/改身分/重號 · SDD 每條規則)→ 有不過就把牽連的家族 / 檔剔除,換新 worktree 重證(最多 3 輪)。
  搬:主樹 git mv 證過的 → ①② 標退役(同一套算法)→ 再跑 VCGC 檢查,比搬前變差就整批還原;RETIRE_MANIFEST 記搬移 + 標記數。
不碰:VDF / VRN 自己的冊(各自發號)、凍結來源、鎖定帳點名的、程式碼點名的。
用法同 v0102;prune 預設類別加 REG_REF(活冊有登記的,先標退役再證)。| --selftest
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

import contextlib
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

VERSION = "v0103"
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
P1 = PRIOR.PRIOR                     # v0101
P0 = PRIOR.P0                        # v0100


def __getattr__(name):
    return getattr(PRIOR, name)


CODE_ROOT = PRIOR.CODE_ROOT
find_tail, _probe, _vcgc_metrics, _worse = PRIOR.find_tail, PRIOR._probe, PRIOR._vcgc_metrics, PRIOR._worse
REGISTRY_REL = Path("supportive modules") / "registry"
COMPONENT_BOOK = REGISTRY_REL / "VIA_Component_Inventory_SSOT_v0100.json"
NUMBER_BOOKS = REGISTRY_REL / "VIA_NumberBooks"
_NAME_RX = re.compile(r"[A-Za-z0-9_\-]+_v\d{4}\.py")


# ------------------------------------------------------------------------------
# ③ 寫冊:檔案鎖 + 唯一暫存 + 原子換檔
# ------------------------------------------------------------------------------
@contextlib.contextmanager
def file_lock(target: Path, wait: float = 120.0):
    """作業系統檔案鎖(鎖檔放 TEMP,以目標路徑雜湊命名;不刪別人的鎖、不在倉裡留檔)。"""
    d = Path(tempfile.gettempdir()) / "via_book_locks"
    d.mkdir(parents=True, exist_ok=True)
    lk = d / (hashlib.sha256(str(Path(target).resolve()).encode()).hexdigest()[:24] + ".lock")
    fh = open(lk, "a+b")
    t0 = time.time()
    try:
        while True:
            try:
                if os.name == "nt":
                    import msvcrt
                    fh.seek(0)
                    msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError:
                if time.time() - t0 > wait:
                    raise TimeoutError(f"冊被別的行程鎖住超過 {wait:.0f}s:{target}")
                time.sleep(0.5)
        yield
    finally:
        try:
            if os.name == "nt":
                import msvcrt
                fh.seek(0)
                msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
        except OSError:
            pass
        fh.close()


def atomic_write_bytes(path: Path, data: bytes) -> None:
    tmp = path.with_name(f".{path.name}.{os.getpid()}.{uuid.uuid4().hex[:8]}.tmp")
    tmp.write_bytes(data)
    os.replace(tmp, path)


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S +0000")      # MDL237 編號冊時間格式


# ------------------------------------------------------------------------------
# ① 中央元件冊:引擎算、只帶本批
# ------------------------------------------------------------------------------
_ENGINE_SNIPPET = r"""
import contextlib, importlib.util, io, json, shutil, sys
from pathlib import Path
V, src, dst = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
shutil.copy2(src, dst)
s = importlib.util.spec_from_file_location("vcgc_console_for_retire", V)
m = importlib.util.module_from_spec(s)
sys.modules[s.name] = m
with contextlib.redirect_stdout(io.StringIO()):
    s.loader.exec_module(m)
    r = m.registry_sync(True, dst)
print("RS_JSON " + json.dumps({k: r.get(k) for k in ("state", "new", "stale", "changed")}))
"""


def engine_component_sync(via: Path, timeout: int = 900) -> tuple[Path | None, dict]:
    """VCGC 主控台自己的 registry_sync 寫到 TEMP 複本;回(複本路徑, 引擎摘要)。"""
    V = find_tail("CGC_MDL149_VeritasCentralGovernanceConsole", [via])
    book = via / COMPONENT_BOOK
    if not V or not book.is_file():
        return None, {"error": "主控台尾版或元件冊不在"}
    dst = Path(tempfile.mkdtemp(prefix="via_regsync_")) / book.name
    cp = subprocess.run([sys.executable, "-c", _ENGINE_SNIPPET, str(V), str(book), str(dst)], cwd=str(via), capture_output=True,
                        text=True, encoding="utf-8", errors="replace", timeout=timeout, env=PRIOR._child_env(root=via))
    m = re.search(r"RS_JSON (\{.*\})", cp.stdout or "")
    if cp.returncode != 0 or not m or not dst.is_file():
        return None, {"error": f"引擎同步失敗 rc {cp.returncode}", "tail": ((cp.stdout or "") + (cp.stderr or ""))[-400:]}
    return dst, json.loads(m.group(1))


def merge_component_retire(real: dict, synced: dict, moved: set[str]) -> dict:
    """只併「來源 = 本批檔」且原本 ACTIVE 的記錄:引擎標 RETIRED 的照標;引擎把來源換到活檔的照換。其他一律不帶。"""
    tby = {r.get("key"): r for r in synced.get("records", []) if r.get("key")}
    retired, resourced = [], []
    for r in real.get("records", []):
        if r.get("state", "ACTIVE") != "ACTIVE" or r.get("source") not in moved:
            continue
        t = tby.get(r.get("key"))
        if not t:
            continue
        if t.get("state") == "RETIRED":
            r["state"] = "RETIRED"
            r["retired_at"] = t.get("retired_at") or datetime.now().isoformat(timespec="seconds")
            retired.append(r["key"])
        elif t.get("source") != r.get("source"):
            for k in ("category", "identity", "source", "line", "via"):
                if k in t:
                    r[k] = t[k]
            r["changed_at"] = t.get("changed_at") or datetime.now().isoformat(timespec="seconds")
            resourced.append(r["key"])
    return {"retired": retired, "resourced": resourced}


def mark_component_book(via: Path, moved: set[str], apply: bool) -> dict:
    synced_path, eng = engine_component_sync(via)
    if synced_path is None:
        return {"error": eng.get("error"), "detail": eng.get("tail", "")}
    try:
        book = via / COMPONENT_BOOK
        with file_lock(book):
            real = json.loads(book.read_text(encoding="utf-8"))
            synced = json.loads(synced_path.read_text(encoding="utf-8"))
            res = merge_component_retire(real, synced, moved)
            if apply and (res["retired"] or res["resourced"]):
                real["updated_at"] = datetime.now().isoformat(timespec="seconds")
                real.setdefault("retire_batches", []).append({"by": f"{FAMILY} {VERSION} prune", "at": real["updated_at"],
                                                              "retired": len(res["retired"]), "resourced": len(res["resourced"])})
                atomic_write_bytes(book, (json.dumps(real, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))
    finally:
        shutil.rmtree(synced_path.parent, ignore_errors=True)
    return {"retired": len(res["retired"]), "resourced": len(res["resourced"]),
            "engine_new_ignored": eng.get("new"), "engine_stale": eng.get("stale"), "engine_changed": eng.get("changed")}


# ------------------------------------------------------------------------------
# ② 編號冊:來源 = 本批檔的列補 gone_since(號不改不刪;其他行位元組不動)
# ------------------------------------------------------------------------------
def mark_numberbook_text(data: bytes, moved: set[str], stamp: str) -> tuple[bytes, int]:
    names = {Path(m).name.encode() for m in moved}
    out, n = [], 0
    for line in data.split(b"\n"):
        if line.strip() and any(nm in line for nm in names):
            try:
                row = json.loads(line)
            except ValueError:
                out.append(line)
                continue
            if row.get("source") in moved and not row.get("gone_since"):
                row["gone_since"] = stamp
                row["lamp"] = "AMBER"
                line = json.dumps(row, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
                n += 1
        out.append(line)
    return b"\n".join(out), n


def mark_number_books(via: Path, moved: set[str], apply: bool, stamp: str | None = None) -> dict:
    stamp = stamp or _stamp()
    per = {}
    for book in sorted((via / NUMBER_BOOKS).glob("*.jsonl")):
        with file_lock(book):
            data = book.read_bytes()
            new, n = mark_numberbook_text(data, moved, stamp)
            if n:
                per[book.name] = n
                if apply:
                    atomic_write_bytes(book, new)
    return {"rows": sum(per.values()), "books": per, "stamp": stamp}


def retire_mark(via: Path, moved_paths: list[str], apply: bool = True) -> dict:
    moved = set(moved_paths)
    return {"component": mark_component_book(via, moved, apply), "numberbooks": mark_number_books(via, moved, apply)}


# ------------------------------------------------------------------------------
# 證明(標退役 → 再量;失敗自動剔除重證,最多 3 輪)
# ------------------------------------------------------------------------------
def _fam_of(rel: str) -> tuple[str, str]:
    return str(Path(rel).parent), re.sub(r"_v\d{4}$", "", Path(rel).stem)


def prune_prove(via: Path, cands: list[dict], log=print, lanes: int = 4, rounds: int = 3) -> dict:
    from concurrent.futures import ThreadPoolExecutor
    top = Path(subprocess.run(["git", "-C", str(via), "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip())
    sub = via.resolve().relative_to(top.resolve())
    entries = [str(t.relative_to(via)) for fam, _d, _e in PRIOR.SYS_ENTRY.values() if (t := find_tail(fam, [via]))]
    base_p: dict = {}
    base_m: dict | None = None
    cur = list(cands)
    hist = []
    for rnd in range(1, rounds + 1):
        if not cur:
            break
        tails = []
        for d, stem in sorted({(x["dir"], x["family"]) for x in cur}):
            vs = sorted((via / d).glob(stem + "_v*.py"), key=_vnum)
            if vs:
                tails.append(str(vs[-1].relative_to(via)))
        jobs = [(r, r in entries) for r in dict.fromkeys(tails + entries)]
        tmp = Path(tempfile.mkdtemp(prefix="via_prune_proof_"))
        wt = tmp / "wt"
        subprocess.run(["git", "-C", str(top), "worktree", "add", "-q", "--detach", str(wt), "HEAD"], check=True, capture_output=True)
        wvia = wt / sub
        try:
            def run(js):
                with ThreadPoolExecutor(max_workers=max(1, min(6, lanes))) as ex:
                    return dict(zip([j[0] for j in js], ex.map(lambda j: _probe(wvia, j[0], j[1]), js)))
            need = [j for j in jobs if j[0] not in base_p]
            if need:
                base_p.update(run(need))
            if base_m is None:
                base_m = _vcgc_metrics(wvia)
                log(f"[prove] 基準 VCGC:{ {k: v for k, v in base_m.items() if k not in ('lost_paths', 'sdd_rules')} }")
            rel = [str(sub / x["path"]) for x in cur]
            for i in range(0, len(rel), 200):
                subprocess.run(["git", "-C", str(wt), "rm", "-q", "--", *rel[i:i + 200]], check=True, capture_output=True)
            mk = retire_mark(wvia, [x["path"] for x in cur], apply=True)
            log(f"[prove] 第 {rnd} 輪 · 候選 {len(cur)} · 標退役:元件冊 RETIRED {mk['component'].get('retired')} · "
                f"改指活檔 {mk['component'].get('resourced')} · 編號冊 gone_since {mk['numberbooks']['rows']} 列"
                + (f" · 元件冊標記失敗:{mk['component'].get('error')}" if mk["component"].get("error") else ""))
            after_p = run(jobs)
            after_m = _vcgc_metrics(wvia)
            log(f"[prove] 第 {rnd} 輪 拿掉 + 標退役後 VCGC:{ {k: v for k, v in after_m.items() if k not in ('lost_paths', 'sdd_rules')} }")
        finally:
            subprocess.run(["git", "-C", str(top), "worktree", "remove", "--force", str(wt)], capture_output=True)
            shutil.rmtree(tmp, ignore_errors=True)
        bad, implicated = [], set()
        names_in_cur = {Path(x["path"]).name for x in cur}
        for r, st in jobs:
            a, b = base_p[r], after_p[r]
            if (a[0] == 0 and b[0] != 0) or (a[0] != b[0] and not st):
                bad.append(r)
                implicated |= {n for n in _NAME_RX.findall(b[1]) if n in names_in_cur}
                log(f"  [FAIL] {r} · 前 rc {a[0]} · 後 rc {b[0]}" + (f" · 點名 {sorted(implicated)[:4]}" if implicated else ""))
        new_lost = set(after_m.get("lost_paths", [])) - set(base_m.get("lost_paths", []))
        implicated |= {Path(p).name for p in new_lost}
        worse = [w for w in _worse(base_m, after_m) if not (w.startswith("lost") and new_lost)]
        bad_fams = {_fam_of(r) for r in bad if r not in entries}
        bad_entry = [r for r in bad if r in entries]
        hist.append({"round": rnd, "n": len(cur), "bad": bad, "implicated": sorted(implicated), "worse": worse, "mark": mk})
        if not bad and not new_lost and not worse and not mk["component"].get("error"):
            log(f"[prove] 第 {rnd} 輪通過:{len(cur)} 支可退役")
            return {"checked": len(jobs), "failed": [], "new_lost": [], "worse": [], "proven": cur, "rounds": hist,
                    "vcgc_before": base_m, "vcgc_after": after_m}
        drop = [x for x in cur if (x["dir"], x["family"]) in bad_fams or Path(x["path"]).name in implicated]
        if bad_entry and not implicated:
            log("[prove] 系統入口自測變差、又點不出是哪支 → 整批不證(不猜)")
            break
        if worse and not drop:
            log(f"[prove] 其他指標變差 {worse}、點不出牽連 → 整批不證")
            break
        if not drop:
            break
        cur = [x for x in cur if x not in drop]
        log(f"[prove] 剔除牽連 {len(drop)} 支(家族 {len(bad_fams)} · 點名 {len(implicated)})→ 下一輪 {len(cur)} 支")
    return {"checked": 0, "failed": hist[-1]["bad"] if hist else [], "new_lost": [], "worse": hist[-1]["worse"] if hist else [],
            "proven": [], "rounds": hist, "vcgc_before": base_m}


def prune_apply(via: Path, proven: list[dict]) -> dict:
    """主樹:量搬前 → git mv → 標退役 → 再量;變差整批還原。"""
    before = _vcgc_metrics(via)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    dest_root = Path("functional modules") / "VIA_RetiredEngines" / f"prune_{ts}"
    moved = []
    for x in proven:
        src = Path(x["path"])
        dst = dest_root / src
        (via / dst).parent.mkdir(parents=True, exist_ok=True)
        sha = hashlib.sha256((via / src).read_bytes()).hexdigest()
        if subprocess.run(["git", "-C", str(via), "mv", str(src), str(dst)], capture_output=True).returncode == 0:
            moved.append({"from": src.as_posix(), "to": dst.as_posix(), "sha256": sha, "family": x["family"], "v": x["v"]})
    mk = retire_mark(via, [m["from"] for m in moved], apply=True)
    after = _vcgc_metrics(via)
    worse = _worse(before, after)
    if worse or mk["component"].get("error"):
        for m in moved:
            subprocess.run(["git", "-C", str(via), "mv", m["to"], m["from"]], capture_output=True)
        subprocess.run(["git", "-C", str(via), "checkout", "--", str(COMPONENT_BOOK), str(NUMBER_BOOKS)], capture_output=True)
        shutil.rmtree(via / dest_root, ignore_errors=True)
        return {"dest": None, "moved": 0, "rolled_back": True, "worse": worse, "mark": mk}
    man = {"schema": "VIA.RetireManifest.v1", "batch": f"prune_{ts}", "by": f"{FAMILY} {VERSION} prune",
           "rule": "先在編號冊標退役 → 證明(worktree 前後 VCGC 檢查不變差)→ 搬;以搬代刪",
           "marks": {"component_retired": mk["component"].get("retired"), "component_resourced": mk["component"].get("resourced"),
                     "numberbook_gone_since": mk["numberbooks"]["rows"], "numberbooks": mk["numberbooks"]["books"],
                     "stamp": mk["numberbooks"]["stamp"]},
           "vcgc_before": {k: v for k, v in before.items() if k not in ("lost_paths", "sdd_rules")},
           "vcgc_after": {k: v for k, v in after.items() if k not in ("lost_paths", "sdd_rules")},
           "restore": "CGC_MDL276_QuarantineRecover restore <原路徑> --apply(或 git mv 回去;冊的標記 git 可還原)", "moved": moved}
    (via / dest_root).mkdir(parents=True, exist_ok=True)
    (via / dest_root / "RETIRE_MANIFEST.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"dest": dest_root.as_posix(), "moved": len(moved), "mark": man["marks"]}


_GLOB_RX = re.compile(r"\.glob\(")
_PRIOR_RX = re.compile(r"_vnum|<\s*Path\(__file__\)\.name|p\.name\s*<")


def live_versions(stem: str, vs: dict, link) -> set:
    """v0102 的鏈判只看第一個標籤(exec / 釘名 / glob 擇一);VRN 管理器 v0279–v0280 同時 exec v0240 本體「又」glob 取前版
    (容器實錄:拿掉 v0241–v0277 後 v0277 _owner('EM_CFG') 拿到 None)。本版三種連結各自判、全都走(只會更保守)。"""
    live: set = set()
    todo = [max(vs)]
    while todo:
        cur = todo.pop()
        if cur in live or cur not in vs:
            continue
        live.add(cur)
        text = vs[cur].read_text(encoding="utf-8", errors="replace")
        todo += [int(x) for x in re.findall(re.escape(stem) + r"_v(\d{4})\.py", text) if int(x) != cur and int(x) in vs]
        if (_GLOB_RX.search(text) and _PRIOR_RX.search(text)) or (link(text, stem, vs[cur].name) or "").startswith("glob"):
            older = [v for v in vs if v < cur]
            if older:
                todo.append(max(older))
    return live


PRIOR.live_versions = live_versions
PRIOR.prune_prove = prune_prove
PRIOR.prune_apply = prune_apply
PRIOR.CMD["via-prune"]["help"] = ("預設乾跑:列出鏈上走不到、程式碼與鎖定帳都沒點名的舊版。--prove:在 TEMP worktree 先在編號冊標退役"
                                  "(中央元件冊 RETIRED · 編號冊 gone_since,只限本批)→ 拿掉 → 實跑 VCGC 檢查,有牽連就剔除重證(最多 3 輪);"
                                  "--apply:主樹同樣先標後搬到 VIA_RetiredEngines(以搬代刪,可找回),變差整批還原。--system 縮範圍。")
PRIOR.CMD["via-prune"]["title"] = "舊版退役(先標退役 → 證明 → 搬)"


_V0102_MAIN = PRIOR.main


def _main_with_kinds(argv=None):
    """v0102 的 main(選單 / x 轉派也走這裡):prune 沒給 --kinds 時,預設把活冊登記的 REG_REF 也納入(先標退役再證)。"""
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] == ["prune"] and "--kinds" not in a:
        a += ["--kinds", "UNREF,DOC_REF,SNAP_REF,REG_REF"]
    return _V0102_MAIN(a)


PRIOR.main = _main_with_kinds


def main(argv: list[str] | None = None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    return _main_with_kinds(a)


def selftest() -> int:
    ok = bad = 0

    def chk(name, cond, note=""):
        nonlocal ok, bad
        ok += bool(cond)
        bad += not cond
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}", flush=True)

    with tempfile.TemporaryDirectory(prefix="vcgc_retire_st_") as td:
        T = Path(td)
        rows = [{"code": "VIA-VDF-MDL001", "name": "A", "source": "functional modules/VDF/A_v0100.py", "lamp": "GREEN"},
                {"code": "VIA-VDF-MDL002", "name": "A", "source": "functional modules/VDF/A_v0101.py", "lamp": "GREEN"},
                {"code": "VIA-VDF-FNC003", "name": "A:f", "source": "functional modules/VDF/A_v0100.py", "lamp": "GREEN",
                 "gone_since": "2026-09-29 16:34:30 +0000"},
                {"code": "VIA-VDF-MDL004", "name": "B", "source": "functional modules/VDF/B_v0100.py", "lamp": "GREEN"}]
        raw = b"\n".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")).encode() for r in rows) + b"\n"
        moved = {"functional modules/VDF/A_v0100.py"}
        new, n = mark_numberbook_text(raw, moved, "2026-11-23 00:00:00 +0000")
        nl, ol = new.split(b"\n"), raw.split(b"\n")
        chk("① 編號冊:只標本批來源、號不變、已有 gone_since 不覆蓋", n == 1 and json.loads(nl[0])["gone_since"] == "2026-11-23 00:00:00 +0000"
            and json.loads(nl[0])["code"] == "VIA-VDF-MDL001" and json.loads(nl[0])["lamp"] == "AMBER"
            and nl[2] == ol[2])
        chk("② 編號冊:其他行位元組不動、結尾換行保留、可重跑(冪等)", nl[1] == ol[1] and nl[3] == ol[3] and new.endswith(b"\n")
            and mark_numberbook_text(new, moved, "x")[1] == 0)
        nb = T / "VIA_NumberBooks"
        nb.mkdir()
        (nb / "VIA_NumberBook_MDL_v0100.jsonl").write_bytes(raw)
        reg = T / "supportive modules" / "registry"
        reg.mkdir(parents=True)
        shutil.move(str(nb), str(reg / "VIA_NumberBooks"))
        r = mark_number_books(T, moved, apply=True, stamp="2026-11-23 00:00:00 +0000")
        chk("③ 寫冊:鎖 + 原子換檔、沒留暫存檔", r["rows"] == 1 and not list((reg / "VIA_NumberBooks").glob(".*.tmp")))
        real = {"records": [
            {"key": "module|A", "source": "functional modules/VDF/A_v0100.py", "state": "ACTIVE", "code": "VIA-MOD-0001"},
            {"key": "function|A:f", "source": "functional modules/VDF/A_v0100.py", "state": "ACTIVE", "code": "VIA-FNC-0002"},
            {"key": "module|C", "source": "functional modules/VDF/C_v0100.py", "state": "ACTIVE", "code": "VIA-MOD-0003"},
            {"key": "module|old", "source": "functional modules/VDF/A_v0100.py", "state": "RETIRED", "code": "VIA-MOD-0004"}]}
        synced = {"records": [
            {"key": "module|A", "source": "functional modules/VDF/A_v0100.py", "state": "RETIRED", "retired_at": "t1", "code": "VIA-MOD-0001"},
            {"key": "function|A:f", "source": "functional modules/VDF/A_v0101.py", "line": 9, "state": "ACTIVE", "code": "VIA-FNC-0002"},
            {"key": "module|C", "source": "functional modules/VDF/C_v0100.py", "state": "RETIRED", "retired_at": "t1", "code": "VIA-MOD-0003"},
            {"key": "module|NEW", "source": "x.py", "state": "ACTIVE", "code": "VIA-MOD-0005"}]}
        res = merge_component_retire(real, synced, moved)
        recs = {r["key"]: r for r in real["records"]}
        chk("④ 元件冊:只帶本批來源(RETIRED / 改指活檔);別的檔被引擎標退役也不帶、新列不帶、號不動",
            res == {"retired": ["module|A"], "resourced": ["function|A:f"]} and recs["module|A"]["state"] == "RETIRED"
            and recs["function|A:f"]["source"].endswith("A_v0101.py") and recs["module|C"]["state"] == "ACTIVE"
            and "module|NEW" not in recs and recs["module|A"]["code"] == "VIA-MOD-0001")
        with file_lock(T / "x.json"):
            got = True
        chk("⑤ 檔案鎖可取可放", got)
    with tempfile.TemporaryDirectory(prefix="vcgc_chain_st_") as td2:
        F = Path(td2)
        g = ("from pathlib import Path\nimport re\ndef _vnum(p):\n    return int(re.search(r'_v(\\d{4})$',Path(p).stem).group(1))\n"
             "PRIOR_PATH=max((p for p in Path(__file__).parent.glob('M_v*.py') if _vnum(p)<_vnum(__file__)),key=_vnum)\n")
        (F / "M_v0100.py").write_text("x=1\n", encoding="utf-8")
        (F / "M_v0101.py").write_text("y=1\n", encoding="utf-8")
        (F / "M_v0102.py").write_text(g, encoding="utf-8")
        (F / "M_v0103.py").write_text("exec(open('M_v0100.py').read())\n" + g, encoding="utf-8")   # exec 本體又 glob 取前版
        vs2 = {_vnum(p): p for p in F.glob("M_v*.py")}
        lv = live_versions("M", vs2, lambda t, s_, n: "exec 本體 v0100" if "exec(" in t else ("glob 取前版" if ".glob(" in t else "本體"))
        chk("⑩ 鏈判:exec 本體又 glob 取前版的,兩條都走(v0102 漏的情形)", lv == {100, 101, 102, 103}, f"(live {sorted(lv)})")
    chk("⑥ 時間格式 = MDL237 編號冊格式", re.fullmatch(r"\d{4}-\d\d-\d\d \d\d:\d\d:\d\d \+0000", _stamp()) is not None)
    chk("⑦ 主控台尾版在(元件冊同步引擎)", find_tail("CGC_MDL149_VeritasCentralGovernanceConsole", [CODE_ROOT]) is not None)
    chk("⑧ 加速器橋執行時生效", VIA_ACCEL is not None)
    with contextlib.redirect_stdout(io.StringIO()) as buf:
        rc = PRIOR.selftest()
    t = [l for l in buf.getvalue().splitlines() if "[計]" in l]
    chk("⑨ 前版 v0102 自測", rc == 0, f"({t[-1].strip() if t else rc})")
    print(f"  [計] {FAMILY} {VERSION} 自測 OK {ok} · FAIL {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
