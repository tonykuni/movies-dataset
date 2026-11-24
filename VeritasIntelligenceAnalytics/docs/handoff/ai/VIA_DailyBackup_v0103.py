#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_DailyBackup v0103 — 薄尾(v0100–v0102 一字不動):一鍵還原(還原前驗證)+ 多 AI 共讀的備份卡(省 Token)

操作員 2026-11-24:「可以用 PY 寫這個引擎然後用短指令啟動?? 強化備份功能」→ 選「多 AI 備份共顯節省 TOKEN · 一鍵還原 + 還原前驗證」。
本版在既有每日備份(backup / check)上多兩個動詞,照舊:只讀來源 · 備份夾只增 · 不出網 · 不起子行程 · 不 import 他系統。

  restore [--stamp <UTC 時戳>|latest] [--sys VCGC,VDF,…] [--only <路徑片段>] [--apply]
    ① 先驗證(任何一項不過 → 紅 · 零寫入):SHA256SUMS 每一行 = 實檔 · MANIFEST 記的 zip sha = 實檔 · zip 裡每個檔的 sha = MANIFEST。
    ② 列計畫:跟倉裡現在的檔比 → 同(不動)· 變(要蓋回)· 缺(要補回);路徑一律要落在倉根之內(防 ../ 跳出)。
    ③ 預設只列計畫(乾跑);加 --apply 才寫:
         先把「要被蓋掉的現檔」另存到 VIA_Reports/backup/_pre_restore/<UTC>/(只增,附 MANIFEST)→
         每檔寫同夾暫存檔再原子換名 → 寫完逐檔再算 sha,要等於備份時的 sha,不等就紅並點名。
    收據:VIA_Reports/backup/RESTORE_latest.json(計畫與結果)。
  card
    多 AI 共讀的一張小卡(Claude / Gemini / ChatGPT / Cowork 都只讀這一張,不必掃備份夾):
      docs/handoff/backup/BACKUP_CARD_latest.md(≤ 40 行)+ BACKUP_CARD_latest.json
    內容只有:最新備份時間與每系統檔數 · 最近一次 check 的燈 · 最近一次還原 · Graphify 各系統圖在不在 · 一行指令。
    沒有任何資料內容(只有計數 · 路徑 · sha 前 12 碼)。backup / check / restore 跑完都會自動重寫這張卡。
  另補一個備份範圍(實錄缺口):VCGC 自己的 Graphify(CGC_MDL280 graphify run)把圖寫在
    VIA_Reports/vcgc/agentos/graphify/<系統>/graphify-out/,v0102 只收 VIA_Reports/graphify/ → 這些圖從來沒進備份。
    本版多收 graph.json · GRAPH_REPORT.md · VIA_Graphify_<系統>_latest.json · via-graph build 寫的快照
    SNAPSHOT_<系統>_latest.json 與 SNAPSHOT_ledger.jsonl(提交 · 工作樹改動數 · 圖 sha256)(graph.html 可由 graph.json 重生,不收)。
其餘(backup · check · OmniRoute 範圍 · 單檔上限)照 v0102。
用法:python VIA_DailyBackup_v0103.py backup | check | restore [...] | card | --selftest
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
import importlib.util
import json
import os
import re
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

VERSION = "v0103"
HERE = Path(__file__).resolve().parent
FAMILY = "VIA_DailyBackup"
ENGINE = "VIA_DailyBackup " + VERSION
CARD_MAX_LINES = 40


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0103", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR.BASE                                       # v0100:VIA · BACKUP_ROOT_REL · MANIFEST_DIR_REL · sha256 · do_backup / do_check


GRAPH_DIRS = ("VIA_Reports/graphify", "VIA_Reports/vcgc/agentos/graphify")     # 桌機 via_graphify · VCGC CGC_MDL280
EXTRA_SCOPE = {"GRAPHIFY_VCGC": {"all": ["VIA_Reports/vcgc/agentos/graphify/*/graphify-out/graph.json",
                                         "VIA_Reports/vcgc/agentos/graphify/*/graphify-out/GRAPH_REPORT.md",
                                         "VIA_Reports/vcgc/agentos/graphify/VIA_Graphify_*_latest.json",
                                         "VIA_Reports/vcgc/agentos/graphify/SNAPSHOT_*_latest.json",
                                         "VIA_Reports/vcgc/agentos/graphify/SNAPSHOT_ledger.jsonl"]}}


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def install() -> None:
    PRIOR.install()                                      # v0101 / v0102 的安裝照做
    BASE.SCOPE = {**BASE.SCOPE, **EXTRA_SCOPE}           # 多收 VCGC 自己的 Graphify 圖


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read(p: Path) -> dict:
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _write_atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(".%s.via_restore_tmp" % path.name)
    tmp.write_bytes(data)
    os.replace(tmp, path)


def repo_target(via: Path, rel: str) -> Path | None:
    """MANIFEST 的路徑 → 倉裡的實際位置(同 v0100 check 的對法);跳出倉根(含 ../../)→ None。"""
    p = (via.parent / rel[3:]) if rel.startswith("../") else (via / rel)
    root = via.parent.resolve()
    try:
        p.resolve().relative_to(root)
    except ValueError:
        return None
    return p


def find_backup(out_root: Path, stamp: str = "latest") -> Path | None:
    if stamp and stamp != "latest":
        d = out_root / stamp
        return d if (d / "MANIFEST.json").is_file() else None
    ptr = _read(out_root / "BACKUP_latest.json")
    if ptr.get("backup_dir") and (Path(ptr["backup_dir"]) / "MANIFEST.json").is_file():
        return Path(ptr["backup_dir"])
    dirs = sorted(d for d in out_root.glob("*Z") if (d / "MANIFEST.json").is_file())
    return dirs[-1] if dirs else None


def verify_backup(bdir: Path) -> dict:
    """還原前驗證:SHA256SUMS · MANIFEST 的 zip sha · zip 內每個檔的 sha。回 {ok, problems[], manifest}。"""
    problems = []
    man = _read(bdir / "MANIFEST.json")
    if not man.get("systems"):
        return {"ok": False, "problems": ["MANIFEST.json 缺或沒有 systems"], "manifest": man}
    sums = bdir / "SHA256SUMS.txt"
    if not sums.is_file():
        problems.append("SHA256SUMS.txt 缺")
    else:
        for line in sums.read_text(encoding="utf-8").splitlines():
            if "  " not in line:
                continue
            sha, name = line.split("  ", 1)
            p = bdir / name
            if not p.is_file():
                problems.append("SHA256SUMS 列的 %s 不在" % name)
            elif BASE.sha256(p) != sha:
                problems.append("%s 的 sha 跟 SHA256SUMS 不符" % name)
    for sysname, s in man["systems"].items():
        zp = bdir / s.get("zip", "")
        if not zp.is_file():
            problems.append("%s 的 zip 不在" % sysname)
            continue
        if BASE.sha256(zp) != s.get("zip_sha256"):
            problems.append("%s 的 zip sha 跟 MANIFEST 不符" % sysname)
            continue
        try:
            with zipfile.ZipFile(zp) as z:
                names = set(z.namelist())
                for e in s.get("files", []):
                    if "sha256" not in e:
                        continue
                    if e["path"] not in names:
                        problems.append("%s zip 裡少了 %s" % (sysname, e["path"]))
                    elif hashlib.sha256(z.read(e["path"])).hexdigest() != e["sha256"]:
                        problems.append("%s zip 裡 %s 的 sha 不符" % (sysname, e["path"]))
        except zipfile.BadZipFile:
            problems.append("%s 的 zip 壞了" % sysname)
    return {"ok": not problems, "problems": problems, "manifest": man}


def restore_plan(via: Path, man: dict, systems: list | None = None, only: str | None = None) -> dict:
    rows = []
    for sysname, s in man["systems"].items():
        if systems and sysname not in systems:
            continue
        for e in s.get("files", []):
            if "sha256" not in e or (only and only not in e["path"]):
                continue
            tgt = repo_target(via, e["path"])
            if tgt is None:
                rows.append({"sys": sysname, "path": e["path"], "state": "REFUSED", "why": "路徑跳出倉根"})
                continue
            state = "MISSING" if not tgt.is_file() else ("SAME" if BASE.sha256(tgt) == e["sha256"] else "CHANGED")
            rows.append({"sys": sysname, "path": e["path"], "state": state, "sha256": e["sha256"], "zip": s["zip"]})
    count = {k: sum(1 for r in rows if r["state"] == k) for k in ("SAME", "CHANGED", "MISSING", "REFUSED")}
    return {"rows": rows, "count": count}


def do_restore(via: Path, out_root: Path, stamp: str = "latest", systems: list | None = None, only: str | None = None,
               apply: bool = False) -> dict:
    rec = {"engine": ENGINE, "verb": "restore", "at": _now(), "apply": apply, "stamp": stamp}
    bdir = find_backup(out_root, stamp)
    if bdir is None:
        rec.update(lamp="RED", meaning="找不到備份(%s · %s)→ 先 backup" % (out_root, stamp))
        return rec
    rec["backup_dir"] = str(bdir)
    ver = verify_backup(bdir)
    rec["verify"] = {"ok": ver["ok"], "problems": ver["problems"][:50]}
    if not ver["ok"]:
        rec.update(lamp="RED", meaning="還原前驗證沒過(%d 項)→ 這份備份不能拿來還原,零寫入" % len(ver["problems"]))
        return rec
    plan = restore_plan(via, ver["manifest"], systems, only)
    todo = [r for r in plan["rows"] if r["state"] in ("CHANGED", "MISSING")]
    rec["plan"] = {"count": plan["count"], "todo": [{k: r[k] for k in ("sys", "path", "state")} for r in todo][:200]}
    if plan["count"]["REFUSED"]:
        rec.update(lamp="RED", meaning="MANIFEST 有 %d 個路徑跳出倉根 → 拒絕還原(零寫入)" % plan["count"]["REFUSED"])
        return rec
    if not apply:
        rec.update(lamp="GREEN" if not todo else "YELLOW",
                   meaning=("倉裡跟備份一模一樣,不用還原" if not todo else
                            "乾跑:要蓋回 %d 檔 · 補回 %d 檔(加 --apply 才寫;寫之前先另存現檔)" % (plan["count"]["CHANGED"], plan["count"]["MISSING"])))
        return rec
    if not todo:
        rec.update(lamp="GREEN", meaning="倉裡跟備份一模一樣,不用還原", restored=[], pre_restore_dir=None)
        return rec
    pre = out_root / "_pre_restore" / datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%fZ")
    pre.mkdir(parents=True, exist_ok=False)
    saved = []
    for r in todo:                                       # 先另存要被蓋掉的現檔(只增)
        tgt = repo_target(via, r["path"])
        if tgt is not None and tgt.is_file():
            dst = pre / r["path"].replace("../", "_up_/")
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(tgt.read_bytes())
            saved.append({"path": r["path"], "sha256": BASE.sha256(dst)})
    (pre / "MANIFEST.json").write_text(json.dumps({"engine": ENGINE, "at": _now(), "from_backup": str(bdir), "saved": saved},
                                                 ensure_ascii=False, indent=1), encoding="utf-8")
    done, bad = [], []
    zips = {}
    try:
        for r in todo:
            z = zips.get(r["zip"]) or zips.setdefault(r["zip"], zipfile.ZipFile(bdir / r["zip"]))
            tgt = repo_target(via, r["path"])
            _write_atomic(tgt, z.read(r["path"]))
            (done if BASE.sha256(tgt) == r["sha256"] else bad).append(r["path"])
    finally:
        for z in zips.values():
            z.close()
    rec.update(restored=done, mismatched=bad, pre_restore_dir=str(pre), saved_before=len(saved),
               lamp="RED" if bad else "GREEN",
               meaning=("還原 %d 檔 · 寫完逐檔 sha 都等於備份時 · 原檔另存在 %s" % (len(done), pre)) if not bad else
                       ("還原後 %d 檔 sha 不等於備份時:%s" % (len(bad), ", ".join(bad[:5]))))
    return rec


def _graph_status(via: Path) -> list:
    rows = []
    for rel_dir in GRAPH_DIRS:
        base = via / rel_dir
        for sysdir in sorted(p for p in base.glob("*") if p.is_dir()) if base.is_dir() else []:
            g = sysdir / "graphify-out" / "graph.json"
            rows.append({"sys": sysdir.name, "where": rel_dir, "graph": g.is_file(), "bytes": g.stat().st_size if g.is_file() else 0,
                         "at": datetime.fromtimestamp(g.stat().st_mtime, timezone.utc).strftime("%Y-%m-%dT%H:%MZ") if g.is_file() else None})
    return rows


def build_card(via: Path, out_root: Path, manifest_dir: Path) -> dict:
    ptr = _read(out_root / "BACKUP_latest.json") or {}
    man = _read(manifest_dir / "BACKUP_MANIFEST_latest.json") or {}
    chk = _read(out_root / "CHECK_latest.json") or {}
    rst = _read(out_root / "RESTORE_latest.json") or {}
    systems = {k: v.get("count", 0) for k, v in (man.get("systems") or {}).items()}
    return {
        "schema": "VIA-BACKUP-CARD/1.0", "engine": ENGINE, "written_at": _now(),
        "backup": {"stamp": ptr.get("stamp") or man.get("stamp"), "at": ptr.get("at") or man.get("at"),
                   "total_files": ptr.get("total_files", man.get("total_files")), "systems": systems,
                   "git": ((man.get("git") or {}).get("branch"), ((man.get("git") or {}).get("sha") or "")[:12])},
        "check": {"lamp": chk.get("lamp", "GRAY"), "at": chk.get("at"), "meaning": (chk.get("meaning") or "")[:160],
                  "files": {k: (chk.get("files") or {}).get(k) for k in ("same", "changed", "missing")}},
        "restore": {"lamp": rst.get("lamp", "GRAY"), "at": rst.get("at"), "apply": rst.get("apply"),
                    "meaning": (rst.get("meaning") or "")[:160]},
        "graphify": _graph_status(via),
        "commands": ["via-bak(備份 + Graphify / OmniRoute)", "via-bak check(對倉)", "via-bak restore(乾跑:先驗證再列計畫)",
                     "via-bak restore --apply [--sys VCGC] [--only <路徑片段>](先另存現檔再還原)", "via-bak card(重寫本卡)",
                     "via-graph status · via-graph query \"<問題>\" --sys VRN"],
    }


def write_card(via: Path, out_root: Path, manifest_dir: Path) -> dict:
    card = build_card(via, out_root, manifest_dir)
    b, c, r = card["backup"], card["check"], card["restore"]
    lines = ["# VIA 備份卡(多 AI 共讀 · 只讀這一張就好)· %s" % card["written_at"], "",
             "- 最新備份:%s · %s 檔 · git %s@%s" % (b["stamp"] or "—", b["total_files"] if b["total_files"] is not None else "—", b["git"][0] or "—", b["git"][1] or "—"),
             "- 各系統檔數:%s" % (" · ".join("%s %d" % kv for kv in sorted(b["systems"].items())) or "—"),
             "- 最近 check:**%s** · %s · %s" % (c["lamp"], c["at"] or "—", c["meaning"] or "—"),
             "- 最近還原:**%s** · %s · %s" % (r["lamp"], r["at"] or "—", r["meaning"] or "—"),
             "- Graphify:%s" % (" · ".join("%s %s" % (g["sys"], "有圖 %s" % g["at"] if g["graph"] else "沒圖") for g in card["graphify"]) or "本機還沒有圖(via-graph build 建)"),
             "", "指令(一行一個):"] + ["- `%s`" % x for x in card["commands"]] + [
             "", "規則:本卡只有計數 · 路徑 · sha 前 12 碼,沒有資料內容;備份夾只增;還原預設乾跑。"]
    lines = lines[:CARD_MAX_LINES]
    manifest_dir.mkdir(parents=True, exist_ok=True)
    _write_atomic(manifest_dir / "BACKUP_CARD_latest.md", ("\n".join(lines) + "\n").encode("utf-8"))
    _write_atomic(manifest_dir / "BACKUP_CARD_latest.json", (json.dumps(card, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))
    card["md_lines"] = len(lines)
    return card


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in argv or argv[:1] == ["selftest"]:
        return selftest()
    install()
    verb = argv[0] if argv else ""
    if verb not in ("restore", "card"):
        rc = PRIOR.main(argv)
        if verb in ("backup", "check"):
            via, out_root, mdir = _paths(argv)
            write_card(via, out_root, mdir)
        return rc
    ap = argparse.ArgumentParser(prog="VIA_DailyBackup_v0103.py", description=__doc__.split("\n")[0])
    ap.add_argument("verb", choices=["restore", "card"])
    ap.add_argument("--via", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--manifest-dir", dest="manifest_dir", default=None)
    ap.add_argument("--stamp", default="latest")
    ap.add_argument("--sys", default="")
    ap.add_argument("--only", default="")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args(argv)
    via = Path(a.via).resolve() if a.via else BASE.VIA
    out_root = Path(a.out) if a.out else via / BASE.BACKUP_ROOT_REL
    mdir = Path(a.manifest_dir) if a.manifest_dir else via / BASE.MANIFEST_DIR_REL
    if a.verb == "card":
        card = write_card(via, out_root, mdir)
        print("[%s] %s card · %d 行 → %s" % (card["check"]["lamp"], ENGINE, card["md_lines"], mdir / "BACKUP_CARD_latest.md"), flush=True)
        return 0
    rec = do_restore(via, out_root, a.stamp, [s for s in a.sys.split(",") if s] or None, a.only or None, a.apply)
    out_root.mkdir(parents=True, exist_ok=True)
    _write_atomic(out_root / "RESTORE_latest.json", (json.dumps(rec, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))
    print("[%s] %s restore%s · %s" % (rec["lamp"], ENGINE, " --apply" if a.apply else "(乾跑)", rec.get("meaning", "")), flush=True)
    for p in (rec.get("verify") or {}).get("problems", [])[:10]:
        print("  [驗證] " + p, flush=True)
    for t in (rec.get("plan") or {}).get("todo", [])[:20]:
        print("  [%s] %s · %s" % (t["state"], t["sys"], t["path"]), flush=True)
    write_card(via, out_root, mdir)
    return {"GREEN": 0, "YELLOW": 0, "RED": 2}[rec["lamp"]]


def _paths(argv: list) -> tuple:
    def opt(name):
        return argv[argv.index(name) + 1] if name in argv and argv.index(name) + 1 < len(argv) else None
    via = Path(opt("--via")).resolve() if opt("--via") else BASE.VIA
    out_root = Path(opt("--out")) if opt("--out") else via / BASE.BACKUP_ROOT_REL
    mdir = Path(opt("--manifest-dir")) if opt("--manifest-dir") else via / BASE.MANIFEST_DIR_REL
    return via, out_root, mdir


def selftest() -> int:
    import contextlib
    import io
    import tempfile
    ok = []

    def chk(n, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", n, (" · " + str(note)[:300]) if note and not cond else ""), flush=True)

    print("=== %s 自測(零網路 · 暫存假倉 · 前版 %s)===" % (ENGINE, PRIOR_PATH.name), flush=True)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc_prior = PRIOR.selftest()                       # 先跑前版(本版還沒動任何模組狀態)
    with tempfile.TemporaryDirectory(prefix="via_bak103_") as td:
        repo = Path(td) / "repo"
        via = repo / "VeritasIntelligenceAnalytics"
        reg = via / "supportive modules" / "registry"
        reg.mkdir(parents=True)
        for name in ("VIA_Requirements_SSOT_v0100.json", "VIA_Handoff_Continuity_SSOT_v0100.json"):
            (reg / name).write_text('{"a": 1}\n', encoding="utf-8")
        (repo / "CLAUDE.md").write_text("# rules\n", encoding="utf-8")
        out_root, mdir = via / "VIA_Reports" / "backup", via / "docs" / "handoff" / "backup"
        install()
        chk("⓪ 多收 VCGC 自己的 Graphify 圖(VIA_Reports/vcgc/agentos/graphify)", "GRAPHIFY_VCGC" in BASE.SCOPE
            and any("vcgc/agentos/graphify" in g for g in BASE.SCOPE["GRAPHIFY_VCGC"]["all"]))
        keep_scope = BASE.SCOPE
        BASE.SCOPE = {"VCGC": {"all": ["supportive modules/registry/VIA_*.json", "../CLAUDE.md"]}}
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                man = BASE.do_backup(via, out_root, mdir)
        finally:
            BASE.SCOPE = keep_scope
        files = man["systems"]["VCGC"]["files"]
        chk("① 假倉備份成功(含倉根的 ../CLAUDE.md)", man["total_files"] == 3 and any(e["path"] == "../CLAUDE.md" for e in files), files)
        same = do_restore(via, out_root)
        chk("② 倉裡沒變 → 乾跑 GREEN、不用還原", same["lamp"] == "GREEN" and same["plan"]["count"]["SAME"] == 3, same.get("meaning"))
        (reg / "VIA_Requirements_SSOT_v0100.json").write_text('{"a": 2}\n', encoding="utf-8")
        (repo / "CLAUDE.md").unlink()
        dry = do_restore(via, out_root)
        chk("③ 改一檔 · 刪一檔 → 乾跑 YELLOW、列出 1 變 1 缺、一個字都沒寫",
            dry["lamp"] == "YELLOW" and dry["plan"]["count"]["CHANGED"] == 1 and dry["plan"]["count"]["MISSING"] == 1
            and (reg / "VIA_Requirements_SSOT_v0100.json").read_text(encoding="utf-8") == '{"a": 2}\n' and not (repo / "CLAUDE.md").exists(), dry.get("plan"))
        applied = do_restore(via, out_root, apply=True)
        pre = Path(applied.get("pre_restore_dir") or "")
        chk("④ --apply:先另存現檔 → 還原 2 檔 → 寫完 sha 都對、內容回到備份時",
            applied["lamp"] == "GREEN" and len(applied["restored"]) == 2
            and (reg / "VIA_Requirements_SSOT_v0100.json").read_text(encoding="utf-8") == '{"a": 1}\n' and (repo / "CLAUDE.md").is_file()
            and (pre / "supportive modules" / "registry" / "VIA_Requirements_SSOT_v0100.json").read_text(encoding="utf-8") == '{"a": 2}\n',
            applied.get("meaning"))
        bdir = Path(applied["backup_dir"])
        zp = bdir / "VCGC.zip"
        raw = bytearray(zp.read_bytes())
        raw[-5] ^= 0xFF
        zp.write_bytes(bytes(raw))
        (reg / "VIA_Requirements_SSOT_v0100.json").write_text('{"a": 3}\n', encoding="utf-8")
        tampered = do_restore(via, out_root, apply=True)
        chk("⑤ 備份 zip 被動過 → 還原前驗證紅、零寫入(現檔原封不動)",
            tampered["lamp"] == "RED" and not tampered["verify"]["ok"]
            and (reg / "VIA_Requirements_SSOT_v0100.json").read_text(encoding="utf-8") == '{"a": 3}\n', tampered.get("verify"))
        chk("⑥ 跳出倉根的路徑一律拒絕", repo_target(via, "../../outside.txt") is None and repo_target(via, "../CLAUDE.md") is not None)
        card = write_card(via, out_root, mdir)
        md = (mdir / "BACKUP_CARD_latest.md").read_text(encoding="utf-8")
        chk("⑦ 多 AI 共讀卡:≤ 40 行 · 有最新備份 / check / 還原 / 指令 · 沒有檔案內容",
            card["md_lines"] <= CARD_MAX_LINES and "最新備份" in md and "最近還原" in md and "via-bak restore" in md and '"a"' not in md,
            md[:300])
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    chk("⑧ 零網路 · 零 TA-Lib · 不起子行程 · 不 import 他系統",
        not re.search(r"^\s*(?:import|from)\s+(talib|requests|urllib|socket|http|subprocess|CGC_|VDF_|VRN_)", body, re.M))
    chk("⑨ 前版 %s 自測照過" % PRIOR_PATH.name, rc_prior == 0, buf.getvalue()[-300:])
    n = sum(ok)
    print("[%s] %s selftest · %d/%d" % ("PASS" if n == len(ok) else "FAIL", ENGINE, n, len(ok)), flush=True)
    return 0 if n == len(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
