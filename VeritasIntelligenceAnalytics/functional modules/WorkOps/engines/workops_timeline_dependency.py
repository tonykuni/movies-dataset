# -*- coding: utf-8 -*-
r"""Veritas WorkOps 時間軸/依賴引擎 v0100 — GapFill 自建路 B(裁定序 D;append-only 連結)

六機制研究「下游衝擊」落地:里程碑間掛依賴(link A→B = B 依賴 A),build 重建每案
時間軸並算下游衝擊 — A 逾期/未完 → 依賴它的 B 全部列示受阻(提前發現問題)。
動詞:link MLS-A MLS-B / build(預設)/ list
側車:out/timeline_links.json(append-only)+ out/timeline.json(衍生,每跑重算)。
via-workops timeline。
"""
import json, sys
from datetime import datetime, date
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "out"
LINKS_P = OUT / "timeline_links.json"


def jload(p, d):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8-sig"))
    except Exception:
        return d


def cmd_link(a, b):
    ms = jload(OUT / "milestones.json", {}).get("items", {})
    for m in (a, b):
        if m not in ms:
            print("[FAIL] 查無里程碑 %s(先 milestones create)" % m)
            return 1
    d = jload(LINKS_P, {"links": []})
    if {"from": a, "to": b} in d["links"]:
        print("[略] 連結已存在(冪等)")
        return 0
    d["links"].append({"from": a, "to": b, "ts": datetime.now().isoformat(timespec="seconds")})
    OUT.mkdir(parents=True, exist_ok=True)
    LINKS_P.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    print("[依賴] %s → %s(%s 依賴 %s;append-only)" % (a, b, b, a))
    return 0


def cmd_build():
    ms = jload(OUT / "milestones.json", {}).get("items", {})
    links = jload(LINKS_P, {"links": []})["links"]
    dec = []
    today = date.today().isoformat()
    by_wop = {}
    for mid, it in ms.items():
        by_wop.setdefault(it["wop"], []).append((it.get("due", "9999"), mid, it))
    impact = []
    for lk in links:
        src = ms.get(lk["from"])
        if src and src["status"] == "OPEN":
            reason = "逾期" if src.get("due", "9999") < today else "未完"
            impact.append({"blocked": lk["to"], "by": lk["from"], "reason": reason,
                           "name": (ms.get(lk["to"]) or {}).get("name", "")})
    tl = {"ts": datetime.now().isoformat(timespec="seconds"),
          "wops": {w: [{"mid": m, "due": d_, "name": it["name"], "status": it["status"]}
                       for d_, m, it in sorted(rows)] for w, rows in by_wop.items()},
          "links": links, "impact": impact}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "timeline.json").write_text(json.dumps(tl, ensure_ascii=False, indent=1), encoding="utf-8")
    print("[時間軸] %d 案 · %d 里程碑 · %d 依賴連結 → out/timeline.json" % (len(by_wop), len(ms), len(links)))
    if impact:
        print("[下游衝擊] ⚠ %d 件受阻(提前發現):" % len(impact))
        for im in impact:
            print("  %s(%s)受阻於 %s(%s)" % (im["blocked"], im["name"][:24], im["by"], im["reason"]))
    else:
        print("[下游衝擊] 無受阻(或尚無依賴連結 — timeline link 建立)")
    return 0


def cmd_list():
    for lk in jload(LINKS_P, {"links": []})["links"]:
        print("  %s → %s(%s)" % (lk["from"], lk["to"], lk.get("ts", "")[:16]))
    return 0


def main(argv):
    a = argv[1:]
    try:
        if a and a[0] == "link":
            return cmd_link(a[1], a[2])
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
