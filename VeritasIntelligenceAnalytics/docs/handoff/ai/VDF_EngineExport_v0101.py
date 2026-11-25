#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_EngineExport_v0101 — v0100 整檔 + 支援工具 · 鎖冊測試夾複本 · 多餘的舊匯出搬 _prev · 匯出後當場驗加速器 / 網路工具名稱版號

操作員 2026-11-25:「用 VCGC 工具去 GITHUB 隔離區讀取 VDF 相關引擎檔案以及非隔離區的檔案 …
  擷取輸入輸出參數設定檔案 / 全部台股個股清單引擎 / 全部主動式台股 ETF 清單引擎 / TWSE/TPEX / YFINANCE / 共識資料 / VALUATION / AKSHARE
  都擷取最新的那一個放到 C:\\Users\\tonyk\\OneDrive\\Desktop\\測試\\VDF\\engine」
清單 = 同夾 VDF_EngineExport_Manifest_v*.json 尾版(VCGC 工具在倉內建:擷取冊 VDF_FetchSystem_SSOT 尾版的來源組對引擎 ·
  各家族現役尾版 + 執行時要載入的鏈上前版(省 Token 工具 chain 判法)· 隔離區 intake 附件;隔離區 VIA_RetiredEngines / intake 也查過沒有更新的版)。
做法:git show <ref>:<路徑> 取位元組(不經 PowerShell 管線,不改換行)→ LF 正規化後 SHA-256 對清單 → 唯一暫存檔 + 原子換檔寫入;
  目的地已有不同內容的同名檔 → 先搬到 <目的地>\\_prev\\<時戳>\\ 再寫(不覆蓋掉舊的);相同內容就略過。
  不切分支、不 stash、不動倉的工作樹(倉裡有未提交的改動也沒關係)。零網路(git fetch 由呼叫端那一行做)。
v0101(操作員 2026-11-25「一種引擎只留一個最強的其他刪除 · 最新版本有版本號的支援工具 layout nlp 加速器 網路工具 等放入
  ...\\測試\\supportive modules · 加速器網路工具名稱版本號要正確」):
  ① 清單 v0101:每類一支最強 + 實測載入一定要的前版(容器逐支拿掉驗過,其餘不帶);支援工具取 VIA_ToolVersion_Lock 現役版
     (加速器 VeritasCeleritas_v1141 · 網路 VeritasAegisNexus_v1652 · layout SUP_MDL743 v0110 · nlp SUP_MDL866 v0108 · frame · pdfplumber · ocr)+ 它們載入一定要的前版
  ② 鎖冊測試夾複本:加速器本體(SUP_MDL737)照鎖冊路徑找工具;路徑前綴改成測試夾名才找得到正確版號(VCGC 正本不改)
  ③ 上次本工具匯出過、這次清單沒有的檔 → 搬到 <engine>\\_prev\\<時戳>\\(只動自己匯出過的檔,不刪)
  ④ 匯出後當場驗:加速器 / 網路工具實際載到的檔名 = 清單 expect;各類引擎尾版載入
用法:python VDF_EngineExport_v0101.py --repo <倉> --ref origin/<分支> --dest <...\\VDF\\engine> [--dry] | --selftest
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
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime
from pathlib import Path

VERSION = "v0101"
HERE = Path(__file__).resolve().parent
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (OSError, ValueError):
        pass


def manifest_path(folder: Path = HERE) -> Path | None:
    hits = sorted(folder.glob("VDF_EngineExport_Manifest_v*.json"))
    return hits[-1] if hits else None


def sha_lf(data: bytes) -> str:
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


def git_blob(repo: Path, ref: str, path: str) -> bytes | None:
    cp = subprocess.run(["git", "-C", str(repo), "show", f"{ref}:{path}"], capture_output=True)
    return cp.stdout if cp.returncode == 0 else None


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.{uuid.uuid4().hex[:8]}.tmp")
    tmp.write_bytes(data)
    os.replace(tmp, path)


def export(repo: Path, ref: str, dest: Path, man: dict, dry: bool = False, log=print) -> dict:
    """dest = ...\\VDF\\engine。條目 dest 欄 'engine' → dest;其他(如 references/intake/...)→ dest 的上一層 / 該相對路徑。"""
    prefix = man.get("repo_prefix", "")
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    rows, wrote, same, bad = [], 0, 0, []
    for e in man["entries"]:
        target = dest / e["name"] if e.get("dest", "engine") == "engine" else dest.parent / e["dest"] / e["name"]
        data = git_blob(repo, ref, prefix + e["path"])
        if data is None:
            bad.append(e["name"])
            rows.append({**e, "status": "MISSING_IN_REF", "target": str(target)})
            log(f"  [缺] {e['name']}:{ref} 上沒有 {e['path']}")
            continue
        h = sha_lf(data)
        if h != e["sha256_lf"]:
            bad.append(e["name"])
            rows.append({**e, "status": "HASH_MISMATCH", "got": h, "target": str(target)})
            log(f"  [不符] {e['name']}:雜湊 {h[:12]} ≠ 清單 {e['sha256_lf'][:12]}(不寫)")
            continue
        if e.get("role") == "lockcopy":
            root = dest.parent.parent.name                     # 測試夾名(例:測試)
            j = json.loads(data.decode("utf-8"))
            for k, v in j.items():
                if isinstance(v, dict) and str(v.get("path", "")).startswith("VeritasIntelligenceAnalytics/"):
                    v["path"] = root + "/" + v["path"][len("VeritasIntelligenceAnalytics/"):]
                    v["note_test_copy"] = "測試夾複本:路徑改指測試夾(VCGC 正本未改)"
            data = (json.dumps(j, ensure_ascii=False, indent=1) + "\n").encode("utf-8")
        if target.is_file() and target.read_bytes().replace(b"\r\n", b"\n") == data.replace(b"\r\n", b"\n"):
            same += 1
            rows.append({**e, "status": "SAME", "target": str(target)})
            continue
        if not dry:
            if target.is_file():
                prev = dest / "_prev" / stamp / target.name
                prev.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(target), str(prev))
            atomic_write(target, data)
        wrote += 1
        rows.append({**e, "status": "WROTE" if not dry else "WOULD_WRITE", "target": str(target)})
        log(f"  [{'寫' if not dry else '會寫'}] {e['category']:<12} {e['role']:<10} {e['name']}")
    moved_old = []
    old_rec = dest / "VDF_ENGINE_EXPORT_RECEIPT.json"
    if old_rec.is_file():
        try:
            prev_targets = {r.get("target") for r in json.loads(old_rec.read_text(encoding="utf-8")).get("rows", [])
                            if r.get("status") in ("WROTE", "SAME")}
        except (OSError, ValueError):
            prev_targets = set()
        now_targets = {r["target"] for r in rows}
        for t in sorted(x for x in prev_targets - now_targets if x):
            tp = Path(t)
            if tp.is_file() and not dry:
                prev = dest / "_prev" / stamp / tp.name
                prev.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(tp), str(prev))
            moved_old.append(tp.name)
        if moved_old:
            log(f"  [舊] 上次匯出、這次不需要的 {len(moved_old)} 支 → {dest / '_prev' / stamp}")
    rep = {"tool": f"VDF_EngineExport {VERSION}", "at": datetime.now().isoformat(timespec="seconds"), "ref": ref,
           "repo": str(repo), "dest": str(dest), "manifest": man.get("version"), "manifest_head": man.get("git_head"),
           "counts": {"should": len(man["entries"]), "wrote": wrote, "same": same, "skipped": bad, "moved_old": moved_old},
           "rows": rows}
    if not dry:
        atomic_write(dest / "VDF_ENGINE_EXPORT_RECEIPT.json", json.dumps(rep, ensure_ascii=False, indent=1).encode("utf-8"))
    return rep


_VERIFY = r"""
import importlib, importlib.util, json, sys
from pathlib import Path
sm, eng = Path(sys.argv[1]), Path(sys.argv[2])
sys.path.insert(0, str(sm))
out = {}
try:
    import VIA_SuperAccel_Module  # noqa: F401
    for bare in ("VeritasCeleritas", "VeritasAegisNexus"):
        try:
            out[bare] = Path(importlib.import_module(bare).__file__).name
        except Exception as e:  # noqa: BLE001
            out[bare] = "FAIL " + type(e).__name__
except Exception as e:  # noqa: BLE001
    out["bridge"] = "FAIL " + type(e).__name__ + " " + str(e)[:120]
print("VERIFY " + json.dumps(out, ensure_ascii=False))
"""


def verify(dest: Path, man: dict, log=print) -> dict:
    sm = dest.parent.parent / "supportive modules"
    res = {"tools": {}, "engines": {}}
    if sm.is_dir():
        cp = subprocess.run([sys.executable, "-c", _VERIFY, str(sm), str(dest)], cwd=str(sm), capture_output=True, text=True,
                            encoding="utf-8", errors="replace", timeout=600)
        line = [l for l in cp.stdout.splitlines() if l.startswith("VERIFY ")]
        res["tools"] = json.loads(line[0][7:]) if line else {"error": (cp.stdout + cp.stderr)[-300:]}
    exp = man.get("expect", {})
    for fam, want in exp.items():
        got = res["tools"].get({"accelerator": "VeritasCeleritas", "network": "VeritasAegisNexus"}.get(fam, fam))
        log(f"  [{'OK' if got == want else 'FAIL'}] {fam:<11} 應 {want} · 實載 {got}")
    imp = "import importlib.util,sys;s=importlib.util.spec_from_file_location('e',sys.argv[1]);m=importlib.util.module_from_spec(s);sys.modules['e']=m;s.loader.exec_module(m);print('IMPORT_OK')"
    for e in man["entries"]:
        if e["role"] == "tail" and e.get("dest", "engine") == "engine" and e["name"].endswith(".py"):
            cp = subprocess.run([sys.executable, "-c", imp, e["name"]], cwd=str(dest), capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=600)
            ok = "IMPORT_OK" in cp.stdout
            res["engines"][e["name"]] = ok
            log(f"  [{'OK' if ok else 'FAIL'}] 載入 {e['name']}" + ("" if ok else " · " + ((cp.stderr or '').strip().splitlines() or ['?'])[-1][:140]))
    res["ok"] = all(res["engines"].values()) and all(res["tools"].get({"accelerator": "VeritasCeleritas", "network": "VeritasAegisNexus"}[f]) == w
                                                    for f, w in exp.items())
    return res


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a:
        return selftest()
    ap = argparse.ArgumentParser(description="VDF 引擎匯出(git show → 本機資料夾)")
    ap.add_argument("--repo", required=True)
    ap.add_argument("--ref", default="origin/claude/sweet-hamilton-gei01h")
    ap.add_argument("--dest", required=True)
    ap.add_argument("--manifest")
    ap.add_argument("--dry", action="store_true")
    x = ap.parse_args(a)
    mp = Path(x.manifest) if x.manifest else manifest_path()
    if not mp or not mp.is_file():
        print("[export] 找不到 VDF_EngineExport_Manifest_v*.json")
        return 2
    man = json.loads(mp.read_text(encoding="utf-8"))
    dest = Path(x.dest)
    print(f"[export] {mp.name} · {len(man['entries'])} 檔 · {x.ref} → {dest}{'(乾跑)' if x.dry else ''}")
    rep = export(Path(x.repo), x.ref, dest, man, dry=x.dry)
    c = rep["counts"]
    print(f"[export] 應擷取 {c['should']} · 寫入 {c['wrote']} · 相同略過 {c['same']} · 缺 / 不符 {len(c['skipped'])}"
          + (f":{c['skipped']}" if c["skipped"] else ""))
    by = {}
    for r in rep["rows"]:
        by.setdefault(r["category"], []).append(r["name"] if r["role"] in ("tail", "config") else None)
    for k, v in by.items():
        print(f"  {k:<14} " + " · ".join(n for n in v if n))
    vr = {"ok": True}
    if not x.dry:
        print("[驗] 加速器 / 網路工具實際載到的檔 · 引擎尾版載入")
        vr = verify(dest, man)
        rp = dest / "VDF_ENGINE_EXPORT_RECEIPT.json"
        j = json.loads(rp.read_text(encoding="utf-8"))
        j["verify"] = vr
        atomic_write(rp, json.dumps(j, ensure_ascii=False, indent=1).encode("utf-8"))
        print(f"[收據] {rp}")
    print(f"NEXT: {'把上面 [OK]/[FAIL] 行貼回' if vr.get('ok') else '有 FAIL → 把 FAIL 行貼回'}")
    return 0 if not c["skipped"] and vr.get("ok") else 1


def selftest() -> int:
    ok = bad = 0

    def chk(name, cond, note=""):
        nonlocal ok, bad
        ok += bool(cond)
        bad += not cond
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}", flush=True)

    with tempfile.TemporaryDirectory(prefix="vdf_export_st_") as td:
        T = Path(td)
        repo = T / "repo"
        (repo / "VIA" / "VDF" / "engine").mkdir(parents=True)
        (repo / "VIA" / "VDF" / "refs").mkdir(parents=True)
        files = {"VIA/VDF/A_v0101.py": b"x = 1\r\n", "VIA/VDF/engine/B_v0100.py": b"y = 2\n", "VIA/VDF/refs/dep.py": b"z = 3\n"}
        for k, v in files.items():
            (repo / k).write_bytes(v)
        g = ["git", "-C", str(repo), "-c", "user.email=x@x", "-c", "user.name=x"]
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        subprocess.run(g + ["add", "-A"], check=True)
        subprocess.run(g + ["commit", "-qm", "t"], check=True)
        (repo / "VIA" / "VDF" / "A_v0101.py").write_bytes(b"dirty working tree\n")      # 工作樹有未提交改動
        man = {"version": "t", "repo_prefix": "VIA/", "entries": [
            {"category": "C", "role": "tail", "path": "VDF/A_v0101.py", "dest": "engine", "name": "A_v0101.py", "sha256_lf": sha_lf(b"x = 1\n")},
            {"category": "C", "role": "tail", "path": "VDF/engine/B_v0100.py", "dest": "engine", "name": "B_v0100.py", "sha256_lf": sha_lf(b"y = 2\n")},
            {"category": "C", "role": "dependency", "path": "VDF/refs/dep.py", "dest": "refs", "name": "dep.py", "sha256_lf": sha_lf(b"z = 3\n")},
            {"category": "C", "role": "tail", "path": "VDF/nope_v0100.py", "dest": "engine", "name": "nope_v0100.py", "sha256_lf": "0"}]}
        dest = T / "Desktop" / "測試" / "VDF" / "engine"
        dest.mkdir(parents=True)
        (dest / "B_v0100.py").write_bytes(b"old content\n")
        rep = export(repo, "HEAD", dest, man, log=lambda *a: None)
        chk("① 取的是分支上的內容,不是工作樹的未提交改動", (dest / "A_v0101.py").read_bytes() == b"x = 1\r\n")
        chk("② LF 正規化後雜湊對清單(CRLF 也過)", rep["counts"]["wrote"] == 3, f"({rep['counts']})")
        chk("③ 舊同名檔先搬到 _prev 再寫", (dest / "B_v0100.py").read_bytes() == b"y = 2\n"
            and any(p.read_bytes() == b"old content\n" for p in (dest / "_prev").rglob("B_v0100.py")))
        chk("④ 附件寫到 engine 的上一層對應路徑", (dest.parent / "refs" / "dep.py").read_bytes() == b"z = 3\n")
        chk("⑤ 分支上沒有的照實列缺、不假裝寫了", rep["counts"]["skipped"] == ["nope_v0100.py"])
        rep2 = export(repo, "HEAD", dest, man, log=lambda *a: None)
        chk("⑥ 再跑一次:相同內容全略過(冪等)", rep2["counts"]["wrote"] == 0 and rep2["counts"]["same"] == 3)
        man["entries"][0]["sha256_lf"] = "f" * 64
        rep3 = export(repo, "HEAD", T / "other", man, log=lambda *a: None)
        chk("⑦ 雜湊不符不寫", not (T / "other" / "A_v0101.py").exists() and "A_v0101.py" in rep3["counts"]["skipped"])
        chk("⑧ 沒留暫存檔", not list(dest.rglob(".*.tmp")))
    mp = manifest_path()
    m = json.loads(mp.read_text(encoding="utf-8")) if mp else {}
    cats = {e["category"] for e in m.get("entries", [])}
    need = {"輸入輸出參數設定", "全部台股個股清單", "全部主動式台股ETF清單", "TWSE/TPEX", "YFINANCE", "共識資料", "VALUATION", "AKSHARE"}
    chk("⑨ 清單涵蓋操作員點名的 8 類", need <= cats, f"({len(cats & need)}/8)")
    chk("⑩ 加速器橋執行時生效(在倉內跑時)", VIA_ACCEL is not None or not (HERE.parent.parent.parent / "supportive modules").is_dir())
    with tempfile.TemporaryDirectory(prefix="vdf_export_st2_") as td:
        T = Path(td)
        repo = T / "repo"
        (repo / "VIA" / "supportive modules" / "registry").mkdir(parents=True)
        lockj = {"accelerator": {"path": "VeritasIntelligenceAnalytics/supportive modules/VeritasCeleritas_v1141.py"}}
        (repo / "VIA" / "supportive modules" / "registry" / "L.json").write_text(json.dumps(lockj), encoding="utf-8")
        (repo / "VIA" / "x.py").write_text("x=1\n", encoding="utf-8")
        g = ["git", "-C", str(repo), "-c", "user.email=x@x", "-c", "user.name=x"]
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        subprocess.run(g + ["add", "-A"], check=True)
        subprocess.run(g + ["commit", "-qm", "t"], check=True)
        raw = (repo / "VIA" / "supportive modules" / "registry" / "L.json").read_bytes()
        man2 = {"repo_prefix": "VIA/", "entries": [
            {"category": "L", "role": "lockcopy", "path": "supportive modules/registry/L.json", "dest": "../supportive modules/registry",
             "name": "L.json", "sha256_lf": sha_lf(raw)},
            {"category": "C", "role": "tail", "path": "x.py", "dest": "engine", "name": "x.py", "sha256_lf": sha_lf(b"x=1\n")}]}
        dest = T / "Desktop" / "測試" / "VDF" / "engine"
        dest.mkdir(parents=True)
        (dest / "stale.py").write_text("old\n", encoding="utf-8")
        (dest / "mine.txt").write_text("user\n", encoding="utf-8")
        atomic_write(dest / "VDF_ENGINE_EXPORT_RECEIPT.json", json.dumps({"rows": [{"target": str(dest / "stale.py"), "status": "WROTE"}]}).encode())
        r = export(repo, "HEAD", dest, man2, log=lambda *a: None)
        lc = json.loads((T / "Desktop" / "測試" / "supportive modules" / "registry" / "L.json").read_text(encoding="utf-8"))
        chk("⑪ 鎖冊複本路徑改指測試夾(測試/supportive modules/…)", lc["accelerator"]["path"] == "測試/supportive modules/VeritasCeleritas_v1141.py")
        chk("⑫ 上次匯出、這次不需要的檔搬 _prev(不刪)", not (dest / "stale.py").exists() and r["counts"]["moved_old"] == ["stale.py"]
            and any((dest / "_prev").rglob("stale.py")))
        chk("⑬ 使用者自己放的檔(不在上次收據裡)不動", (dest / "mine.txt").read_text(encoding="utf-8") == "user\n")
    print(f"  [計] VDF_EngineExport {VERSION} 自測 OK {ok} · FAIL {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
