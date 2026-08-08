"""SSOT ↔ MS Project 同步引擎（append-only、衝突偵測、任務↔BOM 橋接）。

錨點（沿用你貼的 Gemini 架構）：
  - MS Project：[Project_ID]-[Task_ID]-[Timestamp]
  - BOM/PLM   ：[Part_Number]-[Revision]-[State]

同步原則：
  - 只增不減：任務內容變了 → 新增版本(v+1)、舊版標 deprecated，絕不覆寫。
  - 衝突偵測：相依死結（後續早於前置完成/循環）、資源超載（同資源時段重疊）。
  - 驗證後可用：同步報告列出 added/versioned/unchanged/conflicts，供人核可。
  - 橋接：任務可連到 BOM 料號（task ↔ part），打通排程與物料。
純 stdlib、離線、可測。
"""
from __future__ import annotations

import hashlib


# ── 錨點 ────────────────────────────────────────────────
def ms_anchor(project_id, task_id, ts=""):
    return f"{project_id}-{task_id}" + (f"-{ts}" if ts else "")


def bom_anchor(part, rev, state=""):
    return f"{part}-{rev}" + (f"-{state}" if state else "")


def _sig(task):
    """任務內容指紋（變更偵測用）——只取有意義欄位。"""
    keys = ("name", "resource", "start", "finish", "pct", "predecessors", "part")
    payload = "|".join(f"{k}={task.get(k, '')}" for k in keys)
    return hashlib.blake2s(payload.encode("utf-8"), digest_size=6).hexdigest()


# ── 同步（append-only 版本化）───────────────────────────
def sync_tasks(ssot: dict, tasks: list) -> dict:
    """把 MS Project 任務對帳進 SSOT。

    ssot: {anchor: {"sig":..., "version":n, "state":"active"/"deprecated", "task":{...}}}
          （會就地更新；傳入 {} 即首次建立）
    回傳報告 {added, versioned, unchanged, conflicts, ledger[]}
    """
    added, versioned, unchanged = [], [], []
    ledger = []
    for t in tasks:
        anchor = ms_anchor(t.get("project_id", "P"), t.get("task_id", "?"), "")
        sig = _sig(t)
        cur = ssot.get(anchor)
        if cur is None:
            ssot[anchor] = {"sig": sig, "version": 1, "state": "active", "task": dict(t)}
            added.append(anchor)
            ledger.append(("ADD", anchor, "v1"))
        elif cur["sig"] != sig:
            old_v = cur["version"]
            # append-only：保留舊版快照、建新版
            ssot.setdefault("_history", []).append(
                {"anchor": anchor, "version": old_v, "sig": cur["sig"],
                 "state": "deprecated", "task": cur["task"]})
            ssot[anchor] = {"sig": sig, "version": old_v + 1, "state": "active", "task": dict(t)}
            versioned.append(anchor)
            ledger.append(("VERSION", anchor, f"v{old_v}→v{old_v + 1}"))
        else:
            unchanged.append(anchor)
    conflicts = detect_conflicts(tasks)
    return {"added": added, "versioned": versioned, "unchanged": unchanged,
            "conflicts": conflicts, "ledger": ledger,
            "usable": len(conflicts) == 0}


# ── 衝突偵測 ────────────────────────────────────────────
def detect_conflicts(tasks: list) -> list:
    by_id = {t.get("task_id"): t for t in tasks}
    out = []
    # 相依死結：後續任務開始 < 前置任務完成
    for t in tasks:
        for pid in (t.get("predecessors") or []):
            p = by_id.get(pid)
            if p and t.get("start") and p.get("finish") and t["start"] < p["finish"]:
                out.append({"type": "schedule", "task": t.get("task_id"),
                            "detail": f"開始 {t['start']} 早於前置 {pid} 完成 {p['finish']}"})
    # 循環相依
    for t in tasks:
        seen = set()
        stack = list(t.get("predecessors") or [])
        while stack:
            n = stack.pop()
            if n == t.get("task_id"):
                out.append({"type": "cycle", "task": t.get("task_id"), "detail": "相依循環"})
                break
            if n in seen:
                continue
            seen.add(n)
            stack.extend(by_id.get(n, {}).get("predecessors") or [])
    # 資源超載：同資源、日期區間重疊
    res = {}
    for t in tasks:
        r = t.get("resource")
        if r and t.get("start") and t.get("finish"):
            res.setdefault(r, []).append(t)
    for r, ts in res.items():
        ts.sort(key=lambda x: x["start"])
        for i in range(len(ts) - 1):
            if ts[i]["finish"] > ts[i + 1]["start"]:
                out.append({"type": "resource", "task": ts[i + 1].get("task_id"),
                            "detail": f"資源 {r} 與 {ts[i].get('task_id')} 時段重疊(超載)"})
    return out


# ── 任務 ↔ BOM 橋接 ─────────────────────────────────────
def link_task_bom(tasks: list, bom_parts: list) -> dict:
    """把任務連到 BOM 料號：以任務 part 欄位或名稱含料號比對。"""
    part_ids = {p.get("part"): p for p in bom_parts}
    links, unlinked = [], []
    for t in tasks:
        pid = t.get("part")
        if not pid:
            pid = next((p for p in part_ids if p and p in (t.get("name") or "")), None)
        if pid and pid in part_ids:
            links.append({"task": t.get("task_id"), "part": pid,
                          "bom_anchor": bom_anchor(pid, part_ids[pid].get("rev", "A"),
                                                   part_ids[pid].get("state", "Active"))})
        else:
            unlinked.append(t.get("task_id"))
    return {"links": links, "unlinked": unlinked,
            "coverage": round(100 * len(links) / len(tasks), 1) if tasks else 0.0}


# ── 雙向回寫:SSOT → MS Project(append-only + 核可閘門)──────
def writeback_set(ssot, tasks, approved_only=True):
    """從 SSOT 產出可回寫 MS Project 的任務集。

    - 只取 active 版本(append-only:歷史版不回寫)。
    - 核可閘門:有未解決衝突的任務預設「保留、不自動回寫」(approved_only=True)。
    回傳 {writeback:[...], held:[...], conflicts:n}
    """
    conflicts = detect_conflicts(tasks)
    conflicted = {c["task"] for c in conflicts}
    writeback, held = [], []
    for t in tasks:
        tid = t.get("task_id")
        anchor = ms_anchor(t.get("project_id", "P"), tid, "")
        node = ssot.get(anchor)
        # 只回寫 active(若 SSOT 有記錄且非 active 則跳過)
        if node and node.get("state") not in (None, "active"):
            continue
        if approved_only and tid in conflicted:
            held.append({"task": tid, "reason": "未解決衝突,待人工核可"})
        else:
            writeback.append(t)
    return {"writeback": writeback, "held": held, "conflicts": len(conflicts),
            "approved_only": approved_only,
            "usable": True}   # 回寫集本身恆可用;衝突任務被 held 保護


def to_msproject_xml(tasks, project_name="VIA_SSOT_Export"):
    """便捷:SSOT 任務 → MS Project XML(委派 msproject_io)。"""
    from . import msproject_io
    return msproject_io.to_xml(tasks, project_name=project_name)


def roundtrip_check(tasks):
    from . import msproject_io
    return msproject_io.roundtrip(tasks)
