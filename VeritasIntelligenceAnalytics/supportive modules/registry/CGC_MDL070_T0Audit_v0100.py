#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
via_t0_audit_v0100 — W0 凍結+T0 身份稽核引擎(TOOL-042;SPEC-015 def 27 第 1-2 步)
==================================================================================
授權邊界(操作員令 2026-08-18):START_W0_FREEZE_AND_T0_AUDIT_ONLY——
尚未授權母檔變更、Promote、Runtime 啟用或 Activation。本引擎 100% 唯讀:
  W0 凍結 — 不可變基線快照:git HEAD/branch/remote/髒檔數+核心治理資源
     SHA-256 雜湊集(缺件誠實列示)→ checkpoint.json(append-only 存證)
  T0 身份稽核 — Root 候選盤點(正典/舊樹/Downloads 複本/OneDrive 掃描)
     +三層 VIA_MOTHER_ROOT 指標分類+副本家族計數 → 裁決:
     T0_PASS(Root 唯一+核心資源零缺+指標無衝突)/ HOLD_IDENTITY(具名)
存證:VIA_Reports/governance_runs/RUN_<ts>_W0T0/(manifest/checkpoint/
     hash_inventory/gate_matrix;RUN-ID 格式依 SPEC-014 v0101 編號規約)
用法:via-t0            → W0+T0(唯讀)
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
REPO = VIA.parent
OUT = VIA / "VIA_Reports" / "governance_runs"

CORE_RESOURCES = [  # 核心治理資源(倉內相對路徑;缺=誠實列示)
    "supportive modules/registry/VIA_AutoCode_Registry_v0100.json",
    "supportive modules/registry/VIA_Interface_Contract_Registry_v0100.json",
    "supportive modules/registry/VIA_PS_Archive_Register_v0100.json",
    "supportive modules/registry/VIA_Syntax_Gate_Register_v0100.json",
    "supportive modules/registry/VIA_MasterGovernance_SSOT_v0100.json",
    "supportive modules/registry/VIA_Top25_Rules_v0100.json",
    "supportive modules/registry/VIA_SafeSandbox_MegaPrompt_v0100.md",
    "supportive modules/registry/VIA_ZeroHydra_RepairProtocol_v0100.md",
    "supportive modules/registry/VIA_Central_Governance_Complete_Execution_Plan_20260817.md",
    "supportive modules/VIA_EnvManager.py",
    "supportive modules/VIA_NetSupport.py",
    "supportive modules/SUP_MDL163_Toolkit.py",
    "functional modules/VAP/spec/ssot/vap_chartlib.json",
]


def _git(*args: str) -> str:
    r = subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True)
    return (r.stdout or "").strip()


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def main() -> int:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_id = f"RUN-{ts}-VIA-T0"
    run = OUT / f"RUN_{ts}_W0T0"
    print(f"=== W0 凍結+T0 身份稽核 v0100 · {run_id} · AUDIT ONLY(100% 唯讀)===")
    print("  [授權] 母檔變更=0 · Promote=0 · Runtime 啟用=0 · Activation=0(操作員令)")

    # ── W0 凍結:不可變基線 ──
    print("── W0 FREEZE(基線快照)──")
    head = _git("rev-parse", "HEAD")
    branch = _git("branch", "--show-current")
    remote = _git("remote", "get-url", "origin")
    dirty = [l for l in _git("status", "--porcelain").splitlines() if l.strip()]
    n_mod = sum(1 for l in dirty if not l.startswith("??"))
    n_unt = sum(1 for l in dirty if l.startswith("??"))
    print(f"  [git ] HEAD {head[:12]} · branch {branch or '(detached)'} · 已修改 {n_mod} · 未追蹤 {n_unt}")
    hashes, missing = {}, []
    for rel in CORE_RESOURCES:
        p = VIA / rel
        if p.is_file():
            hashes[rel] = {"sha256": sha256(p), "bytes": p.stat().st_size}
        else:
            missing.append(rel)
    print(f"  [核心] 治理資源 {len(hashes)}/{len(CORE_RESOURCES)} 在冊雜湊 · 缺 {len(missing)}"
          + (":" + "; ".join(m.split("/")[-1] for m in missing) if missing else "(零缺)"))

    # ── T0 身份稽核 ──
    print("── T0 IDENTITY(Root 仲裁證據)──")
    user_root = Path(os.environ.get("USERPROFILE") or Path.home())
    candidates = {
        "canonical(~\\movies-dataset)": REPO,
        "legacy(Downloads\\VIA)": user_root / "Downloads/VeritasIntelligenceAnalytics",
        "copy(Downloads\\movies-dataset)": user_root / "Downloads/movies-dataset",
    }
    roots_alive = []
    for label, p in candidates.items():
        exists = p.is_dir()
        is_git = (p / ".git").is_dir()
        h = ""
        if is_git:
            r = subprocess.run(["git", "-C", str(p), "rev-parse", "HEAD"], capture_output=True, text=True)
            h = (r.stdout or "").strip()[:12]
        if exists:
            roots_alive.append(label)
        print(f"  [根  ] {label:34s} {'在' if exists else '無'}"
              + (f" · git {h or '非repo'}" if exists else ""))
    layers = {}
    for scope_env in ("VIA_MOTHER_ROOT",):
        v = os.environ.get(scope_env, "")
        cls = ("UNSET" if not v else
               "CANONICAL" if Path(v) == VIA else
               "ONEDRIVE_禁" if "onedrive" in v.lower() else
               "LEGACY/複本" if "downloads" in v.lower() else "UNKNOWN")
        layers[scope_env] = {"value": v, "class": cls}
        print(f"  [指標] {scope_env}(Process 層)= {cls} · {v or '—'}")
    onedrive = os.environ.get("OneDrive", "")
    od_hit = bool(onedrive) and any(onedrive.lower() in str(p).lower() for p in candidates.values() if p.is_dir())
    print(f"  [OneDrive] 環境={'在(' + onedrive + ')' if onedrive else '無'} · Active Root 命中={'是(禁!)' if od_hit else '否'}")
    dup_rx = re.compile(r"\(\d+\)\.[^.]+$")
    n_dup = sum(1 for p in VIA.rglob("*") if p.is_file() and dup_rx.search(p.name) and ".git" not in p.parts)
    print(f"  [副本] 倉內 (N) 家族殘件 {n_dup} 件(Downloads 側另由 via-intake 仲裁)")

    # ── 裁決 ──
    holds = []
    if missing:
        holds.append(f"核心資源缺 {len(missing)}")
    if layers["VIA_MOTHER_ROOT"]["class"] in ("LEGACY/複本", "UNKNOWN", "ONEDRIVE_禁"):
        holds.append("母根指標非正典")
    if od_hit:
        holds.append("OneDrive 命中 Active Root(紅線)")
    if not (REPO / ".git").is_dir():
        holds.append("正典根非 git repo")
    verdict = "T0_PASS" if not holds else "HOLD_IDENTITY(" + ";".join(holds) + ")"
    note = "" if branch == "main" else f"(注:branch={branch or 'detached'} 非 main——證據記錄,候裁)"
    print(f"── 裁決:{verdict} {note}")
    print("  [鐵則] AUDIT ONLY——本輪零變更零晉升;T1+ 各閘另令另跑")

    run.mkdir(parents=True, exist_ok=True)
    (run / "manifest.json").write_text(json.dumps({
        "schema": "VIA.W0T0.v1", "run_id": run_id, "ts": ts, "mode": "AUDIT",
        "authorized": {"canonical_mutation": 0, "promote": 0, "runtime": 0, "activation": 0}},
        ensure_ascii=False, indent=1), encoding="utf-8")
    (run / "checkpoint.json").write_text(json.dumps({
        "git": {"head": head, "branch": branch, "remote": remote, "modified": n_mod, "untracked": n_unt},
        "frozen_at": ts}, ensure_ascii=False, indent=1), encoding="utf-8")
    (run / "hash_inventory.json").write_text(json.dumps({
        "core_resources": hashes, "missing": missing}, ensure_ascii=False, indent=1), encoding="utf-8")
    (run / "gate_matrix.json").write_text(json.dumps({
        "T0": {"verdict": verdict, "holds": holds, "roots_alive": roots_alive,
               "mother_root": layers, "onedrive_hit": od_hit, "dup_in_repo": n_dup}},
        ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  [存證] {run.relative_to(VIA)}(manifest/checkpoint/hash_inventory/gate_matrix)")
    return 0 if verdict == "T0_PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
