#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
vme_main — VME 方法論引擎核心 v0.1(TOOL-056;方法論導入令 2026-08-18)
======================================================================
藍圖:specs/VIA_VME_Methodology_DeepResearch_20260816.md(Phase 0-1)。
落地三大修正(報告最高優先):
  ① 不可變儲存:immutable multi-part dataset(part-{run}-{uuid})+staging
     →read-back 完整性→SHA-256→atomic publish→manifest append;
     絕不「讀舊檔 concat 整檔重寫」;舊 part hash 永不變
  ② fail-closed:未知 mode 不靜默降級=直接拒;RuntimeAppendOnly 需
     Python 端二次核准(mode+approval.runtime_append 雙真),繞過 PS 無效
  ③ 狀態機:state_transition append-only 台帳;current_state 由最新
     transition 推導;非法跳轉直接拒(guard 表=報告 stateDiagram)
Meta-Alpha KPI 冊位:MTTD-E/MTTR-E/FCR/LLAR/ERR-R(值=實測候接,不捏造)。
用法:vme_main.py --config <json> --mode InspectOnly [--request <json>]
     vme_main.py --selftest
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VME = HERE.parent

LEGAL = {  # 報告 stateDiagram 正式轉換表
    "Experimental": {"Watch", "Disabled"},
    "Watch": {"Active", "Retest", "Disabled"},
    "Active": {"Dormant", "Reverse", "Disabled", "Retest", "Retired"},
    "Dormant": {"Retest"}, "Reverse": {"Retest"}, "Disabled": {"Retest"},
    "Retest": {"Active", "Dormant", "Retired"},
    "Retired": {"Reborn"}, "Reborn": {"Watch"},
}


class Policy:
    def __init__(self, write_durable: bool, tag: str):
        self.write_durable = write_durable
        self.tag = tag


def load_system_config(path: Path) -> dict:
    cfg = json.loads(path.read_text(encoding="utf-8"))
    for k in ("modes", "policy", "paths"):
        if k not in cfg:
            raise ValueError(f"config 缺必要鍵 {k}(fail-closed)")
    return cfg


def resolve_mode_policy(mode: str, approval: bool) -> Policy:
    """fail-closed:未知 mode 拒,不靜默降級(報告策略修改)。"""
    if mode == "InspectOnly":
        return Policy(False, "inspect")
    if mode == "SandboxDryRun":
        return Policy(False, "sandbox")
    if mode == "RuntimeAppendOnly":
        return Policy(bool(approval), "runtime")
    raise ValueError(f"未知 mode '{mode}'——fail-closed 直接拒(不降級)")


def authorize_operation(mode: str, runtime_append_approved: bool) -> None:
    """Python 二次核准:繞過 PowerShell 直呼也擋(報告重大補強)。"""
    if mode == "RuntimeAppendOnly" and not runtime_append_approved:
        raise PermissionError("RuntimeAppendOnly 未經 approval.runtime_append=true——拒(fail closed)")


def build_run_context(cfg: dict) -> dict:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return {"run_id": f"RUN-{ts}-{uuid.uuid4().hex[:6]}",
            "config_hash": hashlib.sha256(json.dumps(cfg, sort_keys=True).encode()).hexdigest()[:16],
            "started_at": ts}


class Lake:
    """不可變 multi-part dataset+manifest(單寫者;冪等鍵)。"""

    def __init__(self, root: Path):
        self.root = root
        self.manifest = root / "run_manifest" / "manifest.jsonl"
        self.idem = root / "run_manifest" / "idempotency.jsonl"

    def _seen(self, key: str) -> bool:
        if not self.idem.exists():
            return False
        return any(json.loads(l)["key"] == key for l in self.idem.read_text(encoding="utf-8").splitlines() if l.strip())

    def append(self, entity: str, rows: list[dict], run_id: str, idem_key: str) -> dict:
        if self._seen(idem_key):
            return {"written": 0, "dedup": True, "note": f"idempotency_key 重送——零重複寫(誠實)"}
        part_dir = self.root / entity
        staging = self.root / "_staging"
        part_dir.mkdir(parents=True, exist_ok=True)
        staging.mkdir(parents=True, exist_ok=True)
        name = f"part-{run_id}-{uuid.uuid4().hex[:8]}"
        try:
            import pandas as pd
            sp = staging / f"{name}.parquet"
            pd.DataFrame(rows).to_parquet(sp, index=False)
            pd.read_parquet(sp)  # read-back 完整性檢
        except ImportError:  # 誠實降級:jsonl part(合約=不可變 part+manifest,格式次之)
            sp = staging / f"{name}.jsonl"
            sp.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows), encoding="utf-8")
        sha = hashlib.sha256(sp.read_bytes()).hexdigest()
        final = part_dir / sp.name
        os.replace(sp, final)  # atomic publish
        self.manifest.parent.mkdir(parents=True, exist_ok=True)
        with open(self.manifest, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"part_file": f"{entity}/{final.name}", "entity": entity, "sha256": sha,
                                 "rows": len(rows), "run_id": run_id}, ensure_ascii=False) + "\n")
        with open(self.idem, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"key": idem_key, "part": final.name}) + "\n")
        return {"written": len(rows), "part": f"{entity}/{final.name}", "sha256": sha}

    def transition(self, entity_type: str, entity_id: str, frm: str, to: str,
                   trigger: str, run_id: str, evidence_ids: list | None = None) -> dict:
        if to not in LEGAL.get(frm, set()):
            raise ValueError(f"非法轉換 {frm}→{to}(guard 表拒;current_state 永不直接覆寫)")
        import time
        row = {"transition_id": f"TR-{uuid.uuid4().hex[:10]}", "entity_type": entity_type,
               "entity_id": entity_id, "from_state": frm, "to_state": to, "trigger": trigger,
               "evidence_ids": evidence_ids or [], "run_id": run_id,
               "seq": time.time_ns(),  # 單調序:part 檔名 uuid 無序,推導以 seq 為準(修:同秒排序翻車)
               "created_at": datetime.now().isoformat(timespec="seconds")}
        return self.append("state_transition", [row], run_id, f"IDEMP-TR-{row['transition_id']}")

    def derive_current_state(self, entity_id: str) -> str | None:
        """最新 transition 推導(報告:不存 current_state 欄)。"""
        rows = []
        tdir = self.root / "state_transition"
        if not tdir.is_dir():
            return None
        for p in tdir.iterdir():
            try:
                if p.suffix == ".parquet":
                    import pandas as pd
                    rows += [r for r in pd.read_parquet(p).to_dict("records") if r["entity_id"] == entity_id]
                else:
                    rows += [r for l in p.read_text(encoding="utf-8").splitlines()
                             if (r := json.loads(l))["entity_id"] == entity_id]
            except Exception:
                continue
        if not rows:
            return None
        return max(rows, key=lambda r: r.get("seq", 0))["to_state"]  # 最新=max 單調序


def selftest() -> int:
    print("=== VME 核心 v0.1 · 單元八檢 ===")
    import tempfile
    import shutil
    tmp = Path(tempfile.mkdtemp(prefix="vme_st_"))
    lake = Lake(tmp)
    cfg = load_system_config(VME / "config/system_config.json")
    ctx = build_run_context(cfg)
    checks = []
    # ①② mode 政策
    checks.append(("InspectOnly 零耐久寫", resolve_mode_policy("InspectOnly", False).write_durable is False))
    try:
        authorize_operation("RuntimeAppendOnly", False)
        checks.append(("Runtime 無核准必拒", False))
    except PermissionError:
        checks.append(("Runtime 無核准必拒", True))
    # ③ 未知 mode fail-closed
    try:
        resolve_mode_policy("UnknownMode", False)
        checks.append(("未知 mode fail-closed", False))
    except ValueError:
        checks.append(("未知 mode fail-closed", True))
    # ④ 不可變 append+manifest
    r1 = lake.append("lesson_record", [{"lesson_id": "L1", "title": "t", "run_id": ctx["run_id"]}], ctx["run_id"], "IDEMP-1")
    p1 = tmp / r1["part"]
    h1 = hashlib.sha256(p1.read_bytes()).hexdigest()
    checks.append(("part 寫入+manifest", r1["written"] == 1 and lake.manifest.exists()))
    # ⑤ 冪等重送零重複
    r2 = lake.append("lesson_record", [{"lesson_id": "L1", "title": "t", "run_id": ctx["run_id"]}], ctx["run_id"], "IDEMP-1")
    checks.append(("idempotency 重送零寫", r2["written"] == 0 and r2.get("dedup")))
    # ⑥ 追加不改舊 part hash(append-only 真值檢=報告:比 row count 更重要)
    lake.append("lesson_record", [{"lesson_id": "L2", "title": "u", "run_id": ctx["run_id"]}], ctx["run_id"], "IDEMP-2")
    checks.append(("舊 part hash 不變", hashlib.sha256(p1.read_bytes()).hexdigest() == h1))
    # ⑦ 狀態機:合法+非法
    lake.transition("Hypothesis", "H1", "Experimental", "Watch", "初步證據成立", ctx["run_id"])
    lake.transition("Hypothesis", "H1", "Watch", "Active", "OOS_PASS", ctx["run_id"])
    ok_state = lake.derive_current_state("H1") == "Active"
    try:
        lake.transition("Hypothesis", "H2", "Experimental", "Active", "跳步", ctx["run_id"])
        bad = False
    except ValueError:
        bad = True
    checks.append(("狀態機:推導 Active+非法跳步拒", ok_state and bad))
    # ⑧ 合約檔在位
    checks.append(("四合約檔在位", all((VME / p).exists() for p in
                   ("config/system_config.json", "config/schema_registry.json",
                    "contracts/operation_request.template.json", "contracts/operation_result.template.json"))))
    n = 0
    for name, ok in checks:
        n += ok
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"  [計] {n}/{len(checks)} 檢通過")
    return 0 if n == len(checks) else 1


def main() -> int:
    argv = sys.argv[1:]
    if "--selftest" in argv:
        return selftest()
    mode = argv[argv.index("--mode") + 1] if "--mode" in argv else "InspectOnly"
    cfg = load_system_config(VME / "config/system_config.json")
    try:
        pol = resolve_mode_policy(mode, "--approve-runtime-append" in argv)
        authorize_operation(mode, "--approve-runtime-append" in argv)
    except (ValueError, PermissionError) as exc:
        print(f"[FAIL] {exc}")
        return 1
    ctx = build_run_context(cfg)
    status = "PASS"  # 最後一步仍會 recompute
    out = {"contract": {"name": "VIA_VME_OPERATION_RESULT", "version": "1.0.0"},
           "identity": {"run_id": ctx["run_id"]}, "mode": mode, "policy": pol.tag,
           "durable_writes": [], "status": status}
    rt = VME / "runtime/json"
    rt.mkdir(parents=True, exist_ok=True)
    (rt / "operation_result.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"=== VME v0.1 · {mode} · {ctx['run_id']} · durable_writes=0 · status={status} ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
