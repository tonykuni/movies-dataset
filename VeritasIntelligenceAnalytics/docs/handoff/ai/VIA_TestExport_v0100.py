#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_TestExport_v0100 — 全子系統最新引擎 → 本機測試夾(相對位置),從 GitHub 分支直接匯出(只讀倉、不切分支)

操作員 2026-11-25:「同樣的邏輯將剩下子系統最新引擎移動到 ...\\\\測試\\\\{supportive modules, VAP, VDF, VQG, VRN, VCGC}
  相對位置用 VCGC 全景式掃描等節省工具進行」。
清單 = 同夾 VIA_AllSystems_TestExport_Manifest_v*.json 尾版(VCGC 工具在倉內建,容器模擬測試夾逐支載入驗過):
  · 各系統引擎一種一支(現役尾版)+ 鏈上前版(省 Token 工具 chain 判法)+ 載入實測補齊的前版 / 依賴;系統冊取各家族尾版
  · 支援工具只帶:鎖冊現役(加速器 VeritasCeleritas_v1141 · 網路 VeritasAegisNexus_v1652 · layout · nlp · frame · pdfplumber · ocr)·
    一種一支的 NLP / layout / markdown 入口 · 引擎實際載入的(同功能的休眠重複件不帶)
  · 相對位置:functional modules/<系統>/… → 測試\\<系統>\\… ;supportive modules/registry/CGC_* → 測試\\VCGC\\… ;
    supportive modules/… → 測試\\supportive modules\\…
做法照 VDF_EngineExport v0101:git show 取位元組 → LF 雜湊核對 → 唯一暫存 + 原子換檔;不同內容的同名舊檔先搬 _prev;
  上次匯出過(本工具或 VDF_EngineExport 的收據)、這次清單沒有的檔 → 搬 _prev(只動自己匯出過的,不刪);
  鎖冊測試夾複本把路徑前綴改成測試夾名;匯出後驗加速器 / 網路工具實載檔名與各系統尾版載入。
用法:python VIA_TestExport_v0100.py --repo <倉> --ref origin/<分支> --root <...\\測試> [--dry] [--no-verify] | --selftest
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

import argparse
import collections
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

VERSION = "v0100"
HERE = Path(__file__).resolve().parent
RECEIPT = "VIA_TEST_EXPORT_RECEIPT.json"
OLD_RECEIPTS = ["VDF/engine/VDF_ENGINE_EXPORT_RECEIPT.json"]
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (OSError, ValueError):
        pass


def manifest_path(folder: Path = HERE) -> Path | None:
    hits = sorted(folder.glob("VIA_AllSystems_TestExport_Manifest_v*.json"))
    return hits[-1] if hits else None


def sha_lf(data: bytes) -> str:
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.{uuid.uuid4().hex[:8]}.tmp")
    tmp.write_bytes(data)
    os.replace(tmp, path)


def git_blobs(repo: Path, ref: str, paths: list[str]) -> dict[str, bytes | None]:
    """git cat-file --batch 一次取全部(快;位元組原樣)。"""
    out: dict[str, bytes | None] = {}
    p = subprocess.Popen(["git", "-C", str(repo), "cat-file", "--batch"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    for path in paths:
        p.stdin.write(f"{ref}:{path}\n".encode("utf-8"))
        p.stdin.flush()
        head = p.stdout.readline().decode("utf-8", "replace").strip()
        if head.endswith(" missing") or not head:
            out[path] = None
            continue
        size = int(head.split()[-1])
        out[path] = p.stdout.read(size)
        p.stdout.read(1)
    p.stdin.close()
    p.wait()
    return out


def lock_copy(data: bytes, root_name: str) -> bytes:
    j = json.loads(data.decode("utf-8"))
    for v in j.values():
        if isinstance(v, dict) and str(v.get("path", "")).startswith("VeritasIntelligenceAnalytics/"):
            v["path"] = root_name + "/" + v["path"][len("VeritasIntelligenceAnalytics/"):]
            v["note_test_copy"] = "測試夾複本:路徑改指測試夾(VCGC 正本未改)"
    return (json.dumps(j, ensure_ascii=False, indent=1) + "\n").encode("utf-8")


def export(repo: Path, ref: str, root: Path, man: dict, dry: bool = False, log=print) -> dict:
    prefix = man.get("repo_prefix", "")
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    blobs = git_blobs(repo, ref, [prefix + e["path"] for e in man["entries"]])
    rows, wrote, same, bad = [], 0, 0, []
    for e in man["entries"]:
        target = root / e["to"]
        data = blobs.get(prefix + e["path"])
        if data is None:
            bad.append(e["to"])
            rows.append({**e, "status": "MISSING_IN_REF"})
            continue
        if sha_lf(data) != e["sha256_lf"]:
            bad.append(e["to"])
            rows.append({**e, "status": "HASH_MISMATCH"})
            continue
        if e.get("role") == "lockcopy":
            data = lock_copy(data, root.name)
        if target.is_file() and target.read_bytes().replace(b"\r\n", b"\n") == data.replace(b"\r\n", b"\n"):
            same += 1
            rows.append({**e, "status": "SAME", "target": str(target)})
            continue
        if not dry:
            if target.is_file():
                prev = root / "_prev" / stamp / e["to"]
                prev.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(target), str(prev))
            atomic_write(target, data)
        wrote += 1
        rows.append({**e, "status": "WROTE" if not dry else "WOULD_WRITE", "target": str(target)})
    now = {os.path.normcase(os.path.normpath(str(root / e["to"]))) for e in man["entries"]}
    moved_old = []
    for rc in [RECEIPT] + OLD_RECEIPTS:
        rp = root / rc
        if not rp.is_file():
            continue
        try:
            prev_t = {r.get("target") for r in json.loads(rp.read_text(encoding="utf-8")).get("rows", []) if r.get("status") in ("WROTE", "SAME")}
        except (OSError, ValueError):
            continue
        stale = {os.path.normpath(x) for x in prev_t if x and os.path.normcase(os.path.normpath(x)) not in now}
        for t in sorted(stale):
            tp = Path(t)
            if tp.is_file():
                rel = tp.relative_to(root) if Path(os.path.normpath(root)) in tp.parents else Path(tp.name)
                if not dry:
                    dst = root / "_prev" / stamp / rel
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(tp), str(dst))
                moved_old.append(str(rel))
        if rc in OLD_RECEIPTS and not dry:              # 舊匯出器的收據功成身退,一起收進 _prev
            dst = root / "_prev" / stamp / rc
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(rp), str(dst))
    rep = {"tool": f"VIA_TestExport {VERSION}", "at": datetime.now().isoformat(timespec="seconds"), "ref": ref, "repo": str(repo),
           "root": str(root), "manifest": man.get("version"), "manifest_head": man.get("git_head"),
           "counts": {"should": len(man["entries"]), "wrote": wrote, "same": same, "skipped": bad, "moved_old": len(moved_old)},
           "moved_old": moved_old, "rows": rows}
    if not dry:
        atomic_write(root / RECEIPT, json.dumps(rep, ensure_ascii=False, indent=1).encode("utf-8"))
    return rep


_VERIFY_TOOLS = r"""
import importlib, json, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
out = {}
try:
    import VIA_SuperAccel_Module  # noqa: F401
    for bare in ("VeritasCeleritas", "VeritasAegisNexus"):
        try:
            out[bare] = Path(importlib.import_module(bare).__file__).name
        except Exception as e:  # noqa: BLE001
            out[bare] = "FAIL " + type(e).__name__
except Exception as e:  # noqa: BLE001
    out["bridge"] = "FAIL " + type(e).__name__
print("VERIFY " + json.dumps(out, ensure_ascii=False))
"""
_IMP = ("import importlib.util,sys,os;os.environ['VIA_PANORAMA_AUTO']='0';s=importlib.util.spec_from_file_location('e',sys.argv[1]);"
        "m=importlib.util.module_from_spec(s);sys.modules['e']=m;s.loader.exec_module(m);print('IMPORT_OK')")


def verify(root: Path, man: dict, lanes: int = 6, log=print) -> dict:
    sm = root / "supportive modules"
    res: dict = {"tools": {}, "systems": {}}
    cp = subprocess.run([sys.executable, "-c", _VERIFY_TOOLS, str(sm)], cwd=str(sm), capture_output=True, text=True,
                        encoding="utf-8", errors="replace", timeout=600)
    line = [l for l in cp.stdout.splitlines() if l.startswith("VERIFY ")]
    res["tools"] = json.loads(line[0][7:]) if line else {"error": (cp.stdout + cp.stderr)[-200:]}
    ok_tools = True
    for fam, want in man.get("expect", {}).items():
        got = res["tools"].get({"accelerator": "VeritasCeleritas", "network": "VeritasAegisNexus"}.get(fam, fam))
        ok_tools &= got == want
        log(f"  [{'OK' if got == want else 'FAIL'}] {fam:<11} 應 {want} · 實載 {got}")

    def one(t):
        p = root / t
        try:
            c = subprocess.run([sys.executable, "-c", _IMP, str(p)], cwd=str(p.parent), capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=180, stdin=subprocess.DEVNULL,
                               env={**os.environ, "VIA_FROM_VCGC": "YES", "VIA_PANORAMA_AUTO": "0", "VIA_NO_OPEN": "1"})
            return t, "IMPORT_OK" in c.stdout, ((c.stderr or "").strip().splitlines() or [""])[-1][:160]
        except subprocess.TimeoutExpired:
            return t, False, "逾時"
    with ThreadPoolExecutor(max_workers=lanes) as ex:
        results = list(ex.map(one, man.get("tails", []) + ["supportive modules/" + x for x in man.get("support_probe", [])]))
    per = collections.defaultdict(lambda: [0, 0])
    fails = []
    for t, ok, why in results:
        per[t.split("/")[0]][0 if ok else 1] += 1
        if not ok:
            fails.append({"tail": t, "why": why})
    for s, (a, b) in sorted(per.items()):
        log(f"  [{'OK' if not b else 'PART'}] {s:<20} 尾版載入 OK {a} · 不過 {b}")
    res["systems"] = {k: {"ok": v[0], "fail": v[1]} for k, v in per.items()}
    res["fails"] = fails
    res["tools_ok"] = ok_tools
    return res


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a:
        return selftest()
    ap = argparse.ArgumentParser(description="全子系統最新引擎 → 測試夾(相對位置)")
    ap.add_argument("--repo", required=True)
    ap.add_argument("--ref", default="origin/claude/sweet-hamilton-gei01h")
    ap.add_argument("--root", required=True)
    ap.add_argument("--manifest")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--no-verify", action="store_true")
    x = ap.parse_args(a)
    mp = Path(x.manifest) if x.manifest else manifest_path()
    if not mp or not mp.is_file():
        print("[export] 找不到 VIA_AllSystems_TestExport_Manifest_v*.json")
        return 2
    man = json.loads(mp.read_text(encoding="utf-8"))
    root = Path(x.root)
    print(f"[export] {mp.name} · {len(man['entries'])} 檔 · {x.ref} → {root}{'(乾跑)' if x.dry else ''}")
    rep = export(Path(x.repo), x.ref, root, man, dry=x.dry)
    c = rep["counts"]
    by = collections.Counter(e["to"].split("/")[0] for e in man["entries"])
    print(f"[export] 應擷取 {c['should']} · 寫入 {c['wrote']} · 相同略過 {c['same']} · 舊匯出搬 _prev {c['moved_old']} · 缺 / 不符 {len(c['skipped'])}"
          + (f":{c['skipped'][:8]}" if c["skipped"] else ""))
    print("  各夾:" + " · ".join(f"{k} {v}" for k, v in sorted(by.items())))
    vr: dict = {"tools_ok": True}
    if not x.dry and not x.no_verify:
        print("[驗] 加速器 / 網路工具實載 · 各系統尾版載入(缺套件的照實列)")
        vr = verify(root, man)
        j = json.loads((root / RECEIPT).read_text(encoding="utf-8"))
        j["verify"] = vr
        atomic_write(root / RECEIPT, json.dumps(j, ensure_ascii=False, indent=1).encode("utf-8"))
        print(f"[收據] {root / RECEIPT}")
    print("NEXT: 把 [export] / [OK] / [PART] / [FAIL] 行貼回")
    return 0 if not c["skipped"] and vr.get("tools_ok") else 1


def selftest() -> int:
    ok = bad = 0

    def chk(name, cond, note=""):
        nonlocal ok, bad
        ok += bool(cond)
        bad += not cond
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}", flush=True)

    with tempfile.TemporaryDirectory(prefix="via_testexport_st_") as td:
        T = Path(td)
        repo = T / "repo"
        files = {"VIA/functional modules/VRN/a_v0100.py": b"a=1\r\n", "VIA/supportive modules/registry/CGC_X_v0100.py": b"c=1\n",
                 "VIA/supportive modules/registry/L.json": json.dumps({"accelerator": {"path": "VeritasIntelligenceAnalytics/supportive modules/A.py"}}).encode()}
        for k, v in files.items():
            (repo / k).parent.mkdir(parents=True, exist_ok=True)
            (repo / k).write_bytes(v)
        g = ["git", "-C", str(repo), "-c", "user.email=x@x", "-c", "user.name=x"]
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        subprocess.run(g + ["add", "-A"], check=True)
        subprocess.run(g + ["commit", "-qm", "t"], check=True)
        (repo / "VIA/functional modules/VRN/a_v0100.py").write_bytes(b"dirty\n")
        man = {"repo_prefix": "VIA/", "entries": [
            {"path": "functional modules/VRN/a_v0100.py", "to": "VRN/a_v0100.py", "role": "tail", "sha256_lf": sha_lf(b"a=1\n")},
            {"path": "supportive modules/registry/CGC_X_v0100.py", "to": "VCGC/CGC_X_v0100.py", "role": "tail", "sha256_lf": sha_lf(b"c=1\n")},
            {"path": "supportive modules/registry/L.json", "to": "supportive modules/registry/L.json", "role": "lockcopy",
             "sha256_lf": sha_lf(files["VIA/supportive modules/registry/L.json"])},
            {"path": "nope.py", "to": "VRN/nope.py", "role": "tail", "sha256_lf": "0"}]}
        root = T / "Desktop" / "測試"
        (root / "VDF" / "engine").mkdir(parents=True)
        (root / "VDF" / "engine" / "old_flat.py").write_text("x\n", encoding="utf-8")
        (root / "VDF" / "engine" / "mine.txt").write_text("user\n", encoding="utf-8")
        atomic_write(root / "VDF/engine/VDF_ENGINE_EXPORT_RECEIPT.json",
                     json.dumps({"rows": [{"target": str(root / "VDF/engine/old_flat.py"), "status": "WROTE"},
                                          {"target": str(root / "VDF/engine/../../VCGC/CGC_X_v0100.py"), "status": "WROTE"}]}).encode())
        r = export(repo, "HEAD", root, man, log=lambda *a: None)
        chk("① 相對位置:VRN/… · VCGC/…;取分支內容不取工作樹", (root / "VRN/a_v0100.py").read_bytes() == b"a=1\r\n" and (root / "VCGC/CGC_X_v0100.py").is_file())
        lc = json.loads((root / "supportive modules/registry/L.json").read_text(encoding="utf-8"))
        chk("② 鎖冊複本路徑改指測試夾", lc["accelerator"]["path"] == "測試/supportive modules/A.py")
        chk("③ 上一版 VDF 平放的舊匯出搬 _prev、使用者自己的檔不動", not (root / "VDF/engine/old_flat.py").exists()
            and any((root / "_prev").rglob("old_flat.py")) and (root / "VDF/engine/mine.txt").is_file())
        chk("③b 舊收據寫成 ../ 形式、但就是這次要的檔 → 不搬(路徑正規化後比)", (root / "VCGC/CGC_X_v0100.py").is_file()
            and not any((root / "_prev").rglob("CGC_X_v0100.py")))
        chk("④ 分支上沒有的照實列缺", r["counts"]["skipped"] == ["VRN/nope.py"])
        r2 = export(repo, "HEAD", root, man, log=lambda *a: None)
        chk("⑤ 再跑一次相同內容全略過(冪等)", r2["counts"]["wrote"] == 0 and r2["counts"]["same"] == 3, f"({r2['counts']})")
        chk("⑥ 沒留暫存檔", not list(root.rglob(".*.tmp")))
    mp = manifest_path()
    m = json.loads(mp.read_text(encoding="utf-8")) if mp else {}
    tops = {e["to"].split("/")[0] for e in m.get("entries", [])}
    chk("⑦ 清單涵蓋 6 個夾", {"supportive modules", "VAP", "VDF", "VQG", "VRN", "VCGC"} <= tops, f"({sorted(tops)})")
    chk("⑧ 加速器 / 網路工具期望版號在清單", m.get("expect", {}).get("accelerator") == "VeritasCeleritas_v1141.py"
        and m.get("expect", {}).get("network") == "VeritasAegisNexus_v1652.py")
    print(f"  [計] VIA_TestExport {VERSION} 自測 OK {ok} · FAIL {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
