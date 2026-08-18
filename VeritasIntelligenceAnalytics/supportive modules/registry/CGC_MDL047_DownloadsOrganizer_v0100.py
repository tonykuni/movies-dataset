#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
via_downloads_organizer_v0100 — Downloads 整理歸納去重引擎(TOOL-023)
======================================================================
操作員令(2026-08-12):Downloads 近期非常雜亂,協助整理歸納去重。
治理鐵則:
  ① dry-run 預設 — 只出分類+搬移計畫與清單,零搬動;--commit 才執行
  ② 零刪除 — 一律「搬移歸位」到 Downloads\\_VIA_Tidy\\<類>\\,永不刪檔
  ③ 全程可逆 — 每次 commit 寫 manifest(from→to 全記錄),--undo 可整批還原
  ④ 對庫去重 — 與 movies-dataset 倉內正本同名比 hash:全同=已在庫(可歸檔);
     不同=變體(候裁決);無同名=候上傳(價值件清單)
  ⑤ 白名單零觸碰 — 系統資料夾(VeritasIntelligenceAnalytics/movies-dataset
     等)與正在使用之根目錄不搬
分類:
  dup_identical   瀏覽器複本 (N) 與本體 hash 全同(冗餘)
  dup_variant     瀏覽器複本 (N) 與本體內容不同(候裁決)
  in_repo         與倉內正本 hash 全同(已收容,Downloads 副本可歸檔)
  candidate_upload 倉內無同名之 VIA 件(候上傳價值清單)
  gemini_temp     gemini-code-* 暫存
  installer       安裝程式 exe
  archive_zip     壓縮包
  personal        個人文件(PIP/WorkMatrix/email 系列)
  data_file       數據檔(csv/json/parquet 非 VIA 命名)
  other           其餘
用法:via-tidy               → dry-run 計畫
     via-tidy --commit      → 執行搬移(寫 manifest)
     via-tidy --undo <manifest.json> → 整批還原
     via-tidy --root <路徑> → 指定掃描根(預設 ~/Downloads)
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent

PROTECT_DIRS = {"veritasintelligenceanalytics", "movies-dataset", "_via_tidy", "_via_sorted"}
DUP_RX = re.compile(r"^(.*?)[ ]?\((\d+)\)(\.[^.]+)?$")
VIA_RX = re.compile(r"^(via|via_|via-|vrn|vdf|vap|vmt|vpns|veritas|invoke-via|invoke-veritas|invoke_via|ssot_|flow_|tfe_|panoramic|qa_|readme_|release_notes|stage2|it_|target_acceptance|board_|selftest_|registry_proposal)", re.I)
PERSONAL_RX = re.compile(r"^(pip[_ ]|workmatrix|email_|engine_manager|engine_analytics|prompt_voice|sop_|qtracker|batchtracking|onboarding|methodology|deep-research|Overleveraged)", re.I)


def h12(p: Path) -> str | None:
    try:
        return hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()[:12]
    except Exception:
        return None


def build_repo_index():
    idx = {}
    for p in VIA.rglob("*"):
        if p.is_file() and ".git" not in p.parts and "__pycache__" not in p.parts:
            idx.setdefault(p.name.lower(), []).append(p)
    return idx


def classify(p: Path, root: Path, repo_idx: dict):
    name = p.name
    low = name.lower()
    if low.startswith("gemini-code-"):
        return "gemini_temp", ""
    if low.endswith(".exe"):
        return "installer", ""
    m = DUP_RX.match(name)
    if m:
        base = root / (m.group(1).rstrip() + (m.group(3) or ""))
        if base.exists() and base.is_file():
            same = h12(p) == h12(base)
            return ("dup_identical" if same else "dup_variant"), f"本體={base.name}"
    hits = repo_idx.get(low, [])
    if hits:
        ph = h12(p)
        for c in hits:
            if h12(c) == ph:
                return "in_repo", str(c.relative_to(VIA))
        return "dup_variant", f"倉內同名異內容:{hits[0].relative_to(VIA)}"
    if PERSONAL_RX.search(name):
        return "personal", ""
    if low.endswith(".zip"):
        return "archive_zip", ""
    if VIA_RX.search(name):
        return "candidate_upload", "倉內無同名(候上傳)"
    if low.endswith((".csv", ".json", ".parquet", ".jsonl", ".xlsx")):
        return "data_file", ""
    return "other", ""


def main() -> int:
    args = sys.argv[1:]
    commit = "--commit" in args
    if "--undo" in args:
        mf = Path(args[args.index("--undo") + 1])
        plan = json.loads(mf.read_text(encoding="utf-8"))
        n = 0
        for mv in reversed(plan.get("moves", [])):
            src, dst = Path(mv["to"]), Path(mv["from"])
            if src.exists() and not dst.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), str(dst))
                n += 1
        print(f"[undo] 還原 {n}/{len(plan.get('moves', []))} 件(既存目標誠實略過)")
        return 0

    root = Path(args[args.index("--root") + 1]) if "--root" in args else Path.home() / "Downloads"
    if not root.is_dir():
        print(f"[FAIL] 掃描根不存在:{root}")
        return 1
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    tidy = root / "_VIA_Tidy"
    print(f"=== Downloads 整理歸納去重 v0100 · {root} · {'COMMIT' if commit else 'DRY-RUN(--commit 才搬)'} ===")
    print("  [索引] 建倉內正本索引…")
    repo_idx = build_repo_index()
    print(f"  [索引] 倉內 {sum(len(v) for v in repo_idx.values()):,} 檔")

    groups: dict[str, list] = {}
    skipped_dirs = 0
    for p in sorted(root.iterdir()):
        if p.name.lower() in PROTECT_DIRS or p.name.startswith(("_VIA_Tidy", "VIA_Tidy_Manifest")):
            continue
        if p.is_dir():
            skipped_dirs += 1  # 資料夾第一輪不搬(誠實列示,候第二輪裁決)
            continue
        cat, note = classify(p, root, repo_idx)
        groups.setdefault(cat, []).append((p, note))

    order = ["dup_identical", "in_repo", "gemini_temp", "installer", "dup_variant",
             "candidate_upload", "archive_zip", "personal", "data_file", "other"]
    moves = []
    for cat in order:
        items = groups.get(cat, [])
        if not items:
            continue
        print(f"  ── {cat}({len(items)} 件)──")
        for p, note in items[:8]:
            print(f"     · {p.name[:70]}" + (f"  [{note[:40]}]" if note else ""))
        if len(items) > 8:
            print(f"     …(共 {len(items)} 件,全清單見 manifest)")
        for p, note in items:
            moves.append({"from": str(p), "to": str(tidy / cat / p.name), "cat": cat, "note": note})

    n_files = sum(len(v) for v in groups.values())
    print(f"  [計] 檔案 {n_files} 件分 {len([c for c in order if groups.get(c)])} 類 · 資料夾 {skipped_dirs} 個(第一輪不搬,誠實列示)")
    cu = groups.get("candidate_upload", [])
    if cu:
        print(f"  [候上傳] {len(cu)} 件倉內無同名——清單在 manifest,逐批上傳即歸巢")

    mf = root / f"VIA_Tidy_Manifest_{ts}.json"
    mf.write_text(json.dumps({"schema": "VIA.TidyManifest.v1", "ts": ts, "root": str(root),
                              "mode": "commit" if commit else "dry_run", "moves": moves,
                              "skipped_dirs": skipped_dirs}, ensure_ascii=False, indent=1),
                  encoding="utf-8")
    print(f"  [單] {mf.name}(from→to 全記錄;--undo 可整批還原)")

    if not commit:
        print("  [dry-run] 零搬動。確認計畫後:via-tidy --commit")
        return 0
    done = skip = 0
    for mv in moves:
        src, dst = Path(mv["from"]), Path(mv["to"])
        if not src.exists() or dst.exists():
            skip += 1
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        done += 1
    print(f"  [搬] {done} 件歸位 _VIA_Tidy\\ · 略過 {skip}(零刪除;--undo \"{mf}\" 可還原)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
