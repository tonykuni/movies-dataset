#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_DailyBackup v0100 — 五系統每日收尾備份 + 隔天「檢查備份」一指令(治理冊 · 交接 · 證據 · 工具鎖;只讀來源 · 只增備份)。

操作員 2026-11-09:「啟動 GRAPHIFY / PONYTAIL / 所有 VCGC 備份功能及交接工具合併,每個子系統都有;VCGC TOKEN SAVING 工具完善化備份收尾;
明天只要要求檢查備份即可開始;今日收尾」。

  backup   每個子系統(VCGC · VDF · VRN-2 · VQG · VAP · 共用交接)照冊 SCOPE 收集治理冊尾版 / 數冊 / 交接冊 / 證據 / 工具鎖 →
           <VIA>/VIA_Reports/backup/<UTC 時戳>/<SYS>.zip(zipfile · 只增)+ MANIFEST.json(每檔 sha256 · 大小 · git HEAD)+ SHA256SUMS.txt;
           同時把 MANIFEST(小 · 可入倉)寫到 docs/handoff/backup/BACKUP_MANIFEST_latest.json + BACKUP_MANIFEST_<時戳>.json(只增),
           讓隔天在任何機器(含全新容器)都能對冊:倉裡的檔 ≟ 備份時的 sha。
           旁證(只讀 · 不跑):Graphify 收據 VIA_Reports/graphify/VIA_Graphify_latest.json(有 / 無)· Ponytail(倉內無 → ABSENT 照實)·
           省 Token 工具鎖 VIA_ToolVersion_Lock(token / nlp 指到的檔在不在)· HANDOFF_latest.json 摘要 · CGC_MDL221 SystemBackup 冊在不在。
  check    讀最新 MANIFEST(先倉內 docs/handoff/backup,再 VIA_Reports/backup):逐檔 sha 對倉 → 同 / 變 / 缺;zip 在本機就驗 SHA256SUMS;
           報 git HEAD 是否前進、備份幾小時前;GREEN(全同 · zip 驗過)/ YELLOW(有變或 zip 不在本機 · 照實)/ RED(MANIFEST 缺 · zip sha 不符 · 或倉內 ≥ 50% 檔已不在;檔內容變了 = 正常進度 → YELLOW 點名)。
  selftest 零網路 · tempfile 假倉 · backup → check 綠 · 改一檔 → check 黃並點名 · 刪 zip → 黃 · 不碰 environ。
邊界:不連網 · 不起子行程(git HEAD 直接讀 .git)· 不改任何來源檔 · 備份夾只增 · 不備份 VIA_Reports 大檔與 VRN2 運行副本。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

VERSION = "v0100"
ENGINE = "VIA_DailyBackup " + VERSION
HERE = Path(__file__).resolve().parent
VIA = HERE.parents[2] if HERE.name == "ai" else HERE
MANIFEST_DIR_REL = "docs/handoff/backup"
BACKUP_ROOT_REL = "VIA_Reports/backup"
# 冊 SCOPE:每系統要備的 glob(相對 VIA 根;只收小檔 · 尾版以 sorted()[-1] 取;* 全收)
SCOPE = {
    "VCGC": {"tail": ["supportive modules/registry/VIA_Requirements_SSOT_v*.json", "supportive modules/registry/VIA_Workflow_VCGC_SSOT_v*.json",
                      "supportive modules/registry/VIA_VCGC_FunctionInventory_SSOT_v*.json", "supportive modules/registry/VIA_Policy_Laws_SSOT_v*.json",
                      "supportive modules/registry/VIA_AI_FunctionCard_SSOT_v*.json", "supportive modules/registry/VIA_Numbering_SSOT_v*.json",
                      "supportive modules/registry/CGC_MDL149_VeritasCentralGovernanceConsole_v*.py", "supportive modules/registry/VIA_LampLock_v*.json"],
             "all": ["supportive modules/registry/VIA_ToolVersion_Lock_v*.json", "supportive modules/registry/VIA_VCGC_FunctionLedger_v*.jsonl",
                     "supportive modules/registry/VIA_NumberBooks/*.jsonl", "supportive modules/registry/VIA_NumberBooks/*.json", "supportive modules/registry/VIA_Handoff_Continuity_SSOT_v*.json",
                     "supportive modules/registry/VIA_Component_Inventory_SSOT_v*.json", "supportive modules/registry/VIA_VCGC_SystemBackup_v*.json"]},
    "VDF": {"tail": ["functional modules/VDF/VDF_FetchGroups_SSOT_v*.json", "functional modules/VDF/VDF_FetchSystem_SSOT_v*.json", "functional modules/VDF/VDF_InputUniverse_SSOT_v*.json",
                     "functional modules/VDF/VDF_DataHome_SSOT_v*.json", "functional modules/VDF/VDF_SystemManager_v*.py", "functional modules/VDF/VDF_MDL013_ActivateVDF_v*.py",
                     "functional modules/VDF/VDF_MacroKeyword_SSOT_v*.json", "functional modules/VDF/VDF_MacroCrossCheck_Pairs_SSOT_v*.json", "supportive modules/registry/VIA_Workflow_VDF_SSOT_v*.json"],
            "all": ["functional modules/VDF/VDF_USMacro_*_v*.json", "functional modules/VDF/VDF_FetchGroups_MemberLedger_v*.jsonl"]},
    "VRN2": {"tail": ["functional modules/VRN/VRN_SystemManager_v*.py", "docs/handoff/ai/VRN2_Handover_v*.md", "docs/handoff/ai/VRN2_FreezeLock_v*.json", "supportive modules/registry/VIA_Workflow_VRN_SSOT_v*.json"],
             "all": ["functional modules/VRN/nonstock_v0310/REUSE_MANIFEST_v*.json", "docs/handoff/ai/vrn2_release_v*/VRN2_Release_v*.json"]},
    "VQG": {"tail": ["functional modules/VQG/VQG_AllInOne_v*.py", "docs/handoff/ai/VIA_VQG_to_VAP_Contract_*.md"], "all": ["docs/handoff/ai/VIA_VQG_v*_*.md"]},
    "VAP": {"tail": ["functional modules/VAP/VAP_Param_Registry_v*.json", "functional modules/VAP/VAP_SystemManager_v*.py"], "all": ["functional modules/VAP/VAP_Subsystem_Manifest.json", "functional modules/VAP/intake/allinone_v0300/VAP_AllInOne_v*.py"]},
    "HANDOFF": {"tail": ["docs/handoff/ai/VIA_MasterPrompt_Baseline_v*.md", "docs/handoff/ai/VIA_FiveSystemConstitution_v*.py", "docs/handoff/ai/VIA_SettleAll_v*.py", "docs/handoff/ai/VIA_DailyBackup_v*.py"],
                "all": ["docs/handoff/HANDOFF_latest.json", "docs/handoff/README.md", "docs/handoff/evidence/*.json", "AGENTS.md", "CLAUDE.md", "../CLAUDE.md"]},
}
SIDE = {"graphify_receipt": "VIA_Reports/graphify/VIA_Graphify_latest.json", "graphify_doc": "docs/handoff/ai/via_graphify_v0101/VIA_Graphify_v0101.md",
        "ponytail": None, "external_tools_plan": "docs/handoff/ai/VIA_ExternalTools_Plan_20261106.md", "handoff_latest": "docs/handoff/HANDOFF_latest.json",
        "tool_lock": "supportive modules/registry/VIA_ToolVersion_Lock_v0100.json", "system_backup_book": "supportive modules/registry/VIA_VCGC_SystemBackup_v0100.json"}
MAX_FILE_BYTES = 40 * 1024 * 1024


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head(via: Path) -> dict:
    """直接讀 .git(倉根 = via 的上一層或 via 本身);不起子行程。"""
    for root in (via, via.parent):
        g = root / ".git"
        if not g.exists():
            continue
        try:
            if g.is_file():                                     # worktree / submodule:gitdir 指標
                g = Path(g.read_text(encoding="utf-8").split(":", 1)[1].strip())
                g = g if g.is_absolute() else (root / g)
            head = (g / "HEAD").read_text(encoding="utf-8").strip()
            if head.startswith("ref:"):
                ref = head.split(" ", 1)[1].strip()
                rp = g / ref
                sha = rp.read_text(encoding="utf-8").strip() if rp.is_file() else ""
                if not sha:
                    pk = g / "packed-refs"
                    if pk.is_file():
                        for line in pk.read_text(encoding="utf-8").splitlines():
                            if line.endswith(" " + ref):
                                sha = line.split(" ", 1)[0]
                return {"repo": str(root), "branch": ref.replace("refs/heads/", ""), "sha": sha}
            return {"repo": str(root), "branch": "(detached)", "sha": head}
        except (OSError, IndexError):
            return {"repo": str(root), "branch": "?", "sha": ""}
    return {"repo": None, "branch": None, "sha": ""}


def collect(via: Path, scope: dict) -> dict:
    """{SYS: [相對路徑…]}:tail 類取尾版 · all 類全收;不存在 = 跳過(列在 missing)。"""
    out, missing = {}, {}
    for sysname, spec in scope.items():
        files = []
        for pat in spec.get("tail", []):
            hits = sorted(p for p in via.glob(pat) if p.is_file())
            (files.append(hits[-1]) if hits else missing.setdefault(sysname, []).append(pat))
        for pat in spec.get("all", []):
            hits = sorted(p for p in via.glob(pat) if p.is_file())
            files.extend(hits) if hits else missing.setdefault(sysname, []).append(pat)
        out[sysname] = sorted({str(p.resolve()) for p in files})
    return {"files": out, "missing": missing}


def rel(via: Path, p: str) -> str:
    try:
        return str(Path(p).resolve().relative_to(via.resolve())).replace("\\", "/")
    except ValueError:
        return "../" + Path(p).name


def side_evidence(via: Path) -> dict:
    ev = {}
    for k, r in SIDE.items():
        if r is None:
            ev[k] = {"state": "ABSENT", "note": "倉內沒有 Ponytail 任何檔;外部工具計畫冊只有規劃 → 未安裝 · 未整合(照實);要啟用需桌機隔離環境安裝(同 Graphify 做法 · 同意閘操作員設)"}
            continue
        p = via / r
        if not p.exists():
            ev[k] = {"state": "ABSENT", "path": r}
            continue
        item = {"state": "PRESENT", "path": r, "bytes": p.stat().st_size}
        if p.suffix == ".json":
            try:
                d = json.loads(p.read_text(encoding="utf-8"))
                if k == "tool_lock":
                    item["tools"] = {t: {"path": v.get("path"), "exists": (via / str(v.get("path", "")).replace("VeritasIntelligenceAnalytics/", "", 1)).is_file() or (via.parent / str(v.get("path", ""))).is_file()}
                                     for t, v in d.items() if isinstance(v, dict) and v.get("path")}
                elif k == "handoff_latest":
                    item["summary"] = {kk: d.get(kk) for kk in ("generated_at", "ts", "lamp", "summary", "pending_count", "main") if kk in d}
                elif k == "graphify_receipt":
                    item["summary"] = {kk: d.get(kk) for kk in ("at", "lamp", "systems", "version") if kk in d}
            except (OSError, ValueError) as error:
                item["note"] = "讀不了 %s" % error
        ev[k] = item
    return ev


def do_backup(via: Path, out_root: Path, manifest_dir: Path) -> dict:
    at = datetime.now(timezone.utc)
    stamp = at.strftime("%Y%m%d_%H%M%SZ")
    bdir = out_root / stamp
    bdir.mkdir(parents=True, exist_ok=False)
    col = collect(via, SCOPE)
    head = git_head(via)
    man = {"schema": "VIA-DAILY-BACKUP-MANIFEST/1.0", "engine": ENGINE, "at": at.strftime("%Y-%m-%dT%H:%M:%SZ"), "stamp": stamp, "via_root": str(via), "git": head,
           "backup_dir": str(bdir), "systems": {}, "missing_patterns": col["missing"], "side_evidence": side_evidence(via), "reminders": []}
    total = 0
    for sysname, files in col["files"].items():
        zp = bdir / ("%s.zip" % sysname)
        entries = []
        with zipfile.ZipFile(zp, "w", compression=zipfile.ZIP_DEFLATED) as z:
            for f in files:
                p = Path(f)
                if p.stat().st_size > MAX_FILE_BYTES:
                    entries.append({"path": rel(via, f), "skipped": "too_large", "bytes": p.stat().st_size})
                    continue
                arc = rel(via, f)
                z.write(p, arc)
                entries.append({"path": arc, "sha256": sha256(p), "bytes": p.stat().st_size})
        man["systems"][sysname] = {"zip": zp.name, "zip_sha256": sha256(zp), "zip_bytes": zp.stat().st_size, "files": entries, "count": sum(1 for e in entries if "sha256" in e)}
        total += man["systems"][sysname]["count"]
    man["total_files"] = total
    if man["side_evidence"]["ponytail"]["state"] == "ABSENT":
        man["reminders"].append("Ponytail 未安裝 · 未整合(倉內無檔)· 要啟用請在桌機隔離環境安裝(同 Graphify)· 同意閘操作員設")
    if man["side_evidence"]["graphify_receipt"]["state"] == "ABSENT":
        man["reminders"].append("Graphify 收據不在本機(VIA_Reports/graphify/VIA_Graphify_latest.json)· 桌機跑 via_graphify_v0101 開機行後才有")
    man["reminders"].append("商業化 / 封裝 / 授權編號功能:倉內沒有(只有 MDL064 v0355「導入工具給 VIA 開頭商業化名稱」的命名註冊)· 操作員說在找上傳 → 到了再登")
    (bdir / "MANIFEST.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    sums = "\n".join("%s  %s" % (sha256(p), p.name) for p in sorted(bdir.iterdir()) if p.is_file() and p.name != "SHA256SUMS.txt") + "\n"
    (bdir / "SHA256SUMS.txt").write_text(sums, encoding="utf-8")
    manifest_dir.mkdir(parents=True, exist_ok=True)
    small = {k: v for k, v in man.items() if k != "backup_dir"}
    small["backup_dir"] = str(bdir)
    (manifest_dir / ("BACKUP_MANIFEST_%s.json" % stamp)).write_text(json.dumps(small, ensure_ascii=False, indent=1), encoding="utf-8")
    (manifest_dir / "BACKUP_MANIFEST_latest.json").write_text(json.dumps(small, ensure_ascii=False, indent=1), encoding="utf-8")
    (out_root / "BACKUP_latest.json").write_text(json.dumps({"stamp": stamp, "at": man["at"], "backup_dir": str(bdir), "total_files": total, "git": head, "lamp": "GREEN" if total else "RED"}, ensure_ascii=False, indent=1), encoding="utf-8")
    return man


def do_check(via: Path, out_root: Path, manifest_dir: Path) -> dict:
    cands = [manifest_dir / "BACKUP_MANIFEST_latest.json", out_root / "BACKUP_latest.json"]
    mp = next((p for p in cands if p.is_file()), None)
    at = datetime.now(timezone.utc)
    rec = {"engine": ENGINE, "verb": "check", "at": at.strftime("%Y-%m-%dT%H:%M:%SZ")}
    if mp is None:
        rec.update(lamp="RED", meaning="沒有任何備份 MANIFEST(docs/handoff/backup · VIA_Reports/backup)→ 先跑 backup")
        return rec
    man = json.loads(mp.read_text(encoding="utf-8"))
    if "systems" not in man:                                     # 只有 BACKUP_latest(指標)→ 去備份夾拿 MANIFEST
        mp2 = Path(man.get("backup_dir", "")) / "MANIFEST.json"
        if not mp2.is_file():
            rec.update(lamp="RED", meaning="備份夾 MANIFEST 缺 %s" % mp2)
            return rec
        man = json.loads(mp2.read_text(encoding="utf-8"))
    rec["manifest"] = str(mp)
    rec["backup_at"], rec["backup_git"] = man.get("at"), man.get("git")
    try:
        age_h = (at - datetime.strptime(man["at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)).total_seconds() / 3600.0
    except (KeyError, ValueError):
        age_h = None
    rec["age_hours"] = None if age_h is None else round(age_h, 2)
    head = git_head(via)
    rec["git_now"] = head
    rec["git_advanced"] = bool(head.get("sha") and man.get("git", {}).get("sha") and head["sha"] != man["git"]["sha"])
    same = changed = missing = 0
    changed_list, missing_list = [], []
    for sysname, s in man["systems"].items():
        for e in s["files"]:
            if "sha256" not in e:
                continue
            p = via / e["path"] if not e["path"].startswith("../") else via.parent / e["path"][3:]
            if not p.is_file():
                missing += 1
                missing_list.append(e["path"])
            elif sha256(p) != e["sha256"]:
                changed += 1
                changed_list.append(e["path"])
            else:
                same += 1
    rec["files"] = {"same": same, "changed": changed, "missing": missing, "changed_list": changed_list[:50], "missing_list": missing_list[:50]}
    bdir = Path(man.get("backup_dir", ""))
    zips = {}
    if bdir.is_dir() and (bdir / "SHA256SUMS.txt").is_file():
        want = dict(line.split("  ", 1)[::-1] for line in (bdir / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines() if "  " in line)
        for name, sha in want.items():
            p = bdir / name
            zips[name] = "OK" if p.is_file() and sha256(p) == sha else ("MISSING" if not p.is_file() else "SHA_MISMATCH")
        rec["zips"] = zips
        zip_state = "OK" if zips and all(v == "OK" for v in zips.values()) else ("MISMATCH" if any(v == "SHA_MISMATCH" for v in zips.values()) else "PARTIAL")
    else:
        zip_state = "NOT_LOCAL"
        rec["zips"] = {"note": "備份 zip 不在這台機器(%s)· 只能對倉內 sha" % bdir}
    rec["zip_state"] = zip_state
    total = same + changed + missing
    if zip_state == "MISMATCH" or (total and missing / total >= 0.50):
        lamp = "RED"
    elif changed or missing or zip_state != "OK" or rec["git_advanced"]:
        lamp = "YELLOW"
    else:
        lamp = "GREEN"
    rec["lamp"] = lamp
    rec["side_evidence_then"] = {k: v.get("state") for k, v in (man.get("side_evidence") or {}).items()}
    rec["reminders"] = man.get("reminders", [])
    rec["meaning"] = {"GREEN": "備份完整 · 倉內 %d 檔與備份時一字不差 · zip 驗過 · git 沒前進" % same,
                      "YELLOW": "可開工 · 但:%s" % " / ".join(x for x in (("%d 檔變了" % changed if changed else ""), ("%d 檔缺" % missing if missing else ""), ("zip %s" % zip_state if zip_state != "OK" else ""), ("git 已前進 %s→%s" % ((man.get("git") or {}).get("sha", "")[:8], head.get("sha", "")[:8]) if rec["git_advanced"] else "")) if x),
                      "RED": "備份不可信:zip sha 不符或 ≥50% 檔已不在 → 先 backup 再開工"}[lamp]
    return rec


def write_check_md(path: Path, rec: dict) -> None:
    L = ["# 備份檢查 · %s · %s · **%s**" % (rec["engine"], rec["at"], rec["lamp"]), "", rec.get("meaning", ""), ""]
    if "files" in rec:
        L += ["| 項 | 值 |", "|---|---|", "| 備份時間 | %s(%s 小時前) |" % (rec.get("backup_at"), rec.get("age_hours")), "| 備份 git | %s @ %s |" % ((rec.get("backup_git") or {}).get("branch"), ((rec.get("backup_git") or {}).get("sha") or "")[:12]),
              "| 現在 git | %s @ %s%s |" % ((rec.get("git_now") or {}).get("branch"), ((rec.get("git_now") or {}).get("sha") or "")[:12], " · 已前進" if rec.get("git_advanced") else ""),
              "| 倉內檔 | 同 %d · 變 %d · 缺 %d |" % (rec["files"]["same"], rec["files"]["changed"], rec["files"]["missing"]), "| zip | %s |" % rec.get("zip_state")]
        if rec["files"]["changed_list"]:
            L += ["", "變了的檔:", ""] + ["- %s" % x for x in rec["files"]["changed_list"]]
        if rec["files"]["missing_list"]:
            L += ["", "缺的檔:", ""] + ["- %s" % x for x in rec["files"]["missing_list"]]
    if rec.get("reminders"):
        L += ["", "## 提醒", ""] + ["- %s" % x for x in rec["reminders"]]
    path.write_text("\n".join(L) + "\n", encoding="utf-8")


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in argv or argv[:1] == ["selftest"]:                      # VCGC 站表 / 交接案用 --selftest 旗標
        return selftest()
    ap = argparse.ArgumentParser(prog="VIA_DailyBackup_v0100.py", description=__doc__.split("\n")[0])
    ap.add_argument("verb", choices=["backup", "check", "selftest"])
    ap.add_argument("--via", default=None, help="VIA 根(預設由本檔位置推)")
    ap.add_argument("--out", default=None, help="備份根(預設 <VIA>/VIA_Reports/backup)")
    ap.add_argument("--manifest-dir", dest="manifest_dir", default=None, help="入倉 MANIFEST 夾(預設 <VIA>/docs/handoff/backup)")
    args = ap.parse_args(argv)
    if args.verb == "selftest":
        return selftest()
    via = Path(args.via).resolve() if args.via else VIA
    out_root = Path(args.out) if args.out else via / BACKUP_ROOT_REL
    mdir = Path(args.manifest_dir) if args.manifest_dir else via / MANIFEST_DIR_REL
    if args.verb == "backup":
        man = do_backup(via, out_root, mdir)
        print("[%s] %s backup · %d 檔 · %d 系統 zip · git %s@%s → %s" % ("GREEN" if man["total_files"] else "RED", ENGINE, man["total_files"], len(man["systems"]), (man["git"] or {}).get("branch"), ((man["git"] or {}).get("sha") or "")[:8], man["backup_dir"]), flush=True)
        for r in man["reminders"]:
            print("  [提醒] " + r, flush=True)
        return 0 if man["total_files"] else 2
    rec = do_check(via, out_root, mdir)
    out_root.mkdir(parents=True, exist_ok=True)
    (out_root / "CHECK_latest.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    write_check_md(out_root / "CHECK_latest.md", rec)
    print("[%s] %s check · %s" % (rec["lamp"], ENGINE, rec.get("meaning", "")), flush=True)
    for r in rec.get("reminders", []):
        print("  [提醒] " + r, flush=True)
    return {"GREEN": 0, "YELLOW": 0, "RED": 2}[rec["lamp"]]


def selftest() -> int:
    checks = []

    def chk(name, cond, note=""):
        checks.append((name, bool(cond), note))
        print("  [%s] %s%s" % ("PASS" if cond else "FAIL", name, (" · " + note) if note else ""), flush=True)
    env_before = dict(os.environ)
    with tempfile.TemporaryDirectory(prefix="dailybackup_") as td:
        td = Path(td)
        repo = td / "repo"
        via = repo / "VeritasIntelligenceAnalytics"
        for r in ("supportive modules/registry", "functional modules/VDF", "functional modules/VRN", "functional modules/VQG", "functional modules/VAP", "docs/handoff/evidence", "docs/handoff/ai"):
            (via / r).mkdir(parents=True)
        (repo / ".git" / "refs" / "heads").mkdir(parents=True)
        (repo / ".git" / "HEAD").write_text("ref: refs/heads/test\n", encoding="utf-8")
        (repo / ".git" / "refs" / "heads" / "test").write_text("a" * 40 + "\n", encoding="utf-8")
        (via / "supportive modules/registry/VIA_Requirements_SSOT_v0001.json").write_text('{"v":1}', encoding="utf-8")
        (via / "supportive modules/registry/VIA_Requirements_SSOT_v0002.json").write_text('{"v":2}', encoding="utf-8")
        (via / "supportive modules/registry/VIA_NumberBook_X.jsonl").write_text('{"a":1}\n', encoding="utf-8")
        (via / "supportive modules/registry/VIA_ToolVersion_Lock_v0100.json").write_text(json.dumps({"token": {"path": "VeritasIntelligenceAnalytics/supportive modules/registry/tok.py"}}), encoding="utf-8")
        (via / "supportive modules/registry/tok.py").write_text("x=1\n", encoding="utf-8")
        (via / "functional modules/VDF/VDF_FetchGroups_SSOT_v0102.json").write_text('{"g":1}', encoding="utf-8")
        (via / "functional modules/VQG/VQG_AllInOne_v0108.py").write_text("# vqg\n", encoding="utf-8")
        (via / "docs/handoff/HANDOFF_latest.json").write_text(json.dumps({"lamp": "RED", "summary": "x"}), encoding="utf-8")
        (via / "docs/handoff/evidence/C-a.json").write_text("{}", encoding="utf-8")
        out, mdir = via / "VIA_Reports/backup", via / "docs/handoff/backup"
        man = do_backup(via, out, mdir)
        chk("① backup:只收尾版(Requirements v0002 不收 v0001)· jsonl 全收 · 每系統一 zip · MANIFEST + SHA256SUMS · 入倉 MANIFEST latest + 時戳檔",
            any(e["path"].endswith("VIA_Requirements_SSOT_v0002.json") for e in man["systems"]["VCGC"]["files"]) and not any("v0001" in e["path"] for e in man["systems"]["VCGC"]["files"])
            and (Path(man["backup_dir"]) / "VCGC.zip").is_file() and (Path(man["backup_dir"]) / "SHA256SUMS.txt").is_file() and (mdir / "BACKUP_MANIFEST_latest.json").is_file()
            and len(list(mdir.glob("BACKUP_MANIFEST_2*.json"))) == 1 and man["total_files"] >= 6)
        chk("② git HEAD 直接讀 .git(不起子行程)· 分支 test · sha 40 a", man["git"]["branch"] == "test" and man["git"]["sha"] == "a" * 40)
        se = man["side_evidence"]
        chk("③ 旁證照實:Ponytail ABSENT · Graphify 收據 ABSENT · 工具鎖 token 檔在 · HANDOFF 摘要 lamp RED · 提醒含商業化編號功能未在", se["ponytail"]["state"] == "ABSENT" and se["graphify_receipt"]["state"] == "ABSENT"
            and se["tool_lock"]["tools"]["token"]["exists"] is True and se["handoff_latest"]["summary"]["lamp"] == "RED" and any("商業化" in r for r in man["reminders"]))
        with zipfile.ZipFile(Path(man["backup_dir"]) / "VCGC.zip") as z:
            names = z.namelist()
        chk("④ zip 內路徑 = 相對 VIA 根 · 原檔一字沒動", "supportive modules/registry/VIA_Requirements_SSOT_v0002.json" in names and (via / "supportive modules/registry/VIA_Requirements_SSOT_v0002.json").read_text(encoding="utf-8") == '{"v":2}')
        rec = do_check(via, out, mdir)
        chk("⑤ check 緊接 backup:GREEN · 全同 · zip OK · git 沒前進", rec["lamp"] == "GREEN" and rec["files"]["changed"] == 0 and rec["zip_state"] == "OK" and not rec["git_advanced"])
        (via / "functional modules/VDF/VDF_FetchGroups_SSOT_v0102.json").write_text('{"g":2}', encoding="utf-8")
        (repo / ".git" / "refs" / "heads" / "test").write_text("b" * 40 + "\n", encoding="utf-8")
        rec = do_check(via, out, mdir)
        chk("⑥ 改一檔 + git 前進 → YELLOW · 點名變了的檔 · git_advanced", rec["lamp"] == "YELLOW" and rec["files"]["changed"] == 1 and rec["files"]["changed_list"][0].endswith("VDF_FetchGroups_SSOT_v0102.json") and rec["git_advanced"])
        (Path(man["backup_dir"]) / "VDF.zip").unlink()
        rec = do_check(via, out, mdir)
        chk("⑦ 刪一個 zip → zip PARTIAL(MISSING)· 仍 YELLOW(倉內 sha 還能對)", rec["zips"]["VDF.zip"] == "MISSING" and rec["zip_state"] == "PARTIAL" and rec["lamp"] == "YELLOW")
        (Path(man["backup_dir"]) / "VCGC.zip").write_bytes(b"tampered")
        rec = do_check(via, out, mdir)
        chk("⑧ zip 內容被改 → SHA_MISMATCH → RED", rec["zips"]["VCGC.zip"] == "SHA_MISMATCH" and rec["lamp"] == "RED")
        import shutil  # noqa: PLC0415
        shutil.rmtree(Path(man["backup_dir"]))
        rec = do_check(via, out, mdir)
        chk("⑨ 備份夾整個不在(全新容器)→ 仍能用入倉 MANIFEST 對 sha · zip NOT_LOCAL · YELLOW 照實", rec["zip_state"] == "NOT_LOCAL" and rec["lamp"] == "YELLOW" and rec["files"]["same"] >= 5)
        rc = main(["check", "--via", str(via)])
        chk("⑩ main check:寫 CHECK_latest.json / .md · rc 0(YELLOW)", rc == 0 and (out / "CHECK_latest.md").is_file())
        src = Path(__file__).read_text(encoding="utf-8")
        import re  # noqa: PLC0415
        chk("⑪ 邊界:不 import subprocess / urllib / requests · 不寫 environ", re.search(r"^\s*(import|from)\s+(subprocess|urllib|requests)\b", src, re.M) is None and not re.findall(r"os\.environ\[[^\]]+\]\s*=", src))
        chk("⑫ 環境變數原樣", dict(os.environ) == env_before)
    n = sum(1 for _, ok, _ in checks if ok)
    print("[%s] %s selftest · %d/%d" % ("PASS" if n == len(checks) else "FAIL", ENGINE, n, len(checks)), flush=True)
    return 0 if n == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
