# -*- coding: utf-8 -*-
r"""Veritas WorkOps 案件結案智能 v0100 — GapFill 自建路 B(裁定序 E;候選+顯式確認)

絕不自動結案:build 只產「結案候選」(證據齊備的 WOP 案:里程碑全完+最新回覆已完成
+無未結決議);confirm 需人下令才發 CLS-####(append-only;WOP 編號與 registry 零觸碰,
結案記錄獨立側車,板/矩陣讀取對照)。閉環一致性:結案候選=Lesson Learned 候選源。
動詞:build(預設)/ confirm WOP-#### --reason 事由 / list
側車:out/closure_candidates.json(衍生)+ out/closures.json(append-only)。
via-workops closure。
"""
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全引擎導入令 2026-08-18;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # accel_map/fetch/pip_install/run_fast
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
import csv, io, json, sys
from datetime import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "out"
CAND_P = OUT / "closure_candidates.json"
CLS_P = OUT / "closures.json"


def jload(p, d):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8-sig"))
    except Exception:
        return d


def now():
    return datetime.now().isoformat(timespec="seconds")


def open_decisions():
    try:
        with io.open(OUT / "decision_log.csv", "r", encoding="utf-8-sig", errors="replace", newline="") as f:
            return {(r.get("關聯THR") or ""): r for r in csv.DictReader(f) if (r.get("狀態") or "") != "DONE"}
    except Exception:
        return {}


def cmd_build():
    reg = jload(OUT / "wop_registry.json", {}).get("projects", {}) or {}
    ms = jload(OUT / "milestones.json", {}).get("items", {})
    rs = jload(OUT / "reply_status.json", {}).get("status", {})
    closed = set(v.get("wop") for v in jload(CLS_P, {}).get("items", {}).values())
    odec = open_decisions()
    cands = []
    for wid, pr in reg.items():
        if wid in closed:
            continue
        wms = [it for it in ms.values() if it["wop"] == wid]
        ms_done = bool(wms) and all(it["status"] == "COMPLETED" for it in wms)
        thr_done = [t for t in pr.get("thr", []) if (rs.get(t) or {}).get("status") == "已完成"]
        dec_block = [t for t in pr.get("thr", []) if t in odec]
        evidence = []
        if ms_done:
            evidence.append("里程碑 %d/%d 全完" % (len(wms), len(wms)))
        if thr_done:
            evidence.append("回覆已完成 %d 串" % len(thr_done))
        if evidence and not dec_block:
            cands.append({"wop": wid, "label": pr.get("label", ""), "evidence": evidence})
    CAND_P.parent.mkdir(parents=True, exist_ok=True)
    CAND_P.write_text(json.dumps({"ts": now(), "candidates": cands}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("[結案候選] %d 件(證據齊備;絕不自動結案 — confirm 才成立)→ %s" % (len(cands), CAND_P.name))
    for c in cands[:10]:
        print("  %s %s · %s" % (c["wop"], c["label"][:24], " / ".join(c["evidence"])))
    if not cands:
        print("  (無候選 — 里程碑未全完或回覆無已完成訊號;誠實不湊)")
    return 0


def cmd_confirm(wop, reason):
    if not reason:
        print("[FAIL] 需 --reason 事由(人工顯式確認=結案唯一路徑)")
        return 1
    d = jload(CLS_P, {"seq": 0, "items": {}})
    if any(v.get("wop") == wop for v in d["items"].values()):
        print("[略] %s 已有結案記錄(冪等;編號永不變)" % wop)
        return 0
    d["seq"] += 1
    cid = "CLS-%04d" % d["seq"]
    label = (jload(OUT / "wop_registry.json", {}).get("projects", {}).get(wop) or {}).get("label", "")
    d["items"][cid] = {"wop": wop, "label": label, "reason": reason, "ts": now(),
                      "lesson_candidate": True}
    OUT.mkdir(parents=True, exist_ok=True)
    CLS_P.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    print("[結案] %s ← %s(%s)· 事由:%s" % (cid, wop, label, reason))
    print("[閉環] 已標 Lesson 候選 — via-workops lessons build 檢視")
    return 0


def cmd_list():
    d = jload(CLS_P, {"items": {}})
    for cid, v in sorted(d["items"].items()):
        print("  %s %s %s · %s · %s" % (cid, v["wop"], v.get("label", "")[:24], v.get("reason", ""), v.get("ts", "")[:16]))
    print("[共] %d 件正式結案" % len(d["items"]))
    return 0


def main(argv):
    a = argv[1:]

    def opt(flag):
        return a[a.index(flag) + 1] if flag in a and a.index(flag) + 1 < len(a) else ""
    try:
        if a and a[0] == "confirm":
            return cmd_confirm(a[1], opt("--reason"))
        if a and a[0] == "list":
            return cmd_list()
        if not a or a[0] == "build":
            return cmd_build()
    except IndexError:
        pass
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
