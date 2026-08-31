# -*- coding: utf-8 -*-
r"""Veritas WorkOps 教訓引擎 v0100 — GapFill 自建路 B(裁定序 F;候選+顯式確認)

AI 推論絕不冒充正式教訓:build 只列候選(來源:結案記錄未出教訓者+決策逾期完成者
+風險越級後解決者);confirm 由人補「根因/預防/複用規則」後才發 LLN-####(append-only)。
複用規則可回饋:追蹤節奏(提早檢查點)→ watchtower、歸戶規則 → product_code_map(人工貼)。
動詞:build(預設)/ confirm 候選序號 --root-cause X --prevention Y [--reuse-rule Z] / list
側車:out/lesson_candidates.json(衍生)+ out/lessons.json(append-only)。
via-workops lessons。
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
CAND_P = OUT / "lesson_candidates.json"
LSN_P = OUT / "lessons.json"


def jload(p, d):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8-sig"))
    except Exception:
        return d


def now():
    return datetime.now().isoformat(timespec="seconds")


def cmd_build():
    lessons = jload(LSN_P, {}).get("items", {})
    used = set((v.get("source") or "") for v in lessons.values())
    cands = []
    cls = jload(OUT / "closures.json", {}).get("items", {})
    for cid, v in sorted(cls.items()):
        if cid not in used:
            cands.append({"source": cid, "wop": v.get("wop", ""), "kind": "結案",
                          "situation": "%s(%s)結案:%s" % (v.get("wop", ""), v.get("label", ""), v.get("reason", ""))})
    try:
        with io.open(OUT / "decision_log.csv", "r", encoding="utf-8-sig", errors="replace", newline="") as f:
            for r in csv.DictReader(f):
                did = r.get("編號", "")
                late = (r.get("狀態") == "DONE" and (r.get("完成日") or "") > (r.get("截止") or "9999"))
                if late and did and did not in used:
                    cands.append({"source": did, "wop": "", "kind": "決策逾期",
                                  "situation": "%s 逾期完成(截止 %s)— 建議提早檢查點" % (did, r.get("截止", ""))})
    except Exception:
        pass
    fl = jload(OUT / "reply_status.json", {}).get("flags", {})
    st = jload(OUT / "reply_status.json", {}).get("status", {})
    for thr, f in fl.items():
        key = "RISK|" + thr
        if f.get("risk") and (st.get(thr) or {}).get("status") == "已完成" and key not in used:
            cands.append({"source": key, "wop": "", "kind": "風險解除",
                          "situation": "%s 曾風險越級後完結 — 值得記錄升級路徑" % thr})
    CAND_P.parent.mkdir(parents=True, exist_ok=True)
    CAND_P.write_text(json.dumps({"ts": now(), "candidates": cands}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("[教訓候選] %d 件(AI 只提名;confirm 補根因/預防才成正式教訓)→ %s" % (len(cands), CAND_P.name))
    for i, c in enumerate(cands[:10]):
        print("  [%d] %-6s %s" % (i, c["kind"], c["situation"][:60]))
    if not cands:
        print("  (無候選 — 誠實不湊)")
    return 0


def cmd_confirm(idx, root_cause, prevention, reuse_rule=""):
    if not root_cause or not prevention:
        print("[FAIL] 需 --root-cause 與 --prevention(人工確認=正式教訓唯一路徑)")
        return 1
    cands = jload(CAND_P, {}).get("candidates", [])
    try:
        c = cands[int(idx)]
    except (ValueError, IndexError):
        print("[FAIL] 候選序號無效(先 lessons build)")
        return 1
    d = jload(LSN_P, {"seq": 0, "items": {}})
    if any(v.get("source") == c["source"] for v in d["items"].values()):
        print("[略] 此候選已成教訓(冪等)")
        return 0
    d["seq"] += 1
    lid = "LLN-%04d" % d["seq"]
    d["items"][lid] = {"source": c["source"], "wop": c.get("wop", ""), "kind": c["kind"],
                       "situation": c["situation"], "root_cause": root_cause,
                       "prevention": prevention, "reuse_rule": reuse_rule, "ts": now()}
    OUT.mkdir(parents=True, exist_ok=True)
    LSN_P.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    print("[教訓] %s 正式成立(源 %s)" % (lid, c["source"]))
    if reuse_rule:
        print("[複用] 「%s」— 追蹤類貼 watchtower_params、歸戶類貼 product_code_map(人工套用,不自動改參)" % reuse_rule)
    return 0


def cmd_list():
    d = jload(LSN_P, {"items": {}})
    for lid, v in sorted(d["items"].items()):
        print("  %s [%s] %s" % (lid, v.get("kind", ""), v.get("situation", "")[:52]))
        print("        根因:%s · 預防:%s" % (v.get("root_cause", ""), v.get("prevention", "")))
    print("[共] %d 筆正式教訓" % len(d["items"]))
    return 0


def main(argv):
    a = argv[1:]

    def opt(flag):
        return a[a.index(flag) + 1] if flag in a and a.index(flag) + 1 < len(a) else ""
    try:
        if a and a[0] == "confirm":
            return cmd_confirm(a[1], opt("--root-cause"), opt("--prevention"), opt("--reuse-rule"))
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
